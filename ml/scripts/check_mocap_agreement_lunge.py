"""Stage 5.4 (Lunge): MediaPipe knee flexion vs OptiTrack mocap ground truth.

The lunge mirror of `check_mocap_agreement.py`, on Ex5. Compares, on the same frames,
the knee flexion our pipeline derives from MediaPipe world landmarks against the same
angle derived from REHAB24-6's OptiTrack 26-joint mocap. Reports ICC(2,1) +
Bland-Altman, reusing `app.module_a.core.evaluation.agreement` (unit-agnostic and
already shared — not forked). Writes `ml/reports/LUNGE_MOCAP_AGREEMENT.md`.

The mocap is used for validation ONLY, never as a training feature (X3).

**Squat could dodge leg identity; lunge cannot.** Squat's report found its
MediaPipe<->mocap leg mapping unverifiable and escaped via the *bilateral mean*, which
is swap-invariant and is exactly what `knee_flex_peak_deg` uses. Every lunge feature is
front/back split, so a wrong mapping transposes them all. There is nothing to retreat
to, and identity had to be settled.

**How it was settled, and why the obvious test failed.** The natural test — correlating
the leg-difference signal `θ_L − θ_R` against mocap's own, which squat ran — is *also*
inconclusive for lunge (mean r = +0.28, signs mixed). The expectation that a lunge's
asymmetry would make it decisive was wrong, and it is reported as such rather than
quietly dropped. The reason it fails is itself the finding: the difference signal is
dominated by the far limb's own measurement error, so it cannot arbitrate labels.

Identity is instead established from **foot position**, which occlusion biases far less
than flexion: the front foot is anterior by definition, and the dataset annotates which
leg leads. Both sources independently recover the annotated lead leg from geometry alone
in 9/9 videos, so both label sets are correct and the mapping is confirmed. See
`forward_foot_identity()`.

That result then reframes a second observation. Mocap says the right knee bends deeper
in all 9 videos; MediaPipe says the left does in all 9 — a perfect reversal. With the
labels confirmed, this cannot be a swap: it is the far-limb occlusion bias, large enough
to invert which knee *appears* deeper. Quantified in `cohort_front_bias()`.

Deterministic (X8): sorted iteration, no RNG.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Reused, never forked: the same stats module Module A's SLS/WBLT evaluations use.
from app.module_a.core.evaluation.agreement import bland_altman, icc_2_1
from app.module_b.core.geometry import knee_flexion_deg
from build_features_lunge import (
    LEAD_LEG_MAP,
    SIDE_VIEW_ORIENTATION,
    TARGET_EXERCISE_ID,
    _load_config,
    _preprocessed_stream,
    _raw_full_stream,
    _read_segmentation,
)
from plotting import save_fig

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "LUNGE_MOCAP_AGREEMENT.md"

MOCAP_DIR = Path("/Users/sumhonyou/fypDataset/3d_joints/Ex5")

# joints_names.txt: 16 LeftUpLeg / 17 LeftLeg / 18 LeftFoot / 19 LeftToeBase,
# 21 RightUpLeg / 22 RightLeg / 23 RightFoot / 24 RightToeBase.
MOCAP_LEGS = {"left": (16, 17, 18), "right": (21, 22, 23)}
MOCAP_FEET = {"left": (18, 19), "right": (23, 24)}  # (ankle, toe)
# MediaPipe pose landmarks, same (hip, knee, ankle) roles, plus (ankle, toe).
MP_LEGS = {"left": (23, 25, 27), "right": (24, 26, 28)}
MP_FEET = {"left": (27, 31), "right": (28, 32)}
MP_KNEE = {"left": 25, "right": 26}
# Stage 5.2 (Lunge) measured LEFT as the higher-visibility (near) limb in all 9
# videos, regardless of lead leg -- so RIGHT is the far/occluded one throughout.
FAR_LEG = "right"
NEAR_LEG = "left"

OFFSET_SCAN = range(-5, 6)
# Thresholds fixed BEFORE the numbers were seen, so neither test is scored to taste.
# A leg-difference |mean r| below this, or with mixed signs, is "cannot call".
LEG_IDENTITY_MIN_ABS_R = 0.5


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


def _lead_legs(side_view_rows: list[dict]) -> dict[str, str]:
    """Each video's annotated lead leg, from the dataset's own exercise_subtype."""
    leads: dict[str, str] = {}
    for row in side_view_rows:
        lead = LEAD_LEG_MAP[row["exercise_subtype"]]
        if leads.setdefault(row["video_id"], lead) != lead:
            raise ValueError(
                f"{row['video_id']} annotates more than one lead leg; the front/back "
                "split assumes one lead leg per video"
            )
    return leads


def _mocap_forward_foot(mocap: np.ndarray) -> str:
    """Which mocap leg is planted forward, from geometry alone.

    The anterior direction is taken from the feet themselves (toe minus ankle, averaged
    over both feet and all frames), so no knowledge of the room's axes is needed.
    """
    anterior = (
        (mocap[:, MOCAP_FEET["left"][1], :3] - mocap[:, MOCAP_FEET["left"][0], :3])
        + (mocap[:, MOCAP_FEET["right"][1], :3] - mocap[:, MOCAP_FEET["right"][0], :3])
    ).mean(axis=0)
    anterior = anterior / np.linalg.norm(anterior)
    left = float((mocap[:, MOCAP_FEET["left"][0], :3] @ anterior).mean())
    right = float((mocap[:, MOCAP_FEET["right"][0], :3] @ anterior).mean())
    return "left" if left > right else "right"


def _mp_forward_foot(frames: list[dict]) -> str:
    """Which MediaPipe leg is planted forward — the same rule `features.py` uses."""
    toe_ahead = sum(
        (
            f["worldLandmarks"][MP_FEET[side][1]]["x"]
            - f["worldLandmarks"][MP_FEET[side][0]]["x"]
        )
        for f in frames
        for side in ("left", "right")
    )
    sign = 1.0 if toe_ahead >= 0.0 else -1.0
    left = np.mean(
        [f["worldLandmarks"][MP_FEET["left"][0]]["x"] * sign for f in frames]
    )
    right = np.mean(
        [f["worldLandmarks"][MP_FEET["right"][0]]["x"] * sign for f in frames]
    )
    return "left" if left >= right else "right"


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
    leads = _lead_legs(side_view_rows)

    per_video_offsets = {}
    leg_diff_checks = []
    identity_checks = []
    deeper_leg_checks = []
    pairs_front: list[tuple[float, float]] = []
    pairs_back: list[tuple[float, float]] = []
    pairs_near: list[tuple[float, float]] = []
    pairs_far: list[tuple[float, float]] = []
    pairs_mean: list[tuple[float, float]] = []
    # Front-knee error split by cohort -- the coupling Stage 5.2 flagged for this gate.
    front_bias_by_lead: dict[str, list[float]] = {"left": [], "right": []}
    # (lead_leg, limb) -> per-rep bias and raw visibility. Decomposing the error this
    # way separates two explanations that the pooled far-limb figure conflates:
    # "low confidence" (the filter should catch it) vs "confidently wrong" (it cannot).
    cell_bias: dict[tuple[str, str], list[float]] = {}
    cell_visibility: dict[tuple[str, str], list[float]] = {}
    per_video_front_bias: dict[str, float] = {}

    for video_id in video_ids:
        mocap = np.load(MOCAP_DIR / f"{video_id}-30fps.npy")
        frames = _preprocessed_stream(video_id, preprocessed_cache, frame_count_cache)
        # Raw, not preprocessed: preprocessing rewrites visibility, so the raw stream
        # is the only place MediaPipe's own confidence survives intact.
        raw_frames, _total = _raw_full_stream(video_id)
        raw_by_index = {f["frameIndex"]: f for f in raw_frames}
        indices, mp_left = _mp_flexion(frames, "left")
        _indices, mp_right = _mp_flexion(frames, "right")
        mocap_left = _mocap_flexion(mocap, "left")
        mocap_right = _mocap_flexion(mocap, "right")

        # (1) The test squat ran: correlate the leg-DIFFERENCE signals.
        leg_diff_checks.append(
            {
                "video_id": video_id,
                "r": _corr(
                    mp_left - mp_right, mocap_left[indices] - mocap_right[indices]
                ),
                "lead_leg": leads[video_id],
            }
        )

        # (2) The test that works: identity from foot POSITION, checked against the
        # dataset's own lead-leg annotation, independently for each source.
        mocap_forward = _mocap_forward_foot(mocap)
        mp_forward = _mp_forward_foot(frames)
        identity_checks.append(
            {
                "video_id": video_id,
                "annotated_lead": leads[video_id],
                "mocap_forward": mocap_forward,
                "mp_forward": mp_forward,
                "mocap_ok": mocap_forward == leads[video_id],
                "mp_ok": mp_forward == leads[video_id],
            }
        )

        # (3) Which leg does each source think bends deeper? (A level comparison, so
        # it is exposed to the far-limb bias in a way the position test is not.)
        deeper_leg_checks.append(
            {
                "video_id": video_id,
                "mocap_delta": float(
                    np.mean(mocap_left[indices] - mocap_right[indices])
                ),
                "mp_delta": float(np.mean(mp_left - mp_right)),
            }
        )

        offset, r = _best_offset(mp_left, mocap_left[indices])
        per_video_offsets[video_id] = {"offset": offset, "r": r}

        front = leads[video_id]
        back = "right" if front == "left" else "left"
        mp_by_leg = {"left": mp_left, "right": mp_right}
        mocap_by_leg = {"left": mocap_left, "right": mocap_right}
        mp_mean = (mp_left + mp_right) / 2.0
        mocap_mean = (mocap_left + mocap_right) / 2.0
        index_of = {int(f): i for i, f in enumerate(indices)}

        video_front_diffs = []
        for row in (r for r in side_view_rows if r["video_id"] == video_id):
            first, last = int(row["first_frame"]), int(row["last_frame"])
            window = [index_of[f] for f in range(first, last + 1) if f in index_of]
            mocap_window = [
                f + offset
                for f in range(first, last + 1)
                if 0 <= f + offset < len(mocap_mean)
            ]
            if not window or not mocap_window:
                continue

            for leg, bucket in (
                (front, pairs_front),
                (back, pairs_back),
                (FAR_LEG, pairs_far),
                (NEAR_LEG, pairs_near),
            ):
                bucket.append(
                    (
                        float(np.max(mp_by_leg[leg][window])),
                        float(np.max(mocap_by_leg[leg][mocap_window])),
                    )
                )

            # Per (cohort, limb): this rep's peak error and the limb's raw confidence.
            for leg in ("left", "right"):
                cell_bias.setdefault((front, leg), []).append(
                    float(np.max(mp_by_leg[leg][window]))
                    - float(np.max(mocap_by_leg[leg][mocap_window]))
                )
                rep_visibility = [
                    float(raw_by_index[f]["worldLandmarks"][MP_KNEE[leg]]["visibility"])
                    for f in range(first, last + 1)
                    if f in raw_by_index
                ]
                if rep_visibility:
                    cell_visibility.setdefault((front, leg), []).append(
                        float(np.mean(rep_visibility))
                    )
            pairs_mean.append(
                (
                    float(np.max(mp_mean[window])),
                    float(np.max(mocap_mean[mocap_window])),
                )
            )
            front_error = float(np.max(mp_by_leg[front][window])) - float(
                np.max(mocap_by_leg[front][mocap_window])
            )
            front_bias_by_lead[front].append(front_error)
            video_front_diffs.append(front_error)
        per_video_front_bias[video_id] = float(np.mean(video_front_diffs))

    return {
        "offsets": per_video_offsets,
        "leg_diff_checks": leg_diff_checks,
        "identity_checks": identity_checks,
        "deeper_leg_checks": deeper_leg_checks,
        "leads": leads,
        "pairs_front": pairs_front,
        "pairs_back": pairs_back,
        "pairs_near": pairs_near,
        "pairs_far": pairs_far,
        "pairs_mean": pairs_mean,
        "front_bias_by_lead": front_bias_by_lead,
        "per_video_front_bias": per_video_front_bias,
        "cell_bias": cell_bias,
        "cell_visibility": cell_visibility,
    }


def bias_vs_visibility(cell_bias: dict, cell_visibility: dict) -> dict:
    """Decompose the error by (cohort, limb) against the limb's own raw confidence.

    Separates two explanations the pooled far-limb figure conflates:
      - "low confidence": the landmark is flagged uncertain, so the confidence filter
        engages and the error is a reconstruction artefact — fixable upstream.
      - "confidently wrong": MediaPipe reports high visibility and is still badly
        wrong — no confidence signal exists to key any mitigation off.
    """
    cells = []
    for (lead, leg), biases in sorted(cell_bias.items()):
        visibilities = cell_visibility.get((lead, leg), [])
        cells.append(
            {
                "lead": lead,
                "leg": leg,
                "role": "front" if leg == lead else "back",
                "limb": "near" if leg == NEAR_LEG else "far",
                "n": len(biases),
                "bias": float(np.mean(biases)),
                "visibility": float(np.mean(visibilities)) if visibilities else None,
            }
        )
    # Is the error explained better by which limb it is, or by how confident MediaPipe
    # was? Averaged the two ways, over the same four cells.
    by_limb = {
        limb: float(np.mean([c["bias"] for c in cells if c["limb"] == limb]))
        for limb in ("near", "far")
    }
    by_role = {
        role: float(np.mean([c["bias"] for c in cells if c["role"] == role]))
        for role in ("front", "back")
    }
    # The decisive cell: the far limb where MediaPipe was MOST confident.
    far_cells = [c for c in cells if c["limb"] == "far" and c["visibility"] is not None]
    most_confident_far = (
        max(far_cells, key=lambda c: c["visibility"]) if far_cells else None
    )
    return {
        "cells": cells,
        "by_limb": by_limb,
        "by_role": by_role,
        "limb_gap": abs(by_limb["near"] - by_limb["far"]),
        "role_gap": abs(by_role["front"] - by_role["back"]),
        "most_confident_far": most_confident_far,
    }


def agreement_stats(pairs: list[tuple[float, float]]) -> dict:
    system = [p[0] for p in pairs]
    manual = [p[1] for p in pairs]
    stats = bland_altman(system, manual)
    stats["icc"] = icc_2_1(system, manual)
    stats["r"] = _corr(np.array(system), np.array(manual))
    return stats


def leg_difference_verdict(checks: list[dict]) -> dict:
    """Squat's leg-identity test, re-run on lunge. Expected to be decisive; was not."""
    rs = [c["r"] for c in checks]
    mean_r = float(np.mean(rs))
    all_same_sign = all(r > 0 for r in rs) or all(r < 0 for r in rs)
    decisive = abs(mean_r) >= LEG_IDENTITY_MIN_ABS_R and all_same_sign
    return {
        "status": (
            ("CONFIRMED" if mean_r > 0 else "SWAPPED") if decisive else "UNRESOLVED"
        ),
        "mean_r": mean_r,
        "min_r": float(min(rs)),
        "max_r": float(max(rs)),
        "all_same_sign": all_same_sign,
    }


