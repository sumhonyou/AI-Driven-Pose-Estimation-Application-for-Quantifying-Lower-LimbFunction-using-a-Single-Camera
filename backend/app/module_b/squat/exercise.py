"""Squat implementation of the Module B exercise contract."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.exercise import ModuleBExercise
from app.module_b.squat.config import SQUAT_CONFIG
from app.module_b.squat.fault_gates import FaultGateResult, evaluate_fault_gates
from app.module_b.squat.features import extract_squat_features
from app.module_b.squat.rules import score_squat_rep, score_squat_set
from app.module_b.squat.segmentation import segment_squat_frames
from app.module_b.squat.tags import build_squat_error_tags

if TYPE_CHECKING:
    from app.module_b.core.features import FeatureVector
    from app.module_b.core.fsm import Rep
    from app.module_b.core.rules import RuleScores


class SquatExercise(ModuleBExercise):
    """Squat implementation of the generic Module B exercise interface."""

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

    @property
    def band_policy(self) -> dict[str, Any] | None:
        # Squat uses binary Good/Poor; exercises without a policy keep 3-band scoring.
        return SQUAT_CONFIG.get("band_policy")

    def evaluate_fault_gates(
        self, reps: list[Rep], feature_vectors: list[FeatureVector]
    ) -> FaultGateResult | None:
        # None means the router treats this like a gate-less exercise.
        gate_config = SQUAT_CONFIG.get("fault_gates")
        if not gate_config:
            return None
        return evaluate_fault_gates(reps, feature_vectors, gate_config)

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

    def build_error_tags(
        self, *, fusion: Any, gate_result: Any, rule_scores: RuleScores
    ) -> list[Any]:
        # One taxonomy owns squat system, fault-gate, and soft tempo tags.
        return build_squat_error_tags(
            fusion_flags=fusion.flags,
            gate_result=gate_result,
            rule_scores=rule_scores,
        )
