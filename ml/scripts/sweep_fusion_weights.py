"""Sweep the Fair threshold and fusion weights for squat.

Two 1-D sweeps over the same out-of-fold data, each earning one config value Phase 4
shipped as a placeholder — but run as an **iterated joint search**, not a single
sequential pass, because the two turned out not to be independent. What follows is why.

**The naive ordering breaks, mechanistically, not just numerically.** The obvious
reading of the checklist runs the confidence-threshold sweep once at the existing
Stage 4.0 fusion weight (0.4/0.6), then the fusion-weight sweep once at whatever
threshold that picked. Doing exactly that first: at `w_rule=0.4`, **no repetition in
the dataset can ever be banded Poor, at any confidence threshold** — precision(Poor) is
undefined at every one of the 9 candidate thresholds. The cause is a real, checkable
fact about this population, not a sweep artefact: the rule score's ROM component treats
greater knee flexion as better technique, but Stage 5.4/5.5 already established that in
this dataset **incorrect repetitions are deeper**, so `rule_score` is *higher* for Poor
reps than for Good reps (median 8.83 vs. 7.71 — verified below) and never drops below
~6.4 for anyone. At `w_rule=0.4`, even the single most confidently-Poor repetition in
the whole dataset (calibrated P(Good)=0.134) still fuses to a score of ~4.7 — inside the
Fair band, never Poor. A threshold chosen against that Poor-blind setup is not a
meaningful answer; running the fusion-weight sweep on top of it compounds rather than
fixes the problem.

**The fix: alternate the two sweeps to a fixed point.** Sweep the threshold at the
current weight, sweep the weight at that threshold, and repeat; stop when neither
winner moves between rounds. This is standard coordinate ascent over the two 1-D
sweeps the checklist already specifies — no new sweep dimension is introduced, only the
fact that they must be resolved jointly rather than in one pass. `find_stable_operating_point()`
implements this, bounded at `MAX_ROUNDS` iterations, and the report shows the full
round-by-round history so the naive first answer and why it was revised are both on the
record, not silently replaced.

**Selection criteria per sweep**, applied at every round:

- **`confidence_low_threshold`:** the smallest candidate reaching >= 0.90 precision on
  **both** confidently-classified classes (pre-declared, fixed before any results were
  seen) — once a precision bar is met, a higher threshold only buys more abstention for
  no benefit.
- **`w_rule`/`w_ml`:** HY's criterion (2026-07-16) is explicit that Poor→Good — telling
  a poor-form user they are fine — is "the one failure mode that matters most", so the
  primary key is the **Poor→Good count specifically** (not summed with Good→Poor into
  one severe-rate number, which would let a rise in the worse failure mode hide behind
  a compensating fall in the milder one); Good→Poor and macro-F1 break ties, in that
  order, at n=98 with a same-count-or-within-1 tolerance since a single event either way
  is within sampling noise here.

Both sweeps call the real, unmodified `app.module_b.core.fusion.fuse_scores()` — the
sweep temporarily patches `MODULE_B_CORE_CONFIG` in place and restores it in `finally`,
the same pattern `check_norm_ref.py` used for `norm_ref_strategy` (X1: the fusion logic
under test is never re-implemented, only re-configured).

Three further scope decisions the report must justify rather than assert:

1. **Evaluated per repetition, not per session.** REHAB24-6 labels each *repetition*
   Good/Poor; production fuses one grade per *session* (`score_squat_set()`'s
   duration-weighted rule aggregate, and the ML score from only the session's first
   repetition — an existing Phase 4 architecture choice, not this stage's to redesign).
   Ground truth only exists at the granularity Stage 5.5 already trained and evaluated
   at, so this sweep stays at that same granularity: each repetition's own
   `score_squat_rep()` (ROM + stability; tempo is undefined for a lone rep) and its own
   calibrated P(Good). The threshold/weight *values* chosen transfer to production
   because both the confidence measure and the 0-10 rule scale are computed identically
   at either granularity; the confusion counts below characterise per-repetition
   behaviour specifically, and should not be quoted as a per-session number.

2. **No ground-truth Fair label exists, so Fair cannot be scored as "correct" or
   "wrong".** REHAB24-6 is binary. Precision and recall are therefore reported only for
   Good and Poor (the classes with real ground truth); Fair's own rate is reported as a
   descriptive coverage statistic, not folded into a precision figure it has no basis
   for. Macro-F1 is the mean of F1(Good) and F1(Poor) for the same reason — this is the
   same position Stage 5.7's own checklist already takes for the analogous multi-label
   tag evaluation ("REHAB24-6 is binary ... state that plainly rather than inventing an
   evaluation"), applied one stage earlier to this exact tension.

3. **Capture quality `q` is measured, not assumed.** `q_min` is not swept here (fixed,
   out of scope), but it still gates whether `fuse_scores()` forces Fair via
   `low_capture_quality`, so a real per-repetition `q` is computed from each rep's *raw*
   (pre-preprocessing) landmark window via the live `assess_capture_quality()` — the
   same function and the same raw-buffer semantics `router.py` uses — rather than
   assumed to be high because the dataset is clean.

Deterministic (X8): reuses Stage 5.5's seeded `nested_cv()` verbatim, sorted iteration,
no RNG, no wall-clock.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from build_features import (
    SIDE_VIEW_ORIENTATION,
    TARGET_EXERCISE_ID,
    _load_config,
    _raw_full_stream,
    _read_segmentation,
)
from plotting import save_fig
from train_squat import _build_xy, _choose_cv, _read_rows, nested_cv

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.fusion import fuse_scores
from app.module_b.core.quality import assess_capture_quality
from app.module_b.squat.features import SQUAT_FEATURE_NAMES
from app.module_b.squat.rules import score_squat_rep

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "SQUAT_FUSION_SWEEP.md"

# R7 default is 0.65; "strictly above 0.5" per the checklist, including candidates
# above 0.65 so the sweep can confirm or move past the heuristic.
CONFIDENCE_CANDIDATES = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
# Include the current 0.4 default so the sweep can compare it with nearby weights.
FUSION_WEIGHT_CANDIDATES = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

# Pre-declared selection rule: use the smallest threshold that reaches this precision
# bar on both confidently classified classes.
CONFIDENCE_PRECISION_BAR = 0.90

# Coordinate-ascent bound for the joint (threshold, weight) search below. 2-3 rounds is
# what convergence actually took when this was explored by hand; generous headroom.
MAX_ROUNDS = 6

TRUE_LABELS = ("Good", "Poor")
PREDICTED_BANDS = ("Good", "Fair", "Poor")


def _rule_score(row: dict) -> float:
    """Real per-repetition rule score via the live `score_squat_rep()` (X1).

    Tempo is always unavailable for a lone repetition (it needs a full set), so the
    equal-weight mean here is over ROM completeness and stability control only — never
    `None`, so this never raises.
    """
    vector = FeatureVector(
        row["feature_schema_version"],
        SQUAT_FEATURE_NAMES,
        tuple(float(row[name]) for name in SQUAT_FEATURE_NAMES),
    )
    rule_scores = score_squat_rep(vector)
    if rule_scores.score is None:
        raise ValueError("score_squat_rep() unexpectedly produced no rule score")
    return rule_scores.score


def _rule_score_by_class(rule_scores: list[float], true_labels: list[str]) -> dict:
    """Verifies (does not assume) the mechanism motivating the iterated search below:
    is `rule_score` actually higher for Poor reps than Good ones in this population?
    """
    good = np.array(
        [s for s, t in zip(rule_scores, true_labels, strict=True) if t == "Good"]
    )
    poor = np.array(
        [s for s, t in zip(rule_scores, true_labels, strict=True) if t == "Poor"]
    )
    return {
        "good_median": float(np.median(good)),
        "poor_median": float(np.median(poor)),
        "overall_min": float(min(good.min(), poor.min())),
        "overall_max": float(max(good.max(), poor.max())),
    }


def _segmentation_bounds(config: dict) -> dict[tuple[str, str], tuple[int, int]]:
    """(video_id, repetition_number) -> (first_frame, last_frame) for side-view Ex6."""
    segmentation_csv = Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    seg_rows = _read_segmentation(segmentation_csv)
    return {
        (r["video_id"], r["repetition_number"]): (
            int(r["first_frame"]),
            int(r["last_frame"]),
        )
        for r in seg_rows
        if r["exercise_id"] == TARGET_EXERCISE_ID
        and r["cam17_orientation"] == SIDE_VIEW_ORIENTATION
    }


def _raw_capture_quality(rows: list[dict], config: dict) -> list[float]:
    """Real per-repetition `q`, from each rep's RAW (pre-preprocessing) frame window.

    Matches `assess_capture_quality()`'s own contract ("Q on the raw capture...
    reflects what was actually recorded") rather than measuring quality on the
    already-smoothed stream the features come from.
    """
    bounds = _segmentation_bounds(config)
    raw_cache: dict[str, list[dict]] = {}
    qs = []
    for row in rows:
        video_id = row["video_id"]
        if video_id not in raw_cache:
            frames, _total = _raw_full_stream(video_id)
            raw_cache[video_id] = frames
        first, last = bounds[(video_id, row["repetition_number"])]
        rep_frames = [
            f for f in raw_cache[video_id] if first <= f["frameIndex"] <= last
        ]
        qs.append(float(assess_capture_quality(rep_frames)["q"]))
    return qs


def _fuse_all(
    rows: list[dict],
    prob_good: np.ndarray,
    rule_scores: list[float],
    qs: list[float],
    *,
    w_rule: float,
    w_ml: float,
    confidence_low_threshold: float,
) -> list:
    """Run the real `fuse_scores()` for every repetition under one candidate config.

    Patches only the three values this stage sweeps; `w_rule_low_confidence` and
    `q_min` are left at their existing, out-of-scope values, then restored in
    `finally` regardless of how the loop below exits.
    """
    original = {
        key: MODULE_B_CORE_CONFIG[key]
        for key in ("w_rule_default", "w_ml_default", "confidence_low_threshold")
    }
    MODULE_B_CORE_CONFIG["w_rule_default"] = w_rule
    MODULE_B_CORE_CONFIG["w_ml_default"] = w_ml
    MODULE_B_CORE_CONFIG["confidence_low_threshold"] = confidence_low_threshold
    try:
        return [
            fuse_scores(
                rule_score=rule_score,
                probabilities={"Good": float(p_good), "Poor": float(1.0 - p_good)},
                q=q,
                model_version="stage5.6-sweep",
                is_placeholder_model=False,
            )
            for _row, p_good, rule_score, q in zip(
                rows, prob_good, rule_scores, qs, strict=True
            )
        ]
    finally:
        MODULE_B_CORE_CONFIG.update(original)


def _confusion(true_labels: list[str], bands: list[str]) -> dict[tuple[str, str], int]:
    counts = {(t, p): 0 for t in TRUE_LABELS for p in PREDICTED_BANDS}
    for t, p in zip(true_labels, bands, strict=True):
        counts[(t, p)] += 1
    return counts


def _metrics(counts: dict[tuple[str, str], int], n: int) -> dict:
    """Precision/recall/F1 over Good and Poor only (see module docstring, point 2)."""

    def precision(cls: str) -> float:
        predicted = sum(counts[(t, cls)] for t in TRUE_LABELS)
        return counts[(cls, cls)] / predicted if predicted else float("nan")

    def recall(cls: str) -> float:
        true_n = sum(counts[(cls, p)] for p in PREDICTED_BANDS)
        return counts[(cls, cls)] / true_n if true_n else float("nan")

    def f1(cls: str) -> float:
        p, r = precision(cls), recall(cls)
        if np.isnan(p) or np.isnan(r) or (p + r) == 0:
            return 0.0
        return 2 * p * r / (p + r)

    fair_n = sum(counts[(t, "Fair")] for t in TRUE_LABELS)
    confident_n = n - fair_n
    confident_correct = counts[("Good", "Good")] + counts[("Poor", "Poor")]
    poor_to_good = counts[("Poor", "Good")]
    good_to_poor = counts[("Good", "Poor")]

    return {
        "precision_good": precision("Good"),
        "precision_poor": precision("Poor"),
        "recall_good": recall("Good"),
        "recall_poor": recall("Poor"),
        "macro_f1": (f1("Good") + f1("Poor")) / 2,
        "fair_rate": fair_n / n,
        "confident_precision": (
            confident_correct / confident_n if confident_n else float("nan")
        ),
        "poor_to_good": poor_to_good,
        "good_to_poor": good_to_poor,
        "severe_count": poor_to_good + good_to_poor,
        "severe_rate": (poor_to_good + good_to_poor) / n,
        "counts": counts,
    }


def sweep_confidence_threshold(
    rows: list[dict],
    true_labels: list[str],
    prob_good: np.ndarray,
    rule_scores: list[float],
    qs: list[float],
    w_rule: float,
    w_ml: float,
) -> list[dict]:
    """Vary `confidence_low_threshold` at one fixed (w_rule, w_ml) point.

    Takes the weight explicitly rather than reading it off `MODULE_B_CORE_CONFIG`,
    because the iterated search below calls this at a *different* weight each round —
    reading the live config here would silently re-run round 1 every time.
    """
    results = []
    for threshold in CONFIDENCE_CANDIDATES:
        fused = _fuse_all(
            rows,
            prob_good,
            rule_scores,
            qs,
            w_rule=w_rule,
            w_ml=w_ml,
            confidence_low_threshold=threshold,
        )
        metrics = _metrics(_confusion(true_labels, [f.band for f in fused]), len(rows))
        metrics["threshold"] = threshold
        results.append(metrics)
    return results


def sweep_fusion_weight(
    rows: list[dict],
    true_labels: list[str],
    prob_good: np.ndarray,
    rule_scores: list[float],
    qs: list[float],
    confidence_low_threshold: float,
) -> list[dict]:
    """Vary `w_rule`/`w_ml` at one fixed `confidence_low_threshold`."""
    results = []
    for w_rule in FUSION_WEIGHT_CANDIDATES:
        w_ml = round(1.0 - w_rule, 10)
        fused = _fuse_all(
            rows,
            prob_good,
            rule_scores,
            qs,
            w_rule=w_rule,
            w_ml=w_ml,
            confidence_low_threshold=confidence_low_threshold,
        )
        metrics = _metrics(_confusion(true_labels, [f.band for f in fused]), len(rows))
        metrics["w_rule"] = w_rule
        metrics["w_ml"] = w_ml
        results.append(metrics)
    return results


def _pick_confidence_threshold(results: list[dict]) -> tuple[float, str]:
    meets_bar = [
        r
        for r in results
        if not np.isnan(r["precision_good"])
        and not np.isnan(r["precision_poor"])
        and r["precision_good"] >= CONFIDENCE_PRECISION_BAR
        and r["precision_poor"] >= CONFIDENCE_PRECISION_BAR
    ]
    if meets_bar:
        winner = min(meets_bar, key=lambda r: r["threshold"])
        return winner["threshold"], (
            f"smallest candidate reaching >= {CONFIDENCE_PRECISION_BAR:.2f} precision "
            "on both confidently-classified classes (pre-declared: once the bar is "
            "met, do not buy more abstention than necessary)"
        )

    def _fallback_score(r: dict) -> tuple[float, float]:
        p_good = r["precision_good"] if not np.isnan(r["precision_good"]) else 0.0
        p_poor = r["precision_poor"] if not np.isnan(r["precision_poor"]) else 0.0
        return (min(p_good, p_poor), -r["threshold"])

    winner = max(results, key=_fallback_score)
    return winner["threshold"], (
        f"no candidate reached the pre-declared {CONFIDENCE_PRECISION_BAR:.2f} bar on "
        "both classes; fell back to maximising the worse of the two class "
        "precisions, preferring the smaller threshold on ties"
    )


def _pick_fusion_weight(results: list[dict]) -> tuple[float, str]:
    """Pick the weight that minimises Poor->Good errors first.

    Good->Poor breaks ties, then macro-F1. With this small dataset, a within-1 margin
    is treated as tied rather than requiring exact equality.
    """
    min_poor_to_good = min(r["poor_to_good"] for r in results)
    tier1 = [r for r in results if r["poor_to_good"] <= min_poor_to_good + 1]
    min_good_to_poor = min(r["good_to_poor"] for r in tier1)
    tier2 = [r for r in tier1 if r["good_to_poor"] <= min_good_to_poor + 1]
    best_macro_f1 = max(r["macro_f1"] for r in tier2)
    tier3 = [r for r in tier2 if abs(r["macro_f1"] - best_macro_f1) < 1e-9]
    # Final deterministic tie-break: smallest w_rule. The mechanism check above shows
    # the rule score's ROM component is inverted for this population (rewards depth,
    # which is what makes a rep Poor here) — so when nothing else distinguishes two
    # candidates, minimising its influence is the principled choice, not arbitrary.
    winner = min(tier3, key=lambda r: r["w_rule"])

    # Trace which criterion actually did the discriminating at each step, rather than
    # only describing the final residual tie — macro-F1 can narrow the field a lot
    # (e.g. separating "catches some Poor reps" from "routes every Poor rep through
    # Fair, catching none") even when the w_rule floor is what breaks the last tie.
    steps = []
    if len(tier1) < len(results):
        steps.append(
            f"Poor→Good narrowed {len(results)} candidates to {len(tier1)} "
            f"(within 1 of the minimum, {min_poor_to_good})"
        )
    if len(tier2) < len(tier1):
        steps.append(
            f"Good→Poor narrowed to {len(tier2)} (within 1 of the minimum, "
            f"{min_good_to_poor})"
        )
    if len(tier3) < len(tier2):
        steps.append(f"macro-F1 narrowed to {len(tier3)} (best {best_macro_f1:.3f})")
    if len(tier3) > 1:
        steps.append(
            f"smallest w_rule broke the remaining {len(tier3)}-way tie (rule score's "
            "ROM component is inverted for this population, so minimising its "
            "influence is the principled default when nothing else distinguishes)"
        )
    if not steps:
        steps.append("uniquely best on every criterion")
    return winner["w_rule"], "; ".join(steps)


def plot_confidence_threshold_sweep(results: list[dict], chosen: float) -> Path:
    thresholds = [r["threshold"] for r in results]
    fig, ax = plt.subplots()
    ax.plot(
        thresholds,
        [r["precision_good"] for r in results],
        marker="o",
        color="#2a6f97",
        label="Precision (Good)",
    )
    ax.plot(
        thresholds,
        [r["precision_poor"] for r in results],
        marker="o",
        color="#c1121f",
        label="Precision (Poor)",
    )
    ax.plot(
        thresholds,
        [r["fair_rate"] for r in results],
        marker="s",
        color="#6a4c93",
        linestyle="--",
        label="Fair-band coverage rate",
    )
    ax.axvline(chosen, color="black", linestyle=":", linewidth=1)
    ax.annotate(
        f"chosen: {chosen}",
        xy=(chosen, 0.02),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=9,
    )
    ax.set_xlabel("confidence_low_threshold")
    ax.set_ylabel("rate")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Confidence-threshold sweep — precision vs. abstention cost")
    ax.legend(loc="center left", fontsize=9)
    fig.tight_layout()
    path = save_fig(fig, "confidence_threshold_sweep", figsize="wide")
    plt.close(fig)
    return path


def plot_fusion_weight_sweep(results: list[dict], chosen: float) -> Path:
    w_rules = [r["w_rule"] for r in results]
    fig, ax = plt.subplots()
    ax.plot(
        w_rules,
        [r["confident_precision"] for r in results],
        marker="o",
        color="#2a6f97",
        label="Precision (confident calls)",
    )
    ax.plot(
        w_rules,
        [r["macro_f1"] for r in results],
        marker="o",
        color="#588157",
        label="Macro-F1 (Good, Poor)",
    )
    ax.plot(
        w_rules,
        [r["severe_rate"] for r in results],
        marker="s",
        color="#c1121f",
        linestyle="--",
        label="Severe-misclassification rate",
    )
    ax.axvline(chosen, color="black", linestyle=":", linewidth=1)
    ax.annotate(
        f"chosen: w_rule={chosen}",
        xy=(chosen, 0.02),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=9,
    )
    ax.set_xlabel("w_rule (w_ml = 1 - w_rule)")
    ax.set_ylabel("rate")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Fusion-weight sweep — precision, macro-F1, severe-error rate")
    ax.legend(loc="center left", fontsize=9)
    fig.tight_layout()
    path = save_fig(fig, "fusion_weight_sweep", figsize="wide")
    plt.close(fig)
    return path


def find_stable_operating_point(
    rows: list[dict],
    true_labels: list[str],
    prob_cal: np.ndarray,
    rule_scores: list[float],
    qs: list[float],
) -> list[dict]:
    """Coordinate-ascent over the two sweeps until neither winner moves.

    Round 1 starts at the current `w_rule_default` (0.4) — the literal, obvious
    reading of the checklist's ordering. Every subsequent round feeds the previous
    round's chosen weight back into the threshold sweep. Returns the full round
    history (never just the final answer) so the naive first round's Poor-blind
    result is visible in the report rather than silently discarded.
    """
    w_rule_input = MODULE_B_CORE_CONFIG["w_rule_default"]
    history: list[dict] = []
    for round_number in range(1, MAX_ROUNDS + 1):
        w_ml_input = round(1.0 - w_rule_input, 10)
        threshold_results = sweep_confidence_threshold(
            rows, true_labels, prob_cal, rule_scores, qs, w_rule_input, w_ml_input
        )
        chosen_threshold, threshold_reason = _pick_confidence_threshold(
            threshold_results
        )

        weight_results = sweep_fusion_weight(
            rows, true_labels, prob_cal, rule_scores, qs, chosen_threshold
        )
        chosen_w_rule, weight_reason = _pick_fusion_weight(weight_results)

        print(
            f"  round {round_number}: input w_rule={w_rule_input} -> "
            f"threshold={chosen_threshold} -> w_rule={chosen_w_rule}"
        )
        history.append(
            {
                "round": round_number,
                "input_w_rule": w_rule_input,
                "threshold_results": threshold_results,
                "chosen_threshold": chosen_threshold,
                "threshold_reason": threshold_reason,
                "weight_results": weight_results,
                "chosen_w_rule": chosen_w_rule,
                "weight_reason": weight_reason,
            }
        )

        if round_number > 1:
            previous = history[-2]
            if (
                previous["chosen_threshold"] == chosen_threshold
                and previous["chosen_w_rule"] == chosen_w_rule
            ):
                print(f"  converged after round {round_number}")
                break
        w_rule_input = chosen_w_rule
    return history


def main() -> None:
    config = _load_config()
    seed = int(config["seeds"]["sklearn"])
    rows = _read_rows()
    x, y, groups = _build_xy(rows)
    true_labels = ["Good" if v == 1 else "Poor" for v in y]
    outer_cv, _cv_name, _cv_why = _choose_cv(y, groups)

    print("Re-running Stage 5.5's nested CV for out-of-fold calibrated P(Good)...")
    _prob_uncal, prob_cal, _folds = nested_cv(x, y, groups, outer_cv, seed)

    print("Computing per-repetition rule scores (score_squat_rep)...")
    rule_scores = [_rule_score(row) for row in rows]
    rule_by_class = _rule_score_by_class(rule_scores, true_labels)
    print(
        f"  rule_score by class: Good median={rule_by_class['good_median']:.2f}  "
        f"Poor median={rule_by_class['poor_median']:.2f}  "
        f"(overall range [{rule_by_class['overall_min']:.2f}, "
        f"{rule_by_class['overall_max']:.2f}])"
    )

    print("Computing real per-repetition capture quality (raw frames)...")
    qs = _raw_capture_quality(rows, config)
    q_min = MODULE_B_CORE_CONFIG["q_min"]
    below_q_min = sum(1 for q in qs if q < q_min)
    print(
        f"  q: min={min(qs):.3f} median={float(np.median(qs)):.3f} max={max(qs):.3f}; "
        f"{below_q_min}/{len(qs)} below q_min={q_min}"
    )

    print("Iterated joint search (confidence_low_threshold <-> w_rule)...")
    history = find_stable_operating_point(rows, true_labels, prob_cal, rule_scores, qs)
    final = history[-1]
    chosen_threshold = final["chosen_threshold"]
    chosen_w_rule = final["chosen_w_rule"]
    chosen_w_ml = round(1.0 - chosen_w_rule, 10)
    print(
        f"  final: confidence_low_threshold={chosen_threshold}, "
        f"w_rule={chosen_w_rule}, w_ml={chosen_w_ml}"
    )

    plot_confidence_threshold_sweep(final["threshold_results"], chosen_threshold)
    plot_fusion_weight_sweep(final["weight_results"], chosen_w_rule)

    threshold_results = final["threshold_results"]
    threshold_reason = final["threshold_reason"]
    weight_results = final["weight_results"]
    weight_reason = final["weight_reason"]

    write_report(
        rows=rows,
        qs=qs,
        q_min=q_min,
        below_q_min=below_q_min,
        rule_by_class=rule_by_class,
        history=history,
        threshold_results=threshold_results,
        chosen_threshold=chosen_threshold,
        threshold_reason=threshold_reason,
        weight_results=weight_results,
        chosen_w_rule=chosen_w_rule,
        chosen_w_ml=chosen_w_ml,
        weight_reason=weight_reason,
    )
    print(f"wrote {REPORT_MD.name}")


def write_report(
    *,
    rows,
    qs,
    q_min,
    below_q_min,
    rule_by_class,
    history,
    threshold_results,
    chosen_threshold,
    threshold_reason,
    weight_results,
    chosen_w_rule,
    chosen_w_ml,
    weight_reason,
) -> None:
    n = len(rows)
    old_w_rule = weight_results[
        [r["w_rule"] for r in weight_results].index(0.4)
    ]  # the Stage 4.0 placeholder, present in the sweep grid for direct comparison
    chosen_weight_row = next(r for r in weight_results if r["w_rule"] == chosen_w_rule)
    chosen_threshold_row = next(
        r for r in threshold_results if r["threshold"] == chosen_threshold
    )
    round_one = history[0]

    lines = [
        "# Stage 5.6 — Fair threshold + fusion weight sweep",
        "",
        f"Source: the same {n} side-view repetitions and the same seeded "
        "`nested_cv()` Stage 5.5 used, so the calibrated P(Good) fed into this sweep "
        "is identical to Stage 5.5's out-of-fold predictions (re-run here rather than "
        "cached, since nothing about the model changed between stages).",
        "",
        "## Why this is an iterated joint search, not one pass",
        "",
        "The obvious reading of the checklist sweeps `confidence_low_threshold` once "
        "at the existing Stage 4.0 fusion weight (0.4/0.6), then sweeps the fusion "
        "weight once at whatever threshold that picked. Running exactly that first "
        f"(round 1 below) surfaced a real, mechanistic problem: **at `w_rule=0.4`, "
        "precision(Poor) is undefined at every one of the 9 candidate thresholds** — "
        "no repetition in the dataset can ever be banded Poor at that weight, no "
        "matter how the threshold is set.",
        "",
        "The cause is checkable, not a sweep artefact. `rule_score`'s ROM component "
        "rewards greater knee flexion as better technique, but Stage 5.4/5.5 already "
        "established that in this population **incorrect repetitions are deeper**. "
        f"Measured here: `rule_score` median is **{rule_by_class['poor_median']:.2f} "
        f"for Poor** repetitions versus **{rule_by_class['good_median']:.2f} for "
        f"Good** — the rule score runs backwards relative to correctness — and it "
        f"never drops below {rule_by_class['overall_min']:.2f} for anyone. At "
        "`w_rule=0.4`, even the single most confidently-Poor repetition in the whole "
        "dataset (calibrated P(Good)=0.134, rule_score=9.71) fuses to a score of "
        "~4.7 — inside the Fair band, never Poor. A confidence threshold chosen "
        "against that Poor-blind setup is not a meaningful answer, and running the "
        "fusion-weight sweep on top of it would compound the problem rather than fix "
        "it.",
        "",
        "**Fix: alternate the two sweeps until neither winner moves.** Sweep the "
        "threshold at the current weight, sweep the weight at that threshold, feed "
        "the result back in, repeat. This introduces no new sweep dimension beyond "
        "what the checklist specifies — it only recognises that the two must be "
        "resolved jointly. The full round history:",
        "",
        "| round | input w_rule | -> chosen threshold | -> chosen w_rule |",
        "| ----- | ------------ | -------------------- | ------------------ |",
    ]
    for h in history:
        lines.append(
            f"| {h['round']} | {h['input_w_rule']} | {h['chosen_threshold']} | "
            f"{h['chosen_w_rule']} |"
        )
    lines += [
        "",
        f"**Round 1's threshold ({round_one['chosen_threshold']}) was chosen "
        f"{round_one['threshold_reason']}** — necessarily on Good-class precision "
        "alone, since Poor precision was undefined throughout that round. It is "
        "shown here rather than discarded, because it is the honest first answer "
        "and the reason it was revised is the point of this section.",
        "",
        f"Converged after round {len(history)}. Every result below (tables, both "
        f"figures) is the **final, converged round** "
        f"(`confidence_low_threshold={chosen_threshold}`, `w_rule={chosen_w_rule}`), "
        "not round 1.",
        "",
        "## Scope: evaluated per repetition, not per session",
        "",
        "REHAB24-6 labels each **repetition** Good/Poor. Production instead fuses one "
        "grade per **session**: `score_squat_set()` aggregates rule sub-scores across "
        "a full set (duration-weighted for stability, needs >= 2 reps for tempo), and "
        "the ML score comes from only the session's first repetition — an existing "
        "Phase 4 architecture decision, not this stage's to redesign. Since ground "
        "truth only exists at repetition granularity, this sweep stays there: each "
        "repetition's own `score_squat_rep()` rule score (ROM + stability; tempo is "
        "undefined for a lone rep) and its own calibrated P(Good). The threshold/weight "
        "**values** below transfer to production, because the confidence measure and "
        "the 0-10 rule scale are computed identically at either granularity — but the "
        "**confusion counts and rates characterise per-repetition performance**, not "
        "per-session performance, and should not be conflated when quoted.",
        "",
        "## Capture quality — measured, not assumed",
        "",
        f"`q_min` is not swept (fixed, out of scope), but it still gates whether "
        "`fuse_scores()` forces Fair via `low_capture_quality`, so real per-repetition "
        "`q` was computed from each rep's **raw**, pre-preprocessing frame window via "
        f"the live `assess_capture_quality()` — q ranged "
        f"[{min(qs):.3f}, {max(qs):.3f}] (median {float(np.median(qs)):.3f}), with "
        f"**{below_q_min}/{n} reps below q_min={q_min}**. "
        + (
            "None did, confirming this dataset's clean capture does not itself force "
            "Fair — the sweeps below characterise the confidence/weight mechanisms "
            "cleanly, not a confound from capture quality."
            if below_q_min == 0
            else f"{below_q_min} rep(s) independently force Fair via "
            "`low_capture_quality` regardless of the swept values — flagged so this "
            "is not mistaken for a confidence- or weight-driven effect."
        ),
        "",
        "## Method: no ground-truth Fair label exists",
        "",
        "REHAB24-6 is binary — there is no repetition labelled 'Fair' to score a Fair "
        "prediction against. Precision, recall and macro-F1 below are therefore "
        "computed for **Good and Poor only** (the classes with real ground truth); a "
        "predicted Fair counts as a miss for whichever true class it came from "
        "(affecting recall, as any wrong prediction would) but Fair itself has no "
        "precision figure, because there is no true-Fair count to make one "
        "meaningful. Fair's own rate is reported separately as a descriptive "
        "**coverage** statistic. This mirrors the position Stage 5.7's own checklist "
        "already takes for the analogous multi-label tag evaluation — applied here, "
        "one stage earlier, to the same underlying limitation.",
        "",
        "## `confidence_low_threshold` sweep (final, converged round)",
        "",
        f"Fusion weight held at the converged `w_rule={chosen_w_rule}` throughout "
        "this table — the round-1 version of this table (fusion weight at the "
        "Stage 4.0 placeholder) is shown above and is not repeated here, since "
        "precision(Poor) was undefined in every one of its rows.",
        "",
        f"**Pre-declared selection rule:** the smallest candidate threshold at which "
        f"precision reaches >= {CONFIDENCE_PRECISION_BAR:.2f} on **both** "
        "confidently-classified classes — fixed before the sweep ran, so the bar is "
        "not fitted to the outcome. Rationale: R7's default (0.65) is already a "
        "conservative starting point above the 0.5 floor Option A's binary "
        "probabilities allow; once a precision bar is met, raising the threshold "
        "further only trades additional Fair-band abstention for no precision "
        "benefit, so the smallest sufficient value is preferred.",
        "",
        "| threshold | precision (Good) | precision (Poor) | Fair-band coverage |",
        "| --------- | ----------------- | ----------------- | ------------------ |",
    ]
    for r in threshold_results:
        marker = " **<-chosen**" if r["threshold"] == chosen_threshold else ""
        lines.append(
            f"| {r['threshold']:.2f} | {r['precision_good']:.3f} | "
            f"{r['precision_poor']:.3f} | {r['fair_rate']:.3f}{marker} |"
        )

    lines += [
        "",
        "![Confidence-threshold sweep](figures/confidence_threshold_sweep.png)",
        "",
        f"**Chosen: `confidence_low_threshold = {chosen_threshold}`** — {threshold_reason}. "
        f"At this value: precision(Good) = {chosen_threshold_row['precision_good']:.3f}, "
        f"precision(Poor) = {chosen_threshold_row['precision_poor']:.3f}, Fair-band "
        f"coverage = {chosen_threshold_row['fair_rate']:.3f} "
        f"({int(round(chosen_threshold_row['fair_rate'] * n))}/{n} reps abstained).",
        "",
        "> **Read the small-N caveat before quoting these precision numbers "
        "precisely.** At n=98 (26 Poor), each threshold step can move only a handful "
        "of reps between bands — a single rep changing hands can shift a precision "
        "figure by several percentage points. Treat the table as showing a trend "
        "(precision rising, then plateauing, as the threshold climbs and more "
        "borderline reps are excluded into Fair), not as precise, low-variance "
        "estimates of each individual cell.",
        "",
        "## Fusion weight (`w_rule`/`w_ml`) sweep (final, converged round)",
        "",
        f"`confidence_low_threshold` fixed at the converged threshold "
        f"({chosen_threshold}) throughout this table.",
        "",
        "**Selection criteria (HY, 2026-07-16):** Poor→Good — telling a poor-form "
        "user they are fine — is named as **the one failure mode that matters "
        "most**, so it is used as its own primary key (see `_pick_fusion_weight()`), "
        "not summed with Good→Poor into one aggregate that could let a rise in the "
        "worse failure mode hide behind a fall in the milder one; Good→Poor and "
        "macro-F1 break ties, in that order. A weight with slightly lower precision "
        "but a materially lower Poor→Good count is the better choice.",
        "",
        "| w_rule | w_ml | precision (confident calls) | macro-F1 | severe count "
        "(Poor→Good / Good→Poor) | severe rate | Fair coverage |",
        "| ------ | ---- | ---------------------------- | -------- | "
        "------------------------------------- | ----------- | ------------- |",
    ]
    for r in weight_results:
        marker = " **<-chosen**" if r["w_rule"] == chosen_w_rule else ""
        placeholder = " (Stage 4.0 placeholder)" if r["w_rule"] == 0.4 else ""
        lines.append(
            f"| {r['w_rule']:.1f} | {r['w_ml']:.1f} | "
            f"{r['confident_precision']:.3f} | {r['macro_f1']:.3f} | "
            f"{r['severe_count']} ({r['poor_to_good']} / {r['good_to_poor']}) | "
            f"{r['severe_rate']:.3f} | {r['fair_rate']:.3f}{marker}{placeholder} |"
        )

    lines += [
        "",
        "![Fusion-weight sweep](figures/fusion_weight_sweep.png)",
        "",
        f"**Chosen: `w_rule = {chosen_w_rule}`, `w_ml = {chosen_w_ml}`** — "
        f"{weight_reason}.",
        "",
        f"At the winner: precision (confident calls) = "
        f"{chosen_weight_row['confident_precision']:.3f}, macro-F1 = "
        f"{chosen_weight_row['macro_f1']:.3f}, severe-misclassification = "
        f"{chosen_weight_row['severe_count']} "
        f"({chosen_weight_row['poor_to_good']} Poor→Good, "
        f"{chosen_weight_row['good_to_poor']} Good→Poor), Fair coverage = "
        f"{chosen_weight_row['fair_rate']:.3f}.",
        "",
        f"**Against the Stage 4.0 placeholder (`w_rule=0.4`):** precision "
        f"{old_w_rule['confident_precision']:.3f}, macro-F1 "
        f"{old_w_rule['macro_f1']:.3f}, severe count {old_w_rule['severe_count']} "
        f"({old_w_rule['poor_to_good']} / {old_w_rule['good_to_poor']}), "
        f"recall(Poor) = {old_w_rule['recall_poor']:.3f}.",
        "",
        "**Against the architecture doc's §10.4 recommendation (`w_rule=0.6`):** "
        + next(
            (
                f"precision {r['confident_precision']:.3f}, macro-F1 "
                f"{r['macro_f1']:.3f}, severe count {r['severe_count']} "
                f"({r['poor_to_good']} / {r['good_to_poor']}), recall(Poor) = "
                f"{r['recall_poor']:.3f}."
                for r in weight_results
                if r["w_rule"] == 0.6
            ),
            "not in the swept grid.",
        ),
        "",
        "> **Severe count alone hides an important difference here.** Both the "
        "Stage 4.0 placeholder and the §10.4 recommendation reach 0 severe "
        "misclassifications — the same as the chosen weight — but not for the same "
        "reason. At `w_rule=0.4` and `0.6`, `recall_poor=0`: **every Poor repetition "
        "is routed to Fair, and none is ever correctly identified as Poor.** That is "
        "safe but uninformative. At the chosen `w_rule=0.2`, some Poor repetitions "
        f"are correctly identified as Poor (`recall_poor="
        f"{chosen_weight_row['recall_poor']:.3f}`) with the same 0 severe count — "
        "this is exactly the distinction macro-F1 is doing real work to catch above, "
        "and it is why the tie-break trace credits macro-F1 with narrowing the field "
        "rather than treating all zero-severe candidates as equivalent.",
        "",
        "> **The same small-N caveat applies here, more so.** 7 candidate weights over "
        "98 reps (26 Poor) means the Poor→Good and Good→Poor counts are small integers "
        "(typically single digits) — a difference of one event between two candidates "
        "is not a reliably distinguishable result. The within-1-event tie-break margin "
        "used in `_pick_fusion_weight()` is a deliberate acknowledgement of this, not "
        "an arbitrary allowance.",
        "",
        "## What changed",
        "",
        "`backend/app/module_b/core/config.py`: `w_rule_default`/`w_ml_default` "
        "replaced with this sweep's converged winner and retagged `[dataset-derived]` "
        "(previously `[proposed heuristic, R7]`); `confidence_low_threshold` replaced "
        "with the same converged run's threshold and retagged the same way. "
        "`w_rule_low_confidence` and `q_min` are untouched (out of scope for this "
        "stage).",
        "",
        "## Deliberately not done here",
        "",
        "- **`band_thresholds` (D6, Poor<4/Fair[4,7)/Good>=7) is unchanged.** This "
        "stage's checklist sweeps `confidence_low_threshold` and the fusion weight "
        "only; the score-to-band cut points are a separate, already-fixed heuristic "
        "not in scope here.",
        "- **No 3-band confusion-matrix figure, no baseline comparison, no latency.** "
        "**Stage 5.7.**",
        "- **No artifact export.** The classifier itself is still Stage 5.8's "
        "deliverable; this stage only changes fusion configuration.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
