# Module B Limitations — Deliberately Not Measured

**Scope:** Phase 6 onward
**Sources of truth:** `task.md` Phase 6 Stage 6.1, Phase 5 measurement findings
(`ml/reports/PHASE5_CHAPTER_DRAFT.md`), and the taxonomy in
`backend/app/module_b/squat/tags.py`.

An examiner reads an omission as rigour or as oversight depending entirely on whether it
was named. Each entry below is a fault the original Phase 6 tag table proposed, deliberately
**excluded** because a single monocular side-view camera cannot measure it reliably. This is
the same principle that already dropped knee valgus (Module B Decision Record §3).

---

## Table of Contents

- [1. Knee valgus / frontal-plane faults](#1-knee-valgus-frontal-plane-faults)
- [2. asymmetry (left/right imbalance) — dropped from the tag taxonomy](#2-asymmetry-leftright-imbalance-dropped-from-the-tag-taxonomy)
- [3. feet_too_wide (stance width) — dropped from the tag taxonomy](#3-feettoowide-stance-width-dropped-from-the-tag-taxonomy)
- [Tags that ARE measured (for contrast)](#tags-that-are-measured-for-contrast)

---

## 1. Knee valgus / frontal-plane faults

- **Not measured.** Ill-posed from a single sagittal (side) view. Dropped from features,
  rules, tags, and evaluation since Phase 4.
- **Why:** a side camera resolves sagittal knee/hip/ankle motion but cannot also provide a
  reliable frontal-plane valgus measurement. See Module B Decision Record §3.

## 2. `asymmetry` (left/right imbalance) — dropped from the tag taxonomy

- **Not measured.** The original table proposed an `asymmetry` tag from `symmetry_index_pct`.
  Excluded at Stage 6.1.
- **Why:** from one side view the far limb is occluded (Phase 5: far-knee visibility
  0.59–0.78 vs near-side 0.95–0.99), so a left-vs-right comparison is not observable. The
  feature was validated against OptiTrack mocap and did not track true inter-leg difference
  (leg-difference vs mocap r ≈ −0.05) — it "isn't measuring what it claims." The trained
  model also ranked it near-last (11/13, importance ≈ 0.040). A tag built on it would report
  an imbalance the camera cannot actually see.
- **What would reverse it:** a validated multi-view or depth-aware capture design with
  compatible training data — a new architecture decision, not a threshold change.

## 3. `feet_too_wide` (stance width) — dropped from the tag taxonomy

- **Not measured.** The original table proposed a `feet_too_wide` tag from `stance_width_norm`.
  Excluded at Stage 6.1.
- **Why:** in a profile view the feet are separated mainly along the camera's depth axis —
  exactly the axis a single camera resolves worst. Empirically the feature is near-useless
  for the Good/Poor split (in-sample AUC 0.37, i.e. below chance) and its direction inverts
  on the external EC3D set (AUC 0.66 the other way). A stance-width fault flagged from a side
  view would fire on measurement noise, not on real form.
- **What would reverse it:** a frontal or depth-aware capture path with compatible labels.

## Tags that ARE measured (for contrast)

The five retained squat tags are each observable from one side view: `insufficient_depth`,
`excessive_forward_lean`, `heel_lift` (the Stage 5.12 fault gates, sagittal-plane angles /
in-plane heel rise), `inconsistent_tempo` (within-set timing, needs no depth), and the
system capture/confidence tags. See `backend/app/module_b/squat/tags.py`.
