"""Squat implementation of the Module B exercise contract."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.exercise import ModuleBExercise
from app.module_b.squat.config import SQUAT_CONFIG
from app.module_b.squat.features import extract_squat_features
from app.module_b.squat.rules import score_squat_rep, score_squat_set
from app.module_b.squat.segmentation import segment_squat_frames

if TYPE_CHECKING:
    from app.module_b.core.features import FeatureVector
    from app.module_b.core.fsm import Rep
    from app.module_b.core.rules import RuleScores


class SquatExercise(ModuleBExercise):
    """Squat plugin shell; analysis methods are filled by Stages 4.2-4.5."""

    @property
    def code(self) -> str:
        return SQUAT_CONFIG["exercise_code"]

    @property
    def config(self) -> dict[str, Any]:
        return {
            "core": deepcopy(MODULE_B_CORE_CONFIG),
            "exercise": deepcopy(SQUAT_CONFIG),
        }

    @property
    def required_view(self) -> str:
        return SQUAT_CONFIG["required_view"]

    @property
    def model_key(self) -> str:
        return SQUAT_CONFIG["model_key"]

    def segment(self, frames: list[dict[str, Any]]) -> list[Rep]:
        return segment_squat_frames(frames)

    def extract_features(self, rep: Rep) -> FeatureVector:
        return extract_squat_features(rep)

    def rule_subscores(self, rep: Rep, features: FeatureVector) -> RuleScores:
        return score_squat_rep(features)

    def set_rule_scores(
        self, reps: list[Rep], feature_vectors: list[FeatureVector]
    ) -> RuleScores:
        return score_squat_set(feature_vectors)

    def error_tags(
        self, features: FeatureVector, rules: RuleScores, ml: Any
    ) -> list[str]:
        raise NotImplementedError("Squat error tags are implemented in Stage 4.4")
