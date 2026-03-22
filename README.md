# AiZynthFinder

[![License](https://img.shields.io/github/license/MolecularAI/aizynthfinder)](https://github.com/MolecularAI/aizynthfinder/blob/master/LICENSE)
[![Tests](https://github.com/MolecularAI/aizynthfinder/workflows/tests/badge.svg)](https://github.com/MolecularAI/aizynthfinder/actions?workflow=tests)
[![codecov](https://codecov.io/gh/MolecularAI/aizynthfinder/branch/master/graph/badge.svg)](https://codecov.io/gh/MolecularAI/aizynthfinder)

AiZynthFinder is a CPU-friendly retrosynthesis planning toolkit for Linux-first scientific workflows. It combines neural-network-guided policy models with route-search algorithms such as Monte Carlo tree search to propose synthetic routes from a target molecule to purchasable precursors.

## What it provides

- Route planning from SMILES with configurable search strategies.
- CLI and Python APIs for batch jobs, notebooks, and service integration.
- Pluggable stocks, scorers, policies, and search implementations.
- Production-friendly packaging with a `uv` workflow and optional extras.
- Docker/Linux suitability without requiring GPU dependencies.

## Quickstart

### Install with `uv`

```bash
uv venv
source .venv/bin/activate
uv pip install aizynthfinder
```

Optional extras stay behind extras so the default install remains lean:

```bash
uv pip install "aizynthfinder[notebooks]"
uv pip install "aizynthfinder[tf]"
uv pip install "aizynthfinder[mongo,bloom]"
uv pip install "aizynthfinder[all]"
```

### Download public assets

AiZynthFinder needs model and stock assets separately from the base package. You can download the public example assets and a starter config with:

```bash
download_public_data ./public-data
```

That command creates a usable `config.yml` alongside the downloaded assets.

### Run the CLI

Single target:

```bash
aizynthcli --config ./public-data/config.yml --smiles "CC(=O)Oc1ccccc1C(=O)O" --output trees.json
```

Batch file:

```bash
aizynthcli --config ./public-data/config.yml --smiles molecules.txt --output output.json.gz
```

Notebook/web UI:

```bash
aizynthapp --config ./public-data/config.yml
```

## Python API

```python
from aizynthfinder.aizynthfinder import AiZynthFinder

finder = AiZynthFinder(configfile="./public-data/config.yml")
finder.target_smiles = "CC(=O)Oc1ccccc1C(=O)O"
finder.prepare_tree()
finder.tree_search(show_progress=True)
finder.build_routes()

print(finder.extract_statistics())
print(finder.routes.dict_with_extra(include_scores=True))
```

### Service-layer API for tool integration

If you want another tool or agent to submit a SMILES string and receive the full retrosynthesis payload in one call, use the planning service layer:

```python
from aizynthfinder.schemas import PlanningRequest
from aizynthfinder.services import plan_reaction_routes

result = plan_reaction_routes(
    PlanningRequest(
        smiles="CC(=O)Oc1ccccc1C(=O)O",
        config_file="./public-data/config.yml",
        show_progress=False,
    )
)

print(result.solved)
print(result.statistics)
print(result.stock_info)
print(result.routes)  # full serialized retrosynthesis trees
```

A reusable agent prompt is included at [`docs/prompts/full_retrosynthesis_tool_prompt.md`](docs/prompts/full_retrosynthesis_tool_prompt.md).

## Development workflow

### Sync a development environment

```bash
uv sync --group dev
```

### Editable install

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install -e ".[dev]"
```

### Tests and checks

```bash
uv run pytest -v
uv run pytest tests/test_cli.py -v
uv run ruff check .
```

### Build artifacts

```bash
uv build
```

## Docker basics

A simple container workflow is:

```bash
docker build -t aizynthfinder .
docker run --rm -it -v "$PWD/public-data:/opt/data" aizynthfinder \
  aizynthcli --config /opt/data/config.yml --smiles "CCO"
```

Use bind mounts for model/stock assets rather than baking large data files into the image unless you control that deployment pipeline.

## Architecture at a glance

The package is organized around a small set of responsibilities:

- `aizynthfinder.cli`: CLI-oriented orchestration helpers.
- `aizynthfinder.config`: configuration entry points and compatibility exports.
- `aizynthfinder.schemas`: Pydantic models for validated external contracts.
- `aizynthfinder.domain`: dataclasses for internal immutable value objects.
- `aizynthfinder.services`: configuration loading and planning orchestration.
- `aizynthfinder.adapters`: external integration boundary modules.
- `aizynthfinder.search`, `aizynthfinder.chem`, and related packages: core chemistry and search logic.

Pydantic is used at boundaries such as config validation and service payloads. Dataclasses remain the preferred choice for internal runtime/domain objects where coercion is unnecessary and lightweight state matters more than validation.

## Production and deployment notes

- Default installation is CPU-only.
- Linux is the primary deployment target, especially for Docker and batch execution.
- Large models, template libraries, and stock data should be managed as external assets.
- Async wrappers are available for I/O-oriented orchestration, but the core planning algorithm remains synchronous and CPU-bound by design.

## Contributing

1. Create an environment with `uv sync --group dev`.
2. Make focused changes with tests.
3. Run `uv run pytest -v` and any targeted checks.
4. Submit a pull request with a concise description of behavior, compatibility, and asset assumptions.

For more detailed usage and background, see the hosted documentation: https://molecularai.github.io/aizynthfinder/.
