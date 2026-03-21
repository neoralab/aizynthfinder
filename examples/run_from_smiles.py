from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aizynthfinder.aizynthfinder import AiZynthFinder


# Edit these values directly in the script. No CLI arguments are required.
TARGET_SMILES = "CC(=O)Oc1ccccc1C(=O)O"
CONFIG_FILE = REPO_ROOT / "public-data" / "config.yml"
STOCK_NAME = "zinc"
EXPANSION_POLICY_NAME = "uspto"
FILTER_POLICY_NAME: str | None = "uspto"
SHOW_PROGRESS = True
PRINT_FULL_FIRST_ROUTE = True


def _select_or_raise(collection: Any, selection_name: str, collection_label: str) -> None:
    available = collection.items
    if selection_name not in available:
        available_text = ", ".join(available) if available else "<none loaded>"
        raise ValueError(
            f"Configured {collection_label} '{selection_name}' was not found. "
            f"Available values: {available_text}"
        )
    collection.select(selection_name)


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

    finder = AiZynthFinder(configfile=str(CONFIG_FILE))

    _select_or_raise(finder.stock, STOCK_NAME, "stock")
    _select_or_raise(
        finder.expansion_policy,
        EXPANSION_POLICY_NAME,
        "expansion policy",
    )

    if FILTER_POLICY_NAME:
        _select_or_raise(finder.filter_policy, FILTER_POLICY_NAME, "filter policy")
    elif finder.filter_policy.items:
        finder.filter_policy.select_all()

    finder.target_smiles = TARGET_SMILES
    finder.prepare_tree()
    search_time = finder.tree_search(show_progress=SHOW_PROGRESS)
    finder.build_routes()

    statistics = finder.extract_statistics()
    routes = finder.routes.dict_with_extra(include_scores=True, include_metadata=True)

    print(f"Target SMILES: {TARGET_SMILES}")
    print(f"Configuration: {CONFIG_FILE}")
    print(f"Search time: {search_time:.2f} s")
    print(f"Solved: {statistics.get('is_solved', False)}")
    print(f"Routes found: {len(routes)}")
    print()
    print("Search statistics:")
    print(json.dumps(statistics, indent=2, sort_keys=True))

    if routes:
        print()
        print("First route:")
        first_route = routes[0] if PRINT_FULL_FIRST_ROUTE else {
            "children": routes[0].get("children", []),
            "scores": routes[0].get("scores", {}),
            "smiles": routes[0].get("smiles"),
        }
        print(json.dumps(first_route, indent=2, sort_keys=True))

        stock_info = finder.stock_info()
        if stock_info:
            print()
            print("Stock availability for route leaves:")
            print(json.dumps(stock_info, indent=2, sort_keys=True))
    else:
        print()
        print("No complete route was built for the configured target and search settings.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


