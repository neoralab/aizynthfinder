"""Command-line entry points and batch orchestration for AiZynthFinder."""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import tempfile
import time
from collections import defaultdict
from collections.abc import Iterable
from typing import TYPE_CHECKING, Callable

import pandas as pd

from aizynthfinder.aizynthfinder import AiZynthFinder
from aizynthfinder.chem import Molecule
from aizynthfinder.utils.files import (
    cat_datafiles,
    load_smiles_batch,
    save_datafile,
    split_file,
    start_processes,
)
from aizynthfinder.utils.logging import logger, setup_logger

if TYPE_CHECKING:
    from aizynthfinder.utils.type_utils import (
        Any,
        Callable,
        Dict,
        List,
        Optional,
        StrDict,
    )

    _PostProcessingJob = Callable[[AiZynthFinder], StrDict]
    _PreProcessingJob = Callable[[AiZynthFinder, int], None]


def _do_clustering(
    finder: AiZynthFinder,
    results: StrDict,
    detailed_results: bool,
) -> None:
    time0 = time.perf_counter_ns()
    results["cluster_labels"] = finder.routes.cluster(n_clusters=0)  # type: ignore
    if not detailed_results:
        return

    results["cluster_time"] = (time.perf_counter_ns() - time0) * 1e-9
    results["distance_matrix"] = finder.routes.distance_matrix().tolist()


def _do_post_processing(finder: AiZynthFinder, results: StrDict, jobs: List[_PostProcessingJob]) -> None:
    for job in jobs:
        results.update(job(finder))


def _get_arguments() -> argparse.Namespace:
    """Parse command-line arguments for ``aizynthcli``."""
    parser = argparse.ArgumentParser("aizynthcli")
    parser.add_argument(
        "--smiles",
        required=True,
        help="the target molecule smiles or the path of a file containing the smiles",
    )
    parser.add_argument("--config", required=True, help="the filename of a configuration file")
    parser.add_argument(
        "--policy",
        nargs="+",
        default=[],
        help="the name of the expansion policy to use",
    )
    parser.add_argument("--filter", nargs="+", default=[], help="the name of the filter to use")
    parser.add_argument("--stocks", nargs="+", default=[], help="the name of the stocks to use")
    parser.add_argument("--output", help="the name of the output file (JSON or HDF5 file)")
    parser.add_argument(
        "--log_to_file",
        action="store_true",
        default=False,
        help="if provided, detailed logging to file is enabled",
    )
    parser.add_argument(
        "--nproc",
        type=int,
        help="if given, the input is split over a number of processes",
    )
    parser.add_argument(
        "--cluster",
        action="store_true",
        default=False,
        help="if provided, perform automatic clustering",
    )
    parser.add_argument(
        "--post_processing",
        nargs="+",
        help="a number of modules that performs post-processing tasks",
    )
    parser.add_argument("--pre_processing", help="a module that perform pre-processing tasks")
    parser.add_argument(
        "--checkpoint",
        required=False,
        help="the path to the checkpoint file",
    )
    return parser.parse_args()


def _load_postprocessing_jobs(modules: Optional[List[str]]) -> List[_PostProcessingJob]:
    jobs: List[_PostProcessingJob] = []
    for module_name in modules or []:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            logger().warning("Post-processing module '%s' could not be imported", module_name)
            continue
        if hasattr(module, "post_processing"):
            print(f"Adding post-processing job from {module_name}")
            jobs.append(getattr(module, "post_processing"))
    return jobs


def _load_preprocessing_job(module_name: Optional[str]) -> Optional[_PreProcessingJob]:
    if not module_name:
        return None

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        logger().warning("Pre-processing module '%s' could not be imported", module_name)
        return None

    if hasattr(module, "pre_processing"):
        print(f"Adding pre-processing job from {module_name}")
        return getattr(module, "pre_processing")
    return None


def _select_stocks(finder: AiZynthFinder, args: argparse.Namespace) -> None:
    stocks = list(args.stocks)
    try:
        module = importlib.import_module("custom_stock")
    except ModuleNotFoundError:
        pass
    else:
        if hasattr(module, "stock"):
            finder.stock.load(module.stock, "custom_stock")  # type: ignore
            stocks.append("custom_stock")
    finder.stock.select(stocks or finder.stock.items)


