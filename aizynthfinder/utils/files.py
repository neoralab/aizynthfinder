"""Utilities for working with output files and subprocess orchestration."""

from __future__ import annotations

import asyncio
import gzip
import json
import os
import subprocess
import tempfile
import time
import warnings
from collections.abc import Callable, Iterator, Sequence
from contextlib import ExitStack
from pathlib import Path
from typing import Any, TypeAlias

import pandas as pd
from deprecated import deprecated

from aizynthfinder.domain import SmilesBatch
from aizynthfinder.utils.logging import logger

_HDF_FILE_SUFFIXES = (".hdf5", ".hdf")
CommandFactory: TypeAlias = Callable[[int, Any], Sequence[str]]


def _is_hdf5_file(filename: str | Path) -> bool:
    return str(filename).endswith(_HDF_FILE_SUFFIXES)


def _ensure_tree_column(data: pd.DataFrame, filename: str | Path) -> None:
    if "trees" not in data.columns:
        raise ValueError(
            f"Cannot extract trees from {filename!s}: missing required 'trees' column"
        )


def _collect_tree_payloads(
    dataframes: Sequence[tuple[str | Path, pd.DataFrame]], trees_name: str | None
) -> tuple[list[Any] | None, list[pd.DataFrame]]:
    if not trees_name:
        return None, [dataframe for _, dataframe in dataframes]

    first_filename, first_dataframe = dataframes[0]
    if "trees" not in first_dataframe.columns:
        return None, [dataframe for _, dataframe in dataframes]

    tree_payloads: list[Any] = []
    dataframes_without_trees: list[pd.DataFrame] = []
    for filename, dataframe in dataframes:
        _ensure_tree_column(dataframe, filename)
        tree_payloads.extend(dataframe["trees"].tolist())
        dataframes_without_trees.append(dataframe.drop(columns="trees"))
    return tree_payloads, dataframes_without_trees


def _normalize_trees_filename(filename: str) -> str:
    return filename if filename.endswith(".gz") else f"{filename}.gz"


def _write_tree_payloads(tree_payloads: Sequence[Any], trees_name: str) -> None:
    with gzip.open(_normalize_trees_filename(trees_name), "wt", encoding="utf-8") as fileobj:
        json.dump(list(tree_payloads), fileobj)


def read_datafile(filename: str | Path) -> pd.DataFrame:
    """Read AiZynthFinder output data from disk.

    Args:
        filename: Path to a JSON or HDF5 data file.

    Returns:
        The loaded tabular data.
    """
    if _is_hdf5_file(filename):
        return pd.read_hdf(filename, "table")
    return pd.read_json(filename, orient="table")


async def read_datafile_async(filename: str | Path) -> pd.DataFrame:
    """Asynchronously read an output data file.

    Args:
        filename: Path to a JSON or HDF5 data file.

    Returns:
        The loaded tabular data.
    """
    return await asyncio.to_thread(read_datafile, filename)


def save_datafile(data: pd.DataFrame, filename: str | Path) -> None:
    """Persist output data to disk.

    Args:
        data: The data to serialize.
        filename: Path to a JSON or HDF5 output file.
    """
    if _is_hdf5_file(filename):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data.to_hdf(filename, key="table")
        return

    data.to_json(filename, orient="table")


async def save_datafile_async(data: pd.DataFrame, filename: str | Path) -> None:
    """Asynchronously persist output data to disk.

    Args:
        data: The data to serialize.
        filename: Path to a JSON or HDF5 output file.
    """
    await asyncio.to_thread(save_datafile, data, filename)


@deprecated(version="4.0.0", reason="replaced by 'cat_datafiles'")
def cat_hdf_files(input_files: list[str], output_name: str, trees_name: str | None = None) -> None:
    """Concatenate HDF5 or JSON data files."""
    cat_datafiles(input_files, output_name, trees_name)


def cat_datafiles(input_files: list[str], output_name: str, trees_name: str | None = None) -> None:
    """Concatenate multiple output files into a single artifact.

    Args:
        input_files: Paths to the files to concatenate.
        output_name: Path to the merged tabular output file.
        trees_name: Optional path for a gzipped JSON file containing serialized
            tree payloads extracted from the ``trees`` column.
    """
    if not input_files:
        raise ValueError("Expected at least one input file")

    dataframes = [(filename, read_datafile(filename)) for filename in input_files]
    tree_payloads, tabular_data = _collect_tree_payloads(dataframes, trees_name)
    concatenated_data = pd.concat(tabular_data, ignore_index=True)

    save_datafile(concatenated_data, output_name)
    if tree_payloads is not None and trees_name:
        _write_tree_payloads(tree_payloads, trees_name)


