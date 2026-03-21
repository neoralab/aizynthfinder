# Examples

## `run_from_smiles.py`

Minimal Python example that runs AiZynthFinder from a SMILES string defined directly in the script.

### What to edit

Open `examples/run_from_smiles.py` and change the constants at the top of the file:

- `TARGET_SMILES`
- `CONFIG_FILE`
- `STOCK_NAME`
- `EXPANSION_POLICY_NAME`
- `FILTER_POLICY_NAME`

No command-line arguments are needed.

### Prepare public demo assets

From the repository root:

```bash
mkdir -p ./public-data
python -m aizynthfinder.tools.download_public_data ./public-data
```

If you installed the project entry points, this works too:

```bash
mkdir -p ./public-data
download_public_data ./public-data
```

That command downloads the public models/stock files and writes `./public-data/config.yml`.

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

- basic search statistics
- number of routes found
- the first extracted route as formatted JSON
- stock availability for the route leaves

