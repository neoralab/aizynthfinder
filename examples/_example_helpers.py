from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_FILE = REPO_ROOT / "public-data" / "config.yml"


JSONDict = dict[str, Any]


def ensure_repo_root_on_path() -> None:
    """Allow the examples to import the local package when run from the repo root."""
    repo_root = str(REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


ensure_repo_root_on_path()


def build_missing_config_message(config_file: Path) -> str:
    """Return a helpful message that explains how to download the demo assets."""
    config_dir = config_file.parent
    return (
        f"Configuration file not found: {config_file}\n\n"
        "Download the public demo assets first, for example from the repository root:\n"
        f"  mkdir -p {config_dir} && python -m aizynthfinder.tools.download_public_data {config_dir}\n"
        "or, if you installed the project entry points:\n"
        f"  mkdir -p {config_dir} && download_public_data {config_dir}\n\n"
        "Then rerun this script."
    )


def validate_config_file(config_file: Path) -> bool:
    """Check that the example configuration file exists."""
    if config_file.exists():
        return True

    print(build_missing_config_message(config_file), file=sys.stderr)
    return False


def print_section(title: str, payload: Any) -> None:
    """Print a section title followed by formatted JSON content."""
    print(title)
    print(json.dumps(payload, indent=2, sort_keys=True))


def summarize_route(route: Mapping[str, Any], *, route_metadata_key: str | None = None) -> JSONDict:
    """Return a beginner-friendly subset of the route payload."""
    summary: JSONDict = {
        "smiles": route.get("smiles"),
        "scores": route.get("scores", {}),
        "children": route.get("children", []),
    }
    if route_metadata_key:
        summary[route_metadata_key] = route.get(route_metadata_key, {})
    return summary


def format_first_route(
    routes: Sequence[Mapping[str, Any]],
    *,
    include_full_route: bool,
    route_metadata_key: str | None = None,
) -> JSONDict | None:
    """Return either the full first route or a small, readable summary."""
    if not routes:
        return None

    first_route = routes[0]
    return dict(first_route) if include_full_route else summarize_route(
        first_route,
        route_metadata_key=route_metadata_key,
    )
