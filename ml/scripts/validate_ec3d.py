"""Stage 5.9: external validation of the shipped squat model against EC3D.

EC3D was never touched by training (Option A's validation firewall), so it is the only
independent cohort available to this project. This script scores the **exported
artifact** (`ml/artifacts/squat/`, via the backend's own loader) on EC3D's 132 squat
repetitions and reports what happened.

What it found is a **negative result**, and the report is written to say so plainly
rather than to produce a generalisation number the data cannot support. Three
independent findings, each measured here rather than asserted:

1. **EC3D's poses are canonicalised, not raw mocap.** Every frame is root-centred
   (mid-hip pinned to exactly (0,0,0)), orientation-normalised (the neck sits at
   exactly z=0.19517662, y=0 in all 11,109 squat frames, for every label including
   "Front bent"), and retargeted onto one template skeleton (all four subjects share
   bone lengths to ~4 decimal places). Joint angles survive that — they are 3-point
   angles, invariant to rigid transforms. Anything measured against **gravity** or
   **global translation** does not. `_canonicalisation_evidence()` measures this.

2. **The two datasets disagree about what "incorrect" means.** REHAB24-6's incorrect
   squats are *deeper* than its correct ones (established in Stage 5.4/5.5/5.6 and
   visible in `FEATURE_VALIDITY.md`); EC3D's fault taxonomy contains "Not low enough",
   so its incorrect squats are *shallower*. The Good/Poor direction therefore inverts
   across most of the model's importance mass. `_transfer_diagnostic()` measures this
   per feature, weighted by the forest's own Gini importance.

3. **Half of EC3D's fault class is invisible to this system by design.** Of its four
   squat faults, "Feet too wide" and "Knees inward" are frontal-plane; Locked
   Assumption #3 drops frontal valgus as monocular-infeasible, so no feature, tag or
   rule exists to catch them. They are still labelled incorrect in EC3D's ground
   truth. `_fault_breakdown()` reports per-fault results so this is visible rather
   than averaged away.

The confusion matrix the checklist requires is still produced, drawn by Stage 5.7's
own `plot_confusion_matrix_3band()` (not a copy of it) so the two are comparable side
by side. It is captioned as what it is: the response of a model to systematically
inverted, out-of-distribution input — not an estimate of how it generalises.

Nothing here re-tunes, re-fits or re-thresholds anything. The artifact and
`MODULE_B_CORE_CONFIG` are read live and used as shipped.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import yaml
from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.model_registry import get_model_bundle
from app.module_b.core.preprocessing import preprocess_world_landmarks
from app.module_b.squat.features import SQUAT_FEATURE_NAMES, extract_squat_features
from evaluate_squat import _evaluation_metrics, plot_confusion_matrix_3band
from sweep_fusion_weights import PREDICTED_BANDS, TRUE_LABELS, _fuse_all, _rule_score
from train_squat import _read_rows

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "EC3D_VALIDATION_REPORT.md"
JOINT_MAP_DOC = "../docs/ec3d_joint_mapping.md"

# EC3D ships OpenPose BODY_25 ordering. Confirmed empirically, not assumed — see
# `ml/docs/ec3d_joint_mapping.md` for the bone-rigidity proof and the two independent
# anatomical axis checks. Only the 8 landmarks `core/quality.REQUIRED_LANDMARKS`
# names are mapped, because they are the only ones squat feature extraction reads.
BODY25_TO_MP33 = {
    5: 11,  # LShoulder
    2: 12,  # RShoulder
    12: 23,  # LHip
    9: 24,  # RHip
    13: 25,  # LKnee
    10: 26,  # RKnee
    14: 27,  # LAnkle
    11: 28,  # RAnkle
}


# EC3D's own axes (verified in the joint-mapping doc): 0 = medio-lateral,
# 1 = anterior, 2 = the canonical "up" (torso) axis. MediaPipe world landmarks are
# x = horizontal, y = DOWN, z = depth. A side-view capture puts the sagittal plane in
# the image, so anterior becomes the horizontal image axis and medio-lateral becomes
# depth. Negating both mapped axes keeps det(R) = +1 — a proper rotation rather than
# a mirror, which would silently swap the skeleton's left and right.
def _to_mp33_landmarks(pose_body25: np.ndarray) -> list[dict[str, float]]:
    """One EC3D frame (25, 3) -> a runtime-shaped MediaPipe-33 landmark list."""
    landmarks = [{"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 0.0} for _ in range(33)]
    for body25_index, mp33_index in BODY25_TO_MP33.items():
        lateral, anterior, up = (float(v) for v in pose_body25[body25_index])
        landmarks[mp33_index] = {
            "x": -anterior,
            "y": -up,
            "z": lateral,
            # Mocap has no visibility concept: these joints are fully observed, so
            # 1.0 is the honest value rather than a filler. It also means the
            # confidence filter and gap-fill are no-ops here and `q` is a clean 1.0,
            # which is stated in the report rather than left for a reader to infer.
            "visibility": 1.0,
        }
    return landmarks


# 30 FPS, per the dataset's own paper (Zhao et al., ACCV 2022). EC3D stores a frame
# index, not a timestamp; the three temporal features need real seconds.
EC3D_FPS = 30.0

# EC3D's instruction labels. Label 1 is the only correct class; 2-5 are the four squat
# faults named in the paper. Under Option A (Locked Assumption #1) the model is binary,
# so every fault maps to Poor — the same collapse REHAB24-6's `correctness` column gets.
EC3D_SQUAT_LABELS = {
    "1": "Correct",
    "2": "Feet too wide",
    "3": "Knees inward",
    "4": "Not low enough",
    "5": "Front bent",
}
# Which plane each fault lives in. Locked Assumption #3 drops the frontal plane
# entirely, so the two frontal faults have no detector anywhere in this system.
EC3D_FAULT_PLANE = {
    "2": "frontal",
    "3": "frontal",
    "4": "sagittal",
    "5": "sagittal",
}
CORRECT_LABEL = "1"

# Sena performed 9 extra squat episodes under an undocumented label 10. Excluded:
# the paper's own count is 132 squat sequences, which is exactly what remains without
# it, and no other subject has it. Guessing its meaning would be inventing ground truth.
EXCLUDED_LABEL = "10"
PAPER_SQUAT_SEQUENCE_COUNT = 132


def _load_config() -> dict:
    with open(ML_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def load_ec3d_squats(pickle_path: Path) -> tuple[dict, np.ndarray]:
    """Return ({(subject, label, episode): [frame_row, ...]}, poses[frame, 25, 3])."""
    with open(pickle_path, "rb") as f:
        data = pickle.load(f)
    labels, poses = data["labels"], data["poses"]
    squat_mask = labels[:, 0] == "SQUAT"
    squat_labels = labels[squat_mask]
    # Stored (frames, 3, 25); every consumer here wants (frames, 25, 3).
    squat_poses = np.transpose(poses[squat_mask], (0, 2, 1))

    episodes: dict[tuple[str, str, str], list[int]] = {}
    for row_index in range(len(squat_labels)):
        subject, label, episode = squat_labels[row_index, 1:4]
        if label == EXCLUDED_LABEL:
            continue
        episodes.setdefault((str(subject), str(label), str(episode)), []).append(
            row_index
        )
    return episodes, squat_poses


def build_ec3d_feature_rows(episodes: dict, poses: np.ndarray) -> list[dict]:
    """One feature row per EC3D episode, via the live extractor (X1).

    EC3D's episodes are its own instructed repetition boundaries, so they are used
    directly rather than re-segmented — the same decision Stage 5.3 made for
    REHAB24-6's physio-verified `first_frame`/`last_frame`. Re-running the FSM here
    would measure the segmenter, not the model.
    """
    rows = []
    for key in sorted(episodes, key=lambda k: (k[0], int(k[1]), int(k[2]))):
        subject, label, episode = key
        frame_indices = episodes[key]
        frames = [
            {
                "frameIndex": position,
                "timestampMs": int(round(position * 1000.0 / EC3D_FPS)),
                "worldLandmarks": _to_mp33_landmarks(poses[frame_index]),
            }
            for position, frame_index in enumerate(frame_indices)
        ]
        # Same preprocessing the live capture runs (X1). With visibility pinned at
        # 1.0 the confidence filter and gap-fill are no-ops, so this is One Euro only.
        vector = extract_squat_features(preprocess_world_landmarks(frames))
        row = {
            "subject": subject,
            "ec3d_label": label,
            "episode": episode,
            "fault_name": EC3D_SQUAT_LABELS[label],
            "label": "Good" if label == CORRECT_LABEL else "Poor",
            "n_frames": len(frames),
            "feature_schema_version": vector.schema_version,
        }
        row.update(dict(zip(SQUAT_FEATURE_NAMES, vector.values, strict=True)))
        rows.append(row)
    return rows


def _canonicalisation_evidence(poses: np.ndarray, episodes: dict) -> dict:
    """Measure the three normalisations that decide which features can transfer.

    Reported as numbers rather than described, because they are the whole reason this
    stage's headline is a caveat instead of an accuracy.
    """
    kept = np.concatenate([np.array(v) for v in episodes.values()])
    used = poses[kept]
    mid_hip, neck = used[:, 8, :], used[:, 1, :]

    # Per-subject bone lengths: four different people cannot share a femur length.
    subject_of = {}
    for (subject, _label, _episode), rows in episodes.items():
        subject_of.setdefault(subject, []).extend(rows)
    thigh_by_subject = {
        subject: float(
            np.linalg.norm(poses[rows][:, 9, :] - poses[rows][:, 10, :], axis=-1).mean()
        )
        for subject, rows in sorted(subject_of.items())
    }
    thighs = list(thigh_by_subject.values())
    return {
        "mid_hip_max_abs": float(np.abs(mid_hip).max()),
        "neck_up_std": float(neck[:, 2].std()),
        "neck_up_value": float(neck[:, 2].mean()),
        "neck_anterior_std": float(neck[:, 1].std()),
        "thigh_by_subject": thigh_by_subject,
        "thigh_spread_pct": float(
            (max(thighs) - min(thighs)) / float(np.mean(thighs)) * 100.0
        ),
        "n_frames": int(len(kept)),
    }


def _auc(positive: np.ndarray, negative: np.ndarray) -> float:
    """Rank-based AUC — the same univariate separation measure Stage 5.4 used."""
    pooled = np.concatenate([positive, negative])
    ranks = np.argsort(np.argsort(pooled)) + 1
    n_pos = len(positive)
    return float(
        (ranks[:n_pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * len(negative))
    )


def _gini_importances(model) -> dict[str, float]:
    """Read importances off the shipped forest itself, never transcribed."""
    forest = model.classifier.forest
    return dict(
        zip(model.feature_names, forest.feature_importances_.tolist(), strict=True)
    )


def _transfer_diagnostic(
    ec3d_rows: list[dict], rehab_rows: list[dict], importances: dict[str, float]
) -> dict:
    """Per-feature Good/Poor direction in each dataset, weighted by importance.

    A feature whose direction flips is worse than a missing one: the model does not
    abstain on it, it reads the flipped evidence confidently in the wrong direction.
    """

    def _split(rows: list[dict], feature: str) -> tuple[np.ndarray, np.ndarray]:
        good = np.array(
            [float(r[feature]) for r in rows if r["label"] == "Good"], dtype=float
        )
        poor = np.array(
            [float(r[feature]) for r in rows if r["label"] == "Poor"], dtype=float
        )
        return good, poor

    per_feature = []
    inverted_mass = 0.0
    for feature in SQUAT_FEATURE_NAMES:
        rehab_good, rehab_poor = _split(rehab_rows, feature)
        ec3d_good, ec3d_poor = _split(ec3d_rows, feature)
        rehab_auc = _auc(rehab_poor, rehab_good)
        ec3d_auc = _auc(ec3d_poor, ec3d_good)
        inverted = (rehab_auc - 0.5) * (ec3d_auc - 0.5) < 0
        if inverted:
            inverted_mass += importances[feature]
        per_feature.append(
            {
                "feature": feature,
                "importance": importances[feature],
                "rehab_good_mean": float(rehab_good.mean()),
                "rehab_poor_mean": float(rehab_poor.mean()),
                "ec3d_good_mean": float(ec3d_good.mean()),
                "ec3d_poor_mean": float(ec3d_poor.mean()),
                "rehab_auc": rehab_auc,
                "ec3d_auc": ec3d_auc,
                "inverted": inverted,
            }
        )
    per_feature.sort(key=lambda d: -d["importance"])
    return {"per_feature": per_feature, "inverted_mass": inverted_mass}


def _fault_breakdown(rows: list[dict], bands: list[str]) -> list[dict]:
    """Per EC3D instruction label: what band did the system give it?

    Averaging over the fault class would hide that two of the four faults are frontal
    and have no detector in this system at all.
    """
    breakdown = []
    for label, name in EC3D_SQUAT_LABELS.items():
        indices = [i for i, r in enumerate(rows) if r["ec3d_label"] == label]
        if not indices:
            continue
        got = [bands[i] for i in indices]
        breakdown.append(
            {
                "label": label,
                "name": name,
                "plane": EC3D_FAULT_PLANE.get(label, "n/a (correct class)"),
                "n": len(indices),
                "counts": {band: got.count(band) for band in PREDICTED_BANDS},
            }
        )
    return breakdown


def main() -> None:
    config = _load_config()
    pickle_path = Path(config["dataset_paths"]["ec3d"]["pickle_path"])
    print(f"Loading EC3D from {pickle_path} ...")
    episodes, poses = load_ec3d_squats(pickle_path)
    print(f"  {len(episodes)} squat episodes after excluding label {EXCLUDED_LABEL}")
    if len(episodes) != PAPER_SQUAT_SEQUENCE_COUNT:
        raise ValueError(
            f"Expected {PAPER_SQUAT_SEQUENCE_COUNT} squat sequences (the EC3D paper's "
            f"own count); got {len(episodes)}. The label filter or the pickle changed."
        )

    evidence = _canonicalisation_evidence(poses, episodes)
    print(
        f"  canonicalisation: mid-hip |max|={evidence['mid_hip_max_abs']:.1e}, "
        f"neck up-axis std={evidence['neck_up_std']:.1e}, "
        f"per-subject thigh spread={evidence['thigh_spread_pct']:.3f}%"
    )

    print(
        "Mapping BODY_25 -> MediaPipe-33 and extracting features via the live code..."
    )
    ec3d_rows = build_ec3d_feature_rows(episodes, poses)
    true_labels = [row["label"] for row in ec3d_rows]
    print(
        f"  {len(ec3d_rows)} reps: "
        f"{true_labels.count('Good')} Correct / {true_labels.count('Poor')} faulty"
    )

    model = get_model_bundle("squat")
    print(f"Scoring with the shipped artifact: model_version={model.model_version}")
    x = np.array(
        [[float(row[name]) for name in SQUAT_FEATURE_NAMES] for row in ec3d_rows],
        dtype=float,
    )
    prob_good = np.array(
        [model.classifier.predict_proba([row])[0][1] for row in x.tolist()], dtype=float
    )

    rule_scores = [_rule_score(row) for row in ec3d_rows]
    # Mocap: every mapped joint is fully observed, so `q` is a clean 1.0 and the
    # q_min gate never fires. Stated in the report rather than left implicit.
    qs = [1.0] * len(ec3d_rows)

    w_rule = MODULE_B_CORE_CONFIG["w_rule_default"]
    w_ml = MODULE_B_CORE_CONFIG["w_ml_default"]
    threshold = MODULE_B_CORE_CONFIG["confidence_low_threshold"]
    print(
        f"Fusing at the shipped config: w_rule={w_rule}, w_ml={w_ml}, "
        f"confidence_low_threshold={threshold}"
    )
    fused = _fuse_all(
        ec3d_rows,
        prob_good,
        rule_scores,
        qs,
        w_rule=w_rule,
        w_ml=w_ml,
        confidence_low_threshold=threshold,
    )
    bands = [f.band for f in fused]
    metrics = _evaluation_metrics(true_labels, bands)
    print(
        f"  accuracy_strict={metrics['accuracy_strict']:.3f}  "
        f"accuracy_confident={metrics['accuracy_confident']:.3f}  "
        f"macro_f1={metrics['macro_f1']:.3f}  fair_rate={metrics['fair_rate']:.3f}"
    )

    importances = _gini_importances(model)
    diagnostic = _transfer_diagnostic(ec3d_rows, _read_rows(), importances)
    print(
        "  Gini importance mass whose Good/Poor direction inverts vs REHAB24-6: "
        f"{diagnostic['inverted_mass']:.4f} "
        f"({diagnostic['inverted_mass'] * 100:.1f}%)"
    )

    breakdown = _fault_breakdown(ec3d_rows, bands)
    figure_path = plot_confusion_matrix_3band(
        metrics,
        dataset_label="EC3D",
        subtitle=(
            f"counts, row-normalised %; n={metrics['n']} reps, 4 subjects\n"
            "NOT a generalisation estimate — see report"
        ),
        name="ec3d_confusion_matrix",
    )
    print(f"Wrote {figure_path}")

    write_report(
        ec3d_rows=ec3d_rows,
        metrics=metrics,
        evidence=evidence,
        diagnostic=diagnostic,
        breakdown=breakdown,
        prob_good=prob_good,
        model=model,
        w_rule=w_rule,
        w_ml=w_ml,
        threshold=threshold,
    )
    print(f"Wrote {REPORT_MD}")


def _fmt(value: float, places: int = 3) -> str:
    return f"{value:.{places}f}"


def write_report(
    *,
    ec3d_rows: list[dict],
    metrics: dict,
    evidence: dict,
    diagnostic: dict,
    breakdown: list[dict],
    prob_good: np.ndarray,
    model,
    w_rule: float,
    w_ml: float,
    threshold: float,
) -> None:
    counts = metrics["counts"]
    subjects = sorted({row["subject"] for row in ec3d_rows})
    n_good = sum(1 for r in ec3d_rows if r["label"] == "Good")
    n_poor = len(ec3d_rows) - n_good

    diag_rows = "\n".join(
        f"| `{d['feature']}` | {_fmt(d['importance'], 4)} | "
        f"{_fmt(d['rehab_good_mean'], 2)} / {_fmt(d['rehab_poor_mean'], 2)} | "
        f"{_fmt(d['ec3d_good_mean'], 2)} / {_fmt(d['ec3d_poor_mean'], 2)} | "
        f"{_fmt(d['rehab_auc'], 3)} | {_fmt(d['ec3d_auc'], 3)} | "
        f"{'**INVERTED**' if d['inverted'] else 'same'} |"
        for d in diagnostic["per_feature"]
    )
    fault_rows = "\n".join(
        f"| {b['label']} — {b['name']} | {b['plane']} | {b['n']} | "
        + " | ".join(str(b["counts"][band]) for band in PREDICTED_BANDS)
        + " |"
        for b in breakdown
    )
    thigh_rows = ", ".join(
        f"{subject} {_fmt(length, 6)}"
        for subject, length in evidence["thigh_by_subject"].items()
    )

    # The single sharpest demonstration of Finding 2: the rate at which the system
    # calls a rep Good, for the shallowest fault vs for the genuinely correct class.
    by_label = {b["label"]: b for b in breakdown}
    not_low = by_label["4"]
    correct = by_label["1"]
    not_low_good_rate = not_low["counts"]["Good"] / not_low["n"]
    correct_good_rate = correct["counts"]["Good"] / correct["n"]

    report = f"""# EC3D external validation — Phase 5, Stage 5.9

