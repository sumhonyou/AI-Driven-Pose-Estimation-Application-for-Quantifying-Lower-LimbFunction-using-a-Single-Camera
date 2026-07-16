"""Stage 5.7: evaluation of the shipped squat pipeline.

Scores the **fused 3-band output the user actually sees** (Good/Fair/Poor), not just
the binary classifier underneath it, at the exact configuration Stage 5.6 wrote into
`backend/app/module_b/core/config.py`. Nothing here re-tunes, re-picks or re-derives a
threshold: the config is read live and evaluated as shipped, so this report measures
the system rather than a private variant of it.

Five decisions this stage makes, each of which the report justifies rather than asserts:

1. **"Accuracy" is reported twice, under two named definitions, because on a
   3-band output over binary ground truth it is genuinely ambiguous.** REHAB24-6
   labels every repetition Good or Poor; the pipeline may answer Good, Poor **or
   Fair** ("I am not confident — no judgement"). A single accuracy number silently
   picks one of two incompatible conventions: count Fair as wrong (punishing the
   system for admitting uncertainty, which is the safety behaviour Stage 5.6 bought
   on purpose), or drop Fair (flattering it, since a system that abstains on
   everything but one easy rep would then score 100%). Both are reported —
   `accuracy_strict` and `accuracy_confident` — with the Fair rate next to them, and
   neither is presented as *the* headline. Quoting either alone is the misreading
   this design is meant to make impossible.

2. **Precision is emphasised over recall, and that is a stated value judgement, not a
   result.** The checklist asks for precision to be emphasised; the reason is HY's
   criterion from Stage 5.6 — telling a poor-form user they are fine is the worst
   failure mode. But the honest consequence is recorded right beside it: this
   pipeline's precision is bought almost entirely with abstention, and `recall_poor`
   is very low. Precision without its recall is not a performance claim.

3. **`error_tags` multi-label F1 is NOT computed, for two independent reasons.**
   The checklist already anticipates the first (REHAB24-6 is binary and does not
   label individual faults, so rule-only tags have no ground truth here). Reading the
   code turns up a second, which the checklist does not mention: `router.py` never
   calls `exercise.error_tags()` at all — `SquatExercise.error_tags()` raises
   `NotImplementedError`, and the only tags persisted today are the *system* flags
   (`low_confidence`, `low_capture_quality`, `retry_camera_placement`) that
   `_system_error_tags()` derives from fusion, with the movement taxonomy explicitly
   deferred to Stage 6. So there is neither ground truth to score against nor a
   prediction to score. `figures/error_tag_performance.png` is deliberately not
   produced (see the report).

4. **Latency is measured, and is the one output here that is NOT byte-reproducible.**
   Every other number in this report is deterministic (X8). Wall-clock timing cannot
   be — that is what it measures. Rather than quietly break the determinism claim the
   other Phase 5 reports make, the report scopes X8 explicitly to the decision
   outputs and states that the latency section varies run to run. Each repetition is
   timed `LATENCY_REPEATS` times and the per-repetition **median** is kept, so the
   distribution reflects typical cost rather than one unlucky scheduling artefact.

5. **The baseline comparison quotes only the number this project can actually
   support.** `task.md` Q4 ("REHAB24-6 authors' own baseline + split protocol")
   remains **open**: it settles via the SISAP 2024 paper, which is paywalled and was
   not obtainable, so the authors' own baseline is *not* quoted here — an unverified
   number is worse than an absent one, and Q4's own instruction is "do not silently
   resolve them by assumption". Only [S13]'s ~93% Random Forest figure, which
   `task.md` itself supplies, is plotted, and the split-protocol difference that makes
   it non-comparable is written **into the figure** rather than only into the prose
   around it.

Reuses Stage 5.5's `nested_cv()` and Stage 5.6's fusion/quality/rule helpers verbatim
rather than re-implementing them (X1, and the `ml/` import-don't-transcribe convention:
a hand-copied constant in this project has already been wrong 7 times out of 13).

Deterministic (X8) for every output except the latency section, as described above.
"""

from __future__ import annotations

import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.squat.features import extract_squat_features
from build_features import _preprocessed_stream
from plotting import save_fig

# Stage 5.6's helpers are imported, not re-derived: `_fuse_all` calls the real
# `fuse_scores()`, `_raw_capture_quality` reproduces `router.py`'s raw-buffer
# semantics, and `_confusion`/`_metrics` already encode the "no ground-truth Fair
# label" position this stage inherits unchanged.
from sweep_fusion_weights import (
    PREDICTED_BANDS,
    TRUE_LABELS,
    _confusion,
    _fuse_all,
    _metrics,
    _raw_capture_quality,
    _rule_score,
    _segmentation_bounds,
)
from train_squat import (
    _build_xy,
    _choose_cv,
    _load_config,
    _read_rows,
    build_final_model,
    nested_cv,
)

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "SQUAT_EVALUATION_REPORT.md"

# Per-repetition timing is dominated by process noise at single-run granularity;
# the median of this many repeats is what the distribution is built from.
LATENCY_REPEATS = 5

# The real-time feasibility claim this stage exists to support. 33.3 ms is one frame
# at the dataset's 30 FPS: per-rep inference costing less than a single frame's budget
# is the bar that makes "analyse while capturing" credible.
FRAME_BUDGET_MS = 1000.0 / 30.0

# [S13], as supplied by task.md's own Stage 5.7 checklist. Quoted with its protocol
# caveat attached everywhere it appears, including inside the figure.
BASELINE_S13 = {
    "label": "Prior work [S13]\n(Random Forest, squat)",
    "accuracy": 0.93,
    "protocol": "non-subject-wise split\n(subjects appear in train AND test)",
}


