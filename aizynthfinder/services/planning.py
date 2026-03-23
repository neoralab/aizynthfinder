"""Planning orchestration services that wrap the synchronous search core."""

from __future__ import annotations

import asyncio

from aizynthfinder.aizynthfinder import AiZynthFinder
from aizynthfinder.domain import PlannerRunArtifacts
from aizynthfinder.schemas.planning import PlanningRequest, PlanningResult


def _configure_finder_from_request(request: PlanningRequest) -> AiZynthFinder:
    """Create and configure a finder from a validated planning request."""
    finder = AiZynthFinder(configfile=request.config_file, configdict=request.config)
    if request.depth is not None:
        finder.config.search.max_transforms = request.depth
    if request.stocks:
        finder.stock.select(request.stocks)
    if request.policy:
        finder.expansion_policy.select(request.policy)
    else:
        if not finder.expansion_policy.items:
            raise ValueError(
                "No expansion policies are loaded; provide a config with at least one policy"
            )
        finder.expansion_policy.select_first()
    if request.filter:
        finder.filter_policy.select(request.filter)
    else:
        finder.filter_policy.select_all()
    return finder


def plan_reaction_routes(request: PlanningRequest) -> PlanningResult:
    """Execute a single planning request via the existing synchronous core.

    Args:
        request: A validated planning request.

    Returns:
        A serialized planning result including full route payloads.
    """
    finder = _configure_finder_from_request(request)
    finder.target_smiles = request.smiles
    finder.prepare_tree()
    search_time = finder.tree_search(show_progress=request.show_progress)
    finder.build_routes(scorer=request.scorer)
    finder.routes.compute_scores(*finder.scorers.objects())

    artifacts = PlannerRunArtifacts(
        target_smiles=finder.target_smiles,
        statistics=finder.extract_statistics(),
        stock_info=finder.stock_info(),
        routes=finder.routes.dict_with_extra(include_metadata=True, include_scores=True),
    )
    return PlanningResult(
        target_smiles=artifacts.target_smiles,
        search_time=search_time,
        solved=bool(artifacts.statistics.get("is_solved", False)),
        statistics=artifacts.statistics,
        stock_info=artifacts.stock_info,
        routes=artifacts.routes,
    )


async def plan_reaction_routes_async(request: PlanningRequest) -> PlanningResult:
    """Asynchronously orchestrate a planning request.

    Args:
        request: A validated planning request.

    Returns:
        A serialized planning result.

    Notes:
        The actual route search remains synchronous and CPU-bound. This wrapper
        is only intended to compose planning with other I/O-bound application
        tasks, not to make the search algorithm itself faster.
    """
    return await asyncio.to_thread(plan_reaction_routes, request)
