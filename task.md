# FYP Development Tasks

**Project:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera  
**Status:** Phases 0-3E complete (full-stack skeleton, camera/MediaPipe, Module A: STS/SLS/WBLT all verified live) · Phase 5 (squat ML) Stages 5.0-5.8 complete — trained, calibrated, LOSO-evaluated Extra Trees squat model exported and wired into the real backend, verified live end-to-end (2026-07-16). **Stage 5.9 (EC3D external validation) is next and unblocked; not started per rules.md scope discipline.** Phase 5B (lunge) gate is satisfied but lunge itself not started.  
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

### Fourth Milestone (Module B Squat, Placeholder Model)

> Module B runs end-to-end for squat with an honest, announced placeholder model (`model_version: "stub-0"`) — verified live against the real backend + Postgres. Closes Phase 4.

### Data Audit Gate (Phase 5, Stage 5.0)

> `ml/reports/DATA_AUDIT.md` reports the exact usable side-view squat (Ex6) rep count after the camera-orientation filter, and HY has chosen among options (a) accept the smaller N, (b) admit half-profile reps as a flagged cohort, or (c) relax to both views and add `view` as a feature. No ML training work begins before this decision (see [Open Questions](#open-questions-phases-47) Q1/Q2).

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

- [~] Show dashboard trend — **partially done**: WBLT has a real per-session "vs last session" trend row on the Report page (`Report.tsx`, Phase 3E Stage 6, MDC-gated), computed live against account history. STS and SLS have no equivalent yet, and the actual **Dashboard page** (`Dashboard.tsx`) score-trend/band-distribution/confidence panels are still static placeholders for all 3 exercise types (`dash.placeholderScoring`) — see Phase 7 below, which is the real home for this remaining work.

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

**Backend (`backend/app/module_a/`):**

- `core/` — shared, exercise-agnostic: `config.py`, `schemas.py`, `banding.py` (dispatcher + `score_to_band`/`compute_session_status`), `crud.py` (generic `save_result`/history/landmark-log), `geometry.py`, `quality.py`, `smoothing.py`, `router.py` (the shared `/api/module-a/analyze` endpoint, renamed from `rest_router.py`)
- `sts/` — `config.py`, `engine.py` (`run_sts`, extracted from the old `SessionEngine._run_sts`), `banding.py`, `schemas.py` (`ModuleAMetrics`)
- `wblt/` — `config.py`, `engine.py` (`run_wblt`), `banding.py`
- `sls/` — extended with `config.py` (the `SLS_*` rebuild constants), `schemas.py` (`Sls*` request/response models), `crud.py` (`save_sls_result`), `router.py` (renamed from the top-level `sls_router.py`), `evaluation/` (moved in from `module_a/evaluation/`)
- Deleted: the old flat `session_engine.py`, `banding.py`, `config.py`, `crud.py`, `schemas.py`, `rest_router.py`, `sls_router.py`, top-level `evaluation/` — plus the **dead legacy single-leg SLS code path** (`_run_sls`, `_compute_sls_band`, and its config constants/tests) that the SLS rebuild (Phase 3B) had already superseded but never removed. Verified dead by grepping for every caller and the frontend before deleting.
- All 40 backend tests pass; `app.main` imports cleanly (27 routes); Black/isort applied.

**Frontend (`frontend/src/`):** `pages/LiveSession.tsx` (which was STS-only in practice despite its generic name — confirmed every code path gated on `isSts`) moved to `pages/sts/StsLiveSessionPage.tsx`, mirroring the existing `pages/sls/` folder; its estimator util moved from `utils/stsLiveEstimate.ts` to `utils/sts/stsLiveEstimate.ts`; route renamed `/live` → `/sts/live`. Deleted the dead legacy `utils/slsLiveEstimate.ts` and its two orphaned constants in `moduleAThresholds.ts` (only referenced from commented-out code). `CameraSetup.tsx`, `ExerciseSelection.tsx`, `Report.tsx`, `Dashboard.tsx`, `SessionHistory.tsx` were **not** moved — they're genuinely shared across all 3 exercises (each branches internally by exercise code), so nesting them under one exercise's folder would misrepresent what they do.

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
  - **Separate `module_b_error_tags` table:** `session_id` FK, `tag`, `severity`, `source` (`"rule"` / `"ml"` / `"system"`) — one row per tag, enabling cross-session tag aggregation.
  - **JSONB `metrics_json`:** `feature_vector` (needed for the replay harness), rule sub-score breakdown, `w_rule`/`w_ml` actually used, per-rep summaries — the part whose shape genuinely differs between squat, lunge, and future exercises.
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
- [x] `frontend/src/utils/squat/squatLiveEstimate.ts` — client-side live rep count + band _estimate_ only. **Fetches thresholds from `GET /api/module-b/squat/config*`*; local constants are the pre-fetch fallback only (X7 — this is Phase 3E Stage 5's exact lesson, do not repeat it).
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
  - [x] exact rep counts **per exercise × correctness × `person_id`**
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
      confirmed `/Users/sumhonyou/fypDataset/` is outside the repo tree, no `.gitignore`
      change needed), `ml/docs/rehab24_6_schema.md` (authoritative column dictionary,
      transcribed from `Segmentation.txt` and cross-checked against a live read of all 1072
      CSV rows — flags a real inconsistency in the dataset's own docs: the orientation
      mapping table says `side` where the actual column enumerates `profile`), and
      `ml/scripts/audit_rehab246.py` (loads `Segmentation.csv`, filters
      `exercise_id ∈ {5, 6}` in code, reports every number below; Black/isort clean).
- [x] **Numbers (full detail in `ml/reports/DATA_AUDIT.md`):** Ex6 (Squats) raw = 195
      reps, Good 134 / Poor 61, across 9 subjects (1–9), all with both classes present
      unfiltered. `cam17_orientation`: front 98 / half-profile 97 / **profile 0** (the
      `profile` value never occurs for Ex6 — it's exclusive to Ex3 in this dataset). Ex5
      (Leg lunge, Phase 5B reference only): 174 reps, Good 78 / Poor 96, subject 3 is
      single-class (0 Good) even before any view filter.
- [x] **View question verified visually, not assumed:** extracted real frames (via
      OpenCV, `cv2.VideoCapture`) from both cameras for one `front`-orientation rep and one
      `half-profile`-orientation rep of `PM_008` (Ex6). Confirmed: `cam17_orientation ==
"front"` → Camera17 shows the subject facing the camera dead-on, Camera18 shows a
      clean true sagittal/profile view. `cam17_orientation == "half-profile"` → **both**
      cameras show a diagonal angle, neither is a true side view. Composite comparison
      image saved to `ml/reports/figures/view_verification.png` and embedded in
      `DATA_AUDIT.md`.
- [x] **Usable side-view Ex6 rep count: 98** (all `front`-orientation reps, sourced from
      Camera18) — Good 72 / Poor 26, all 9 subjects still represented, but subjects 2, 4,
      and 9 become single-class (0 Poor) once filtered to side-view only — a real LOSO
      problem for those 3 folds. Half-profile-only Ex6 reps (excluded from this count): 97
      total, Good 62 / Poor 35.
- [x] **Gate triggered:** Poor-class count after the view filter (26) is materially
      below the ~90/category reference the gate text names, even though Good (72) is close.
      `DATA_AUDIT.md` §"The gate" lays out options (a)/(b)/(c) with trade-offs specific to
      the numbers above (LOSO fold viability for (a), the half-profile correctness split
      for (b), the live-capture `view`-feature availability problem for (c)) — no option is
      chosen; per the hard-gate instruction this is HY's call.
- [ ] **Not done, correctly:** Stage 5.2 onward (landmark extraction, feature table,
      training) — blocked on the gate above, per scope discipline.

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

- [x] `ml/` importing from `backend/app/module_b` must work (X1). Set it up as a path/editable install — **document the exact command in `ml/README.md`**. A copy-pasted feature function is a Phase-5-breaking bug, not a shortcut.
- [x] `scripts/plotting.py` — one shared `save_fig(fig, name: str) -> Path` that writes to `ml/reports/figures/{name}.png` at a fixed DPI (150) and fixed figure size per plot type, and a shared style (`seaborn` theme or matplotlib rcParams set once here). **Every** plotting call below goes through this — no script sets its own DPI/style ad hoc.
- [x] **Every report `.md` file embeds its figures**, not just links to the folder — `![caption](figures/whatever.png)` — so `ml/reports/*.md` is self-contained and reads correctly if copied straight into the FYP report/appendix.

### Phase 5 — Stage 5.1: `ml/` scaffold (2026-07-16)

- [x] Created `ml/data/` (gitignored via a new `ml/data/*` rule in `.gitignore`, with
      `.gitkeep` excepted so the empty dir is still tracked) and `ml/artifacts/`
      (committed, `.gitkeep` placeholder — no artifacts exist yet, that's Stage 5.5+).
      `ml/reports/` and `ml/reports/figures/` already existed from Stage 5.0.
- [x] `ml/requirements.txt` — mediapipe, scikit-learn, pandas, numpy, joblib,
      matplotlib, seaborn, pyyaml (the last one because `audit_rehab246.py`, shipped in
      Stage 5.0, already imports it).
- [x] **X1 editable install, verified live, not just documented:** added a minimal
      `backend/pyproject.toml` (setuptools, `include = ["app*"]`) so `app` is
      pip-installable in editable mode — it does not replace `backend/requirements.txt` as
      the FastAPI app's own dependency list, it exists solely for this. Documented the
      exact commands in `ml/README.md`. **Verified in a throwaway venv**: `pip install -e
./backend` followed by `from app.module_b.core.features import FeatureVector` and
      `from app.module_b.squat.exercise import SquatExercise` both succeeded — real import,
      not a hypothetical path. Confirmed the change doesn't affect the backend app itself:
      full backend suite still 126/126 passing after adding the file.
- [x] `ml/scripts/plotting.py` — `save_fig(fig, name, figsize=None) -> Path`, fixed
      DPI 150, a `FIGSIZES` dict of named sizes (`single`/`wide`/`grid_4x4`/
      `bland_altman` — the sizes Stage 5.4's known figures need; more can be added when a
      later stage needs a new one, not speculatively now), one `sns.set_theme()` call
      applied lazily on first save. Smoke-tested: a real matplotlib figure saved through it
      round-tripped to disk correctly (deleted after the check).
- [x] `ml/README.md` — the install commands above, the macOS/Apple-Silicon MediaPipe
      GPU-delegate note pre-recorded for Stage 5.2 (so nobody "fixes" the CPU delegate
      later), the report figure-embedding convention, and the directory layout.
- [ ] **Deliberately not created (scope discipline — these are later stages' work, not
      5.1's):** `ml/docs/ec3d_joint_mapping.md` (Stage 5.9), and every `scripts/*.py` shown
      in the target tree besides `plotting.py` and the already-existing
      `audit_rehab246.py` — `extract_landmarks.py` (5.2), `build_features.py` (5.3),
      `check_feature_validity.py`/`check_mocap_agreement.py` (5.4), `train_squat.py` (5.5),
      `sweep_fusion_weights.py` (5.6), `evaluate_squat.py` (5.7), `validate_ec3d.py` (5.9).

### Stage 5.2 — Landmark extraction from RGB video

- [x] `extract_landmarks.py`:
  - **Loads the _same_ `pose_landmarker_full.task` asset the frontend self-hosts.** This is the whole point of X3 — a different model variant reintroduces the domain gap. Path in `ml/config.yaml`, pointing at the frontend's asset.
  - `RunningMode.VIDEO`, `delegate=CPU`. **MediaPipe Python's GPU delegate is Ubuntu-only** — on macOS/Apple Silicon it errors; CPU + XNNPACK is the correct and only path here. Document this in `ml/README.md` so nobody "fixes" it later.
  - Extracts **world landmarks** (X3), not image landmarks.
  - Processes only the videos needed: **Ex6 (squat)**, the camera chosen in Stage 5.0, honouring the orientation filter.
  - **Resumable + cached** — writes one `.npz` per video, skips existing. A 2.7 GB batch should never need to restart from zero.
  - Records extraction metadata: model asset **hash**, mediapipe version, delegate, fps.
- [x] **Parity check (blocking):** extract one short clip via this Python pipeline, and record the same clip through the browser runtime. Compare per-frame world-landmark distributions. Report the divergence in `ml/reports/PARITY_CHECK.md`. Small numeric differences are expected (delegate/backend); a _structural_ difference means the pipeline is wrong.
- [x] Apply the **same preprocessing as runtime** (X1): confidence filter 0.6, ≤5-frame linear interpolation, One Euro, normalisation. Import it from the backend — do not re-implement.

### Phase 5 — Stage 5.2: Landmark extraction (2026-07-16)

- [x] **Reconciliation finding, resolved by HY before writing code:** traced the
      actual live squat pipeline (`POST /api/module-b/analyze` -> `SquatExercise.
segment`/`extract_features`, and `useMediaPipePose.ts` upstream of it) and found
      it applies **zero** confidence-filter/gap-fill/One-Euro preprocessing — raw
      MediaPipe world landmarks flow straight from the frontend into segmentation and
      feature extraction. `MODULE_B_CORE_CONFIG["interpolation_max_gap_frames"]` is
      defined but never consumed anywhere. This differs from Module A (STS/SLS/WBLT),
      which does run `LandmarkSmoother` server-side. X3's "confidence filter -> gap
      fill -> One Euro -> normalisation" pipeline is therefore aspirational for
      Module B squat, not implemented. **HY's decision: option (a)** — match runtime
      as it actually is (no smoothing in `extract_landmarks.py` either), preserving
      true X1 parity with the pipeline that exists today, rather than smoothing
      offline data the live model will never see smoothed (option b) or silently
      changing Phase 4's already-verified live squat code (option c, out of scope for
      this stage). Recorded in `extract_landmarks.py`'s module docstring so this
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
    non-monotonic against video 1's last frame (~171,000ms), crashing the batch
    on the 3rd video. Fixed: one fresh `PoseLandmarker` per video (closed after
    use) — correct and still fast enough (~92 fps on this machine).
  - **Extraction result (all 9 side-view Ex6 videos, verified by reading every
    `.npz` back):** 30,028 total frames processed, only **1** frame with no
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
      `claude/serene-bhaskara-74aaf3`, coordinated live with the parallel session
      doing Stage 5.1-5.3 in the main checkout) and confirmed the gap: raw
      MediaPipe world landmarks flowed straight from the frontend into
      `SquatExercise.segment`/`extract_features`, with zero confidence-filter/
      gap-fill/One-Euro preprocessing, unlike Module A (STS/SLS/WBLT), which runs
      `LandmarkSmoother` server-side. `MODULE_B_CORE_CONFIG["interpolation_max_gap_frames"]`
      (=5) was defined but never consumed anywhere.
- [x] **HY decision:** add real preprocessing now, before Stage 5.3's feature
      table gets used further — re-extraction cost was still low (nothing built
      on the unsmoothed `ml/data/landmarks/*.npz` yet). Build genuine linear
      interpolation for the gap-fill (Module A's smoother only hold-lasts on low
      visibility, it never interpolated).
- [x] **New shared module:** `backend/app/module_b/core/preprocessing.py` —
      `preprocess_world_landmarks(frames)` runs confidence filter (`MIN_VISIBILITY`,
      reused from `app.module_a.core.config`) → gap fill (new: linear
      interpolation, time-weighted, up to `interpolation_max_gap_frames`, leaving
      longer/leading/trailing gaps for the next step) → One Euro (`LandmarkSmoother`,
      imported from `app.module_a.core.smoothing`, not forked). Deliberately built
      as a plain importable function (not inlined in the router) so `ml/`'s
      offline extractor can import the identical implementation later — X1.
- [x] **Stateful-filter ordering, confirmed with the parallel session:**
      `preprocess_world_landmarks` takes the _entire_ session's frame stream and
      must be called once over the whole thing before segmentation — `OneEuroFilter`
      is stateful (per-landmark-per-axis history), so windowing into reps first
      and smoothing per-window would reset filter state at every rep boundary and
      diverge from what live capture actually produces. Added a regression test
      asserting this: preprocessing a stream in one call vs. two independently
      preprocessed halves gives different results.
- [x] **Wired into `backend/app/module_b/core/router.py`:** `assess_capture_quality`
      still runs on the raw capture (it's a diagnostic on what was actually
      recorded); `exercise.segment`/`extract_features` now run on the
      preprocessed stream. No frontend change needed — Module A's precedent
      already showed this preprocessing belongs server-side.
- [x] **Tests:** `backend/tests/test_module_b_preprocessing.py` (8 new tests —
      short-gap interpolation, gap-longer-than-max left for hold-last, leading/
      trailing gaps untouched, interpolated-point visibility bump, the stateful
      full-stream contract, and a Phase 4 regression check: `_five_clean_reps()`
      through `preprocess_world_landmarks` → `segment_squat_frames` →
      `extract_squat_features` still yields 5 reps with a valid feature vector
      each). Full backend suite: **134/134 passing** (126 previous + 8 new).
      Black/isort clean.
- [x] **Done in the follow-up below (2026-07-16), not in this entry:** the `ml/`
      re-run. See "Cross-cutting follow-up — far-limb occlusion" immediately below;
      it also **amends this entry's hold-last design**, which did not survive
      contact with real side-view data.

### Cross-cutting follow-up — far-limb occlusion breaks hold-last (2026-07-16)

Found by the `ml/` re-run above landing on real REHAB24-6 side-view data. The
preprocessing entry above assumed "gaps longer than `interpolation_max_gap_frames`
or without an anchor → leave them to `LandmarkSmoother`'s hold-last." That
assumption is wrong for a single side-view camera, and the failure was loud.

- [x] **The finding (measured, not inferred):** a side-view camera tracks the near
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
- [x] **Why it was released, not worked around:** the far leg is **low-confidence,
      not wrong** — its raw trajectory still tracks a plausible squat (peak 99.9° on
      a rep where the near knee read 77.9°). Hold-last was therefore discarding real
      signal and substituting a stale value: turning "uncertain but usable" into
      "confidently stale", which is strictly worse than the noisy estimate.
- [x] **HY decision (option b of three offered):** release hold-last for persistent
      occlusion, **scoped to Module B's preprocessing**. Rejected alternatives:
      (a) accept the damage and document it as a limitation — would have shipped a
      knowingly broken live rep counter; (c) make squat's features prefer the near
      leg only — would have silently cost `symmetry_index_pct` (it is literally
      `|θ_L − θ_R|`, unmeasurable from one leg) and thrown away usable far-leg data.
- [x] `core/preprocessing._release_persistent_occlusions()` — a low-visibility run
      **longer than `interpolation_max_gap_frames`** has its visibility raised to
      exactly `MIN_VISIBILITY`, so the One-Euro pass smooths the landmark's own raw
      estimate instead of hold-lasting a stale one. Runs of ≤5 frames are untouched,
      so a genuine brief flicker still hold-lasts as designed. Reuses the same
      visibility-bump idiom `_interpolate_gap` already used — the one lever that
      steers hold-last **without forking `LandmarkSmoother`**.
- [x] **No second config knob, and this was reviewed, not assumed.** The release
      threshold reuses `interpolation_max_gap_frames` rather than introducing its own
      tunable. Asked the session that owns `preprocessing.py` to confirm or object;
      it reviewed the diff and confirmed (2026-07-16): that constant already means
      "how long a gap can be before we stop trusting continuity assumptions", so this
      is the same semantic rather than an overload, and a separate constant would be
      two numbers to keep in sync for no benefit. It also confirmed the layering
      (`_fill_gaps` gets first crack at short runs; this only fires beyond the max) and
      that Module A is untouched. Do not split these into two knobs without a reason
      that defeats the above.
- [x] **`LandmarkSmoother` itself deliberately untouched** — it is shared with
      Module A (STS/SLS/WBLT all call `smooth_frame(t, world)`), whose behavior and
      verified results must stay byte-identical. The fix lives entirely in Module B's
      preprocessing layer. Confirmed: full suite green with zero Module A changes.
- [x] **Result:** far-leg signal restored. Median `knee_flex_peak_deg` back to 98.3°
      (vs 99.8° raw — the small residual is legitimate smoothing damping). FSM front-rep
      agreement **93/98 (94.9%)**, marginally _better_ than the 92/98 raw baseline,
      i.e. preprocessing now helps rep detection instead of destroying it.
- [x] **Tests:** rewrote `test_gap_longer_than_max_is_left_for_hold_last` →
      `test_gap_longer_than_max_is_released_not_frozen` — the old test _encoded the
      exact bug_ (asserting a long gap stays frozen), so it was changed deliberately
      as a contract change, not bent to pass. Added
      `test_brief_gap_without_anchor_still_holds_last` (proves the fix is bounded to
      persistent occlusion) and `PersistentOcclusionTests` (a far-limb-style landmark
      that is never confident must still track its real excursion). Full backend suite:
      **136/136**. Black/isort clean.
- [ ] **Left open for Stage 5.4, deliberately:** whether the far leg's estimate is
      _accurate_ rather than merely plausible is exactly what `check_mocap_agreement.py`
      settles against the OptiTrack ground truth — not asserted here. Also unresolved:
      `symmetry_index_pct`'s median of ~30% looks inflated by its own formula
      (dividing by a near-zero mean while standing), a feature-design question for
      that gate, not this fix.

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
      previous stages make about the X1 contract. `app.module_b.squat.features.
extract_squat_features` and `SQUAT_FEATURE_NAMES` (13 features), `app.module_b.
squat.segmentation.segment_squat_frames`, and the `FeatureVector`/`Rep` dataclasses
      all exist as Stage 4.2/4.3 describe, and the ml venv's editable install imports
      them cleanly (X1 — the offline extractor calls the live functions, never
      re-implements them). Also re-verified the dataset↔extraction frame alignment
      Stage 5.0/5.2 rely on: Segmentation.csv `first_frame`/`last_frame` index directly
      into the Camera18 `.npz` (e.g. PM_008 rep 1 = frames 100–220), the same range
      Stage 5.2's parity check used.
- [x] `ml/scripts/build_features.py` — windows every **side-view** rep
      (`exercise_id == 6` AND `cam17_orientation == "front"`, i.e. Camera18 = profile,
      per Stage 5.0 option a) by the dataset's physio-verified `first_frame`/`last_frame`
      (inclusive), builds the runtime frame shape (`worldLandmarks` xyz + `timestampMs`)
      from the `.npz`, and calls the backend's `extract_squat_features()` (X1). Emits
      `ml/data/squat_features.csv` — **98 rows** (one per rep, matching the audit's 98
      verified side-view reps), **72 Good / 26 Poor**, across **9 subjects / 9 videos**.
      Columns: `person_id`, `video_id`, `repetition_number`, the 13 features in
      `SQUAT_FEATURE_NAMES` order, `correctness` (raw 0/1), `label` (Good/Poor),
      `orientation`, `lights_on`, `mocap_erroneous`, `feature_schema_version` (`1.0.0`).
  - **Naming note (not drift):** the checklist says `lighting`; the actual
    Segmentation.csv column is `lights_on` (0/1) — the CSV uses the real column name,
    consistent with the Stage 5.0 schema-doc correction. A separate `label` column
    (the normalised Good/Poor target) is emitted alongside the raw `correctness` for
    traceability; the checklist's "`correctness` label" wording is satisfied by both.
- [x] **Schema validation:** `write_features_csv()` asserts the CSV's feature block,
      in order, equals `SQUAT_FEATURE_NAMES` before writing — the build raises loudly on
      any drift. `extract_squat_features` also re-checks `FeatureVector.names` per rep.
- [x] **Label normalisation (Option A):** `ml/artifacts/label_map.json` written (a
      committed artifact — `ml/artifacts/` is not gitignored, per Locked Assumption #4):
      `{"1": "Good", "0": "Poor"}`, `no_fair_in_training: true`, plus an explicit note
      that Fair is derived at inference from the calibrated low-confidence margin
      (Stage 5.6), never a trained class.
- [x] **FSM-vs-dataset segmentation agreement (free validation, Stage 4.3 FSM):**
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
  - **Correctness fix caught during implementation:** the first matcher let one merged
    detection count against two GT reps, producing the impossible `detected 17 /
matched 20` for PM_038 (matches exceeding detections). Reworked to strict
    one-to-one greedy matching so `matched ≤ min(detected, gt)` always holds — the
    numbers dropped from an inflated 187/195 to an honest 182/195.
- [x] **Windowed-rep sanity (logged in the report, not a gate — Stage 5.4 does the real
      validity check):** `knee_flex_peak_deg` spans 69.7°–129.8° (median 99.8°) and
      `rep_duration_s` 2.13–5.13 s across the 98 reps — non-trivial squat depth in every
      window, corroborating the frame-alignment reconciliation above.
- [x] Verification: `build_features.py` runs clean; **byte-identical CSV across two
      runs** (X8 determinism — `md5` confirmed). Black + isort clean. Backend untouched
      (`git status backend/` empty; suite stays 126/126). `ml/data/squat_features.csv`
      and the `.npz` landmarks are gitignored (regenerable from the raw dataset via
      `extract_landmarks.py` → `build_features.py`); `label_map.json` and
      `FEATURE_TABLE.md` are committed.
- [ ] **Deliberately not done (out of Stage 5.3 scope):** per-subject class presence is
      only surfaced (subjects 2/4/9 are single-class Good, subject 1 is 16 Good/1 Poor),
      not acted on — the LOSO/stratified-group-k-fold fallback that handles it is
      Stage 5.5's job. No feature was dropped or kept on the basis of the sanity stats
      above; the keep/drop verdict and the `norm_ref` bake-off are Stage 5.4's gate.

#### Re-run against the real preprocessing (2026-07-16, supersedes the numbers above)

The cross-cutting preprocessing change landed on `main` (merge `ecddd9a`), so the
unsmoothed feature table built above no longer matched the live runtime and was
rebuilt — X1 is only real if the offline features come from the _same_ pipeline.

- [x] `build_features.py` now imports the backend's
      `preprocess_world_landmarks` (X1 — the shared `module_b/core/preprocessing.py`
      function, not a re-implementation) and applies it **once per video over the full
      chronological stream, then windows** by the dataset boundaries — mirroring
      `router.py`'s single call site ahead of `segment()`. Windowing first would reset
      `OneEuroFilter`'s per-landmark state at every rep boundary and drift from live.
      One shared preprocessed-stream cache feeds **both** the feature table and the FSM
      agreement check, so neither path can derive a subtly different stream.
- [x] `visibility` is now carried into the offline frame dicts (previously x/y/z only) —
      both the gap-fill's confidence filter and `LandmarkSmoother`'s hold-last branch on
      it, so omitting it would have silently disabled them offline while they ran live.
- [x] The FSM agreement check now runs on the **preprocessed** stream, matching what the
      live FSM actually receives, rather than raw landmarks.
- [x] **This re-run is what surfaced the far-limb occlusion failure** — see the
      "Cross-cutting follow-up" entry above. Final numbers after that fix: **98 reps
      (72 Good / 26 Poor) unchanged**; `knee_flex_peak_deg` median **98.3°** (was 99.8°
      unsmoothed — the difference is legitimate smoothing damping); FSM front-rep
      agreement **93/98 (94.9%)**, total **184/195** (94.4% recall / 95.8% precision).
- [x] Verification: byte-identical CSV across two runs (X8 determinism, `md5`);
      Black/isort clean; full backend suite **136/136**.
- [ ] **Flagged for Stage 5.4, not acted on here:** `knee_flex_peak_deg` separates the
      classes but in the **opposite direction to the plan's stated expectation** — Good
      median 92.8° vs Poor median **107.7°**, i.e. incorrect reps go _deeper_, whereas
      Stage 5.4's gate text assumes "`knee_flex_peak_deg` should be lower for incorrect
      reps". The gate's pass/fail condition is separation, which holds — but its
      directional assumption does not, and the keep/drop reasoning must not be written
      as if it did. Not investigated here; it is that gate's job.

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
> 2. **`symmetry_index_pct` is suspect on its own formula, independent of the data.**
>    It is a per-frame `|θ_L − θ_R| / mean × 100` averaged over the rep, so near
>    standing (both angles ≈ 0) the denominator collapses and the percentage explodes —
>    which is most of why its median sits at ~30%. Judge the feature on that basis, not
>    just its boxplot.

- [x] `check_feature_validity.py` — per feature, plot **and** report its distribution split by class. A feature enters the model **only if it visibly separates classes** (e.g. `knee_flex_peak_deg` should be lower for incorrect reps). Output `ml/reports/FEATURE_VALIDITY.md` with an explicit keep/drop verdict + justification per feature.
  - [x] **Figure (required):** `figures/feature_validity_boxplots.png` — one boxplot (or violin) per feature, class on the x-axis, arranged as a grid (e.g. 4×4 subplots via `plt.subplots`), so every feature's class separation is visible on one page.
  - [x] **Figure (required):** `figures/feature_correlation_heatmap.png` — a correlation matrix across all candidate features (seaborn `heatmap`), to justify any later "these two features are redundant, drop one" calls.
- [x] `**norm_ref` bake-off** (R5.3): compute cross-subject variance under `trunk_length` vs `thigh_length`; pick the lower. Record the number. Update the backend config to match — **and re-run any Phase 4 test that depended on the default.**
  - [x] **Figure (required):** `figures/norm_ref_variance_comparison.png` — a paired bar chart, per-subject variance under each candidate, so the "lower" claim is visually checkable, not just a single number in prose.
- [x] `check_mocap_agreement.py` _(uses `3d_joints.zip`)_ — compute knee-flexion angle from our MediaPipe world landmarks vs from the **OptiTrack 26-joint mocap GT** on the same frames. Report **ICC(2,1) + Bland-Altman**, reusing `backend/app/module_a/core/evaluation/agreement.py` (it's unit-agnostic and already shared — do not fork it).
  - [x] **Figure (required):** `figures/mocap_agreement_bland_altman.png` — the standard Bland-Altman plot (mean vs difference, limits of agreement shaded). If `agreement.py` already produces one for Module A, reuse that plotting function too — don't write a second implementation of the same chart.
- [x] **Gate:** if `knee_flex_peak_deg` does **not** separate the classes, stop. Either the extraction, the view filter, or the windowing is wrong. Do not train through a red flag.

### Phase 5 — Stage 5.4: Feature-validity sanity [GATE] (2026-07-16)

- [x] **GATE: PASS.** `knee_flex_peak_deg` separates the classes decisively — **AUC
      0.837** (Good median 92.8° vs Poor median 107.7°), and the direction holds in
      **5/5** of the subjects able to vote on it, so it is not one subject's artefact.
      Extraction, view filter and windowing are not broken, which is what this gate
      exists to catch. Training may proceed.
  - **The separation runs OPPOSITE to the plan's stated expectation.** The checklist
    says "`knee_flex_peak_deg` should be lower for incorrect reps"; measured, incorrect
    reps go **deeper** (Poor 107.7° > Good 92.8°). The gate's condition is _separation_,
    which holds either way, so this is not a failure — but REHAB24-6's Ex6 "incorrect"
    reps are a mix of deliberate faults, not specifically shallow ones, so **no
    downstream rule may assume "deeper = better"** for this cohort. Flagged for
    Stage 5.5/5.6.
- [x] `ml/scripts/check_feature_validity.py` → `ml/reports/FEATURE_VALIDITY.md` +
      `figures/feature_validity_boxplots.png` (4×4 grid, all 13 features) +
      `figures/feature_correlation_heatmap.png`. **Verdicts: 10 KEEP / 3 DROP**
      (`rep_duration_s` AUC 0.492, `descent_ascent_ratio` 0.467, `symmetry_index_pct`
      0.442 — all effectively at the 0.5 no-separation point). Strongest features:
      `ankle_df_proxy_deg` (0.882), `knee_rom_deg` (0.859), `knee_flex_peak_deg`
      (0.837). Redundant pairs recorded, not acted on: `knee_flex_peak_deg` ~
      `knee_rom_deg` (r=0.97) and `trunk_lean_peak_deg` ~ `trunk_lean_mean_deg` (0.93).
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
      `figures/norm_ref_variance_comparison.png`. **Winner: `trunk_length`** (mean
      cross-subject CV **0.180 vs 0.201**), beating `thigh_length` on **both**
      normalised features and on **both** metrics. `SQUAT_CONFIG["norm_ref_strategy"]`
      updated `thigh_length` → `trunk_length` and **retagged
      `[proposed heuristic, R5.3]` → `[dataset-derived, R5.3]`** — it is earned now, not
      guessed. Feature table + validity report regenerated under the new reference
      (verdicts unchanged; the gate feature is unaffected by `norm_ref`).
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
      `figures/mocap_agreement_bland_altman.png`. Reuses `module_a/core/evaluation/
agreement.py`'s `icc_2_1`/`bland_altman` (confirmed stats-only — it has no plotting to
      reuse, so the Bland-Altman chart is drawn in `ml/` via the shared `plotting.py`).
      Compares the **peak of the bilateral mean knee flexion per rep** — i.e. exactly
      `knee_flex_peak_deg` — over all 98 reps (all `mocap_erroneous=0`, so no
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
  - **This independently condemns `symmetry_index_pct`, mechanistically.** The feature
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
  - [x] `ml/reports/SQUAT_TRAINING_REPORT.md` includes the **full `cv_results_` table** (every combination + score), not a one-line "best params were X" summary. Losing combinations stay in the table — do not prune them out after the fact.
- [x] **Calibration** — `CalibratedClassifierCV` (isotonic if N allows, else sigmoid/Platt) on a held-out fold. ET `predict_proba` is over-confident; the Fair band depends entirely on calibrated probabilities being meaningful.
  - [x] **Figure (required):** `figures/calibration_reliability_curve.png` — predicted probability (x-axis, binned) vs observed frequency (y-axis), plotted **before and after** calibration on the same axes (`sklearn.calibration.calibration_curve` + a plotted 45° reference line), so the improvement from calibration is visible, not asserted. An uncalibrated Fair band is a fabricated third class — this figure is the evidence it isn't.
  - [x] Output `ml/reports/SQUAT_TRAINING_REPORT.md`: the full hyperparameter search table and figure above, which CV scheme was used and why, and the reliability curve embedded inline.

### Phase 5 — Stage 5.5: Train the Extra Trees classifier (2026-07-16)

- [x] **`ml/scripts/train_squat.py`** — binary Good/Poor (Option A), `random_state=42`
      from `config.yaml`, splitters `shuffle=False`. Structure: `_choose_cv()`,
      `_inner_splits()`, `_search()`, `_calibrate()`, `build_final_model()`,
      `nested_cv()`, `_plateau_stats()`, `_wilson_interval()`, `_reliability_bins()`,
      `plot_hyperparameter_search()`, `plot_calibration()`, `_importances()`,
      `write_report()`. Added `"grid_2x2": (11, 8)` to `plotting.py`'s `FIGSIZES`
      (its documented extension point, as Stage 5.4 did with `heatmap`).
- [x] **CV: `StratifiedGroupKFold(5, groups=person_id)` — the plan's fallback, and it
      was triggered by the data, not chosen.** `_choose_cv()` detects the condition
      rather than hardcoding it: **subjects 2, 4, 9 are Good-only**, so LOSO would give
      three of nine folds a test set with no Poor rep, making ROC AUC and Poor-recall
      _undefined_ there. No subject appears in both train and test, so there is no
      identity leakage — but each test fold now holds ~2 subjects. **The write-up must
      say "subject-wise 5-fold", not "LOSO".** Per-fold AUC: 0.889 / 0.887 / 0.773 /
      0.893 / 1.000.
- [x] **Nested tuning, 180 combinations** (`n_estimators` × `max_depth` ×
      `min_samples_leaf` × `min_samples_split`), `GridSearchCV` inside each outer
      training fold only, 3 subject-disjoint inner folds. Full unpruned `cv_results_`
      table (all 180 rows, both metrics) is in the report. **Tuned on ROC AUC, not
      F1/precision** — Stage 5.6's whole job is to replace the 0.5 threshold, so tuning
      a threshold-dependent metric would optimise a rule about to be discarded;
      `f1_macro` recorded per combination anyway. `GridSearchCV.best_score_` is
      explicitly **not** quoted as a generalisation estimate (it is the max over 180
      noisy estimates).
- [x] **Result: out-of-fold ROC AUC 0.832**, macro-F1 0.631 @0.5, Brier 0.154 → 0.149.
      Chosen params `n_estimators=500, max_depth=None, min_samples_leaf=2,
min_samples_split=10`.
- [x] **Finding — the search is a plateau, and that is the honest result.** The entire
      grid spans **0.0407** ROC AUC (0.8718–0.9125) while the **median std across inner
      folds is 0.0455 — larger than the whole span**; **163/180** combinations sit
      within 1 std of the winner. ET is _insensitive to these hyperparameters at this
      sample size_. Do not present the winner as a tuned optimum. Verified
      mechanistically: `max_depth` None/12/16 score **identically to 4 dp** because
      trees average depth 7.5 (max 13) and only **1 in 500** exceeds depth 12 — the
      constraint never activates; `min_samples_split≥10` on 98 reps binds first.
- [x] **Finding — Poor recall collapses 0.808 → 0.385 at the 0.5 threshold while AUC is
      unchanged.** Not a regression: `class_weight='balanced'` puts the raw forest's 0.5
      at the _reweighted_ boundary, and calibration correctly pushes P(Good) up toward
      the true 73% base rate, so fewer reps fall below 0.5. **The model misses ~62% of
      Poor reps at 0.5** — the worst failure mode for a rehab grader. **Handoff to Stage
      5.6:** its text sweeps `confidence_low_threshold` "above 0.5" as a _Fair band_,
      but the **decision boundary itself** also wants to move above 0.5. Those are two
      distinct knobs its checklist currently blurs into one. Not resolved here.
- [x] **Bug found by my own assertion, fixed properly.** The report claims calibration is
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
- [x] **Calibration: sigmoid, not isotonic — N does not allow.** 26 Poor reps from 6
      subjects; isotonic would memorise. **Reported honestly as weak evidence:** Brier
      gains only 3% relative, neither curve tracks the diagonal (uncalibrated is
      under-confident at the top, sigmoid over-corrects mid-range), and with ~19 reps
      per bin **the two curves are not separated by more than their own uncertainty**.
      Switched the error bars from Wald to **95% Wilson** after noticing Wald collapses
      to _zero width_ at p=1 — two bins sit there and would have plotted as perfect
      certainty from 19 samples. Consequence for 5.6: the Fair band's real justification
      is the ranking (AUC 0.832), not demonstrated probability calibration.
- [x] **Answered Stage 5.4's two open questions, with model evidence.**
  - **Trained on all 13 features; DROP verdicts recorded, not executed** — both for
    scope (editing `SQUAT_FEATURE_NAMES` bumps `feature_schema_version`) and because
    5.4's verdicts used the held-out subjects' reps, so acting on them would be
    selection bias. **Two independent methods converged: Spearman rho = 0.775** between
    Gini importance and 5.4's univariate effect size; all three DROP features rank
    10/11/13 of 13. **`symmetry_index_pct` — the check that mattered passed:** despite
    correlating with mocap truth at r ≈ −0.05, the model did _not_ latch onto it as a
    subject fingerprint (rank 11, 0.0395). Still flagged for 5.8's model card.
  - **Redundant pair `knee_flex_peak_deg` ~ `knee_rom_deg` (r=0.97): keep both.** They
    rank 2nd/3rd (0.127, 0.104) — correlated features _split_ importance, so together
    depth accounts for ~0.23, on par with `ankle_df_proxy_deg`'s 0.24. One signal, two
    labels; ET is unbothered, and dropping either bumps the schema for no gain.
- [x] **`check_feature_validity.analyse_feature()` is imported, not transcribed** — the
      first draft hardcoded 5.4's AUCs into a table and **7 of 13 were wrong** (e.g.
      `stance_width_norm` written as 0.652, actually 0.374 with verdict
      _KEEP (caveat)_). Importing eliminated the whole class of error and keeps the two
      reports from diverging. Same discipline as X1.
- [x] **Verified:** X8 determinism — SHA-256 of the report and both figures byte-identical
      across consecutive runs (and again after formatting). Backend suite **136/136**
      via `python -m unittest discover -s tests` (unchanged; no backend file touched).
      `black` clean and `isort --profile black` clean — the profile matters, bare `isort`
      fails on every pre-existing `ml/` script too.
- [ ] **Deliberately not done (out of Stage 5.5 scope):** no artifact exported —
      `model.joblib`/`calibrator.joblib`/`feature_schema.json`/`model_card.md` are
      **Stage 5.8**'s deliverable, and `build_final_model()` is the entry point it should
      call so the model is defined in one place. No threshold chosen (the 0.5 used for
      the recall columns is a reporting convenience, **Stage 5.6** decides). No 3-band
      confusion matrix, latency, or baseline comparison (**Stage 5.7**). Permutation
      importance not run — Gini's ranking is enough to _corroborate_ 5.4, but if a
      feature is ever dropped on importance evidence, permutation is the measure that
      should justify it.

### Stage 5.6 — Fair threshold + fusion weight sweep

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision) item 1): this stage is where the Phase 4 Stage 4.0 `w_rule_default`/architecture-doc-§10.4 conflict actually gets settled — **empirically, not by picking one document over the other.** The selection criteria below are expanded beyond precision alone.

- [x] `**confidence_low_threshold**` (the Fair band): the R7 default of 0.65 is a **[proposed heuristic]**. Because Option A has only binary Good/Poor probabilities, sweep **only thresholds strictly above 0.5**, and include candidates above 0.65; pick against the calibration curve + the precision objective. Report the chosen value **and** the sweep — the number must be earned, not asserted.
  - [x] **Figure (required):** `figures/confidence_threshold_sweep.png` — precision/recall (or precision + Fair-band size) as a line plot against the swept threshold, with the chosen value marked (vertical line + annotation).
- [x] `sweep_fusion_weights.py` — sweep `w_r` from **0.2 → 0.8 in 0.1 steps** on the validation folds; report Good/Fair/Poor confusion + precision + **macro-F1** at each. **Selection criteria (HY 2026-07-16):** the winning weight must be justified against **both** (a) macro-F1 across the 3 bands, **and** (b) the **severe-misclassification rate** — the count/rate of Poor→Good and Good→Poor confusions specifically, tracked as its own number, not folded into an aggregate. A weight with slightly lower precision but a materially lower severe-misclassification rate is the better choice for a rehab-grading system (telling a poor-form user they're fine is the one failure mode that matters most); do not default to "highest precision wins" if it trades away severe-error safety.
  - [x] **Figure (required):** `figures/fusion_weight_sweep.png` — precision, macro-F1, **and severe-misclassification rate** (three lines) plotted against `w_r` from 0.2–0.8, chosen weight marked the same way as above.
- [x] Write the winner back into `backend/app/module_b/core/config.py`, replacing the 0.4/0.6 placeholder, and **retag it `[dataset-derived]`** (it is no longer a heuristic). Record in the report why this value won over both the Stage 4.0 default and the architecture doc's §10.4 recommendation, citing the actual macro-F1 and severe-misclassification numbers.
- [x] Output `ml/reports/SQUAT_FUSION_SWEEP.md` with all three figures/lines embedded.

### Phase 5 — Stage 5.6: Fair threshold + fusion weight sweep (2026-07-16)

- [x] **`ml/scripts/sweep_fusion_weights.py`** — reuses Stage 5.5's seeded `nested_cv()`
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
- [x] **Major finding: the naive single-pass ordering is Poor-blind, and it's
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
- [x] **Fix: iterated joint search, not a single pass.** Alternates the threshold sweep
      and weight sweep, feeding each round's winner into the next, until neither moves
      (`find_stable_operating_point()`, bounded at `MAX_ROUNDS=6`). **Converged after 3
      rounds:** round 1 (input 0.4) → threshold 0.55 → weight 0.2; round 2 (input 0.2)
      → threshold 0.85 → weight 0.2; round 3 confirms the same pair. This is standard
      coordinate ascent over the two sweeps the checklist already specifies — no new
      sweep dimension, only recognising they must be resolved jointly. The naive
      round-1 answer is kept in the report (not discarded) alongside why it was revised.
- [x] **Fusion-weight selection rule corrected to match HY's literal wording.** Initial
      draft summed Poor→Good + Good→Poor into one "severe count" for the primary key;
      re-read HY's criterion ("Poor→Good ... is the one failure mode that matters
      most") and fixed `_pick_fusion_weight()` to use **Poor→Good alone** as the
      primary key (summing would let a rise in the worse failure mode hide behind a
      fall in the milder one), with Good→Poor then macro-F1 breaking ties (within-1
      margin at n=98, since a single event either way is sampling noise).
- [x] **Result (converged): `confidence_low_threshold = 0.85`, `w_rule = 0.2`,
      `w_ml = 0.8`.** At this point: precision(Good)=1.000, precision(Poor)=1.000,
      **0 severe misclassifications** (0 Poor→Good, 0 Good→Poor), macro-F1=0.481,
      Fair-band coverage=0.469 (46/98 reps abstain) — a deliberate, large safety
      trade-off, not hidden.
- [x] **Both the Stage 4.0 placeholder (0.4) and the architecture doc's §10.4
      recommendation (0.6) also reach 0 severe misclassifications at the converged
      threshold — but not for the same reason, and this distinction is the actual
      reason macro-F1 mattered in selection.** At `w_rule=0.4`/`0.6`, `recall(Poor)=0`:
      every Poor rep is safely routed to Fair, **none is ever correctly identified as
      Poor**. At the chosen `w_rule=0.2`, some Poor reps are correctly caught
      (`recall(Poor)=0.077`) with the same 0 severe count. Severe-count alone would
      have missed this; macro-F1 (0.481 vs 0.410) is what distinguishes "safe but
      blind" from "safe and somewhat informative."
- [x] **Config updated and retagged:** `backend/app/module_b/core/config.py` —
      `w_rule_default: 0.4→0.2`, `w_ml_default: 0.6→0.8`,
      `confidence_low_threshold: 0.65→0.85`, all retagged `[dataset-derived, Stage
5.6]` with the reasoning inline. `w_rule_low_confidence` (0.7) and `q_min` (0.6)
      untouched (out of scope).
- [x] **Two backend tests updated, both real fixes not bent to pass:**
      `test_module_b_registry.py`'s single `test_core_config_freezes_stage_4_0_values`
      split into `test_core_config_freezes_still_unresolved_stage_4_0_values`
      (everything Stage 5.6 didn't touch) + a new
      `test_core_config_stage_5_6_dataset_derived_fusion_values` (the three changed
      values); `test_module_b_fusion.py`'s
      `test_model_fusion_carries_model_version_and_default_weights` bumped its
      `StubModel(rule_score=8.0)` to `9.0` so its resulting confidence (0.9) still
      clears the new 0.85 bar and actually exercises the default-weight path, rather
      than silently falling into the already-covered low-confidence branch.
- [x] **Verified:** X8 determinism — SHA-256 of the report and both figures
      byte-identical across consecutive runs, including after formatting. Backend
      suite **137/137** (136 + 1 net new, from the registry-test split) via
      `python -m unittest discover -s tests`. `black` clean, `isort --profile black`
      clean.
- [ ] **Deliberately not done (out of Stage 5.6 scope):** `band_thresholds` (D6,
      Poor/Fair/Good score cut points) unchanged — a separate, already-fixed
      heuristic this stage doesn't touch. No 3-band confusion-matrix figure, baseline
      comparison, or latency measurement (Stage 5.7). No artifact export (Stage 5.8).
      The grid's own lower boundary (`w_rule=0.2`) won outright — the trend suggests
      going lower might help further, but extending below the checklist's specified
      0.2–0.8 range would be scope creep; flagged for reconsideration, not acted on.

### Stage 5.7 — Evaluation

**Completed 2026-07-16.** `ml/scripts/evaluate_squat.py` → `ml/reports/SQUAT_EVALUATION_REPORT.md`
(4 figures); `backend/app/module_b/core/evaluation/replay_squat_session.py` +
`ml/scripts/generate_squat_replay_corpus.py` → 7-sample corpus committed to
`backend/app/module_b/replay_corpus/squat/`; `backend/tests/test_module_b_replay.py`
(9 tests, incl. `SquatDeterminismTests`).

- [x] `evaluate_squat.py` → `ml/reports/SQUAT_EVALUATION_REPORT.md`:
  - [x] Accuracy, **Precision (emphasised)**, Recall, **Macro-F1**, per-class + macro.
        **Accuracy is reported twice under two named definitions, and neither is
        presented as the headline** — on a 3-band output over binary ground truth it is
        genuinely ambiguous. `accuracy_strict = 0.531` counts Fair as wrong (punishes
        the abstention Stage 5.6 bought on purpose); `accuracy_confident = 1.000`
        excludes Fair (a system abstaining on 97/98 reps and getting the last right
        would also score 1.000). The pair is the honest summary: **the system commits
        on 52/98 reps (53.1%) and is right 100% of the time when it does.** Macro-F1
        0.481, macro precision 1.000, macro recall 0.386.
  - [x] **Confusion matrix** over the final fused 3-band output. Good→Good 50, Good→Fair
        22, Good→Poor 0; Poor→Good 0, Poor→Fair 24, Poor→Poor 2. **Both severe cells are
        0 — but this is consistent with Stage 5.6, not independent evidence for it**
        (same out-of-fold predictions selected the operating point). Reported because
        its absence would signal a bug.
    - [x] **Figure:** `figures/confusion_matrix_3band.png` — 2×3, deliberately
          non-square: ground truth has no Fair class, so that column is an abstention,
          not a class that can be right or wrong. Stated on the figure itself.
  - [x] **`error_tags` multi-label F1 NOT computed — two independent reasons, the second
        found by reading the code and not in this checklist.** (1) REHAB24-6 is binary,
        no per-fault ground truth. (2) **`router.py` never calls `exercise.error_tags()`
        at all**: `SquatExercise.error_tags()` raises `NotImplementedError`, and only
        the system flags (`low_confidence`/`low_capture_quality`/
        `retry_camera_placement`) from `_system_error_tags()` are persisted, movement
        taxonomy deferred to Stage 6. **Neither a prediction nor a reference exists.**
    - [x] **Figure deliberately NOT produced:** `figures/error_tag_performance.png` —
          per this checklist's own instruction not to fabricate bars for tags with no
          ground truth. EC3D (5.9) is the only honest source.
  - [x] **Robustness signals — the headline finding of this stage.**
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
    - [x] **Figure:** `figures/robustness_signals.png` — histogram (not a mean) + flag
          rates. The saturation spike at 100% is the point.
  - [x] **Inference latency measured:** median **8.11 ms**, p95 **9.10 ms** vs a 33.3 ms
        single-frame budget at 30 FPS (~3.7× headroom). Median of 5 timed repeats per
        rep. **Scope stated: excludes pose estimation and preprocessing** (per-frame
        browser costs); this is the per-rep cost the backend adds at the end of a set.
        Supports "the analysis layer is not the bottleneck", **not** "the whole system
        runs in real time".
        **⚠ X8 carve-out, stated in the report rather than left to be discovered:
        latency is the ONE Phase 5 output that is not byte-reproducible.** Wall-clock
        cannot be. Verified: every other metric and all 3 other figures are byte-
        identical across runs; only this section varies.
    - [x] **Figure:** `figures/inference_latency_distribution.png` — x-axis scaled to the
          data. The 33.3 ms budget is annotated, **not drawn as a line**: drawing it set
          the x-limit ~4× wider than the data and crushed the whole distribution into one
          invisible spike — the reference line destroyed the plot it was meant to
          contextualise.
  - [x] **Baseline comparison: `0.7347` (subject-wise) vs [S13] ~0.93 (non-subject-wise).**
        The comparable quantity is the **binary classifier's** accuracy, not the fused
        3-band system's — a published classifier cannot abstain.
        **⚠ Our accuracy exactly equals the Good base rate (72/98 = 0.7347). This is a
        coincidence, NOT a degenerate always-predict-Good classifier, and the report
        proves the difference:** the model predicts Poor for 20/98 reps and is right
        about 10 — it buys 10 correct Poor calls at the price of 10 Good reps it now gets
        wrong, netting +0. It breaks even. The model has learned something (AUC 0.832);
        accuracy is simply the wrong summary for an imbalanced problem.
    - [x] **Figure:** `figures/baseline_comparison_bar.png` — the "NOT AN APPLES-TO-APPLES
          COMPARISON" caveat is drawn **inside the axes** so a screenshot carries it.
- [x] **Q4 remains OPEN — the REHAB24-6 authors' own baseline is deliberately NOT quoted.**
      The checklist says to extract their protocol from the SISAP 2024 paper [S12] first.
      Attempted: the Springer chapter is paywalled (auth redirect, not followed), the
      Zenodo record carries no baseline results, and no open-access version was found.
      Per Q4's own instruction ("do not silently resolve them by assumption") **no number
      was invented for it** — the comparison rests solely on [S13], which `task.md`
      itself supplies. Extend §6 of the report if the paper becomes available.
- [x] **Deterministic replay harness** (Module A Stage 7 parity):
  - [x] `backend/app/module_b/core/evaluation/replay_squat_session.py` — `--json-file`
        (full replay: quality→preprocess→segment→features→rules→fuse, asserts two fresh
        runs identical), `--session-id` (partial), `--corpus` (replays all 7 samples and
        checks them against `labels.json`).
  - [x] `ml/scripts/generate_squat_replay_corpus.py` → 7 committed samples: 2 Good, 2
        Fair, 2 Poor, 1 low-Q reject. Fixed seed (20260716), byte-identical on
        regeneration. 3.6 MB, in line with Module A's SLS corpus (3.4 MB).
        **The manifest records the MEASURED band, not a hand-written expectation** —
        every sample is run through the real pipeline at build time. This caught two real
        bugs immediately: both Poor specs landed in Fair, and reps were being silently
        dropped (1 and 2 segmented instead of 3 and 4).
  - [x] Backend `SquatDeterminismTests` (+ corpus/harness tests): 9 tests. Suite
        **146/146** (was 137).
  - [x] **The WBLT caveat applies, and is strictly stronger for Module B: there is no
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

**Findings for later stages (recorded, not acted on):**

- **Under `StubModel`, `score == rule_score` exactly** (P(Good)=rule/10 ⇒ ml_score=rule,
  weights sum to 1). With `confidence_low_threshold=0.85` the only reachable bands are
  Poor (`rule<1.5`), Fair (`1.5≤rule≤8.5`, always via `low_confidence`) and Good
  (`rule>8.5`) — **the Fair _score band_ (4.0–7.0) is currently unreachable**; every Fair
  is an abstention. **Stage 5.8 replaces `StubModel` and these bands move — regenerate
  the corpus then, do not hand-patch `labels.json`.**
- **One Euro's speed-adaptive cutoff couples whole-body translation to angle smoothing.**
  Measured while building the corpus: raw peak knee flexion is identical (36.19°) at sway
  0.0 and 0.4, but the _preprocessed_ peak moves 35.44°→36.44° — enough to change how many
  reps segment. Larger sway ⇒ higher velocity ⇒ wider cutoff ⇒ _less_ smoothing. Sway and
  depth are not independent downstream, only in the raw pose.
- **`_release_persistent_occlusions` preserves coordinates for a wholly-occluded landmark**
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
- [x] `model_version = squat-1.0.0+rehab246-loso-3c441ac.dirty` — a real
      `git rev-parse --short HEAD`, `.dirty`-suffixed (uncommitted changes present at
      export time) rather than falsely implying an exact committed snapshot.
- [x] `core/model_registry.py`: `StubModel` **deleted**, not left behind.
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
- [x] Schema guard fires on mismatch (Stage 4.5): re-verified against the **real**
      bundle (`test_module_b_fusion.py::RealSquatModelBundleTests`), not only the fake
      classifier the Stage 4.5 tests originally used.
- [x] **Verified live end-to-end**, against the real `fyp_postgres` docker container
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

- [ ] **Confirm EC3D's 25-joint index order from the repo's data-loader before trusting any mapping.** This is a known open question (see Q3) and the "knee-passes-toe" lunge feature depends on it. Empirical fallback: plot one frame's 25 points and label limbs. Write `ml/docs/ec3d_joint_mapping.md`.
- [ ] `validate_ec3d.py` — map EC3D 25 → MediaPipe-33 for hip/knee/ankle/shoulder, recompute the **angle-based features only**, score with the trained model, report metrics.
  - [ ] **Figure (required):** `figures/ec3d_confusion_matrix.png` — same style as `confusion_matrix_3band.png` in Stage 5.7, so the two are visually comparable side by side in the write-up.
  - [ ] Output `ml/reports/EC3D_VALIDATION_REPORT.md` with the figure embedded and the 4-subject caveat stated directly beneath it, not just in surrounding prose.
- [ ] **Honest scoping:** EC3D has **4 subjects** — this is an external _check_, never a headline generalisation claim. Say so in the report.
- [ ] **Do not evaluate frontal-plane features here.** EC3D has true 3D, so a valgus feature would score well — and would be meaningless, because that feature doesn't exist in your monocular runtime. (Moot given the side-only decision, but state it: it's the reason the decision is right, and it belongs in the write-up.)

### Stage 5.10 — Option B: documented, not built _(for Chapter 3)_

- [ ] `docs/module_b_option_b_alternative.md` — the methodology alternative, written to be examiner-facing:
  - The mapping: Correct → Good; minor fault (Not-low-enough) → Fair; severe fault (Knees-inward / Front-bent) → Poor; then reconcile REHAB24-6 `incorrect` by the physio-noted mistake.
  - **Why it was not built — three real costs:** (1) two datasets speak different label languages and merging needs a translation _we_ author; (2) ranking a fault "minor" vs "severe" needs a physiotherapy severity source — **without one, it's opinion dressed as ground truth**, which is exactly the invented-cutoff trap this project has already been caught by once; (3) it **breaks the validation firewall** — once EC3D defines the bands it can't also be the independent test set, forcing Mendeley (26 subjects, unverified labels, no rep segmentation) in as the held-out check.
  - What would reverse the decision: a citable fault-severity source **and** an examiner requiring a genuinely learned third class.
- [ ] **Do not write Option B code.** Not even a stub.

**Deliverable:** Trained Extra Trees model for squat, calibrated and LOSO-evaluated, backend can load and use it.

---

### Phase 5B: Lunge **[GATE — do not start until Phase 5 Stage 5.8 is verified live]**

> **Frontend placeholder already exists (Stage 4.7, 2026-07-16, HY decision).** Ahead of this phase, `backend/app/seed.py` already seeds a `lunge` exercise catalog row (`mode: "rehab"`), and the frontend already shows its real thumbnail (`ExerciseSelection.tsx`) and tutorial video (`CameraSetup.tsx`, `assets/videos/Leg Lunge.mp4`). **Nothing else exists yet** — no `backend/app/module_b/lunge/` plugin, no `LungeExercise` registration, no `/lunge/live` page, no `POST`/analyze wiring. `CameraSetup.tsx`'s Start Session button is intentionally replaced with a "coming soon" message (`isLungePlaceholder`) and auto-start is disabled for this code, so no one can reach a broken session. When this phase builds the real plugin + live page, remove that gate and wire `beginSession`'s navigation the same way squat's `isSquat` branch does.

Repeat Phase 4 Stages 4.1–4.8 and Phase 5 Stages 5.0–5.9 for lunge, as `backend/app/module_b/lunge/` + a `LungeExercise` registered in the registry. **Only the deltas:**

- [ ] **ROM band edges are dataset-derived, not clinical.** The front-knee ≈90° cue is a **coaching convention, not a normative table** — no McBride-equivalent exists for the bodyweight lunge (open question, see Q6). So **calibrate the band edges from REHAB24-6's correct-rep distribution** and tag them **[dataset-derived]**. Do **not** assert 90° as a sourced cutoff.
- [ ] **Symmetry is cross-rep, not within-rep** (R5.2): the two legs do different jobs in one rep, so within-rep L-vs-R is meaningless. Compare **front-knee peak flexion + ROM when leading left vs leading right**, across reps.
- [ ] **Lead-leg tag:** at runtime, infer from which foot is forward in world landmarks. For training, **use `exercise_subtype` from `Segmentation.csv`** — it's given.
- [ ] **Generalisation must be stated modestly.** REHAB24-6 is the **only public labelled lunge dataset**; there is no second source. Claims lean on subject-wise CV + EC3D (4 subjects) and must be worded accordingly.
- [ ] `**knee_passes_toe**` needs a toe/foot-tip joint. If EC3D lacks one (Stage 5.9's open question), approximate from ankle **or drop it** — and say which.
- [ ] **Registry check:** adding lunge must require **zero** changes to `core/router.py`. If it doesn't, the Stage 4.1 abstraction was wrong — fix the abstraction, don't special-case.

**Deliverable:** Module B works end-to-end for lunge with a trained, LOSO-evaluated model, using the same registry with zero router changes.

---

## Phase 6: After-Set Report and External LLM API

**Goal:** readable after-set coaching text that **never** changes the grade, and a system that works perfectly when the API is down.

**Build order is deliberate: the fallback is built _first_.** If the template layer is built last it will be an afterthought; if it's built first, the LLM is provably optional polish.

### Stage 6.1 — Structured feedback + error-tag taxonomy

- [ ] `backend/app/module_b/squat/tags.py` — the R10 taxonomy, **valgus removed** (side-only):

| Tag                  | Observable from                  | User-facing message                                                 | Severity | Signal    |
| -------------------- | -------------------------------- | ------------------------------------------------------------------- | -------- | --------- |
| `insufficient_depth` | `knee_flex_peak_deg` < band [S1] | "Try to squat a little deeper — aim for thighs closer to parallel." | Medium   | rule + ML |
| `forward_trunk_lean` | `trunk_lean_peak_deg` [S4][S8]   | "Keep your chest up as you lower."                                  | Medium   | rule + ML |
| `feet_too_wide`      | `stance_width_norm`              | "Bring your feet a bit closer, about shoulder-width."               | Low      | rule + ML |
| `heel_lift`          | `ankle_df_proxy_deg`             | "Keep your heels flat on the floor."                                | Medium   | rule-only |
| `asymmetry`          | `symmetry_index_pct`             | "Try to lower evenly on both sides."                                | Medium   | rule-only |
| `inconsistent_tempo` | tempo CV                         | "Aim for a steadier pace across your reps."                         | Low      | rule-only |
| `low_confidence`     | calibrated `max(P)` / `Q`        | "Result is uncertain — try improving your camera placement."        | —        | system    |

- [ ] `**knee_valgus` is NOT in this table.** Record the omission + reason in `docs/module_b_limitations.md`: it is a frontal-plane fault, ill-posed from a single monocular side view. This mirrors the WBLT precedent of refusing to measure what one camera cannot (see [Deliberately Not Built](#deliberately-not-built-phases-47)).
- [ ] `core/feedback.py` — `build_structured_feedback(session) -> StructuredFeedback`: band, S_final, three sub-scores, confidence, ranked tags (severity → magnitude), rep count. **Pure and deterministic** (X8).

### Stage 6.2 — Template fallback _(built first, on purpose)_

- [ ] `core/feedback_templates.py` — deterministic composition from the R10 messages: `"Grade: {band}. {top_tag_message}. {second_tag_message}"`. Messages come **straight from the table above**, so the fallback can never invent a medical claim and can never change the grade. i18n-aware (en/zh/ms).
- [ ] **Gate:** the entire Phase 6 report renders correctly with the LLM **disabled by config**. Prove it before writing a single line of API client code.

### Stage 6.3 — Safety filter

- [ ] `core/feedback_safety.py`, applied to LLM output **before** it is stored or shown:
  - [ ] Reject/strip any diagnostic or clinical claim. Reuse the forbidden-phrase list from `test_frontend_disclaimers.py` — **one list, shared** (don't fork it).
  - [ ] **Grade-integrity check:** the band/score in the rewritten text must match the structured input. Mismatch → discard the LLM output, fall back to the template. (X5)
  - [ ] Reject output that introduces a tag not in the structured input.
  - [ ] Length cap.
- [ ] **Tests:** an adversarial LLM response that changes the grade → rejected, template used.

### Stage 6.4 — Groq adapter

- [ ] `core/llm_client.py` — provider-agnostic interface; `GroqClient` (OpenAI-compatible API), model `llama-3.3-70b`. Key from env (`.env.example` updated), **never** committed.
- [ ] System prompt: _rewrite only; add no medical claims; do not change the grade or the tags_. The prompt carries **metrics + tags only** — never raw video, never health records (the app persists only metrics anyway).
- [ ] **After-set only.** Never in the live loop. A test asserts the live path makes no LLM call.
- [ ] Timeout + retry-once + **fall back to template on any error/timeout/429**.
- [ ] **Re-verify Groq's free-tier limits and model name at build time.** Free tiers drift monthly (a documented May–June 2026 model-list purge is precedent). Record the retrieval date in `docs/`. The template fallback means a silent model deletion can't break the app — but a stale model name in config will still throw, so pin and check. (See Q7.)
- [ ] **Deployment note for Phase 8:** Cloud Run → Groq is an outbound call. Decide then whether the deployed demo defaults to Groq or template-only. Flag it; don't decide it here. (See Q8.)

### Stage 6.5 — Persist + display

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)): keep `feedback_source: "llm" | "template"` + provider/`model_version`, **and add `llm_attempted: bool`** so the three-state distinction survives — `source="template"` + `attempted=true` means "tried the LLM, output was rejected by the safety filter (Stage 6.3), fell back"; `attempted=false` means "never called (config-disabled, or after-set-only gate not yet reached)." This is strictly more informative than the architecture doc's `llm_used BOOLEAN`, which collapses those two cases. Drop `safety_disclaimer` as stored free text — the disclaimer the user sees always comes from the current i18n render (rules.md #19), so storing a duplicate copy of it per row is redundant. Store `**disclaimer_version**` instead (not the string): a small versioned id bumped whenever the disclaimer copy changes, giving audit-grade traceability ("this session was shown disclaimer v2") without duplicating text that already lives in i18n.

- [ ] Store **both** the structured feedback and the rewritten text, plus `feedback_source: "llm" | "template"`, `llm_attempted: bool`, `provider`, `model_version`, and `disclaimer_version`.
- [ ] `Report.tsx` renders the coaching text with the sub-score breakdown and tags. Surface `feedback_source` honestly (an examiner will ask which one produced it).
- [ ] **Test:** grade before rewrite == grade after rewrite, byte-identical (X5). Add a case asserting `feedback_source="template"` + `llm_attempted=true` when a safety-filter rejection occurs (Stage 6.3), distinct from `llm_attempted=false` when the LLM was never called.

**Deliverable:** User receives readable after-set report; system still works even if LLM API fails.

---

## Phase 7: Dashboard and Progress Tracking

**Goal:** kill `dash.placeholderScoring` for **every** exercise and make multi-session progress real.

**Context:** this is pre-existing cross-cutting tech debt, flagged three separate times in this document (SLS Stage 6, WBLT Stage 6, Phase 3 checklist) and deliberately deferred each time because a one-off per-exercise chart would have been inconsistent. Phase 7 is its home. It is **one charting API either way** — doing Module B only would repeat the same mistake.

### Stage 7.0 — Trend API

> ✅ **Resolved 2026-07-16** (see [Contradictions found — need HY decision](#contradictions-found-need-hy-decision)): follow the architecture doc's §14.8 endpoint names — `GET /api/dashboard/trends` (plural) and `GET /api/dashboard/error-tags` as two separate endpoints, not the single parameterised `trend` endpoint originally drafted here. **Both must return their data keyed by `exercise_type`** (e.g. `{"sts": {...}, "sls": {...}, "wblt": {...}, "squat": {...}, "lunge": {...}}`), not require a separate call per exercise — this is what actually satisfies the Locked Assumption that "Phase 7 fixes the trend/band panels for all exercises" in one dashboard load, and lets the frontend render every panel from one response instead of fan-out fetching.

- [ ] `backend/app/dashboard/router.py` — `GET /api/dashboard/summary` + `GET /api/dashboard/trends?from=&to=` (data keyed by `exercise_type`) + `GET /api/dashboard/error-tags?from=&to=` (data keyed by `exercise_type`, only present for Module B exercise types — Module A has warning tags, not error tags, per Stage 7.1's distinction).
- [ ] Built on the **exercise-agnostic** `sessions.score` / `sessions.band` columns wherever possible (`Dashboard.tsx` and `SessionHistory.tsx` already read only these — confirmed in Phase 3E). Exercise-specific detail comes from the per-exercise endpoints.
- [ ] **Apply the MDC-suppression principle beyond WBLT.** WBLT already suppresses changes below the published MDC (Powden et al. 2015) so measurement noise never reads as improvement. For exercises **without** a published MDC, do **not** invent one — instead present the trend without a "meaningful change" claim, or derive a pilot repeatability estimate from the replay corpus and label it **[dataset-derived]**. **Never assert a clinical MDC that doesn't exist.**

### Stage 7.1 — Dashboard panels

- [ ] **Recent sessions** — already partly present; wire to the real API.
- [ ] **Score trend chart** — per exercise, over time. Removes `dash.placeholderScoring`.
- [ ] **Band distribution** — Good/Fair/Poor counts.
- [ ] **Common error tags** — Module B only (Module A has warning tags, not error tags — don't conflate the two vocabularies in one panel).
- [ ] **Capture-quality trend** — `Q` over sessions. Directly feeds the evaluation question: _do users improve camera placement after being prompted?_
- [ ] **Confidence trend** — Module B only; feeds the low-confidence-frame robustness metric.
- [ ] Delete the `dash.placeholderScoring` i18n key (en/zh/ms) once nothing references it. **Grep for callers before deleting** — the house rule.

### Stage 7.2 — Per-session trend rows for STS and SLS

- [ ] WBLT has a real per-session "vs last session" row on `Report.tsx` (Phase 3E Stage 6). STS and SLS do not. Add the equivalent, reusing `compute_trend`'s shape.
- [ ] For STS/SLS, the MDC caveat from 7.0 applies: **no invented "meaningful change" threshold.**

### Stage 7.3 — Reminders

- [ ] Reminders exist as a Phase 1A mock page. Wire to a real backend table + CRUD.
- [ ] Keep it simple — this is the lowest-value item in Phase 7. Do not build scheduling infrastructure.

### Stage 7.4 — Verification

- [ ] Backend suite green; `tsc --noEmit` + build clean.
- [ ] **Verified live end-to-end** with a multi-session account across ≥2 exercise types.
- [ ] Update this document's Phase 3 line (`[~] Show dashboard trend`) to `[x]` — this phase is what closes it.

**Deliverable:** User can track progress over time across all exercises, with no placeholder scoring left in the Dashboard.

---

## Open Questions (Phases 4–7)

Track these; do not silently resolve them by assumption.

| #   | Question                                                                                                                                                                                                                                                                                          | Blocks                                                  | Settles via                                                                                           |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Q1  | **Usable side-view Ex6 rep count** after the orientation filter                                                                                                                                                                                                                                   | Phase 5 Stage 5.0 gate                                  | `Segmentation.csv` + `Segmentation.txt` + one visual check per orientation value                      |
| Q2  | Which camera is profile for each `cam17_orientation` value                                                                                                                                                                                                                                        | Phase 5 Stage 5.2                                       | Same as Q1 — **verify, don't assume** the working hypothesis                                          |
| Q3  | EC3D's exact 25-joint index order                                                                                                                                                                                                                                                                 | Phase 5 Stage 5.9; `knee_passes_toe`                    | EC3D repo data-loader, or an empirical frame plot                                                     |
| Q4  | REHAB24-6 authors' own baseline **+ split protocol** — **STILL OPEN, attempted 2026-07-16:** SISAP 2024 chapter is paywalled (Springer auth redirect), Zenodo record has no baseline results, no open-access version found. **No number invented**; Stage 5.7's §6 quotes only [S13] and says so. | Phase 5 Stage 5.7's comparison (**shipped without it**) | SISAP 2024 paper [S12] — a random-split number is not comparable to LOSO. Needs institutional access. |
| Q5  | No validated sway/jitter threshold exists for the Control sub-score                                                                                                                                                                                                                               | Phase 4 Stage 4.4 (heuristic, pilot-tune)               | A postural-sway study with a quantitative in-plane cutoff (_not found_)                               |
| Q6  | No normative lunge front-knee angle table exists                                                                                                                                                                                                                                                  | Phase 5B ROM bands                                      | A published bodyweight-lunge kinematics norm (_not found_) — until then, dataset-derived only         |
| Q7  | Groq free-tier limits + model name at build time                                                                                                                                                                                                                                                  | Phase 6 Stage 6.4                                       | Live provider docs; record retrieval date                                                             |
| Q8  | Cloud Run → Groq egress in the deployed demo                                                                                                                                                                                                                                                      | Phase 8                                                 | HY decision at Phase 8                                                                                |

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

- **✅ Resolved:** follow the architecture doc — `GET /api/dashboard/trends` + `GET /api/dashboard/error-tags` as two endpoints. Both return their payload **keyed by `exercise_type`** in one response (not one call per exercise), so a single dashboard load covers every exercise type per the Locked Assumption that Phase 7 fixes trend/band panels for all of them. See Stage 7.0.

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
