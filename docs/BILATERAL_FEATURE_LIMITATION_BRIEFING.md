# Limitation Briefing: Bilateral-Mean ML Features Carry Far-Leg Noise

Self-contained briefing for use when writing Chapter 5 (Conclusion) — specifically the
**Limitations** and **Future Work** sections. This describes one specific, verified
limitation of the squat grading model, distinct from (but related to) the existing
"far-limb occlusion" limitation already documented elsewhere in this project.

---

## The limitation, stated plainly

The Extra Trees classifier's 13 features are computed as **bilateral means** — the
average of the left and right leg's value, for nearly every angle-based feature
(`knee_flex_peak_deg`, `hip_flex_peak_deg`, `ankle_df_proxy_deg`, etc.). In a side-view
squat, one leg (near the camera) is tracked reliably; the other (far leg) is partially
occluded and tracked with lower confidence (visibility 0.59–0.78 vs. 0.95–0.99 for the
near leg). When the far leg is occluded for longer than the gap-fill window, the system
does not freeze it — it releases it back to a "low but valid" state so it keeps being
tracked (and smoothed) rather than frozen. That means the far leg's **noisier, less
certain** position estimate is averaged directly into the same features the model
trains and predicts on.

## Why this matters, with the exact evidence

- The system's own motion-capture validation check (comparing the pipeline's bilateral
  `knee_flex_peak_deg` against OptiTrack ground truth) found a systematic bias of
  **−11.96°** with 95% limits of agreement of **[−21.00°, −2.94°]** — an ~18°-wide
  spread. Some portion of that spread is plausibly attributable to far-leg noise
  entering the bilateral mean, though this has not been isolated from other error
  sources (e.g. definitional differences between MediaPipe's and OptiTrack's joint
  centres).
- The correlation with true motion (Pearson r = 0.956) shows the bilateral mean still
  _tracks the shape of the movement_ well — this is not a broken feature, only a
  noisier one than a near-leg-only version might be.
- **Direct in-project precedent that this class of fix works:** a structurally
  identical problem was found and fixed for the heel-rise fault gate (a separate,
  rule-based signal, not one of the 13 trained features) — switching it from a
  bilateral average to a near-leg-only calculation (selecting the camera-side leg by
  visibility) measurably improved its specificity (fewer false alarms on good-form
  reps). This is real evidence, from within this same system, that near-leg-only
  computation reduces far-leg-noise-driven error — but it was applied only to that one
  rule, not to the 13 trained ML features.

## Why the same fix was not applied to the trained model

1. The bilateral mean was originally adopted for a **different** reason than noise —
   **leg-identity robustness**. Early in development, it was not reliably possible to
   confirm which of MediaPipe's "left"/"right" labels corresponded to the true near/far
   leg (a left-right difference signal correlated with the equivalent mocap signal at
   only r ≈ −0.05 — essentially no relationship). Averaging both legs sidesteps that
   identity problem entirely, since it doesn't matter which leg is which.
2. The 13-feature schema is **frozen** for the shipped model. Changing any of the
   features that feed the classifier would require retraining and recalibrating the
   whole model — a substantially larger and riskier change than adjusting one
   standalone rule, and was out of scope given the project timeline.
3. The bilateral mean was not shown to fail — it still correlates strongly with ground
   truth (r = 0.956) — so it is a **quantified trade-off**, not a defect discovered too
   late to matter.

## What this is NOT

- Not evidence the model is broken or unusable — it is a known, bounded source of
  measurement noise in an already-modest dataset (98 reps, 9 subjects).
- Not the same limitation as "far-limb occlusion causes asymmetry to be untaggable" —
  that is about the _symmetry feature/tag specifically_ being unmeasurable; this
  limitation is about noise entering the _core angle features_ (depth, hip flexion,
  ankle proxy) that the classifier is actually trained on.

---

## Suggested text for Chapter 5

### For §5.3 Limitations (place under the dataset/model-limitations subsection,

alongside the existing far-limb-occlusion and small-sample-size points)

> The trained classifier's features are computed as bilateral means across both legs.
> In a side-view squat, the far leg is tracked with lower confidence (visibility
> 0.59–0.78) than the near leg (0.95–0.99), and this noisier estimate is averaged
> directly into the same angle-based features (e.g. knee flexion, hip flexion, ankle
> dorsiflexion proxy) the classifier is trained and predicted on. The system's own
> motion-capture validation shows this bilateral measure still tracks true movement
> closely (r = 0.956) but with a wide margin of error (95% limits of agreement
> [−21.00°, −2.94°]), part of which is plausibly attributable to far-leg noise. This
> is a quantified, bounded limitation rather than a discovered defect: the bilateral
> design was originally chosen to avoid a separate leg-identity ambiguity problem, and
> the trade-off was accepted rather than corrected because doing so would require
> retraining and recalibrating the classifier under a changed feature schema.

### For §5.4 Future Work (pair directly with the limitation above)

> Re-deriving the feature set with near-leg-only computation (selecting the
> camera-side leg per rep by visibility, as already implemented for this system's
> heel-rise fault gate) and re-running the full training, calibration, and validation
> pipeline against it. This system already has direct internal evidence that this
> class of fix reduces far-leg-noise-driven error — the same near-leg-only redesign
> measurably improved the heel-rise gate's specificity — but it has not yet been
> applied to the trained classifier's feature schema, since doing so requires a full
> retrain rather than a standalone rule adjustment.

---

## One instruction for whoever writes this into the final report

Do not present this as something that was missed or overlooked. State it as a
deliberate, reasoned trade-off (leg-identity robustness over noise minimisation),
support it with the exact numbers above, and connect it explicitly to the heel-rise
precedent — that connection is what turns this from "a flaw I found" into "a
trade-off I understood, with in-project evidence, and scoped correctly as future
work."
