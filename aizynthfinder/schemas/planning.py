"""Service-layer request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlanningRequest(BaseModel):
    """Validated request payload for planning orchestration services."""

    model_config = ConfigDict(extra="forbid")

    smiles: str = Field(min_length=1)
    config_file: str | None = None
    config: dict[str, object] | None = None
    scorer: str | list[str] | None = None


class PlanningResult(BaseModel):
    """Serialized response payload for planning orchestration services."""

    model_config = ConfigDict(extra="forbid")

    target_smiles: str
    search_time: float
    solved: bool
    statistics: dict[str, object] = Field(default_factory=dict)
    stock_info: dict[str, object] = Field(default_factory=dict)