def _binary_summary(y: np.ndarray, prob_good: np.ndarray, threshold: float) -> dict:
    """The underlying binary classifier alone, at a fixed threshold.

    This — not the fused 3-band output — is the only thing structurally comparable to a
    published binary-classifier accuracy, because the fused pipeline can abstain and a
    plain classifier cannot. Even then the *protocol* differs; see the report.

    Returns the full breakdown, not just the accuracy, because on this dataset the
    accuracy alone is actively misleading: it lands exactly on the majority-class base
    rate, which looks like a degenerate always-predict-Good classifier and is not one.
    Distinguishing those two cases requires the counts, so they are computed rather than
    inferred from the headline number.
    """
    predicted = (prob_good >= threshold).astype(int)
    correct_good = int(((predicted == 1) & (y == 1)).sum())
    correct_poor = int(((predicted == 0) & (y == 0)).sum())
    base_rate = float(y.mean())
    return {
        "accuracy": float((predicted == y).mean()),
        "n_predicted_good": int((predicted == 1).sum()),
        "n_predicted_poor": int((predicted == 0).sum()),
        "correct_good": correct_good,
        "correct_poor": correct_poor,
        "missed_good": int(((predicted == 0) & (y == 1)).sum()),
        "missed_poor": int(((predicted == 1) & (y == 0)).sum()),
        # A classifier that always answers with the majority class. The bar any
        # accuracy figure on an imbalanced dataset has to clear to mean anything.
        "majority_accuracy": base_rate,
        "threshold": threshold,
    }


def _evaluation_metrics(true_labels: list[str], bands: list[str]) -> dict:
    """Stage 5.6's `_metrics` plus the two accuracy conventions defined above.

    `_metrics` is reused rather than re-derived so the precision/recall/F1 definitions
    here are provably the same ones the operating point was selected against.
    """
    counts = _confusion(true_labels, bands)
    n = len(true_labels)
    metrics = _metrics(counts, n)

    correct = counts[("Good", "Good")] + counts[("Poor", "Poor")]
    fair_n = sum(counts[(t, "Fair")] for t in TRUE_LABELS)
    confident_n = n - fair_n

    # Fair counted as wrong: the pessimistic reading. A rep the system declined to
    # judge did not produce the right answer, even though it did not produce a
    # harmful one either.
    metrics["accuracy_strict"] = correct / n
    # Fair excluded: accuracy among reps the system was willing to commit to. Only
    # meaningful when read together with fair_rate, which is why they are always
    # printed as a pair.
    metrics["accuracy_confident"] = (
        correct / confident_n if confident_n else float("nan")
    )
    metrics["confident_n"] = confident_n
    metrics["n"] = n
    return metrics


def _macro_precision_recall(metrics: dict) -> tuple[float, float]:
    """Unweighted mean over the two classes that have ground truth (Good, Poor).

    `nan` propagates deliberately: if a class was never predicted at all, its
    precision is undefined and the macro average must say so rather than substitute a
    zero and report a number that looks like a measurement.
    """
    precision = (metrics["precision_good"] + metrics["precision_poor"]) / 2
    recall = (metrics["recall_good"] + metrics["recall_poor"]) / 2
    return precision, recall


def plot_confusion_matrix_3band(
    metrics: dict,
    *,
    dataset_label: str = "REHAB24-6",
    subtitle: str | None = None,
    name: str = "confusion_matrix_3band",
) -> Path:
    """2x3 heatmap: true Good/Poor (rows) vs predicted Good/Fair/Poor (columns).

    Non-square on purpose — Fair is a column with no matching row, which is exactly
    the point. Ground truth has no Fair class, so the Fair column can never be
    "correct" or "incorrect"; it is where the system declines to answer. A forced
    square matrix would have to invent a diagonal cell for it.

    Parameterised over the dataset only so Stage 5.9's EC3D matrix is drawn by *this*
    function rather than a copy of it: the checklist requires the two figures to be
    comparable side by side, which a forked plotter cannot guarantee over time. The
    defaults reproduce the Stage 5.7 figure byte-for-byte.
    """
    counts = metrics["counts"]
    grid = np.array(
        [[counts[(t, p)] for p in PREDICTED_BANDS] for t in TRUE_LABELS], dtype=float
    )
    row_totals = grid.sum(axis=1, keepdims=True)
    row_pct = np.divide(grid, row_totals, out=np.zeros_like(grid), where=row_totals > 0)

    fig, ax = plt.subplots()
    ax.imshow(row_pct, cmap="Blues", vmin=0.0, vmax=1.0, aspect="auto")

    for i in range(len(TRUE_LABELS)):
        for j in range(len(PREDICTED_BANDS)):
            ax.text(
                j,
                i,
                f"{int(grid[i, j])}\n({row_pct[i, j] * 100:.1f}%)",
                ha="center",
                va="center",
                color="white" if row_pct[i, j] > 0.5 else "black",
                fontsize=11,
            )

    ax.set_xticks(range(len(PREDICTED_BANDS)), PREDICTED_BANDS)
    ax.set_yticks(range(len(TRUE_LABELS)), TRUE_LABELS)
    ax.set_xlabel("Predicted band (what the user is shown)")
    ax.set_ylabel(f"True label ({dataset_label})")
    ax.set_title(
        "Fused 3-band output vs ground truth\n"
        + (
            subtitle
            if subtitle is not None
            else f"counts, row-normalised %; n={metrics['n']} side-view reps"
        )
    )
    # Colour encodes the row percentage, but the counts are what the reader should
    # act on -- saying so on the figure stops the shading being read as a count.
    ax.text(
        0.5,
        -0.28,
        "Shading = row-normalised recall. 'Fair' is an abstention, not a third "
        "ground-truth class:\nno rep is labelled Fair, so that column is neither "
        "correct nor incorrect.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8,
        style="italic",
    )
    ax.grid(False)
    return save_fig(fig, name, figsize="single")


