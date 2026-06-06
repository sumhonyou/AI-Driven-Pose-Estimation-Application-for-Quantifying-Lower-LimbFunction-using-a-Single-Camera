# PhysioFit — AI Lower-Limb Function Frontend

A modern, accessible React web application for guided lower-limb functional checking and rehabilitation exercise grading using MediaPipe Pose. Built with React 19, TypeScript, Tailwind CSS v4, and Vite.

**Phase 1A Status:** UI clickable prototype with all 11 pages, dark/light theme, 4-language i18n, accessibility font-size control, and full responsive design (mobile, tablet, desktop).

## Tech Stack

- **Framework:** React 19 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS v4
- **Routing:** React Router v6
- **i18n:** react-i18next + i18next-browser-languagedetector
- **Icons & SVG:** Custom Figma-inspired component library

## Quick Start

### Prerequisites
- Node.js LTS (v18+ recommended)
- npm or yarn

### Installation & Development

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run type check
npx tsc -b

# Lint
npm run lint
```

## How to Test the App

The frontend is a full UI prototype with mock data (no backend calls yet).

### Key User Flows

**Landing Page → Dashboard:**
1. Open http://localhost:5173
2. Click **"Start a check"** → taken to `/mode`
3. Select **Functional Checking** or **Rehab Grading**
4. Choose an exercise (Sit-to-Stand, etc.)
5. Camera setup page with guidance checklist
6. Live session with timer, reps, and live band indicator
7. Post-session report with score dial, sub-scores, and error tags
8. Return to dashboard or session history

**Try These Features:**

| Feature | How to Test |
|---------|-----------|
| **Dark/Light Toggle** | Click the 🌙/☀️ icon in any topbar |
| **Font Size (A/A+/A++)** | Click the "A" button in the topbar — text scales globally |
| **4-Language Switch** | Click 🌐 **English** dropdown → select 中文, Bahasa Malaysia, or हिन्दी → entire UI changes |
| **Mobile Responsive** | Resize browser to 375×812 (mobile preset in DevTools) → sidebar collapses, hamburger menu slides in |
| **Disclaimer** | Present on Landing, Dashboard, and Report pages (non-diagnostic safety warning) |

### Page Tour

| Route | Page | Features |
|-------|------|----------|
| `/` | **Landing** | Hero with pose skeleton, modules explainer, 4-step walkthrough |
| `/login` | **Login** | Email/password form (UI only) |
| `/register` | **Register** | Registration with optional profile fields |
| `/dashboard` | **Dashboard** | 4 metric cards, score-trend chart (with emerald line in light mode), band distribution, recent sessions table, error tags, reminders list |
| `/mode` | **Mode Selection** | Choose Functional Checking or Rehab Grading |
| `/exercise` | **Exercise Selection** | Pick from 3 functional checks or 1 rehab exercise |
| `/camera` | **Camera Setup** | Pose skeleton, capture quality badge, pre-start checklist |
| `/live` | **Live Session** | Real-time timer, reps counter, live good/fair/poor band indicator |
| `/report` | **Report** | Score dial (7.0/10), sub-scores (ROM, Tempo, Stability), error tags, coaching feedback |
| `/history` | **Session History** | Filterable table of past sessions with bands and scores |
| `/reminders` | **Reminders** | Checkable reminder list |

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # Entry point (with PreferencesProvider + i18n)
│   ├── App.tsx               # React Router setup
│   ├── index.css             # Design system (colors, spacing, components, responsive)
│   ├── i18n/                 # Internationalization
│   │   ├── en.ts             # English translations
│   │   ├── zh.ts             # Simplified Chinese
│   │   ├── ms.ts             # Bahasa Malaysia
│   │   ├── hi.ts             # Hindi
│   │   └── index.ts          # i18n configuration
│   ├── preferences.tsx        # Theme + font-scale context (persisted to localStorage)
│   ├── useReveal.ts          # Scroll-reveal animation hook
│   ├── components/
│   │   ├── Icons.tsx         # SVG icon library
│   │   ├── Controls.tsx      # Theme toggle, font-size control, language switcher
│   │   └── PoseFigure.tsx    # Reusable pose skeleton SVG
│   ├── layouts/
│   │   ├── PublicLayout.tsx  # Nav + footer for landing, login, register
│   │   └── DashboardLayout.tsx # Sidebar + mobile drawer for dashboard pages
│   └── pages/
│       ├── Landing.tsx
│       ├── Login.tsx
│       ├── Register.tsx
│       ├── Dashboard.tsx
│       ├── ModeSelection.tsx
│       ├── ExerciseSelection.tsx
│       ├── CameraSetup.tsx
│       ├── LiveSession.tsx
│       ├── Report.tsx
│       ├── SessionHistory.tsx
│       └── Reminders.tsx
├── index.html
├── vite.config.ts
├── tsconfig.app.json
├── eslint.config.js
└── package.json
```

