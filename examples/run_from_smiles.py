from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _example_helpers import (
    DEFAULT_CONFIG_FILE,
    format_first_route,
    print_section,
    validate_config_file,
)

from aizynthfinder.aizynthfinder import AiZynthFinder

# Edit these values directly in the script. No CLI arguments are required.
TARGET_SMILES = "CC(=O)Oc1ccccc1C(=O)O"
CONFIG_FILE = DEFAULT_CONFIG_FILE
STOCK_NAME = "zinc"
EXPANSION_POLICY_NAME = "uspto"
FILTER_POLICY_NAME: str | None = "uspto"
SHOW_PROGRESS = True
MAX_TRANSFORMS = 8
PRINT_FULL_FIRST_ROUTE = True

@dataclass(frozen=True)
class ExampleSettings:
    """Editable settings for this example script."""

    target_smiles: str
    config_file: Path
    stock_name: str
    expansion_policy_name: str
    filter_policy_name: str | None
    show_progress: bool
    max_transforms: int
    print_full_first_route: bool

SETTINGS = ExampleSettings(
    target_smiles=TARGET_SMILES,
    config_file=CONFIG_FILE,
    stock_name=STOCK_NAME,
    expansion_policy_name=EXPANSION_POLICY_NAME,
    filter_policy_name=FILTER_POLICY_NAME,
    show_progress=SHOW_PROGRESS,
    max_transforms=MAX_TRANSFORMS,
    print_full_first_route=PRINT_FULL_FIRST_ROUTE,
)

def select_item(collection: Any, selection_name: str, collection_label: str) -> None:
    """Select a configured stock or policy and fail with a clear message if missing."""
    available_items = list(collection.items)
    if selection_name not in available_items:
        available_text = ", ".join(available_items) if available_items else "<none loaded>"
        raise ValueError(
            f"Configured {collection_label} '{selection_name}' was not found. "
            f"Available values: {available_text}"
        )
    collection.select(selection_name)


def configure_finder(settings: ExampleSettings) -> AiZynthFinder:
    """Create a finder configured with the example stock and policy selections."""
    finder = AiZynthFinder(configfile=str(settings.config_file))
    finder.config.search.max_transforms = settings.max_transforms
    select_item(finder.stock, settings.stock_name, "stock")
    select_item(
        finder.expansion_policy,
        settings.expansion_policy_name,
        "expansion policy",
    )

    if settings.filter_policy_name:
        select_item(finder.filter_policy, settings.filter_policy_name, "filter policy")
    elif finder.filter_policy.items:
        finder.filter_policy.select_all()

    return finder


def run_search(settings: ExampleSettings) -> tuple[AiZynthFinder, float, dict[str, object], list[dict[str, Any]]]:
    """Run a retrosynthesis search and return the objects used for presentation."""
    finder = configure_finder(settings)
    finder.target_smiles = settings.target_smiles
    finder.prepare_tree()
    search_time = finder.tree_search(show_progress=settings.show_progress)
    finder.build_routes()

    statistics = finder.extract_statistics()
    routes = finder.routes.dict_with_extra(include_scores=True, include_metadata=True)
    return finder, search_time, statistics, routes


def print_search_summary(
    settings: ExampleSettings,
    search_time: float,
    statistics: dict[str, object],
    route_count: int,
) -> None:
    """Print the high-level search summary."""
    print(f"Target SMILES: {settings.target_smiles}")
    print(f"Configuration: {settings.config_file}")
    print(f"Max depth: {settings.max_transforms}")
    print(f"Search time: {search_time:.2f} s")
    print(f"Solved: {statistics.get('is_solved', False)}")
    print(f"Routes found: {route_count}")


def print_search_output(
    settings: ExampleSettings,
    finder: AiZynthFinder,
    statistics: dict[str, object],
    routes: list[dict[str, Any]],
) -> None:
    """Print the search statistics, first route, and stock information."""
    print()
    print_section("Search statistics:", statistics)

    first_route = format_first_route(
        routes,
        include_full_route=settings.print_full_first_route,
    )
    if first_route is None:
        print()
        print("No complete route was built for the configured target and search settings.")
        return

    print()
    print_section("First route:", first_route)

    stock_info = finder.stock_info()
    if stock_info:
        print()
        print_section("Stock availability for route leaves:", stock_info)


def main() -> int:
    if not validate_config_file(SETTINGS.config_file):
        return 1

    finder, search_time, statistics, routes = run_search(SETTINGS)
    print_search_summary(SETTINGS, search_time, statistics, len(routes))
    print_search_output(SETTINGS, finder, statistics, routes)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