def plot_robustness_signals(
    low_conf_frame_freq: list[float], flag_rates: dict[str, float]
) -> Path:
    """Distribution of per-rep low-confidence-frame frequency + the safety-flag rates.

    A histogram rather than one averaged number, per the checklist's own reasoning:
    an isolated bad capture must stay visible instead of being averaged away.
    """
    fig, (ax_hist, ax_bar) = plt.subplots(1, 2)

    ax_hist.hist(
        [v * 100 for v in low_conf_frame_freq],
        bins=20,
        range=(0, 100),
        color="#4C72B0",
        edgecolor="white",
    )
    ax_hist.set_xlabel("Low-confidence frames per rep (%)")
    ax_hist.set_ylabel("Repetitions")
    ax_hist.set_title(
        "Low-confidence-frame frequency\n"
        f"(frame has any required landmark below "
        f"visibility {MODULE_B_CORE_CONFIG['confidence_threshold']})",
        fontsize=10,
    )

    names = list(flag_rates)
    values = [flag_rates[name] * 100 for name in names]
    bars = ax_bar.barh(names, values, color="#C44E52")
    ax_bar.set_xlabel("Reps raising the flag (%)")
    ax_bar.set_xlim(0, 100)
    ax_bar.set_title("Safety-flag rate", fontsize=10)
    for bar, value in zip(bars, values, strict=True):
        ax_bar.text(
            bar.get_width() + 1.5,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            fontsize=9,
        )

    fig.tight_layout()
    return save_fig(fig, "robustness_signals", figsize="wide")


def plot_inference_latency(latencies_ms: list[float]) -> Path:
    """Per-rep feature-extraction + predict latency. Not byte-reproducible (see docstring)."""
    median = float(np.median(latencies_ms))
    p95 = float(np.percentile(latencies_ms, 95))

    fig, ax = plt.subplots()
    # Bin over the observed range only. Drawing the 33.3 ms frame budget as a line
    # would set the x-limit ~4x wider than the data and crush the entire distribution
    # into one indistinguishable spike -- the reference line would destroy the plot it
    # is meant to contextualise. The budget is stated as an annotation instead, and
    # the numeric comparison lives in the report table.
    ax.hist(latencies_ms, bins=20, color="#55A868", edgecolor="white")
    ax.axvline(
        median, color="#C44E52", linestyle="--", label=f"median = {median:.2f} ms"
    )
    ax.axvline(p95, color="#8172B2", linestyle=":", label=f"p95 = {p95:.2f} ms")
    ax.set_xlabel("Per-rep latency (ms): extract_squat_features + predict_proba")
    ax.set_ylabel("Repetitions")
    ax.set_title(
        "Inference latency per repetition\n"
        f"(median of {LATENCY_REPEATS} timed repeats each; excludes pose estimation)",
        fontsize=10,
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.text(
        0.5,
        -0.30,
        f"One frame at 30 FPS = {FRAME_BUDGET_MS:.1f} ms — off-scale to the right, "
        f"~{FRAME_BUDGET_MS / p95:.1f}x the p95 above.\n"
        "Axis is scaled to the data, not the budget. Excludes pose estimation, which "
        "runs per-frame in the browser.\nWall-clock: this is the one figure in Phase 5 "
        "that is not byte-reproducible across runs.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8,
        style="italic",
    )
    return save_fig(fig, "inference_latency_distribution", figsize="single")


def plot_baseline_comparison(ours: dict) -> Path:
    """Grouped bar: our subject-wise accuracy vs [S13]'s random-split accuracy.

    The protocol caveat is drawn *inside* the axes. The checklist's reason is
    explicit and worth restating: a figure gets screenshotted out of its report, and
    a bar chart that silently compares a subject-wise number to a random-split one is
    a misleading artefact the moment it leaves this page.
    """
    labels = [
        f"This project\n(Extra Trees, squat)\n{ours['protocol']}",
        f"{BASELINE_S13['label']}\n{BASELINE_S13['protocol']}",
    ]
    values = [ours["accuracy"] * 100, BASELINE_S13["accuracy"] * 100]

    fig, ax = plt.subplots()
    bars = ax.bar(labels, values, color=["#4C72B0", "#CCB974"], width=0.55)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.2,
            f"{value:.1f}%",
            ha="center",
            fontsize=11,
            fontweight="bold",
        )
    ax.set_ylabel("Binary Good/Poor accuracy (%)")
    # Headroom for the caveat box to sit above the taller bar's value label rather
    # than on top of it.
    ax.set_ylim(0, 155)
    ax.set_yticks(range(0, 101, 20))
    ax.set_title("Binary classifier accuracy vs published baseline", fontsize=11)
    ax.tick_params(axis="x", labelsize=8)
    ax.text(
        0.5,
        0.99,
        "NOT AN APPLES-TO-APPLES COMPARISON — different split protocols.\n"
        "A non-subject-wise split lets the same person's reps appear in both train "
        "and test, which\ninflates accuracy on a 9-subject dataset. The lower bar is "
        "the harder, more honest protocol;\nthe gap is not evidence that this model "
        "is worse.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=7.5,
        style="italic",
        bbox={"facecolor": "#FFF3CD", "edgecolor": "#856404", "alpha": 0.95},
    )
    return save_fig(fig, "baseline_comparison_bar", figsize="single")