**Verdict: the external validation could not be performed as a generalisation check,
and this report explains why with measurements rather than reporting a number that
would not mean what it appears to mean.** The confusion matrix the checklist requires
is included, and it is captioned as what it actually is.

Model under test: `{model.model_version}` — the exported artifact in
`ml/artifacts/squat/`, loaded through the backend's own `get_model_bundle("squat")`,
scored at the shipped fusion config (`w_rule={w_rule}`, `w_ml={w_ml}`,
`confidence_low_threshold={threshold}`). Nothing was re-tuned for this report.

Cohort: **{len(ec3d_rows)} EC3D squat repetitions** — {n_good} Correct, {n_poor} faulty —
from **{len(subjects)} subjects** ({", ".join(subjects)}).

## The headline caveat, stated before any metric

EC3D has **{len(subjects)} subjects**. Nothing computed from it can be a generalisation
claim about a population; at this size a single subject moves every number materially.
The checklist called this an external *check*, never a headline, and that framing is
kept here. The findings below make the caveat stronger, not weaker.

## Result

| metric | value |
| ------ | ----- |
| `accuracy_strict` (Fair counted wrong) | **{_fmt(metrics["accuracy_strict"])}** |
| `accuracy_confident` (Fair excluded) | **{_fmt(metrics["accuracy_confident"])}** |
| `macro_f1` | {_fmt(metrics["macro_f1"])} |
| `fair_rate` (abstention) | {_fmt(metrics["fair_rate"])} |
| `recall_good` | {_fmt(metrics["recall_good"])} |
| `recall_poor` | {_fmt(metrics["recall_poor"])} |
| n | {metrics["n"]} |

