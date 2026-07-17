# Stage 5.4 (Lunge) — far-limb visibility at rep depth

Closes the question Stage 5.2 (Lunge) flagged and deliberately left open. Its visibility numbers were **per-video means**, and the lowest of them (0.672, PM_117b's right knee) sat above `MIN_VISIBILITY = 0.6` — but only just, and a whole-video average says nothing about the deepest frames of individual reps, which is where the far knee is most occluded and where the features are read.

## Why the threshold is not cosmetic

`MIN_VISIBILITY = 0.6` switches real behaviour. Below it, `preprocess_world_landmarks` treats the landmark as missing and either gap-fills it (gaps up to `interpolation_max_gap_frames = 5`) or releases hold-last beyond that. So crossing the line at the bottom of a rep means the feature values there are **reconstructions rather than measurements** — and because the far limb is `right` in every video while lead leg is fixed per subject, that lands on `back_knee_*` for left-lead subjects and on `front_knee_*` — the gate feature — for right-lead ones.

Measured on the **raw** stream on purpose: preprocessing rewrites visibility (a released landmark is set to exactly `MIN_VISIBILITY`), so asking the preprocessed stream would be asking the filter to grade its own homework.

## Answer

**10 of 88 reps (11.4%) have the far knee drop below `MIN_VISIBILITY` in their deepest 20% of frames**, and 5.2% of all at-depth frames are below the line. Across the whole rep window (not just the bottom), 11 of 88 reps (12.5%) dip below it at least once.

**So the Stage 5.2 mean did hide the dip — the concern was justified.** The per-video averages sat comfortably above the threshold while a substantial share of individual reps cross it at exactly the moment the features are computed.

| video | lead leg | far-knee mean | near-knee mean | far-knee min | median at-depth min | reps below at depth |
| ----- | -------- | ------------- | -------------- | ------------ | ------------------- | ------------------- |
| PM_021 | left | 0.776 | 0.974 | 0.239 | 0.716 | 2/10 |
| PM_028 | right | 0.952 | 0.994 | 0.308 | 0.876 | 0/11 |
| PM_037 | right | 0.931 | 0.989 | 0.283 | 0.969 | 0/10 |
| PM_042 | right | 0.918 | 0.988 | 0.190 | 0.896 | 0/13 |
| PM_104 | left | 0.764 | 0.979 | 0.241 | 0.617 | 4/10 |
| PM_112 | right | 0.958 | 0.993 | 0.253 | 0.931 | 0/12 |
| PM_117a | left | 0.672 | 0.965 | 0.201 | 0.636 | 2/9 |
| PM_117b | left | 0.652 | 0.986 | 0.413 | 0.560 | 2/3 |
| PM_125 | left | 0.713 | 0.979 | 0.175 | 0.703 | 0/10 |

The near limb's mean visibility (0.965–0.994) never approaches the threshold; the far limb's (0.652–0.958) is a different regime altogether. `PM_117b` is the worst case by median at-depth minimum (0.560).

## The dip is cohort-bound, which the whole-video means also hid

| cohort | right (far) knee is the... | mean far-knee visibility | reps below at depth |
| ------ | -------------------------- | ------------------------ | ------------------- |
| lead=left | back leg | 0.715 | 10/42 |
| lead=right | front leg | 0.940 | 0/46 |

**Every affected rep is a lead=left subject's.** The far limb is the right knee throughout, but how badly it is occluded depends on the job it is doing: as the **back** leg it sits behind the body and is partly hidden by the front leg (0.715 mean visibility); as the **front** leg it is out ahead and clearly seen (0.940). So 'right = far limb' is true but too coarse — the visibility penalty is a near/far *and* front/back interaction.

## What this means — and, importantly, what it does NOT explain

**Answer to the flagged question: yes, the Stage 5.2 means hid a real dip.** Per-video averages sat at 0.652 and above, but 10 of 88 individual reps cross the threshold at exactly the moment the features are read. Averages over a whole video were the wrong instrument, and the concern that flagged this was well founded.

**But this is NOT the cause of the far limb's measurement error, and it would be wrong to present it as one.** `LUNGE_MOCAP_AGREEMENT.md` decomposes the per-rep peak error by cohort and limb against this same raw visibility (the figures live there, in the report that computes them, rather than being retyped here). Two of its findings bear directly on this one:

- The error tracks **near vs far**, not front vs back — the opposite of the pattern the visibility dip follows, since the dip is confined to the cohort where the far limb is the *back* leg.
- The far limb is badly under-read **even where MediaPipe is confident**. For lead=right subjects the right knee averages 0.940 visibility — comfortably above `MIN_VISIBILITY = 0.6`, so the filter never engages — and its reps never dip below at depth (0/46), yet the mocap comparison still finds a large negative bias there.

So the far-limb bias is **not** a reconstruction artefact from the confidence filter. It is the landmark model's own error: MediaPipe is *confidently wrong* about the occluded knee far more often than it flags it as uncertain. That is the worse of the two failure modes — a low-visibility landmark at least announces itself and can be gated on, while a confident bad estimate offers no signal to key any mitigation off.

The 10/88 reps measured here are the smaller, honest part of the problem: the part the pipeline *knows* about. The larger part is invisible to every confidence-based defence the system could mount.

**Not acted on here, deliberately.** Changing `MIN_VISIBILITY`, the gap-fill width, or the release policy would alter Module B behaviour for **squat as well as lunge** — `preprocess_world_landmarks` is the single shared implementation (X1), and squat's Phase 5 results were verified against its current behaviour. This gate's job is to establish the fact; any change to the shared preprocessing is a cross-cutting decision with its own re-verification cost, and belongs to HY, not to this stage.

## Caveats

- **'At depth' is defined as the deepest 20% of each rep's frames**, bracketed around the far knee's lowest vertical position. The fraction was fixed before the numbers were seen. A wider or narrower window would move the percentages, though not the direction of the finding.
- **Depth is located by the far knee's own vertical excursion**, not by its flexion angle — using the angle would risk circularity, since the angle is the quantity whose reliability is in question.
- **Visibility is MediaPipe's own confidence, not a measurement of occlusion.** It is the model's self-report, and a model can be confident and wrong (which the mocap comparison shows it is). Low visibility is evidence of occlusion; high visibility is not evidence of accuracy.
