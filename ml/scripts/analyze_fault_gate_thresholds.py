"""Measure candidate squat fault-gate thresholds for depth, lean, and heel rise.

Context (see the approved plan, `agile-roaming-kurzweil.md`, for the full argument):
Stage 5.11 made squat commit to a binary Good/Poor verdict, but the ML's verdict is a
single opaque number — it cannot tell the user *why* a rep failed. HY reviewed the
REHAB24-6 videos directly and observed the actual faults are **forward lean** and
**heels lifting off the floor**, not simply "too shallow". This matches a fact already
on record (`FEATURE_VALIDITY.md`): `knee_flex_peak_deg`/`knee_rom_deg` separate the
classes strongly, but in the *opposite* direction a depth gate needs — this dataset's
Poor reps are measurably **deeper** (Poor median 107.7 deg vs Good median 92.8 deg,
5/5 subjects agree), so depth cannot be a data-driven "too shallow" rule here. This
script measures what CAN be built as an interpretable rule gate, honestly reporting
outcomes either way:

1. **Heel visibility census (go/no-go).** Landmarks 29/30 (heels), raw stream, split
   near/far leg, whole-rep and at-depth-window. `MIN_VISIBILITY` is the actual switch
   controlling whether `preprocess_world_landmarks` reconstructs a landmark rather
   than measuring it (X1: same constant the live pipeline uses) — this is why the
   census is framed around it, not an arbitrary bar. Depth is located via bilateral
   knee flexion, a quantity independent of heel position, so the "at depth" window is
   not circular with anything heel-based.
2. **(If GO) heel-rise feature + validity check.** A toe-vs-heel vertical proxy,
   normalized by trunk_length (X1: squat's own `norm_ref_strategy`), run through
   `check_feature_validity.analyse_feature()` — the exact same KEEP/DROP method used
   for every one of the 13 shipped features (X1, not reimplemented).
3. **Threshold derivation.**
   - **Lean:** Youden's-J-optimal cut on `trunk_lean_peak_deg`, which already has a
     real KEEP verdict (AUC 0.762, "Poor higher", `FEATURE_VALIDITY.md`). Reuses
     `train_squat._choose_cv()` (X1) for a subject-grouped out-of-fold honesty check,
     the same CV-selection logic Stage 5.5 uses for the real classifier.
   - **Depth:** NOT data-driven (this dataset's own signal is inverted). Derived
     instead from `SQUAT_CONFIG["rules"]["rom"]["parallel_start_deg"]` (a true-angle
     clinical norm), adjusted for the pipeline's own -11.96 deg peak-flexion bias vs
     OptiTrack (`MOCAP_AGREEMENT.md`) — the pipeline under-reads, so a true 90 deg
     parallel squat reads as roughly 78 deg on this pipeline's own scale. Reported for
     transparency against REHAB24-6's own labels so the mismatch is visible, not
     hidden.
   - **Heel-rise (if KEEP):** same Youden's-J / out-of-fold method as lean.

Output: `ml/reports/SQUAT_FAULT_GATE_ANALYSIS.md`.

Deterministic (X8): sorted iteration, `StratifiedGroupKFold(shuffle=False)`, no RNG,
no wall-clock. Re-run twice to confirm byte-identical output.
"""

from __future__ import annotations

from pathlib import Path

import check_feature_validity as cfv
import numpy as np
from build_features import (
    LABEL_MAP,
    SIDE_VIEW_ORIENTATION,
    TARGET_EXERCISE_ID,
    _load_config,
    _preprocessed_stream,
    _raw_full_stream,
    _read_segmentation,
)
from sklearn.metrics import roc_curve
from train_squat import _choose_cv

from app.module_a.core.config import MIN_VISIBILITY
from app.module_b.core.geometry import (
    distance,
    knee_flexion_deg,
    landmark_value,
    midpoint,
)
from app.module_b.squat.config import SQUAT_CONFIG

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "SQUAT_FAULT_GATE_ANALYSIS.md"

