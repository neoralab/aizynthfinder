"""Validated configuration schemas for external-facing settings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SearchSettingsSchema(BaseModel):
    """Validate search settings loaded from files or other user inputs.

    Notes:
        This schema is intended for configuration boundaries. The core search
        implementation still uses dataclasses and plain Python objects once the
        validated data has crossed the boundary.
    """

    model_config = ConfigDict(extra="forbid")

    algorithm: str = "mcts"
    algorithm_config: dict[str, object] = Field(
        default_factory=lambda: {
            "C": 1.4,
            "default_prior": 0.5,
            "use_prior": True,
            "prune_cycles_in_search": True,
            "search_rewards": ["state score"],
            "immediate_instantiation": (),
            "mcts_grouping": None,
            "search_rewards_weights": [],
        }
    )
    max_transforms: int | None = 6
    iteration_limit: int = 100
    time_limit: int = 120
    return_first: bool = False
    exclude_target_from_stock: bool = True
    break_bonds: list[list[int]] = Field(default_factory=list)
    freeze_bonds: list[list[int]] = Field(default_factory=list)
    break_bonds_operator: str = "and"

    @field_validator("break_bonds", "freeze_bonds")
    @classmethod
    def validate_bonds(cls, value: list[list[int]]) -> list[list[int]]:
        """Ensure bond constraints are pairs of atom-map indices."""
        if not all(len(bond_pair) == 2 for bond_pair in value):
            raise ValueError("Lists of bond pairs to break/freeze should be of length 2")
        return [bond_pair[:2] for bond_pair in value]

    @field_validator("algorithm_config")
    @classmethod
    def validate_algorithm_config(cls, value: dict[str, object]) -> dict[str, object]:
        """Ensure algorithm configuration is represented as a dictionary."""
        if not isinstance(value, dict):
            raise ValueError("algorithm_config settings need to be dictionary")
        return value


class PostProcessingSchema(BaseModel):
    """Validate route post-processing settings."""

    model_config = ConfigDict(extra="forbid")

    min_routes: int = 5
    max_routes: int = 25
    all_routes: bool = False
    route_distance_model: str | None = None
    route_scorers: list[str] = Field(default_factory=list)
    scorer_weights: list[float] | None = None

    @model_validator(mode="after")
    def validate_route_limits(self) -> "PostProcessingSchema":
        """Ensure route bounds remain internally consistent."""
        if self.max_routes < self.min_routes:
            raise ValueError("max_routes must be greater than or equal to min_routes")
        return self


class PlanningRuntimeSchema(BaseModel):
    """Validate the top-level runtime configuration contract.

    The dynamic plugin-oriented sections are intentionally kept permissive,
    because their structure depends on user-selected integrations.
    """

    model_config = ConfigDict(extra="allow")

    search: SearchSettingsSchema = Field(default_factory=SearchSettingsSchema)
    post_processing: PostProcessingSchema = Field(default_factory=PostProcessingSchema)
    expansion: dict[str, object] = Field(default_factory=dict)
    filter: dict[str, object] = Field(default_factory=dict)
    stock: dict[str, object] = Field(default_factory=dict)
    scorer: dict[str, object] = Field(default_factory=dict)
