"""Stage 5.4 (Lunge): per-feature class-separation sanity + the R5.5 gate.

The lunge mirror of `check_feature_validity.py`. Reads `ml/data/lunge_features.csv`
and, for every feature, reports how well it separates Good from Poor — then writes an
explicit keep/drop verdict per feature to `ml/reports/LUNGE_FEATURE_VALIDITY.md`, plus
the boxplot grid and correlation heatmap.

**The gate (R5.5):** if the primary depth feature does not separate the classes, stop —
that would mean the extraction, the view filter, or the windowing is wrong.

Deltas from squat, and why:

- **`GATE_FEATURE = "front_knee_flex_peak_deg"`**, not `knee_flex_peak_deg`. A lunge is
  asymmetric, so there is no bilateral-mean depth feature to gate on; the front knee is
  the one the movement is about and the one squat's gate feature corresponds to.
- **17 features in a 5x4 grid**, against squat's 13 in 4x4.
- **The verdict rule below is squat's, unchanged and deliberately so.** It was fixed
  before squat's results were seen; re-picking the thresholds now, with lunge's numbers
  already on disk from Stage 5.3, would be fitting the rule to the outcome. Reusing it
  keeps it pre-declared for lunge too.

Deterministic (X8): fixed feature order, sorted subject iteration, no RNG.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# X1: the feature order is the backend's frozen contract, not a local list.
from app.module_b.lunge.features import LUNGE_FEATURE_NAMES
from plotting import save_fig
from scipy.stats import mannwhitneyu

ML_ROOT = Path(__file__).resolve().parent.parent
FEATURES_CSV = ML_ROOT / "data" / "lunge_features.csv"
REPORT_MD = ML_ROOT / "reports" / "LUNGE_FEATURE_VALIDITY.md"

GATE_FEATURE = "front_knee_flex_peak_deg"
# The clearest instance of the pooling reversal documented in the report; its
# mechanism is measured by `pooling_confound()` rather than asserted.
PARADOX_FEATURE = "back_knee_rom_deg"

# --- Verdict rule: squat's, reused unchanged (see module docstring). ---
AUC_KEEP_MARGIN = 0.10
MIN_REPS_PER_CLASS = 2  # a subject needs this many of BOTH to vote on direction
DIRECTION_CONSISTENCY_MIN = 0.60  # >= 60% of voting subjects must agree on the sign


def _read_rows() -> list[dict]:
    with open(FEATURES_CSV, newline="") as f:
        return list(csv.DictReader(f))


def _auc(good: list[float], poor: list[float]) -> tuple[float, float]:
    """Return (AUC, mannwhitney_p) for Poor-vs-Good ranking of one feature.

    AUC > 0.5 means Poor reps tend to score HIGHER on this feature than Good reps.
    The p-value is reported for completeness only — reps within a subject are
    correlated, so it is not the verdict basis.
    """
    statistic, p_value = mannwhitneyu(poor, good, alternative="two-sided")
    return statistic / (len(poor) * len(good)), p_value


def _direction_consistency(
    rows: list[dict], feature: str
) -> tuple[int, int, list[str]]:
    """Per subject with both classes, does Poor sit above Good on this feature?"""
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


def _within_subject_auc(rows: list[dict], feature: str) -> float | None:
    """AUC after subtracting each subject's own median — a diagnostic, not a verdict.

    The pooled AUC mixes two sources of variation: the Good-vs-Poor difference we want,
    and the (much larger) differences in how subjects are built and move. Subtracting
    each subject's own median removes the second, leaving the within-subject effect.

    Centring uses **no label information** — the median is taken over all of a
    subject's reps regardless of class — so this does not leak the outcome into its own
    diagnostic. Single-class subjects are excluded (they cannot contribute a
    within-subject contrast).

    **This is NOT achievable accuracy.** At inference the model sees one rep and has no
    subject median to subtract, so a high within-subject AUC does not promise a good
    classifier. It answers only "does this feature carry a real signal that pooling is
    masking?" — which is exactly what a keep/drop verdict needs to know.
    """
    centred: list[dict] = []
    for person in sorted({r["person_id"] for r in rows}, key=int):
        subject_rows = [r for r in rows if r["person_id"] == person]
        if len({r["label"] for r in subject_rows}) < 2:
            continue
        median = np.median([float(r[feature]) for r in subject_rows])
        centred.extend(
            {"label": r["label"], feature: float(r[feature]) - median}
            for r in subject_rows
        )
    good = [r[feature] for r in centred if r["label"] == "Good"]
    poor = [r[feature] for r in centred if r["label"] == "Poor"]
    if not good or not poor:
        return None
    return _auc(good, poor)[0]


def analyse_feature(rows: list[dict], feature: str) -> dict:
    good = [float(r[feature]) for r in rows if r["label"] == "Good"]
    poor = [float(r[feature]) for r in rows if r["label"] == "Poor"]
    auc, p_value = _auc(good, poor)
    agree, voters, _details = _direction_consistency(rows, feature)
    within_auc = _within_subject_auc(rows, feature)

    separates = abs(auc - 0.5) >= AUC_KEEP_MARGIN
    consistent = voters > 0 and (agree / voters) >= DIRECTION_CONSISTENCY_MIN
    if separates and consistent:
        verdict = "KEEP"
    elif separates and not consistent:
        verdict = "KEEP (caveat)"
    else:
        verdict = "DROP"

    # Flag where the pooled verdict and the within-subject evidence disagree. The
    # verdict itself is NOT changed by this (the rule is pre-declared) -- it is
    # surfaced so a DROP that pooling caused is visible rather than silent.
    within_effect = None if within_auc is None else abs(within_auc - 0.5)
    pooling_misleads = within_effect is not None and (
        (not separates and within_effect >= AUC_KEEP_MARGIN)
        or ((auc > 0.5) != (within_auc > 0.5) and within_effect >= AUC_KEEP_MARGIN)
    )

    return {
        "feature": feature,
        "good_median": float(np.median(good)),
        "poor_median": float(np.median(poor)),
        "good_iqr": float(np.subtract(*np.percentile(good, [75, 25]))),
        "poor_iqr": float(np.subtract(*np.percentile(poor, [75, 25]))),
        "auc": auc,
        "effect": abs(auc - 0.5),
        "within_auc": within_auc,
        "within_effect": within_effect,
        "pooling_misleads": pooling_misleads,
        "p_value": p_value,
        "direction": "Poor higher" if auc > 0.5 else "Poor lower",
        "agree": agree,
        "voters": voters,
        "separates": separates,
        "consistent": consistent,
        "verdict": verdict,
    }


def per_cohort_gate(rows: list[dict]) -> dict[str, dict]:
    """The gate feature's AUC within each lead-leg cohort, computed separately.

    Stage 5.0 found lead_leg perfectly confounded with subject, so the pooled AUC
    mixes two disjoint subject groups. If the gate only passes pooled but fails in
    both cohorts, the "separation" would be a between-cohort offset rather than a
    within-subject effect — worth knowing before training.
    """
    out = {}
    for lead in sorted({r["lead_leg"] for r in rows}):
        cohort = [r for r in rows if r["lead_leg"] == lead]
        good = [float(r[GATE_FEATURE]) for r in cohort if r["label"] == "Good"]
        poor = [float(r[GATE_FEATURE]) for r in cohort if r["label"] == "Poor"]
        if not good or not poor:
            out[lead] = {"n": len(cohort), "auc": None}
            continue
        auc, _p = _auc(good, poor)
        out[lead] = {
            "n": len(cohort),
            "n_good": len(good),
            "n_poor": len(poor),
            "auc": auc,
            "good_median": float(np.median(good)),
            "poor_median": float(np.median(poor)),
        }
    return out


def plot_boxplots(rows: list[dict]) -> Path:
    """One box per class per feature, 5x4 grid — every feature visible on one page."""
    fig, axes = plt.subplots(5, 4)
    for ax, feature in zip(axes.flat, LUNGE_FEATURE_NAMES, strict=False):
        data = [
            [float(r[feature]) for r in rows if r["label"] == label]
            for label in ("Good", "Poor")
        ]
        ax.boxplot(data, tick_labels=["Good", "Poor"])
        ax.set_title(feature, fontsize=9)
        ax.tick_params(labelsize=8)
    # 17 features in a 20-slot grid: blank the 3 unused axes rather than leave frames.
    for ax in axes.flat[len(LUNGE_FEATURE_NAMES) :]:
        ax.axis("off")
    fig.suptitle(
        f"Lunge feature distributions by class ({len(rows)} side-view reps)", y=0.995
    )
    fig.tight_layout()
    path = save_fig(fig, "lunge_feature_validity_boxplots", figsize="grid_5x4")
    plt.close(fig)
    return path


def plot_correlation_heatmap(rows: list[dict]) -> tuple[Path, list[tuple]]:
    """Correlation matrix across candidate features; also return redundant pairs."""
    matrix = np.array(
        [[float(r[f]) for f in LUNGE_FEATURE_NAMES] for r in rows], dtype=float
    )
    corr = np.corrcoef(matrix, rowvar=False)

    fig, ax = plt.subplots()
    sns.heatmap(
        corr,
        ax=ax,
        xticklabels=LUNGE_FEATURE_NAMES,
        yticklabels=LUNGE_FEATURE_NAMES,
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        annot=True,
        fmt=".2f",
        annot_kws={"size": 5},
        square=True,
        cbar_kws={"shrink": 0.8},
    )
    ax.set_title("Lunge feature correlation matrix (Pearson)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=6)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=6)
    path = save_fig(fig, "lunge_feature_correlation_heatmap", figsize="heatmap")
    plt.close(fig)

    redundant = [
        (LUNGE_FEATURE_NAMES[i], LUNGE_FEATURE_NAMES[j], corr[i, j])
        for i in range(len(LUNGE_FEATURE_NAMES))
        for j in range(i + 1, len(LUNGE_FEATURE_NAMES))
        if abs(corr[i, j]) >= 0.90
    ]
    return path, redundant


def pooling_confound(rows: list[dict], feature: str) -> dict:
    """Measure WHY pooling reverses a feature, rather than asserting a cause.

    A pooled median can invert every subject's own direction (Simpson's paradox) when
    subject-level *level* correlates with subject-level *class mix*: a subject who sits
    low on the feature and contributes mostly Poor reps drags the pooled Poor median
    down, even if that subject's own Poor reps sit above their own Good reps.

    Returns the per-subject levels and mixes plus their correlation, so the mechanism
    is evidenced rather than claimed.
    """
    subjects = sorted({r["person_id"] for r in rows}, key=int)
    detail = []
    for person in subjects:
        subject_rows = [r for r in rows if r["person_id"] == person]
        n_poor = sum(1 for r in subject_rows if r["label"] == "Poor")
        detail.append(
            {
                "person": person,
                "lead_leg": subject_rows[0]["lead_leg"],
                "n": len(subject_rows),
                "n_good": len(subject_rows) - n_poor,
                "n_poor": n_poor,
                "poor_fraction": n_poor / len(subject_rows),
                "median": float(np.median([float(r[feature]) for r in subject_rows])),
            }
        )
    levels = [d["median"] for d in detail]
    mixes = [d["poor_fraction"] for d in detail]

    # Drop the single-class subject with the most extreme level and re-pool, to show
    # the reversal is that one subject's doing rather than a diffuse cohort effect.
    single_class = [d for d in detail if d["n_good"] == 0 or d["n_poor"] == 0]
    culprit = min(single_class, key=lambda d: d["median"]) if single_class else None
    auc_without_culprit = None
    if culprit is not None:
        remaining = [r for r in rows if r["person_id"] != culprit["person"]]
        auc_without_culprit = _auc(
            [float(r[feature]) for r in remaining if r["label"] == "Good"],
            [float(r[feature]) for r in remaining if r["label"] == "Poor"],
        )[0]

    return {
        "detail": detail,
        "level_vs_mix_r": float(np.corrcoef(levels, mixes)[0, 1]),
        "culprit": culprit,
        "auc_without_culprit": auc_without_culprit,
    }


def main() -> None:
    rows = _read_rows()
    results = [analyse_feature(rows, f) for f in LUNGE_FEATURE_NAMES]
    plot_boxplots(rows)
    _heatmap_path, redundant = plot_correlation_heatmap(rows)

    gate = next(r for r in results if r["feature"] == GATE_FEATURE)
    gate_passes = gate["separates"]
    cohorts = per_cohort_gate(rows)

    print(
        f"gate feature {GATE_FEATURE}: AUC={gate['auc']:.3f} "
        f"({gate['direction']}) -> {'PASS' if gate_passes else 'FAIL'}"
    )
    for lead, c in sorted(cohorts.items()):
        if c["auc"] is None:
            print(f"  cohort lead={lead}: n={c['n']} (single class, no AUC)")
        else:
            print(
                f"  cohort lead={lead}: n={c['n']} "
                f"({c['n_good']}G/{c['n_poor']}P) AUC={c['auc']:.3f}"
            )
    for r in results:
        within = "  n/a" if r["within_auc"] is None else f"{r['within_auc']:.3f}"
        flag = "  <-- POOLING MISLEADS" if r["pooling_misleads"] else ""
        print(
            f"  {r['feature']:<28} AUC={r['auc']:.3f} within={within} "
            f"dir={r['direction']:<11} subj={r['agree']}/{r['voters']} "
            f"-> {r['verdict']}{flag}"
        )
    if redundant:
        for a, b, c in redundant:
            print(f"  redundant: {a} ~ {b} (r={c:.2f})")

    confound = pooling_confound(rows, PARADOX_FEATURE)
    print(
        f"pooling confound on {PARADOX_FEATURE}: corr(subject level, subject %Poor) "
        f"= {confound['level_vs_mix_r']:+.3f}"
    )

    write_report(results, gate, gate_passes, redundant, rows, cohorts, confound)
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
    cohorts: dict[str, dict],
    confound: dict,
) -> None:
    n_good = sum(1 for r in rows if r["label"] == "Good")
    n_poor = sum(1 for r in rows if r["label"] == "Poor")
    n_subjects = len({r["person_id"] for r in rows})
    voters = gate["voters"]

    lines = [
        "# Stage 5.4 (Lunge) — feature-validity sanity (R5.5 gate)",
        "",
        f"Source: `ml/data/lunge_features.csv` — {len(rows)} side-view reps "
        f"({n_good} Good / {n_poor} Poor) from {n_subjects} subjects, features computed "
        "by the backend's `extract_lunge_features()` on the preprocessed stream (X1).",
        "",
        "## The gate",
        "",
        f"**{GATE_FEATURE}: AUC {gate['auc']:.3f}** "
        f"(Good median {gate['good_median']:.1f}° vs Poor median "
        f"{gate['poor_median']:.1f}°) — **{'PASS' if gate_passes else 'FAIL'}**.",
        "",
        "The gate feature is `front_knee_flex_peak_deg`, not squat's "
        "`knee_flex_peak_deg`: a lunge is asymmetric, so no bilateral-mean depth "
        "feature exists to gate on, and the front knee is both what the movement is "
        "about and the direct correspondent of squat's gate feature.",
        "",
        f"The gate asks only whether this feature separates the classes. An AUC of "
        f"{gate['auc']:.3f} is {abs(gate['auc'] - 0.5):.3f} away from the 0.5 "
        f"no-separation point, and the direction is consistent across "
        f"{gate['agree']}/{voters} of the subjects who can vote on it.",
        "",
    ]

    lines += [
        "### The gate within each lead-leg cohort",
        "",
        "Stage 5.0 established that **lead leg is perfectly confounded with subject** — "
        "no subject performs both. So the pooled AUC above mixes two disjoint subject "
        "groups, and a pooled separation could in principle be a between-cohort offset "
        "rather than a real within-subject effect. Computed separately:",
        "",
        "| cohort | n reps | Good median | Poor median | AUC |",
        "| ------ | ------ | ----------- | ----------- | --- |",
    ]
    for lead in sorted(cohorts):
        c = cohorts[lead]
        if c["auc"] is None:
            lines.append(f"| lead={lead} | {c['n']} | — | — | single class |")
        else:
            lines.append(
                f"| lead={lead} | {c['n']} ({c['n_good']}G/{c['n_poor']}P) | "
                f"{c['good_median']:.1f}° | {c['poor_median']:.1f}° | {c['auc']:.3f} |"
            )
    lines.append("")

    lines += [
        "## Method",
        "",
        "- **AUC** = Mann-Whitney U / (n_good x n_poor). 0.5 = no separation; "
        "distance from 0.5 is the effect size. AUC > 0.5 means Poor reps score higher.",
        f"- **Cross-subject direction consistency.** The {len(rows)} reps come from only "
        f"{n_subjects} subjects, so reps are **not independent** — a p-value that treats "
        "them as independent is anti-conservative (pseudo-replication). p-values are "
        "listed below for completeness but are **not** the verdict basis. Instead each "
        f"subject with >= {MIN_REPS_PER_CLASS} reps in *both* classes votes on whether "
        f"the difference points the same way as the pooled result ({voters} of "
        f"{n_subjects} subjects qualify).",
        "- **The verdict rule is squat's, reused unchanged and deliberately so:** "
        f"**KEEP** if |AUC - 0.5| >= {AUC_KEEP_MARGIN} *and* >= "
        f"{int(DIRECTION_CONSISTENCY_MIN * 100)}% of voting subjects agree on the "
        "direction; **KEEP (caveat)** if it separates but the direction is "
        "subject-inconsistent; **DROP** otherwise. The rule was fixed before squat's "
        "results were seen. Re-picking thresholds now — with lunge's numbers already on "
        "disk from Stage 5.3 — would be fitting the rule to the outcome, so it is "
        "carried over as-is.",
        "",
        "## Per-feature verdicts",
        "",
        "The **within-subject AUC** column is a diagnostic, not part of the verdict "
        "rule — see the section below it, which is the most consequential finding of "
        "this gate. ⚠ marks a feature whose pooled verdict the within-subject evidence "
        "contradicts.",
        "",
        "| feature | Good median | Poor median | AUC | within-subj AUC | direction | subjects agreeing | p | verdict |",
        "| ------- | ----------- | ----------- | --- | --------------- | --------- | ----------------- | - | ------- |",
    ]
    for r in sorted(results, key=lambda r: -r["effect"]):
        within = "n/a" if r["within_auc"] is None else f"{r['within_auc']:.3f}"
        flag = " ⚠" if r["pooling_misleads"] else ""
        lines.append(
            f"| `{r['feature']}` | {r['good_median']:.2f} | {r['poor_median']:.2f} | "
            f"{r['auc']:.3f} | {within}{flag} | {r['direction']} | "
            f"{r['agree']}/{r['voters']} | "
            f"{r['p_value']:.3g} | **{r['verdict']}** |"
        )

    keeps = [r for r in results if r["verdict"].startswith("KEEP")]
    drops = [r for r in results if r["verdict"] == "DROP"]
    lines += [
        "",
        f"**{len(keeps)} keep / {len(drops)} drop** of {len(results)} candidate "
        "features.",
        "",
        "![Lunge feature distributions by class](figures/lunge_feature_validity_boxplots.png)",
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

    misled = [r for r in results if r["pooling_misleads"]]
    paradox = next(r for r in results if r["feature"] == PARADOX_FEATURE)
    detail = confound["detail"]
    single_class = [d for d in detail if d["n_good"] == 0 or d["n_poor"] == 0]
    lines += [
        "",
        "## ⚠ The pooled AUC is misleading on this cohort — the gate's biggest finding",
        "",
        "**Squat's pooled-AUC verdict rule does not transfer cleanly to lunge, and "
        f"acting on the DROP column above without reading this section would discard "
        f"{len(misled)} of the {len(results)} features on an artefact.** This is a "
        "lunge-specific problem: it is caused by this cohort's class-mix imbalance "
        "across subjects, which squat's cohort did not have to the same degree.",
        "",
        f"### `{PARADOX_FEATURE}`: every subject says one thing, the pool says the "
        "opposite",
        "",
        f"Pooled, `{PARADOX_FEATURE}` looks like nothing: AUC "
        f"{paradox['auc']:.3f} (Good median {paradox['good_median']:.1f}° vs Poor "
        f"{paradox['poor_median']:.1f}° — *Poor lower*), which the pre-declared rule "
        f"scores **{paradox['verdict']}**. But the direction vote is "
        f"**{paradox['agree']}/{paradox['voters']}** — that is, **not one** of the "
        f"{paradox['voters']} subjects who can vote agrees with the pooled direction. "
        f"Every single subject shows Poor reps with a *higher* back-knee ROM than their "
        f"own Good reps. Subtracting each subject's own median and re-pooling gives a "
        f"within-subject AUC of **{paradox['within_auc']:.3f}** — from the weakest "
        "features in the table to the strongest.",
        "",
        "This is **Simpson's paradox**, and the mechanism is measured rather than "
        "asserted. It requires subject-level *level* to correlate with subject-level "
        "*class mix*, and here it does: **corr(subject median, subject %Poor) = "
        f"{confound['level_vs_mix_r']:+.3f}**.",
        "",
        f"| subject | lead leg | reps | %Poor | subject median `{PARADOX_FEATURE}` |",
        "| ------- | -------- | ---- | ----- | --------------------------------- |",
    ]
    for d in detail:
        lines.append(
            f"| P{d['person']} | {d['lead_leg']} | {d['n_good']}G/{d['n_poor']}P | "
            f"{100 * d['poor_fraction']:.0f}% | {d['median']:.1f}° |"
        )
    if confound["culprit"] is not None:
        culprit = confound["culprit"]
        lines += [
            "",
            f"**One subject causes it.** P{culprit['person']} is the cohort's only "
            f"single-class subject ({culprit['n_good']} Good / {culprit['n_poor']} "
            f"Poor) *and* has the lowest `{PARADOX_FEATURE}` of anyone "
            f"({culprit['median']:.1f}°, against "
            f"{min(d['median'] for d in detail if d is not culprit):.1f}–"
            f"{max(d['median'] for d in detail if d is not culprit):.1f}° for the "
            f"rest); every other subject is close to 50/50. So P{culprit['person']} "
            f"pours {culprit['n_poor']} low-ROM reps into the Poor pool and nothing "
            "into the Good pool, dragging the pooled Poor median below the pooled Good "
            "median — reversing a direction that holds inside every subject. Excluding "
            f"P{culprit['person']} alone lifts the pooled AUC from "
            f"{paradox['auc']:.3f} to {confound['auc_without_culprit']:.3f} — and that "
            "is a demonstration, not a fix: it stays well short of the within-subject "
            f"{paradox['within_auc']:.3f}, because the remaining between-subject level "
            "differences still dilute the effect.",
            "",
        ]

    lines += [
        "### What this does and does not license",
        "",
        "**The within-subject AUC is not achievable accuracy, and must not be quoted "
        "as a performance figure.** At inference the model sees one rep with no subject "
        "median to subtract against, so it cannot access the within-subject contrast. "
        "The column answers one narrower question: *does this feature carry real signal "
        "that pooling is masking?* For the ⚠ features, the answer is yes.",
        "",
        "The centring uses **no label information** (each subject's median is taken over "
        "all their reps regardless of class), so the diagnostic does not leak the "
        "outcome into itself. Single-class subjects contribute nothing to it, by "
        "construction.",
        "",
        "**The pre-declared verdicts above were deliberately NOT rewritten in light of "
        "this.** The rule was fixed in advance and is left as it fell; silently "
        "swapping in whichever statistic produced the nicer answer is exactly the "
        "practice that pre-declaring a rule exists to prevent. The verdicts stand, the "
        "contradicting evidence is published beside them, and the resolution is handed "
        "to Stage 5.5 explicitly:",
        "",
        f"- **Stage 5.5 must train on all {len(results)} features** and read the "
        "verdicts above as advisory only. Squat's Stage 5.5 already took this route "
        "for an unrelated reason (avoiding selection bias against the LOSO folds), so "
        "this is the established path, not a special case — and it means **no feature "
        "is actually lost to the artefact**. The DROP column is not wired to anything.",
        "- The model's own importances, on the held-out folds, are the trustworthy "
        "keep/drop evidence. This gate's job is to catch a broken pipeline, and on that "
        "question it is unambiguous.",
        "",
        "**This also warns about the evaluation to come.** A statistic pooled across "
        "subjects can invert the truth on this cohort. Stage 5.5's LOSO design is the "
        "right response — it never pools across the subject boundary — but any pooled "
        "summary reported later (a single confusion matrix, a pooled AUC over all "
        "folds) inherits exactly this hazard and should be read with it in mind.",
        "",
        "## Redundancy",
        "",
        "![Lunge feature correlation matrix](figures/lunge_feature_correlation_heatmap.png)",
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
        f"Every verdict above was computed on **all {len(rows)} reps** — including the "
        "reps of subjects that Stage 5.5 will hold out for LOSO. Dropping a feature on "
        "that evidence and then reporting LOSO scores over the same data is a mild "
        "selection bias: the held-out subject influenced which features existed. This "
        "is tolerable here because the stage's purpose is a **sanity gate** (catch a "
        "broken pipeline), not statistical feature selection. The honest options for "
        "Stage 5.5 are to train on all 17 features and let the model's own importances "
        "speak, or to nest the selection inside each CV fold. Recorded so the choice "
        "is deliberate rather than accidental — squat's Stage 5.5 took the former "
        "route for exactly this reason.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