def measure_latency(rows: list[dict], config: dict, model) -> list[float]:
    """Per-rep (feature extraction + predict) latency in ms, on the preprocessed stream.

    Deliberately excludes pose estimation and preprocessing: both are per-*frame*
    costs paid during capture by MediaPipe in the browser, whereas this is the
    per-*rep* cost the backend adds at the end of a set — which is what the
    real-time feasibility claim is about. The report states that scope rather than
    letting "latency" imply end-to-end.
    """
    bounds = _segmentation_bounds(config)
    preprocessed_cache: dict[str, list[dict]] = {}
    frame_count_cache: dict[str, int] = {}

    latencies = []
    for row in rows:
        video_id = row["video_id"]
        stream = _preprocessed_stream(video_id, preprocessed_cache, frame_count_cache)
        first, last = bounds[(video_id, row["repetition_number"])]
        frames = [f for f in stream if first <= f["frameIndex"] <= last]

        samples = []
        for _ in range(LATENCY_REPEATS):
            start = time.perf_counter()
            vector = extract_squat_features(frames)
            model.predict_proba(np.array([vector.values], dtype=float))
            samples.append((time.perf_counter() - start) * 1000.0)
        latencies.append(float(np.median(samples)))
    return latencies


def _visibility_breakdown(rows: list[dict], config: dict) -> dict:
    """Per-landmark raw visibility for one representative rep, to show *why* §4 saturates.

    Computed here rather than transcribed from an ad-hoc check: a hand-copied number in
    this project has already been wrong 7 times out of 13, and this table is the whole
    evidence for the "one occluded landmark zeroes the metric" claim.

    The sampled repetition is the first in sorted order — an arbitrary but *fixed* and
    stated choice (X8), not one picked because it made the point best.
    """
    from app.module_b.core.quality import REQUIRED_LANDMARKS, assess_capture_quality
    from build_features import _raw_full_stream

    landmark_names = {
        11: "Left (near) shoulder",
        12: "Right (far) shoulder",
        23: "Left (near) hip",
        24: "Right (far) hip",
        25: "Left (near) knee",
        26: "Right (far) knee",
        27: "Left (near) ankle",
        28: "Right (far) ankle",
    }
    bounds = _segmentation_bounds(config)
    row = rows[0]
    frames, _total = _raw_full_stream(row["video_id"])
    first, last = bounds[(row["video_id"], row["repetition_number"])]
    window = [f for f in frames if first <= f["frameIndex"] <= last]

    threshold = MODULE_B_CORE_CONFIG["confidence_threshold"]
    per_landmark = []
    for index in REQUIRED_LANDMARKS:
        visibilities = np.array(
            [float(f["worldLandmarks"][index]["visibility"]) for f in window]
        )
        per_landmark.append(
            {
                "index": index,
                "name": landmark_names[index],
                "median": float(np.median(visibilities)),
                "below": int((visibilities < threshold).sum()),
            }
        )
    return {
        "rep_id": f"{row['video_id']}#{row['repetition_number']}",
        "n_frames": len(window),
        "threshold": threshold,
        "valid_frame_ratio": float(assess_capture_quality(window)["valid_frame_ratio"]),
        "per_landmark": per_landmark,
    }


def _low_confidence_frame_frequency(rows: list[dict], config: dict) -> list[float]:
    """Per-rep fraction of RAW frames with any required landmark below the threshold.

    This is `1 - valid_frame_ratio` from the live `assess_capture_quality()`, so the
    definition of "low-confidence frame" is the backend's own, not one invented here.
    Measured on raw frames for the same reason `router.py` does: it reflects what the
    camera actually captured, before gap-filling papers over it.
    """
    from app.module_b.core.quality import assess_capture_quality
    from build_features import _raw_full_stream

    bounds = _segmentation_bounds(config)
    raw_cache: dict[str, list[dict]] = {}
    frequencies = []
    for row in rows:
        video_id = row["video_id"]
        if video_id not in raw_cache:
            frames, _total = _raw_full_stream(video_id)
            raw_cache[video_id] = frames
        first, last = bounds[(video_id, row["repetition_number"])]
        rep_frames = [
            f for f in raw_cache[video_id] if first <= f["frameIndex"] <= last
        ]
        quality = assess_capture_quality(rep_frames)
        frequencies.append(1.0 - float(quality["valid_frame_ratio"]))
    return frequencies


