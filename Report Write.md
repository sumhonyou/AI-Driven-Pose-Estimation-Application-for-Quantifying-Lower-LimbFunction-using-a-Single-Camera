#### 3.4.3.2 System Architecture
 
Looking at the system architecture, this project adopted a client-server design across three tiers, which were a React and TypeScript frontend, a FastAPI backend, and a PostgreSQL database.
 
Coming to the actual data flow, webcam video never left the browser. MediaPipe (@mediapipe/tasks-vision) ran entirely client-side through requestAnimationFrame. The backend's requirements.txt contained no MediaPipe, opencv-python, or cv2, and no image-upload endpoint existed anywhere in the API. Hence, the backend only ever received already-extracted numeric landmarks, sent as a {timestampMs, worldLandmarks} JSON payload.

This design was justified on four grounds. Firstly, it protected user privacy, and this was not only an engineering preference but user-evidenced, since 16 of 20 requirements-survey respondents preferred on-device analysis with no video saved. Secondly, it reduced latency, since landmarks are far smaller than video frames and did not need to travel to a server before feedback could be shown. Thirdly, it reduced storage cost, since only derived numeric results were ever persisted. Fourthly, it kept deployment simpler, since the backend never needed to run a heavy vision pipeline.

Coming to backend responsibilities, the backend handled authentication, session management, rule scoring, machine learning inference for Module B, fusion scoring, report generation, the optional LLM rewriting call, and data access. However, routing to the correct exercise logic was not handled uniformly across both modules. Only Module B used a plugin registry, implemented in module_b/core/registry.py. Module A had no single generic dispatcher; instead, each of its three exercises, namely STS, SLS and WBLT, was handled by its own dedicated router, precisely because their result contracts differed from one another. Apart from that, the frontend had no direct access to the database at all, and all persistence was mediated through the backend.
 
**[FIGURE Y — `F3.6_web_app_architecture.mmd`, Mermaid source]**
*Figure Y: Web Application Architecture*
 
Last but not least, the two modules followed genuinely different processing paths rather than one uniform live-versus-after-set model. Module A maintained a real live backend round-trip: once per detected repetition boundary for STS, or once per completed leg for SLS and WBLT, the frontend called the same `/analyze` endpoint, gated by a `forceFinalize` threshold flag that distinguished an in-progress check, whose result was shown live but not persisted, from a completed one, whose result was persisted. In contrast, Module B made zero backend calls during the set itself. Everything shown live during a squat set, including the local repetition count and a client-side fault-gate preview, was a cosmetic estimate only, and the entire buffered set was posted once, at "Finish Set", to `/api/module-b/analyze`. This difference existed because Module A's per-check results were simple enough to compute and persist incrementally, whereas Module B's grading, which included segmentation, feature extraction, rule scoring, ML inference, fusion, and majority voting, was a single atomic computation over the whole set, so a partial result mid-set would not have been meaningful.
 
**[FIGURE Y2 — `F3.7_sequence_diagram.mmd`, Mermaid source]**
*Figure Y2: Sequence diagram showing Module A's per-rep/leg loop versus Module B's single after-set request*
 
#### 3.4.3.3 Application Pages and Database Design
 
Coming to the application pages and features, this project implemented eight broad categories of functionality. Account and profile covered registration and login using JWT-based authentication, together with a user profile capturing age, gender, height and weight, user type, and focus area. Exercise selection and guidance covered mode selection between Functional Checking and Rehab Grading, catalog-driven exercise selection across four exercises, a step-by-step instructions page before each exercise showing a demonstration clip, a camera-angle guide, and an equipment note, and a camera setup page with a live pose overlay and a body-visibility check that started automatically once framing became stable.
 
The exercise modules themselves were Module A, covering STS, SLS and WBLT through rule-based checking, and Module B, covering the squat exercise through a hybrid design that fused rule-based sub-scores with an Extra Trees classifier into a binary Good or Needs Improvement verdict. Live session feedback, shared across all four exercises, included a real-time skeleton overlay rendered from MediaPipe running in-browser, a repetition or hold counter, a recording indicator combining a visual and an audio cue, instant corrective pop-ups on faults, spoken coaching cues with a mute toggle, and an on-screen demonstration reference clip.
 
After a session ended, the post-session report presented the score, band and confidence, the rule-based sub-scores for range of motion, tempo and stability, error tags, coaching feedback that was either template-based or LLM-rewritten for the squat exercise, and glossary tooltips explaining technical terms. Progress tracking covered a filterable session history, a dashboard summarising recent sessions and common errors, and a progress deep-dive showing per-exercise trend charts. Reminders could be created and managed, exported to Google Calendar or as an `.ics` file, and surfaced as an in-app due alert. Last but not least, accessibility and trust features included a multi-language interface across English, Chinese and Malay, non-diagnostic disclaimers shown throughout the application, and privacy-by-design, since video never left the browser and only numeric landmarks were sent to the server.
 
