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

- [ ] Implement Sit-to-Stand session flow
- [ ] Implement Supported SLS session flow
- [ ] Implement WBLT session flow
- [ ] Calculate simple metrics
- [ ] Generate Good/Fair/Poor band
- [ ] Save Module A results to PostgreSQL
- [ ] Show report page
- [ ] Show dashboard trend

**Deliverable:**

- User can complete all 3 functional checks
- Results are saved and viewable

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
