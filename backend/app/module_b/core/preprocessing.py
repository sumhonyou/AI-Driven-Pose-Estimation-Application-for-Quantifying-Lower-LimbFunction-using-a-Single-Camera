"""Shared world-landmark preprocessing for Module B exercises.

Confidence filter -> gap fill -> One Euro, in that order (X3). This module is
the single importable implementation both the live backend (core/router.py)
and ml/'s offline extractor call (X1) — do not fork it into a second copy for
offline use, or the two pipelines silently drift apart.

`LandmarkSmoother` (app.module_a.core.smoothing) already reused, not forked;
it only hold-lasts a landmark below MIN_VISIBILITY, it does not interpolate.
The gap fill below is genuinely new logic that fills short gaps (up to
MODULE_B_CORE_CONFIG["interpolation_max_gap_frames"]) before the One Euro
pass runs.

Beyond that window, hold-last is deliberately *released* (see
`_release_persistent_occlusions`) rather than left to freeze a landmark for
the rest of the capture. LandmarkSmoother's hold-last is documented for a
"brief occlusion"; a single side-view camera violates that assumption
structurally — the far leg sits below MIN_VISIBILITY for most of a squat
(Stage 5.3 measured mean right-knee visibility 0.59-0.78 vs 0.95-0.99 left,
across all 9 REHAB24-6 subjects), so hold-last would pin the far knee at its
standing angle for entire reps. That is worse than the raw estimate, which
still tracks a plausible trajectory (measured peak 99.9 deg on a rep where
the near knee read 77.9 deg) — it is low-*confidence*, not wrong. Freezing it
turns "uncertain but usable" into "confidently stale", halving the bilateral
mean knee flexion that segmentation and features both depend on.

Scoped to Module B on purpose: LandmarkSmoother itself is untouched, so
Module A's (STS/SLS/WBLT) verified behavior is byte-identical.
"""

from __future__ import annotations

from app.module_a.core.config import MIN_VISIBILITY
from app.module_a.core.smoothing import LandmarkSmoother
from app.module_b.core.config import MODULE_B_CORE_CONFIG


def preprocess_world_landmarks(frames: list[dict]) -> list[dict]:
    """Run the full confidence-filter -> gap-fill -> One-Euro pipeline.

    `frames` must be the entire chronologically ordered capture (a whole
    session/set), not a single rep's window: OneEuroFilter is stateful, so
    windowing before calling this would reset its history at every rep
    boundary and diverge from what the live capture actually produced.
    """
    if not frames:
        return []

    max_gap_frames = MODULE_B_CORE_CONFIG["interpolation_max_gap_frames"]
    filled = _fill_gaps(frames, max_gap_frames)
    _release_persistent_occlusions(filled, max_gap_frames)

    num_landmarks = len(filled[0]["worldLandmarks"])
    smoother = LandmarkSmoother(num_landmarks=num_landmarks)
    return [
        {
            **frame,
            "worldLandmarks": smoother.smooth_frame(
                float(frame["timestampMs"]) / 1000.0, frame["worldLandmarks"]
            ),
        }
        for frame in filled
    ]


