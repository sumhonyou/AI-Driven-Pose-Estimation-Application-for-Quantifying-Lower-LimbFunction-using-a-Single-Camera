# Module B Research Brief (for the research agent)

**Purpose:** Gather the external, evidence-based information needed to build Module B
(Rehabilitation Grading) — the rule sub-scores, the ML model, and the clinical thresholds.
The coding agent will turn your answers into code/config, so answers must be **specific,
cited, and actionable** (numbers, joint names, thresholds, dataset URLs, licenses), not general.

## Fixed decisions (do NOT re-open these — build the research around them)

1. **Data source:** Public datasets ONLY. No self-collected data.
2. **Selection order:** DATASET-AVAILABILITY FIRST. Shortlist exercises that already have a
   suitable public dataset; the user picks the exercise from your shortlist.
3. **Grading scheme:** Good / Fair / Poor (3-class). Dataset labels must support 3 honest
   levels or a continuous score that can be defensibly split into 3 bands.
4. **Scope:** TWO exercises — ideally ONE knee + ONE ankle. If a suitable ankle dataset does
   not exist, say so explicitly and recommend a second knee exercise as fallback.

## Hard filters (a dataset that fails these is disqualified — state pass/fail for each)

- **F1 — Raw video included** (not skeleton-only). REQUIRED: we re-extract features with our own
  MediaPipe pipeline to eliminate the Kinect/OpenPose → MediaPipe domain gap. If a strong
  dataset is skeleton-only, list it separately and note the joint format so we can assess a
  joint-mapping fallback.
- **F2 — Quality labels with ≥3 levels OR a continuous score** (binary-only is a fallback, not preferred).
- **F3 — Subject IDs provided** (mandatory for leave-one-subject-out / subject-wise split; without
  it, reported accuracy is inflated by leakage).
- **F4 — License usable for an academic FYP and a public demo deployment.**

---

## R1 — Rehab exercise clinical protocol (per chosen exercise, knee + ankle)

- Standard protocol: start position, reps/sets, target tempo/cadence, target ROM in degrees.
- Biomechanical definition of "correct form" (this defines the rule sub-scores).
- Common compensations / faults list → becomes our `error_tags` taxonomy (see R8).
- Recommended camera view for a SINGLE monocular webcam (side vs front) and why.
- **Normative ROM/angle values WITH citations** → become the Good/Fair/Poor thresholds
  (the same way WBLT used McBride et al.'s normative table).
- Safety / contraindication notes for the non-diagnostic disclaimer.

## R2 — Public dataset compatibility (screen against the hard filters)

Screen at least: UI-PRMD, KIMORE, IntelliRehabDS, REHAB24-6, EC3D, and anything else you find.
For each candidate report a table row:

- Contains which of our two target exercises (knee / ankle)?
- F1 raw video? / F2 label type (binary | ordinal | continuous, #classes) / F3 subject IDs? / F4 license.
- Skeleton format & joints (Kinect 25 / OpenPose / MediaPipe 33), 2D vs 3D, frame rate.
- Sample count, subject count, class balance.
- Capture view (frontal Kinect vs our side/front webcam) — note domain mismatch.

Deliver a ranked shortlist of exercise+dataset pairs that pass F1–F4, one knee + one ankle if possible.

## R3 — Label harmonization

- Concrete mapping rule: dataset native labels → Good / Fair / Poor.
- If continuous, the exact cutoff values (with justification).

## R4 — Feature discriminativeness

- Which pose-derived features are shown to separate quality for each exercise
  (knee ROM, angular velocity, tempo/cadence variability, trunk-lean proxy, symmetry index)?
- Definition of the symmetry index for a UNILATERAL vs BILATERAL exercise.
- Normalization reference (which body-segment length to normalize by).

## R5 — ML methodology

- Recommended Extra Trees hyperparameters for pose-tabular features.
- Cross-validation strategy: leave-one-subject-out vs stratified k-fold (recommend one).
- Class-imbalance handling (class weights vs resampling).
- Expected baseline macro-F1 from comparable published work (so we can sanity-check our result).

## R6 — Rep segmentation

- How to detect rep boundaries for each exercise. Is it repetition-based (like our STS FSM
  with hysteresis) or a continuous/hold movement? Give the state-transition cue (angle/position).

## R7 — LLM provider for after-set feedback (Phase 6, lower urgency)

- Compare providers on cost-per-call, latency, data-handling terms, safety-instruction adherence.
- Recommend a default. (Working assumption: Anthropic Claude Haiku — confirm suitability + key/budget.)

## R8 — Error-tag taxonomy

- The clinically-grounded fault list per exercise (feeds `error_tags` and the LLM structured input),
  each with a plain-language user-facing message and a low/medium/high severity suggestion.

---