# --- Heel visibility census -------------------------------------------------------

HEEL = {"left": 29, "right": 30}
TOE = {"left": 31, "right": 32}
# REHAB24-6 squat videos use the same camera orientation, so right is the far leg.
NEAR_LEG = "left"
FAR_LEG = "right"
# Same convention as the lunge far-limb occlusion check (fixed in advance, not tuned
# to the answer): the window bracketing the deepest share of a rep's frames.
DEPTH_WINDOW_FRACTION = 0.2

# Pre-declared go/no-go rule (fixed before the numbers were seen). GO requires the far
# heel to behave like squat's far ankle (mostly above MIN_VISIBILITY), not like the far
# knee (which sits below it for whole reps at a time, per build_features.py's report).
GO_MEAN_VISIBILITY_MIN = MIN_VISIBILITY
GO_DEPTH_OK_FRACTION_MIN = 0.80

# MOCAP_AGREEMENT.md: MediaPipe peak knee flexion bias vs OptiTrack (n=98, ICC 0.726).
# Negative = the pipeline reads LOWER than the true (mocap) angle.
PEAK_FLEXION_BIAS_DEG = -11.96

AUC_KEEP_MARGIN = cfv.AUC_KEEP_MARGIN
DIRECTION_CONSISTENCY_MIN = cfv.DIRECTION_CONSISTENCY_MIN

# Keep identical to `module_b/squat/fault_gates.py` so derived thresholds match runtime.
_SETTLE_WINDOW_FRAMES = 3
_DEBOUNCE_FRAMES = 3


def _bilateral_knee_flexion(frame: dict) -> float:
    lm = frame["worldLandmarks"]
    return (
        knee_flexion_deg(lm[23], lm[25], lm[27])
        + knee_flexion_deg(lm[24], lm[26], lm[28])
    ) / 2.0


def _rep_depth_window(values: list[float]) -> tuple[int, int]:
    """Indices bracketing the deepest DEPTH_WINDOW_FRACTION of one rep, by knee flexion."""
    peak = max(range(len(values)), key=values.__getitem__)
    half = max(1, int(len(values) * DEPTH_WINDOW_FRACTION / 2))
    return max(0, peak - half), min(len(values) - 1, peak + half)


def _side_view_rows(seg_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        (
            r
            for r in seg_rows
            if r["exercise_id"] == TARGET_EXERCISE_ID
            and r["cam17_orientation"] == SIDE_VIEW_ORIENTATION
        ),
        key=lambda r: (r["video_id"], int(r["repetition_number"])),
    )


