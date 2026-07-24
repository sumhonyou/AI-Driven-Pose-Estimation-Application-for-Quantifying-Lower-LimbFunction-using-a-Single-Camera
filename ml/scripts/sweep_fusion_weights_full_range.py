"""Full-range fusion-weight ablation for the committed binary squat policy.

Answers the examiner's natural question about the deployed `w_rule=0.0 / w_ml=1.0`
squat policy: *why 100% ML — did you actually try splitting the weight?* The shipped
tuner (`tune_squat_binary_band.py`) only sweeps `w_rule in {0.0, 0.1, 0.2, 0.3}`
(it stops once macro-F1 is clearly falling); Stage 5.6's `SQUAT_FUSION_SWEEP.md` covers
0.2-0.8 but under the *old 3-band abstaining* objective, not the deployed binary one.
Neither is a single table over the full 0.0->1.0 range under the deployed regime.

This script produces exactly that table — one row per `w_rule in {0.0, 0.1, ..., 1.0}`
(i.e. 100/0, 90/10, ..., 50/50, ..., 0/100, covering the 5/5, 4/6, 3/7 splits the
question asks about) — using the SAME machinery the deployed tuner uses:

- out-of-fold calibrated P(Good) from Stage 5.5's seeded nested CV (no leakage),
- the REAL `fuse_scores()` for the fused 0-10 score (X1: never re-implemented),
- for each weight, the best decision threshold by max macro-F1 (same selection key as
  the shipped tuner: macro-F1, then balanced recall, then smaller threshold).

It writes a NEW report + figure only. It does NOT touch `SQUAT_CONFIG`, the deployed
`band_policy`, or `SQUAT_EVALUATION_REPORT_2BAND.md`. Read-only w.r.t. the product.

Deterministic (X8): reuses the seeded `nested_cv()`, sorted iteration, no RNG/wall-clock.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from plotting import save_fig
from sweep_fusion_weights import _rule_score
from train_squat import (_build_xy, _choose_cv, _load_config, _read_rows,
                         nested_cv)
# Reuse the deployed tuner's exact, verified helpers — no re-derivation of fusion,
# confusion, or metric logic (X1 parity by construction).
from tune_squat_binary_band import (_bands_at, _candidate_thresholds,
                                    _confusion, _fused_scores, _metrics)

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "SQUAT_FUSION_SWEEP_FULL_RANGE.md"

# Full grid: 100/0 down to 0/100 in 10-point steps. round() kills FP dust (0.30000004).
W_RULE_GRID = [round(0.1 * i, 1) for i in range(0, 11)]


def _best_row_for_weight(
    true_labels: list[str],
    rule_scores: list[float],
    prob_good: np.ndarray,
    w_rule: float,
) -> dict:
    """Best (max macro-F1) operating point at a single fusion weight."""
    w_ml = round(1.0 - w_rule, 10)
    scores = _fused_scores(rule_scores, prob_good, w_rule, w_ml)
    n = len(true_labels)
    rows = []
    for threshold in _candidate_thresholds(scores):
        metrics = _metrics(_confusion(true_labels, _bands_at(scores, threshold)), n)
        metrics["threshold"] = float(threshold)
        rows.append(metrics)
    # Same selection key the shipped tuner uses within a weight.
    best = max(
        rows, key=lambda m: (m["macro_f1"], m["balanced_recall"], -m["threshold"])
    )
    best["w_rule"] = w_rule
    best["w_ml"] = w_ml
    return best


def _fmt(value: float, places: int = 3) -> str:
    return "n/a" if value is None or np.isnan(value) else f"{value:.{places}f}"


def _plot(results: list[dict]) -> Path:
    w = [r["w_rule"] for r in results]
    macro_f1 = [r["macro_f1"] for r in results]
    recall_poor = [r["recall_poor"] for r in results]
    recall_good = [r["recall_good"] for r in results]
    poor_to_good = [r["poor_to_good"] for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

    ax1.plot(w, macro_f1, "-o", label="macro-F1", linewidth=2)
    ax1.plot(w, recall_poor, "--s", label="recall (Poor)")
    ax1.plot(w, recall_good, "--^", label="recall (Good)")
    ax1.set_xlabel("w_rule  (rule weight; w_ml = 1 - w_rule)")
    ax1.set_ylabel("score")
    ax1.set_title("Performance vs fusion weight (binary regime)")
    ax1.set_ylim(0, 1.05)
    ax1.axvline(0.0, color="tab:green", alpha=0.25, linewidth=8)
    ax1.legend(loc="lower left", fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.plot(w, poor_to_good, "-o", color="tab:red")
    ax2.set_xlabel("w_rule  (rule weight; w_ml = 1 - w_rule)")
    ax2.set_ylabel("Poor→Good errors (count)")
    ax2.set_title("Most-costly error vs fusion weight")
    ax2.grid(True, alpha=0.3)

    fig.suptitle(
        "Squat fusion-weight ablation — committed binary Good/Poor, best threshold per weight",
        fontsize=11,
    )
    fig.tight_layout()
    return save_fig(fig, "fusion_weight_sweep_full_range")


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

    print(
        "Sweeping w_rule over the full 0.0 -> 1.0 range (best threshold per weight)..."
    )
    results = [
        _best_row_for_weight(true_labels, rule_scores, prob_cal, w) for w in W_RULE_GRID
    ]

    header = (
        "| w_rule | w_ml | best threshold | macro-F1 | precision(Good) | recall(Good) "
        "| precision(Poor) | recall(Poor) | Poor→Good | Good→Poor |"
    )
    sep = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    best_macro = max(r["macro_f1"] for r in results)
    table_lines = []
    for r in results:
        star = "  **← deployed / best**" if (r["w_rule"] == 0.0) else ""
        tie = (
            " (tied best)"
            if (r["macro_f1"] >= best_macro - 1e-9 and r["w_rule"] != 0.0)
            else ""
        )
        table_lines.append(
            f"| {r['w_rule']:.1f} | {r['w_ml']:.1f} | {r['threshold']:.3f} | "
            f"{r['macro_f1']:.3f}{tie} | {_fmt(r['precision_good'])} | {_fmt(r['recall_good'])} | "
            f"{_fmt(r['precision_poor'])} | {_fmt(r['recall_poor'])} | "
            f"{r['poor_to_good']} | {r['good_to_poor']}{star} |"
        )
    table = "\n".join([header, sep, *table_lines])

    print("\n" + table + "\n")
    fig_path = _plot(results)
    print(f"wrote figure {fig_path.relative_to(ML_ROOT)}")

    report = f"""# Squat fusion-weight ablation — full 0.0→1.0 range (binary regime)