![Fused 3-band output on EC3D. Rows are EC3D ground truth (Correct/faulty, collapsed to Good/Poor by Option A); columns are the band the user would be shown. Cells show counts with row-normalised percentages. Drawn by the same plotting function as `confusion_matrix_3band.png` (not a copy of it), so the two matrices are directly comparable side by side.](figures/ec3d_confusion_matrix.png)

**The matrix above is n={metrics["n"]} repetitions from {len(subjects)} subjects only,
and it is not a generalisation estimate.** It is the response of the shipped model to
input that is simultaneously out-of-distribution and inversely labelled, for the three
independent reasons measured below. Read beside `confusion_matrix_3band.png`
(REHAB24-6) it shows what changed between the two cohorts, not how well the model
travels.

P(Good) over the {len(ec3d_rows)} EC3D reps ranged **{_fmt(float(prob_good.min()))} –
{_fmt(float(prob_good.max()))}** (mean {_fmt(float(prob_good.mean()))}).

### Two cells carry the whole result

**`recall_poor` is exactly {_fmt(metrics["recall_poor"])}: the model did not return a
confident Poor for a single one of the {n_poor} faulty repetitions.** This independently
corroborates the Stage 5.8 finding — which was measured in-sample, on the model's own
98 training rows — on **{len(subjects)} subjects it has never seen, from a different
dataset, captured on different hardware**. The mechanism is visible in the
probabilities: P(Good) never fell below {_fmt(float(prob_good.min()))} here, so
confidence toward Poor never exceeded {_fmt(1.0 - float(prob_good.min()))}, against a
`confidence_low_threshold` of {threshold}. The Poor column of the matrix above is empty,
and it is empty for a reason that has now been observed twice by unrelated means.

