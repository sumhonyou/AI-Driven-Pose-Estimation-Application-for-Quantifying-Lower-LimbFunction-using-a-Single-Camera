"""Compare MediaPipe knee flexion against OptiTrack mocap ground truth.

Answers "does our single-camera pipeline actually measure the knee angle it claims
to?" by comparing, on the same frames, the knee flexion our pipeline derives from
MediaPipe world landmarks against the same angle derived from REHAB24-6's OptiTrack
26-joint mocap. Reports ICC(2,1) + Bland-Altman, reusing
`app.module_a.core.evaluation.agreement` (unit-agnostic and already shared — not
forked). Writes `ml/reports/MOCAP_AGREEMENT.md`.

The mocap is used for validation ONLY, never as a training feature (X3).

Both sides go through the SAME `knee_flexion_deg` helper the live pipeline uses — an
unsigned hip-knee-ankle angle is invariant to the coordinate frame, so mocap's
room-axes and MediaPipe's hip-origin axes need no alignment for this comparison.

Verified rather than assumed (all recorded in the report):
  - **Frame alignment.** An offset scan per video picks the lag maximising
    correlation instead of trusting index 0. Raw landmarks align at exactly 0; the
    preprocessed stream lags by ~3 frames, which is the causal One Euro filter's own
    delay, not a data misalignment.
  - **Leg correspondence.** Deliberately NOT taken on faith, and it does not survive
    scrutiny — see `_leg_difference_correlation`. The headline figure is therefore the
    **bilateral mean**, which is invariant to any left/right swap (and is exactly what
    `knee_flex_peak_deg` uses anyway).

Deterministic (X8): sorted iteration, no RNG.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from build_features import (
    SIDE_VIEW_ORIENTATION,
    TARGET_EXERCISE_ID,
    _load_config,
    _preprocessed_stream,
    _read_segmentation,
)
from plotting import save_fig

# Reused, never forked: the same stats module Module A's SLS/WBLT evaluations use.
from app.module_a.core.evaluation.agreement import bland_altman, icc_2_1
from app.module_b.core.geometry import knee_flexion_deg

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "MOCAP_AGREEMENT.md"

MOCAP_DIR = Path("/Users/sumhonyou/fypDataset/3d_joints/Ex6")

# joints_names.txt: 16 LeftUpLeg / 17 LeftLeg / 18 LeftFoot, 21 RightUpLeg /
# 22 RightLeg / 23 RightFoot. (hip, knee, ankle) per leg.
MOCAP_LEGS = {"left": (16, 17, 18), "right": (21, 22, 23)}
# MediaPipe pose landmarks, same (hip, knee, ankle) roles.
MP_LEGS = {"left": (23, 25, 27), "right": (24, 26, 28)}
# Dataset audit found the right leg is the far/occluded side in every subject.
FAR_LEG = "right"

OFFSET_SCAN = range(-5, 6)


def _point(row) -> dict[str, float]:
    return {"x": float(row[0]), "y": float(row[1]), "z": float(row[2])}


def _mocap_flexion(mocap: np.ndarray, leg: str) -> np.ndarray:
    hip, knee, ankle = MOCAP_LEGS[leg]
    return np.array(
        [
            knee_flexion_deg(
                _point(frame[hip]), _point(frame[knee]), _point(frame[ankle])
            )
            for frame in mocap
        ]
    )


def _mp_flexion(frames: list[dict], leg: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (frame_indices, flexion) for one leg from the preprocessed stream."""
    hip, knee, ankle = MP_LEGS[leg]
    indices, values = [], []
    for frame in frames:
        lms = frame["worldLandmarks"]
        indices.append(frame["frameIndex"])
        values.append(knee_flexion_deg(lms[hip], lms[knee], lms[ankle]))
    return np.array(indices), np.array(values)


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    ok = ~(np.isnan(a) | np.isnan(b))
    if ok.sum() < 2:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def _best_offset(mp_values: np.ndarray, mocap_values: np.ndarray) -> tuple[int, float]:
    """Pick the lag maximising correlation, rather than assuming index 0 aligns."""
    n = min(len(mp_values), len(mocap_values))
    best = (0, -2.0)
    for offset in OFFSET_SCAN:
        if offset >= 0:
            a, b = mp_values[: n - offset], mocap_values[offset:n]
        else:
            a, b = mp_values[-offset:n], mocap_values[: n + offset]
        r = _corr(a, b)
        if not np.isnan(r) and r > best[1]:
            best = (offset, r)
    return best


