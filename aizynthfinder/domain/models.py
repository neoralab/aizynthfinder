"""Internal immutable value objects used by orchestration layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SmilesBatch:
    """Represent a resolved batch of input SMILES.

    Attributes:
        source: The source file, if the batch originated from disk.
        smiles: The ordered SMILES values to process.
    """

    source: Path | None
    smiles: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PlannerRunArtifacts:
    """Carry lightweight in-memory artifacts from a planning run.

    Attributes:
        target_smiles: The input target used for the run.
        statistics: Aggregated search statistics.
        stock_info: Stock availability extracted from built routes.
        routes: Serialized full retrosynthesis trees and scores.
    """

    target_smiles: str
    statistics: dict[str, object]
    stock_info: dict[str, object]
    routes: list[dict[str, Any]]