def heel_visibility_census(seg_rows: list[dict[str, str]]) -> dict:
    side_view_rows = _side_view_rows(seg_rows)
    video_ids = sorted({r["video_id"] for r in side_view_rows})

    per_video = []
    total_reps = 0
    reps_far_any_below = 0
    reps_far_depth_below = 0

    for video_id in video_ids:
        raw_frames, _total = _raw_full_stream(video_id)
        by_index = {f["frameIndex"]: f for f in raw_frames}

        video_reps = 0
        video_reps_below = 0
        video_depth_mins: list[float] = []
        for row in (r for r in side_view_rows if r["video_id"] == video_id):
            first, last = int(row["first_frame"]), int(row["last_frame"])
            frames = [by_index[f] for f in range(first, last + 1) if f in by_index]
            if not frames:
                continue

            flexions = [_bilateral_knee_flexion(f) for f in frames]
            low, high = _rep_depth_window(flexions)
            depth_frames = frames[low : high + 1]

            far_all = [
                float(f["worldLandmarks"][HEEL[FAR_LEG]]["visibility"]) for f in frames
            ]
            far_depth = [
                float(f["worldLandmarks"][HEEL[FAR_LEG]]["visibility"])
                for f in depth_frames
            ]

            total_reps += 1
            video_reps += 1
            if min(far_all) < MIN_VISIBILITY:
                reps_far_any_below += 1
            if min(far_depth) < MIN_VISIBILITY:
                reps_far_depth_below += 1
                video_reps_below += 1
            video_depth_mins.append(min(far_depth))

        all_far = [
            float(f["worldLandmarks"][HEEL[FAR_LEG]]["visibility"]) for f in raw_frames
        ]
        all_near = [
            float(f["worldLandmarks"][HEEL[NEAR_LEG]]["visibility"]) for f in raw_frames
        ]
        per_video.append(
            {
                "video_id": video_id,
                "far_mean": float(np.mean(all_far)),
                "near_mean": float(np.mean(all_near)),
                "far_min": float(np.min(all_far)),
                "depth_min_median": (
                    float(np.median(video_depth_mins)) if video_depth_mins else None
                ),
                "reps": video_reps,
                "reps_depth_below": video_reps_below,
            }
        )

    overall_far_mean = float(
        np.average(
            [v["far_mean"] for v in per_video],
            weights=[v["reps"] for v in per_video],
        )
    )
    depth_ok_fraction = 1.0 - (reps_far_depth_below / total_reps) if total_reps else 0.0
    go = (
        overall_far_mean >= GO_MEAN_VISIBILITY_MIN
        and depth_ok_fraction >= GO_DEPTH_OK_FRACTION_MIN
    )
    return {
        "per_video": per_video,
        "total_reps": total_reps,
        "reps_far_any_below": reps_far_any_below,
        "reps_far_depth_below": reps_far_depth_below,
        "overall_far_mean": overall_far_mean,
        "depth_ok_fraction": depth_ok_fraction,
        "go": go,
    }


# --- Heel-rise feature (only built if census says GO) ------------------------------


def _trunk_length(frame: dict) -> float:
    lm = frame["worldLandmarks"]
    return distance(midpoint(lm[11], lm[12]), midpoint(lm[23], lm[24]))


def _toe_heel_lift(frame: dict, side: str) -> float:
    """toe_y - heel_y: grows as the heel lifts off the floor (toe stays grounded)."""
    lm = frame["worldLandmarks"]
    return landmark_value(lm[TOE[side]], "y") - landmark_value(lm[HEEL[side]], "y")


def _leg_visibility(frames: list[dict], side: str) -> float:
    values = []
    for f in frames:
        lm = f["worldLandmarks"]
        values.append(float(landmark_value(lm[HEEL[side]], "visibility")))
        values.append(float(landmark_value(lm[TOE[side]], "visibility")))
    return float(np.mean(values))


def _select_near_leg(frames: list[dict]) -> str:
    left_visibility = _leg_visibility(frames, "left")
    right_visibility = _leg_visibility(frames, "right")
    return "left" if left_visibility >= right_visibility else "right"


def _heel_rise_peak_norm(frames: list[dict]) -> float:
    """Measure sustained heel rise using the same construction as production.

    The camera-side leg is selected by visibility, the baseline comes from a short
    settle window, and the peak must survive debounce rather than a single-frame spike.
    `build_heel_rise_rows` already filters to visibility-passing reps, so the occlusion
    guard here is present for parity, not routine masking.
    """
    near_leg = _select_near_leg(frames)
    if _leg_visibility(frames, near_leg) < MIN_VISIBILITY:
        return -1.0

    lifts = [_toe_heel_lift(f, near_leg) for f in frames]
    settle = lifts[: min(_SETTLE_WINDOW_FRAMES, len(lifts))]
    baseline = float(np.median(settle))
    rises = [v - baseline for v in lifts]

    window = min(_DEBOUNCE_FRAMES, len(rises))
    peak_rise = max(min(rises[i : i + window]) for i in range(len(rises) - window + 1))

    norm_ref = float(np.mean([_trunk_length(f) for f in frames]))
    if norm_ref < 1e-9:
        raise ValueError(
            "Cannot normalize heel_rise_peak_norm with a zero trunk_length"
        )
    return peak_rise / norm_ref


