from __future__ import annotations

import argparse
from pathlib import Path

from aizynthfinder.schemas import PlanningCliOutput, PlanningErrorReport, PlanningRequest, PlanningSummary
from aizynthfinder.services import plan_reaction_routes


def _classify_exception(exc: Exception) -> str:
    message = str(exc).lower()
    if any(token in message for token in ["smiles", "sanitize", "sanitiz", "rdkit", "molecule"]):
        return "invalid_smiles"
    if any(
        token in message
        for token in ["model", "stock", "template", "policy", "onnx", "checkpoint", "file not found", "no such file", "could not load"]
    ):
        return "missing_assets"
    if any(token in message for token in ["config", "yaml", "jsonschema", "configuration"]):
        return "configuration"
    return "unknown"


def _build_output(smiles: str, config_file: str) -> PlanningCliOutput:
    try:
        result = plan_reaction_routes(
            PlanningRequest(smiles=smiles, config_file=config_file, show_progress=False)
        )
    except Exception as exc:  # pragma: no cover - classification path exercised via tests with mocks
        return PlanningCliOutput(
            input_smiles=smiles,
            config_file=config_file,
            summary=PlanningSummary(),
            error=PlanningErrorReport(
                type=exc.__class__.__name__,
                message=str(exc),
                category=_classify_exception(exc),
            ),
        )

    return PlanningCliOutput(
        input_smiles=smiles,
        config_file=config_file,
        summary=PlanningSummary(
            solved=result.solved,
            search_time=result.search_time,
            statistics=result.statistics,
            stock_info=result.stock_info,
        ),
        routes=result.routes,
        result=result,
    )


def _get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser("aizynthplan")
    parser.add_argument("--smiles", required=True, help="the target molecule SMILES")
    parser.add_argument("--config", required=True, help="the runtime configuration file")
    parser.add_argument("--output", help="optional path to save the JSON payload")
    return parser.parse_args()


def main() -> None:
    args = _get_arguments()
    payload = _build_output(args.smiles, args.config)
    json_payload = payload.model_dump_json(indent=2)
    if args.output:
        Path(args.output).write_text(json_payload + "\n", encoding="utf-8")
    print(json_payload)


if __name__ == "__main__":
    main()
