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
    # Optional metadata, NOT a model input: which anatomical leg led the rep
    # ("left"/"right"). Set by asymmetric exercises (lunge) for cross-rep symmetry
    # and the report; left None by symmetric exercises (squat). Kept out of
    # `values`/`names` so the numeric vector stays lead-leg-invariant.
    lead_leg: str | None = None

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
        if self.lead_leg is not None and self.lead_leg not in {"left", "right"}:
            raise ValueError("FeatureVector.lead_leg must be 'left', 'right', or None")

    def as_dict(self) -> dict[str, float]:
        """Return named values while preserving the declared vector order."""
        return dict(zip(self.names, self.values, strict=True))
