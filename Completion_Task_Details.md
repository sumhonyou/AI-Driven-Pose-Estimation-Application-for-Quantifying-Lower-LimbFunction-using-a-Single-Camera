# Completion Task Details

**Project:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function  
**Session Date:** 2026-06-05  
**Status:** Phase 1A — UI Clickable Prototype COMPLETE  
**Completed By:** Claude Sonnet (AI coding agent)

---

## What Was Done

### Overview

This session delivered the **complete Phase 1A UI clickable prototype** for PhysioFit — an AI-powered lower-limb rehabilitation and functional checking web application. The work started from a bare-scaffold Vite + React + TypeScript + Tailwind frontend (Phase 0 already done), and produced a fully navigable, multi-language, accessible, responsive React prototype with all 11 required pages and a comprehensive design system.

Two artefacts were built:

1. **HTML mockup** (`mockups/physiofit-mockup.html`) — a self-contained standalone mockup used to lock the visual language (Landing + Dashboard) before the React build.
2. **React application** (`frontend/src/`) — the real production-ready prototype in the existing Vite + React + TS + Tailwind v4 project.

---

## Part 1 — HTML Mockup (Design Lock)

### File

- `mockups/physiofit-mockup.html`

### What it contains

- **Landing page** and **Dashboard page** side by side, switchable via a floating pill.
- **Dark/light toggle** (light default).
- Full brand design system rendered in vanilla CSS.
- Used as a visual approval step before porting to React.

### Design decisions made and agreed in this session

- **Theme:** Dark-first health-tech with a dark + light toggle. Light mode is the **default**.
- **Palette:**
  - Deep Dark Green `#051D0C` — primary dark surface
  - Neon Lime `#9BFF00` — primary accent (buttons, active states, chart line in dark)
  - Bright Emerald `#00AE54` — secondary accent (text links, icons, chart line in **light** mode)
  - Amber `#F5B731` — Fair band colour
  - Coral `#FF6B5E` — Poor band colour
