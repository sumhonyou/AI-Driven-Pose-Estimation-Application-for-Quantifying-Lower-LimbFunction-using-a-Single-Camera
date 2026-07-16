"""Versioned Module B model bundles and the explicit Phase 4 placeholder model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector


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
class StubModel:
    """Deterministic, clearly-labelled Phase 4 stand-in for the trained model."""

    rule_score: float
    feature_schema_version: str = MODULE_B_CORE_CONFIG["feature_schema_version"]
    model_version: str = "stub-0"
    label_order: tuple[str, ...] = ("Poor", "Good")
    feature_names: tuple[str, ...] = ()
    is_placeholder: bool = True

    def __post_init__(self) -> None:
        _assert_0_to_10(self.rule_score, "rule_score")
        validate_model_bundle(self)

    def predict_proba(self, features: FeatureVector) -> dict[str, float]:
        """Return stable binary probabilities derived only from the rule score."""
        assert_feature_vector_compatible(self, features)
        probability_good = self.rule_score / 10.0
        return {"Poor": 1.0 - probability_good, "Good": probability_good}


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
    feature_schema_path: Path,
    label_map_path: Path,
    model_version: str,
) -> JoblibModelBundle:
    """Load a trained artifact and reject stale feature metadata immediately."""
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
    return JoblibModelBundle(
        classifier=joblib.load(model_path),
        feature_schema_version=str(feature_schema["schema_version"]),
        model_version=model_version,
        label_order=tuple(str(label) for label in labels),
        feature_names=tuple(str(name) for name in feature_schema["names"]),
    )


def _assert_0_to_10(value: float, name: str) -> None:
    if not 0.0 <= value <= 10.0:
        raise ValueError(f"{name} must be on the 0–10 scale")