def _release_persistent_occlusions(filled: list[dict], max_gap_frames: int) -> None:
    """Stop hold-last from freezing a landmark that is occluded for a long run.

    Runs of `max_gap_frames` or fewer are left alone: those are the brief
    occlusions LandmarkSmoother's hold-last is designed for (and short runs with
    an anchor either side were already interpolated by `_fill_gaps`). A *longer*
    run is released — its visibility is raised to exactly MIN_VISIBILITY so the
    One Euro pass smooths the landmark's own raw estimate instead of hold-lasting
    a stale value for the rest of the run. Same visibility-bump idiom
    `_interpolate_gap` already uses, and for the same reason: it is the one lever
    that steers LandmarkSmoother's hold-last branch without forking it.

    Mutates `filled` in place. Only the smoother reads this visibility — the
    capture-quality metric is computed on the raw frames upstream (router.py),
    so raising it here cannot flatter a quality score.
    """
    num_landmarks = len(filled[0]["worldLandmarks"])
    for landmark_index in range(num_landmarks):
        run_start = None
        for i, frame in enumerate(filled):
            is_low = (
                frame["worldLandmarks"][landmark_index]["visibility"] < MIN_VISIBILITY
            )
            if is_low and run_start is None:
                run_start = i
            elif not is_low and run_start is not None:
                _release_run(filled, landmark_index, run_start, i, max_gap_frames)
                run_start = None
        if run_start is not None:
            # A run reaching the end of the stream has no trailing anchor, but the
            # same reasoning applies: a long freeze is worse than the raw estimate.
            _release_run(filled, landmark_index, run_start, len(filled), max_gap_frames)


def _release_run(
    filled: list[dict],
    landmark_index: int,
    start: int,
    end: int,
    max_gap_frames: int,
) -> None:
    if (end - start) <= max_gap_frames:
        return
    for i in range(start, end):
        filled[i]["worldLandmarks"][landmark_index]["visibility"] = MIN_VISIBILITY


def _fill_gaps(frames: list[dict], max_gap_frames: int) -> list[dict]:
    """Linearly interpolate runs of low-visibility frames up to `max_gap_frames` long.

    Confidence filter: a landmark below MIN_VISIBILITY is treated as missing.
    Gap fill: a missing run with a valid frame on both sides, no longer than
    `max_gap_frames`, is interpolated between those two anchors (weighted by
    real elapsed time, since frame spacing is not guaranteed uniform). A run
    with no anchor on one side (leading/trailing gap) or longer than the max
    is left untouched — LandmarkSmoother's own hold-last covers it downstream.
    """
    num_landmarks = len(frames[0]["worldLandmarks"])
    filled = [
        {**frame, "worldLandmarks": [dict(point) for point in frame["worldLandmarks"]]}
        for frame in frames
    ]
    timestamps = [frame["timestampMs"] for frame in frames]

    for landmark_index in range(num_landmarks):
        gap_start = None
        for i, frame in enumerate(filled):
            is_low = (
                frame["worldLandmarks"][landmark_index]["visibility"] < MIN_VISIBILITY
            )
            if is_low and gap_start is None:
                gap_start = i
            elif not is_low and gap_start is not None:
                _interpolate_gap(
                    filled, timestamps, landmark_index, gap_start, i, max_gap_frames
                )
                gap_start = None
        # A gap reaching the end of the stream has no trailing anchor —
        # left for LandmarkSmoother's hold-last, same as a leading gap.

    return filled


def _interpolate_gap(
    filled: list[dict],
    timestamps: list[float],
    landmark_index: int,
    gap_start: int,
    gap_end: int,
    max_gap_frames: int,
) -> None:
    before_index = gap_start - 1
    if before_index < 0 or (gap_end - gap_start) > max_gap_frames:
        return

    before = filled[before_index]["worldLandmarks"][landmark_index]
    after = filled[gap_end]["worldLandmarks"][landmark_index]
    t_before, t_after = timestamps[before_index], timestamps[gap_end]
    span = t_after - t_before

    for i in range(gap_start, gap_end):
        weight = (timestamps[i] - t_before) / span if span > 0 else 0.0
        point = filled[i]["worldLandmarks"][landmark_index]
        point["x"] = before["x"] + (after["x"] - before["x"]) * weight
        point["y"] = before["y"] + (after["y"] - before["y"]) * weight
        point["z"] = before["z"] + (after["z"] - before["z"]) * weight
        # Bumped to exactly the threshold so the One-Euro pass treats this
        # interpolated point as confident, instead of its own hold-last
        # discarding it in favor of a stale cached value.
        point["visibility"] = MIN_VISIBILITY
