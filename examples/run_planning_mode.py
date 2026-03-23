from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aizynthfinder.schemas import PlanningRequest  # noqa: E402
from aizynthfinder.services import plan_reaction_routes  # noqa: E402


# Edit these values directly in the script. No CLI arguments are required.
TARGET_SMILES = "CC(=O)Oc1ccccc1C(=O)O"
CONFIG_FILE = REPO_ROOT / "public-data" / "config.yml"
POLICY = "uspto"
FILTER_POLICIES = ["uspto"]
STOCKS = ["zinc"]
SHOW_PROGRESS = False
PRINT_FULL_FIRST_ROUTE = False


def _build_missing_config_message() -> str:
    config_dir = CONFIG_FILE.parent
    return (
        f"Configuration file not found: {CONFIG_FILE}\n\n"
        "Download the public demo assets first, for example from the repository root:\n"
        f"  mkdir -p {config_dir} && python -m aizynthfinder.tools.download_public_data {config_dir}\n"
        "or, if you installed the project entry points:\n"
        f"  mkdir -p {config_dir} && download_public_data {config_dir}\n\n"
        "Then rerun this script."
    )


def main() -> int:
    if not CONFIG_FILE.exists():
        print(_build_missing_config_message(), file=sys.stderr)
        return 1

    request = PlanningRequest(
        smiles=TARGET_SMILES,
        config_file=str(CONFIG_FILE),
        policy=POLICY,
        filter=FILTER_POLICIES,
        stocks=STOCKS,
        show_progress=SHOW_PROGRESS,
    )
    result = plan_reaction_routes(request)

    print("Planning request:")
    print(json.dumps(request.model_dump(mode="json"), indent=2, sort_keys=True))
    print()
    print("Planning result summary:")
    print(
        json.dumps(
            {
                "target_smiles": result.target_smiles,
                "search_time": result.search_time,
                "solved": result.solved,
                "routes_found": len(result.routes),
                "statistics": result.statistics,
                "stock_info": result.stock_info,
            },
            indent=2,
            sort_keys=True,
        )
    )

    if result.routes:
        print()
        print("First route:")
        first_route = result.routes[0] if PRINT_FULL_FIRST_ROUTE else {
            "children": result.routes[0].get("children", []),
            "route_metadata": result.routes[0].get("route_metadata", {}),
            "scores": result.routes[0].get("scores", {}),
            "smiles": result.routes[0].get("smiles"),
        }
        print(json.dumps(first_route, indent=2, sort_keys=True))
    else:
        print()
        print("No complete route was built for the configured target and planning request.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