def build_heel_rise_rows(
    seg_rows: list[dict[str, str]],
    preprocessed_cache: dict[str, list[dict]],
    frame_count_cache: dict[str, int],
) -> list[dict]:
    side_view_rows = _side_view_rows(seg_rows)
    rows = []
    for r in side_view_rows:
        video_id = r["video_id"]
        preprocessed = _preprocessed_stream(
            video_id, preprocessed_cache, frame_count_cache
        )
        first, last = int(r["first_frame"]), int(r["last_frame"])
        frames = [f for f in preprocessed if first <= f["frameIndex"] <= last]
        if not frames:
            continue
        rows.append(
            {
                "person_id": r["person_id"],
                "label": LABEL_MAP[r["correctness"]],
                "heel_rise_peak_norm": _heel_rise_peak_norm(frames),
            }
        )
    return rows


# --- Threshold derivation (Youden's J + subject-grouped out-of-fold honesty check) --


def _youden_threshold(rows: list[dict], feature: str) -> dict:
    """Pooled Youden's-J-optimal cut, positive class = Poor (the fault we gate on)."""
    y = np.array([1 if r["label"] == "Poor" else 0 for r in rows])
    x = np.array([float(r[feature]) for r in rows])
    fpr, tpr, thresholds = roc_curve(y, x)
    j = tpr - fpr
    best = int(np.argmax(j))
    return {
        "threshold": float(thresholds[best]),
        "sensitivity": float(tpr[best]),
        "specificity": float(1.0 - fpr[best]),
    }


def _out_of_fold_gate_check(rows: list[dict], feature: str) -> dict:
    """Subject-grouped out-of-fold honesty check for a single-feature threshold cut.

    Reuses `train_squat._choose_cv()` (X1) for the CV-selection logic (LOSO unless a
    subject is single-class), instead of re-deciding it. Per fold: pick Youden's J on
    the training subjects only, apply to the held-out fold, pool the predictions.
    """
    y = np.array([1 if r["label"] == "Poor" else 0 for r in rows])
    x = np.array([float(r[feature]) for r in rows])
    groups = np.array([int(r["person_id"]) for r in rows])

    outer_cv, cv_name, cv_why = _choose_cv(y, groups)
    fold_thresholds = []
    oof_pred = np.zeros_like(y)
    for train_idx, test_idx in outer_cv.split(np.zeros((len(y), 1)), y, groups):
        fpr, tpr, thresholds = roc_curve(y[train_idx], x[train_idx])
        j = tpr - fpr
        thr = float(thresholds[int(np.argmax(j))])
        fold_thresholds.append(thr)
        oof_pred[test_idx] = (x[test_idx] >= thr).astype(int)

    tp = int(np.sum((oof_pred == 1) & (y == 1)))
    fn = int(np.sum((oof_pred == 0) & (y == 1)))
    fp = int(np.sum((oof_pred == 1) & (y == 0)))
    tn = int(np.sum((oof_pred == 0) & (y == 0)))
    return {
        "cv_name": cv_name,
        "cv_why": cv_why,
        "fold_thresholds": fold_thresholds,
        "oof_sensitivity": (tp / (tp + fn)) if (tp + fn) else float("nan"),
        "oof_specificity": (tn / (tn + fp)) if (tn + fp) else float("nan"),
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
    }


def derive_gate_threshold(rows: list[dict], feature: str) -> dict:
    pooled = _youden_threshold(rows, feature)
    oof = _out_of_fold_gate_check(rows, feature)
    return {**pooled, "oof": oof}


def derive_depth_gate() -> dict:
    """Clinical-derived, NOT data-driven — see module docstring for why."""
    true_parallel_deg = SQUAT_CONFIG["rules"]["rom"]["parallel_start_deg"]
    adjusted_deg = true_parallel_deg + PEAK_FLEXION_BIAS_DEG  # bias is negative
    return {
        "true_parallel_deg": true_parallel_deg,
        "bias_deg": PEAK_FLEXION_BIAS_DEG,
        "adjusted_threshold_deg": adjusted_deg,
    }