def _load_checkpoint(
    checkpoint: str,
) -> Dict[str, List[Any]]:
    """Load checkpointed batch results from newline-delimited JSON."""
    if not os.path.exists(checkpoint):
        return defaultdict(list)
    with open(checkpoint) as json_file:
        checkpoint_data = [json.loads(line) for line in json_file]

    checkpoint_results = defaultdict(list)
    if checkpoint_data:
        checkpoint_results["processed_smiles"] = [data["processed_smiles"] for data in checkpoint_data]
        for data in checkpoint_data:
            for key, value in data["results"].items():
                checkpoint_results[key].append(value)
    return checkpoint_results


def _prepare_and_build_routes(
    finder: AiZynthFinder,
    smiles: str,
    show_progress: bool,
) -> float:
    """Prepare the search tree, execute search, and build scored routes."""
    finder.target_smiles = smiles
    finder.prepare_tree()
    search_time = finder.tree_search(show_progress=show_progress)
    finder.build_routes()
    finder.routes.compute_scores(*finder.scorers.objects())
    return search_time


def _format_setup_error(smiles: str | None, error: ValueError) -> str:
    prefix = f"Failed to setup search for {smiles}" if smiles else "Failed to setup search"
    return f"{prefix} due to: '{str(error).lower()}'"


def _store_processed_results(
    results: StrDict,
    processed_results: StrDict,
) -> None:
    for key, value in processed_results.items():
        results[key].append(value)


def _create_processed_results(
    finder: AiZynthFinder,
    stats: StrDict,
) -> StrDict:
    processed_results = dict(stats)
    processed_results["stock_info"] = finder.stock_info()
    processed_results["trees"] = finder.routes.dict_with_extra(include_metadata=True, include_scores=True)
    return processed_results


def _append_checkpoint_entry(checkpoint: str, smiles: str, processed_results: StrDict) -> None:
    with open(checkpoint, "a") as checkpoint_file:
        checkpoint_file.write(json.dumps({"processed_smiles": smiles, "results": processed_results}) + "\n")
    logger().debug("Results for processed smiles '%s' saved to %s", smiles, checkpoint)


def _configure_policy_selection(finder: AiZynthFinder, args: argparse.Namespace) -> None:
    finder.expansion_policy.select(args.policy or finder.expansion_policy.items[0])
    if args.filter:
        finder.filter_policy.select(args.filter)
        return
    finder.filter_policy.select_all()


def _prepare_finder(args: argparse.Namespace) -> tuple[AiZynthFinder, List[_PostProcessingJob], Optional[_PreProcessingJob]]:
    finder = AiZynthFinder(configfile=args.config)
    _select_stocks(finder, args)
    post_processing = _load_postprocessing_jobs(args.post_processing)
    pre_processing = _load_preprocessing_job(args.pre_processing)
    _configure_policy_selection(finder, args)
    return finder, post_processing, pre_processing


def _process_single_smiles(
    smiles: str,
    finder: AiZynthFinder,
    output_name: str,
    do_clustering: bool,
    post_processing: List[_PostProcessingJob],
    pre_processing: Optional[_PreProcessingJob],
) -> None:
    output_name = output_name or "trees.json"
    if pre_processing:
        pre_processing(finder, -1)
    try:
        _prepare_and_build_routes(finder, smiles, show_progress=True)
    except ValueError as err:
        print(_format_setup_error(None, err))
        return

    with open(output_name, "w") as fileobj:
        json.dump(
            finder.routes.dict_with_extra(include_metadata=True, include_scores=True),
            fileobj,
            indent=2,
        )
    logger().info("Trees saved to %s", output_name)

    stats = finder.extract_statistics()
    if do_clustering:
        _do_clustering(finder, stats, detailed_results=False)
    _do_post_processing(finder, stats, post_processing)
    stats_str = "\n".join(f"{key.replace('_', ' ')}: {value}" for key, value in stats.items())
    logger().info(stats_str)


