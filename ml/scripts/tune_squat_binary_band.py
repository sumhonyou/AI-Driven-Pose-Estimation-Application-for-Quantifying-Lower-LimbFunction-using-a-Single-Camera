"""Stage 5.11: choose the committed binary Good/Poor operating point for squat.

Phase 4/5 shipped squat as a 3-band Good/Fair/Poor output, where **Fair is an
abstention** the fusion layer forces whenever calibrated confidence is below 0.85.
Because this model's confidence never exceeds ~0.76 (Stage 5.8), that override fires on
almost every rep and "Poor" is essentially never shown (3-band recall(Poor) ~ 0.077).
HY's decision (2026-07-19) is to make squat **commit** to Good or Poor on every rep, so
the app can actually flag a poor squat — accepting that removing abstention gives up the
3-band system's "zero severe misclassification" property.

The model itself is unchanged: this is a decision-policy choice, not a retrain. The
forest + sigmoid in `ml/artifacts/squat/` are byte-identical to Stage 5.8; nothing here
re-fits them. What is chosen here is a single **decision threshold on the fused 0-10
score** and the **fusion weight** behind it, selected for a binary objective.

Four decisions this stage makes, each justified rather than asserted:

1. **Objective = macro-F1 over Good/Poor (HY's "Balanced" choice).** Not accuracy —
   accuracy on a 73%-Good set is dominated by the majority class. Not recall(Poor) alone
   — maximising it collapses to "call everything Poor". Macro-F1 is the mean of F1(Good)
   and F1(Poor), so it weights the minority class up to parity and rewards catching Poor
   reps *without* drowning Good ones in false alarms.

2. **The fusion weight is re-swept, because Stage 5.6's `w_rule=0.2` was tuned for the
   abstention objective, not this one.** The ROM rule is inverted for this population
   (rewards depth; incorrect reps are deeper — Stage 5.4/5.5), so any rule weight pulls
   a deep/Poor rep's fused score *up* toward Good. The sweep is free to drive `w_rule`
   to 0 (pure ML) if that is what macro-F1 prefers; it is a data-driven outcome here,
   not an assumption.

3. **The threshold is placed at the midpoint of the winning plateau, not on a data
   point.** Many thresholds between two adjacent fused scores produce the identical
   confusion matrix; the shipped cut is the median of that plateau so it sits maximally
   far from any rep's score and cannot flip under a rounding-level perturbation (X8).

4. **Direction and reachability are asserted, not hoped.** At the chosen point,
   recall(Poor) must be > 0 (otherwise "Poor" is still unreachable and the whole change
   is pointless), and the reps called Poor must have a lower mean P(Good) than the reps
   called Good (guards against an inverted score silently shipping — the lunge-derived
   negative-Platt-slope hazard, here checked at the band level).

   What the hazard is: Platt scaling calibrates via a sigmoid,
   P = 1 / (1 + exp(a*raw_score + b)), and nothing in that fit constrains the sign of
   `a`. `train_squat.py`'s per-fold monotonicity assertion
   (`assert np.isclose(auc_uncal, auc_cal)`) implicitly assumes `a` comes out negative
   (higher raw score -> higher P(Good), the intended direction) and so a calibrated
   fold's AUC should equal its uncalibrated AUC. That assumption held for every squat
   fold in practice, but it is not guaranteed by the fitting procedure itself: on the
   now-removed lunge model, fit with the same code on a cohort where the inner folds'
   raw score anti-correlated with the label, the sigmoid legitimately fit a *positive*
   `a` in 2 of 5 folds, which reverses the ranking end to end and sends AUC to its
   mirror about 0.5 (one fold moved 0.554 -> 0.446 -> those two values sum to exactly
   1.000, confirming an exact reversal rather than noise). Had the calibrator been
   exported in that state, every live verdict would have been inverted -- the reported
   probability of good technique would *rise* as technique worsened -- and nothing
   downstream would detect it, because the probabilities remain perfectly well-formed.
   Squat's own slope has always come out negative, so `train_squat.py`'s assertion has
   never needed the reversal-tolerant form the lunge finding motivated, but it is the
   reason the check below does not simply trust the sign of the score: it independently
   re-verifies, on the actual banded output, that "Poor" reps score lower than "Good"
   reps, rather than assuming direction from the calibration step upstream.

Deterministic (X8): reuses Stage 5.5's seeded `nested_cv()` for the out-of-fold
calibrated P(Good), the real `fuse_scores()` for the fused score (X1 — the fusion blend
is never re-implemented), sorted iteration, no RNG, no wall-clock.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from app.module_b.core.fusion import fuse_scores
from evaluate_squat import plot_confusion_matrix_3band
# X1: the per-rep rule score comes from the same live helper Stage 5.6/5.7 use, not a
# re-derivation.
from sweep_fusion_weights import _rule_score
from train_squat import (_build_xy, _choose_cv, _load_config, _read_rows,
                         nested_cv)

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "SQUAT_EVALUATION_REPORT_2BAND.md"

# Binary-objective fusion-weight grid. Starts at 0.0 (pure ML) because the ROM rule is
# inverted for this population; steps up in case a little rule signal still helps.
W_RULE_CANDIDATES = [0.0, 0.1, 0.2, 0.3]

TRUE_LABELS = ("Good", "Poor")
PREDICTED_BANDS = ("Good", "Poor")


def _fused_scores(
    rule_scores: list[float], prob_good: np.ndarray, w_rule: float, w_ml: float
) -> np.ndarray:
    """Fused 0-10 score per rep from the REAL `fuse_scores()` (X1), one weight setting.

    The score a binary policy produces is `w_rule*rule + w_ml*10*P(Good)` — but it is
    read out of the live fusion function rather than recomputed here, so this sweep
    cannot silently disagree with what the backend will actually score. The threshold
    passed in is irrelevant to `.score`; it only affects `.band`, which is swept
    separately below.
    """
    policy = {
        "scheme": "binary",
        "w_rule": w_rule,
        "w_ml": w_ml,
        "decision_threshold": 5.0,
    }
    scores = []
    for p_good, rule in zip(prob_good, rule_scores, strict=True):
        result = fuse_scores(
            rule_score=rule,
            probabilities={"Good": float(p_good), "Poor": float(1.0 - p_good)},
            q=1.0,
            model_version="stage5.11-tune",
            is_placeholder_model=False,
            band_policy=policy,
        )
        scores.append(result.score)
    return np.array(scores, dtype=float)


def _confusion(true_labels: list[str], bands: list[str]) -> dict[tuple[str, str], int]:
    counts = {(t, p): 0 for t in TRUE_LABELS for p in PREDICTED_BANDS}
    for t, p in zip(true_labels, bands, strict=True):
        counts[(t, p)] += 1
    return counts


def _metrics(counts: dict[tuple[str, str], int], n: int) -> dict:
    """Precision/recall/F1 and macro-F1 over the two real classes, plus severe counts."""

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

    recall_good = recall("Good")
    recall_poor = recall("Poor")
    balanced_recall = min(
        recall_good if not np.isnan(recall_good) else 0.0,
        recall_poor if not np.isnan(recall_poor) else 0.0,
    )
    return {
        "precision_good": precision("Good"),
        "precision_poor": precision("Poor"),
        "recall_good": recall_good,
        "recall_poor": recall_poor,
        "f1_good": f1("Good"),
        "f1_poor": f1("Poor"),
        "macro_f1": (f1("Good") + f1("Poor")) / 2,
        "balanced_recall": balanced_recall,
        "poor_to_good": counts[("Poor", "Good")],
        "good_to_poor": counts[("Good", "Poor")],
        "severe_count": counts[("Poor", "Good")] + counts[("Good", "Poor")],
        "counts": counts,
        "n": n,
    }


def _bands_at(scores: np.ndarray, threshold: float) -> list[str]:
    return ["Good" if s >= threshold else "Poor" for s in scores]


def _candidate_thresholds(scores: np.ndarray) -> np.ndarray:
    """Midpoints between consecutive distinct fused scores — every meaningful cut."""
    unique = np.unique(np.round(scores, 6))
    return (unique[:-1] + unique[1:]) / 2.0


def sweep_operating_point(
    true_labels: list[str], rule_scores: list[float], prob_good: np.ndarray
) -> dict:
    """Scan (w_rule, threshold) for the max-macro-F1 committed binary operating point.

    Selection key (all deterministic): maximise macro-F1; break ties by the more
    balanced recall (higher min(recall_good, recall_poor)); then prefer the smaller
    w_rule (minimising the inverted ROM rule's influence, the same principled default
    Stage 5.6 used). The final threshold is the MEDIAN of the plateau of thresholds that
    all reproduce the winning confusion at the winning weight, so the shipped cut is not
    balanced on a knife-edge next to a rep's score.
    """
    n = len(true_labels)
    per_weight = []
    best_key: tuple[float, float, float] | None = None
    best = None

    for w_rule in W_RULE_CANDIDATES:
        w_ml = round(1.0 - w_rule, 10)
        scores = _fused_scores(rule_scores, prob_good, w_rule, w_ml)
        thresholds = _candidate_thresholds(scores)
        rows = []
        for threshold in thresholds:
            metrics = _metrics(_confusion(true_labels, _bands_at(scores, threshold)), n)
            metrics["threshold"] = float(threshold)
            rows.append(metrics)
        # Best row for this weight, by the same key used across weights.
        weight_best = max(
            rows, key=lambda m: (m["macro_f1"], m["balanced_recall"], -m["threshold"])
        )
        per_weight.append(
            {"w_rule": w_rule, "w_ml": w_ml, "scores": scores, "best": weight_best}
        )
        key = (weight_best["macro_f1"], weight_best["balanced_recall"], -w_rule)
        if best_key is None or key > best_key:
            best_key = key
            best = {"w_rule": w_rule, "w_ml": w_ml, "scores": scores, "rows": rows}

    # Median-of-plateau threshold: all thresholds whose confusion matches the winner's.
    winner_counts = max(
        best["rows"],
        key=lambda m: (m["macro_f1"], m["balanced_recall"], -m["threshold"]),
    )["counts"]
    plateau = [m["threshold"] for m in best["rows"] if m["counts"] == winner_counts]
    chosen_threshold = float(np.median(plateau))

    chosen_bands = _bands_at(best["scores"], chosen_threshold)
    chosen = _metrics(_confusion(true_labels, chosen_bands), n)
    chosen["threshold"] = chosen_threshold
    chosen["w_rule"] = best["w_rule"]
    chosen["w_ml"] = best["w_ml"]
    chosen["plateau"] = (float(min(plateau)), float(max(plateau)))
    return {"chosen": chosen, "per_weight": per_weight, "scores": best["scores"]}


def _assert_sane(chosen: dict, prob_good: np.ndarray, scores: np.ndarray) -> None:
    """Reachability + direction: the two ways this could ship broken and go unnoticed."""
    if not chosen["recall_poor"] > 0:
        raise AssertionError(
            "recall(Poor)=0 at the chosen threshold — 'Poor' would still be unreachable, "
            "which defeats the purpose of committing to a binary output."
        )
    predicted_poor = scores < chosen["threshold"]
    mean_p_good_poor = float(prob_good[predicted_poor].mean())
    mean_p_good_good = float(prob_good[~predicted_poor].mean())
    if not mean_p_good_poor < mean_p_good_good:
        raise AssertionError(
            "Reps banded Poor have a HIGHER mean P(Good) than reps banded Good — the "
            "fused score is inverted relative to the model. Shipping this would flip "
            "every verdict (the negative-Platt-slope hazard, at the band level)."
        )


def main() -> None:
    config = _load_config()
    seed = int(config["seeds"]["sklearn"])
    rows = _read_rows()
    x, y, groups = _build_xy(rows)
    true_labels = ["Good" if v == 1 else "Poor" for v in y]
    n = len(rows)
    n_good = int((y == 1).sum())
    n_poor = n - n_good
    n_subjects = len(np.unique(groups))
    print(f"loaded {n} reps ({n_good} Good / {n_poor} Poor) from {n_subjects} subjects")

    outer_cv, cv_name, cv_why = _choose_cv(y, groups)
    print("Re-running Stage 5.5's nested CV for out-of-fold calibrated P(Good)...")
    _prob_uncal, prob_cal, _folds = nested_cv(x, y, groups, outer_cv, seed)

    print("Computing per-repetition rule scores (score_squat_rep)...")
    rule_scores = [_rule_score(row) for row in rows]

    print("Sweeping (w_rule, decision_threshold) for max macro-F1...")
    sweep = sweep_operating_point(true_labels, rule_scores, prob_cal)
    chosen = sweep["chosen"]
    _assert_sane(chosen, prob_cal, sweep["scores"])

    print(
        f"  CHOSEN: w_rule={chosen['w_rule']}, w_ml={chosen['w_ml']}, "
        f"decision_threshold={chosen['threshold']:.4f} "
        f"(plateau [{chosen['plateau'][0]:.3f}, {chosen['plateau'][1]:.3f}])"
    )
    print(
        f"  macro-F1={chosen['macro_f1']:.3f}  recall(Good)={chosen['recall_good']:.3f} "
        f" recall(Poor)={chosen['recall_poor']:.3f}  "
        f"severe={chosen['severe_count']} "
        f"(Poor->Good {chosen['poor_to_good']}, Good->Poor {chosen['good_to_poor']})"
    )

    plot_confusion_matrix_3band(
        chosen,
        predicted_bands=PREDICTED_BANDS,
        true_labels=TRUE_LABELS,
        name="confusion_matrix_2band",
        title_prefix="Committed binary output vs ground truth",
        subtitle=f"counts, row-normalised %; n={n} side-view reps",
        caption=(
            "Shading = row-normalised recall. Committed Good/Poor: every rep is judged, "
            "there is no abstention,\nso BOTH off-diagonal cells are severe errors "
            "(Poor→Good and Good→Poor)."
        ),
    )

    write_report(
        rows=rows,
        cv_name=cv_name,
        cv_why=cv_why,
        n=n,
        n_good=n_good,
        n_poor=n_poor,
        n_subjects=n_subjects,
        sweep=sweep,
        chosen=chosen,
    )
    print(f"wrote {REPORT_MD.name}")
    print(
        "\nCopy into backend/app/module_b/squat/config.py SQUAT_CONFIG['band_policy']:\n"
        f'  "decision_threshold": {chosen["threshold"]!r},\n'
        f'  "w_rule": {chosen["w_rule"]!r}, "w_ml": {chosen["w_ml"]!r}'
    )


def _fmt(value: float, places: int = 3) -> str:
    return "n/a" if np.isnan(value) else f"{value:.{places}f}"


def write_report(
    *, rows, cv_name, cv_why, n, n_good, n_poor, n_subjects, sweep, chosen
) -> None:
    counts = chosen["counts"]
    confusion_rows = "\n".join(
        f"| **{t}** (n={sum(counts[(t, p)] for p in PREDICTED_BANDS)}) | "
        + " | ".join(str(counts[(t, p)]) for p in PREDICTED_BANDS)
        + " |"
        for t in TRUE_LABELS
    )
    weight_rows = "\n".join(
        f"| {pw['w_rule']:.1f} | {pw['w_ml']:.1f} | {pw['best']['macro_f1']:.3f} | "
        f"{_fmt(pw['best']['recall_good'])} | {_fmt(pw['best']['recall_poor'])} | "
        f"{pw['best']['severe_count']} |"
        + ("  **<- chosen weight**" if pw["w_rule"] == chosen["w_rule"] else "")
        for pw in sweep["per_weight"]
    )

    report = f"""# Squat Evaluation Report — committed binary Good/Poor (Stage 5.11)

