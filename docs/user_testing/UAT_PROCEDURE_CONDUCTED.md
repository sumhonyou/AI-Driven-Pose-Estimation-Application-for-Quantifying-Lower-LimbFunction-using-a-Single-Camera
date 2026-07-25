# User Acceptance Testing — Procedure as Conducted

This document records **what was actually done** for user acceptance testing, as a factual
basis for Chapter 3 (Methodology → Evaluation and Testing) and Chapter 4 (Results →
User Acceptance Testing). It is a companion to, and supersedes where they differ, the
earlier planning documents `TESTING_PROTOCOL.md` and `SCENARIO_TASKS.md` in this folder
— those describe the intended design; this describes the session as it was run.

`dates the sessions were conducted: 2026-07-18 to 2026-07-23`

`a quiet and spacious room and use my laptop to test on everyone`

---



## 1. Overview

Testing was conducted as a **moderated, in-person, one-on-one usability evaluation** with
**21 participants**. Each session combined two independent evidence streams so that
findings could be triangulated rather than relying on self-report alone:

1. **Structured self-report** — a Google Form questionnaire completed by the participant
  at the end of the session, capturing their own rating of and reaction to the system.
2. **Direct behavioural observation** — the researcher observed each participant working
  through the tasks in real time and took written notes on how they actually interacted
   with the application: where they hesitated, what they clicked first, what they
   misread, what surprised them, and what they said aloud.

Running both in-person and one-on-one (rather than, say, an unmoderated remote survey)
was a deliberate choice: it is the only way to capture the behavioural stream at all, and
it let genuine safety supervision happen during the physical exercises (Sit-to-Stand,
Single-Leg Stance, WBLT, Squat), which matters for a lower-limb movement application.

## 2. Participants

- **N = 21**, tested individually (not in groups), one session per participant.
- `Participants include my university coursemate and friends, my family members`
- `majority did not have the rehab experience and used any exercise guidance application but a few of participants have.`



## 3. Session Procedure

Every participant went through the same sequence, in this order:

1. **Briefing.** The researcher explained, in plain language, what the project is and
  what it is for — a webcam-based lower-limb functional self-check and rehabilitation
   exercise-grading web application — before any task began, so participants approached
   the tasks with the same baseline understanding of the system's purpose.
2. **Ten guided tasks** (below), completed in order, with the researcher observing and
  taking notes throughout.
3. **Questionnaire.** Participants completed the Google Form independently.
4. **Observation notes** were written up by the researcher immediately after each
  session while still fresh, rather than relying on memory later.

`Read task instruction in a script` 

### The ten tasks


| #   | Task given to the participant                                                                                                                    | What it evaluates                                                                                                                                                                                          |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Read the home page, then explain in their own words what the system does — including whether they understood it is **not** for medical diagnosis | First impression / information architecture of the landing page; whether the **non-diagnostic disclaimer** actually registers with a first-time user — a safety-relevant finding, not just a usability one |
| 2   | Create a new account                                                                                                                             | Sign-up flow: field clarity, validation, time to reach the dashboard                                                                                                                                       |
| 3   | Explore and explain the dashboard                                                                                                                | Whether the dashboard's layout and labelling are self-explanatory without guidance                                                                                                                         |
| 4   | Complete the Sit-to-Stand exercise                                                                                                               | Module A functional check: camera setup guidance, live feedback, understanding of the completion report                                                                                                    |
| 5   | Complete the Supported Single-Leg Stance exercise                                                                                                | Module A: the lift-line/hold mechanic, the stability indicator, per-leg reporting                                                                                                                          |
| 6   | Complete the Weight-Bearing Lunge Test                                                                                                           | Module A: the stricter camera-positioning gate, and the self-measured-distance step                                                                                                                        |
| 7   | Complete the Squat exercise                                                                                                                      | Module B hybrid grading: live corrective feedback, the Good/Needs-Improvement band, error-tag explanations                                                                                                 |
| 8   | View session history and open a specific past record                                                                                             | Whether users can locate and re-open a prior result                                                                                                                                                        |
| 9   | Explore whether the progress trend is understandable                                                                                             | Whether the dashboard/progress charts communicate change over time in a way a first-time user can read                                                                                                     |
| 10  | Add a new reminder, then add it to Google Calendar (or another calendar)                                                                         | The reminder feature end-to-end, including the external calendar hand-off                                                                                                                                  |


`the researcher did not physically demonstrated each exercise movement beforehand for safety, it fully let user to explore and test around the web application.`

## 4. What Was Recorded

For each participant and task, the researcher's observation notes captured:

- Whether the task was completed unaided, completed with the researcher's help, or not
completed.
- Points of hesitation or confusion — what the participant looked at, clicked, or asked
about before proceeding.
- Verbatim or near-verbatim comments made while working through the task.
- Any safety-relevant reaction — e.g. anyone who described the system as diagnosing a
medical condition (Task 1), or any physical discomfort during an exercise task.

`2–4 concrete examples pulled from your actual notes`

`Example: `  
`1. single leg stance: the user do not know what is the purpose of the ball, try to add teh instruction, and teh ball can make in the centre.` 

`2. User show the wrong side of the body to camera when conducting the session.` 

`3. User tend to watch demo video instead of reading the instruction`

`4. User did not know it need chair as equipment to complete the session.`  

## 5. Why This Method

Moderated one-on-one testing with a combined questionnaire-plus-observation design was
chosen over an unmoderated or survey-only approach for three reasons:

1. **Self-report alone under-reports usability problems.** Participants can complete a
  task with visible hesitation or a wrong turn and still rate it favourably afterward
   (social-desirability bias); direct observation catches this gap.
2. **Safety.** The physical exercise tasks (Sit-to-Stand, Single-Leg Stance, WBLT,
  Squat) involve real movement; being physically present allowed the researcher to
   intervene if a participant showed signs of discomfort or instability.
3. **The non-diagnostic boundary is a safety requirement, not just a UX detail** (§6 of
  the implementation plan). Task 1 was placed first and phrased to test comprehension
   directly, because a user who believes a webcam self-check is a medical diagnosis is
   a genuine risk the evaluation needed to check for, not an incidental finding.



## 6. Where This Feeds Into the Report

- **Chapter 3 (Methodology → 3.6.5 User Acceptance Testing Design):** this document's
§1–§3 and §5, rewritten in past tense as the evaluation method.
- **Chapter 4 (Results → 4.7 User Acceptance Testing):**
- **Chapter 5 (Limitations):** state the sample honestly — convenience sample, N=21,
single-session (so the Progress-trend task, #9, evaluates perceived rather than
actual longitudinal usefulness), and any recruitment skew noted in §2.

> **Before finalising:** reconcile the participant count above with any other number
> already used elsewhere in the report or supporting docs — an earlier project note
> refers to "22 participants / 21 questionnaires" (one participant with no submitted
> form). If that is the same testing round, state it consistently everywhere as
> **N = 22 tested, 21 questionnaires returned** rather than switching between 21 and 22.
> If this is a different, later round, say so explicitly instead of leaving the
> discrepancy unexplained.

