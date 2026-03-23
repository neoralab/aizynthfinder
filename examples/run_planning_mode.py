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

from aizynthfinder.schemas import PlanningRequest, PlanningResult
from aizynthfinder.services import plan_reaction_routes

# Edit these values directly in the script. No CLI arguments are required.
TARGET_SMILES = "CC(=O)Oc1ccccc1C(=O)O"
CONFIG_FILE = DEFAULT_CONFIG_FILE
POLICY = "uspto"
FILTER_POLICIES = ["uspto"]
STOCKS = ["zinc"]
SHOW_PROGRESS = False
PRINT_FULL_FIRST_ROUTE = False

@dataclass(frozen=True)
class ExampleSettings:
    """Editable settings for this example planning script."""

    target_smiles: str
    config_file: Path
    policy_name: str
    filter_policy_names: list[str]
    stock_names: list[str]
    show_progress: bool
    print_full_first_route: bool

SETTINGS = ExampleSettings(
    target_smiles=TARGET_SMILES,
    config_file=CONFIG_FILE,
    policy_name=POLICY,
    filter_policy_names=FILTER_POLICIES,
    stock_names=STOCKS,
    show_progress=SHOW_PROGRESS,
    print_full_first_route=PRINT_FULL_FIRST_ROUTE,
)


def build_request(settings: ExampleSettings) -> PlanningRequest:
    """Create the validated planning request used by the service-layer API."""
    return PlanningRequest(
        smiles=settings.target_smiles,
        config_file=str(settings.config_file),
        policy=settings.policy_name,
        filter=settings.filter_policy_names,
        stocks=settings.stock_names,
        show_progress=settings.show_progress,
    )


def build_result_summary(result: PlanningResult) -> dict[str, Any]:
    """Create a compact summary of the planning result."""
    return {
        "target_smiles": result.target_smiles,
        "search_time": result.search_time,
        "solved": result.solved,
        "routes_found": len(result.routes),
        "statistics": result.statistics,
        "stock_info": result.stock_info,
    }


def print_result_output(
    settings: ExampleSettings,
    request: PlanningRequest,
    result: PlanningResult,
) -> None:
    """Print the planning request, summary, and first route."""
    print_section("Planning request:", request.model_dump(mode="json"))
    print()
    print_section("Planning result summary:", build_result_summary(result))

    first_route = format_first_route(
        result.routes,
        include_full_route=settings.print_full_first_route,
        route_metadata_key="route_metadata",
    )
    if first_route is None:
        print()
        print("No complete route was built for the configured target and planning request.")
        return

    print()
    print_section("First route:", first_route)


def main() -> int:
    if not validate_config_file(SETTINGS.config_file):
        return 1

    request = build_request(SETTINGS)
    result = plan_reaction_routes(request)
    print_result_output(SETTINGS, request, result)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
