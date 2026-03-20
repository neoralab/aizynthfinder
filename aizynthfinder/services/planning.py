"""Planning orchestration services that wrap the synchronous search core."""

from __future__ import annotations

import asyncio

from aizynthfinder.aizynthfinder import AiZynthFinder
from aizynthfinder.domain import PlannerRunArtifacts
from aizynthfinder.schemas import PlanningRequest, PlanningResult


def plan_reaction_routes(request: PlanningRequest) -> PlanningResult:
    """Execute a single planning request via the existing synchronous core.

    Args:
        request: A validated planning request.

    Returns:
        A serialized planning result.
    """
    finder = AiZynthFinder(configfile=request.config_file, configdict=request.config)
    finder.target_smiles = request.smiles
    finder.prepare_tree()
    search_time = finder.tree_search()
    finder.build_routes(scorer=request.scorer)

    artifacts = PlannerRunArtifacts(
        target_smiles=finder.target_smiles,
        statistics=finder.extract_statistics(),
        stock_info=finder.stock_info(),
    )
    return PlanningResult(
        target_smiles=artifacts.target_smiles,
        search_time=search_time,
        solved=bool(artifacts.statistics.get("is_solved", False)),
        statistics=artifacts.statistics,
        stock_info=artifacts.stock_info,
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