Coming to the database design, nine tables supported this feature set. A `users` table held the core account record, while a separate `user_profiles` table, joined one-to-one, held the extended profile fields. An `exercise_catalog` table drove exercise selection directly from data rather than from hardcoded values, so a retired exercise could be excluded through an `is_active` flag without being deleted from the system. A `sessions` table recorded one row per attempt, linked to both the user and the exercise catalog, and also stored the session's capture-quality indicators. Two further tables, `module_a_results` and `module_b_results`, held each module's own grading output, since a single session could produce at most one of either. `module_b_error_tags` recorded Module B's error tags specifically, since Module A's warning tags were instead embedded as JSON within its own results table rather than normalised into a separate table. A `feedback_texts` table held both the structured and, where applicable, the LLM-rewritten feedback, together with the `feedback_source`, `llm_attempted` and `fallback_reason` fields described in Section 3.4.3.4. Lastly, a `reminders` table supported the reminder feature.
 
**[FIGURE Y3 — `F3.8_er_diagram.mmd`, Mermaid source]**
*Figure Y3: Entity relationship diagram*
 
For further clarity, both `module_a_results` and `module_b_results` stored their exercise-specific metrics inside a JSONB column, since the four exercises produced different shapes of result data, and a single fixed schema across all of them would not have been practical. Multilingual support was implemented using English, Chinese and Malay interface translations, with translation-key parity enforced by the type system to prevent a missing translation from being silently skipped.
 
#### 3.4.3.4 Feedback Generation Layer
 
Coming to the feedback generation layer, this project implemented an optional hosted large language model rewriting layer, rather than a Transformer built specifically for this project. A deterministic template was always generated first and used as the default feedback output. When the optional rewriting layer was enabled, its output replaced the template only after passing a safety filter, and only for the squat exercise under Module B; Module A's reports were never rewritten.
 
The rewriting layer called a third-party pre-trained model, Llama 3.3 70B, hosted through Groq, which was chosen over a comparable free-tier alternative on the basis of its policy against training on user data. Building a custom coaching-text generator was not pursued, since no labelled coaching-text dataset existed for this domain.
 
The safety filter rejected a rewritten response under five conditions: if it altered the band, altered the score, introduced an error tag that had not actually been detected, contained prohibited clinical language, or violated the required length or JSON format. If a response was rejected, or if the API call failed outright, the original deterministic template remained unchanged, so the user was never shown a broken or partial rewrite.
 
To track this behaviour, the system recorded three fields for every feedback record: `feedback_source`, `llm_attempted`, and `fallback_reason`. Together, these distinguished an LLM-disabled template, an accepted rewrite, and an attempted rewrite that fell back due to an API failure or a specific safety-filter rejection. Listing 1 shows the acceptance and fallback branch, and Listing 2 shows the specific checks performed inside the safety filter itself.
 
```python
# Listing 1 — acceptance and fallback-reason branch
safety = check_llm_feedback(result.text, structured=structured)
if safety.accepted:
    rewritten_text = result.text
    feedback_source = "llm"
    fallback_reason = "llm_used"
else:
    fallback_reason = f"guard_rejected:{safety.reason}"
```
 
```python
# Listing 2 — inside the safety filter itself
if _contradicts_band(lowered, structured.band):
    return SafetyCheckResult(False, "grade_mismatch_band")
if _contradicts_score(lowered, structured.score):
    return SafetyCheckResult(False, "grade_mismatch_score")
invented_tag = _find_invented_tag(lowered, structured)
if invented_tag is not None:
    return SafetyCheckResult(False, f"invented_tag:{invented_tag}")
return SafetyCheckResult(True)
```
 
Last but not least, the rewriting feature was disabled by default. Under the default configuration, no AI-rewritten text ever appeared in any report.
 
---
 
### 3.4.4 Tools and Technology Stack
 
Coming to the tools and technology stack, this section consolidates every library and platform used across Module A, Module B, and the web application into one place, closing this chapter before Section 3.5 covers where the system was deployed.
 
**A. Module A and Module B Development**
 
The AI pipeline relied on MediaPipe Tasks Vision for pose estimation, run entirely in the browser, together with custom Python and TypeScript functions for geometric processing, a custom rule engine for rule-based grading, and a custom finite-state machine for repetition segmentation. Model-specific tools were used only for Module B, including NumPy, scikit-learn, an Extra Trees classifier, and Joblib for model serialisation. Feedback was generated first through custom deterministic templates, with an optional rewriting step calling a Groq-hosted large language model behind a custom validation filter, as described in Section 3.4.3.4. Table 9a lists these tools in full.
 
*Table 9a: AI Pipeline Libraries and Tools*
 
