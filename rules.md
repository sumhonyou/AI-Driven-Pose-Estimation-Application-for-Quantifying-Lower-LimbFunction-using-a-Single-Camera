# Coding Agent Rules

The AI coding agent must follow these rules strictly on every request and modification.

1. Do not build a mobile app.
2. Do not store raw videos by default.
3. Do not make medical diagnosis claims.
4. Do not hardcode secrets or API keys.
5. Use PostgreSQL as the main database.
6. Use FastAPI as the backend framework.
7. Use React + TypeScript + Tailwind for frontend.
8. Run MediaPipe Pose in browser.
9. Prioritize a working local full-stack system before deployment.
10. Prioritize Module B rehab grading if time becomes limited, but keep Module A structure with 3 checks.
11. Keep the Module B exercise configurable because the exact exercise will be decided later.
12. Use External LLM API only after-set and only for rewriting structured feedback.
13. Always include fallback feedback if LLM API fails.
14. Store derived metrics, session results, error tags, and feedback text in PostgreSQL.
15. Write clean code with clear module separation.
16. Add API documentation through FastAPI Swagger.
17. Keep UI simple, clear, and suitable for non-technical users.
18. Add safety disclaimers in the UI and report.
19. Do not add too much unnecessary code; just execute what requirements are asked for.
20. After completing work, report to the user what was done or modified (files changed, features added, how to run or test).
21. Always show to-do list progress when executing the task
22. Always put simple and straightforward comment on the code, so it easier for me to refer what it does. but do not add too many of comments.
23. Put console message on the output, so that easier for me to find bug and track. But do not put too many, put on those important process like connection, output, and etc.
24. Every time code changes or is generated, run it through Prettier formatting to ensure consistent code style (frontend files: .js, .jsx, .ts, .tsx, .css, .json, .md; backend: use Black + isort for Python).
25. Remember these rules whenever starting to execute a request or making any modification.

**Most importantly:** Do not assume clear goals and instructions — ask questions for clarity when needed.

---

## Frontend Design Rules

**Apply these rules only when the user asks for designing webpages or UI.**

### Always Do First

- **Invoke the `frontend-design` skill** before writing any frontend code, every session, no exceptions.

### Reference Images

- If a reference image is provided: match layout, spacing, typography, and color exactly. Swap in placeholder content (images via https://placeholder.co/, generic copy). Do not improve or add to the design.
- If no reference image: design from scratch with high craft (see guardrails below).
- Screenshot your output, compare against reference, fix mismatches, re-screenshot. Do at least 2 comparison rounds. Stop only when no visible differences remain or user says so.
