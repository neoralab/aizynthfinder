import asyncio

import pytest

from aizynthfinder.aizynthfinder import AiZynthFinder
from aizynthfinder.domain import SmilesBatch
from aizynthfinder.schemas import PlanningRequest
from aizynthfinder.services.configuration import (
    load_configuration_dict,
    load_configuration_dict_async,
    validate_runtime_config,
)
from aizynthfinder.utils.files import load_smiles_batch, load_smiles_batch_async


def test_validate_runtime_config_unknown_search_key_raises_attribute_error():
    with pytest.raises(AttributeError, match="Could not find attribute to set: dummy"):
        validate_runtime_config({"search": {"dummy": 1}})


def test_configuration_loader_validates_and_expands_env(write_yaml, monkeypatch):
    monkeypatch.setenv("AIZYNTH_TEST_LIMIT", "321")
    filename = write_yaml({"search": {"time_limit": "${AIZYNTH_TEST_LIMIT}"}})

    config = load_configuration_dict(filename)

    assert config["search"]["time_limit"] == 321


def test_async_configuration_loader(write_yaml):
    filename = write_yaml({"search": {"iteration_limit": 11}})

    config = asyncio.run(load_configuration_dict_async(filename))

    assert config["search"]["iteration_limit"] == 11


def test_load_smiles_batch(tmp_path):
    filename = tmp_path / "smiles.txt"
    filename.write_text("CCO\nCCC\n", encoding="utf-8")

    batch = load_smiles_batch(str(filename))

    assert batch == SmilesBatch(source=filename, smiles=("CCO", "CCC"))


def test_load_smiles_batch_async(tmp_path):
    filename = tmp_path / "smiles.txt"
    filename.write_text("CCO\nCCC\n", encoding="utf-8")

    batch = asyncio.run(load_smiles_batch_async(str(filename)))

    assert batch.smiles == ("CCO", "CCC")


def test_tree_search_async_wraps_sync_method(mocker):
    finder = AiZynthFinder()
    mocked = mocker.patch.object(finder, "tree_search", return_value=1.23)

    result = asyncio.run(finder.tree_search_async())

    mocked.assert_called_once_with(False)
    assert result == 1.23


def test_planning_request_schema_accepts_boundary_payload():
    request = PlanningRequest(smiles="CCO", config={"search": {"time_limit": 10}})

    assert request.smiles == "CCO"
    assert request.config == {"search": {"time_limit": 10}}
