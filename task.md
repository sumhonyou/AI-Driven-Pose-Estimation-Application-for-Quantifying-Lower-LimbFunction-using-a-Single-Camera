# FYP Development Tasks

**Project:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera  
**Status:** 0% coding progress  
**Related docs:** [FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md](./FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md) (architecture & design), [rules.md](./rules.md) (coding agent rules)

---

## Recommended Start Order

Since the project is at 0 progress, do **not** start with ML first. Work in this order:

1. Create React + TypeScript + Tailwind frontend
2. Create FastAPI backend
3. Create PostgreSQL Docker setup
4. Make backend connect to PostgreSQL
5. Implement register/login
6. Implement session start/end
7. Build dashboard and mode selection
8. Add webcam and MediaPipe Pose
9. Implement Module A simple rule-based checking
10. Then start Module B placeholder pipeline
11. Only after that, train/integrate Extra Trees model
12. Deploy after core flow works locally

---

## Milestones

### First Milestone

> A user can register, login, start a session, end a session, and see that session saved in PostgreSQL.

### Second Milestone

> The webcam page can show MediaPipe Pose skeleton overlay and capture quality.

### Third Milestone

> Module A produces and stores Good/Fair/Poor results for at least one functional check.

---

## Phase 0: Project Setup

**Goal:** Prepare development environment and repository.

**Tasks:**

- [ ] Create frontend folder using React + TypeScript + Vite
- [ ] Install Tailwind CSS
- [ ] Create backend folder using FastAPI
- [ ] Add Docker Compose for PostgreSQL
- [ ] Connect FastAPI to PostgreSQL
- [ ] Create `.env.example` files
- [ ] Add basic README

**Deliverable:**

- Frontend runs locally
- Backend runs locally
- PostgreSQL runs locally
- Backend can connect to database

---

## Phase 1: Basic Full-Stack Skeleton

**Goal:** Build the minimum working application structure.

**Tasks:**

- [ ] Implement register/login
- [ ] Implement JWT authentication
- [ ] Create user profile page
- [ ] Create dashboard page with placeholder data
- [ ] Create exercise catalog seed data
- [ ] Create session start/end APIs
- [ ] Create session history page

**Deliverable:**

- User can register/login
- User can start and end a session
- Session appears in history

---

## Phase 2: Camera and MediaPipe Integration

**Goal:** Make the frontend detect body landmarks.

**Tasks:**

- [ ] Build Camera Setup page
- [ ] Access webcam using Browser MediaDevices API
- [ ] Integrate MediaPipe Pose
- [ ] Draw skeleton overlay on canvas
- [ ] Calculate landmark visibility
- [ ] Show capture quality badge
- [ ] Add side/front view instruction by exercise type

**Deliverable:**

- Webcam works
- Pose landmarks are visible
- Capture quality is shown

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