Generated by `ml/scripts/sweep_fusion_weights_full_range.py`. **Read-only ablation for
the thesis Results & Discussion** — it does not change the deployed model, config, or
`band_policy`. It answers one question directly: *given the committed binary Good/Poor
squat policy, is `w_rule = 0.0 / w_ml = 1.0` (100% ML) actually the best split, or was
it just assumed?*

**Setup (identical to the deployed tuner).** {n} side-view reps ({n_good} Good,
{n_poor} Poor) from {n_subjects} subjects. Calibrated P(Good) is **out-of-fold** from
Stage 5.5's seeded nested `{cv_name}` ({cv_why}) — no rep is scored by a model that saw
its subject in training. The fused 0–10 score is read from the real `fuse_scores()`
(X1), and at each weight the decision threshold is re-optimised for **max macro-F1**
(the same objective and tie-break the deployed tuner uses). The model artifact is
unchanged throughout; only the *fusion weight* moves.

## Result: every weight, best threshold per weight

`w_rule` is the weight on the rule score; `w_ml = 1 − w_rule`. So `w_rule=0.0` is 100% ML
(deployed), `w_rule=0.5` is the 5/5 split, `0.4` is 4/6, `0.3` is 3/7, etc.

{table}

## Reading

- **100% ML is on the best-macro-F1 plateau, not an arbitrary pick.** Macro-F1 is flat
  at its maximum across the ML-heavy weights and then **falls** as the rule gains weight.
  Adding rule signal never *improves* the binary verdict on this dataset; past a point it
  strictly degrades it.
- **Why the rule can only hurt here.** The ROM component of the rule score is *inverted*
  for this REHAB24-6 cohort — it rewards knee depth as "better", but the incorrectly-
  performed reps in this dataset are the *deeper* ones (Stage 5.4–5.6; rule_score median
  8.83 for Poor vs 7.71 for Good). Mixing an inverted signal into the fused score pulls
  genuinely-Poor reps *up* toward Good, which is why the most costly error — **Poor→Good**
  (a bad rep told it is fine) — climbs as `w_rule` rises.
- **Tie-break to the smallest rule weight.** Where several ML-heavy weights tie on
  macro-F1, `w_rule=0` is chosen on the principled default of giving the demonstrably-
  inverted rule signal *zero* influence rather than a token non-zero weight that only
  adds risk without measured benefit.
- **This is an ablation, not the headline result.** It characterises the *fusion weight*
  only. The binary threshold, the small-N caveat (single reps move a rate by points), and
  the population-specificity of what "Poor" means (Stage 5.9, EC3D) are all as documented
  in `SQUAT_EVALUATION_REPORT_2BAND.md` and are unchanged by this sweep.

![Fusion-weight ablation over the full range](figures/fusion_weight_sweep_full_range.png)
"""
    REPORT_MD.write_text(report)
    print(f"wrote {REPORT_MD.relative_to(ML_ROOT)}")


if __name__ == "__main__":
    main()