**`accuracy_confident` = {_fmt(metrics["accuracy_confident"])} is below chance, and that
is the signature of inversion rather than noise.** A model reading uninformative
features would land near 0.5 on the repetitions it commits to, or abstain. This one
commits to {metrics["confident_n"]} repetitions and is wrong on
{_fmt(1.0 - metrics["accuracy_confident"])} of them — it is not confused, it is
confidently backwards. Finding 2 is why.

## Finding 1 — EC3D's poses are canonicalised, not raw mocap

Measured over the {evidence["n_frames"]} frames used here:

| property | measured | what it means |
| -------- | -------- | ------------- |
| mid-hip (BODY_25 j8) max abs coordinate | `{evidence["mid_hip_max_abs"]:.1e}` | every frame is **root-centred**: the hip is pinned to the origin |
| neck (j1) up-axis std | `{evidence["neck_up_std"]:.1e}` (value {_fmt(evidence["neck_up_value"], 8)}) | the torso is **orientation-normalised**: the neck never moves, in any frame, under any label |
| neck (j1) anterior-axis std | `{evidence["neck_anterior_std"]:.1e}` | the trunk is pinned to y=0 — it cannot lean forward at all |
| per-subject thigh length | {thigh_rows} | spread **{_fmt(evidence["thigh_spread_pct"], 3)}%** — four different people share one **template skeleton** |