| Component | Library / Tool | Used in | Purpose |
|---|---|---|---|
| Pose estimation | MediaPipe Tasks Vision Pose Landmarker | A and B | Extracts normalized pose landmarks and 3D world landmarks from webcam frames in the browser |
| Browser application | React and TypeScript | A and B | Handles webcam capture, MediaPipe execution, live quality checks, lightweight cues and landmark buffering |
| Geometric processing | Custom Python and TypeScript functions | A and B | Calculates joint angles, distances, movement timing, symmetry and stability measurements |
| Numerical processing | NumPy | B | Supports model inference and offline ML data processing, evaluation and numerical analysis |
| Confidence filtering | Custom visibility-based filtering | A and B | Detects unreliable landmarks using MediaPipe visibility values |
| Gap handling | Custom hold-last and interpolation functions | A and B | Module A holds the previous value during brief landmark loss; Module B also interpolates gaps of up to five frames |
| Smoothing | Custom One Euro Filter | A and B | Reduces landmark jitter while remaining responsive to movement |
| Feature extraction | Custom feature functions | A and B | Converts landmark sequences into interpretable movement metrics. Module B creates a 13-feature vector for each squat repetition |
| Repetition segmentation | Custom finite-state machine | A and B | Detects movement phases and separates complete repetitions using joint-angle thresholds and hysteresis |
| Rule-based grading | Custom rule engine | A and B | Produces Module A scores and bands; produces Module B ROM, tempo and stability sub-scores and fault gates |
| ML framework | Scikit-learn | B | Trains, validates, calibrates and executes the squat classification model |
| Primary classifier | Extra Trees Classifier | B | Learns non-linear relationships between the 13 features and binary Good/Poor labels |
| Probability calibration | Scikit-learn sigmoid calibration | B | Converts classifier output into calibrated `P(Good)` probabilities |
| Model serialisation | Joblib | B | Stores and loads the trained Extra Trees model and sigmoid calibrator |
| Error tags | Custom deterministic tag rules | B | Generates named issues from fault gates, movement rules, confidence and capture-quality flags |
| Feedback generation | Custom templates | B | Always produces structured, non-diagnostic coaching feedback from the grade and error tags |
| Optional rewriting | Groq-hosted LLM through HTTPX | B | Rewrites after-set feedback for clarity without changing the score, band or detected issues |
| Feedback safety | Custom validation filter | B | Rejects unsafe or inconsistent LLM responses and falls back to deterministic template feedback |
| Offline ML evaluation | Pandas, SciPy, Matplotlib and Seaborn | B | Supports dataset analysis, feature checks, statistical evaluation and training-report figures |
 
**B. Web Application Development**
 
The web application half of the stack was chosen to support session management, real-time feedback delivery, secure data storage, and dashboard-based progress tracking. The frontend was built using React and TypeScript, with Vite and Tailwind CSS for development and styling, React Router for navigation, i18next for the three-language interface, and Recharts and Framer Motion for charts and animation. The backend used Python, FastAPI and Pydantic, connected to PostgreSQL through SQLAlchemy and Alembic. Authentication relied on OAuth2 bearer tokens, PyJWT and bcrypt. Testing used Vitest and React Testing Library on the frontend and Python's `unittest` on the backend. Table 9b lists these tools in full.
 
*Table 9b: Web Application Technology Stack*
 
| Layer | Technology / Tools | Purpose |
|---|---|---|
| Frontend | React and TypeScript | Builds the browser-based user interface for exercise selection, guided sessions, reports and dashboards |
| Frontend build and styling | Vite and Tailwind CSS | Provides frontend development, production builds and responsive interface styling |
| Frontend navigation | React Router | Handles navigation between authentication, exercise, live-session, report and progress pages |
| Localisation | i18next and React-i18next | Provides English, Malay and Chinese interface translations |
| Charts and animation | Recharts and Framer Motion | Displays progress charts and supports interface animations and transitions |
| Browser platform | HTML5, MediaDevices API and Canvas API | Provides webcam access, video display and pose-overlay rendering in the browser |
| Backend | Python, FastAPI, Uvicorn and Pydantic | Implements the REST API, request validation, session management and processing endpoints |
| API layer | FastAPI and Pydantic | Validates analysis requests and connects the frontend with the backend processing pipelines used by both Module A and Module B |
| Database | PostgreSQL | Stores users, exercises, sessions, results, metrics, tags, feedback and historical data |
| Database access | SQLAlchemy and Psycopg | Connects the Python backend to PostgreSQL and performs database operations |
| Database migration | Alembic | Manages version-controlled database schema changes |
| Authentication and security | OAuth2 bearer tokens, PyJWT and bcrypt | Handles login authentication, access tokens and secure password hashing |
| API communication | REST and JSON | Transfers session data, pose landmarks and analysis results between the frontend and backend |
| Frontend testing | Vitest and React Testing Library | Tests frontend utilities, components and user-interface behaviour |
| Backend testing | Python `unittest` | Tests backend processing, API behaviour, persistence and grading logic |
| User evaluation | Google Forms | Collects structured participant feedback during user testing |
| Supporting design tools | Canva, Draw.io and/or Visual Paradigm | Creates report graphics, prototypes and system diagrams, where applicable |
 
It should be noted that PostgreSQL, SQLAlchemy, Alembic, FastAPI and Pydantic served both the AI pipeline in Table 9a and the general web application in Table 9b equally, so these shared tools are listed once each rather than duplicated across both tables.
 
---