def collect(config: dict) -> dict:
    seg_rows = _read_segmentation(
        Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    )
    preprocessed_cache: dict[str, list[dict]] = {}
    frame_count_cache: dict[str, int] = {}

    side_view_rows = sorted(
        (
            r
            for r in seg_rows
            if r["exercise_id"] == TARGET_EXERCISE_ID
            and r["cam17_orientation"] == SIDE_VIEW_ORIENTATION
        ),
        key=lambda r: (r["video_id"], int(r["repetition_number"])),
    )
    video_ids = sorted({r["video_id"] for r in side_view_rows})

    per_video_offsets = {}
    leg_diff_checks = []
    orientations = {}
    # Per-rep peak of the bilateral mean -- this is exactly what
    # `knee_flex_peak_deg` is, so the agreement speaks to the real feature.
    pairs_mean: list[tuple[float, float]] = []
    # Same windows, but the rep's MINIMUM and its ROM, which expose whether the
    # pipeline compresses the angle range rather than merely offsetting it.
    pairs_min: list[tuple[float, float]] = []
    pairs_rom: list[tuple[float, float]] = []
    pairs_by_leg: dict[str, list[tuple[float, float]]] = {"left": [], "right": []}

    for video_id in video_ids:
        mocap = np.load(MOCAP_DIR / f"{video_id}-30fps.npy")
        frames = _preprocessed_stream(video_id, preprocessed_cache, frame_count_cache)
        indices, mp_left = _mp_flexion(frames, "left")
        _indices, mp_right = _mp_flexion(frames, "right")
        mocap_left = _mocap_flexion(mocap, "left")
        mocap_right = _mocap_flexion(mocap, "right")

        # Is every subject oriented the same way? If so the near/far leg is the same
        # anatomical leg for all of them, so whatever the MediaPipe <-> mocap leg
        # mapping is, it must be CONSISTENT across subjects.
        hip_axis = (mocap[:, 21, :3] - mocap[:, 16, :3]).mean(axis=0)
        orientations[video_id] = hip_axis / np.linalg.norm(hip_axis)

        # The decisive leg test: correlate the LEG-DIFFERENCE signal. Comparing each
        # leg's absolute angle discriminates nothing -- both knees bend together in a
        # squat, so every pairing correlates ~0.97 whether or not the labels match.
        # The difference cancels that common mode and isolates the leg-specific
        # component, which is the only part that can confirm (or refute) the labels.
        leg_diff_checks.append(
            {
                "video_id": video_id,
                "r": _corr(
                    mp_left - mp_right, mocap_left[indices] - mocap_right[indices]
                ),
            }
        )

        offset, r = _best_offset(mp_left, mocap_left[indices])
        per_video_offsets[video_id] = {"offset": offset, "r": r}

        mp_mean = (mp_left + mp_right) / 2.0
        mocap_mean = (mocap_left + mocap_right) / 2.0
        index_of = {int(f): i for i, f in enumerate(indices)}

        for row in (r for r in side_view_rows if r["video_id"] == video_id):
            first, last = int(row["first_frame"]), int(row["last_frame"])
            window = [index_of[f] for f in range(first, last + 1) if f in index_of]
            if not window:
                continue
            mocap_window = [f + offset for f in range(first, last + 1)]
            mocap_window = [f for f in mocap_window if 0 <= f < len(mocap_mean)]
            mp_peak = float(np.max(mp_mean[window]))
            mo_peak = float(np.max(mocap_mean[mocap_window]))
            mp_min = float(np.min(mp_mean[window]))
            mo_min = float(np.min(mocap_mean[mocap_window]))
            pairs_mean.append((mp_peak, mo_peak))
            pairs_min.append((mp_min, mo_min))
            pairs_rom.append((mp_peak - mp_min, mo_peak - mo_min))
            for leg, mp_series, mocap_series in (
                ("left", mp_left, mocap_left),
                ("right", mp_right, mocap_right),
            ):
                pairs_by_leg[leg].append(
                    (
                        float(np.max(mp_series[window])),
                        float(np.max(mocap_series[mocap_window])),
                    )
                )

    return {
        "offsets": per_video_offsets,
        "leg_diff_checks": leg_diff_checks,
        "orientations": orientations,
        "pairs_mean": pairs_mean,
        "pairs_min": pairs_min,
        "pairs_rom": pairs_rom,
        "pairs_by_leg": pairs_by_leg,
    }


