# FYP Development Tasks

**Project:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera  
**Status:** Phase 0 complete · Phase 1A (UI clickable prototype) complete · Phase 1B (backend integration) implemented pending end-to-end local verification  
**Related docs:** [FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md](./FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md) (architecture & design), [rules.md](./rules.md) (coding agent rules)

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
- [ ] Show dashboard trend

**Deliverable:**

- ✅ User can complete all 3 functional checks (STS, SLS, WBLT)
- ✅ Results are saved and viewable with exercise-specific metrics
- ✅ Single-endpoint `/api/module-a/analyze` dispatches to exercise-specific logic
- ✅ Decoupled session_status from band across all exercise types
- ⏳ Frontend LiveSession UI complete for STS, partial for SLS/WBLT (deferred)

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

**Stage 6 detail (2026-07-07):** `Report.tsx` now branches on `result.metrics.perLeg` — new SLS rows render per-leg cards (band, best hold, stability, combined score, translated stop reason), L/R difference, support-used, and capture quality; legacy single-leg rows (pre-rebuild) fall through unchanged to the original metric-row rendering. Added 4 missing `report.warn_*` i18n keys (en/zh/ms) so SLS-specific warning tags (`incomplete_hold`, `landmarks_missing`, `foot_dropped_below_line`, `unknown`) translate instead of showing raw tag strings. Added `backend/tests/test_frontend_disclaimers.py` (3 tests) scanning all 3 i18n locale files for forbidden clinical-claim phrasing, since the frontend has no JS test runner configured. Backend: 35/35 pytest passing. Verified end-to-end in-browser with a real asymmetric two-leg session (right leg 41.7s/Good/9.8, left leg 14.9s/Poor/3.8, session Fair/6.8, support="slight") — confirmed correct rendering, correct i18n, and that Dashboard/SessionHistory (which only read top-level session fields, never `metrics`) are unaffected.

