# Examples

These examples are intentionally small and are meant to be edited in place.
Change the settings near the top of each script, then run the script from the repository root.

## Shared setup

Both examples expect the public demo assets to be available at `./public-data/config.yml`.
From the repository root, download them with:

```bash
mkdir -p ./public-data
python -m aizynthfinder.tools.download_public_data ./public-data
```

If you installed the project entry points, this works too:

```bash
mkdir -p ./public-data
download_public_data ./public-data
```

## `run_from_smiles.py`

Minimal Python example that uses `AiZynthFinder` directly to plan routes for a SMILES string.

### What to edit

Open `examples/run_from_smiles.py` and update the `SETTINGS` values near the top of the file:

- `target_smiles`
- `config_file`
- `stock_name`
- `expansion_policy_name`
- `filter_policy_name`
- optional output flags such as `show_progress`

No command-line arguments are required.

### Run the example

From the repository root:

```bash
python examples/run_from_smiles.py
```

Or, with `uv`:

```bash
uv run python examples/run_from_smiles.py
```

### What the script prints

- a short search summary
- formatted search statistics
- the first extracted route as formatted JSON
- stock availability for the route leaves

## `run_planning_mode.py`

Minimal Python example that uses the service-layer planning API with a validated `PlanningRequest`.

### What to edit

Open `examples/run_planning_mode.py` and update the `SETTINGS` values near the top of the file:

- `target_smiles`
- `config_file`
- `policy_name`
- `filter_policy_names`
- `stock_names`
- optional output flags such as `show_progress`

No command-line arguments are required.

### Run the example

From the repository root:

```bash
python examples/run_planning_mode.py
```

Or, with `uv`:

```bash
uv run python examples/run_planning_mode.py
```

### What the script prints

- the validated planning request payload
- a compact planning result summary
- the first serialized route (truncated by default)