## Features

### 🎨 Design System
- **Brand Colors:** Neon Lime (#9BFF00), Emerald (#00AE54), Deep Dark Green (#051D0C)
- **Typography:** Inter font family throughout
- **Themes:** Light (default) and dark modes with smooth transitions
- **Responsive:** Mobile (375px), tablet (768px), desktop (1280px+)
- **Accent Bands:** Good (lime/emerald), Fair (amber), Poor (coral)

### 🌍 Internationalization
- **4 Languages:** English (en), 中文 (zh), Bahasa Malaysia (ms), हिन्दी (hi)
- **Automatic Persistence:** Language preference saved to localStorage
- **Auto-Detection:** Falls back to browser language if available
- **Full Coverage:** All UI strings, form labels, tooltips, and content translated

### ♿ Accessibility
- **Font-Size Control:** A (base 16px) / A+ (17.5px) / A++ (19px) via CSS rem scaling
- **Preference Persistence:** Theme and font-size saved to localStorage, restored on reload
- **Focus Visible:** Outline styling for keyboard navigation
- **Semantic HTML:** Proper ARIA labels and roles throughout
- **High Contrast:** WCAG-compliant color combinations

### 📱 Responsive Design
- **Desktop:** Full sidebar navigation, multi-column grids
- **Tablet:** Collapsed sidebar, 2-column layouts
- **Mobile:** Hamburger menu, drawer sidebar (with scrim), single-column stacks
- **Navigation:** All pages adapt layout without horizontal scroll

### 🎬 Motion & Interactions
- **Scroll Reveal:** Staggered fade-in animations on page load
- **Hover Effects:** Subtle lifts and color shifts on cards and buttons
- **Smooth Transitions:** CSS-based theme toggling, page navigation
- **Live Indicators:** Animated progress rings, pulsing status dots

## Design Tokens

Key CSS variables (set in `index.css`):

```css
/* Light Theme (default) */
--bg: #EEF4EC              /* Page background */
--surface: #FFFFFF         /* Card backgrounds */
--text: #062012            /* Primary text */
--accent-text: #00AE54     /* Emerald for links, highlights */
--good: #00AE54            /* Success/good indicator */

/* Dark Theme */
--bg: #04160A              /* Dark page background */
--surface: #0A2914         /* Dark card */
--text: #EAF7EC            /* Light text */
--accent-text: #9BFF00     /* Lime for links, highlights */
--good: #9BFF00            /* Success/good in dark mode */
```

Font sizes use `rem` units (scaled by the `data-fs` attribute on `<html>`):
- `data-fs="1"` (A): root { font-size: 16px }
- `data-fs="2"` (A+): root { font-size: 17.5px }
- `data-fs="3"` (A++): root { font-size: 19px }

## Available Scripts

```bash
npm run dev       # Start Vite dev server
npm run build     # Compile TypeScript & build with Vite
npm run lint      # Run ESLint on src/
npm run preview   # Preview production build locally
```

## Environment Variables

Currently not required for the UI prototype. When Phase 1B (backend) is ready:

```env
VITE_API_BASE_URL=http://localhost:8000  # Backend API URL
VITE_ENABLE_DEBUG_POSE=true               # Debug MediaPipe (future)
```

## Next Steps (Phase 1B)

- Connect pages to FastAPI backend (`/api/auth/*`, `/api/sessions/*`, etc.)
- Implement real WebSocket for live MediaPipe Pose overlay
- Load mock data from backend instead of hardcoded state
- Add JWT authentication flow
- Add camera preview and pose landmark rendering

## Notes

- **All text is mock data** — future phases will wire to backend APIs.
- **No camera access yet** — CameraSetup and LiveSession pages show placeholder UI.
- **Non-diagnostic** — All pages display the required non-diagnostic disclaimer per project rules.
- **Keyboard Navigation** — Full `:focus-visible` support for accessibility.

## Support & Documentation

- **Project Docs:** See `../FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md`
- **Task Tracking:** See `../task.md`
- **Design Reference:** See `../mockups/physiofit-mockup.html` (HTML prototype)
- **Styling:** Refer to `src/index.css` for the complete design system

---

Built with ❤️ for PhysioFit | **Phase 1A UI Prototype** | React 19 + TypeScript + Tailwind v4 + Vite
