"""Service-layer request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanningRequest(BaseModel):
    """Validated request payload for planning orchestration services."""

    model_config = ConfigDict(extra="forbid")

    smiles: str = Field(min_length=1)
    config_file: str | None = None
    config: dict[str, object] | None = None
    policy: str | list[str] | None = None
    filter: list[str] = Field(default_factory=list)
    stocks: list[str] = Field(default_factory=list)
    scorer: str | list[str] | None = None
    show_progress: bool = False

    @model_validator(mode="after")
    def validate_configuration_source(self) -> "PlanningRequest":
        if not self.config_file and not self.config:
            raise ValueError("either 'config_file' or 'config' must be provided")
        return self


class PlanningResult(BaseModel):
    """Serialized response payload for planning orchestration services."""

    model_config = ConfigDict(extra="forbid")

    target_smiles: str
    search_time: float
    solved: bool
    statistics: dict[str, object] = Field(default_factory=dict)
    stock_info: dict[str, object] = Field(default_factory=dict)
    routes: list[dict[str, Any]] = Field(default_factory=list)
