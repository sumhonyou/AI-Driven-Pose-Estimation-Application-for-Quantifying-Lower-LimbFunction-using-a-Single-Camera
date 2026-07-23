# FYP Project Description and Implementation Plan

> ⚠️⚠️⚠️ **Leg Lunge exercise removed (2026-07-19, HY's decision).** Squat is
> the only Module B rehabilitation-grading exercise. This document has been
> updated so its architecture and design sections describe the squat-only
> system as currently built; it no longer plans for a second Module B
> exercise. For the retained historical record of the lunge investigation
> (data audit, feature engineering, model training, and the reasons for its
> removal), see [task.md](./task.md)'s Phase 5B section.

**Project Title:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera  
**Current Recommended Architecture:** React + TypeScript frontend, MediaPipe Pose in browser, FastAPI backend, PostgreSQL database, Google Cloud deployment

**Related files:**

- [task.md](./task.md) — phased tasks, deliverables, and milestones
- [rules.md](./rules.md) — coding agent rules (must be followed on every development request)

---

- [FYP Project Description and Implementation Plan](#fyp-project-description-and-implementation-plan)
  - [1. Short Project Summary](#1-short-project-summary)
  - [2. Current High-Level Goal](#2-current-high-level-goal)
  - [3. Recommended Final Tech Stack](#3-recommended-final-tech-stack)
    - [3.1 Frontend](#31-frontend)
    - [3.2 Backend](#32-backend)
    - [3.3 Database](#33-database)
    - [3.4 Deployment](#34-deployment)
  - [4. Why This Architecture Is Recommended](#4-why-this-architecture-is-recommended)
  - [5. Recommended System Architecture](#5-recommended-system-architecture)
    - [5.1 Main Architecture](#51-main-architecture)
    - [5.2 Important Architecture Decision](#52-important-architecture-decision)
  - [6. Non-Diagnostic Boundary](#6-non-diagnostic-boundary)
  - [7. User Roles and Target Users](#7-user-roles-and-target-users)
    - [7.1 User Type](#71-user-type)
    - [7.2 User Account Data](#72-user-account-data)
  - [8. Application Pages](#8-application-pages)
    - [8.0 Phase 1 Development Approach](#80-phase-1-development-approach)
    - [8.1 Required Pages](#81-required-pages)
  - [9. Module A: Functional Checking](#9-module-a-functional-checking)
    - [9.1 Functional Checks](#91-functional-checks)
    - [9.2 Module A Output](#92-module-a-output)
    - [9.3 Conservative Banding](#93-conservative-banding)
    - [9.4 Module A Evaluation (Measurement Agreement)](#94-module-a-evaluation-measurement-agreement)
  - [10. Module B: Rehabilitation Grading](#10-module-b-rehabilitation-grading)
    - [10.1 Module B Pipeline](#101-module-b-pipeline)
    - [10.2 Module B Output](#102-module-b-output)
    - [10.3 Why Extra Trees Classifier](#103-why-extra-trees-classifier)
    - [10.4 Fusion Scoring](#104-fusion-scoring)
  - [11. Live Feedback Strategy](#11-live-feedback-strategy)
    - [11.1 Recommended MVP Strategy](#111-recommended-mvp-strategy)
    - [11.2 Optional Enhancement](#112-optional-enhancement)
  - [12. Pose Processing and Feature Pipeline](#12-pose-processing-and-feature-pipeline)
    - [12.1 Frontend Processing](#121-frontend-processing)
    - [12.2 Backend Processing](#122-backend-processing)
    - [12.3 Preprocessing Methods](#123-preprocessing-methods)
  - [13. PostgreSQL Database Design](#13-postgresql-database-design)
    - [13.1 Why PostgreSQL](#131-why-postgresql)
    - [13.2 Recommended Tables](#132-recommended-tables)
      - [users](#users)
      - [userprofiles](#user_profiles)
      - [exercisecatalog](#exercise_catalog)
      - [sessions](#sessions)
      - [modulearesults](#module_a_results)
      - [modulebresults](#module_b_results)
      - [errortags](#error_tags)
      - [feedbacktexts](#feedback_texts)
      - [reminders](#reminders)
  - [14. Backend API Design](#14-backend-api-design)
    - [14.1 Auth APIs](#141-auth-apis)
    - [14.2 User Profile APIs](#142-user-profile-apis)
    - [14.3 Exercise APIs](#143-exercise-apis)
    - [14.4 Session APIs](#144-session-apis)
    - [14.5 Module A APIs](#145-module-a-apis)
    - [14.6 Module B APIs](#146-module-b-apis)
    - [14.7 Report APIs](#147-report-apis)
    - [14.8 Dashboard APIs](#148-dashboard-apis)
    - [14.9 Reminder APIs](#149-reminder-apis)
  - [15. External LLM API Usage](#15-external-llm-api-usage)
  - [16. Suggested Project Folder Structure](#16-suggested-project-folder-structure)
  - [17. Environment Variables](#17-environment-variables)
    - [Backend](#backend-env) `.env`
    - [Frontend](#frontend-env) `.env`
  - [18. Local Development Setup Plan](#18-local-development-setup-plan)
    - [18.1 Tools to Install](#181-tools-to-install)
    - [18.2 Local PostgreSQL with Docker](#182-local-postgresql-with-docker)
  - [19. Development Plan from 0 Progress](#19-development-plan-from-0-progress)
  - [20. What to Start With Right Now](#20-what-to-start-with-right-now)
  - [21. Coding Agent Rules](#21-coding-agent-rules)
  - [Coding agent rules are maintained in **rules.md**. They must be followed on every development request.](#coding-agent-rules-are-maintained-in-rulesmd-they-must-be-followed-on-every-development-request)
  - [22. Future Enhancements](#22-future-enhancements)
  - [23. Final Implementation Priority](#23-final-implementation-priority)
  - [24. Additions and Deviations from the Original Plan](#24-additions-and-deviations-from-the-original-plan)
  - [25. Current System Limitations (for the Final Report)](#25-current-system-limitations-for-the-final-report)



## 1. Short Project Summary

This FYP is a **web-based AI pose-estimation application** that uses a **single webcam** to support home-based lower-limb functional checking and rehabilitation exercise grading.

The application focuses on the **knee and ankle**. It is designed for general users, with priority consideration for **older adults with knee problems** and **athletes**. The system is **non-diagnostic**, meaning it must not claim to diagnose injuries, prescribe treatment, give medical clearance, or make return-to-sport decisions.

The system uses the webcam to capture movement, applies **MediaPipe Pose** to extract body landmarks, calculates movement features, and provides conservative feedback such as:

- Good / Fair / Poor movement band
- Capture quality warning
- Range of motion indicator
- Stability or sway indicator
- Symmetry proxy
- Error tags
- Confidence score
- After-set coaching feedback
- Progress trend across sessions

The project has two main modules:

1. **Module A: Functional Checking**
  Rule-based functional self-checks for knee and ankle function.
2. **Module B: Rehabilitation Grading**
  Hybrid rule-based + machine learning grading for rehabilitation exercise quality. This is the **main priority** if time becomes limited.

---



## 2. Current High-Level Goal

Build a deployed AI web application that can:

1. Allow users to register/login.
2. Let users choose a mode: Functional Check or Rehab Grading.
3. Guide users through camera setup.
4. Run MediaPipe Pose through the browser webcam.
5. Provide simple live Good/Fair/Poor feedback without causing high latency.
6. Generate a detailed after-set report after the user finishes the session.
7. Store user profile, session summaries, module results, error tags, feedback text, and reminders in PostgreSQL.
8. Show dashboard history and progress trend.
9. Deploy the project to Google Cloud Platform.

---



## 3. Recommended Final Tech Stack



### 3.1 Frontend


| Layer             | Technology                                                      | Purpose                                   |
| ----------------- | --------------------------------------------------------------- | ----------------------------------------- |
| Web Framework     | React                                                           | Build interactive web app UI              |
| Language          | TypeScript                                                      | Type-safe frontend development            |
| Build Tool        | Vite                                                            | Fast development and build process        |
| Styling           | Tailwind CSS                                                    | Fast and consistent UI styling            |
| Webcam Access     | Browser MediaDevices API                                        | Access user webcam in browser             |
| Pose Estimation   | MediaPipe Pose / MediaPipe Tasks Vision                         | Extract body landmarks from webcam frames |
| Charts            | Recharts or Chart.js                                            | Dashboard progress visualization          |
| API Communication | Axios or Fetch API                                              | REST API calls to backend                 |
| Live Feedback     | Frontend local rule calculation first; optional WebSocket later | Avoid latency during live session         |




### 3.2 Backend


| Layer             | Technology                          | Purpose                                                |
| ----------------- | ----------------------------------- | ------------------------------------------------------ |
| Backend Framework | Python FastAPI                      | REST API, session handling, scoring, report generation |
| Validation        | Pydantic                            | Validate request and response data                     |
| Database ORM      | SQLAlchemy or SQLModel              | PostgreSQL database mapping                            |
| Migration         | Alembic                             | Database schema migrations                             |
| ML Libraries      | scikit-learn, NumPy, pandas, joblib | Feature processing and model inference                 |
| ML Model          | Extra Trees Classifier              | Exercise-specific rehab grading model                  |
| External Feedback | External LLM API                    | Rewrite structured feedback after the set only         |
| Testing           | Pytest                              | Backend unit and integration testing                   |




### 3.3 Database


| Layer          | Technology               | Purpose                         |
| -------------- | ------------------------ | ------------------------------- |
| Local Database | PostgreSQL in Docker     | Local development database      |
| Cloud Database | Cloud SQL for PostgreSQL | Production/deployed database    |
| DB GUI         | DBeaver or pgAdmin       | View and manage database tables |




### 3.4 Deployment


| Component          | Recommended Platform                           |
| ------------------ | ---------------------------------------------- |
| Frontend           | Firebase Hosting or Cloud Run static container |
| Backend            | Google Cloud Run                               |
| Database           | Google Cloud SQL for PostgreSQL                |
| Container Registry | Google Artifact Registry                       |
| CI/CD, optional    | Google Cloud Build                             |


---



## 4. Why This Architecture Is Recommended

The current recommendation is to use a **FastAPI-only backend** instead of adding ASP.NET Core at the beginning.

Reason:

- Phase 0–1B baseline is now implemented; the main contribution remains AI-based rehab grading (Phases 2–5).
- Python is more direct for MediaPipe, NumPy, pandas, scikit-learn, and Extra Trees.
- Deployment is already an added complexity, so keeping one backend service reduces risk.
- A completed, deployed, evaluated project will score better than an overcomplicated unfinished project.

ASP.NET Core can be mentioned as a **future enhancement**, especially for stronger enterprise backend orchestration and SignalR real-time communication. However, it should not be implemented in the first version unless the supervisor specifically requests it.

---



## 5. Recommended System Architecture



### 5.1 Main Architecture

```text
User Browser
  ├── React + TypeScript + Tailwind UI
  ├── Browser MediaDevices API
  ├── MediaPipe Pose running in browser
  ├── Lightweight live feedback calculation
  │
  └── Sends selected mode, exercise type, landmarks/features, and session data
        ↓
FastAPI Backend on Cloud Run
  ├── Auth module
  ├── User/session manager
  ├── Mode and exercise router
  ├── Rule-based scoring engine
  ├── ML inference handler
  ├── Fusion scoring module
  ├── Report generator
  ├── External LLM API caller for after-set rewriting
  └── PostgreSQL data access layer
        ↓
Cloud SQL PostgreSQL
  ├── Users
  ├── User profiles
  ├── Sessions
  ├── Module A results
  ├── Module B results
  ├── Error tags
  ├── Feedback text
  └── Reminders
```



### 5.2 Important Architecture Decision

**Do not send raw video to the backend for the normal system flow.**

Instead:

```text
Webcam video stays in browser
→ MediaPipe extracts landmarks in browser
→ frontend sends landmarks/features/results to backend
→ backend stores derived metrics only
```

This improves:

- Privacy
- Latency
- Storage cost
- Deployment simplicity
- Final report justification

The backend may accept landmark arrays or precomputed feature windows, but should not require raw video upload.

---



## 6. Non-Diagnostic Boundary

The application must clearly state that it is not a medical device and not a replacement for a doctor or physiotherapist.

The system must not provide:

- Medical diagnosis
- Injury confirmation
- Disease classification
- Prescription
- Medical clearance
- Return-to-sport decision
- Emergency medical advice

The system can provide:

- Movement quality indicator
- Good/Fair/Poor band
- Capture quality warning
- General technique cue
- Progress trend
- Reminder to seek professional advice when needed

Suggested UI disclaimer:

> This application provides non-diagnostic movement-quality feedback only. It does not replace professional medical advice. If you experience pain, discomfort, or uncertainty, stop the activity and consult a qualified healthcare professional.

---



## 7. User Roles and Target Users



### 7.1 User Type

The project is intended for:

- General users
- Older adults with knee-related concerns
- Athletes
- Users doing basic home rehabilitation or functional self-checking



### 7.2 User Account Data

The system should store basic user information required for account and progress tracking.

Recommended fields:

- id
- email
- password_hash or external auth id
- full_name
- age_group, optional
- gender, optional
- height_cm, optional
- weight_kg, optional
- user_type, e.g. general, older_adult, athlete
- focus_area, e.g. knee, ankle, both
- created_at
- updated_at

Avoid storing detailed medical diagnosis unless truly necessary. If any self-reported condition is stored, keep it general and optional.

---



## 8. Application Pages



### 8.0 Phase 1 Development Approach

Phase 1 is split into two steps (see **[task.md](./task.md)**):

1. **Phase 1A — UI clickable prototype (do first):** Build all pages listed in §8.1 as a frontend-only prototype. Use React Router, Tailwind, mock/placeholder data, and wired navigation. No real API calls, JWT, or database integration yet. Camera and pose pages use placeholder UI only (real webcam/MediaPipe comes in Phase 2).
2. **Phase 1B — Full-stack integration (after prototype):** Implement register/login, JWT, session APIs, exercise catalog seed data, and connect the existing UI to the FastAPI backend and PostgreSQL.

The prototype validates layout, user flow, and page content before backend work begins.

### 8.1 Required Pages

1. **Landing Page**
  - Project introduction
  - Non-diagnostic disclaimer
  - Login/register buttons
2. **Register Page**
  - Email
  - Password
  - Basic profile details
3. **Login Page**
  - Email
  - Password
  - JWT/session handling
4. **Dashboard Page**
  - Summary cards
  - Recent sessions
  - Average score
  - Latest band
  - Progress chart
  - Common error tags
5. **Mode Selection Page**
  - Functional Checking
  - Rehab Grading
6. **Exercise Selection Page**
  - Module A: Sit-to-Stand, Supported SLS, WBLT
  - Module B: placeholder exercise-specific rehab grading exercise
7. **Camera Setup Page**
  - Webcam preview
  - Pose skeleton overlay
  - Camera distance guidance
  - View guidance: side/front depending on exercise
  - Body visibility check
  - Capture quality indicator
8. **Live Session Page**
  - Webcam feed
  - Pose overlay
  - Timer
  - Rep or hold progress
  - Live Good/Fair/Poor indicator
  - Capture quality warning
  - Stop/end set button
9. **Post-Performance Report Page**
  - Final score
  - Final band
  - Rule-based sub-scores
  - ML prediction, if Module B
  - Confidence score
  - Error tags
  - Coaching feedback text
  - Non-diagnostic reminder
10. **Session History Page**
  - List of previous sessions
    - Filter by mode/exercise/date
11. **Reminder Page**
  - Add reminder
    - View reminders
    - Mark reminder as complete
12. **Progress Deep-Dive Page** *(added in Phase 7 — route* `/progress`*, see [§24](#24-additions-and-deviations-from-the-original-plan))*
  - Per-exercise trend deep dive (one exercise at a time, chosen via a category selector: Functional Checking / Rehab Grading)
    - Date-range control (14 days / 30 days / All)
    - Score trend chart with Good/Fair/Poor band zones
    - Band distribution for the selected exercise
    - Capture-quality trend
    - Module B only: rep-volume chart (attempts vs. counted-good reps per session, Stage 5.22 — replaces an earlier Confidence trend, dropped for being a model-internal diagnostic a patient can't act on and, for squat, indistinguishable from its own ML-prediction card in every recorded rep) + ranked error-tag bar chart
    - Score trend's band-zone boundaries are now per-exercise (Stage 5.22): squat uses its real binary cut (`Good` iff `score > 5.0`, no Fair zone) instead of the shared Good/Fair/Poor 7/4 cutoffs, which never matched squat's actual voting rule
    - Complements the Dashboard's multi-exercise "at a glance" overview (the Dashboard shows small-multiples across all exercises; the Progress page shows one exercise in full detail)

---



## 9. Module A: Functional Checking

Module A uses deterministic rule-based quantification. It does not require machine learning training.

### 9.1 Functional Checks


| Check                       | View Guidance        | Reps/Duration | Main Outputs                                            |
| --------------------------- | -------------------- | ------------- | ------------------------------------------------------- |
| Sit-to-Stand                | Side view            | 5 reps        | Completion time, knee ROM band, trunk lean proxy, grade |
| Supported Single-Leg Stance | Front view preferred | 30 seconds    | Hold duration, sway/stability proxy, grade              |
| Weight-Bearing Lunge Test   | Side view            | 3 trials      | Dorsiflexion ROM band, symmetry proxy, grade            |




### 9.2 Module A Output

For each Module A session, return:

```json
{
  "session_id": "uuid",
  "mode": "functional_check",
  "exercise_type": "sit_to_stand",
  "capture_quality": 0.88,
  "valid_frame_ratio": 0.91,
  "metrics": {
    "completion_time_sec": 12.4,
    "rom_band": "fair",
    "trunk_lean_proxy": 0.32,
    "stability_proxy": null,
    "symmetry_proxy": null
  },
  "final_band": "fair",
  "confidence_level": "moderate",
  "warnings": [],
  "created_at": "timestamp"
}
```



### 9.3 Conservative Banding

Use Good/Fair/Poor bands instead of overclaiming exact clinical values.

Example:

```text
Good: movement completed with good capture quality and expected range
Fair: movement completed but some indicator is below expected range
Poor: low performance or unreliable movement/capture quality
```

Thresholds can start as heuristic values and be refined during pilot testing.

### 9.4 Module A Evaluation (Measurement Agreement)

> **Note — added beyond the original plan.** As originally written, this document specified an evaluation method only for **Module B** (classifier metrics: accuracy, precision, recall, macro-F1, confusion matrix) and for the **system** (FPS, response time, usability). It did **not** specify how the deterministic, rule-based **Module A** checks should be evaluated. This subsection records the approach actually implemented for the Single-Leg Stance (SLS) check. See [§24](#24-additions-and-deviations-from-the-original-plan) for the full list of additions beyond the original plan.

Module A checks are **deterministic rule-based measurements**, not trained classifiers, so classifier-accuracy metrics do not apply. The SLS hold-timer is instead evaluated as a **measurement instrument** — how closely the system's measured hold time agrees with a human-timed (stopwatch) reference. This is the standard framing for method-comparison / inter-rater reliability and fits the project's non-diagnostic, functional-self-check boundary (§6).

**Statistics used** (pure-Python, no numpy/scipy dependency — closed-form formulas over a small sample):


| Statistic     | What it measures                                                       | Why chosen                                                                                                                                                                  |
| ------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ICC(2,1)      | Absolute agreement between system hold-time and manual hold-time       | Two-way random effects, single measurement, absolute agreement (Shrout & Fleiss, 1979) — we care whether the seconds literally match, not just move proportionally together |
| Bland-Altman  | Bias (mean difference) and 95% limits of agreement                     | Standard method-comparison analysis (Bland & Altman, 1986); difference is defined as `system − manual`                                                                      |
| Cohen's kappa | Categorical agreement of the Good/Fair/Poor/Invalid **hold-time band** | Chance-corrected band agreement a stopwatch-only human reviewer could reproduce (Cohen, 1960)                                                                               |


Band agreement (kappa) is computed on the **hold-time band only**, because a human with a stopwatch can independently reproduce that dimension but cannot judge the ball-in-circle stability sub-score without a separate rater protocol (future work).

**Evaluation harness (reproducible, committed):**

- `backend/app/module_a/sls/evaluation/agreement.py` — the three statistics, plus unit tests using hand-verified boundary cases.
- `backend/app/module_a/replay_corpus/sls/` — fixed-seed **synthetic** corpus (10 per-leg samples spanning Poor/Fair/Good/Invalid, steady and swaying). No real pilot recordings exist yet for this prototype; the corpus is produced by `generate_sls_replay_corpus.py`.
- `run_sls_evaluation.py` — replays the corpus through the deterministic `analyze_leg` core, computes the statistics, and writes `SLS_EVALUATION_REPORT.md`. Run with `python -m app.module_a.scripts.run_sls_evaluation`.

**Results (current fixed-seed corpus, reproducible byte-identical across runs):**


| Metric                                   | Value                                                                                                      |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| ICC(2,1) — absolute agreement, hold time | **0.995**                                                                                                  |
| Cohen's kappa — hold-time band agreement | **0.857**                                                                                                  |
| Bland-Altman bias (`system − manual`)    | **−0.753 s** — system reads slightly shorter, consistent with the FSM's drop-hysteresis persistence frames |
| Bland-Altman 95% limits of agreement     | **[−4.08 s, 2.57 s]**                                                                                      |


The single band disagreement (1 of 10) is a genuine edge case, not a bug: the system correctly reports `invalid` for a leg that never validly crossed the lift-line, while the naive time-based reference calls a small positive duration `poor`. The monocular-depth limitation (frontal-plane-only stability scoring) and all prototype thresholds (`sls/config.py`) are documented in the generated report for the final report's limitations chapter.

> **The numbers above come from the current fixed-seed corpus** and will change if the corpus or thresholds change. `SLS_EVALUATION_REPORT.md` always holds the live values — re-run the harness before quoting them in the final report.

**Generalizable to STS and WBLT (future work):** the same measurement-agreement framing applies to the Sit-to-Stand completion-time and WBLT dorsiflexion-ROM measurements, but those replay/agreement harnesses are not yet built — only SLS has one today.

---



## 10. Module B: Rehabilitation Grading

Module B is the main AI contribution of the project.

> **Update:** the exact rehab exercise has since been decided — **squat**. The module remains an **exercise-specific grading module** exactly as designed below: exercise is still configurable, added via a **registry of exercise plugins** behind one thin shared router, not hardcoded per exercise. The full staged build plan lives in [task.md](./task.md); this section stays the architectural specification those phases implement.



### 10.1 Module B Pipeline

```text
User selects Rehab Grading mode
→ user selects exercise type (squat)
→ frontend starts webcam and MediaPipe Pose
→ landmarks extracted in browser
→ frontend performs capture quality check and lightweight live cue
→ after set ends, frontend sends session landmark/features summary to backend
→ backend preprocesses/validates features
→ rule-based sub-scores are calculated
→ Extra Trees model predicts quality label and confidence (a deterministic, clearly-announced stub model stands in until the real model is trained — Phase 4 ships end-to-end on the stub; Phase 5 swaps it in)
→ error tags are generated
→ rule score and ML score are fused
→ final report is generated
→ external LLM API rewrites structured feedback
→ results are stored in PostgreSQL
```

> **As-built detail — how the hybrid grading pipeline actually works, live session vs post-session (2026-07-19).** The arrow list above is the high-level shape; this is the concrete "who does what, with what data, producing what" breakdown for squat as it ships today.

**A. Live session — frontend only, no backend calls per frame**

- Webcam frames → MediaPipe Pose (in-browser) → per-frame body landmarks. Raw video never leaves the browser.
- Frontend buffers landmarks in memory for the whole set and computes a **capture-quality score** (visibility/framing) continuously.
- Frontend also runs a **rough local estimate** purely for on-screen feedback — a hysteresis rep counter + a crude ROM band guess. This is a display-only approximation, clearly separate from the real grade; it never touches the database.
- Squat has no fixed rep count (unlike STS's clinical 5 reps), so the set ends when the user taps **"Finish Set"** (or the inactivity/rep-goal prompts). At that point the frontend sends the **entire session's buffered landmark/feature summary in one request** — `POST /api/module-b/analyze` — not per-frame streaming.

**B. Post-session — backend, one request, after the set ends**

1. **Registry dispatch** — `exercise_code` (`"squat"`) resolves to the squat plugin behind the shared generic router.
2. **Rep segmentation** — a hysteresis finite-state machine (`STANDING → DESCENDING → BOTTOM → ASCENDING → STANDING`, driven by knee-flexion angle) splits the raw landmark stream into discrete reps.
3. **Feature extraction** — for each rep, 13 ordered features are computed (knee ROM, trunk lean, tempo, symmetry, etc.), each a pure function of that rep's own frames.
4. **Rule sub-scores** — ROM / Tempo / Stability, each 0–10, from clinical-norm and heuristic bands → averaged into `S_rule`.
5. **ML inference (per rep, Stage 5.13)** — the calibrated Extra Trees model scores **every rep's own** feature vector independently → each rep's `P(Good)` → `ml_score = 10·P(Good)`. (Superseded the original Phase 5 implementation, which scored `feature_vectors[0]` only — see the correction note in §10.4.)
6. **Per-rep pass/fail, then majority vote (Stage 5.13)** — each rep's fused score `w_rule·S_rule + w_ml·ml_score` (squat's tuned weights: `w_rule=0`, `w_ml=1`, i.e. pure ML) is compared against `decision_threshold=8.447974`; a rep counts as clean only if it clears that **and** has no failed fault gate (step 7). The set's **band** is a strict majority of these per-rep verdicts. The **headline 0–10 score is not this fused value** — see the Stage 5.18 correction in §10.4 for what it is instead and why it changed.
7. **Fault gates (override layer)** — independently of the score above, three rule thresholds (depth / forward lean / heel rise) are checked on **every** rep. Any failure forces the band to **Poor with a named reason**, regardless of what fusion decided.
8. **Error tags** — assembled from the fault gates (rule-sourced), a soft tempo-consistency tag, and system tags (low confidence / low capture quality), each ranked by severity.
9. **Feedback** — a deterministic template is always composed from the band/score/tags first; if the LLM is enabled, its rewrite must pass a safety filter (no grade/band/score change, no invented tags) before it's allowed to replace the template.
10. **Persistence** — final score, band, confidence, model version, rule sub-scores, ML score, feature vector, error tags, and feedback text are written to PostgreSQL in one pass.
11. **Response** — the full report is returned to the frontend and rendered on the Report page.

> **Which layers look at every rep (corrected — this used to be a real gap).** Every rep is segmented and turned into features, and now every layer evaluates every rep: the **rule sub-scores** (ROM / tempo / stability) across all reps, the **three fault gates** on every rep, and — since **Stage 5.13** — the **trained ML classifier** too, which originally scored `feature_vectors[0]` only (a documented, deliberately-deferred gap at the time this section was first written) and was corrected to score each rep's own feature vector independently. A rep's final `counted_good` is `ml_passed AND not failed_gates`, decided per rep; the set's band is a strict majority of these per-rep verdicts. So "the system evaluates every rep after the session" is now **true for every layer**, not just the rule + fault-gate layers.

**Result the user sees:** a 0–10 score, a **Good / Needs Improvement** band, a confidence percentage, the three rule sub-scores plus the mean ML score for transparency, ranked error tags (with the specific fault named when a gate fired, or a named "flagged by the movement model, no specific fault identified" tag when the ML alone rejected a gate-clean rep — Stage 5.19), and coaching text — never a raw model score with no explanation.

> **Why train a machine learning model at all, instead of only using rules / an angle threshold?** (plain-language explanation + viva defence — a natural question once you see the fault gates already cover the obvious faults with pure thresholds)
>
> **The framing that defuses the question: this system does not use ML *instead of* thresholds — it uses both, each where it is justified.** Where a validated clinical cutoff exists (squat-to-parallel depth, forward-lean, heel-lift), an explicit **rule** is used — those are the transparent, clinically-anchored fault gates. ML is used only for the part a single threshold **cannot** do. So an examiner's "just set an angle threshold" is not rejected — it is already in the system as the fault gates.
>
> 1. **A threshold is one number on one feature; "good form" is many features interacting.** A rep can hit perfect depth but with a collapsing trunk, uneven tempo, and wobble. To grade *overall* quality with rules you would have to hand-write a combination formula across all 13 features **and hand-pick every weight and interaction term** (e.g. "shallow depth is acceptable *if* ankle mobility is limited"). Every one of those numbers is a guess. The model learns those weights from labeled data, and the **feature-importance ranking can be reported as evidence** — a threshold gives no importance, no weighting, no principled way to combine features.
> 2. **The strongest single point: a hand-picked assumption was empirically *wrong*, and only the data caught it.** The obvious rule "deeper squat = better" seemed safe. But in the labeled training data the reps marked *incorrect* were actually **deeper** on average — the opposite of the assumption. A designer setting that threshold by hand would have graded backwards. This is the thesis in one fact: **hand-set thresholds encode the designer's assumptions, which can be false; a trained model learns the real relationship from ground truth.** When the fusion weight was chosen empirically it drove `w_rule → 0`, i.e. on this data the ML carried signal the rules did not.
> 3. **ML gives a confidence/probability; a threshold gives only a hard yes/no.** The calibrated classifier outputs `P(Good)`, which the system uses to flag low-confidence reps. A bare threshold has no notion of "borderline."
> 4. **It is the methodological contribution being assessed — done honestly.** Module B is specified as a hybrid rule + ML system; building the full pipeline (feature engineering → training → calibration → cross-validation → **external validation on EC3D**) is a core deliverable. Crucially, the honest scientific step was taken: it was *tested* whether ML actually beats rules, and *where it does not generalise is reported* — that rigour is itself the contribution.
>
> **Honest caveat (state it, don't hide it):** this project's own external validation found the model does **not** generalise well beyond its small dataset (see [§25.2](#252-squat-model--grading-limitations-module-b), items 6–7) — 98 reps from 9 people, so it may have partly learned quirks of that group rather than universal biomechanics. ML adds genuine value over pure rules *in principle* (catching interactions a person would not think to hand-code); how much is realised here is limited by how little labeled data was available.
>
> *One-line viva version:* "I don't use ML instead of thresholds — I use thresholds where a validated clinical cutoff exists (the fault gates) and ML for the part a threshold can't do: judging overall quality across many interacting features, where I showed empirically that a naive single-feature threshold can even point the wrong way."
>
> **Why does grading run after the set, not live, if rehab is about correcting form?** (a fair, strong challenge — answered head-on)
>
> **The framing: live feedback is *not* absent — the precise *grade* is deferred.** The split is **immediate low-risk cues live, accurate grade the instant the set ends** — not "nothing live."
>
> 1. **Live feedback already exists, kept deliberately light.** During the set the frontend gives real-time capture-quality, body-visibility, camera-alignment warnings, a rep counter, and a rough movement-band estimate — the things that are safe and cheap to say in real time. Running the full pipeline (rep splitting + 13 features + ML inference + fusion) on every video frame would add latency for no benefit and defeat the privacy design (video never leaves the browser).
> 2. **An accurate grade physically requires a *completed* rep.** "Did you reach parallel depth?" is only defined at the bottom of the movement; "was your tempo consistent?" needs the rep(s) to be over. A grade produced mid-rep would be a **wrong** grade — and in rehab, confidently telling someone the wrong thing mid-movement is worse than telling them the right thing a second later.
> 3. **Safety / non-diagnostic boundary.** Flashing "bad form, stop!" from a noisy half-computed mid-rep estimate could make a user jerk or alter their movement — an injury risk. Acting on unreliable real-time signals contradicts the conservative, non-diagnostic design; high-confidence feedback delivered the moment the set ends is safer to act on.
> 4. **It mirrors how a physiotherapist actually works** — quick nudges *during* ("keep going, a bit deeper"), detailed correction and explanation *after* the set, not a paragraph mid-squat. And for rehab the real feedback loop is per-**session over weeks**, which is exactly what the post-session report + progress dashboard deliver.
>
> **Honest scope:** true per-rep real-time coaching (an instant "that rep was too shallow" the moment a rep finishes) is a genuine enhancement, documented as future work (the optional WebSocket per-rep push, [§11.2](#112-optional-enhancement)). It was not built because MVP priority was a complete, deployed, evaluated, *safe* pipeline first — defensible scoping, named as future work rather than hidden. This ties to the ML-scores-first-rep-only limitation above: making the ML score every rep is the same piece of future work that would enable richer live per-rep grading.
>
> *One-line viva version:* "The immediate, low-risk guidance — stay in frame, keep going, roughly on track — happens live. The precise 'this rep was poor and here's why' comes the moment the set ends, because an accurate grade requires a completed rep and acting on a noisy mid-rep judgment is itself an injury risk. It's the same way a physio nudges during and explains after."



### 10.2 Module B Output

> **Note:** field names below match the actual `sessions`/`module_b_results`/`module_b_error_tags`/`feedback_texts` schema in [§13](#13-postgresql-database-design). **Updated 2026-07-20** to the current as-built shape after Stages 5.13–5.23 (per-rep ML voting, the Stage 5.18 headline-score redefinition, and the `rep_count`/`target_rep_count` fields) — the previous version of these examples predated Stage 5.13 and showed a single-rep-only shape with `score` equal to the raw ML value, which is no longer how the headline score works. See [§10.4](#104-fusion-scoring) for the score formula and why it changed.

**Example A — 10 attempts, 9 rule-clean-and-ML-passed, 1 rejected by the ML alone (no named fault):**

```json
{
  "session_id": "uuid",
  "mode": "rehab_grading",
  "exercise_type": "squat",
  "capture_quality": 0.86,
  "rep_count": 10,
  "target_rep_count": 10,
  "score": 9.0,
  "band": "Good",
  "confidence": 0.87,
  "model_version": "squat-1.0.0+rehab246-loso-<shorthash>",
  "feature_schema_version": "1.0.0",
  "metrics_json": {
    "rule_score": 7.2,
    "rule_subscores": [
      { "code": "rom_completeness", "score": 7.5, "notes": [] },
      { "code": "tempo_consistency", "score": 9.3, "metrics": { "cv": 0.04 } },
      { "code": "stability_control", "score": 9.7, "notes": [] }
    ],
    "ml_score": 8.7,
    "fusion_weights": { "w_rule": 0.0, "w_ml": 1.0 },
    "fusion_flags": [],
    "placeholder_model_notice": false,
    "capture_quality": {
      "q": 0.86,
      "valid_frame_ratio": 0.94,
      "capture_quality_band": "good"
    },
    "per_rep_summaries": [
      {
        "rep_index": 0,
        "bottom_knee_flexion_deg": 101.3,
        "ml_score": 8.38,
        "confidence": 0.838,
        "counted_good": true,
        "failed_gates": []
      },
      {
        "rep_index": 1,
        "bottom_knee_flexion_deg": 98.1,
        "ml_score": 8.03,
        "confidence": 0.803,
        "counted_good": false,
        "failed_gates": []
      }
    ]
  },
  "error_tags": [
    {
      "tag": "model_only_rejection",
      "severity": "Low",
      "source": "ml",
      "message": "Flagged by the movement model — no specific fault identified"
    }
  ],
  "structured_feedback": "Grade: Good. No specific issues were flagged for this set.",
  "rewritten_feedback": "Solid set — your form held up well across all ten reps...",
  "feedback_source": "llm",
  "llm_attempted": true,
  "disclaimer_version": "v2",
  "created_at": "timestamp"
}
```

`score: 9.0` is `10 × 9 good ÷ 10 attempts` (Stage 5.18) — not the mean `ml_score` (`8.7`, shown separately in `metrics_json` for transparency, and never equal to `score` unless every rep happens to agree). `rep_index: 1` shows the mechanism behind Example A's one rejection: no `failed_gates`, but its own `ml_score` (8.03) sits just under `decision_threshold` (8.447974), so the ML alone rejects it — surfaced as the honestly-named `model_only_rejection` tag rather than silently under-counting.

**Example B — a fault-gate override: the ML alone would have said Good, but a depth fault forces that rep to Poor:**

```json
{
  "session_id": "uuid",
  "exercise_type": "squat",
  "capture_quality": 0.81,
  "rep_count": 20,
  "target_rep_count": 10,
  "score": 2.0,
  "band": "Poor",
  "confidence": 0.82,
  "model_version": "squat-1.0.0+rehab246-loso-<shorthash>",
  "feature_schema_version": "1.0.0",
  "metrics_json": {
    "rule_score": 6.9,
    "ml_score": 8.0,
    "fusion_weights": { "w_rule": 0.0, "w_ml": 1.0 },
    "fusion_flags": [],
    "per_rep_summaries": [
      {
        "rep_index": 0,
        "bottom_knee_flexion_deg": 42.7,
        "ml_score": 8.89,
        "confidence": 0.889,
        "counted_good": false,
        "failed_gates": ["insufficient_depth"]
      }
    ]
  },
  "error_tags": [
    {
      "tag": "insufficient_depth",
      "severity": "High",
      "source": "rule",
      "message": "Didn't reach enough depth — bend your knees to about 80° or more (thighs near parallel)."
    }
  ],
  "structured_feedback": "Grade: Needs Improvement. Didn't reach enough depth — bend your knees to about 80° or more (thighs near parallel).",
  "rewritten_feedback": null,
  "feedback_source": "template",
  "llm_attempted": false,
  "disclaimer_version": "v1",
  "created_at": "timestamp"
}
```

> **What the two examples show:** in Example B, rep 0's own `ml_score` (8.89, above `decision_threshold: 8.447974`) would count it Good on the ML's judgment alone — but its peak knee flexion (42.7°) is far below the depth-gate threshold (78.04°), so the fault gate **overrides** `counted_good` to `false` regardless of the ML score. This is the fault-gate override layer described in [§10.4](#104-fusion-scoring) acting exactly as designed: interpretable rules win over an opaque score when they disagree — and, per the live measurement recorded in [§25.2](#252-squat-model--grading-limitations-module-b) item 8, this disagreement is common, not an edge case: the shallower a rep, the *higher* the ML tends to score it, on this dataset. The internal `band` value stays lowercase `"poor"`/`"good"` in the database/model; the UI displays `"poor"` as **"Needs Improvement"**.

> **Placeholder-model note:** during Phase 4 (before Phase 5 trains the real model), `model_version` reads `"stub-0"` and the response/report both carry a visible placeholder-model notice — see task.md Phase 4 Stage 4.5. `model_version` has been unchanged since Stage 5.8 — Stages 5.11/5.12 changed only the decision policy on top of the model, not the model itself.



### 10.3 Why Extra Trees Classifier

Extra Trees Classifier is chosen because the ML input is expected to be **tabular pose-derived features**, not raw video.

> **Update (2026-07-15):** the illustrative feature vector below is superseded by squat's actual, decided `FeatureVector` (side-view-computable only, valgus deliberately excluded) — see task.md Phase 4 Stage 4.2 for the full definition table with landmarks and `[clinical norm]`/`[dataset-derived]`/`[proposed heuristic]` tags per feature:

```text
knee_flex_peak_deg
knee_flex_min_deg
knee_rom_deg
hip_flex_peak_deg
trunk_lean_peak_deg
trunk_lean_mean_deg
knee_ang_vel_max_dps
rep_duration_s
descent_ascent_ratio
symmetry_index_pct
ankle_df_proxy_deg
hip_mid_jitter_norm
stance_width_norm
```

Reasons:

- Suitable for structured/tabular data.
- Works better than deep learning when dataset size is limited.
- Handles non-linear relationships between movement features.
- More robust than a single decision tree.
- Fast inference for deployed applications.
- Easier to explain in final report using feature importance.
- Fits the hybrid approach: rule-based logic provides transparency, Extra Trees provides flexible classification.



### 10.4 Fusion Scoring

The final score combines rule-based score and ML score.

```text
S_final = w_rule * S_rule + w_ml * S_ml
where w_rule + w_ml = 1
```

> **Update (2026-07-16, resolved during Phase 4–7 planning — see [§24](#24-additions-and-deviations-from-the-original-plan)):** the "recommended initial weights" and capture-quality example below were a starting illustration only; the fusion planning for Phase 4/5 fully supersedes them. **Starting default (Phase 4, before training):** `w_rule = 0.4` / `w_ml = 0.6` — the opposite split from the original recommendation below, chosen so the plan doesn't over-trust an untrained stub model's rule-derived placeholder score. **This default is not final** — Phase 5 Stage 5.6 sweeps `w_rule` from 0.2–0.8 and picks the winner empirically, evaluated against **both macro-F1 and the severe-misclassification rate** (Poor↔Good confusions specifically), not precision alone, because telling a poor-form user they're fine is the failure mode that matters most for a rehab-grading system. The result is written back into `backend/app/module_b/core/config.py` and retagged `[dataset-derived]`.

Recommended initial weights (superseded by the update above — kept here for historical reference):

```text
w_rule = 0.6
w_ml = 0.4
```

Reason: The rule-based score is more transparent and safer. ML confidence can be uncertain due to public dataset limitations.

**Actual capture-quality/confidence adaptive rule (Phase 4 Stage 4.5, replacing the illustrative 3-tier example below):**

```text
If ML confidence is high (max(P) >= confidence_low_threshold) AND Q >= q_min:
  w_rule = 0.4, w_ml = 0.6         (the Stage 5.6-tuned value, once available)
Else (low ML confidence OR Q < q_min):
  w_rule = 0.7, w_ml = 0.3         # rule-heavy fallback
  band is forced to Fair, low_confidence flag raised
```

Original illustrative example (superseded — kept for historical reference; the real gate uses a single `q_min` threshold plus a `confidence_low_threshold`, not three capture-quality tiers):

```text
If capture_quality >= 0.80:
  w_rule = 0.6, w_ml = 0.4
If 0.70 <= capture_quality < 0.80:
  w_rule = 0.8, w_ml = 0.2
If capture_quality < 0.70:
  do not produce final confident score; ask user to retry
```

**As-built squat decision policy (Phase 5 Stages 5.11 + 5.12, 2026-07-19 — this is what actually ships):**

The squat model itself was trained, calibrated and LOSO/nested-CV-evaluated in Phase 5 and then **left byte-identical**; Stages 5.11 and 5.12 changed only the *decision policy* on top of it, not the model.

1. **Committed binary band (Stage 5.11).** The three-band output relied on `Fair` as an *abstention* — the fusion layer forced `Fair` whenever calibrated confidence fell below 0.85. The shipped model's confidence never exceeds ~0.76, so that override fired on almost every rep and `Poor` was effectively never shown (three-band recall(Poor) ≈ 0.077). HY chose to make squat **commit** to Good/Poor so the app can actually flag poor form. This is implemented as a per-exercise `band_policy` in `SQUAT_CONFIG`: fusion weights `w_rule = 0.0` / `w_ml = 1.0`, and a single cut on the fused 0–10 score at `decision_threshold = 8.447974` (chosen for maximum macro-F1 on the out-of-fold predictions). `band_policy = None` (the default) preserves the original three-band abstention for Module A and the retired lunge, byte-for-byte. **The trade-off is explicit and accepted:** out-of-fold recall(Poor) rises 0.077 → **1.000**, at the cost of flagging **22/72 (31%) of Good reps as Poor**; critically **0** poor-form reps are ever called Good, so the app never tells a poor-form user they are fine.
2. **Interpretable fault gates (Stage 5.12).** Because the fused score is opaque (it can't say *why* a rep was bad), three interpretable rule gates run on **every** rep as a separate override layer (not blended into any score):

```text
depth gate       : knee_flex_peak_deg  <  78.04°   (clinical parallel norm 90° minus the pipeline's measured -11.96° under-read)
lean gate        : trunk_lean_peak_deg >= 41.42°   (data-driven, Youden-J on the training set)
heel-rise gate   : heel_rise_peak_norm >= 0.084    (data-driven, Youden-J; rule-only, not an ML feature)

If any gate fails on a rep -> that rep is not counted, with a specific named error tag,
regardless of the ML verdict. A rep counts as clean only if it clears the ML threshold
AND passes every gate.
```

The depth gate is **not** data-driven from REHAB24-6 (that dataset's own depth signal is inverted — its incorrect reps are actually deeper), so it is anchored to the clinical parallel-squat norm instead.

1. **Low-confidence handling still applies.** A low-`Q` / low-confidence rep still surfaces a `low_confidence` system error tag, but the band now still commits (it no longer abstains to Fair for squat).
2. **Correction — the ML classifier now scores every rep, not just the first (Stage 5.13, 2026-07-19).** Item 2 above originally said the fault gates existed partly to compensate for the ML scoring only `feature_vectors[0]`. That gap was closed the same day: `score_set()` now runs the calibrated classifier over **every rep's own feature vector** and builds a `RepVerdict` (`ml_score`, `confidence`, `ml_passed`, `failed_gates`, `counted_good`) for each one; the set's band is a **strict majority vote** across all of them, not a single fused score. Voting (rather than averaging) deliberately keeps the per-rep cut at the value it was calibrated at — a mean over reps has a much narrower spread, so the same cut would mean something different — and it is what lets a single bad rep's per-rep verdict actually count against the set.
3. **Correction — the headline 0–10 score is no longer the ML value at all (Stage 5.18, 2026-07-20).** Real webcam testing surfaced a session that scored 8.0/10 next to a "Needs Improvement" band — a direct contradiction, because the old headline score was the **mean of the per-rep** `ml_score` while the band was a **majority vote**, two different quantities that could disagree. Root cause, confirmed on real captured sessions: the classifier's score is **anti-correlated** with the depth fault it is meant to help judge (gate-failing reps averaged a *higher* `ml_score`, 8.845, than gate-clean reps, 8.807, in the session that surfaced this) — the same REHAB24-6 label-inversion already documented in [§25.2](#252-squat-model--grading-limitations-module-b) item 7, now measured live rather than only on the external EC3D set. The headline score was redefined to `10 × good_reps ⁄ total_reps` — the share of reps that were both fault-gate-clean and ML-passed — which makes `band == "Good"` and `score > 5.0` true by construction; they can no longer contradict. The mean `ml_score` is unchanged and still shown on its own card for transparency, it just no longer drives the headline number. See [§10.2](#102-module-b-output)'s examples for the corrected shape and [§25.2](#252-squat-model--grading-limitations-module-b) item 8 for the live-measured scale of the disagreement this fixed.

---



## 11. Live Feedback Strategy

To avoid latency issues after deployment, the live session should not depend heavily on backend round trips.

### 11.1 Recommended MVP Strategy

During live session, the frontend should calculate simple live indicators locally:

- capture quality
- body visibility
- camera alignment warning
- approximate movement band
- timer/rep count
- simple cue such as “keep body visible” or “movement detected”

After the set ends, the backend performs the final scoring and ML inference.

### 11.2 Optional Enhancement

If there is enough time, add WebSocket support for periodic backend feedback.

Do not start with WebSocket unless the main REST-based flow is stable.

---



## 12. Pose Processing and Feature Pipeline



### 12.1 Frontend Processing

The frontend should:

1. Start webcam.
2. Load MediaPipe Pose.
3. Extract landmarks per frame.
4. Display skeleton overlay.
5. Calculate visibility/capture quality.
6. Store temporary landmark sequence in browser memory during session.
7. Send only summarized landmarks/features to backend when the set ends.



### 12.2 Backend Processing

The backend should:

1. Validate incoming payload.
2. Check mode and exercise type.
3. Apply preprocessing if needed.
4. Calculate feature summary.
5. Route to Module A or Module B.
6. Generate score/band/error tags.
7. Store results.
8. Return report response.



### 12.3 Preprocessing Methods

Use:

- Confidence-based filtering
- Missing keypoint handling for short gaps
- One Euro smoothing or simpler moving average for MVP
- Normalization based on body segment length
- Windowing or repetition segmentation

If implementation time is limited, start with:

```text
confidence filtering + simple moving average + basic feature extraction
```

Then upgrade to One Euro Filter later.

---



## 13. PostgreSQL Database Design



### 13.1 Why PostgreSQL

PostgreSQL is used because this project has structured relationships:

```text
one user → many sessions
one session → one module result
one module B result → many error tags
one user → many reminders
one user → many feedback reports
```

This supports:

- ERD creation
- data integrity
- session history
- progress trend queries
- better final report explanation
- Cloud SQL deployment on Google Cloud



### 13.2 Recommended Tables



#### users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```



#### user_profiles

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    age_group VARCHAR(50),
    exact_age INTEGER, -- added for WBLT's McBride age-band lookup; see §24
    gender VARCHAR(50),
    height_cm NUMERIC(5,2),
    weight_kg NUMERIC(5,2),
    user_type VARCHAR(50),
    focus_area VARCHAR(50),
    self_reported_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```



#### exercise_catalog

```sql
CREATE TABLE exercise_catalog (
    id UUID PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    mode VARCHAR(50) NOT NULL,
    description TEXT,
    view_guidance VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

Seed data:

```text
sit_to_stand, Functional Check
supported_single_leg_stance, Functional Check
weight_bearing_lunge_test, Functional Check
squat, Rehab Grading            # replaces module_b_placeholder_exercise
```

> **Update:** `module_b_placeholder_exercise` is superseded now that the exercise is decided (squat). Note for whoever touches the exercise catalog: `ExerciseSelection.tsx` has no hardcoded placeholder branch of its own — it renders whatever this table returns via `exerciseService.list()` — so changing the offered exercises means updating this seed row, not editing the frontend component.



#### sessions

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercise_catalog(id),
    mode VARCHAR(50) NOT NULL,
    exercise_type VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    capture_quality NUMERIC(4,3),
    valid_frame_ratio NUMERIC(4,3),
    device_info TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```



#### module_a_results

```sql
CREATE TABLE module_a_results (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    completion_time_sec NUMERIC(8,3),
    hold_duration_sec NUMERIC(8,3),
    rep_count INT,
    rom_band VARCHAR(50),
    stability_proxy NUMERIC(8,4),
    sway_proxy NUMERIC(8,4),
    symmetry_proxy NUMERIC(8,4),
    trunk_lean_proxy NUMERIC(8,4),
    final_band VARCHAR(50) NOT NULL,
    confidence_level VARCHAR(50),
    metrics_json JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```



#### module_b_results

> **Update:** replaced the original all-flat-columns design below with a **hybrid** schema. Flat, typed, exercise-agnostic columns for what the dashboard queries directly by `WHERE`/`ORDER BY`/aggregate (mirrors the `sessions.score`/`sessions.band` precedent this repo already uses for Module A); a JSONB column for the part that's genuinely variable-shape across exercises (squat's three rule sub-scores aren't guaranteed to match any future Module B exercise's). The named `rom_score`/`tempo_score`/`stability_score` columns below assumed every Module B exercise has exactly those three sub-scores — not a safe assumption for a registry of exercise plugins — so they moved into JSONB instead of staying named columns.

```sql
CREATE TABLE module_b_results (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    exercise_code VARCHAR(100) NOT NULL,
    score NUMERIC(5,2),
    band VARCHAR(50),
    confidence NUMERIC(5,4),
    model_version VARCHAR(100),
    feature_schema_version VARCHAR(20),
    q NUMERIC(5,4),
    metrics_json JSONB,          -- rule_score, ml_score, w_rule/w_ml actually used,
                                  -- rule sub-score breakdown, feature_vector, per-rep summaries
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Original all-flat design (superseded — kept for historical reference):

```sql
CREATE TABLE module_b_results (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    rule_score NUMERIC(5,2),
    ml_score NUMERIC(5,2),
    final_score NUMERIC(5,2),
    final_band VARCHAR(50),
    ml_label VARCHAR(50),
    ml_confidence NUMERIC(5,4),
    rom_score NUMERIC(5,2),
    tempo_score NUMERIC(5,2),
    stability_score NUMERIC(5,2),
    fusion_weights_json JSONB,
    feature_summary_json JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```



#### module_b_error_tags

> **Renamed from** `error_tags` (2026-07-16) to make the FK direction unambiguous now that it references `sessions` directly rather than `module_b_results` — needed so Phase 7 Stage 7.1's "common error tags" panel can `GROUP BY tag` across sessions without an extra join, and so a rejected/low-Q attempt that never produced a `module_b_results` row can still (in principle) be tagged. Added `source` to distinguish rule-derived tags from ML-derived and system tags (task.md Phase 6 Stage 6.1's taxonomy has both).

```sql
CREATE TABLE module_b_error_tags (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    severity VARCHAR(50),
    source VARCHAR(20),          -- 'rule' | 'ml' | 'system'
    message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```



#### feedback_texts

> **Update (2026-07-16, resolved during Phase 4–7 planning — see [§24](#24-additions-and-deviations-from-the-original-plan)):** `llm_used BOOLEAN` collapsed two different situations into one bit — "the LLM was never called" and "the LLM was called but Stage 6.3's safety filter rejected the output" both read as `FALSE`, losing exactly the information an examiner would ask about. Replaced with `feedback_source` + `llm_attempted` so both cases are distinguishable (`source="template"` + `attempted=true` = tried and rejected; `attempted=false` = never tried). Dropped stored `safety_disclaimer` text — the disclaimer the user actually sees always comes from the current i18n render (rules.md #19), so storing a duplicate copy per row is redundant; `disclaimer_version` gives audit-grade traceability ("this session was shown disclaimer v2") without duplicating text that already lives in i18n.

```sql
CREATE TABLE feedback_texts (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    structured_feedback TEXT,
    rewritten_feedback TEXT,
    feedback_source VARCHAR(20) NOT NULL DEFAULT 'template',  -- 'llm' | 'template'
    llm_attempted BOOLEAN NOT NULL DEFAULT FALSE,
    provider VARCHAR(50),
    model_version VARCHAR(100),
    disclaimer_version VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Original design (superseded — kept for historical reference):

```sql
CREATE TABLE feedback_texts (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    structured_feedback TEXT,
    rewritten_feedback TEXT,
    llm_used BOOLEAN NOT NULL DEFAULT FALSE,
    safety_disclaimer TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```



#### reminders

```sql
CREATE TABLE reminders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    reminder_time TIMESTAMP NOT NULL,
    frequency VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---



## 14. Backend API Design



### 14.1 Auth APIs

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```



### 14.2 User Profile APIs

```text
GET  /api/users/me/profile
PUT  /api/users/me/profile
```



### 14.3 Exercise APIs

```text
GET /api/exercises
GET /api/exercises/{exercise_code}
```



### 14.4 Session APIs

```text
POST /api/sessions/start
POST /api/sessions/{session_id}/end
GET  /api/sessions
GET  /api/sessions/{session_id}
```



### 14.5 Module A APIs

```text
POST /api/module-a/analyze
GET  /api/module-a/results/{session_id}
```

Sit-to-Stand is the only exercise left on this shared endpoint. SLS and WBLT
each have their own dedicated router instead, because their result contracts
differ from the shared single-buffer shape (see §24):

```text
POST /api/sls/analyze
POST /api/sls/support
GET  /api/sls/session/{session_id}

GET  /api/wblt/config
POST /api/wblt/analyze
GET  /api/wblt/session/{session_id}
```



### 14.6 Module B APIs

`POST /analyze` and `GET /results/{session_id}` stay generic, resolved the same way
Module A resolved this in §14.5: a thin router dispatching by `exercise_code`
through a **registry of exercise plugins** (task.md Phase 4 Stage 4.1), not a
per-exercise-code URL or a per-exercise duplicated router. The one addition
beyond the original plan is `GET /{code}/config`, added for the same reason
WBLT's `GET /api/wblt/config` was added beyond §14.5 — the frontend can't sync
its thresholds without a config endpoint to sync from (X7 in task.md's
Cross-Cutting Rules).

```text
GET  /api/module-b/{code}/config          -- added 2026-07-16, see above
POST /api/module-b/analyze                -- exercise_code carried in the request body
GET  /api/module-b/results/{session_id}
```



### 14.7 Report APIs

```text
GET  /api/reports/session/{session_id}
POST /api/reports/{session_id}/rewrite-feedback
```



### 14.8 Dashboard APIs

> **Update:** both endpoints below return their payload **keyed by** `exercise_type` in a single response (e.g. `{"sts": {...}, "sls": {...}, "wblt": {...}, "squat": {...}}`), not one call per exercise — this fixes the trend/band panels for every exercise (Module A + B) in one dashboard load. `error-tags` only has entries for Module B exercise types (Module A has warning tags, not error tags — the two vocabularies are kept separate).

```text
GET /api/dashboard/summary
GET /api/dashboard/trends            -- response keyed by exercise_type; accepts ?from=&to=
GET /api/dashboard/error-tags        -- response keyed by exercise_type (Module B only); accepts ?from=&to=
```

> **As-built note (Phase 7):** these three endpoints back **both** the Dashboard overview and the new `/progress` deep-dive page — the Progress page reuses `trends` and `error-tags` with the `from`/`to` range parameters (14d/30d/All), no extra endpoints. **MDC honesty:** `ExerciseTrend.mdc_source` is `"none"` (and `mdc = null`) for **every** exercise on the 0–10 composite score — no published MDC exists on that composite for any exercise, so the UI shows an honest "no meaningful-change threshold" caption rather than inventing one. (WBLT's real published MDC applies only to its raw distance/angle, shown per-session on the report, not on the dashboard's 0–10 trend.)



### 14.9 Reminder APIs

```text
GET    /api/reminders
POST   /api/reminders
PATCH  /api/reminders/{reminder_id}
DELETE /api/reminders/{reminder_id}
POST   /api/reminders/{reminder_id}/complete       -- mark done (sets last_completed_at)
GET    /api/reminders/{reminder_id}/export.ics     -- RFC-5545 .ics download (VEVENT + popup VALARM + RRULE)
```

> **As-built note (Phase 7 Stage 7.3):** reminders are now fully implemented (they were a hardcoded UI mock before). The `reminders` table gained nullable `exercise_code` (deep-link target — deliberately **not** an FK, so a reminder survives its exercise being retired) and `last_completed_at`. Delivery is **client-side, no email/scheduler infrastructure**: each reminder offers a **Google Calendar link** (`calendar.google.com/render`, no OAuth) and a downloadable `.ics` — the user's own calendar app fires the timed alert. In-app, a nav **red-dot badge** and a Dashboard **due-banner** appear only when a reminder is actually due (`is_due()` supports `once`/`daily`/`mwf`/`weekly`, failing closed on unknown frequencies). Clicking a reminder **deep-links straight into its exercise** (sets mode + exercise and navigates to camera setup). **Email verification on signup was explicitly scoped out** (it was the only ask that required building email infrastructure from scratch).

---



## 15. External LLM API Usage

> **Update (2026-07-15/16):** the default provider is **Groq / Llama 3.3 70B** (task.md Locked Assumptions #6, Phase 6 Stage 6.4); the template fallback (task.md Phase 6 Stage 6.2) is built **first**, before the LLM client, so the LLM is provably optional polish rather than a dependency. Groq's free-tier limits and exact model name must be re-verified at build time and the retrieval date recorded — free-tier model lists have drifted before.

The external LLM API is only used **after the set is completed**.

It must not:

- change the score
- change the band
- create new medical claims
- diagnose the user
- prescribe treatment

A dedicated safety filter (task.md Phase 6 Stage 6.3) enforces this on every LLM response **before** it is stored or shown: it strips/rejects diagnostic language, verifies the band/score in the rewritten text matches the structured input exactly (a mismatch discards the LLM output and falls back to the template), rejects any tag not present in the structured input, and caps length. A test asserts the grade is byte-identical before and after the rewrite.

Input to LLM:

```json
{
  "final_band": "fair",
  "final_score": 6.2,
  "error_tags": ["limited_range_of_motion", "unstable_tempo"],
  "structured_feedback": "Movement quality is fair. ROM score is lower than expected...",
  "safety_rules": [
    "Do not diagnose",
    "Do not prescribe treatment",
    "Keep feedback general and non-medical",
    "Recommend professional consultation for pain or uncertainty"
  ]
}
```

Output from LLM:

```json
{
  "rewritten_feedback": "Your movement quality was fair overall. You completed the set, but your range of motion and movement rhythm can be improved. Try to move in a more controlled way and make sure your full body remains visible to the camera. This is not a medical diagnosis."
}
```

Always store both:

- structured feedback
- rewritten feedback
- `feedback_source` (`"llm"` or `"template"`) and `llm_attempted` (whether the LLM was called at all, distinct from whether its output survived the safety filter) — see the updated `feedback_texts` schema in [§13](#13-postgresql-database-design)

The structured feedback is the trusted source. The LLM text is only a readability layer.

> **As-built note (Phase 6 complete, 2026-07-19):**
>
> - **Provider:** Groq, model `llama-3.3-70b-versatile` (the plan's `llama-3.3-70b` was a shorthand; the real production id was verified live against the Groq docs and API — free tier 30 RPM / 1,000 RPD / 12,000 TPM / 100,000 TPD).
> - **Disabled by default.** `feedback_llm_enabled` defaults to **False** — with the LLM off, the report is still fully populated by the deterministic **template fallback** (built *first*, on purpose), which proves the LLM is optional polish rather than a dependency. Enabling it in production is a config flip, not a code change.
> - **Template-first flow.** The template is always composed first; the LLM only overwrites `rewritten_feedback`/`feedback_source` **if** the safety filter accepts its output. On any error/timeout/429/empty-response/safety-rejection it silently falls back to the template. Timeout 8s, retry-once **only** on a 429.
> - **Safety filter (enforced before store/display):** rejects forbidden diagnostic phrases; verifies the band and score in the rewritten text match the structured input exactly (a mismatch discards the LLM text — the "Needs Improvement" relabel is accounted for so it isn't a false positive); rejects any taxonomy tag not in the structured input; caps length at 600 chars. A test asserts the grade is byte-identical before and after the rewrite.
> - **Scope: Module B (squat) only.** Confirmed against the proposal that the rewriting layer is a Module B component; Module A reports keep a static "General tip" panel and are **not** LLM-rewritten (a mislabelled "AI" panel on Module A was corrected to "General tip" during this phase).
> - **Payload carries only** band/score/confidence/rep_count/tags — never raw video, never health records. There is no live/per-frame LLM endpoint; the call happens only after the set is fully scored.

---



## 16. Suggested Project Folder Structure

```text
fyp-pose-rehab/
  README.md
  docker-compose.yml
  .env.example

  frontend/
    package.json
    vite.config.ts
    src/
      main.tsx
      App.tsx
      routes/
      pages/
        LandingPage.tsx
        LoginPage.tsx
        RegisterPage.tsx
        DashboardPage.tsx
        ModeSelectionPage.tsx
        ExerciseSelectionPage.tsx
        CameraSetupPage.tsx
        LiveSessionPage.tsx
        ReportPage.tsx
        SessionHistoryPage.tsx
        ReminderPage.tsx
      components/
        PoseCanvas.tsx
        WebcamPreview.tsx
        LiveBandIndicator.tsx
        CaptureQualityBadge.tsx
        ProgressChart.tsx
        ReportCard.tsx
      hooks/
        useAuth.ts
        useMediaPipePose.ts
        useSessionRecorder.ts
      services/
        apiClient.ts
        authService.ts
        sessionService.ts
        reportService.ts
      utils/
        poseFeatures.ts
        captureQuality.ts
        liveFeedback.ts
      types/
        pose.ts
        session.ts
        report.ts

  backend/
    pyproject.toml or requirements.txt
    Dockerfile
    app/
      main.py
      core/
        config.py
        security.py
      db/
        database.py
        models.py
        schemas.py
        migrations/
      api/
        auth_routes.py
        user_routes.py
        exercise_routes.py
        session_routes.py
        module_a_routes.py
        module_b_routes.py
        report_routes.py
        dashboard_routes.py
        reminder_routes.py
      services/
        auth_service.py
        session_service.py
        module_a_service.py
        module_b_service.py
        feature_service.py
        fusion_service.py
        report_service.py
        llm_service.py
      ml/
        models/
          placeholder_exercise_extra_trees.joblib
        train_extra_trees.py
        evaluate_model.py
        feature_schema.json
      tests/
        test_auth.py
        test_sessions.py
        test_module_a.py
        test_module_b.py

  docs/
    architecture.md
    api_contract.md
    database_schema.md
    deployment_guide.md
    evaluation_plan.md
```

---



## 17. Environment Variables



### Backend `.env`

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg://fyp_user:fyp_password@localhost:5432/fyp_rehab_db
JWT_SECRET_KEY=change_this_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
LLM_API_KEY=optional_for_later
LLM_API_BASE_URL=optional_for_later
CORS_ORIGINS=http://localhost:5173
```



### Frontend `.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_DEBUG_POSE=true
```

---



## 18. Local Development Setup Plan



### 18.1 Tools to Install

Install these first:

1. Git
2. VS Code
3. Node.js LTS
4. Python 3.11 or 3.12
5. Docker Desktop
6. DBeaver Community or pgAdmin
7. Google Cloud CLI, later when deployment starts



### 18.2 Local PostgreSQL with Docker

Use Docker instead of installing PostgreSQL directly.

`docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:17
    container_name: fyp_postgres
    environment:
      POSTGRES_USER: fyp_user
      POSTGRES_PASSWORD: fyp_password
      POSTGRES_DB: fyp_rehab_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---



## 19. Development Plan from 0 Progress

The phased development plan (Phase 0–9), recommended start order, and milestones are maintained in **[task.md](./task.md)**.

Use that file to track task progress. This document keeps architecture, design, and technical specifications. Additions to and deviations from this plan are tracked in [§24](#24-additions-and-deviations-from-the-original-plan).

Phase-by-phase status is not duplicated here since it drifts every session — always check [task.md](./task.md) directly for the current phase.

---



## 20. What to Start With Right Now

See **[task.md](./task.md)** for the recommended start order and first three milestones.

---



## 21. Coding Agent Rules



## Coding agent rules are maintained in **[rules.md](./rules.md)**. They must be followed on every development request.



## 22. Future Enhancements

These are optional and should not be built before the MVP works:

1. ASP.NET Core main backend with Python FastAPI ML microservice.
2. SignalR real-time communication.
3. More rehabilitation exercises.
4. More advanced ML models such as LSTM or CNN-LSTM.
5. Better camera angle detection.
6. More advanced personalization.
7. Cloud Build CI/CD pipeline.
8. Admin dashboard.
9. Multi-language support.
10. Raw landmark debug storage with strict privacy controls.

---



## 23. Final Implementation Priority

The most important priority is not to build the most complicated architecture.

The priority is to deliver a complete system that is:

- working
- deployed
- explainable
- safe
- evaluated
- aligned with the final proposal
- supported by clear database design
- supported by AI/ML evidence

The recommended MVP target is:

> A deployed React + FastAPI + PostgreSQL web application where users can log in, run MediaPipe webcam-based lower-limb checking, receive Good/Fair/Poor feedback, store results, view progress, and generate an after-set report using rule-based and ML-supported scoring.

---



## 24. Additions and Deviations from the Original Plan

This section records where the implementation **added to or diverged from** the plan above, so the differences are easy to cite in the final report's "deviations from plan" discussion. The rest of this document remains the as-planned specification; the phase-by-phase progress log lives in [task.md](./task.md).


| Area                                                                                                    | Original plan (this document)                                                                                                          | What was actually implemented                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Rationale                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Module A evaluation                                                                                     | No evaluation method specified for the rule-based checks — §9.3 only said Good/Fair/Poor bands would be "refined during pilot testing" | **Measurement-agreement evaluation** (ICC(2,1), Bland-Altman, Cohen's kappa) for the SLS hold-timer versus a human-timed reference — see [§9.4](#94-module-a-evaluation-measurement-agreement)                                                                                                                                                                                                                                                                                                                                                                | Module A is deterministic, not a trained classifier, so classifier-accuracy metrics do not apply; method-comparison statistics are the correct framing and fit the non-diagnostic boundary (§6)                                                                                                                                                                                        |
| SLS scope                                                                                               | "Supported Single-Leg Stance, front view, 30 seconds" as a single check (§9.1)                                                         | Rebuilt as a **both-legs, 45-second-cap** check with a lift-line entry gate and a ball-in-circle stability sub-score (Phase 3B rebuild, see task.md)                                                                                                                                                                                                                                                                                                                                                                                                          | Fuller and more defensible functional check; detailed in task.md                                                                                                                                                                                                                                                                                                                       |
| WBLT design                                                                                             | §9.1 listed WBLT as a single camera-measured "dorsiflexion ROM band" (3 trials, no user measurement, no age/sex norms)                 | Redesigned as **dual output**: the official band is a *user-measured* distance (ruler/tape, self-reported) scored against McBride et al. (2026) age/sex percentile bands; camera-measured dorsiflexion angle is kept as an unbanded secondary signal (corroboration, symmetry, trend). Requires the account's exact age (not the existing `age_group` range) to resolve the correct band — see the `exact_age` column above. Stage 1 (this build) covers one right-leg attempt end-to-end; guided 3-attempt bracketing and the left leg are follow-up stages. | Monocular depth/contact detection is unreliable on a single webcam (§5, non-diagnostic boundary), so camera-only ROM banding had no defensible clinical anchor. Self-measured distance unlocks a real published normative table instead of an invented cutoff; the camera's job narrows to what it *can* reliably judge (heel-lift validity), consistent with the SLS precedent above. |
| WBLT routing                                                                                            | §14.5 put WBLT on the shared `POST /api/module-a/analyze` endpoint (like STS)                                                          | Given a **dedicated** `/api/wblt/`* **router** (`GET /config`, `POST /analyze`, `GET /session/{id}`), mirroring SLS's precedent                                                                                                                                                                                                                                                                                                                                                                                                                               | The dual distance+angle, per-attempt contract doesn't fit the shared single-buffer response shape, exactly the same reasoning that put SLS on its own router                                                                                                                                                                                                                           |
| Module B fusion weights                                                                                 | §10.4 recommended initial weights `w_rule = 0.6` / `w_ml = 0.4`, with a 3-tier capture-quality example                                 | Phase 4 starting default is `w_rule = 0.4` / `w_ml = 0.6` (opposite split), superseded by Phase 5 Stage 5.6's empirical sweep against **macro-F1 and the severe-misclassification rate**, not precision alone; the adaptive rule is a binary confident/low-confidence switch (`q_min` + `confidence_low_threshold`), not the original 3-tier capture-quality table                                                                                                                                                                                            | An untrained Phase 4 stub model shouldn't be over-trusted by a rule-favoring default; the final weight needs to be earned against data, and the rehab-grading failure mode that matters most is telling a poor-form user they're fine, which precision alone doesn't directly measure — see task.md Phase 4 Stage 4.0 and Phase 5 Stage 5.6                                            |
| Module B `module_b_results` schema                                                                      | §13 defined all-flat typed columns (`rule_score`, `ml_score`, `rom_score`, `tempo_score`, `stability_score`, ...)                      | Hybrid: flat typed columns only for what Phase 7's dashboard queries directly (`score`, `band`, `confidence`, `model_version`, `q`, ...); rule sub-scores, feature vector, and per-rep summaries moved into JSONB `metrics_json`; `error_tags` renamed `module_b_error_tags` and keyed off `session_id` directly, with a `source` column added                                                                                                                                                                                                                | Named sub-score columns (`rom_score`/`tempo_score`/`stability_score`) assumed every Module B exercise has exactly those three sub-scores — not a safe assumption for a registry of exercise plugins; JSONB is for what's genuinely variable-shape, flat columns for what's genuinely queried — see task.md Phase 4 Stage 4.6                                                           |
| Module B `feedback_texts` schema                                                                        | §13/§15 had `llm_used BOOLEAN` + stored `safety_disclaimer` text                                                                       | Replaced with `feedback_source` (`"llm"`/`"template"`) + `llm_attempted BOOLEAN` + `provider`/`model_version` + `disclaimer_version`                                                                                                                                                                                                                                                                                                                                                                                                                          | `llm_used=FALSE` couldn't distinguish "never called" from "called, output rejected by the safety filter" — an examiner-relevant distinction; the disclaimer shown is always the current i18n render, so storing a duplicate text copy per row was redundant — a version id gives audit traceability instead — see task.md Phase 6 Stage 6.5                                            |
| Dashboard trend/error-tag payload shape                                                                 | §14.8 listed `GET /api/dashboard/trends` and `GET /api/dashboard/error-tags` without specifying response shape                         | Both endpoints return their payload **keyed by** `exercise_type` in one response, not one call per exercise                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Phase 7's goal is fixing the trend/band panels for every exercise (Module A + B) in a single dashboard load — see task.md Phase 7 Stage 7.0                                                                                                                                                                                                                                            |
| Squat live-session end condition                                                                        | §10/§14 never specified how a squat set (unlike STS's clinically-validated fixed 5 reps) should end                                    | Decided 2026-07-16: **unlimited reps**, live client-side counter, ended manually via a **"Finish Set"** button that posts the whole buffer once. Plus an **inactivity safety net** (~9s no motion after ≥1 rep prompts finish-or-continue, never auto-submits) and an **optional motivational rep-goal** (10–80, step 10, or blank) shown as "Rep X of Y" + a progress bar — display-only, never sent to grading, hitting it only prompts, never auto-finishes                                                                                                | A fixed rep count would be an uncited clinical threshold (unlike STS's 5) and a fixed time window can cut a rep mid-motion or reward a fast/sloppy squatter over a slow, controlled one; a user-owned motivational goal has no such grading risk since it's never sent to the backend — see task.md Phase 4 Stage 4.7                                                                  |
| Squat output: committed binary band                                                                     | §10 designed a three-band Good/Fair/Poor output for every Module B exercise                                                            | Squat commits to **binary Good/Poor** (no Fair), `Poor` displayed as **"Needs Improvement"**, `w_rule=0`/`w_ml=1`, single score cut at 8.447974 — a decision-policy change on an unchanged model (Stage 5.11). Module A + retired lunge keep three bands via a default `band_policy=None`. **Concrete example:** [§10.2 Example A](#102-module-b-output) — `ml_score: 9.4` above threshold → `band: "Good"`, no Fair possible                                                                                                                                 | The three-band scheme's `Fair` was an abstention that fired on ~every rep (model confidence never > ~0.76), so `Poor` was effectively unreachable (recall 0.077). Committing makes the app able to flag poor form (recall(Poor) → 1.0), accepting 31% false-alarm on Good reps but zero poor-called-Good — see task.md Phase 5 Stage 5.11                                              |
| Squat interpretable fault gates                                                                         | §10 planned a single fused ML+rule score with no per-rep rule override                                                                 | Added three **per-rep fault gates** (depth < 78.04°, lean ≥ 41.42°, heel-rise ≥ 0.084) as a separate override layer that forces `Poor` with a named reason if any gate fails on any rep (Stage 5.12); additive hook, model unchanged, no feature-schema bump. **Concrete example:** [§10.2 Example B](#102-module-b-output) — `ml_score: 9.42` (would band Good on its own) but `bottom_knee_flexion_deg: 73.7` trips the depth gate (< 78.04°) → band forced to `"Poor"` with tag `insufficient_depth`, ML overridden                                        | The fused score is opaque (can't say *why*) and the ML scores only rep 0; gates add an interpretable "why" and cover every rep for fault detection. Depth is anchored to the clinical parallel norm, not the training data (REHAB24-6's depth signal is inverted) — see task.md Phase 5 Stage 5.12                                                                                     |
| Squat error-tag taxonomy trimmed                                                                        | §10 illustrative taxonomy implied faults like asymmetry / stance width could be tagged                                                 | Taxonomy **reconciled to 5 tags** (3 fault-gate + `inconsistent_tempo` soft + `low_confidence` system); `knee_valgus`, `asymmetry`, `feet_too_wide` **excluded** as un-measurable from one side view                                                                                                                                                                                                                                                                                                                                                          | A single monocular side view cannot resolve frontal-plane valgus, far-limb asymmetry (occluded), or depth-axis stance width — tagging them would report noise. Documented in `docs/module_b_limitations.md` — see task.md Phase 6 Stage 6.1                                                                                                                                            |
| LLM default state + provider                                                                            | §15 implied the LLM rewrite is part of the normal flow                                                                                 | Groq `llama-3.3-70b-versatile`, **disabled by default** (`feedback_llm_enabled=False`); the deterministic template fallback is built first and fully populates the report with the LLM off; enabling is a config flip                                                                                                                                                                                                                                                                                                                                         | Proves the LLM is optional polish, not a dependency; keeps the demo working with no external egress unless deliberately enabled at Phase 8 — see task.md Phase 6 Stages 6.2/6.4                                                                                                                                                                                                        |
| Reminders delivery mechanism                                                                            | §11/§13 planned a `reminders` table with add/view/complete, delivery unspecified                                                       | Client-side delivery: **Google Calendar link + downloadable** `.ics` (no backend email, no scheduler, no OAuth); in-app due-alert badge/banner; reminder deep-links into its exercise. Email verification on signup explicitly skipped                                                                                                                                                                                                                                                                                                                        | Avoids building email/scheduler/OAuth infrastructure from scratch; the user's own calendar app fires the real timed alert — see task.md Phase 7 Stage 7.3                                                                                                                                                                                                                              |
| Progress deep-dive page                                                                                 | §8.1 listed 11 pages; no dedicated per-exercise progress page                                                                          | Added a 12th page (`/progress`): one-exercise-at-a-time trend deep dive with a Functional/Rehab category selector, date-range control, band zones, capture-quality trend, and a ranked error-tag chart (Module B only)                                                                                                                                                                                                                                                                                                                                        | The Dashboard's multi-exercise overview becomes unreadable if each exercise shows full-detail sub-trends; the deep dive is where a per-exercise trend line is actually legible — see task.md Phase 7 Stage 7.1b                                                                                                                                                                        |
| Module B ML classifier scored rep 0 only                                                                | Not planned either way — an implementation gap introduced in Phase 5, not a documented design choice                                   | **Corrected at Stage 5.13** (2026-07-19): the calibrated classifier now scores every rep's own feature vector independently; the set's band is a strict majority vote across all per-rep verdicts, not a single fused score                                                                                                                                                                                                                                                                                                                                   | The rep-0-only gap was already flagged as a known limitation (former §25.2 item 10); closing it removed a real blind spot rather than leaving it "mitigated" by the fault gates alone — see task.md Stage 5.13                                                                                                                                                                         |
| Module B headline score = mean ML value                                                                 | §10.4 specified `S_final = w_rule·S_rule + w_ml·S_ml` as both the displayed score and the band input                                   | **Redefined at Stage 5.18** (2026-07-20) to `10 × good_reps ⁄ total_reps` (share of clean reps), decoupled from the ML value entirely; the mean `ml_score` stays visible on its own card but no longer drives the headline number                                                                                                                                                                                                                                                                                                                             | Real testing surfaced a session scoring 8.0/10 next to a "Needs Improvement" band; root cause was the ML score running anti-correlated with the depth fault (confirmed live: gate-failing reps scored *higher* on average than clean ones), the same REHAB24-6 inversion documented in item 7 of [§25.2](#252-squat-model--grading-limitations-module-b) — see task.md Stage 5.18/A    |
| Module B report clarity (rep target, attempts wording, unreconciled rejections, bullets, depth wording) | Not specified at this level of detail                                                                                                  | Session now persists the user's chosen rep target (`target_rep_count`); the report relabels the raw rep count "Attempts" (vs. counted-good reps); reps rejected by the ML alone with no named fault get their own line ("flagged by the movement model") so every attempt is accounted for; list bullets (broken by a Tailwind reset) restored; the depth-fault message quotes the actual gate angle instead of "closer to parallel"                                                                                                                          | Real webcam testing surfaced all four as concrete confusions in one session's report — see task.md Stage 5.19–5.21/C                                                                                                                                                                                                                                                                   |
| Module B live-session layout                                                                            | §11 specified live cues only in general terms, no layout                                                                               | Live feedback (rejected/counted-rep verdict) promoted to the most prominent panel, directly under the HUD; the redundant "Rep X of Y" status box removed (the HUD already shows it); the panel persists the last verdict rather than clearing after a timeout                                                                                                                                                                                                                                                                                                 | Real webcam testing showed corrective feedback was easy to miss at exercising distance from the screen — see task.md Stage 5.20/D                                                                                                                                                                                                                                                      |




*These are enhancements consistent with the project goals in §23, not departures from the MVP priorities. This list covers the deviations identified so far — add further rows here as the implementation continues to evolve.*

---



## 25. Current System Limitations (for the Final Report)

This section is a **single consolidated list of the current version's known limitations**, written so they can be lifted directly into the final report's limitations chapter. An examiner reads a named limitation as rigour and an unnamed one as oversight — so every limitation below is stated with *what* it is, *why* it exists, and (where relevant) *what would reverse it*. These are the limits of the system **as it will be presented for user testing**; user-testing feedback may add usability limitations on top of these.

Sources of truth: `task.md` (Phases 5–7), `docs/module_b_limitations.md`, `ml/reports/SQUAT_EVALUATION_REPORT_2BAND.md` (+ `_3BAND`), and `ml/reports/PHASE5_CHAPTER_DRAFT.md`. Where a number is quoted, re-verify it against the live report before final submission — several are computed from a fixed corpus and will move if the corpus changes.

### 25.1 Monocular single-camera limitations (whole system)

1. **Depth axis is unreliable.** A single webcam resolves the plane facing it well but resolves the camera-depth axis worst. Every feature that lives on that axis was either dropped or down-weighted. This is the root cause of several limitations below.
2. **Frontal-plane faults are not measured at all.** Knee valgus / knock-knee is **deliberately excluded** from features, rules, tags, and evaluation — it is ill-posed from a sagittal (side) view. *(Excluded, not unimplemented.)*
3. **Far-limb occlusion.** From one side view the far limb is partly occluded (far-knee visibility ≈ 0.59–0.78 vs near-side ≈ 0.95–0.99). This is why left/right **asymmetry is not tagged** — the feature did not track true inter-leg difference against mocap (r ≈ −0.05) and the model ranked it near-last.
4. **Stance width is not tagged.** In profile the feet separate mainly along the depth axis; the stance-width feature was below chance in-sample (AUC 0.37) and inverted on external data, so a `feet_too_wide` tag would fire on noise.
5. **No true 3D / clinical goniometry.** All angles are 2D projections from image landmarks; the system is explicitly **non-diagnostic** and reports conservative Good/Fair/Poor bands, not exact clinical degrees.



### 25.2 Squat model & grading limitations (Module B)

1. **Small dataset.** The squat model is trained/evaluated on **98 side-view reps from 9 subjects (72 Good / 26 Poor)**, out-of-fold. Per-cell counts are small integers — a single rep changing hands moves a rate by several points. Treat all squat metrics as order-of-magnitude, not precise.
2. **The "Poor" construct is population-specific and did not transfer.** The classifier learned "resembles REHAB24-6's *incorrect* reps", which in that cohort skew **deeper and faster** — not a clinical "you exceeded a safe angle" rule. On the external EC3D set this construct **did not transfer** (and partly inverted). The model is a within-dataset quality proxy, not a validated clinical grader. **Now also confirmed live (2026-07-20)**, on two of HY's own real webcam sessions, not just the EC3D dataset: depth vs. `ml_score` correlates at **r = −0.975** on a session with zero rule faults (deeper reps scored *lower*), and reps that failed the depth gate for being too shallow averaged a *higher* `ml_score` (9.04) than gate-clean reps (7.87) — the inversion is not a dataset artifact, it reproduces on this exact camera/pipeline in normal use.
3. **Committing to binary Good/Poor gives up the zero-severe-error guarantee (by design).** At the shipped operating point, **recall(Poor) = 1.000** but **22/72 (31%) of Good reps are flagged Poor** (false alarms) *in-sample*. The safer direction is preserved — **0** poor-form reps are ever called Good — but a well-performed rep being told "Needs Improvement" is a real and expected failure mode. **Live measurement (2026-07-20) suggests the real-world rate runs well above the in-sample figure**: across two real sessions, 21 reps passed every rule gate, and 17 of them (81%) were still rejected by the ML alone — consistent with `core/set_scoring.py`'s own documented caveat that per-rep errors are not independent within one subject/camera/session, so the true whole-set failure rate is higher than an independence assumption would predict.
4. **The ROM rule is inverted for this population, so fusion is pure-ML (**`w_rule = 0`**).** The rule rewards depth, but in the training data incorrect reps are deeper; the empirical sweep therefore weighted the rule to zero. The rule sub-scores are still shown for transparency but do not drive the squat band or, since Stage 5.18, the headline score.
5. ~~**The ML scores only the first rep of a set.~~ Resolved at Stage 5.13 (2026-07-19).** This limitation is no longer accurate and is kept here, struck through, so anyone cross-referencing an earlier draft or citation of this document can see it was corrected rather than silently disappearing. The calibrated classifier now scores every rep's own feature vector independently, and the set's band is a majority vote across all of them — see [§10.1](#101-module-b-pipeline) and [§10.4](#104-fusion-scoring) item 4.
6. **The depth gate threshold is clinically anchored, not data-driven.** Depth < 78.04° = clinical parallel norm (90°) minus the pipeline's measured −11.96° under-read. It is **not** learned from REHAB24-6 because that dataset's own depth signal is inverted. The lean (41.42°) and heel-rise (0.084) gates are data-driven (Youden-J) on the same small sample.
7. **No published MDC / repeatability threshold on the 0–10 score.** The dashboard shows trends with **no "meaningful change" claim** for any exercise because no published MDC exists on the composite score. Small trend movements may be measurement noise. *(WBLT does have a published MDC, but only on raw distance/angle, shown per-session — not on the 0–10 trend.)*
8. **Only one Module B exercise ships (squat).** The leg lunge was investigated and then **removed** (2026-07-19); the second Module B exercise seen in earlier planning no longer exists. The architecture remains a registry of exercise plugins, so this is a scope limit, not an architectural one.



### 25.3 Module A (functional check) limitations

1. **SLS stability is frontal-plane only.** The single-leg-stance ball-in-circle stability sub-score is scored in the image plane; sway toward/away from the camera is not captured (monocular-depth limitation).
2. **SLS agreement is validated on a synthetic corpus, not real pilot recordings.** The ICC(2,1) ≈ 0.995 / kappa ≈ 0.857 / Bland-Altman figures come from a fixed-seed **synthetic** replay corpus — no real pilot recordings exist yet. There is a small systematic bias (system reads ≈ 0.75 s shorter than a stopwatch) from the FSM's drop-hysteresis frames.
3. **STS and WBLT have no measurement-agreement harness yet.** Only SLS has a replay/agreement evaluation; the same framing is planned but not built for STS completion-time and WBLT dorsiflexion-ROM.
4. **WBLT's official band relies on user self-measurement.** The banded output uses a **self-reported** ruler/tape distance scored against McBride et al. age/sex norms; the camera angle is only a secondary corroboration signal. Accuracy depends on the user measuring correctly, and it requires the account's **exact age** (not just an age range).
5. **All Module A thresholds are heuristic/prototype values.** Band cutoffs are starting heuristics to be refined with pilot data, not clinically validated cut points.



### 25.4 LLM / feedback limitations

1. **The LLM rewrite is disabled by default and Module-B-only.** With `feedback_llm_enabled=False` (the default), users see the deterministic **template** feedback, not LLM-rewritten text. Module A reports are never LLM-rewritten (they show a static "General tip"). If the demo is run with the LLM off, no AI-rewritten coaching text appears at all.
2. **LLM output is best-effort and can silently fall back.** On any timeout / rate-limit (429) / safety-filter rejection, the system falls back to the template with no user-visible error. The LLM never changes the grade, band, score, or tags (enforced by the safety filter), so it is a readability layer only — but the polish is not guaranteed to appear. **This actually happened (2026-07-20):** a `.env` model id (`llama-3.3-70b-instruct`) that Groq doesn't host degraded every report to the template for hours, invisibly, because it's exactly this failure mode working as designed — compounded by the backend having no logging configuration at all, so the diagnostic lines the code already emitted on this exact failure were silently discarded rather than shown. Fixed (Stage 5.23): corrected the model id, and added `core/logging_config.py` so `llm_failed`/`llm_rejected`/`llm_used`/`llm_disabled` are always visible.
3. **External dependency + free-tier limits when enabled.** When enabled, feedback depends on Groq's free tier (30 RPM / 1,000 RPD / 12,000 TPM / 100,000 TPD) and outbound egress; not yet decided/verified for the deployed Cloud Run demo (Phase 8, open question Q8).



### 25.5 Platform / operational limitations

1. **Not yet deployed.** Phase 8 (Google Cloud deployment) is not complete; the system runs locally (FastAPI + Postgres + Vite dev server). User testing is against a local instance unless deployment lands first.
2. **Camera capture cannot run in a sandboxed/automated browser.** Live webcam + MediaPipe requires a real browser with camera permission; this is a testing-environment limitation, not a product defect, but it means some flows can only be verified manually.
3. **No email verification / password recovery.** Signup does not verify email and there is no account-recovery flow (email infrastructure was deliberately scoped out).
4. **Reminder alerts are client-side only.** There is no server-side push/email; timed alerts fire only if the user adds the reminder to their own calendar (Google Calendar link / `.ics`). The in-app badge/banner only shows while the app is open.
5. **Single-language grade values in the DB.** Band values are stored in English (`good`/`fair`/`poor`); the UI translates them (en/zh/ms), and `poor` is displayed as "Needs Improvement" — but any raw DB inspection shows the internal English values.
6. **Demo/seed data is clearly marked, not real model runs.** The multi-session demo account uses `model_version="demo-seed"` rows; it exists to exercise the dashboard/progress panels, not to represent real captured sessions.

> **Before final submission:** re-run the evaluation harnesses and re-quote any number cited above from the live report files, and fold in whatever usability limitations the post-user-testing questionnaire surfaces.