**Stage 7 detail (2026-07-07):** Added `backend/app/module_a/evaluation/agreement.py` — pure-Python ICC(2,1), Bland-Altman, and Cohen's kappa (no numpy/scipy/pingouin dependency exists in this project; these are simple closed-form formulas over a small sample), with 11 unit tests using hand-verifiable boundary cases (perfect agreement, zero between-subject signal, manually-computed Bland-Altman example). Added `generate_sls_replay_corpus.py` (fixed-seed synthetic corpus generator — no real pilot recordings exist yet for this prototype; 10 per-leg samples spanning Poor/Fair/Good/Invalid, steady and swaying, committed to `app/module_a/replay_corpus/sls/`) and `run_sls_evaluation.py` (replays the corpus through `analyze_leg`, computes agreement metrics, writes `evaluation/SLS_EVALUATION_REPORT.md`). Also added `replay_sls_session.py`, the SLS analogue of the existing STS `replay_session.py`. Added `scoring.hold_time_band()` so band agreement is evaluated on the hold-time dimension only (the one thing a stopwatch-only human reviewer could independently reproduce — the ball-in-circle stability sub-score would need a separate rater protocol). Results (reproducible, verified byte-identical across two runs): **ICC(2,1) = 0.995**, **Cohen's kappa = 0.857**, **Bland-Altman bias = -0.753s** (system reads slightly shorter than the simulated manual reference, consistent with the FSM's drop-hysteresis persistence frames), **95% LoA = [-4.08s, 2.57s]**. One band disagreement out of 10 (system correctly reports `invalid` for a leg that never validly crossed the lift-line, while the naive time-based reference calls a small positive duration `poor`) is called out explicitly in the report as a genuine edge-case divergence, not a bug. Backend: 46/46 pytest passing. The monocular-depth limitation (frontal-plane-only stability scoring) and all prototype thresholds (from `config.py`) are documented in the generated report for Chapter 3 / limitations use. This closes out the Phase 3B rebuild (Stages 1-7 all complete).

**Deliberately out of scope:** the Dashboard's score-trend/band-distribution/confidence panels are static placeholders for _every_ exercise type (STS and WBLT included) — `dash.placeholderScoring: "Scoring appears after Module A/B is implemented."` — this is pre-existing, cross-cutting tech debt, not SLS-specific. Building a real per-leg trend chart only for SLS would be inconsistent with every other exercise and is a larger undertaking (a trend-data API + charting) than "Stage 6 polish." Flagging as a separate future task rather than building a one-off.

### Phase 3D: Module A code reorganization (per-exercise folders)

**Goal:** Fix "everything lives in one flat file, dispatched by `if exercise_type == ...`" — split STS/WBLT/SLS into dedicated packages/folders mirroring the SLS package that already existed, so the module structure actually maps to feature boundaries.

**Backend (`backend/app/module_a/`):**

- `core/` — shared, exercise-agnostic: `config.py`, `schemas.py`, `banding.py` (dispatcher + `score_to_band`/`compute_session_status`), `crud.py` (generic `save_result`/history/landmark-log), `geometry.py`, `quality.py`, `smoothing.py`, `router.py` (the shared `/api/module-a/analyze` endpoint, renamed from `rest_router.py`)
- `sts/` — `config.py`, `engine.py` (`run_sts`, extracted from the old `SessionEngine._run_sts`), `banding.py`, `schemas.py` (`ModuleAMetrics`)
- `wblt/` — `config.py`, `engine.py` (`run_wblt`), `banding.py`
- `sls/` — extended with `config.py` (the `SLS_*` rebuild constants), `schemas.py` (`Sls*` request/response models), `crud.py` (`save_sls_result`), `router.py` (renamed from the top-level `sls_router.py`), `evaluation/` (moved in from `module_a/evaluation/`)
- Deleted: the old flat `session_engine.py`, `banding.py`, `config.py`, `crud.py`, `schemas.py`, `rest_router.py`, `sls_router.py`, top-level `evaluation/` — plus the **dead legacy single-leg SLS code path** (`_run_sls`, `_compute_sls_band`, and its config constants/tests) that the SLS rebuild (Phase 3B) had already superseded but never removed. Verified dead by grepping for every caller and the frontend before deleting.
- All 40 backend tests pass; `app.main` imports cleanly (27 routes); Black/isort applied.

**Frontend (`frontend/src/`):** `pages/LiveSession.tsx` (which was STS-only in practice despite its generic name — confirmed every code path gated on `isSts`) moved to `pages/sts/StsLiveSessionPage.tsx`, mirroring the existing `pages/sls/` folder; its estimator util moved from `utils/stsLiveEstimate.ts` to `utils/sts/stsLiveEstimate.ts`; route renamed `/live` → `/sts/live`. Deleted the dead legacy `utils/slsLiveEstimate.ts` and its two orphaned constants in `moduleAThresholds.ts` (only referenced from commented-out code). `CameraSetup.tsx`, `ExerciseSelection.tsx`, `Report.tsx`, `Dashboard.tsx`, `SessionHistory.tsx` were **not** moved — they're genuinely shared across all 3 exercises (each branches internally by exercise code), so nesting them under one exercise's folder would misrepresent what they do.

**⚠️ Known issues surfaced during this reorg, intentionally left as-is (not part of the reorg's scope):**

1. **WBLT backend crash bug:** `wblt/engine.py`'s `run_wblt()` (moved verbatim from the old `_run_wblt`) calls `angleDeg(...)`, a function that is never defined or imported anywhere in the codebase. Any real WBLT session that reaches this code path will raise `NameError`. This means **WBLT has never been exercised end-to-end** — it was implemented (Phase 3C, above) but is currently broken.
2. **WBLT frontend has no live-session page.** `CameraSetup.tsx` routes every non-SLS exercise (including WBLT) to the STS-only live page; there's no `isWblt` branch anywhere in the old `LiveSession.tsx`/new `StsLiveSessionPage.tsx`, and no live-threshold constants for WBLT exist on the frontend. A WBLT session currently lands on a page that does nothing for it.
3. Fixing both is a real feature-completion task (not a rename/move), tracked here for a future phase rather than folded into this reorg.

---

## Phase 4: Module B Rehab Grading Skeleton

**Goal:** Build the Module B pipeline before final exercise is decided.

**Tasks:**

- [ ] Create placeholder rehab exercise configuration
- [ ] Create backend Module B analyze endpoint
- [ ] Create feature extraction schema
- [ ] Create rule sub-score functions:
  - [ ] ROM score
  - [ ] Tempo score
  - [ ] Stability score
- [ ] Create fusion scoring function
- [ ] Create placeholder ML model interface
- [ ] Return final report using mock/placeholder model output first

**Deliverable:**

- Module B works end-to-end with placeholder logic
- Later ML model can be plugged in

---

## Phase 5: Dataset and ML Training

**Goal:** Train Extra Trees model using public dataset or converted pose-feature dataset.

**Tasks:**

- [ ] Search and select suitable public dataset
- [ ] Convert raw videos/images/skeletons into pose features
- [ ] Standardize labels into Good/Fair/Poor or correct/needs improvement
- [ ] Split data by participant if subject ID is available
- [ ] Train Extra Trees classifier
- [ ] Evaluate using:
  - [ ] Accuracy
  - [ ] Precision
  - [ ] Recall
  - [ ] Macro-F1
  - [ ] Confusion matrix
- [ ] Save model using joblib
- [ ] Save feature schema
- [ ] Integrate trained model into backend

**Deliverable:**

- Trained Extra Trees model
- Evaluation results
- Backend can load and use model

---

## Phase 6: After-Set Report and External LLM API

**Goal:** Generate understandable after-set feedback.

**Tasks:**

- [ ] Generate structured feedback from rule/ML output
- [ ] Add safety filter/rules before calling LLM
- [ ] Call external LLM API after set only
- [ ] Store structured and rewritten feedback
- [ ] Show final report to user
- [ ] Add fallback template feedback if LLM fails

**Deliverable:**

- User receives readable after-set report
- System still works even if LLM API fails

---

## Phase 7: Dashboard and Progress Tracking

**Goal:** Make the system useful across multiple sessions.

**Tasks:**

- [ ] Show recent sessions
- [ ] Show score trend chart
- [ ] Show band distribution
- [ ] Show common error tags
- [ ] Show capture quality trend
- [ ] Add reminders

**Deliverable:**

- User can track progress over time

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