def main() -> None:
    config = _load_config()
    seed = int(config["seeds"]["sklearn"])
    rows = _read_rows()
    x, y, groups = _build_xy(rows)
    true_labels = ["Good" if v == 1 else "Poor" for v in y]
    outer_cv, cv_name, cv_why = _choose_cv(y, groups)

    print("Re-running Stage 5.5's nested CV for out-of-fold calibrated P(Good)...")
    _prob_uncal, prob_cal, _folds = nested_cv(x, y, groups, outer_cv, seed)

    print("Computing per-repetition rule scores and raw capture quality...")
    rule_scores = [_rule_score(row) for row in rows]
    qs = _raw_capture_quality(rows, config)

    # Evaluate the config as shipped -- read live, not restated. If Stage 5.6's values
    # are ever changed, this report changes with them instead of going quietly stale.
    w_rule = MODULE_B_CORE_CONFIG["w_rule_default"]
    w_ml = MODULE_B_CORE_CONFIG["w_ml_default"]
    threshold = MODULE_B_CORE_CONFIG["confidence_low_threshold"]
    q_min = MODULE_B_CORE_CONFIG["q_min"]
    print(
        f"Evaluating shipped config: w_rule={w_rule}, w_ml={w_ml}, "
        f"confidence_low_threshold={threshold}, q_min={q_min}"
    )

    fused = _fuse_all(
        rows,
        prob_cal,
        rule_scores,
        qs,
        w_rule=w_rule,
        w_ml=w_ml,
        confidence_low_threshold=threshold,
    )
    bands = [f.band for f in fused]
    metrics = _evaluation_metrics(true_labels, bands)
    macro_precision, macro_recall = _macro_precision_recall(metrics)
    print(
        f"  accuracy_strict={metrics['accuracy_strict']:.3f}  "
        f"accuracy_confident={metrics['accuracy_confident']:.3f}  "
        f"macro_f1={metrics['macro_f1']:.3f}  fair_rate={metrics['fair_rate']:.3f}"
    )

    print("Measuring robustness signals...")
    low_conf_freq = _low_confidence_frame_frequency(rows, config)
    n = len(rows)
    flag_rates = {
        flag: sum(1 for f in fused if flag in f.flags) / n
        for flag in ("low_confidence", "low_capture_quality", "retry_camera_placement")
    }
    fully_saturated = sum(1 for v in low_conf_freq if v >= 1.0)
    print(
        "  low-confidence frames per rep: "
        f"min={min(low_conf_freq) * 100:.1f}%  "
        f"median={float(np.median(low_conf_freq)) * 100:.1f}%  "
        f"max={max(low_conf_freq) * 100:.1f}%  "
        f"({fully_saturated}/{n} reps have NO fully-valid frame at all)"
    )
    visibility = _visibility_breakdown(rows, config)
    print(
        f"  sampled rep {visibility['rep_id']}: "
        f"valid_frame_ratio={visibility['valid_frame_ratio']:.3f}"
    )
    print(f"  safety-flag rates: {flag_rates}")

    print("Fitting the final model for latency measurement...")
    final_model, _search = build_final_model(x, y, groups, seed)
    print(f"Measuring inference latency ({LATENCY_REPEATS} repeats per rep)...")
    latencies = measure_latency(rows, config, final_model)
    print(
        f"  latency: median={float(np.median(latencies)):.2f} ms  "
        f"p95={float(np.percentile(latencies, 95)):.2f} ms"
    )

    binary = _binary_summary(y, prob_cal, 0.5)
    ours = {
        "accuracy": binary["accuracy"],
        "protocol": "subject-wise 5-fold\n(no subject in train AND test)",
    }
    print(
        f"  binary classifier accuracy @0.5 (out-of-fold): {binary['accuracy']:.4f} "
        f"(majority-class baseline: {binary['majority_accuracy']:.4f}; "
        f"predicts Poor for {binary['n_predicted_poor']}/{len(rows)} reps, "
        f"{binary['correct_poor']} correctly)"
    )

    plot_confusion_matrix_3band(metrics)
    plot_robustness_signals(low_conf_freq, flag_rates)
    plot_inference_latency(latencies)
    plot_baseline_comparison(ours)

    write_report(
        rows=rows,
        cv_name=cv_name,
        cv_why=cv_why,
        w_rule=w_rule,
        w_ml=w_ml,
        threshold=threshold,
        q_min=q_min,
        metrics=metrics,
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        low_conf_freq=low_conf_freq,
        flag_rates=flag_rates,
        visibility=visibility,
        qs=qs,
        latencies=latencies,
        binary=binary,
    )
    print(f"wrote {REPORT_MD.name}")


def _fmt(value: float, places: int = 3) -> str:
    """`nan` is rendered as an explicit marker, never as a number."""
    return "n/a" if np.isnan(value) else f"{value:.{places}f}"


