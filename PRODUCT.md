# Product

## Register

product

## Platform

web

## Users

PhysioFit is primarily for home users who want guided lower-limb movement checks and rehabilitation exercise feedback through an ordinary webcam. The default audience includes general users, athletes, and older adults, with extra care for older adults who may need larger text, clearer steps, calmer pacing, and low cognitive load.

Users are usually in a practical self-check workflow: sign in, choose a mode, prepare their camera, complete a guided movement session, and review conservative feedback they can track over time.

## Product Purpose

PhysioFit turns a single browser camera into a non-diagnostic movement-quality tool for lower-limb functional checking and rehabilitation grading. It uses in-browser MediaPipe Pose, a FastAPI backend, and PostgreSQL persistence to guide sessions, calculate derived metrics, save results, and show reports/history.

Success means a home user can complete a session without technical confusion, understand Good/Fair/Poor movement-quality feedback, and review progress without the interface implying diagnosis, treatment, medical clearance, or return-to-sport decisions.

## Positioning

Clear single-camera movement feedback for home users, with conservative lower-limb scoring that is understandable without being clinical diagnosis.

## Brand Personality

Calm, clear, and trustworthy. The voice should feel supportive and practical: confident enough to guide movement, careful enough to avoid medical overclaiming, and simple enough for non-technical users.

## Anti-references

Avoid diagnostic, hospital-heavy, or medical-authority presentation that makes the app feel like a clinician replacement. Avoid aggressive sports-performance language that sidelines older adults or general home users. Avoid decorative complexity, vague AI spectacle, and motion or visual effects that distract from the guided task.

## Design Principles

1. **Guide the next safe action.** Every screen should make the next step obvious, especially camera setup, live sessions, and reports.
2. **Conservative confidence over clinical certainty.** Feedback should explain movement quality and capture quality without diagnosis, prescription, or clearance claims.
3. **Readable first, polished second.** Typography, contrast, spacing, and controls must support older adults and non-technical users before adding visual flair.
4. **Use the webcam story directly.** The interface should keep the single-camera pose-estimation flow visible and concrete, not abstract or overly promotional.
5. **Keep state and feedback consistent.** Good/Fair/Poor bands, capture-quality warnings, errors, loading, and saved-session states should use one predictable visual language across pages.

## Accessibility & Inclusion

No formal WCAG target has been specified yet. The project already supports responsive web layouts, light/dark theme, text-size controls, multilingual UI, visible focus states, and reduced-motion handling. Future design work should continue prioritizing high contrast, large touch targets, plain-language labels, reduced-motion alternatives, and error/help text that older adults can understand without technical knowledge.
