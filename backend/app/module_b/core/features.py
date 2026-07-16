"""Versioned feature-vector contract shared by live and offline Module B code."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureVector:
    """An ordered feature vector whose name order is part of the model contract."""

    schema_version: str
    names: tuple[str, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("FeatureVector.schema_version must not be empty")
        if not self.names:
            raise ValueError("FeatureVector.names must not be empty")
        if len(self.names) != len(self.values):
            raise ValueError("FeatureVector.names and values must have the same length")
        if len(set(self.names)) != len(self.names):
            raise ValueError("FeatureVector.names must be unique")
        if any(not math.isfinite(value) for value in self.values):
            raise ValueError("FeatureVector.values must be finite")

    def as_dict(self) -> dict[str, float]:
        """Return named values while preserving the declared vector order."""
        return dict(zip(self.names, self.values, strict=True))
