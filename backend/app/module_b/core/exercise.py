"""Contract implemented by every Module B exercise plugin."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.module_b.core.features import FeatureVector
    from app.module_b.core.fsm import Rep
    from app.module_b.core.rules import RuleScores


class ModuleBExercise(ABC):
    """Exercise-owned behavior used by the shared Module B pipeline."""

    @property
    @abstractmethod
    def code(self) -> str:
        """Stable exercise code used by the catalog, API, and registry."""

    @property
    @abstractmethod
    def config(self) -> dict[str, Any]:
        """Serializable core and exercise thresholds served to the frontend."""

    @property
    @abstractmethod
    def required_view(self) -> str:
        """Camera orientation required for this exercise."""

    @property
    @abstractmethod
    def model_key(self) -> str:
        """Stable key used to resolve the exercise's model bundle."""

    @abstractmethod
    def segment(self, frames: list[dict[str, Any]]) -> list[Rep]:
        """Split a buffered set into exercise repetitions."""

    @abstractmethod
    def extract_features(self, rep: Rep) -> FeatureVector:
        """Build the ordered FeatureVector for one repetition."""

    @abstractmethod
    def rule_subscores(self, rep: Rep, features: FeatureVector) -> RuleScores:
        """Calculate exercise-specific RuleScores for one repetition."""

    @abstractmethod
    def set_rule_scores(
        self, reps: list[Rep], feature_vectors: list[FeatureVector]
    ) -> RuleScores:
        """Aggregate a completed set's per-rep features into RuleScores."""

    @abstractmethod
    def error_tags(
        self, features: FeatureVector, rules: RuleScores, ml: Any
    ) -> list[str]:
        """Return deterministic exercise-specific movement-quality tags."""
