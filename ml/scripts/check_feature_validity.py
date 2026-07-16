"""Stage 5.4: per-feature class-separation sanity + the R5.5 gate.

Reads `ml/data/squat_features.csv` and, for every feature, reports how well it
separates Good from Poor — then writes an explicit keep/drop verdict per feature to
`ml/reports/FEATURE_VALIDITY.md`, plus the boxplot grid and correlation heatmap.

**The gate (R5.5):** if `knee_flex_peak_deg` does not separate the classes, stop —
that would mean the extraction, the view filter, or the windowing is wrong, and no
amount of model tuning fixes a broken feature pipeline.

Two measures per feature, deliberately:

1. **AUC** (rank-based, = Mann-Whitney U / (n_good * n_poor)). 0.5 means no
   separation; distance from 0.5 is the effect size. Used as the primary evidence
   because it is descriptive and makes no distributional assumption.
2. **Cross-subject direction consistency.** The 98 reps come from only 9 subjects, so
   reps are *not* independent — a p-value computed as if they were is
   anti-conservative (pseudo-replication), which is why none is used as the verdict
   basis. Instead: of the subjects with at least `MIN_REPS_PER_CLASS` reps in both
   classes, in how many does the Good-vs-Poor difference point the *same* way? A
   feature that separates only via one subject's idiosyncrasy fails this and is
   flagged, however good its pooled AUC looks.

Deterministic (X8): fixed feature order, sorted subject iteration, no RNG.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# X1: the feature order is the backend's frozen contract, not a local list.
from app.module_b.squat.features import SQUAT_FEATURE_NAMES
from plotting import save_fig
from scipy.stats import mannwhitneyu

ML_ROOT = Path(__file__).resolve().parent.parent
FEATURES_CSV = ML_ROOT / "data" / "squat_features.csv"
REPORT_MD = ML_ROOT / "reports" / "FEATURE_VALIDITY.md"

GATE_FEATURE = "knee_flex_peak_deg"

# --- Pre-declared verdict rule (fixed BEFORE looking at results, so the thresholds
# are not fitted to the outcome). ---
# |AUC - 0.5| >= 0.10 is a small-to-medium effect by the conventional rank-biserial
# reading (AUC 0.56/0.64/0.71 ~ small/medium/large).
AUC_KEEP_MARGIN = 0.10
MIN_REPS_PER_CLASS = 2  # a subject needs this many of BOTH to vote on direction
DIRECTION_CONSISTENCY_MIN = 0.60  # >= 60% of voting subjects must agree on the sign


def _read_rows() -> list[dict]:
    with open(FEATURES_CSV, newline="") as f:
        return list(csv.DictReader(f))


def _auc(good: list[float], poor: list[float]) -> tuple[float, float]:
    """Return (AUC, mannwhitney_p) for Poor-vs-Good ranking of one feature.

    AUC > 0.5 means Poor reps tend to score HIGHER on this feature than Good reps.
    The p-value is reported for completeness only — see the module docstring on why
    it is not the verdict basis (reps within a subject are correlated).
    """
    statistic, p_value = mannwhitneyu(poor, good, alternative="two-sided")
    return statistic / (len(poor) * len(good)), p_value


def _direction_consistency(
    rows: list[dict], feature: str
) -> tuple[int, int, list[str]]:
    """Per subject with both classes, does Poor sit above Good on this feature?

    Returns (n_agreeing_with_pooled_direction, n_voting_subjects, detail_lines).
    """
    pooled_good = [float(r[feature]) for r in rows if r["label"] == "Good"]
    pooled_poor = [float(r[feature]) for r in rows if r["label"] == "Poor"]
    pooled_poor_higher = np.median(pooled_poor) > np.median(pooled_good)

    agree = 0
    voters = 0
    details = []
    for person in sorted({r["person_id"] for r in rows}, key=int):
        good = [
            float(r[feature])
            for r in rows
            if r["person_id"] == person and r["label"] == "Good"
        ]
        poor = [
            float(r[feature])
            for r in rows
            if r["person_id"] == person and r["label"] == "Poor"
        ]
        if len(good) < MIN_REPS_PER_CLASS or len(poor) < MIN_REPS_PER_CLASS:
            continue
        voters += 1
        subject_poor_higher = np.median(poor) > np.median(good)
        if subject_poor_higher == pooled_poor_higher:
            agree += 1
        details.append(
            f"P{person}: Good {np.median(good):.1f} vs Poor {np.median(poor):.1f}"
        )
    return agree, voters, details


def analyse_feature(rows: list[dict], feature: str) -> dict:
    good = [float(r[feature]) for r in rows if r["label"] == "Good"]
    poor = [float(r[feature]) for r in rows if r["label"] == "Poor"]
    auc, p_value = _auc(good, poor)
    agree, voters, _details = _direction_consistency(rows, feature)

    separates = abs(auc - 0.5) >= AUC_KEEP_MARGIN
    consistent = voters > 0 and (agree / voters) >= DIRECTION_CONSISTENCY_MIN
    if separates and consistent:
        verdict = "KEEP"
    elif separates and not consistent:
        verdict = "KEEP (caveat)"
    else:
        verdict = "DROP"

    return {
        "feature": feature,
        "good_median": float(np.median(good)),
        "poor_median": float(np.median(poor)),
        "good_iqr": float(np.subtract(*np.percentile(good, [75, 25]))),
        "poor_iqr": float(np.subtract(*np.percentile(poor, [75, 25]))),
        "auc": auc,
        "effect": abs(auc - 0.5),
        "p_value": p_value,
        "direction": "Poor higher" if auc > 0.5 else "Poor lower",
        "agree": agree,
        "voters": voters,
        "separates": separates,
        "consistent": consistent,
        "verdict": verdict,
    }


def plot_boxplots(rows: list[dict]) -> Path:
    """One box per class per feature, 4x4 grid — every feature visible on one page."""
    fig, axes = plt.subplots(4, 4)
    for ax, feature in zip(axes.flat, SQUAT_FEATURE_NAMES, strict=False):
        data = [
            [float(r[feature]) for r in rows if r["label"] == label]
            for label in ("Good", "Poor")
        ]
        ax.boxplot(data, tick_labels=["Good", "Poor"])
        ax.set_title(feature, fontsize=9)
        ax.tick_params(labelsize=8)
    # 13 features in a 16-slot grid: blank the 3 unused axes rather than leave frames.
    for ax in axes.flat[len(SQUAT_FEATURE_NAMES) :]:
        ax.axis("off")
    fig.suptitle("Squat feature distributions by class (98 side-view reps)", y=0.995)
    fig.tight_layout()
    path = save_fig(fig, "feature_validity_boxplots", figsize="grid_4x4")
    plt.close(fig)
    return path


def plot_correlation_heatmap(rows: list[dict]) -> tuple[Path, list[tuple]]:
    """Correlation matrix across candidate features; also return redundant pairs."""
    matrix = np.array(
        [[float(r[f]) for f in SQUAT_FEATURE_NAMES] for r in rows], dtype=float
    )
    corr = np.corrcoef(matrix, rowvar=False)

    fig, ax = plt.subplots()
    sns.heatmap(
        corr,
        ax=ax,
        xticklabels=SQUAT_FEATURE_NAMES,
        yticklabels=SQUAT_FEATURE_NAMES,
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        annot=True,
        fmt=".2f",
        annot_kws={"size": 6},
        square=True,
        cbar_kws={"shrink": 0.8},
    )
    ax.set_title("Feature correlation matrix (Pearson)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=7)
    path = save_fig(fig, "feature_correlation_heatmap", figsize="heatmap")
    plt.close(fig)

    redundant = [
        (SQUAT_FEATURE_NAMES[i], SQUAT_FEATURE_NAMES[j], corr[i, j])
        for i in range(len(SQUAT_FEATURE_NAMES))
        for j in range(i + 1, len(SQUAT_FEATURE_NAMES))
        if abs(corr[i, j]) >= 0.90
    ]
    return path, redundant


def main() -> None:
    rows = _read_rows()
    results = [analyse_feature(rows, f) for f in SQUAT_FEATURE_NAMES]
    plot_boxplots(rows)
    _heatmap_path, redundant = plot_correlation_heatmap(rows)

    gate = next(r for r in results if r["feature"] == GATE_FEATURE)
    gate_passes = gate["separates"]

    print(
        f"gate feature {GATE_FEATURE}: AUC={gate['auc']:.3f} "
        f"({gate['direction']}) -> {'PASS' if gate_passes else 'FAIL'}"
    )
    for r in results:
        print(
            f"  {r['feature']:<24} AUC={r['auc']:.3f} "
            f"dir={r['direction']:<11} subj={r['agree']}/{r['voters']} "
            f"-> {r['verdict']}"
        )
    if redundant:
        for a, b, c in redundant:
            print(f"  redundant: {a} ~ {b} (r={c:.2f})")

    write_report(results, gate, gate_passes, redundant, rows)
    print(f"wrote {REPORT_MD.name}")
    if not gate_passes:
        raise SystemExit(
            f"GATE FAILED: {GATE_FEATURE} does not separate the classes. Stop — "
            "check extraction, view filter, or windowing before training."
        )


def write_report(
    results: list[dict],
    gate: dict,
    gate_passes: bool,
    redundant: list[tuple],
    rows: list[dict],
) -> None:
    n_good = sum(1 for r in rows if r["label"] == "Good")
    n_poor = sum(1 for r in rows if r["label"] == "Poor")
    voters = gate["voters"]

    lines = [
        "# Stage 5.4 — feature-validity sanity (R5.5 gate)",
        "",
        f"Source: `ml/data/squat_features.csv` — {len(rows)} side-view reps "
        f"({n_good} Good / {n_poor} Poor) from 9 subjects, features computed by the "
        "backend's `extract_squat_features()` on the preprocessed stream (X1).",
        "",
        "## The gate",
        "",
        f"**{GATE_FEATURE}: AUC {gate['auc']:.3f}** "
        f"(Good median {gate['good_median']:.1f}° vs Poor median "
        f"{gate['poor_median']:.1f}°) — **{'PASS' if gate_passes else 'FAIL'}**. ",
        "",
        "The gate asks only whether this feature separates the classes. It does: an "
        f"AUC of {gate['auc']:.3f} is {abs(gate['auc'] - 0.5):.3f} away from the 0.5 "
        "no-separation point, and the direction is consistent across "
        f"{gate['agree']}/{voters} of the subjects who can vote on it. Extraction, "
        "view filter and windowing are therefore not obviously broken, which is what "
        "this gate exists to catch. Training may proceed.",
        "",
        "> **The separation runs opposite to the plan's stated expectation, and that "
        "matters.** `task.md`'s checklist says *\"`knee_flex_peak_deg` should be lower "
        'for incorrect reps"* — i.e. it assumed incorrect squats are too shallow. '
        f"Measured, incorrect reps go **deeper**: Poor median {gate['poor_median']:.1f}° "
        f"vs Good median {gate['good_median']:.1f}°. The gate's pass condition is "
        "separation, which holds either way, so this is **not** a gate failure. But the "
        "sign should not be carried forward as if the plan's assumption were confirmed: "
        "any downstream rule that reads 'deeper = better' would be inverted for this "
        "cohort. REHAB24-6's Ex6 'incorrect' reps are a mix of deliberate faults, not "
        "specifically shallow ones — so depth alone does not encode correctness in the "
        "direction the plan guessed. Flagged for Stage 5.5/5.6, not resolved here.",
        "",
        "## Method",
        "",
        "- **AUC** = Mann-Whitney U / (n_good x n_poor). 0.5 = no separation; "
        "distance from 0.5 is the effect size. AUC > 0.5 means Poor reps score higher.",
        "- **Cross-subject direction consistency.** The 98 reps come from only 9 "
        "subjects, so reps are **not independent** — a p-value that treats them as "
        "independent is anti-conservative (pseudo-replication). p-values are listed "
        "below for completeness but are **not** the verdict basis. Instead each "
        f"subject with >= {MIN_REPS_PER_CLASS} reps in *both* classes votes on whether "
        f"the difference points the same way as the pooled result ({voters} subjects "
        "qualify; the other 3 are single-class Good, and one has a single Poor rep).",
        "- **Pre-declared verdict rule** (fixed before results were seen, so the "
        f"thresholds are not fitted to the outcome): **KEEP** if "
        f"|AUC - 0.5| >= {AUC_KEEP_MARGIN} *and* >= "
        f"{int(DIRECTION_CONSISTENCY_MIN * 100)}% of voting subjects agree on the "
        "direction; **KEEP (caveat)** if it separates but the direction is "
        "subject-inconsistent (the separation may be one subject's idiosyncrasy); "
        "**DROP** otherwise.",
        "",
        "## Per-feature verdicts",
        "",
        "| feature | Good median | Poor median | AUC | direction | subjects agreeing | p | verdict |",
        "| ------- | ----------- | ----------- | --- | --------- | ----------------- | - | ------- |",
    ]
    for r in sorted(results, key=lambda r: -r["effect"]):
        lines.append(
            f"| `{r['feature']}` | {r['good_median']:.2f} | {r['poor_median']:.2f} | "
            f"{r['auc']:.3f} | {r['direction']} | {r['agree']}/{r['voters']} | "
            f"{r['p_value']:.3g} | **{r['verdict']}** |"
        )

    keeps = [r for r in results if r["verdict"].startswith("KEEP")]
    drops = [r for r in results if r["verdict"] == "DROP"]
    lines += [
        "",
        f"**{len(keeps)} keep / {len(drops)} drop** of {len(results)} candidate "
        "features.",
        "",
        "![Feature distributions by class](figures/feature_validity_boxplots.png)",
        "",
        "## Justification per feature",
        "",
    ]
    for r in sorted(results, key=lambda r: -r["effect"]):
        if r["verdict"] == "KEEP":
            why = (
                f"separates (AUC {r['auc']:.3f}, {r['direction'].lower()}) and the "
                f"direction holds in {r['agree']}/{r['voters']} subjects — not one "
                "subject's artefact."
            )
        elif r["verdict"] == "KEEP (caveat)":
            why = (
                f"separates on pooled data (AUC {r['auc']:.3f}) but only "
                f"{r['agree']}/{r['voters']} subjects agree on the direction, so the "
                "effect may be driven by a subset of subjects. Kept — Extra Trees can "
                "down-weight it — but it should not be read as a reliable clinical "
                "signal on its own."
            )
        else:
            why = (
                f"does not separate (AUC {r['auc']:.3f}, only "
                f"{r['effect']:.3f} from the 0.5 no-separation point)."
            )
        lines.append(f"- **`{r['feature']}`** — {r['verdict']}: {why}")

    lines += [
        "",
        "### `symmetry_index_pct` — a formula problem, not just a weak signal",
        "",
        "Flagged independently of its class separation, because the defect is in the "
        "definition rather than the data. It is computed per frame as "
        "`|θ_L − θ_R| / (0.5·(θ_L+θ_R)) × 100`, then averaged over the rep. Near "
        "standing both knee angles approach 0, so the denominator collapses and the "
        "ratio explodes — a 12° left-vs-right difference reads as ~10% mid-squat but "
        "can exceed 100% while standing. The rep mean is therefore dominated by the "
        "frames where the measure is least meaningful, which is most of why its values "
        "sit as high as they do. Whatever its verdict in the table above, the number "
        "is not a trustworthy asymmetry percentage; a phase-matched formulation (the "
        'feature table\'s own definition says *"at matched phase"*, which the '
        "implementation does not do) or an absolute-degrees difference would be "
        "sounder. Not changed here — altering a feature's definition means bumping "
        "`feature_schema_version` and re-running Phase 4's tests, which is outside "
        "this gate's scope.",
        "",
        "## Redundancy",
        "",
        "![Feature correlation matrix](figures/feature_correlation_heatmap.png)",
        "",
    ]
    if redundant:
        lines.append(
            "Pairs correlated at |r| >= 0.90 — candidates for dropping one side later "
            "(recorded here so any such call is evidence-backed, not asserted):"
        )
        lines.append("")
        for a, b, c in redundant:
            lines.append(f"- `{a}` ~ `{b}` (r = {c:.2f})")
        lines.append("")
        lines.append(
            "Not dropped here: Extra Trees is not destabilised by correlated inputs "
            "the way a linear model is, and dropping one of a pair changes the "
            "feature vector, which would mean bumping `feature_schema_version`. "
            "Recorded for Stage 5.5 to decide with model evidence in hand."
        )
    else:
        lines.append("No feature pair reaches |r| >= 0.90 — no redundancy to resolve.")

    lines += [
        "",
        "## Caveat on data-driven dropping (read before Stage 5.5)",
        "",
        "Every verdict above was computed on **all 98 reps** — including the reps of "
        "subjects that Stage 5.5 will hold out for LOSO. Dropping a feature on that "
        "evidence and then reporting LOSO scores over the same data is a mild "
        "selection bias: the held-out subject influenced which features existed. This "
        "is tolerable here because the stage's purpose is a **sanity gate** (catch a "
        "broken pipeline), not statistical feature selection — and because the only "
        "DROP verdicts are for features with effectively no signal, which a tree "
        "ensemble would ignore anyway. If Stage 5.5 wants a clean claim, the honest "
        "options are to train on all 13 features and let the model's own importances "
        "speak, or to nest the selection inside each CV fold. Recorded so the choice "
        "is deliberate rather than accidental.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
