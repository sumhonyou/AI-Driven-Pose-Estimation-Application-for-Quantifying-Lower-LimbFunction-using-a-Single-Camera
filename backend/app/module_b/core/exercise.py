"""Contract implemented by every Module B exercise plugin."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.module_b.core.features import FeatureVector
    from app.module_b.core.fsm import Rep
    from app.module_b.core.rules import RuleScores
    from app.module_b.squat.fault_gates import FaultGateResult


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

    @property
    def band_policy(self) -> dict[str, Any] | None:
        """Optional banding override for fusion. None keeps the 3-band abstention."""
        return None

    def evaluate_fault_gates(
        self, reps: list[Rep], feature_vectors: list[FeatureVector]
    ) -> FaultGateResult | None:
        """Optional interpretable fault gates run across every rep of a set.

        Returns None by default: an exercise that defines no gates is unaffected, so
        Module A keeps its exact behaviour. An exercise that opts in returns a
        FaultGateResult; if it is not ``all_passed``, the router overrides the fused
        band to Poor with a specific reason.
        """
        return None

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

    def build_error_tags(
        self, *, fusion: Any, gate_result: Any, rule_scores: RuleScores
    ) -> list[Any] | None:
        """Optional taxonomy-driven error-tag builder for the analyzed set.

        Returns None by default so the router falls back to its generic system+gate tag
        construction. An exercise that owns a tag taxonomy returns the full
        ErrorTagWrite list, keeping every tag's severity/source in one place.
        """
        return None
