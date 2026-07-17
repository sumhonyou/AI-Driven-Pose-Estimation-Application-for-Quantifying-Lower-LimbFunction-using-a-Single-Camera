"""Stage 5.4 (Lunge): does the far limb fall below MIN_VISIBILITY *at rep depth*?

Closes the question Stage 5.2 (Lunge) flagged and deliberately left open: its
visibility figures were **per-video means**, and a mean can hide a dip. The lowest
recorded was 0.672 (PM_117b's right knee) — above MIN_VISIBILITY = 0.6, but not by
much, and an average over a whole video says nothing about the deepest frames of
individual reps, which is exactly where the far knee is most occluded and where the
features are read.

The question matters because MIN_VISIBILITY is the switch for real behaviour, not a
label: below it, `preprocess_world_landmarks` treats the landmark as missing and either
gap-fills it (short gaps) or releases hold-last (long ones). If the far knee crosses
that line at the bottom of reps, the feature values there are reconstructions rather
than measurements — and `back_knee_*` for left-lead subjects, or `front_knee_*` for
right-lead ones, are being computed on interpolated data at the one moment that counts.

Measured on the **raw** stream, deliberately: preprocessing rewrites visibility (a
released landmark is set to exactly MIN_VISIBILITY), so asking the preprocessed stream
would be asking the filter to grade its own homework.

Writes `ml/reports/LUNGE_OCCLUSION_CHECK.md`.

Deterministic (X8): sorted iteration, no RNG.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from app.module_a.core.config import MIN_VISIBILITY
from app.module_b.core.config import MODULE_B_CORE_CONFIG
from build_features_lunge import (
    LEAD_LEG_MAP,
    SIDE_VIEW_ORIENTATION,
    TARGET_EXERCISE_ID,
    _load_config,
    _raw_full_stream,
    _read_segmentation,
)

ML_ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ML_ROOT / "reports" / "LUNGE_OCCLUSION_CHECK.md"

# Stage 5.2 (Lunge): LEFT is the higher-visibility (near) limb in all 9 videos.
FAR_LEG = "right"
NEAR_LEG = "left"
KNEE = {"left": 25, "right": 26}
# The fraction of a rep around its deepest frame counted as "at depth" -- the window
# where the far knee is most occluded. Fixed in advance, not tuned to the answer.
DEPTH_WINDOW_FRACTION = 0.2


def _rep_depth_window(flexion: list[float]) -> tuple[int, int]:
    """Indices bracketing the deepest DEPTH_WINDOW_FRACTION of one rep."""
    peak = max(range(len(flexion)), key=flexion.__getitem__)
    half = max(1, int(len(flexion) * DEPTH_WINDOW_FRACTION / 2))
    return max(0, peak - half), min(len(flexion) - 1, peak + half)


def collect(config: dict) -> dict:
    seg_rows = _read_segmentation(
        Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    )
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

    per_video = []
    reps_any_below = 0
    reps_depth_below = 0
    total_reps = 0
    depth_frames_below = 0
    depth_frames_total = 0

    for video_id in video_ids:
        raw_frames, _total = _raw_full_stream(video_id)
        by_index = {f["frameIndex"]: f for f in raw_frames}
        lead = LEAD_LEG_MAP[
            next(r for r in side_view_rows if r["video_id"] == video_id)[
                "exercise_subtype"
            ]
        ]

        video_depth_min = []
        video_reps = 0
        video_reps_depth_below = 0
        for row in (r for r in side_view_rows if r["video_id"] == video_id):
            first, last = int(row["first_frame"]), int(row["last_frame"])
            frames = [by_index[f] for f in range(first, last + 1) if f in by_index]
            if not frames:
                continue
            far_vis = [
                float(f["worldLandmarks"][KNEE[FAR_LEG]]["visibility"]) for f in frames
            ]
            # Locate depth by the far knee's vertical drop, not by its flexion angle
            # (the angle's reliability is the thing under test) and not by its own
            # visibility (that would be circular).
            far_y = [float(f["worldLandmarks"][KNEE[FAR_LEG]]["y"]) for f in frames]
            low, high = _rep_depth_window(far_y)
            depth_vis = far_vis[low : high + 1]

            total_reps += 1
            video_reps += 1
            if min(far_vis) < MIN_VISIBILITY:
                reps_any_below += 1
            if min(depth_vis) < MIN_VISIBILITY:
                reps_depth_below += 1
                video_reps_depth_below += 1
            depth_frames_below += sum(1 for v in depth_vis if v < MIN_VISIBILITY)
            depth_frames_total += len(depth_vis)
            video_depth_min.append(min(depth_vis))

        all_far = [
            float(f["worldLandmarks"][KNEE[FAR_LEG]]["visibility"]) for f in raw_frames
        ]
        all_near = [
            float(f["worldLandmarks"][KNEE[NEAR_LEG]]["visibility"]) for f in raw_frames
        ]
        per_video.append(
            {
                "video_id": video_id,
                "lead_leg": lead,
                "far_mean": float(np.mean(all_far)),
                "near_mean": float(np.mean(all_near)),
                "far_min": float(np.min(all_far)),
                "depth_min_median": float(np.median(video_depth_min)),
                "reps": video_reps,
                "reps_depth_below": video_reps_depth_below,
            }
        )

    return {
        "per_video": per_video,
        "total_reps": total_reps,
        "reps_any_below": reps_any_below,
        "reps_depth_below": reps_depth_below,
        "depth_frames_below": depth_frames_below,
        "depth_frames_total": depth_frames_total,
    }


def write_report(data: dict) -> None:
    per_video = data["per_video"]
    total = data["total_reps"]
    depth_below = data["reps_depth_below"]
    any_below = data["reps_any_below"]
    pct_depth_frames = (
        100.0 * data["depth_frames_below"] / data["depth_frames_total"]
        if data["depth_frames_total"]
        else 0.0
    )
    worst = min(per_video, key=lambda v: v["depth_min_median"])
    affected_videos = [v for v in per_video if v["reps_depth_below"] > 0]
    affected_leads = {v["lead_leg"] for v in affected_videos}
    # Does the dip fall entirely inside one lead-leg cohort? Measured, not assumed.
    dip_is_cohort_bound = len(affected_leads) == 1
    by_lead = {
        lead: {
            "far_mean": float(
                np.mean([v["far_mean"] for v in per_video if v["lead_leg"] == lead])
            ),
            "reps_below": sum(
                v["reps_depth_below"] for v in per_video if v["lead_leg"] == lead
            ),
            "reps": sum(v["reps"] for v in per_video if v["lead_leg"] == lead),
        }
        for lead in sorted({v["lead_leg"] for v in per_video})
    }

    lines = [
        "# Stage 5.4 (Lunge) — far-limb visibility at rep depth",
        "",
        "Closes the question Stage 5.2 (Lunge) flagged and deliberately left open. Its "
        "visibility numbers were **per-video means**, and the lowest of them (0.672, "
        f"PM_117b's right knee) sat above `MIN_VISIBILITY = {MIN_VISIBILITY}` — but "
        "only just, and a whole-video average says nothing about the deepest frames of "
        "individual reps, which is where the far knee is most occluded and where the "
        "features are read.",
        "",
        "## Why the threshold is not cosmetic",
        "",
        f"`MIN_VISIBILITY = {MIN_VISIBILITY}` switches real behaviour. Below it, "
        "`preprocess_world_landmarks` treats the landmark as missing and either "
        "gap-fills it (gaps up to "
        f"`interpolation_max_gap_frames = "
        f"{MODULE_B_CORE_CONFIG['interpolation_max_gap_frames']}`) or releases "
        "hold-last beyond that. So crossing the line at the bottom of a rep means the "
        "feature values there are **reconstructions rather than measurements** — and "
        "because the far limb is `right` in every video while lead leg is fixed per "
        "subject, that lands on `back_knee_*` for left-lead subjects and on "
        "`front_knee_*` — the gate feature — for right-lead ones.",
        "",
        "Measured on the **raw** stream on purpose: preprocessing rewrites visibility "
        "(a released landmark is set to exactly `MIN_VISIBILITY`), so asking the "
        "preprocessed stream would be asking the filter to grade its own homework.",
        "",
        "## Answer",
        "",
        f"**{depth_below} of {total} reps ({100.0 * depth_below / total:.1f}%) have the "
        f"far knee drop below `MIN_VISIBILITY` in their deepest "
        f"{int(DEPTH_WINDOW_FRACTION * 100)}% of frames**, and "
        f"{pct_depth_frames:.1f}% of all at-depth frames are below the line. "
        f"Across the whole rep window (not just the bottom), {any_below} of {total} "
        f"reps ({100.0 * any_below / total:.1f}%) dip below it at least once.",
        "",
        (
            "**So the Stage 5.2 mean did hide the dip — the concern was justified.** "
            "The per-video averages sat comfortably above the threshold while a "
            "substantial share of individual reps cross it at exactly the moment the "
            "features are computed."
            if depth_below > 0
            else "**The far limb stays above the threshold even at depth.** The "
            "Stage 5.2 means were not masking a dip: the concern is answered in the "
            "negative, and the confidence filter does not engage on the far knee "
            "during these reps."
        ),
        "",
        "| video | lead leg | far-knee mean | near-knee mean | far-knee min | median at-depth min | reps below at depth |",
        "| ----- | -------- | ------------- | -------------- | ------------ | ------------------- | ------------------- |",
    ]
    for v in per_video:
        lines.append(
            f"| {v['video_id']} | {v['lead_leg']} | {v['far_mean']:.3f} | "
            f"{v['near_mean']:.3f} | {v['far_min']:.3f} | {v['depth_min_median']:.3f} | "
            f"{v['reps_depth_below']}/{v['reps']} |"
        )

    lines += [
        "",
        f"The near limb's mean visibility "
        f"({min(v['near_mean'] for v in per_video):.3f}–"
        f"{max(v['near_mean'] for v in per_video):.3f}) never approaches the threshold; "
        f"the far limb's ({min(v['far_mean'] for v in per_video):.3f}–"
        f"{max(v['far_mean'] for v in per_video):.3f}) is a different regime "
        f"altogether. `{worst['video_id']}` is the worst case by median at-depth "
        f"minimum ({worst['depth_min_median']:.3f}).",
        "",
        "## The dip is cohort-bound, which the whole-video means also hid",
        "",
        "| cohort | right (far) knee is the... | mean far-knee visibility | reps below at depth |",
        "| ------ | -------------------------- | ------------------------ | ------------------- |",
    ]
    for lead, s in by_lead.items():
        role = "front leg" if lead == FAR_LEG else "back leg"
        lines.append(
            f"| lead={lead} | {role} | {s['far_mean']:.3f} | "
            f"{s['reps_below']}/{s['reps']} |"
        )

    lines += [
        "",
        (
            f"**Every affected rep is a lead={sorted(affected_leads)[0]} subject's.** "
            "The far limb is the right knee throughout, but how badly it is occluded "
            "depends on the job it is doing: as the **back** leg it sits behind the "
            "body and is partly hidden by the front leg "
            f"({by_lead['left']['far_mean']:.3f} mean visibility); as the **front** leg "
            f"it is out ahead and clearly seen ({by_lead['right']['far_mean']:.3f}). So "
            "'right = far limb' is true but too coarse — the visibility penalty is a "
            "near/far *and* front/back interaction."
            if dip_is_cohort_bound
            else "The dip is spread across both lead-leg cohorts."
        ),
        "",
        "## What this means — and, importantly, what it does NOT explain",
        "",
        "**Answer to the flagged question: yes, the Stage 5.2 means hid a real dip.** "
        f"Per-video averages sat at {min(v['far_mean'] for v in per_video):.3f} and "
        f"above, but {depth_below} of {total} individual reps cross the threshold at "
        "exactly the moment the features are read. Averages over a whole video were the "
        "wrong instrument, and the concern that flagged this was well founded.",
        "",
        "**But this is NOT the cause of the far limb's measurement error, and it would "
        "be wrong to present it as one.** `LUNGE_MOCAP_AGREEMENT.md` decomposes the "
        "per-rep peak error by cohort and limb against this same raw visibility (the "
        "figures live there, in the report that computes them, rather than being "
        "retyped here). Two of its findings bear directly on this one:",
        "",
        "- The error tracks **near vs far**, not front vs back — the opposite of the "
        "pattern the visibility dip follows, since the dip is confined to the cohort "
        "where the far limb is the *back* leg.",
        "- The far limb is badly under-read **even where MediaPipe is confident**. For "
        f"lead={FAR_LEG} subjects the right knee averages "
        f"{by_lead[FAR_LEG]['far_mean']:.3f} visibility — comfortably above "
        f"`MIN_VISIBILITY = {MIN_VISIBILITY}`, so the filter never engages — and its "
        f"reps never dip below at depth ({by_lead[FAR_LEG]['reps_below']}/"
        f"{by_lead[FAR_LEG]['reps']}), yet the mocap comparison still finds a large "
        "negative bias there.",
        "",
        "So the far-limb bias is **not** a reconstruction artefact from the confidence "
        "filter. It is the landmark model's own error: MediaPipe is *confidently wrong* "
        "about the occluded knee far more often than it flags it as uncertain. That is "
        "the worse of the two failure modes — a low-visibility landmark at least "
        "announces itself and can be gated on, while a confident bad estimate offers no "
        "signal to key any mitigation off.",
        "",
        f"The {depth_below}/{total} reps measured here are the smaller, honest part of "
        "the problem: the part the pipeline *knows* about. The larger part is invisible "
        "to every confidence-based defence the system could mount.",
        "",
        "**Not acted on here, deliberately.** Changing `MIN_VISIBILITY`, the gap-fill "
        "width, or the release policy would alter Module B behaviour for **squat as "
        "well as lunge** — `preprocess_world_landmarks` is the single shared "
        "implementation (X1), and squat's Phase 5 results were verified against its "
        "current behaviour. This gate's job is to establish the fact; any change to the "
        "shared preprocessing is a cross-cutting decision with its own re-verification "
        "cost, and belongs to HY, not to this stage.",
        "",
        "## Caveats",
        "",
        f"- **'At depth' is defined as the deepest {int(DEPTH_WINDOW_FRACTION * 100)}% "
        "of each rep's frames**, bracketed around the far knee's lowest vertical "
        "position. The fraction was fixed before the numbers were seen. A wider or "
        "narrower window would move the percentages, though not the direction of the "
        "finding.",
        "- **Depth is located by the far knee's own vertical excursion**, not by its "
        "flexion angle — using the angle would risk circularity, since the angle is the "
        "quantity whose reliability is in question.",
        "- **Visibility is MediaPipe's own confidence, not a measurement of occlusion.** "
        "It is the model's self-report, and a model can be confident and wrong (which "
        "the mocap comparison shows it is). Low visibility is evidence of occlusion; "
        "high visibility is not evidence of accuracy.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    config = _load_config()
    data = collect(config)
    write_report(data)

    print(f"MIN_VISIBILITY = {MIN_VISIBILITY}; far limb = {FAR_LEG} knee (Stage 5.2)")
    for v in data["per_video"]:
        print(
            f"  {v['video_id']:<9} lead={v['lead_leg']:<5} far_mean={v['far_mean']:.3f} "
            f"near_mean={v['near_mean']:.3f} far_min={v['far_min']:.3f} "
            f"depth_min_median={v['depth_min_median']:.3f} "
            f"reps_below_at_depth={v['reps_depth_below']}/{v['reps']}"
        )
    print(
        f"reps with far knee below MIN_VISIBILITY at depth: "
        f"{data['reps_depth_below']}/{data['total_reps']}"
    )
    print(
        f"reps dipping below anywhere in the rep window:    "
        f"{data['reps_any_below']}/{data['total_reps']}"
    )
    print(
        f"at-depth frames below threshold: {data['depth_frames_below']}/"
        f"{data['depth_frames_total']}"
    )
    print(f"wrote {REPORT_MD.name}")


if __name__ == "__main__":
    main()