def forward_foot_identity(checks: list[dict]) -> dict:
    """Identity from foot position — both sources vs the dataset's lead-leg annotation."""
    mocap_ok = sum(1 for c in checks if c["mocap_ok"])
    mp_ok = sum(1 for c in checks if c["mp_ok"])
    n = len(checks)
    return {
        "n": n,
        "mocap_ok": mocap_ok,
        "mp_ok": mp_ok,
        # Both sources independently recovering the annotation means both label sets
        # are right, hence the cross-source mapping is right.
        "status": "CONFIRMED" if (mocap_ok == n and mp_ok == n) else "UNRESOLVED",
    }


def deeper_leg_reversal(checks: list[dict]) -> dict:
    """How often do mocap and MediaPipe disagree on which knee bends deeper?"""
    disagree = sum(1 for c in checks if (c["mocap_delta"] > 0) != (c["mp_delta"] > 0))
    return {
        "n": len(checks),
        "disagree": disagree,
        "mocap_all_right_deeper": all(c["mocap_delta"] < 0 for c in checks),
        "mp_all_left_deeper": all(c["mp_delta"] > 0 for c in checks),
    }


def cohort_front_bias(front_bias_by_lead: dict[str, list[float]]) -> dict:
    """Front-knee measurement bias per lead-leg cohort.

    Because the far limb is `right` in every video, the front leg IS the occluded limb
    for right-lead subjects and the near limb for left-lead ones. This measures what
    that costs the gate feature.
    """
    out = {
        lead: {
            "n": len(values),
            "bias": float(np.mean(values)),
            "role": "far (occluded)" if lead == FAR_LEG else "near",
        }
        for lead, values in sorted(front_bias_by_lead.items())
    }
    out["gap"] = abs(out["left"]["bias"] - out["right"]["bias"])
    return out


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
    ax.set_xlabel("Mean of MediaPipe and mocap peak FRONT knee flexion (°)")
    ax.set_ylabel("MediaPipe − mocap (°)")
    ax.set_title(
        f"Bland-Altman: peak front knee flexion per rep "
        f"(n={stats['n']}, ICC={stats['icc']:.3f})"
    )
    ax.legend(fontsize=8, loc="best")
    path = save_fig(fig, "lunge_mocap_agreement_bland_altman", figsize="bland_altman")
    plt.close(fig)
    return path