- **Typography:** Inter font throughout (user-mandated for readability; overrides the frontend-design skill's guideline to avoid Inter).
- **Audience:** Balanced — older adults + athletes. Larger font sizes, strong contrast, generous touch targets, modern aesthetic.
- **Band colours:** Good = lime/emerald, Fair = amber, Poor = coral.
- **Chart line:** Emerald in light mode (lime has insufficient contrast on white), lime in dark mode.
- **Non-diagnostic disclaimer** mandatory on Landing, Dashboard, and Report pages (project rule).

### Key visual elements

- Subtle green grid background + radial glow atmosphere (body::before, body::after).
- Floating animated "device" card with a SVG pose skeleton and scan-line animation.
- Float cards (Knee ROM + Capture Quality) with `floaty` keyframe animation.
- Scroll-reveal stagger animations (IntersectionObserver).
- Hover lifts on cards/buttons, smooth transitions.
- Glass nav bar (backdrop-filter blur).

---

## Part 2 — React Application Build

### Location

All files under `frontend/src/` in the project root.

### Dependencies Added

```bash
npm install react-router-dom i18next react-i18next i18next-browser-languagedetector
```

(Added to `frontend/package.json`)

---

## Files Created / Modified

### New files created

#### `frontend/src/index.css`

Complete design system CSS. Key contents:

- CSS custom properties (variables) for both `html[data-theme="light"]` (default) and `html[data-theme="dark"]`.
- Font-size accessibility control via `html[data-fs]` attribute:
  - `data-fs="1"` → `font-size: 16px` (default A)
  - `data-fs="2"` → `font-size: 17.5px` (A+)
  - `data-fs="3"` → `font-size: 19px` (A++)
- All component styles: nav, hero, device/pose visuals, float cards, disclaimer, sections, modules, steps, CTA strip, footer, auth forms, dashboard shell, sidebar, metric cards, charts, band distribution, session table, error tags, reminders, flow pages (mode selection, exercise grid, camera, live session, report, history, reminders).
- Responsive breakpoints at 1050px (sidebar collapses to mobile drawer) and 760px (mobile — single column stacks, hamburger nav).
- `.reveal` scroll animation class (opacity 0 → 1, translateY 20px → 0).
- `@media (prefers-reduced-motion: reduce)` override.

#### `frontend/src/i18n/en.ts`

English source translation file (TypeScript). Contains ~200 translation keys in a nested object covering sections: `common`, `nav`, `landing`, `auth`, `dash`, `mode`, `exercise`, `camera`, `live`, `report`, `history`, `reminders`. Exports `Dict` type used by other language files.

**Duplicate key fix applied:** The `landing.ctaPrimary` / `landing.ctaSecondary` keys existed twice (hero + CTA strip). Renamed CTA strip versions to `ctaOpen` and `ctaExplore`.

#### `frontend/src/i18n/zh.ts`

Simplified Chinese (中文) full translation of all keys. Implements `Dict` type from `en.ts`.

#### `frontend/src/i18n/ms.ts`

Bahasa Malaysia full translation of all keys. Implements `Dict` type from `en.ts`.

#### `frontend/src/i18n/hi.ts`

Hindi (हिन्दी) full translation of all keys. Implements `Dict` type from `en.ts`.

#### `frontend/src/i18n/index.ts`

i18n configuration:

- Exports `LANGUAGES` array: `[{code:'en', label:'English', flag:'🇬🇧'}, {code:'zh', label:'中文', flag:'🇨🇳'}, {code:'ms', label:'Bahasa Malaysia', flag:'🇲🇾'}, {code:'hi', label:'हिन्दी', flag:'🇮🇳'}]`
- Initialises i18next with `LanguageDetector` (reads from localStorage key `physiofit-lang`, then browser `navigator`).
- Fallback language: `en`.

#### `frontend/src/preferences.tsx`

React context provider for persistent user preferences.

- **Theme:** `"light" | "dark"`, persisted to localStorage key `physiofit-theme`, default `"light"`.
- **FontScale:** `1 | 2 | 3`, persisted to localStorage key `physiofit-fontscale`, default `1`.
- On change: sets `data-theme` and `data-fs` attributes on `document.documentElement`.
- Exports: `PreferencesProvider`, `usePreferences()` hook.

#### `frontend/src/useReveal.ts`

Custom React hook. On mount (or when `deps` change), runs an `IntersectionObserver` over all `.reveal:not(.in)` elements in the DOM. When each element enters the viewport, adds `.in` class to trigger the CSS reveal animation. Stagger delay: `min(i * 45ms, 320ms)`. Returns void, disconnects observer on cleanup.

#### `frontend/src/components/Icons.tsx`

Inline SVG icon component library (no external icon package). All icons use `stroke="currentColor"` and accept `SVGProps<SVGSVGElement>`. Exports: `Check`, `ArrowRight`, `ArrowLeft`, `Sun`, `Moon`, `Globe`, `Play`, `Activity`, `Camera`, `User`, `ShieldCheck`, `Alert`, `Chart`, `Clock`, `Plus`, `Menu`, `Close`, `Bell`, `Grid`, `CirclePlus`, `History`, `Balance`, `Stretch`, `Target`, `Lightbulb`, `LogoMark`.

#### `frontend/src/components/Controls.tsx`

Shared UI controls used in both layouts:

- `Logo` — brand mark + wordmark link, accepts `to` prop.
- `ThemeToggle` — button that calls `usePreferences().toggleTheme()`. Shows sun/moon depending on current theme.
- `FontSizeControl` — segmented button group (A/A+/A++) that calls `setFontScale(1|2|3)`. The three buttons differ in rendered font-size to be self-illustrating.
- `LanguageSwitcher` — dropdown (`ctrl` button + `lang-menu`) that calls `i18n.changeLanguage(code)` for each of the 4 languages. Menu closes on outside click. Displays current language label on desktop.
- `Disclaimer` — styled alert banner with emerald left border.

#### `frontend/src/components/PoseFigure.tsx`

Reusable SVG pose skeleton component. Renders a stick figure with `bone` (stroke lines) and `joint` (circles) elements using CSS classes. Used on hero (Landing), Camera Setup, and Live Session pages. The lower-limb bones use the `.lime` class for accent colour.

#### `frontend/src/layouts/PublicLayout.tsx`

Layout wrapper for public pages (Landing, Login, Register). Contains:

- Sticky glass navbar with: `Logo`, nav links (Modules, How it works, For clinicians, About), `FontSizeControl` (desktop-only), `ThemeToggle`, `LanguageSwitcher`, Log in + Start a check buttons.
- Mobile hamburger menu that toggles a `MobileMenu` with the same links and controls.
- `<Outlet />` for page content.
- `Footer` component with brand, tagline, two-column links grid, and copyright.
- Calls `useReveal([pathname])` to re-trigger scroll animations on route change.

#### `frontend/src/layouts/DashboardLayout.tsx`

Layout wrapper for all dashboard/app pages. Contains:

- `<aside class="side">` — sticky sidebar (desktop), slide-in drawer (mobile/tablet). Contains: `Logo`, grouped nav links (`Grid/Dashboard`, `CirclePlus/New session`, `History/Session history`, `Chart/Progress`, `Bell/Reminders`, `User/Profile`), "Daily check due" side card with Start now button.
- Scrim `<div class="scrim">` — dark overlay when drawer is open on mobile; click closes drawer.
- `.dash-mobilebar` — mobile-only top bar with Logo + hamburger toggle (only visible at ≤1050px).
- `<main class="main"><Outlet /></main>` — page content area.
- `DashTopbar` exported component — reusable topbar with title, subtitle, `FontSizeControl`, `ThemeToggle`, `LanguageSwitcher`, and optional `actions` slot (used for "New session" button + avatar on Dashboard, "View history" + "New session" on Report, etc.).
- Calls `useReveal([pathname])`.

#### `frontend/src/pages/Landing.tsx`

Full landing page. Sections:

1. **Hero** — pill badge, h1 with highlighted `<span class="hl">`, lead paragraph, CTA buttons (Start a free check → `/mode`, See how it works → `#how`), 3 stats (3 functional checks, 33 landmarks, On-device).
2. **Hero visual** — `<div class="device">` with `PoseFigure`, scan-line animation, two float cards (Knee ROM · Good, Capture quality 92%).
3. **Disclaimer banner** (non-diagnostic).
4. **Modules section** (`#modules`) — Module A card (3 check-rows: Sit-to-Stand, Supported Single-Leg Stance, Weight-Bearing Lunge Test), Module B card (3 check-rows: ROM completeness, Tempo consistency, Stability control with AI badge).
5. **How it works section** (`#how`) — 4-step grid (Camera → Move → Report → Track).
6. **CTA strip** — heading, lead, two buttons (Open dashboard → `/dashboard`, Explore modules → `#modules`).
   All content uses `t()` calls from react-i18next. All major elements have `.reveal` class.

#### `frontend/src/pages/Login.tsx`

Login form page (UI only). Email + password fields, forgot password link, submit navigates to `/dashboard`. "Continue as guest" button also navigates to `/dashboard`. Link to `/register`. Uses `useNavigate()` from react-router-dom.

#### `frontend/src/pages/Register.tsx`

Registration form (UI only). Fields: Full name, email, password, age group (select), user type (select), gender (select, optional), focus area (select). Submit navigates to `/dashboard`. Non-diagnostic agreement disclaimer. Link to `/login`.

#### `frontend/src/pages/Dashboard.tsx`

Main app dashboard. Uses `DashTopbar` with "New session" button + avatar. Sections:

1. **4 Metric cards** — Average score (7.4/10, ▲6%), Latest band (Good), Sessions (18, ▲2), Capture quality (89%, ▼3%).
2. **Score trend panel** — SVG line chart with area gradient fill. `--chart-line` CSS variable ensures emerald in light, lime in dark. Segmented 14d/30d/All filter (UI only). `areaFill` SVG linearGradient.
3. **Band distribution panel** — Good 61%, Fair 28%, Poor 11% progress bars. Confidence sub-section.
4. **Recent sessions table** — 4 rows (Sit-to-Stand, Single-Leg Stance, Knee Rehab Set, Lunge Test) with exercise icon, mode tag, date, quality %, band pill, score. Scrollable on mobile (`tbl-scroll`).
5. **Common error tags** — 6 tags with severity dots (low/med/high) and counts.
6. **Reminders panel** — 3 reminders with toggle-able `done` state (local state, no backend). Renders `.is-done` strike-through on completion. "+" Add button links to `/reminders`.
7. **Non-diagnostic note** at the bottom.

#### `frontend/src/pages/ModeSelection.tsx`

Two large choice cards — Functional Checking and Rehab Grading. Each navigates to `/exercise?mode=functional` or `/exercise?mode=rehab`. Uses `DashTopbar`.

#### `frontend/src/pages/ExerciseSelection.tsx`

Reads `?mode=` from URL search params. Shows:

- **Functional** mode: 3 exercise cards (Sit-to-Stand, Supported Single-Leg Stance, Weight-Bearing Lunge Test) with view and rep chips.
- **Rehab** mode: 1 placeholder exercise card (Knee Rehab Exercise).
  All cards link to `/camera`. Back link to `/mode`.

#### `frontend/src/pages/CameraSetup.tsx`

Two-column layout (camera preview + checklist sidebar):

- **Left:** `.cam-stage` with `PoseFigure`, capture-quality badge (92%), dashed frame with lime corner indicators (CSS position tricks), scan-line animation placeholder.
- **Right:** "Before you start" checklist (4 items with emerald check icons), "View guidance" panel (side-view instruction for this exercise type), "Start session" button → `/live`.
  Back link to `/exercise`.

#### `frontend/src/pages/LiveSession.tsx`

Live session page with local state:

- Timer (`useEffect` interval, increments every second, displays `mm:ss`).
- Rep counter (randomly increments up to 5 with each tick, simulating detection).
- Left: `.cam-stage` with `PoseFigure` and quality badge.
- Right: Timer card + Reps card (HUD), Live band panel (shows "Good" with animated progress bar filling as reps increase), "End set" button → `/report`.
  "End set" button in topbar (red/coral style) also navigates to `/report`.

#### `frontend/src/pages/Report.tsx`

Post-session report. Uses `DashTopbar` with "View history" and "New session" buttons. Sections:

1. **Report hero panel** — SVG score dial (circle with strokeDasharray, score 7.0/10), Final band "Good" pill, confidence pill, ML prediction line.
2. **Rule-based sub-scores** — 3 sub-score cards (ROM 7.5, Tempo 6.8, Stability 7.1) each with label, number, and fill bar.
3. **Coaching feedback panel** — "AI" label tag, coaching text paragraph (uses i18n key `report.coachingBody`).
4. **Error tags panel** — 2 error tags (Limited range of motion, Unstable tempo) with severity dots.
5. **Non-diagnostic disclaimer note** at bottom.

#### `frontend/src/pages/SessionHistory.tsx`

Session history with filter state (`all | functional | rehab`). Filter pills at top. Full table of 6 mock sessions. "View" button on each row links to `/report`. Empty state message if no rows match filter. Horizontally scrollable table on mobile.

#### `frontend/src/pages/Reminders.tsx`

Reminders page. Local state array of 3 reminders with `done` toggle. Each rendered as `.rem-card` with a clickable checkbox button (`rem-check`, turns lime with check icon when done). Chips show frequency. Clock icon + time displayed. "Add reminder" button in `DashTopbar` actions (no-op in Phase 1A).

---

### Files Modified

#### `frontend/src/App.tsx`

**Completely replaced** the old Phase 0 backend health-check UI. New content:

- `ScrollToTop` component — scrolls to top on route change (preserves hash anchors).
- `BrowserRouter` wrapping `Routes`.
- Two route groups:
  - `PublicLayout` — index (`/`), `/login`, `/register`
  - `DashboardLayout` — `/dashboard`, `/mode`, `/exercise`, `/camera`, `/live`, `/report`, `/history`, `/reminders`
- `path="*"` catch-all → `Landing`.

#### `frontend/src/main.tsx`

Added:

- `import './i18n'` — initialises i18next before React renders.
- `<PreferencesProvider>` wrapping `<App />` so `usePreferences()` is available everywhere.

#### `frontend/index.html`

Changed `<title>` from "frontend" to "PhysioFit — AI Lower-Limb Function".

#### `frontend/README.md`

**Completely replaced** the default Vite template README with a comprehensive project README covering: quick start, how to test, feature test table, page tour (all 11 routes), project structure, features, design tokens, available scripts, environment variables, and next steps.

#### `frontend/.env.example`

Not modified (already existed from Phase 0 with `VITE_API_BASE_URL`).

---

### Artefacts (Mockups)

#### `mockups/physiofit-mockup.html`

The original self-contained HTML/CSS/JS mockup. Now superseded by the React app but kept as a design reference. The `.claude/launch.json` "mockups" config serves it on port 4178.

---

### Configuration Files Modified

#### `.claude/launch.json`

Added a second server configuration for the React dev server:

```json
{
  "name": "frontend",
  "runtimeExecutable": "npm",
  "runtimeArgs": [
    "--prefix",
    "frontend",
    "run",
    "dev",
    "--",
    "--port",
    "5180",
    "--strictPort"
  ],
  "port": 5180
}
```

This allows the Claude Code preview tool to start and screenshot the running React app.

---

### Project Tracking Files Modified

#### `task.md`

- Updated status line from "Phase 0 complete — Phase 1A next" to "Phase 0 complete · Phase 1A complete — Phase 1B next".
- Checked all 13 Phase 1A tasks as `[x]`.
- Added a note documenting the extras delivered (theme, i18n, font-size, responsive).

#### Memory file: `.claude/projects/.../memory/physiofit-design-direction.md`

Updated with Phase 1A completion status, React file structure, dev server command, and "next: Phase 1B backend integration".

---

## Verification Done (Browser Screenshots)

All screens were verified in the Claude Code preview panel (Chromium, 1320×900 desktop + 375×812 mobile):

| Screen                              | Verified                                                      |
| ----------------------------------- | ------------------------------------------------------------- |
| Landing — light, desktop            | ✅ hero, pose skeleton, stats, disclaimer                     |
| Landing — dark, desktop             | ✅ lime accent, glows, atmosphere                             |
| Landing — Chinese (中文), dark      | ✅ full page translated including nav, hero, disclaimer       |
| Dashboard — light, desktop          | ✅ metrics, emerald chart line, table, tags, reminders        |
| Dashboard — dark (via toggle)       | ✅ lime chart line, dark surfaces                             |
| Font-size A++ on Report page        | ✅ all text scales larger via rem                             |
| Camera Setup — light                | ✅ pose skeleton, checklist, guidance, corners                |
| Report — light                      | ✅ score dial (7.0/10), sub-score bars, coaching, disclaimer  |
| Dashboard — mobile (375px)          | ✅ single-column stacks, hamburger button visible             |
| Mobile sidebar drawer open          | ✅ slides in, scrim visible, all nav items present            |
| Theme toggle (dark ↔ light)         | ✅ persists across navigation, `data-theme` attribute updates |
| Language switch (EN → ZH → EN)      | ✅ full page re-renders, persists in localStorage             |
| Font-size control (A/A+/A++)        | ✅ `data-fs` attribute updates, UI grows                      |
| TypeScript typecheck (`npx tsc -b`) | ✅ zero errors                                                |

---

## What Is NOT Done Yet (Future Phases)

The following are explicitly **not** part of this session and are left for future phases:

- **No backend calls.** All data is mock/hardcoded local state. No `fetch()` or Axios calls.
- **No JWT or authentication.** Forms navigate directly to `/dashboard` on submit.
- **No real camera access.** `CameraSetup` and `LiveSession` use `PoseFigure` placeholder.
- **No MediaPipe Pose integration.** Phase 2 item.
- **No WebSocket.** Live session timer is a local `useEffect` interval only.
- **No Module A or B scoring logic.** All scores are hardcoded.
- **No PostgreSQL interaction.** Phase 1B connects the UI to the existing FastAPI/PostgreSQL backend.

---

## How to Run the React App

```bash
# From project root:
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

Or via Claude Code preview (uses `.claude/launch.json` "frontend" config, port 5180).

---

## Architecture Context

- Stack: React 19 + TypeScript + Tailwind CSS v4 + Vite 8 + React Router v6 + react-i18next.
- Styling: **No Tailwind utility classes used** in JSX — all styles are in `index.css` using class names (`.btn`, `.panel`, `.metric`, etc.). Tailwind is imported at the top of `index.css` via `@import "tailwindcss"` for its reset/base layer.
- State: All local React state (`useState`). No Redux, Zustand, or other state managers.
- Preferences: `useContext` with `PreferencesContext`. Theme and fontScale synced to `document.documentElement` attributes (`data-theme`, `data-fs`).
- i18n: `useTranslation()` hook from `react-i18next`. Keys accessed as `t("section.key")`.

---

_This document was written on 2026-06-05 to give complete context to future AI agents or developers picking up this project._

## Phase 2 Completion Details — Camera and MediaPipe Pose Integration

**Session Date:** 2026-06-29  
**Status:** Phase 2 COMPLETE  
**Goal:** Replace the static camera placeholder with a real browser webcam + MediaPipe pose pipeline, show live skeleton overlay, calculate real capture quality, and send real quality metrics when ending a session.

### Summary

Phase 2 implemented the first real pose-estimation layer in the frontend. Camera Setup and Live Session no longer use the decorative `PoseFigure` placeholder for the active camera area. They now use the browser `MediaDevices.getUserMedia()` API, MediaPipe Tasks Vision `PoseLandmarker`, a mirrored live video feed, and a canvas skeleton overlay.

Important privacy rule followed: **raw video stays in the browser**. No video frames are uploaded to the backend. Only derived summary metrics, `capture_quality` and `valid_frame_ratio`, are sent through the existing `sessionService.end()` API.

### Key Decisions Implemented

- MediaPipe model: `pose_landmarker_full`.
- Runtime package: `@mediapipe/tasks-vision`.
- Model hosting: self-hosted from `frontend/public/models/pose_landmarker_full.task`.
- WASM hosting: self-hosted from `frontend/public/mediapipe/wasm/`.
- Detection mode: `runningMode: "VIDEO"` inside a `requestAnimationFrame` loop.
- Pose instance strategy: singleton-style `PoseLandmarker` instance in `useMediaPipePose.ts`, so page navigation does not recreate the model unnecessarily.
- Capture quality gate: Camera Setup disables **Start session** when live quality is below `0.6`.
- Rep counting remains mocked. Real rep/ROM/tempo/stability metrics are intentionally left for Phase 3 and later phases.

### Dependencies and Static Assets Added

#### `frontend/package.json`

Added:

```bash
npm install @mediapipe/tasks-vision
```

Added script:

```json
"postinstall": "node scripts/copy-wasm.js"
```

This keeps MediaPipe WASM files available under `public/` after future `npm install` runs.

#### `frontend/scripts/copy-wasm.js`

Small Node script that copies:

```text
frontend/node_modules/@mediapipe/tasks-vision/wasm/*
```

to:

```text
frontend/public/mediapipe/wasm/
```

It logs a simple success message:

```text
[copy-wasm] MediaPipe WASM files copied to public/mediapipe/wasm/
```

#### Static files added under `frontend/public/`

- `frontend/public/models/pose_landmarker_full.task`
- `frontend/public/mediapipe/wasm/vision_wasm_internal.js`
- `frontend/public/mediapipe/wasm/vision_wasm_internal.wasm`
- `frontend/public/mediapipe/wasm/vision_wasm_module_internal.js`
- `frontend/public/mediapipe/wasm/vision_wasm_module_internal.wasm`
- `frontend/public/mediapipe/wasm/vision_wasm_nosimd_internal.js`
- `frontend/public/mediapipe/wasm/vision_wasm_nosimd_internal.wasm`

These assets allow the pose pipeline to load without relying on a CDN at runtime.

### New Frontend Source Files

#### `frontend/src/types/pose.ts`

Defines the shared pose data shape:

- `Landmark` with `x`, `y`, `z`, and `visibility`.
- `PoseFrame` with `timestampMs` and 33 landmarks.
- `CaptureQuality` with `score` and `validFrameRatio`.
- `LM` landmark constants for MediaPipe indices, including shoulders, hips, knees, ankles, heels, and foot index points.

This file is the shared reference point for later Phase 3/4 metric extraction.

#### `frontend/src/utils/poseLandmarks.ts`

Contains:

- `POSE_CONNECTIONS`: skeleton line pairs for torso, arms, and lower limbs.
- `LOWER_LIMB_INDICES`: key hip/knee/ankle/foot landmarks used for highlighted drawing.
- `createLandmarkSmoother()`: small moving-average smoother to reduce frame-to-frame jitter.

The lower-limb landmarks are highlighted visually because this FYP focuses on lower-limb function.

#### `frontend/src/utils/captureQuality.ts`

Contains:

- `computeFrameQuality(landmarks)`: returns a `0–1` score for one frame.
- `createSessionQualityTracker(minQuality = 0.6)`: tracks total frames and valid frames across a session.

Quality currently focuses on visibility of:

- left/right shoulders
- left/right hips
- left/right knees
- left/right ankles

A frame is counted as valid when its quality is at least `0.6`.

#### `frontend/src/hooks/useWebcam.ts`

Handles browser camera access:

- Requests webcam using `navigator.mediaDevices.getUserMedia()`.
- Attaches stream to a `<video>` element through a React ref.
- Sets `ready` when the video is playing.
- Stops all media tracks on unmount.
- Handles common error states:
  - `permission-denied`
  - `no-camera`
  - `unknown`

Important console logs:

```text
[useWebcam] Camera stream acquired
[useWebcam] Video playing
[useWebcam] Camera stream stopped
```

#### `frontend/src/hooks/useMediaPipePose.ts`

Handles MediaPipe model loading and pose detection:

- Loads WASM from `/mediapipe/wasm`.
- Loads model from `/models/pose_landmarker_full.task`.
- Creates `PoseLandmarker` with:
  - `runningMode: "VIDEO"`
  - `delegate: "GPU"`
  - `numPoses: 1`
- Runs detection inside `requestAnimationFrame`.
- Returns:
  - `landmarks`
  - `fps`
  - `ready`
  - `error`

Important console logs:

```text
[useMediaPipePose] Loading MediaPipe PoseLandmarker...
[useMediaPipePose] PoseLandmarker ready
[useMediaPipePose] Detection loop started
[useMediaPipePose] Detection loop stopped
```

If `VITE_ENABLE_DEBUG_POSE=true`, it also logs pose landmark debug messages.

#### `frontend/src/components/PoseCanvas.tsx`

New camera display component used by Camera Setup and Live Session.

It renders:

- Mirrored live `<video>`.
- Mirrored overlay `<canvas>`.
- Skeleton lines and joints based on current landmarks.
- Green-highlighted lower-limb bones and joints.
- Loading spinner while webcam/model starts.
- Friendly error UI when camera permission is denied or no camera is detected.

This component replaces the active camera use of `PoseFigure`. `PoseFigure` remains useful for decorative/static UI, such as the landing page.

#### `frontend/src/components/CaptureQualityBadge.tsx`

Reusable live quality badge.

Input:

```ts
quality: number // 0 to 1
label?: string
```

Displays quality as a percentage and changes colour by score:

- `>= 0.75`: good
- `>= 0.5`: fair
- `< 0.5`: poor

#### `frontend/src/hooks/useSessionRecorder.ts`

Buffers pose frames during Live Session for future Phase 3/4 logic.

Provides:

- `start()`
- `record(frame, quality)`
- `summary()`

`summary()` returns:

- `score`
- `validFrameRatio`
- `frameCount`
- `durationMs`
- `frames`

Only `score` and `validFrameRatio` are currently sent to the backend. The buffered frames remain in memory only and are not persisted.

### Existing Files Modified

#### `frontend/src/pages/CameraSetup.tsx`

Changed from static placeholder to real camera setup page.

Implemented:

- `useWebcam()`
- `useMediaPipePose()`
- `computeFrameQuality()`
- `PoseCanvas`
- `CaptureQualityBadge`
- dynamic view guidance:
  - `supported_single_leg_stance` / codes containing `single_leg` use front view
  - other exercises default to side view
- quality warning when body is not visible enough
- Start button disabled when quality is below `0.6`

The existing `sessionService.start()` flow is preserved.

#### `frontend/src/pages/LiveSession.tsx`

Changed from static placeholder to real live session camera page.

Implemented:

- `useWebcam()`
- `useMediaPipePose()`
- `PoseCanvas`
- `CaptureQualityBadge`
- `useSessionRecorder()`
- per-frame landmark recording when landmarks are available
- real `capture_quality` and `valid_frame_ratio` sent to `sessionService.end()`

Removed hardcoded values:

```ts
capture_quality: 0.9;
valid_frame_ratio: 0.9;
```

Now the values come from:

```ts
const { score, validFrameRatio } = recorder.summary();
```

#### `frontend/src/index.css`

Added styles for the new camera/pose display:

- `.pose-canvas-wrap`
- `.pose-video`
- `.pose-overlay`
- `.pose-loading`
- `.pose-error`
- `.spinner`
- `@keyframes spin`

The styles keep the video and canvas aligned inside the existing `.cam-stage` layout.

#### `frontend/.env`

Created from `frontend/.env.example`.

Current relevant flag:

```env
VITE_ENABLE_DEBUG_POSE=true
```

This enables extra pose debug logs in the browser console.

#### `task.md`

Updated Phase 2 checklist to `[x]` and expanded completed items:

- webcam access
- MediaPipe model integration
- skeleton overlay
- capture quality badge
- side/front view instruction
- Start button quality gate
- session recorder
- real backend quality metrics

### Runtime Behaviour

#### Camera Setup

Expected behaviour:

- Browser asks for camera permission.
- Live camera preview appears.
- Skeleton overlay tracks body landmarks.
- Capture quality badge changes as the user enters/leaves the frame.
- Start session is blocked when quality is too low.
- View guidance changes based on exercise type.

#### Live Session

Expected behaviour:

- Camera and skeleton overlay appear again.
- Session recorder starts automatically.
- Landmark frames are stored in memory while user moves.
- End set sends real quality metrics to backend.
- Timer and rep count remain prototype/mock behaviour for now.

### Verification Completed

Ran TypeScript build check:

```bash
cd frontend
npx tsc -b
```

Result:

```text
zero TypeScript errors
```

One TypeScript issue was fixed during implementation: `LOWER_LIMB_INDICES` was explicitly typed as `Set<number>` so generic numeric landmark indices can be checked safely.

### Manual Testing Instructions

To test Phase 2 locally:

```bash
cd frontend
npm run dev
```

Open the local Vite URL, usually:

```text
http://localhost:5173
```

Then:

1. Navigate to Mode Selection.
2. Choose Functional Checking.
3. Select an exercise.
4. Open Camera Setup.
5. Allow camera permission.
6. Confirm live video appears.
7. Confirm skeleton overlay follows the body.
8. Move out of frame and confirm quality decreases.
9. Move fully into frame and confirm quality increases.
10. Confirm Start session is disabled below 60% quality.
11. Start session when quality is acceptable.
12. On Live Session, move for a few seconds.
13. Click End set.
14. In browser DevTools Network tab, confirm the end-session request sends real `capture_quality` and `valid_frame_ratio`, not hardcoded `0.9`.

### Console Logs to Expect

Useful browser console logs:

```text
[useWebcam] Camera stream acquired
[useWebcam] Video playing
[useMediaPipePose] Loading MediaPipe PoseLandmarker...
[useMediaPipePose] PoseLandmarker ready
[useMediaPipePose] Detection loop started
[LiveSession] Session recorder started
[useSessionRecorder] Recording started
[useSessionRecorder] Summary — frames: ..., quality: ..., validRatio: ...
[LiveSession] Ending session — quality: ..., validRatio: ...
```

### Known Limitations / Next Phase Notes

- Rep counting is still mocked with random increments. Real rep counting belongs to Phase 3.
- ROM, tempo, trunk lean, sway, and stability metrics are not implemented yet.
- The recorder currently keeps frame data in browser memory only.
- No raw video is stored or uploaded.
- The capture-quality algorithm is intentionally simple for Phase 2: it uses key landmark visibility, not full biomechanics.
- Backend schema/API did not need changes because `capture_quality` and `valid_frame_ratio` already existed.

### Developer Handoff Notes

Future Phase 3 work should reuse:

- `PoseFrame` from `frontend/src/types/pose.ts`
- `LM` landmark constants from `frontend/src/types/pose.ts`
- buffered frames from `useSessionRecorder()`
- lower-limb landmarks and connections from `poseLandmarks.ts`

Recommended next technical step:

- Implement deterministic Module A feature extraction from the recorder frames:
  - Sit-to-Stand: knee angle range, trunk lean proxy, repetition segmentation.
  - Supported Single-Leg Stance: center/ankle/hip sway proxy and hold duration.
  - Weight-Bearing Lunge Test: ankle dorsiflexion proxy and left/right symmetry.

---

## Phase 3A Completion Details — Sit-to-Stand Attempted vs. Valid Rep Counting with Live Backend Confirmation

**Session Date:** 2026-07-06  
**Status:** Phase 3A COMPLETE  
**Goal:** Separate "attempted reps" (loose client-side heuristic) from "valid reps" (authoritative backend confirmation), implement live boundary-triggered backend calls, and decouple session completeness/confidence status from movement-quality band to prevent tracking failures from being mislabeled as poor form.

### Summary

Phase 3A redesigned the Sit-to-Stand rep-counting workflow from naive client-only heuristics to a hybrid model:

- **Client-side:** fast rep-boundary detection (sitting → rising → standing → sitting FSM with hysteresis exit bands) that fires at each attempt conclusion.
- **Backend confirmation:** every boundary triggers a `POST /api/module-a/analyze` call with accumulated frames; the backend runs the authoritative `SessionEngine` + `banding` and returns the true `rep_count`.
- **Auto-persist:** the backend persists to the database automatically when `rep_count >= target_rep_count`, signaled by a `persisted: true` flag; frontend navigates to report on that flag alone—no separate "finalize" call needed.
- **Decoupled status:** introduced `session_status` ("complete" / "incomplete" / "low_confidence") as a separate axis from `band` (movement quality), so poor capture quality never masquerades as poor form.

### Key Files Changed

#### Backend

**`backend/app/module_a/banding.py`**

- New: `compute_session_status()` derives completeness/confidence independent of band (e.g., `quality_band=="poor"` → `"low_confidence"`; `rep_count < target` → `"incomplete"`; else → `"complete"`).
- Rewrote: `compute_band()` no longer caps scores for incomplete reps; band/score computed purely from valid reps actually captured; returns new fields `session_status` and `is_partial_score`.
- Result: a session with 3/5 clean reps can score "good" + "incomplete" (not forced to "poor" just for incompleteness).

**`backend/app/module_a/schemas.py`**

- `AnalyzeRequest`: added `clientAttemptedReps: int | None` (UI-only signal), `forceFinalize: bool` (60s-timeout flag).
- `ModuleAMetrics`: added `client_attempted_reps: int | None` for Report's "Attempted reps" row.
- `ModuleAResultResponse`: added `session_status`, `is_partial_score`, `persisted: bool`.

**`backend/app/module_a/rest_router.py`**

- `analyze_session()`: same route, new logic. Always computes engine + band; persists only when `forceFinalize=True` OR `rep_count >= target`. Returns `persisted` flag so frontend knows whether to navigate.
- `_to_response()`: extended to include new fields.
- `get_session_result()`, `get_history()`: legacy-row fallback (infer `session_status="complete"` for pre-migration rows where it's NULL).

**`backend/app/module_a/crud.py`**

- `save_result()`: became an upsert—checks for existing `ModuleAResult` row and updates in-place instead of always inserting. Persists `session_status`, `is_partial_score`, `client_attempted_reps` in `metrics_json`.

**`backend/app/db/models.py`**

- Added nullable `session_status: str | None` and `is_partial_score: bool` (default False) to `ModuleAResult`.

**`backend/alembic/versions/20260706_0003_module_a_session_status.py`**

- New migration: adds both columns, no backfill.

**`backend/tests/test_module_a_banding.py`** (new file)

- 5 unit tests covering: complete clean session, incomplete clean reps not force-capped, zero-rep edge case, poor quality as low_confidence (not poor band), and genuinely poor form still correctly labeled as "complete."
- All tests pass.

#### Frontend

**`frontend/src/config/moduleAThresholds.ts`**

- Added: `LIVE_KNEE_STAND_EXIT = 150`, `LIVE_KNEE_SIT_EXIT = 120` (hysteresis bands), `MAX_SESSION_SECONDS = 60`, `LIVE_MIN_QUALITY_FOR_VALID_REP = 0.7`.

**`frontend/src/utils/stsLiveEstimate.ts`** (complete rewrite)

- Replaced naive `count` / `"good_rep"` logic with three-state FSM (sitting → rising → standing) + hysteresis exit bands.
- Every concluded attempt fires `"rep_boundary"` event, increments `attemptedRepCount`.
- Includes `reasonCode` (optimistic client guess: `"low_visibility"`, `"too_unstable"`, `"incomplete"`) for instant UI feedback.
- No client-side validity decision — backend confirmation only.

**`frontend/src/services/moduleAService.ts`**

- Extended types: `SessionStatus`, `ModuleAMetrics.client_attempted_reps`, `ModuleAResult` gains `session_status`, `is_partial_score`, `persisted`.
- `analyze()` takes optional `{ clientAttemptedReps, forceFinalize }` params.

**`frontend/src/pages/LiveSession.tsx`** (major rewrite)

- New state: `attemptedReps`, `validReps`, `liveReasonGuess`, `validRepsRef`, `checkInFlightRef`, `pendingCheckRef`, `timeoutTriggeredRef`.
- Per-frame effect: on `rep_boundary`, calls `analyze()` with accumulated frames + `{ clientAttemptedReps: attemptedReps, forceFinalize: false }`.
- Response handler: updates `validReps` from response; if `persisted=true`, navigates to report immediately (no extra call).
- Timeout guard: at 60s with `validReps < 5`, sends one final `analyze(..., { forceFinalize: true })`.
- Request coalescing: if a call is in flight when another boundary fires, queues the latest frames and sends once the first call completes.
- Live status text: shows `validReps/5` (never `attemptedReps`); when not-counted reps exist, displays reason.
- Cancel button: unchanged—discards session, no analyze call.

**`frontend/src/pages/Report.tsx`**

- Added status banner (reusing `dash-note` pattern): shows "Session incomplete: X/5 valid reps" or "Low confidence: camera tracking wasn't reliable..." when `session_status !== "complete"`.
- Metrics section: renamed "Reps completed" to "Valid reps"; added "Attempted reps" row when `client_attempted_reps != null`.
- Score dial: added "Partial movement-quality score" pill when `is_partial_score=true`.

**`frontend/src/i18n/{en,ms,zh}.ts`**

- New keys across all three languages:
  - Live: `reasonLowVisibilityRep`, `reasonTooUnstable`, `validRepsStatus`, `repsNotCountedStatus`, `oneMoreRepPrompt`.
  - Report: `incompleteStatus`, `lowConfidenceStatus`, `validReps`, `attemptedReps`, `partialScoreLabel`.

### Verification Completed

**Backend tests:** All 8 unit tests pass (5 new banding tests + 3 existing quality tests):

- Incomplete but clean reps can score "good" (not force-capped to "poor").
- Poor capture quality marked as `"low_confidence"`, not as poor band.
- Genuinely poor form (high wobble/lean) correctly labeled "complete" with low score.

**API verification:** Created 4 fresh test sessions:

1. Partial session (2 reps, `forceFinalize=false`): returned `persisted=false`, no database row.
2. Completed session (5 reps, `forceFinalize=false`): returned `persisted=true`, created one database row.
3. Stray retry (same session, same frames): upsert succeeded, no duplicate row.
4. Early timeout (2 reps, `forceFinalize=true`): persisted with `session_status="incomplete"`.

**Frontend browser verification:** Via preview tool:

- Report page renders "Session incomplete: 2/5 valid reps" with partial-score pill.
- Legacy row (pre-migration `session_status=NULL`) inferred as `"complete"` at read time.
- Low-confidence legacy row correctly shows distinct message.
- TypeScript compilation: zero errors.

### Architecture Decisions

1. **Single endpoint, backend decides when to persist.** No duplicate `live-check` route; same `analyze` endpoint used for both progress updates and final save. Backend auto-persists on `rep_count >= target`, eliminating the need for a separate "finalize" round-trip on the happy path.

2. **No manual early-end button.** Session ends via Cancel (discard) or 60s timeout (force-finalize). This simplifies the frontend and avoids a third codepath for ending sessions.

3. **Upsert semantics in `save_result()`.** A stray/retried request after persistence already happened will safely re-save consistent data instead of creating a duplicate row.

4. **Decoupled `session_status` from `band`.** Tracking problems (poor quality, incomplete reps) never masquerade as movement-quality verdicts. A partial session with clean form can score "good" + "incomplete," and poor tracking is transparently labeled "low_confidence" with the score still shown.

### Known Limitations / Next Phase Notes

- Session timeout is client-side only (60s timer). Real backoff/timeout should be server-side if this goes to production.
- Wobble detection and quality thresholds in `stsLiveEstimate.ts` are heuristic-based, not tuned to actual movement. Threshold calibration deferred to Phase 4.
- Rep-boundary detection uses knee-angle hysteresis; other joints (hip, ankle, trunk) are not yet factored into the "valid rep" decision.
- Single-Leg Stance and Weight-Bearing Lunge still use Phase 2's random-rep simulation. Phase 3B (next) will apply the same attempted/valid architecture to Single-Leg Stance.

### Developer Handoff Notes

For Single-Leg Stance (Phase 3B) and Weight-Bearing Lunge (Phase 3C):

- Reuse the same `rep_boundary` / `analyze()` / `persisted` architecture implemented here.
- Define new movement thresholds (balance sway, hold duration, ankle dorsiflexion range) in `moduleAThresholds.ts`.
- Create new `createStsLiveEstimator` equivalents for each exercise (e.g., `createSingleLegStanceLiveEstimator`).
- New `ComputeSessionStatus` function can be reused; only `compute_band()` logic needs per-exercise tuning.
- Update `Report.tsx` to show exercise-specific metrics (e.g., sway instead of wobble for Single-Leg Stance).

### Recommended Next Step

Implement Single-Leg Stance (Supported Single-Leg Stance) using the same rep-boundary + backend-confirmation pattern:

- Define balance thresholds: max hip/ankle sway (from `left_hip.z - right_hip.z`, etc.), min hold duration.
- Implement `createSingleLegStanceLiveEstimator()` with state machine: standing on one leg → full stand (goal) → return to two-leg or fall.
- New i18n keys for Single-Leg Stance specific feedback (e.g., "Stay balanced," "Hold longer").
