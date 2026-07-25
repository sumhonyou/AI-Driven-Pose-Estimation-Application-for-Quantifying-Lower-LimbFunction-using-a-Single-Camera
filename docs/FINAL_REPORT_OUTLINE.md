# Final Report — Content Structure (Chapters 3, 4, 5)

**Project:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera
**Basis:** Capstone 1 proposal (`PS_22089262.pdf`) + as-built codebase

**Revision 3 (2026-07-24) — trimmed.** Ch4 cut from ~45 to ~30 pages: sections merged, the
candidate-classifier bake-off dropped (justified in §3.4.2.5 instead), functional testing grouped
into 5 areas instead of 10.

**Budget:** Ch3 ≈ 20 p · Ch4 ≈ 30 p · Ch5 ≈ 5 p → **~55 pages total**

Annotations: `[HAVE]` exists in repo · `[NEW]` needs writing · `[RUN]` needs a script re-run

---

## CHAPTER 3 — METHODOLOGY (~20 pages)

> Keeps the proposal's skeleton. Rewrite future tense ("will") → past tense ("was").

### 3.1 Methodology Overview
- **3.1.1 Research and Development Approach** — iterative, phase-based, evidence-driven: design decisions settled by measurement where possible. `[NEW, short]`
- **3.1.2 Revised System Workflow** — updated Figure 6 (squat-only, per-rep ML + majority vote, fault-gate layer, LLM rewrite). `[NEW figure — old Fig 6 is out of date]`
- **3.1.3 Summary of Deviations from the Proposal** — table: *proposed → as-built → why*. **Do not skip.** `[HAVE — plan §24; trim 15 rows to ~10]`

### 3.2 Data Acquisition and Dataset Preparation
- **3.2.1 Dataset Selection and Rationale** — REHAB24-6; public dataset over recruitment; side-view choice. `[HAVE]`
- **3.2.2 Label Alignment and Usable Sample** — 98 reps, 9 subjects, 72 Good / 26 Poor. `[HAVE]`
- **3.2.3 Landmark Extraction and Runtime Parity** — offline pipeline + parity check vs in-browser runtime. `[HAVE — PARITY_CHECK.md]`
- **3.2.4 External Validation Dataset (EC3D)** — introduce here as a deliberate method choice. `[HAVE]`
- **3.2.5 Participant-Level (LOSO) Splitting** `[HAVE]`

### 3.3 Data Preprocessing
- **3.3.1 Confidence Filtering and Capture-Quality Gating** (Eq. 1–2) `[HAVE]`
- **3.3.2 Missing Keypoint Handling** (interpolation, ≤5-frame gap) `[HAVE]`
- **3.3.3 Smoothing** (One-Euro, Eq. 4–5) `[HAVE]`
- **3.3.4 Normalisation and Reference-Scale Selection** — expand: the scale was chosen empirically, not asserted. `[HAVE — NORM_REF_BAKEOFF.md]`
- **3.3.5 Output of Preprocessing** `[HAVE]`

### 3.4 System Development

**3.4.1 Module A — Rule-Based Functional Quantification**
- 3.4.1.1 Exercise protocols as built (STS; SLS both legs / 45 s cap; WBLT dual output) `[HAVE]`
- 3.4.1.2 Metric computation and FSM segmentation (incl. the dwell-time fix) `[HAVE]`
- 3.4.1.3 Conservative banding and capture-quality gating `[HAVE]`
- 3.4.1.4 WBLT redesign: self-measured distance + published age/sex norms `[HAVE]`

