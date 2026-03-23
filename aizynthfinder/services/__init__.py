"""Service-layer helpers for configuration and planning orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aizynthfinder.services.configuration import (
    load_configuration_dict,
    load_configuration_dict_async,
    validate_runtime_config,
)

if TYPE_CHECKING:
    from aizynthfinder.schemas.planning import PlanningRequest, PlanningResult

__all__ = [
    "load_configuration_dict",
    "load_configuration_dict_async",
    "validate_runtime_config",
    "plan_reaction_routes",
    "plan_reaction_routes_async",
]


def plan_reaction_routes(request: "PlanningRequest") -> "PlanningResult":
    """Lazily import planning services to avoid package initialization cycles."""
    from aizynthfinder.services.planning import plan_reaction_routes as _plan_reaction_routes

    return _plan_reaction_routes(request)


async def plan_reaction_routes_async(request: "PlanningRequest") -> "PlanningResult":
    """Lazily import async planning services to avoid package initialization cycles."""
    from aizynthfinder.services.planning import (
        plan_reaction_routes_async as _plan_reaction_routes_async,
    )

    return await _plan_reaction_routes_async(request)
