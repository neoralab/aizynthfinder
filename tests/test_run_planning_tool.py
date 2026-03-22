import json
from pathlib import Path

from aizynthfinder.schemas import PlanningResult
from aizynthfinder.tools.run_planning import _build_output, _classify_exception, main


def test_build_output_returns_full_json_payload(mocker):
    result = PlanningResult(
        target_smiles="CCO",
        search_time=1.25,
        solved=True,
        statistics={"is_solved": True, "iterations": 8},
        stock_info={"CCO": ["stock"]},
        routes=[{"route_metadata": {"score": 0.8}, "children": []}],
    )
    mocker.patch("aizynthfinder.tools.run_planning.plan_reaction_routes", return_value=result)

    payload = _build_output("CCO", "config.yml")

    assert payload.input_smiles == "CCO"
    assert payload.config_file == "config.yml"
    assert payload.summary.solved is True
    assert payload.summary.search_time == 1.25
    assert payload.summary.statistics == {"is_solved": True, "iterations": 8}
    assert payload.summary.stock_info == {"CCO": ["stock"]}
    assert payload.routes == [{"route_metadata": {"score": 0.8}, "children": []}]
    assert payload.result == result
    assert payload.error is None


def test_build_output_reports_classified_errors(mocker):
    mocker.patch(
        "aizynthfinder.tools.run_planning.plan_reaction_routes",
        side_effect=FileNotFoundError("Could not load stock model from config"),
    )

    payload = _build_output("CCO", "config.yml")

    assert payload.summary.solved is None
    assert payload.error is not None
    assert payload.error.type == "FileNotFoundError"
    assert payload.error.category == "missing_assets"


def test_classify_exception_invalid_smiles():
    error = ValueError("Failed to sanitize smiles with RDKit")

    assert _classify_exception(error) == "invalid_smiles"


def test_main_prints_json_and_writes_output(mocker, tmp_path, monkeypatch, capsys):
    output_path = tmp_path / "planning.json"
    payload = PlanningResult(
        target_smiles="CCO",
        search_time=0.5,
        solved=False,
        statistics={"is_solved": False},
        stock_info={},
        routes=[],
    )
    mocker.patch("aizynthfinder.tools.run_planning.plan_reaction_routes", return_value=payload)
    monkeypatch.setattr(
        "sys.argv",
        [
            "aizynthplan",
            "--smiles",
            "CCO",
            "--config",
            "config.yml",
            "--output",
            str(output_path),
        ],
    )

    main()

    printed = json.loads(capsys.readouterr().out)
    saved = json.loads(Path(output_path).read_text())
    assert printed == saved
    assert printed["input_smiles"] == "CCO"
    assert printed["summary"]["search_time"] == 0.5