Generated by `ml/scripts/tune_squat_binary_band.py`. This is the **deployed** squat
policy as of Stage 5.11: the app commits to a binary **Good/Poor** verdict on every rep.
The earlier 3-band abstaining evaluation is preserved in
[SQUAT_EVALUATION_REPORT_3BAND.md](SQUAT_EVALUATION_REPORT_3BAND.md) as the historical
record; it is no longer the shipped behaviour.

**The model is unchanged.** The forest and sigmoid in `ml/artifacts/squat/` are
byte-identical to Stage 5.8 — this stage chose a *decision policy* (a threshold and a
fusion weight), not a new model. Probabilities are **out-of-fold** from Stage 5.5's
nested `{cv_name}` ({cv_why}); no rep is scored by a model that saw its subject in
training.

**Evaluation set:** {n} side-view squat repetitions from {n_subjects} subjects
({n_good} Good, {n_poor} Poor).

---

## 1. What changed and why

Phase 4/5 shipped a 3-band Good/Fair/Poor output in which **Fair was an abstention**:
the fusion layer forced Fair whenever calibrated confidence fell below 0.85. This
model's confidence never exceeds ~0.76, so that override fired on almost every rep and
"Poor" was effectively never shown (3-band recall(Poor) ~ 0.077). That design bought a
*zero severe-misclassification* guarantee at the cost of never actually flagging poor
form.

