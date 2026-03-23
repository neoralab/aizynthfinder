from aizynthfinder.schemas import PlanningRequest
from aizynthfinder.services import plan_reaction_routes


def test_planning_request_requires_config_source():
    try:
        PlanningRequest(smiles="CCO")
    except ValueError as err:
        assert "config_file" in str(err)
    else:
        raise AssertionError("PlanningRequest should require a config source")


def test_plan_reaction_routes_returns_full_payload(mocker):
    finder = mocker.Mock()
    finder.target_smiles = "CCO"
    finder.extract_statistics.return_value = {"is_solved": True, "iterations": 3}
    finder.stock_info.return_value = {"O": ["stock"]}
    finder.routes.dict_with_extra.return_value = [{"route_metadata": {"score": 0.9}}]
    finder.scorers.objects.return_value = ["state score"]

    finder_cls = mocker.patch("aizynthfinder.services.planning.AiZynthFinder", return_value=finder)

    result = plan_reaction_routes(
        PlanningRequest(
            smiles="CCO",
            config_file="config.yml",
            policy=["policy1"],
            filter=["filter1"],
            stocks=["stock1"],
            scorer="state score",
            depth=8,
        )
    )

    finder_cls.assert_called_once_with(configfile="config.yml", configdict=None)
    assert finder.config.search.max_transforms == 8
    finder.stock.select.assert_called_once_with(["stock1"])
    finder.expansion_policy.select.assert_called_once_with(["policy1"])
    finder.filter_policy.select.assert_called_once_with(["filter1"])
    finder.prepare_tree.assert_called_once_with()
    finder.tree_search.assert_called_once_with(show_progress=False)
    finder.build_routes.assert_called_once_with(scorer="state score")
    finder.routes.compute_scores.assert_called_once_with("state score")
    assert result.solved is True
    assert result.routes == [{"route_metadata": {"score": 0.9}}]
    assert result.stock_info == {"O": ["stock"]}