def _create_temp_filename() -> str:
    file_descriptor, filename = tempfile.mkstemp()
    os.close(file_descriptor)
    Path(filename).unlink(missing_ok=True)
    return filename


def _line_batches(lines: Sequence[str], nparts: int) -> Iterator[list[str]]:
    batch_size, remainder = divmod(len(lines), nparts)
    start = 0
    for part_index in range(nparts):
        stop = start + batch_size + (1 if part_index < remainder else 0)
        yield list(lines[start:stop])
        start = stop


def split_file(filename: str | Path, nparts: int) -> list[str]:
    """Split a text file into temporary batches.

    Args:
        filename: Path to the input text file.
        nparts: Number of parts to create.

    Returns:
        A list of temporary filenames.
    """
    if nparts <= 0:
        raise ValueError("nparts must be a positive integer")

    lines = Path(filename).read_text(encoding="utf-8").splitlines()

    filenames: list[str] = []
    for line_batch in _line_batches(lines, nparts):
        temp_filename = _create_temp_filename()
        Path(temp_filename).write_text("\n".join(line_batch), encoding="utf-8")
        filenames.append(temp_filename)
    return filenames


def load_smiles_batch(filename: str | Path) -> SmilesBatch:
    """Load a SMILES batch from a text file.

    Args:
        filename: Path to the SMILES input file.

    Returns:
        A lightweight immutable batch model.
    """
    path = Path(filename)
    smiles = tuple(line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return SmilesBatch(source=path, smiles=smiles)


async def load_smiles_batch_async(filename: str | Path) -> SmilesBatch:
    """Asynchronously load a SMILES batch from disk.

    Args:
        filename: Path to the SMILES input file.

    Returns:
        A lightweight immutable batch model.
    """
    return await asyncio.to_thread(load_smiles_batch, filename)


def _wait_for_processes(
    processes: Sequence[subprocess.Popen[Any]],
    output_fileobjs: Sequence[Any],
    poll_freq: int,
) -> None:
    logger().info("Waiting for background tasks to complete...")
    while True:
        time.sleep(poll_freq)
        unfinished_processes = 0
        for process, fileobj in zip(processes, output_fileobjs):
            fileobj.flush()
            if process.poll() is None:
                unfinished_processes += 1
        if unfinished_processes == 0:
            return


def _raise_for_failed_processes(processes: Sequence[subprocess.Popen[Any]], log_prefix: str) -> None:
    failed_processes = [
        (index, process.returncode)
        for index, process in enumerate(processes, start=1)
        if process.returncode not in (0, None)
    ]
    if not failed_processes:
        return

    failed_processes_str = ", ".join(
        f"{index} (exit code {returncode}, log: {log_prefix}{index}.log)"
        for index, returncode in failed_processes
    )
    raise subprocess.CalledProcessError(
        returncode=failed_processes[0][1],
        cmd=f"background processes for prefix {log_prefix}",
        output=f"Processes failed: {failed_processes_str}",
    )


def start_processes(
    inputs: Sequence[Any],
    log_prefix: str,
    cmd_callback: CommandFactory,
    poll_freq: int = 5,
) -> None:
    """Start background subprocesses and wait for completion.

    Args:
        inputs: Input values used to build subprocess commands.
        log_prefix: Prefix for process log files.
        cmd_callback: Callback that creates each subprocess command.
        poll_freq: Polling interval, in seconds.
    """
    if poll_freq <= 0:
        raise ValueError("poll_freq must be a positive integer")

    processes: list[subprocess.Popen[Any]] = []
    with ExitStack() as stack:
        output_fileobjs: list[Any] = []
        for index, input_item in enumerate(inputs, 1):
            logfile = stack.enter_context(
                open(f"{log_prefix}{index}.log", "w", encoding="utf-8")
            )
            output_fileobjs.append(logfile)
            cmd = list(cmd_callback(index, input_item))
            process = subprocess.Popen(cmd, stdout=logfile, stderr=subprocess.STDOUT)
            processes.append(process)
            logger().info("Started background task with pid=%s", process.pid)

        _wait_for_processes(processes, output_fileobjs, poll_freq)

    _raise_for_failed_processes(processes, log_prefix)