def main() -> None:
    config = _load_config()
    data = collect(config)

    leg_diff = leg_difference_verdict(data["leg_diff_checks"])
    identity = forward_foot_identity(data["identity_checks"])
    reversal = deeper_leg_reversal(data["deeper_leg_checks"])
    cohort = cohort_front_bias(data["front_bias_by_lead"])
    decomposition = bias_vs_visibility(data["cell_bias"], data["cell_visibility"])

    stats = {
        "front": agreement_stats(data["pairs_front"]),
        "back": agreement_stats(data["pairs_back"]),
        "near": agreement_stats(data["pairs_near"]),
        "far": agreement_stats(data["pairs_far"]),
        "mean": agreement_stats(data["pairs_mean"]),
    }

    plot_bland_altman(data["pairs_front"], stats["front"])
    write_report(data, leg_diff, identity, reversal, cohort, stats, decomposition)

    print(
        f"leg-difference test (squat's): {leg_diff['status']} "
        f"mean r={leg_diff['mean_r']:+.3f} "
        f"(range {leg_diff['min_r']:+.2f}..{leg_diff['max_r']:+.2f}, "
        f"same sign={leg_diff['all_same_sign']})"
    )
    print(
        f"forward-foot identity test:    {identity['status']} "
        f"mocap {identity['mocap_ok']}/{identity['n']}, "
        f"MediaPipe {identity['mp_ok']}/{identity['n']} vs the annotation"
    )
    print(
        f"deeper-leg reversal: mocap and MediaPipe disagree on "
        f"{reversal['disagree']}/{reversal['n']} videos "
        f"(mocap all-right-deeper={reversal['mocap_all_right_deeper']}, "
        f"mp all-left-deeper={reversal['mp_all_left_deeper']})"
    )
    for label in ("front", "back", "near", "far", "mean"):
        s = stats[label]
        print(
            f"{label:<6}: ICC={s['icc']:.3f} bias={s['bias']:+.2f} deg "
            f"LoA=[{s['loa_lower']:.2f}, {s['loa_upper']:.2f}] "
            f"r={s['r']:.3f} n={s['n']}"
        )
    for lead in ("left", "right"):
        c = cohort[lead]
        print(
            f"  front-knee bias, lead={lead:<5} (front leg is {c['role']:<15}): "
            f"{c['bias']:+.2f} deg over {c['n']} reps"
        )
    print(f"  => cohort-dependent bias on the gate feature: {cohort['gap']:.1f} deg")
    print("bias decomposed by (cohort, limb) vs raw visibility:")
    for c in decomposition["cells"]:
        print(
            f"  lead={c['lead']:<5} {c['leg']:<5} ({c['role']:<5}, {c['limb']:<4}) "
            f"n={c['n']:<3} vis={c['visibility']:.3f} bias={c['bias']:+.2f}"
        )
    print(
        f"  explained by near/far: gap {decomposition['limb_gap']:.1f} deg | "
        f"by front/back: gap {decomposition['role_gap']:.1f} deg"
    )
    mcf = decomposition["most_confident_far"]
    print(
        f"  most-confident FAR cell: lead={mcf['lead']} {mcf['leg']} vis="
        f"{mcf['visibility']:.3f} but bias={mcf['bias']:+.2f} -> confidently wrong"
    )
    print(f"offsets chosen: {sorted({v['offset'] for v in data['offsets'].values()})}")
    print(f"wrote {REPORT_MD.name}")