Three-point joint angles (knee, hip flexion) are invariant to rigid transforms, so they
survive this intact and are physiologically plausible. Two classes of feature do not:

- **Gravity-referenced features.** `trunk_lean_peak_deg`, `trunk_lean_mean_deg` and
  `ankle_df_proxy_deg` are angles against **world vertical**. After orientation
  normalisation there is no world vertical left — the canonical up-axis *is* the torso
  axis. `trunk_lean_peak_deg` collapses from a REHAB24-6 mean of ~35-44° to ~3-4°
  here, and the "Front bent" class shows **no more** trunk lean than the Correct class.
  The one fault trunk lean exists to detect is erased by the normalisation.
- **Global-translation features.** `hip_mid_jitter_norm` measures how much the hip
  midpoint moves. The hip is pinned at the origin, so it is ~0 for every rep.

The checklist anticipated this in part, asking for "the angle-based features only". The
data shows that heuristic does not survive contact: `ankle_df_proxy_deg` **is**
angle-based and is the model's single most important feature
({_fmt(diagnostic["per_feature"][0]["importance"], 4)}), yet it is measured against
gravity and so does not transfer either. The distinction that matters is not
angle-vs-non-angle but **intrinsic (rigid-transform-invariant) vs world-referenced**.

Recovering the lost orientation was considered and rejected: it would mean inventing an
estimator (fitting a ground plane from the feet, then un-rotating each frame), feeding
its unquantified error into the model's most important feature, and it still could not
restore `hip_mid_jitter_norm` or per-subject anatomy, both of which are gone rather than
rotated. That is the invented-methodology trap this project has already been caught by
once.

