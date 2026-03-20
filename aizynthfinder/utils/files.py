"""Utilities for working with output files and subprocess orchestration."""

from __future__ import annotations

import asyncio
import gzip
import json
import subprocess
import tempfile
import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from deprecated import deprecated

from aizynthfinder.domain import SmilesBatch
from aizynthfinder.utils.logging import logger

if TYPE_CHECKING:
    from aizynthfinder.utils.type_utils import (
        Any,
        Callable,
        List,
        Optional,
        Sequence,
        Union,
    )


def read_datafile(filename: Union[str, Path]) -> pd.DataFrame:
    """Read AiZynthFinder output data from disk.

    Args:
        filename: Path to a JSON or HDF5 data file.

    Returns:
        The loaded tabular data.
    """
    filename_str = str(filename)
    if filename_str.endswith(".hdf5") or filename_str.endswith(".hdf"):
        return pd.read_hdf(filename, "table")
    return pd.read_json(filename, orient="table")


async def read_datafile_async(filename: Union[str, Path]) -> pd.DataFrame:
    """Asynchronously read an output data file.

    Args:
        filename: Path to a JSON or HDF5 data file.

    Returns:
        The loaded tabular data.
    """
    return await asyncio.to_thread(read_datafile, filename)


def save_datafile(data: pd.DataFrame, filename: Union[str, Path]) -> None:
    """Persist output data to disk.

    Args:
        data: The data to serialize.
        filename: Path to a JSON or HDF5 output file.
    """
    filename_str = str(filename)
    if filename_str.endswith(".hdf5") or filename_str.endswith(".hdf"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data.to_hdf(filename, key="table")
    else:
        data.to_json(filename, orient="table")


async def save_datafile_async(data: pd.DataFrame, filename: Union[str, Path]) -> None:
    """Asynchronously persist output data to disk.

    Args:
        data: The data to serialize.
        filename: Path to a JSON or HDF5 output file.
    """
    await asyncio.to_thread(save_datafile, data, filename)


@deprecated(version="4.0.0", reason="replaced by 'cat_datafiles'")
def cat_hdf_files(input_files: List[str], output_name: str, trees_name: Optional[str] = None) -> None:
    """Concatenate HDF5 or JSON data files."""
    cat_datafiles(input_files, output_name, trees_name)


def cat_datafiles(input_files: List[str], output_name: str, trees_name: Optional[str] = None) -> None:
    """Concatenate multiple output files into a single artifact.

    Args:
        input_files: Paths to the files to concatenate.
        output_name: Path to the merged tabular output file.
        trees_name: Optional path for a gzipped JSON file containing serialized
            tree payloads extracted from the ``trees`` column.
    """
    data = read_datafile(input_files[0])
    if "trees" not in data.columns:
        trees_name = None

    if trees_name:
        columns = list(data.columns)
        columns.remove("trees")
        trees = list(data["trees"].values)
        data = data[columns]

    for filename in input_files[1:]:
        new_data = read_datafile(filename)
        if trees_name:
            trees.extend(new_data["trees"].values)
            new_data = new_data[columns]
        data = pd.concat([data, new_data])

    save_datafile(data.reset_index(drop=True), output_name)
    if trees_name:
        if not trees_name.endswith(".gz"):
            trees_name += ".gz"
        with gzip.open(trees_name, "wt", encoding="UTF-8") as fileobj:
            json.dump(trees, fileobj)


def split_file(filename: str, nparts: int) -> List[str]:
    """Split a text file into temporary batches.

    Args:
        filename: Path to the input text file.
        nparts: Number of parts to create.

    Returns:
        A list of temporary filenames.
    """
    with open(filename, "r", encoding="utf-8") as fileobj:
        lines = fileobj.read().splitlines()

    filenames = []
    batch_size, remainder = divmod(len(lines), nparts)
    stop = 0
    for part in range(1, nparts + 1):
        start = stop
        stop += batch_size + 1 if part <= remainder else batch_size
        filenames.append(tempfile.mktemp())
        with open(filenames[-1], "w", encoding="utf-8") as fileobj:
            fileobj.write("\n".join(lines[start:stop]))
    return filenames


def load_smiles_batch(filename: str) -> SmilesBatch:
    """Load a SMILES batch from a text file.

    Args:
        filename: Path to the SMILES input file.

    Returns:
        A lightweight immutable batch model.
    """
    path = Path(filename)
    smiles = tuple(line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return SmilesBatch(source=path, smiles=smiles)


async def load_smiles_batch_async(filename: str) -> SmilesBatch:
    """Asynchronously load a SMILES batch from disk.

    Args:
        filename: Path to the SMILES input file.

    Returns:
        A lightweight immutable batch model.
    """
    return await asyncio.to_thread(load_smiles_batch, filename)


def start_processes(inputs: Sequence[Any], log_prefix: str, cmd_callback: Callable, poll_freq: int = 5) -> None:
    """Start background subprocesses and wait for completion.

    Args:
        inputs: Input values used to build subprocess commands.
        log_prefix: Prefix for process log files.
        cmd_callback: Callback that creates each subprocess command.
        poll_freq: Polling interval, in seconds.
    """
    processes = []
    output_fileobjs = []
    for index, iinput in enumerate(inputs, 1):
        output_fileobjs.append(open(f"{log_prefix}{index}.log", "w", encoding="utf-8"))
        cmd = cmd_callback(index, iinput)
        processes.append(subprocess.Popen(cmd, stdout=output_fileobjs[-1], stderr=subprocess.STDOUT))
        logger().info(f"Started background task with pid={processes[-1].pid}")

    logger().info("Waiting for background tasks to complete...")
    not_finished = True
    while not_finished:
        time.sleep(poll_freq)
        not_finished = False
        for process, fileobj in zip(processes, output_fileobjs):
            fileobj.flush()
            if process.poll() is None:
                not_finished = True

    for fileobj in output_fileobjs:
        fileobj.close()