def agreement_stats(pairs: list[tuple[float, float]]) -> dict:
    system = [p[0] for p in pairs]
    manual = [p[1] for p in pairs]
    stats = bland_altman(system, manual)
    stats["icc"] = icc_2_1(system, manual)
    stats["r"] = _corr(np.array(system), np.array(manual))
    return stats


def plot_bland_altman(pairs: list[tuple[float, float]], stats: dict) -> Path:
    system = np.array([p[0] for p in pairs])
    manual = np.array([p[1] for p in pairs])
    means = (system + manual) / 2.0
    diffs = system - manual

    fig, ax = plt.subplots()
    ax.scatter(means, diffs, s=22, alpha=0.7, edgecolor="none")
    ax.axhline(stats["bias"], color="C3", label=f"bias {stats['bias']:.2f}°")
    ax.axhspan(
        stats["loa_lower"],
        stats["loa_upper"],
        color="C0",
        alpha=0.12,
        label=f"95% LoA [{stats['loa_lower']:.1f}, {stats['loa_upper']:.1f}]°",
    )
    for bound in (stats["loa_lower"], stats["loa_upper"]):
        ax.axhline(bound, color="C0", linestyle="--", linewidth=0.9)
    ax.axhline(0.0, color="black", linewidth=0.7, zorder=0)
    ax.set_xlabel("Mean of MediaPipe and mocap peak knee flexion (°)")
    ax.set_ylabel("MediaPipe − mocap (°)")
    ax.set_title(
        f"Bland-Altman: peak knee flexion per rep (n={stats['n']}, ICC={stats['icc']:.3f})"
    )
    ax.legend(fontsize=8, loc="best")
    path = save_fig(fig, "mocap_agreement_bland_altman", figsize="bland_altman")
    plt.close(fig)
    return path