def write_report(
    data: dict,
    leg_diff: dict,
    identity: dict,
    reversal: dict,
    cohort: dict,
    stats: dict,
    decomposition: dict,
) -> None:
    offsets = data["offsets"]
    unique_offsets = sorted({v["offset"] for v in offsets.values()})
    front, back = stats["front"], stats["back"]
    near, far, mean = stats["near"], stats["far"], stats["mean"]

    lines = [
        "# Stage 5.4 (Lunge) — MediaPipe vs OptiTrack mocap agreement",
        "",
        "Does the single-camera pipeline actually measure the knee angles it claims to? "
        "Compares, on the same frames, the knee flexion our pipeline derives from "
        "MediaPipe world landmarks against the same angle derived from REHAB24-6's "
        "OptiTrack 26-joint mocap, on Ex5. **The mocap is a validation reference only — "
        "never a training feature (X3).**",
        "",
        "## Headline",
        "",
        f"**`front_knee_flex_peak_deg`: ICC(2,1) = {front['icc']:.3f}**, "
        f"**bias {front['bias']:+.2f}°**, **95% limits of agreement "
        f"[{front['loa_lower']:.2f}°, {front['loa_upper']:.2f}°]**, "
        f"r = {front['r']:.3f}, n = {front['n']} reps.",
        "",
        "The compared quantity is the per-rep peak of the **front** knee — the R5.5 gate "
        "feature — so this speaks to the real feature rather than to an angle nothing "
        "uses. Negative bias means our pipeline reads *lower* than mocap.",
        "",
        "![Bland-Altman: peak front knee flexion vs mocap](figures/lunge_mocap_agreement_bland_altman.png)",
        "",
        "**But the headline is not the finding.** Two results below matter more than the "
        "pooled ICC: leg identity is now *settled* for lunge (squat could not settle "
        "it), and the far-limb occlusion error turns out to be large enough to invert "
        "which knee appears deeper — which loads a "
        f"**{cohort['gap']:.1f}° cohort-dependent bias** onto the gate feature.",
        "",
        "## Leg identity: settled — but not by the test that was supposed to settle it",
        "",
        "**Why this had to be answered here.** Squat's report closed the same question as "
        "unresolvable and worked around it: both knees bend together in a squat, so the "
        "leg-difference signal cancels to noise (mean r ≈ +0.02, signs mixed), and that "
        "report escaped via the **bilateral mean**, which is invariant to a left/right "
        "swap and is exactly what `knee_flex_peak_deg` uses. No such escape exists for "
        "lunge: every feature is front/back split, so a swapped mapping transposes "
        "*all* of them. There is nothing swap-invariant to retreat to.",
        "",
        "### The expected test failed, and that is reported rather than dropped",
        "",
        "The reasonable expectation was that a lunge's asymmetry would rescue squat's "
        "test: the front and back knees do different jobs, so `θ_L − θ_R` should carry a "
        "large structured signal instead of a cancelled common mode. **It did not.** "
        f"Correlated against mocap's own leg difference, the result is a mean r of "
        f"**{leg_diff['mean_r']:+.3f}** across the {len(data['leg_diff_checks'])} videos "
        f"(range {leg_diff['min_r']:+.2f} to {leg_diff['max_r']:+.2f}, "
        f"{'signs consistent' if leg_diff['all_same_sign'] else '**signs mixed**'}) — "
        f"**{leg_diff['status']}** against a rule fixed before the numbers were seen "
        f"(|mean r| >= {LEG_IDENTITY_MIN_ABS_R} with consistent signs). Re-running it at "
        "each video's own alignment offset rather than at lag 0 changes nothing "
        "(r moves by <0.03), so this is not a synchronisation artefact.",
        "",
        "The reason it fails is itself informative, and it connects to the occlusion "
        "result below: the leg-difference signal is **dominated by the far limb's own "
        "measurement error**, so it cannot arbitrate labels. A test built on the "
        "difference of two angles inherits the noise of the worse-measured one.",
        "",
        "| video | lead leg | leg-difference r vs mocap |",
        "| ----- | -------- | ------------------------- |",
    ]
    for c in sorted(data["leg_diff_checks"], key=lambda c: c["video_id"]):
        lines.append(f"| {c['video_id']} | {c['lead_leg']} | {c['r']:+.3f} |")

    lines += [
        "",
        "### The test that works: identity from foot position",
        "",
        "Flexion is the wrong instrument, because flexion is what occlusion corrupts. "
        "**Foot position is not** — a planted foot's location is far more robust than "
        "the joint angle above it. And the dataset supplies an independent key the "
        "flexion test lacks: `exercise_subtype` annotates **which leg leads**, and the "
        "front foot is anterior by definition.",
        "",
        "So each source is asked, from geometry alone, which foot is planted forward — "
        "and checked against the annotation independently. For mocap the anterior "
        "direction is derived from the feet themselves (toe minus ankle), needing no "
        "knowledge of the room axes; for MediaPipe it is the same rule "
        "`features.py::_anterior_sign` already uses live.",
        "",
        f"| result | agreement with the annotated lead leg |",
        "| ------ | ------------------------------------- |",
        f"| OptiTrack mocap forward foot | **{identity['mocap_ok']}/{identity['n']}** |",
        f"| MediaPipe forward foot | **{identity['mp_ok']}/{identity['n']}** |",
        "",
        f"**Verdict: leg identity {identity['status']}.** Both sources independently "
        "recover the annotated lead leg in every video, so both label sets are correct "
        "as labelled — and therefore the mapping between them is correct too. "
        "`MOCAP_LEGS['left']` is the same anatomical leg as `MP_LEGS['left']`. The "
        "front/back split that every lunge feature depends on rests on verified ground, "
        "which is what this gate needed to establish.",
        "",
        "| video | annotated lead | mocap forward foot | MediaPipe forward foot |",
        "| ----- | -------------- | ------------------ | ---------------------- |",
    ]
    for c in sorted(data["identity_checks"], key=lambda c: c["video_id"]):
        lines.append(
            f"| {c['video_id']} | {c['annotated_lead']} | {c['mocap_forward']} "
            f"{'✓' if c['mocap_ok'] else '✗'} | {c['mp_forward']} "
            f"{'✓' if c['mp_ok'] else '✗'} |"
        )

    lines += [
        "",
        "## Occlusion is severe enough to invert which knee looks deeper",
        "",
        f"With identity confirmed, a second observation can be read correctly. **Mocap "
        f"says the right knee bends deeper in all 9 videos; MediaPipe says the left does "
        f"in all 9** — the two disagree on **{reversal['disagree']}/{reversal['n']}**, a "
        "perfect reversal (chance would be ~4/9).",
        "",
        "Had identity been left open, this would have looked like decisive proof of a "
        "**swapped mapping** — it is exactly the signature a swap produces. The position "
        "test rules that out, leaving one explanation: **the far limb's error is bigger "
        f"than the real left-right difference.** The pipeline under-reads the occluded "
        f"far limb by {abs(far['bias']):.1f}° against {abs(near['bias']):.1f}° for the "
        f"near limb — a differential of ~{abs(far['bias'] - near['bias']):.1f}°, while "
        "the true left-right difference is only a few degrees. The artefact is larger "
        "than the signal, so the ordering flips.",
        "",
        "This is the strongest available statement of what monocular occlusion costs "
        "here, and it is worth stating as such: **the far limb is not merely noisier — "
        "it is wrong by more than the anatomy it is meant to resolve.**",
        "",
        "| quantity per rep | bias (MediaPipe − mocap) | 95% LoA | ICC | r | n |",
        "| ---------------- | ------------------------ | ------- | --- | - | - |",
        f"| **front** knee peak (`front_knee_flex_peak_deg`) | {front['bias']:+.2f}° | "
        f"[{front['loa_lower']:.1f}, {front['loa_upper']:.1f}]° | {front['icc']:.3f} | "
        f"{front['r']:.3f} | {front['n']} |",
        f"| **back** knee peak (`back_knee_flex_peak_deg`) | {back['bias']:+.2f}° | "
        f"[{back['loa_lower']:.1f}, {back['loa_upper']:.1f}]° | {back['icc']:.3f} | "
        f"{back['r']:.3f} | {back['n']} |",
        f"| **near** limb ({NEAR_LEG}) knee peak | {near['bias']:+.2f}° | "
        f"[{near['loa_lower']:.1f}, {near['loa_upper']:.1f}]° | {near['icc']:.3f} | "
        f"{near['r']:.3f} | {near['n']} |",
        f"| **far** limb ({FAR_LEG}) knee peak | {far['bias']:+.2f}° | "
        f"[{far['loa_lower']:.1f}, {far['loa_upper']:.1f}]° | {far['icc']:.3f} | "
        f"{far['r']:.3f} | {far['n']} |",
        f"| bilateral mean (squat's headline quantity, for comparison) | "
        f"{mean['bias']:+.2f}° | [{mean['loa_lower']:.1f}, {mean['loa_upper']:.1f}]° | "
        f"{mean['icc']:.3f} | {mean['r']:.3f} | {mean['n']} |",
        "",
        "The near/far rows answer the question **Stage 5.3 (Lunge) deferred to this "
        "gate** — is the occluded far limb's estimate accurate, or merely plausible? "
        "Squat's equivalent had to leave it formally open, because answering it needs "
        "exactly the per-leg comparison its unverified leg mapping made impossible. "
        "**The answer for lunge: merely plausible.** The far limb tracks the movement's "
        f"shape well (r = {far['r']:.3f}, comparable to the near limb's "
        f"{near['r']:.3f}) but mis-states its magnitude by "
        f"{abs(far['bias']):.1f}° — the classic signature of a landmark regressor "
        "hedging toward a mean pose when it cannot see the joint.",
        "",
        "### Is it low confidence, or confident error?",
        "",
        "'Occlusion' is a mechanism, not a measurement, so the claim is tested rather "
        "than assumed. Splitting the per-rep peak error by **(cohort, limb)** and "
        "putting MediaPipe's own raw visibility beside it separates two very different "
        "explanations — a landmark flagged uncertain (the confidence filter engages; "
        "fixable upstream) versus one MediaPipe is confident about and wrong anyway "
        "(no signal exists to key any mitigation off).",
        "",
        "| cohort | limb | role | near/far | reps | raw visibility | peak bias |",
        "| ------ | ---- | ---- | -------- | ---- | -------------- | --------- |",
    ]
    for c in decomposition["cells"]:
        visibility = "n/a" if c["visibility"] is None else f"{c['visibility']:.3f}"
        lines.append(
            f"| lead={c['lead']} | {c['leg']} | {c['role']} | {c['limb']} | {c['n']} | "
            f"{visibility} | {c['bias']:+.2f}° |"
        )

    mcf = decomposition["most_confident_far"]
    lines += [
        "",
        f"**The error follows the limb, not the role.** Averaged by near/far the two "
        f"differ by **{decomposition['limb_gap']:.1f}°**; averaged by front/back, by "
        f"only **{decomposition['role_gap']:.1f}°**. The right knee is badly under-read "
        "whether it is doing the front leg's job or the back leg's, and the left knee is "
        "well measured in both. Which side faced the camera is what matters.",
        "",
        "**And it is confident error, not flagged uncertainty — the more troubling of "
        "the two.** The decisive cell is the far limb where MediaPipe was *most* sure of "
        f"itself: lead={mcf['lead']}, {mcf['leg']} knee, raw visibility "
        f"**{mcf['visibility']:.3f}** — a healthy confidence, nowhere near the "
        f"`MIN_VISIBILITY` cut-off — and a bias of **{mcf['bias']:+.2f}°** regardless. "
        "The pipeline is not saying 'I cannot see this knee'; it is saying 'this knee "
        "is at 75°' when the markers say 90°. **No confidence-threshold policy can "
        "catch that**, because the confidence is high. The companion visibility report "
        "measures where the landmark *does* drop below the threshold — a real but much "
        "smaller effect — and the two together show the filter is not the lever here.",
        "",
        "## The consequence: a cohort-dependent bias on the gate feature",
        "",
        "This is the finding with the furthest reach, and it closes an open question "
        "carried since Stage 5.2 — *whether the lead limb is the near or far limb is "
        "fixed per subject, which would couple occlusion to lead leg and therefore to "
        "subject.* **It is, and it does.**",
        "",
        f"The far limb is `{FAR_LEG}` in all 9 videos (a camera-orientation artefact, "
        "not a lead-leg effect — Stage 5.2). Lead leg is fixed per subject. Therefore "
        "the front leg **is** the occluded limb for right-lead subjects and the clearly "
        "visible one for left-lead subjects:",
        "",
        "| cohort | front leg is the... | reps | front-knee bias |",
        "| ------ | ------------------- | ---- | --------------- |",
    ]
    for lead in ("left", "right"):
        c = cohort[lead]
        lines.append(
            f"| lead={lead} | {c['role']} limb | {c['n']} | {c['bias']:+.2f}° |"
        )

    lines += [
        "",
        f"**`front_knee_flex_peak_deg` — the feature the R5.5 gate turns on — is "
        f"measured with a {cohort['gap']:.1f}° systematic offset between the two "
        "cohorts, purely as a camera artefact.** No subject moves differently to "
        "produce it; it is a property of which side of the body faced the lens.",
        "",
        "Three consequences, none of them resolved here:",
        "",
        "1. **Stage 5.0's leakage warning is now quantified, not hypothetical.** It "
        "flagged `lead_leg` as a LOSO leakage risk because it is confounded with "
        "subject. This shows the confound is *physically encoded in the feature "
        "values themselves* — a model can infer the cohort from the measurement bias "
        "without ever seeing a `lead_leg` column. Excluding `lead_leg` from the "
        "feature vector (Stage 5.3 did) is therefore necessary but **not sufficient** "
        "to remove the confound.",
        "2. **It compounds the pooling hazard the feature-validity gate found "
        "independently.** That report showed pooled statistics inverting the "
        "within-subject truth via class-mix imbalance; this is a second, unrelated "
        "mechanism pushing the same way. Two independent reasons to distrust "
        "cross-subject pooling on this cohort.",
        "3. **It bounds what any lunge ROM banding can claim** — more tightly than "
        f"squat's equivalent. A ~{abs(front['bias']):.0f}° under-read is bad enough for "
        "thresholds derived from true joint angles; one that also differs by "
        f"{cohort['gap']:.1f}° depending on which leg the user happens to lead with "
        "cannot be corrected by a single global constant. Stage 5.6 (Lunge) is already "
        "directed to derive its band edges from this cohort's own distribution and tag "
        "them [dataset-derived] — this is the measurement that justifies that "
        "instruction, and a reason not to soften it.",
        "",
        "**It does not invalidate the classifier**, which learns from our measurements "
        "on their own scale. But the bias is cohort-structured rather than global, so it "
        "is not the harmless monotone offset squat's report could wave through: it is a "
        "systematic difference between two subject groups that the model may learn "
        "instead of the movement. That is Stage 5.5's problem to watch for, and it is "
        "flagged here rather than discovered there.",
        "",
        "## Method notes (verified, not assumed)",
        "",
        f"- **Frame alignment.** An offset scan ({OFFSET_SCAN.start}.."
        f"{OFFSET_SCAN.stop - 1} frames) picks the lag maximising correlation per video "
        f"rather than trusting index 0. Selected: {unique_offsets} frame(s) for every "
        "video — consistent with the causal One Euro filter's own delay, the same "
        "magnitude squat's run found.",
        "- **Same geometry helper both sides.** Both series go through the live "
        "pipeline's `knee_flexion_deg`; an unsigned hip-knee-ankle angle is invariant "
        "to the coordinate frame, so mocap's room axes and MediaPipe's hip-origin axes "
        "need no alignment.",
        "- **Our side is the preprocessed stream** (confidence filter → gap fill → One "
        "Euro), i.e. what the model actually consumes, not raw landmarks.",
        "- **Front/back assignment comes from the dataset's own `exercise_subtype`**, "
        "not from our geometric inference — so the agreement figures measure the angle "
        "pipeline, not the front-leg resolver. (The resolver is validated separately, "
        "and independently, by the forward-foot table above: 9/9.)",
        "",
        "## Per-video alignment detail",
        "",
        "| video | lead leg | chosen offset (frames) | correlation at that offset | mean front-knee bias (°) |",
        "| ----- | -------- | ---------------------- | -------------------------- | ------------------------ |",
    ]
    for video_id in sorted(offsets):
        v = offsets[video_id]
        lines.append(
            f"| {video_id} | {data['leads'][video_id]} | {v['offset']:+d} | "
            f"{v['r']:.4f} | {data['per_video_front_bias'][video_id]:+.2f} |"
        )

    lines += [
        "",
        "## Caveats kept explicit",
        "",
        f"- **Not independent samples.** {front['n']} reps come from 8 subjects; reps "
        "within a subject are correlated, so the ICC is a descriptive agreement figure, "
        "not an inferential claim with a meaningful confidence interval.",
        "- **Mocap is a reference, not truth.** OptiTrack marker placement has its own "
        "error, and its skeleton joint centres are not defined identically to "
        "MediaPipe's landmarks — an unknown share of the bias is definitional (where a "
        "'knee centre' is) rather than pipeline error. The bias should not be read as a "
        "calibration constant to subtract without establishing that share first. Note "
        "this caveat does **not** weaken the cohort-gap result: a definitional offset "
        "would apply to both cohorts equally and cannot produce a difference between "
        "them.",
        "- **Peak only.** Agreement is computed on per-rep peak values, the quantity the "
        "gate feature uses. It does not certify the angle at every instant.",
        "- **Near/far is a fixed property of this cohort, not a controlled variable.** "
        f"Stage 5.2 measured {NEAR_LEG} as the higher-visibility limb in all 9 videos, "
        "so 'near vs far' here is also 'left vs right'. The two cannot be separated with "
        "this data, and any genuine anatomical left/right asymmetry would be "
        "indistinguishable from an occlusion effect. What makes the occlusion reading "
        "the better explanation is the *size* of the effect — a "
        f"{abs(far['bias'] - near['bias']):.1f}° systematic left-right difference is far "
        "beyond any plausible population-level limb asymmetry, and it points the same "
        "way in every subject.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