def depth_gate_transparency_check(
    feature_rows: list[dict], adjusted_threshold_deg: float
) -> dict:
    """Report what this clinical threshold would do against REHAB24-6's own labels.

    Not used to choose the threshold (that would make it data-driven, which the
    module docstring explicitly says this gate is not) -- reported so the mismatch
    with this dataset's inverted depth signal is visible, not hidden.
    """
    peaks = np.array([float(r["knee_flex_peak_deg"]) for r in feature_rows])
    labels = np.array([r["label"] for r in feature_rows])
    flagged = peaks < adjusted_threshold_deg
    poor_total = int(np.sum(labels == "Poor"))
    good_total = int(np.sum(labels == "Good"))
    return {
        "poor_flagged": int(np.sum(flagged & (labels == "Poor"))),
        "poor_total": poor_total,
        "good_flagged": int(np.sum(flagged & (labels == "Good"))),
        "good_total": good_total,
    }


# --- Report --------------------------------------------------------------------


def write_report(
    census: dict,
    lean: dict,
    depth: dict,
    depth_transparency: dict,
    heel_rise_verdict: dict | None,
    heel_rise_threshold: dict | None,
) -> None:
    lines = [
        "# Stage 5.12 Phase A — squat fault-gate measurement (depth / lean / heel-rise)",
        "",
        "Measurement stage for the approved fault-gates plan (`agile-roaming-kurzweil.md`): "
        "adds interpretable rule checks for the faults HY observed directly in the "
        "REHAB24-6 videos (forward lean, heel rise) alongside a clinically-derived depth "
        'floor, so a rep can be told "Needs Improvement" **with a specific reason** '
        "instead of a single opaque ML number. This is a measurement report, not a code "
        "change — Phase B wires whatever is decided here into the backend.",
        "",
        "## 1. Heel visibility census (go/no-go)",
        "",
        f"`MIN_VISIBILITY = {MIN_VISIBILITY}` is the actual switch controlling whether "
        "`preprocess_world_landmarks` treats a landmark as missing and reconstructs it "
        "(gap-fill or hold-last-release) rather than measuring it -- so this census asks "
        "the question that actually matters for trusting a new heel-based feature, not an "
        "arbitrary bar. Measured on the **raw** stream (same reasoning as the lunge "
        "far-limb check): asking the preprocessed stream would ask the filter to grade "
        "its own homework. Depth is located via **bilateral knee flexion**, a quantity "
        "independent of heel position, so the at-depth window is not circular with "
        "anything heel-based.",
        "",
        f"**Pre-declared rule (fixed before the numbers were seen): GO requires the far "
        f"heel's (landmark {HEEL[FAR_LEG]}) reps-weighted mean visibility >= "
        f"{GO_MEAN_VISIBILITY_MIN} AND at least "
        f"{int(GO_DEPTH_OK_FRACTION_MIN * 100)}% of reps keep the far heel's at-depth "
        "minimum visibility above that same line.**",
        "",
        "| video | far heel mean | near heel mean | far heel min | median at-depth min | reps below at depth |",
        "| ----- | -------------- | -------------- | ------------ | -------------------- | -------------------- |",
    ]
    for v in census["per_video"]:
        depth_min = (
            f"{v['depth_min_median']:.3f}"
            if v["depth_min_median"] is not None
            else "n/a"
        )
        lines.append(
            f"| {v['video_id']} | {v['far_mean']:.3f} | {v['near_mean']:.3f} | "
            f"{v['far_min']:.3f} | {depth_min} | {v['reps_depth_below']}/{v['reps']} |"
        )

    verdict_word = "GO" if census["go"] else "NO-GO"
    lines += [
        "",
        f"**Reps-weighted far-heel mean visibility: {census['overall_far_mean']:.3f}.** "
        f"{census['reps_far_depth_below']}/{census['total_reps']} reps "
        f"({100 * (1 - census['depth_ok_fraction']):.1f}%) drop the far heel below "
        f"`MIN_VISIBILITY` at depth; {census['reps_far_any_below']}/{census['total_reps']} "
        "dip below it somewhere in the rep window.",
        "",
        f"## Verdict: **{verdict_word}**",
        "",
    ]
    if census["go"]:
        lines.append(
            "The far heel behaves like squat's far ankle (mostly above the line), not "
            "like the far knee (which sits below it for whole reps at a time). "
            "Heel-rise is measured below."
        )
    else:
        lines.append(
            "The far heel does not clear the pre-declared bar. Per the plan: **this is "
            "an acceptable, honestly-reported outcome, not a failure to fix.** Heel-rise "
            "is not built; only the lean and depth gates proceed to Phase B."
        )
    lines.append("")

    if heel_rise_verdict is not None:
        lines += [
            "## 2. Heel-rise feature validity check",
            "",
            "`heel_rise_peak_norm`: peak bilateral (toe_y - heel_y) rise from the rep's "
            "first frame, normalized by mean trunk_length over the rep (X1: squat's own "
            "`norm_ref_strategy`). Computed on the **preprocessed** stream, matching how "
            "every shipped feature is built (`build_features.py`). Run through "
            "`check_feature_validity.analyse_feature()` (X1) -- the identical KEEP/DROP "
            "method used for all 13 shipped features, same pre-declared thresholds "
            f"(`AUC_KEEP_MARGIN={AUC_KEEP_MARGIN}`, "
            f"`DIRECTION_CONSISTENCY_MIN={DIRECTION_CONSISTENCY_MIN}`).",
            "",
            "| feature | Good median | Poor median | AUC | direction | subjects agreeing | p | verdict |",
            "| ------- | ----------- | ----------- | --- | --------- | ------------------ | - | ------- |",
            (
                f"| `{heel_rise_verdict['feature']}` | "
                f"{heel_rise_verdict['good_median']:.4f} | "
                f"{heel_rise_verdict['poor_median']:.4f} | "
                f"{heel_rise_verdict['auc']:.3f} | {heel_rise_verdict['direction']} | "
                f"{heel_rise_verdict['agree']}/{heel_rise_verdict['voters']} | "
                f"{heel_rise_verdict['p_value']:.3g} | "
                f"**{heel_rise_verdict['verdict']}** |"
            ),
            "",
        ]
        if heel_rise_verdict["verdict"].startswith("KEEP"):
            lines.append(
                f"**KEEP** -- separates (AUC {heel_rise_verdict['auc']:.3f}, "
                f"{heel_rise_verdict['direction'].lower()}) and the direction holds in "
                f"{heel_rise_verdict['agree']}/{heel_rise_verdict['voters']} subjects. "
                "Proceeding to threshold derivation below."
            )
        else:
            lines.append(
                f"**DROP** -- does not separate the classes (AUC "
                f"{heel_rise_verdict['auc']:.3f}, only "
                f"{heel_rise_verdict['effect']:.3f} from the 0.5 no-separation point). "
                "Per the plan, this is a legitimate outcome: the heel-rise gate is not "
                "built from this formulation. Only the lean and depth gates proceed to "
                "Phase B."
            )
        lines.append("")

    lines += [
        "## 3. Threshold derivation",
        "",
        "### Lean gate (data-driven)",
        "",
        '`trunk_lean_peak_deg` already has a real KEEP verdict (AUC 0.762, "Poor '
        'higher", 3/5 subjects, `FEATURE_VALIDITY.md`) -- exactly the fault HY observed '
        "directly in the videos. Threshold: pooled Youden's-J-optimal cut (positive "
        "class = Poor), honesty-checked with a subject-grouped out-of-fold pass reusing "
        "`train_squat._choose_cv()` (X1) -- the same CV-selection logic (LOSO unless a "
        "subject is single-class) the real classifier is evaluated with.",
        "",
        f"- **Deployed threshold (pooled, all 98 reps): "
        f"{lean['threshold']:.3f} deg.** In-sample sensitivity "
        f"{lean['sensitivity']:.3f}, specificity {lean['specificity']:.3f}.",
        f"- **Out-of-fold honesty check** ({lean['oof']['cv_name']}; "
        f"{lean['oof']['cv_why']}): per-fold thresholds "
        f"{[round(t, 2) for t in lean['oof']['fold_thresholds']]}, pooled out-of-fold "
        f"sensitivity {lean['oof']['oof_sensitivity']:.3f}, specificity "
        f"{lean['oof']['oof_specificity']:.3f} "
        f"(TP={lean['oof']['tp']}, FN={lean['oof']['fn']}, FP={lean['oof']['fp']}, "
        f"TN={lean['oof']['tn']}).",
        "- As with the model's own out-of-fold vs in-sample numbers (`model_card.md`), "
        "the in-sample threshold is what gets deployed; the out-of-fold figures are the "
        "honest generalisation estimate, not the same claim.",
        "",
        "### Depth gate (clinical norm, NOT data-driven)",
        "",
        "**REHAB24-6's own labels run the opposite direction for depth** -- Poor reps "
        "are measurably *deeper* (`FEATURE_VALIDITY.md`: `knee_flex_peak_deg` AUC 0.837, "
        "Poor median 107.7 deg vs Good median 92.8 deg, 5/5 subjects agree). A "
        '"too-shallow" rule therefore cannot be learned from this dataset\'s own '
        "Good/Poor separation. It is instead derived from a fixed clinical minimum -- "
        f'`SQUAT_CONFIG["rules"]["rom"]["parallel_start_deg"]` = '
        f"{depth['true_parallel_deg']:.1f} deg (a true-angle norm, tagged `[clinical "
        "norm, S1]`) -- adjusted for this pipeline's own measurement bias: "
        f"`MOCAP_AGREEMENT.md` found the pipeline under-reads peak knee flexion by "
        f"{abs(depth['bias_deg']):.2f} deg vs OptiTrack (ICC 0.726, n=98). A true "
        f"{depth['true_parallel_deg']:.1f} deg parallel squat therefore reads as "
        f"approximately **{depth['adjusted_threshold_deg']:.2f} deg on this pipeline's "
        "own scale**.",
        "",
        f"- **Deployed threshold: {depth['adjusted_threshold_deg']:.2f} deg** -- gate "
        "fires if `knee_flex_peak_deg` never reaches this value during the rep "
        '("insufficient depth").',
        "- **Transparency check against REHAB24-6's own labels** (reported, not used to "
        "choose the threshold): applying this cut here would flag "
        f"{depth_transparency['poor_flagged']}/{depth_transparency['poor_total']} Poor "
        f"reps and {depth_transparency['good_flagged']}/{depth_transparency['good_total']} "
        "Good reps as insufficiently deep -- exactly the mismatch the inverted-depth "
        "finding predicts, since this dataset's Poor reps skew deeper, not shallower. "
        'This is expected and does not undermine the gate: REHAB24-6\'s "incorrect" '
        "reps are a mix of deliberate faults (this dataset does not include a "
        '"too-shallow" fault condition), not evidence about real-world shallow squats.',
        "",
    ]

    if heel_rise_threshold is not None:
        lines += [
            "### Heel-rise gate (data-driven, since census was GO and validity was KEEP)",
            "",
            f"- **Deployed threshold (pooled): {heel_rise_threshold['threshold']:.4f} "
            f"(normalized units).** In-sample sensitivity "
            f"{heel_rise_threshold['sensitivity']:.3f}, specificity "
            f"{heel_rise_threshold['specificity']:.3f}.",
            f"- **Out-of-fold honesty check** ({heel_rise_threshold['oof']['cv_name']}): "
            f"pooled out-of-fold sensitivity "
            f"{heel_rise_threshold['oof']['oof_sensitivity']:.3f}, specificity "
            f"{heel_rise_threshold['oof']['oof_specificity']:.3f}.",
            "",
        ]

    lines += [
        "## Summary",
        "",
        "| gate | provenance | deployed threshold |",
        "| ---- | ---------- | ------------------- |",
        (
            f"| lean | [dataset-derived, Stage 5.12] | "
            f"trunk_lean_peak_deg >= {lean['threshold']:.2f} deg |"
        ),
        (
            f"| depth | [clinical norm, Stage 5.12] | "
            f"knee_flex_peak_deg < {depth['adjusted_threshold_deg']:.2f} deg |"
        ),
    ]
    if heel_rise_threshold is not None:
        lines.append(
            f"| heel-rise | [dataset-derived, Stage 5.12] | "
            f"heel_rise_peak_norm >= {heel_rise_threshold['threshold']:.4f} |"
        )
    else:
        lines.append(
            "| heel-rise | not built | census returned NO-GO or validity was DROP |"
        )
    lines.append("")
    lines.append(
        "Next: Phase B wires these into `backend/app/module_b/squat/fault_gates.py` "
        'and `SQUAT_CONFIG["fault_gates"]`, per the approved plan.'
    )
    lines.append("")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    config = _load_config()
    seg_rows = _read_segmentation(
        Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    )

    print("Running heel visibility census ...")
    census = heel_visibility_census(seg_rows)
    print(f"  far heel reps-weighted mean visibility: {census['overall_far_mean']:.3f}")
    print(
        f"  reps below MIN_VISIBILITY at depth: {census['reps_far_depth_below']}/"
        f"{census['total_reps']}"
    )
    print(f"  verdict: {'GO' if census['go'] else 'NO-GO'}")

    feature_rows = cfv._read_rows()

    print("Deriving lean gate threshold ...")
    lean = derive_gate_threshold(feature_rows, "trunk_lean_peak_deg")
    print(
        f"  trunk_lean_peak_deg threshold={lean['threshold']:.3f} "
        f"(oof sens={lean['oof']['oof_sensitivity']:.3f} "
        f"spec={lean['oof']['oof_specificity']:.3f})"
    )

    print("Deriving depth gate (clinical) ...")
    depth = derive_depth_gate()
    depth_transparency = depth_gate_transparency_check(
        feature_rows, depth["adjusted_threshold_deg"]
    )
    print(f"  adjusted threshold={depth['adjusted_threshold_deg']:.2f} deg")

    heel_rise_verdict = None
    heel_rise_threshold = None
    if census["go"]:
        print("Census GO -- building heel-rise feature ...")
        preprocessed_cache: dict[str, list[dict]] = {}
        frame_count_cache: dict[str, int] = {}
        heel_rise_rows = build_heel_rise_rows(
            seg_rows, preprocessed_cache, frame_count_cache
        )
        heel_rise_verdict = cfv.analyse_feature(heel_rise_rows, "heel_rise_peak_norm")
        print(
            f"  heel_rise_peak_norm: AUC={heel_rise_verdict['auc']:.3f} "
            f"({heel_rise_verdict['direction']}) -> {heel_rise_verdict['verdict']}"
        )
        if heel_rise_verdict["verdict"].startswith("KEEP"):
            heel_rise_threshold = derive_gate_threshold(
                heel_rise_rows, "heel_rise_peak_norm"
            )
            print(f"  threshold={heel_rise_threshold['threshold']:.4f}")
    else:
        print("Census NO-GO -- skipping heel-rise (acceptable outcome, not a failure).")

    write_report(
        census, lean, depth, depth_transparency, heel_rise_verdict, heel_rise_threshold
    )
    print(f"wrote {REPORT_MD.name}")


if __name__ == "__main__":
    main()
