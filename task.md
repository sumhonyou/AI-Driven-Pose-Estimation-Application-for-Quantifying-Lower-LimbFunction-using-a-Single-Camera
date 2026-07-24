# FYP Development Tasks

**Project:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera  
**Status:** ⚠️⚠️⚠️ **Leg Lunge (Phase 4 + Phase 5B, the entire Module B lunge exercise) was REMOVED from the product on 2026-07-19 (HY's decision).** All lunge backend/frontend/ML source code has been deleted; the registry no longer registers it and its API endpoints 404. Everything below about Phase 4 (Lunge)/Phase 5B in this Status line and in the Phase 5B section further down is **historical record only** — see the removal banner at the top of the Phase 5B section for the full detail. Phases 0-3E complete (full-stack skeleton, camera/MediaPipe, Module A: STS/SLS/WBLT all verified live) · Phase 5 (squat ML) Stages 5.0-5.9 complete — trained, calibrated, LOSO-evaluated Extra Trees squat model exported and wired into the real backend, verified live end-to-end (2026-07-16); EC3D external validation run (2026-07-17) and returned a **documented negative result** — see Stage 5.9. **Stage 5.11 (deployed squat output → committed binary Good/Poor) is complete (2026-07-19, HY's call):** the Fair abstention was removed for squat; the decision is a single cut on the fused score (`decision_threshold=8.447974`, `w_rule=0` → the calibrated classifier alone), chosen for **max macro-F1** on the out-of-fold predictions (the aggressive/safety-first point). "Poor" is now reachable — out-of-fold recall **0.077→1.000** — at the cost of flagging **22/72 (31%) of Good reps** as Poor (0 Poor→Good, so no poor-form rep is ever told it is fine). The **model artifact is unchanged** (decision-policy change only, verified byte-identical). Implemented as a per-exercise `band_policy` in `SQUAT_CONFIG` threaded through `fuse_model`/`fuse_scores` (lunge placeholder + Module A keep 3-band); replay corpus regenerated (now spans Good+Poor); "Poor" is displayed as **"Needs Improvement"** in the UI (i18n only, band value stays `"poor"`). New `ml/scripts/tune_squat_binary_band.py`, `ml/reports/SQUAT_EVALUATION_REPORT_2BAND.md` + `confusion_matrix_2band.png`; the old evaluation report renamed to `SQUAT_EVALUATION_REPORT_3BAND.md`; chapter §8.5 + limitation 19. Backend 200/200, tsc clean. **Stage 5.10 (Option B: documented, not built) is next and unblocked.** Phase 5B (lunge) gate is satisfied — **Phase 4 (Lunge) is now fully complete**, Stages 4.1-4.8, verified live end-to-end against the real backend + Postgres (2026-07-17): Module B works for lunge with an announced `stub-0` placeholder model, using the same registry with zero router changes. **Phase 5B Stage 5.0 (Lunge) data audit is complete and its gate is resolved (2026-07-17): HY chose option (a), accept the smaller N** — side-view Ex5 = **88 reps, 39 Good / 49 Poor** (small but balanced, the opposite shape to squat's 72/26); the audit also found that **lead-leg is perfectly confounded with subject** (no subject performs both legs — so `lead_leg` is a LOSO leakage risk and cross-rep Symmetry has no ground truth here), and that **REHAB24-6 is _not_ the only labelled lunge dataset** — EC3D's lunge partition (127 sequences, both faults sagittal, incl. "Knee passes toe") is already on disk. See `[ml/reports/LUNGE_DATA_AUDIT.md](./ml/reports/LUNGE_DATA_AUDIT.md)`. **Stage 5.1 (Lunge)** `ml/` **scaffold is complete (2026-07-17)** — no lunge-specific delta; verified the shared scaffold (editable install, `plotting.py`, `requirements.txt`) extends to the `LungeExercise` plugin live, not assumed. **Stage 5.2 (Lunge) landmark extraction is complete (2026-07-17):** all 9 side-view Ex5 videos extracted, **26,087 frames, 0 missing pose (0.00%)**; the toe-joint delta closed with real data (foot-index landmarks present in 100% of frames); and a real finding — **near/far-limb visibility asymmetry is a camera-orientation artifact, not lead-leg-linked** (left is the higher-visibility limb in all 9 videos regardless of lead leg), milder than squat's but flagged for Stage 5.4 to confirm empirically. **Stage 5.3 (Lunge) is complete (2026-07-17):** `ml/data/lunge_features.csv` built — **88 reps, 39 Good / 49 Poor, 8 subjects, 17 features**, byte-identical across runs (X8); `knee_passes_toe` **kept** as a real measured feature (no ankle proxy needed); `lead_leg` emitted as **metadata only**, outside the feature block (Stage 5.5 must not train on it). Two real findings: a dataset annotation overruns its video by 2 frames on one rep (`PM_117a` rep 9 — clamped, tabled, guard tightened rather than loosened), and — significant — **the lunge rep detector merged reps, 56.8% recall vs squat's 94.9%**, because the bilateral-mean signal never falls back under the 20° exit threshold at the top of each cycle (reps are annotated back-to-back, median 1-frame gap — a set is continuous, not rest-separated). **That is now fixed** (cross-cutting entry, HY chose cycle detection after all three proposed options were measured and rejected as unworkable): front-rep agreement **50/88 → 88/88 (100%)**, overall 173/174, and the feature table is provably unchanged (byte-identical CSV). Backend suite 195/195. **Stage 5.4 (Lunge) is complete and its GATE PASSES (2026-07-17):** `front_knee_flex_peak_deg` separates the classes (**AUC 0.639**, Good 77.2° vs Poor 83.8°, direction holding in 5/7 subjects and in _both_ lead-leg cohorts) — weaker than squat's 0.837 but unambiguous, and **in the same "Poor reps are deeper" direction**, now found independently in two exercises. The `norm_ref` bake-off picked `trunk_length` (variance ratio 1.606 vs 2.118, unanimous across all three normalised features) and the backend config was changed to match; feature table regenerated (md5 → `54f98787…`), X8 determinism re-verified, backend **195/195** after fixing one genuine fixture breakage (a zero-length trunk). **Five significant findings, four of them about method rather than results:** (1) **⚠⚠ squat's pooled-AUC rule does not transfer — pooling inverts the truth for 9 of 17 features**; `back_knee_rom_deg` pools to AUC 0.564 (DROP) while **0/7 subjects agree with the pooled direction** and its within-subject AUC is **0.860** — a textbook Simpson's paradox caused by **one** single-class subject (P3: 0 Good/11 Poor, lowest ROM of anyone), mechanism measured at corr(level, %Poor) = −0.505. Pre-declared verdicts were **deliberately not rewritten**; **Stage 5.5 must train on all 17 features** and treat DROP as advisory (squat's 5.5 already did, so nothing is lost). (2) squat's **CV statistic is invalid** for the signed, zero-crossing `knee_passes_toe_norm` (18/88 reps negative) — a **variance ratio** was used instead, and CV agrees where valid. (3) **⚠⚠ leg identity is SETTLED for lunge, where squat's was not** — squat's leg-difference test failed here too (r=+0.28, mixed signs, and the prediction that lunge's asymmetry would rescue it was **wrong**), so identity was established from **foot position** instead: mocap 9/9 and MediaPipe 9/9 against the annotated lead leg ⇒ **mapping CONFIRMED**. (4) **⚠⚠ occlusion inverts the anatomy** — mocap says right knee deeper in 9/9, MediaPipe says left in 9/9; with identity confirmed this is not a swap but a far-limb under-read of **18.2° vs 2.5° near**, i.e. the artefact is **larger than the signal**; it follows near/far (15.7° gap) not front/back (0.3°), and is **confident** error (0.938 visibility, −15.1° bias) that no confidence threshold can catch. Stage 5.3's deferred far-leg question is answered: **"merely plausible."** (5) **⚠⚠ the gate feature carries an 8.9° cohort-dependent bias** (−6.19° left-lead vs −15.13° right-lead), closing Stage 5.2's open question — the lead limb IS near/far fixed per subject — and upgrading Stage 5.0's leakage warning to a measured fact: the confound is encoded in the feature _values_, so dropping the `lead_leg` column is necessary but **not sufficient**. Stage 5.2's other flagged question also answered: the far limb **does** dip below `MIN_VISIBILITY` at depth in **10/88** reps (the mean masked it), but that is the _smaller_ part of the problem. See `[LUNGE_FEATURE_VALIDITY.md](./ml/reports/LUNGE_FEATURE_VALIDITY.md)`, `[LUNGE_NORM_REF_BAKEOFF.md](./ml/reports/LUNGE_NORM_REF_BAKEOFF.md)`, `[LUNGE_MOCAP_AGREEMENT.md](./ml/reports/LUNGE_MOCAP_AGREEMENT.md)`, `[LUNGE_OCCLUSION_CHECK.md](./ml/reports/LUNGE_OCCLUSION_CHECK.md)`. **Stage 5.5 (Lunge) is complete (2026-07-17) and returned a ⚠⚠⚠ DOCUMENTED NEGATIVE RESULT: the lunge classifier trained the plan's way DOES NOT WORK** — out-of-fold AUC **0.344**, **indistinguishable from chance** under a 200-shuffle permutation test (**p=0.657**, null 0.487±0.085), against squat's 0.832 from the _same code, grid and CV_. It is **not** "predicting backwards" (the null refutes that reading) and **not** a tuning failure (grid is a plateau: 180 combos span 0.077 AUC vs 0.068 median fold-noise; in-sample AUC **0.982**). The model learns _who the subject is_, which does not transfer — that gap **is** the Stage 5.4 confound. **But two interventions recover real signal, and both attack the confound rather than the model:** `S1_session_centred` **0.670 (p=0.005)** and `S2_lead_near_only` **0.696 (p=0.005)**, vs `S0_baseline` 0.344 (p=0.657) and `S3_cohort_centred` 0.355 (p=0.423). **S2 empirically vindicates HY's turn-around protocol** — it is the train/serve match that protocol produces and the **only subset where true LOSO works** (LOSO folds 0.960/1.000/0.760/0.750). **S3's failure is a finding in itself:** correcting only the cohort-level 8.9° offset recovers _nothing_, so the variation burying the signal is mostly **not** the camera artefact but individual build/movement differences — which is why turn-around is a **capture** fix, not a modelling one. S1 **cannot ship** despite its score (centring redefines the question to "better than your other reps" — a uniformly-poor set would read as average). "Subtract the measured 8.9° bias" was ruled out on **principle**: X3 forbids mocap as a model input. Also found: **a real bug in squat's calibration assertion** — its premise _"a sigmoid cannot reorder predictions"_ is **false** (Platt with a positive slope reverses the ranking exactly); it fired on lunge fold 3 (a=+2.70, 0.554→0.446), was corrected to the true invariant, and squat's own script was left untouched (its slopes are all negative, so its results stand). A **deployment-critical** check was added — the exported model's Platt slope must be negative or every live verdict is inverted with nothing downstream noticing; verified **−1.31 (OK)**, and **Stage 5.8 must re-run it**. New `ml/scripts/train_lunge.py`, `[LUNGE_TRAINING_REPORT.md](./ml/reports/LUNGE_TRAINING_REPORT.md)`, and `lunge_roc_curves.png` **— the project's first model ROC figure** (there was no AUC chart anywhere; only per-_feature_ tables). **Frontend turn-around protocol shipped (2026-07-17):** `lunge/config.py` gained a `capture` block (advisory, outside `rules`, never scores) with `lead_leg_near_margin_vis=0.05` [dataset-derived — front-minus-back knee visibility separates the two geometries with **zero overlap** over 88 reps: near-lead +0.129..+0.319, far-lead −0.106..−0.027, so 0.05 is the midpoint of an empty gap]; `lungeLiveEstimate.ts` detects the wrong facing and the live page prompts a turn-around; CameraSetup + all 3 locales updated; 7 new frontend tests (11/11 total). **That decision was superseded (2026-07-19): HY chose to remove Leg Lunge from the product entirely rather than resolve it — see the removal banner at the top of the Phase 5B section.** Phase 5B, Stages 5.6 onward, never happened. **Phase 6 (After-Set Report + LLM API) is complete (2026-07-19):** the Stage 6.1 tag table was reconciled to the 5 tags squat can actually support from one side view (the 3 shipped Stage 5.12 fault gates + a new `inconsistent_tempo` soft tag + the `low_confidence` system tag), dropping `asymmetry`/`feet_too_wide` as side-view-invalid (documented in `docs/module_b_limitations.md`, same precedent as valgus); the deterministic template (6.2) and safety filter (6.3) were built and gated _before_ the optional Groq adapter (6.4), which was built and live-verified last, proving the report never depends on it. `feedback_texts` reshaped (migration `0010`) and wired end-to-end into `/analyze`; `Report.tsx` gained a Module B coaching panel that surfaces `feedback_source` honestly ("Automatic summary" vs "AI-rewritten"). Backend suite **225/225**; live-verified against real Postgres + a running backend + the real Groq API (not mocked) with both the LLM disabled and enabled, and browser-verified in both states.  
**Related docs:** [FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md](./FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md) (architecture & design), [rules.md](./rules.md) (coding agent rules)

---

## Table of Contents

- [Recommended Start Order](#recommended-start-order)
- [Milestones](#milestones)
  - [Phase 1A Milestone (UI Prototype)](#phase-1a-milestone-ui-prototype)
  - [First Milestone (Phase 1B)](#first-milestone-phase-1b)
  - [Second Milestone](#second-milestone)
  - [Third Milestone](#third-milestone)
  - [Fourth Milestone (Module B Squat, Placeholder Model)](#fourth-milestone-module-b-squat-placeholder-model)
  - [Data Audit Gate (Phase 5, Stage 5.0)](#data-audit-gate-phase-5-stage-50)
  - [Data Audit Gate (Phase 5B, Stage 5.0 — Lunge)](#data-audit-gate-phase-5b-stage-50--lunge)
  - [Fifth Milestone (Trained Squat Model)](#fifth-milestone-trained-squat-model)
- [Phase 0: Project Setup](#phase-0-project-setup)
- [Phase 1: Basic Full-Stack Skeleton](#phase-1-basic-full-stack-skeleton)
  - [Phase 1A: UI Clickable Prototype *(current focus)](#phase-1a-ui-clickable-prototype-current-focus)*
  - [Phase 1B: Full-Stack Integration *(after Phase 1A)](#phase-1b-full-stack-integration-after-phase-1a)*
- [Phase 2: Camera and MediaPipe Integration](#phase-2-camera-and-mediapipe-integration)
- [Phase 3: Module A Functional Checking](#phase-3-module-a-functional-checking)
  - [Phase 3B rebuild: Single-Leg Stance (both legs, lift-line, ball-in-circle)](#phase-3b-rebuild-single-leg-stance-both-legs-lift-line-ball-in-circle)
  - [Phase 3D: Module A code reorganization (per-exercise folders)](#phase-3d-module-a-code-reorganization-per-exercise-folders)
  - [Phase 3E: WBLT rebuild — dual output (distance + angle), guided bracket](#phase-3e-wblt-rebuild-dual-output-distance-angle-guided-bracket)
  - [Phase 3E — Stage 5: frontend live-feedback config sync (2026-07-12)](#phase-3e-stage-5-frontend-live-feedback-config-sync-2026-07-12)
  - [Phase 3E — Stage 6: trend summary with MDC suppression (2026-07-12)](#phase-3e-stage-6-trend-summary-with-mdc-suppression-2026-07-12)
  - [Phase 3E — Stage 7: evaluation hooks (2026-07-13)](#phase-3e-stage-7-evaluation-hooks-2026-07-13)
- [Locked Assumptions (Phases 4–7)](#locked-assumptions-phases-47)
- [Cross-Cutting Rules (Phases 4–7)](#cross-cutting-rules-phases-47)
- [Phase 4: Module B Skeleton — Squat, Placeholder Model](#phase-4-module-b-skeleton-squat-placeholder-model)
  - [Stage 4.0 — Decision & config freeze *(no code yet)](#stage-40-decision-config-freeze-no-code-yet)*
  - [Phase 4 — Stage 4.0: Decision & config freeze (2026-07-16)](#phase-4-stage-40-decision-config-freeze-2026-07-16)
  - [Stage 4.1 — Backend package + exercise registry](#stage-41-backend-package-exercise-registry)
  - [Phase 4 — Stage 4.1: Backend package + exercise registry (2026-07-16)](#phase-4-stage-41-backend-package-exercise-registry-2026-07-16)
  - [Stage 4.2 — Feature extraction schema *(the X1 contract — most important stage in Phase 4)](#stage-42-feature-extraction-schema-the-x1-contract-most-important-stage-in-phase-4)*
  - [Phase 4 — Stage 4.2: Feature extraction schema (2026-07-16)](#phase-4-stage-42-feature-extraction-schema-2026-07-16)
  - [Stage 4.3 — Rep segmentation (squat FSM)](#stage-43-rep-segmentation-squat-fsm)
  - [Phase 4 — Stage 4.3: Rep segmentation (squat FSM) (2026-07-16)](#phase-4-stage-43-rep-segmentation-squat-fsm-2026-07-16)
  - [Stage 4.4 — Rule sub-scores (squat)](#stage-44-rule-sub-scores-squat)
  - [Phase 4 — Stage 4.4: Rule sub-scores (squat) (2026-07-16)](#phase-4-stage-44-rule-sub-scores-squat-2026-07-16)
  - [Stage 4.5 — Fusion + placeholder ML interface](#stage-45-fusion-placeholder-ml-interface)
  - [Phase 4 — Stage 4.5: Fusion + placeholder ML interface (2026-07-16)](#phase-4-stage-45-fusion-placeholder-ml-interface-2026-07-16)
  - [Stage 4.6 — Persistence + read-back](#stage-46-persistence-read-back)
  - [Phase 4 — Stage 4.6: Persistence + read-back (2026-07-16)](#phase-4-stage-46-persistence-read-back-2026-07-16)
  - [Stage 4.7 — Frontend (squat)](#stage-47-frontend-squat)
  - [Phase 4 — Stage 4.7: Frontend (squat) (2026-07-16)](#phase-4-stage-47-frontend-squat-2026-07-16)
  - [Stage 4.8 — Phase 4 verification gate](#stage-48-phase-4-verification-gate)
  - [Phase 4 — Stage 4.8: Verification gate (complete, 2026-07-16)](#phase-4-stage-48-verification-gate-complete-2026-07-16)
- [Phase 5: Dataset and ML Training (Squat)](#phase-5-dataset-and-ml-training-squat)
  - [Stage 5.0 — Data audit **[HARD GATE — no training work until this reports numbers]](#stage-50-data-audit-hard-gate-no-training-work-until-this-reports-numbers)**
  - [Phase 5 — Stage 5.0: Data audit (2026-07-16)](#phase-5-stage-50-data-audit-2026-07-16)
  - [Stage 5.1 —](#stage-51-ml-scaffold) `ml/` [scaffold](#stage-51-ml-scaffold)
  - [Phase 5 — Stage 5.1:](#phase-5-stage-51-ml-scaffold-2026-07-16) `ml/` [scaffold (2026-07-16)](#phase-5-stage-51-ml-scaffold-2026-07-16)
  - [Stage 5.2 — Landmark extraction from RGB video](#stage-52-landmark-extraction-from-rgb-video)
  - [Phase 5 — Stage 5.2: Landmark extraction (2026-07-16)](#phase-5-stage-52-landmark-extraction-2026-07-16)
  - [Cross-cutting — Wire real preprocessing into Module B squat pipeline (2026-07-16)](#cross-cutting-wire-real-preprocessing-into-module-b-squat-pipeline-2026-07-16)
  - [Cross-cutting follow-up — far-limb occlusion breaks hold-last (2026-07-16)](#cross-cutting-follow-up-far-limb-occlusion-breaks-hold-last-2026-07-16)
  - [Stage 5.3 — Build the feature table](#stage-53-build-the-feature-table)
  - [Phase 5 — Stage 5.3: Build the feature table (2026-07-16)](#phase-5-stage-53-build-the-feature-table-2026-07-16)
  - [Stage 5.4 — Feature-validity sanity **[GATE — R5.5]](#stage-54-feature-validity-sanity-gate-r55)**
  - [Phase 5 — Stage 5.4: Feature-validity sanity [GATE] (2026-07-16)](#phase-5-stage-54-feature-validity-sanity-gate-2026-07-16)
  - [Stage 5.5 — Train the Extra Trees classifier](#stage-55-train-the-extra-trees-classifier)
  - [Phase 5 — Stage 5.5: Train the Extra Trees classifier (2026-07-16)](#phase-5-stage-55-train-the-extra-trees-classifier-2026-07-16)
  - [Stage 5.6 — Fair threshold + fusion weight sweep](#stage-56-fair-threshold-fusion-weight-sweep)
  - [Phase 5 — Stage 5.6: Fair threshold + fusion weight sweep (2026-07-16)](#phase-5-stage-56-fair-threshold-fusion-weight-sweep-2026-07-16)
  - [Stage 5.7 — Evaluation](#stage-57-evaluation)
  - [Stage 5.8 — Export + backend integration](#stage-58-export-backend-integration)
  - [Stage 5.9 — EC3D external validation *(the firewall pays off here)](#stage-59-ec3d-external-validation-the-firewall-pays-off-here)*
  - [Phase 5 — Stage 5.9: EC3D external validation (2026-07-17)](#phase-5-stage-59-ec3d-external-validation-2026-07-17)
  - [Stage 5.10 — Option B: documented, not built *(for Chapter 3)](#stage-510-option-b-documented-not-built-for-chapter-3)*
  - [Phase 5B: Lunge **[GATE — do not start until Phase 5 Stage 5.8 is verified live]](#phase-5b-lunge-gate-do-not-start-until-phase-5-stage-58-is-verified-live)**
  - [Phase 5B — Stage 4.1 (Lunge): Backend package + exercise registry (2026-07-17)](#phase-5b-stage-41-lunge-backend-package-exercise-registry-2026-07-17)
- [Phase 6: After-Set Report and External LLM API](#phase-6-after-set-report-and-external-llm-api)
  - [Stage 6.1 — Structured feedback + error-tag taxonomy](#stage-61-structured-feedback-error-tag-taxonomy)
  - [Stage 6.2 — Template fallback *(built first, on purpose)](#stage-62-template-fallback-built-first-on-purpose)*
  - [Stage 6.3 — Safety filter](#stage-63-safety-filter)
  - [Stage 6.4 — Groq adapter](#stage-64-groq-adapter)
  - [Stage 6.5 — Persist + display](#stage-65-persist-display)
- [Phase 7: Dashboard and Progress Tracking](#phase-7-dashboard-and-progress-tracking)
  - [Stage 7.0 — Trend API](#stage-70-trend-api)
  - [Stage 7.1 — Dashboard panels](#stage-71-dashboard-panels)
  - [Stage 7.2 — Per-session trend rows for STS and SLS](#stage-72-per-session-trend-rows-for-sts-and-sls)
  - [Stage 7.3 — Reminders](#stage-73-reminders)
  - [Stage 7.4 — Verification](#stage-74-verification)
- [Open Questions (Phases 4–7)](#open-questions-phases-47)
- [Deliberately Not Built (Phases 4–7)](#deliberately-not-built-phases-47)
- [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)
- [Path/assumption mismatches found (non-blocking, informational)](#pathassumption-mismatches-found-non-blocking-informational)
- [Phase 8: Deployment](#phase-8-deployment)
- [Phase 9: Evaluation and Final Report Evidence](#phase-9-evaluation-and-final-report-evidence)

---

## Recommended Start Order

Since the project is at 0 progress, do **not** start with ML first. Work in this order:

1. Create React + TypeScript + Tailwind frontend
2. Create FastAPI backend
3. Create PostgreSQL Docker setup
4. Make backend connect to PostgreSQL
5. **Phase 1A:** Build UI clickable prototype (all main pages, mock data, wired navigation)
6. **Phase 1B:** Implement register/login, JWT, session APIs, and connect UI to backend
7. Add webcam and MediaPipe Pose
8. Implement Module A simple rule-based checking
9. Then start Module B placeholder pipeline
10. Only after that, train/integrate Extra Trees model
11. Deploy after core flow works locally

---

## Milestones

### Phase 1A Milestone (UI Prototype)

> A user can click through all main application pages with placeholder data and understand the full app flow (no real backend yet).

### First Milestone (Phase 1B)

> A user can register, login, start a session, end a session, and see that session saved in PostgreSQL.

### Second Milestone

> The webcam page can show MediaPipe Pose skeleton overlay and capture quality.

### Third Milestone

> Module A produces and stores Good/Fair/Poor results for at least one functional check.

### Fourth Milestone (Module B Squat, Placeholder Model)

> Module B runs end-to-end for squat with an honest, announced placeholder model (`model_version: "stub-0"`) — verified live against the real backend + Postgres. Closes Phase 4.

### Data Audit Gate (Phase 5, Stage 5.0)

> `ml/reports/DATA_AUDIT.md` reports the exact usable side-view squat (Ex6) rep count after the camera-orientation filter, and HY has chosen among options (a) accept the smaller N, (b) admit half-profile reps as a flagged cohort, or (c) relax to both views and add `view` as a feature. No ML training work begins before this decision (see [Open Questions](#open-questions-phases-47) Q1/Q2). **✅ Resolved 2026-07-16 — option (a).**

### Data Audit Gate (Phase 5B, Stage 5.0 — Lunge)

> `ml/reports/LUNGE_DATA_AUDIT.md` reports the usable side-view lunge (Ex5) rep count — **88 reps, Good 39 / Poor 49** — and lays out the same three options with lunge-specific trade-offs. **✅ Resolved by HY (2026-07-17): option (a) — accept the smaller N.** Stage 5.2 (Lunge) onward trains on these 88 reps only.

### Fifth Milestone (Trained Squat Model)

> A trained, calibrated, LOSO-evaluated Extra Trees squat model is loaded by the backend, replacing the Phase 4 stub — verified live end-to-end. Closes Phase 5.

---

## Phase 0: Project Setup

**Goal:** Prepare development environment and repository.

**Tasks:**

- [x] Create frontend folder using React + TypeScript + Vite
- [x] Install Tailwind CSS
- [x] Create backend folder using FastAPI
- [x] Add Docker Compose for PostgreSQL
- [x] Connect FastAPI to PostgreSQL
- [x] Create `.env.example` files
- [x] Add basic README

**Deliverable:**

- Frontend runs locally
- Backend runs locally
- PostgreSQL runs locally
- Backend can connect to database

---

## Phase 1: Basic Full-Stack Skeleton

**Goal:** Build the minimum working application structure.

**Approach:** Complete **Phase 1A (UI clickable prototype)** first. Only after the prototype is done, start **Phase 1B (backend integration)**.

---

### Phase 1A: UI Clickable Prototype _(current focus)_

**Goal:** Build all main pages as a clickable frontend prototype with mock/placeholder data. No real API calls, auth, or database yet.

**Tasks:**

- [x] Set up React Router and shared app layout (nav, footer, disclaimer)
- [x] Landing Page — intro, non-diagnostic disclaimer, login/register links
- [x] Register Page — email, password, basic profile form (UI only)
- [x] Login Page — email, password form (UI only)
- [x] Dashboard Page — summary cards, recent sessions, chart, error tags (mock data)
- [x] Mode Selection Page — Functional Checking / Rehab Grading
- [x] Exercise Selection Page — Module A checks + Module B placeholder
- [x] Camera Setup Page — layout, guidance text, placeholder preview area
- [x] Live Session Page — timer, rep/hold progress, band indicator (mock)
- [x] Post-Performance Report Page — score, band, sub-scores, feedback (mock)
- [x] Session History Page — mock session list with filters (UI only)
- [x] Reminder Page — add/view/complete reminders (mock)
- [x] Wire clickable navigation across the full user flow

**Phase 1A extras delivered:** dark/light theme toggle (light default), 4-language i18n
(English, 中文, Bahasa Malaysia, हिन्दी), accessibility text-size control (A/A+/A++),
fully responsive layouts (desktop / tablet / mobile drawer). Design language first
prototyped in `mockups/physiofit-mockup.html`, then implemented in the React app.

**Deliverable:**

- All 11 required pages exist and are reachable
- User can click through the full app journey using placeholder data
- Non-diagnostic disclaimer visible on key pages

---

### Phase 1B: Full-Stack Integration _(after Phase 1A)_

**Goal:** Connect the prototype to the FastAPI backend and PostgreSQL.

**Tasks:**

- [x] Implement register/login
- [x] Implement JWT authentication
- [x] Create user profile page (connect to backend)
- [x] Replace dashboard placeholder data with API-driven data
- [x] Create exercise catalog seed data
- [x] Create session start/end APIs
- [x] Connect session history page to backend

**Deliverable:**

- User can register/login
- User can start and end a session
- Session appears in history

---

## Phase 2: Camera and MediaPipe Integration

**Goal:** Make the frontend detect body landmarks.

**Tasks:**

- [x] Build Camera Setup page
- [x] Access webcam using Browser MediaDevices API
- [x] Integrate MediaPipe Pose (`pose_landmarker_full`, self-hosted WASM + model)
- [x] Draw skeleton overlay on canvas (`PoseCanvas` component)
- [x] Calculate landmark visibility (`computeFrameQuality`)
- [x] Show capture quality badge (`CaptureQualityBadge` component)
- [x] Add side/front view instruction by exercise type
- [x] Gate "Start session" button on capture quality ≥ 60%
- [x] Session recorder buffers landmark frames for Phase 3/4
- [x] Replace hardcoded `0.9` quality in `sessionService.end` with real metrics

**Deliverable:**

- Webcam works
- Pose landmarks are visible with skeleton overlay
- Capture quality is shown (real, not hardcoded)
- Session end sends genuine `capture_quality` + `valid_frame_ratio` to backend

---

## Phase 3: Module A Functional Checking

**Goal:** Implement the three rule-based functional checks.

**Tasks:**

- [x] Implement Sit-to-Stand session flow (Phase 3A)
  - [x] Live rep-boundary detection (FSM with hysteresis)
  - [x] Backend auto-persistence on rep target
  - [x] Decoupled session_status from band
  - [x] Partial score support for incomplete sessions
- [x] Implement Supported Single-Leg Stance session flow (Phase 3B)
  - [x] Backend balance detection (ankle height diff)
  - [x] Hold duration metrics collection
  - [x] SLS-specific scoring (hold quality band)
  - [x] Report page SLS metrics display
- [x] Implement Weight-Bearing Lunge Test session flow (Phase 3C)
  - [x] Lunge pose detection (knee angle-based entry/exit)
  - [x] Dorsiflexion ROM measurement
  - [x] Trial tracking (target 3 trials)
  - [x] Ankle symmetry proxy metrics
  - [x] ROM and symmetry-based scoring
- [x] Calculate simple metrics
- [x] Generate Good/Fair/Poor band
- [x] Save Module A results to PostgreSQL
- [x] Show report page

- [x] Show dashboard trend — **done (Phase 7)**: the Dashboard page (`Dashboard.tsx`) score-trend/band-distribution/confidence panels are now real Recharts views over account history (Stage 7.1, `dash.placeholderScoring` removed), the Progress deep-dive page adds per-exercise trends (Stage 7.1b), and all four exercises now carry a per-session "vs last session" trend row on the Report page — WBLT (Phase 3E Stage 6, MDC-gated), STS/SLS (Stage 7.2), and squat (Stage 7.4). See Phase 7 dated entries.

**Deliverable:**

- ✅ User can complete all 3 functional checks (STS, SLS, WBLT)
- ✅ Results are saved and viewable with exercise-specific metrics
- ✅ Single-endpoint `/api/module-a/analyze` dispatches to exercise-specific logic
- ✅ Decoupled session_status from band across all exercise types
- ✅ Frontend LiveSession UI complete for all 3 exercises — `StsLiveSessionPage` (`/sts/live`), `SlsLiveSessionPage` (`/sls/live`), `WbltLiveSessionPage` (`/wblt/live`); SLS verified E2E (Phase 3B), WBLT verified live (Phase 3E)

### Phase 3B rebuild: Single-Leg Stance (both legs, lift-line, ball-in-circle)

**Goal:** Supersede the original single-leg SLS with the full plan-doc spec — both legs, 45s cap, lift-line gate, ball-in-circle stability sub-score, gamified live combo, and specific chair/wall support guidance. See `~/.claude/plans/users-sumhonyou-downloads-physiofit-sin-distributed-newell.md` for the full plan.

**Tasks:**

- [x] Stage 1: SLS config (45s/lift-line/circle/weights), per-leg `crud.save_sls_result`, i18n support guidance (en/zh/ms), SLS demo video wired into Camera Setup
- [x] Stage 2: `SlsLiveSessionPage` shell + client-side `liveGeometry.ts` (lift-line, hip-midpoint ball, inside-circle) mirroring the backend
- [x] Stage 3: Backend `sls/geometry.py` + `sls/fsm.py` + `sls/analysis.py` (deterministic, 13 unit tests) + `POST /api/sls/analyze`
- [x] Stage 4: `sls/scoring.py` (hold + time-in-circle stability, 50/50 combined) + live combo-multiplier overlay (`ComboScore`, `SLS score.mp3` on step-ups) — display-only, never persisted
- [x] Stage 5: Both-legs orchestration (right → left) in `SlsLiveSessionPage`, `GET /api/sls/session/{id}`, `SupportSelfReportModal` → `POST /api/sls/support`
- [x] Stage 6: `Report.tsx` per-leg display + migration branch on `metrics.perLeg` (legacy single-leg rows still render via the pre-existing code path); forbidden-clinical-phrase test
- [x] Stage 7: Replay/evaluation harness (ICC/Bland-Altman, Cohen's kappa), prototype-threshold + monocular-depth-limitation write-up

**Verified 2026-07-07:** full browser E2E (register → select exercise → camera setup guidance/video → live session → both legs → support modal → session end) against the real backend + Postgres. Confirmed: `POST /api/sls/analyze` persists correct per-leg JSONB, `POST /api/sls/support` stores `usedSupport` without changing `score`, leg orchestration and i18n (stop-reason translation, leg prompts) all correct. Backend: 32/32 pytest passing.

**Stage 6 detail (2026-07-07):** `Report.tsx` now branches on `result.metrics.perLeg` — new SLS rows render per-leg cards (band, best hold, stability, combined score, translated stop reason), L/R difference, support-used, and capture quality; legacy single-leg rows (pre-rebuild) fall through unchanged to the original metric-row rendering. Added 4 missing `report.warn_`* i18n keys (en/zh/ms) so SLS-specific warning tags (`incomplete_hold`, `landmarks_missing`, `foot_dropped_below_line`, `unknown`) translate instead of showing raw tag strings. Added `backend/tests/test_frontend_disclaimers.py` (3 tests) scanning all 3 i18n locale files for forbidden clinical-claim phrasing, since the frontend has no JS test runner configured. Backend: 35/35 pytest passing. Verified end-to-end in-browser with a real asymmetric two-leg session (right leg 41.7s/Good/9.8, left leg 14.9s/Poor/3.8, session Fair/6.8, support="slight") — confirmed correct rendering, correct i18n, and that Dashboard/SessionHistory (which only read top-level session fields, never `metrics`) are unaffected.

**Stage 7 detail (2026-07-07):** Added `backend/app/module_a/evaluation/agreement.py` — pure-Python ICC(2,1), Bland-Altman, and Cohen's kappa (no numpy/scipy/pingouin dependency exists in this project; these are simple closed-form formulas over a small sample), with 11 unit tests using hand-verifiable boundary cases (perfect agreement, zero between-subject signal, manually-computed Bland-Altman example). Added `generate_sls_replay_corpus.py` (fixed-seed synthetic corpus generator — no real pilot recordings exist yet for this prototype; 10 per-leg samples spanning Poor/Fair/Good/Invalid, steady and swaying, committed to `app/module_a/replay_corpus/sls/`) and `run_sls_evaluation.py` (replays the corpus through `analyze_leg`, computes agreement metrics, writes `evaluation/SLS_EVALUATION_REPORT.md`). Also added `replay_sls_session.py`, the SLS analogue of the existing STS `replay_session.py`. Added `scoring.hold_time_band()` so band agreement is evaluated on the hold-time dimension only (the one thing a stopwatch-only human reviewer could independently reproduce — the ball-in-circle stability sub-score would need a separate rater protocol). Results (reproducible, verified byte-identical across two runs): **ICC(2,1) = 0.995**, **Cohen's kappa = 0.857**, **Bland-Altman bias = -0.753s** (system reads slightly shorter than the simulated manual reference, consistent with the FSM's drop-hysteresis persistence frames), **95% LoA = [-4.08s, 2.57s]**. One band disagreement out of 10 (system correctly reports `invalid` for a leg that never validly crossed the lift-line, while the naive time-based reference calls a small positive duration `poor`) is called out explicitly in the report as a genuine edge-case divergence, not a bug. Backend: 46/46 pytest passing. The monocular-depth limitation (frontal-plane-only stability scoring) and all prototype thresholds (from `config.py`) are documented in the generated report for Chapter 3 / limitations use. This closes out the Phase 3B rebuild (Stages 1-7 all complete).

**Deliberately out of scope:** the Dashboard's score-trend/band-distribution/confidence panels are static placeholders for _every_ exercise type (STS and WBLT included) — `dash.placeholderScoring: "Scoring appears after Module A/B is implemented."` — this is pre-existing, cross-cutting tech debt, not SLS-specific. Building a real per-leg trend chart only for SLS would be inconsistent with every other exercise and is a larger undertaking (a trend-data API + charting) than "Stage 6 polish." Flagging as a separate future task rather than building a one-off.

### Phase 3D: Module A code reorganization (per-exercise folders)

**Goal:** Fix "everything lives in one flat file, dispatched by `if exercise_type == ...`" — split STS/WBLT/SLS into dedicated packages/folders mirroring the SLS package that already existed, so the module structure actually maps to feature boundaries.

**Backend (**`backend/app/module_a/`**):**

- `core/` — shared, exercise-agnostic: `config.py`, `schemas.py`, `banding.py` (dispatcher + `score_to_band`/`compute_session_status`), `crud.py` (generic `save_result`/history/landmark-log), `geometry.py`, `quality.py`, `smoothing.py`, `router.py` (the shared `/api/module-a/analyze` endpoint, renamed from `rest_router.py`)
- `sts/` — `config.py`, `engine.py` (`run_sts`, extracted from the old `SessionEngine._run_sts`), `banding.py`, `schemas.py` (`ModuleAMetrics`)
- `wblt/` — `config.py`, `engine.py` (`run_wblt`), `banding.py`
- `sls/` — extended with `config.py` (the `SLS_*` rebuild constants), `schemas.py` (`Sls*` request/response models), `crud.py` (`save_sls_result`), `router.py` (renamed from the top-level `sls_router.py`), `evaluation/` (moved in from `module_a/evaluation/`)
- Deleted: the old flat `session_engine.py`, `banding.py`, `config.py`, `crud.py`, `schemas.py`, `rest_router.py`, `sls_router.py`, top-level `evaluation/` — plus the **dead legacy single-leg SLS code path** (`_run_sls`, `_compute_sls_band`, and its config constants/tests) that the SLS rebuild (Phase 3B) had already superseded but never removed. Verified dead by grepping for every caller and the frontend before deleting.
- All 40 backend tests pass; `app.main` imports cleanly (27 routes); Black/isort applied.

**Frontend (**`frontend/src/`**):** `pages/LiveSession.tsx` (which was STS-only in practice despite its generic name — confirmed every code path gated on `isSts`) moved to `pages/sts/StsLiveSessionPage.tsx`, mirroring the existing `pages/sls/` folder; its estimator util moved from `utils/stsLiveEstimate.ts` to `utils/sts/stsLiveEstimate.ts`; route renamed `/live` → `/sts/live`. Deleted the dead legacy `utils/slsLiveEstimate.ts` and its two orphaned constants in `moduleAThresholds.ts` (only referenced from commented-out code). `CameraSetup.tsx`, `ExerciseSelection.tsx`, `Report.tsx`, `Dashboard.tsx`, `SessionHistory.tsx` were **not** moved — they're genuinely shared across all 3 exercises (each branches internally by exercise code), so nesting them under one exercise's folder would misrepresent what they do.

**⚠️ Known issues surfaced during this reorg, resolved in Phase 3E below:**

1. **WBLT backend crash bug:** `wblt/engine.py`'s `run_wblt()` (moved verbatim from the old `_run_wblt`) calls `angleDeg(...)`, a function that is never defined or imported anywhere in the codebase. Any real WBLT session that reaches this code path will raise `NameError`. This means **WBLT has never been exercised end-to-end** — it was implemented (Phase 3C, above) but is currently broken. ~~Fixing both is a real feature-completion task (not a rename/move), tracked here for a future phase rather than folded into this reorg.~~ **Resolved:** `wblt/engine.py` and the old ROM/symmetry `wblt/banding.py` were deleted and replaced with a dual-output (distance + angle) design — see Phase 3E.
2. **WBLT frontend has no live-session page.** `CameraSetup.tsx` routes every non-SLS exercise (including WBLT) to the STS-only live page; there's no `isWblt` branch anywhere in the old `LiveSession.tsx`/new `StsLiveSessionPage.tsx`, and no live-threshold constants for WBLT exist on the frontend. A WBLT session currently lands on a page that does nothing for it. **Resolved** in Phase 3E (right leg only; both-legs frontend flow is a follow-up stage).

---

### Phase 3E: WBLT rebuild — dual output (distance + angle), guided bracket

**Status:** Stages 0-4 (age migration; right leg; guided bracket/both legs/symmetry; capture-quality gate Q; persistence audit trail) complete, verified live against a running Postgres. Stages 5-7 (frontend config sync polish, trend, evaluation harness) are follow-up work — see the full blueprint this phase implements for the staged plan.

**Why a rebuild, not a bug fix:** the old WBLT design (Phase 3C) tried to camera-measure absolute ROM and band it directly — structurally unsound on a single monocular webcam (no reliable depth/contact detection) and never had a real normative source for its band cutoffs. Redesigned as **dual output**: the _official_ band is a **user-measured distance** (ruler/tape self-report) scored against McBride et al. (2026) Table 2 age/sex percentile bands — sidesteps monocular depth entirely and unlocks a real published normative table. The **camera-measured dorsiflexion angle** is kept as a secondary, never-banded signal (corroboration/symmetry/trend). The camera's one enforced job is **heel-lift validity** (self-referential vertical motion — tractable on one camera, and the main way the test is gamed), which can also override an over-optimistic "yes I touched" self-report. Full rationale in [FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md §24](./FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md#24-additions-and-deviations-from-the-original-plan).

**Stage 0 — age migration (blocking prerequisite):**

- [x] `user_profiles.exact_age` (Integer, nullable) added via Alembic migration `20260712_0005_user_profile_exact_age.py`, backfilled for every existing row from the `age_group` bucket's midpoint (`under_40`→30, `40_60`→50, `over_60`→70) — an interim estimate, not a substitute for the real value.
- [x] `age_to_band(exact_age)` — single shared resolver (`backend/app/module_a/wblt/age_band.py`), never inlined elsewhere. Clamps under-18 up to the youngest McBride band rather than leaving it unbanded.
- [x] `resolve_ageband_sex(exact_age, gender)` blocks banding (returns `None`) on missing age or on `gender="prefer_not_to_say"`/unset — never guesses a sex.
- [x] `UserRegister`/`ProfileRead`/`ProfileUpdate` schemas and the register/profile-update routes carry `exact_age` through.
- [x] Registration fallback: `auth_routes.register()` now derives `exact_age` from the `age_group` bucket midpoint (`exact_age_from_age_group`) whenever the client doesn't supply one — closes a real gap where every _new_ signup (not just pre-existing rows) landed with `exact_age = NULL` and silently blocked WBLT banding.
- [x] Follow-up migration `20260712_0006_backfill_remaining_exact_age.py` fills any row `20260712_0005`'s bucket backfill couldn't cover (non-standard/blank `age_group` values found in existing test data) with a flat placeholder age — confirmed test-only data, not real users.
- [x] **Resolved (superseding the profile-completion-prompt idea below):** rather than a one-time prompt, `age_group` was removed entirely and replaced with a required "How old are you?" number input, collected directly at signup with the same required posture as gender (both fields lost their "(optional)" label; age gained real 1-120 validation). `user_profiles.age_group` dropped via migration `20260713_0007_drop_age_group.py`; `UserProfile`/`UserRegister`/`ProfileRead`/`ProfileUpdate` and every route (`auth_routes.py`, `user_routes.py`) updated to use only `exact_age`. The now-dead `exact_age_from_age_group()` fallback and `_AGE_GROUP_MIDPOINTS` bucket table were deleted from `age_band.py` — no code path derives an age from a bucket anymore, only from what the user actually typed. `Register.tsx`, `Login.tsx`'s inline register form, and `Profile.tsx` (view + edit) all updated; i18n `ageGroup`/`ageUnder40`/`age40_60`/`ageOver60`/`optional` keys removed (en/zh/ms), replaced with `auth.age`/`auth.agePh`/`auth.invalidAge`. Existing accounts keep whatever `exact_age` the earlier bucket-midpoint backfill gave them (still an approximation until they edit their profile) — verified live: a fresh registration through the real UI persisted `exact_age`/`gender` correctly with no `age_group` anywhere in the DB or API responses; full 76-test backend suite + frontend typecheck/build clean.

**Stage 1 — right leg, one attempt:**

- [x] Dedicated `/api/wblt/*` router, mirroring the SLS precedent — deviates from the plan's shared `/api/module-a/analyze` (§14.5); WBLT removed from that shared dispatcher (`core/router.py`, `core/banding.py`) entirely, STS is the only exercise left on it.
- [x] `wblt/config.py` — `WBLT_CONFIG` (McBride Table 2 distance bands, Table 1 seed distances, heel-lift thresholds, `q_min`); config-driven, never hard-coded inline.
- [x] `wblt/geometry.py` — dorsiflexion angle (sagittal-plane projection of the shank vs. world-vertical) + `HeelLiftDetector` (hysteresis on heel-rise-ratio).
- [x] `wblt/analysis.py` — `analyze_attempt()`: theta_peak from heel-valid frames only, heel-lift overrides an over-optimistic touch self-report, distance band via McBride only when the touch is valid AND `ageband_sex` resolves, capture-quality gate blocks banding (not the angle) below `q_min`.

**Stage 2 — guided 3-attempt bracket, both legs, symmetry:**

- [x] `analysis.bracket_state()` — pure function implementing §4.2: seeds from McBride Table 1 (`seed_distance_cm[ageband_sex]`, with a `fallback_seed_distance_cm` when the profile can't resolve one), steps `+bracket_step_cm` on a valid touch / `-bracket_step_cm` (floored at `bracket_min_distance_cm`) on a fail, offers exactly one bonus attempt when all `attempts_per_leg` base attempts were valid touches.
- [x] `analysis.summarize_leg()` — leg distance score = largest valid-touch distance (never the failed bonus attempt); leg angle = max theta_peak over every heel-down-valid attempt regardless of touch outcome; `floor_flag` when every attempt in the leg failed.
- [x] `analysis.compute_symmetry()` / `compute_session_summary()` — `|angle_R - angle_L| >= angle_symmetry_flag_deg` → `asymmetry_flag`, only once both legs have an angle; overall session score/band = mean of legs with a resolved band via the shared `score_to_band`.
- [x] Router: `GET /session/{id}/bracket/{leg}` (next target + attempt number, needed even before attempt 1 since the seed is resolved server-side from the account's exact_age/sex, never the client); `POST /analyze` now accepts both legs and appends to that leg's attempt list instead of overwriting; `GET /session/{id}` returns the full both-legs + symmetry summary.
- [x] `crud.save_wblt_session()` persists the nested `{legs: {right: {...}, left: {...}}, symmetry: {...}}` shape incrementally, one write per attempt.
- [x] Frontend `WbltLiveSessionPage.tsx` rewritten: loops `leg_order` from `GET /config`, fetches the bracket's next target before every attempt (never computed client-side), shows attempt-result → leg-result → session-result (symmetry) stages; `wblt.*` i18n extended with left-leg/bracket/symmetry strings (en/zh/ms).
- [x] **Report page gap found and fixed:** `Report.tsx`'s per-exercise metrics renderer only branched STS vs. SLS (`hasPerLeg`/`isSls`) — a finished WBLT session rendered a "Sit-to-Stand metrics" panel with blank/undefined fields, because `GET /api/module-a/sessions/{id}` (the generic read-back endpoint, unaffected by WBLT's move off the shared analyze dispatcher) just echoes back whatever `metrics_json` shape is stored. Added an `isWblt`/`hasWbltLegs` branch rendering both legs + symmetry, plus a WBLT-specific incomplete-session message; `moduleAService.ts`'s `ModuleAMetrics` type extended with the `legs`/`symmetry` shape. `Dashboard.tsx`/`SessionHistory.tsx` checked and don't have the same gap — they only read the exercise-agnostic `sessions.score`/`band` columns.
- [x] 27 backend unit tests (`tests/test_module_a_wblt.py`): geometry (vertical/forward-lean/left-leg-mirrored angle, heel-lift invalidation/override), bracket stepping (seed, step out/in, floor, bonus-attempt offer/close-out), leg summarization (best-distance selection, floor_flag, angle-from-any-valid-attempt), symmetry (symmetric/flagged/single-leg), session summary (both-done, one-incomplete, both-floor-flagged). Full suite: 67 tests passing.
- [x] **Verified live end-to-end** against a real running Postgres (Docker unpaused, migrations `20260712_0005`/`20260712_0006` applied): a scripted both-legs run through the real HTTP API reproduced the exact bracket math (seeded at 11.2cm for `30-39_male`, stepped 11.2→13.2→15.2cm on 3 valid touches, correctly offered and then closed out a bonus attempt at 17.2cm), picked the correct best distance (15.2cm, not the failed bonus), computed a real 24.1° asymmetry flag between a deliberately different-angle left/right, persisted correctly (`module_a_results`/`sessions` rows), and rendered correctly on the Report page (confirmed via rendered page text, not just API response).

**Stage 3 — capture-quality gate Q (§8):**

- [x] `geometry.hip_x_separation_norm()` — the `lateral_alignment` sub-check, derived entirely from WORLD landmarks already collected for §5.1 (no new wire-format field needed): a true side-on camera sees the anatomical left-right hip axis foreshortened onto its own depth axis (small hip world-x separation), a frontal camera sees it face-on (hip world-x separation approaches real anatomical hip width). Computed from the median hip-x-diff over the same foot-flat calibration window `HeelLiftDetector` already uses.
- [x] `analyze_attempt()` now computes the real `Q = min(lateral_alignment, leg_visibility, landmark_conf)` (previously `Q` was just `valid_frame_ratio` alone — Stage 1/2 shipped with a placeholder). `leg_visibility`/`landmark_conf` reuse the existing valid-frame-ratio/average-visibility from `core.quality`. Whichever sub-check is lowest becomes `q_limiting_factor`, surfaced as a specific `retry_lateral_alignment`/`retry_leg_visibility`/`retry_landmark_conf` warning tag (blueprint's "retry + specific placement guidance").
- [x] **Correctness fix caught while implementing this:** a `Q < q_min` attempt was still being appended to the leg's bracket and consuming an attempt slot — contradicting the blueprint's "retry" language (a bad-camera-angle capture shouldn't count as data at all). Fixed in `router.py`: when the Q gate trips, the attempt is neither appended to `legs[leg]["attempts"]` nor persisted (`persisted: false` in the response); the response instead returns the SAME `attempt_number`/`next_target_distance_cm` the user just tried, so the very next capture retries the identical slot.
- [x] 3 new backend tests (`WbltCaptureQualityTests`): a frontal-camera fixture (large hip world-x separation) correctly zeroes `lateral_alignment`, blocks the band, and flags `retry_lateral_alignment`; a genuine side-on fixture never trips it; a moderately-off angle sits strictly between 0 and 1 (not a hard cliff). Full suite: 70 tests passing.
- [x] Frontend: no JS changes needed — `WbltLiveSessionPage.tsx`'s attempt-result panel already renders every `warning_tags` entry through a generic `t('wblt.warn_' + tag)` lookup, so only the three new i18n messages (en/zh/ms) were needed to surface Stage 3's guidance.
- [x] **Verified live end-to-end** against the running Postgres: a scripted frontal-camera attempt was rejected (`q=0.0`, `band=null`, `persisted=false`, tagged `retry_lateral_alignment`) with the bracket state confirmed byte-identical via a fresh `GET /bracket` call before and after; a follow-up good side-on attempt at the exact same target then succeeded normally and advanced the bracket, landing on `attempt_number=2` as if the rejected attempt had never happened. Direct DB query confirmed only 1 attempt was ever persisted for that leg despite 2 `POST /analyze` calls.

**Stage 4 — persistence audit trail (§9):**

- [x] `analysis.resolve_profile_snapshot()` — stores the `exact_age`/`age_band_resolved`/`sex` a band was ACTUALLY computed from, snapshotted at analysis time. Without this, re-deriving the band later from the account's _current_ stored age (which can change) would silently rewrite history for old sessions; the snapshot makes that impossible.
- [x] `analysis.compute_agreement_pairs()` — per-leg `(distance_cm, angle_deg)` pairs for the Stage 7 angle-vs-distance Bland-Altman export; only legs with both a resolved distance and angle qualify (a floor-flagged leg has nothing to pair).
- [x] `crud.save_wblt_session()` persists `profile`/`agreement_pairs`/`session_summary.captured_at` alongside `legs`/`symmetry`. `captured_at` is stamped once, the first time both legs complete, and preserved on every later save/read — proven live by two successive `GET`s returning byte-identical timestamps.
- [x] `WbltSessionSummaryResponse` extended with `profile`, `agreement_pairs`, `captured_at`; frontend `WbltSessionSummary` type updated to match (no UI changes yet — the data is available for Report.tsx/Stage 7 to consume later).
- [x] 6 new backend tests (`WbltProfileSnapshotTests`, `WbltAgreementPairsTests`) covering full/missing-age/prefer-not-to-say snapshots and both-banded/floor-flagged/incomplete-leg pairing. Full suite: 76 tests passing.
- [x] **Verified live end-to-end**: a completed both-legs session persisted the exact expected profile snapshot (`{"exact_age": 30, "age_band_resolved": "30-39", "sex": "male"}`), 2 agreement pairs, and a `captured_at` confirmed stable across two independent `GET /session/{id}` calls.
- [ ] **Not done:** no runtime enforcement that blocks a session if the account's age is still unmigrated (the "fails loudly" language in the blueprint's gate) — moot in practice since Stage 0's migration already guarantees every account has an `exact_age`, but if that invariant is ever broken by a future migration, `resolve_profile_snapshot` will silently record `age_band_resolved: null` rather than erroring. Acceptable given rules.md's "don't add unnecessary code," but worth a comment for anyone touching this later.

The deterministic-replay/agreement evaluation harness (mirroring [§9.4](./FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md#94-module-a-evaluation-measurement-agreement)'s SLS approach), deferred at Stages 1-4, is now built — see Stage 7 below.

### Phase 3E — Stage 5: frontend live-feedback config sync (2026-07-12)

**Goal:** the live heel-lift/calibration UI (`wbltGeometry.ts`'s `createWbltLiveTracker`) was reading hardcoded `moduleAThresholds.ts` constants instead of the already-fetched `GET /api/wblt/config` response — cosmetic drift risk if `backend/app/module_a/wblt/config.py`'s heel-lift tuning is ever tweaked without a matching frontend edit. Distance/seed bands were never duplicated client-side (already fetched live), so this closes the one remaining hand-synced gap.

- [x] `createWbltLiveTracker(leg, heelLiftConfig?)` now takes an optional `WbltHeelLiftConfig` (`heelBaselineFrames`/`heelLiftTolRatio`/`heelLiftHysteresisRatio`); defaults to the `moduleAThresholds.ts` constants only as a fallback for the brief window before `GET /config` resolves.
- [x] `WbltLiveSessionPage.tsx` stores the fetched config's heel-lift fields in a ref (set alongside the existing `leg_order`/`attempts_per_leg` config effect) and passes it into `createWbltLiveTracker` in `startRecording()`, so every attempt after the first config fetch uses the backend's live values.
- [x] Removed `WBLT_CALIBRATION_SEC`, `WBLT_MIN_VALID_FRAMES_PER_ATTEMPT`, `WBLT_Q_MIN` from `moduleAThresholds.ts` — confirmed zero callers via grep; these were placeholder constants never wired to anything.
- [x] Verified: frontend `tsc --noEmit` clean, production build clean, and a live WBLT session (webcam + real backend) exercised the heel-lift indicator/angle gauge unchanged in behavior (defaults match the backend config values exactly, so no visible regression — the change is only in _where_ the numbers come from).

### Phase 3E — Stage 6: trend summary with MDC suppression (2026-07-12)

**Goal:** per blueprint §11 — compare the current session's per-leg distance + band to the account's WBLT history, suppressing changes smaller than the published MDC (Powden et al. 2015: distance MDC ~1.0-1.5cm; `angle_mdc_deg` mirrors the same principle for the secondary angle signal) so a sub-measurement-error fluctuation never reads as a real improvement or decline.

- [x] `analysis.compute_trend(current_legs, previous_legs)` — pure function, per leg: `distance_delta_cm`/`angle_delta_deg` plus `_meaningful` flags gated on `distance_mdc_cm`/`angle_mdc_deg` from `WBLT_CONFIG`, and the previous session's band for context. Returns `None` for a leg with no previous session or a floor-flagged/incomplete leg on either side — nothing honest to compare.
- [x] `crud.get_previous_wblt_legs()` — reuses the existing generic `core.crud.list_history()` (already used by SLS/STS) filtered to `weight_bearing_lunge_test`, walking back until it finds the most recent OTHER session with `captured_at` stamped (i.e. actually completed, not abandoned mid-test).
- [x] `GET /api/wblt/session/{id}` now also returns `trend: {right, left}`; `WbltSessionSummaryResponse` extended with a new `WbltLegTrend` schema.
- [x] 5 new backend tests (`WbltTrendTests`): no-previous-session, above-MDC change flagged meaningful, sub-MDC change suppressed, floor-flagged leg has no trend, legs are independent (one leg can have a previous session while the other doesn't). Full suite: 81 tests passing.
- [x] Frontend: `Report.tsx` fetches `wbltApi.session()` alongside the existing `moduleAService.get()` call when `exercise_type` is WBLT (trend isn't part of the persisted `metrics_json` — it's computed live against the account's history — so it can't come from the generic module-a read) and renders a one-line "vs last session" summary per leg, honoring the same suppression the backend already computed. New i18n keys (`trendVsLast`/`trendNoPrevious`/`trendDistanceChanged`/`trendDistanceNoChange`/`trendAngleChanged`/`trendAngleNoChange`) added to en/zh/ms.
- [x] **Verified live end-to-end** against the real backend + Postgres (not just unit tests): ran two sequential real WBLT sessions for one account via scripted HTTP calls through the actual `/api/wblt/analyze` → `/api/wblt/session/{id}` flow. Session 1 correctly showed `trend: {right: None, left: None}` (no history yet). Session 2 showed `right: {distance_delta_cm: 3.0, distance_meaningful: true, angle_delta_deg: 19.65, angle_meaningful: true}` (both changes deliberately set above MDC) and `left: {distance_delta_cm: 0.3, distance_meaningful: false, angle_delta_deg: 0.0, angle_meaningful: false}` (both changes deliberately set below MDC) — confirming the suppression logic is correctly wired through the real database, not just exercised in isolation.

**Deliberately out of scope:** the Dashboard's global score-trend chart (`dash.placeholderScoring`) is a separate, pre-existing piece of cross-cutting tech debt affecting every exercise (see the SLS Stage 6 note above) — this WBLT-specific per-session trend row is intentionally narrower in scope and doesn't touch that placeholder.

### Phase 3E — Stage 7: evaluation hooks (2026-07-13)

**Goal:** per blueprint §12 — prove deterministic replay (same stored frames → identical official result) and add a measurement-agreement evaluation harness (ICC, Bland-Altman, Cohen's kappa), mirroring the SLS Stage 7 precedent. This closes out the WBLT blueprint entirely.

- [x] **Shared statistics module**: moved `app/module_a/sls/evaluation/agreement.py` → `app/module_a/core/evaluation/agreement.py` (ICC(2,1), Bland-Altman, Cohen's kappa are unit-agnostic pure-Python formulas, genuinely reused by both SLS and WBLT — duplicating them per-exercise would violate DRY for no benefit). Generified the Bland-Altman output keys from `_sec`-suffixed (`bias_sec`, `sd_sec`, `loa_lower_sec`, `loa_upper_sec`) to unit-agnostic (`bias`, `sd`, `loa_lower`, `loa_upper`) since WBLT's units are cm/deg, not seconds — callers now label the unit in their own report text. Updated `run_sls_evaluation.py`'s two call sites and `test_module_a_evaluation.py`'s key assertions to match; re-ran the SLS evaluation script to confirm byte-identical numeric output after the move (ICC=0.995, kappa=0.857, bias=-0.753 — unchanged from the Phase 3B Stage 7 report).
- [x] `replay_wblt_session.py` — replays one attempt's stored (`--session-id`, reads `module_a_landmark_log`) or offline JSON (`--json-file`) frames through a fresh `analysis.analyze_attempt()` call and asserts the re-run is byte-identical to a second immediate re-run (a live in-script determinism check, not just "trust the DB"). Documented caveat: `module_a_landmark_log` has no per-attempt id (frame_index restarts at 0 per POST), so `--session-id` replay loads the most-recently-written attempt for that session; replaying an earlier specific attempt needs `--json-file` with frames saved at capture time.
- [x] `generate_wblt_replay_corpus.py` — 10 synthetic per-attempt samples (fixed seed `20260713`, committed to `app/module_a/replay_corpus/wblt/`): 9 valid touches spanning Poor/Fair/Good across both legs against a fixed `30-39_male` profile, plus one deliberate heel-lift-invalid case. Each sample carries a simulated independent "manual" (repeat tape) distance reading — intended distance + Gaussian noise (SD 0.4cm, comparable to Powden et al. 2015's reported ~1.0-1.5cm distance MDC) — since WBLT's official distance is self-measured, not camera-derived, so the real reliability question is "does the camera-gated `distance_cm` agree with an independent repeat tape reading," not "does the camera measure distance correctly." Sanity-checked by replaying every sample and confirming the resolved band exactly matches each sample's `target_band_hint`.
- [x] `run_wblt_evaluation.py` — replays the corpus, computes: **distance agreement** (ICC(2,1) + Bland-Altman on the 9 valid-touch samples' `distance_cm` vs the simulated manual reading) and **band agreement** (Cohen's kappa on McBride band vs a band independently computed from the manual reading, across all 10 samples including the invalid one — mapped to an `"Invalid"` category). Also adds a secondary **angle-vs-distance corroboration** check: since angle (deg) and distance (cm) are different units, a literal same-scale Bland-Altman has no physical meaning, so this standardizes (z-scores) both signals first and reports the standardized bias/limits purely as a directional "do the two signals move together" check — explicitly documented as NOT a same-unit agreement claim, consistent with the project's rule of never inventing a band the literature doesn't support. Writes `wblt/evaluation/WBLT_EVALUATION_REPORT.md`. Results (reproducible, fixed-seed corpus): **ICC(2,1) = 0.9771**, **Bland-Altman bias = -0.228cm**, **95% LoA = [-1.135cm, 0.678cm]**, **Cohen's kappa = 0.7143** (2/10 band disagreements: the deliberate heel-lift-invalid case, explained as the camera's validity gate correctly rejecting what a tape-only method would have accepted; and one genuine boundary case where the simulated tape noise crossed a McBride cutoff, explained as expected given the noise SD is comparable to the published MDC — both called out explicitly in the report as documented edge cases, not bugs, mirroring the SLS Stage 7 report's own single documented disagreement).
- [x] 2 new backend tests (`WbltDeterminismTests`): same frames → identical result, for both a valid-touch attempt and a heel-lift-invalid attempt. Full suite: 83 tests passing.
- [x] **Verified live end-to-end** against the real backend + Postgres: created a real session via scripted HTTP calls, posted one real `/api/wblt/analyze` attempt, then ran `replay_wblt_session.py --session-id <id>` against the live `module_a_landmark_log` table — the DB-backed replay reproduced `theta_peak_deg=26.35`, `distance_cm=10.0`, `band=Good`, `q=1.0`, exactly matching the live POST response. This is the real Stage 7 gate ("replay reproduces official results") proven against the actual database, not just the synthetic corpus.

**This closes the WBLT blueprint (Stages 0-7 all complete).** Remaining ideas noted along the way (Dashboard global trend chart, per-exercise trend/evaluation UI polish) are pre-existing cross-cutting tech debt shared by every exercise, not WBLT-specific gaps.

---

## Locked Assumptions (Phases 4–7)

> Locked by HY on 2026-07-15 — if any of these is found to be wrong during implementation, stop and re-plan rather than silently working around it:
>
> 1. **Label design = Option A.** Train binary (Good/Poor) on REHAB24-6; derive **Fair** from a calibrated low-confidence margin. Option B is documented, not built (see Phase 5 Stage 5.10).
> 2. **Squat first, fully verified, before lunge starts.** Lunge is committed scope, not optional — see Phase 5B.
> 3. **Side (sagittal) view only.** Frontal knee valgus is **dropped from the taxonomy** and written up as a monocular limitation. No valgus feature, no valgus tag, no valgus rule.
> 4. `ml/` is a new third top-level folder. Model artifacts **are committed** (examiner reproducibility).
> 5. Module B uses a **registry + plugin** router (Phase 4 Stage 4.1) — this is _not_ Module A's rejected `if exercise_type ==` dispatcher; rationale in that stage.
> 6. LLM default = **Groq / Llama 3.3 70B**, template fallback is the deterministic base layer.
> 7. Phase 7 fixes the trend/band panels for **all** exercises (Module A + B), killing `dash.placeholderScoring`.
> 8. Module B gets a **deterministic replay harness** mirroring Module A's Stage 7 precedent, _in addition to_ the classifier metrics Phase 5 Stage 5.7 requires.
> 9. **Supported languages are en/zh/ms only** (resolved 2026-07-16, corrects earlier "en/zh/ms/hi" wording found in this file). `frontend/src/i18n/index.ts` registers exactly these three; there is no `hi.ts` anywhere in this codebase. Do not add Hindi unless HY explicitly asks for it as new scope.

---

## Cross-Cutting Rules (Phases 4–7)

These bind every stage in Phases 4–7. A stage that violates one is not done.

| #      | Rule                                                                                                                                                                                                                                                                                                | Why                                                                                                              |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **X1** | **Runtime feature parity is enforced by construction, not by discipline.** The offline extractor in `ml/` **imports** the feature functions from `backend/app/module_b/` — it never re-implements them. If a feature can't be computed live per-rep from streamed world landmarks, it cannot exist. | Hard constraint (Phase 4 Stage 4.4). Hand-synced duplicates already burned this project once (Phase 3E Stage 5). |
| **X2** | **No threshold without a tag.** Every constant in a `config.py` carries an inline comment tagged `[clinical norm, S1]`, `[dataset-derived]`, or `[proposed heuristic]`. No untagged number.                                                                                                         | The invented-cutoff trap. Source integrity is graded.                                                            |
| **X3** | **World landmarks only** (3D, metric, scale-invariant), post-preprocessing (confidence filter → gap fill → One Euro → normalisation). Never raw pixels, never image landmarks.                                                                                                                      | Matches Module A precedent.                                                                                      |
| **X4** | **No raw video persisted.** Only metrics + feature vectors in JSONB.                                                                                                                                                                                                                                | Per rules.md #2 and the architecture doc.                                                                        |
| **X5** | **The LLM never changes the grade.** It receives structured output and returns prose. A test asserts the grade before and after the rewrite is byte-identical.                                                                                                                                      | Per rules.md #12.                                                                                                |
| **X6** | **Non-diagnostic language everywhere.** Extend the existing `backend/tests/test_frontend_disclaimers.py` forbidden-phrase scan to cover new Module B i18n keys **and** LLM output templates.                                                                                                        | Existing precedent (rules.md #3, #19).                                                                           |
| **X7** | **Config-driven, never inline.** Thresholds live in `config.py` and are served to the frontend via `GET /config`. The frontend's local constants are a _fallback for the pre-fetch window only_.                                                                                                    | Phase 3E Stage 5's exact lesson.                                                                                 |
| **X8** | **Determinism.** Same input frames → byte-identical output. No wall-clock, no unseeded RNG, no dict-iteration-order dependence in analysis code.                                                                                                                                                    | Phase 3E Stage 7 precedent.                                                                                      |

---

## Phase 4: Module B Skeleton — Squat, Placeholder Model

**Goal:** a complete, honest Module B vertical slice for **squat** that runs end-to-end with a **stub** model, so the real Extra Trees model in Phase 5 is a drop-in replacement and nothing else has to move.

**Why placeholder-first:** the fusion, banding, persistence, report, and UI surface are all independent of whether the ML score came from a stub or a trained model. Building them first means Phase 5 is purely a data/ML problem, not a plumbing problem.

### Stage 4.0 — Decision & config freeze _(no code yet)_

- [x] Create `docs/module_b_decisions.md` recording: Option A (with Option B named as the documented alternative), squat-first, **side-only + valgus dropped**, registry pattern, Groq default, artifacts committed. Each entry: decision, rationale, what would reverse it.
- [x] Create `backend/app/module_b/core/config.py` with `MODULE_B_CORE_CONFIG`:
  - `band_thresholds`: Poor `0 ≤ S < 4.0`, Fair `4.0 ≤ S < 7.0`, Good `7.0 ≤ S ≤ 10.0` — **[fixed by D6 / proposal Table 6]**
  - `w_rule_default = 0.4`, `w_ml_default = 0.6` — **[proposed heuristic, R7 — to be replaced by Phase 5.6's sweep result]**
  - `w_rule_low_confidence = 0.7` — **[proposed heuristic, R7]**
  - `confidence_low_threshold = 0.65` — **[proposed heuristic, R7 — pilot-tune; HY 2026-07-16]**. Option A has only Good/Poor probabilities, so a binary confidence threshold must be strictly above 0.5 to be reachable.
  - `q_min` capture-quality gate + `confidence_threshold = 0.6`, `Q` bands (≥0.85 good / 0.70–0.85 moderate / <0.70 poor) — **[proposal §3.3.1, Tables 3 & 4]**
  - `feature_schema_version = "1.0.0"`, `interpolation_max_gap_frames = 5` — **[proposal §3.3.2]**
- [x] **Gate:** every constant has an X2 tag. Reject the stage otherwise.

### Phase 4 — Stage 4.0: Decision & config freeze (2026-07-16)

- [x] Added `docs/module_b_decisions.md` with the required decision/rationale/reversal records for Option A, squat-first scope, side-only capture with valgus omitted, registry routing, Groq default, and committed artifacts.
- [x] Added `backend/app/module_b/core/config.py` with frozen Phase 4 defaults: D6 score bands, `w_rule_default = 0.4`, `w_ml_default = 0.6`, `w_rule_low_confidence = 0.7`, `confidence_low_threshold = 0.65`, `q_min = 0.6`, `confidence_threshold = 0.6`, Q bands, `feature_schema_version = "1.0.0"`, and `interpolation_max_gap_frames = 5`.
- [x] X2 provenance tags were recorded inline beside the constants as proposed heuristics, dataset-derived values, or clinical/proposal references as applicable.
- [x] Verification: `cd backend && .venv/bin/python -m unittest discover -s tests -v` passed 96 tests.

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)): `w_rule_default = 0.4`/`w_ml_default = 0.6` above **stays as the Phase 4 starting point**, conflicting with the architecture doc's §10.4 "Recommended initial weights" (`w_rule = 0.6`/`w_ml = 0.4`) only until Stage 5.6 runs. HY's decision: the final weight is not asserted from either document — it's **earned empirically** by Stage 5.6's sweep, selected against **macro-F1 and the severe-misclassification rate** (Poor↔Good confusions), not precision alone. See Stage 5.6 below for the updated selection criteria.

### Stage 4.1 — Backend package + exercise registry

**Architecture decision (read before writing code).** Module A learned that a shared `if exercise_type == ...` dispatcher was wrong — but its _other_ extreme (fully duplicated `sls/router.py` + `wblt/router.py`) duplicated real logic. Module B's situation is different: one shared preprocessing + feature pipeline with one model per exercise is required. So the correct shape is neither: **one thin router + a registry of exercise plugins.**

```
backend/app/module_b/
├── core/
│   ├── config.py            # MODULE_B_CORE_CONFIG (Stage 4.0)
│   ├── schemas.py           # shared Pydantic request/response
│   ├── exercise.py          # ModuleBExercise ABC/Protocol  <-- the contract
│   ├── registry.py          # {code: ModuleBExercise}; get_exercise(code) or 404
│   ├── geometry.py          # angle helpers (import from module_a/core/geometry where identical — DRY)
│   ├── fsm.py               # generic hysteresis rep FSM + refractory (parameterised)
│   ├── features.py          # FeatureVector + shared extractors  <-- X1 contract surface
│   ├── rules.py             # SubScore dataclass + fusion-input assembly
│   ├── fusion.py            # S_final = w_r*S_rule + w_m*S_ml, adaptive weights, banding
│   ├── model_registry.py    # loads joblib + feature schema + version id; StubModel for Phase 4
│   ├── quality.py           # reuse module_a/core/quality (import, don't fork)
│   ├── crud.py              # generic save/read of module_b results (hybrid schema — see Stage 4.6)
│   ├── router.py            # generic /api/module-b/* endpoints (Stage 4.1 resolution) — THIN
│   └── evaluation/          # Phase 5.7 + replay harness
├── squat/
│   ├── config.py            # SQUAT_CONFIG
│   ├── features.py          # squat-specific feature assembly
│   ├── rules.py             # squat ROM/Tempo/Stability
│   ├── segmentation.py      # squat FSM params + lead-in
│   └── exercise.py          # SquatExercise(ModuleBExercise) — registered
└── lunge/                   # Phase 5B ONLY. Do not scaffold now.
```

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)): follow the architecture doc's §14.6 generic endpoint shape — `POST /api/module-b/analyze`, `GET /api/module-b/results/{session_id}` — not per-exercise-code URL segments. The routing logic still follows **how Module A actually built its generic endpoint**: `core/router.py` stays a thin dispatcher that reads `exercise_code` out of the request body/path param and looks it up in `core/registry.py` (`get_exercise(code)` → 404 on unknown), exactly like `module_a/core/router.py` does for STS today. The one addition beyond §14.6 is `GET /api/module-b/{code}/config`, which is genuinely new work the architecture doc didn't anticipate — justified the same way Module A's `GET /api/wblt/config` was added beyond the original §14.5 plan, for the same reason (X7: frontend threshold sync can't happen without a config endpoint to sync from).

- [x] `core/exercise.py` — `ModuleBExercise` abstract base with: `code`, `config`, `required_view`, `segment(frames) -> list[Rep]`, `extract_features(rep) -> FeatureVector`, `rule_subscores(rep, features) -> RuleScores`, `model_key` (which artifact to load), `error_tags(features, rules, ml) -> list[str]`.
- [x] `core/registry.py` — dict of code → instance. `get_exercise("squat")`. Unknown code → 404, never a silent default.
- [x] `core/router.py` — endpoints, all delegating to the registry, **zero exercise-specific branching**:
  - `GET  /api/module-b/{code}/config` — serves thresholds to the frontend (X7); the one addition beyond §14.6, see resolution note above
  - `POST /api/module-b/analyze` — generic per §14.6; body carries `exercise_code`, buffer-and-send, dispatches via the registry
  - `GET  /api/module-b/results/{session_id}` — generic per §14.6; full session summary
- [x] `squat/exercise.py` — `SquatExercise` registered under `"squat"`.
- [x] Seed the exercise catalog: add `squat` as a **Module B** exercise in the existing catalog seed. **Path note:** `frontend/src/pages/ExerciseSelection.tsx` renders exercises entirely data-driven from `exerciseService.list()` against the backend catalog — it has no hardcoded "Module B placeholder" branch of its own. "Replace the placeholder" therefore means updating the backend catalog seed row (`module_b_placeholder_exercise`, per the architecture doc's exercise catalog table) to a real `squat` row, not editing a component branch. Flagged as a path/assumption clarification, not a blocking contradiction.
- [x] **Gate:** `app.main` imports cleanly; `GET /api/module-b/squat/config` returns the config; `GET /api/module-b/bogus/config` returns 404.

### Phase 4 — Stage 4.1: Backend package + exercise registry (2026-07-16)

- [x] Added the Module B backend package skeleton with a thin shared router, an explicit registry, and `SquatExercise` registered under `"squat"`.
- [x] Added `GET /api/module-b/{code}/config`, `POST /api/module-b/analyze`, and `GET /api/module-b/results/{session_id}` in `core/router.py`; the latter two resolve via the registry and intentionally return 501 until Stages 4.2-4.6 provide segmentation, feature extraction, rules, fusion, and persistence.
- [x] Updated the backend exercise catalog seed from the old `module_b_placeholder_exercise` entry to a real Module B `squat` catalog row, while deactivating any legacy placeholder rows if encountered during seeding.
- [x] Verification: `cd backend && .venv/bin/python -c "import app.main; print('import ok')"` passed; `cd backend && .venv/bin/python -m unittest tests.test_module_b_registry -v` passed 7 tests; full backend unittest discovery passed 96 tests.

### Stage 4.2 — Feature extraction schema _(the X1 contract — most important stage in Phase 4)_

This is the single artifact both the live backend and the offline `ml/` extractor consume. Get it wrong and Phase 5 trains on features the runtime can't reproduce.

- [x] `core/features.py` — define `FeatureVector` as an **ordered, versioned, named** structure (`schema_version`, `names: tuple[str, ...]`, `values: tuple[float, ...]`). Order is part of the contract; a joblib model trained on order N must refuse a vector of order M.
- [x] Implement per-rep features, side-view-computable only:

| Feature                | Definition                                                         | Landmarks (world)   | Tag                                       |
| ---------------------- | ------------------------------------------------------------------ | ------------------- | ----------------------------------------- |
| `knee_flex_peak_deg`   | max angle hip–knee–ankle in rep                                    | 23/24, 25/26, 27/28 | [clinical norm basis, S1]                 |
| `knee_flex_min_deg`    | min over rep                                                       | same                | —                                         |
| `knee_rom_deg`         | max − min                                                          | same                | [S1]                                      |
| `hip_flex_peak_deg`    | angle shoulder–hip–knee                                            | 11/12, 23/24, 25/26 | [S3]                                      |
| `trunk_lean_peak_deg`  | shoulder-mid→hip-mid vector vs world vertical                      | 11+12, 23+24        | [S4][S8]                                  |
| `trunk_lean_mean_deg`  | mean over rep                                                      | same                | —                                         |
| `knee_ang_vel_max_dps` | max                                                                | d(knee angle)/dt    |                                           |
| `rep_duration_s`       | FSM boundaries                                                     | —                   | —                                         |
| `descent_ascent_ratio` | time DESCENDING / time ASCENDING                                   | —                   | [proposed heuristic]                      |
| `symmetry_index_pct`   | `                                                                  | θ_L − θ_R           | / (0.5·(θ_L+θ_R)) × 100` at matched phase |
| `ankle_df_proxy_deg`   | shank-vs-vertical                                                  | 25/26, 27/28        | [partial — monocular caveat]              |
| `hip_mid_jitter_norm`  | smoothed frame-to-frame in-plane hip-mid displacement / `norm_ref` | 23+24               | [proposed heuristic, R6]                  |
| `stance_width_norm`    | inter-ankle distance / `norm_ref`                                  | 27/28               | [dataset-derived, R10 "feet too wide"]    |

- [x] **Explicitly NOT implemented:** `knee_valgus_proxy`. Add a comment in `features.py` naming the omission and pointing to the limitations write-up (see [Deliberately Not Built](#deliberately-not-built-phases-47)). Do not leave a dead stub.
- [x] `norm_ref` — implement **both** candidates from R5.3 (`trunk_length` = hip-mid→shoulder-mid, `thigh_length` = hip→knee) behind a config switch. **Phase 5.4 picks the winner empirically** (lower cross-subject variance). Default `thigh_length` — **[proposed heuristic, R5.3]**.
- [x] Every feature is a **pure function** of one rep's frames (X8) — no clip-level hindsight (X1).
- [x] **Tests:** hand-computed fixtures for each angle; a synthetic deep-squat rep and a shallow rep produce the expected ordering of `knee_flex_peak_deg`.
- [x] **Gate:** `FeatureVector.names` is stable and asserted in a test. Changing it requires bumping `feature_schema_version`.

### Phase 4 — Stage 4.2: Feature extraction schema (2026-07-16)

- [x] Added the frozen `FeatureVector` contract in `backend/app/module_b/core/features.py`: schema version, unique ordered names, and finite values are validated before a vector can reach a model.
- [x] Added pure shared geometry helpers and the squat per-rep extractor in `backend/app/module_b/core/geometry.py` and `backend/app/module_b/squat/features.py`. The extractor exposes the 13 agreed side-view features in `SQUAT_FEATURE_NAMES` order; it deliberately omits frontal-plane knee valgus.
- [x] Added `norm_ref_strategy` to `SQUAT_CONFIG`, defaulting to `thigh_length`, while retaining the `trunk_length` alternative for the Stage 5.4 empirical selection.
- [x] Wired `SquatExercise.extract_features()` to the shared extractor. Stage 4.3's future `Rep` only needs to expose `frames`; no FSM or segmentation behavior was added early.
- [x] Verification: `cd backend && .venv/bin/python -m unittest tests.test_module_b_features tests.test_module_b_registry -v` passed 13 tests; complete backend discovery passed 102 tests.

### Stage 4.3 — Rep segmentation (squat FSM)

Reuse Module A's hysteresis-FSM-with-refractory house style (`sls/fsm.py` is the reference).

- [x] `core/fsm.py` — generic, parameterised: `enter_threshold`, `exit_threshold`, `refractory_s`, `min_rep_duration_s`, state enum. Exercise-agnostic.
- [x] `squat/segmentation.py` — `STANDING → DESCENDING → BOTTOM → ASCENDING → STANDING`, driven by knee-flexion angle. Config:
  - `enter_descending_deg = 30.0` (from standing baseline) — **[proposed heuristic, R9]**
  - `exit_standing_deg = 20.0` (hysteresis — deliberately ≠ enter) — **[proposed heuristic, R9]**
  - `refractory_s = 0.5` — **[proposed heuristic, R9]**
- [x] BOTTOM = local max flexion within the rep, not a fixed threshold.
- [x] **Tests:** clean 5-rep synthetic stream → exactly 5 reps; jitter at the threshold → still 5 (no phantom reps); a partial descent that never crosses → 0 reps.
- [x] **Gate:** determinism — same frames twice → identical rep boundaries.

### Phase 4 — Stage 4.3: Rep segmentation (squat FSM) (2026-07-16)

- [x] Added `backend/app/module_b/core/fsm.py`: an exercise-agnostic rising-signal hysteresis collector with explicit `READY`/`ACTIVE`/`REFRACTORY` states, duration filtering, refractory handling, and immutable `Rep` boundaries.
- [x] Added `backend/app/module_b/squat/segmentation.py` and wired `SquatExercise.segment()`. It derives bilateral mean knee flexion, tracks `STANDING → DESCENDING → BOTTOM → ASCENDING → STANDING`, and records the bottom as the completed rep's local maximum flexion frame.
- [x] Added tagged squat segmentation config: 30° entry, 20° exit, 0.5 s refractory, and a 0.5 s minimum-duration noise filter (the latter is a documented R9 heuristic required by the generic FSM contract).
- [x] Verification: `cd backend && .venv/bin/python -m unittest tests.test_module_b_features tests.test_module_b_registry tests.test_module_b_segmentation -v` passed 18 focused Module B tests; complete backend unittest discovery passed 107 tests.

### Stage 4.4 — Rule sub-scores (squat)

Three sub-scores, each **0–10**. Live in `squat/rules.py`, config in `squat/config.py`.

- [x] **Completeness (ROM)** — piecewise on `knee_flex_peak_deg`. Band **edges are [clinical norm, S1]**; the 0–10 interpolation _inside_ each band is **[proposed heuristic — pilot-tune]**:
  - `< 60°` → 0–2 · `60–90°` (shallow) → 2–5 · `90–110°` (parallel) → 5–8 · `≥ 110°` (deep) → 8–10
  - **Must implement R3's caveat:** limited ankle DF can physically cap achievable depth. When `ankle_df_proxy_deg` indicates a DF limit, the ROM sub-score is **floor-limited, not zeroed**, and a `rom_possibly_df_limited` note is attached. Do **not** punish a mobility limit as if it were a control fault.
- [x] **Consistency (Tempo)** — `CV = std(rep_durations)/mean(rep_durations)` across the set. `CV ≤ 0.10` → 9–10 · `0.10–0.25` → 5–8 · `> 0.25` → < 5. **[proposed heuristic, R6]** Deliberately **not** an absolute speed target (no sourced tempo norm exists — see [Open Questions](#open-questions-phases-47) Q5). **Only computable from rep 2 onward** — with 1 rep, tempo is `None`, not `0`. Handle this explicitly in fusion (renormalise over available sub-scores).
- [x] **Control (Stability)** — `Stability = f(1 − normalised_jitter)`, **duration-weighted**. **[proposed heuristic, R6]**
  - **The perverse-incentive check is mandatory here.** Write a test proving a _long, well-controlled_ rep scores **≥** a _brief still moment_. This is the exact trap caught in the SLS work (proportion-only stability rewarded short perfect holds). If the formula fails that test, the formula is wrong — do not ship it and adjust the test.
  - In-plane only. No depth-axis sway (monocular).
- [x] `S_rule` = mean of available sub-scores (equal weights) — **[proposed heuristic]**. Record each sub-score individually; the report shows the breakdown.
- [x] **Tests:** each sub-score's band boundaries; the DF-limit floor; the duration-weighting anti-trap test; tempo `None` on a 1-rep set.

### Phase 4 — Stage 4.4: Rule sub-scores (squat) (2026-07-16)

- [x] Added `backend/app/module_b/core/rules.py` with validated named `SubScore` values, `RuleScores`, and equal-weight aggregation over available components.
- [x] Added `backend/app/module_b/squat/rules.py` with per-rep ROM/stability scoring and set-level ROM/tempo/stability assembly. `SquatExercise.rule_subscores()` now returns the per-rep breakdown; `score_squat_set()` supplies the set-level tempo component needed by the later pipeline.
- [x] Added tagged rule configuration for ROM interpolation, the possible DF-limit floor, tempo CV bands, and duration-aware in-plane stability. The stability formula gives full credit only after sustained control, avoiding the short-stillness incentive.
- [x] Verification: `cd backend && .venv/bin/python -m unittest tests.test_module_b_features tests.test_module_b_registry tests.test_module_b_segmentation tests.test_module_b_rules -v` passed 26 focused Module B tests; complete backend unittest discovery passed 115 tests.

### Stage 4.5 — Fusion + placeholder ML interface

- [x] `core/model_registry.py`:
  - `ModelBundle` protocol: `predict_proba(FeatureVector) -> dict[str, float]`, `feature_schema_version`, `model_version`, `label_order`.
  - `StubModel(ModelBundle)` — returns a **deterministic** proba derived from the rule score (e.g. `P(Good) = clamp(S_rule/10)`), so the Phase 4 slice produces sensible-looking output without pretending to be a model.
  - `**StubModel` must announce itself.** Every response carries `model_version: "stub-0"` and the report renders a visible "placeholder model" notice. A stub that looks like a real result is a lie to your own testing.
  - **Schema guard:** loading a bundle whose `feature_schema_version` ≠ the runtime's raises loudly. Never silently score a mismatched vector.
- [x] `core/fusion.py`:
  - `S_ml` projection (Option A): `S_ml = 10·P(Good) + 0·P(Poor)`. **Fair is not an ML class** — it comes from the margin (below). **[R7]**
  - **Fair rule (Option A):** if calibrated `max(P) < confidence_low_threshold` → surface **Fair** and raise `low_confidence` flag, regardless of which side of the boundary S_final lands.
  - Adaptive weights: confident → `w_r=0.4/w_m=0.6`; low-confidence **or** `Q < q_min` → `w_r=0.7`.
  - `S_final = w_r·S_rule + w_m·S_ml` → band via `MODULE_B_CORE_CONFIG.band_thresholds`.
  - **Assert** both inputs are on 0–10 before fusing (R7 explicitly asks for this check).
- [x] **Capture-quality gate:** mirror WBLT Stage 3's lesson — a `Q < q_min` set does **not** silently produce a confident band. Surface Fair + `retry_camera_placement`, lean rule-heavy.
- [x] **Tests:** the D6 band boundaries exactly (3.999→Poor, 4.0→Fair, 6.999→Fair, 7.0→Good); low-confidence forces Fair; low-Q shifts weights; schema-mismatch raises.

### Phase 4 — Stage 4.5: Fusion + placeholder ML interface (2026-07-16)

- [x] Added `backend/app/module_b/core/model_registry.py` with the versioned `ModelBundle` contract, a deterministic `StubModel` (`model_version = "stub-0"`, explicit placeholder flag), an order-aware joblib adapter, and loud schema-version validation.
- [x] Added `backend/app/module_b/core/fusion.py`: Option A's binary probability projection, 0–10 input assertions, D6 banding, adaptive rule-heavy weights, low-confidence Fair override, and low-Q Fair/retry override. Fusion output carries the model version and placeholder notice for Stage 4.6 persistence and Stage 4.7 report rendering.
- [x] Updated `confidence_low_threshold` to `0.65` after identifying that binary Good/Poor probabilities make a `< 0.5` confidence gate unreachable. This remains a tagged Phase 4 heuristic.
- [x] Verification: `cd backend && .venv/bin/python -m unittest tests.test_module_b_features tests.test_module_b_registry tests.test_module_b_segmentation tests.test_module_b_rules tests.test_module_b_fusion -v` passed 33 focused Module B tests; complete backend unittest discovery passed 122 tests.

### Stage 4.6 — Persistence + read-back

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)): neither the architecture doc's all-flat schema nor this stage's original all-JSONB schema — a **hybrid**. Flat typed columns for small, fixed-shape, exercise-agnostic fields that Phase 7's dashboard queries directly (mirrors the `sessions.score`/`sessions.band` precedent already in this repo); a separate child table for `error_tags` (needs cross-session `GROUP BY tag_code` aggregation for Phase 7 Stage 7.1's "common error tags" panel — JSONB makes that query awkward); JSONB only for what's genuinely variable-shape across exercises/versions.

- [x] Alembic migration: `module_b_results` with:
  - **Flat typed columns:** `session_id`, `exercise_code`, `score`, `band`, `confidence`, `model_version`, `feature_schema_version`, `q`, `created_at` — indexed by user + timestamp, reused directly by Phase 7's trend/dashboard queries.
  - **Separate** `module_b_error_tags` **table:** `session_id` FK, `tag`, `severity`, `source` (`"rule"` / `"ml"` / `"system"`) — one row per tag, enabling cross-session tag aggregation.
  - **JSONB** `metrics_json`**:** `feature_vector` (needed for the replay harness), rule sub-score breakdown, `w_rule`/`w_ml` actually used, per-rep summaries — the part whose shape genuinely differs between squat, lunge, and future exercises.
- [x] Persist: **final score, band, rule sub-score breakdown, confidence value, predicted error tags with severity, and (Phase 6) the rewritten coaching text.**
- [x] **Profile/version snapshot** — mirror WBLT Stage 4's lesson: store the `model_version` and weights a grade was **actually computed with**, so re-deriving a historical session later can't silently rewrite it.
- [x] `GET /api/module-b/results/{session_id}` returns the full summary (endpoint name per Stage 4.1's resolution).
- [x] **Gate:** two successive GETs return byte-identical payloads.

### Phase 4 — Stage 4.6: Persistence + read-back (2026-07-16)

- [x] Added Alembic revision `20260716_0008_module_b_hybrid_results.py`, replacing the legacy all-flat Module B fields with the hybrid result summary and `metrics_json`; renamed `error_tags` to session-owned `module_b_error_tags` with source-aware rows. The migration preserves legacy values as `legacy-unversioned` snapshots.
- [x] Reworked `ModuleBResult`/`ModuleBErrorTag` ORM mappings and added `core/crud.py` for upserted result snapshots, stable tag ordering, and deterministic read-back. Raw browser frames/video are not persisted; only feature vectors and derived per-rep summaries are stored.
- [x] Activated the generic analysis endpoint: registry plugin → segmentation → feature extraction → set rules → transparent stub fusion → hybrid persistence. `GET /api/module-b/results/{session_id}` now returns the stored snapshot rather than recomputing it.
- [x] System confidence/capture tags are persisted with severity/source now. Movement-specific tags are intentionally not invented here; Stage 6.1's squat taxonomy will populate the same generic table.
- [x] Verification: `PYTHONPATH=backend backend/.venv/bin/alembic -c alembic.ini upgrade head --sql` reached revision `20260716_0008`; persistence tests cover bilateral Q, derived-only storage, and byte-stable read-back. Focused Module B tests passed (36 tests) and complete backend unittest discovery passed (125 tests).

### Stage 4.7 — Frontend (squat)

> **Design note (HY 2026-07-16):** this is not a new UI design. Squat's live-session layout, components, and styling **reuse Module A's existing live-session pages as-is** (`StsLiveSessionPage`/`SlsLiveSessionPage` — rep-based, not WBLT's attempt/bracket-based flow, since squat has no discrete attempts). No new visual design work, no new component patterns. The only changes are **wording/copy** — e.g. Module A's rep-based pages say "reps"/"session" already, so most terminology carries over directly; where a Module B string doesn't fit an existing Module A key as-is (e.g. any leftover "attempt"-style copy inherited from a WBLT-flavoured pattern), reword it to session/rep language rather than introducing a new term. Treat this stage as a copy/wiring pass over an existing layout, not a redesign — don't invoke a UI design skill or propose new layout choices for it.

- [x] `frontend/src/pages/squat/SquatLiveSessionPage.tsx` — mirrors `SlsLiveSessionPage`'s structure. Route `/squat/live`.
- [x] `frontend/src/utils/squat/squatLiveEstimate.ts` — client-side live rep count + band _estimate_ only. _*Fetches thresholds from* `GET /api/module-b/squat/config`_; local constants are the pre-fetch fallback only (X7 — this is Phase 3E Stage 5's exact lesson, do not repeat it).
- [x] `CameraSetup.tsx` — add a **side-view** branch for squat (guidance text + demo video), matching the existing per-exercise view instruction mechanism.
- [x] `ExerciseSelection.tsx` — no component change needed (see Stage 4.1's path note); update the backend catalog seed's `module_b_placeholder_exercise` row to the real squat entry.
- [x] `Report.tsx` — add an `isModuleB` branch: final score, band, **three sub-scores broken out**, confidence, error tags, capture quality, and the `model_version` placeholder notice. _(Note the Phase 3E Stage 2 lesson: the report's per-exercise renderer has silently rendered the wrong panel before. Add a test.)_
- [x] i18n keys (en/zh/ms — this repo's actual supported languages, see [Locked Assumptions](#locked-assumptions)) for every new string, including error tags via the existing generic `t('moduleB.tag_' + tag)` lookup pattern.
- [x] **Gate:** `tsc --noEmit` clean; production build clean.

> ✅ **Resolved 2026-07-16 (HY decision) — squat's end-of-set UX.** Squat has no clinical rep target (unlike STS's validated 5 reps), so `SquatLiveSessionPage.tsx` is an **unlimited-rep continuous set**: a live client-side rep counter (estimate only), ended manually by a **"Finish Set"** button that posts the whole buffer once to `POST /api/module-b/analyze`. Two additions, both frontend-only / display-only, never sent to grading:
>
> - **Inactivity safety net:** ~9s with no meaningful knee-flexion change after ≥1 rep prompts "No movement detected — finish set now?" (Finish/Continue). Never auto-submits.
> - **Optional motivational rep-goal:** user may pick 10–80 (step 10) before starting, or leave it blank. Shown as "Rep X of Y" + a progress bar. Hitting the goal only prompts "Hit your goal — keep going, or finish?"; it never auto-finishes and is never sent to the backend — a user with a goal of 10 who does 7 is graded identically to a user with no goal who does 7.
>
> **Flagged for Phase 7, not built now:** any future "beat previous session" comparison must pair rep count with quality (e.g. "8 reps, mostly Good vs last time 6, mostly Fair"), never a bare rep count — a bare-count comparison rewards rushing over good form. Also see `FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md` §24 for the corresponding record of this decision.

### Phase 4 — Stage 4.7: Frontend (squat) (2026-07-16)

- [x] `frontend/src/pages/squat/SquatLiveSessionPage.tsx` (route `/squat/live`, registered in `App.tsx`) — unlimited-rep continuous set per the resolved decision above: optional rep-goal picker, live HUD (timer + rep count), inactivity prompt, target-hit prompt, "Finish Set" → `moduleBService.analyze()` → `sessionService.end()` → `/report`.
- [x] `frontend/src/utils/squat/squatLiveEstimate.ts` — client-side hysteresis rep counter (mirrors `HysteresisRepFSM`/`segment_squat_frames`) + a rough per-rep ROM band estimate (mirrors `rom_subscore`'s band shape, without the DF-limit floor). `fetchSquatLiveConfig()` reads `GET /api/module-b/squat/config`; local constants are the pre-fetch fallback only (X7).
- [x] `frontend/src/services/moduleBService.ts` — new generic Module B client (`analyze`, `get`, `config`), mirroring `moduleAService.ts`'s shape against the backend's generic router.
- [x] `CameraSetup.tsx` — added `isSquat` (side-view guidance + `Squat.mp4` demo) and routes `beginSession` to `/squat/live`. Also added a **placeholder-only** `isLungePlaceholder` branch (thumbnail + `Leg Lunge.mp4` demo, Start Session replaced with a "coming soon" message, auto-start disabled) — see the Phase 5B note above; out of this stage's squat-only scope but requested directly by HY alongside the squat assets.
- [x] `ExerciseSelection.tsx` — confirmed no hardcoded placeholder branch (Stage 4.1's path note held). Added `squatImage`/`lungeImage` to `imageFor()` and switched the card-type choice from `mode === "functional"` to "has a real thumbnail" so both new rehab-mode cards reuse the existing image-forward bento card as-is (no new markup/CSS) instead of the icon-only rehab card.
- [x] `backend/app/seed.py` — added the `lunge` placeholder catalog row (`mode: "rehab"`) so its card/thumbnail can render; `squat` row already existed from Stage 4.1.
- [x] `Report.tsx` — added an `isModuleB` branch (`session.exercise_type === "squat"`): restructured the data-loading effect to fetch the session first, then branch to `moduleBService.get()` vs `moduleAService.get()` (the two response shapes are incompatible, so they can no longer be fetched in one unconditional `Promise.all`). Renders final score/band (lowercased from Module B's `Poor/Fair/Good`), the three rule sub-scores plus ML score/confidence/capture-quality-band as sub-score rows, an error-tags panel (`t('moduleB.tag_' + tag)`), and a placeholder-model-notice banner naming `model_version`.
- [x] i18n: added `squat.*` and `moduleB.*` blocks plus new `exercise.*`/`report.*` keys to **en/zh/ms** — this repo's actual supported language set (see [Locked Assumptions](#locked-assumptions) #9); the checklist's "hi" wording above was pre-existing drift, corrected 2026-07-16 rather than newly adding Hindi.
- [x] **Added the frontend test framework** (HY decision, 2026-07-16): this repo had zero frontend test tooling before this stage. Added Vitest + jsdom + React Testing Library (`frontend/package.json`'s `test` script, `vite.config.ts`'s `test` block, `frontend/src/test/setup.ts` for jest-dom matchers + an `IntersectionObserver` stub jsdom lacks for `useReveal.ts`). Added `frontend/src/pages/Report.test.tsx` covering exactly the Phase 3E Stage 2 wrong-panel lesson this stage's checklist called out: a `squat` session renders the Module B panel and never Module A's, and vice versa for a Module A exercise type.
- [x] Verified: `npx tsc --noEmit` clean, `npm run build` clean (538 modules, no errors), `npm run test` — 2/2 passing, ESLint clean on all touched files, Prettier clean, Black/isort clean on `seed.py`. Full backend suite still green: 125/125 (`python -m unittest discover -s tests`).
- [ ] **Left undone:** Stage 4.8's live end-to-end verification (real webcam squat session through to a rendered report) — that is Stage 4.8's own gate, not run as part of this stage.

### Stage 4.8 — Phase 4 verification gate

- [x] Full backend suite green (existing 83 + new).
- [x] `test_frontend_disclaimers.py` extended to the new Module B i18n keys (X6).
- [x] **Verified live end-to-end** against real backend + Postgres — the Module A house standard, not just unit tests: real webcam squat session → reps segmented → sub-scores → stub fusion → persisted row → Report page renders correctly (confirm via rendered page text, not just the API response).
- [x] Record the result in `task.md` in the Phase 3E style (what was verified, with numbers).

### Phase 4 — Stage 4.8: Verification gate (complete, 2026-07-16)

- [x] Extended `backend/tests/test_frontend_disclaimers.py` with a Module B/squat locale-block guard across en/zh/ms, preserving the existing forbidden clinical-claim scan.
- [x] Verified the local PostgreSQL migration at `20260716_0008` and the real authenticated API/persistence path with a generated non-video pose stream: five reps segmented, sub-scores and `stub-0` fusion produced, result persisted, and two API reads were byte-identical (`Good`, 7.17 in this deterministic verification stream).
- [x] Verification: complete backend unittest discovery passed 126 tests.
- [x] Physical-camera/browser verification was completed manually: camera permission and pose overlay worked; the setup view correctly warned at 23% quality when the full body/head/feet were outside the frame; a squat session reached the rendered report with `Good` 7.1/10, ROM 6.6, tempo 4.8, stability 9.9, confidence 71%, `stub-0` notice, non-medical disclaimer, and no error tags. The tester observed occasional false-positive rep counts while walking toward or standing near the device at low capture quality; accepted as a current skeleton-model limitation, not a clinical measurement claim.
- [x] Follow-up report polish: added the missing `common.moderate` locale value in en/zh/ms, so the capture-quality band now renders as human-readable text rather than the raw i18n key. Regression coverage uses the `moderate` value; report tests, TypeScript checking, and the production build pass.

**Deliverable:** Module B works end-to-end for squat with an announced placeholder model. Phase 5 only has to replace `StubModel`.

---

## Phase 5: Dataset and ML Training (Squat)

**Goal:** a trained, calibrated, LOSO-evaluated Extra Trees model for squat, exported with its feature schema and version id, loaded by the backend.

### Stage 5.0 — Data audit **[HARD GATE — no training work until this reports numbers]**

Everything downstream depends on counts nobody has actually looked at yet.

**Downloads — all confirmed present on disk (2026-07-15):**

- [x] `videos` (unzipped, 2.7 GB) — **the labels + rep boundaries**
- [x] `Segmentation.csv` (53.3 kB)
- [x] `Segmentation.txt` (1.7 kB) — **the column dictionary**
- [x] `joints_names.txt` (395 B)
- [x] `3d_joints` (unzipped, 551.3 MB) — mocap GT, for the Stage 5.4 agreement check _(not training — X3)_
- [x] EC3D `data_3D.pickle` — present
- [ ] _Not downloaded, not needed:_ `2d_joints.zip`, `2d_markers.zip`, `3d_markers.zip`

**Tasks:**

- [x] Create `ml/config.yaml` with the dataset root **exactly as below** — paths point at the existing local dataset location; nothing is copied or moved into the repo:
  ```yaml
  dataset_paths:
    rehab246:
      videos_dir: /Users/sumhonyou/fypDataset/videos
      segmentation_csv: /Users/sumhonyou/fypDataset/Segmentation.csv
      segmentation_txt: /Users/sumhonyou/fypDataset/Segmentation.txt
      joints_names_txt: /Users/sumhonyou/fypDataset/joints_names.txt
      joints_3d_dir: /Users/sumhonyou/fypDataset/3d_joints
    ec3d:
      pickle_path: /Users/sumhonyou/fypDataset/data_3D.pickle
  ```
  `ml/config.yaml` itself **is committed** (it's just paths); the directories it points at are **not** — add `/Users/sumhonyou/fypDataset/` patterns to `.gitignore` only if the dataset ever ends up under the repo root (it currently doesn't, so no `.gitignore` change should be needed — confirm the dataset root is genuinely outside the repo tree before skipping this).
- [x] `extract_landmarks.py` and `audit_rehab246.py` filter to `exercise_id ∈ {5, 6}` **in code** (Ex5 = Leg lunge, Ex6 = Squats) — never require the video folder itself to be pre-sorted or pruned. All 65 recordings across all 6 exercises stay exactly where they are; Ex1–Ex4 files are simply never opened.
- [x] Read `Segmentation.txt` and write `ml/docs/rehab24_6_schema.md` — the **authoritative** column dictionary. Do not trust the column names guessed from a screenshot.
- [x] `ml/scripts/audit_rehab246.py` — loads `Segmentation.csv`, filters `exercise_id ∈ {5, 6}` (Ex5 = Leg lunge, Ex6 = Squats), and **reports**:
  - [x] exact rep counts **per exercise × correctness ×** `person_id`
  - [x] the distribution of `cam17_orientation`
  - [x] `mocap_erroneous` count (candidates for exclusion)
  - [x] `exercise_subtype` values for Ex5 (**this is the lead-leg tag** — R5.2/R9 needs it and it is given, not inferred)
  - [x] `lighting` distribution
  - [x] **Per-subject class presence** — the LOSO viability check (R8): does any subject have only one class?
- [x] **The view question (critical, see below).** Determine, from `Segmentation.txt` + a visual check of one clip per orientation value:
  - Which camera yields a **true sagittal/profile** view for each `cam17_orientation` value. _Working hypothesis from the Zenodo description — **must be verified, not assumed**: subject facing the horizontal camera (Camera17) → **c17 = front, c18 = profile**; subject facing the wall between cameras → **half-profile in both**._
  - [x] Report the **usable side-view rep count** for Ex6 after this filter.
- [x] Write `ml/reports/DATA_AUDIT.md` with every number above.

> **⚠ The gate.** If the side-view-usable Ex6 rep count is materially below the ~90/category aggregate, that is a **finding, not a failure** — but it changes the plan and HY must decide before training. Options to present with trade-offs (do not choose unilaterally):
> **(a)** accept the smaller N and report it honestly as a limitation;
> **(b)** additionally admit half-profile reps as a separate, flagged cohort and test whether including them helps or hurts LOSO;
> **(c)** relax to both views and add `view` as an explicit feature.
> **Do not proceed to Stage 5.2 until HY chooses.**
>
> **✅ Resolved by HY (2026-07-16): option (a) — accept the smaller N.** Stage 5.2
> onward trains on the 98 verified side-view Ex6 reps (72 Good / 26 Poor) only.
> Rationale: matches exactly what the live app captures (single side-view camera, per
> `CameraSetup.tsx`'s existing squat guidance), keeps Stage 5.4's feature-validity check
> free of a confounding geometry variable, and the known weakness (3 of 9 subjects lose
> the Poor class when held out) is already covered by Stage 5.5's documented
> stratified-group-k-fold fallback — not a surprise the plan is unprepared for.
> (b) and (c) were considered and set aside: (b) needs its own validity check for a
> confirmed-different camera geometry before it could be trusted, and (c) would reopen
> Locked Assumption #3 (side-view only, valgus dropped) without the live pipeline
> supplying a `view` feature at inference time.

### Phase 5 — Stage 5.0: Data audit (2026-07-16)

- [x] Built `ml/config.yaml` (dataset paths, pose model asset path, seeds — committed;
  ```
  confirmed `/Users/sumhonyou/fypDataset/` is outside the repo tree, no `.gitignore`
  change needed), `ml/docs/rehab24_6_schema.md` (authoritative column dictionary,
  transcribed from `Segmentation.txt` and cross-checked against a live read of all 1072
  CSV rows — flags a real inconsistency in the dataset's own docs: the orientation
  mapping table says `side` where the actual column enumerates `profile`), and
  `ml/scripts/audit_rehab246.py` (loads `Segmentation.csv`, filters
  `exercise_id ∈ {5, 6}` in code, reports every number below; Black/isort clean).
  ```
- [x] **Numbers (full detail in** `ml/reports/DATA_AUDIT.md`**):** Ex6 (Squats) raw = 195
  ```
  reps, Good 134 / Poor 61, across 9 subjects (1–9), all with both classes present
  unfiltered. `cam17_orientation`: front 98 / half-profile 97 / **profile 0** (the
  `profile` value never occurs for Ex6 — it's exclusive to Ex3 in this dataset). Ex5
  (Leg lunge, Phase 5B reference only): 174 reps, Good 78 / Poor 96, subject 3 is
  single-class (0 Good) even before any view filter.
  ```
- [x] **View question verified visually, not assumed:** extracted real frames (via
  ```
  OpenCV, `cv2.VideoCapture`) from both cameras for one `front`-orientation rep and one
  `half-profile`-orientation rep of `PM_008` (Ex6). Confirmed: `cam17_orientation ==
  ```

"front"`→ Camera17 shows the subject facing the camera dead-on, Camera18 shows a       clean true sagittal/profile view.`cam17_orientation == "half-profile"`→ **both**       cameras show a diagonal angle, neither is a true side view. Composite comparison       image saved to`ml/reports/figures/view_verification.png`and embedded in` DATA_AUDIT.md`.

- [x] **Usable side-view Ex6 rep count: 98** (all `front`-orientation reps, sourced from
  ```
  Camera18) — Good 72 / Poor 26, all 9 subjects still represented, but subjects 2, 4,
  and 9 become single-class (0 Poor) once filtered to side-view only — a real LOSO
  problem for those 3 folds. Half-profile-only Ex6 reps (excluded from this count): 97
  total, Good 62 / Poor 35.
  ```
- [x] **Gate triggered:** Poor-class count after the view filter (26) is materially
  ```
  below the ~90/category reference the gate text names, even though Good (72) is close.
  `DATA_AUDIT.md` §"The gate" lays out options (a)/(b)/(c) with trade-offs specific to
  the numbers above (LOSO fold viability for (a), the half-profile correctness split
  for (b), the live-capture `view`-feature availability problem for (c)) — no option is
  chosen; per the hard-gate instruction this is HY's call.
  ```
- [ ] **Not done, correctly:** Stage 5.2 onward (landmark extraction, feature table,
  ```
  training) — blocked on the gate above, per scope discipline.
  ```

### Stage 5.1 — `ml/` scaffold

```
ml/
├── config.yaml                # dataset paths (committed — see Stage 5.0), model asset path, seeds
├── requirements.txt           # mediapipe, scikit-learn, pandas, numpy, joblib, matplotlib, seaborn
├── docs/
│   ├── rehab24_6_schema.md
│   └── ec3d_joint_mapping.md  # Stage 5.9
├── scripts/
│   ├── audit_rehab246.py
│   ├── extract_landmarks.py
│   ├── build_features.py
│   ├── check_feature_validity.py
│   ├── check_mocap_agreement.py
│   ├── train_squat.py
│   ├── sweep_fusion_weights.py
│   ├── evaluate_squat.py
│   ├── validate_ec3d.py
│   └── plotting.py            # shared plot helpers — one save_fig() used by every script below
├── data/                      # gitignored — landmarks cache, feature CSVs
├── artifacts/                 # COMMITTED — *.joblib, feature_schema.json, label_map.json
└── reports/
    ├── figures/                # COMMITTED — all .png outputs listed in Stages 5.4/5.5/5.6/5.7/5.9
    └── *.md                    # COMMITTED — DATA_AUDIT.md, SQUAT_*_REPORT.md, embed figures via relative path
```

- [x] `ml/` importing from `backend/app/module_b` must work (X1). Set it up as a path/editable install — **document the exact command in** `ml/README.md`. A copy-pasted feature function is a Phase-5-breaking bug, not a shortcut.
- [x] `scripts/plotting.py` — one shared `save_fig(fig, name: str) -> Path` that writes to `ml/reports/figures/{name}.png` at a fixed DPI (150) and fixed figure size per plot type, and a shared style (`seaborn` theme or matplotlib rcParams set once here). **Every** plotting call below goes through this — no script sets its own DPI/style ad hoc.
- [x] **Every report** `.md` **file embeds its figures**, not just links to the folder — `![caption](figures/whatever.png)` — so `ml/reports/*.md` is self-contained and reads correctly if copied straight into the FYP report/appendix.

### Phase 5 — Stage 5.1: `ml/` scaffold (2026-07-16)

- [x] Created `ml/data/` (gitignored via a new `ml/data/*` rule in `.gitignore`, with
  ```
  `.gitkeep` excepted so the empty dir is still tracked) and `ml/artifacts/`
  (committed, `.gitkeep` placeholder — no artifacts exist yet, that's Stage 5.5+).
  `ml/reports/` and `ml/reports/figures/` already existed from Stage 5.0.
  ```
- [x] `ml/requirements.txt` — mediapipe, scikit-learn, pandas, numpy, joblib,
  ```
  matplotlib, seaborn, pyyaml (the last one because `audit_rehab246.py`, shipped in
  Stage 5.0, already imports it).
  ```
- [x] **X1 editable install, verified live, not just documented:** added a minimal
  ```
  `backend/pyproject.toml` (setuptools, `include = ["app*"]`) so `app` is
  pip-installable in editable mode — it does not replace `backend/requirements.txt` as
  the FastAPI app's own dependency list, it exists solely for this. Documented the
  exact commands in `ml/README.md`. **Verified in a throwaway venv**: `pip install -e
  ```

./backend`followed by`from app.module_b.core.features import FeatureVector`and` from app.module_b.squat.exercise import SquatExercise` both succeeded — real import,
not a hypothetical path. Confirmed the change doesn't affect the backend app itself:
full backend suite still 126/126 passing after adding the file.

- [x] `ml/scripts/plotting.py` — `save_fig(fig, name, figsize=None) -> Path`, fixed
  ```
  DPI 150, a `FIGSIZES` dict of named sizes (`single`/`wide`/`grid_4x4`/
  `bland_altman` — the sizes Stage 5.4's known figures need; more can be added when a
  later stage needs a new one, not speculatively now), one `sns.set_theme()` call
  applied lazily on first save. Smoke-tested: a real matplotlib figure saved through it
  round-tripped to disk correctly (deleted after the check).
  ```
- [x] `ml/README.md` — the install commands above, the macOS/Apple-Silicon MediaPipe
  ```
  GPU-delegate note pre-recorded for Stage 5.2 (so nobody "fixes" the CPU delegate
  later), the report figure-embedding convention, and the directory layout.
  ```
- [ ] **Deliberately not created (scope discipline — these are later stages' work, not
  ```
  5.1's):** `ml/docs/ec3d_joint_mapping.md` (Stage 5.9), and every `scripts/*.py` shown
  in the target tree besides `plotting.py` and the already-existing
  `audit_rehab246.py` — `extract_landmarks.py` (5.2), `build_features.py` (5.3),
  `check_feature_validity.py`/`check_mocap_agreement.py` (5.4), `train_squat.py` (5.5),
  `sweep_fusion_weights.py` (5.6), `evaluate_squat.py` (5.7), `validate_ec3d.py` (5.9).
  ```

### Stage 5.2 — Landmark extraction from RGB video

- [x] `extract_landmarks.py`:
  - **Loads the _same_** `pose_landmarker_full.task` **asset the frontend self-hosts.** This is the whole point of X3 — a different model variant reintroduces the domain gap. Path in `ml/config.yaml`, pointing at the frontend's asset.
  - `RunningMode.VIDEO`, `delegate=CPU`. **MediaPipe Python's GPU delegate is Ubuntu-only** — on macOS/Apple Silicon it errors; CPU + XNNPACK is the correct and only path here. Document this in `ml/README.md` so nobody "fixes" it later.
  - Extracts **world landmarks** (X3), not image landmarks.
  - Processes only the videos needed: **Ex6 (squat)**, the camera chosen in Stage 5.0, honouring the orientation filter.
  - **Resumable + cached** — writes one `.npz` per video, skips existing. A 2.7 GB batch should never need to restart from zero.
  - Records extraction metadata: model asset **hash**, mediapipe version, delegate, fps.
- [x] **Parity check (blocking):** extract one short clip via this Python pipeline, and record the same clip through the browser runtime. Compare per-frame world-landmark distributions. Report the divergence in `ml/reports/PARITY_CHECK.md`. Small numeric differences are expected (delegate/backend); a _structural_ difference means the pipeline is wrong.
- [x] Apply the **same preprocessing as runtime** (X1): confidence filter 0.6, ≤5-frame linear interpolation, One Euro, normalisation. Import it from the backend — do not re-implement.

### Phase 5 — Stage 5.2: Landmark extraction (2026-07-16)

- [x] **Reconciliation finding, resolved by HY before writing code:** traced the
  ```
  actual live squat pipeline (`POST /api/module-b/analyze` -> `SquatExercise.
  ```

segment`/`extract_features`, and` useMediaPipePose.ts`upstream of it) and found       it applies **zero** confidence-filter/gap-fill/One-Euro preprocessing — raw       MediaPipe world landmarks flow straight from the frontend into segmentation and       feature extraction.`MODULE_B_CORE_CONFIG["interpolation_max_gap_frames"]`is       defined but never consumed anywhere. This differs from Module A (STS/SLS/WBLT),       which does run`LandmarkSmoother`server-side. X3's "confidence filter -> gap       fill -> One Euro -> normalisation" pipeline is therefore aspirational for       Module B squat, not implemented. **HY's decision: option (a)** — match runtime       as it actually is (no smoothing in`extract_landmarks.py`either), preserving       true X1 parity with the pipeline that exists today, rather than smoothing       offline data the live model will never see smoothed (option b) or silently       changing Phase 4's already-verified live squat code (option c, out of scope for       this stage). Recorded in`extract_landmarks.py`'s module docstring so this
isn't re-discovered as a "bug" later.

- **[x] Follow-up spawned for later, not fixed here:** flagged as a separate
  background task (`Wire real preprocessing into Module B squat pipeline`) —
  unifying Module A's and Module B's preprocessing approach is a genuine
  Phase-4-touching decision outside Stage 5.2's scope.

- [x] `ml/scripts/extract_landmarks.py` — `PoseLandmarkerOptions` matches
      `useMediaPipePose.ts` exactly (CPU delegate, `VIDEO` running mode, `num_poses=1`,
      all three confidence thresholds 0.5). Filters `Segmentation.csv` to
      `exercise_id == 6` in code (9 unique `video_id`s), reads only **Camera18**
      (the side-view camera verified in Stage 5.0). One `.npz` per video
      (`ml/data/landmarks/`, gitignored — regenerable), skip-if-exists resumability
      (verified live: re-running mid-batch after a crash correctly skipped the 2
      already-completed videos and resumed from the 3rd). Metadata
      (`model_asset_sha256`, `mediapipe_version`, `delegate`, `fps`,
      `detection_config`) stored inside each `.npz` via a JSON string array.
  - **Real bug found and fixed during this stage:** the first version reused one
    `PoseLandmarker` instance across all 9 videos for efficiency; MediaPipe's
    `VIDEO` running mode tracks an internal "last timestamp" that isn't reset
    between videos, so video 2's frame-0 timestamp (0ms) was rejected as
    non-monotonic against video 1's last frame (~~171,000ms), crashing the batch
    on the 3rd video. Fixed: one fresh~~ `PoseLandmarker` ~~per video (closed after
    use) — correct and still fast enough (~~92 fps on this machine).
  - **Extraction result (all 9 side-view Ex6 videos, verified by reading every**
    `.npz` **back):** 30,028 total frames processed, only **1** frame with no
    detected pose (0.00%) — full run completed in ~6 minutes.
- [x] `ml/reports/PARITY_CHECK.md` + `figures/parity_check_knee_flexion.png` — a
      temporary dev-only browser harness (`frontend/parity-check.html` +
      `frontend/src/devPages/parityCheck.ts`, both **removed** after the check ran,
      per the report's own "Cleanup" section) ran the frontend's actual installed
      `@mediapipe/tasks-vision` package against the identical self-hosted WASM +
      model asset, with `PoseLandmarkerOptions` copied verbatim from
      `useMediaPipePose.ts`, fed frame-by-frame via `<video>` seeking (not a live
      webcam) against `PM_008`'s rep-1 clip (frames 100-219, the same range visually
      verified in Stage 5.0). **Result: 0.9996 Pearson correlation across all
      landmarks; the squat-relevant landmarks (hips/knees/ankles) differed by
      0.8-7.3mm on average; the derived knee-flexion angle — the actual squat ROM
      signal — differed by 0.90° mean / 4.6° max across 120 frames.** Verdict: small
      numeric differences consistent with native-TFLite-vs-browser-WASM delegate
      divergence, no structural mismatch — parity confirmed, gate cleared.
- [x] Verification: `ml/scripts/extract_landmarks.py` and the parity-check
      harness's deletion left `git status` clean on `frontend/`; Black/isort clean
      on the new script; full backend suite still 126/126 (untouched by this stage).

### Cross-cutting — Wire real preprocessing into Module B squat pipeline (2026-07-16)

- [x] **Reconciliation:** re-traced the live squat pipeline (worked in worktree
  ```
  `claude/serene-bhaskara-74aaf3`, coordinated live with the parallel session
  doing Stage 5.1-5.3 in the main checkout) and confirmed the gap: raw
  MediaPipe world landmarks flowed straight from the frontend into
  `SquatExercise.segment`/`extract_features`, with zero confidence-filter/
  gap-fill/One-Euro preprocessing, unlike Module A (STS/SLS/WBLT), which runs
  `LandmarkSmoother` server-side. `MODULE_B_CORE_CONFIG["interpolation_max_gap_frames"]`
  (=5) was defined but never consumed anywhere.
  ```
- [x] **HY decision:** add real preprocessing now, before Stage 5.3's feature
  ```
  table gets used further — re-extraction cost was still low (nothing built
  on the unsmoothed `ml/data/landmarks/*.npz` yet). Build genuine linear
  interpolation for the gap-fill (Module A's smoother only hold-lasts on low
  visibility, it never interpolated).
  ```
- [x] **New shared module:** `backend/app/module_b/core/preprocessing.py` —
  ```
  `preprocess_world_landmarks(frames)` runs confidence filter (`MIN_VISIBILITY`,
  reused from `app.module_a.core.config`) → gap fill (new: linear
  interpolation, time-weighted, up to `interpolation_max_gap_frames`, leaving
  longer/leading/trailing gaps for the next step) → One Euro (`LandmarkSmoother`,
  imported from `app.module_a.core.smoothing`, not forked). Deliberately built
  as a plain importable function (not inlined in the router) so `ml/`'s
  offline extractor can import the identical implementation later — X1.
  ```
- [x] **Stateful-filter ordering, confirmed with the parallel session:**
  ```
  `preprocess_world_landmarks` takes the _entire_ session's frame stream and
  must be called once over the whole thing before segmentation — `OneEuroFilter`
  is stateful (per-landmark-per-axis history), so windowing into reps first
  and smoothing per-window would reset filter state at every rep boundary and
  diverge from what live capture actually produces. Added a regression test
  asserting this: preprocessing a stream in one call vs. two independently
  preprocessed halves gives different results.
  ```
- [x] **Wired into** `backend/app/module_b/core/router.py`**:** `assess_capture_quality`
  ```
  still runs on the raw capture (it's a diagnostic on what was actually
  recorded); `exercise.segment`/`extract_features` now run on the
  preprocessed stream. No frontend change needed — Module A's precedent
  already showed this preprocessing belongs server-side.
  ```
- [x] **Tests:** `backend/tests/test_module_b_preprocessing.py` (8 new tests —
  ```
  short-gap interpolation, gap-longer-than-max left for hold-last, leading/
  trailing gaps untouched, interpolated-point visibility bump, the stateful
  full-stream contract, and a Phase 4 regression check: `_five_clean_reps()`
  through `preprocess_world_landmarks` → `segment_squat_frames` →
  `extract_squat_features` still yields 5 reps with a valid feature vector
  each). Full backend suite: **134/134 passing** (126 previous + 8 new).
  Black/isort clean.
  ```
- [x] **Done in the follow-up below (2026-07-16), not in this entry:** the `ml/`
  ```
  re-run. See "Cross-cutting follow-up — far-limb occlusion" immediately below;
  it also **amends this entry's hold-last design**, which did not survive
  contact with real side-view data.
  ```

### Cross-cutting follow-up — far-limb occlusion breaks hold-last (2026-07-16)

Found by the `ml/` re-run above landing on real REHAB24-6 side-view data. The
preprocessing entry above assumed "gaps longer than `interpolation_max_gap_frames`
or without an anchor → leave them to `LandmarkSmoother`'s hold-last." That
assumption is wrong for a single side-view camera, and the failure was loud.

- [x] **The finding (measured, not inferred):** a side-view camera tracks the near
  ```
  leg well and the far leg poorly, **systematically, in all 9 subjects**. Mean
  landmark visibility: left knee 0.95–0.99 / left ankle 0.97–0.99 versus right
  knee **0.59–0.78** / right ankle **0.68–0.87**. The far knee sits below
  `MIN_VISIBILITY = 0.6` for _whole reps_ — all 121 frames of PM_008's rep-1
  window, vastly longer than the 5-frame gap-fill cap. `LandmarkSmoother`'s
  hold-last is documented for a **"brief occlusion"**; this violates that design
  envelope structurally, so it froze the far knee at its standing angle for
  entire reps. Since squat segmentation and features both use the **bilateral
  mean** knee flexion, a frozen far knee ~halved the signal: median
  `knee_flex_peak_deg` fell 99.8° → 78.5°, and FSM rep agreement collapsed from
  92/98 to **32/98** front reps. This would have hit **live users identically**
  — same shared function, same camera guidance.
  ```
- [x] **Why it was released, not worked around:** the far leg is **low-confidence,
  ```
  not wrong** — its raw trajectory still tracks a plausible squat (peak 99.9° on
  a rep where the near knee read 77.9°). Hold-last was therefore discarding real
  signal and substituting a stale value: turning "uncertain but usable" into
  "confidently stale", which is strictly worse than the noisy estimate.
  ```
- [x] **HY decision (option b of three offered):** release hold-last for persistent
  ```
  occlusion, **scoped to Module B's preprocessing**. Rejected alternatives:
  (a) accept the damage and document it as a limitation — would have shipped a
  knowingly broken live rep counter; (c) make squat's features prefer the near
  leg only — would have silently cost `symmetry_index_pct` (it is literally
  `|θ_L − θ_R|`, unmeasurable from one leg) and thrown away usable far-leg data.
  ```
- [x] `core/preprocessing._release_persistent_occlusions()` — a low-visibility run
  ```
  **longer than `interpolation_max_gap_frames`** has its visibility raised to
  exactly `MIN_VISIBILITY`, so the One-Euro pass smooths the landmark's own raw
  estimate instead of hold-lasting a stale one. Runs of ≤5 frames are untouched,
  so a genuine brief flicker still hold-lasts as designed. Reuses the same
  visibility-bump idiom `_interpolate_gap` already used — the one lever that
  steers hold-last **without forking `LandmarkSmoother`**.
  ```
- [x] **No second config knob, and this was reviewed, not assumed.** The release
  ```
  threshold reuses `interpolation_max_gap_frames` rather than introducing its own
  tunable. Asked the session that owns `preprocessing.py` to confirm or object;
  it reviewed the diff and confirmed (2026-07-16): that constant already means
  "how long a gap can be before we stop trusting continuity assumptions", so this
  is the same semantic rather than an overload, and a separate constant would be
  two numbers to keep in sync for no benefit. It also confirmed the layering
  (`_fill_gaps` gets first crack at short runs; this only fires beyond the max) and
  that Module A is untouched. Do not split these into two knobs without a reason
  that defeats the above.
  ```
- [x] `**LandmarkSmoother` itself deliberately untouched** — it is shared with
  ```
  Module A (STS/SLS/WBLT all call `smooth_frame(t, world)`), whose behavior and
  verified results must stay byte-identical. The fix lives entirely in Module B's
  preprocessing layer. Confirmed: full suite green with zero Module A changes.
  ```
- [x] **Result:** far-leg signal restored. Median `knee_flex_peak_deg` back to 98.3°
  ```
  (vs 99.8° raw — the small residual is legitimate smoothing damping). FSM front-rep
  agreement **93/98 (94.9%)**, marginally _better_ than the 92/98 raw baseline,
  i.e. preprocessing now helps rep detection instead of destroying it.
  ```
- [x] **Tests:** rewrote `test_gap_longer_than_max_is_left_for_hold_last` →
  ```
  `test_gap_longer_than_max_is_released_not_frozen` — the old test _encoded the
  exact bug_ (asserting a long gap stays frozen), so it was changed deliberately
  as a contract change, not bent to pass. Added
  `test_brief_gap_without_anchor_still_holds_last` (proves the fix is bounded to
  persistent occlusion) and `PersistentOcclusionTests` (a far-limb-style landmark
  that is never confident must still track its real excursion). Full backend suite:
  **136/136**. Black/isort clean.
  ```
- [ ] **Left open for Stage 5.4, deliberately:** whether the far leg's estimate is
  ```
  _accurate_ rather than merely plausible is exactly what `check_mocap_agreement.py`
  settles against the OptiTrack ground truth — not asserted here. Also unresolved:
  `symmetry_index_pct`'s median of ~30% looks inflated by its own formula
  (dividing by a near-zero mean while standing), a feature-design question for
  that gate, not this fix.
  ```

### Stage 5.3 — Build the feature table

- [ ] `build_features.py`:
  - Windows each rep using `Segmentation.csv`'s `first_frame`/`last_frame` (**not** our FSM — the dataset's physio-verified boundaries are ground truth here).
  - **But also:** run our FSM over the same clips and report rep-boundary agreement vs the dataset's segmentation. This is a free, honest validation of Stage 4.3's FSM and belongs in the report.
  - Calls the **backend's** `extract_features()` (X1).
  - Emits `ml/data/squat_features.csv`: one row per rep = `person_id`, `video_id`, `repetition_number`, feature columns (in `FeatureVector.names` order), `correctness` label, `orientation`, `lighting`, `mocap_erroneous`, `feature_schema_version`.
- [ ] **Schema validation:** assert column order/count matches `FeatureVector.names`; fail loudly on drift.
- [ ] **Label normalisation** (Option A): `correct → Good`, `incorrect → Poor`. Write `ml/artifacts/label_map.json`. **No Fair in training** — record that explicitly in the file.

### Phase 5 — Stage 5.3: Build the feature table (2026-07-16)

- [x] **Reconciliation confirmed before writing code:** spot-checked every claim the
  ```
  previous stages make about the X1 contract. `app.module_b.squat.features.
  ```

extract_squat_features`and`SQUAT_FEATURE_NAMES`(13 features),`app.module_b.
squat.segmentation.segment_squat_frames`, and the` FeatureVector`/`Rep`dataclasses       all exist as Stage 4.2/4.3 describe, and the ml venv's editable install imports       them cleanly (X1 — the offline extractor calls the live functions, never       re-implements them). Also re-verified the dataset↔extraction frame alignment       Stage 5.0/5.2 rely on: Segmentation.csv`first_frame`/`last_frame`index directly       into the Camera18`.npz` (e.g. PM_008 rep 1 = frames 100–220), the same range
Stage 5.2's parity check used.

- [x] `ml/scripts/build_features.py` — windows every **side-view** rep
  ```
  (`exercise_id == 6` AND `cam17_orientation == "front"`, i.e. Camera18 = profile,
  per Stage 5.0 option a) by the dataset's physio-verified `first_frame`/`last_frame`
  (inclusive), builds the runtime frame shape (`worldLandmarks` xyz + `timestampMs`)
  from the `.npz`, and calls the backend's `extract_squat_features()` (X1). Emits
  `ml/data/squat_features.csv` — **98 rows** (one per rep, matching the audit's 98
  verified side-view reps), **72 Good / 26 Poor**, across **9 subjects / 9 videos**.
  Columns: `person_id`, `video_id`, `repetition_number`, the 13 features in
  `SQUAT_FEATURE_NAMES` order, `correctness` (raw 0/1), `label` (Good/Poor),
  `orientation`, `lights_on`, `mocap_erroneous`, `feature_schema_version` (`1.0.0`).
  ```
  - **Naming note (not drift):** the checklist says `lighting`; the actual
    Segmentation.csv column is `lights_on` (0/1) — the CSV uses the real column name,
    consistent with the Stage 5.0 schema-doc correction. A separate `label` column
    (the normalised Good/Poor target) is emitted alongside the raw `correctness` for
    traceability; the checklist's "`correctness` label" wording is satisfied by both.
- [x] **Schema validation:** `write_features_csv()` asserts the CSV's feature block,
  ```
  in order, equals `SQUAT_FEATURE_NAMES` before writing — the build raises loudly on
  any drift. `extract_squat_features` also re-checks `FeatureVector.names` per rep.
  ```
- [x] **Label normalisation (Option A):** `ml/artifacts/label_map.json` written (a
  ```
  committed artifact — `ml/artifacts/` is not gitignored, per Locked Assumption #4):
  `{"1": "Good", "0": "Poor"}`, `no_fair_in_training: true`, plus an explicit note
  that Fair is derived at inference from the calibrated low-confidence margin
  (Stage 5.6), never a trained class.
  ```
- [x] **FSM-vs-dataset segmentation agreement (free validation, Stage 4.3 FSM):**
  ```
  `ml/reports/FEATURE_TABLE.md`. Ran `segment_squat_frames` over each full Camera18
  clip and matched detections to the dataset boundaries **strictly one-to-one**
  (greedy by overlap, each detected/GT rep used once). Across all 195 Ex6 reps in
  these clips (front + half-profile; the FSM is orientation-blind): **192 detected,
  182 matched → 93.3% recall (13 missed), 94.8% precision (10 spurious)**; on the
  98 **front** (trained) reps, **92/98 = 93.9% recall**. Boundary error on matched
  reps: start median 17 frames, end median 15 frames (≈0.5 s at 30 fps) — expected
  from the FSM's 30°-enter / 20°-exit hysteresis starting/ending a rep slightly
  inside the dataset's onset/offset. Recorded, not corrected: the dataset boundaries
  remain ground truth for windowing.
  ```
  - **Correctness fix caught during implementation:** the first matcher let one merged
    detection count against two GT reps, producing the impossible `detected 17 /

matched 20`for PM_038 (matches exceeding detections). Reworked to strict     one-to-one greedy matching so`matched ≤ min(detected, gt)` always holds — the
numbers dropped from an inflated 187/195 to an honest 182/195.

- [x] **Windowed-rep sanity (logged in the report, not a gate — Stage 5.4 does the real
  ```
  validity check):** `knee_flex_peak_deg` spans 69.7°–129.8° (median 99.8°) and
  `rep_duration_s` 2.13–5.13 s across the 98 reps — non-trivial squat depth in every
  window, corroborating the frame-alignment reconciliation above.
  ```
- [x] Verification: `build_features.py` runs clean; **byte-identical CSV across two
  ```
  runs** (X8 determinism — `md5` confirmed). Black + isort clean. Backend untouched
  (`git status backend/` empty; suite stays 126/126). `ml/data/squat_features.csv`
  and the `.npz` landmarks are gitignored (regenerable from the raw dataset via
  `extract_landmarks.py` → `build_features.py`); `label_map.json` and
  `FEATURE_TABLE.md` are committed.
  ```
- [ ] **Deliberately not done (out of Stage 5.3 scope):** per-subject class presence is
  ```
  only surfaced (subjects 2/4/9 are single-class Good, subject 1 is 16 Good/1 Poor),
  not acted on — the LOSO/stratified-group-k-fold fallback that handles it is
  Stage 5.5's job. No feature was dropped or kept on the basis of the sanity stats
  above; the keep/drop verdict and the `norm_ref` bake-off are Stage 5.4's gate.
  ```

#### Re-run against the real preprocessing (2026-07-16, supersedes the numbers above)

The cross-cutting preprocessing change landed on `main` (merge `ecddd9a`), so the
unsmoothed feature table built above no longer matched the live runtime and was
rebuilt — X1 is only real if the offline features come from the _same_ pipeline.

- [x] `build_features.py` now imports the backend's
  ```
  `preprocess_world_landmarks` (X1 — the shared `module_b/core/preprocessing.py`
  function, not a re-implementation) and applies it **once per video over the full
  chronological stream, then windows** by the dataset boundaries — mirroring
  `router.py`'s single call site ahead of `segment()`. Windowing first would reset
  `OneEuroFilter`'s per-landmark state at every rep boundary and drift from live.
  One shared preprocessed-stream cache feeds **both** the feature table and the FSM
  agreement check, so neither path can derive a subtly different stream.
  ```
- [x] `visibility` is now carried into the offline frame dicts (previously x/y/z only) —
  ```
  both the gap-fill's confidence filter and `LandmarkSmoother`'s hold-last branch on
  it, so omitting it would have silently disabled them offline while they ran live.
  ```
- [x] The FSM agreement check now runs on the **preprocessed** stream, matching what the
  ```
  live FSM actually receives, rather than raw landmarks.
  ```
- [x] **This re-run is what surfaced the far-limb occlusion failure** — see the
  ```
  "Cross-cutting follow-up" entry above. Final numbers after that fix: **98 reps
  (72 Good / 26 Poor) unchanged**; `knee_flex_peak_deg` median **98.3°** (was 99.8°
  unsmoothed — the difference is legitimate smoothing damping); FSM front-rep
  agreement **93/98 (94.9%)**, total **184/195** (94.4% recall / 95.8% precision).
  ```
- [x] Verification: byte-identical CSV across two runs (X8 determinism, `md5`);
  ```
  Black/isort clean; full backend suite **136/136**.
  ```
- [ ] **Flagged for Stage 5.4, not acted on here:** `knee_flex_peak_deg` separates the
  ```
  classes but in the **opposite direction to the plan's stated expectation** — Good
  median 92.8° vs Poor median **107.7°**, i.e. incorrect reps go _deeper_, whereas
  Stage 5.4's gate text assumes "`knee_flex_peak_deg` should be lower for incorrect
  reps". The gate's pass/fail condition is separation, which holds — but its
  directional assumption does not, and the keep/drop reasoning must not be written
  as if it did. Not investigated here; it is that gate's job.
  ```

### Stage 5.4 — Feature-validity sanity **[GATE — R5.5]**

> ✅ **Hold cleared (2026-07-16).** This gate was held until the Module B preprocessing
> change landed, because a feature-validity verdict is meaningless on features the live
> model won't actually produce. That change is now merged (`ecddd9a`) and the `ml/`
> offline pipeline has been re-run against it — `build_features.py` imports the shared
> `preprocess_world_landmarks`, applies it full-stream-then-window, and carries
> `visibility` through; `squat_features.csv` is regenerated. See the Stage 5.3 "Re-run
> against the real preprocessing" sub-entry and the "Cross-cutting follow-up — far-limb
> occlusion" entry above. **This gate is now unblocked and runs on the current table.**
>
> **Two findings from the re-run that this gate must handle, not inherit blindly:**
>
> 1. **The directional assumption below is wrong.** The checklist says
>    "`knee_flex_peak_deg` should be lower for incorrect reps." Measured, it is the
>    opposite: Good median 92.8° vs **Poor median 107.7°** — incorrect reps go _deeper_.
>    Separation (the actual pass/fail condition) holds, so the gate passes; but the
>    keep/drop justification must be written from the real direction, and the "e.g."
>    below should not be treated as the expected sign.
> 2. `**symmetry_index_pct` is suspect on its own formula, independent of the data.**
>    It is a per-frame `|θ_L − θ_R| / mean × 100` averaged over the rep, so near
>    standing (both angles ≈ 0) the denominator collapses and the percentage explodes —
>    which is most of why its median sits at ~30%. Judge the feature on that basis, not
>    just its boxplot.

- [x] `check_feature_validity.py` — per feature, plot **and** report its distribution split by class. A feature enters the model **only if it visibly separates classes** (e.g. `knee_flex_peak_deg` should be lower for incorrect reps). Output `ml/reports/FEATURE_VALIDITY.md` with an explicit keep/drop verdict + justification per feature.
  - [x] **Figure (required):** `figures/feature_validity_boxplots.png` — one boxplot (or violin) per feature, class on the x-axis, arranged as a grid (e.g. 4×4 subplots via `plt.subplots`), so every feature's class separation is visible on one page.
  - [x] **Figure (required):** `figures/feature_correlation_heatmap.png` — a correlation matrix across all candidate features (seaborn `heatmap`), to justify any later "these two features are redundant, drop one" calls.
- [x] `**norm_ref` bake-off** (R5.3): compute cross-subject variance under `trunk_length` vs `thigh_length`; pick the lower. Record the number. Update the backend config to match — **and re-run any Phase 4 test that depended on the default.**
  - [x] **Figure (required):** `figures/norm_ref_variance_comparison.png` — a paired bar chart, per-subject variance under each candidate, so the "lower" claim is visually checkable, not just a single number in prose.
- [x] `check_mocap_agreement.py` _(uses_ `3d_joints.zip`_)_ — compute knee-flexion angle from our MediaPipe world landmarks vs from the **OptiTrack 26-joint mocap GT** on the same frames. Report **ICC(2,1) + Bland-Altman**, reusing `backend/app/module_a/core/evaluation/agreement.py` (it's unit-agnostic and already shared — do not fork it).
  - [x] **Figure (required):** `figures/mocap_agreement_bland_altman.png` — the standard Bland-Altman plot (mean vs difference, limits of agreement shaded). If `agreement.py` already produces one for Module A, reuse that plotting function too — don't write a second implementation of the same chart.
- [x] **Gate:** if `knee_flex_peak_deg` does **not** separate the classes, stop. Either the extraction, the view filter, or the windowing is wrong. Do not train through a red flag.

### Phase 5 — Stage 5.4: Feature-validity sanity [GATE] (2026-07-16)

- [x] **GATE: PASS.** `knee_flex_peak_deg` separates the classes decisively — **AUC
  ```
  0.837** (Good median 92.8° vs Poor median 107.7°), and the direction holds in
  **5/5** of the subjects able to vote on it, so it is not one subject's artefact.
  Extraction, view filter and windowing are not broken, which is what this gate
  exists to catch. Training may proceed.
  ```
  - **The separation runs OPPOSITE to the plan's stated expectation.** The checklist
    says "`knee_flex_peak_deg` should be lower for incorrect reps"; measured, incorrect
    reps go **deeper** (Poor 107.7° > Good 92.8°). The gate's condition is _separation_,
    which holds either way, so this is not a failure — but REHAB24-6's Ex6 "incorrect"
    reps are a mix of deliberate faults, not specifically shallow ones, so **no
    downstream rule may assume "deeper = better"** for this cohort. Flagged for
    Stage 5.5/5.6.
- [x] `ml/scripts/check_feature_validity.py` → `ml/reports/FEATURE_VALIDITY.md` +
  ```
  `figures/feature_validity_boxplots.png` (4×4 grid, all 13 features) +
  `figures/feature_correlation_heatmap.png`. **Verdicts: 10 KEEP / 3 DROP**
  (`rep_duration_s` AUC 0.492, `descent_ascent_ratio` 0.467, `symmetry_index_pct`
  0.442 — all effectively at the 0.5 no-separation point). Strongest features:
  `ankle_df_proxy_deg` (0.882), `knee_rom_deg` (0.859), `knee_flex_peak_deg`
  (0.837). Redundant pairs recorded, not acted on: `knee_flex_peak_deg` ~
  `knee_rom_deg` (r=0.97) and `trunk_lean_peak_deg` ~ `trunk_lean_mean_deg` (0.93).
  ```
  - **Method, deliberately not p-values:** 98 reps come from only 9 subjects, so reps
    are **not independent** and a p-value that treats them as such is
    anti-conservative (pseudo-replication). Verdicts rest on **AUC** (effect size) plus
    **cross-subject direction consistency** (does each subject with ≥2 reps of both
    classes agree on the sign?), which catches a feature that "separates" only via one
    subject. p-values are listed for completeness only. The keep/drop rule
    (|AUC−0.5| ≥ 0.10 **and** ≥60% subject agreement) was **pre-declared before
    results were seen** so the thresholds are not fitted to the outcome.
  - **Selection-bias caveat recorded** (`FEATURE_VALIDITY.md`, final section): verdicts
    were computed on all 98 reps, including subjects Stage 5.5 will hold out for LOSO,
    so a data-driven DROP is mildly circular. Tolerable because this is a _sanity gate_
    and the only DROPs have ~zero signal — but Stage 5.5 must choose deliberately
    between training on all 13 and nesting selection inside each fold.
- [x] `ml/scripts/check_norm_ref.py` → `ml/reports/NORM_REF_BAKEOFF.md` +
  ```
  `figures/norm_ref_variance_comparison.png`. **Winner: `trunk_length`** (mean
  cross-subject CV **0.180 vs 0.201**), beating `thigh_length` on **both**
  normalised features and on **both** metrics. `SQUAT_CONFIG["norm_ref_strategy"]`
  updated `thigh_length` → `trunk_length` and **retagged
  `[proposed heuristic, R5.3]` → `[dataset-derived, R5.3]`** — it is earned now, not
  guessed. Feature table + validity report regenerated under the new reference
  (verdicts unchanged; the gate feature is unaffected by `norm_ref`).
  ```
  - **Method deviation, deliberate:** the checklist says "compute cross-subject
    _variance_ … pick the lower". Taken literally that is **scale-confounded** — the
    two references have different magnitudes, so dividing by the larger one shrinks the
    feature and its raw variance regardless of how well it normalises. The verdict is
    therefore taken on the scale-invariant **coefficient of variation**; raw variance is
    still reported so the confound is visible. It did not change the answer here
    (`trunk_length` wins either way), it just makes the claim defensible. The figure
    scales each candidate by its own mean for the same reason — plotting raw bars would
    have let a reader "see" the right answer for the wrong reason.
  - **Two Phase 4 tests failed on the config change — both were real fixture bugs the
    old default was masking, fixed rather than bent:** (1)
    `test_module_b_segmentation._frame()` never set the shoulder landmarks, so
    `shoulder_mid == hip_mid` and **trunk_length was 0** — an anatomically impossible
    pose that only survived because `thigh_length` was the default (and it was silently
    producing meaningless `trunk_lean` too); shoulders now sit 1 unit above the hips.
    (2) `test_norm_ref_strategy_switches_between_thigh_and_trunk_length` relied on the
    default being `thigh_length`; it now patches **both** strategies explicitly so it
    can never silently re-point when a default moves again.
- [x] `ml/scripts/check_mocap_agreement.py` → `ml/reports/MOCAP_AGREEMENT.md` +
  ```
  `figures/mocap_agreement_bland_altman.png`. Reuses `module_a/core/evaluation/
  ```

agreement.py`'s` icc_2_1`/`bland_altman`(confirmed stats-only — it has no plotting to       reuse, so the Bland-Altman chart is drawn in`ml/`via the shared`plotting.py`).       Compares the **peak of the bilateral mean knee flexion per rep** — i.e. exactly` knee_flex_peak_deg`— over all 98 reps (all`mocap_erroneous=0`, so no
exclusions). **ICC(2,1) = 0.726, bias −11.96°, 95% LoA [−21.0°, −2.9°],
r = 0.956.**

- **The r/ICC gap is the finding: our pipeline tracks the movement's shape faithfully
  (r 0.956) and mis-states its magnitude.** Adding the per-rep minimum and ROM shows
  it is **range compression, not a constant offset**: peak under-read by 12.0°,
  minimum over-read by 1.6°, so ROM is compressed by ~14° (ROM bias −13.56°).
- **⚠ Consequence flagged for Stage 5.6, not fixed here:** the ROM rule's band edges
  (`<60/60-90/90-110/≥110°`) are tagged **[clinical norm, S1]** — derived from
  literature on _true_ joint angles — but they are being applied to a measurement
  that reads ~12° low. A genuine 110° deep squat arrives as ~98° and is banded
  "parallel", systematically under-crediting depth. Fixing it means calibrating the
  measurement or re-deriving the edges on this pipeline's scale; both change Phase 4
  banding. **The classifier is unaffected** (a monotone offset applied consistently).
- **One Euro lag measured:** raw landmarks align with mocap at offset **0**, the
  preprocessed stream at **−3 frames**, i.e. the causal filter adds **~100 ms** — live
  on-screen feedback inherits it.
- **Leg identity could not be established, and that is itself a finding.** The Stage
  5.3 far-leg-accuracy question needed a per-leg comparison, which needs the
  MediaPipe↔mocap leg mapping. Absolute per-leg angles cannot discriminate it (both
  knees bend together — every pairing correlates ~0.97). The leg-**difference** signal
  can, and it correlates with mocap's own leg difference at mean **r = −0.053**
  (signs mixed) — no relationship. Geometry proves the mapping must be _consistent_
  (all 9 subjects stand identically — hip-axis cosine similarity 0.99–1.00 — and
  MediaPipe calls the far knee "right" in all 9), so those mixed signs are **noise,
  not a flipping mapping**. Per-leg numbers are therefore reported **without a
  verdict**; the far-leg question stays formally open. Partial honest answer: the
  bilateral mean includes the far leg and still tracks mocap at r = 0.956, so the far
  limb is not grossly wrong — supporting, but not proving, the hold-last release.
- **This independently condemns** `symmetry_index_pct`**, mechanistically.** The feature
  is _entirely_ a function of the leg-difference signal, and that signal correlates
  with marker-based truth at r ≈ −0.05. It is not a weak feature — it is **not
  measuring the thing it claims**. That is a far stronger basis for its DROP than the
  AUC of 0.442, and it is the same monocular limitation that already removed
  frontal-plane valgus (Locked Assumption #3). Its formula is separately broken too
  (per-frame `|θ_L−θ_R|/mean` explodes near standing where the denominator ≈ 0).

- [x] Verification: full backend suite **136/136** after the config change and fixture
      fixes; Black/isort clean on every touched file; all four required figures render
      and are embedded in their reports; feature table regenerated deterministically.
- [ ] **Deliberately not done:** no feature was actually removed from
      `SQUAT_FEATURE_NAMES` — the DROP verdicts are recorded, not executed. Editing the
      vector means bumping `feature_schema_version` and re-running Phase 4's contract
      tests, and Stage 5.5 may prefer to train on all 13 and let Extra Trees' own
      importances speak (which also sidesteps the selection-bias caveat above). Left as
      Stage 5.5's deliberate choice. `symmetry_index_pct`'s formula is likewise not
      rewritten, for the same schema-version reason.

### Stage 5.5 — Train the Extra Trees classifier

- [x] `train_squat.py`, **binary** Good/Poor (Option A), fixed `random_state`.
- [x] Hyperparameter grid (R8):

| Param               | Start        | Grid                                                  |
| ------------------- | ------------ | ----------------------------------------------------- |
| `n_estimators`      | 300          | 100–500                                               |
| `max_features`      | `'sqrt'`     | —                                                     |
| `max_depth`         | None         | 8–16                                                  |
| `min_samples_leaf`  | 2            | 2–5                                                   |
| `min_samples_split` | 10           | 10–20                                                 |
| `class_weight`      | `'balanced'` | —                                                     |
| `bootstrap`         | False        | — (ET default; part of what distinguishes it from RF) |

- [x] **CV = Leave-One-Subject-Out** (10 subjects), groups = `person_id` (D10, R8). **Fallback:** if Stage 5.0's audit showed a subject with only one class, or a fold loses a class → **stratified group k-fold (5-fold, groups = subjects)**. Record which was used and why.
- [x] **Imbalance:** `class_weight='balanced'`. **No SMOTE** — synthetic pose features can be biomechanically impossible, and small-N resampling risks duplicating a subject's reps across folds (leakage). R8 is explicit on this.
- [x] **Nested tuning** — tune inside the training folds only. Tuning on the LOSO test fold is leakage and an examiner will spot it.
  - [x] **Record every combination tried, not just the winner.** Use `sklearn.model_selection.GridSearchCV` (or an explicit manual loop) and keep its full `cv_results_` — every hyperparameter combination alongside its mean validation score and variance across folds. This is the actual evidence of experimentation: a table showing "these 20 combinations were tried, here's how each scored, this one won" is what makes the search a documented investigation rather than a number that appears from nowhere.
  - [x] **Figure (required):** `figures/hyperparameter_search_results.png` — one line or bar chart per swept parameter (e.g. validation score vs `n_estimators`, holding others at their best value; same for `max_depth`, `min_samples_leaf`, `min_samples_split`), with the chosen value marked. If the grid is small enough, a single heatmap of the two most-varied parameters (e.g. `n_estimators` × `max_depth`) is also acceptable instead of separate charts.
  - [x] `ml/reports/SQUAT_TRAINING_REPORT.md` includes the **full** `cv_results_` **table** (every combination + score), not a one-line "best params were X" summary. Losing combinations stay in the table — do not prune them out after the fact.
- [x] **Calibration** — `CalibratedClassifierCV` (isotonic if N allows, else sigmoid/Platt) on a held-out fold. ET `predict_proba` is over-confident; the Fair band depends entirely on calibrated probabilities being meaningful.
  - [x] **Figure (required):** `figures/calibration_reliability_curve.png` — predicted probability (x-axis, binned) vs observed frequency (y-axis), plotted **before and after** calibration on the same axes (`sklearn.calibration.calibration_curve` + a plotted 45° reference line), so the improvement from calibration is visible, not asserted. An uncalibrated Fair band is a fabricated third class — this figure is the evidence it isn't.
  - [x] Output `ml/reports/SQUAT_TRAINING_REPORT.md`: the full hyperparameter search table and figure above, which CV scheme was used and why, and the reliability curve embedded inline.

### Phase 5 — Stage 5.5: Train the Extra Trees classifier (2026-07-16)

- [x] `**ml/scripts/train_squat.py**` — binary Good/Poor (Option A), `random_state=42`
  ```
  from `config.yaml`, splitters `shuffle=False`. Structure: `_choose_cv()`,
  `_inner_splits()`, `_search()`, `_calibrate()`, `build_final_model()`,
  `nested_cv()`, `_plateau_stats()`, `_wilson_interval()`, `_reliability_bins()`,
  `plot_hyperparameter_search()`, `plot_calibration()`, `_importances()`,
  `write_report()`. Added `"grid_2x2": (11, 8)` to `plotting.py`'s `FIGSIZES`
  (its documented extension point, as Stage 5.4 did with `heatmap`).
  ```
- [x] **CV: `StratifiedGroupKFold(5, groups=person_id)` — the plan's fallback, and it
  ```
  was triggered by the data, not chosen.** `_choose_cv()` detects the condition
  rather than hardcoding it: **subjects 2, 4, 9 are Good-only**, so LOSO would give
  three of nine folds a test set with no Poor rep, making ROC AUC and Poor-recall
  _undefined_ there. No subject appears in both train and test, so there is no
  identity leakage — but each test fold now holds ~2 subjects. **The write-up must
  say "subject-wise 5-fold", not "LOSO".** Per-fold AUC: 0.889 / 0.887 / 0.773 /
  0.893 / 1.000.
  ```
- [x] **Nested tuning, 180 combinations** (`n_estimators` × `max_depth` ×
  ```
  `min_samples_leaf` × `min_samples_split`), `GridSearchCV` inside each outer
  training fold only, 3 subject-disjoint inner folds. Full unpruned `cv_results_`
  table (all 180 rows, both metrics) is in the report. **Tuned on ROC AUC, not
  F1/precision** — Stage 5.6's whole job is to replace the 0.5 threshold, so tuning
  a threshold-dependent metric would optimise a rule about to be discarded;
  `f1_macro` recorded per combination anyway. `GridSearchCV.best_score_` is
  explicitly **not** quoted as a generalisation estimate (it is the max over 180
  noisy estimates).
  ```
- [x] **Result: out-of-fold ROC AUC 0.832**, macro-F1 0.631 @0.5, Brier 0.154 → 0.149.
  ```
  Chosen params `n_estimators=500, max_depth=None, min_samples_leaf=2,
  ```

min_samples_split=10`.

- [x] **Finding — the search is a plateau, and that is the honest result.** The entire
  ```
  grid spans **0.0407** ROC AUC (0.8718–0.9125) while the **median std across inner
  folds is 0.0455 — larger than the whole span**; **163/180** combinations sit
  within 1 std of the winner. ET is _insensitive to these hyperparameters at this
  sample size_. Do not present the winner as a tuned optimum. Verified
  mechanistically: `max_depth` None/12/16 score **identically to 4 dp** because
  trees average depth 7.5 (max 13) and only **1 in 500** exceeds depth 12 — the
  constraint never activates; `min_samples_split≥10` on 98 reps binds first.
  ```
- [x] **Finding — Poor recall collapses 0.808 → 0.385 at the 0.5 threshold while AUC is
  ```
  unchanged.** Not a regression: `class_weight='balanced'` puts the raw forest's 0.5
  at the _reweighted_ boundary, and calibration correctly pushes P(Good) up toward
  the true 73% base rate, so fewer reps fall below 0.5. **The model misses ~62% of
  Poor reps at 0.5** — the worst failure mode for a rehab grader. **Handoff to Stage
  5.6:** its text sweeps `confidence_low_threshold` "above 0.5" as a _Fair band_,
  but the **decision boundary itself** also wants to move above 0.5. Those are two
  distinct knobs its checklist currently blurs into one. Not resolved here.
  ```
- [x] **Bug found by my own assertion, fixed properly.** The report claims calibration is
  ```
  monotone so AUC must be preserved; the assert fired (0.852 → 0.833). Root cause:
  `CalibratedClassifierCV` defaults to `ensemble=True`, averaging 3 forests each
  trained on 2/3 of the data — so the before/after figure was measuring _ensembling_,
  not calibration. Switched to **`ensemble=False`** (one forest + one sigmoid on
  out-of-fold scores), which also matches Stage 5.8's `model.joblib` +
  `calibrator.joblib` split. The assert then **still fired** — because it was at the
  wrong level: each of the 5 folds fits its _own_ sigmoid, so pooled predictions
  apply 5 different monotone maps and the pooled ranking legitimately shifts. Moved
  the assert **per fold**, where the property must hold, and it passes exactly on all
  5 (0.8889→0.8889, …). Both the wrong assertion and the reason are recorded in the
  report rather than quietly deleted.
  ```
- [x] **Calibration: sigmoid, not isotonic — N does not allow.** 26 Poor reps from 6
  ```
  subjects; isotonic would memorise. **Reported honestly as weak evidence:** Brier
  gains only 3% relative, neither curve tracks the diagonal (uncalibrated is
  under-confident at the top, sigmoid over-corrects mid-range), and with ~19 reps
  per bin **the two curves are not separated by more than their own uncertainty**.
  Switched the error bars from Wald to **95% Wilson** after noticing Wald collapses
  to _zero width_ at p=1 — two bins sit there and would have plotted as perfect
  certainty from 19 samples. Consequence for 5.6: the Fair band's real justification
  is the ranking (AUC 0.832), not demonstrated probability calibration.
  ```
- [x] **Answered Stage 5.4's two open questions, with model evidence.**
  - **Trained on all 13 features; DROP verdicts recorded, not executed** — both for
    scope (editing `SQUAT_FEATURE_NAMES` bumps `feature_schema_version`) and because
    5.4's verdicts used the held-out subjects' reps, so acting on them would be
    selection bias. **Two independent methods converged: Spearman rho = 0.775** between
    Gini importance and 5.4's univariate effect size; all three DROP features rank
    10/11/13 of 13. `**symmetry_index_pct` — the check that mattered passed:** despite
    correlating with mocap truth at r ≈ −0.05, the model did _not_ latch onto it as a
    subject fingerprint (rank 11, 0.0395). Still flagged for 5.8's model card.
  - **Redundant pair** `knee_flex_peak_deg` **~** `knee_rom_deg` **(r=0.97): keep both.** They
    rank 2nd/3rd (0.127, 0.104) — correlated features _split_ importance, so together
    depth accounts for ~0.23, on par with `ankle_df_proxy_deg`'s 0.24. One signal, two
    labels; ET is unbothered, and dropping either bumps the schema for no gain.
- [x] `**check_feature_validity.analyse_feature()` is imported, not transcribed** — the
  ```
  first draft hardcoded 5.4's AUCs into a table and **7 of 13 were wrong** (e.g.
  `stance_width_norm` written as 0.652, actually 0.374 with verdict
  _KEEP (caveat)_). Importing eliminated the whole class of error and keeps the two
  reports from diverging. Same discipline as X1.
  ```
- [x] **Verified:** X8 determinism — SHA-256 of the report and both figures byte-identical
  ```
  across consecutive runs (and again after formatting). Backend suite **136/136**
  via `python -m unittest discover -s tests` (unchanged; no backend file touched).
  `black` clean and `isort --profile black` clean — the profile matters, bare `isort`
  fails on every pre-existing `ml/` script too.
  ```
- [ ] **Deliberately not done (out of Stage 5.5 scope):** no artifact exported —
  ```
  `model.joblib`/`calibrator.joblib`/`feature_schema.json`/`model_card.md` are
  **Stage 5.8**'s deliverable, and `build_final_model()` is the entry point it should
  call so the model is defined in one place. No threshold chosen (the 0.5 used for
  the recall columns is a reporting convenience, **Stage 5.6** decides). No 3-band
  confusion matrix, latency, or baseline comparison (**Stage 5.7**). Permutation
  importance not run — Gini's ranking is enough to _corroborate_ 5.4, but if a
  feature is ever dropped on importance evidence, permutation is the measure that
  should justify it.
  ```

### Stage 5.6 — Fair threshold + fusion weight sweep

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision) item 1): this stage is where the Phase 4 Stage 4.0 `w_rule_default`/architecture-doc-§10.4 conflict actually gets settled — **empirically, not by picking one document over the other.** The selection criteria below are expanded beyond precision alone.

- [x] `**confidence_low_threshold**` (the Fair band): the R7 default of 0.65 is a **[proposed heuristic]**. Because Option A has only binary Good/Poor probabilities, sweep **only thresholds strictly above 0.5**, and include candidates above 0.65; pick against the calibration curve + the precision objective. Report the chosen value **and** the sweep — the number must be earned, not asserted.
  - [x] **Figure (required):** `figures/confidence_threshold_sweep.png` — precision/recall (or precision + Fair-band size) as a line plot against the swept threshold, with the chosen value marked (vertical line + annotation).
- [x] `sweep_fusion_weights.py` — sweep `w_r` from **0.2 → 0.8 in 0.1 steps** on the validation folds; report Good/Fair/Poor confusion + precision + **macro-F1** at each. **Selection criteria (HY 2026-07-16):** the winning weight must be justified against **both** (a) macro-F1 across the 3 bands, **and** (b) the **severe-misclassification rate** — the count/rate of Poor→Good and Good→Poor confusions specifically, tracked as its own number, not folded into an aggregate. A weight with slightly lower precision but a materially lower severe-misclassification rate is the better choice for a rehab-grading system (telling a poor-form user they're fine is the one failure mode that matters most); do not default to "highest precision wins" if it trades away severe-error safety.
  - [x] **Figure (required):** `figures/fusion_weight_sweep.png` — precision, macro-F1, **and severe-misclassification rate** (three lines) plotted against `w_r` from 0.2–0.8, chosen weight marked the same way as above.
- [x] Write the winner back into `backend/app/module_b/core/config.py`, replacing the 0.4/0.6 placeholder, and **retag it** `[dataset-derived]` (it is no longer a heuristic). Record in the report why this value won over both the Stage 4.0 default and the architecture doc's §10.4 recommendation, citing the actual macro-F1 and severe-misclassification numbers.
- [x] Output `ml/reports/SQUAT_FUSION_SWEEP.md` with all three figures/lines embedded.

### Phase 5 — Stage 5.6: Fair threshold + fusion weight sweep (2026-07-16)

- [x] `**ml/scripts/sweep_fusion_weights.py**` — reuses Stage 5.5's seeded `nested_cv()`
  ```
  verbatim for out-of-fold calibrated P(Good) (never re-tuned, never transcribed);
  calls the real, unmodified `app.module_b.core.fusion.fuse_scores()` for every
  candidate, patching `MODULE_B_CORE_CONFIG` in place and restoring in `finally`
  (same pattern as `check_norm_ref.py`). Evaluated **per repetition, not per
  session** (ground truth is per-rep; production fuses per-session via
  `score_squat_set()` + rep-0-only ML score — an existing Phase 4 decision, not
  redesigned here) — stated explicitly so the confusion counts aren't misquoted at
  the wrong granularity. Real per-rep `q` computed from raw (pre-preprocessing)
  frames via the live `assess_capture_quality()`, not assumed: q ranged
  [0.828, 0.930], **0/98 below q_min=0.6** — capture-quality forcing is confirmed
  not to confound the sweep.
  ```
- [x] **Major finding: the naive single-pass ordering is Poor-blind, and it's
  ```
  mechanistic, not a fluke.** Running the checklist's literal ordering once
  (threshold swept at the Stage 4.0 default weight 0.4/0.6, then weight swept at
  that threshold) found **precision(Poor) undefined at every one of the 9
  threshold candidates** — no repetition could ever be banded Poor at `w_rule=0.4`,
  at any threshold. Root cause, verified not assumed: `rule_score`'s ROM component
  rewards greater knee flexion, but Stage 5.4/5.5 already found **incorrect reps
  are deeper** in this population, so `rule_score` runs backwards relative to
  correctness — median **8.83 for Poor vs 7.71 for Good**, floor 6.43 for anyone.
  Even the single most confidently-Poor rep in the dataset (P(Good)=0.134,
  rule_score=9.71) fused to ~4.7 at `w_rule=0.4` — Fair, never Poor.
  ```
- [x] **Fix: iterated joint search, not a single pass.** Alternates the threshold sweep
  ```
  and weight sweep, feeding each round's winner into the next, until neither moves
  (`find_stable_operating_point()`, bounded at `MAX_ROUNDS=6`). **Converged after 3
  rounds:** round 1 (input 0.4) → threshold 0.55 → weight 0.2; round 2 (input 0.2)
  → threshold 0.85 → weight 0.2; round 3 confirms the same pair. This is standard
  coordinate ascent over the two sweeps the checklist already specifies — no new
  sweep dimension, only recognising they must be resolved jointly. The naive
  round-1 answer is kept in the report (not discarded) alongside why it was revised.
  ```
- [x] **Fusion-weight selection rule corrected to match HY's literal wording.** Initial
  ```
  draft summed Poor→Good + Good→Poor into one "severe count" for the primary key;
  re-read HY's criterion ("Poor→Good ... is the one failure mode that matters
  most") and fixed `_pick_fusion_weight()` to use **Poor→Good alone** as the
  primary key (summing would let a rise in the worse failure mode hide behind a
  fall in the milder one), with Good→Poor then macro-F1 breaking ties (within-1
  margin at n=98, since a single event either way is sampling noise).
  ```
- [x] **Result (converged): `confidence_low_threshold = 0.85`, `w_rule = 0.2`,
  ```
  `w_ml = 0.8`.** At this point: precision(Good)=1.000, precision(Poor)=1.000,
  **0 severe misclassifications** (0 Poor→Good, 0 Good→Poor), macro-F1=0.481,
  Fair-band coverage=0.469 (46/98 reps abstain) — a deliberate, large safety
  trade-off, not hidden.
  ```
- [x] **Both the Stage 4.0 placeholder (0.4) and the architecture doc's §10.4
  ```
  recommendation (0.6) also reach 0 severe misclassifications at the converged
  threshold — but not for the same reason, and this distinction is the actual
  reason macro-F1 mattered in selection.** At `w_rule=0.4`/`0.6`, `recall(Poor)=0`:
  every Poor rep is safely routed to Fair, **none is ever correctly identified as
  Poor**. At the chosen `w_rule=0.2`, some Poor reps are correctly caught
  (`recall(Poor)=0.077`) with the same 0 severe count. Severe-count alone would
  have missed this; macro-F1 (0.481 vs 0.410) is what distinguishes "safe but
  blind" from "safe and somewhat informative."
  ```
- [x] **Config updated and retagged:** `backend/app/module_b/core/config.py` —
  ```
  `w_rule_default: 0.4→0.2`, `w_ml_default: 0.6→0.8`,
  `confidence_low_threshold: 0.65→0.85`, all retagged `[dataset-derived, Stage
  ```

5.6]`with the reasoning inline.`w_rule_low_confidence`(0.7) and`q_min` (0.6)
untouched (out of scope).

- [x] **Two backend tests updated, both real fixes not bent to pass:**
  ```
  `test_module_b_registry.py`'s single `test_core_config_freezes_stage_4_0_values`
  split into `test_core_config_freezes_still_unresolved_stage_4_0_values`
  (everything Stage 5.6 didn't touch) + a new
  `test_core_config_stage_5_6_dataset_derived_fusion_values` (the three changed
  values); `test_module_b_fusion.py`'s
  `test_model_fusion_carries_model_version_and_default_weights` bumped its
  `StubModel(rule_score=8.0)` to `9.0` so its resulting confidence (0.9) still
  clears the new 0.85 bar and actually exercises the default-weight path, rather
  than silently falling into the already-covered low-confidence branch.
  ```
- [x] **Verified:** X8 determinism — SHA-256 of the report and both figures
  ```
  byte-identical across consecutive runs, including after formatting. Backend
  suite **137/137** (136 + 1 net new, from the registry-test split) via
  `python -m unittest discover -s tests`. `black` clean, `isort --profile black`
  clean.
  ```
- [ ] **Deliberately not done (out of Stage 5.6 scope):** `band_thresholds` (D6,
  ```
  Poor/Fair/Good score cut points) unchanged — a separate, already-fixed
  heuristic this stage doesn't touch. No 3-band confusion-matrix figure, baseline
  comparison, or latency measurement (Stage 5.7). No artifact export (Stage 5.8).
  The grid's own lower boundary (`w_rule=0.2`) won outright — the trend suggests
  going lower might help further, but extending below the checklist's specified
  0.2–0.8 range would be scope creep; flagged for reconsideration, not acted on.
  ```

### Stage 5.7 — Evaluation

**Completed 2026-07-16.** `ml/scripts/evaluate_squat.py` → `ml/reports/SQUAT_EVALUATION_REPORT_3BAND.md`
(renamed in Stage 5.11; 4 figures); `backend/app/module_b/core/evaluation/replay_squat_session.py` +
`ml/scripts/generate_squat_replay_corpus.py` → 7-sample corpus committed to
`backend/app/module_b/replay_corpus/squat/`; `backend/tests/test_module_b_replay.py`
(9 tests, incl. `SquatDeterminismTests`).

- [x] `evaluate_squat.py` → `ml/reports/SQUAT_EVALUATION_REPORT_3BAND.md`:
  - [x] Accuracy, **Precision (emphasised)**, Recall, **Macro-F1**, per-class + macro.
    ```
    **Accuracy is reported twice under two named definitions, and neither is
    presented as the headline** — on a 3-band output over binary ground truth it is
    genuinely ambiguous. `accuracy_strict = 0.531` counts Fair as wrong (punishes
    the abstention Stage 5.6 bought on purpose); `accuracy_confident = 1.000`
    excludes Fair (a system abstaining on 97/98 reps and getting the last right
    would also score 1.000). The pair is the honest summary: **the system commits
    on 52/98 reps (53.1%) and is right 100% of the time when it does.** Macro-F1
    0.481, macro precision 1.000, macro recall 0.386.
    ```
  - [x] **Confusion matrix** over the final fused 3-band output. Good→Good 50, Good→Fair
    ```
    22, Good→Poor 0; Poor→Good 0, Poor→Fair 24, Poor→Poor 2. **Both severe cells are
    0 — but this is consistent with Stage 5.6, not independent evidence for it**
    (same out-of-fold predictions selected the operating point). Reported because
    its absence would signal a bug.
    ```
    - [x] **Figure:** `figures/confusion_matrix_3band.png` — 2×3, deliberately
      ```
      non-square: ground truth has no Fair class, so that column is an abstention,
      not a class that can be right or wrong. Stated on the figure itself.
      ```
  - [x] **`error_tags` multi-label F1 NOT computed — two independent reasons, the second
    ```
    found by reading the code and not in this checklist.** (1) REHAB24-6 is binary,
    no per-fault ground truth. (2) **`router.py` never calls `exercise.error_tags()`
    at all**: `SquatExercise.error_tags()` raises `NotImplementedError`, and only
    the system flags (`low_confidence`/`low_capture_quality`/
    `retry_camera_placement`) from `_system_error_tags()` are persisted, movement
    taxonomy deferred to Stage 6. **Neither a prediction nor a reference exists.**
    ```
    - [x] **Figure deliberately NOT produced:** `figures/error_tag_performance.png` —
      ```
      per this checklist's own instruction not to fabricate bars for tags with no
      ground truth. EC3D (5.9) is the only honest source.
      ```
  - [x] **Robustness signals — the headline finding of this stage.**
    ```
    **Low-confidence-frame frequency is saturated: 87/98 reps (89%) have NOT ONE
    fully-valid frame** (median 100%). A metric pinned at its worst value for 89% of
    the data cannot discriminate a good capture from a bad one — **it must not be
    used as a robustness gate as it stands.** Cause measured, not assumed: sampling
    rep `PM_008#1` (first in sorted order, fixed choice), far-limb R_knee median
    visibility **0.396 (121/121 frames below threshold)** and R_ankle 0.598 (68/121)
    vs near-limb 0.98–0.99 — and `valid_frame_ratio` requires **all 8** landmarks to
    clear the bar simultaneously, so one occluded landmark zeroes the whole rep.
    Safety flags: `low_confidence` 46.9%, `low_capture_quality` **0.0%**,
    `retry_camera_placement` 0.0%.
    **⚠ New limitation: `q` is blind to this capture geometry's dominant failure.**
    q range [0.828, 0.930], **0/98 below `q_min=0.6`** — because `q` is a _mean_ over
    the 8 landmarks and the 4 near-side ones are tracked near-perfectly. The far limb
    can be entirely invisible while `q` stays "good".
    ```
    - [x] **Figure:** `figures/robustness_signals.png` — histogram (not a mean) + flag
      ```
      rates. The saturation spike at 100% is the point.
      ```
  - [x] **Inference latency measured:** median **8.11 ms**, p95 **9.10 ms** vs a 33.3 ms
    ```
    single-frame budget at 30 FPS (~3.7× headroom). Median of 5 timed repeats per
    rep. **Scope stated: excludes pose estimation and preprocessing** (per-frame
    browser costs); this is the per-rep cost the backend adds at the end of a set.
    Supports "the analysis layer is not the bottleneck", **not** "the whole system
    runs in real time".
    **⚠ X8 carve-out, stated in the report rather than left to be discovered:
    latency is the ONE Phase 5 output that is not byte-reproducible.** Wall-clock
    cannot be. Verified: every other metric and all 3 other figures are byte-
    identical across runs; only this section varies.
    ```
    - [x] **Figure:** `figures/inference_latency_distribution.png` — x-axis scaled to the
      ```
      data. The 33.3 ms budget is annotated, **not drawn as a line**: drawing it set
      the x-limit ~4× wider than the data and crushed the whole distribution into one
      invisible spike — the reference line destroyed the plot it was meant to
      contextualise.
      ```
  - [x] **Baseline comparison:** `0.7347` **(subject-wise) vs [S13] ~0.93 (non-subject-wise).**
    ```
    The comparable quantity is the **binary classifier's** accuracy, not the fused
    3-band system's — a published classifier cannot abstain.
    **⚠ Our accuracy exactly equals the Good base rate (72/98 = 0.7347). This is a
    coincidence, NOT a degenerate always-predict-Good classifier, and the report
    proves the difference:** the model predicts Poor for 20/98 reps and is right
    about 10 — it buys 10 correct Poor calls at the price of 10 Good reps it now gets
    wrong, netting +0. It breaks even. The model has learned something (AUC 0.832);
    accuracy is simply the wrong summary for an imbalanced problem.
    ```
    - [x] **Figure:** `figures/baseline_comparison_bar.png` — the "NOT AN APPLES-TO-APPLES
      ```
      COMPARISON" caveat is drawn **inside the axes** so a screenshot carries it.
      ```
- [x] **Q4 remains OPEN — the REHAB24-6 authors' own baseline is deliberately NOT quoted.**
  ```
  The checklist says to extract their protocol from the SISAP 2024 paper [S12] first.
  Attempted: the Springer chapter is paywalled (auth redirect, not followed), the
  Zenodo record carries no baseline results, and no open-access version was found.
  Per Q4's own instruction ("do not silently resolve them by assumption") **no number
  was invented for it** — the comparison rests solely on [S13], which `task.md`
  itself supplies. Extend §6 of the report if the paper becomes available.
  ```
- [x] **Deterministic replay harness** (Module A Stage 7 parity):
  - [x] `backend/app/module_b/core/evaluation/replay_squat_session.py` — `--json-file`
    ```
    (full replay: quality→preprocess→segment→features→rules→fuse, asserts two fresh
    runs identical), `--session-id` (partial), `--corpus` (replays all 7 samples and
    checks them against `labels.json`).
    ```
  - [x] `ml/scripts/generate_squat_replay_corpus.py` → 7 committed samples: 2 Good, 2
    ```
    Fair, 2 Poor, 1 low-Q reject. Fixed seed (20260716), byte-identical on
    regeneration. 3.6 MB, in line with Module A's SLS corpus (3.4 MB).
    **The manifest records the MEASURED band, not a hand-written expectation** —
    every sample is run through the real pipeline at build time. This caught two real
    bugs immediately: both Poor specs landed in Fair, and reps were being silently
    dropped (1 and 2 segmented instead of 3 and 4).
    ```
  - [x] Backend `SquatDeterminismTests` (+ corpus/harness tests): 9 tests. Suite
    ```
    **146/146** (was 137).
    ```
  - [x] **The WBLT caveat applies, and is strictly stronger for Module B: there is no
    ```
    `module_b_landmark_log` table at all.** Module B **never persists frames** by
    design — `crud.save_result()` stores "the exact analyzed snapshot without
    persisting browser frames/video". So `--session-id` can only replay **rules +
    fusion** from the `FeatureVector`s stored in `metrics_json`; preprocessing,
    segmentation and feature extraction are unreplayable from the DB. (WBLT loses
    _which attempt_; Module B has no frames at all.) `--session-id` also **reports**
    rather than asserts drift vs the stored snapshot: `router.py` treats stored
    results as historical and never recomputes them, and Stage 5.6 moved the fusion
    weights, so any pre-5.6 session legitimately re-derives differently — asserting
    equality would turn a correct config change into a crash.
    ```

**Findings for later stages (recorded, not acted on):**

- **Under** `StubModel`**,** `score == rule_score` **exactly** (P(Good)=rule/10 ⇒ ml_score=rule,
  weights sum to 1). With `confidence_low_threshold=0.85` the only reachable bands are
  Poor (`rule<1.5`), Fair (`1.5≤rule≤8.5`, always via `low_confidence`) and Good
  (`rule>8.5`) — **the Fair _score band_ (4.0–7.0) is currently unreachable**; every Fair
  is an abstention. **Stage 5.8 replaces** `StubModel` **and these bands move — regenerate
  the corpus then, do not hand-patch** `labels.json`**.**
- **One Euro's speed-adaptive cutoff couples whole-body translation to angle smoothing.**
  Measured while building the corpus: raw peak knee flexion is identical (36.19°) at sway
  0.0 and 0.4, but the _preprocessed_ peak moves 35.44°→36.44° — enough to change how many
  reps segment. Larger sway ⇒ higher velocity ⇒ wider cutoff ⇒ _less_ smoothing. Sway and
  depth are not independent downstream, only in the raw pose.
- `**_release_persistent_occlusions` preserves coordinates for a wholly-occluded landmark**
  (raises visibility to `MIN_VISIBILITY` rather than dropping it), which is why the low-Q
  corpus sample still segments 3 reps at visibility 0.45 and is rejected on `q`, not on
  a broken skeleton.

**Deliberately not done (out of Stage 5.7 scope):** `q_min`/`confidence_threshold`
unchanged despite §4's finding that `q` is blind to far-limb occlusion and
`valid_frame_ratio` is saturated — **flagged for Stage 5.8's model card and a future
quality-metric revision, not fixed here.** ROM band edges still untouched (see 5.6).
No artifact export, no `StubModel` deletion (Stage 5.8). No EC3D (Stage 5.9).

### Stage 5.8 — Export + backend integration

**Completed 2026-07-16.** `ml/scripts/export_squat_model.py` → `ml/artifacts/squat/{model.joblib,calibrator.joblib,feature_schema.json,model_card.md}` +
updated `ml/artifacts/label_map.json`; `core/model_registry.py` loads the real bundle,
`StubModel` deleted; `router.py`/`replay_squat_session.py`/
`generate_squat_replay_corpus.py` all switched to it; backend suite **150/150**
(was 146); verified live against the real Postgres container + a running backend.

- [x] Export to `ml/artifacts/squat/` (**committed**): `model.joblib` (the fitted
  ```
  Extra Trees forest), `calibrator.joblib` (a plain `{"a":..., "b":...}` dict —
  **not** sklearn's private `_SigmoidCalibration` object, deliberately, so the
  calibrator file doesn't depend on a private class surviving a future sklearn
  upgrade), `feature_schema.json` (names + order + `schema_version` +, since this
  file is created fresh by this stage and owned by no earlier one,
  `model_version`), and the extended `label_map.json` (now carries `label_order`,
  needed by the loader). `model_card.md` **links** to Stage 5.5/5.7's confusion
  matrix, calibration and robustness figures by relative path — does not
  regenerate or duplicate them.
  **The split is verified, not assumed:** `_verify_recomposition()` asserts
  `np.array_equal` between the untouched `CalibratedClassifierCV.predict_proba()`
  and the forest+sigmoid recomposition (`P(Good)=1/(1+exp(a·raw_p_good+b))`) on
  the real training matrix before anything is written — confirmed bit-for-bit
  identical (max abs diff `0.0`). Byte-identical on regeneration (X8).
  ```
- [x] `model_version = squat-1.0.0+rehab246-loso-3c441ac.dirty` — a real
  ```
  `git rev-parse --short HEAD`, `.dirty`-suffixed (uncommitted changes present at
  export time) rather than falsely implying an exact committed snapshot.
  ```
- [x] `core/model_registry.py`: `StubModel` **deleted**, not left behind.
  ```
  `_CalibratedForestClassifier` composes the two files back into calibrated
  probabilities; `get_model_bundle(model_key)` is the `lru_cache`d, load-once
  accessor, keyed by `model_key` (not hardcoded to squat) so a future exercise's
  own artifact directory is picked up without a router change. `router.py`,
  `replay_squat_session.py` (both `--json-file` and `--session-id` paths) and
  `generate_squat_replay_corpus.py` all switched to it. The placeholder notice in
  `Report.tsx` is now unreachable (`is_placeholder=False` on every live result)
  without any frontend change — the mechanism is generic and stays for any future
  placeholder model.
  **Backend now depends on `scikit-learn`/`numpy`** (added to
  `backend/requirements.txt`, unpinned floor matching `ml/requirements.txt`) —
  `joblib.load()` of a fitted sklearn model requires the library to be importable;
  this was a real, previously-latent gap in Stage 4.5's `load_joblib_model_bundle`
  scaffolding, only surfaced once a real artifact was actually loaded.
  ```
- [x] Schema guard fires on mismatch (Stage 4.5): re-verified against the **real**
  ```
  bundle (`test_module_b_fusion.py::RealSquatModelBundleTests`), not only the fake
  classifier the Stage 4.5 tests originally used.
  ```
- [x] **Verified live end-to-end**, against the real `fyp_postgres` docker container
  ```
  and a real running `uvicorn` backend (no browser/webcam available to this agent,
  so this is the most rigorous available proxy): registered a test user via
  `/api/auth/register`, started a real squat session via `/api/sessions/start`,
  POSTed a realistic frame stream to `/api/module-b/analyze`. Result:
  `model_version="squat-1.0.0+rehab246-loso-3c441ac.dirty"`,
  `placeholder_model_notice=false`, band/score derived from the real model — and
  the **same** `model_version` confirmed directly in the `module_b_results` table
  via SQL, and via `GET /api/module-b/results/{id}`. The `--session-id` replay
  path was also run against this real, live session and reproduced the stored
  score/band/rule_score exactly.
  ```

**⚠ Major finding, not anticipated by this checklist: the shipped model may never
return a confident "Poor" verdict for squat, for any input.** Checked directly
(`export_squat_model.py::_deployed_confidence_check`) against every row in its own
98-repetition training set: the single most Poor-leaning row reaches only
P(Good)=0.244 (confidence 0.756), short of the 0.85 bar `confidence_low_threshold`
requires. **Zero of 98 training rows clear it.** This is distinct from — not a
contradiction of — Stage 5.7's reported recall(Poor)=0.077: that figure describes the
5-fold **nested cross-validation** pooled estimate (5 different fold-specific
calibrations, min P(Good)=0.134, 2/26 caught), an estimate of generalisation. This
in-sample check is the first point the **actual shipped calibration** could be
examined directly, and it is more conservative than that estimate suggested. A
deliberate geometry sweep while rebuilding the replay corpus (below) could not
reach a confident Poor synthetically either (closest: P(Good)≈0.50). Recorded
prominently in `model_card.md`'s limitations section, not silently shipped.

**Consequence — the replay corpus was substantially rebuilt, not just re-run:**

- The original Stage 5.7 corpus was designed against `StubModel`'s analytic
  `score == rule_score`, which rewards depth. The real forest learned the opposite
  relationship for this population (incorrect reps are deeper — Stage 5.4/5.5/5.6),
  so the old "deep + unstable = Poor" specs now read as confidently **Good** or merely
  uncertain. All 7 specs were rebuilt from the real model's actual Good/Poor feature
  statistics; the two "attempted Poor" samples are kept as the closest approach found
  (`target_band_hint="Fair"`, honestly), not as a working Poor fixture.
- `test_corpus_spans_every_reachable_band_plus_a_low_quality_reject` now asserts
  `{"Good", "Fair"}`, with the finding above recorded inline — asserting the old
  `{"Good","Fair","Poor"}` would assert something the shipped model cannot currently
  do.
- Corpus remains byte-identical on regeneration (X8); all 9 `test_module_b_replay.py`
  tests + the `--corpus` CLI check still pass against the rebuilt manifest.

**Deliberately not done (out of Stage 5.8 scope):** the ROM rule / `q` capture-quality
blind spot (Stage 5.7 findings) are unchanged — this stage exports and wires the
classifier, it does not revisit the rule engine or the quality metric. No EC3D
validation (Stage 5.9). No fix attempted for the Poor-unreachability finding above; it
is recorded for Stage 5.9/examiner visibility, not acted on — fixing it would mean
re-touching calibration or the training data split, outside this stage's checklist.

### Stage 5.9 — EC3D external validation _(the firewall pays off here)_

Under Option A, EC3D was **never touched by training** — so it is a legitimate independent generalisation check. Protect that.

- [x] **Confirm EC3D's 25-joint index order from the repo's data-loader before trusting any mapping.** This is a known open question (see Q3) and the "knee-passes-toe" lunge feature depends on it. Empirical fallback: plot one frame's 25 points and label limbs. Write `ml/docs/ec3d_joint_mapping.md`.
- [x] `validate_ec3d.py` — map EC3D 25 → MediaPipe-33 for hip/knee/ankle/shoulder, recompute the **angle-based features only**, score with the trained model, report metrics.
  - [x] **Figure (required):** `figures/ec3d_confusion_matrix.png` — same style as `confusion_matrix_3band.png` in Stage 5.7, so the two are visually comparable side by side in the write-up.
  - [x] Output `ml/reports/EC3D_VALIDATION_REPORT.md` with the figure embedded and the 4-subject caveat stated directly beneath it, not just in surrounding prose.
- [x] **Honest scoping:** EC3D has **4 subjects** — this is an external _check_, never a headline generalisation claim. Say so in the report.
- [x] **Do not evaluate frontal-plane features here.** EC3D has true 3D, so a valgus feature would score well — and would be meaningless, because that feature doesn't exist in your monocular runtime. (Moot given the side-only decision, but state it: it's the reason the decision is right, and it belongs in the write-up.)

### Phase 5 — Stage 5.9: EC3D external validation (2026-07-17)

**Completed, and the result is a documented NEGATIVE one.** Every checklist item is
built and run; the honest conclusion is that **EC3D cannot serve as a generalisation
check for this model**, for three independently measured reasons. The report says so in
its first paragraph rather than reporting a number that would not mean what it appears
to mean. `ml/scripts/validate_ec3d.py` → `ml/reports/EC3D_VALIDATION_REPORT.md` +
`figures/ec3d_confusion_matrix.png`; `ml/docs/ec3d_joint_mapping.md` closes **Q3**.
Backend suite unchanged at **150/150**. Deterministic (X8): report + figure verified
byte-identical across consecutive runs.

- [x] **Q3 RESOLVED — EC3D is OpenPose** `BODY_25`**, proven empirically, not assumed.**
  ```
  The repo's README documents the pickle's shape but **not** its joint order and
  names no skeleton format, so the checklist's primary route (the repo's
  data-loader) does not exist; the order was recovered from the data by four
  independent checks, each recorded in `ml/docs/ec3d_joint_mapping.md`:
  (1) **every** published `BODY_25` tree edge is rigid across the 10,283 squat
  frames at an anatomically sensible length (thigh 0.1403 / shank 0.1357 / torso
  0.1954, CV 0.00007–0.00173); (2) the **decisive** test — each foot triad's ankle
  attachment splits exactly along `BODY_25`'s grouping with a ~130× rigidity margin
  (j19/20/21→j14 at CV ~0.0015 vs ~0.21 against j11; j22/23/24→j11 likewise), heel
  nearest its ankle and big toe furthest; (3) j08 is **exactly** (0,0,0) in every
  frame — only `MidHip` is a plausible root; (4) two unrelated anatomical checks
  agree that axis 1 is anterior (big-toe-minus-heel +0.075/+0.067; nose-minus-ear
  +0.047). Source confirmed as Zhao et al., ACCV 2022 — the paper's own
  `(29789, 3, 25)` shape, 4 subjects, 30 fps and **132 squat sequences** all match
  the file.
  ```
- [x] **Left/right handedness is unresolved — and proven not to matter here.** Whether
  ```
  `BODY_25`'s "R" joints are anatomically right depends on a handedness convention
  the pickle does not record. Rather than guess, this was tested: swapping the L/R
  halves of the mapping and re-extracting leaves **all 13 features bit-identical**
  (max |delta| = `0.0` over all 132 reps) — every squat feature is a both-legs mean,
  an `abs()` difference, a midpoint, or an inter-ankle distance. **⚠ Does not extend
  to Phase 5B:** a lunge's lead leg is side-specific, so `knee_passes_toe` needs
  this resolved first.
  ```
- [x] **Label 10 excluded, with a reason.** Sena alone has 9 extra squat episodes under
  ```
  an undocumented label 10; excluding it leaves exactly the paper's **132**. The
  script asserts that count at load time, so a changed pickle fails loudly instead
  of quietly reporting different numbers.
  ```
- [x] **`validate_ec3d.py` maps the 8 `REQUIRED_LANDMARKS` joints and runs the LIVE
  ```
  extractor (X1)** — `preprocess_world_landmarks` + `extract_squat_features`, never
  re-implemented — then scores the **shipped artifact** through the backend's own
  `get_model_bundle("squat")` and the real `fuse_scores()` at the shipped config
  (`w_rule=0.2`, `w_ml=0.8`, `confidence_low_threshold=0.85`). Nothing re-tuned.
  EC3D's own episode boundaries are used as rep windows (its instructed
  repetitions), mirroring Stage 5.3's use of REHAB24-6's physio-verified
  `first_frame`/`last_frame`; re-segmenting would measure the FSM, not the model.
  `visibility=1.0` and `q=1.0` because mocap joints are fully observed — stated in
  the report, not left implicit. Timestamps from the paper's 30 fps (the pickle
  stores only a frame index).
  ```
- [x] **Figure reuses Stage 5.7's plotter rather than forking it.**
  ```
  `plot_confusion_matrix_3band()` gained `dataset_label`/`subtitle`/`name` kwargs
  whose defaults reproduce the 5.7 figure — verified **byte-identical**
  (`c2f89f7c…`) after the refactor. The checklist requires the two figures to be
  comparable side by side; a copied plotter cannot guarantee that over time. (Only
  `SQUAT_EVALUATION_REPORT_3BAND.md`'s latency lines differ between runs, which 5.7
  already documents as its one non-reproducible output — confirmed by diffing two
  consecutive runs: 12 lines, all latency.)
  ```

**⚠ Finding 1 — EC3D's poses are canonicalised, not raw mocap.** Measured, not inferred:
mid-hip max abs coordinate `**0.0**` (root-centred); neck up-axis std `**4.7e-17**`,
pinned at 0.19517662, and anterior-axis std `**0.0**`, in all 11,109 squat frames under
**every** label including "Front bent" (orientation-normalised); per-subject thigh length
spread **0.160%** across four different people (one **template skeleton** — all
inter-subject anatomy is gone). Three-point joint angles survive this (invariant to rigid
transforms) and are physiologically plausible. Gravity-referenced and global-translation
features do not: `trunk_lean_peak_deg` collapses from a REHAB24-6 mean of ~~35–44° to
**~~3–4°**, and the "Front bent" class shows **no more** trunk lean than the Correct class
— the one fault the feature exists to detect is erased by the normalisation.
`hip_mid_jitter_norm` ≈ 0 for every rep. **The checklist's own "angle-based features
only" heuristic does not survive contact with this:** `ankle_df_proxy_deg` _is_
angle-based and is the model's single most important feature (Gini **0.2388**), but it is
an angle against **gravity**, so it does not transfer either. The distinction that
actually matters is **intrinsic (rigid-transform-invariant) vs world-referenced**.
Recovering the lost orientation (fitting a ground plane from the feet, un-rotating each
frame) was considered and **rejected**: it would feed an invented estimator's
unquantified error into the model's most important feature and still could not restore
`hip_mid_jitter_norm` or per-subject anatomy — the invented-methodology trap this project
has already been caught by once.

**⚠⚠ Finding 2 — the two datasets disagree about what "incorrect" means. This is the
decisive one.** REHAB24-6's incorrect squats are **deeper** than its correct ones
(established at 5.4/5.5/5.6 — the reason the ROM rule had to be down-weighted). EC3D's
fault taxonomy contains **"Not low enough"**, so its incorrect squats are **shallower**.
**56.7% of the forest's Gini importance mass sits on features whose Good/Poor direction
inverts between the two datasets** (`knee_rom_deg` REHAB AUC 0.86 → EC3D 0.42;
`knee_flex_peak_deg` 0.84 → 0.42; `hip_flex_peak_deg` 0.78 → **0.24**;
`stance_width_norm` 0.37 → 0.66). An inverted feature is worse than a missing one — the
model does not abstain on it, it reads the evidence confidently the wrong way round. The
sharpest evidence is the outcome, not the table: **of the 21 "Not low enough" reps the
system called 17 (81.0%) Good; of the 41 genuinely Correct reps it called only 7 (17.1%)
Good — it is 4.7× more likely to approve the shallow fault than a correct squat.** No
threshold change fixes that; the ordering itself is wrong for this population. This is
not a bug in either dataset — it is evidence the model learned a **population-specific**
notion of squat correctness, and it is arguably the most useful thing this stage
produced.

**⚠ Finding 3 — half of EC3D's fault class is invisible to this system by design.** Of
EC3D's four squat faults, **"Feet too wide" (23 reps) and "Knees inward" (23 reps) are
frontal-plane** — **46 of the 91** faulty reps. Locked Assumption #3 drops frontal valgus
as monocular-infeasible: no valgus feature, tag or rule exists anywhere, deliberately.
Those reps are still labelled incorrect in EC3D's ground truth, so the system is marked
wrong for failing a test it was explicitly designed never to sit. The checklist's
instruction ("do not evaluate frontal-plane **features**") was aimed at not _crediting_
the model for a valgus feature it lacks; the sharper problem is the reverse — EC3D's
fault **class**, not just its features, is substantially frontal.

**Result (reported for completeness; NOT a generalisation estimate, in either
direction):** `accuracy_strict` **0.053**, `accuracy_confident` **0.184**, `macro_f1`
**0.089**, `fair_rate` **0.712**, `recall_good` 0.171, `**recall_poor` 0.000**, n=132.

- [x] **Stage 5.8's headline finding independently corroborated on unseen subjects.**
  ```
  `recall_poor` is **exactly 0.000**: not one confident Poor across all 91 faulty
  reps. P(Good) never fell below **0.618** (range 0.618–0.942), so confidence toward
  Poor never exceeded 0.382 against the 0.85 bar. Stage 5.8 measured this **in-sample**
  on the model's own 98 training rows (min P(Good) 0.244); EC3D reproduces it on **4
  subjects it has never seen, from a different dataset on different hardware**. Two
  unrelated methods, same conclusion — the model effectively cannot reach Poor.
  ```
- [x] **`accuracy_confident` = 0.184 is BELOW chance, and that is the signature of
  ```
  inversion, not noise.** A model reading uninformative features lands near 0.5 on
  what it commits to, or abstains. This one commits to 38 reps and is wrong on 81.6%
  of them. It is not confused; it is confidently backwards. Finding 2 is why.
  ```

**Deliberately not done (out of Stage 5.9 scope), each with its reason:**

- [ ] **No fix attempted for Findings 1–3.** They are recorded for examiner visibility.
  ```
  Fixing Finding 2 means retraining on a different label construct; fixing Finding 1
  needs raw EC3D mocap, which is not published.
  ```
- [ ] **No intrinsic-features-only model trained.** A parallel model over just the
  ```
  rigid-transform-invariant features _could_ be scored on EC3D honestly and is the
  only route to a real external number — but training is Stage 5.5's checklist, not
  this one's, it would be a **different artifact from the one that ships**, and it
  would still face Finding 2's label-construct mismatch. **Flagged for HY as the one
  genuine option this stage leaves on the table.**
  ```
- [ ] The ROM rule / `q` blind spot (5.7 findings) and the Poor-unreachability finding
  ```
  (5.8) are unchanged — this stage validates, it does not revisit them.
  ```
- [ ] EC3D's **Lunges** (127 sequences, incl. label 6 = "Knee passes toe") were not
  ```
  touched. Phase 5B's scope, not this stage's.
  ```

### Phase 5 — Stage 5.11: Committed binary Good/Poor squat output (2026-07-19)

**HY's call (2026-07-19) — a decision/product change, not a retrain.** The squat model was
already binary (Option A: `correctness` → Good/Poor); the three visible bands came entirely
from the backend fusion layer, where **Fair is an abstention** forced whenever model
confidence < 0.85. Because the shipped model's confidence never exceeds ~0.76 (Stage 5.8),
that override fired on almost every rep and "Poor" was effectively never shown (3-band
recall(Poor) ≈ 0.077). HY chose to make squat **commit** to Good/Poor so the app can flag
poor form, accepting the loss of the zero-severe-error guarantee.

- [x] **No retrain.** `model.joblib`/`calibrator.joblib`/`feature_schema.json` unchanged and
  ```
  byte-identical; `model_version` unchanged. The forest+sigmoid reproduce identically (X8),
  so re-fitting was deliberately skipped — this stage chose a _decision policy_, not a model.
  ```
- [x] **Operating point tuned** — `ml/scripts/tune_squat_binary_band.py` (new): imports Stage
  ```
  5.5's seeded `nested_cv()` OOF calibrated P(Good) (X1) and the real `fuse_scores`, sweeps
  `(w_rule, score_threshold)` for **max macro-F1** (HY's "Balanced" pick; on this data it
  coincides with the max-Youden / balanced-accuracy point). Winner: **w_rule=0.0, w_ml=1.0,
  decision_threshold=8.447974** (median of the winning plateau; since w_rule=0 the score is
  `10·P(Good)`, so the cut is P(Good) ≥ 0.8448 → Good). Sanity-asserted: recall(Poor) > 0,
  and Poor-banded reps have lower mean P(Good) than Good-banded (guards the lunge-derived
  inverted-verdict hazard at the band level). Deterministic — two runs identical.
  ```
- [x] **The tradeoff, chosen with real numbers in front of HY** (the AUC-0.83 overlap means
  ```
  you cannot get both high poor-recall and few false alarms): at the chosen point
  **recall(Poor)=1.000, recall(Good)=0.694, macro-F1=0.761, severe=22 (Poor→Good 0, Good→Poor 22)**. No poor-form rep is ever called Good; 22/72 (31%) of Good reps are flagged Poor. HY
  picked the aggressive/safety-first point over Moderate (thr 7.0) and Conservative (thr 5.0).
  ```
- [x] **Backend** — per-exercise `band_policy` in `SQUAT_CONFIG` threaded through
  ```
  `fuse_model`/`fuse_scores` (`backend/app/module_b/core/fusion.py`); `band_policy=None`
  (default) preserves the 3-band abstention byte-for-byte for Module A + lunge, and a
  placeholder model always keeps abstaining even under a binary policy. `router.py` passes
  `exercise.band_policy`; base `ModuleBExercise.band_policy` defaults to None, `SquatExercise`
  returns the binary dict. No DB change (`band` is already unconstrained `String(50)`).
  ```
- [x] **Reports** — new `ml/reports/SQUAT_EVALUATION_REPORT_2BAND.md` +
  ```
  `figures/confusion_matrix_2band.png` (via a parameterised
  `evaluate_squat.plot_confusion_matrix_3band`, 3-band default byte-identical); the old
  `SQUAT_EVALUATION_REPORT.md` **renamed** to `SQUAT_EVALUATION_REPORT_3BAND.md` (superseded
  header added; references repointed in task.md / model_card.md / export_squat_model.py).
  Chapter §8.5 + limitation 19; model_card deployed-banding note.
  ```
- [x] **Replay corpus regenerated** under the binary policy (harness + generator now pass
  ```
  `band_policy`, faithful to the endpoint): now spans **Good + Poor** (Poor reachable at last),
  low-Q sample commits a band + raises retry flags. `test_module_b_replay.py` updated to assert
  `{Good, Poor}`; `test_module_b_fusion.py` gained `BinaryBandPolicyTests`. Backend **200/200**.
  ```
- [x] **Frontend** — squat live estimate (`squatLiveEstimate.ts`) now binary (a rough ROM
  ```
  hint, single cut at ROM score 7.0; authoritative verdict is the backend's). i18n
  `common.poor` display relabelled **"Needs Improvement"** (en/zh/ms) — internal band value
  stays `"poor"` so CSS/DB/model are untouched; this also relabels the bottom band of the
  3-band exercises. `tsc --noEmit` clean.
  ```
- [x] **Live E2E re-verified (2026-07-19):** real Postgres + uvicorn + the recorded
  ```
  `attempted_poor_deep_unstable_1` sample POSTed through `/api/module-b/analyze` →
  `band="Poor"` score 5.03 persisted in `sessions` (a Good sample → `band="Good"` 9.42);
  **"Poor" reachable live for the first time, no "Fair" for squat.** Frontend (dev
  server, logged in): Session History shows **"Needs Improvement"** + "Good" (layout
  clean), Report shows band "Needs Improvement", score 5.0, Reps 3, low-confidence flag
  surfaced as an error tag while the band still commits (not abstains). Test data cleaned up.
  ```
- [ ] **Deliberately not done:** no forest retrain; the ROM rule was **not** realigned to
  ```
  penalise excessive depth (HY chose "lean on the ML"); lunge + Module A untouched;
  landing-page marketing copy still enumerates "Good / Fair / Poor" (low priority, flagged).
  ```

### Phase 5 — Stage 5.12: Interpretable fault gates (depth / lean / heel-rise) (2026-07-19)

**HY's call (2026-07-19) — add a "why" to the verdict.** Stage 5.11 made squat commit to a
binary Good/Poor number, but that number is opaque (can't say _why_ a rep was bad) and the ML
only ever scores the first rep of a set. HY reviewed the REHAB24-6 videos directly and observed
the real faults are **forward lean** and **heels lifting off the floor** — not simply "too
shallow". The chosen design: interpretable **rule gates + ML as a secondary opinion**. If any
gate fails on any rep the band is forced to Poor **with a specific reason**; only when every gate
passes does the ML's holistic verdict decide. Gates are a separate override layer, not blended
into any score.

- [x] **Phase A — measurement** (`ml/scripts/analyze_fault_gate_thresholds.py`, new; report
  ```
  `ml/reports/SQUAT_FAULT_GATE_ANALYSIS.md`). Heel-visibility go/no-go census on the **raw**
  stream (X1 reuse of `build_features` helpers): far heel (landmark 30) reps-weighted mean
  visibility **0.784**, only 17/98 reps dip below `MIN_VISIBILITY` at depth → **GO** (behaves
  like the far ankle, not the far knee). New `heel_rise_peak_norm` (peak bilateral toe−heel
  lift / trunk length) run through the identical `check_feature_validity.analyse_feature()`
  KEEP/DROP method → **KEEP** (AUC 0.728, Poor higher, 4/5 subjects). Thresholds: **lean**
  Youden-J on `trunk_lean_peak_deg` = **41.42°** (data-driven, KEEP feature AUC 0.762);
  **depth** = **78.04°** = clinical parallel norm (90°) − the pipeline's measured −11.96°
  under-read (`MOCAP_AGREEMENT.md`), **NOT** data-driven since REHAB24-6's own depth signal
  is _inverted_ (Poor reps are deeper) — the report says so explicitly; **heel-rise** Youden-J
  = **0.084** (OOF sensitivity 0.81). Deterministic — two runs byte-identical.
  ```
- [x] **Phase B — backend.** New `backend/app/module_b/squat/fault_gates.py`: pure
  ```
  `depth_gate`/`lean_gate`/`heel_rise_gate` + `evaluate_fault_gates(reps, feature_vectors,
  ```

config)`running every enabled gate across **every** rep (the concrete fix for the ML's       rep-0-only blind spot, for faults).`FaultGateResult`/`GateCheck`frozen dataclasses. New` SQUAT_CONFIG["fault_gates"]`block, each threshold provenance-tagged and traced to the       Phase A report. New`ModuleBExercise.evaluate_fault_gates()`hook defaulting **None**       (mirrors`band_policy`— lunge + Module A unaffected by construction);`SquatExercise `implements it.`router.py`wires it right after`fuse_model`:` dataclasses.replace(fusion,
band="Poor")`on any failure + new`_fault_gate_tags()`helper (duck-typed,`source="rule"`,       severity` high`, one tag per fault kind with its human message).` heel_rise_gate`is       rule-only — **not** in`SQUAT_FEATURE_NAMES`, so no` feature_schema_version` bump / retrain.

- [x] **Tests** — new `backend/tests/test_module_b_squat_fault_gates.py` (21 tests): each gate at
  ```
  its Phase A threshold, the multi-rep aggregator (the direct regression: a clean rep 0 + a
  bad rep 1 is still caught), the router `_fault_gate_tags`/override composition, and lunge
  staying `None`. Full backend suite **222/222**.
  ```
- [x] **Replay corpus regenerated** (harness `replay_squat_session.py` + generator now apply the
  ```
  gate override, faithful to the endpoint — same discipline as Stage 5.11's `band_policy`). Two
  samples legitimately shifted Good→Poor (peak ~73.7° < the 78.04° parallel floor):
  `good_moderate_depth_1` is now the **depth-gate override fixture** (ML score 9.42 Good, gate →
  Poor), `good_moderate_depth_2` stays the clean all-gates-pass Good fixture. `labels.json`
  records per-sample `fault_gate_tags`; new `test_module_b_replay` assertion proves the corpus
  exercises the override. Corpus regeneration deterministic (byte-identical on re-run).
  ```
- [x] **Frontend** — i18n only (`tag_insufficient_depth`, `tag_excessive_forward_lean`,
  ```
  `tag_heel_lift` in en/zh/ms). **Zero `Report.tsx` change** — tag rendering is already generic
  (`t("moduleB.tag_"+tag.tag)`). `tsc --noEmit` clean.
  ```
- [ ] **Deliberately not done (explicitly deferred):** the ML's **single-rep scoring** is _not_
  ```
  fixed here (still scores only `feature_vectors[0]`) — a separate, flagged finding; the gates
  fix it for _fault detection_ only. No **live per-rep push** (HY chose "keep at end"). No ML
  retrain / no new ML feature. Lunge + Module A untouched (hook returns None).
  ```

### Phase 5 — Stage 5.13: Rep-count parity between the live counter and the backend (2026-07-20)

**HY's report (2026-07-20):** "even though I have chosen 10 reps in the squat exercise, sometimes
it comes out 9 reps." Stage 1 of a 5-stage plan (see
`~/.claude/plans/need-you-propose-plan-compiled-nova.md`); the remaining stages (set-level ML
scoring, live fault gates + auto-finish, report clarity, feedback formatting) are **not** started.

- [x] **Root cause 1 — the two counters read different signals.** `useMediaPipePose.ts:51`
      smooths only the 2D `landmarks` (for drawing); `worldLandmarks` are handed over raw. So the
      live estimator segmented a **raw** stream while `core/router.py` segments the
      **One-Euro-smoothed** stream from `preprocess_world_landmarks`. Fixed in
      `utils/squat/squatLiveEstimate.ts` by smoothing inside `createSquatLiveEstimator` with the
      **existing** `LandmarkSmoother` from `utils/oneEuroFilter.ts` (same 1.0/0.5/1.0 params as
      `module_a/core/smoothing.py`) — reused, not forked. A fresh smoother per `reset()`, since
      One Euro is stateful. Frames posted to the backend stay **raw**, so the backend still runs
      its own preprocessing exactly once (double-smoothing would re-introduce the divergence).
- [x] **Root cause 2 — the final rep was dropped.** `HysteresisRepFSM` only confirms a rep on the
      return below `exit_standing_deg` (20°), so a capture stopping anywhere in the 20–30°
      hysteresis deadband silently lost a rep the user completed. New opt-in
      `HysteresisRepFSM.flush(max_signal_to_close=...)` + `SquatSegmentationFSM.flush()`, called
      once at end-of-stream by `segment_squat_frames`. Gated by new
      `SQUAT_CONFIG["segmentation"]["flush_trailing_rep"]`. The ceiling is the **existing**
      `enter_descending_deg` (30°), so **no new tuned number was introduced**, and a capture cut
      off mid-rep (still deep in the movement) is still discarded.
- [x] **Root cause 3 — refractory divergence.** `squatLiveEstimate.ts` armed the refractory window
      on _every_ exit; `fsm.py:_close_candidate` arms it only on a **confirmed** rep. Aligned to
      the backend, so a fast rebound the backend counts is no longer invisible to the live counter.
- [x] **Verified by a cross-language parity sweep** (temporary harness, since a real 10-rep webcam
      set cannot be automated). One seeded generator produced identical noisy streams for both
      sides: **6 rep depths × 5 jitter levels = 30 conditions**, 10 reps each. The live estimator
      and `segment_squat_frames(preprocess_world_landmarks(frames))` now agree in **30/30**.
      **The decisive condition is a 30.5° peak** — reps hovering on the 30° entry threshold, where
      the crossing slope is shallowest: raw segments **10** reps but the smoothed/backend stream
      segments **2 / 7 / 8 / 7 / 9** across the five jitter levels, and the fixed live counter now
      returns exactly those same numbers. That is HY's "picked 10, got 9" symptom reproduced and
      closed. Above ~31° peak, raw and smoothed agreed anyway (10/10) — the bug only bites reps
      near the entry threshold.
- [x] Backend **276/276** (4 new `TrailingRepFlushTests`; the count is 276 not the 222 quoted in
      the Stage 5.12 note — the suite grew during Phase 6/7). Frontend vitest 4/4, `tsc` clean,
      Prettier + Black + `isort --profile black` applied. **Replay corpus unchanged** — every
      corpus rep already ends at standing, so nothing to flush and no fixture regeneration needed.
- [ ] **Deliberately not done:** live/backend parity is now _close_, not _exact_ — the backend also
      gap-fills and releases persistent occlusions before smoothing, and **both need future frames,
      so neither can run live**. Residual divergence is possible on captures with long
      low-visibility runs. Not measured here; flag for the limitations write-up.
- [ ] **Not started (later stages of the same plan):** ML still scores only `feature_vectors[0]`;
      the fault-gate band override still leaves `fusion.score` untouched (the 8.0-vs-"Needs
      Improvement" contradiction); target reps still do not auto-finish; feedback still renders
      raw markdown.

### Phase 5 — Stage 5.14: Set-level ML scoring by majority vote (2026-07-20)

**HY's report (2026-07-20):** a post-session squat report showed **8.0/10 next to "Needs
Improvement"**. Root cause was two-fold and both halves are fixed here. Stage 2 of the same
5-stage plan; Stages 3-5 (live fault gates + auto-finish, report clarity, feedback
formatting) are **not** started.

- [x] **Fixed the long-deferred single-rep defect.** `router.py` passed
      `features=feature_vectors[0]`, so with `w_rule=0.0` the whole displayed score was
      `10 × P(Good)` **for rep 0 only** — flagged at Stage 5.12 and deferred there. New
      `backend/app/module_b/core/set_scoring.py` (`score_set`, `RepVerdict`, `SetScoreResult`,
      `failed_gates_by_rep`) scores **every** rep. Driven entirely by a new
      `band_policy["aggregation"] = "majority_vote"` key, so an exercise without it keeps the
      exact single-vector path — **Module A untouched by construction** (same additive pattern
      as `band_policy` and the gate hook). A placeholder model never votes.
- [x] **Majority vote, not a mean — and the reason is the calibration.** The threshold
      `8.447974` was tuned on **individual** reps (`tune_squat_binary_band.py`, max macro-F1
      over OOF predictions). Averaging reps then applying that cut changes what the cut means,
      because a mean over N reps has a far narrower spread. Voting applies the threshold where
      it was calibrated and **needs no re-calibration** — which matters, because labels are
      per-rep and **no set-level ground truth exists** to re-tune against. It is also the
      noise-robust choice at the accepted ~31% per-rep false-alarm rate: on 10 genuinely good
      reps, "any rep Poor→Poor" misgrades ~**98%** of sets (1−0.69¹⁰), majority ~~**5.5%**
      (binomial P(X≥6), X~~B(10,0.31)), and the old rep-0 logic **31%** by construction.
      ⚠ Those assume independent per-rep errors, which they are not — same subject/camera/
      lighting — so the true majority rate is higher than 5.5%. **Ties break toward Poor.**
- [x] **Fault gates moved from set-level override to per-rep verdict.** Stage 5.12's
      `dataclasses.replace(fusion, band="Poor")` is **deleted**. A rep is Good iff the model
      passes it **and** no gate fired on it. This removes the score/band contradiction's
      structural cause: one bad rep in 30 no longer condemns the set. `failed_gates_by_rep`
      lives in `set_scoring.py` and is shared by the router, the replay harness **and** the
      corpus generator (X1) — a forked copy is exactly how the pre-5.11 harness drifted.
      **The score is deliberately NOT adjusted to agree with a gate-decided band:**
      `heel_rise_peak_norm` is rule-only and not in `SQUAT_FEATURE_NAMES`, so the model
      genuinely cannot see a heel lift. Stage 4 must explain that in the UI, not fake agreement.
- [x] **Per-rep detail persisted.** `crud._metrics_json` extends each `per_rep_summaries`
      entry with `ml_score` / `confidence` / `failed_gates` / `counted_good`. Additive only —
      absent for non-voting exercises, so historical rows still read back.
- [x] **Live end-to-end verified** (real `fyp_postgres` + real uvicorn on port 8932, curl
      through register→session/start→analyze, DB checked by direct SQL). A 3-rep corpus sample
      returned `ml_score=9.2693` = the mean of its three reps (9.2563/9.2571/9.2946); the
      **old** value was rep 0's 9.2563 exactly. DB row, session row and API response all agree.
      ⚠⚠ **The decisive check was a MIXED set, which the corpus cannot produce**: 9 reps built
      by concatenating two clean samples with one depth-failing sample →
      **6 good / 3 gated → band Good** on a 6/9 majority, with `insufficient_depth` still
      surfaced as a tag. Under Stage 5.12's override that identical set was Poor. Note reps 6-8
      scored **9.42-9.45** from the model while failing the depth gate — a live demonstration
      of the inverted-depth finding (the model cannot judge depth; the gate can).
- [x] Backend **289/289** (13 new in `tests/test_module_b_set_scoring.py`). **Both key
      behaviours mutation-checked**, not just asserted: relaxing the strict majority to `>=`
      failed exactly the tie test; dropping gates from `counted_good` failed 5 tests. Formatted
      with Black + `isort --profile black`.
- [x] `PHASE5_CHAPTER_DRAFT.md` §8.7 added; **limitation 20 corrected** (its "the classifier's
      own verdict continues to be formed from the first repetition alone" clause is now false)
      and **new limitation 21** records the aggregation rule as a reasoned choice rather than a
      measured optimum, plus the deliberate relaxation of the gate guarantee.
- [ ] **⚠ Replay corpus regenerated but it CANNOT test this change.** Its synthetic samples have
      near-identical reps within each set, so every set is unanimous — precisely where old and
      new rules agree. **No band changed**; only scores moved (now means over reps) plus a new
      `good_rep_count`. This **contradicts the plan's prediction** that `good_moderate_depth_1`
      would flip to Good: all 3 of its reps fail the depth gate (peak 73.69° < 78.04°), so
      0/3 good → Poor either way. The corpus is now non-regression evidence only; correctness
      rests on the mixed-verdict unit tests and the live mixed-set check above.
- [ ] **Deliberately not done:** no model retrain, no threshold re-tune (impossible without
      set-level labels), no frontend change — the report still renders the old way and still
      shows no pass mark, so **the 8.0-looks-like-a-pass confusion survives until Stage 4**.
      `replay_rules_and_fusion` (`--session-id` path) still cannot run gates — heel-rise needs
      raw frames, which are never stored — so a gate-decided band replays model-only. That gap
      predates this stage but per-rep voting makes it visible more often; documented in the
      function's docstring.

### Phase 5 — Stage 5.15: Live fault gates + auto-finish at target (2026-07-20)

**HY's design (2026-07-20):** a rep that trips a fault gate should be rejected **live** with
its reason and not count toward the target, so the user redoes it — but it is still recorded,
still sent, and still graded, so the post-session report stays honest about every attempt.
Stage 3 of the 5-stage plan; Stages 4-5 (report clarity, feedback formatting) **not** started.

- [x] **Fault gates ported to the browser.** New `frontend/src/utils/squat/squatFaultGates.ts`
      mirrors `squat/fault_gates.py`: depth (`<` threshold), lean (`>=`), heel rise (`>=`),
      with the same `_heel_rise_peak_norm` construction (peak bilateral toe−heel lift relative
      to the rep's FIRST frame, divided by mean trunk length) built incrementally, since the
      live path sees one frame at a time. **Thresholds are never hardcoded** — they come from
      `GET /api/module-b/squat/config`, which already serves the whole `SQUAT_CONFIG` including
      the `fault_gates` block; the local constants are pre-fetch fallback only (X7). A gate
      disabled server-side is disabled live.
- [x] **Heel gate abstains when it cannot see.** Heels/toes (29-32) are the lowest-visibility
      landmarks in a side view and a false heel-lift rejection discards a rep the user did
      correctly. `heelLandmarksVisible` requires all four above `MIN_VISIBILITY`; if any frame
      of the rep was occluded the tracker returns `null` and **only** the heel gate is skipped
      (depth and lean still apply), deferring that call to the backend.
- [x] **Rejected reps don't count but are still attempts.** `SquatLiveUpdate` gains
      `attemptCount`, `repJustRejected` and `lastRepFailedGates`. The reason renders from the
      **same i18n keys the report uses** (`moduleB.tag_`*), so live wording and report wording
      are identical by construction. No success chime on a rejected rep.
- [x] **Auto-finish at target.** The target now drives the session — pick 10, get exactly 10
      counted reps. Replaced the one-shot "Hit your goal!" modal (itself a Stage 5.13 root
      cause: it paused the frame buffer mid-motion). `TARGET_OPTIONS`' "motivational-only"
      comment and the `targetHitTitle`/`targetHitBody` keys are gone from en/zh/ms; new
      `repDidNotCount` / `attemptsSummary` / `finishWhenReadyTargeted`.
- [x] **Attempt cap so nobody is trapped.** `ATTEMPT_CAP_MULTIPLIER = 2` finishes the set at
      `target × 2` attempts, and "Finish Set" stays available throughout. Necessary because the
      depth gate is a **clinical** floor (78.04°), not learned from this cohort — a user with
      restricted mobility may genuinely never pass it, and a rehab tool must not loop forever
      (rules.md #3, #18).
- [x] **⚠⚠ Found and fixed a real live/backend divergence the gate check exposed.** On
      `lowq_reject_occluded_1` the live estimator segmented **0 reps** where the backend found 3. Cause: **every leg landmark is below `MIN_VISIBILITY` in all 342 frames** (median
      0.450), so `LandmarkSmoother`'s hold-last froze the pose at standing and flexion never
      crossed the 30° entry — precisely the failure `preprocessing._release_persistent_occlusions`
      was written to prevent backend-side ("confidently stale" beats nothing). Fixed with a new
      **opt-in** `createOcclusionReleaser` in `utils/oneEuroFilter.ts`, applied before smoothing
      to match the backend's gap-fill→release→One-Euro order. `LandmarkSmoother` itself is
      **untouched**, so WBLT (`services/wblt/wbltGeometry.ts`, the other consumer) is unaffected.
      This is the residual limitation Stage 5.13 flagged as theoretical — now measured and
      largely closed.
- [x] **Cross-language gate parity verified, 7/7.** A temporary harness ran the live estimator
      over all seven committed corpus samples and compared, per rep, against
      `evaluate_fault_gates` + `failed_gates_by_rep` on the same frames. Before the occlusion
      fix: **6/7** (the mismatch above). After: **7/7 exact** — same rep count, same
      counted/rejected split, and the same specific tag on every rep.
- [x] Frontend **17/17** (13 new in `src/test/squatFaultGates.test.ts`, covering each gate's
      comparison direction at its exact boundary, the heel abstention, multi-fault reps and a
      server-disabled gate). `tsc` clean, Prettier applied. Backend **289/289** unchanged —
      this stage is frontend-only.
- [ ] **Deliberately not done:** no new sound file for rejections (visual reason only). The
      occlusion release is a **causal approximation** — the backend releases a long run
      retroactively from its first frame, but live the run is only known to be long once it
      exceeds 5 frames, so the first ~5 frames (~0.2 s at 25 fps) of each run still hold-last.
      Bounded and self-correcting, but not exact parity.
- [ ] **⚠ Not verified in a real browser** — the gates and auto-finish were checked against
      recorded corpus frames, not a live webcam. **HY must confirm in-browser**: a deliberately
      shallow rep is rejected with the right reason and does not advance the counter; selecting
      10 yields exactly 10 counted reps; and the attempt cap fires.
- [ ] **Still open until Stage 4:** the report shows no pass mark, so a score below 8.448 still
      reads as a pass, and the rejected-attempt count is not surfaced post-session.

### Phase 5 — Stage 5.16: Report clarity — pass mark, band reason, rep breakdown (2026-07-20)

**HY's original report (2026-07-20):** the screenshot showing 8.0/10 next to "Needs
Improvement" with no explanation. Stage 4 of the 5-stage plan; this closes the original
complaint structurally rather than by fixing one number. Stage 5 (feedback formatting)
**not** started.

- [x] **Pass-mark tick on the score ring.** `Report.tsx` fetches `band_policy.decision_threshold`
      from `GET /api/module-b/squat/config` (the same endpoint the live estimator already
      uses) and draws a short tick at that position on the ring — **never hardcoded** (X7). A
      caption states it plainly: "The pass mark is 8.4/10." This alone resolves "why does 8.0
      fail" — the ring itself now shows the cut isn't 8.0.
- [x] **The band's reason is now a headline sentence, not silence.** New copy under the band:
      "N of M reps counted as good" (or "All M reps counted as good"), read from the Stage
      5.14 per-rep verdicts already in `per_rep_summaries`. Falls back to nothing on rows from
      before that stage (`hasRepVerdicts` guard) — old sessions render exactly as before.
- [x] **Rep breakdown block**, shown only when at least one rep was rejected:
      "N reps counted · M didn't count" plus one line per fault kind with a count
      ("Didn't reach enough depth ×3"). Reuses the **same** `moduleB.tag_`* i18n keys the
      Error tags panel and the Stage 5.15 live rejection note already use, so all three
      surfaces say the same thing verbatim by construction, not by convention.
- [x] **Trend-line wording fixed (Part 3.4 of the plan, done here since it touches the same
      lines).** `report.trendScoreChanged`/`trendRepsChanged`/`trendTimeChanged`/
      `trendHoldChanged` only ever prepended `+` for non-negative deltas, so a drop rendered
      as e.g. "score -1.0/10" — reading as an absolute score of minus one, not a decrease.
      Replaced with **direction-worded** keys (`trendScoreUp`/`Down`/`Same`, and the same
      pattern for time/hold/reps) via a new shared `deltaPart()` helper — one change point
      for all four exercises' trend lines (STS/SLS/WBLT/squat), not a squat-only patch.
- [x] **`ModuleBRepSummary` extended** (optional fields: `ml_score`, `confidence`,
      `failed_gates`, `counted_good`) to type the Stage 5.14 payload the frontend now reads.
- [x] **Live-verified against a real backend + Postgres row** — the exact mixed 6-good/3-gated
      session built for Stage 5.14's verification (`session_id=eedc86aa-...`), loaded through
      the real running dev server (`localhost:5180` + `localhost:8000`, JWT injected into
      `localStorage` since the session belongs to a scratch test account). **Confirmed via the
      page's accessibility tree** (a full authoritative read of rendered content, independent
      of any animation timing): `"9.3 / 10"`, `"Good"`, `"The pass mark is 8.4/10. 6 of 9 reps
counted as good."`, `"6 reps counted · 3 didn't count"` + `"Didn't reach enough depth —
aim for closer to parallel ×3"`, and the trend line `"Vs last session: score up 0.1
pts · 6 more reps"` — all present, in order, exactly as designed.
- [x] **Found and diagnosed a rendering-tool artifact, not a code defect.** The rep-breakdown
      block's `.reveal.in` CSS transition was observed stuck at `opacity:0` despite having the
      `.in` class in this automated preview tab. Confirmed **not** a Stage 4 regression: two
      pre-existing panels (Coaching feedback, Error tags) showed the identical symptom in the
      same load. Root-caused to the animation itself (`getAnimations()` showed a `CSSTransition`
      stuck in `"running"` state) rather than a CSS/specificity bug — verified by forcing
      `transition:none; opacity:1 !important` and confirming the final state matches the
      intended design exactly. Real users are unaffected; only this specific automated tab's
      rendering was implicated. **Also caused two 30s `computer` scroll-action timeouts**
      during verification — worth flagging if this preview environment is used again.
- [x] Frontend `tsc` clean; **4/4** `Report.test.tsx` (unchanged — no regression) + squat gate
      tests unaffected (17 total across the two suites). Backend untouched — this stage is
      frontend-only. Prettier applied to all touched files.
- [ ] **Deliberately not done:** the "Reps" card still shows total segmented reps (9), not
      counted reps (6) — deliberate, since it already matches `session.rep_count` (the
      backend's stored total) and the new copy right below it already disambiguates "6 of 9
      counted". No screenshot capture was possible for this record due to the tooling
      artifact above; the accessibility-tree read is the verification evidence instead.
- [ ] **Still open until Stage 5:** the coaching feedback card (visible in the same verified
      session: `"Grade: Good. Didn't reach enough depth — aim for closer to parallel."`) is
      still one run-on sentence — no bullets, no LLM JSON contract yet.

### Phase 5 — Stage 5.16 follow-up: removed the score-ring pass-mark tick (2026-07-20)

**HY's report (2026-07-20, after Stage 5.17):** a real webcam session showed a `9.3/10`
ring banded `"Needs Improvement"` with a small tick mark on the ring and **no** accompanying
"The pass mark is X/10" sentence — the tick's own visibility only depended on the
`band_policy` config fetch succeeding, while the explanatory sentence beside it additionally
required `hasRepVerdicts` (per-rep verdict data, only present on sessions analyzed after
Stage 5.14). On an older session lacking that data, the tick rendered as an unexplained
mark with zero context — the exact confusion HY flagged.

- [x] Removed the ring tick entirely (the `<line>` element + the now-unused `passMarkPct`
      derived value) from `Report.tsx`. The `passMark` state and its `"The pass mark is
X/10..."` sentence are kept — that text-based explanation degrades gracefully (simply
      absent on legacy rows, same as the rep-breakdown block already does), where the tick
      could not.
- [x] Verified: `npx tsc -b --force` shows only the one already-flagged, pre-existing,
      out-of-scope `Report.test.tsx` error (unchanged); frontend vitest **17/17**; Prettier
      applied.

### Phase 5 — Stage 5.17: Structured coaching feedback (JSON contract, no more raw markdown) (2026-07-20)

**HY's original report (2026-07-20):** the coaching card showed literal `* ` asterisks
inline instead of a bullet list. Stage 5 (final stage) of the 5-stage plan.

- [x] **New `backend/app/module_b/core/feedback_contract.py`** — the one JSON shape both
      the template and the LLM path now produce: `{"summary": "...", "tips": ["...", ...]}`.
      `parse()` is a total function (never raises) validating only SHAPE (dict, non-empty
      `summary` string, `tips` a list of non-empty strings) and tolerates a wrapping
      ` ```-fence` (LLMs add one despite being told not to). It deliberately does **not**
      check markdown content or grade integrity — those stay owned by `feedback_safety.py`,
      the one existing content-policy gate, so responsibilities don't blur.
- [x] **`feedback_templates.compose_template`** now returns a `RewrittenFeedback`
      (summary + tips) instead of one string — `_band_label` promoted to public
      `band_label` (reused by `llm_client.py`). `router.py` serializes it once via
      `feedback_contract.serialize` before storing, so `structured_feedback` and
      `rewritten_feedback` are always the same canonical JSON shape.
- [x] **`llm_client.py`**: new system prompt demands the JSON contract, no markdown, no
      code fences, and explicitly "use the exact band word given — never invent a
      different one." `rewrite_feedback` parses the reply via `feedback_contract.parse`;
      **malformed JSON is retried exactly once, then treated as a failure**, same as a
      timeout — never a half-parsed rewrite shown to the user.
- [x] **Band-name leak fixed.** `_chat_payload` now sends `band_label(structured.band)` —
      the DISPLAY word ("Needs Improvement") — instead of the raw internal value ("Poor").
      Live-verified: HY's original screenshot showed the LLM writing _"falls into the Poor
      band"_ while the UI said "Needs Improvement"; the model now has no reason to write
      the internal name at all.
- [x] **`feedback_safety.check_llm_feedback`** now parses the candidate via
      `feedback_contract.parse` (reason `invalid_json` on failure) and adds a **new
      markdown-formatting check** (`_MARKDOWN_CHARS_RE` for `*_#\``, `_LEADING_BULLET_RE`    for a leading`-`/`*`/`1.`on any tip) — reason`markdown_formatting`. All existing
checks (forbidden phrase, grade/score/tag integrity) now run against the
**joined summary+tips text**, not the raw JSON string, so they can't false-positive
on JSON syntax (`{`, `"summary"`, etc.).
- [x] **Read-path guard in `crud.feedback_summary`**: new `rewritten_feedback_structured`
      field. Parses the stored string; a row from before this stage (a plain sentence, not
      JSON) wraps as `{summary: <the old sentence>, tips: []}` rather than crashing — the
      raw `rewritten_feedback` string is left untouched alongside it for audit. New
      `RewrittenFeedbackStructured` Pydantic model in `schemas.py`.
- [x] **Frontend renders natively.** `Report.tsx`'s coaching card now renders
      `rewritten_feedback_structured.summary` as a `<p>` and `.tips` as a real `<ul>`/`<li>`
      list — no markdown library added. `ModuleBFeedback` gains the typed
      `rewritten_feedback_structured` field in `moduleBService.ts`.
- [x] **Backend 316/316** (22 new: `test_module_b_feedback_contract.py` is new; safety/
      template/llm_client/persistence suites rewritten for the JSON contract, not just
      patched). **Markdown-rejection mutation-checked**: disabling the check made exactly
      the 3 markdown tests fail, nothing else. Black + `isort --profile black` applied.
- [x] **Live end-to-end verified against the real dev backend** (already running with
      `--reload`, so no restart needed): a fresh `/analyze` call returned
      `rewritten_feedback_structured: {"summary": "Grade: Good.", "tips": ["No specific
issues were flagged for this set."]}` (LLM disabled locally → template path, correct
      fallback); the Stage 5.14/5.16 session from **before** this stage still read back as
      `{"summary": "Grade: Good. Didn't reach enough depth...", "tips": []}` — the legacy
      guard working on a real pre-existing DB row, not just a unit-test fixture. Both
      confirmed in the browser via the accessibility tree: a real `<ul>`/`<listitem>` for
      the new row, a plain paragraph (no crash) for the legacy one.
- [ ] **Deliberately not done:** no retry-with-corrected-prompt on a rejected LLM rewrite
      (a `markdown_formatting` or `grade_mismatch_*` rejection falls straight back to the
      template, same as any other rejection reason — no special-casing added).

**⚠⚠ Process finding, not scoped to this stage — every prior "tsc clean" claim in Stages
5.13–5.16 needs this caveat.** `npx tsc --noEmit` (bare, no `-p`/`-b`) was being used to
"verify" all four earlier stages. Discovered here: the root `tsconfig.json` has
`"files": []` and only `references` — bare `tsc --noEmit` against it silently checks
**zero files** and exits with no output, indistinguishable from "clean." Confirmed by
injecting an obvious type error into `src/main.tsx` and re-running the exact command
previously used: still no output. **The correct invocation is `npx tsc -b` (project
reference build mode)**, which actually walks `tsconfig.app.json`'s `include: ["src"]`.
Running it for the first time against the full accumulated diff surfaced exactly three
real issues, no more:

1. **A genuine Stage 5.15 regression**, now fixed: `SquatLiveSessionPage.tsx`'s
   `finishSet()` still called `setShowTargetHitPrompt(false)` after that state (and its
   whole modal) was deleted when the target-hit prompt was replaced by auto-finish —
   dead code left behind by the removal script, invisible until real tsc ran.
2. **`Report.test.tsx`'s squat fixture was missing the (required) `feedback` field**
   entirely — surfaced only because this stage made `ModuleBFeedback` a field on it; fixed
   by adding a realistic fixture, which also let the test assert the new `<li>` rendering
   for the first time (previously it asserted nothing about the coaching card).
3. **One pre-existing, out-of-scope error left AS-IS**: `Report.test.tsx` line 183 (the
   `warning_tags` test) spreads `{...moduleAResult, id: "s5", ...}`, and `id` is not a
   `ModuleAResult` field. Confirmed via `git diff`/`git show HEAD:...` that this file is
   **byte-identical to HEAD** — it predates every stage in this session and is unrelated to
   feedback formatting. Left unfixed per scope discipline; flagging here since real tsc
   finally makes it visible. **Every other file across all 5 stages is clean under the
   correct invocation** — Stages 5.13/5.14/5.16's own "clean" claims hold up in retrospect,
   only Stage 5.15 had a real latent bug, now fixed.

### Phase 5 — Stage 5.18: The reported score becomes the share of clean reps (2026-07-20)

**HY's report (2026-07-20), from a real webcam session:** "even I do quite a lot of errors, it
still gives me quite high marks." Investigation turned this into the phase's sharpest finding.
Stage A of a 5-stage plan (`~/.claude/plans/need-you-propose-plan-compiled-nova.md`); Stages
B-E (history cleanup, report fixes, live redesign, progress page) are **not** started.

- [x] **⚠⚠ Root cause measured on HY's own 16-rep session: the reported score ran
      ANTI-CORRELATED with the faults the system detects.** Gate-failing reps carried a mean
      classifier output of **8.845** against **8.807** for clean reps, and the set's
      **highest-scoring rep (9.458) was a depth failure**. This is the EC3D construct
      inversion (limitation 16) reproduced in deployment, on a participant and camera absent
      from every dataset used in this project. Consequence: across all recorded sessions the
      score spanned only **8.02-9.27** while real performance spanned 0%-100% clean — about
      one eighth of the nominal scale for the entire quality range.
- [x] **Score redefined — a one-line change.** `set_scoring.py`'s `final_score` is now
      `10.0 * good / len(verdicts)` instead of `w_rule*rule + w_ml*mean_ml_score`. `good` is
      the **same count the band vote already computed**, so no new arithmetic was introduced.
      `mean_ml_score`/`mean_confidence` are untouched and still populate `fusion.ml_score`/
      `fusion.confidence` for the report's secondary cards. Only squat sets
      `aggregation="majority_vote"`, so Module A never reaches the line — no guard needed.
- [x] **The headline property: band and score can no longer contradict.** `band == "Good"`
      ⟺ `good*2 > total` ⟺ `score > 5.0`. The defect that started this whole line of work
      (8.0 displayed beside "Needs Improvement") is now **arithmetically impossible**, not
      merely unlikely. New `BandAndScoreCannotContradictTests` asserts the invariant across
      **every split from 0/10 to 10/10** via `subTest`, plus the exact 5.0 tie boundary.
- [x] **Both tests that pinned the OLD contract were rewritten, not patched** — as the plan
      required: `test_set_score_is_the_mean_of_the_per_rep_ml_scores` →
      `test_set_score_is_the_share_of_clean_reps`, and
      `test_the_score_still_reports_what_the_model_measured` →
      `test_gate_failures_now_move_the_score_as_well_as_the_band` (Stage 5.13's "gates change
      the band, never the number" is **deliberately reversed** here).
- [x] **Mutation-checked.** Replacing `good` with `len(verdicts)` failed **15 cases**,
      including every subTest of the invariant. Only `clean=10` survived — correct, since
      there `good == total` makes the mutation an identity. Green tests that cannot fail are
      not evidence.
- [x] **Replay corpus regenerated; ZERO bands changed** (verified by grepping the diff for
      `"band"` lines: 0 hits). Only scores moved, e.g. `good_moderate_depth_1` 9.4212 → **0.0**
      (all 3 reps depth-gated) and `good_moderate_depth_2` 9.2563 → **10.0** (all 3 clean).
      Re-running the generator produced an identical diff — deterministic (X8).
- [x] **Live end-to-end verified** against the running dev backend + Postgres. A 9-rep mixed
      set (6 clean + 3 depth-gated) scored **6.67 = 10×6/9** and banded Good; the same set
      scored **9.33** under the old definition. `ml_score` preserved at 9.325. Both
      `sessions.score` and `module_b_results.score` persisted 6.67, and the invariant held in
      the API response.
- [x] Backend **320/320** (17 in the set-scoring module, 4 net new). Black + `isort` applied.
- [x] `PHASE5_CHAPTER_DRAFT.md` **§8.8** written (deployment evidence: the anti-correlation,
      the compressed range, and `confidence == P(Good)` in **47/47** live records with minimum
      0.780 — a third independent confirmation of §8.2). **New limitations 22 and 23**; the
      closing synthesis paragraph rewritten around the trajectory "the model is the score" →
      "the model decides what the score counts".
- [ ] **Deliberately not done:** no model retrain (the label construct is itself
      population-specific — retraining on the same labels reproduces the confound); no change
      to `confidence` in the API/DB (**HY chose to keep the Confidence card**); no frontend
      change at all, so the report still shows the old "Reps" wording and no ML-only rejection
      line until Stage C.
- [ ] **⚠ Known display inconsistency until Stage E:** `dashboardChartUtils.ts` hardcodes score
      band zones at 4/7 for every exercise, but squat's cut is now a clean 5.0. A squat point
      can still sit in the wrong colour zone on the trend chart. Pre-existing (the old cut was
      8.448, an even worse mismatch) — scheduled for Stage E, not introduced here.
- [ ] **⚠ Historical data now mixes two score meanings.** 21 of 26 stored squat results
      pre-date per-rep verdicts and cannot be recomputed. HY approved deleting them in
      **Stage B**, which has not run yet — until it does, Dashboard averages and the trend
      chart straddle the definition change.

### Phase 5 — Stage 5.19: Squat history cleanup + backfill under the new score (2026-07-20)

Stage B of the 5-stage plan, following Stage 5.18's score redefinition. Destructive, so it
ran audit-first with HY confirming the exact set. Stages C-E not started.

- [x] **⚠ The audit contradicted the plan's premise and the plan was corrected before acting.**
      The plan assumed "21 legacy dev/test sessions". Reality: **42** squat sessions lacked
      per-rep verdicts, because the earlier count only included rows that had a
      `module_b_results` row and therefore missed every `in_progress`/`cancelled` capture. More
      importantly **6 of them were deliberately seeded demo data** (`demo-progress@physiofit-
demo.com`, all timestamped identically, created by `app/seed_demo_progress.py` so the
      Dashboard/Progress charts have something to render) — not dev junk, and deleting them
      would have emptied the Progress-page demo. Surfaced to HY with the full table before
      anything was deleted; HY chose to keep the demo account.
- [x] **DB-level cascade verified before deleting**, not assumed: queried
      `information_schema` and confirmed `ON DELETE CASCADE` from `sessions` to
      `module_b_results`, `module_b_error_tags`, `feedback_texts`, `module_a_results`,
      `module_a_landmark_log`.
- [x] **Backup taken first** — `pg_dump --data-only` of `sessions`/`module_b_results`/
      `module_b_error_tags`/`feedback_texts` (260K) to the session scratchpad. ⚠ Credentials
      are `fyp_user`/`fyp_rehab_db`, **not** `postgres` (the obvious guess fails).
- [x] **Dry-run-by-default cleanup script** (`--apply` to write). Deleted **36** sessions
      (20 abandoned `in_progress`/`cancelled` with no score + 16 legacy completed from
      `tester123` and throwaway `stageXX@` accounts); the demo account was excluded by email.
- [x] **Backfilled 6 sessions instead of deleting them** (HY's call). Their `counted_good`
      flags were already persisted at analyze time, so score/band were recomputed as
      `10 × good/total` with **no model re-run**: `9.27→10.00`, `9.33→6.67`, `9.27→10.00`,
      `8.80→3.75`, `8.75→**5.00**`, `6.67→6.67` (the last a no-op — it was already recorded
      under the new definition, a useful self-check). **HY's own 16-rep session from the
      original screenshots is now exactly 5.00/Poor** — 8 of 16 clean, landing precisely on
      the tie boundary where a strict majority still bands Poor.
- [x] **⚠ Found and fixed a fixture that violated the new invariant.** The demo seed hardcoded
      `(11, 5.2, "Poor", …)` — written straight to the DB, bypassing the scoring pipeline, so
      nothing enforced consistency. Under Stage 5.18 a 5.2 must band Good, so that row would
      have rendered as a contradictory "5.2 · Needs Improvement" report: precisely the defect
      5.18 eliminated everywhere else. Changed to `4.8` (preserving the improving-trend
      narrative 3.1→3.6→4.4→4.8→6.9→7.5), updated the one stored row to match, and added an
      **import-time assertion** over `SQUAT_SESSIONS` so a future hand-edit cannot reintroduce
      it.
- [x] **Verified after applying:** 12 squat sessions remain, **0 invariant violations**;
      orphaned `module_b_results`/`module_b_error_tags`/`feedback_texts` all **0** (cascade
      clean); Module A untouched at **98** sessions (STS 53, WBLT 26, SLS 19) plus 3 legacy
      lunge rows. Backend **320/320**.
- [ ] **Deliberately not done:** the throwaway `stageXX@…` **user accounts** still exist with
      zero squat sessions — harmless, and deleting user rows was outside what HY approved.
      The demo account's 6 squat sessions still carry no per-rep verdicts, so their report
      pages show no rep breakdown; that is inherent to fabricated fixture data and acceptable,
      since its purpose is chart rendering, not report detail.

### Phase 5 — Stage 5.20: Report clarity — target, attempts, model-only rejections, bullets (2026-07-20)

Stage C of the 5-stage plan, addressing HY's issues 3, 5, 6, 7 and 8 from real webcam
testing. Stages D-E (live redesign, progress page) not started.

- [x] **Issue 8 — the counts now reconcile.** A rep counts only if it clears the gates
      **and** the model's threshold, so a rep can be rejected with no named fault; those
      were invisible, leaving "8 didn't count" above only 6 reasons (one session was 9 reps
      → 0 good, 0 gated, **9 model-only** = a completely empty reason list). `Report.tsx`
      now counts rejected reps with no failed gate — **by rep, not by tag**, since a rep can
      trip two gates and would otherwise double-count — and renders
      `report.modelOnlyRejection`. Also added `report.liveCountProvisional` explaining that
      the live counter is gates-only while the final count also applies the model, so
      "I hit my target of 10 but the report says 8" now has a stated reason.
- [x] **Issue 3 — rep target persisted end-to-end.** New Alembic migration
      `20260720_0012` adds nullable `sessions.target_rep_count`. ⚠ Sent on the **analyze**
      request, not `session/start`: the goal is chosen on the live page _after_ the session
      row exists. `crud.save_result` only writes it when non-None, so a re-analyze without a
      target cannot erase one already recorded. Exposed via `SessionRead`/`SessionDTO`.
      **Downgrade round-trip verified**, not just the upgrade.
- [x] **Issue 3 — "Reps" relabelled "Attempts"** with an InfoTooltip ("every repetition
      detected in this set, including the ones that didn't count"), plus a new "Rep goal"
      card rendered only when a target was stored. 16 no longer reads as "16 completed".
- [x] **⚠ `backend/alembic.ini` was missing entirely** even though `README.md` step 3
      instructs `alembic upgrade head` — so the documented command could not work for anyone
      cloning the repo. Not gitignored; simply absent. Added, with the DB URL deliberately
      **not** in it (`alembic/env.py` injects `settings.database_url`, keeping credentials
      out of version control per rules.md #4). ⚠ Postgres credentials are
      `fyp_user`/`fyp_rehab_db`, not the obvious `postgres`.
- [x] **Issue 5 — scroll-reveal removed from the report only.** Dropped `useReveal` and all
      17 `reveal` class usages from `Report.tsx`; other pages keep theirs. Verified in-browser:
      `document.querySelectorAll(".reveal").length === 0`. This also removes the
      fade-in that made earlier screenshot verification unreliable.
- [x] **Issue 6 — depth message now names the angle.** `"aim for closer to parallel"` →
      `"aim for a knee bend of at least 78° (thighs close to parallel)"` in
      `squat/config.py` and `moduleB.tag_insufficient_depth` (en/zh/ms). New
      `test_the_message_quotes_the_actual_threshold` guards against the copy and
      `min_knee_flex_peak_deg` drifting apart.
- [x] **⚠ Surfaced a real config inconsistency behind issue 6, and HY chose to leave it.**
      The depth gate fires below **78.04°** but `rules.rom` labels 60-90° "Shallow" and only
      90°+ "Parallel" — so a rep at 85° passes the gate while the gauge calls it Shallow.
      Cause: the gate **was** corrected for the pipeline's measured -11.96° under-read; the
      ROM band edges were **not** — they are raw clinical numbers on a scale that reads ~12°
      low. Re-basing them would change `rom_subscore` and the rule score, so it needs its own
      validation stage. Documented in `squat/config.py` rather than silently patched.
- [x] **Issue 7 — bullets restored.** Root cause is `@import "tailwindcss"` Preflight setting
      `ul { list-style: none }` globally. Set `list-style: disc` + `padding-left: 22px` on
      `.feedback-box ul`, `.rep-breakdown ul` and `.squat-reject-note ul`. Verified in-browser
      via `getComputedStyle` → `listStyleType: "disc"` on both report lists.
- [x] **Confidence card kept (HY's call) but no longer reads as a second opinion.** Added an
      InfoTooltip explaining it reports how sure the model is of its own call and that it
      tracks the ML prediction, because the model has not leaned toward Needs Improvement on
      any recorded repetition. `moduleBRows` gained an optional `info` field; nothing removed
      from the API or DB.
- [x] **Verified live end-to-end**: a 9-rep mixed set with `target_rep_count: 10` returned
      score **6.67**, band Good, and reconciled **6 counted + 3 gated + 0 model-only = 9**;
      `target_rep_count` round-tripped DB → API → UI. Browser accessibility tree confirmed
      "Attempts", "Rep goal 10 reps", the 78° wording in both the breakdown and the error
      tags, the provisional-count note, both InfoTooltip buttons, and the coaching card
      rendering as a real `<ul>` with two `<li>` tips.
- [x] Backend **321/321** (1 new drift guard). Frontend **18/18** (1 new test asserting the
      counts reconcile) — **mutation-checked** by disabling the model-only line, which failed
      exactly that test. `npx tsc -b` clean apart from the known pre-existing
      `Report.test.tsx:213` `id`-on-`ModuleAResult` error. Prettier + Black + isort applied.
- [ ] **⚠ Pre-existing error still not fixed** (unchanged from Stage 5.17): `Report.test.tsx`
      spreads `id` into a `ModuleAResult`, which has no such field. Byte-identical to HEAD,
      unrelated to Module B, deliberately left alone per scope discipline.
- [ ] **Deliberately not done:** the demo-progress account's squat sessions still have no
      per-rep verdicts, so their reports show no rep breakdown — inherent to fabricated
      fixture data whose purpose is chart rendering. The trend chart's 4/7 band zones still
      do not match squat's 5.0 cut; that is Stage E.

### Phase 5 — Stage 5.21: Live session redesign — promoted, persistent feedback (2026-07-20)

Stage D of the 5-stage plan, addressing HY's issue 1: on a real webcam session, the "Rep 5
of 10" status box sat below Live angles, and corrective feedback was easy to miss at a
distance from the screen. Stage E (Progress page) not started.

- [x] **Loaded the `ui-ux-pro-max` skill** (Stage plan requirement). It selected the
      "Accessible & Ethical" style — high contrast, 16px+ text, WCAG AAA, reduced-motion —
      appropriate for a screen read from several feet away mid-exercise. Kept PhysioFit's
      existing palette and Inter type per the skill's own `consistency` rule; only the
      pattern/style guidance was used, not a new color system.
- [x] **New `.live-feedback-panel`, promoted directly under the `[Time | Reps]` HUD**,
      replacing the deleted `.sls-live-status-box` ("Rep 5 of 10"). Three states —
      `idle`/`counted`/`rejected` — each with a distinct icon, background and border
      (`Play`/neutral, `Check`/green `--good`, `Alert`/amber `--warn-bg`). Rejected reasons
      render at **1.05rem/600**, up from the report's 0.9rem, since this is read
      mid-exercise, not at rest. Fixed `min-height: 128px` so switching states never
      shifts the layout beneath it. `role="status" aria-live="polite"` preserved.
- [x] **Persistent, not timed.** Deleted `REJECT_TOAST_MS` and the `setTimeout` that used
      to auto-clear the rejection note after 3.2s (HY's chosen option: "Last rep verdict,
      persistent — never blank"). `feedbackKind` is **derived**, not new state:
      `rejectedGates` already held exactly "reasons for the most recent rejection, or none
      if the most recent event was a good rep" — removing the auto-clear was the whole
      change; no new state variable was needed.
- [x] **Live angles panel demoted to third**, content byte-identical, position only.
- [x] **HUD Reps card shows `5 / 10` when a target is set.** ⚠ Per the plan's explicit
      warning, the shared `live.reps` **label** key (used by STS/SLS/WBLT too) was left
      untouched — only this page's rendered _value_ changed, via a new squat-scoped
      `squat.repsOfTargetValue` key.
- [x] **Old per-rep UI removed from the "Live status" panel** (now just target picker +
      progress bar + attempts summary + Finish button) since the promoted panel and the
      HUD cover that ground. Two now-dead i18n keys (`repOfTarget`, `repCounted`) replaced
      with the new panel's copy, confirmed unused via grep before deletion.
- [x] **⚠ Fixed `--warn-bg`, found while styling the rejected state.** Used by
      `.squat-reject-note`/`.rep-breakdown` since Stage 5.15/5.17 but **never defined** in
      `:root` or either theme block — the hardcoded `rgba(245,158,11,.12)` fallback always
      won, silently ignoring dark mode, and that fallback is a _different_ amber
      (`#f59e0b`) from the `--amber` token (`#f5b731` = `rgb(245,183,49)`) used for the
      border on the same elements. Now defined properly in both theme blocks, derived from
      `--amber`'s own rgb; the two stale inline fallbacks updated to match.
- [x] **Verified via direct DOM injection into the running dev server**, not a component
      test — no mock harness exists for `useWebcam`/`useMediaPipePose` on any live-session
      page yet, and building one from scratch was judged out of scope for a layout/CSS
      check. Injected the actual three-state markup with the real `index.css` in effect
      and confirmed via `getComputedStyle`: idle panel background = `rgb(10, 41, 20)` =
      `--surface`'s dark-mode value exactly, matching the HUD card's own background
      byte-for-byte. (A screenshot of the same panel looked visually lighter than the
      computed value — traced to a compositing artifact in the screenshot tool over that
      region, not a real color difference; computed style is the authoritative source and
      it is correct.) Light mode screenshot confirmed three visually distinct states,
      legible bold text, and the bullet marker rendering in the rejected reasons list.
- [x] `npx tsc -b` clean apart from the known pre-existing `Report.test.tsx:213` error
      (unrelated, unchanged). Frontend **18/18** (unaffected — this stage touched no tested
      logic, only layout/CSS/copy). Prettier applied.
- [ ] **⚠⚠ This stage's actual gate is NOT met yet.** The plan states it explicitly: "HY
      confirms in a real webcam session that feedback is legible at a distance." Everything
      above is static/injected verification of the CSS and markup: no live squat rep was
      performed against this code, so timing (does the panel update fast enough after a
      rep completes?), real-world legibility (screen brightness, actual viewing distance,
      webcam framing) and the interaction with the countdown/inactivity/finish flows are
      **unverified**. This is not a caveat to a mostly-complete verification — it is the
      one thing that actually validates this stage, and it can only be done by HY.
- [ ] **Deliberately not done:** no change to the setup-stage target picker, the countdown
      overlay, or the inactivity/finish-set modals — out of scope for the feedback-panel
      redesign. The `.sls-live-status-box`/`.sls-live-status-text` CSS rules were left in
      `index.css` (confirmed still used by `SlsLiveSessionPage.tsx`/`WbltLiveSessionPage.tsx`).

### Phase 5 — Stage 5.22: Progress page — rep volume replaces Confidence (2026-07-20)

Stage E, the **final stage** of the 5-stage plan addressing HY's 10 issues from real
webcam testing. Closes issue 10.

- [x] **Asked HY before building, per the plan's own flagged fork.** Since Stage 5.18 the
      squat score already equals `10 × counted/attempts`, so a "clean-rep rate" chart
      would just replot the score series as a percentage — genuine duplication, zero new
      code. The richer alternative (attempts vs counted reps per session) shows what the
      score alone can't: training volume, and whether a low score came from a hard
      session or a short one — but needs a new chart component and a new backend field.
      **HY chose the richer option.**
- [x] **`rep_count` added to `TrendPoint`** (`db/schemas.py`, populated in
      `dashboard_service.build_trends` from the session's own already-existing
      `rep_count` column — no migration needed). Frontend `types/api.ts` mirrors it.
      Broke 3 existing `test_dashboard.py` tests whose `_session()` fixture predated the
      field (`SimpleNamespace` with no `rep_count` attribute); fixed the shared fixture
      itself rather than the individual tests, and added a real assertion
      (`test_rep_count_is_denormalized_onto_the_trend_point`) that it actually
      propagates, including the `None` case for SLS/WBLT.
- [x] **New `RepAttemptsBarChart.tsx`** — a stacked bar per session, counted (green
      `--good`) + rejected (amber `--amber`) to the total. `counted` is derived
      client-side as `round(score/10 × rep_count)` rather than summed from raw
      verdicts — the trend endpoint doesn't store per-rep data, and this recovers
      exactly the integer the report itself would show, not an approximation.
      Replaces the Confidence `PercentTrendChart` panel in `Progress.tsx` (which is
      **not** deleted — still imported and used for the unrelated capture-quality
      panel on the same page).
- [x] **`dash.confidence` and the Dashboard page's own separate Confidence panel left
      untouched** — deliberately out of scope; the plan and issue 10 were specifically
      about the Progress page.
- [x] **⚠ Fixed a pre-existing inconsistency while here, not a new one.** Score band
      reference zones were hardcoded at 4/7 for every exercise, but squat has committed
      to a binary Good/Poor vote since Stage 5.11 — a squat point could already sit in
      the green 7-10 zone while its own badge said "Poor", **before** any of this
      session's changes. Post-5.18 the cut is a clean 5.0. Added
      `scoreBandThresholdsFor(exerciseType)` in `dashboardChartUtils.ts`
      (`{poorMax:5, fairMax:5}` for squat — equal bounds collapse the middle
      `ReferenceArea` to zero height, so `ScoreTrendChart` needed no new rendering
      branch) and threaded it through `Progress.tsx`'s one `variant="full"` call site.
      `ZoneLegend` now hides the "Fair" swatch when the zone is zero-width, so the
      legend never promises a band that can't appear. `MiniTrendCard`'s `variant="mini"`
      never rendered these zones at all (guarded by `!isMini`), so it needed no change.
- [x] **New `src/test/progressCharts.test.ts`** (9 tests): the counted/rejected
      derivation across the full score range (0 through 10 rep-tenths, asserting
      `counted + rejected === attempts` every time), the real Stage 5.18 session
      (8/16 clean → 5.0), zero-clean and zero-rejected edges, `rep_count: null` →
      `null` (SLS/WBLT), zero-rep-count → `null` (no divide-by-zero), and
      `scoreBandThresholdsFor` for squat vs every other exercise type.
      **Mutation-checked**: broke the `rejected` derivation (off-by-one) and squat's
      `fairMax` (gave it a real Fair band) — both failed exactly the tests written to
      catch them, nothing else.
- [x] **Verified live end-to-end**, not just unit tests: `GET /api/dashboard/trends`
      returns `rep_count: 9` on real stored sessions; in-browser, read the DOM directly
      (screenshot scroll-following is unreliable in this environment, a known limitation
      from Stage 5.16 — verified via `getComputedStyle`/SVG inspection instead, which is
      authoritative regardless): **4 `<path>` bar segments** (2 sessions × 2 stacked
      colors) rendered in exactly `rgb(0,174,84)` and `rgb(245,183,49)` — `--good` and
      `--amber`. Accessibility tree confirmed the "Rep volume" heading, "Counted"/
      "Didn't count" legend, and the Score trend zone legend showing only
      **"Good"/"Needs Improvement"** for squat — no "Fair" swatch.
- [x] Backend **322/322** (fixed a shared test fixture + 1 new test). Frontend
      **27/27** (9 new). `npx tsc -b` clean apart from the known pre-existing
      `Report.test.tsx:213` error. Black + isort + Prettier applied.
- [ ] **Deliberately not done:** `MiniTrendCard`'s mini chart (used on the Dashboard
      page) still uses the shared 4/7 zones' _data_, though it never visually renders
      them — no functional gap, noted for completeness. No change to `SessionHistory.tsx`
      or any other raw-score display outside the two touched charts.

---

## Closing this 5-stage plan (Stages A–E, 2026-07-20)

All 10 issues HY raised from real webcam testing are now addressed:

1. **Live feedback redesign** (Stage D) — promoted, persistent verdict panel.
2. **ML undermining scoring** (Stage A) — the headline score no longer comes from the
   classifier at all; §8.8 + limitations 22–23 document why.
3. **Rep target + "attempts" wording** (Stage C) — persisted end-to-end, migration
   `20260720_0012`.
4. **Confusing 8.8 with heavy errors** (Stage A) — root-caused (gate-failing reps scored
   _higher_ than clean ones) and fixed by redefinition, not cosmetics.
5. **Report scroll animation** (Stage C) — removed from `Report.tsx`.
6. **Vague depth message** (Stage C) — quotes the actual 78° gate threshold, drift-guarded
   by a test.
7. **Missing bullets** (Stage C) — Tailwind Preflight's `list-style:none` restored on all
   three affected lists.
8. **Rejected-rep count not reconciling** (Stage C) — the ML-only-rejection line.
9. **Rule-based vs ML explanation** (Part 5, folded into Stage A/C's chapter writing) —
   segmentation/fault-gating vs holistic per-repetition assessment, with a stated boundary.
10. **Confidence on the Progress page** (Stage E, this entry) — replaced with rep volume.

Two things were surfaced during this work that were not on HY's original list and are
recorded here so they aren't lost: **`backend/alembic.ini` was entirely missing** (Stage
C) despite the README instructing `alembic upgrade head`, and **`npx tsc --noEmit`
(bare) silently checks zero files in this repo** (discovered at Stage 5.17, before this
plan) — `npx tsc -b` is the correct invocation and was used for every verification in
Stages A–E.

One process note for whoever picks this up next: the demo-progress account
(§Stage B/5.19) and the throwaway `stageXX@…` test accounts (§Stage B) were deliberately
left in the database — say so explicitly if a future cleanup pass should remove them.

## Stage 5.23 — LLM feedback silently degraded + the logging gap that hid it (2026-07-20)

**Symptom.** HY's post-session report showed `AUTOMATIC SUMMARY` (the deterministic
template) where earlier sessions showed `AI-REWRITTEN`. Nothing was visibly broken —
the report rendered correctly, which is exactly Stage 6.4's designed graceful
degradation working as intended, and exactly why it went unnoticed.

**Root cause.** `backend/.env` had `LLM_MODEL=llama-3.3-70b-instruct`, annotated
"#cheap version". Groq does not host that model id. Verified live against
`GET /v1/models`: the only llama models on the key are `llama-3.3-70b-versatile` and
`llama-3.1-8b-instant`. A direct call with the bad id returns **HTTP 404
`model_not_found`**; `GroqClient.rewrite_feedback` catches it, does not retry (only 429
is retried, correctly), returns `text=None`, and `_build_and_save_feedback` falls back
to the template. Both ids were confirmed by curl: `instruct` → 404, `versatile` → 200.
Note the premise was also wrong — both Groq models are free-tier, so "cheap" was never a
reason to switch. Fixed in `.env`, with a comment recording the verified model list so
the same substitution isn't retried.

**The DB already recorded the fingerprint** (`feedback_texts`): `llm_attempted=true` +
`feedback_source=template` means "the call was made and did not survive", which is
distinct from `llm_attempted=false` (LLM disabled). History showed a clean cutover —
`llm` for every session 06:52→11:00, `template` for every session after.

**Three sessions (11:02, 12:00, 12:02) failed while configured to the _valid_ model and
remain unattributed.** Replaying the real pipeline for those exact stored sessions
against `versatile` now returns call-OK + `safety.accepted=True` for all three, so it
was transient (a timeout against `_TIMEOUT_S = 8.0`, or a 429) rather than reproducible.
Stated as unresolved rather than guessed — the logs that would have said which were
never captured, which is the second half of this entry.

**The real gap: the diagnostics existed but could never be seen.** `core/router.py`
already logs `module-b feedback llm_failed session=… error=…` and
`llm_rejected session=… reason=…` — the two lines that would have named this
immediately. But no logging configuration existed anywhere in the backend: root logger
at default `WARNING`, zero handlers, so every `logger.info(...)` in the codebase was
discarded before being written. Confirmed directly (`isEnabledFor(INFO)` → `False`,
`root.handlers` → `[]`). `startup.sh` redirects to `/tmp/fyp_backend.log`, but that file
did not exist (server started manually), and `startup.bat` redirects nowhere at all — so
even the dropped lines had no destination.

**Fix.** New `backend/app/core/logging_config.py` — `configure_logging(level)` attaches
one stdout handler to the root logger, called from `main.py` **before** `FastAPI(...)`
so import-time and startup records are captured too. Idempotent under `uvicorn --reload`
(handler tagged `_fyp_configured` and reused, verified: 3 calls → 1 handler, no
duplicate lines). `httpx` pinned to WARNING — it logs one INFO line per outbound request
and would narrate every Groq call on top of the app's own, more useful, session-tagged
lines. Level is env-configurable via new `settings.log_level` (`LOG_LEVEL`, default
INFO).

**Verification.** Backend **322/322** (the INFO line now visibly emitted mid-run, which
is itself the proof); `settings.llm_model` re-resolves to `llama-3.3-70b-versatile`
after the `.env` fix; reload-idempotency checked explicitly; Black + isort clean. The
running uvicorn's child had already restarted at 20:37 and `/health` was green, so the
reload picked the change up. **Not yet verified:** a real webcam session showing
`AI-REWRITTEN` again — only HY can do that, and it is the true gate on this entry.

**Deliberately not done:** no file-based logging, rotation, or structured/JSON logs
added — stdout is what `--reload` development and `startup.sh`'s existing redirect both
already consume, and anything more is unjustified scope here. `_TIMEOUT_S = 8.0` left
unchanged pending evidence it is actually too tight (see the three unattributed
failures above — with logging now live, a recurrence will finally name itself).

### Stage 5.10 — Option B: documented, not built _(for Chapter 3)_

- [ ] `docs/module_b_option_b_alternative.md` — the methodology alternative, written to be examiner-facing:
  - The mapping: Correct → Good; minor fault (Not-low-enough) → Fair; severe fault (Knees-inward / Front-bent) → Poor; then reconcile REHAB24-6 `incorrect` by the physio-noted mistake.
  - **Why it was not built — three real costs:** (1) two datasets speak different label languages and merging needs a translation _we_ author; (2) ranking a fault "minor" vs "severe" needs a physiotherapy severity source — **without one, it's opinion dressed as ground truth**, which is exactly the invented-cutoff trap this project has already been caught by once; (3) it **breaks the validation firewall** — once EC3D defines the bands it can't also be the independent test set, forcing Mendeley (26 subjects, unverified labels, no rep segmentation) in as the held-out check.
  - What would reverse the decision: a citable fault-severity source **and** an examiner requiring a genuinely learned third class.
- [ ] **Do not write Option B code.** Not even a stub.

**Deliverable:** Trained Extra Trees model for squat, calibrated and LOSO-evaluated, backend can load and use it.

---

### Phase 5B: Lunge **[GATE — do not start until Phase 5 Stage 5.8 is verified live]**

> ## ⚠️⚠️⚠️ REMOVED FROM THE PRODUCT (2026-07-19, HY's decision)
>
> **Leg Lunge (the entire Module B lunge exercise) was removed from the shipped
> application on 2026-07-19.** All backend, frontend, and ML source code for it —
> `backend/app/module_b/lunge/`, `frontend/src/pages/lunge/`,
> `frontend/src/utils/lunge/`, `frontend/src/components/lunge/`, the seven
> `ml/scripts/*_lunge.py` scripts, `ml/data/lunge_features.csv` +
> `ml/data/landmarks_lunge/`, and the seven standalone `ml/reports/LUNGE_*.md`
> engineering reports — has been **deleted**. The registry no longer registers a
> `LungeExercise`; `GET /api/module-b/lunge/config` now 404s like any unregistered
> exercise; `backend/app/seed.py`'s catalog seeder deactivates any pre-existing
> `lunge` row, and that seeder has been re-run against the local dev DB — the
> `lunge` catalog row is confirmed `is_active=False`.
>
> **Everything below this banner, through the end of Phase 5B, is retained as a
> historical record of the completed investigation — it no longer describes the
> shipped system.** Numbers, findings, and code references in it (file paths,
> function names) may no longer exist in the current codebase. The dissertation
> chapter draft (`ml/reports/PHASE5_CHAPTER_DRAFT.md` §11) is kept for the same
> reason and carries the same notice, but its embedded figures were **not**
> kept — HY asked separately for the lunge figures under `ml/reports/figures/`
> to be removed too (2026-07-19), so §11's eight `![...]` image references now
> point at deleted files; each was replaced with a `_[Figure N removed...]_`
> marker, and the descriptive caption text was left in place. Nothing
> lunge-related survives on disk in `ml/` beyond this document's prose and
> `task.md`'s own text.
>
> Also removed (2026-07-19): the still-unbuilt lunge deltas that were sitting in
> Phase 6/7 as future plan items — the unimplemented `backend/app/module_b/lunge/tags.py`
> spec in Phase 6 Stage 6.1, the `"lunge"` entry in Phase 7's illustrative
> dashboard-payload example, and Q6 in the Open Questions table (lunge ROM norms).
> Those were forward-looking plan text with no completed work behind them, so
> they were deleted outright rather than marked historical.
>
> Reason for removal: HY's product decision — not further elaborated in this log.

> **Frontend placeholder already exists (Stage 4.7, 2026-07-16, HY decision).** Ahead of this phase, `backend/app/seed.py` already seeds a `lunge` exercise catalog row (`mode: "rehab"`), and the frontend already shows its real thumbnail (`ExerciseSelection.tsx`) and tutorial video (`CameraSetup.tsx`, `assets/videos/Leg Lunge.mp4`). **Nothing else exists yet** — no `backend/app/module_b/lunge/` plugin, no `LungeExercise` registration, no `/lunge/live` page, no `POST`/analyze wiring. `CameraSetup.tsx`'s Start Session button is intentionally replaced with a "coming soon" message (`isLungePlaceholder`) and auto-start is disabled for this code, so no one can reach a broken session. When this phase builds the real plugin + live page, remove that gate and wire `beginSession`'s navigation the same way squat's `isSquat` branch does.

Repeat Phase 4 Stages 4.1–4.8 and Phase 5 Stages 5.0–5.9 for lunge, as `backend/app/module_b/lunge/` + a `LungeExercise` registered in the registry. Each stage below mirrors its squat equivalent (line range given); apply only the deltas listed under that stage. **Stages with no delta listed have none** — repeat the squat steps as-is for `lunge/`.

NOTE: Ask HY question for clarity because this stage is not details as squat, so if something is not clear ask question with provide simple explanation and your recommendation.

#### Stage 4.1 (Lunge) — Backend package + exercise registry

Mirrors squat's Stage 4.1 — `task.md:405-453`.

- [x] **Registry check:** adding lunge must require **zero** changes to `core/router.py`. If it doesn't, the Stage 4.1 abstraction was wrong — fix the abstraction, don't special-case.
- [x] Apply squat's Stage 4.1 steps to `backend/app/module_b/lunge/`, registering `LungeExercise`, swapping in the delta above.

### Phase 5B — Stage 4.1 (Lunge): Backend package + exercise registry (2026-07-17)

- [x] Added `backend/app/module_b/lunge/` — `config.py` (`LUNGE_CONFIG`: `exercise_code="lunge"`, `required_view="side_view"` [dataset-derived, Locked Assumption #3], `model_key="lunge"` [proposed heuristic], each X2-tagged) and `exercise.py` (`LungeExercise(ModuleBExercise)`), mirroring `squat/exercise.py`'s shell exactly. `segment`/`extract_features`/`rule_subscores`/`set_rule_scores` raise `NotImplementedError` naming the Lunge stage that fills them (4.3/4.2/4.4/4.4); `error_tags` raises `NotImplementedError` naming Stage 6.1 — identical to squat's own current `error_tags` stub, since Phase 6 hasn't shipped for either exercise yet.
- [x] Registered `LungeExercise()` in `backend/app/module_b/core/registry.py` alongside the existing `SquatExercise()` registration. `core/router.py` untouched (confirmed via `git diff --stat` — zero lines changed), proving the Stage 4.1 registry abstraction extends to a second exercise with no dispatcher edit.
- [x] No seed change needed: `backend/app/seed.py` already carries the `lunge` catalog row (`mode: "rehab"`) from the Stage 4.7 pre-work referenced in the Phase 5B intro note.
- [x] Updated `backend/tests/test_module_b_registry.py`: added `test_lunge_plugin_implements_contract`, `test_lunge_analysis_methods_are_not_yet_implemented`, `test_lunge_config_endpoint_returns_registered_config`; replaced the now-stale single-plugin `registered_exercise_codes() == ("squat",)` assertion with `test_registered_exercise_codes_lists_both_plugins` (`("lunge", "squat")`); extended the catalog-seed test to also assert `"lunge" in codes`.
- [x] **Gate:** `python -c "import app.main; print('import ok')"` passed; `GET /api/module-b/lunge/config` returns the config (asserted in the new router test); `GET /api/module-b/bogus/config` still 404 (unchanged). Full backend suite: 155/155 passing (was 151 before this stage — 12 in `test_module_b_registry.py`, up from 8).
- [ ] No lunge-specific delta was needed beyond the registry check itself — `task.md`'s Phase 5B intro lists none for this stage, and nothing surfaced during implementation that warranted asking HY for clarification.

#### Stage 4.2 (Lunge) — Feature extraction schema

Mirrors squat's Stage 4.2 — `task.md:454-490`.

- [x] **Lead-leg tag:** add a schema field so the feature vector records which leg is leading.
- [x] `**knee_passes_toe**` needs a toe/foot-tip joint in the schema. If EC3D lacks one (Stage 5.9's open question), approximate from ankle **or drop it** — and say which.
- [x] Apply squat's Stage 4.2 steps to `backend/app/module_b/lunge/features.py`, swapping in the deltas above.

### Phase 5B — Stage 4.2 (Lunge): Feature extraction schema (2026-07-17)

**Three design decisions taken with HY (the stage's "ask HY" note), all confirmed as recommended:**

1. **Feature structure = front/back split (lead-leg-invariant).** A lunge is asymmetric — the front (lead) and back leg do different jobs — so squat's both-legs-mean structure would blur them. Features are defined in `front_`_/`back_`_ terms where "front" = the lead leg, so a left-lead and an identical right-lead rep produce a **bit-identical** vector (proven by `test_features_are_lead_leg_invariant`). The model never sees left vs right.
2. **Lead-leg tag = metadata, not a numeric feature.** Added an optional `lead_leg: str | None` field to the shared `FeatureVector` (`core/features.py`), validated to `{"left","right",None}`, kept **out of** `names`/`values`. Squat leaves it `None` (unchanged); lunge sets it. This keeps the numeric vector lead-leg-invariant while still recording the anatomical side for Stage 4.4's cross-rep symmetry, the report, and the `knee_passes_toe` front-leg pick.
3. `knee_passes_toe` **= included (front leg).** Live uses MediaPipe `foot_index` (31/32) — confirmed streamed unsliced through `useMediaPipePose.ts` → `preprocessing.py`; EC3D carries `BigToe` (19/22) per `ml/docs/ec3d_joint_mapping.md`. So **no ankle approximation is needed** — the joint exists on both sides. (Left/right EC3D handedness is still open per Q3, but the lead leg is resolved from `exercise_subtype`/geometry, not from EC3D's L/R joint labels, so it doesn't block this feature.)

- [x] `backend/app/module_b/lunge/features.py` — `LUNGE_FEATURE_NAMES` (17 ordered features) + `extract_lunge_features(rep, lead_leg=None)`, a pure per-rep function (X8) that imports the shared `core/geometry` helpers (X1: same helpers the live path uses). Features: `front_/back_knee_flex_peak/min/rom_deg` (6), `front_/back_hip_flex_peak_deg` (2), `trunk_lean_peak/mean_deg` (2, central), `front_knee_ang_vel_max_dps`, `rep_duration_s`, `descent_ascent_ratio` (front-knee-driven), `front_ankle_df_proxy_deg`, `hip_mid_jitter_norm` (central), `stance_length_norm` (sagittal inter-ankle step length, replacing squat's lateral `stance_width_norm`), `knee_passes_toe_norm`.
- [x] **Lead-leg inference (live):** `_anterior_sign()` reads which way the toes point (foot_index − ankle in world-x) to fix the forward direction; `_resolve_front_leg()` then picks the more-forward ankle as front. `lead_leg=` overrides it for offline training (Stage 5.3 passes `exercise_subtype`; Stage 5.2 infers live) — same function, identical output given the same lead-leg assignment (X1 parity).
- [x] **Deliberately excluded, each with a code comment:** `knee_valgus_proxy` (frontal-plane, monocular-ill-posed — same as squat) and **within-rep left-vs-right** `symmetry_index_pct` (meaningless for a lunge; Stage 4.4's cross-rep symmetry replaces it, per that stage's delta).
- [x] `norm_ref_strategy` added to `LUNGE_CONFIG`, default `thigh_length` [proposed heuristic, R5.3] with the `trunk_length` alternative behind the switch — mirrors squat's Stage 4.2 starting state; lunge's own Stage 5.4 bake-off picks the winner empirically. `LungeExercise.extract_features()` wired to the extractor.
- [x] **Tests** (`tests/test_module_b_lunge_features.py`, 11): schema/names/metadata stable, `FrameIn` acceptance, requires-33-landmarks (foot-tip) guard, lead-leg **invariance** (left vs right bit-identical), inferred-front-leg, `lead_leg` override, deeper-front-knee ordering, `knee_passes_toe` sign flip, norm_ref thigh/trunk switch, determinism. Full backend suite: **166 passing** (was 155).
- [x] `FeatureVector` **change is backward-compatible:** the new `lead_leg` defaults to `None`; nothing iterates dataclass fields; `as_dict()`/`names`/`values` unchanged, so `model_registry`, `fusion`, `crud`, and the offline squat ML extractor (`ml/scripts/build_features.py`) are unaffected — squat's own feature tests still pass.
- [ ] **Deferred, not skipped —** `ml/reports/PHASE5_CHAPTER_DRAFT.md` **not updated this stage.** The result-recording rule triggers on a measured metric/comparison/validation finding; a feature-schema definition has no run behind it yet. The lunge feature set's dissertation write-up lands with the first numbers that exercise it (Stage 5.4 bake-off CV, Stage 5.5 training), same as squat's feature list was discussed alongside its `NORM_REF_BAKEOFF.md`/training results rather than at schema-definition time.

#### Stage 4.3 (Lunge) — Rep segmentation (lunge FSM)

Mirrors squat's Stage 4.3 — `task.md:491-510`.

- [x] Apply squat's Stage 4.3 steps to `backend/app/module_b/lunge/segmentation.py` — no lunge-specific delta.

### Phase 5B — Stage 4.3 (Lunge): Rep segmentation (2026-07-17)

**Research done before writing code, per HY's request, since a lunge is not a symmetric movement like squat:**

1. **Read** `/Users/sumhonyou/fypDataset/Segmentation.csv` **directly (Ex5, n=174 rows).** `exercise_subtype` (the lead-leg tag) **never changes within one video** (checked all 9 Ex5 videos) — front leg is a per-set stance property, not something that flips mid-recording. This matters for the FSM design: it rules out needing a per-frame lead-leg re-resolution loop, but also means the FSM cannot assume a fixed lead leg is safe to hard-code, since the live frontend for lunge (Stage 4.7 Lunge) doesn't exist yet and could still buffer more than one stance per `POST /analyze` call.
2. **Rep-duration parity is real, not assumed:** Ex5 mean rep duration = 3.37s (median 3.33s) vs Ex6 (squat) mean 3.31s (median 3.20s) — computed directly from `first_frame`/`last_frame` at the documented 30fps. Close enough that squat's tuned timing constants (`refractory_s`/`min_rep_duration_s` = 0.5s each) are a defensible starting point rather than a blind copy, pending Stage 5.4's own empirical check once real lunge landmarks exist.
3. **Biomechanical reasoning for the driving signal — landed on bilateral MEAN, same as squat, deliberately not a front-knee-only or max(left,right) signal:**

- A lunge's front and back knee both flex and extend in near-synchrony through one rep (they cycle together even though peak magnitude differs), so the mean still rises on descent and falls on return-to-standing — the only thing a phase FSM needs.
- `max(left, right)` was considered and rejected: at the bottom of a real lunge the **back** knee's joint angle can be as or more acute than the front knee's (hip-extended, near-floor back knee), so max doesn't reliably track "the front leg" anyway — it would just pick whichever knee's raw angle is momentarily larger, no better than mean for phase-boundary purposes, and it is _more_ exposed to single-leg landmark noise (in a side-view capture the far leg is the more occlusion-prone one; a max signal lets one noisy leg trigger a false rep boundary, while mean halves that impact).
- Resolving the true front leg (Stage 4.2's toe-forward geometry) was rejected for the FSM specifically: that inference needs the whole rep's frames and only matters for the _feature values_, not for detecting _where a rep is_ in a continuous stream.
- **Conclusion: task.md's "no lunge-specific delta" for this stage is correct**, not just a scope-following default — confirmed by the reasoning above and directly verified with a new invariance test (below).

- [x] `backend/app/module_b/lunge/segmentation.py` — `LungeState`, `LungeSegmentationFSM`, `segment_lunge_frames()`, `mean_knee_flexion_deg()`, mirroring `squat/segmentation.py` line-for-line (same `STANDING → DESCENDING → BOTTOM → ASCENDING → STANDING` phases over the generic `core/fsm.HysteresisRepFSM`). Only needs landmarks through index 28 (hip/knee/ankle) — Stage 4.2's toe-tip requirement is a feature-extraction-only concern.
- [x] `LUNGE_CONFIG["segmentation"]` added: `enter_descending_deg=30.0`, `exit_standing_deg=20.0`, `refractory_s=0.5`, `min_rep_duration_s=0.5`, each `[proposed heuristic, R9]` with the rep-duration-parity finding recorded inline as the reason squat's values were reused rather than guessed fresh.
- [x] `LungeExercise.segment()` wired to `segment_lunge_frames()`.
- [x] **Intentional duplication, not an oversight:** `mean_knee_flexion_deg()` is now defined identically in both `squat/segmentation.py` and `lunge/segmentation.py`. Not consolidated into `core/` this stage, matching the project's own established pattern (SLS/WBLT's `agreement.py` was duplicated first and consolidated later, at Phase 3E Stage 7, as its own dedicated move) — flagged here for a future DRY pass rather than bundled into an out-of-scope stage.
- [x] **Tests** (`tests/test_module_b_lunge_segmentation.py`, 6): clean-five-reps, jitter-noise-rejection, partial-descent-no-reps, phase-transition-to-BOTTOM, determinism — all four reusing a `_front_back_split()` helper (front=1.2x, back=0.8x a target sequence) so the bilateral mean reproduces squat's own already-validated numbers exactly while still exercising genuinely different per-leg values. Plus one new test with no squat equivalent: `test_rep_boundaries_are_invariant_to_which_leg_leads` — swaps which side leads and asserts identical rep count/duration/peak, directly proving the "mean signal doesn't need to know the front leg" conclusion above rather than just asserting it.
- [x] Fixed a Stage 4.1 test gone stale: `test_lunge_analysis_methods_are_not_yet_implemented` asserted `exercise.segment([])` raised `NotImplementedError`, which stopped being true the moment this stage wired `segment()` for real. Retargeted at `set_rule_scores` (still unimplemented until Stage 4.4).
- [x] **Gate:** `python -c "import app.main"` clean; `core/router.py` and `squat/` untouched (`git status --porcelain` empty for both). Full backend suite: **172 passing** (was 166).

#### Stage 4.4 (Lunge) — Rule sub-scores

Mirrors squat's Stage 4.4 — `task.md:511-531`.

- [x] **Symmetry is cross-rep, not within-rep** (R5.2): the two legs do different jobs in one rep, so within-rep L-vs-R is meaningless. Compare **front-knee peak flexion + ROM when leading left vs leading right**, across reps.
- [x] Apply squat's Stage 4.4 steps to `backend/app/module_b/lunge/rules.py`, swapping in the delta above.

### Phase 5B — Stage 4.4 (Lunge): Rule sub-scores (2026-07-17)

**Two architectural questions asked and confirmed with HY before writing code** (this stage genuinely diverges from squat, unlike Stage 4.3):

1. **Does cross-rep Symmetry count toward** `S_rule`**?** → **No — report-only.** It never enters the graded mean; only ROM/Tempo/Stability do, exactly as in squat.
2. **Minimum reps per leg before attempting the comparison?** → **1 rep per leg**, mirroring Tempo's "score as soon as it's computable" philosophy rather than waiting for a larger, more stable N.

**How "report-only" was made real, not just documented:** `core/rules.py`'s `RuleScores.score` is a mean over every sub-score whose `.score is not None` — there is no way to attach a _value_ to a sub-score without it entering that mean. So Symmetry's `SubScore.score` is always `None` (mechanically excluded), and its numbers live in a new `SubScore.metrics: dict[str, float]` field instead — added to the shared `core/rules.py` dataclass with a `default_factory=dict`, backward-compatible with every existing `SubScore(...)` call site (verified: none construct it positionally past `notes`). This mirrors Stage 4.2's own precedent of adding optional metadata (`FeatureVector.lead_leg`) to a shared core dataclass rather than forking a lunge-only copy. `core/crud.py`'s existing per-subscore JSON serialization was extended by one line (`"metrics": dict(sub_score.metrics)`) so the numbers actually reach the persisted report — squat's sub-scores just serialize an empty `{}}`, unaffected. A new test (`test_symmetry_never_moves_the_overall_set_score`) proves a badly-asymmetric set scores identically to a symmetric one on every other axis, not just asserts the design intent.

- [x] `backend/app/module_b/lunge/rules.py` — `rom_subscore`/`tempo_subscore`/`stability_subscore` mirror squat's formulas exactly, applied to the front leg's features (`front_knee_flex_peak_deg`, `front_ankle_df_proxy_deg`) or the lead-leg-agnostic central signal (`hip_mid_jitter_norm`, unchanged from squat since hip-midpoint jitter isn't a front/back concept). New: `symmetry_subscore(feature_vectors)` groups the set's `FeatureVector`s by `.lead_leg`, and when both cohorts have `>= min_reps_per_leg`, computes the same `|A-B|/(0.5*(A+B))*100` index formula squat's own (unused-so-far) `symmetry_index_pct` feature uses, for both front-knee peak flexion and ROM, storing rep counts and both percentages in `metrics`.
- [x] **ROM band edges re-tagged, not silently reused.** Squat's ROM bands are `[clinical norm, S1]`; lunge has no equivalent per Q6 ("no normative lunge front-knee angle table exists"). `LUNGE_CONFIG["rules"]["rom"]` reuses squat's exact same degree cutoffs (60/90/110/130) as an interim starting point — the "front knee to ~90°" cue is a real coaching convention, just not a sourced clinical cutoff — but every one is now tagged `[proposed heuristic]`, with an inline note that Stage 5.6 (Lunge) replaces them with edges calibrated from REHAB24-6's own correct-rep distribution and re-tags them `[dataset-derived]`, per that stage's own already-written delta.
- [x] Tempo and Stability configs are byte-identical to squat's (no delta needed — both movements' rep-timing envelopes measured near-identical in Stage 4.3's research, and jitter is a central-hip signal already lead-leg-agnostic).
- [x] `LungeExercise.rule_subscores()`/`set_rule_scores()` wired to `score_lunge_rep()`/`score_lunge_set()`.
- [x] Fixed a Stage 4.1 test gone stale again: `test_lunge_rule_scoring_is_not_yet_implemented` asserted `set_rule_scores([], [])` raised `NotImplementedError`, no longer true. Retargeted at `error_tags` — the only ABC method still unimplemented (Stage 6.1).
- [x] **Tests** (`tests/test_module_b_lunge_rules.py`, 11): ROM band boundaries, DF-limit floor+note, tempo unavailable-at-1-rep + CV bands, stability jitter/duration boundaries, the anti-trap long-vs-brief test, set-level duration weighting, symmetry unavailable-with-one-leg (with metrics still showing the rep counts), symmetry available at 1 rep/leg, symmetry index correctness on a real 100°-vs-80° difference (22.22%), and symmetry-never-moves-the-score. Full backend suite: **183 passing** (was 172).
- [x] **Gate:** `python -c "import app.main"` clean; `core/router.py` and `squat/` untouched (`git status --porcelain` empty for both) — the only shared-core touches were the backward-compatible `SubScore.metrics` addition and its one-line `crud.py` serialization, both verified not to break squat's own rule tests.

#### Stage 4.5 (Lunge) — Fusion + placeholder ML interface

Mirrors squat's Stage 4.5 — `task.md:532-554`.

- [x] Apply squat's Stage 4.5 steps to `backend/app/module_b/lunge/` — no lunge-specific delta.

### Phase 5B — Stage 4.5 (Lunge): Fusion + placeholder ML interface (2026-07-17)

**Reconciliation-check finding (rules.md), not silently patched over:** squat's _original_ Stage 4.5 built a `StubModel` deriving `P(Good) = rule_score/10`, but that class was deleted in Stage 5.8 once squat had a real trained model (rules.md #20). `get_model_bundle(model_key)` now unconditionally loads `ml/artifacts/{model_key}/model.joblib`, which doesn't exist for lunge (Stage 5.8 (Lunge) is far off) — calling it for lunge would crash. The old `StubModel` design can't simply be restored: it took `rule_score` as a constructor argument, baked in per-request by the _pre-Stage-5.8_ router calling it directly; today's router instead calls the cached, `model_key`-only `get_model_bundle()`, which has no access to any request's `RuleScores`, and per Stage 4.1's registry invariant `core/router.py` cannot be touched to restore that old wiring. `ModelBundle.predict_proba(features)`'s protocol genuinely has no rule-score input anymore.

**Asked HY how the restored placeholder should behave, since this is a real design fork, not a mechanical port:** confirmed **constant neutral 50/50** (`P(Good)=P(Poor)=0.5`, ignoring `features` entirely) over the alternative of a feature-derived heuristic proxy (rejected — would duplicate `rules.py` ROM logic inside `model_registry.py`, blurring the two independent signals the fusion architecture deliberately keeps separate). Consequence, stated plainly: every lunge session shows `band="Fair"` during Stages 4.6-4.8's live verification, regardless of how good the rule score is, until Stage 5.5 (Lunge) trains a real model — this is intentional honesty (confidence=0.5 is definitionally low), not a bug to fix later.

- [x] `backend/app/module_b/core/model_registry.py` — added `PlaceholderModelBundle` (constant 50/50 `predict_proba`, `model_version="stub-0"`, `is_placeholder=True`, `feature_names=()` so it skips the name-order check like the old stub did) and made `get_model_bundle()` fall back to it when `{model_key}/model.joblib` doesn't exist on disk, instead of crashing. Caching the placeholder via the existing `@lru_cache` is safe (unlike the old per-request `StubModel`) because it carries no per-request state — it's a pure constant function of nothing.
- [x] `core/fusion.py` — **zero changes**, exactly as squat's Stage 4.5 already built it: `low_confidence` (confidence=0.5 < `confidence_low_threshold`) already forces `Fair` + rule-heavy weights with no new branching needed. This is the one part of the delta-free "no lunge-specific delta" instruction that held completely true.
- [x] **No** `lunge/*.py` **file needed touching for this stage.** Fusion/model resolution is entirely router-orchestrated (`model = get_model_bundle(exercise.model_key)` in `core/router.py`, unchanged) using `LungeExercise.model_key` (already wired in Stage 4.1) — there is no exercise-level "fuse" method to implement.
- [x] **Tests** (`tests/test_module_b_lunge_fusion.py`, 5): `get_model_bundle("lunge")` falls back to the placeholder; `predict_proba` is a constant 50/50 regardless of feature values (checked at both a low and a high input); the bundle is still `lru_cache`d; **squat's own path is unaffected** (`get_model_bundle("squat")` still resolves the real trained model, not the placeholder — a direct regression guard on the new branch, not just an assumption); and a full `fuse_model()` integration proving a rule score of 9.5/10 still can't buy a confident band through the placeholder. Full backend suite: **188 passing** (was 183).
- [x] **Gate:** `python -c "import app.main"` clean; `core/router.py` and `squat/` untouched (`git status --porcelain` empty for both).

#### Stage 4.6 (Lunge) — Persistence + read-back

Mirrors squat's Stage 4.6 — `task.md:555-575`.

- [x] Apply squat's Stage 4.6 steps to `backend/app/module_b/lunge/` — no lunge-specific delta.

### Phase 5B — Stage 4.6 (Lunge): Persistence + read-back (2026-07-17)

**Schema/migration: genuinely no delta.** `module_b_results`/`module_b_error_tags` (Alembic `20260716_0008`) are already exercise-agnostic — `exercise_code` is a plain `String(100)` with no enum/check constraint anywhere in the migration or ORM model. No new migration needed; confirmed by grepping every `module_b_`*-touching migration for a `CheckConstraint` (none found).

**Reconciliation-check finding (rules.md), not silently patched over:** `core/crud.py::_metrics_json()` persisted each rep's `FeatureVector` as `{schema_version, names, values}` only — dropping the `lead_leg` metadata Stage 4.2 added. Harmless for squat (`lead_leg` is always `None` there), but a real bug for lunge: a future replay harness (Stage 5.7 (Lunge), mirroring `replay_squat_session.py`'s `--session-id` mode, which reconstructs `FeatureVector`s from exactly this persisted dict since Module B stores no raw frames by design, X4) would rebuild every vector with `lead_leg=None`, and `score_lunge_set()`'s Symmetry sub-score groups reps by `.lead_leg` — so the reconstructed replay would silently report Symmetry as "unavailable" even when the original live analysis found both legs and computed a real index. **Proved concretely, not just reasoned about:** ran the exact persist -> reconstruct round-trip before fixing it — original `{'left_lead_reps': 1.0, 'right_lead_reps': 1.0, 'front_knee_peak_symmetry_index_pct': 11.76, ...}` degraded to `{'left_lead_reps': 0.0, 'right_lead_reps': 0.0}` after a round-trip through the pre-fix serialization.

- [x] **Fix:** added `"lead_leg": features.lead_leg` to `_metrics_json()`'s `feature_vectors` entries — one field, backward-compatible (squat's vectors now persist `"lead_leg": null`, harmless).
- [x] **Tests** (`tests/test_module_b_lunge_persistence.py`, 4, mirroring squat's `test_module_b_persistence.py` structure with an in-memory `_FakeDb`): snapshot recorded without raw frames; `lead_leg` survives the persist round-trip; a full reconstruct-and-rescore proof that replayed Symmetry metrics exactly match the original (not just that the key exists); and a squat-shaped regression guard confirming a `lead_leg=None` vector persists `null` without breaking anything. Full backend suite: **192 passing** (was 188).
- [x] Everything else already generic and unchanged: `GET /api/module-b/results/{session_id}`, profile/version snapshot (`model_version`, `fusion_weights` actually used), byte-stable read-back, error-tag persistence via `_system_error_tags(fusion.flags)` (not the still-`NotImplementedError` `LungeExercise.error_tags()`, which the router never calls — confirmed unaffected, matches Stage 4.1's finding that this ABC hook is unwired until Stage 6.1).
- [x] **Gate:** `python -c "import app.main"` clean; `core/router.py` and `squat/` untouched (`git status --porcelain` empty for both).

#### Stage 4.7 (Lunge) — Frontend (lunge)

Mirrors squat's Stage 4.7 — `task.md:576-608`.

- [x] **Placeholder already exists** (Stage 4.7, 2026-07-16, HY decision): `backend/app/seed.py` seeds the `lunge` catalog row, `ExerciseSelection.tsx` shows its real thumbnail, `CameraSetup.tsx` shows `Leg Lunge.mp4` with `isLungePlaceholder` gating Start Session to a "coming soon" message and auto-start disabled. This stage's real work is **removing that gate** and wiring `beginSession`'s navigation to `/lunge/live` the same way squat's `isSquat` branch does.
- [x] Apply squat's Stage 4.7 steps to the lunge live page, swapping in the delta above.

### Phase 5B — Stage 4.7 (Lunge): Frontend (2026-07-17)

**Browser-first, per HY's explicit request.** Before writing any code, loaded the running dev server and clicked through the existing (uncommitted, HY's own) placeholder UI. That surfaced a real, pre-existing bug the plan text didn't mention: `CameraSetup.tsx`'s `isWblt` check was `exerciseCode?.includes("lunge") || exerciseCode?.includes("wblt")` — since Module B's own `"lunge"` code also contains the substring `"lunge"`, a real lunge session was silently being treated as WBLT. Confirmed live in-browser (not just by reading code): the "View guidance" panel showed WBLT's wall-distance instructions, and the demo video resolved to `(WBLT) Knee to Wall...mp4` even though `lungeDemoSrc` was correctly imported and referenced — it was simply unreachable, shadowed by the `isWblt` branch evaluated first. The exact same collision existed in `Report.tsx` (`isModuleB`/`isWblt`, plus a WBLT-trend-fetch branch keyed off the same substring). `ExerciseSelection.tsx` already had the correct fix precedent (an exact `code === "lunge"` check, with its own comment explaining why) — mirrored that pattern into both files rather than inventing a new one.

- [x] `CameraSetup.tsx`**:** `isWblt` changed to an exact match (`exerciseCode === "weight_bearing_lunge_test"`); added `isLunge = exerciseCode === "lunge"` with its own guidance steps (`lunge.setupGuidanceSide/Stance/Depth`) and correctly-reached `lungeDemoSrc`. Removed `isLungePlaceholder` entirely — Start Session and auto-start are no longer gated, `beginSession()` routes to `/lunge/live`.
- [x] `frontend/src/utils/lunge/lungeLiveEstimate.ts` (new) — mirrors `squatLiveEstimate.ts`'s shape (fetches `GET /api/module-b/lunge/config`, same hysteresis rep FSM), adapted for the asymmetric front/back structure Stages 4.2/4.3/4.4 already established: the FSM's entry/exit signal is still the **bilateral mean** (matches backend's segmentation decision), but the front leg is re-resolved only while standing (mirrors Stage 4.3's "front leg is a stance property, not a per-frame one" finding) and the depth gauge, peak tracking, and band estimate all read the **front knee** specifically. Added a live **knee-passes-toe** boolean, computed every frame from the front knee vs. front toe (foot_index) position along the inferred anterior direction — the one lunge-specific fault signal, directly answering HY's ask for live feedback on "what they go wrong."
- [x] `frontend/src/pages/lunge/LungeLiveSessionPage.tsx` (new) + `frontend/src/components/lunge/StartSetCountdown.tsx` (new) — structurally a close mirror of `SquatLiveSessionPage.tsx`/`components/squat/StartSetCountdown.tsx` (same `setup → countdown → recording → posting` stage machine, same target-rep picker, inactivity/target-hit prompts, Finish Set → `POST /api/module-b/analyze` → `sessionService.end` → `/report` flow), per HY's explicit "copy squat's structure and flow" instruction. The countdown component was duplicated rather than generalized into a shared component — matches this project's own established per-exercise-duplication convention (e.g. backend `lunge/segmentation.py` duplicating `squat/segmentation.py`'s shape) over a cross-cutting refactor not asked for.
  - **Countdown pauses capture, verified by re-reading squat's own logic before copying it (HY's point 5):** the frame-recording `useEffect` only runs `if (stage === "recording")`; the countdown timer calls `startSet()` (which resets the estimator/recorder and flips `stage` to `"recording"`) only once it reaches zero. No frames are buffered and no landmarks reach the estimator during the 5s countdown — confirmed by tracing the effect's guard, not assumed.
  - Live panel additionally shows a front-leg badge (`lunge.frontLeg_left/right`) and a highlighted knee-passes-toe warning banner when triggered, neither of which squat's page has (squat has no asymmetric-leg or toe-position concept).
- [x] `App.tsx` — registered `lunge/live` → `LungeLiveSessionPage`.
- [x] `Report.tsx`**:** `isModuleB` now checks a `MODULE_B_EXERCISE_CODES = new Set(["squat", "lunge"])` set (exact match) instead of `=== "squat"`; the same substring-collision fix applied to `isWblt` and the WBLT-trend-fetch branch. `ModuleBSubScore` (in `moduleBService.ts`) extended with an optional `metrics` field. Since Stage 4.4's cross-rep Symmetry sub-score always has `score: null` by design (report-only), a plain sub-score row would show an unexplained "—" — added a `symmetryNote()` helper that renders its `metrics` (left/right lead rep counts, peak/ROM symmetry index %) as a sub-line instead, or an "not enough reps on both legs yet" message when only one leg was led.
- [x] `ExerciseSelection.tsx`**:** `repInfoFor("lunge")` no longer returns `exercise.comingSoon` (now `exercise.repsUnlimited`, matching squat's own unlimited-set UX). `backend/app/seed.py`'s lunge catalog description no longer says "Coming soon."
- [x] **i18n (en/zh/ms):** added a full `lunge.`* block (mirroring `squat.`*'s 20+ keys, values genuinely translated per locale — not copied English placeholders) plus `moduleB.subscore_symmetry_cross_rep` and `report.lungeMetrics`/`symmetryUnavailableSingleLeg`/`symmetryCrossRep`. Deleted the now-dead `squat.lungeComingSoon` key from all three locales (grepped for callers first — the house rule — confirmed zero after the `CameraSetup.tsx` gate was removed).
- [x] **Tests:** extended `Report.test.tsx` (the file this exact stage's own precedent — Phase 3E Stage 2's "wrong panel" lesson — designated as the regression guard) with two new cases: a lunge session renders the Module B panel (never Module A) and its Symmetry note renders correctly from a synthetic `metrics` payload; a `weight_bearing_lunge_test` session still renders the Module A panel (never Module B) — a live regression proof for the exact collision bug fixed above, not just a hypothetical one. Also fixed a **pre-existing, unrelated** build break in this same file (`baseSession` mock missing the `rep_count` field `SessionDTO` now requires, from an earlier uncommitted session's work) — a one-line, mechanical fix, confirmed via `git log`/`git diff` to be unrelated to any of this stage's own logic before touching it.
- [x] **Verified live in-browser**, not just by reading code: registered a fresh test account, clicked the Leg Lunge card (now shows "SIDE VIEW · REPS", not "COMING SOON"), confirmed the demo video element's resolved `src` is `Leg Lunge.mp4` (was `(WBLT) Knee to Wall...mp4` before the fix), confirmed "View guidance" shows the new lunge-specific steps, clicked "Start session" through to a real `/lunge/live` navigation, clicked "Start Set" and watched the countdown render "LEG LUNGE" / "Get into position — the set starts automatically." (matching the exact visual style HY showed for squat), watched it auto-transition to the recording stage with the front-leg badge / depth gauge / trunk lean panel rendering correctly. Also re-verified the **real** WBLT flow (functional mode) still shows its own correct guidance and demo video after the collision fix — a live regression check, not just the unit test.
- [x] **Gate:** `npx tsc --noEmit` clean, `npm run build` clean, `npm run test` 4/4 passing, ESLint clean, Prettier clean on every touched frontend file; backend `test_frontend_disclaimers.py` (forbidden-clinical-phrase scan) passes on the new locale content; full backend suite still 192/192; `core/router.py` and backend `squat/` untouched.

#### Stage 4.8 (Lunge) — Phase 4 verification gate

Mirrors squat's Stage 4.8 — `task.md:609-627`.

- [x] Apply squat's Stage 4.8 verification gate to lunge — no lunge-specific delta.

### Phase 5B — Stage 4.8 (Lunge): Phase 4 verification gate (2026-07-17)

- [x] Full backend suite green: **192/192** (unchanged since Stage 4.7 — this stage adds no new backend code, only verification).
- [x] `test_frontend_disclaimers.py` already covers the `lunge.*` i18n block (confirmed in Stage 4.7's own gate; re-ran here, still 4/4 passing).
- [x] **Verified live end-to-end against the real backend + Postgres — the Module A house standard, not just unit tests.** This environment's sandboxed browser cannot grant real webcam access (confirmed: every capture attempt returns `NotAllowedError: Permission denied`), so unlike squat's own Stage 4.8 (which had physical-camera access), a scripted-but-real HTTP flow substitutes for the live capture step while every other link in the chain is the real thing: authenticated as a real registered user, driven through the browser's own `fetch`/stored bearer token (the exact request path `moduleBService`/`sessionService` use, not a bypass), against the actually-running FastAPI + Postgres instance.
  - `POST /api/sessions/start` (`exercise_code: "lunge"`) → real session id.
  - Built a 90-frame, 6-rep synthetic world-landmark stream — 3 reps leading left, 3 leading right (deliberately covering **both** lead-leg cohorts in one continuous set, exercising Stage 4.4's cross-rep Symmetry, not just ROM/Tempo/Stability) — using the exact front=1.2x/back=0.8x-of-a-validated-mean-sequence construction already proven correct in `test_module_b_lunge_segmentation.py`.
  - `POST /api/module-b/analyze` → **6/6 reps segmented**, all four rule sub-scores present: ROM 6.99/10, Tempo 10.0/10 (near-perfectly consistent synthetic rep durations, as designed), Stability 5.0/10, Symmetry correctly **available** (`left_lead_reps: 3, right_lead_reps: 3, front_knee_peak_symmetry_index_pct: 0.16%, front_knee_rom_symmetry_index_pct: 0.28%` — near-zero, correctly reflecting the deliberately balanced synthetic performer). Fusion: `rule_score=7.33`, `ml_score=5.0` (the constant 50/50 placeholder), `confidence=0.5` → `low_confidence` flag → **Fair** band, rule-heavy weights (0.7/0.3) — exactly Stage 4.5's designed behavior, not a surprise.
  - **Confirmed the Stage 4.6 persistence fix works for real, not just in a unit test:** every returned `feature_vectors[i].lead_leg` was correctly `"left"`/`"right"` (3 and 3), proving the round-trip fix actually reached the live database write path.
  - `POST /api/sessions/{id}/end` → session `status: "completed"`.
  - Two successive `GET /api/module-b/results/{id}` calls → **byte-identical** (`body1 === body2`, compared as raw response text, not just parsed-equal).
  - Navigated the real browser to `/report?session={id}` and read the **rendered page text** (not the API response): `LEG LUNGE METRICS` eyebrow, `6.6 / 10`, `Fair` band, `Capture quality: Good`, all four sub-score rows correct including the Symmetry note (`"3 left-lead reps, 3 right-lead reps — 0.2% peak-depth difference, 0.3% ROM difference"` — `symmetryNote()` from Stage 4.7 rendering live, real persisted data, not a test fixture), `ML prediction 5.0/10`, `Confidence 50%`, the `low_confidence` error tag, and the non-diagnostic disclaimer.
- [x] **Found and fixed a second, previously-unnoticed collision bug from this exact live check** (not from re-reading code — the rendered banner text is what caught it): `report.moduleBPlaceholderNotice` was hardcoded to _"...while the trained **squat** model is being built..."_ regardless of which Module B exercise the session actually was — nobody had a second Module B exercise to notice this until now. Fixed by parametrizing the string with `{{exercise}}` (`session.exercise_name`) in en/zh/ms and passing it from `Report.tsx`; re-verified live — now correctly reads _"...while the trained **Leg Lunge** model is being built..."_ for this session, and remains correct for squat (parametrized off the same field squat's own sessions already carry).
- [x] **Gate:** `npx tsc --noEmit` clean, `npm run build` clean, `npm run test` 4/4, ESLint/Prettier clean on every re-touched file, backend disclaimer scan 4/4, full backend suite 192/192 after the fix.

**Deliverable:** Module B works end-to-end for lunge with an announced placeholder model, verified against the real backend + Postgres, matching squat's own Stage 4.8 standard. Phase 5 (Lunge) only has to replace the placeholder with a trained artifact.

#### Stage 5.0 (Lunge) — Data audit **[HARD GATE — no training work until this reports numbers]**

Mirrors squat's Stage 5.0 — `task.md:632-730`.

- [x] **Generalisation note:** confirm during the audit that REHAB24-6 is the **only public labelled lunge dataset** — there is no second source to cross-check against. **→ Checked, and the premise is false. See the Phase 5B — Stage 5.0 entry below.**
- [x] Apply squat's Stage 5.0 steps to the lunge data audit, swapping in the delta above.

### Phase 5B — Stage 5.0 (Lunge): Data audit (2026-07-17)

Full numbers and the three options with trade-offs: `[ml/reports/LUNGE_DATA_AUDIT.md](./ml/reports/LUNGE_DATA_AUDIT.md)`. The side-view Ex5 cohort is **88 reps, Good 39 / Poor 49** — both classes materially below the gate text's ~90/category reference, so the gate triggered, but with the **opposite shape to squat's** (squat was large-but-lopsided at 72/26; lunge is small-but-balanced). Options were (a) accept 88 / (b) admit half-profile as a flagged cohort (+86 reps, 39 Good / 47 Poor) / (c) relax to both views + a `view` feature.

**✅ Resolved by HY (2026-07-17): option (a) — accept the smaller N.** Stage 5.2 (Lunge)
onward trains on the 88 verified side-view Ex5 reps (39 Good / 49 Poor, 8 subjects) only.
The lead-leg/subject confound (§5.1 of the report) and the unvalidated cross-rep Symmetry
metric remain open regardless of this choice — neither is fixed by any gate option — and
carry forward into Stage 5.3's feature decisions and the eventual write-up.

- [x] **Reconciliation check passed first:** every artifact squat's Stage 5.0 claims (`ml/config.yaml`, `ml/docs/rehab24_6_schema.md`, `ml/scripts/audit_rehab246.py`, `ml/reports/DATA_AUDIT.md`) exists on disk and the dataset root is present; re-ran `audit_rehab246.py` and reproduced `DATA_AUDIT.md`'s Ex6 numbers exactly before touching anything.
- [x] `ml/scripts/audit_rehab246.py` — the side-view/view-question block was hardcoded to Ex6; extracted it into `_side_view_report(rows, ex_id)` and ran it for **both** Ex5 and Ex6. Purely additive: a section-by-section comparison of the old and new output confirmed **all 8 pre-existing sections byte-identical**, 10 new ones added. Also added, for Ex5 only, the lead-leg tag's survival through the view filter (`ex5_side_view_by_subtype`, `..._subtype_x_correctness`) — Stage 4.4's Symmetry and Stage 5.3's lead-leg feature both depend on it. Black/isort clean.
- [x] `ml/scripts/make_view_figure.py` (new) — squat's own view verification was done ad hoc and left no script behind; this one makes the answer reproducible (`--exercise`/`--video`, reads `config.yaml`, read-only, goes through `plotting.save_fig()`).
- [x] **Ex5 raw numbers:** 174 reps, Good **78** / Poor **96** (Poor is the _majority_ — inverts Ex6's 134/61). `cam17_orientation`: front **88** / half-profile **86** / profile **0**. `mocap_erroneous` **0**. `lights_on` 154 on / 20 off. `exercise_subtype` (lead-leg tag): right **91** / left **83**. **Subjects: 8 (ids 2-9) — subject 1 is absent from Ex5 entirely**, where Ex6 has 9; every lunge LOSO fold count is 8, not 9. Subject **3** is single-class (21 Poor, 0 Good) **before** any filter — unlike Ex6, where the raw data was clean and the view filter created the problem.
- [x] **View question verified for Ex5 specifically, not carried over from Ex6** — a lunge is a _directional_ movement (the subject steps along their facing axis), so squat's verification does not transfer on its own. Extracted real mid-rep frames from both cameras (`PM_021` rep 1 front / rep 11 half-profile): `cam17_orientation == "front"` → Camera17 sees the subject dead-on with the split stance foreshortened almost to overlap; **Camera18 shows a clean true sagittal view** (forward leg, dropped rear knee, hip/knee/ankle separated in the image plane). `half-profile` → both cameras diagonal, neither usable. **Confirmed on a second subject with the opposite lead leg** (`PM_028`, front-leg-right) — squat's audit checked only one video. Figure: `ml/reports/figures/view_verification_ex5.png`.
- [x] **Usable side-view Ex5 rep count: 88** (all `front`, from Camera18) — **50.6%** of Ex5. Good **39** / Poor **49**. Lead-leg left **42** / right **46** (both cohorts survive). All 8 subjects still present; **the view filter creates no new single-class subject** (only subject 3, which already was) — 7 of 8 folds carry both classes, vs squat's 6 of 9. Dropping subject 3 would leave **77 reps, 39 Good / 38 Poor, 7 subjects**.
- [x] **Real finding #1 — lead-leg is perfectly confounded with subject.** `exercise_subtype` is constant within every video **and within every subject**: all 8 subjects lunged with exactly one lead leg, **none performed both** (9 videos, verified in code). Not a view artifact — no gate option fixes it. Two consequences: (i) under LOSO, `lead_leg` is perfectly collinear with the held-out subject, so **Stage 5.3 (Lunge) must treat** `lead_leg` **as a leakage risk, not a free feature choice** — the apparent lead-leg/label association (left 21G/21P vs right 18G/28P) is **entirely subject 3**, and vanishes without it (right → 18G/17P); (ii) **Stage 4.4's cross-rep Symmetry sub-score has no ground truth in this dataset at all** and cannot be validated by any filtering of it. It is already report-only by HY's Stage 4.4 decision, so nothing shipped is wrong — but Phase 5B cannot produce evidence for it, and the write-up must not imply it was validated.
- [x] **Real finding #2 — the generalisation note's premise is false, and it's good news.** REHAB24-6 is **not** the only public labelled lunge dataset. **EC3D** (already on disk — the same `data_3D.pickle` Stage 5.9 used for squat) has **127 lunge sequences, 4 subjects, 46 Correct / 81 faulty**, and its lunge partition is **larger than its squat one** (12,754 frames vs 11,109). Label ids confirmed against the EC3D paper's own Table 1 by **exact count match, not inference**: `1`=Correct (46), `4`="Not low enough" (40), `6`="Knee passes toe" (41). **Both lunge faults are sagittal-plane** — unlike EC3D squat, where 2 of 4 were frontal and invisible under Locked Assumption #3 — and "Knee passes toe" is **exactly** the signal Stage 4.2/4.7 already implemented. **UI-PRMD** also has inline/side lunge (10 subjects, correct/incorrect), Kinect+Vicon skeletons only. **The plan's practical consequence survives:** both alternatives ship skeletons, not RGB, and Stage 5.2's pipeline needs RGB video (X1/X3) — so the corrected statement is "the only public labelled lunge dataset **with RGB video**". **Caveat kept explicit:** EC3D's canonicalisation and its shallower-is-incorrect fault direction are the same two failure modes that sank squat's Stage 5.9; lunge has a _better-matched_ external cohort available, not a guaranteed-successful one.
- [x] **Open question flagged, not answered:** because each subject has a fixed facing _and_ a fixed lead leg, whether the lead limb is the near or far limb from Camera18 may be fixed per subject — which would couple the known far-limb occlusion problem (chapter draft §3.2) to lead-leg and therefore to subject. The frames are _consistent_ with this but cannot establish it (near/far limb is not reliably readable by eye). Needs landmark-level visibility/`z`-ordering measurement at **Stage 5.4 (Lunge)**. Recorded as a risk to measure, not a finding.
  - ✅ **RESOLVED at Stage 5.4 (Lunge) (2026-07-17) — the risk is real and now measured.**
    The far limb is **right in all 9 videos** and lead leg is fixed per subject, so the front
    leg **is** the occluded limb for right-lead subjects and the clearly-visible one for
    left-lead. Against OptiTrack, `front_knee_flex_peak_deg` is biased **−6.19° (left-lead)**
    vs **−15.13° (right-lead)** — an **8.9° cohort-dependent offset on the gate feature**,
    produced purely by which side faced the lens. This upgrades Stage 5.0's `lead_leg`
    leakage warning from hypothesis to fact **and sharpens it**: the confound is physically
    encoded in the feature _values_, so excluding the `lead_leg` column is necessary but
    **not sufficient**. See `ml/reports/LUNGE_MOCAP_AGREEMENT.md`.
- [x] **Reports written:** `ml/reports/LUNGE_DATA_AUDIT.md` (every number above + the gate options; supersedes `DATA_AUDIT.md` §2's Ex5 forward-reference summary), and `ml/reports/PHASE5_CHAPTER_DRAFT.md` extended in place per rules.md with **§11 The Lunge Dataset** (§11.1 data availability, §11.2 view selection + Figure 16, §11.3 sample size + Table 7, §11.4 the lead-leg confound, §11.5 limitations **19-21** added to the running list). Chapter title/preamble widened from "Squat Model Development" to "Model Development" since §11 is no longer squat-only.
- [ ] **Not done, correctly:** Stage 5.1/5.2 onward (scaffold reuse, landmark extraction, feature table, training) — gate is now resolved (option (a), above), but Stage 5.1 has not been started, per scope discipline (this stage stops at the gate decision).

#### Stage 5.1 (Lunge) — `ml/` scaffold

Mirrors squat's Stage 5.1 — `task.md:731-795`.

- [x] Apply squat's Stage 5.1 steps to the lunge `ml/` scaffold — no lunge-specific delta.

### Phase 5B — Stage 5.1 (Lunge): `ml/` scaffold (2026-07-17)

**No lunge-specific delta, and none was needed:** `ml/`'s scaffold (`config.yaml`,
`requirements.txt`, `scripts/plotting.py`, `data/`, `artifacts/`, `reports/`,
`backend/pyproject.toml`'s editable install) is shared infrastructure, already built by
squat's own Stage 5.1 (2026-07-16) and untouched by Phase 5B's plugin work so far. This
stage's real job was verifying that shared scaffold actually extends to a second exercise,
not rebuilding it.

- [x] **Reconciliation check passed first:** confirmed every item squat's Stage 5.1 claims
  ```
  built (`ml/data/`, `ml/artifacts/` with `.gitkeep`, `requirements.txt`,
  `backend/pyproject.toml`, `scripts/plotting.py`, `ml/README.md`) is present and unchanged
  on disk before touching anything.
  ```
- [x] **X1 editable install re-verified live for the lunge plugin specifically, not
  ```
  assumed from squat's own check:** `from app.module_b.lunge.exercise import
  ```

LungeExercise`and`from app.module_b.lunge.features import LUNGE_FEATURE_NAMES,
extract_lunge_features`both succeeded through the same`pip install -e ../backend `squat's Stage 5.1 set up — real import inside`ml/.venv`, not a hypothetical path.` LUNGE_FEATURE_NAMES` resolved to all 17 features Stage 4.2 (Lunge) defined.

- [x] **Real finding:** `app.module_b.core.registry` imports FastAPI at module level, and
  ```
  `ml/requirements.txt` does not install the backend's web-framework dependencies — only
  `app`'s feature/exercise modules, which is all any Stage 5 script needs. Verified this is
  not new to lunge (squat's own Stage 5.1 check also went through `squat.exercise`
  directly, never `core.registry`) — recorded explicitly in `ml/README.md` so a later
  script doesn't `import app.module_b.core.registry` by habit and hit a confusing
  `ModuleNotFoundError: fastapi` in the `ml/` venv.
  ```
- [x] `requirements.txt` needs no lunge-specific addition — the same
  ```
  mediapipe/scikit-learn/pandas/numpy/joblib/matplotlib/seaborn/pyyaml stack serves both
  exercises' Stage 5.2+ scripts.
  ```
- [x] `ml/README.md` updated: title and opening line widened from "Squat model training
  ```
  (Phase 5)" to cover both exercises (Phase 5 squat / Phase 5B lunge) explicitly, noting
  per-exercise work lives in per-exercise scripts/subdirectories inside the same shared
  tree, not a forked `ml/`; the verify snippet now imports both `SquatExercise` and
  `LungeExercise`; added the FastAPI/registry note above.
  ```
- [x] **Gate:** full backend suite still 192/192 (nothing in `backend/app` touched);
  ```
  Prettier clean on `ml/README.md`.
  ```
- [ ] **Deliberately not created (scope discipline, same as squat's own Stage 5.1):** any
  ```
  lunge-specific `scripts/*.py` (`extract_landmarks`/`build_features`-equivalents for
  lunge land in Stage 5.2/5.3), and no `ml/reports/PHASE5_CHAPTER_DRAFT.md` update — this
  stage produced no measured metric or comparison, matching Stage 4.2 (Lunge)'s own
  precedent for schema/scaffold-only stages.
  ```

#### Stage 5.2 (Lunge) — Landmark extraction from RGB video

Mirrors squat's Stage 5.2 — `task.md:796-987`.

- [x] **Lead-leg tag:** at runtime, infer from which foot is forward in world landmarks.
- [x] Check whether a toe/foot-tip joint is available in the extracted landmark set, for `knee_passes_toe` (see Stage 4.2 and Stage 5.9's open question).
- [x] Apply squat's Stage 5.2 steps to lunge landmark extraction, swapping in the deltas above.

### Phase 5B — Stage 5.2 (Lunge): Landmark extraction (2026-07-17)

- [x] **Reconciliation check passed first:** confirmed squat's `extract_landmarks.py`, its
  ```
  9 cached `.npz` files, and `ml/reports/PARITY_CHECK.md` are all present and unchanged;
  confirmed all 9 Ex5 video files exist for both cameras (including the `PM_117a`/
  `PM_117b` two-file split for subject 9) before writing anything.
  ```
- [x] `ml/scripts/extract_landmarks_lunge.py` (new) — a structural mirror of
  ```
  `extract_landmarks.py`: identical `PoseLandmarkerOptions` (CPU delegate, `VIDEO` mode,
  `num_poses=1`, confidence thresholds 0.5), one fresh `PoseLandmarker` per video (avoids
  the non-monotonic-timestamp crash squat's own Stage 5.2 hit and fixed), skip-if-exists
  resumability (verified live: a second run correctly skipped all 9 cached videos),
  `.npz` output to `ml/data/landmarks_lunge/` (gitignored, matches `ml/data/*`, no new
  `.gitignore` rule needed). Swapped: `TARGET_EXERCISE_ID = "5"`, `videos_dir / "Ex5"`.
  Black/isort clean.
  ```
- [x] **Two Stage 5.2 (Lunge) deltas resolved by reading the code, not by adding new
  ```
  logic:** (1) **lead-leg inference** is rep-scoped
  (`app.module_b.lunge.features._anterior_sign`/`_resolve_front_leg`), which this
  extractor — dumping raw, unsegmented per-frame landmarks — has no reps to run it on;
  live inference already shipped at Stage 4.2/4.7, offline training uses
  `exercise_subtype` instead per Stage 5.3 (Lunge)'s own delta, so there is nothing for
  this script to compute. (2) **toe/foot-tip joint availability** is a property of
  MediaPipe's fixed 33-landmark output (`LEFT_FOOT_INDEX`=31, `RIGHT_FOOT_INDEX`=32),
  not something that varies by exercise — verified against the real extracted data
  below rather than just asserted.
  ```
- [x] **Extraction result, all 9 side-view Ex5 videos (verified by reading every `.npz`
  ```
  back):** **26,087 total frames, 0 frames with no detected pose (0.00%)** — cleaner
  than squat's own 30,028-frame run (1 missing frame). Runtime ~4m 44s (9 videos, one
  landmarker each). Per-video frame counts: PM_021 2846, PM_028 3638, PM_037 2246,
  PM_042 3614, PM_104 3193, PM_112 4445, PM_117a 1184, PM_117b 1772, PM_125 3149 — all at
  30fps, matching `Segmentation.csv`'s frame indices.
  ```
- [x] **Toe-joint delta closed with real numbers:** landmarks 31 (`LEFT_FOOT_INDEX`) and
  ```
  32 (`RIGHT_FOOT_INDEX`) are present (non-NaN) in **100% of all 26,087 frames**, with
  plausible mean visibility (left 0.967–0.989, right 0.826–0.980) and coordinates that
  visibly change frame-to-frame rather than sitting frozen (spot-checked `PM_021` frames
  150/300). No ankle-approximation fallback is needed — confirmed, not assumed.
  ```
- [x] **Real finding — partially answers Stage 5.0's open question about near/far-limb
  ```
  occlusion and lead leg.** Measured mean knee/ankle visibility **within the labelled rep
  windows only** (`Segmentation.csv`'s `first_frame`/`last_frame`), cross-referenced
  against each video's `exercise_subtype`: **left knee/ankle visibility is higher than
  right in all 9 videos, regardless of lead leg** (true for both `front leg left` and
  `front leg right` videos alike — e.g. `PM_028`, lead=right: knee L 0.996/R 0.966;
  `PM_104`, lead=left: knee L 0.981/R 0.773). This means near/far-limb visibility is a
  **camera/subject-orientation artifact** (Camera18 consistently sees the subject's left
  side more clearly), **not** coupled to lead leg as Stage 5.0 speculated it might be —
  the open question is now answered in the "not lead-leg-linked" direction, though the
  camera-orientation mechanism itself is still not fully explained. **Severity is milder
  than squat's:** the lowest right-knee mean visibility here is 0.672 (`PM_117b`), still
  above the `MIN_VISIBILITY = 0.6` threshold that triggered squat's persistent-occlusion
  freeze bug (squat's right knee fell to 0.59–0.78). This does not prove lunge is free of
  the same failure mode — mean-over-rep-window can mask a lower minimum at the deepest
  part of individual reps — so it is **flagged for Stage 5.4 (Lunge)'s feature-validity
  check to confirm empirically**, not resolved here.
  ```
  - ✅ **RESOLVED at Stage 5.4 (Lunge) (2026-07-17): the mean DID mask it — 10/88 reps drop
    below** `MIN_VISIBILITY` **in their deepest 20% of frames** (all of them left-lead subjects,
    where the far/right limb is the _back_ leg). **But the dip is not the important part:**
    the far limb's ~18° under-read persists where visibility is high (right-lead: 0.938 mean,
    0/46 reps dipping, still −15.1° bias), so MediaPipe is _confidently wrong_ rather than
    flagging uncertainty, and no confidence-threshold policy can catch it. See
    `ml/reports/LUNGE_OCCLUSION_CHECK.md` and `ml/reports/LUNGE_MOCAP_AGREEMENT.md`.
- [x] **Parity check reused by reference, not re-run — reasoning recorded, not silently
  ```
  skipped.** `ml/reports/PARITY_CHECK.md` measured WASM-vs-native-delegate numeric
  divergence (0.90° mean / 4.6° max knee-flexion angle) using the _same_ model asset,
  _same_ `PoseLandmarkerOptions`, and _same_ delegate this script also uses — a property
  of the shared pose-landmarker pipeline, invariant to which exercise the subject is
  performing. Rebuilding the removed browser harness (`frontend/parity-check.html` +
  `devPages/parityCheck.ts`, deliberately deleted after squat's check per that report's
  own "Cleanup" section) to re-measure the same infrastructure fact on a lunge clip would
  not test anything the squat result didn't already establish. Recorded as a scoping
  decision, not an oversight.
  ```
- [x] **Gate:** Black/isort clean on `extract_landmarks_lunge.py`; full backend suite
  ```
  still 192/192 (nothing in `backend/app` touched); `npx tsc --noEmit` clean (nothing in
  `frontend/src` touched); `git status` on `frontend/` clean (no harness re-created).
  ```
- [x] `ml/reports/PHASE5_CHAPTER_DRAFT.md` extended with **§11.6 Landmark Extraction**
  ```
  (frame counts, the toe-joint verification, the near/far-limb finding, and the parity
  reuse rationale) since this stage produced measured results, per the Phase 5 Result
  Recording rule.
  ```

#### Stage 5.3 (Lunge) — Build the feature table

Mirrors squat's Stage 5.3 — `task.md:988-1098`.

- [x] **Lead-leg tag:** for training, **use** `exercise_subtype` **from** `Segmentation.csv` — it's given.
- [x] `knee_passes_toe` feature column: approximate from ankle **or drop it**, per Stage 5.2's finding — and say which.
- [x] Apply squat's Stage 5.3 steps to the lunge feature table, swapping in the deltas above.

### Phase 5B — Stage 5.3 (Lunge): Build the feature table (2026-07-17)

- [x] **Reconciliation check passed first:** `extract_lunge_features`/`LUNGE_FEATURE_NAMES` (17 features), `segment_lunge_frames`, and `preprocess_world_landmarks` all import cleanly through the `ml/` editable install (X1 — the offline builder calls the live functions, never re-implements them); `Segmentation.csv`'s Ex5 side-view count re-derived as **88 reps, 39 Good / 49 Poor**, exactly matching Stage 5.0 (Lunge)'s audit before writing anything.
- [x] `ml/scripts/build_features_lunge.py` (new) — structural mirror of `build_features.py`: preprocesses each video's **entire** stream once via the backend's `preprocess_world_landmarks` (X1; stateful OneEuroFilter means windowing-first would reset per-rep and drift from live), windows the _preprocessed_ stream by the dataset's physio-verified `first_frame`/`last_frame` (not our FSM), calls `extract_lunge_features()`, and emits `ml/data/lunge_features.csv` **— 88 rows, 39 Good / 49 Poor, 8 subjects (2-9), 9 videos, 17 features, 27 total columns**, `feature_schema_version` `1.0.0`. Per-subject Good/Poor verified identical to `LUNGE_DATA_AUDIT.md`'s table. Black/isort clean.
- [x] **Schema validation:** `write_features_csv()` asserts the CSV's feature block, in order, equals `LUNGE_FEATURE_NAMES` before writing; the per-rep extractor re-checks `FeatureVector.names`; and the build asserts the lead-leg override actually took effect (`vector.lead_leg == lead_leg`) rather than trusting it. Fails loudly on drift.
- [x] **Delta 1 — lead-leg tag: used the dataset's given** `exercise_subtype`, mapped `"front leg left"` → `left` / `"front leg right"` → `right` and passed as `extract_lunge_features(rep, lead_leg=...)`, overriding live geometric inference. Result: 42 left-lead / 46 right-lead, matching the audit.
- [x] **Delta 2 —** `knee_passes_toe`**: KEPT as a real measured feature** (the answer the plan asked to "say which"): **not** approximated from the ankle and **not** dropped. Stage 5.2 (Lunge) verified the foot-tip landmarks are present in 100% of all 26,087 frames (mean visibility ≥0.826/side), so the fallback the plan allowed for is unnecessary. `knee_passes_toe_norm` shows a real spread across reps, not a frozen default — logged in the report.
- [x] `lead_leg` **emitted as metadata, NOT as a model feature** — enforced structurally, not by convention: it sits outside the CSV's feature block (asserted), and Stage 4.2 already designed the vector lead-leg-**invariant** (front/back split ⇒ a left-lead and identical right-lead rep produce a bit-identical vector), with `lead_leg` living on `FeatureVector.lead_leg` metadata outside `names`/`values`. Written for traceability and Stage 5.4's per-cohort analysis only. **Stage 5.5 must not train on it** (Stage 5.0's subject-confound leakage risk).
- [x] `label_map.json` **reused, not forked:** it is exercise-agnostic (Option A, `correctness` → Good/Poor, `no_fair_in_training: true`), so this build **verifies** it agrees with the mapping used rather than writing a second copy to keep in sync.
- [x] **Real finding #1 — a dataset annotation overruns its video, caught by the frame-alignment guard.** `PM_117a` rep 9 is annotated `1110-1185`, but the video is 1184 frames (last valid index 1183) — an overshoot of 2 frames / 67 ms at the tail of a 2.53 s rep. **Investigated before acting rather than loosening the guard:** both cameras report _and decode_ exactly 1184 frames, all 8 other reps in that video sit well inside it, and it is the **only** such rep in the entire Ex5+Ex6 corpus (369 reps) — so this is an annotation artifact, not the "frame/camera misalignment" the guard's message asserted. Squat never hit it (zero Ex6 overruns), which is why the guard never fired before. Fix: split the guard into two — a rep starting past the video's end still raises (real misalignment), and a tail overshoot raises only beyond `MAX_TAIL_OVERSHOOT_FRAMES = 5`; within tolerance the window is clamped, **counted, printed, and tabled in the report** (never silent). Kept rather than dropped because the loss is post-peak tail (peak/ROM features unaffected; only `rep_duration_s` shortens by 67 ms) and because HY's Stage 5.0 gate decision was explicitly to train on **88** reps — dropping one would silently deviate from the approved cohort and cost a Poor-class rep.
- [x] **Real finding #2 (significant) — the lunge FSM merges reps, at 56.8% recall vs squat's 94.9%.** The free FSM-vs-dataset validation returned **112/174 GT reps matched overall; front (trained) reps 50/88 = 56.8%**, against squat's 184/195 / 93/98. **Diagnosed rather than reported bare**, via a new reproducible `exit_threshold_diagnostic()`: it is **not** the enter threshold (the driving signal peaks above 30° in **173 of 174** reps — the FSM sees every descent); it is the **exit** threshold. `segment_lunge_frames` drives off the **bilateral mean** knee flexion and closes a rep only when that mean falls under `exit_standing_deg = 20°`; a subject who only **partially extends between consecutive reps** never returns it to baseline, so consecutive reps **merge into one detection**. Hence **precision stays high (94.1%) while recall collapses** — it fires correctly, just too few times. The mechanism predicts the damage almost exactly: **59 inter-rep gaps never drop below 20°, against 62 missed reps**; **7 of 9 videos have ≥1 non-releasing gap, 3 in >half their gaps**. `PM_037`: 18/19 gaps never release (median inter-rep minimum **46.1°**, >2× the exit threshold) → 20 reps collapse to **2** detections; `PM_042`/`PM_117b` release every gap and detect near-perfectly (24/25, 14/14). **This validates Stage 4.3 (Lunge)'s own caveat** that squat's borrowed thresholds transfer _"pending Stage 5.4's own empirical check on real lunge reps"_ — the assumption does not hold: a squat always returns to two-legs-straight so its mean falls to baseline; a lunge need not.
  - **Reaches live users, not just training:** the live `LungeLiveSessionPage`/`lungeLiveEstimate.ts` and the backend FSM share this signal and these thresholds, so a real user who does not fully extend between reps will have reps undercounted identically.
  - **The 88-rep feature table is unaffected** — every rep is windowed by the dataset's physio-verified boundaries, never by the FSM.
  - **Not fixed inside this stage, deliberately:** Stage 5.3 defines the FSM comparison as a report, not a gate (squat's own Stage 5.3 recorded its numbers and tuned nothing), and changing the driving signal or thresholds alters already-verified live Phase 4 (Lunge) behaviour — an HY decision. **Spawned as a separate follow-up task**, mirroring how squat's Stage 5.2 spawned its preprocessing follow-up rather than widening scope mid-stage. **→ That follow-up has since been completed (see the cross-cutting entry below): HY chose cycle detection, and front-rep agreement is now 88/88 (100%).**
- [x] **Verification:** `build_features_lunge.py` runs clean; **byte-identical CSV across two runs** (X8 determinism, `md5` = `1a66a9f6…`); Black/isort clean; backend untouched (full suite still **192/192**); `ml/data/lunge_features.csv` and `landmarks_lunge/*.npz` are gitignored (regenerable via `extract_landmarks_lunge.py` → `build_features_lunge.py`), `LUNGE_FEATURE_TABLE.md` committed.
- [ ] **Deliberately not done (out of Stage 5.3 scope):** no feature dropped/kept and no `norm_ref` bake-off on the basis of the sanity stats — that verdict is **Stage 5.4 (Lunge)**'s gate. Per-subject class presence (subject 3 single-class, 11 Poor / 0 Good) is surfaced only; the LOSO/stratified-fallback that handles it is Stage 5.5's job.

### Cross-cutting — Lunge rep detector: threshold FSM → cycle detection (2026-07-17)

Follow-up to Stage 5.3 (Lunge)'s finding #2, spawned rather than fixed mid-stage. **HY's decision: option (d), cycle detection** — chosen after the three options originally proposed were each measured and rejected. Mirrors squat's own "Cross-cutting — Wire real preprocessing into Module B squat pipeline" precedent (a Phase-4-touching fix, evidenced first, decided by HY, then executed as its own unit).

- [x] **Reconciliation first:** confirmed `segment_lunge_frames` drove off `mean_knee_flexion_deg` with `LUNGE_CONFIG`'s enter 30 / exit 20, and that the module's own docstring asserted the very claim the data refutes — _"the mean still rises on descent and falls on return-to-standing — the only thing this phase FSM needs"_. It rises; it does not reliably fall.
- [x] **Corrected an inaccuracy in Stage 5.3's own report before anything else** (factual fix, independent of the chosen option): that report described the mechanism as subjects _"holding a split/staggered stance between reps"_, implying rest. Measured the annotations: **reps are back-to-back, median gap = 1 frame** — a set is _continuous_, and each boundary sits at the **top of a cycle**, not in a rest. The conclusion stood; the explanation was wrong. Corrected in `LUNGE_FEATURE_TABLE.md`, `PHASE5_CHAPTER_DRAFT.md` §11.7, and `task.md`.
- [x] **All three proposed options measured and rejected — none was viable:**
  - **(a) front-knee-only signal:** measured **worse**, not better. Subjects rest with the _front_ knee more flexed than the bilateral mean (`PM_021` cycle tops 37.5° vs 26.0°; `PM_117a` 42.2° vs 25.8°), so it releases less often.
  - **(b) raise** `exit_standing_deg`**:** **arithmetically impossible**. A single global pair needs `exit > 60.0°` (PM_037's worst cycle top) **and** `enter < 14.8°` (PM_042's weakest rep peak) **and** `exit < enter`.
  - **(c) baseline-relative exit:** also fails globally, at every baseline estimator tried (5th/10th/25th percentile, min): PM_037 rests **46.1° above its own baseline** while PM_117a's reps peak only **24.7°** above theirs.
  - **Root cause, now stated precisely:** rest posture and rep depth **overlap across subjects** on any absolute scale, so no fixed angle — absolute or baseline-relative — separates them. Cycle _shape_ does.
- [x] **(d) Cycle detection — the option none of the three named, proposed only because the data pointed at it.** Reps are found as movement cycles (a flexion maximum bracketed by the minima either side), confirmed by a zigzag/swing pass where a running extremum is only accepted once the signal reverses by `cycle_prominence_deg`. Prominence does the noise-rejection job the old hysteresis deadband + refractory window did, in cycle terms rather than absolute-posture terms.
- [x] `backend/app/module_b/lunge/segmentation.py` rewritten: `HysteresisRepFSM` usage replaced by `_confirmed_maxima()` + bounded trough search. **No scipy** (not a backend dep — hand-rolled, ~25 lines, deterministic). `Rep` contract unchanged, so features/rules/persistence are untouched. **Real bug caught in my own port and fixed:** the first version searched for the closing trough to the _end of the stream_ rather than stopping at the next bottom, so it grabbed a distant global minimum and the next rep's start ran backwards past it (the scipy prototype bounded this; I dropped the bound). A second latent bug found via a failing test: `previous_end` didn't advance when a rep was rejected for duration, letting the next rep's start search backwards across it.
- [x] `LungeState` **removed** (STANDING/DESCENDING/BOTTOM/ASCENDING) — it belonged to the per-frame threshold FSM and a cycle detector has no "standing" state. Grepped for callers first: none outside its own test (squat's equivalent is likewise consumed only by its own segmentation + test, never the API or UI), so nothing user-facing regressed. A rep's shape remains recoverable from `Rep.peak_signal_frame_index`.
- [x] `cycle_prominence_deg = 17.5` **[dataset-derived], selected by a swept rule fixed in advance:** the _largest_ prominence that still recovers every side-view rep (stricter = fewer spurious detections, so take the strictest setting costing no recall). Swept 10-30°: 10-17.5° all hold **100%** front recall while precision climbs monotonically 86.5% → 99.4%; recall first drops at 20° (87/88). 17.5° sits mid-plateau, not on a knife edge. **Honest caveat recorded in the config comment:** tuned on the same cohort it is measured against, so 99.4% is in-sample, not a generalisation estimate.
- [x] **Result (real harness, same one-to-one matching as Stage 5.3):** front (trained) reps **50/88 = 56.8% → 88/88 = 100%**; overall **112/174 → 173/174 (99.4% recall, 99.4% precision)**; `PM_037` **2 → 20/20**. Boundary error also improved sharply as a side effect: start median **25 → 7** frames, end median **12 → 7**. The hand-rolled detector reproduces the scipy prototype's numbers exactly, per-video.
- [x] **The feature table is provably unaffected:** `ml/data/lunge_features.csv` is **byte-identical before and after** the detector change (`md5 1a66a9f6…`), confirming the claim that reps are windowed by the dataset's physio-verified boundaries and never by the FSM.
- [x] **Tests rewritten as a deliberate contract change, not bent to pass** (the squat-preprocessing precedent): the old suite asserted enter/exit behaviour that no longer exists. Replaced with prominence-based equivalents, plus `test_continuous_reps_without_returning_to_standing` — the regression guard for the actual bug, **verified to genuinely fail against the old model** (it finds **0** reps on that fixture where the new one finds 4), so it is a real guard rather than a vacuous pass. Also added non-monotonic-timestamp and empty-stream guards. Backend suite **192 → 195**, all green.
- [x] `frontend/src/utils/lunge/lungeLiveEstimate.ts` ported to the same cycle model (X7 config contract updated: `enter_descending_deg`/`exit_standing_deg`/`refractory_s` → `cycle_prominence_deg`; fallback now 17.5). **The live path is the only causal one** — the backend receives the whole buffered set in one POST (`exercise.segment(preprocessed_frames)`), so it is batch and has no lookahead constraint, which is why the offline measurement transfers to it directly. Two deliberate live divergences, documented in-file: a rep is counted at **bottom-confirmation** (as the user rises out of the lunge) rather than at the closing trough, so the final rep of a set isn't stranded uncounted; and `minRepDurationS` acts as a debounce, since trough-to-trough duration isn't known at count time.
- [x] **Live estimator verified against real data, not just typechecked:** exported the 9 videos' real preprocessed mean-knee signals and drove the causal counter over them. It agrees with the backend on **8/9 videos exactly** and totals **174/174 = 100%** vs ground truth (it recovers `PM_117a`'s final rep the batch detector misses — exactly the stranded-last-rep case bottom-confirmation counting was designed for).
- [x] **Gate:** backend suite **195/195**; `npx tsc --noEmit`, `npm run build`, `npm run test` (4/4), ESLint, Prettier all clean; Black/isort clean; `core/router.py` and backend `squat/` untouched.
- [ ] **Deliberately not done:** squat's detector is **unchanged**. It scores 94.9% because a squat genuinely does return to a two-legs-extended stance, so its threshold model fits; converting it for symmetry would alter verified Phase 4 behaviour for no measured gain. The two exercises now use different segmentation paradigms **because the movements differ**, and both `segmentation.py` docstrings say so.

#### Stage 5.4 (Lunge) — Feature-validity sanity **[GATE]**

Mirrors squat's Stage 5.4 — `task.md:1099-1245`.

- [x] Apply squat's Stage 5.4 gate to lunge features — the gate itself had no
  ```
  lunge-specific delta, but three of its four mechanics did (gate feature, CV
  validity, leg identity). See the dated entry below.
  ```

### Phase 5B — Stage 5.4 (Lunge): Feature-validity sanity [GATE] (2026-07-17)

- [x] **GATE: PASS.** `front_knee_flex_peak_deg` separates the classes — **AUC 0.639**
  ```
  (Good median 77.2° vs Poor median 83.8°), 0.139 from the 0.5 no-separation point,
  direction holding in **5/7** voting subjects. Extraction, view filter and windowing are
  not broken, which is what the gate exists to catch. Weaker than squat's 0.837 but
  unambiguous, and **the direction matches squat's** (Poor reps are _deeper_) — the same
  counter-intuitive relationship now found independently in two exercises.
  ```
  - **Gate feature is** `front_knee_flex_peak_deg`**, not** `knee_flex_peak_deg` — the one
    real delta in the gate: a lunge is asymmetric, so no bilateral-mean depth feature
    exists to gate on. The front knee is squat's gate feature's direct correspondent.
  - **Checked per lead-leg cohort too**, since Stage 5.0 found lead-leg confounded with
    subject and a pooled AUC could be a between-cohort offset: it is not — left 0.580 /
    right 0.728, both above 0.5, same direction. New `ml/scripts/check_feature_validity_lunge.py`,
    report `ml/reports/LUNGE_FEATURE_VALIDITY.md`, figures `lunge_feature_validity_boxplots.png`
    (new `grid_5x4` figsize in `plotting.py` — 17 features need 20 slots, not squat's 16)
    and `lunge_feature_correlation_heatmap.png`. Only redundant pair at |r|>=0.90:
    `front_ankle_df_proxy_deg ~ knee_passes_toe_norm` (r=0.95) — not dropped (tree
    ensemble, and dropping changes the vector => schema bump).
- [x] **⚠⚠ Real finding #1 (the big one) — squat's pooled-AUC rule DOES NOT transfer:
  ```
  pooling inverts the truth for 9 of 17 lunge features.** The pre-declared rule returns
  **7 keep / 10 drop**, but several DROPs are pooling artefacts. Worst case
  `back_knee_rom_deg`: pooled AUC **0.564** (scored DROP), yet the direction vote is
  **0/7** — _not one_ voting subject agrees with the pooled direction; every subject shows
  Poor with **higher** back-knee ROM. Subtracting each subject's own median (label-free
  centring) and re-pooling gives a within-subject AUC of **0.860** — from weakest feature
  to strongest. **Textbook Simpson's paradox, mechanism measured not asserted:**
  corr(subject median, subject %Poor) = **−0.505**, and **one subject causes it** — P3 is
  the cohort's only single-class subject (0 Good / 11 Poor) _and_ has the lowest
  `back_knee_rom_deg` of anyone (40.1° vs 42–92°), while every other subject is ~50/50.
  Excluding P3 alone lifts pooled AUC 0.564 → 0.679 (still << 0.860).
  ```
  - **The pre-declared verdicts were deliberately NOT rewritten** — the rule was fixed
    before squat's results were seen; swapping in whichever statistic gives the nicer
    answer is what pre-declaring exists to prevent. Verdicts stand, contradicting evidence
    published beside them, resolution handed to Stage 5.5.
  - **Stage 5.5 MUST train on all 17 features** and treat the DROP column as advisory —
    squat's 5.5 already did this (to avoid LOSO selection bias), so **no feature is
    actually lost to the artefact**. The DROP column is not wired to anything.
- [x] `norm_ref` **bake-off:** `trunk_length` **WINS** (mean cross-subject variance ratio
  ```
  **1.606 vs 2.118**), unanimously on all three normalised features. **Backend config
  changed** `thigh_length` → `trunk_length` in `backend/app/module_b/lunge/config.py`,
  re-tagged `[dataset-derived, Stage 5.4 (Lunge) bake-off]`. Reproduces squat's result on
  an independent exercise. New `ml/scripts/check_norm_ref_lunge.py`, report
  `ml/reports/LUNGE_NORM_REF_BAKEOFF.md`, figure `lunge_norm_ref_variance_comparison.png`.
  ```
  - **Real finding #2 — squat's CV statistic is INVALID for one lunge feature.** Lunge
    normalises **three** features (vs squat's two), and `knee_passes_toe_norm` is
    **signed** (positive = knee past toe = the fault) and genuinely crosses zero: **18/88
    reps negative, one subject's mean at +0.06**. CV = std/mean explodes near a zero mean,
    so a CV verdict there would turn on where the cohort's zero happened to fall. Verdict
    therefore taken on a **variance ratio** (between-subject var of per-subject means /
    mean within-subject var) — scale-invariant like CV, needs no non-zero mean, and
    penalises a reference that cancels between-subject spread by inflating within-subject
    noise. **CV agrees on the two features where it is valid**, so the statistic choice did
    not decide the outcome. Squat never hit this: both its normalised features are unsigned.
  - **Re-ran everything the default touched, as the stage requires.** Backend suite
    **195/195** after one genuine test breakage: `test_knee_passes_toe_sign_flips_with_knee_position`
    left the shoulders at the hip midpoint => zero-length trunk => divide-by-zero under
    `trunk_length`. Fixed the **fixture** (gave the pose a real trunk — the same fix squat's
    `test_module_b_segmentation.py` already carries), not the production guard. Feature
    table regenerated: md5 `1a66a9f6…` → `54f98787ca56aac742ad3c6637b89451`, X8
    determinism re-verified (byte-identical across two runs), gate re-run on the new table
    and still PASS.
- [x] **⚠⚠ Real finding #3 — leg identity SETTLED for lunge (squat could not), and the
  ```
  test that was supposed to settle it failed.** Squat closed this as unresolvable and
  escaped via the swap-invariant **bilateral mean**; lunge has no such escape (every
  feature is front/back split — a swapped mapping transposes all of them).
  ```
  - **The expected test failed and is reported, not dropped.** Predicted that a lunge's
    asymmetry would rescue squat's leg-difference test (`θ_L − θ_R`). It did **not**: mean
    r = **+0.28**, signs mixed, **UNRESOLVED** against a rule fixed in advance
    (|mean r| ≥ 0.5 + consistent signs). Checked it was not a sync artefact — recomputing
    at each video's own offset instead of lag 0 moves r by <0.03. _Why_ it fails is the
    insight: the difference of two angles inherits the worse-measured one's error.
  - **The test that works: foot POSITION**, which occlusion perturbs far less than angle,
    checked against an independent key (the dataset annotates the lead leg; the front foot
    is anterior by definition). Mocap recovers the annotated lead leg **9/9**; MediaPipe
    **9/9**. Both label sets correct ⇒ **mapping CONFIRMED**. The front/back split every
    lunge feature rests on is now verified ground.
- [x] **⚠⚠ Real finding #4 — occlusion is large enough to INVERT the anatomy, and it is
  ```
  _confident_ error.** Mocap says right knee deeper in **9/9** videos; MediaPipe says left
  deeper in **9/9** — a perfect reversal (chance ≈ 4/9). With identity confirmed this
  **cannot** be a swap (it is exactly a swap's signature — which is why identity had to be
  settled first): the far limb is under-read by **18.2°** vs **2.5°** near, a ~15.7°
  differential, while the true L-R difference is a few degrees. **The artefact is bigger
  than the signal.**
  ```
  - **Answers Stage 5.3's deferred far-leg question: "merely plausible."** Far limb tracks
    shape (r=0.824, cf. near 0.713) but mis-states magnitude by 18.2°.
  - **Decomposed by (cohort × limb) vs raw visibility:** error follows **near/far (15.7°
    gap)**, NOT front/back (**0.3°**) — the right knee is bad in _both_ roles. And it is
    **confidently** wrong: where the far limb leads, mean visibility **0.938** (far above
    `MIN_VISIBILITY=0.6`, filter never engages) yet bias **−15.1°**. **No
    confidence-threshold policy can catch this.**
  - New `ml/scripts/check_mocap_agreement_lunge.py` (reuses `module_a/core/evaluation/agreement.py`,
    not forked), report `ml/reports/LUNGE_MOCAP_AGREEMENT.md`, figure
    `lunge_mocap_agreement_bland_altman.png`. Headline `front_knee_flex_peak_deg`:
    **ICC 0.623, bias −10.87°, LoA [−29.57°, 7.84°], r 0.791, n 88**. Offset −3 frames
    (One Euro's own lag) on every video.
- [x] **⚠⚠ Real finding #5 (the one with the furthest reach) — the gate feature carries an
  ```
  8.9° COHORT-DEPENDENT bias, closing Stage 5.2's open question (`task.md:2346`).** _Is the
  lead limb the near or far limb, fixed per subject?_ **YES.** Far limb = right in all 9
  videos (camera artefact, not lead-leg — Stage 5.2); lead leg is fixed per subject ⇒ the
  front leg **is** the occluded limb for right-lead subjects and the clearly-visible one
  for left-lead. Measured: `front_knee_flex_peak_deg` bias **−6.19° (left-lead, front=near)**
  vs **−15.13° (right-lead, front=far)** ⇒ **8.9° systematic offset between two subject
  groups, produced purely by which side faced the lens.** No subject moves differently.
  ```
  - **Upgrades Stage 5.0's leakage warning from hypothesis to measured fact, and sharpens
    it:** the lead-leg confound is **physically encoded in the feature values themselves**,
    so a model can infer the cohort from measurement bias alone. **Excluding** `lead_leg` **from
    the vector (Stage 5.3 did) is necessary but NOT sufficient.** Stage 5.5 must watch for it.
  - **The mocap definitional caveat does not weaken this** — a definitional offset applies to
    both cohorts equally and cannot create a difference between them.
  - **Bounds Stage 5.6 (Lunge)'s ROM banding**: an error differing by 8.9° by lead leg cannot
    be corrected by one global constant — this is the measurement justifying 5.6's existing
    [dataset-derived] instruction, and a reason not to soften it.
- [x] **Answered Stage 5.2's other flagged question: does the far limb dip below
  ```
  `MIN_VISIBILITY=0.6` at rep depth (window means may mask it)?** **YES — the mean did hide
  it, the concern was justified**: **10/88 reps** cross the threshold in their deepest 20% of
  frames (75/1452 at-depth frames), where per-video means bottom out at 0.652.
  **But it is NOT the cause of the bias** — every affected rep is a _left-lead_ subject's
  (far limb = back leg, vis 0.652–0.776), the opposite of the pattern the bias follows, and
  right-lead subjects never dip (0/46) yet still carry −15.1°. The flagged reps are the
  smaller, _honest_ part of the problem; the larger part is invisible to any confidence-based
  defence. New `ml/scripts/check_far_limb_visibility_lunge.py` (measures **raw** visibility —
  preprocessing rewrites it, so asking the preprocessed stream would let the filter grade its
  own homework), report `ml/reports/LUNGE_OCCLUSION_CHECK.md`.
  ```
- [x] `ml/reports/PHASE5_CHAPTER_DRAFT.md` **extended in place** (not forked): §11.9 feature
  ```
  validity + the pooling artefact, §11.10 body-scale normalisation, §11.11 agreement with
  marker-based mocap, §11.12 limitations **23/24/25**; Figures 17–20 continuing the existing
  numbering and `_Figure N._` caption style.
  ```
- [ ] **Deliberately not done — shared preprocessing untouched.** Changing `MIN_VISIBILITY`,
  ```
  the gap-fill width or the release policy would alter Module B behaviour for **squat as well
  as lunge** (`preprocess_world_landmarks` is the single shared implementation, X1) and squat's
  Phase 5 results were verified against current behaviour. This gate establishes the fact; the
  change is a cross-cutting decision for HY.
  ```
- [ ] **Deliberately not done — no feature dropped, no calibration constant applied.** The
  ```
  DROP verdicts are advisory (see finding #1) and the mocap bias is **not** applied as a
  correction: an unknown share of it is definitional (where a "knee centre" is), so
  subtracting it would encode marker-convention differences as pipeline calibration.
  ```

#### Stage 5.5 (Lunge) — Train the Extra Trees classifier

Mirrors squat's Stage 5.5 — `task.md:1246-1369`.

- [x] Apply squat's Stage 5.5 steps to train the lunge classifier. The steps had no delta;
  ```
  **the result does** — see the dated entry below.
  ```

### Phase 5B — Stage 5.5 (Lunge): Train the Extra Trees classifier (2026-07-17)

- [x] **⚠⚠⚠ HEADLINE — DOCUMENTED NEGATIVE RESULT: the lunge classifier trained the plan's
  ```
  way DOES NOT WORK.** Out-of-fold ROC AUC **0.344**, and a **200-shuffle permutation test
  cannot distinguish it from chance (p = 0.657)**. Squat's equivalent scored 0.832 with the
  _same code, same grid, same CV machinery_. `ml/scripts/train_lunge.py`,
  `ml/reports/LUNGE_TRAINING_REPORT.md`.
  ```
  - **It is NOT "predicting backwards", and the report says so explicitly.** An AUC below 0.5
    invites that reading; the permutation null refutes it — null mean **0.487 ± 0.085**,
    range 0.30–0.68, so a sub-0.5 point estimate is well inside what random labels produce.
    Honest statement: **no detectable cross-subject signal**, not inverted signal.
  - **Not a broken pipeline:** in-sample AUC **0.982**. The model fits the training reps
    almost perfectly and carries none of it to a new subject. That gap **is** the confound.
- [x] **⚠⚠ TWO INTERVENTIONS RECOVER REAL SIGNAL — and both attack the confound, not the

  ```
  model** (this is the answer to HY's "research methods to raise AUC"):
  ```

  | strategy                 | n   | AUC       | perm. p   | signal?         |
  | ------------------------ | --- | --------- | --------- | --------------- |
  | `S0_baseline` (the plan) | 88  | 0.344     | 0.657     | **no — chance** |
  | `S1_session_centred`     | 88  | **0.670** | **0.005** | **YES**         |
  | `S3_cohort_centred`      | 88  | 0.355     | 0.423     | no — chance     |
  | `S2_lead_near_only`      | 42  | **0.696** | **0.005** | **YES**         |
  - **S2 empirically vindicates HY's turn-around protocol.** It is the train/serve match the
    protocol produces (deployment only ever sees lead-near reps) **and the only subset where
    TRUE LOSO is possible** (subjects 2/6/7/9 all carry both classes; the lead-far cohort holds
    the single-class subject 3). Per-subject LOSO folds: 0.960 / 1.000 / 0.760 / 0.750.
  - **S3's failure is itself the finding:** correcting only the _cohort-level_ 8.9° offset
    recovers **nothing** (p=0.423), while subtracting each _subject's own_ median works. So the
    between-subject variation burying the signal is **mostly NOT the camera bias** — it is
    individual build/movement differences the artefact only adds to. Correcting the artefact
    alone is insufficient; that is why turn-around is a **capture** fix, not a modelling one.
  - **S1 cannot ship despite its score, for a reason no metric shows:** centring redefines the
    question from _"is this rep good?"_ to _"is this rep better than your other reps?"_ — a
    uniformly-poor set would centre to look average. Safety-relevant, not a trade-off.
  - **"Subtract the measured 8.9° bias" was ruled out on principle, not score:** the bias is an
    OptiTrack measurement and **X3 forbids mocap as a model input**. S3 is the mocap-free
    equivalent.

- [x] **⚠ Real bug found in squat's assertion, corrected here rather than deleted.**
  ```
  `train_squat.py` asserts calibration preserves AUC exactly, on the premise _"a sigmoid
  cannot reorder predictions"_. **That premise is false.** Platt fits `1/(1+exp(a·f+b))` and
  nothing constrains the sign of `a`; when inner folds show the score anti-correlating with the
  label, the sigmoid correctly fits a **positive** `a`, becomes monotone _decreasing_, and
  exactly reverses the ranking (AUC → 1−AUC). **It fired on lunge fold 3** (Platt a=**+2.70**,
  0.554→0.446, sum exactly 1.000; inner OOF AUC on train subjects **0.368**). Squat never hit
  it because its signal is consistent. Assertion corrected to the true invariant: a monotone
  map preserves **or exactly reverses**. Flips are now recorded per fold, not suppressed —
  2 of 5 baseline folds flip. **Squat's script deliberately NOT touched** (out of scope, its
  assertion never fires on its data).
  ```
- [x] **⚠ Deployment-critical check added:** `final_model_platt_slope()`**.** The fold-level flips
  ```
  prove the sign is not guaranteed on this cohort, so an **inverted exported model** is a real
  risk — it would report P(Good) _rising_ as technique worsened and nothing downstream would
  notice, because the probabilities would still look well-formed. Verified: the exported
  model's slope is **−1.3057 (normal orientation)**. **Stage 5.8 MUST re-run this check.**
  ```
- [x] **CV: `StratifiedGroupKFold(5, groups=person_id)` — the plan's fallback, data-triggered
  ```
  not chosen.** `_choose_cv()` detects it: **subject 3 is single-class (0 Good / 11 Poor)**, so
  LOSO would hand it a single-class test fold. Write-ups must say **subject-wise 5-fold, not
  LOSO**. Per-fold AUC: 0.700 / 0.306 / 0.446 / 0.640 / 0.214.
  ```
- [x] **Grid is a plateau, not a peak:** across all **180** combinations the mean inner-CV AUC
  ```
  spans only **0.0773** while the median fold std is **0.0679** — the spread between
  combinations is **smaller than the noise on each one**; **95/180** sit within 1 std of the
  best. Best params `{max_depth: None, min_samples_leaf: 5, min_samples_split: 10,
  ```

n_estimators: 100}`. Full` cv_results_`table (all 180, losers kept) in the report.` best_score_` deliberately never quoted as a generalisation estimate.

- [x] **Calibration = sigmoid, not isotonic** (49 Poor reps / 8 subjects — N does not allow
  ```
  isotonic). Brier 0.291 → 0.298. Figures: `lunge_hyperparameter_search_results.png`,
  `lunge_calibration_reliability_curve.png` (Wilson intervals, not Wald — Wald collapses to
  zero width at p=0/1), and **new `lunge_roc_curves.png`** — added because **HY could not see
  an AUC chart anywhere**; the project had per-_feature_ AUC tables but no model ROC. S0/S3 sit
  **below** the diagonal, S1/S2 clearly above.
  ```
- [x] **All 17 features trained on; Stage 5.4's DROP verdicts NOT executed** — its own caveat
  ```
  (verdicts computed on all 88 reps incl. held-out subjects → selection bias) plus its finding
  that pooling inverts 9/17. Importances recomputed by _calling_ `analyse_feature()`, never
  transcribed.
  ```
- [ ] **⚠ DECISION REQUIRED BEFORE STAGE 5.8 — HY's call, deliberately not taken here.**
  ```
  Stage 5.8 is scheduled to export `S0_baseline`, i.e. **a chance-level classifier**. The fusion
  would still emit plausible Good/Fair/Poor verdicts — a merely-uninformative model is invisible
  downstream. Options: **(1)** ship S0 announced (but "trained" ≠ Phase 4's announced `stub-0`);
  **(2)** ship **S2 lead-near** and let the turn-around protocol enforce its input distribution
  (real signal, but 4 subjects / 42 reps); **(3)** keep the placeholder and document the
  negative result, as Stage 5.10 does for squat's EC3D finding.
  ```
- [ ] **Deliberately not done:** no artifact exported (Stage 5.8's job); `build_final_model()`
  ```
  is the entry point it will call. No feature dropped. No bias correction applied.
  ```

#### Stage 5.6 (Lunge) — Fair threshold + fusion weight sweep

Mirrors squat's Stage 5.6 — `task.md:1370-1462`.

- [ ] **ROM band edges are dataset-derived, not clinical.** The front-knee ≈90° cue is a **coaching convention, not a normative table** — no McBride-equivalent exists for the bodyweight lunge (open question, see Q6). So **calibrate the band edges from REHAB24-6's correct-rep distribution** and tag them **[dataset-derived]**. Do **not** assert 90° as a sourced cutoff.
- [ ] Apply squat's Stage 5.6 sweep to lunge, swapping in the delta above.

#### Stage 5.7 (Lunge) — Evaluation

Mirrors squat's Stage 5.7 — `task.md:1463-1598`.

- [ ] **Generalisation must be stated modestly.** REHAB24-6 is the **only public labelled lunge dataset**; there is no second source. Claims lean on subject-wise CV + EC3D (4 subjects) and must be worded accordingly.
- [ ] Apply squat's Stage 5.7 evaluation to lunge, swapping in the delta above.

#### Stage 5.8 (Lunge) — Export + backend integration

Mirrors squat's Stage 5.8 — `task.md:1599-1692`.

- [ ] Apply squat's Stage 5.8 steps to export and wire the lunge model — no lunge-specific delta.

#### Stage 5.9 (Lunge) — EC3D external validation

Mirrors squat's Stage 5.9 — `task.md:1693-1842`.

- [ ] `**knee_passes_toe**` needs a toe/foot-tip joint. If EC3D lacks one, approximate from ankle **or drop it** — and say which (same open question as Stage 4.2 / Stage 5.2).
- [ ] Generalisation wording applies here too: EC3D is only 4 subjects, so external-validation claims must be worded modestly.
- [ ] Apply squat's Stage 5.9 steps to lunge EC3D validation, swapping in the deltas above.

**Deliverable:** Module B works end-to-end for lunge with a trained, LOSO-evaluated model, using the same registry with zero router changes.

---

## Phase 6: After-Set Report and External LLM API

**Goal:** readable after-set coaching text that **never** changes the grade, and a system that works perfectly when the API is down.

**Build order is deliberate: the fallback is built _first_.** If the template layer is built last it will be an afterthought; if it's built first, the LLM is provably optional polish.

### Stage 6.1 — Structured feedback + error-tag taxonomy

- [x] `backend/app/module_b/squat/tags.py` — the taxonomy, **reconciled to 5 tags** (HY, 2026-07-19). The original 7-row table predated Stages 5.11/5.12; `asymmetry` and `feet_too_wide` are **dropped** (invalid from a single side view — see below) and the `Signal` column is corrected (`w_rule=0`, so no tag is "rule + ML" — the ML sets the band, gates override it, soft tags only explain):

| Tag                      | Observable from              | User-facing message                                             | Severity | Kind / source         |
| ------------------------ | ---------------------------- | --------------------------------------------------------------- | -------- | --------------------- |
| `insufficient_depth`     | `knee_flex_peak_deg` [gate]  | "Didn't reach enough depth — aim for closer to parallel."       | High     | fault gate (rule)     |
| `excessive_forward_lean` | `trunk_lean_peak_deg` [gate] | "Leaning too far forward — keep your chest more upright."       | High     | fault gate (rule)     |
| `heel_lift`              | `heel_rise_peak_norm` [gate] | "Heels lifting off the floor — keep your weight through heels." | High     | fault gate (rule)     |
| `inconsistent_tempo`     | tempo CV ≥ 0.25 (≥2 reps)    | "Aim for a steadier pace across your reps."                     | Low      | soft (rule) — new 6.1 |
| `low_confidence`         | fusion capture/confidence    | (i18n `moduleB.tag_low_confidence`)                             | Medium   | system                |

- [x] The 3 fault-gate tags already shipped live in Stage 5.12; `inconsistent_tempo` is added at 6.1 (Low severity, never overrides the band — only the gates can). System tags (`low_confidence`, `low_capture_quality`, `retry_camera_placement`) carried through from fusion. `tags.py` is the single source of truth for each tag's severity/source/kind/i18n key; gate messages stay single-sourced in `squat/config.py`.
- [x] `**knee_valgus`, `asymmetry`, `feet_too_wide` are NOT in the taxonomy.** Recorded with reasons in `docs/module_b_limitations.md`: valgus = frontal-plane (ill-posed side-on); `asymmetry` = L/R indistinguishable from one side view (Phase 5 finding 4, leg-diff vs mocap r≈−0.05); `feet_too_wide` = stance width ill-posed in profile (in-sample AUC 0.37, inverts on EC3D). Mirrors the WBLT/valgus precedent of refusing to measure what one camera cannot.
- [x] `core/feedback.py` — `build_structured_feedback(summary) -> StructuredFeedback`: band, S_final, three sub-scores, confidence, ranked tags (severity → tag-name tiebreak; per-tag magnitude is not persisted so severity is the ranking key), rep count. **Pure and deterministic** (X8) — consumes the `crud.result_summary` dict, never re-derives a grade.

### Phase 6 — Stage 6.1: Structured feedback + error-tag taxonomy (2026-07-19)

- [x] Built `backend/app/module_b/squat/tags.py` (`TagSpec`, `SQUAT_TAG_TAXONOMY`, `build_squat_error_tags`) — the reconciled 5-tag taxonomy and single source of truth for tag metadata. Trimmed from 7 to 5 per HY's decision; `asymmetry` + `feet_too_wide` documented as side-view limitations.
- [x] Added `backend/app/module_b/core/feedback.py` (`build_structured_feedback` + `StructuredFeedback`/`FeedbackTag`/`FeedbackSubScore`) — pure/deterministic, severity-ranked.
- [x] `inconsistent_tempo` emission wired: `squat/rules.py` `tempo_subscore` now attaches `metrics={"cv": cv}` (report-only, also persisted); the tag fires at CV ≥ `moderate_consistency_cv_max` (0.25) and only with ≥2 reps — CV reused, never recomputed.
- [x] Refactored the router: `SquatExercise.build_error_tags` (replaces the old `NotImplementedError` `error_tags()` stub) delegates to the taxonomy; `core/router.py` `_build_error_tags` prefers the plugin's builder and falls back to the generic `_system_error_tags`/`_fault_gate_tags` (kept for future gate-only exercises + their unit tests). Base `ModuleBExercise` gained a `build_error_tags` hook (default None) and dropped the dead abstract `error_tags`.
- [x] `docs/module_b_limitations.md` created (valgus + the two dropped tags).
- [x] Verified: backend suite **192/192** green (incl. 13 new tag/feedback tests); Black + isort clean.
- [x] Deferred to 6.2/6.5: i18n key `moduleB.tag_inconsistent_tempo` and the report rendering (6.2 owns i18n, 6.5 owns display) — i18n key done at 6.2 below; display still deferred to 6.5.

### Stage 6.2 — Template fallback _(built first, on purpose)_ (2026-07-19)

- [x] `backend/app/module_b/core/feedback_templates.py` — `compose_template(structured) -> str`, deterministic composition: `"Grade: {band}. {top_tag_message}. {second_tag_message}"`. Messages come **straight from** `tags.py`**'s** `TagSpec.message` (the taxonomy built at 6.1), so the fallback can never invent a claim and can never change the grade — pure function of already-persisted data, no network/randomness/config. Squat's stored `"Poor"` band is relabelled `"Needs Improvement"` in the composed text, matching the Stage 5.11 UI relabel exactly (text and displayed grade never disagree).
- [x] Added English fallback `message=` to the 3 system TagSpecs in `squat/tags.py` (`low_confidence`/`low_capture_quality`/`retry_camera_placement`), matching `en.ts`'s wording — same deliberate-duplication precedent as the Stage 5.12 fault-gate messages, since the backend template composer has no access to the frontend's i18n bundle.
- [x] i18n: added `moduleB.tag_inconsistent_tempo` to `en.ts`/`zh.ts`/`ms.ts` (en defines the `Dict` type; zh/ms match). Needed now because 6.1 already emits this tag live and Report.tsx's existing generic tag renderer (`t("moduleB.tag_" + tag.tag)`) would otherwise show the raw code.
- [x] **Gate met:** `test_module_b_feedback_templates.py`'s `TemplateGateTests` composes a full realistic squat report (system tag + fault-gate tag + soft tempo tag) end-to-end with **zero LLM/API-client code in existence** — proven before Stage 6.4 is even started, not just before it runs.
- [x] Verified: backend suite **200/200** green (8 new tests); Black + isort clean; frontend `tsc --noEmit` clean.
- [ ] Frontend report rendering of the composed text is Stage 6.5's job (persist + display), not this stage's.

### Stage 6.3 — Safety filter

- [x] `backend/app/core/safety_phrases.py` — `FORBIDDEN_PHRASES` **promoted out of the test file** into importable app code (2026-07-19); `test_frontend_disclaimers.py` now imports it instead of forking its own copy — **one list, shared**.
- [x] `backend/app/module_b/core/feedback_safety.py` — `check_llm_feedback(candidate, structured) -> SafetyCheckResult`, applied to LLM output **before** it is stored or shown:
  - [x] Reject any candidate containing a `FORBIDDEN_PHRASES` match (shared list above).
  - [x] **Grade-integrity check:** band contradiction (`_contradicts_band`, aware of the Stage 5.11 "Needs Improvement" relabel so it isn't a false positive) and score contradiction (`_contradicts_score`, matches `"X/10"`/`"X out of 10"` patterns, ±0.05 tolerance). Mismatch → `accepted=False`, caller falls back to `compose_template`. (X5)
  - [x] Reject output naming a _known-taxonomy_ tag (`squat/tags.py`'s `SQUAT_TAG_TAXONOMY`) that isn't in the structured input's tags — scoped to the closed 5-tag taxonomy, not open-ended hallucination detection.
  - [x] Length cap: `MAX_REWRITE_LENGTH = 600` chars; empty/blank candidates also rejected.
- [x] **Tests** (`test_module_b_feedback_safety.py`, 10 tests): `test_adversarial_response_that_changes_the_grade_is_rejected` — a candidate falsely claiming "Good" when the true band is "Poor" is rejected (`grade_mismatch_band`), and the fallback (`compose_template`) is asserted to show the true grade and omit the false claim. Plus score-mismatch, invented-tag, forbidden-phrase, length-cap, and false-positive-avoidance cases (relabelled band text, a legitimately-flagged tag mentioned by name).
- [x] Verified: backend suite **210/210** green; Black + isort clean.

### Stage 6.4 — Groq adapter (2026-07-19)

- [x] `backend/app/module_b/core/llm_client.py` — provider-agnostic `LlmClient` `Protocol` + `GroqClient` (OpenAI-compatible chat-completions API via `httpx`). Model id corrected from the plan's `llama-3.3-70b` shorthand to the real production id `llama-3.3-70b-versatile` (see Q7 resolution below). `groq_api_key` + `feedback_llm_enabled` (default **False**) added to `core/config.py`; `.env.example` updated with both, key **never** committed (verified `backend/.env` stays gitignored + untracked).
- [x] System prompt: _rewrite only; add no medical claims; do not change the grade, band, or score; do not introduce a fault/tag not in the input_. Payload (`_chat_payload`) carries only `band`/`score`/`confidence`/`rep_count`/`tags` — never raw video, never health records (`StructuredFeedback` never carries frames in the first place). Verified by `PayloadContentTests`.
- [x] **After-set only; no separate live/per-frame HTTP endpoint exists in this backend at all** (MediaPipe runs client-side, rules.md #8) — `GroqClient` is reachable only from `core/router.py`'s `_build_and_save_feedback`, itself only called from `POST /analyze` after the set is fully scored. **Test:** `LiveLoopMakesNoLlmCallTests` patches `httpx.post` to raise if called and runs the real pre-analyze pipeline (`analyse_frames` — quality/preprocessing/segmentation/features/rules/fusion/gates) against a real corpus fixture; it completes without the patched call ever firing.
- [x] Timeout (8s) + retry-once, but **only on a 429** (other 4xx/5xx won't self-resolve, so they fail fast instead of doubling latency) — **falls back to the template on any error/timeout/429/empty-response/safety-rejection**, wired in `_build_and_save_feedback`: template is always built first (Stage 6.2), the LLM only overwrites `rewritten_feedback`/`feedback_source` if `check_llm_feedback` (Stage 6.3) accepts it.
- [x] **Re-verified Groq's free-tier limits and model name at build time** (`docs/groq_model_verification.md`, retrieved 2026-07-19 from `console.groq.com/docs/{models,rate-limits}`): `llama-3.3-70b-versatile`, free tier 30 RPM / 1,000 RPD / 12,000 TPM / 100,000 TPD. **Q7 resolved.**
- [x] **Deployment note for Phase 8 (Q8, still open):** Cloud Run → Groq is an outbound call; `feedback_llm_enabled` defaults False so this is a config flip, not a code change, whenever Phase 8 decides. Not decided here.
- [x] **Tests:** `test_module_b_llm_client.py` (7 tests) — success, timeout-retries-once, 429-retries-once, non-429-does-not-retry, empty-response-is-failure, payload-content, live-loop-never-calls-network.
- [x] Verified: backend suite **225/225** green; Black + isort clean; `httpx>=0.27.0` added to `requirements.txt` (only new backend dependency this stage needed).
- [x] **Live-verified against the real Groq API**, not mocked: ran a real squat analyze with `feedback_llm_enabled=true` and the user's own `GROQ_API_KEY` (from `backend/.env`, never touched/logged) against a scratch server; DB row and API response both showed `feedback_source="llm"`, `provider="groq"`, `model_version="llama-3.3-70b-versatile"`, a real rewritten paragraph that passed Stage 6.3's grade-integrity check. **Browser-verified**: the report's Coaching feedback panel rendered the "AI-REWRITTEN" label (distinct from "AUTOMATIC SUMMARY" in the LLM-disabled case), no console errors, screenshot taken.

**Phase 6 complete.** All five stages (6.1–6.5) shipped, tested, and live-verified end-to-end both with the LLM disabled (the required gate) and enabled.

### Module A coaching-panel label fix (2026-07-19, out-of-phase)

- [x] **Confirmed against the proposal (**`PS_22089262.pdf`**) that the LLM/Transformer rewriting layer is scoped to Module B only** — Table 7 ("Libraries and Tools") marks every shared component "Used in: A and B" but the Rewriting layer row "Used in: B" only; §3.4.2.6 places it right after Module B's fusion equation; §3.4.1 (Module A) never mentions it. Phase 6 as built (squat/Module B only) is correctly scoped — **no LLM added to Module A**, by design, not by omission.
- [x] Found and fixed a real, separate defect exposed by this review: Module A's `Report.tsx` coaching panel (static `report.coachingBody` text, unchanged since before Phase 6) was labelled `common.ai` ("AI") despite never being LLM-generated — misleading now that Module B's genuinely-labelled panel (`feedback_source`-driven "Automatic summary"/"AI-rewritten") sits right next to it in the same app. Relabelled to a new, honest `report.coachingTipLabel` ("General tip" / en, "通用提示" / zh, "Petua umum" / ms) — `common.ai` itself untouched (still used by `Landing.tsx`'s legitimate "coming soon" badge).
- [x] **Found and fixed a related test-isolation bug** while re-verifying: `test_module_b_feedback_persistence.py`'s `BuildAndSaveFeedbackTests` read the real process-global `settings` object, so it silently depended on the developer's local `backend/.env` — once `FEEDBACK_LLM_ENABLED=true` was set for manual Groq testing, this test started making a live network call and failing its "LLM never attempted" assertions. Fixed by patching `feedback_llm_enabled=False` in `setUp` so the template-only path is tested deterministically regardless of local `.env` state.
- [x] Verified: backend suite **225/225** green; frontend `tsc --noEmit` + Prettier clean; live-browser-verified against the user's own real SLS session (`get_page_text` confirmed "GENERAL TIP" renders in place of "AI").

### Stage 6.5 — Persist + display

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)): keep `feedback_source: "llm" | "template"` + provider/`model_version`, **and add** `llm_attempted: bool` so the three-state distinction survives — `source="template"` + `attempted=true` means "tried the LLM, output was rejected by the safety filter (Stage 6.3), fell back"; `attempted=false` means "never called (config-disabled, or after-set-only gate not yet reached)." This is strictly more informative than the architecture doc's `llm_used BOOLEAN`, which collapses those two cases. Drop `safety_disclaimer` as stored free text — the disclaimer the user sees always comes from the current i18n render (rules.md #19), so storing a duplicate copy of it per row is redundant. Store `**disclaimer_version`** instead (not the string): a small versioned id bumped whenever the disclaimer copy changes, giving audit-grade traceability ("this session was shown disclaimer v2") without duplicating text that already lives in i18n.

- [x] **Migration** `20260719_0010` (`backend/alembic/versions/`) reshapes `feedback_texts`: drops `llm_used`/`safety_disclaimer`, adds `feedback_source` (default `'template'`), `llm_attempted` (default `false`), `provider`, `model_version`, `disclaimer_version`, and a `uq_feedback_texts_session_id` unique constraint (mirrors `module_b_results`' one-row-per-session shape, since `crud.save_feedback` upserts by `session_id`). Backfills existing rows from `llm_used`. `FeedbackText` model (`app/db/models.py`) updated to match. **Live-verified**: ran `upgrade head` / `downgrade -1` / `upgrade head` against real `fyp_postgres`, confirmed the resulting schema column-by-column via `psql \d`, both directions round-trip cleanly.
- [x] Store **both** the structured feedback and the rewritten text, plus `feedback_source`, `llm_attempted`, `provider`, `model_version`, `disclaimer_version` — `crud.FeedbackWrite`/`save_feedback`/`get_feedback_by_session`/`feedback_summary` (`app/module_b/core/crud.py`), wired into the generic analyze flow via `core/router.py`'s `_build_and_save_feedback` (composes Stage 6.2's template from the just-built result; no LLM call yet — that's Stage 6.4). The read endpoint (`GET /results/{session_id}`) reads the stored feedback row verbatim, same "never recompute a historical grade" contract as the rest of that endpoint. `ModuleBResultResponse` gained a `feedback: ModuleBFeedbackResponse | None` field.
- [x] `Report.tsx` — Module B's tag-only panel became a two-panel `dash-grid-2` (coaching feedback + error tags), mirroring Module A's existing layout exactly (same `panel`/`feedback-box`/`fb-label` CSS, zero new styles). Surfaces `feedback_source` honestly via new i18n keys `report.feedbackSourceTemplate`/`feedbackSourceLlm`/`feedbackUnavailable` (en/zh/ms). `moduleBService.ts` gained the `ModuleBFeedback` type.
- [x] **Tests:** `test_module_b_feedback_persistence.py` — `test_never_mutates_the_result_summarys_grade` (grade byte-identical before/after feedback composition, X5); `ThreeStateFeedbackSourceTests` covers all three states (`llm_attempted=false`; `feedback_source="template"` + `llm_attempted=true`, i.e. tried-and-rejected; `feedback_source="llm"` + `llm_attempted=true`, i.e. tried-and-used) at the persistence layer, since Stage 6.4's LLM client doesn't exist yet to drive the middle case end-to-end. Plus `test_module_b_persistence.py`'s `FeedbackPersistenceTests`.
- [x] **Verified live end-to-end**, not just unit-tested: real `fyp_postgres` + real running backend, curl register→session/start→module-b/analyze with the real `good_moderate_depth_1` replay fixture. Response, DB row (`feedback_texts` + `module_b_error_tags` via direct SQL), and the `GET /results/{id}` readback all agreed byte-for-byte: band `Poor` ("Needs Improvement"), tag `insufficient_depth`, feedback text `"Grade: Needs Improvement. Didn't reach enough depth — aim for closer to parallel."`, `feedback_source="template"`, `llm_attempted=false`, `disclaimer_version="v1"`. **Browser-verified**: logged into the running frontend, opened this session's report, confirmed the Coaching feedback panel renders with the "AUTOMATIC SUMMARY" label and the exact composed text, no console errors, screenshot taken.
- [x] Backend suite **218/218** green; Black + isort clean; frontend `tsc --noEmit` and Prettier clean.

**Deliverable:** User receives readable after-set report; system still works even if LLM API fails. **Met** — the report is fully populated with the LLM disabled (Stage 6.4 not yet built), proving the fallback truly is optional polish.

---

## Phase 7: Dashboard and Progress Tracking

**Goal:** kill `dash.placeholderScoring` for **every** exercise and make multi-session progress real.

**Context:** this is pre-existing cross-cutting tech debt, flagged three separate times in this document (SLS Stage 6, WBLT Stage 6, Phase 3 checklist) and deliberately deferred each time because a one-off per-exercise chart would have been inconsistent. Phase 7 is its home. It is **one charting API either way** — doing Module B only would repeat the same mistake.

### Stage 7.0 — Trend API

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)): follow the architecture doc's §14.8 endpoint names — `GET /api/dashboard/trends` (plural) and `GET /api/dashboard/error-tags` as two separate endpoints, not the single parameterised `trend` endpoint originally drafted here. **Both must return their data keyed by** `exercise_type` (e.g. `{"sts": {...}, "sls": {...}, "wblt": {...}, "squat": {...}}`), not require a separate call per exercise — this is what actually satisfies the Locked Assumption that "Phase 7 fixes the trend/band panels for all exercises" in one dashboard load, and lets the frontend render every panel from one response instead of fan-out fetching.

- [x] `backend/app/dashboard/router.py` — `GET /api/dashboard/summary` + `GET /api/dashboard/trends?from=&to=` (data keyed by `exercise_type`) + `GET /api/dashboard/error-tags?from=&to=` (data keyed by `exercise_type`, only present for Module B exercise types — Module A has warning tags, not error tags, per Stage 7.1's distinction).
- [x] Built on the **exercise-agnostic** `sessions.score` / `sessions.band` columns wherever possible (`Dashboard.tsx` and `SessionHistory.tsx` already read only these — confirmed in Phase 3E). Exercise-specific detail comes from the per-exercise endpoints.
- [x] **Apply the MDC-suppression principle beyond WBLT.** WBLT already suppresses changes below the published MDC (Powden et al. 2015) so measurement noise never reads as improvement. For exercises **without** a published MDC, do **not** invent one — instead present the trend without a "meaningful change" claim, or derive a pilot repeatability estimate from the replay corpus and label it **[dataset-derived]**. **Never assert a clinical MDC that doesn't exist.**

### Phase 7 — Stage 7.0: Trend & error-tag APIs (2026-07-19)

- [x] Built on the **existing** router `backend/app/api/dashboard_routes.py` (already registered in `main.py`), **not** the checklist's speculative `backend/app/dashboard/router.py` path — that file/package never existed; creating it would have split the dashboard router in two. Path deviation noted deliberately.
- [x] `GET /api/dashboard/trends?from=&to=` and `GET /api/dashboard/error-tags?from=&to=` now return real data **keyed by `exercise_type`** (`dict[str, ExerciseTrend]` / `dict[str, list[DashboardErrorTag]]`), replacing the two hard `[]` stubs. `GET /api/dashboard/summary` extended with a per-exercise `latest` map (`dict[str, ExerciseLatest]`) while keeping the old top-level `latest_score`/`latest_band` for back-compat with the current `Dashboard.tsx` tiles.
- [x] **Clean separation** per rules 15/16: pure, DB-free aggregation builders live in new `backend/app/api/dashboard_service.py` (`build_latest`, `build_trends`, `build_error_tags`, `module_b_types`); the router only fetches (one query per endpoint, `selectinload` of `module_b_result` / `module_b_error_tags`) and delegates. This is what makes the grouping unit-testable in the project's existing fake-object style.
- [x] **Module B vs Module A distinction** implemented by presence of `module_b_result`: only those exercise types appear in `/error-tags` (a Module B type with 0 tags is present with an empty list; Module A types are **absent**, so the frontend can tell "no tags this period" from "not a tagging exercise"), and `confidence` on trend points is populated only for Module B (`None` for Module A). Error tags read the DB column `module_b_error_tags.tag` and expose it as `tag_code` to preserve the existing `DashboardErrorTag` schema + frontend contract; ranked most-frequent-first for the bar chart.
- [x] **MDC discipline — correction to the plan (flagged to HY, not silently patched):** the plan literally said WBLT's score trend would be `mdc_source="published"`. That is wrong: WBLT's published MDC (`distance_mdc_cm=1.5`, `angle_mdc_deg=4.6`) is on raw distance/angle in cm/deg, **not** on the 0-10 composite `score` the dashboard plots. No published MDC exists on the 0-10 score for **any** exercise, so `ExerciseTrend.mdc_source` is `"none"` (and `mdc=None`) for all — asserting otherwise would be exactly the fabricated-clinical-threshold error task.md:3165 forbids. WBLT's real MDC stays where it belongs (per-session distance/angle in `Report.tsx` + Stage 7.2). The field is kept explicit so the UI renders an honest "no meaningful-change threshold" caption uniformly.
- [x] Schema changes in `backend/app/db/schemas.py`: added `ExerciseLatest`, `TrendPoint`, `ExerciseTrend`; removed the now-unused flat `DashboardTrendPoint` (grep-confirmed only the replaced stub referenced it); kept/reused `DashboardErrorTag`.
- [x] **Verified:** 10 new unit tests in `backend/tests/test_dashboard.py` (empty account → `{}`; Module A trend present + error-tags key absent; Module B confidence populated + tags grouped/counted/ranked; oldest-first ordering; `mdc_source=="none"` for WBLT and squat) — all pass. Full backend suite **235/235 green**. `from app.main import app` imports clean with 3 `/api/dashboard` routes registered (FastAPI validates the new `response_model` shapes at registration). Files auto-formatted by the repo's PostToolUse hook (Black/isort not present in `.venv`).
- [ ] **Deferred to Stage 7.4 (by the approved plan's execution order):** live end-to-end check hitting the endpoints with a multi-session seeded account. Code-level verification (unit + import + response_model) is complete; the with-data live curl/screenshot waits on the seed script.

### Stage 7.1 — Dashboard panels

- [x] **Recent sessions** — already partly present; wire to the real API.
- [x] **Score trend chart** — per exercise, over time. Removes `dash.placeholderScoring`.
- [x] **Band distribution** — Good/Fair/Poor counts.
- [x] **Common error tags** — Module B only (Module A has warning tags, not error tags — don't conflate the two vocabularies in one panel).
- [ ] **Capture-quality trend** — `Q` over sessions. Directly feeds the evaluation question: _do users improve camera placement after being prompted?_ **Deferred to Stage 7.1b (Progress page)** per the approved `docs/phase7_plan.md` split — see note below.
- [ ] **Confidence trend** — Module B only; feeds the low-confidence-frame robustness metric. **Deferred to Stage 7.1b** — Dashboard ships an account-wide _aggregate_ confidence percentage tile instead of a trend-over-time chart; the actual trend line belongs on the per-exercise Progress deep-dive, not the multi-exercise overview.
- [x] Delete the `dash.placeholderScoring` i18n key (en/zh/ms) once nothing references it. **Grep for callers before deleting** — the house rule.

### Phase 7 — Stage 7.1: Dashboard panels (2026-07-19)

- [x] **Scope note (approved deviation, `docs/phase7_plan.md`):** this task.md checklist lists 6 panels under one "Stage 7.1"; the approved plan splits them across a Dashboard _overview_ (this stage) and a new Progress _deep-dive_ page (Stage 7.1b, next). Rationale: the Locked Assumption requires the dashboard to show **every** exercise the account has done — a full-detail per-exercise trend chart (with capture-quality and confidence sub-trends) doesn't fit a multi-exercise "at a glance" overview without becoming unreadable once an account has 3-4 exercise types. So this stage ships: real recent-sessions, real per-exercise score-trend small multiples, real account-wide band distribution, real ranked error tags, and an account-wide aggregate confidence tile. The two genuinely time-series panels (capture-quality trend, confidence trend) move to Stage 7.1b where they're scoped to one exercise at a time with a date-range control — that is where a trend line is actually legible and useful, not a duplication of effort.
- [x] **Recharts installed** (`frontend/package.json` — `recharts: ^3.9.2`, 36 packages, zero peer-dependency conflicts with React 19). Chosen per HY's decision over hand-rolled SVG.
- [x] **New shared chart toolkit** (`frontend/src/components/charts/`), reused by Dashboard now and intended for Progress (7.1b) next — "one charting API" per the Phase 7 goal, not per-exercise one-offs:
  - `dashboardChartUtils.ts` — `SCORE_BAND_THRESHOLDS` (Poor 0-4 / Fair 4-7 / Good 7-10, the actual Table 6 cutoffs read from `app/module_a/core/config.py` + `app/module_b/core/config.py`, confirmed identical across both modules), `bandKey`, `severityClass` (`module_b_error_tags.severity` is `"high"/"medium"/"low"`; CSS is `.sev.high/.med/.low` — mapped, not conflated), `humanizeExerciseType`, `formatShortDate`, `averageScore`.
  - `ScoreTrendChart.tsx` — Recharts `AreaChart`, `variant="mini"` (sparkline, no axes, used by `MiniTrendCard` below) or `variant="full"` (axes + Good/Fair/Poor `ReferenceArea` zones + custom tooltip, built now, reserved for Stage 7.1b's per-exercise deep dive — same component, not a duplicate).
  - `MiniTrendCard.tsx` — one small-multiple card per exercise: name, latest band pill, mini sparkline, latest score, session-over-session delta badge (reuses the existing `.trend.up/.down` CSS, previously dead code showing only static "—"/"DB" text).
  - `BandDistributionBar.tsx` — single 100%-stacked bar (not 3 separate progress bars) + legend with real counts; deliberately plain CSS flex-segments rather than a Recharts chart (a native `title` tooltip and 3 divs is simpler and equally informative than fighting Recharts' axis-hiding for a single categorical bar — avoided over-engineering per rule 20).
  - `QualitySparkline.tsx` — built now (capture-quality 0-1 over time, Recharts `AreaChart`), not yet wired into any page; reserved for Stage 7.1b's capture-quality-trend panel.
  - All chart colors are passed as literal `"var(--chart-line)"` / `"var(--good)"` etc. **strings**, not resolved via `getComputedStyle` — SVG presentation attributes accept CSS custom properties directly in evergreen browsers, so the chart re-themes on the existing light/dark toggle purely through CSS, with no React re-render or JS theme-detection needed. (Deviation from the plan's original wording, which said "reading CSS vars via `getComputedStyle`" — the simpler direct-string approach is more robust and was verified live in both themes.)
- [x] **Backend contract reused, not modified:** `types/api.ts` gained `ExerciseLatest`/`TrendPoint`/`ExerciseTrend`/`DashboardTrends`/`DashboardErrorTag`/`DashboardErrorTags` matching Stage 7.0's response shapes exactly; `dashboardService.trends()`/`errorTags()` updated to the keyed shapes and now accept an optional `{from, to}` date range (unused by Dashboard's all-time overview, added for Stage 7.1b's range control to reuse the same service without changing it again).
- [x] **`Dashboard.tsx` rewritten to bind real data, same DOM/CSS structure preserved** (deliberately minimal-diff — the original `.metrics`/`.dash-grid`/`.dash-grid-2`/`.dash-note` layout and panel positions are untouched; only inner placeholder content changed): avg-score tile now averages real trend points from the last 14 days (client-side, no backend change needed); latest-band tile binds to the first recently-completed session with a score, including its real exercise name; score-trend panel became a `.mini-trend-grid` of real per-exercise cards; band-distribution panel renders `BandDistributionBar` over all pooled trend points; the previously-static confidence sub-panel is now a real average-confidence bar, hidden entirely when the account has no Module B sessions; error-tags panel renders real ranked tags via the existing `moduleB.tag_<code>` i18n messages (already present in en/zh/ms from Phase 6, reused rather than inventing new labels) with `severityClass`-mapped dots, with a real empty state when the account has zero Module B sessions.
- [x] **i18n (en/zh/ms), all three kept in sync:** added `dash.sessionsCount`, `dash.noErrorTags`; changed `dash.latestBand` (dropped the hardcoded "· Sit-to-Stand" example — the real exercise name is now interpolated in JSX, matching how `exercise_name` is already rendered untranslated elsewhere, e.g. the recent-sessions table) and `dash.bandDistSub`/`dash.scoreTrendSub` wording to describe the real panels; **removed `dash.placeholderScoring`** from all three locale files after grepping and converting its 4 callers (score-trend sub, band-dist sub, confidence sub, error-tags sub) — no callers remained before deletion.
- [x] **New CSS** in `frontend/src/index.css` (`.mini-trend-grid/.mini-trend-card/.mini-trend-head/.mini-trend-sub/.mini-trend-foot/.mini-trend-score`, `.band-dist-bar/.band-dist-seg/.band-dist-legend/.band-dist-legend-item`), themed with the existing design tokens only — no new colors introduced.
- [x] **Verified:** `npx tsc --noEmit` clean; `npx vite build` succeeds (1101 modules, no errors); `npm run test` (Vitest) 3/3 pass. **Pre-existing, unrelated issue found and left alone (not caused by this stage, confirmed via `git stash`):** `npx tsc -b` (the stricter build-mode project-references check `npm run build` actually invokes) fails on `src/pages/Report.test.tsx:60` — `ModuleBResult` is missing a `feedback` field the test's fixture doesn't provide. Reproduced with my changes stashed out, so it predates Stage 7.1; flagged to HY rather than silently fixed, since Report.tsx/ModuleBResult are outside this stage's scope.
- [x] **Live end-to-end**, using Stage 7.4's seeded `demo-progress@physiofit-demo.com` account against the real backend on `:8000`: logged in via the browser, confirmed all three dashboard endpoints return `200 OK` with zero console errors; every number on the page traced back to the seed data exactly — avg score 6.9/10 (14d), latest band "Good · 7.5 · Squat", 12 sessions, 76% avg quality, band distribution "Good 3 / Fair 3 / Needs Improvement 6" (hand-computed from `seed_demo_progress.py`'s 12 rows and matched exactly), confidence 86% (mean of the 6 seeded squat confidences, matched exactly), 4 ranked error tags with correct counts (2/2/2/1) using the real `moduleB.tag_`* messages, "Needs Improvement" label correctly shown for the "Poor" band per the existing Stage 5.11 UI relabeling. Verified in both light and dark theme (dark: lime accent applied automatically, no code path change) and at mobile viewport (375×812: tiles stack single-column, full content present via `get_page_text`).
- [ ] Capture-quality trend and confidence-trend line charts — moved to Stage 7.1b (next), not built here (see scope note above).

### Phase 7 — Stage 7.1b: Progress deep-dive page (2026-07-19)

- [x] **New route:** `GET /progress` wired in `frontend/src/App.tsx` (new `Progress.tsx` page under the same `ProtectedRoute`/`DashboardLayout`). **This closes the bug HY reported at the start of this work:** the sidebar's "Progress" nav link in `frontend/src/layouts/DashboardLayout.tsx:80` was hardcoded to `to="/dashboard"` with a no-op `className={() => ""}` (dead code — no `/progress` route existed at all), so clicking it silently re-rendered the Dashboard. Fixed to `to="/progress"` with the same `isActive` pattern every other sidebar link already used; live-verified the nav item now highlights correctly on the new page instead of redirecting.
- [x] **Generalized `QualitySparkline.tsx` (built in Stage 7.1, unused until now) into `PercentTrendChart.tsx`.** Both the capture-quality trend and the confidence trend are the exact same shape — a 0-1 fraction plotted over time with the same tooltip/axis mechanism — differing only in field name, color, and label. Rule 16 treats that as genuinely shared logic, not per-metric variants, so one component takes a `dataKey: "capture_quality" | "confidence"` prop instead of two near-duplicate files. Supports the same `mini`/`full` variant split as `ScoreTrendChart`.
- [x] **New `ErrorTagBarChart.tsx`** — ranked horizontal bar chart (Recharts `BarChart layout="vertical"`), one bar per tag, colored by `severityClass` (high=coral/medium=amber/low=emerald, matching the existing `.sev` dot colors), axis label is a short humanized tag name, full clinical message (`moduleB.tag_<code>`) shown on hover. Deliberately more analytical than Dashboard's compact `.tags` chip list — appropriate for a single-exercise deep dive, not a duplicate of the overview panel.
- [x] **`humanizeExerciseType` split**, `dashboardChartUtils.ts`: extracted the generic snake-case-to-Title-Case part into `humanizeSnakeCase` (used by `ErrorTagBarChart` for tag codes) so `humanizeExerciseType` (which also does the recent-sessions name lookup) isn't misused for an unrelated purpose under a misleading name.
- [x] **`Progress.tsx`:** exercise segmented selector (one button per key in the `/trends` response, reusing the existing `.seg` CSS already defined for the previously-nonfunctional 14d/30d/All mockup buttons) + a real 14d/30d/All date-range control that computes `from` client-side and re-fetches both `dashboardService.trends({from})` and `.errorTags({from})` — the exact two endpoints Stage 7.0 built, no new backend work needed. Selected exercise persists across a range change when still present in the new response, otherwise falls back to the first available key. Panels per selected exercise: full `ScoreTrendChart` (band zones + axes), `BandDistributionBar` (reused from Stage 7.1, now scoped to one exercise instead of pooled), capture-quality `PercentTrendChart`; **Module B only** (detected via presence of the exercise's key in the `/error-tags` response, the same "key present = has module_b_result" signal Stage 7.0 established): confidence `PercentTrendChart` + `ErrorTagBarChart`. Empty states for zero exercises and zero sessions-in-range.
- [x] **Verified:** `npx tsc --noEmit` clean; `npx vite build` succeeds; `npm run test` (Vitest) 3/3 pass.
- [x] **Live end-to-end** against the same seeded `demo-progress@physiofit-demo.com` account: confirmed via direct SVG DOM inspection (not just screenshots) that `ScoreTrendChart`'s three `ReferenceArea` zones render at the correct Y positions (Poor red at the bottom `y=128.4`, Fair amber in the middle `y=67.2`, Good green at the top `y=6`, for a `[0,10]`-domain chart) and that both axes' tick labels are present (Y: `0/3/6/10`; X: real dates) — an early DOM query missed them by using the wrong Recharts v3 class name (`.recharts-reference-area rect` / nested tick text) and returned an empty array, which could have been mistaken for a real bug; the correct selectors (`.recharts-reference-area-rect`, `.recharts-{x,y}Axis-tick-labels`) confirmed everything renders correctly. STS tab: band distribution 1/3/2 matched the seed exactly; Squat tab: band distribution 2/0/4 matched, confidence trend + 4 ranked error tags (correct severity colors) appeared as Module-B-only panels; switching to the 14d range correctly re-fetched and narrowed Squat to 3 sessions, band distribution 2/0/1, and exactly the 2 tags present on those 3 sessions (the other 2 tags, only present on older sessions, correctly dropped) — confirming the date-range filter round-trips through the real backend rather than filtering stale client-side data. Checked in both light/dark theme.
- [ ] `dashboardChartUtils.ts`'s `SCORE_BAND_THRESHOLDS`/`bandKey` etc. remain hand-mirrored from the backend's Python config rather than served by an API — acceptable since Table 6 is a fixed, cross-exercise constant (confirmed identical in both `module_a` and `module_b` configs in Stage 7.1), but noted as a value to re-verify if that constant ever changes on the backend.

#### Fix (2026-07-19): score-trend zone colors too subtle

HY flagged (with screenshots, both light and dark theme) that the Good/Fair/Poor `ReferenceArea` background zones on `ScoreTrendChart` (`variant="full"`) were not obviously distinguishable — the three zones sat at ~12-13% opacity (`GOOD_ZONE` reused the app-wide `--good-bg` token; `FAIR_ZONE`/`POOR_ZONE` were literal low-alpha `rgba()`), which read as a near-flat wash once layered under the line's own semi-transparent area-fill gradient, especially in dark mode.

- [x] `frontend/src/components/charts/ScoreTrendChart.tsx`: zone fills switched to `color-mix(in srgb, var(--good|--amber|--coral) 22%, transparent)` — a dedicated, theme-aware ~1.7x opacity boost that doesn't touch the shared `--good-bg` token (which is also used by unrelated UI — tags, metric icons — and shouldn't have been bumped globally). Added a matching 25%-opacity `stroke` on each `ReferenceArea`'s boundary for a visible edge between zones. Added a small color-swatch legend (`Good`/`Fair`/`Needs Improvement`, reusing the existing `common.good/fair/poor` i18n keys) rendered directly under the chart whenever `variant="full"` — so the mapping doesn't rely on color perception alone.
- [x] **Verified:** `tsc --noEmit` clean; live screenshots in both light and dark theme on the Progress page (`demo-progress@physiofit-demo.com`, Sit-to-Stand) confirm all three bands are now clearly distinct with the legend directly beneath.

#### Follow-up (2026-07-19): exercise-picker categorization + active-exercise gating

HY raised three ad-hoc requirements against the Phase 7 UI beyond the original stage checklists, prompted by a live screenshot showing the retired "Leg Lunge" exercise still selectable as a Progress-page tab:

1. Categorize the Progress page's flat exercise-tab row into Functional Checking / Rehab Grading, with a dropdown for the exercise itself within the chosen category.
2. Gate exercise **pickers** (not historical data) to only currently-active exercises, so a retired exercise like the old Leg Lunge can't be newly selected even though its past sessions remain in the database.
3. Add an exercise sub-filter to `SessionHistory.tsx` alongside the existing mode filter, later refined (2026-07-19, same day) so the exercise dropdown only appears once a specific mode ("Functional" or "Rehab") is chosen — not under "All" — and is scoped to that mode's exercises.

**Root cause of the Leg Lunge leak:** `GET /api/exercises` already server-filters to `is_active=true` (confirmed in `backend/app/api/exercise_routes.py`), so the catalog itself was never the problem. The Progress/Dashboard exercise pickers were instead deriving their exercise lists from `Object.keys(trends)` -- i.e. whichever exercise types have **historical sessions** -- which includes retired exercises for any account that used them before removal. The fix cross-references those keys against a fresh `exerciseService.list()` fetch, not a change to any endpoint.

**Decisions confirmed with HY before implementing:**

- Session History's "All" view still shows every historical session including retired exercises; only the exercise-filter **picker** options are gated to active exercises (matches the existing "deactivate, don't delete" precedent from the Lunge removal itself).
- The same active-exercise gate was applied to Dashboard's score-trend small-multiples grid too, not just Progress, since it had the identical bug.
- Progress's category tabs reuse the existing `landing.modATitle`/`modBTitle` i18n copy ("Functional Checking" / "Rehab Grading") rather than inventing new strings.

**Files:**

- `frontend/src/components/Dropdown.tsx` (new) -- generic single-select popover dropdown, styled to match the existing `LanguageSwitcher` pattern (`Controls.tsx`) rather than a native `<select>`; new `.dropdown`/`.dropdown-menu` CSS in `index.css` mirrors the existing `.lang`/`.lang-menu` rules without touching them (avoids any regression risk to the already-verified language switcher used on every page). Added a `ChevronDown` icon to `Icons.tsx`.
- `frontend/src/pages/Progress.tsx` -- exercise picker rebuilt as category `.seg` toggle (Functional Checking / Rehab Grading) + `Dropdown` scoped to that category's active exercises that also have session data (`exercisesWithData`/`categoryExercises` derived via `useMemo`); selection re-derives via a dedicated `useEffect` keyed on `[categoryExercises]` so switching category or range never leaves a stale/invalid exercise selected. No longer needs `sessionService`/`humanizeExerciseType` for exercise names -- `exerciseService.list()` supplies the authoritative name directly.
- `frontend/src/pages/Dashboard.tsx` -- added `exerciseService.list()` to the existing `Promise.all` fetch; new `activeTrendEntries` filters the score-trend small-multiples grid to active exercise codes only. Deliberately **not** applied to `allPoints` (band distribution, avg score, confidence, error tags) -- those aggregate tiles keep counting a retired exercise's historical sessions, same "gate the picker, not the history" principle.
- `frontend/src/pages/SessionHistory.tsx` -- added `exerciseFilter` state + `Dropdown`, combinable with the existing mode filter pills. Refined same-day: `categoryExercises` now filters by `e.mode === filter` (no `filter === "all"` fallback), the dropdown only renders when `filter !== "all"`, and a new `selectFilter` handler resets `exerciseFilter` back to "All exercises" on every mode-pill click so a stale cross-category selection can't survive a filter change.
- i18n (en/zh/ms): `progress.chooseExercise`, `progress.noExerciseInCategory`, `progress.exercisePicker`, `history.allExercises`.

**Verified:** `tsc --noEmit` clean; `vite build` succeeds; Vitest 4/4 (unrelated `Report.test.tsx`/`Report.tsx` changes appeared in the working tree from outside this session during this work -- not touched, flagged to HY). **Live end-to-end**, with a temporary historical Leg Lunge session manually seeded onto `demo-progress@physiofit-demo.com` for regression coverage (removed afterward to restore the account's documented 12-session state): Progress's category tabs correctly show "Functional Checking" -> Sit-to-Stand only and "Rehab Grading" -> Squat only, no Leg Lunge in either; Dashboard's small-multiples grid excludes the Leg Lunge card while its aggregate tiles (session count, band distribution) still counted the historical row; Session History's "All" view showed the Leg Lunge row in the table while the exercise dropdown (once "Functional" or "Rehab" was clicked) never offered it as an option; "All" mode correctly hides the exercise dropdown entirely, and switching between "Functional"/"Rehab" correctly reset the dropdown to "All exercises" each time.

### Stage 7.2 — Per-session trend rows for STS and SLS

- [x] WBLT has a real per-session "vs last session" row on `Report.tsx` (Phase 3E Stage 6). STS and SLS do not. Add the equivalent, reusing `compute_trend`'s shape.
- [x] For STS/SLS, the MDC caveat from 7.0 applies: **no invented "meaningful change" threshold.**

### Phase 7 — Stage 7.2: Per-session trend rows for STS and SLS (2026-07-19)

- [x] **Reconciliation (rules.md pre-work check):** confirmed WBLT's actual trend architecture by reading `app/module_a/wblt/analysis.py::compute_trend`, `app/module_a/wblt/crud.py::get_previous_wblt_legs`, `app/module_a/wblt/router.py`, and `Report.tsx`'s `wbltTrendText`/fetch/render sites in full (via an Explore agent, then re-verified the exact current file state directly since `Report.tsx` had uncommitted changes from outside this session). Found the task.md checklist's implied "one `compute_trend`, three exercises" picture doesn't hold structurally: **STS has no per-exercise router/crud/schema at all** (it's the fully generic `core/router.py` + `ModuleAResultResponse` with a passthrough `metrics: dict`), **SLS uses camelCase metric keys** (`holdSeconds`/`combinedScore`, not WBLT's `best_distance_cm`/`leg_angle_deg`) and has no `captured_at` completeness stamp (uses `session_status` instead), and **no MDC config exists for either** — so `compute_trend`'s _shape_ (per-thing dict, `None` for incomparable data) was reused, but the `_meaningful`/MDC-flag mechanism was deliberately dropped, not adapted.
- [x] **Chose to enrich the already-fetched generic endpoint rather than add new ones:** `Report.tsx` already calls `moduleAService.get(sessionId)` (`GET /api/module-a/sessions/{id}`) for both STS and SLS reports (confirmed this endpoint is exercise-agnostic — it reads the shared `ModuleAResult` table regardless of which router originally wrote the row). Added an optional `trend` field directly to `ModuleAResultResponse`/`ModuleAResult` (frontend), populated only for `sit_to_stand`/`supported_single_leg_stance` inside `get_session_result`. This means **STS/SLS need no second network call** at all — simpler than WBLT's own pattern, which fetches a dedicated `wbltApi.session()` purely to get `trend` on top of data already in `result.metrics`.
- [x] **New files:** `backend/app/module_a/sts/trend.py` (`compute_trend(current, previous) -> dict|None`: `score_delta`, `completion_time_delta_sec`, `previous_band`, no `_meaningful` field of any kind) and `backend/app/module_a/sls/trend.py` (`compute_trend(current_legs, previous_legs) -> dict[leg]`: `hold_delta_sec`, `score_delta`, `previous_band`, reads the real camelCase `perLeg` keys). Both pure functions, DB-free, unit-tested directly (`backend/tests/test_module_a_sts_trend.py`, `test_module_a_sls_trend.py`, 10 tests, including an explicit `test_no_meaningful_flag_is_ever_present` guard against ever reintroducing an invented MDC claim).
- [x] **Shared "previous completed session" lookup**, `app/module_a/core/crud.py::get_previous_completed_result` — reused by both STS and SLS (genuinely shared logic per rules.md #16, unlike the exercise-specific trend math). Gates on `session_status == "complete"` (the same completeness signal both already write; a private `_inferred_session_status` mirrors `core/router.py`'s existing fallback rather than importing across modules).
- [x] **Bug found and fixed during live verification, not copied from WBLT:** the initial `get_previous_completed_result` picked "the most recent OTHER completed result" with no check that it was chronologically _before_ the session being viewed. This is latent/harmless when a report is viewed right after finishing the newest session (the overwhelmingly common path), but produces a **nonsensical trend** when browsing an _older_ session's report from Session History — e.g. an account's very first session showing a fabricated "improved" comparison against a session that happened later. Caught this via `TestClient`-driven end-to-end testing (not just the pure-function unit tests, which wouldn't catch a DB-ordering issue), not by inspection. Fixed by adding a required `before: datetime` bound (the current session's `created_at`) to the query, filtering out any candidate `created_at >= before`. **Deliberately not back-ported to WBLT's own `get_previous_wblt_legs`**, which has the identical latent characteristic — that file is already-shipped Stage 6 code outside this stage's scope; fixing it would be an unrequested change to verified code. Flagging here in case HY wants it addressed as a follow-up.
- [x] **Frontend** (`frontend/src/pages/Report.tsx`, `services/moduleAService.ts`): added `StsTrend`/`SlsLegTrend` types and an optional `trend` field on `ModuleAResult`, mirroring how `metrics.legs`/`metrics.perLeg` are already exercise-specific optional fields on the same shared type. New `stsTrendText`/`slsLegTrendText` formatters alongside the existing `wbltTrendText` — **structurally simpler than WBLT's**: no `_meaningful` branch, the delta is always shown when available, never suppressed into an "about the same" claim. Rendered: STS gets one trend paragraph below its `.sub-scores` metrics grid (guarded `!isSls && !isWblt`, since SLS's legacy pre-rebuild rows fall through the same `metricRows` branch but carry an SLS-shaped `trend`, not STS's — misreading one as the other would silently render garbage); SLS gets one trend paragraph per leg, inside each leg's existing panel, same position as WBLT's per-leg trend line.
- [x] i18n (en/zh/ms): new `report.trendVsLast`/`trendNoPrevious`/`trendScoreChanged`/`trendTimeChanged`/`trendHoldChanged` keys (distinct from the existing `wblt.trend*` namespace, since the copy and no-MDC semantics genuinely differ).
- [x] **Verified:** `tsc --noEmit` clean; Vitest 4/4; backend suite **245/245** (235 + 10 new trend tests) — `from app.main import app` imports clean with the new `sls`/`sts` trend module imports in `core/router.py`. **Live end-to-end via `TestClient`** (not just unit tests): seeded two real STS sessions and two real SLS sessions with actual `ModuleAResult` rows for a scratch account, confirmed `GET /api/module-a/sessions/{id}` returns the correct `trend` for the latest session, `None`/per-leg-`None` for the oldest (after the chronology fix above), scratch account removed after. **Live in the browser**, via a second scratch account: STS report showed `"Vs last session: score +1.5 · time -2.5s"` exactly matching the API response; SLS report showed the same trend text independently for both Right leg and Left leg panels. Along the way, caught that my own raw test-data script used capitalized `"Good"`/`"Fair"` band values, which STS's real pipeline never produces (`app/module_a/core/banding.score_to_band` returns lowercase `"good"/"fair"/"poor"`) — this produced a `t("common.Good")` untranslated-key artifact and a wrong `bandMeaningKey` fallback in my first browser check; confirmed via reading `banding.py` that this was a test-fixture mistake, not a product bug, fixed the fixture, and re-verified cleanly. Both scratch accounts removed after verification.

### Phase 7 — Stage 7.4: Squat trend row + delta units/tooltip polish + live end-to-end sign-off (2026-07-19)

Two HY-requested polish items done alongside Stage 7.4's outstanding live-verification pass (bundled because 7.4's walkthrough exercises every report screen anyway): (1) give the score/rep deltas a **unit** so a bare "+1.5" reads clearly, and (2) add a **"vs last session" trend row to the squat report**, which had none while STS/SLS/WBLT all did.

- [x] **Reconciliation (rules.md pre-work check):** confirmed via an Explore agent that Module B has **no** reusable "previous result" primitive (no `list_history`, no `get_previous_`* under `module_b/`) and — unlike Module A — **no `session_status` column** (a `Session.status` is unconditionally `"completed"` once any Module B result is saved; low-confidence surfaces only as error tags/fusion flags). So Module B's "previous session" lookup is simpler than Module A's: most-recent prior result, no completeness filter. Also confirmed `ModuleBResult` has **no `completion_time_sec`** like STS — `rep_count` lives on `Session`, not the result row — so squat's delta compares **score + reps completed**, not time.
- [x] **Backend, mirroring Stage 7.2's shape:** new `backend/app/module_b/squat/trend.py` (`compute_trend(current, previous) -> dict|None`: `score_delta`, `rep_count_delta`, `previous_band`, deltas rounded 2dp, **no invented "meaningful"/MDC flag** — same rule as 7.2, guarded by a `test_no_meaningful_flag_is_ever_present` test). New `app/module_b/core/crud.py::list_history` + `get_previous_result(..., before: datetime)` — the `before` bound is present from the start here (the Stage 7.2 chronology bug's fix carried forward by design, not rediscovered). Wired into `GET /api/module-b/results/{id}` via a `_compute_trend` helper + a new optional `trend: dict|None` on `ModuleBResultResponse`; `rep_count` is read from each result's own eager-loaded `Session` row. 5 new tests (`backend/tests/test_module_b_squat_trend.py`).
- [x] **Frontend:** `SquatTrend` type + optional `trend` on `ModuleBResult` (`moduleBService.ts`); new `squatTrendText` formatter and squat trend row rendered below the squat metrics grid (`Report.tsx`). **Score delta now carries a `/10` suffix everywhere** (`report.trendScoreChanged` → `score {{sign}}{{value}}/10`, matching the score dial on the same page) and squat's rep delta uses a new `report.trendRepsChanged` (`reps {{sign}}{{value}}`); WBLT's cm/° and STS/SLS's `s` suffixes were already present. **"Compared to last session" note** implemented as HY asked — a tooltip, not inline text: a shared `TrendLine` component pairs each of the four trend lines (WBLT/STS/SLS/squat) with the existing `InfoTooltip` (`report.trendInfoLabel`/`trendInfoText`), so the affordance is identical across all exercises. i18n keys added to en/zh/ms.
- [x] **Seed-data fix uncovered by the live pass (this is why live verification exists):** the squat Report page crashed to a blank screen on **every** seeded squat session — `TypeError: Cannot read properties of undefined (reading 'capture_quality_band')` in `Report.tsx`. Root cause: `seed_demo_progress.py` left `ModuleBResult.metrics_json` **NULL**, but the real `/analyze` pipeline (`module_b/core/crud.py::_metrics_json`) always writes a rich metrics dict, and the report reads `metrics.capture_quality.capture_quality_band` / `metrics.rule_subscores` / `metrics.ml_score`. The seed's TestClient-level Stage 7.0 checks never caught this because they don't render React. **This was pre-existing — not introduced by the trend work** (the crashing line predates it); it simply had never been rendered live before. Fixed in the seed (not with defensive UI code — real data always has these fields; the seed was the boundary producing malformed data): added `_squat_metrics_json(...)` producing the true pipeline shape (`capture_quality {q, valid_frame_ratio, capture_quality_band}` via the real `quality_band()`, three `rule_subscores`, `ml_score`, `fusion_weights` `{w_rule:0, w_ml:1}` per Stage 5.11, `placeholder_model_notice: False`). Also pinned `ModuleBResult.created_at = started` (the session date) so the trend has a real chronological order to compare against — otherwise all rows share the seeding instant and `get_previous_result`'s `before` filter excludes everything (trend always null).
- [x] **Verified:** backend suite **250/250** (245 + 5 new squat-trend tests); `tsc --noEmit` clean; Vitest 4/4; `vite build` clean; Black + Prettier clean. **Live end-to-end** against the real backend (`:8000`) + Postgres using the reseeded `demo-progress@physiofit-demo.com` account: squat report now renders fully (7.5/10 dial, Good band, **Capture quality: Good** — the previously-crashing field — reps 7, ROM/tempo/stability 7.5/10, ML 7.5/10, confidence 95%), and the new trend row reads **"Vs last session: score +0.6/10 · reps +0"**, matching the seed math exactly (7.5 vs 6.9 = +0.6; 7 vs 7 = 0) with the info-tooltip button present (aria-label resolved from i18n, not a raw key). Confirmed in **both light and dark theme** (trend text + tooltip intact in dark). Dashboard and Progress (Functional=STS and Rehab=Squat) still render with no console errors and no regression from the schema/type additions — squat Progress band distribution "Good 2 / Fair 0 / Needs Improvement 4" matches the seed's binary Good/Poor. Temporary `index.html` error-capture script used to extract the crash stack was reverted (git diff clean).
- [x] **Note for HY:** STS sessions in `seed_demo_progress.py` create only a `Session` row, no `ModuleAResult`, so seeded STS/SLS **reports** 404 and aren't openable from this demo account (Dashboard/Progress read the aggregate `sessions` columns, so they're unaffected). The `/10` unit change and the shared tooltip are proven on the squat report, which reuses the exact same i18n keys and `TrendLine` component, so the change is verified for all four exercises; STS/SLS/WBLT trend _computation_ remains covered by their unit tests and the earlier scratch-account browser check (Stage 7.2). Left as-is (out of this stage's scope) rather than fabricating `ModuleAResult` rows into the seed.

### Phase 7 — Stage 7.3: Reminders — real CRUD, calendar export, due-alerts, exercise deep-link (2026-07-19)

HY asked for reminders to be genuinely useful — Google Calendar / .ics export, a login alert with a red-dot badge, clicking a reminder deep-linking straight into its exercise, and (asked as an optional aside) email verification on signup. Went through a scoping round with HY first since several of these are real architectural decisions (delivery mechanism, whether to build email infra at all) with no existing precedent in this codebase to copy.

- [x] **Reconciliation:** `reminders` (table + `User.reminders` relationship) already existed, created in the very first migration (`20260605_0001_initial_schema.py`) — but with **no schema, router, service, or real UI** at all; `Reminders.tsx` was a fully hardcoded 3-card mock with a no-op "Add" button. Confirmed via research: **no email-sending library, no Google/OAuth integration, and no background scheduler anywhere** in the repo (only `email-validator` for Pydantic's `EmailStr`). This directly shaped the design questions below.
- [x] **Decisions confirmed with HY (asked, not assumed):** (1) delivery is a **Google Calendar link + downloadable `.ics`**, not backend email or Calendar-API OAuth sync — the user's own calendar app fires the real timed alert, honoring this stage's original "keep it simple, no scheduling infrastructure" note with zero new secrets/services; (2) **email verification on signup was explicitly skipped** — it was the only ask that would have forced building email infra from scratch, and HY chose not to take that on; (3) a reminder **deep-links straight to its exercise** when clicked; (4) the nav red-dot shows **only when something is actually due**, not merely because a reminder exists.
- [x] **Backend** (all new): migration `20260719_0011_reminder_exercise_and_completion.py` adds nullable `exercise_code` (deep-link target; deliberately not an FK, so a reminder survives its exercise being retired later, e.g. the removed Lunge — the frontend gates the deep-link itself, not the row) and `last_completed_at`. Pure-function service `app/api/reminders_service.py`: `is_due(reminder, now)` (recurrence vocabulary `once`/`daily`/`mwf`/`weekly`, fails closed on an unrecognised frequency rather than guessing), `build_ics(...)` (RFC-5545 VEVENT + popup VALARM + RRULE), `build_google_calendar_url(...)` (a plain `calendar.google.com/render` link, no OAuth). New `app/db/schemas.py` `ReminderCreate`/`Update`/`Response` and `app/api/reminders_routes.py`: `GET/POST /api/reminders`, `PATCH`/`DELETE /{id}`, `POST /{id}/complete`, `GET /{id}/export.ics` — all owner-scoped via the same `_get_owned_session`-style 404 guard used elsewhere. `ReminderResponse.exercise_name`/`exercise_mode` are resolved from the exercise catalog **at request time, never persisted**, so a retired exercise's name doesn't linger as stale text.
- [x] **Tests:** `backend/tests/test_reminders_service.py` (22 new tests) — every frequency × before/after the scheduled time × completed-today vs not × inactive, `.ics` structure (VEVENT/RRULE/VALARM present, correct per frequency, title escaped), and Google Calendar URL params (base/action/text/dates, `recur` present only when recurring).
- [x] **Frontend:** `services/reminderService.ts` (list/create/update/complete/remove + a Blob-based authenticated `.ics` download, since the endpoint returns `text/calendar` not JSON — `apiClient.ts`'s `API_BASE_URL` exported for this one non-JSON caller). New `src/reminders.tsx` (`RemindersProvider`/`useReminders`, flat top-level file matching this project's existing `auth.tsx`/`session.tsx` convention rather than introducing a `context/` folder), mounted inside `DashboardLayout` so the nav badge and every page share one fetch. `Reminders.tsx` rewritten: real list, a create modal (title, `datetime-local`, frequency select, an exercise `Dropdown` sourced from `exerciseService.list()` — already active-only per Stage 7.1's gating, so a retired exercise never appears as a new target), and per-card actions (Add to Google Calendar, download `.ics`, mark done, delete). Clicking a card body with a resolved `exercise_name` calls `resetSession() → setMode() → setExerciseCode() → navigate("/camera")` via `useSessionFlow` — the same state the existing `/mode → /exercise → /camera` flow already expects, so no new routing was needed. Dashboard gained a due-count banner (coral, dismissed by nothing — it just stops rendering once nothing's due) and its own reminders mini-panel now shows real data instead of a second, separate hardcoded mock. New `Calendar`/`Download`/`Trash` icons (`Icons.tsx`) and `.nav-badge-dot`/`.reminder-modal-`*/`.rem-actions`/`.chip-due` CSS.
- [x] **Two real bugs found live-testing, not just added defensively:**
  1. **`Dashboard.tsx` never called `useReveal` with its own async data as a dependency** — `DashboardLayout`'s `useReveal([pathname])` fires on mount, before `Dashboard`'s `summary`/`trends`/reminders fetches resolve, so its IntersectionObserver never sees the real content and every `.reveal` element (metric tiles, charts, the reminders panel) stayed at `opacity:0` forever. **This predates the reminders work** (confirmed via `git diff` — no `-useReveal` line was ever removed, it simply never existed) and would have silently affected the whole Dashboard page; it only became visible now because the new due-banner made the gap impossible to miss. Fixed by adding `useReveal([loading, allReminders])`, mirroring `Report.tsx`'s established pattern.
  2. **The due chip nested inside `.rem-body`** (`<b>{title}<span className="chip chip-due">...</span></b>`) **was hijacked by the existing `.rem-body span` CSS rule** (intended for the muted subtitle line), which forces `display:block` on any span inside — it rendered as a full-width coral bar instead of a small pill. Fixed by moving the due chip out as a sibling of `.rem-body`, next to the existing frequency chip, which was never nested and never had the problem.
- [x] **Verified:** backend suite **272/272** (250 + 22 new); `tsc --noEmit`, Vitest 4/4, `vite build`, Black + Prettier all clean; migration `upgrade`/`downgrade`/`upgrade` round-tripped cleanly against the dev DB. A `TestClient` smoke test exercised every endpoint end-to-end (register → create → list → export.ics → complete → patch inactive → delete → 404 on re-delete), confirming `is_due`, the resolved exercise name/mode, and both calendar links came back correct. **Live end-to-end** in the browser with the reseeded `demo-progress` account: created a Squat reminder due in the past — it appeared instantly with a **Due** chip, the nav red dot appeared, and the Dashboard due-banner ("You have 1 reminder(s) due today.") rendered; downloaded its `.ics` and fetched it directly, confirming a valid `SUMMARY`/`DTSTART`/`VALARM` with no stray `RRULE` (one-time); its Google Calendar link resolved to the correct `action=TEMPLATE&text=...&dates=...` with no `recur` param; marking it done cleared the chip, the nav dot, and the banner. Created a second reminder tied to Sit-to-Stand and clicked its card — landed on `/camera` showing the STS-specific side-view guidance text, confirming the deep-link set the correct exercise and mode through `useSessionFlow` (camera capture itself is blocked in this sandboxed browser, a known pre-existing limitation, not a defect here). Re-verified the whole flow in **dark theme**. Both scratch reminders removed afterward, demo account left clean.
- [x] **This closes Phase 7.** Stages 7.0–7.4 are all done; Phase 3's `[~] Show dashboard trend` line (flipped in Stage 7.4) now fully covers WBLT, STS/SLS, and squat trend rows plus real Dashboard/Progress panels.

### Stage 7.4 — Verification

> **Seed script built ahead of schedule (2026-07-19), per the approved Phase 7 plan's execution order** (`docs/phase7_plan.md`): the multi-session demo account is created _before_ Stage 7.1/7.1b so those stages have real data to render against. Full live end-to-end screenshot verification below stays deferred until those stages exist.

- [x] **Seed script:** new `backend/app/seed_demo_progress.py` (separate from `app/seed.py`, which only seeds the exercise catalog + a single env-var demo login). Creates account `demo-progress@physiofit-demo.com` / `DemoProgress123!` with 6 `sit_to_stand` (Module A) + 6 `squat` (Module B) sessions spread over the last 26 days, upward-trending scores/bands/capture_quality so the trend charts show visible improvement with realistic noise. Squat sessions carry `module_b_results` (`confidence`, `q`, `model_version="demo-seed"` — clearly marked as not a real trained-model run) and `module_b_error_tags` using the actual squat tag taxonomy (`insufficient_depth`, `excessive_forward_lean`, `heel_lift`, `inconsistent_tempo`) with their real severities. Squat bands are Good/Poor only (no invented "Fair" — squat is a committed binary classifier per Stage 5.11).
- [x] **Idempotent + removable:** re-running `python -m app.seed_demo_progress` clears and recreates the same account's sessions rather than duplicating them (verified: ran twice, row counts unchanged at 12 sessions / 6 module_b_results / 7 error tags). `python -m app.seed_demo_progress --purge` deletes the account entirely (cascades via FK `ondelete="CASCADE"`).
- [x] **Note on the demo email domain:** `.local` was tried first and rejected by `pydantic`'s `EmailStr` validator as a reserved special-use TLD (`demo-progress@physiofit.local` → 422 on login) — switched to `demo-progress@physiofit-demo.com`, confirmed to pass validation and login successfully.
- [x] **End-to-end proof the Stage 7.0 APIs work with real data**, via `TestClient` login + authenticated requests against the seeded account: `/api/dashboard/trends` returns both `sit_to_stand` (6 points, scores 4.2→7.8, `mdc_source: "none"`) and `squat` (6 points, scores 3.1→7.5, `mdc_source: "none"`) keyed correctly, oldest-first; `/api/dashboard/error-tags` returns **only** the `squat` key (Module A correctly absent) with tags ranked most-frequent-first; `/api/dashboard/summary.latest` returns per-exercise latest score/band/quality for both types. Full backend suite still 235/235 green after adding the script.
- [x] Backend suite green (**250/250**); `tsc --noEmit` + Vitest + `vite build` clean; Black + Prettier clean. (See Stage 7.4 dated entry above.)
- [x] **Verified live end-to-end** with the multi-session `demo-progress@physiofit-demo.com` account (STS + squat): Dashboard, Progress (Functional + Rehab categories), Session History, and the squat Report all render against real seeded data with no console errors; the squat "vs last session" trend row shows `"score +0.6/10 · reps +0"` matching the seed. Fixed a pre-existing seed-data crash (NULL `module_b_results.metrics_json`) surfaced by this pass. (See Stage 7.4 dated entry above.)
- [x] Phase 3 line (`[~] Show dashboard trend`) flipped to `[x]` — this phase closes it.

**Deliverable:** User can track progress over time across all exercises, with no placeholder scoring left in the Dashboard.

---

## Open Questions (Phases 4–7)

Track these; do not silently resolve them by assumption.

| #   | Question                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Blocks                                                                 | Settles via                                                                                                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Q1  | **Usable side-view Ex6 rep count** after the orientation filter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Phase 5 Stage 5.0 gate                                                 | `Segmentation.csv` + `Segmentation.txt` + one visual check per orientation value                                        |
| Q2  | Which camera is profile for each `cam17_orientation` value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Phase 5 Stage 5.2                                                      | Same as Q1 — **verify, don't assume** the working hypothesis                                                            |
| Q3  | EC3D's exact 25-joint index order — **✅ RESOLVED 2026-07-17 (Stage 5.9): OpenPose** `BODY_25`**.** The repo's data-loader route does not exist (its README gives the pickle's shape but names no skeleton format), so the order was proven empirically instead: every published `BODY_25` edge is rigid (CV 0.00007–0.00173) at anatomically sensible lengths, each foot triad's ankle attachment splits along `BODY_25`'s grouping with a ~130× margin, j08 is exactly (0,0,0) (the `MidHip` root), and two unrelated anatomical checks agree on the anterior axis. Full proof + the 8-joint MediaPipe-33 mapping in `ml/docs/ec3d_joint_mapping.md`. **⚠ Left/right handedness remains unresolved** (the pickle records no handedness convention) — proven immaterial for squat (all 13 features bit-identical under an L/R swap) but **still open for** `knee_passes_toe`, whose lead leg is side-specific. EC3D _does_ carry big-toe joints (19/22), so no ankle approximation is needed on the dataset side. | Phase 5 Stage 5.9 (**closed**); `knee_passes_toe` (**L/R still open**) | ~~EC3D repo data-loader~~ (absent), or an empirical frame plot — **done, by bone-rigidity analysis rather than a plot** |
| Q4  | REHAB24-6 authors' own baseline **+ split protocol** — **STILL OPEN, attempted 2026-07-16:** SISAP 2024 chapter is paywalled (Springer auth redirect), Zenodo record has no baseline results, no open-access version found. **No number invented**; Stage 5.7's §6 quotes only [S13] and says so.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Phase 5 Stage 5.7's comparison (**shipped without it**)                | SISAP 2024 paper [S12] — a random-split number is not comparable to LOSO. Needs institutional access.                   |
| Q5  | No validated sway/jitter threshold exists for the Control sub-score                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Phase 4 Stage 4.4 (heuristic, pilot-tune)                              | A postural-sway study with a quantitative in-plane cutoff (_not found_)                                                 |
| Q7  | ✅ **RESOLVED 2026-07-19 (Stage 6.4):** model id is `llama-3.3-70b-versatile` (not the plan's `llama-3.3-70b` shorthand); free tier 30 RPM / 1,000 RPD / 12,000 TPM / 100,000 TPD. Live-verified against the real API, not just the docs — see `docs/groq_model_verification.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Phase 6 Stage 6.4 (**closed**)                                         | `console.groq.com/docs/{models,rate-limits}`, retrieved 2026-07-19                                                      |
| Q8  | Cloud Run → Groq egress in the deployed demo                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Phase 8                                                                | HY decision at Phase 8                                                                                                  |

---

## Deliberately Not Built (Phases 4–7)

State each of these in the limitations chapter; an examiner reads omissions as either rigour or oversight depending entirely on whether you named them.

1. **Knee valgus / frontal-plane faults.** Ill-posed from a single monocular side view. Dropped from features, rules, tags, and evaluation. _(Not "unimplemented" — deliberately excluded.)_
2. **Option B's genuinely-learned three-class model.** Documented in `docs/module_b_option_b_alternative.md` (Phase 5 Stage 5.10); not built (no fault-severity source; breaks the EC3D firewall).
3. **Mendeley / Kaggle datasets.** Mendeley (26 subj.) is unverified-label + unsegmented → only a robustness check under Option B, which isn't being built. Kaggle's "incorrect" samples are synthetically perturbed — a model would learn the perturbation, not the biomechanics. Its fault list informed the taxonomy; its data was never used.
4. **KIMORE.** Dropped — its only advantage over REHAB24-6 was raw RGB, which proved inaccessible.
5. **Gamification.** Optional, low priority, out of these phases. If revisited, each mechanic must name its perverse incentive (the stability-trap lesson).
6. **Auto exercise detection.** The user always selects the exercise. Never inferred.

---

## Contradictions found — need HY decision

Found while merging `task_phases_4_to_7.md` into this document. **All 5 resolved by HY on 2026-07-16** — resolution summarized under each, with the full decision written into the linked stage.

1. **Fusion weight defaults (Phase 4 Stage 4.0).** `task_phases_4_to_7.md` specifies `w_rule_default = 0.4` / `w_ml_default = 0.6`. `FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md` §10.4 "Recommended initial weights" specifies `w_rule = 0.6` / `w_ml = 0.4` — the exact opposite split. Both are explicitly labelled starting/heuristic values, not final, but they disagree on which signal should dominate by default.

- **✅ Resolved:** use the new plan's 0.4/0.6 as the Phase 4 starting point, but treat neither document's number as final. The real answer comes from Stage 5.6's empirical sweep, selected against **macro-F1 and the severe-misclassification rate** (Poor↔Good confusions) — not precision alone. See Stage 5.6.

1. **Module B API shape (Phase 4 Stage 4.1).** `task_phases_4_to_7.md` specifies a per-exercise-code registry API: `GET/POST /api/module-b/{code}/config|analyze`, `GET /api/module-b/session/{id}`. The architecture doc's §14.6 specifies a single generic pair: `POST /api/module-b/analyze`, `GET /api/module-b/results/{session_id}`. This mirrors the same shape decision Module A already made differently per exercise (STS stayed on the shared dispatcher; SLS/WBLT got dedicated routers, per §24) — so precedent exists for deviating from the architecture doc, but the doc itself hasn't been updated to reflect it.

- **✅ Resolved:** follow the architecture doc's generic endpoint shape (`POST /api/module-b/analyze`, `GET /api/module-b/results/{session_id}`), implemented the way Module A actually built its own generic endpoint — a thin `core/router.py` dispatching via the registry, exercise_code carried in the request rather than the URL. `GET /api/module-b/{code}/config` is kept as one necessary addition beyond §14.6, justified the same way Module A's `GET /api/wblt/config` was. See Stage 4.1.

1. `**module_b_results` table shape (Phase 4 Stage 4.6).** The new plan wants one JSONB `metrics_json` column (mirroring the Module A pattern used for SLS/WBLT). The architecture doc's §14 SQL schema defines flat typed columns (`rule_score`, `ml_score`, `rom_score`, `tempo_score`, `stability_score`, `fusion_weights_json`, `feature_summary_json`) plus a separate `error_tags` table. These are two different persistence designs, not a superset/subset of each other.

- **✅ Resolved:** neither — a **hybrid**. Flat typed columns for the small, fixed-shape, exercise-agnostic fields Phase 7's dashboard queries directly (`session_id`, `exercise_code`, `score`, `band`, `confidence`, `model_version`, `feature_schema_version`, `q`, `created_at`); a separate `module_b_error_tags` child table (needed for cross-session tag aggregation); JSONB only for the genuinely variable-shape part (`feature_vector`, rule sub-score breakdown, per-rep summaries). See Stage 4.6.

1. `**feedback_texts` table shape (Phase 6 Stage 6.5).** The new plan wants `feedback_source: "llm" | "template"` plus provider/model version fields. The architecture doc's `feedback_texts` table has `llm_used BOOLEAN` and `safety_disclaimer` instead — no `feedback_source` or model-version column exists in the current schema.

- **✅ Resolved:** keep `feedback_source`/`provider`/`model_version`, add `llm_attempted: bool` (so "tried and rejected" is distinguishable from "never tried" — strictly more information than `llm_used`). Drop stored `safety_disclaimer` text in favor of the existing i18n-rendered disclaimer; store `disclaimer_version` instead for audit-grade traceability without duplicating text. See Stage 6.5.

1. **Dashboard endpoint shape (Phase 7 Stage 7.0).** The new plan specifies `GET /api/dashboard/trend?exercise_type=&from=&to=` (singular, parameterised). The architecture doc's §14.8 specifies `GET /api/dashboard/trends` (plural) and a separate `GET /api/dashboard/error-tags` endpoint. Different endpoint count and naming.

- **✅ Resolved:** follow the architecture doc — `GET /api/dashboard/trends` + `GET /api/dashboard/error-tags` as two endpoints. Both return their payload **keyed by** `exercise_type` in one response (not one call per exercise), so a single dashboard load covers every exercise type per the Locked Assumption that Phase 7 fixes trend/band panels for all of them. See Stage 7.0.

---

## Path/assumption mismatches found (non-blocking, informational)

1. `**ExerciseSelection.tsx` "Module B placeholder" claim (Phase 4 Stages 4.1, 4.7).** `task_phases_4_to_7.md` says "`ExerciseSelection.tsx` already renders a Module B placeholder — replace it" as if there's a component branch to swap. Checked the actual file: it renders exercises entirely data-driven from `exerciseService.list()` against the backend exercise catalog — there is no hardcoded Module B branch in the component itself. The "placeholder" is a seeded catalog row (`module_b_placeholder_exercise`, per the architecture doc's exercise catalog table). "Replacing" it means updating that backend seed row to a real `squat` entry, not editing `ExerciseSelection.tsx`. Noted inline at both stages; does not require a decision, just a corrected mental model before implementing.

---

## Phase 8: Deployment

**Goal:** Deploy the system to Google Cloud Platform.

**Tasks:**

- [ ] Dockerize FastAPI backend
- [ ] Create Cloud SQL PostgreSQL instance
- [ ] Deploy backend to Cloud Run
- [ ] Connect Cloud Run to Cloud SQL
- [ ] Deploy frontend to Firebase Hosting or Cloud Run
- [ ] Configure CORS and environment variables
- [ ] Test deployed frontend-backend-database flow

**Deliverable:**

- Public deployed application URL
- Working deployed backend API
- Cloud PostgreSQL database

---

## Phase 9: Evaluation and Final Report Evidence

**Goal:** Collect evidence for final report and presentation.

**Tasks:**

- [ ] Test system responsiveness
- [ ] Measure average FPS or pose processing speed
- [ ] Measure backend response time for report generation
- [ ] Evaluate ML model metrics
- [ ] Conduct usability testing with 5–10 users
- [ ] Collect feedback using Google Forms
- [ ] Implement at least 3 improvements based on feedback
- [ ] Take screenshots of:
  - [ ] Deployed app
  - [ ] Database records
  - [ ] API docs
  - [ ] Reports
  - [ ] Dashboard
  - [ ] ML results

**Deliverable:**

- Evaluation section evidence
- Final report screenshots
- Improvement evidence

---

## Phase 10: UAT Remediation

**Goal:** Turn the moderated UAT backlog (`PhysioFit_UserTesting_Analysis.md`, 22
participants / 21 questionnaires) into discrete, screenshot-able fixes. Curated
high-impact scope; correctness defects first, then page-by-page UX. See the approved
plan (`users-sumhonyou-downloads-physiofit-use-idempotent-dawn.md`) for the full staged
backlog and the future-work list.

### Phase 10 — Stage R1: Squat heel-lift false positive fix (2026-07-24)

- [x] Root cause confirmed: `backend/app/module_b/squat/fault_gates.py::_heel_rise_peak_norm`
      baselined against the rep's first frame only and averaged both legs, letting the
      occluded far foot (side-view squat, far knee measured 0.59-0.78 visibility vs
      0.95-0.99 near, Stage 5.3) manufacture phantom heel-rise. Confirmed exactly as UAT's
      T8 hypothesised (3/18 sessions, incl. one "even though in good form").
- [x] Fixed by switching the gate to **near-leg-only** (camera-side leg selected per rep
      by mean heel+toe landmark visibility, `_select_near_leg`/`_leg_visibility`), a
      **settle-window median baseline** (first 3 frames) instead of frame 0, a **debounce**
      requiring the rise to be sustained across a 3-frame sliding window instead of a
      single-frame max, and an **occlusion guard** that refuses to fire at all if even the
      near leg's visibility falls below `MIN_VISIBILITY` (0.6) for the rep (fail-safe).
      Mirrors the pattern already proven correct in `module_a/wblt/geometry.py::HeelLiftDetector`.
- [x] `ml/scripts/analyze_fault_gate_thresholds.py` updated in lockstep (same near-leg
      selection, settle window, debounce constants) so the re-derived threshold matches
      what production now computes; re-run against the real REHAB24-6 dataset
      (`/Users/sumhonyou/fypDataset`), confirmed byte-identical across two runs (X8).
      `fault_heel_rise_peak_norm` in `backend/app/module_b/squat/config.py` updated
      0.08399336939375095 → **0.07098522548163665**. Validity check still KEEPs (AUC
      0.728→0.714, direction-consistency 4/5→3/5 subjects), but **specificity improved**
      0.569→0.625 in-sample (0.583→0.597 out-of-fold) at a similar sensitivity (0.885→0.846
      in-sample, 0.808 out-of-fold unchanged) — i.e. materially fewer false alarms on Good
      reps, which is the actual defect being fixed, at a small, honestly-reported precision
      cost. See `ml/reports/SQUAT_FAULT_GATE_ANALYSIS.md`.
- [x] Regression tests added/rewritten in `backend/tests/test_module_b_squat_fault_gates.py`
      (`HeelRiseGateTests` + new `NearLegSelectionTests`): sustained lift still fires,
      a single-frame spike no longer fires (the direct debounce regression proof), a noisy
      low-visibility far leg no longer contaminates a clean near leg, and a rep where even
      the near leg is occluded refuses to fire at all. Full backend suite: **329/329
      passing** (28/28 in the fault-gates file). Black + isort applied.
- [ ] Live end-to-end re-verification against a real recorded squat session (browser +
      running backend) deferred to the next working session — not yet run in this pass.

### Phase 10 — Stage R2: SLS lift-detection over-sensitivity fix (2026-07-24)

- [x] Root cause confirmed: `backend/app/module_a/sls/fsm.py::LiftHoldFSM` gated a lift
      confirmation on `SLS_LIFT_PERSIST_FRAMES = 3` **consecutive frames**, not a real
      elapsed time. Since MediaPipe runs via `requestAnimationFrame` (rate varies with
      the browser/device rather than a fixed 30fps), 3 frames could be well under 0.1s
      on a fast machine — inside normal foot jitter. Confirmed as the mechanism behind
      UAT T1/S5 ("the lifting too sensitive").
- [x] Fixed by converting both the lift-confirm and drop-confirm dwell from a frame
      count to a **real minimum elapsed time**, using the timestamp already threaded
      through `update(t, ...)`: `SLS_LIFT_MIN_DWELL_SEC = 0.15`,
      `SLS_DROP_MIN_DWELL_SEC = 0.10` (`backend/app/module_a/sls/config.py`). The FSM now
      tracks `_above_since`/`_below_since` timestamps instead of streak counters
      (`fsm.py`). Geometry thresholds (lift-line height, hysteresis margin) left
      unchanged — the defect was dwell timing, not the height/margin.
- [x] Mirrored the identical fix into the frontend live estimate
      (`frontend/src/services/sls/liveGeometry.ts::createSlsLiveTracker`,
      `frontend/src/config/moduleAThresholds.ts`) so the on-screen hold timer users see
      live matches the backend's authoritative recompute — the old frame-count constants
      were removed outright (no longer read anywhere) rather than left as dead exports.
- [x] Regression tests: `backend/tests/test_module_a_sls.py::FsmTests` rewritten for
      dwell-based timing, incl. a direct regression proof (`test_a_lift_shorter_than_the
_dwell_never_confirms`) that a lift shorter than the dwell window never starts a
      timer. New `frontend/src/services/sls/liveGeometry.test.ts` (4 tests) covers the
      same dwell/drop-dwell behaviour client-side — no prior test file existed for this
      module. Full backend suite **330/330**; frontend `tsc --noEmit` clean, full
      `vitest` suite **31/31**. Black + isort + Prettier applied.
- [x] Re-ran `python -m app.module_a.scripts.run_sls_evaluation` (the committed replay
      corpus, `backend/app/module_a/replay_corpus/sls/`) to confirm the dwell change
      doesn't regress measurement agreement: **ICC(2,1)=0.995, kappa=0.857,
      Bland-Altman bias=-0.753s, LoA=[-4.08s, 2.57s]** — byte-identical to the pre-fix
      Phase 3B baseline (`SLS_EVALUATION_REPORT.md` diff is empty).
- [ ] Live end-to-end re-verification (browser + running backend, a genuinely brief
      accidental foot-twitch vs. a real held lift) deferred to the next working session.

### Phase 10 — Stage R3: LLM coaching fallback telemetry + prompt tightening (2026-07-24)

- [x] Root cause confirmed: `backend/app/module_b/core/router.py::_build_and_save_feedback`
      already computed a precise reason whenever a rewrite wasn't used — the safety filter
      (`feedback_safety.check_llm_feedback`) returns `forbidden_phrase:X`,
      `grade_mismatch_band/score`, `invented_tag:X`, `too_long`, `markdown_formatting`,
      and the client (`llm_client.GroqClient`) returns `result.error` — but both were only
      logged, never stored, so diagnosing a template-only report required a log-file
      search per session rather than a query. `feedback_llm_enabled=False` by default
      means a _fresh_ run always falls back silently for that reason alone; UAT ran with
      it enabled (`.env` already has `FEEDBACK_LLM_ENABLED=true` + a real `LLM_API_KEY`),
      so the observed fallback was downstream of the request, in the client or the guard.
- [x] Added `fallback_reason` telemetry: new nullable `String(80)` column on
      `feedback_texts` (migration `20260724_0013`, applied against the live local
      Postgres and confirmed present via `information_schema` inspection), threaded
      through `crud.FeedbackWrite`/`save_feedback`/`feedback_summary` and set by
      `_build_and_save_feedback` to one of `none` (never attempted) / `llm_used` /
      `rate_limited` / `timeout` / `api_error` / `invalid_json` / `empty_response` /
      `guard_rejected:<safety.reason>`. Diagnostic only — no schema/frontend change
      needed to keep it out of the user-facing report: `ModuleBFeedbackResponse` doesn't
      enumerate the field, so FastAPI/Pydantic silently drops it from the HTTP response
      (verified no `extra="forbid"` anywhere on that model) while it stays queryable
      directly from the `feedback_texts` table or the structured log line.
- [x] `llm_client.py::GroqClient.rewrite_feedback` now catches `httpx.TimeoutException`
      ahead of the generic `httpx.HTTPError` handler (it's a subclass) and reports it as
      the distinct `"timeout"` reason instead of folding it into `"transport_error:..."`,
      so a slow API call is now distinguishable from a dead connection or any other
      `4xx`/`5xx` in the stored telemetry.
- [x] Tightened `_SYSTEM_PROMPT` against the two most likely structural rejection causes
      identified by reading `feedback_safety.py`'s own checks (no live API access in this
      session to confirm empirically, so this is diagnosis-by-code-reading + the new
      telemetry field for further live iteration, not a confirmed-live fix): (1) the
      model was free to restate the score as an approximate "X/10", which
      `_contradicts_score`'s ±0.05 tolerance would reject on any rounding — now
      explicitly forbidden, banded/qualitative language only; (2) the model could add
      generic technique cues that happen to echo an untriggered gate's tag/message text,
      which `_find_invented_tag` would reject — now explicitly told to give only general
      encouragement when no tags are present and never introduce a cue beyond the given
      tags.
- [x] English-only rewrite kept as-is per HY's call — no locale routing added; non-English
      sessions continue to get the localised template. Documented here as the known,
      deliberate limitation for this stage (multi-language LLM output is future work).
- [x] Regression tests: `test_module_b_llm_client.py` updated for the new `"timeout"`
      label plus a new `test_connection_error_is_reported_as_transport_error` proving
      non-timeout transport errors are unaffected. New
      `FallbackReasonTelemetryTests` in `test_module_b_feedback_persistence.py` (5 tests)
      cover all five `fallback_reason` outcomes end-to-end through
      `_build_and_save_feedback`, including a guard-rejection case
      (`guard_rejected:grade_mismatch_band`). Full backend suite: **336/336 passing**.
      Black + isort applied.
- [ ] Live verification against the real Groq API (confirm the tightened prompt actually
      reduces `guard_rejected` fallbacks vs. the UAT-era prompt) deferred to the next
      working session — this stage shipped the diagnostic capability and a
      code-reasoned fix, not yet a live-confirmed reduction in fallback rate.

### Phase 10 — Stage R4: Live-feedback redesign — squat portion (2026-07-24, in progress)

**Scope note:** R4 is a cross-cutting stage across all four live-session pages
(STS/SLS/WBLT/squat). This entry covers **squat only**; STS/SLS/WBLT are not yet
touched. HY additionally specified mid-stage that the corrective-cue pop-out's
background should be a translucent colour wash (can see the webcam feed and HUD rep
count through it), not opaque like the existing start-countdown overlays — folded into
the design below.

- [x] **Discovered and fixed a drift bug from Stage R1** while building this stage:
      `frontend/src/utils/squat/squatFaultGates.ts`'s `createHeelRiseTracker` (the
      client-side live mirror of the backend heel-lift gate) was still on the OLD
      bilateral/first-frame construction — R1 only updated the backend. Rewrote it to
      the same near-leg-selection/settle-window/debounce construction as the backend
      (buffers small per-frame numeric arrays for both legs, decides the near leg by
      mean visibility only once at `result()` time, since the live path can't know the
      whole-rep visibility average until the rep ends). Also fixed a pre-existing,
      unrelated constant drift found in the same file: its local `MIN_VISIBILITY`
      claimed to mirror the backend's `0.6` but was hardcoded `0.5` — now imports
      `LIVE_MIN_VISIBILITY` (already correctly `0.6`) instead of duplicating it. Also
      updated the stale fallback threshold in `squatLiveEstimate.ts`
      (`FALLBACK_SQUAT_LIVE_CONFIG.faultGates.faultHeelRisePeakNorm`:
      `0.08399336939375095` → `0.07098522548163665`, matching R1's re-derived value).
      `src/test/squatFaultGates.test.ts` rewritten (14 tests): sustained lift fires,
      single-frame spike doesn't, near-leg selection ignores a noisy far leg, an
      occluded near leg refuses to fire.
- [x] Built a new shared `frontend/src/components/LiveCueOverlay.tsx` — a full-viewport
      portal (same take-over pattern as `StartHoldCountdown`/`StartSetCountdown`, z-index 500) but with a **translucent tone-coloured background**
      (`color-mix(in srgb, var(--coral) 30%, transparent)` for `warn`, similar for
      `good`/`neutral`) instead of their opaque `background: var(--bg)`, so the camera
      feed and the HUD's rep counter stay visible through it — HY's explicit mid-stage
      request. Giant title text (`clamp(2.6rem, 7vw, 4.5rem)`), optional detail line, a
      10s auto-dismiss countdown ring (SVG, same technique as `AutoStartCountdown`),
      and a manual dismiss button. `pointer-events: none` on the backdrop (only the
      dismiss button is clickable) so it can never block interaction with anything
      underneath even while showing.
- [x] Wired into `SquatLiveSessionPage.tsx`: on `repJustRejected`, the primary failed
      gate drives the big pop-out title (`squat.cueInsufficientDepth` = "Go deeper",
      `cueExcessiveForwardLean` = "Chest up", `cueHeelLift` = "Heels down" — corrective
      wording, not descriptive, per the plan); any additional failed gates for the same
      rep are named in the smaller detail line. Throttled to at most one cue at a time
      by construction (single `liveCue` state, replaced not queued — a new rejection
      just restarts the overlay's own countdown). Cleared on `startSet`/`finishSet`.
      i18n added to en/zh/ms.
- [x] Enlarged the always-visible live-feedback text for distance readability (Q9 =
      3.38/5, the lowest-scoring UAT item): `.hud-card .hv` (HUD timer/rep numbers)
      2.4rem → `clamp(2.4rem, 3.6vw, 2.9rem)`; `.live-feedback-title` (squat) 1.4rem →
      `clamp(1.4rem, 2.6vw, 1.85rem)`; `.live-band` (STS) 1.45rem →
      `clamp(1.45rem, 2.6vw, 1.9rem)`; `.sls-live-status-text` (SLS) 1.55rem →
      `clamp(1.55rem, 2.8vw, 2rem)` — all four pages' persistent panels bumped even
      though only squat has the new pop-out wired in yet.
- [x] Verification: `tsc --noEmit` clean; full frontend `vitest` **32/32**. Visual
      verification of the new overlay's translucency, legibility, and full-page
      takeover done by injecting its exact markup/classes into running pages in both
      light and dark theme and at mobile width (375px) — confirmed real UI content
      (a skeleton figure illustration, a "Knee ROM · Good" pill, a capture-quality
      badge) stays clearly visible through the colour wash behind the giant title text
      in both themes.
- [ ] **Not yet done, deferred:** a real end-to-end check (an actual rejected squat rep
      in front of a real webcam, triggering the overlay live) — the sandboxed preview
      browser used for this session blocks camera permission outright ("Camera
      permission denied"), so this needs HY's own machine. Also not yet done: STS, SLS,
      WBLT corrective-cue wiring (plan items 2/5 — glanceable rep-progress ring,
      surfacing the font-size control in-session) for any exercise; this entry is the
      squat slice only.

**Refinements after HY reviewed a screenshot of the first pass (2026-07-24, same day):**

- [x] Backdrop opacity dropped from tone-tinted 30%/26% to a uniform, much lighter
      `color-mix(in srgb, var(--bg) 10%, transparent)` across all three tones — same
      base colour the sidebar itself already uses for its own translucent background
      (`.side`), just far lighter, so the wash barely tints the feed at all. Tone
      (`warn`/`good`) now only colours the icon, not the backdrop.
- [x] Added a genuine reject sound: `wrongRepAudio` (new
      `assets/sound effect/Wrong sound effect.mp3` ref, same pattern as the existing
      `goodRepAudio`) now plays on `repJustRejected` — previously deliberately silent
      ("no success chime"); HY asked for an actual wrong-buzzer instead.
- [x] Cue copy restructured into a real headline/subheading pair instead of
      title-plus-other-gates-list: `LiveCueOverlay`'s `detail` prop renamed to
      `subheading` (grouped with the title in a new `.live-cue-copy` flex column, tight
      6px gap, clearly smaller font) and now always carries the SPECIFIC reason behind
      the primary cue rather than an optional list of the rep's other failed gates
      (which stays covered by the persistent sidebar panel instead): "Go deeper" / "Aim
      for at least {{deg}}° knee bend" (interpolated live from
      `liveConfig.faultGates.minKneeFlexPeakDeg`, never hardcoded), "Chest up" /
      "Leaning too far forward", "Heels down" / "You're lifting your heels up". New
      `squat.cue*Detail` i18n keys added to en/zh/ms.
- [x] Re-verified: `tsc --noEmit` clean, full `vitest` **32/32**, and the updated markup
      re-injected into a live dashboard page to visually confirm the much lighter,
      neutral-toned wash and the new headline/subheading grouping.

**Further refinements after HY tried the first pass live (screenshot attached, 2026-07-24,
same day):**

- [x] Overlay colours now reuse the persistent live-feedback panel's own state colours
      exactly instead of an invented wash: `--warn-bg`/`--good-bg`/`--surface`
      background (the same `.live-feedback-panel.rejected`/`.counted`/`.idle`
      backgrounds — `--warn-bg` is literally `rgba(245, 183, 49, 0.14)` light /
      `0.16` dark, HY's own quoted values), a real `2px solid` full-page border in the
      matching state colour (`--amber`/`--good`/`--border`), and the icon copied
      exactly (`.live-feedback-icon`'s 40px solid-colour circle + `--on-accent`
      glyph, not the previous white circle + coloured glyph).
- [x] Added a genuine "wrong" sound: `wrongRepAudio` plays
      `assets/sound effect/Wrong sound effect.mp3` on `repJustRejected` (previously
      silent by design — "no success chime"; HY asked for an actual buzzer).
- [x] Cue copy restructured into title + specific subheading (renamed `detail` prop to
      `subheading`, grouped in a new `.live-cue-copy` flex column): "Go deeper" / "Aim
      for at least {{deg}}° knee bend" (still interpolated live from
      `liveConfig.faultGates.minKneeFlexPeakDeg`), "Chest up" / "Leaning too far
      forward", "Heels down" / "You're lifting your heels up" — replacing the previous
      "other failed gates" list (which stays covered by the sidebar panel).
- [x] Simplified the "Live angles" panel from a graphical gauge bar + zone ticks + two
      stacked metric cards + a peak-so-far sentence + a trunk-lean-peak sentence, down
      to one compact `.live-angle-row` of four minimal label:value stats (Knee depth,
      Peak, Trunk lean, Last rep depth) that wraps gracefully instead of scrolling — so
      the whole live squat page (camera + HUD + feedback + angles) fits without
      scrolling, per HY's request. Removed the now-dead `.depth-gauge-head/-value/
-peak-note/-track/-zone*/-marker/-ticks*` CSS and the `depthGaugePct` import
      (kept the exported utility itself in `squatLiveEstimate.ts` since it's harmless
      and may be reused); kept `.depth-gauge-zone-chip` (still used) and
      `.knee-metrics`/`.knee-metric-card`/`.knee-metric-label` (still used by STS,
      untouched). Retired i18n keys `repPeakSoFar`→`repPeakLabel` (short "Peak" label)
      and dropped the now-unused `lastRepTrunkLean` key, in en/zh/ms.
- [x] Re-verified: `tsc --noEmit` clean, full `vitest` **32/32**; both changes
      re-checked visually via injected markup (amber border/icon/background confirmed
      against a real panel; the compact stat row confirmed to read as effectively one
      line at the sidebar column's real width, wrapping gracefully rather than forcing
      scroll on narrower widths).

**Third round of refinements after HY tried the second pass live (screenshots
attached, 2026-07-24, same day):**

- [x] The pop-out now auto-closes on `repJustCompleted`, not just its own 10s timer or
      manual dismiss — a good rep clears `liveCue` immediately, so a stale "Go deeper"
      from an earlier rejected rep can no longer linger on screen after the user has
      already corrected and completed a valid one.
- [x] Backdrop opacity is now a single tunable knob: `--live-cue-bg-alpha` (currently
      `80%`) declared once on `.live-cue-overlay`, consumed by all three tone
      backgrounds via `color-mix(in srgb, <hue> var(--live-cue-bg-alpha), transparent)`
      — raised from the previous `--warn-bg`/`--good-bg` (fixed ~14-16%, shared with
      the sidebar panel so deliberately not reused for this). **Where to tune further:
      `frontend/src/index.css`, the `--live-cue-bg-alpha` declaration inside
      `.live-cue-overlay`** — one line controls the wash strength for every tone and
      every exercise page that uses this component.
      **Contrast heads-up (found while re-verifying, not asked for but worth flagging):**
      title/subheading colour is still `var(--text)`, which is dark in light theme
      (crisp against the 80% amber -- matches HY's own screenshots) but goes
      near-white in dark theme, so it reads noticeably softer against the same bright
      amber wash there. Left as-is since HY is tuning this by feel; if dark theme needs
      fixing too, the fix is forcing `.live-cue-title`/`.live-cue-subheading` to
      `var(--on-accent)` for the `warn`/`good` tones specifically (same pattern already
      used for `.live-cue-icon`).
- [x] Removed the "Live status" panel entirely once recording starts (it now only
      renders during `stage === "setup"` for the target picker + Start Set button).
      Its recording-stage contents relocated: **Finish Set** moved into the topbar
      beside Cancel (`topbar-actions`, shown only while `stage === "recording"`); the
      **progress bar** moved inside the Reps HUD card itself, below the big number
      (new slim `.hud-progress` modifier on the existing `.track`, only shown with a
      target set). The attempts-summary text and "finish whenever ready" caption were
      dropped rather than relocated (the sidebar's "that rep didn't count" panel
      already covers the rejection info); their now-orphaned i18n keys
      (`attemptsSummary`, `finishWhenReady`, `finishWhenReadyTargeted`) removed from
      en/zh/ms.
- [x] `.live-cue-icon` circle enlarged `40px → 68px` (the 40px glyph no longer fits a
      40px circle); the glyph itself sized down to `34px` in `LiveCueOverlay.tsx` so it
      now sits with comfortable padding inside the larger circle.
- [x] Re-verified: `tsc --noEmit` clean, full `vitest` **32/32**; visually re-checked
      the 80%-opaque warn overlay with the enlarged icon in both dark and light theme
      (confirming the contrast note above), matching HY's own screenshots in light
      theme closely.

### Phase 10 — Stage R4: Live-feedback redesign — SLS + STS portion (2026-07-24)

Rolled `LiveCueOverlay` out to the two remaining live pages, plus a new signal HY
flagged from live testing: SLS users aren't told when they lift the **wrong** leg.

- [x] **New: wrong-leg-lift detection** in
      `frontend/src/services/sls/liveGeometry.ts`'s `createSlsLiveTracker()`. The
      tracker already tracked the _target_ leg's ankle against a calibrated
      lift-line; it now also averages the **stance** ankle's baseline during the
      same calibration window and places an identical lift-line above it
      (`wrongLegLineY = baselineStanceAnkleY - SLS_LIFT_LINE_NORM * legLen`). Each
      frame (while `phase !== "stopped"`) checks whether the stance ankle has
      crossed _its own_ line, debounced with the same `SLS_LIFT_MIN_DWELL_SEC` /
      `SLS_DROP_MIN_DWELL_SEC` dwell constants already used for the real lift/drop
      detection (Stage R2) — so a single noisy frame can't flip it either direction.
      Exposed as a new `wrongLegLifted: boolean` field on `SlsLiveUpdate`. Purely a
      display-only client signal (X7: mirrors the "helper only" convention already
      documented at the top of this file) — never sent to the backend, never
      affects the hold timer, combo score, or the official persisted result.
- [x] Wired into `SlsLiveSessionPage.tsx`: edge-triggered (a ref tracks the previous
      frame's `wrongLegLifted` so the sound/cue fire once per lift, not every
      frame, matching the rep-boundary pattern squat/STS use). Rising edge plays
      the existing "Wrong sound effect.mp3" and shows `LiveCueOverlay` with title
      `sls.cueWrongLeg` ("Wrong leg!") and subheading `sls.cueWrongLegDetail`
      ("Keep your {{leg}} on the ground"), `{{leg}}` interpolated from the actual
      stance leg (`sls.legRight`/`sls.legLeft`, lower-cased) so it always names the
      leg that should stay planted for _this_ attempt — never a generic message.
      Falling edge (user self-corrects) clears the cue immediately, same as squat's
      auto-close-on-good-rep. State reset in `startHold()` alongside the tracker.
- [x] Wired `LiveCueOverlay` into `StsLiveSessionPage.tsx` too, reusing the
      existing `InvalidReasonCode` → i18n mapping (`reasonCodeToI18nKey`) that
      already drove the old `liveReasonGuess` timeout-banner — the persistent
      banner is kept as-is (still useful sitting in the panel), `LiveCueOverlay` is
      now shown _alongside_ it as the big glanceable pop-out, and both clear
      together on the next valid rep (`response.metrics.rep_count >
validRepsRef.current`). No subheading (STS's existing reason strings are
      already short/specific enough to stand alone as titles) and no new i18n keys
      needed — this stage only added the plumbing.
- [x] New i18n keys `sls.cueWrongLeg` / `sls.cueWrongLegDetail` added to en/zh/ms.
- [x] New vitest coverage in `liveGeometry.test.ts`
      (`createSlsLiveTracker wrong-leg-lift detection`, 4 cases): a stance-leg rise
      shorter than the dwell window doesn't flag; a sustained one does; it clears
      after a sustained return below the line; and — the case most likely to
      regress silently — a _correct_ target-leg lift never trips `wrongLegLifted`.
- [x] Verified: `tsc --noEmit` clean; full `vitest` **36/36**; Prettier clean;
      visually re-checked the SLS wrong-leg cue's exact copy/typography via the
      same injected-markup technique used for squat (real webcam access stays
      blocked in the sandboxed Browser pane) — renders identically to the squat
      overlay's amber warn treatment, just with the new copy.
- [ ] Still outstanding: WBLT has not had `LiveCueOverlay` wired in at all (no
      rejected-attempt concept currently surfaced live for it — would need its own
      design pass, not just a copy of this pattern). Live end-to-end verification
      with a real webcam (including the wrong-leg cue specifically) remains on HY's
      own machine, as with every other R4 stage so far.

### Phase 10 — Stage R5: One uniform start protocol + unmistakable RECORDING state (2026-07-24)

Start was non-uniform across the 4 live pages (STS auto-recorded on mount with **no**
countdown at all; squat/SLS used a button + 5s countdown; WBLT was auto-gated + a 10s
countdown) — the single most under-reported UAT issue (12/18 sessions). Also, no page
had an actually-unmistakable "you are being recorded right now" signal.

- [x] **New shared `RecordingBadge`** (`components/RecordingBadge.tsx`): a small red
      pulsing-dot pill ("Recording") rendered inside `.cam-stage` during the real
      recording stage, paired with a new `.cam-stage--recording` CSS modifier (red
      border glow) on the surrounding stage. Positioned **top-centre** deliberately —
      `.q-badge` (capture quality) already owns top-left on every page, and WBLT's
      recording HUD also uses top-right (heel-down + angle cards), so centre is the
      only corner guaranteed clear everywhere. `index.css`: `.recording-badge`,
      `.recording-badge-dot` (`recording-pulse` keyframe), `.cam-stage--recording`.
- [x] **New synthesized recording-start tone** (`utils/recordingTone.ts`,
      `playRecordingStartTone()`): a short Web Audio oscillator beep (880Hz, ~0.3s),
      not a bundled asset — no exercise-specific "recording started" clip has been
      supplied (X7), so this has no file dependency. Fires once, exactly when a page
      transitions into its recording stage. Together with the badge + border this is
      the "red dot + border + audio tone" unmistakable-state requirement.
- [x] **Standardised every countdown to 5 seconds:**
  - `pages/CameraSetup.tsx`: `AUTO_START_STABLE_MS` `1800 → 5000`.
  - `pages/wblt/WbltLiveSessionPage.tsx`: `WBLT_GET_READY_DURATION_SEC` `10 → 5`
    (its separate `WBLT_POSITION_STABLE_MS` framing-stability gate and the
    `WBLT_RECORDING_DURATION_SEC` hold duration are untouched — different
    mechanics, not start countdowns).
  - Squat (`COUNTDOWN_START_SEC`) and SLS (`COUNTDOWN_START_SEC`) were already 5s —
    no change needed there.
- [x] **New: gave STS the countdown it lacked entirely.** Built a generic
      `components/GetReadyCountdown.tsx` — reuses the existing shared
      `.countdown-overlay` CSS/portal pattern already proven by
      `squat/StartSetCountdown`, `sls/StartHoldCountdown`, `wblt/WbltGetReadyCountdown`
      (all three stay as their own thin, exercise-specific wrappers; per the plan's
      "unify, don't add a 5th variant", STS renders the generic component directly
      instead of a new near-duplicate `StsGetReadyCountdown`). `StsLiveSessionPage.tsx`
      restructured: new `stage: "countdown" | "recording"` state (was previously
      recording unconditionally from mount); the recorder-start effect, frame/rep-FSM
      effect, and the session timer effect are now all gated on `stage === "recording"`;
      a new `startRecording()` starts the recorder, fires the tone, and flips the stage
      once the 5s countdown reaches zero.
  - **Bug found and fixed in passing:** the STS topbar had a permanently-visible
    green pill reading "Recording" (`t("live.paused")` — the i18n key name and its
    text had drifted apart at some point) regardless of whether recording had
    actually started. Removed it outright now that the real `RecordingBadge` gives
    an accurate, stage-aware signal; the orphaned `live.paused` key removed from
    en/zh/ms and replaced with `live.recordingBadge`/`live.getReadyCaption`.
- [x] `RecordingBadge` + `.cam-stage--recording` + `playRecordingStartTone()` wired
      into all 4 pages: squat (`startSet()`), SLS (`startHold()`), WBLT
      (`startHold()`, the calibrating→recording transition), STS (new
      `startRecording()`).
- [x] Verified: `tsc --noEmit` clean; full `vitest` **36/36**; Prettier clean;
      visually checked the badge/border/countdown markup in the browser via the same
      injected-markup technique used for R4 (real webcam stays blocked in the
      sandboxed Browser pane) — badge sits clear of the quality badge and WBLT's
      corner HUD cards, border glow reads clearly, countdown matches the existing
      squat/SLS/WBLT countdown styling exactly (shared CSS, no visual drift).
- [ ] Still outstanding: live end-to-end verification with a real webcam on all 4
      pages (confirming the 5s countdowns actually fire in sequence, the tone plays
      audibly, and STS's new gated recording doesn't drop any frames at the
      countdown→recording boundary) remains on HY's own machine, as with every prior
      stage. The plan's R5 scope stops at start-protocol/RECORDING-state — the
      "instructions ack → camera check" steps upstream of this page are R9's scope,
      not this stage's.

### Phase 10 — Stage R6: Audio / TTS live cues (2026-07-24)

Most-requested new feature in UAT (5 sessions + 5 comments, including both 45+
testers) — dissolves the reading-distance problem R4 addressed visually, this time
by voice, and doubles as an accessibility win.

- [x] **New `utils/speechCueQueue.ts` (`SpeechCueQueue`)** — a framework-free
      priority queue with no dependency on `speechSynthesis` (that API doesn't exist
      under vitest), so all queue/priority/throttle logic is fully unit-testable via
      an injected `SpeechCueSpeaker` interface. Two categories: `"session"`
      (start/end/leg-transition — never throttled, **interrupts** anything currently
      speaking/queued so it's never delayed or dropped) and `"fault"` (queued +
      spoken **sequentially** via onDone-chaining, throttled per-KEY only —
      `faultThrottleMs` default 4s — so a _different_ fault key is never suppressed
      by another key's throttle). **HY's scope call: no "count" category exists at
      all** — the original plan's rep-number readout was dropped; the queue's type
      system only has `"session" | "fault"`.
- [x] **New `test/speechCueQueue.test.ts`** — 12 cases via a mock speaker: two/three
      simultaneous distinct-key faults are all spoken in order (the "multiple faults
      → all announced" requirement); per-key throttle suppresses a repeat inside the
      window and allows it after; a session cue cancels in-progress speech and drops
      anything still queued; the aborted utterance's `onDone` never double-pumps the
      queue; mute (`setEnabled(false)`) clears the queue and further `enqueue()`
      calls are no-ops until re-enabled.
- [x] **New `hooks/useSpeechCues.ts`** — the real `speechSynthesis`-backed
      `SpeechCueSpeaker`. `utterance.lang` is set from the current UI language
      (en→en-US, zh→zh-CN, ms→ms-MY; HY's call: best-effort, no locale
      validation/routing — falls back to whatever voice the OS/browser provides).
      **Design fix found while wiring this in:** the queue must NOT be cleared on
      component unmount — every live page navigates away immediately after its
      "session complete" cue fires (`finish → sessionService.end() → nav`), so an
      unmount-triggered `clear()` would cut that announcement off before it's ever
      heard. `speechSynthesis` is a browser-global queue independent of the React
      tree, so letting it finish across the navigation matches how the existing rep
      sound effects already behave (nothing pauses them on unmount either). An
      **abandoned** session must still stop speech immediately, though — that's the
      hook's `stop()`, called explicitly from each page's `handleCancel`, not left to
      unmount timing.
- [x] **New `preferences.tsx` flag: `audioCues`** (localStorage
      `physiofit-audio-cues`), same pattern as `theme`/`fontScale`. **Defaults to ON**
      (HY's call) — it's the reading-distance fix the feature exists for, so it
      should be heard immediately rather than requiring discovery of a toggle.
- [x] **New `components/AudioCueToggle.tsx`** + two new icons (`Volume2`, `VolumeX`
      in `Icons.tsx`) — dropped into the shared `DashTopbar`
      (`layouts/DashboardLayout.tsx`, beside `ThemeToggle`, for out-of-session
      discoverability) **and** every live page's own topbar (all 4 build their own
      topbar markup, not `DashTopbar`).
- [x] **Wired into all 4 live pages** (`speech.speakSession(...)` /
      `speech.speakFault(...)` / `speech.stop()`):
  - **Squat**: `speakSession` on `startSet()`; **HY's note: every failed gate is
    spoken, not just the primary one** — the visual `LiveCueOverlay` still shows
    only the primary reason (unchanged, R4's design), but a rep that trips two gates
    at once now has **both** read aloud in the same fixed priority order
    (depth→lean→heel); `speakSession` on a successful `finishSet()`; `speech.stop()`
    in `handleCancel`.
  - **SLS**: `speakSession` on `startHold()` announcing which leg
    (`sls.legPromptRight`/`Left` — reuses the exact on-screen prompt text so spoken
    and visual instructions can't drift apart); **`wrongLegLifted` (the R4 signal
    from HY's earlier note) now speaks too** (`sls.cueWrongLeg`, key `"wrong_leg"`),
    alongside the existing visual `LiveCueOverlay` and sound effect; `speakSession`
    on session end (after the last leg's support self-report is submitted).
  - **STS**: `speakSession` in the new `startRecording()` (R5's get-ready countdown
    completing); every `reasonCode` rejection speaks (`speech.speakFault` reusing
    the same `reasonText` already shown); `speakSession` on the persisted/complete
    response, before navigating to the report.
  - **WBLT**: `speakSession` in `startHold()` (the calibrating→recording moment)
    reusing the on-screen `wblt.lungeNow` text; a confirmed heel-lift now speaks
    (`wblt.heelLifted`) — no edge-detection needed here since the attempt ends
    immediately after, so it only ever fires once; `speakSession` on session end in
    `endSessionAndNavigate()`.
  - All 4: `speech.stop()` added to `handleCancel` so an abandoned session never
    keeps talking after the user has navigated away.
- [x] New i18n: `live.speakStarting` / `live.speakSessionComplete` (shared session
      cues) and `nav.audioCuesOn` / `nav.audioCuesOff` (toggle label), en/zh/ms. No
      other new strings needed — every fault cue reuses text that already existed
      for the R4 visual cues, by design (single source of truth, can't drift).
- [x] Verified: `tsc --noEmit` clean; full `vitest` **48/48** (12 new); Prettier
      clean; `AudioCueToggle`'s two icon states checked visually in the browser next
      to the existing `ThemeToggle` (same `.ctrl.icon-btn` styling, no visual
      inconsistency).
- [ ] **Known limitation (documented, not fixed):** ms-MY voice availability varies
      a lot by OS/browser — where it's missing, the platform silently falls back to
      its default voice or no-ops. Same spirit as R3's English-only LLM deferral.
- [ ] Still outstanding: actually **hearing** the spoken cues (correct text, correct
      language, correct sequencing of simultaneous faults, audible tone/timing) is
      the one thing this sandbox cannot verify at all — no audio output here, a
      harder limitation than even the blocked webcam. This is a live check on HY's
      own machine for all 4 exercises, with particular attention to the two-fault
      squat case and the ms-MY voice availability question above.

### Phase 10 — Stage R6 follow-up: fixed "no audio at all" bug (2026-07-24, same day)

HY reported hearing nothing at all after testing live. Root cause found on code
review, not a live-testing artefact:

- [x] **Root cause:** `SpeechCueQueue.enqueue()`'s `"session"` branch called
      `speaker.cancel()` unconditionally, immediately followed by `pump()` →
      `speaker.speak()` in the **same synchronous tick** — even when nothing was
      speaking yet. Since every single page speaks a `"session"` cue as the very
      first thing in a fresh session (`speakSession("..._start", ...)`), this fired
      on literally every session's first cue. Calling `speechSynthesis.speak()`
      immediately after `speechSynthesis.cancel()` in the same task is a
      well-documented Chromium bug: the new utterance either silently never starts,
      or (confirmed by direct reproduction below) starts and then hangs forever —
      `onstart` fires, `onend` never does, and the synth stays stuck reporting
      `speaking: true` indefinitely, which blocks every later queued utterance too.
- [x] **Empirically reproduced in the Browser pane**, not just reasoned about:
      calling `cancel()` then `speak()` in the same tick → `{started: true, ended:
false, speaking: true}` (hung forever); deferring the same `speak()` by a
      single tick (`setTimeout(..., 0)`) → `{started: true, ended: true, speaking:
false}` (completes normally). Direct confirmation the diagnosis was right, not
      a guess.
- [x] **Fix, `utils/speechCueQueue.ts`:** the `"session"` branch now only calls
      `cancel()` when something is genuinely active (`this.speaking ||
this.queue.length > 0`) — the common "fresh queue, nothing speaking yet" case
      (every session's opening cue) now speaks directly with no cancel() at all, so
      it can never hit this bug. For the rarer genuine-interrupt case (a session cue
      arriving while a fault is still being read), the follow-up `pump()` is now
      deferred through a new injectable `scheduleAfterCancel` option — defaults to
      synchronous execution (keeps every existing test deterministic), and
      `hooks/useSpeechCues.ts` supplies the real `(fn) => setTimeout(fn, 0)` so the
      cancel has a tick to actually settle before the next `speak()` in real
      browsers.
- [x] **Second, independent defensive fix** in the real speaker
      (`useSpeechCues.ts`): calls `synth.resume()` before `synth.speak()` if
      `synth.paused` — a separate, also commonly-cited Chrome quirk where the synth
      gets stuck paused (e.g. after a backgrounded tab) and silently never starts
      newly queued speech until resumed. Harmless no-op when not actually paused.
- [x] **2 new regression tests** in `speechCueQueue.test.ts`: a session cue with
      nothing active never calls `cancel()`; a genuine interrupt defers the
      follow-up speak through `scheduleAfterCancel` and only actually speaks once
      that deferred callback runs.
- [x] Verified: `tsc --noEmit` clean; full `vitest` **50/50** (2 new); Prettier
      clean; the buggy-vs-fixed pattern reproduced live in the Browser pane as
      described above.
- [ ] **Separately noted, not a code bug:** the sandboxed Browser pane itself has
      **zero TTS voices installed** (`speechSynthesis.getVoices().length === 0`), so
      even with this fix, audible verification here is structurally impossible —
      distinct from the hang bug just fixed. HY's own machine (which does have
      system voices) is needed to confirm cues are now actually audible.

### Phase 10 — Stage R6 follow-up #2: the ACTUAL "no audio" cause — user-activation gate (2026-07-24, same day)

HY reported still hearing nothing after follow-up #1. On deeper review the earlier
fix was aimed at the wrong thing:

- [x] **Re-diagnosis (with voices actually present this time):** the "zero voices"
      reading in follow-up #1 was itself a **timing artefact** — `getVoices()`
      returns `[]` until the async `voiceschanged` event fires, then populates (the
      sandbox actually has 180 voices once loaded). Re-testing the two previously
      "fixed" failure modes **with voices loaded** showed **both work fine**:
      lang-only speak → start/end OK; cancel-then-speak-same-tick → start/end OK. So
      neither the cancel/speak fix nor voice-selection was the cause of HY's total
      silence on a machine that has voices. (Those fixes are still correct and kept —
      they matter on the voices-not-yet-loaded window and on non-macOS platforms —
      just not the culprit here.)
- [x] **Actual cause — user activation.** Grep of every `speakSession`/`speakFault`
      call site confirmed **not one cue is ever spoken from inside a user gesture**:
      session-start from a countdown `setInterval`, faults from the per-frame
      MediaPipe callback, session-end from an async finish handler. STS is the worst
      case — it auto-counts-down on mount, so there's never even a click on the page
      before its first cue. Chrome gates `speechSynthesis.speak()` on user
      activation; if a page never calls speak() during/just after a real gesture it
      can silently produce **no audio at all**. This is exactly the class of bug that
      _works in an automated sandbox_ (automation bypasses the gate — which is why it
      could not be reproduced here) but fails in a real browser.
- [x] **Fix — new `utils/speech.ts`, three layers:** (1) `primeSpeechSynthesis()`
      installed as a one-shot `pointerdown`/`keydown` listener at module load —
      speaks a silent (volume-0) utterance on the **first user interaction anywhere
      in the app**, establishing activation app-wide before any session's timer-cue
      fires, regardless of which page reaches a cue first (covers STS's no-click
      case). **Verified firing end-to-end in the bundled app:** dispatching a
      `pointerdown` triggers `speechSynthesis.speak(" ")` at volume 0 from within the
      gesture handler. (2) `pickVoice()` selects a **concrete** `SpeechSynthesisVoice`
      by language (exact tag, else base language) instead of relying on
      `utterance.lang` alone, with the voice list warmed + refreshed on
      `voiceschanged` — closes the voices-not-loaded silent window. (3)
      `speakOnce()` used by the audio toggle.
- [x] **`AudioCueToggle` now speaks a confirmation when switched ON** ("Voice cues
      on", via `speakOnce`, in the current UI language) — double duty: an **in-gesture
      audible self-test** (if HY hears it, TTS + activation both work on their
      machine; if not, the problem is system voices / OS, not the app), and it primes
      activation from a real click.
- [x] `useSpeechCues.ts` refactored to use the shared `toBcp47` + `pickVoice`;
      `LANG_BCP47` map moved into `utils/speech.ts` (single source).
- [x] Verified: `tsc --noEmit` clean; full `vitest` **50/50**; Prettier clean;
      global-prime path and concrete-voice speak both exercised live in the Browser
      pane (start→end confirmed with the "Samantha" en-US voice once voices loaded).
- [ ] **Definitive next step is HY's, and it is now a clean binary:** click the audio
      toggle (speaker icon in any live page's topbar, or the dashboard topbar) to turn
      cues **on** → if you hear "Voice cues on", audio works and the session cues will
      now fire too (global prime already established activation); if you hear nothing
      even then, the issue is your system TTS voices / OS audio, which no app change
      can fix. Report which, and note that a **hard reload** may be needed so the dev
      server serves the new `utils/speech.ts`.

### Phase 10 — Stage R6 follow-up #3: the REAL cause was a wedged Chrome speech engine (2026-07-24, same day)

HY's diagnostic decisively settled this. Console diagnostic showed `voices: 214` and
clicking "speak" produced `event: ERROR: canceled` — a real voice was selected, so
neither of the two previous fixes (cancel/speak race, user-activation) were ever the
cause; both were fixing non-problems. **HY's own key observation cracked it: "it
worked the first time... but only for sit-to-stand,"** and — decisively — **quitting
Chrome entirely (⌘Q, not just reload) made it start speaking again; a page reload
alone had NOT fixed it.**

- [x] **Root cause, confirmed empirically, not guessed:** Chrome's speech engine can
      wedge at the **browser-process** level (a well-documented, long-standing
      Chromium bug) — `speak()` returns normally, no error fires, but the utterance
      silently never starts, and it stays wedged across page reloads/navigations
      until the browser process itself restarts. STS is the only live page whose
      first cue fires almost immediately (~5s post-mount, no button); squat/SLS/WBLT
      don't speak until 30s+ into the session (target-picking, positioning, get-ready,
      calibration all precede their first cue) — long enough to hit the wedge. That
      is why STS "worked" and the other three didn't: nothing page-specific in the
      code, purely a timing coincidence with when the engine happened to still be
      alive.
- [x] **Fix, `hooks/useSpeechCues.ts`:** the real speaker now has a **start
      watchdog** — every `speak()` call arms a 1.5s timer; if `onstart` hasn't fired
      by then (engine wedged, utterance never began), it performs one
      `cancel()+resume()+re-speak` recovery attempt on a fresh tick, and if THAT also
      never starts, gives up cleanly (calls `onDone()` so the queue is never left
      stalled waiting on an utterance that will never report back — a stuck queue
      would otherwise block every future cue too, compounding the original symptom).
      `resume()` is now called unconditionally before every `speak()` (not just when
      already observed `paused`), since a wedged engine's `.paused` flag isn't a
      reliable signal.
- [x] **Honest limitation, not oversold:** this is a mitigation, not a guaranteed
      cure — a page cannot force-reset a truly wedged BROWSER PROCESS the way
      quitting Chrome does; the watchdog's cancel+retry recovers some wedge states
      (worth having) but not all of them. The demo-day mitigation that HY's own test
      proved reliable: **restart the browser**, not just reload the page, if cues go
      silent mid-testing-session.
- [x] Verified: `tsc --noEmit` clean; full `vitest` **50/50** (unchanged --
      the watchdog only touches the real speaker, not the pure/testable
      `SpeechCueQueue`); Prettier clean; app loads with zero console errors in the
      Browser pane.
- [ ] Still outstanding: HY to confirm live that squat/SLS/WBLT now speak reliably
      across a full real session (not just the diagnostic click), including after the
      engine has had time to potentially wedge again naturally.

### Phase 10 — Stage R7: exercise demo media in the live camera stage (2026-07-24)

- [x] **Goal (HY's request):** a small looping reference clip/photo of correct form,
      pinned to the top-right corner of the live camera stage on all four live
      session pages, so the user has something to check their form against without
      leaving the page.
- [x] Built `components/ExerciseDemoOverlay.tsx` — a `kind: "squat" | "sts" | "sls" |
    "wblt"` prop selects the media: squat/STS render their looping `.gif`, WBLT
      renders its looping `.mp4` (`autoPlay loop muted playsInline`), SLS renders the
      static reference photo (`Single Leg Stance pic.png` — a still, not a loop, per
      the source asset HY pointed at).
- [x] CSS (`index.css`): `.demo-overlay` — `position: absolute; top:16px; right:16px;
    z-index:3` inside `.cam-stage` (already `position: relative`), 150px wide,
      rounded corners, translucent blurred backdrop matching `.q-badge`'s existing
      look (same corner treatment, opposite side — badge is top-left, this is
      top-right, so neither ever overlaps). `.demo-overlay--sls` narrows to 96px:
      it's a still photo, not a loop, so keeping it visibly smaller stops it reading
      as a stalled/broken clip next to the three that are actually playing.
- [x] Wired `<ExerciseDemoOverlay kind="..." />` into all 4 live pages
      (`SquatLiveSessionPage`, `SlsLiveSessionPage`, `StsLiveSessionPage`,
      `WbltLiveSessionPage`), immediately after `<CaptureQualityBadge>` inside
      `.cam-stage`, before `<PoseCanvas>`.
- [x] Verified: `tsc --noEmit` clean; Prettier clean. Live pages need an
      authenticated session + webcam to reach `.cam-stage` normally, so rather than
      driving the full session flow, visually verified the actual compiled
      component markup + CSS + real dev-server asset URLs side-by-side in the
      Browser pane (all 4 kinds at once) — confirms rounded corner, correct
      top-right position, SLS's smaller static size, and the WBLT video actually
      playing.