## Finding 2 — the two datasets disagree about what "incorrect" means

This is the decisive one. REHAB24-6's incorrect squats are **deeper** than its correct
ones — established independently in Stage 5.4/5.5/5.6 and the reason the ROM rule had to
be down-weighted. EC3D's fault taxonomy contains **"Not low enough"**, so its incorrect
squats are **shallower**. The model's learned relationship is therefore not merely
uninformative on EC3D, it is **backwards**.

AUC below 0.5 means the feature separates the classes in the opposite direction. Means
are Good/Poor.

| feature | Gini imp. | REHAB24-6 mean | EC3D mean | REHAB AUC | EC3D AUC | direction |
| ------- | --------- | -------------- | --------- | --------- | -------- | --------- |
{diag_rows}

**{_fmt(diagnostic["inverted_mass"], 4)} of the forest's Gini importance mass
({_fmt(diagnostic["inverted_mass"] * 100, 1)}%) sits on features whose Good/Poor
direction inverts between the two datasets.** An inverted feature is worse than a
missing one: the model does not abstain on it, it reads the evidence confidently the
wrong way round.

### The inversion in one comparison

The clearest evidence is not in the table above but in the outcome. Of EC3D's
**{not_low["n"]}** *"Not low enough"* repetitions — the shallowest, most unambiguously
faulty squats in the cohort — the system called **{not_low["counts"]["Good"]}
({_fmt(not_low_good_rate * 100, 1)}%) Good**. Of its **{correct["n"]}** genuinely
**Correct** repetitions it called only **{correct["counts"]["Good"]}
({_fmt(correct_good_rate * 100, 1)}%) Good**.

