# FYP Project Description and Implementation Plan

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
      - [user\_profiles](#user_profiles)
      - [exercise\_catalog](#exercise_catalog)
      - [sessions](#sessions)
      - [module\_a\_results](#module_a_results)
      - [module\_b\_results](#module_b_results)
      - [error\_tags](#error_tags)
      - [feedback\_texts](#feedback_texts)
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
    - [Backend `.env`](#backend-env)
    - [Frontend `.env`](#frontend-env)
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

The exact rehab exercise is not decided yet. The system must be designed as an **exercise-specific grading module** so that the exercise can be configured later.

### 10.1 Module B Pipeline

```text
User selects Rehab Grading mode
→ user selects exercise type
→ frontend starts webcam and MediaPipe Pose
→ landmarks extracted in browser
→ frontend performs capture quality check and lightweight live cue
→ after set ends, frontend sends session landmark/features summary to backend
→ backend preprocesses/validates features
→ rule-based sub-scores are calculated
→ Extra Trees model predicts quality label and confidence
→ error tags are generated
→ rule score and ML score are fused
→ final report is generated
→ external LLM API rewrites structured feedback
→ results are stored in PostgreSQL
```

### 10.2 Module B Output

```json
{
  "session_id": "uuid",
  "mode": "rehab_grading",
  "exercise_type": "placeholder_exercise",
  "capture_quality": 0.86,
  "rule_score": 7.2,
  "ml_score": 6.8,
  "final_score": 7.0,
  "final_band": "good",
  "ml_label": "good",
  "ml_confidence": 0.78,
  "sub_scores": {
    "rom_completeness": 7.5,
    "tempo_consistency": 6.8,
    "stability_control": 7.1
  },
  "error_tags": [
    {
      "tag": "minor_tempo_inconsistency",
      "severity": "low",
      "message": "Your movement speed was slightly inconsistent."
    }
  ],
  "structured_feedback": "Your overall movement quality was good...",
  "rewritten_feedback": "Good job. Your movement was mostly controlled...",
  "created_at": "timestamp"
}
```

### 10.3 Why Extra Trees Classifier

Extra Trees Classifier is chosen because the ML input is expected to be **tabular pose-derived features**, not raw video.

Example feature vector:

```text
knee_angle_min
knee_angle_max
knee_rom
hip_displacement
trunk_lean_proxy
tempo_mean
tempo_variability
stability_proxy
symmetry_proxy
valid_frame_ratio
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

Recommended initial weights:

```text
w_rule = 0.6
w_ml = 0.4
```

Reason: The rule-based score is more transparent and safer. ML confidence can be uncertain due to public dataset limitations.

If capture quality is low:

```text
increase rule weight
reduce ML weight
or return low-confidence warning instead of confident grade
```

Example:

```text
If capture_quality >= 0.80:
  w_rule = 0.6, w_ml = 0.4
If 0.70 <= capture_quality < 0.80:
  w_rule = 0.8, w_ml = 0.2
If capture_quality < 0.70:
  do not produce final confident score; ask user to retry
```

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
module_b_placeholder_exercise, Rehab Grading
```

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

#### error_tags

```sql
CREATE TABLE error_tags (
    id UUID PRIMARY KEY,
    module_b_result_id UUID NOT NULL REFERENCES module_b_results(id) ON DELETE CASCADE,
    tag_code VARCHAR(100) NOT NULL,
    severity VARCHAR(50),
    message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### feedback_texts

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

```text
POST /api/module-b/analyze
GET  /api/module-b/results/{session_id}
```

### 14.7 Report APIs

```text
GET  /api/reports/session/{session_id}
POST /api/reports/{session_id}/rewrite-feedback
```

### 14.8 Dashboard APIs

```text
GET /api/dashboard/summary
GET /api/dashboard/trends
GET /api/dashboard/error-tags
```

### 14.9 Reminder APIs

```text
POST   /api/reminders
GET    /api/reminders
PUT    /api/reminders/{reminder_id}
DELETE /api/reminders/{reminder_id}
```

---

## 15. External LLM API Usage

The external LLM API is only used **after the set is completed**.

It must not:

- change the score
- change the band
- create new medical claims
- diagnose the user
- prescribe treatment

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

The structured feedback is the trusted source. The LLM text is only a readability layer.

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

**Current Phase 1 order:** Phase 1A (UI clickable prototype) → Phase 1B (register/login, JWT, sessions, backend wiring). See §8.0 and [task.md](./task.md) Phase 1.

---

## 20. What to Start With Right Now

See **[task.md](./task.md)** for the recommended start order and first three milestones.

---

## 21. Coding Agent Rules

Coding agent rules are maintained in **[rules.md](./rules.md)**. They must be followed on every development request.
---

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

| Area                | Original plan (this document)                                                                                                          | What was actually implemented                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Rationale                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Module A evaluation | No evaluation method specified for the rule-based checks — §9.3 only said Good/Fair/Poor bands would be "refined during pilot testing" | **Measurement-agreement evaluation** (ICC(2,1), Bland-Altman, Cohen's kappa) for the SLS hold-timer versus a human-timed reference — see [§9.4](#94-module-a-evaluation-measurement-agreement)                                                                                                                                                                                                                                                                                                                                                                | Module A is deterministic, not a trained classifier, so classifier-accuracy metrics do not apply; method-comparison statistics are the correct framing and fit the non-diagnostic boundary (§6)                                                                                                                                                                                        |
| SLS scope           | "Supported Single-Leg Stance, front view, 30 seconds" as a single check (§9.1)                                                         | Rebuilt as a **both-legs, 45-second-cap** check with a lift-line entry gate and a ball-in-circle stability sub-score (Phase 3B rebuild, see task.md)                                                                                                                                                                                                                                                                                                                                                                                                          | Fuller and more defensible functional check; detailed in task.md                                                                                                                                                                                                                                                                                                                       |
| WBLT design         | §9.1 listed WBLT as a single camera-measured "dorsiflexion ROM band" (3 trials, no user measurement, no age/sex norms)                 | Redesigned as **dual output**: the official band is a _user-measured_ distance (ruler/tape, self-reported) scored against McBride et al. (2026) age/sex percentile bands; camera-measured dorsiflexion angle is kept as an unbanded secondary signal (corroboration, symmetry, trend). Requires the account's exact age (not the existing `age_group` range) to resolve the correct band — see the `exact_age` column above. Stage 1 (this build) covers one right-leg attempt end-to-end; guided 3-attempt bracketing and the left leg are follow-up stages. | Monocular depth/contact detection is unreliable on a single webcam (§5, non-diagnostic boundary), so camera-only ROM banding had no defensible clinical anchor. Self-measured distance unlocks a real published normative table instead of an invented cutoff; the camera's job narrows to what it _can_ reliably judge (heel-lift validity), consistent with the SLS precedent above. |
| WBLT routing        | §14.5 put WBLT on the shared `POST /api/module-a/analyze` endpoint (like STS)                                                          | Given a **dedicated `/api/wblt/*` router** (`GET /config`, `POST /analyze`, `GET /session/{id}`), mirroring SLS's precedent                                                                                                                                                                                                                                                                                                                                                                                                                                   | The dual distance+angle, per-attempt contract doesn't fit the shared single-buffer response shape, exactly the same reasoning that put SLS on its own router                                                                                                                                                                                                                           |

_These are enhancements consistent with the project goals in §23, not departures from the MVP priorities. This list covers the deviations identified so far — add further rows here as the implementation continues to evolve._