**3.4.2 Module B — Hybrid Rehabilitation Grading (Squat)**
- 3.4.2.1 Scope decision: squat only (lunge removed — state the measurement-bias reason) `[HAVE]`
- 3.4.2.2 Repetition segmentation and feature design (13 features) + **pre-training validity screening** `[HAVE]`
- 3.4.2.3 Rule-based sub-score design (ROM / Tempo / Stability) `[HAVE]`
- 3.4.2.4 Machine learning workflow — LOSO CV, hyperparameter search, calibration, artifact export `[HAVE]`
- 3.4.2.5 **Classifier selection rationale** — Extra Trees for small-n tabular interpretable features, calibrated probabilities, CPU-latency inference. **State explicitly that a head-to-head classifier comparison was not run, because at n = 98 across 9 subjects the differences would fall within noise** — consistent with §4.4.3. `[NEW, ~half page]`
- 3.4.2.6 Grading output design — fusion sweep, binary Good / Needs-Improvement commitment, per-rep majority vote, headline score `10 × good_reps/total_reps` `[HAVE]`
- 3.4.2.7 Fault gates and error-tag taxonomy — incl. what was **deliberately excluded** (valgus, asymmetry, stance width) `[HAVE]`

**3.4.3 After-Set Feedback Generation**
- 3.4.3.1 Deterministic template layer
- 3.4.3.2 LLM rewriting layer + safety filter (Groq replaced the proposal's "Transformer"; off by default; grade immutability) `[HAVE]`

**3.4.4 Web Application Development**
- 3.4.4.1 Requirement specification (FR/NFR) `[HAVE]`
- 3.4.4.2 System architecture — pose runs in-browser, **raw video never leaves the device**; one post-set request. Update Fig 10. `[HAVE, figure edit]`
- 3.4.4.3 Database design (flat columns vs JSONB) `[HAVE]`
- 3.4.4.4 API design (routers, exercise-plugin registry) `[HAVE]`
- 3.4.4.5 UI and workflow design (12 pages, live HUD, report, dashboard, i18n). Update Fig 11. `[HAVE, figure edit]`
- 3.4.4.6 Privacy and non-diagnostic safeguards `[HAVE]`

### 3.5 System Deployment
~1 page: Cloud Run + Cloud SQL + hosted frontend, containerisation, env/CORS. Diagram + short prose. `[NEW]`

### 3.6 Evaluation and Testing Methodology
- **3.6.1 Module A: measurement-agreement evaluation** — why classifier metrics don't apply to a rule engine; ICC(2,1), Bland–Altman, kappa. `[HAVE — plan §9.4]`
- **3.6.2 Module B: classification evaluation** — standard metrics + the **severe-misclassification rate** as the metric that matters in rehab. `[HAVE]`
- **3.6.3 External validation protocol** `[HAVE]`
- **3.6.4 Functional, performance and regression testing strategy** `[NEW, short]`
- **3.6.5 User acceptance testing design** — 22 participants, scenario tasks, observation sheet, questionnaire; the Functionality / Ease-of-Use split. `[HAVE — docs/user_testing/*]`

---

## CHAPTER 4 — RESULTS AND DISCUSSION (~30 pages)

> **Rule:** every subsection ends with a short discussion paragraph — what the number *means*.
> That is the main B→A difference.
>
> **Weight:** 4.1–4.5 analytical (~16 p) · 4.6–4.7 evidence-heavy tables + screenshots (~13 p).

### 4.1 Project Review (~3 p)
- **4.1.1 Delivered System Walkthrough** — annotated screenshots: camera setup, live HUD, report, dashboard, progress. `[NEW screenshots]`
- **4.1.2 Scope Delivered Against the Proposal** — short; refers back to §3.1.3. `[HAVE]`

### 4.2 Feature and Measurement Validation (~4 p)
> No peer equivalent — a CNN project skips this. You engineered features by hand, so validating
> them *is* a result.

- **4.2.1 Feature Validity Screening and Repetition-Detection Results** — kept/dropped features (AUC, per-subject direction consistency); segmentation vs ground-truth rep counts. `[HAVE — FEATURE_VALIDITY.md]`
- **4.2.2 Agreement with Motion-Capture Ground Truth** — Bland–Altman; the ≈ −11.96° knee-flexion under-read that later anchored the depth gate. `[HAVE — MOCAP_AGREEMENT.md]`
- **4.2.3 Discussion — What a Single Camera Can and Cannot Measure** — far-limb occlusion (0.59–0.78 vs 0.95–0.99); frontal-plane faults excluded by geometry, not omission.

### 4.3 Model Evaluation (~5 p)
- **4.3.1 Training and Calibration Results** — LOSO CV, hyperparameter search, reliability curve. `[HAVE]`
- **4.3.2 Feature Importance Analysis** `[HAVE]`
- **4.3.3 Fusion Weight and Decision Threshold Selection** — the joint search that drove `w_rule → 0`. `[HAVE — SQUAT_FUSION_SWEEP.md]`
- **4.3.4 Final Operating Point and Confusion Matrix** — recall(Poor) 0.077 → 1.000; 22/72 (31%) false alarms; **zero** poor-called-Good. `[HAVE — SQUAT_EVALUATION_REPORT_2BAND.md]`

### 4.4 Comparative Analysis (~3 p)
> Merged: the old "Model Comparative Analysis" + "Comparison with Related Research".
> No candidate-classifier bake-off — see §3.4.2.5.

- **4.4.1 Rule-Based vs Machine Learning vs Hybrid** — your real comparison: the ROM rule was *inverted* for this population, so fusion collapsed to pure ML. `[HAVE]`
- **4.4.2 Comparison with Published Pose-Based Grading Systems** `[HAVE — §7.6]`
- **4.4.3 Why a Single Accuracy Figure Cannot Be Honestly Reported** — n = 98 / 9 subjects; accuracy breaks even against the majority baseline; different papers use different labels and split schemes. `[HAVE — §7.1]`

### 4.5 External Validation and the Transferability Finding ★ (~4 p)
> Your strongest and most original section. No peer project will have one.

- **4.5.1 EC3D Results and the Two Findings** — incompatible definitions of "incorrect"; construct inversion (≈56.7% of importance mass). `[HAVE]`
- **4.5.2 Live Confirmation on Real Webcam Sessions** — depth vs `ml_score` **r = −0.975** on a fault-free session; 17/21 (81%) of gate-clean reps ML-rejected. Not a dataset artefact. `[HAVE]`
- **4.5.3 Design Changes Made in Response** — `w_rule = 0`, interpretable fault gates, Stage 5.18 headline-score redefinition. `[HAVE]`
- **4.5.4 Discussion** — internal cross-validation is not sufficient evidence for a clinical-adjacent grader.

### 4.6 Testing (~11 p)
> Format: **test-case table first, one screenshot per case.**
> Columns: `ID · Test Case · Input / Precondition · Expected · Actual · Status`

- **4.6.1 Module A Measurement-Agreement Testing** — SLS: ICC ≈ 0.995, kappa ≈ 0.857, bias −0.753 s, LoA [−4.08, 2.57]; bias traced to FSM drop-hysteresis; coverage gap (synthetic corpus, no STS/WBLT harness). `[RUN to refresh]`
- **4.6.2 Module B Grading Test Cases** — **one combined table** covering good-form, insufficient-depth, excessive-lean, heel-rise, and invalid/low-capture-quality cases (out of frame, occluded, poor lighting). `[NEW]`
- **4.6.3 Functional Testing** — grouped into 5 areas, not 10:
  - 4.6.3.1 Authentication, profile and settings
  - 4.6.3.2 Camera setup and capture-quality gating
  - 4.6.3.3 Module A — functional checks (STS, SLS, WBLT)
  - 4.6.3.4 Module B — squat grading and after-set report
  - 4.6.3.5 Dashboard, progress and reminders
- **4.6.4 System Performance and Deployment** — in-browser FPS, backend inference + report latency, deployed end-to-end verification. `[RUN + NEW]`
- **4.6.5 Automated Regression Test Suite** — 330 backend + frontend vitest; fixed-seed replay determinism. ~1 page, already written, and stronger evidence than screenshots alone. `[HAVE]`

### 4.7 User Acceptance Testing (~6 p)
- **4.7.1 Participants and Procedure** — 22 participants / 21 questionnaires, scenario tasks, moderated observation. `[HAVE]`
- **4.7.2 Functionality** — core-function results per module; defects identified; **before-and-after improvements** (R1 squat heel-lift false positive · R2 SLS lift over-sensitivity · R3 LLM fallback telemetry · R4 live-feedback redesign · R5 uniform start + recording state · R6 audio cues), presented as *finding → fix → verification*. **Direct evidence for Project Goal 5.** `[HAVE — task.md Phase 10]`
- **4.7.3 Ease-of-Use** — navigation and task completion; clarity of instructions and feedback; language/accessibility. `[HAVE]`
- **4.7.4 Discussion** — R1 and R2 were *correctness* defects found only by real users; that is itself a result about the limits of self-testing.

### 4.8 Achievement of Project Objectives (~1–2 p)
Table: each of the 5 proposal goals → evidence → section. `[NEW, cheap, high value]`

---

## CHAPTER 5 — CONCLUSION (~5 pages)

> A 1-page conclusion is not the model to copy here — your limitations and future work are among
> your strongest material.

### 5.1 Summary of the Project (~1 p)
What was built and what was found, including the transferability result.

### 5.2 Contributions
1. A working, non-diagnostic, single-camera lower-limb self-check and rehab-grading web application.
2. A hybrid design using clinically-anchored rules where a validated cutoff exists and ML only where a threshold cannot decide — with the split justified empirically.
3. A feature-validity screen and motion-capture agreement analysis quantifying what a monocular webcam can actually measure.
4. A documented negative result: an internally-strong classifier whose "incorrect" construct did not transfer and inverted in live use — plus the design changes made in response.
5. A measurement-agreement (ICC / Bland–Altman / kappa) evaluation framing for deterministic rule-based functional checks.

### 5.3 Limitations
- **5.3.1 Monocular single-camera** — depth axis, frontal-plane faults excluded, far-limb occlusion, no clinical goniometry.
- **5.3.2 Dataset and model** — 98 reps / 9 subjects; population-specific "Poor" construct; 31% false-alarm cost; clinically-anchored (not learned) depth gate; no published MDC; one Module B exercise.
- **5.3.3 Module A** — synthetic agreement corpus; STS/WBLT unevaluated; WBLT self-measurement dependency; heuristic thresholds.
- **5.3.4 Feedback and platform** — LLM off by default and best-effort; client-side-only reminders; no email verification/recovery.

### 5.4 Future Work
Pair each item to the limitation it answers:
1. Larger multi-cohort clinician-labelled dataset (→ 5.3.2)
2. Real pilot recordings + agreement harnesses for STS and WBLT (→ 5.3.3)
3. Multi-view or depth capture to unlock valgus / asymmetry / stance width (→ 5.3.1)
4. Per-rep real-time coaching via WebSocket push (deferred §11.2 enhancement)
5. Establishing an MDC so progress trends can make a meaningful-change claim
6. Additional Module B exercises via the plugin registry; mobile support

### 5.5 Concluding Remarks (~2 paragraphs)

---

## Effort notes

**Already written in the repo** — reformat, don't re-derive:
`ml/reports/PHASE5_CHAPTER_DRAFT.md` → most of 3.2, 3.3, 3.4.2, 4.2, 4.3, 4.4, 4.5 ·
plan §9.4 → 3.6.1 + 4.6.1 · plan §24 → 3.1.3 · plan §25 → 5.3 · `task.md` Phase 10 → 4.7.2.

**Needs new work:** Figures 6/10/11 · app screenshots (4.1) · classifier-selection rationale (3.4.2.5) ·
test-case tables (4.6.2, 4.6.3) · deployment (3.5, 4.6.4) · UAT write-up (4.7) · objectives table (4.8) ·
contributions (5.2).

**Re-run before quoting numbers:** SLS agreement harness, squat evaluation reports, latency
measurement — R1 already moved the heel-rise threshold (0.0840 → 0.0710), so older figures shifted.

**Deliberately not done, and say so:** candidate-classifier bake-off (§3.4.2.5) — between-classifier
differences at n = 98 / 9 subjects fall within noise, so reporting one as a selection justification
would contradict §4.4.3.
