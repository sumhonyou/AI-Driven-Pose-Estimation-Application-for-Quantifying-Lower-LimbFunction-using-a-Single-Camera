# Phase 7 — Dashboard & Progress Tracking: Implementation Plan

---

## Table of Contents

- [Context](#context)
  - [Decisions locked with HY (2026-07-19)](#decisions-locked-with-hy-2026-07-19)
  - [Design constraints (from task.md + rules.md)](#design-constraints-from-taskmd-rulesmd)
- [Stage 7.0 — Trend & error-tag APIs (START HERE)](#stage-70-trend-error-tag-apis-start-here)
  - [New/changed schemas (schemas.py, replacing flat DashboardTrendPoint/DashboardErrorTag)](#newchanged-schemas-schemaspy-replacing-flat-dashboardtrendpointdashboarderrortag)
  - [Endpoints](#endpoints)
  - [Tests (test_dashboard.py, mirror tests/test_module_b_persistence.py style)](#tests-testdashboardpy-mirror-teststestmodulebpersistencepy-style)
- [Stage 7.1 — Dashboard overview panels (Recharts)](#stage-71-dashboard-overview-panels-recharts)
- [Stage 7.1b — Progress deep-dive page (new)](#stage-71b-progress-deep-dive-page-new)
- [Stage 7.2 — STS & SLS "vs last session" rows](#stage-72-sts-sls-vs-last-session-rows)
- [Stage 7.3 — Reminders — DEFERRED (not this pass)](#stage-73-reminders-deferred-not-this-pass)
- [Stage 7.4 — Seed data + end-to-end verification](#stage-74-seed-data-end-to-end-verification)
- [Open confirmations](#open-confirmations)
- [Execution order](#execution-order)

---

## Context

Phase 7 is the home for cross-cutting dashboard/progress tech-debt deferred three
times (SLS Stage 6, WBLT Stage 6, Phase 3 checklist). Today the dashboard shows
hardcoded `—` placeholders and a flat fake SVG line (`dash.placeholderScoring`
everywhere), the `/api/dashboard/trends` and `/error-tags` endpoints are hard `[]`
stubs, and the "Progress" nav link is a dead placeholder pointing at `/dashboard`
(no `/progress` route exists). Goal: kill `dash.placeholderScoring` for **every**
exercise, make multi-session progress real, and give the Progress tab a genuine job —
all keyed by `exercise_type` so one dashboard load covers every exercise (Module A:
STS/SLS/WBLT, Module B: squat).

### Decisions locked with HY (2026-07-19)

- **Progress tab** → dedicated deep-dive page (new `/progress` route). Dashboard stays the overview.
- **Charts** → **Recharts** library, wrapped in thin themed components using existing `--lime`/`--emerald`/`--good`/`--fair`/`--poor` tokens (light + dark).
- **This pass scope** → Stages 7.0–7.2 + 7.4. **Reminders (7.3) deferred.**
- **Test data** → seed synthetic multi-session, multi-exercise demo account for live verification.

### Design constraints (from task.md + rules.md)

- Endpoints return data **keyed by `exercise_type`** in one response (task.md:3161, 3250) — not one call per exercise.
- **Capability differs by module:** Module A has _warning_ tags + no confidence; Module B (squat) has _error_ tags + `confidence`. Do NOT conflate the two vocabularies. Panels render conditionally per exercise type.
- **MDC discipline** (task.md:3165): WBLT keeps published-MDC suppression; for exercises with no published MDC, show the trend but assert **no "meaningful change"** — never invent a clinical threshold.
- Rules: keep UI simple/non-technical, no medical claims, safety disclaimer stays, Prettier (FE) + Black/isort (BE), minimal comments, console logs on key processes only.

---

## Stage 7.0 — Trend & error-tag APIs (START HERE)

**Files:** `backend/app/api/dashboard_routes.py`, `backend/app/db/schemas.py`, new `backend/tests/test_dashboard.py`.

Current stubs at `dashboard_routes.py:53-60` return `[]`. Replace with real, `exercise_type`-keyed queries built on the exercise-agnostic `sessions.score`/`band`/`capture_quality` columns (+ `module_b_results.confidence` joined for Module B only).

### New/changed schemas (`schemas.py`, replacing flat `DashboardTrendPoint`/`DashboardErrorTag`)

```python
class TrendPoint(BaseModel):
    session_id: str
    date: datetime            # sessions.started_at
    score: float | None
    band: str | None
    capture_quality: float | None
    confidence: float | None = None   # Module B only

class ExerciseTrend(BaseModel):
    points: list[TrendPoint]
    mdc: float | None = None
    mdc_source: Literal["published", "none"] = "none"

# /trends  -> dict[str, ExerciseTrend]        keyed by exercise_type
# /error-tags -> dict[str, list[DashboardErrorTag]]   Module B keys only
```

Extend `DashboardSummary` with `latest: dict[str, {score, band, capture_quality}]` (per-exercise latest) — keep existing top-level fields for back-compat with the current Dashboard tiles.

### Endpoints

- `GET /api/dashboard/trends?from=&to=` — group user's sessions by `exercise_type`, ordered by `started_at`; only include exercise types the user actually has. `confidence` via `selectinload`/join on `module_b_result` for Module B rows. `mdc`/`mdc_source` = `published` only for `weight_bearing_lunge_test` (reuse WBLT's published MDC constant), else `none`.
- `GET /api/dashboard/error-tags?from=&to=` — `GROUP BY tag_code` over `module_b_error_tags` joined to the user's sessions, keyed by exercise_type; Module B keys only (Module A absent, not empty-listed, so the FE can distinguish "no error-tag concept" from "zero tags").
- `GET /api/dashboard/summary` — add the per-exercise `latest` map.
- Optional `from`/`to` ISO dates; default = all history.

### Tests (`test_dashboard.py`, mirror `tests/test_module_b_persistence.py` style)

Empty account → `{}`; single Module A exercise → trend present, error-tags key absent; Module B → confidence populated + error-tags grouped/counted correctly; multi-exercise → both keys present; `from`/`to` filtering; WBLT `mdc_source == "published"`, others `"none"`.

**Verify 7.0:** `pytest backend/tests/test_dashboard.py` green; Swagger shows new response shapes; hit endpoints with the seeded account (built in 7.4) and eyeball JSON keyed by exercise_type.

---

## Stage 7.1 — Dashboard overview panels (Recharts)

**Files:** `frontend/src/pages/Dashboard.tsx`, new `frontend/src/components/charts/*`, `frontend/src/services/dashboardService.ts`, `frontend/src/types/api.ts`, i18n `en/zh/ms`.

- `npm i recharts`. Build thin themed wrappers reading CSS vars via `getComputedStyle`/inline tokens:
  - `ScoreTrendChart` — `AreaChart`+line, Y 0–10, faint Good/Fair/Poor `ReferenceArea` background zones, dot per session.
  - `BandDistributionBar` — 100% stacked segmented bar (good/fair/poor).
  - `MiniTrendCard` — small-multiple sparkline card (one per exercise on the overview).
  - `QualitySparkline` — thin line 0–100%.
- Update `dashboardService.trends()`/`errorTags()` return types to the new keyed shapes; update `types/api.ts`.
- Replace hardcoded SVG + `—` tiles in `Dashboard.tsx:110-249` with: real latest tiles + **small-multiples grid** (one `MiniTrendCard` per exercise the user has done). Recent-sessions table (`:251-311`) already real — keep.
- **Delete `dash.placeholderScoring`** (en/zh/ms) — grep all callers first (score-trend, band-dist, confidence, error-tags panels), convert all four, then remove the key last.

**Verify:** `tsc --noEmit` + `vite build` clean; live screenshot of overview with seeded data.

---

## Stage 7.1b — Progress deep-dive page (new)

**Files:** new `frontend/src/pages/Progress.tsx`, route in `frontend/src/App.tsx`, fix `frontend/src/layouts/DashboardLayout.tsx:80` (`to="/dashboard"` → `to="/progress"`, restore active styling).

- Exercise **segmented selector** + 14d/30d/All range control (drives `from`/`to`).
- Per selected exercise: large `ScoreTrendChart` (band zones), `BandDistributionBar`, `QualitySparkline`; **Module B only:** confidence-trend line + ranked error-tag horizontal bar (severity-colored).
- Renders entirely from the single keyed `/trends` + `/error-tags` responses — no per-exercise fan-out.
- Empty state when the account has no sessions.

**Verify:** live screenshots of Progress for one Module A (e.g. STS) and one Module B (squat) exercise.

---

## Stage 7.2 — STS & SLS "vs last session" rows

**Files:** `backend/app/module_a/sts/*`, `backend/app/module_a/sls/*`, `frontend/src/pages/Report.tsx`, i18n.

- Reuse the shape of `backend/app/module_a/wblt/analysis.py:483 compute_trend(current, previous)` for STS and SLS; expose in their result/summary payload; render a "vs last" row on `Report.tsx` (mirror the WBLT trend row at `Report.tsx:24-54,144`).
- **No invented MDC** for STS/SLS — show the delta, assert no meaningful-change claim.

**Verify:** unit tests for the new trend fns; live: run 2 STS sessions, confirm the vs-last row appears on the 2nd report.

---

## Stage 7.3 — Reminders — DEFERRED (not this pass)

---

## Stage 7.4 — Seed data + end-to-end verification

**Files:** new `backend/app/seed_demo_progress.py` (idempotent, clearly-named `demo-progress@physiofit.local` account, removable), task.md update.

- Seed ~8–12 sessions across dates for ≥2 exercise types (e.g. STS + squat) with varied score/band/capture_quality; squat sessions get `module_b_results.confidence` + `module_b_error_tags`. Idempotent (safe re-run), and a `--purge` path so it never pollutes real data.
- Full checks: `pytest` backend green; `tsc --noEmit` + `vite build` clean; Prettier + Black/isort.
- **Live end-to-end:** start backend + FE, log into seeded account, screenshot Dashboard small-multiples + Progress page (Module A and Module B) as proof.
- task.md: flip Phase 3 `[~] Show dashboard trend` → `[x]`; add dated Stage 7.0–7.2/7.4 entries in the required format.

---

## Open confirmations

1. **Seed data writes to the dev Postgres the backend points at.** Mitigated: distinct `demo-progress@…` account, idempotent, `--purge`. Flag if you want a throwaway DB instead.
2. `dash.placeholderScoring` deleted only after all four panels convert (last step of 7.1), never piecemeal.

## Execution order

7.0 (backend + tests) → 7.4 seed script (to get data) → 7.1 (Dashboard) → 7.1b (Progress) → 7.2 (STS/SLS rows) → 7.4 live verify + task.md/docs update.
