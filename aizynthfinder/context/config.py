"""Configuration objects for the retrosynthesis runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from aizynthfinder.context.policy import ExpansionPolicy, FilterPolicy
from aizynthfinder.schemas import PostProcessingSchema, SearchSettingsSchema
from aizynthfinder.services.configuration import load_configuration_dict, validate_runtime_config
from aizynthfinder.context.scoring import ScorerCollection
from aizynthfinder.context.stock import Stock
from aizynthfinder.utils.logging import logger

if TYPE_CHECKING:
    from aizynthfinder.utils.type_utils import Any, Dict, List, Optional, StrDict


@dataclass
class _PostprocessingConfiguration:
    min_routes: int = 5
    max_routes: int = 25
    all_routes: bool = False
    route_distance_model: Optional[str] = None
    route_scorers: List[str] = field(default_factory=lambda: [])
    scorer_weights: Optional[List[float]] = field(default_factory=lambda: None)


@dataclass
class _SearchConfiguration:
    algorithm: str = "mcts"
    algorithm_config: Dict[str, Any] = field(
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
    max_transforms: int = 6
    iteration_limit: int = 100
    time_limit: int = 120
    return_first: bool = False
    exclude_target_from_stock: bool = True
    break_bonds: List[List[int]] = field(default_factory=list)
    freeze_bonds: List[List[int]] = field(default_factory=list)
    break_bonds_operator: str = "and"


@dataclass
class Configuration:
    """Store runtime settings and loaded planning resources.

    This dataclass represents the internal mutable runtime state used by the
    search engine. External configuration is validated with Pydantic schemas
    before being converted into these dataclass-based runtime objects.
    """

    search: _SearchConfiguration = field(default_factory=_SearchConfiguration)
    post_processing: _PostprocessingConfiguration = field(default_factory=_PostprocessingConfiguration)
    stock: Stock = field(init=False)
    expansion_policy: ExpansionPolicy = field(init=False)
    filter_policy: FilterPolicy = field(init=False)
    scorers: ScorerCollection = field(init=False)

    def __post_init__(self) -> None:
        self.stock = Stock()
        self.expansion_policy = ExpansionPolicy(self)
        self.filter_policy = FilterPolicy(self)
        self.scorers = ScorerCollection(self)
        self._logger = logger()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Configuration):
            return False
        for key, setting in vars(self).items():
            if isinstance(setting, (int, float, str, bool, list)):
                if (
                    vars(self)[key] != vars(other)[key]
                    or self.search != other.search
                    or self.post_processing != other.post_processing
                ):
                    return False
        return True

    @classmethod
    def from_dict(cls, source: StrDict) -> "Configuration":
        """Load configuration from a dictionary payload.

        Args:
            source: The user-provided configuration dictionary.

        Returns:
            A populated runtime configuration object.

        Raises:
            AttributeError: If an unsupported setting key is provided.
            ValueError: If the configuration values fail validation.
        """
        validated = validate_runtime_config(dict(source)).model_dump(exclude_none=True)
        expansion_config = validated.pop("expansion", {})
        filter_config = validated.pop("filter", {})
        stock_config = validated.pop("stock", {})
        scorer_config = validated.pop("scorer", {})

        config_obj = Configuration()
        config_obj._update_from_config(validated)

        config_obj.expansion_policy.load_from_config(**expansion_config)
        config_obj.filter_policy.load_from_config(**filter_config)
        config_obj.stock.load_from_config(**stock_config)
        config_obj.scorers.create_default_scorers()
        config_obj.scorers.load_from_config(**scorer_config)

        return config_obj

    @classmethod
    def from_file(cls, filename: str) -> "Configuration":
        """Load configuration from a YAML file.

        Args:
            filename: The path to a YAML configuration file.

        Returns:
            A populated runtime configuration object.

        Raises:
            ValueError: If required environment variables are missing or the
                configuration content fails validation.
        """
        return Configuration.from_dict(load_configuration_dict(filename))

    def _update_from_config(self, config: StrDict) -> None:
        """Update runtime dataclasses from already-validated config sections.

        Args:
            config: A validated configuration dictionary.
        """
        post_processing = PostProcessingSchema.model_validate(config.pop("post_processing", {}))
        self.post_processing = _PostprocessingConfiguration(**post_processing.model_dump())

        search_config = SearchSettingsSchema.model_validate(config.pop("search", {}))
        for setting, value in search_config.model_dump().items():
            if value is None:
                continue
            if setting == "algorithm_config":
                self.search.algorithm_config.update(value)
            else:
                setattr(self.search, setting, value)