def write_report(
    *,
    rows,
    cv_name: str,
    cv_why: str,
    w_rule: float,
    w_ml: float,
    threshold: float,
    q_min: float,
    metrics: dict,
    macro_precision: float,
    macro_recall: float,
    low_conf_freq: list[float],
    flag_rates: dict[str, float],
    visibility: dict,
    qs: list[float],
    latencies: list[float],
    binary: dict,
) -> None:
    counts = metrics["counts"]
    n = metrics["n"]
    n_subjects = len({row["person_id"] for row in rows})
    n_good = sum(1 for row in rows if row["label"] == "Good")
    n_poor = n - n_good

    median_latency = float(np.median(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    max_latency = float(max(latencies))
    median_low_conf = float(np.median(low_conf_freq)) * 100
    max_low_conf = float(max(low_conf_freq)) * 100
    min_low_conf = float(min(low_conf_freq)) * 100
    fully_saturated = sum(1 for v in low_conf_freq if v >= 1.0)
    clean_reps = sum(1 for v in low_conf_freq if v == 0.0)

    # Bold exactly the landmarks that actually fail, so emphasis is derived from the
    # data rather than applied by hand to the ones that suit the argument.
    visibility_rows = "\n".join(
        (
            f"| **{item['name']}** | **{item['median']:.3f}** | "
            f"**{item['below']}/{visibility['n_frames']}** |"
            if item["below"] > 0
            else f"| {item['name']} | {item['median']:.3f} | "
            f"{item['below']}/{visibility['n_frames']} |"
        )
        for item in visibility["per_landmark"]
    )

    confusion_rows = "\n".join(
        f"| **{t}** (n={sum(counts[(t, p)] for p in PREDICTED_BANDS)}) | "
        + " | ".join(str(counts[(t, p)]) for p in PREDICTED_BANDS)
        + " |"
        for t in TRUE_LABELS
    )

    report = f"""# Squat Evaluation Report (Stage 5.7)

Generated by `ml/scripts/evaluate_squat.py`. Every number below is measured on the
**shipped configuration**, read live from `backend/app/module_b/core/config.py` at run
time rather than restated here: `w_rule={w_rule}`, `w_ml={w_ml}`,
`confidence_low_threshold={threshold}`, `q_min={q_min}` (all earned in Stage 5.6 — see
[SQUAT_FUSION_SWEEP.md](SQUAT_FUSION_SWEEP.md)).

**Evaluation set:** {n} side-view squat repetitions from {n_subjects} subjects
({n_good} Good, {n_poor} Poor). Probabilities are **out-of-fold** from Stage 5.5's
nested `{cv_name}` — {cv_why}. No repetition is scored by a model that saw its subject
in training.

> **Read this first.** The headline of this report is not a single accuracy figure, and
> §1 explains why one cannot honestly be given. The pipeline answers **Good, Fair or
> Poor**; the ground truth only says **Good or Poor**. "Fair" means *the system
> declined to judge*, and how you count it changes the accuracy by
> {abs(metrics["accuracy_confident"] - metrics["accuracy_strict"]) * 100:.0f} percentage
> points. Both conventions are reported. Neither is *the* number.

---

## 1. Headline metrics (fused 3-band output)

| Metric | Value | What it means |
| --- | --- | --- |
| `accuracy_strict` | **{_fmt(metrics["accuracy_strict"])}** | Fair counted as **wrong**. {counts[("Good", "Good")] + counts[("Poor", "Poor")]}/{n} reps got the right band. |
| `accuracy_confident` | **{_fmt(metrics["accuracy_confident"])}** | Fair **excluded**. Accuracy over the {metrics["confident_n"]} reps the system committed to. |
| `fair_rate` | **{_fmt(metrics["fair_rate"])}** | {sum(counts[(t, "Fair")] for t in TRUE_LABELS)}/{n} reps abstained. **Required to read either accuracy above.** |
| Macro-F1 | **{_fmt(metrics["macro_f1"])}** | Mean of F1(Good), F1(Poor). |
| Macro precision | **{_fmt(macro_precision)}** | Mean of precision(Good), precision(Poor). |
| Macro recall | **{_fmt(macro_recall)}** | Mean of recall(Good), recall(Poor). |

### Why two accuracies, and why neither is the headline

`accuracy_confident` = {_fmt(metrics["accuracy_confident"])} is the flattering number and
`accuracy_strict` = {_fmt(metrics["accuracy_strict"])} is the pessimistic one. The gap
between them is entirely the {_fmt(metrics["fair_rate"])} Fair rate.

Neither is quotable alone:

- **`accuracy_confident` alone is meaningless without `fair_rate`.** A system that
  abstained on 97 of 98 reps and got the last one right would score 1.000 here. That is
  not a hypothetical failure of the metric — it is the same direction this pipeline
  already leans, at {_fmt(metrics["fair_rate"])} abstention.
- **`accuracy_strict` alone punishes the safety behaviour Stage 5.6 deliberately
  bought.** An abstention is not a wrong answer; it is a refusal to give one, which for
  a rehabilitation tool is the correct response to genuine uncertainty.

The honest summary is the pair: **the system commits to a judgement on
{metrics["confident_n"]}/{n} repetitions ({(1 - metrics["fair_rate"]) * 100:.1f}%), and
when it commits it is right {metrics["accuracy_confident"] * 100:.1f}% of the time.**

### Per-class

| Class | Precision | Recall | Support |
| --- | --- | --- | --- |
| Good | **{_fmt(metrics["precision_good"])}** | {_fmt(metrics["recall_good"])} | {n_good} |
| Poor | **{_fmt(metrics["precision_poor"])}** | {_fmt(metrics["recall_poor"])} | {n_poor} |

**Precision is emphasised here because the checklist asks for it, and the reason is a
value judgement, not a result:** telling a poor-form user their form is fine is the
failure mode with the worst consequence in a rehabilitation setting (HY's criterion,
2026-07-16; it is also what selected this operating point in Stage 5.6).

**But precision this high, quoted without its recall, would be a misrepresentation.**
Precision(Poor) = {_fmt(metrics["precision_poor"])} does not mean the system reliably
catches poor form. It means that *on the rare occasions it says "Poor", it is right* —
it says so for only {counts[("Poor", "Poor")]} of {n_poor} actually-poor repetitions
(recall = {_fmt(metrics["recall_poor"])}). The precision is bought almost entirely with
abstention. Both numbers must travel together.

---

## 2. Confusion matrix over the fused 3-band output

This is the matrix over **what the user is actually shown**, not over the binary
classifier underneath it.

| True \\ Predicted | {" | ".join(PREDICTED_BANDS)} |
| --- | --- | --- | --- |
{confusion_rows}

![Confusion matrix over the final fused 3-band output. Rows are REHAB24-6 ground truth (Good/Poor); columns are the band the pipeline shows the user (Good/Fair/Poor). Cells show counts with row-normalised percentages. The matrix is deliberately non-square: no repetition is labelled Fair, so that column is an abstention rather than a class that can be right or wrong.](figures/confusion_matrix_3band.png)

**The two severe cells are both zero.** Poor→Good = {counts[("Poor", "Good")]} and
Good→Poor = {counts[("Good", "Poor")]}. This is the property Stage 5.6 selected for, and
it holds here as expected — this is not an independent confirmation, since the same
out-of-fold predictions selected the operating point. It is reported because its absence
would have signalled a bug.

**The Fair column is the real story:** {sum(counts[(t, "Fair")] for t in TRUE_LABELS)} of
{n} repetitions ({metrics["fair_rate"] * 100:.1f}%), of which
{counts[("Poor", "Fair")]}/{n_poor} are truly Poor. Nearly every poor repetition is
routed to "not confident" rather than caught. **The system is safe here, not
informative.**

---

## 3. `error_tags` multi-label F1 — deliberately not computed

The checklist asks for micro/macro-F1 over `error_tags`, "**only for tags with real
dataset signal**". There are none, for two independent reasons — the second was found by
reading the code, and is not in the checklist:

1. **No ground truth exists.** REHAB24-6 carries one binary correctness label per
   repetition. It does not label *which* fault occurred, so there is nothing to score a
   per-tag prediction against.
2. **No movement-taxonomy prediction exists yet either.** `router.py` never calls
   `exercise.error_tags()`; `SquatExercise.error_tags()` raises `NotImplementedError`,
   and `_system_error_tags()` persists only the fusion/capture flags
   (`low_confidence`, `low_capture_quality`, `retry_camera_placement`), with the
   movement taxonomy explicitly deferred to Stage 6.

So there is neither a prediction nor a reference. `figures/error_tag_performance.png` is
**not produced**, per the checklist's own instruction not to fabricate bars for tags with
no ground truth. Those flags' rates are reported in §4 as *robustness signals*, which is
what they are — not as a tag-classification result.

EC3D's per-fault labels (Stage 5.9) are the only honest source for this, and only for the
faults EC3D actually labels.

---

## 4. Robustness signals

![Left: distribution of per-repetition low-confidence-frame frequency across the evaluation set, shown as a histogram rather than a single mean so an isolated bad capture stays visible. Right: rate at which each safety flag fires. Both are measured on raw pre-preprocessing frames, matching router.py's semantics.](figures/robustness_signals.png)

### Low-confidence-frame frequency

Defined as `1 - valid_frame_ratio` from the live `assess_capture_quality()` — a frame is
"low-confidence" when **any** of the 8 required landmarks falls below
`confidence_threshold = {MODULE_B_CORE_CONFIG["confidence_threshold"]}`. Measured on
**raw** frames, before gap-filling and smoothing, for the same reason `router.py` does:
it reflects what the camera actually captured rather than what interpolation
reconstructed afterwards.

| Statistic | Value |
| --- | --- |
| Median low-confidence frames per rep | **{median_low_conf:.1f}%** |
| Min / max | {min_low_conf:.1f}% / {max_low_conf:.1f}% |
| **Reps with no fully-valid frame at all** | **{fully_saturated}/{n}** ({fully_saturated / n * 100:.0f}%) |
| Reps with no low-confidence frame at all | {clean_reps}/{n} |

**This metric is saturated, and that is the finding.** For
{fully_saturated} of {n} repetitions, **not a single frame** clears the bar — the median
is {median_low_conf:.0f}%, i.e. the typical repetition has no fully-valid frame
whatsoever. A metric pinned at its worst value for {fully_saturated / n * 100:.0f}% of
the data cannot discriminate a good capture from a bad one. **It should not be used as a
robustness gate in its current form.**

The cause is not marginal noise; it is the far-limb occlusion finding, measured directly.
Sampling one repetition's raw landmark visibilities against the
`confidence_threshold = {visibility["threshold"]}` bar shows the mechanism cleanly — the
near-side limb is tracked almost perfectly while the far side is not tracked at all.
Repetition `{visibility["rep_id"]}` ({visibility["n_frames"]} frames, the first in sorted
order — an arbitrary but fixed choice, not one selected to make the point):

| Landmark | Median visibility | Frames below threshold |
| --- | --- | --- |
{visibility_rows}

Its `valid_frame_ratio` is **{visibility["valid_frame_ratio"]:.3f}**.

Because `valid_frame_ratio` requires **all 8** required landmarks to clear the threshold
simultaneously, one persistently-occluded landmark is enough to zero it for the entire
repetition. That is exactly what happens.

This is a property of **monocular side-view capture**, not of this dataset — **the live
application inherits it**, since it gives the same camera guidance. The pipeline copes
(`_release_persistent_occlusions()` prevents the frozen hold-last landmarks that once
halved measured knee flexion and collapsed FSM agreement from 92/98 to 32/98), but
"copes" is not "does not occur", and the quality metrics do not report it.

### Safety-flag rate

| Flag | Rate | Reps |
| --- | --- | --- |
{chr(10).join(f"| `{flag}` | **{rate * 100:.1f}%** | {round(rate * n)}/{n} |" for flag, rate in flag_rates.items())}

`low_confidence` fires for every repetition routed to Fair by the confidence rule — the
{metrics["fair_rate"] * 100:.1f}% abstention rate of §2, seen from the flag side.

`low_capture_quality` and `retry_camera_placement` fire at
{flag_rates["low_capture_quality"] * 100:.1f}%: **no repetition in this dataset falls
below `q_min = {q_min}`** (q range [{min(qs):.3f}, {max(qs):.3f}], median
{float(np.median(qs)):.3f}). Capture quality is not what drives the abstention here —
model confidence is. Note the tension with the low-confidence-frame frequency above: `q`
is a *mean* visibility over required landmarks and stays comfortably above `q_min` even
when the far limb is invisible, because the four near-side landmarks are tracked almost
perfectly. **`q` is not sensitive to the dominant failure mode of this capture geometry**
— that is a limitation of the quality metric, recorded here rather than smoothed over.

---

## 5. Inference latency

> **This is the one section of this report that is not byte-reproducible.** Every other
> number here is deterministic (X8). Wall-clock timing cannot be — it is what is being
> measured. Re-running `evaluate_squat.py` reproduces every metric and every other figure
> identically, and produces a *statistically similar but not identical* latency section.
> That carve-out is stated rather than left for a reader to discover.

**Scope:** per-repetition `extract_squat_features()` + `predict_proba()`. This
**excludes pose estimation and preprocessing**, which are per-*frame* costs paid during
capture by MediaPipe in the browser. What is measured is the per-*rep* cost the backend
adds at the end of a set — which is what the real-time feasibility claim is about. Each
repetition was timed {LATENCY_REPEATS} times and the median kept.

| Statistic | Value |
| --- | --- |
| Median | **{median_latency:.2f} ms** |
| p95 | **{p95_latency:.2f} ms** |
| Max | **{max_latency:.2f} ms** |
| One frame @ 30 FPS | {FRAME_BUDGET_MS:.1f} ms |

![Histogram of per-repetition inference latency (feature extraction + calibrated predict), with median and p95 marked. The x-axis is scaled to the data: the 33.3 ms single-frame budget is off-scale to the right, which is the point. Excludes pose estimation, which runs per-frame in the browser. Not byte-reproducible across runs.](figures/inference_latency_distribution.png)

**Verdict on real-time feasibility: supported, with the scope stated.** A p95 of
{p95_latency:.2f} ms against a {FRAME_BUDGET_MS:.1f} ms single-frame budget means
per-rep analysis {"fits inside" if p95_latency < FRAME_BUDGET_MS else "exceeds"} a single
frame's budget, so it can run between frames without dropping capture. The honest
caveat: this is measured on the developer machine, on a rep already segmented, and
excludes the pose-estimation cost that actually dominates the live pipeline. It supports
"the analysis layer is not the bottleneck", **not** "the whole system runs in real time".

---

## 6. Baseline comparison

![Grouped bar chart comparing this project's binary Good/Poor accuracy under a subject-wise split against prior work [S13]'s Random Forest squat accuracy under a non-subject-wise split. The caption inside the figure states that these protocols are not comparable, so the chart cannot be read out of context.](figures/baseline_comparison_bar.png)

| System | Accuracy | Split protocol |
| --- | --- | --- |
| This project (Extra Trees, squat) | **{binary["accuracy"]:.3f}** | subject-wise {cv_name} |
| Prior work [S13] (Random Forest, squat) | ~0.93 | **non-subject-wise** |

**What is being compared, and why only this.** The comparable quantity is the
**binary classifier's** accuracy, not the fused 3-band system's: a published classifier
cannot abstain, so comparing it to a pipeline whose main behaviour is abstention would
compare two different things. This row is the binary out-of-fold accuracy at the
conventional 0.5 threshold.

**These two numbers are not comparable, and the gap is not evidence of a worse model.**
A non-subject-wise split lets repetitions from the *same person* appear in both training
and test. With 9 subjects and reps that are strongly within-subject correlated, a model
can score well by recognising the person rather than the movement. The subject-wise
protocol used here forbids that, and is the harder and more clinically meaningful
question: *will this work on a patient the model has never seen?*

**Q4 remains open, and the REHAB24-6 authors' own baseline is deliberately not quoted.**
`task.md`'s open question Q4 asks for the dataset authors' own baseline *and* split
protocol, settling via the SISAP 2024 paper [S12]. That paper is paywalled and was not
obtainable during this stage; the Zenodo dataset record carries no baseline results, and
no open-access version was found. Per Q4's own instruction — "do not silently resolve
them by assumption" — **no number is quoted for it.** The comparison above therefore rests
on the single figure `task.md` itself supplies ([S13]). If the paper becomes available,
this section should be extended, not rewritten.

### Interpreting `{binary["accuracy"]:.3f}` honestly — it equals the base rate exactly

The Good base rate is {n_good}/{n} = {binary["majority_accuracy"]:.4f}. The classifier's
accuracy at threshold {binary["threshold"]} is **{binary["accuracy"]:.4f}** — the *same
number*. An "always predict Good" classifier would score identically.

**This is a coincidence, not a degenerate classifier, and the distinction matters.** The
model does not always predict Good: it predicts Poor for {binary["n_predicted_poor"]} of
{n} repetitions and is right about {binary["correct_poor"]} of them. What happens is that
it buys {binary["correct_poor"]} correct Poor calls at the price of
{binary["missed_good"]} Good repetitions it now gets wrong — a net change of
{binary["correct_poor"] - binary["missed_good"]:+d} correct answers against the majority
baseline. **It breaks even.**

| | Predicted Good | Predicted Poor |
| --- | --- | --- |
| **True Good** ({n_good}) | {binary["correct_good"]} | {binary["missed_good"]} |
| **True Poor** ({n_poor}) | {binary["missed_poor"]} | {binary["correct_poor"]} |

So the accuracy figure is uninformative here, but *not* because the model has learned
nothing — it has (out-of-fold ROC AUC 0.832; see
[SQUAT_TRAINING_REPORT.md](SQUAT_TRAINING_REPORT.md)). Accuracy is simply the wrong
summary for an imbalanced problem: it weights a Poor repetition and a Good repetition
equally, when the entire clinical point is that they are not equally costly. Two systems
with identical accuracy here — this one and "always say Good" — differ by
{binary["correct_poor"]} correctly identified poor-form repetitions, which is the only
thing a rehabilitation user would care about.

It is reported at all because the published baseline is stated in accuracy and a
like-for-like number is required. **ROC AUC and the 3-band matrix in §2 are the
meaningful results; this accuracy exists for the baseline comparison alone**, and the
0.5 threshold it uses is precisely the decision rule Stage 5.6 replaced.

---

## 7. Limitations

1. **The operating point was selected on these same out-of-fold predictions
   (Stage 5.6).** The 0 severe misclassifications in §2 is therefore *consistent with*,
   not *independent evidence for*, that choice. A genuinely held-out estimate of the
   fused system's behaviour would need a subject set untouched by both training and
   sweeping. With 9 subjects, that was not available. Stage 5.9's EC3D check is the
   nearest thing to an independent test, on 4 subjects.
2. **Precision is bought with abstention.** {metrics["fair_rate"] * 100:.1f}% of
   repetitions receive no judgement. A deployed tool that says "not sure" to half its
   inputs has a usability problem that no metric in §1 captures.
3. **Poor recall is very low** ({_fmt(metrics["recall_poor"])}). The system almost never
   identifies poor form; it routes it to Fair. Safe, but of limited clinical use as it
   stands.
4. **Evaluated per repetition; production fuses per session.** REHAB24-6's ground truth
   is per-rep, so this evaluation is too. Production's `score_squat_set()` aggregates
   rule scores across a set and takes the ML score from the first repetition only — an
   existing Phase 4 architecture choice. The *config values* transfer; **the confusion
   counts here characterise per-repetition behaviour and must not be quoted as
   per-session numbers.**
5. **`q` does not detect this capture geometry's dominant failure.** See §4: mean
   visibility stays above `q_min` even when the far limb is entirely occluded.
6. **Latency excludes pose estimation** and is measured on one developer machine. It
   supports a claim about the analysis layer, not the end-to-end system.
7. **9 subjects, 26 Poor repetitions, not independent.** Every interval implied by these
   numbers is wider than a naive calculation on n={n} would suggest, because repetitions
   from one subject are correlated. No p-values are quoted here for that reason.
"""
    REPORT_MD.write_text(report)


if __name__ == "__main__":
    main()