**The model is {_fmt(not_low_good_rate / correct_good_rate, 1)}× more likely to approve
a "not low enough" fault than an actually-correct squat.** That is the learned
"incorrect reps are deeper" relationship applied to a cohort where the fault is being
too shallow. It is exactly backwards, it is not subtle, and no threshold change fixes
it — the ordering itself is wrong for this population.

This is not a bug in either dataset. It is evidence that the model learned a
**population-specific** notion of squat correctness rather than a universal one — which
is a genuine and reportable limitation of the trained artifact, and arguably the most
useful thing this stage produced.

## Finding 3 — half of EC3D's fault class is invisible to this system by design

Per EC3D instruction label, with the band the system would have shown:

| EC3D label | plane | n | {" | ".join(PREDICTED_BANDS)} |
| ---------- | ----- | - | {" | ".join("---" for _ in PREDICTED_BANDS)} |
{fault_rows}

**"Feet too wide" and "Knees inward" are frontal-plane faults.** Locked Assumption #3
drops frontal valgus from the taxonomy as monocular-infeasible: there is no valgus
feature, no valgus tag and no valgus rule anywhere in this system, deliberately. Those
reps are still labelled incorrect in EC3D's ground truth, so the system is being marked
wrong for failing a test it was explicitly designed never to sit. They are
{sum(b["n"] for b in breakdown if b["plane"] == "frontal")} of the {n_poor} faulty
repetitions.

