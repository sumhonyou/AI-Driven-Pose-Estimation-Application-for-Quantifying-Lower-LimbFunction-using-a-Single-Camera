# FYP Project Description and Implementation Plan

> ⚠️⚠️⚠️ **Leg Lunge exercise removed (2026-07-19, HY's decision).** Squat is
> the only Module B rehabilitation-grading exercise. This document has been
> updated so its architecture and design sections describe the squat-only
> system as currently built; it no longer plans for a second Module B
> exercise. For the retained historical record of the lunge investigation
> (data audit, feature engineering, model training, and the reasons for its
> removal), see [task.md](./task.md)'s Phase 5B section.

> **Document last synced to codebase: 2026-07-25, through Phase 10 (UAT
> Remediation, Stages R1–R14).** Moderated user acceptance testing (22
> participants) has now run, and its findings drove a large round of
> correctness fixes and UX rework across live feedback (§11.3), the
> instruction/camera-setup flow, the post-session Report (§8.1), Progress/
> Dashboard charts, and Reminders (§14.9). See [§24](#24-additions-and-deviations-from-the-original-plan)
> for the full list of what changed and why, and [§25](#25-current-system-limitations-for-the-final-report)
> for the resulting limitations. Phase 8 (Google Cloud deployment) has not
> started; the system described throughout runs locally.

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
    - [11.3 As-Built Live Feedback (Phase 10)](#113-as-built-live-feedback-phase-10)
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
- Module B: squat (the only Module B exercise; see the header banner)
- **Update (Phase 10 Stage R10/R10-follow-ups):** each card shows only its image/icon, a view+reps eyebrow, and its title — the exercise description, the mode/"Configurable" chip row, and a "why this exercise" blurb were all tried on-card and then removed for visual clarity per HY's direct feedback; "why this exercise" now lives on the Instructions page instead (see page 6.5 below)

7. **Exercise Instructions Page** _(added in Phase 10 Stage R9 — route_ `/instructions`_, sits between Exercise Selection and Camera Setup)_

- One shared template (`config/exerciseInstructions.ts` + `pages/ExerciseInstructions.tsx`) driving all 4 exercises: a looping/static demo media panel, a numbered-steps "document" card, a camera-angle reference photo + expected view, and a footer CTA into Camera Setup
- A non-diagnostic "why this exercise" purpose+benefit blurb (Stage R10), reused from the shared glossary/why-text source
- A per-exercise equipment note where relevant (Stage R9.1: STS → chair, SLS → chair/wall, WBLT → wall, squat → none)
- The last numbered step always states the exercise's real consequence rule in plain language (e.g. SLS: "if your foot drops back below the line, the hold ends immediately and is recorded as-is"; squat: a failed rep is flagged and doesn't count toward the target)
- Text/media only — no embedded live webcam; camera positioning still happens on the next page

8. **Camera Setup Page**

- Webcam preview
- Pose skeleton overlay
- Body visibility check
- Capture quality indicator
- **Update (Phase 10 Stage R9.1):** the separate "View guidance" panel and "Watch Demo" panel were removed once the Instructions page (above) took over that content — Camera Setup now shows only the live preview, a body-visibility banner, and (once the whole body is steadily detected) the auto-start countdown ring. There is no manual "Start session" button; the session always starts automatically once framing is stable for 5 seconds (`AUTO_START_STABLE_MS`, Stage R5)

9. **Live Session Page** _(one component per exercise: STS / SLS / WBLT / squat)_

- Webcam feed, pose overlay, timer, rep or hold progress
- **Unmistakable RECORDING state** (Stage R5): a pulsing red "Recording" badge, a red border glow around the camera stage, and a short start tone — uniform across all 4 pages, each preceded by the same 5-second countdown (STS previously auto-recorded with no countdown at all)
- **Large corrective-cue pop-out** (`LiveCueOverlay`, Stage R4): on a rejected rep/fault, a big glanceable title + specific subheading takes over the screen with a 10-second auto-dismiss countdown, tone-coloured to match the persistent feedback panel; auto-clears on the next good rep. Wired into squat, STS, and SLS (incl. a new SLS "wrong leg lifted" detector); not yet built for WBLT
- **Spoken (TTS) cues** (Stage R6): session start/end, per-fault corrective cues (all simultaneous faults on a rep are read, not just the primary one), and an SLS "which leg" announcement — a `SpeechCueQueue` speaks them sequentially, throttled per fault key; a mute toggle (`AudioCueToggle`, defaults **on**) sits in every live page's topbar and the shared dashboard topbar
- **Exercise demo overlay** (`ExerciseDemoOverlay`, Stage R7): a small looping reference clip (squat/STS: GIF, WBLT: muted looping video) or static reference photo (SLS) pinned to the top-right corner of the camera stage, opposite the capture-quality badge
- **SLS-specific overlay redesign** (Stage R8): the old corner "stability ball" card and side lift-line bar were replaced with a transparent ball-and-ring centred directly over the video and a horizontal lift-line drawn across the video at the calibrated height — both read against the user's own on-screen body instead of an abstract side widget. A short labelled legend appears once before the first hold; the 45-second cap now shows as a visible countdown; the per-leg result screen leads with the headline (hold/band/score) and collapses secondary detail behind a toggle
- Stop/end set button (squat: "Finish Set", unlimited reps with an inactivity safety net and an optional user-set motivational rep-goal, never sent to grading)

10. **Post-Performance Report Page**

- Final score, final band (squat: binary Good / "Needs Improvement", no Fair — §10.4), rule-based sub-scores, confidence, error tags, coaching feedback text, non-diagnostic reminder
- **Update (Phase 10 Stage R11 — full redesign):** reordered by importance (band/score → coaching + error tags → sub-scores → comparison → technical details, coaching moved up from the very bottom of the page); the raw ML-prediction row was dropped from the main view (redundant with confidence — both derive from the same probability) and moved into a collapsed "Technical details" section together with the rule score and fusion weights; squat's 3 rule sub-scores are now an interactive colour-coded bar chart (hover for score + definition) instead of static cards; error-tag severity now has a distinct icon _and_ colour per level (colour-blind safe) plus a legend and a count badge; a **Retry exercise** button and a real **back** button were added (the page previously had neither); the non-diagnostic disclaimer is now an always-visible badge next to the band chip rather than a separate banner further down the page
- **Squat "Valid reps" metric** (Stage R12): a new row beside "Attempts" showing the counted-good rep total, so Attempts + Valid reps together explain the headline score directly (`score = 10 × valid ÷ attempts`)
- Glossary tooltips (Stage R10) on ROM completeness, valid rep, dorsiflexion, symmetry index, hold time, stability, capture quality, plus STS-specific tooltips on knee ROM proxy, trunk lean, attempted reps, and squat's tempo consistency / stability control (Stage R10 follow-up) — not every metric has one, by explicit scope decision

11. **Session History Page**

- List of previous sessions, filter by mode/exercise, plus a **date-range filter** (7d/14d/30d/90d/All, Stage R12) matching the Progress page's own range picker
- No back button (it is a primary sidebar destination, not a drill-down "detail" view — Report already has its own back button; Stage R14 corrected an earlier Stage R12 pass that had added one here)

12. **Reminder Page** _(fully rebuilt, Phase 7 Stage 7.3, then reworked in Phase 10 Stage R13)_

- Add / view / mark-complete reminders, sorted **newest-created first** (was soonest-scheduled first, which buried a reminder just created if it was scheduled far out)
- Creating a reminder now opens a follow-up "add to your calendar?" view with the Google Calendar link and `.ics` download for the reminder just made, instead of just closing the form
- The calendar event title now includes the linked exercise's name (`"{title} — {exercise name}"`), not just the reminder's own title
- **Auto-tick scoped to the launched reminder:** completing a session **opened from a specific reminder's card** automatically marks _that_ reminder done — not any other active reminder that happens to share the same exercise. A launching reminder id is carried through the session flow and consumed exactly once at session completion (or cleared if the session is cancelled/abandoned)
- A distinct "Open exercise" button replaces the previously-silent whole-card click, so it can no longer be confused with the separate "mark complete" checkbox
- Moved from the sidebar's "Account" group into "Overview" (Reminders is a frequent destination, not an account-settings page)

13. **Progress Deep-Dive Page** _(added in Phase 7 — route_ `/progress`_, see [§24](#24-additions-and-deviations-from-the-original-plan))_

- Per-exercise trend deep dive (one exercise at a time, chosen via a category selector: Functional Checking / Rehab Grading)
  - Date-range control (14 days / 30 days / All)
  - Score trend chart with Good/Fair/Poor band zones and an explicit "Score" Y-axis label (Stage R14 micro-fix)
  - Band distribution for the selected exercise
  - **Second per-exercise chart** (Stage R12 — replaces the unanimously-rejected capture-quality trend, UAT's one clearly-negative chart): STS shows completion time + avg rep time; SLS shows best hold per leg, with a "Both legs / Left / Right" selector to isolate one line when the combined view reads as cluttered (Stage R12 follow-up); WBLT shows best reach distance per leg; squat shows valid-rep volume (counted vs. rejected)
  - Module B only: ranked error-tag bar chart
  - Score trend's band-zone boundaries are per-exercise (Stage 5.22): squat uses its real binary cut (`Good` iff `score > 5.0`, no Fair zone) instead of the shared Good/Fair/Poor 7/4 cutoffs, which never matched squat's actual voting rule
  - Complements the Dashboard's multi-exercise "at a glance" overview (the Dashboard shows small-multiples across all exercises; the Progress page shows one exercise in full detail)
- **Dashboard drill-down** (Stage R12): the Dashboard's own Band Distribution and Common Error Tags panels — previously always pooled across every exercise — gained an "All exercises" / per-exercise dropdown filter each, plus a glossary tooltip explaining the Good/Fair/Poor bands

---

## 9. Module A: Functional Checking

Module A uses deterministic rule-based quantification. It does not require machine learning training.

### 9.1 Functional Checks

| Check                       | View Guidance        | Reps/Duration | Main Outputs                                            |
| --------------------------- | -------------------- | ------------- | ------------------------------------------------------- |
| Sit-to-Stand                | Side view            | 5 reps        | Completion time, knee ROM band, trunk lean proxy, grade |
| Supported Single-Leg Stance | Front view preferred | 30 seconds    | Hold duration, sway/stability proxy, grade              |
| Weight-Bearing Lunge Test   | Side view            | 3 trials      | Dorsiflexion ROM band, symmetry proxy, grade            |

> **Update (Phase 10 Stage R2, 2026-07-24):** SLS's lift/drop confirmation was originally gated on a fixed number of consecutive frames (`SLS_LIFT_PERSIST_FRAMES = 3`), which — since MediaPipe runs on `requestAnimationFrame` rather than a fixed frame rate — could be well under 0.1s on a fast machine, inside normal foot jitter (UAT: "the lifting too sensitive"). Fixed by switching to a real elapsed-time dwell: `SLS_LIFT_MIN_DWELL_SEC = 0.15`, `SLS_DROP_MIN_DWELL_SEC = 0.10` (`backend/app/module_a/sls/config.py`), mirrored identically in the frontend's live tracker so the on-screen timer matches the backend's authoritative recompute. Geometry (lift-line height, hysteresis margin) was unchanged; re-running the SLS measurement-agreement harness (§9.4) after the fix reproduced byte-identical results, confirming the dwell change didn't regress agreement.

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
> **The framing that defuses the question: this system does not use ML _instead of_ thresholds — it uses both, each where it is justified.** Where a validated clinical cutoff exists (squat-to-parallel depth, forward-lean, heel-lift), an explicit **rule** is used — those are the transparent, clinically-anchored fault gates. ML is used only for the part a single threshold **cannot** do. So an examiner's "just set an angle threshold" is not rejected — it is already in the system as the fault gates.
>
> 1. **A threshold is one number on one feature; "good form" is many features interacting.** A rep can hit perfect depth but with a collapsing trunk, uneven tempo, and wobble. To grade _overall_ quality with rules you would have to hand-write a combination formula across all 13 features **and hand-pick every weight and interaction term** (e.g. "shallow depth is acceptable _if_ ankle mobility is limited"). Every one of those numbers is a guess. The model learns those weights from labeled data, and the **feature-importance ranking can be reported as evidence** — a threshold gives no importance, no weighting, no principled way to combine features.
> 2. **The strongest single point: a hand-picked assumption was empirically _wrong_, and only the data caught it.** The obvious rule "deeper squat = better" seemed safe. But in the labeled training data the reps marked _incorrect_ were actually **deeper** on average — the opposite of the assumption. A designer setting that threshold by hand would have graded backwards. This is the thesis in one fact: **hand-set thresholds encode the designer's assumptions, which can be false; a trained model learns the real relationship from ground truth.** When the fusion weight was chosen empirically it drove `w_rule → 0`, i.e. on this data the ML carried signal the rules did not.
> 3. **ML gives a confidence/probability; a threshold gives only a hard yes/no.** The calibrated classifier outputs `P(Good)`, which the system uses to flag low-confidence reps. A bare threshold has no notion of "borderline."
> 4. **It is the methodological contribution being assessed — done honestly.** Module B is specified as a hybrid rule + ML system; building the full pipeline (feature engineering → training → calibration → cross-validation → **external validation on EC3D**) is a core deliverable. Crucially, the honest scientific step was taken: it was _tested_ whether ML actually beats rules, and _where it does not generalise is reported_ — that rigour is itself the contribution.
>
> **Honest caveat (state it, don't hide it):** this project's own external validation found the model does **not** generalise well beyond its small dataset (see [§25.2](#252-squat-model--grading-limitations-module-b), items 6–7) — 98 reps from 9 people, so it may have partly learned quirks of that group rather than universal biomechanics. ML adds genuine value over pure rules _in principle_ (catching interactions a person would not think to hand-code); how much is realised here is limited by how little labeled data was available.
>
> _One-line viva version:_ "I don't use ML instead of thresholds — I use thresholds where a validated clinical cutoff exists (the fault gates) and ML for the part a threshold can't do: judging overall quality across many interacting features, where I showed empirically that a naive single-feature threshold can even point the wrong way."
>
> **Why does grading run after the set, not live, if rehab is about correcting form?** (a fair, strong challenge — answered head-on)
>
> **The framing: live feedback is _not_ absent — the precise _grade_ is deferred.** The split is **immediate low-risk cues live, accurate grade the instant the set ends** — not "nothing live."
>
> 1. **Live feedback already exists, kept deliberately light.** During the set the frontend gives real-time capture-quality, body-visibility, camera-alignment warnings, a rep counter, and a rough movement-band estimate — the things that are safe and cheap to say in real time. Running the full pipeline (rep splitting + 13 features + ML inference + fusion) on every video frame would add latency for no benefit and defeat the privacy design (video never leaves the browser).
> 2. **An accurate grade physically requires a _completed_ rep.** "Did you reach parallel depth?" is only defined at the bottom of the movement; "was your tempo consistent?" needs the rep(s) to be over. A grade produced mid-rep would be a **wrong** grade — and in rehab, confidently telling someone the wrong thing mid-movement is worse than telling them the right thing a second later.
> 3. **Safety / non-diagnostic boundary.** Flashing "bad form, stop!" from a noisy half-computed mid-rep estimate could make a user jerk or alter their movement — an injury risk. Acting on unreliable real-time signals contradicts the conservative, non-diagnostic design; high-confidence feedback delivered the moment the set ends is safer to act on.
> 4. **It mirrors how a physiotherapist actually works** — quick nudges _during_ ("keep going, a bit deeper"), detailed correction and explanation _after_ the set, not a paragraph mid-squat. And for rehab the real feedback loop is per-**session over weeks**, which is exactly what the post-session report + progress dashboard deliver.
>
> **Honest scope:** true per-rep real-time coaching (an instant "that rep was too shallow" the moment a rep finishes) is a genuine enhancement, documented as future work (the optional WebSocket per-rep push, [§11.2](#112-optional-enhancement)). It was not built because MVP priority was a complete, deployed, evaluated, _safe_ pipeline first — defensible scoping, named as future work rather than hidden. This ties to the ML-scores-first-rep-only limitation above: making the ML score every rep is the same piece of future work that would enable richer live per-rep grading.
>
> _One-line viva version:_ "The immediate, low-risk guidance — stay in frame, keep going, roughly on track — happens live. The precise 'this rep was poor and here's why' comes the moment the set ends, because an accurate grade requires a completed rep and acting on a noisy mid-rep judgment is itself an injury risk. It's the same way a physio nudges during and explains after."

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

> **What the two examples show:** in Example B, rep 0's own `ml_score` (8.89, above `decision_threshold: 8.447974`) would count it Good on the ML's judgment alone — but its peak knee flexion (42.7°) is far below the depth-gate threshold (78.04°), so the fault gate **overrides** `counted_good` to `false` regardless of the ML score. This is the fault-gate override layer described in [§10.4](#104-fusion-scoring) acting exactly as designed: interpretable rules win over an opaque score when they disagree — and, per the live measurement recorded in [§25.2](#252-squat-model--grading-limitations-module-b) item 8, this disagreement is common, not an edge case: the shallower a rep, the _higher_ the ML tends to score it, on this dataset. The internal `band` value stays lowercase `"poor"`/`"good"` in the database/model; the UI displays `"poor"` as **"Needs Improvement"**.

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

The squat model itself was trained, calibrated and LOSO/nested-CV-evaluated in Phase 5 and then **left byte-identical**; Stages 5.11 and 5.12 changed only the _decision policy_ on top of it, not the model.

1. **Committed binary band (Stage 5.11).** The three-band output relied on `Fair` as an _abstention_ — the fusion layer forced `Fair` whenever calibrated confidence fell below 0.85. The shipped model's confidence never exceeds ~0.76, so that override fired on almost every rep and `Poor` was effectively never shown (three-band recall(Poor) ≈ 0.077). HY chose to make squat **commit** to Good/Poor so the app can actually flag poor form. This is implemented as a per-exercise `band_policy` in `SQUAT_CONFIG`: fusion weights `w_rule = 0.0` / `w_ml = 1.0`, and a single cut on the fused 0–10 score at `decision_threshold = 8.447974` (chosen for maximum macro-F1 on the out-of-fold predictions). `band_policy = None` (the default) preserves the original three-band abstention for Module A and the retired lunge, byte-for-byte. **The trade-off is explicit and accepted:** out-of-fold recall(Poor) rises 0.077 → **1.000**, at the cost of flagging **22/72 (31%) of Good reps as Poor**; critically **0** poor-form reps are ever called Good, so the app never tells a poor-form user they are fine.
2. **Interpretable fault gates (Stage 5.12).** Because the fused score is opaque (it can't say _why_ a rep was bad), three interpretable rule gates run on **every** rep as a separate override layer (not blended into any score):

```text
depth gate       : knee_flex_peak_deg  <  78.04°   (clinical parallel norm 90° minus the pipeline's measured -11.96° under-read)
lean gate        : trunk_lean_peak_deg >= 41.42°   (data-driven, Youden-J on the training set)
heel-rise gate   : heel_rise_peak_norm >= 0.071    (data-driven, Youden-J; near-leg-only — see the R1 update below)

If any gate fails on a rep -> that rep is not counted, with a specific named error tag,
regardless of the ML verdict. A rep counts as clean only if it clears the ML threshold
AND passes every gate.
```

The depth gate is **not** data-driven from REHAB24-6 (that dataset's own depth signal is inverted — its incorrect reps are actually deeper), so it is anchored to the clinical parallel-squat norm instead.

> **Update (Phase 10 Stage R1, 2026-07-24) — heel-rise gate false-positive fix.** UAT flagged the heel-rise gate firing on 3/18 sessions including at least one performed in genuinely good form. Root cause: `_heel_rise_peak_norm()` baselined against the rep's _first frame only_ and _averaged both legs_ — since squat is captured side-view and the far foot's landmarks are the least visible in the whole feature set (0.59–0.78 visibility vs. 0.95–0.99 for the near leg, §25.1 item 3), the occluded far foot's noise alone could manufacture phantom heel-rise. Fixed by switching the gate to **near-leg-only** (the camera-side leg, selected per rep by mean foot-landmark visibility, mirroring the pattern already proven in WBLT's `HeelLiftDetector`), a **settle-window median baseline** (first 3 frames, not frame 0), a **debounce** requiring the rise to be sustained across a 3-frame window (not a single-frame spike), and an **occlusion guard** that refuses to fire at all if even the near leg's visibility falls below 0.6 for the rep (fail-safe). The threshold was re-derived on the same construction against the labelled dataset: `0.08399 → 0.07098`, materially improving specificity (fewer false alarms on Good reps, in-sample 0.569 → 0.625) at a similar sensitivity. The client-side live mirror of this gate (used for the on-screen corrective cue, §11) was updated to the identical construction and threshold in the same stage.

1. **Low-confidence handling still applies.** A low-`Q` / low-confidence rep still surfaces a `low_confidence` system error tag, but the band now still commits (it no longer abstains to Fair for squat).
2. **Correction — the ML classifier now scores every rep, not just the first (Stage 5.13, 2026-07-19).** Item 2 above originally said the fault gates existed partly to compensate for the ML scoring only `feature_vectors[0]`. That gap was closed the same day: `score_set()` now runs the calibrated classifier over **every rep's own feature vector** and builds a `RepVerdict` (`ml_score`, `confidence`, `ml_passed`, `failed_gates`, `counted_good`) for each one; the set's band is a **strict majority vote** across all of them, not a single fused score. Voting (rather than averaging) deliberately keeps the per-rep cut at the value it was calibrated at — a mean over reps has a much narrower spread, so the same cut would mean something different — and it is what lets a single bad rep's per-rep verdict actually count against the set.
3. **Correction — the headline 0–10 score is no longer the ML value at all (Stage 5.18, 2026-07-20).** Real webcam testing surfaced a session that scored 8.0/10 next to a "Needs Improvement" band — a direct contradiction, because the old headline score was the **mean of the per-rep** `ml_score` while the band was a **majority vote**, two different quantities that could disagree. Root cause, confirmed on real captured sessions: the classifier's score is **anti-correlated** with the depth fault it is meant to help judge (gate-failing reps averaged a _higher_ `ml_score`, 8.845, than gate-clean reps, 8.807, in the session that surfaced this) — the same REHAB24-6 label-inversion already documented in [§25.2](#252-squat-model--grading-limitations-module-b) item 7, now measured live rather than only on the external EC3D set. The headline score was redefined to `10 × good_reps ⁄ total_reps` — the share of reps that were both fault-gate-clean and ML-passed — which makes `band == "Good"` and `score > 5.0` true by construction; they can no longer contradict. The mean `ml_score` is unchanged and still shown on its own card for transparency, it just no longer drives the headline number. See [§10.2](#102-module-b-output)'s examples for the corrected shape and [§25.2](#252-squat-model--grading-limitations-module-b) item 8 for the live-measured scale of the disagreement this fixed.

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

### 11.3 As-Built Live Feedback (Phase 10)

> **Update (Phase 10 Stages R4–R8, 2026-07-24).** §11.1's MVP strategy (local capture-quality/visibility checks, an approximate live band, a simple text cue) shipped as originally planned in earlier phases and stayed unchanged in its core architecture — REST-only, no per-frame backend round trip. UAT (Q9 = 3.38/5, the lowest-scoring item — feedback unreadable at 2–3m exercising distance) drove a substantial redesign of _what the local live layer actually shows and says_, all still frontend-only. WebSocket (§11.2) was never needed.

**Corrective-cue pop-out (`LiveCueOverlay`, Stage R4).** On a rejected rep or an active fault, a full-viewport, low-opacity, tone-coloured takeover shows a large corrective title (e.g. "Go deeper", "Chest up", "Heels down" — corrective wording, not a raw metric) with a specific subheading, a 10-second auto-dismiss countdown ring, and a manual dismiss control. It never blocks interaction (`pointer-events: none` on the backdrop) and auto-clears the moment the next rep is good. Wired into squat, STS, and SLS (including a new SLS-specific "wrong leg lifted" detector); **WBLT does not have this yet** — no rejected-attempt concept currently drives a live cue for it (§25 limitations).

**Unmistakable RECORDING state + one uniform start protocol (Stage R5).** Start was previously non-uniform (STS auto-recorded with **no** countdown at all; squat/SLS used a 5s countdown behind a button; WBLT used a 10s countdown) — the single most under-reported UAT issue (12/18 sessions). Every exercise now follows the same shape: **instructions → camera setup → 5-second countdown → recording**, with an unmistakable "you are being recorded" signal once recording starts — a pulsing red badge, a red border glow around the camera stage, and a short synthesized start tone (Web Audio oscillator, no bundled asset dependency).

**Spoken (TTS) live cues (Stage R6) — the most-requested new UAT feature (5 sessions + 5 comments).** A `SpeechCueQueue` speaks session start/end cues (which interrupt anything in progress) and per-fault corrective cues (queued and spoken sequentially, throttled per fault _key_ so two different simultaneous faults on the same rep are both announced, one after the other, never silently dropped). A mute toggle defaults **on** and appears in every live page's topbar plus the shared dashboard topbar; the spoken text always reuses the exact same string already shown visually, so voice and screen can never drift apart. Getting this reliably audible in a real browser required three follow-up fixes beyond the initial build: (1) a `cancel()`-then-`speak()`-in-the-same-tick Chromium race that could hang the speech engine indefinitely; (2) Chrome's user-activation gate on `speechSynthesis.speak()`, which a page that never calls it from inside a real click/keypress can silently violate (fixed with a one-shot silent "priming" utterance on the very first user interaction anywhere in the app); (3) a documented, longer-standing Chromium bug where the whole browser-process-level speech engine can wedge and stay silently dead across page reloads until the _browser itself_ restarts — mitigated (not fully cured) with a start-watchdog that retries once and then gives up cleanly rather than blocking the rest of the cue queue. See §25.4 for the resulting limitations (ms-MY voice availability, the wedge mitigation's honest scope).

**Exercise demo overlay (Stage R7).** A small looping reference clip (squat/STS: `.gif`; WBLT: muted looping `.mp4`) or static reference photo (SLS) is pinned to the top-right corner of the camera stage on all four live pages, opposite the capture-quality badge, so a user can check their form against a reference without leaving the page.

**SLS overlay redesign (Stage R8) — the exercise UAT scored worst overall (14/18 sessions flagged it).** The root cause was that the stability "ball" and the lift-line were both rendered as abstract widgets detached from the user's own body in frame, so their motion carried no felt meaning. The corner ball card and the side lift-line bar were replaced with a **transparent ball-and-ring centred directly over the video** (still the same scale-invariant metric ratio as before — deliberately _not_ a world→pixel hip projection, to avoid a fragile, inaccurate placement) and a **horizontal lift-line drawn across the video** at the calibrated height, reusing the same image-space coordinate system `PoseCanvas`'s own skeleton overlay already uses (so it shares that overlay's pre-existing, accepted `object-fit: cover` imprecision, not a new source of error). A short labelled legend appears once before the first hold; the 45-second cap now shows as a visible ticking countdown; the per-leg result screen leads with the headline number and collapses secondary detail behind a "Show details" toggle.

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
>
> **Further update (Phase 10 Stage R3, migration `20260724_0013`):** added a nullable `fallback_reason VARCHAR(80)` column. `feedback_source`/`llm_attempted` alone could say a rewrite fell back to the template but not _why_ — diagnosing an unexpectedly template-only report required a log-file search per session. `fallback_reason` is one of `none` / `llm_used` / `rate_limited` / `timeout` / `api_error` / `invalid_json` / `empty_response` / `guard_rejected:<safety-filter-reason>`, set on every attempt. It is diagnostic-only and deliberately **not** exposed on the API response model, so it never reaches the frontend — queryable directly against the table for support/debugging.

```sql
CREATE TABLE feedback_texts (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    structured_feedback TEXT,
    rewritten_feedback TEXT,
    feedback_source VARCHAR(20) NOT NULL DEFAULT 'template',  -- 'llm' | 'template'
    llm_attempted BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_reason VARCHAR(80),  -- added Stage R3: 'none' | 'llm_used' | 'rate_limited' |
                                   -- 'timeout' | 'api_error' | 'invalid_json' |
                                   -- 'empty_response' | 'guard_rejected:<reason>'
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
GET  /api/module-a/history          -- ?exerciseType=&limit= (pre-existing, not previously listed here)
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
>
> **Further update (Phase 10 Stage R13, 2026-07-25) — same endpoints, refined behaviour, no new routes:**
>
> - `GET /api/reminders` now orders **newest-created first** (`created_at DESC`, was soonest-scheduled-first) — a reminder scheduled far out no longer gets buried in the list right after being created.
> - `build_ics`/`build_google_calendar_url` (backing `POST /api/reminders` and `GET /{id}/export.ics`) now take the linked exercise's name and fold it into the calendar event title (`"{reminder title} — {exercise name}"`), so the event is identifiable once it's landed in the user's own calendar app, away from PhysioFit's UI.
> - **Auto-complete is scoped to the launching reminder, not "any reminder with a matching exercise":** the frontend session flow carries the id of the reminder a session was launched _from_ (if any) and calls the existing `POST /{id}/complete` exactly once, at real session completion — no backend change was needed for this, only how the frontend decides which id (if any) to call it with.
> - Creating a reminder (`POST /api/reminders`) is followed client-side by a "add to your calendar?" prompt surfacing the response's existing `google_calendar_url`/`ics_url` fields, rather than the form simply closing.

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
> - **Disabled by default.** `feedback_llm_enabled` defaults to **False** — with the LLM off, the report is still fully populated by the deterministic **template fallback** (built _first_, on purpose), which proves the LLM is optional polish rather than a dependency. Enabling it in production is a config flip, not a code change.
> - **Template-first flow.** The template is always composed first; the LLM only overwrites `rewritten_feedback`/`feedback_source` **if** the safety filter accepts its output. On any error/timeout/429/empty-response/safety-rejection it silently falls back to the template. Timeout 8s, retry-once **only** on a 429.
> - **Safety filter (enforced before store/display):** rejects forbidden diagnostic phrases; verifies the band and score in the rewritten text match the structured input exactly (a mismatch discards the LLM text — the "Needs Improvement" relabel is accounted for so it isn't a false positive); rejects any taxonomy tag not in the structured input; caps length at 600 chars. A test asserts the grade is byte-identical before and after the rewrite.
> - **Scope: Module B (squat) only.** Confirmed against the proposal that the rewriting layer is a Module B component; Module A reports keep a static "General tip" panel and are **not** LLM-rewritten (a mislabelled "AI" panel on Module A was corrected to "General tip" during this phase).
> - **Payload carries only** band/score/confidence/rep_count/tags — never raw video, never health records. There is no live/per-frame LLM endpoint; the call happens only after the set is fully scored.
>
> **Further update (Phase 10 Stage R3, 2026-07-24) — fallback diagnosability + prompt tightening:**
>
> - Every fallback now has a stored, queryable **reason** (`feedback_texts.fallback_reason`, §13) instead of only a log line — `none` / `llm_used` / `rate_limited` / `timeout` / `api_error` / `invalid_json` / `empty_response` / `guard_rejected:<specific safety-filter reason>`. Timeout is now distinguished from a generic transport error (it was previously folded into the same bucket).
> - The system prompt was tightened against the two most likely causes of a safety-filter rejection identified by code review: the model restating the score as an approximate number (rejected by the exact-match band/score check) and the model inventing a technique cue that echoes an untriggered fault's wording (rejected as an invented tag). Both are now explicitly forbidden in the prompt.
> - English-only rewriting is kept as a deliberate, documented limitation (§25.4) — non-English sessions continue to get the localised template; no locale routing was added.

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

| Area                                                                                                    | Original plan (this document)                                                                                                          | What was actually implemented                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Rationale                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Module A evaluation                                                                                     | No evaluation method specified for the rule-based checks — §9.3 only said Good/Fair/Poor bands would be "refined during pilot testing" | **Measurement-agreement evaluation** (ICC(2,1), Bland-Altman, Cohen's kappa) for the SLS hold-timer versus a human-timed reference — see [§9.4](#94-module-a-evaluation-measurement-agreement)                                                                                                                                                                                                                                                                                                                                                                      | Module A is deterministic, not a trained classifier, so classifier-accuracy metrics do not apply; method-comparison statistics are the correct framing and fit the non-diagnostic boundary (§6)                                                                                                                                                                                        |
| SLS scope                                                                                               | "Supported Single-Leg Stance, front view, 30 seconds" as a single check (§9.1)                                                         | Rebuilt as a **both-legs, 45-second-cap** check with a lift-line entry gate and a ball-in-circle stability sub-score (Phase 3B rebuild, see task.md)                                                                                                                                                                                                                                                                                                                                                                                                                | Fuller and more defensible functional check; detailed in task.md                                                                                                                                                                                                                                                                                                                       |
| WBLT design                                                                                             | §9.1 listed WBLT as a single camera-measured "dorsiflexion ROM band" (3 trials, no user measurement, no age/sex norms)                 | Redesigned as **dual output**: the official band is a _user-measured_ distance (ruler/tape, self-reported) scored against McBride et al. (2026) age/sex percentile bands; camera-measured dorsiflexion angle is kept as an unbanded secondary signal (corroboration, symmetry, trend). Requires the account's exact age (not the existing `age_group` range) to resolve the correct band — see the `exact_age` column above. Stage 1 (this build) covers one right-leg attempt end-to-end; guided 3-attempt bracketing and the left leg are follow-up stages.       | Monocular depth/contact detection is unreliable on a single webcam (§5, non-diagnostic boundary), so camera-only ROM banding had no defensible clinical anchor. Self-measured distance unlocks a real published normative table instead of an invented cutoff; the camera's job narrows to what it _can_ reliably judge (heel-lift validity), consistent with the SLS precedent above. |
| WBLT routing                                                                                            | §14.5 put WBLT on the shared `POST /api/module-a/analyze` endpoint (like STS)                                                          | Given a **dedicated** `/api/wblt/`* **router** (`GET /config`, `POST /analyze`, `GET /session/{id}`), mirroring SLS's precedent                                                                                                                                                                                                                                                                                                                                                                                                                                     | The dual distance+angle, per-attempt contract doesn't fit the shared single-buffer response shape, exactly the same reasoning that put SLS on its own router                                                                                                                                                                                                                           |
| Module B fusion weights                                                                                 | §10.4 recommended initial weights `w_rule = 0.6` / `w_ml = 0.4`, with a 3-tier capture-quality example                                 | Phase 4 starting default is `w_rule = 0.4` / `w_ml = 0.6` (opposite split), superseded by Phase 5 Stage 5.6's empirical sweep against **macro-F1 and the severe-misclassification rate**, not precision alone; the adaptive rule is a binary confident/low-confidence switch (`q_min` + `confidence_low_threshold`), not the original 3-tier capture-quality table                                                                                                                                                                                                  | An untrained Phase 4 stub model shouldn't be over-trusted by a rule-favoring default; the final weight needs to be earned against data, and the rehab-grading failure mode that matters most is telling a poor-form user they're fine, which precision alone doesn't directly measure — see task.md Phase 4 Stage 4.0 and Phase 5 Stage 5.6                                            |
| Module B `module_b_results` schema                                                                      | §13 defined all-flat typed columns (`rule_score`, `ml_score`, `rom_score`, `tempo_score`, `stability_score`, ...)                      | Hybrid: flat typed columns only for what Phase 7's dashboard queries directly (`score`, `band`, `confidence`, `model_version`, `q`, ...); rule sub-scores, feature vector, and per-rep summaries moved into JSONB `metrics_json`; `error_tags` renamed `module_b_error_tags` and keyed off `session_id` directly, with a `source` column added                                                                                                                                                                                                                      | Named sub-score columns (`rom_score`/`tempo_score`/`stability_score`) assumed every Module B exercise has exactly those three sub-scores — not a safe assumption for a registry of exercise plugins; JSONB is for what's genuinely variable-shape, flat columns for what's genuinely queried — see task.md Phase 4 Stage 4.6                                                           |
| Module B `feedback_texts` schema                                                                        | §13/§15 had `llm_used BOOLEAN` + stored `safety_disclaimer` text                                                                       | Replaced with `feedback_source` (`"llm"`/`"template"`) + `llm_attempted BOOLEAN` + `provider`/`model_version` + `disclaimer_version`                                                                                                                                                                                                                                                                                                                                                                                                                                | `llm_used=FALSE` couldn't distinguish "never called" from "called, output rejected by the safety filter" — an examiner-relevant distinction; the disclaimer shown is always the current i18n render, so storing a duplicate text copy per row was redundant — a version id gives audit traceability instead — see task.md Phase 6 Stage 6.5                                            |
| Dashboard trend/error-tag payload shape                                                                 | §14.8 listed `GET /api/dashboard/trends` and `GET /api/dashboard/error-tags` without specifying response shape                         | Both endpoints return their payload **keyed by** `exercise_type` in one response, not one call per exercise                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Phase 7's goal is fixing the trend/band panels for every exercise (Module A + B) in a single dashboard load — see task.md Phase 7 Stage 7.0                                                                                                                                                                                                                                            |
| Squat live-session end condition                                                                        | §10/§14 never specified how a squat set (unlike STS's clinically-validated fixed 5 reps) should end                                    | Decided 2026-07-16: **unlimited reps**, live client-side counter, ended manually via a **"Finish Set"** button that posts the whole buffer once. Plus an **inactivity safety net** (~9s no motion after ≥1 rep prompts finish-or-continue, never auto-submits) and an **optional motivational rep-goal** (10–80, step 10, or blank) shown as "Rep X of Y" + a progress bar — display-only, never sent to grading, hitting it only prompts, never auto-finishes                                                                                                      | A fixed rep count would be an uncited clinical threshold (unlike STS's 5) and a fixed time window can cut a rep mid-motion or reward a fast/sloppy squatter over a slow, controlled one; a user-owned motivational goal has no such grading risk since it's never sent to the backend — see task.md Phase 4 Stage 4.7                                                                  |
| Squat output: committed binary band                                                                     | §10 designed a three-band Good/Fair/Poor output for every Module B exercise                                                            | Squat commits to **binary Good/Poor** (no Fair), `Poor` displayed as **"Needs Improvement"**, `w_rule=0`/`w_ml=1`, single score cut at 8.447974 — a decision-policy change on an unchanged model (Stage 5.11). Module A + retired lunge keep three bands via a default `band_policy=None`. **Concrete example:** [§10.2 Example A](#102-module-b-output) — `ml_score: 9.4` above threshold → `band: "Good"`, no Fair possible                                                                                                                                       | The three-band scheme's `Fair` was an abstention that fired on ~every rep (model confidence never > ~0.76), so `Poor` was effectively unreachable (recall 0.077). Committing makes the app able to flag poor form (recall(Poor) → 1.0), accepting 31% false-alarm on Good reps but zero poor-called-Good — see task.md Phase 5 Stage 5.11                                              |
| Squat interpretable fault gates                                                                         | §10 planned a single fused ML+rule score with no per-rep rule override                                                                 | Added three **per-rep fault gates** (depth < 78.04°, lean ≥ 41.42°, heel-rise ≥ 0.071 as of Stage R1's near-leg-only re-derivation) as a separate override layer that forces `Poor` with a named reason if any gate fails on any rep (Stage 5.12); additive hook, model unchanged, no feature-schema bump. **Concrete example:** [§10.2 Example B](#102-module-b-output) — `ml_score: 9.42` (would band Good on its own) but `bottom_knee_flexion_deg: 73.7` trips the depth gate (< 78.04°) → band forced to `"Poor"` with tag `insufficient_depth`, ML overridden | The fused score is opaque (can't say _why_) and the ML scores only rep 0; gates add an interpretable "why" and cover every rep for fault detection. Depth is anchored to the clinical parallel norm, not the training data (REHAB24-6's depth signal is inverted) — see task.md Phase 5 Stage 5.12                                                                                     |
| Squat error-tag taxonomy trimmed                                                                        | §10 illustrative taxonomy implied faults like asymmetry / stance width could be tagged                                                 | Taxonomy **reconciled to 5 tags** (3 fault-gate + `inconsistent_tempo` soft + `low_confidence` system); `knee_valgus`, `asymmetry`, `feet_too_wide` **excluded** as un-measurable from one side view                                                                                                                                                                                                                                                                                                                                                                | A single monocular side view cannot resolve frontal-plane valgus, far-limb asymmetry (occluded), or depth-axis stance width — tagging them would report noise. Documented in `docs/module_b_limitations.md` — see task.md Phase 6 Stage 6.1                                                                                                                                            |
| LLM default state + provider                                                                            | §15 implied the LLM rewrite is part of the normal flow                                                                                 | Groq `llama-3.3-70b-versatile`, **disabled by default** (`feedback_llm_enabled=False`); the deterministic template fallback is built first and fully populates the report with the LLM off; enabling is a config flip                                                                                                                                                                                                                                                                                                                                               | Proves the LLM is optional polish, not a dependency; keeps the demo working with no external egress unless deliberately enabled at Phase 8 — see task.md Phase 6 Stages 6.2/6.4                                                                                                                                                                                                        |
| Reminders delivery mechanism                                                                            | §11/§13 planned a `reminders` table with add/view/complete, delivery unspecified                                                       | Client-side delivery: **Google Calendar link + downloadable** `.ics` (no backend email, no scheduler, no OAuth); in-app due-alert badge/banner; reminder deep-links into its exercise. Email verification on signup explicitly skipped                                                                                                                                                                                                                                                                                                                              | Avoids building email/scheduler/OAuth infrastructure from scratch; the user's own calendar app fires the real timed alert — see task.md Phase 7 Stage 7.3                                                                                                                                                                                                                              |
| Progress deep-dive page                                                                                 | §8.1 listed 11 pages; no dedicated per-exercise progress page                                                                          | Added a 12th page (`/progress`): one-exercise-at-a-time trend deep dive with a Functional/Rehab category selector, date-range control, band zones, capture-quality trend, and a ranked error-tag chart (Module B only)                                                                                                                                                                                                                                                                                                                                              | The Dashboard's multi-exercise overview becomes unreadable if each exercise shows full-detail sub-trends; the deep dive is where a per-exercise trend line is actually legible — see task.md Phase 7 Stage 7.1b                                                                                                                                                                        |
| Module B ML classifier scored rep 0 only                                                                | Not planned either way — an implementation gap introduced in Phase 5, not a documented design choice                                   | **Corrected at Stage 5.13** (2026-07-19): the calibrated classifier now scores every rep's own feature vector independently; the set's band is a strict majority vote across all per-rep verdicts, not a single fused score                                                                                                                                                                                                                                                                                                                                         | The rep-0-only gap was already flagged as a known limitation (former §25.2 item 10); closing it removed a real blind spot rather than leaving it "mitigated" by the fault gates alone — see task.md Stage 5.13                                                                                                                                                                         |
| Module B headline score = mean ML value                                                                 | §10.4 specified `S_final = w_rule·S_rule + w_ml·S_ml` as both the displayed score and the band input                                   | **Redefined at Stage 5.18** (2026-07-20) to `10 × good_reps ⁄ total_reps` (share of clean reps), decoupled from the ML value entirely; the mean `ml_score` stays visible on its own card but no longer drives the headline number                                                                                                                                                                                                                                                                                                                                   | Real testing surfaced a session scoring 8.0/10 next to a "Needs Improvement" band; root cause was the ML score running anti-correlated with the depth fault (confirmed live: gate-failing reps scored _higher_ on average than clean ones), the same REHAB24-6 inversion documented in item 7 of [§25.2](#252-squat-model--grading-limitations-module-b) — see task.md Stage 5.18/A    |
| Module B report clarity (rep target, attempts wording, unreconciled rejections, bullets, depth wording) | Not specified at this level of detail                                                                                                  | Session now persists the user's chosen rep target (`target_rep_count`); the report relabels the raw rep count "Attempts" (vs. counted-good reps); reps rejected by the ML alone with no named fault get their own line ("flagged by the movement model") so every attempt is accounted for; list bullets (broken by a Tailwind reset) restored; the depth-fault message quotes the actual gate angle instead of "closer to parallel"                                                                                                                                | Real webcam testing surfaced all four as concrete confusions in one session's report — see task.md Stage 5.19–5.21/C                                                                                                                                                                                                                                                                   |
| Module B live-session layout                                                                            | §11 specified live cues only in general terms, no layout                                                                               | Live feedback (rejected/counted-rep verdict) promoted to the most prominent panel, directly under the HUD; the redundant "Rep X of Y" status box removed (the HUD already shows it); the panel persists the last verdict rather than clearing after a timeout                                                                                                                                                                                                                                                                                                       | Real webcam testing showed corrective feedback was easy to miss at exercising distance from the screen — see task.md Stage 5.20/D                                                                                                                                                                                                                                                      |

| Squat heel-rise fault gate construction | §10.4's fault gates were specified as fixed, already-final thresholds | UAT found the heel-rise gate false-firing on good-form reps (3/18 sessions). Rebuilt as **near-leg-only** (camera-side leg by visibility, not a bilateral average), a settle-window median baseline, a multi-frame debounce, and an occlusion guard; threshold re-derived on the new construction (0.084 → 0.071) — see §10.4's Stage R1 update | The occluded far foot (side-view squat) was the noisiest input in the whole feature set; averaging it into a bilateral baseline manufactured phantom heel-rise — see task.md Phase 10 Stage R1 |
| SLS lift/drop confirmation timing | Not specified at this level of detail — §9.1 only specified the check's shape, not its debounce mechanism | Converted from a fixed **frame-count** dwell (3 consecutive frames, which is not a fixed duration under `requestAnimationFrame`) to a real **elapsed-time** dwell (0.15s lift / 0.10s drop) — see §9.1's Stage R2 update | UAT: "the lifting too sensitive" — a frame count can be well under 0.1s on a fast machine, inside normal foot jitter — see task.md Phase 10 Stage R2 |
| LLM fallback diagnosability | §15 specified `feedback_source`/`llm_attempted` but no reason for a fallback | Added `feedback_texts.fallback_reason` (queryable, not API-exposed) distinguishing rate-limit / timeout / API error / invalid JSON / empty response / a specific safety-filter rejection reason; tightened the system prompt against the two most likely rejection causes — see §15's Stage R3 update | Diagnosing an unexpectedly template-only report previously required a per-session log search; the reason is now queryable directly — see task.md Phase 10 Stage R3 |
| Live-feedback surface (all 4 exercises) | §11 specified only simple local indicators and a text cue (MVP scope) | Added a large corrective-cue pop-out with an auto-dismiss countdown, an unmistakable RECORDING state (badge + border + tone) preceded by a uniform 5-second countdown on every exercise, spoken (TTS) session/fault cues with a mute toggle, and a small looping exercise-demo reference clip/photo pinned to the camera stage — see the new [§11.3](#113-as-built-live-feedback-phase-10) | UAT's lowest-scoring item (Q9 = 3.38/5) was feedback unreadable at exercising distance; addressed visually (large pop-out), audibly (TTS), and via an unmistakable recording signal — see task.md Phase 10 Stages R4-R8 |
| SLS stability-overlay presentation | §9.1 specified the SLS check's metrics, not how its live overlay should render | The corner "stability ball" card and side lift-line bar (UAT's worst-scoring exercise, 14/18 sessions) were replaced with a transparent ball-and-ring centred over the video and a horizontal lift-line drawn across the video at the calibrated height, both read directly against the user's own on-screen body — see [§11.3](#113-as-built-live-feedback-phase-10) | UAT: the ball/line metaphors were "detached from the user's body in frame" and carried no felt meaning — see task.md Phase 10 Stage R8 |
| Pre-session instruction flow | §8.1 went straight from Exercise Selection to Camera Setup, with guidance folded into the Camera Setup page itself | Added a dedicated Exercise Instructions page (`/instructions`) between the two — one shared template per exercise with numbered steps, a demo clip, a camera-angle reference photo, an equipment note, and a "why this exercise" blurb; Camera Setup itself was stripped down to just the live preview + auto-start countdown once this page took over the guidance content — see §8.1, page 7 | UAT: instructions too long / not read / wrong order (14/18 sessions), and camera guidance was the top improvement target — see task.md Phase 10 Stages R9/R9.1 |
| Terminology explanation | Not planned — no glossary/tooltip mechanism existed | Added a shared glossary (10 terms, each with a direction-of-good statement) surfaced via inline tooltip triggers across the Report and Instructions pages | UAT's most-repeated content request: terminology unexplained (12/18 sessions) — see task.md Phase 10 Stage R10 |
| Post-session Report layout | §8.1/§10.2 specified the report's _content_ but not its ordering, chart interactivity, or severity presentation | Reordered by importance (band/score → coaching+errors → sub-scores → comparison → technical details); dropped the redundant ML-prediction row into a collapsed "Technical details" section; squat's 3 rule sub-scores became an interactive colour-coded chart; error-tag severity gained a distinct icon _and_ colour per level plus a legend; added Retry-exercise and back buttons — see §8.1, page 10 | Report was UAT's strongest surface (+15 net) — the goal was fixing redundancy/ordering/colour-semantics without touching what already worked — see task.md Phase 10 Stage R11 |
| Progress/Dashboard second chart per exercise | §8.1 (page 12/13) specified a capture-quality trend as the Progress page's second chart | Capture-quality trend (UAT's one unanimously-rejected chart, 6/18) replaced with a per-exercise raw-metric chart: STS completion+rep time, SLS best hold per leg (with a Both/Left/Right selector), WBLT best reach per leg, squat valid-rep volume; the Dashboard's pooled Band Distribution and Error Tags panels each gained a per-exercise filter — see §8.1, page 13 | UAT: capture-quality trend was the one clearly-negative chart finding; band-distribution and error-tag panels had no way to drill into one exercise — see task.md Phase 10 Stage R12 |
| Reminders — sort order, calendar content, auto-complete scope | §14.9's as-built note (Phase 7) covered add/view/complete/export; ordering, calendar-title content, and auto-complete scope were unspecified | Sort changed to newest-created-first; calendar event titles now include the linked exercise's name; completing a session now auto-ticks only the _specific reminder it was launched from_ (a session-flow-carried id), not any reminder sharing the same exercise; added a post-create "add to calendar?" prompt and a distinct "Open exercise" action separate from the mark-complete checkbox — see §14.9's Stage R13 update | UAT: a newly-created reminder was hard to find; the calendar event gave no hint which exercise it was for; "completed" vs. "just opened" were being conflated — see task.md Phase 10 Stage R13 |
| First-run non-diagnostic disclaimer | Earlier UAT-remediation planning (superseded) called for a one-time first-run acknowledgement modal with backend logging of the ack | **Not built.** The non-diagnostic reminder instead ships as an always-visible badge next to the band chip on every Report (Stage R11) plus the existing landing-page disclaimer (§6) — HY descoped the standalone modal + backend acknowledgement-logging endpoint from the final UAT-remediation plan | Kept here as an explicit "considered, then descoped" note rather than a silent gap — see §25.5 and task.md Phase 10 Stage R14 |
| Pose landmark representation | §3.3/§12 (and the linked proposal) specified extracting raw 2D normalised MediaPipe landmark coordinates `(x, y)` for angle/feature computation | Angle and feature computation (fault gates, feature extraction, rep segmentation, and the live frontend estimators — `fault_gates.py`, `features.py`, `segmentation.py`, and the front-end live estimators) uses MediaPipe's **world landmarks**: a metric-scale (real-world, in metres), hip-centred, monocular 3D pose estimate — not the plain normalised image coordinates | World landmarks give camera-distance-independent angles and segment lengths, which raw pixel-normalised coordinates do not. This does **not** change the single-camera premise: world landmarks are still MediaPipe's own learned body-model reconstruction from the same single camera frame, not a second camera or a depth sensor. The "depth axis is the least reliable axis" limitation (§25.1) still applies unchanged — the depth component of a world landmark is inferred, not measured, so it inherits the same monocular-depth uncertainty for a different technical reason |
| Feedback-rewriting layer: architecture/ownership | Table 7 (§10.4) named this component a **"Transformer"** rewriting layer, implying a component trained or implemented as part of this project | Implemented by calling a third-party, pre-trained large language model via API (see the "LLM default state + provider" row above for the specific provider and default-off state); **no transformer model was trained, fine-tuned, or built from scratch** — the model is used entirely as a hosted, off-the-shelf inference service behind a prompt and a safety filter | Training a custom transformer-based text generator requires labelled coaching-text data that does not exist for this domain. A hosted, pre-trained LLM (which is internally a Transformer architecture, so the label is not false — just not built in-house) fulfils the same non-diagnostic rewriting role without that requirement, behind the deterministic-template fallback and the safety filter that forbids any change to grade/band/score/tags |

_These are enhancements consistent with the project goals in §23, not departures from the MVP priorities. This list covers the deviations identified so far — add further rows here as the implementation continues to evolve._

---

## 25. Current System Limitations (for the Final Report)

This section is a **single consolidated list of the current version's known limitations**, written so they can be lifted directly into the final report's limitations chapter. An examiner reads a named limitation as rigour and an unnamed one as oversight — so every limitation below is stated with _what_ it is, _why_ it exists, and (where relevant) _what would reverse it_.

> **Update (Phase 10, 2026-07-24/25):** moderated user acceptance testing (22 participants, 21 questionnaires) has now actually run, and its findings drove the whole of Phase 10 (Stages R1–R14, §11.3, §24). This section reflects the system **after** that remediation, not before it — several items below name a defect UAT surfaced and then note the stage that fixed it (struck through) so the correction is traceable rather than silently disappearing from the document.

Sources of truth: `task.md` (Phases 5–7, 10), `docs/module_b_limitations.md`, `ml/reports/SQUAT_EVALUATION_REPORT_2BAND.md` (+ `_3BAND`), `ml/reports/PHASE5_CHAPTER_DRAFT.md`, and `PhysioFit_UserTesting_Analysis.md` (the UAT findings Phase 10 remediated). Where a number is quoted, re-verify it against the live report before final submission — several are computed from a fixed corpus and will move if the corpus changes. Several Phase 10 stages also still have an explicit "live end-to-end verification on a real device/browser" item outstanding at the time of writing — see each stage's entry in `task.md` for exactly what remains unconfirmed live vs. confirmed by code review/tests alone.

### 25.1 Monocular single-camera limitations (whole system)

1. **Depth axis is unreliable.** A single webcam resolves the plane facing it well but resolves the camera-depth axis worst. Every feature that lives on that axis was either dropped or down-weighted. This is the root cause of several limitations below.
2. **Frontal-plane faults are not measured at all.** Knee valgus / knock-knee is **deliberately excluded** from features, rules, tags, and evaluation — it is ill-posed from a sagittal (side) view. _(Excluded, not unimplemented.)_
3. **Far-limb occlusion.** From one side view the far limb is partly occluded (far-knee visibility ≈ 0.59–0.78 vs near-side ≈ 0.95–0.99). This is why left/right **asymmetry is not tagged** — the feature did not track true inter-leg difference against mocap (r ≈ −0.05) and the model ranked it near-last.
4. **Stance width is not tagged.** In profile the feet separate mainly along the depth axis; the stance-width feature was below chance in-sample (AUC 0.37) and inverted on external data, so a `feet_too_wide` tag would fire on noise.
5. **No true 3D / clinical goniometry.** All angles are 2D projections from image landmarks; the system is explicitly **non-diagnostic** and reports conservative Good/Fair/Poor bands, not exact clinical degrees.

### 25.2 Squat model & grading limitations (Module B)

1. **Small dataset.** The squat model is trained/evaluated on **98 side-view reps from 9 subjects (72 Good / 26 Poor)**, out-of-fold. Per-cell counts are small integers — a single rep changing hands moves a rate by several points. Treat all squat metrics as order-of-magnitude, not precise.
2. **The "Poor" construct is population-specific and did not transfer.** The classifier learned "resembles REHAB24-6's _incorrect_ reps", which in that cohort skew **deeper and faster** — not a clinical "you exceeded a safe angle" rule. On the external EC3D set this construct **did not transfer** (and partly inverted). The model is a within-dataset quality proxy, not a validated clinical grader. **Now also confirmed live (2026-07-20)**, on two of HY's own real webcam sessions, not just the EC3D dataset: depth vs. `ml_score` correlates at **r = −0.975** on a session with zero rule faults (deeper reps scored _lower_), and reps that failed the depth gate for being too shallow averaged a _higher_ `ml_score` (9.04) than gate-clean reps (7.87) — the inversion is not a dataset artifact, it reproduces on this exact camera/pipeline in normal use.
3. **Committing to binary Good/Poor gives up the zero-severe-error guarantee (by design).** At the shipped operating point, **recall(Poor) = 1.000** but **22/72 (31%) of Good reps are flagged Poor** (false alarms) _in-sample_. The safer direction is preserved — **0** poor-form reps are ever called Good — but a well-performed rep being told "Needs Improvement" is a real and expected failure mode. **Live measurement (2026-07-20) suggests the real-world rate runs well above the in-sample figure**: across two real sessions, 21 reps passed every rule gate, and 17 of them (81%) were still rejected by the ML alone — consistent with `core/set_scoring.py`'s own documented caveat that per-rep errors are not independent within one subject/camera/session, so the true whole-set failure rate is higher than an independence assumption would predict.
4. **The ROM rule is inverted for this population, so fusion is pure-ML (**`w_rule = 0`**).** The rule rewards depth, but in the training data incorrect reps are deeper; the empirical sweep therefore weighted the rule to zero. The rule sub-scores are still shown for transparency but do not drive the squat band or, since Stage 5.18, the headline score.
5. ~~**The ML scores only the first rep of a set.~~ Resolved at Stage 5.13 (2026-07-19).** This limitation is no longer accurate and is kept here, struck through, so anyone cross-referencing an earlier draft or citation of this document can see it was corrected rather than silently disappearing. The calibrated classifier now scores every rep's own feature vector independently, and the set's band is a majority vote across all of them — see [§10.1](#101-module-b-pipeline) and [§10.4](#104-fusion-scoring) item 4.
6. **The depth gate threshold is clinically anchored, not data-driven.** Depth < 78.04° = clinical parallel norm (90°) minus the pipeline's measured −11.96° under-read. It is **not** learned from REHAB24-6 because that dataset's own depth signal is inverted. The lean (41.42°, data-driven Youden-J) and heel-rise (0.071 as of Stage R1's near-leg-only re-derivation, was 0.084 on the original bilateral construction; still data-driven Youden-J) gates are data-driven on the same small sample.
7. ~~**The heel-rise fault gate false-fires on the occluded far foot.~~ Fixed at Stage R1 (2026-07-24).** UAT found this firing on 3/18 sessions, including a genuinely good-form squat. Kept here, struck through, for the same reason as item 5. Rebuilt as near-leg-only (camera-side leg by visibility) with a settle-window baseline, a debounce, and an occlusion guard — see [§10.4](#104-fusion-scoring)'s Stage R1 update.
8. **No published MDC / repeatability threshold on the 0–10 score.** The dashboard shows trends with **no "meaningful change" claim** for any exercise because no published MDC exists on the composite score. Small trend movements may be measurement noise. _(WBLT does have a published MDC, but only on raw distance/angle, shown per-session — not on the 0–10 trend.)_
9. **Only one Module B exercise ships (squat).** The leg lunge was investigated and then **removed** (2026-07-19); the second Module B exercise seen in earlier planning no longer exists. The architecture remains a registry of exercise plugins, so this is a scope limit, not an architectural one.

### 25.3 Module A (functional check) limitations

1. **SLS stability is frontal-plane only.** The single-leg-stance ball-in-circle stability sub-score is scored in the image plane; sway toward/away from the camera is not captured (monocular-depth limitation).
2. **SLS agreement is validated on a synthetic corpus, not real pilot recordings.** The ICC(2,1) ≈ 0.995 / kappa ≈ 0.857 / Bland-Altman figures come from a fixed-seed **synthetic** replay corpus — no real pilot recordings exist yet. There is a small systematic bias (system reads ≈ 0.75 s shorter than a stopwatch) from the FSM's drop-hysteresis frames.
3. **STS and WBLT have no measurement-agreement harness yet.** Only SLS has a replay/agreement evaluation; the same framing is planned but not built for STS completion-time and WBLT dorsiflexion-ROM.
4. **WBLT's official band relies on user self-measurement.** The banded output uses a **self-reported** ruler/tape distance scored against McBride et al. age/sex norms; the camera angle is only a secondary corroboration signal. Accuracy depends on the user measuring correctly, and it requires the account's **exact age** (not just an age range).
5. **All Module A thresholds are heuristic/prototype values.** Band cutoffs are starting heuristics to be refined with pilot data, not clinically validated cut points.

### 25.4 LLM / feedback limitations

1. **The LLM rewrite is disabled by default and Module-B-only.** With `feedback_llm_enabled=False` (the default), users see the deterministic **template** feedback, not LLM-rewritten text. Module A reports are never LLM-rewritten (they show a static "General tip"). If the demo is run with the LLM off, no AI-rewritten coaching text appears at all.
2. **LLM output is best-effort and can silently fall back.** On any timeout / rate-limit (429) / safety-filter rejection, the system falls back to the template with no user-visible error. The LLM never changes the grade, band, score, or tags (enforced by the safety filter), so it is a readability layer only — but the polish is not guaranteed to appear. **This actually happened (2026-07-20):** a `.env` model id (`llama-3.3-70b-instruct`) that Groq doesn't host degraded every report to the template for hours, invisibly, because it's exactly this failure mode working as designed — compounded by the backend having no logging configuration at all, so the diagnostic lines the code already emitted on this exact failure were silently discarded rather than shown. Fixed (Stage 5.23): corrected the model id, and added `core/logging_config.py` so `llm_failed`/`llm_rejected`/`llm_used`/`llm_disabled` are always visible. **Diagnosability improved further at Phase 10 Stage R3:** every fallback now stores a specific `fallback_reason` on the `feedback_texts` row (§13) instead of only a log line, so the exact cause of a template-only report is queryable per session, not just discoverable by log-diving. The system prompt was also tightened against the two most likely safety-filter rejection causes, but this has **not yet been confirmed live** against the real Groq API — it is a code-reasoned fix, not yet a measured reduction in the fallback rate.
3. **External dependency + free-tier limits when enabled.** When enabled, feedback depends on Groq's free tier (30 RPM / 1,000 RPD / 12,000 TPM / 100,000 TPD) and outbound egress; not yet decided/verified for the deployed Cloud Run demo (Phase 8, open question Q8).

### 25.5 Platform / operational limitations

1. **Not yet deployed.** Phase 8 (Google Cloud deployment) is not complete; the system runs locally (FastAPI + Postgres + Vite dev server). User testing is against a local instance unless deployment lands first.
2. **Camera capture cannot run in a sandboxed/automated browser.** Live webcam + MediaPipe requires a real browser with camera permission; this is a testing-environment limitation, not a product defect, but it means some flows can only be verified manually.
3. **No email verification / password recovery.** Signup does not verify email and there is no account-recovery flow (email infrastructure was deliberately scoped out).
4. **Reminder alerts are client-side only.** There is no server-side push/email; timed alerts fire only if the user adds the reminder to their own calendar (Google Calendar link / `.ics`). The in-app badge/banner only shows while the app is open.
5. **Single-language grade values in the DB.** Band values are stored in English (`good`/`fair`/`poor`); the UI translates them (en/zh/ms), and `poor` is displayed as "Needs Improvement" — but any raw DB inspection shows the internal English values.
6. **Demo/seed data is clearly marked, not real model runs.** The multi-session demo account uses `model_version="demo-seed"` rows; it exists to exercise the dashboard/progress panels, not to represent real captured sessions.
7. **No standalone first-run disclaimer acknowledgement.** An earlier draft of the UAT-remediation plan called for a one-time first-run modal plus a backend-logged acknowledgement timestamp; HY descoped it during Phase 10 (Stage R14). The non-diagnostic reminder is instead an always-visible badge on every post-session Report (§8.1, page 10) and the existing landing-page disclaimer (§6) — real, but not a logged, provable per-user acknowledgement event.

### 25.6 Live-feedback / audio-cue limitations (Phase 10, §11.3)

1. **WBLT has no live corrective-cue pop-out.** `LiveCueOverlay` (§11.3) is wired into squat, STS, and SLS; WBLT currently has no rejected-attempt concept surfaced as a live visual/audio cue, only its existing status-box warning text. This would need its own design pass, not a copy of the existing pattern.
2. **The Chrome speech-engine wedge mitigation is not a guaranteed cure.** Chrome's `speechSynthesis` can wedge at the browser-process level (a documented, long-standing Chromium bug) and stay silently dead across page reloads until the browser itself restarts. The shipped start-watchdog retries once and recovers some wedge states, but a page cannot force-reset a genuinely wedged browser process the way quitting and reopening Chrome can. The tested demo-day mitigation is restarting the browser, not just reloading the page, if voice cues go silent mid-session.
3. **ms-MY voice availability is OS/browser-dependent.** Where the operating system has no Malay text-to-speech voice installed, the browser silently falls back to a default voice or no-ops — the same class of best-effort limitation as the English-only LLM rewrite (§25.4).
4. **Audio cues were not verifiable in the development sandbox.** The sandboxed browser used during Phase 10 development has no audio output at all, a harder constraint than even its blocked webcam access; correctness of the spoken cues (text, language, sequencing of simultaneous faults) was verified by code/logic review and, where possible, live diagnostics on HY's own machine rather than by the agent hearing them directly.

> **Before final submission:** re-run the evaluation harnesses and re-quote any number cited above from the live report files, and fold in whatever usability limitations the post-user-testing questionnaire surfaces.
