"""Lunge implementation of the Module B exercise contract."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.exercise import ModuleBExercise
from app.module_b.lunge.config import LUNGE_CONFIG
from app.module_b.lunge.features import extract_lunge_features
from app.module_b.lunge.rules import score_lunge_rep, score_lunge_set
from app.module_b.lunge.segmentation import segment_lunge_frames

if TYPE_CHECKING:
    from app.module_b.core.features import FeatureVector
    from app.module_b.core.fsm import Rep
    from app.module_b.core.rules import RuleScores


class LungeExercise(ModuleBExercise):
    """Lunge plugin shell; analysis methods are filled by Stages 4.2-4.6 (Lunge)."""

    @property
    def code(self) -> str:
        return LUNGE_CONFIG["exercise_code"]

    @property
    def config(self) -> dict[str, Any]:
        return {
            "core": deepcopy(MODULE_B_CORE_CONFIG),
            "exercise": deepcopy(LUNGE_CONFIG),
        }

    @property
    def required_view(self) -> str:
        return LUNGE_CONFIG["required_view"]

    @property
    def model_key(self) -> str:
        return LUNGE_CONFIG["model_key"]

    def segment(self, frames: list[dict[str, Any]]) -> list[Rep]:
        return segment_lunge_frames(frames)

    def extract_features(self, rep: Rep) -> FeatureVector:
        # Live path: lead leg is inferred from frame geometry. Offline training
        # (Stage 5.3) calls extract_lunge_features with the known exercise_subtype.
        return extract_lunge_features(rep)

    def rule_subscores(self, rep: Rep, features: FeatureVector) -> RuleScores:
        return score_lunge_rep(features)

    def set_rule_scores(
        self, reps: list[Rep], feature_vectors: list[FeatureVector]
    ) -> RuleScores:
        return score_lunge_set(feature_vectors)

    def error_tags(
        self, features: FeatureVector, rules: RuleScores, ml: Any
    ) -> list[str]:
        raise NotImplementedError("Lunge error tags are implemented in Stage 6.1")