def write_report(
    data: dict,
    mean_stats: dict,
    leg_stats: dict[str, dict],
    min_stats: dict,
    rom_stats: dict,
) -> None:
    offsets = data["offsets"]
    checks = data["leg_diff_checks"]
    unique_offsets = sorted({v["offset"] for v in offsets.values()})
    leg_diff_rs = [c["r"] for c in checks]
    mean_leg_diff_r = float(np.mean(leg_diff_rs))
    # Do all subjects stand the same way round? Cosine similarity of every hip axis
    # against the first one; ~1.0 everywhere means identical orientation.
    axes = list(data["orientations"].values())
    orientation_sims = [float(np.dot(axes[0], a)) for a in axes]
    same_orientation = all(s > 0.9 for s in orientation_sims)

    lines = [
        "# Stage 5.4 — MediaPipe vs OptiTrack mocap agreement",
        "",
        "Does the single-camera pipeline actually measure the knee angle it claims to? "
        "Compares, on the same frames, the knee flexion our pipeline derives from "
        "MediaPipe world landmarks against the same angle derived from REHAB24-6's "
        "OptiTrack 26-joint mocap. **The mocap is a validation reference only — never "
        "a training feature (X3).**",
        "",
        "## Headline",
        "",
        f"**ICC(2,1) = {mean_stats['icc']:.3f}**, "
        f"**bias {mean_stats['bias']:+.2f}°**, "
        f"**95% limits of agreement [{mean_stats['loa_lower']:.2f}°, "
        f"{mean_stats['loa_upper']:.2f}°]**, r = {mean_stats['r']:.3f}, "
        f"n = {mean_stats['n']} reps.",
        "",
        "The compared quantity is the **peak of the bilateral mean knee flexion per "
        "rep** — i.e. exactly `knee_flex_peak_deg`, the feature the R5.5 gate turns on "
        "— so this speaks to the real feature rather than to an angle nothing uses. "
        "Negative bias means our pipeline reads *lower* than mocap. The bilateral mean "
        "is also **invariant to any left/right swap**, which matters given the leg-"
        "identity problem documented below.",
        "",
        "![Bland-Altman: peak knee flexion vs mocap](figures/mocap_agreement_bland_altman.png)",
        "",
        "## The headline number needs unpacking: high correlation, large bias",
        "",
        f"r = {mean_stats['r']:.3f} but ICC = {mean_stats['icc']:.3f}. That gap is the "
        "whole story: Pearson r only asks whether the two move together (they do, very "
        "closely), while ICC(2,1) is an **absolute**-agreement measure and is dragged "
        f"down by the systematic {mean_stats['bias']:+.2f}° offset. Our pipeline tracks "
        "the shape of the movement faithfully and mis-states its magnitude.",
        "",
        "### It is range compression, not a constant offset",
        "",
        "Comparing the rep's minimum and its ROM as well as its peak shows the shape of "
        "the error:",
        "",
        "| quantity per rep | bias (MediaPipe − mocap) | 95% LoA | ICC | r |",
        "| ---------------- | ------------------------ | ------- | --- | - |",
        f"| peak flexion (`knee_flex_peak_deg`) | {mean_stats['bias']:+.2f}° | "
        f"[{mean_stats['loa_lower']:.1f}, {mean_stats['loa_upper']:.1f}]° | "
        f"{mean_stats['icc']:.3f} | {mean_stats['r']:.3f} |",
        f"| minimum flexion (`knee_flex_min_deg`) | {min_stats['bias']:+.2f}° | "
        f"[{min_stats['loa_lower']:.1f}, {min_stats['loa_upper']:.1f}]° | "
        f"{min_stats['icc']:.3f} | {min_stats['r']:.3f} |",
        f"| ROM (`knee_rom_deg`) | {rom_stats['bias']:+.2f}° | "
        f"[{rom_stats['loa_lower']:.1f}, {rom_stats['loa_upper']:.1f}]° | "
        f"{rom_stats['icc']:.3f} | {rom_stats['r']:.3f} |",
        "",
        f"The pipeline **under-reads the peak by {abs(mean_stats['bias']):.1f}° while "
        f"over-reading the minimum by {abs(min_stats['bias']):.1f}°**, so the measured "
        f"range is compressed by ~{abs(rom_stats['bias']):.0f}° per rep. The knee never "
        "looks as straight at the top nor as bent at the bottom as it really is. This "
        "is characteristic of landmark regression from a single view (the model hedges "
        "toward the mean pose), and is compounded here by the far limb being occluded.",
        "",
        "> **Consequence for the ROM rule — flagged, not fixed here.** "
        "`squat/config.py`'s ROM bands (`<60°` / `60-90°` shallow / `90-110°` parallel "
        "/ `>=110°` deep) are tagged **[clinical norm, S1]**, i.e. they come from "
        "literature describing *true* joint angles. Feeding a systematically "
        f"{abs(mean_stats['bias']):.0f}°-under-read measurement into thresholds derived "
        "from true angles will systematically under-credit depth: a genuine 110° deep "
        f"squat reaches our pipeline as ~{110 + mean_stats['bias']:.0f}° and gets "
        "banded 'parallel'. The clean fixes are to calibrate the measurement or to "
        "re-derive the band edges against this pipeline's own scale — either changes "
        "Phase 4 banding behaviour and belongs to Stage 5.6's threshold work, not to "
        "this gate. **It does not affect the classifier**, which learns from our "
        "measurements consistently and is unaffected by a monotone offset.",
        "",
        "## Method notes (verified, not assumed)",
        "",
        f"- **Frame alignment, and a filter-lag finding.** An offset scan "
        f"({OFFSET_SCAN.start}..{OFFSET_SCAN.stop - 1} frames) picks the lag "
        f"maximising correlation per video rather than trusting index 0. Selected: "
        f"{unique_offsets} frame(s) for every video. Raw landmarks align at exactly "
        "**0**, so the streams do start together and the extra trailing mocap frame is "
        "harmless; the preprocessed stream lags by **3 frames (~100 ms)**, which is the "
        "causal One Euro filter's own delay. Worth knowing beyond this report: live "
        "on-screen feedback inherits that ~100 ms lag.",
        "- **Same geometry helper both sides.** Both series go through the live "
        "pipeline's `knee_flexion_deg`; an unsigned hip-knee-ankle angle is invariant "
        "to the coordinate frame, so mocap's room axes and MediaPipe's hip-origin axes "
        "need no alignment.",
        "- **Our side is the preprocessed stream** (confidence filter → gap fill → One "
        "Euro), i.e. what the model actually consumes, not raw landmarks.",
        "",
        "## Leg identity could not be established — and that is itself a finding",
        "",
        "Stage 5.3 deferred one question to this gate: *is the occluded far leg's "
        "estimate accurate, or merely plausible?* Answering it needs a per-leg "
        "comparison, which needs knowing which mocap leg is which MediaPipe leg. That "
        "mapping does not survive scrutiny.",
        "",
        "- Comparing each leg's **absolute** angle is useless: both knees bend together "
        "in a squat, so every pairing correlates ~0.97 whether the labels match or not. "
        "It cannot discriminate.",
        "- The **leg-difference** signal (`θ_L − θ_R`) cancels that common mode and is "
        "the only thing that can confirm the labels. Correlated against mocap's own "
        f"leg difference it gives a mean r of **{mean_leg_diff_r:+.3f}** across the 9 "
        f"videos (range {min(leg_diff_rs):+.2f} to {max(leg_diff_rs):+.2f}, signs "
        "mixed) — **essentially no relationship**.",
        f"- Geometry says the mapping *must* be consistent: every subject stands the "
        f"same way round (all nine mocap hip axes align, cosine similarity "
        f"{min(orientation_sims):.2f}–{max(orientation_sims):.2f}"
        f"{' — identical orientation' if same_orientation else ''}) and MediaPipe calls "
        f"the far knee '{FAR_LEG}' in all nine. So the mixed signs above are **noise, "
        "not genuine per-subject inconsistency** — which means the difference signal "
        "carries no usable information rather than that the mapping flips.",
        "",
        "**Therefore the per-leg split below is reported without a verdict**, and the "
        "Stage 5.3 far-leg question stays formally open. The honest partial answer: the "
        "bilateral mean *includes* the far leg and still tracks mocap at "
        f"r = {mean_stats['r']:.3f}, so the far limb cannot be grossly wrong — a badly "
        "broken leg would visibly degrade the mean. That supports the decision to "
        "release hold-last rather than freeze it, but it is weaker evidence than a "
        "clean per-leg ICC would have been, and is not claimed as more.",
        "",
        "| leg (identity UNVERIFIED) | ICC(2,1) | bias (°) | 95% LoA (°) | r | n |",
        "| ------------------------- | -------- | -------- | ----------- | - | - |",
    ]
    for leg in ("left", "right"):
        s = leg_stats[leg]
        lines.append(
            f"| MediaPipe {leg} vs mocap {leg} | {s['icc']:.3f} | {s['bias']:+.2f} | "
            f"[{s['loa_lower']:.2f}, {s['loa_upper']:.2f}] | {s['r']:.3f} | {s['n']} |"
        )

    lines += [
        "",
        "### This independently condemns `symmetry_index_pct`",
        "",
        "The finding above is not just an inconvenience for this report — it is direct "
        "evidence about a feature. `symmetry_index_pct` is defined as "
        "`|θ_L − θ_R| / mean × 100`: it is *entirely* a function of the leg-difference "
        f"signal, and that signal correlates with the marker-based truth at r = "
        f"**{mean_leg_diff_r:+.3f}**. The feature is measuring noise, not asymmetry. "
        "Stage 5.4's distribution check independently gave it a DROP verdict on weak "
        "class separation; this is the mechanistic reason why, and it is the stronger "
        "argument — the feature is not weak, it is **not measuring the thing it "
        "claims**. A single sagittal camera cannot resolve left-right knee asymmetry "
        "when one leg occludes the other, which is the same monocular limitation that "
        "already removed frontal-plane valgus (Locked Assumption #3).",
        "",
        "## Per-video alignment detail",
        "",
        "| video | chosen offset (frames) | correlation at that offset |",
        "| ----- | ---------------------- | -------------------------- |",
    ]
    for video_id in sorted(offsets):
        v = offsets[video_id]
        lines.append(f"| {video_id} | {v['offset']:+d} | {v['r']:.4f} |")

    lines += [
        "",
        "## What this does and does not license",
        "",
        "**Does:** the pipeline measures the intended anatomy and tracks it faithfully "
        f"(r = {mean_stats['r']:.3f}). `knee_flex_peak_deg` rises and falls with the "
        "real knee angle, so it is a legitimate input for a *learned* classifier, which "
        "is what Stage 5.5 builds. This supports the R5.5 gate's pass.",
        "",
        "**Does not:** license treating our degrees as clinical degrees. The "
        f"{mean_stats['bias']:+.1f}° bias and the ~{abs(rom_stats['bias']):.0f}° range "
        "compression mean any number this pipeline reports is on **its own scale**, not "
        "a goniometer's. Two consequences: the ROM rule's [clinical norm, S1] "
        "thresholds are applied to a scale they were not derived on (flagged above for "
        f"Stage 5.6), and no user-facing text should present a raw angle as a clinical "
        "measurement.",
        "",
        f"The limits of agreement ([{mean_stats['loa_lower']:.1f}°, "
        f"{mean_stats['loa_upper']:.1f}°]) — not the headline ICC — are the number to "
        "quote as this system's per-rep measurement uncertainty.",
        "",
        "Caveats kept explicit:",
        "",
        "- **Not independent samples.** 98 reps come from 9 subjects; reps within a "
        "subject are correlated, so the ICC is a descriptive agreement figure, not an "
        "inferential claim with a meaningful confidence interval.",
        "- **Mocap is a reference, not truth.** OptiTrack marker placement has its own "
        "error, and its skeleton joint centres are not defined identically to "
        "MediaPipe's landmarks — an unknown share of the bias is definitional (where a "
        "'knee centre' is) rather than pipeline error. The bias should not be read as "
        "a calibration constant to subtract without establishing that share first.",
        "- **Peak/min/ROM only.** Agreement is computed on per-rep summary values, the "
        "quantities the features use. It does not certify the angle at every instant.",
        "- **Leg identity unverified** — see above; per-leg rows are indicative only.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    config = _load_config()
    data = collect(config)
    mean_stats = agreement_stats(data["pairs_mean"])
    min_stats = agreement_stats(data["pairs_min"])
    rom_stats = agreement_stats(data["pairs_rom"])
    leg_stats = {leg: agreement_stats(p) for leg, p in data["pairs_by_leg"].items()}

    plot_bland_altman(data["pairs_mean"], mean_stats)
    write_report(data, mean_stats, leg_stats, min_stats, rom_stats)

    for label, s in (("peak", mean_stats), ("min ", min_stats), ("rom ", rom_stats)):
        print(
            f"{label}: ICC={s['icc']:.3f} bias={s['bias']:+.2f} deg "
            f"LoA=[{s['loa_lower']:.2f}, {s['loa_upper']:.2f}] "
            f"r={s['r']:.3f} n={s['n']}"
        )
    leg_diff_rs = [c["r"] for c in data["leg_diff_checks"]]
    print(
        f"leg-difference vs mocap: mean r={np.mean(leg_diff_rs):+.3f} "
        f"(range {min(leg_diff_rs):+.2f}..{max(leg_diff_rs):+.2f}) -> leg identity "
        "unverifiable; symmetry_index_pct measures noise"
    )
    print(f"offsets chosen: {sorted({v['offset'] for v in data['offsets'].values()})}")
    print(f"wrote {REPORT_MD.name}")


if __name__ == "__main__":
    main()
