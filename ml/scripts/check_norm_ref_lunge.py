"""Stage 5.4 (Lunge): the `norm_ref` bake-off (R5.3) — trunk_length vs thigh_length.

`norm_ref` is the body-size reference the normalised features divide by. The better
reference is the one that cancels body-size differences more completely, i.e. leaves
*less* variation between subjects performing the same movement.

Two method points carried over from squat's `check_norm_ref.py`, and one new:

1. **Raw variance is scale-confounded** (squat's finding, unchanged). `task.md`
   prescribes "compute cross-subject variance ... pick the lower", but the two
   references have different magnitudes, so dividing by the larger one shrinks the
   feature and its raw variance regardless of how well it normalises anything. Raw
   variance is reported so the confound stays visible, never used as the verdict.

2. **Lunge normalises THREE features, not squat's two** — `stance_length_norm` and
   `knee_passes_toe_norm` where squat had `stance_width_norm`, plus the shared
   `hip_mid_jitter_norm`.

3. **NEW, and the reason this is not a copy of squat's script: CV is invalid for
   `knee_passes_toe_norm`.** CV = std/mean assumes a ratio scale with a stable non-zero
   mean. `knee_passes_toe_norm` is a *signed* excursion — positive when the knee passes
   the toe (the fault), negative when it stays behind — and it genuinely crosses zero
   in this cohort (18 of 88 reps are negative; one subject's mean sits at +0.06). A mean
   near zero makes CV explode and a sign flip makes it meaningless, so a CV verdict on
   this feature would be an artefact of where the zero happens to fall.

   The bake-off therefore uses a **variance ratio** (between-subject variance of the
   per-subject means / mean within-subject variance) as the primary, scale-invariant
   verdict statistic for all three features. It is a ratio of two variances in the same
   units, so it is immune to the scale confound in (1) *without* needing a non-zero
   mean, and it says something CV cannot: a reference that cancels between-subject
   spread only by inflating within-subject noise does not win. Lower = better.

   CV is still reported for the two strictly-positive features, both because it is
   squat's metric (so the two exercises stay comparable) and so the two statistics can
   be checked against each other.

Deterministic (X8): sorted subject iteration, no RNG.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# X1: the live config is the thing under test — read and toggled, never copied.
from app.module_b.lunge.config import LUNGE_CONFIG
from build_features_lunge import _load_config, _read_segmentation, build_feature_rows
from plotting import save_fig

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "LUNGE_NORM_REF_BAKEOFF.md"

CANDIDATES = ("trunk_length", "thigh_length")
# The only features norm_ref divides; the other 14 are unaffected by it.
NORMALISED_FEATURES = (
    "hip_mid_jitter_norm",
    "stance_length_norm",
    "knee_passes_toe_norm",
)
# Signed, zero-crossing -> CV is not a valid statistic for it (see module docstring).
SIGNED_FEATURES = frozenset({"knee_passes_toe_norm"})


def _per_subject_values(rows: list[dict], feature: str) -> dict[str, list[float]]:
    subjects = sorted({r["person_id"] for r in rows}, key=int)
    return {
        person: [float(r[feature]) for r in rows if r["person_id"] == person]
        for person in subjects
    }


def evaluate(rows: list[dict], feature: str) -> dict:
    """Cross-subject spread of one normalised feature, by several statistics."""
    per_subject = _per_subject_values(rows, feature)
    means = {p: float(np.mean(v)) for p, v in per_subject.items()}
    values = np.array(list(means.values()), dtype=float)

    between = float(np.var(values, ddof=1))
    # Mean of each subject's own variance = the movement variation the reference
    # should NOT be cancelling. Subjects with <2 reps contribute no variance.
    within_each = [float(np.var(v, ddof=1)) for v in per_subject.values() if len(v) > 1]
    within = float(np.mean(within_each))

    grand_mean = float(np.mean(values))
    # CV is only meaningful on a strictly-positive ratio scale — see module docstring.
    cv = (
        None
        if feature in SIGNED_FEATURES
        else float(np.std(values, ddof=1) / grand_mean)
    )
    return {
        "per_subject": means,
        "variance": between,
        "within_variance": within,
        "variance_ratio": between / within if within > 0 else float("inf"),
        "mean": grand_mean,
        "cv": cv,
    }


def run_bakeoff() -> dict[str, dict[str, dict]]:
    """Extract the full feature table once per candidate; return per-feature spread."""
    config = _load_config()
    seg_rows = _read_segmentation(
        Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    )
    # Preprocessing does not depend on norm_ref, so one cache serves both candidates.
    preprocessed_cache: dict[str, list[dict]] = {}
    frame_count_cache: dict[str, int] = {}

    original = LUNGE_CONFIG["norm_ref_strategy"]
    results: dict[str, dict[str, dict]] = {}
    try:
        for candidate in CANDIDATES:
            # `lunge/features._norm_ref` reads this key at call time, so toggling it
            # here re-extracts through the real backend code path rather than a
            # local re-implementation (X1). Restored in `finally`.
            LUNGE_CONFIG["norm_ref_strategy"] = candidate
            rows, _stats = build_feature_rows(
                seg_rows, preprocessed_cache, frame_count_cache
            )
            results[candidate] = {
                feature: evaluate(rows, feature) for feature in NORMALISED_FEATURES
            }
    finally:
        LUNGE_CONFIG["norm_ref_strategy"] = original
    return results


def plot_comparison(results: dict[str, dict[str, dict]]) -> Path:
    """Paired per-subject bars per candidate — makes the spread visually checkable.

    Each bar is a subject's mean **divided by that candidate's own grand mean**, so
    both candidates centre on 1.0 and the visible spread is comparable rather than a
    reflection of the reference's absolute size (squat's reasoning, unchanged).

    `knee_passes_toe_norm` is plotted on its own terms: its grand mean is small and it
    crosses zero, so mean-scaling it would produce meaningless bars. It is shown as raw
    per-subject means with a zero line instead, and its panel title says so.
    """
    fig, axes = plt.subplots(1, len(NORMALISED_FEATURES))
    for ax, feature in zip(axes, NORMALISED_FEATURES, strict=True):
        signed = feature in SIGNED_FEATURES
        subjects = sorted(results[CANDIDATES[0]][feature]["per_subject"], key=int)
        x = np.arange(len(subjects))
        width = 0.38
        for offset, candidate in zip((-width / 2, width / 2), CANDIDATES, strict=True):
            stats = results[candidate][feature]
            if signed:
                heights = [stats["per_subject"][s] for s in subjects]
                label = f"{candidate} (var ratio={stats['variance_ratio']:.2f})"
            else:
                heights = [stats["per_subject"][s] / stats["mean"] for s in subjects]
                label = f"{candidate} (CV={stats['cv']:.3f})"
            ax.bar(x + offset, heights, width, label=label)
        ax.axhline(
            0.0 if signed else 1.0,
            color="black",
            linewidth=0.8,
            linestyle="--",
            zorder=0,
        )
        ax.set_xticks(x)
        ax.set_xticklabels([f"P{s}" for s in subjects], fontsize=8)
        ax.set_title(
            f"{feature}\n(raw — signed, crosses zero)" if signed else feature,
            fontsize=9,
        )
        ax.set_xlabel("subject")
        ax.set_ylabel("raw mean" if signed else "per-subject mean / grand mean")
        ax.legend(fontsize=7)
    fig.suptitle(
        "Lunge norm_ref bake-off: per-subject means "
        "(tighter spread = better body-size normalisation)"
    )
    fig.tight_layout()
    path = save_fig(fig, "lunge_norm_ref_variance_comparison", figsize="wide")
    plt.close(fig)
    return path


def pick_winner(results: dict[str, dict[str, dict]]) -> tuple[str, dict, dict]:
    """Winner = lower mean variance ratio across the normalised features.

    The variance ratio is the verdict statistic because it is the only one of the two
    that is valid for all three features (see module docstring). Mean CV is computed
    alongside, over the two features where it is defined, as a cross-check.
    """
    mean_ratio = {
        candidate: float(
            np.mean(
                [results[candidate][f]["variance_ratio"] for f in NORMALISED_FEATURES]
            )
        )
        for candidate in CANDIDATES
    }
    cv_features = [f for f in NORMALISED_FEATURES if f not in SIGNED_FEATURES]
    mean_cv = {
        candidate: float(np.mean([results[candidate][f]["cv"] for f in cv_features]))
        for candidate in CANDIDATES
    }
    winner = min(mean_ratio, key=mean_ratio.__getitem__)
    return winner, mean_ratio, mean_cv


def write_report(
    results: dict[str, dict[str, dict]],
    winner: str,
    mean_ratio: dict,
    mean_cv: dict,
    current: str,
) -> None:
    loser = [c for c in CANDIDATES if c != winner][0]
    cv_winner = min(mean_cv, key=mean_cv.__getitem__)
    per_feature_winner = {
        f: min(CANDIDATES, key=lambda c: results[c][f]["variance_ratio"])
        for f in NORMALISED_FEATURES
    }
    unanimous = len(set(per_feature_winner.values())) == 1

    lines = [
        "# Stage 5.4 (Lunge) — `norm_ref` bake-off (R5.3)",
        "",
        "`norm_ref` is the body-size reference that `hip_mid_jitter_norm`, "
        "`stance_length_norm` and `knee_passes_toe_norm` divide by (the other 14 "
        "features do not use it). The better reference cancels body-size differences "
        "more completely — leaving **less spread between subjects** doing the same "
        "movement.",
        "",
        f"**Winner: `{winner}`** (mean cross-subject variance ratio "
        f"{mean_ratio[winner]:.3f} vs {mean_ratio[loser]:.3f} for `{loser}`). "
        f"Backend default was `{current}`.",
        "",
        "## Why the verdict statistic is not squat's",
        "",
        "Squat's bake-off decided on the **coefficient of variation** of the "
        "per-subject means, having established that `task.md`'s literal "
        '"pick the lower variance" is **scale-confounded**: the two references have '
        "different magnitudes, so dividing by the larger one shrinks the feature and "
        "its raw variance too, and a reference that is uniformly 2x larger would win "
        "on raw variance while normalising nothing. That reasoning still holds here, "
        "and raw variance is still reported below so the confound stays visible.",
        "",
        "**But CV cannot be used for `knee_passes_toe_norm`, and that is a real "
        "lunge-specific problem rather than a technicality.** CV = std/mean presumes a "
        "ratio scale with a stable non-zero mean. `knee_passes_toe_norm` is a *signed* "
        "excursion — positive when the front knee passes the toe (the fault it exists "
        "to detect), negative when the knee stays behind it — and it genuinely crosses "
        "zero in this cohort: **18 of 88 reps are negative, and one subject's mean sits "
        "at +0.06**. Near a zero mean the denominator collapses and CV explodes; had "
        "the cohort's zero fallen slightly differently, a CV verdict would have flipped "
        "on that accident alone. Squat never hit this because both its normalised "
        "features are unsigned magnitudes.",
        "",
        "So the verdict is taken on the **variance ratio**: between-subject variance of "
        "the per-subject means, over the mean within-subject variance. Lower is better. "
        "It is a ratio of two variances in the same units, so it is scale-invariant "
        "like CV — but it needs no non-zero mean, and it measures something CV cannot: "
        "a reference that cancels between-subject spread *by inflating within-subject "
        "noise* is not actually normalising, and the ratio catches that trade where CV "
        "would reward it. CV is still reported for the two strictly-positive features, "
        "so lunge stays comparable to squat and the two statistics can be checked "
        "against each other.",
        "",
        "## Numbers",
        "",
        "| feature | candidate | variance ratio (verdict) | CV | between-subj variance | within-subj variance | mean |",
        "| ------- | --------- | ------------------------ | -- | --------------------- | -------------------- | ---- |",
    ]
    for feature in NORMALISED_FEATURES:
        for candidate in CANDIDATES:
            s = results[candidate][feature]
            marker = " **<-**" if candidate == per_feature_winner[feature] else ""
            cv = "n/a (signed)" if s["cv"] is None else f"{s['cv']:.4f}"
            lines.append(
                f"| `{feature}` | {candidate} | {s['variance_ratio']:.3f}{marker} | "
                f"{cv} | {s['variance']:.3e} | {s['within_variance']:.3e} | "
                f"{s['mean']:.3e} |"
            )

    lines += [
        "",
        "Note how the raw between-subject variance column moves with the feature's "
        "absolute scale (the `mean` column) while the variance ratio does not — that is "
        "the scale confound above, made concrete.",
        "",
        "![Lunge norm_ref per-subject comparison](figures/lunge_norm_ref_variance_comparison.png)",
        "",
        "The first two panels plot each subject's mean **divided by that candidate's "
        "own grand mean**, so both candidates centre on 1.0 and the visible spread is "
        "the quantity being compared — plotting raw bars would have made the "
        "longer reference look tighter through scale alone, letting a reader see the "
        "right answer for the wrong reason. `knee_passes_toe_norm` is plotted **raw "
        "against a zero line** instead, for the same reason its CV is omitted: "
        "mean-scaling a zero-crossing quantity produces meaningless bars.",
        "",
    ]

    if unanimous:
        lines.append(
            f"**The verdict is unanimous across features:** `{winner}` wins the "
            "variance ratio on all three, so it does not rest on how the three were "
            "averaged."
        )
    else:
        split = ", ".join(
            f"`{f}` -> {c}" for f, c in sorted(per_feature_winner.items())
        )
        lines.append(
            f"**The verdict is NOT unanimous across features** ({split}), so it rests "
            f"on the mean over the three. Recorded rather than smoothed over: the "
            f"margin ({mean_ratio[winner]:.3f} vs {mean_ratio[loser]:.3f}) is the "
            "honest strength of this call."
        )

    lines += [
        "",
        (
            f"**Cross-check: CV agrees.** `{cv_winner}` also wins on mean CV over the "
            f"two features where CV is defined ({mean_cv[cv_winner]:.4f} vs "
            f"{mean_cv[[c for c in CANDIDATES if c != cv_winner][0]]:.4f}), so the "
            "choice of verdict statistic did not decide the outcome — it only means "
            "the variance ratio is the honest number to quote for all three."
            if cv_winner == winner
            else (
                f"**Cross-check: CV DISAGREES.** On the two features where CV is "
                f"defined it favours `{cv_winner}` ({mean_cv[cv_winner]:.4f} vs "
                f"{mean_cv[winner]:.4f}), while the variance ratio favours `{winner}`. "
                "The two statistics measure different things — CV ignores within-subject "
                "noise, the ratio does not — so this is a genuine disagreement, not a "
                "rounding artefact. The variance ratio is kept as the verdict because "
                "it is the only statistic valid for all three normalised features, but "
                "this call is weaker than a unanimous one and is flagged as such."
            )
        ),
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    current = LUNGE_CONFIG["norm_ref_strategy"]
    results = run_bakeoff()
    winner, mean_ratio, mean_cv = pick_winner(results)
    plot_comparison(results)
    write_report(results, winner, mean_ratio, mean_cv, current)

    for candidate in CANDIDATES:
        for feature in NORMALISED_FEATURES:
            s = results[candidate][feature]
            cv = "n/a (signed)" if s["cv"] is None else f"{s['cv']:.4f}"
            print(
                f"  {candidate:<13} {feature:<22} ratio={s['variance_ratio']:.3f} "
                f"CV={cv} var={s['variance']:.3e}"
            )
    print(f"winner: {winner} (mean variance ratio {mean_ratio[winner]:.3f})")
    print(f"  CV cross-check favours: {min(mean_cv, key=mean_cv.__getitem__)}")
    print(f"backend config currently: {current}")
    if winner != current:
        print(f"ACTION: update LUNGE_CONFIG['norm_ref_strategy'] -> {winner}")
    else:
        print("config already matches the winner; no change needed")
    print(f"wrote {REPORT_MD.name}")


if __name__ == "__main__":
    main()