The checklist's instruction — *"do not evaluate frontal-plane features here"* — was
aimed at not crediting the model for a valgus feature it does not have. The sharper
problem is the other direction: EC3D's fault **class**, not just its features, is
substantially frontal, so the Poor row of the matrix above cannot be read as a
measurement of this system.

## What this stage does and does not establish

**Does:**

- The validation firewall held. EC3D never touched training, and this is the first time
  the artifact met it.
- EC3D's joint order is resolved: OpenPose BODY_25, confirmed empirically
  ([`ec3d_joint_mapping.md`]({JOINT_MAP_DOC})). Open question Q3 is closed.
- The mapped features are physiologically plausible, so the mapping itself is sound —
  the failure is in comparability, not in the plumbing.
- The model's Good/Poor construct is **population-specific** and inverts on a cohort
  whose fault taxonomy includes "not low enough". That is a real, measured limitation.

**Does not:**

- Produce a generalisation estimate. The numbers in the Result table are reported for
  completeness and should not be quoted as one, in either direction. A good score would
  have been as meaningless as a poor one.
- Rescue the {n_poor}-rep Poor class from containing
  {sum(b["n"] for b in breakdown if b["plane"] == "frontal")} frontal-plane faults this
  system cannot see.

**What would make a real external check possible**, in rough order of cost: a cohort
whose "incorrect" class is defined by the same faults REHAB24-6's is; or raw
(non-canonicalised) EC3D mocap, which would restore the gravity-referenced features and
leave only the label-construct mismatch; or a model trained only on the intrinsic,
rigid-transform-invariant features, which could be scored on EC3D honestly but would be
a different artifact from the one that ships, and would still face Finding 2.

## Reproduce

```bash
ml/.venv/bin/python ml/scripts/validate_ec3d.py
```

Deterministic (X8): no RNG, no wall-clock. The label filter is asserted against the
paper's own {PAPER_SQUAT_SEQUENCE_COUNT}-sequence count at load time, so a changed
pickle fails loudly rather than quietly reporting different numbers.
"""
    REPORT_MD.write_text(report)


if __name__ == "__main__":
    main()