def _process_multi_smiles(
    filename: str,
    finder: AiZynthFinder,
    output_name: str,
    do_clustering: bool,
    post_processing: List[_PostProcessingJob],
    pre_processing: Optional[_PreProcessingJob],
    checkpoint: Optional[str],
) -> None:
    output_name = output_name or "output.json.gz"
    smiles = list(load_smiles_batch(filename).smiles)

    checkpoint_data: StrDict = defaultdict(list)
    if checkpoint:
        checkpoint_data = _load_checkpoint(checkpoint)
        start = len(checkpoint_data["processed_smiles"]) if checkpoint_data else 0
        smiles = smiles[start:]

    results: StrDict = defaultdict(list)
    if checkpoint_data:
        results = {key: value for key, value in checkpoint_data.items() if key != "processed_smiles"}
    for idx, smi in enumerate(smiles):
        if pre_processing:
            pre_processing(finder, idx)
        try:
            search_time = _prepare_and_build_routes(finder, smi, show_progress=False)
        except ValueError as err:
            print(_format_setup_error(smi, err))
            continue

        stats = finder.extract_statistics()
        solved_str = "is solved" if stats["is_solved"] else "is not solved"
        logger().info("Done with %s in %.3f s and %s", smi, search_time, solved_str)
        if do_clustering:
            _do_clustering(finder, stats, detailed_results=True)
        _do_post_processing(finder, stats, post_processing)

        processed_results = _create_processed_results(finder, stats)
        if checkpoint:
            _append_checkpoint_entry(checkpoint, smi, processed_results)

        _store_processed_results(results, processed_results)

    data = pd.DataFrame.from_dict(results)
    save_datafile(data, output_name)
    logger().info("Output saved to %s", output_name)


def _create_multiprocess_command(
    args: argparse.Namespace,
    json_files: Iterable[str],
) -> Callable[[int, str], list[str]]:
    json_file_list = list(json_files)

    def create_cmd(index, filename):
        cmd_args = [
            "aizynthcli",
            "--smiles",
            filename,
            "--config",
            args.config,
            "--output",
            json_file_list[index - 1],
        ]
        if args.policy:
            cmd_args.extend(["--policy"] + args.policy)
        if args.filter:
            cmd_args.extend(["--filter"] + args.filter)
        if args.stocks:
            cmd_args.append("--stocks")
            cmd_args.extend(args.stocks)
        if args.cluster:
            cmd_args.append("--cluster")
        if args.post_processing:
            cmd_args.extend(["--post_processing"] + args.post_processing)
        return cmd_args

    return create_cmd


def _multiprocess_smiles(args: argparse.Namespace) -> None:
    if not os.path.exists(args.smiles):
        raise ValueError("For multiprocessing execution the --smiles argument needs to be a filename")

    setup_logger(logging.INFO)
    filenames = split_file(args.smiles, args.nproc)
    json_files = [tempfile.mktemp(suffix=".json.gz") for _ in range(args.nproc)]
    start_processes(filenames, "aizynthcli", _create_multiprocess_command(args, json_files))

    if not all(os.path.exists(filename) for filename in json_files):
        raise FileNotFoundError(
            "Not all output files produced. Please check the individual log files: 'aizynthcli*.log'"
        )
    cat_datafiles(json_files, args.output or "output.json.gz")


def main() -> None:
    """Entry point for the aizynthcli command"""
    args = _get_arguments()

    file_level_logging = logging.DEBUG if args.log_to_file else None
    setup_logger(logging.INFO, file_level_logging)

    if not os.path.exists(args.smiles):
        mol = Molecule(smiles=args.smiles)
        if mol.rd_mol is None:
            logger().error(
                f"The --smiles argument ({args.smiles})"
                " does not point to an existing file or is a valid RDKit SMILES."
                " Cannot start retrosynthesis planning."
            )
            return

    if args.nproc:
        _multiprocess_smiles(args)
        return

    finder, post_processing, pre_processing = _prepare_finder(args)
    if os.path.exists(args.smiles):
        _process_multi_smiles(
            args.smiles,
            finder,
            args.output,
            args.cluster,
            post_processing,
            pre_processing,
            args.checkpoint,
        )
        return

    _process_single_smiles(
        args.smiles,
        finder,
        args.output,
        args.cluster,
        post_processing,
        pre_processing,
    )


if __name__ == "__main__":
    main()