HY's decision (2026-07-19) is to **commit** to Good or Poor on every rep so the app can
flag poor form, explicitly accepting the trade-off: without abstention, some severe
errors will occur. This report measures that trade-off honestly rather than hiding it.

## 2. Operating point

Chosen for **maximum macro-F1** over Good/Poor (HY's "Balanced" preference), swept
jointly over the fusion weight and the score threshold:

| Parameter | Value |
| --- | --- |
| `w_rule` / `w_ml` | **{chosen["w_rule"]} / {chosen["w_ml"]}** |
| `decision_threshold` (on the fused 0-10 score) | **{chosen["threshold"]:.4f}** |
| threshold plateau (all give the same matrix) | [{chosen["plateau"][0]:.3f}, {chosen["plateau"][1]:.3f}] |

The threshold is the **median of the plateau** so it sits far from any rep's score (X8).

### Fusion-weight sweep (best threshold per weight)

The ROM rule is inverted for this population (it rewards depth, but incorrect reps are
deeper — Stage 5.4/5.5), so any rule weight pulls a Poor rep's fused score up toward
Good. The sweep is free to prefer pure ML:

| w_rule | w_ml | macro-F1 | recall(Good) | recall(Poor) | severe |
| --- | --- | --- | --- | --- | --- |
{weight_rows}

## 3. Confusion matrix (committed binary output)

| True \\ Predicted | {" | ".join(PREDICTED_BANDS)} |
| --- | --- | --- |
{confusion_rows}

![Committed binary Good/Poor output vs REHAB24-6 ground truth. Rows are ground truth, columns are the band the user is shown. Both off-diagonal cells are severe errors — with no abstention there is nowhere else for an uncertain rep to go.](figures/confusion_matrix_2band.png)

| Metric | Value |
| --- | --- |
| macro-F1 | **{_fmt(chosen["macro_f1"])}** |
| precision(Good) / recall(Good) | {_fmt(chosen["precision_good"])} / {_fmt(chosen["recall_good"])} |
| precision(Poor) / recall(Poor) | {_fmt(chosen["precision_poor"])} / {_fmt(chosen["recall_poor"])} |
| severe misclassifications | **{chosen["severe_count"]}** (Poor→Good {chosen["poor_to_good"]}, Good→Poor {chosen["good_to_poor"]}) |

## 4. Honest reading of the trade-off

- **"Poor" is now reachable.** recall(Poor) rises from ~0.077 (3-band) to
  **{_fmt(chosen["recall_poor"])}** here — the system now flags roughly
  {chosen["recall_poor"] * 100:.0f}% of poor reps instead of almost none.
- **The zero-severe guarantee is gone, by design.** There are now
  {chosen["severe_count"]} severe misclassifications ({chosen["poor_to_good"]} Poor
  reps called Good, {chosen["good_to_poor"]} Good reps called Poor). The most costly
  case in a rehab setting — a poor-form rep told it is fine — occurs
  {chosen["poor_to_good"]} time(s) here. This is the price of committing, and it is
  reported rather than abstracted away.
- **Same small-N caveat as every squat report.** {n} reps, {n_poor} Poor, from
  {n_subjects} subjects, out-of-fold — the per-cell counts are small integers and a
  single rep changing hands moves a rate by several points. Treat these as the honest
  order of magnitude, not precise estimates.
- **What "Poor" means.** The classifier learned "resembles REHAB24-6's incorrect reps",
  which in this cohort skew deeper/faster — not a clinical "you exceeded a safe angle"
  rule. Stage 5.9 showed this construct is population-specific (it did not transfer to
  EC3D). The binary commitment does not change that; it only stops hiding the verdict
  behind abstention.

## 5. Deliberately not done here

- **No retrain, no re-export.** The forest/sigmoid are unchanged; only the fusion
  decision policy moved. `model_version` is unchanged for the same reason.
- **ROM rule not realigned.** It still rewards depth; the binary sweep simply weights it
  down (or to 0). Realigning it so excessive depth lowers the score is a separate,
  deliberately-deferred change (HY, 2026-07-19).
- **Squat only.** Lunge (placeholder model) and Module A keep their 3-band schemes.
"""
    REPORT_MD.write_text(report)


if __name__ == "__main__":
    main()
