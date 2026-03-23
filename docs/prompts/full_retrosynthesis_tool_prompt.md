# Prompt: full retrosynthesis from a SMILES string

Use this prompt when you want an agent or tool runner to call the installed `aizynthfinder` package and return the full retrosynthesis result for a target molecule.

## Prompt template

```md
You are working inside a Python environment where `aizynthfinder` is installed as a package.

Task:
1. Accept a target SMILES string: `{SMILES}`.
2. Use the AiZynthFinder planning service API instead of re-implementing the workflow.
3. Load the runtime configuration from `{CONFIG_FILE}`.
4. Run retrosynthesis and return the complete serialized route payload.
5. Summarize whether the search was solved, the main statistics, stock availability, and the full route JSON.

Python snippet to run:

```python
from aizynthfinder.schemas import PlanningRequest
from aizynthfinder.services import plan_reaction_routes

result = plan_reaction_routes(
    PlanningRequest(
        smiles="{SMILES}",
        config_file="{CONFIG_FILE}",
        show_progress=False,
    )
)

print(result.model_dump_json(indent=2))
```

Output requirements:
- Echo the exact input SMILES.
- Report `solved`, `search_time`, and key values from `statistics`.
- Include `stock_info`.
- Include the full `routes` payload without truncating keys.
- If planning fails, return the Python exception and explain whether the failure is due to configuration, invalid SMILES, or missing model/stock assets.
```

## Notes

- The package only ships the code; model, stock, and template assets still need to be available through the selected config file.
- `plan_reaction_routes()` returns a validated `PlanningResult` object with the full serialized retrosynthesis routes in `routes`.
- Prefer the Python service-layer API directly for tool integration so validation and serialization stay in one place.
