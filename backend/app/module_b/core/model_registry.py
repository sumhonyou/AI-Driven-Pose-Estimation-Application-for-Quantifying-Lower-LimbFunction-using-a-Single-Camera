"""Versioned Module B model bundles: the trained-artifact loader and its adapter.

The Phase 4 `StubModel` placeholder was deleted in Stage 5.8 (rules.md #20 — no
unnecessary code once its replacement exists) once `get_model_bundle()` below could
load the real trained artifact for every exercise that has one exported.

Phase 5B (Stage 4.5, Lunge) reintroduced a placeholder path -- `PlaceholderModelBundle`
below -- because `get_model_bundle()` is now the ONLY place `router.py` resolves a
model (no per-exercise branching is allowed there, per Stage 4.1's registry
invariant), so an exercise without an exported artifact needs a graceful fallback
here rather than a crash. It is deliberately NOT the old `StubModel`: that one took
`rule_score` as a constructor argument, baked in per-request by the pre-Stage-5.8
router calling it directly -- incompatible with today's cached, `model_key`-only
`get_model_bundle()` accessor, which has no access to any request's `RuleScores`.
`PlaceholderModelBundle` instead returns a constant, feature-independent 50/50 --
honest given it has no real signal, and it existing at all is transitional: once
Stage 5.8 (Lunge) exports a real artifact, `get_model_bundle("lunge")` picks it up
automatically and this path stops being reached for lunge, the same way it already
stopped being reached for squat.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector

# ml/artifacts/{model_key}/ — the one committed location Stage 5.8's export script
# writes to; not duplicated into backend/ (single source, X1). Mirrors the existing
# frontend/pose-model-asset cross-directory reference convention (ml/config.yaml's
# `pose_model_asset: ../frontend/public/models/...`).
_ARTIFACTS_ROOT = Path(__file__).resolve().parents[4] / "ml" / "artifacts"


@runtime_checkable
class ModelBundle(Protocol):
    """A versioned model that refuses incompatible runtime feature vectors."""

    feature_schema_version: str
    model_version: str
    label_order: tuple[str, ...]
    feature_names: tuple[str, ...]
    is_placeholder: bool

    def predict_proba(self, features: FeatureVector) -> dict[str, float]: ...


@dataclass(frozen=True)
class PlaceholderModelBundle:
    """Deliberately neutral stand-in for an exercise with no trained artifact yet.

    Returns a constant P(Good)=P(Poor)=0.5 regardless of `features` -- it has no
    real signal to offer, so it does not pretend to. `fuse_scores()` (unchanged)
    reads that as confidence=0.5, below `confidence_low_threshold`, and honestly
    forces band="Fair" via the existing low_confidence override rather than this
    class inventing its own banding rule.
    """

    feature_schema_version: str = MODULE_B_CORE_CONFIG["feature_schema_version"]
    model_version: str = "stub-0"
    label_order: tuple[str, ...] = ("Poor", "Good")
    feature_names: tuple[str, ...] = ()
    is_placeholder: bool = True

    def __post_init__(self) -> None:
        validate_model_bundle(self)

    def predict_proba(self, features: FeatureVector) -> dict[str, float]:
        """Return a constant neutral probability; ignores `features` on purpose."""
        assert_feature_vector_compatible(self, features)
        return {"Poor": 0.5, "Good": 0.5}


@dataclass(frozen=True)
class _CalibratedForestClassifier:
    """Recomposes calibrated Good/Poor probabilities from the two exported files.

    Stage 5.8 exports the fitted Extra Trees forest (`model.joblib`) and its sigmoid
    calibration parameters (`calibrator.joblib`, a plain `{"a":..., "b":...}` dict, not
    sklearn's private `_SigmoidCalibration` object) separately rather than the whole
    `CalibratedClassifierCV` as one file — see `export_squat_model.py`'s docstring for
    why. This class is the other half of that split: it reproduces exactly what
    `CalibratedClassifierCV(ensemble=False).predict_proba()` computes for a binary
    sigmoid calibration (verified bit-for-bit identical against the real pipeline at
    export time, not assumed from reading sklearn's source):
    `P(Good) = 1 / (1 + exp(a * raw_p_good + b))`, where `raw_p_good` is the
    uncalibrated forest's probability for its class `1` (Good, since the training
    label encoding is `0=Poor, 1=Good` — enforced below rather than assumed).
    """

    forest: Any
    calibration: dict[str, float]

    def __post_init__(self) -> None:
        if list(self.forest.classes_) != [0, 1]:
            raise ValueError(
                f"Forest classes_ {list(self.forest.classes_)} != [0, 1] "
                "(expected 0=Poor, 1=Good per label_map.json)"
            )
        if set(self.calibration) != {"a", "b"}:
            raise ValueError("calibration dict must provide exactly {'a', 'b'}")

    def predict_proba(self, x: list[list[float]]) -> np.ndarray:
        """Same call shape as a fitted sklearn classifier: rows in, (n, 2) probs out."""
        raw_p_good = self.forest.predict_proba(x)[:, 1]
        p_good = 1.0 / (
            1.0 + np.exp(self.calibration["a"] * raw_p_good + self.calibration["b"])
        )
        return np.column_stack([1.0 - p_good, p_good])


@dataclass(frozen=True)
class JoblibModelBundle:
    """Adapter around a fitted sklearn-style joblib classifier artifact."""

    classifier: Any
    feature_schema_version: str
    model_version: str
    label_order: tuple[str, ...]
    feature_names: tuple[str, ...]
    is_placeholder: bool = False

    def __post_init__(self) -> None:
        validate_model_bundle(self)

    def predict_proba(self, features: FeatureVector) -> dict[str, float]:
        """Predict only after enforcing the versioned feature-name order."""
        assert_feature_vector_compatible(self, features)
        probabilities = self.classifier.predict_proba([list(features.values)])[0]
        if len(probabilities) != len(self.label_order):
            raise ValueError("Model probability output does not match label_order")
        return {
            label: float(probability)
            for label, probability in zip(self.label_order, probabilities, strict=True)
        }


def validate_model_bundle(bundle: ModelBundle) -> None:
    """Reject a model artifact whose feature schema differs from this runtime."""
    runtime_schema_version = MODULE_B_CORE_CONFIG["feature_schema_version"]
    if bundle.feature_schema_version != runtime_schema_version:
        raise ValueError(
            "Model feature schema mismatch: "
            f"bundle={bundle.feature_schema_version}, runtime={runtime_schema_version}"
        )
    if not bundle.model_version:
        raise ValueError("Model bundle must declare model_version")
    if tuple(bundle.label_order) != ("Poor", "Good"):
        raise ValueError("Option A ModelBundle.label_order must be ('Poor', 'Good')")


def assert_feature_vector_compatible(
    bundle: ModelBundle, features: FeatureVector
) -> None:
    """Enforce version and order parity before an artifact scores a vector."""
    validate_model_bundle(bundle)
    if features.schema_version != bundle.feature_schema_version:
        raise ValueError(
            "FeatureVector schema mismatch: "
            f"vector={features.schema_version}, bundle={bundle.feature_schema_version}"
        )
    if bundle.feature_names and features.names != bundle.feature_names:
        raise ValueError("FeatureVector names/order does not match the trained model")


def load_joblib_model_bundle(
    *,
    model_path: Path,
    calibrator_path: Path,
    feature_schema_path: Path,
    label_map_path: Path,
) -> JoblibModelBundle:
    """Load Stage 5.8's exported artifact and reject stale feature metadata immediately.

    `model_version` is read from `feature_schema.json`, not passed by the caller: it is
    a property of the exported artifact itself, and having every caller separately
    supply a matching string would risk one of them quoting a stale or wrong version
    for a real model (unlike `StubModel`'s `"stub-0"`, which never needed to be right).
    """
    try:
        import joblib
    except ImportError as error:  # pragma: no cover - exercised in deployment setup.
        raise RuntimeError(
            "joblib is required to load a trained Module B model"
        ) from error

    feature_schema = json.loads(feature_schema_path.read_text())
    label_map = json.loads(label_map_path.read_text())
    labels = label_map.get("label_order", label_map.get("labels", label_map))
    if not isinstance(labels, list):
        raise ValueError("label_map must provide a list under label_order or labels")

    forest = joblib.load(model_path)
    calibration = joblib.load(calibrator_path)
    classifier = _CalibratedForestClassifier(forest=forest, calibration=calibration)
    return JoblibModelBundle(
        classifier=classifier,
        feature_schema_version=str(feature_schema["schema_version"]),
        model_version=str(feature_schema["model_version"]),
        label_order=tuple(str(label) for label in labels),
        feature_names=tuple(str(name) for name in feature_schema["names"]),
    )


@lru_cache(maxsize=None)
def get_model_bundle(model_key: str) -> ModelBundle:
    """Load-once, cache-forever accessor for a registered exercise's trained bundle.

    Keyed by `model_key` (`ModuleBExercise.model_key`, e.g. `SquatExercise`'s `"squat"`)
    rather than hardcoding a single path, so a future exercise's own artifact directory
    (`ml/artifacts/{model_key}/`) is picked up the same way without a router.py change.
    `lru_cache` rather than an app-startup hook: this is a small, pure, deterministic
    load keyed only by `model_key`, and every request needs the same cached object — the
    standard FastAPI idiom for a stateless model artifact, not a new abstraction for its
    own sake. Reloading `model.joblib` (a ~1 MB forest) per request would also add real,
    measurable latency on top of Stage 5.7's ~8 ms feature+predict budget.

    Falls back to `PlaceholderModelBundle` when `model_key` has no exported artifact
    yet (Stage 4.5, Lunge) -- caching that constant, feature-independent bundle is
    safe (no per-request state to go stale), unlike the old per-request `StubModel`.
    """
    artifacts_dir = _ARTIFACTS_ROOT / model_key
    if not (artifacts_dir / "model.joblib").exists():
        return PlaceholderModelBundle()
    return load_joblib_model_bundle(
        model_path=artifacts_dir / "model.joblib",
        calibrator_path=artifacts_dir / "calibrator.joblib",
        feature_schema_path=artifacts_dir / "feature_schema.json",
        label_map_path=_ARTIFACTS_ROOT / "label_map.json",
    )
