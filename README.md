# AiZynthFinder

[![PyPI version](https://img.shields.io/pypi/v/aizynthfinder.svg)](https://pypi.org/project/aizynthfinder/)
[![Python versions](https://img.shields.io/pypi/pyversions/aizynthfinder.svg)](https://pypi.org/project/aizynthfinder/)
[![License](https://img.shields.io/github/license/MolecularAI/aizynthfinder.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-molecularai.github.io-blue)](https://molecularai.github.io/aizynthfinder/)

AiZynthFinder is a retrosynthesis planning toolkit for Linux-first scientific workflows. It combines neural-network-guided policy models with route-search algorithms such as Monte Carlo tree search to propose synthetic routes from a target molecule to purchasable precursors.

## Why AiZynthFinder

- Plan retrosynthetic routes from a target SMILES string.
- Use the Python API for direct search control and route inspection.
- Integrate validated request/response models through the service layer.
- Swap in custom stocks, scorers, policies, and search implementations.
- Keep the default installation CPU-friendly, with optional extras for heavier integrations.

## Installation

### Install from PyPI with `uv`

```bash
uv venv
source .venv/bin/activate
uv pip install aizynthfinder
```

Optional extras are available when you need additional integrations:

```bash
uv pip install "aizynthfinder[tf]"
uv pip install "aizynthfinder[mongo,bloom]"
uv pip install "aizynthfinder[all]"
```

### Install from source for development

```bash
uv sync --group dev
```

If you prefer an editable install:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install -e ".[dev]"
```

## Download public assets

AiZynthFinder ships as code only. Models, template libraries, stock data, and the starter configuration are downloaded separately:

```bash
download_public_data ./public-data
```

The command creates a `config.yml` file next to the downloaded assets, so you can use `./public-data/config.yml` directly in the examples below.

## Quickstart

### Python API

```python
from aizynthfinder.aizynthfinder import AiZynthFinder

finder = AiZynthFinder(configfile="./public-data/config.yml")
finder.config.search.max_transforms = 8
finder.target_smiles = "CC(=O)Oc1ccccc1C(=O)O"
finder.prepare_tree()
finder.tree_search(show_progress=True)
finder.build_routes()

print(finder.extract_statistics())
print(finder.routes.dict_with_extra(include_scores=True))
```

### Service-layer API

Use the planning service layer when another tool, workflow engine, or agent needs a single validated request/response boundary:

```python
from aizynthfinder.schemas import PlanningRequest
from aizynthfinder.services import plan_reaction_routes

result = plan_reaction_routes(
    PlanningRequest(
        smiles="CC(=O)Oc1ccccc1C(=O)O",
        config_file="./public-data/config.yml",
        depth=8,
        show_progress=False,
    )
)

print(result.solved)
print(result.statistics)
print(result.stock_info)
print(result.routes)
```

A reusable agent prompt is included at [`docs/prompts/full_retrosynthesis_tool_prompt.md`](docs/prompts/full_retrosynthesis_tool_prompt.md).

## Documentation map

- [Getting started and configuration guide](docs/index.rst)
- [Python interface](docs/python_interface.rst)
- [Configuration reference](docs/configuration.rst)
- [Stocks and policy setup](docs/stocks.rst)
- [Scoring and route analysis](docs/scoring.rst)
- [Examples](examples/README.md)

Hosted documentation is available at <https://molecularai.github.io/aizynthfinder/>.

## Development workflow

### Common checks

```bash
uv run pytest -v
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
  python - <<'PY'
from aizynthfinder.schemas import PlanningRequest
from aizynthfinder.services import plan_reaction_routes

result = plan_reaction_routes(
    PlanningRequest(smiles="CCO", config_file="/opt/data/config.yml", show_progress=False)
)
print(result.model_dump_json(indent=2))
PY
```

Use bind mounts for model and stock assets instead of baking large data files into the image unless you control that deployment pipeline.

## Project structure

- `aizynthfinder.config`: configuration entry points and compatibility exports.
- `aizynthfinder.schemas`: Pydantic models for validated external contracts.
- `aizynthfinder.domain`: dataclasses for internal immutable value objects.
- `aizynthfinder.services`: configuration loading and planning orchestration.
- `aizynthfinder.adapters`: external integration boundary modules.
- `aizynthfinder.search`, `aizynthfinder.chem`, and related packages: core chemistry and search logic.

Pydantic is used at input and output boundaries, while dataclasses remain the preferred choice for lightweight internal runtime objects.

## Contributing

1. Create an environment with `uv sync --group dev`.
2. Make focused changes with tests.
3. Run `uv run pytest -v` and any targeted checks.
4. Submit a pull request with a concise description of behavior, compatibility, and asset assumptions.
