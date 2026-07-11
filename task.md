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
