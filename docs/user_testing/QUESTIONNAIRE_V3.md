# PhysioSense User-Testing Questionnaire — Version 3 (revised against the as-built system)

**Revised:** 2026-07-20
**Constraint respected:** exactly **30 questions**, only **1 open-ended** question (Q30), everything else rating or option.
**Basis:** the as-built system described in `FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md`, verified against the frontend code, plus the functional/non-functional requirements in the proposal (Table 8, §3.4.3.1).

---

## What changed from Version 2, and why

| Change | Reason |
| --- | --- |
| **New Section 4 — "Live Feedback During the Movement" (2 questions)** | The code audit confirmed the system **does** deliver rich real-time feedback (live joint angles, depth gauge, rep-validity with named fault reasons, stability gauge, hold timer). This directly evidences the proposal's functional requirement *"The system must display real-time feedback to the user during performance"* and the non-functional requirement *"real-time feedback with minimal delay to support effective motor learning."* V2 had only one vague "real-time feedback was useful" item. |
| Old Q22 "The real-time feedback was useful…" **rewritten and split** | The old wording never told the participant *what* the live feedback was, so ratings would have been noise. The new items name the actual on-screen elements. |
| **Added Session History question (Q24)** | Proposal FR: *"Users are able to view a list of their past completed sessions."* V2 had **no** question covering this requirement. |
| **Added Reminders question (Q26)** | Proposal FR: *"Users can schedule automated reminders for future rehabilitation."* V2 had **no** question covering this whole feature (real CRUD + Google Calendar + `.ics` export, built in Phase 7). |
| Merged old Q6 + Q10 (interface design / buttons-icons) into **Q9** | They measured nearly the same thing; merging freed a slot without losing signal. |
| Merged old Q7 + Q8 (navigation / mode selection) into **Q10** | Mode selection is a subset of navigation. |
| Removed old Q15 and Q21 ("which output was most useful") | The per-output Likerts in Sections 5–6 let you **rank outputs by mean score**, which is finer-grained than a single-select. Q28/Q29 already capture component-level prioritisation. |
| Q1 age band "55–59" → **"55 or above"** | Cleaner. Older adults are deliberately **out of scope** for this round (documented as a limitation and future work), but the band is kept so the real sample distribution is reported honestly. |
| Error-tag question (Q22) now names the **real tags** | The live/report tags are `insufficient_depth`, `excessive_forward_lean`, `heel_lift` — naming them makes the question answerable. |

---

## Section 1: Basic Participant Background (Q1–Q4)

**Q1. Age (years old)** — *Mark only one oval*
- 18–24
- 25–34
- 35–44
- 45–54
- 55 or above

**Q2. Do you currently or previously experience knee or ankle discomfort?** — *Mark only one oval*
- No
- Yes, knee discomfort
- Yes, ankle discomfort
- Yes, both knee and ankle discomfort
- Prefer not to say

**Q3. Have you used any fitness, health tracking, physiotherapy, or exercise guidance application before?** — *Mark only one oval*
- Yes
- No
- Not sure

**Q4. Do you have experience with rehabilitation exercises or physiotherapy exercises?** — *Mark only one oval*
- Yes
- No

---

## Section 2: Safety and Setup Experience (Q5–Q8)

*(1 = Strongly disagree, 5 = Strongly agree)*

**Q5.** The movement instructions were clear before I started each exercise.

**Q6.** When the system warned about camera placement or capture quality, the guidance helped me fix my position.

**Q7.** I felt physically safe while performing the movements.

**Q8. Did you experience any discomfort while testing the prototype?** — *Mark only one oval*
- No discomfort
- Mild discomfort
- Moderate discomfort
- Strong discomfort
- Prefer not to say

---

## Section 3: UI / UX and Website Usability (Q9–Q12)

*(1 = Strongly disagree, 5 = Strongly agree)*

**Q9.** The overall interface design was clean, and the buttons, labels and icons were easy to understand.

**Q10.** Navigating between pages, modes (Functional Checking / Rehab Grading), and exercises was easy to follow.

**Q11.** It was easy to start, perform, and complete an exercise session.

**Q12.** The system felt smooth and responsive during testing.

---

## Section 4: Live Feedback During the Movement (Q13–Q14)

> **Note to include in the Google Form section description:** *"These questions are about what the system showed you on screen **while you were still performing the movement** — for example the repetition counter, the live knee-angle / depth gauge, the hold timer and stability gauge, and the message shown when a repetition did not count."*

*(1 = Strongly disagree, 5 = Strongly agree)*

**Q13.** The live on-screen feedback during the movement (repetition count, live angle/depth gauge, hold timer, and the reason shown when a repetition did not count) was easy to understand while I was moving.

**Q14.** The live feedback helped me adjust or correct my movement during the exercise.

---

## Section 5: Module A — Functional Checking (Q15–Q16)

*(Sit-to-Stand, Single-Leg Stance, Weight-Bearing Lunge Test)*

*(1 = Strongly disagree, 5 = Strongly agree)*

**Q15.** The Module A result (Good / Fair / Poor band) was easy to understand.

**Q16.** The Module A session summary helped me understand my lower-limb functional performance.

---

## Section 6: Module B — Rehabilitation Grading (Squat) (Q17–Q20)

*(1 = Strongly disagree, 5 = Strongly agree)*

**Q17.** The Module B grading result was easy to understand.

**Q18.** The score, quality label, and Good / Needs Improvement band were useful for understanding my exercise performance.

**Q19.** The confidence score helped me understand how certain the system was about the result.

**Q20.** The improvement cues shown in the report (for example: not deep enough, leaning too far forward, heels lifting off the floor) were useful for knowing which part of my movement to improve.

---

## Section 7: Report, History, Progress and Reminders (Q21–Q24)

*(1 = Strongly disagree, 5 = Strongly agree)*

**Q21.** The post-performance report was clear and useful after completing the session.

**Q22.** I could easily find and review my past sessions in the Session History page.

**Q23.** The dashboard and progress charts would be useful to me if I repeated these tests over time.

**Q24.** The reminder feature (scheduling a reminder and adding it to my calendar) would help me keep up with regular exercise.

---

## Section 8: Trust and Overall Evaluation (Q25–Q30)

**Q25.** *(1–5)* The system made it clear that the results are for general self-monitoring only and should not be treated as medical advice.

**Q26.** *(1–5)* Overall, I am satisfied with the prototype.

**Q27. Which part of the system was the strongest?** — *Check all that apply*
- UI / UX design
- Camera setup guidance
- Movement instructions
- Live feedback during the movement
- Module A Functional Checking
- Module B Rehab Grading
- Post-performance report
- Session history
- Dashboard / progress tracking
- Reminder feature
- Non-diagnostic explanation
- Other: ______

**Q28. Which part of the system needs the most improvement?** — *Check all that apply*
- UI / UX design
- Camera setup guidance
- Movement instructions
- Live feedback during the movement
- Module A Functional Checking
- Module B Rehab Grading
- Post-performance report
- Session history
- Dashboard / progress tracking
- Reminder feature
- System speed / responsiveness
- Result explanation
- Other: ______

**Q29. Would you consider using this type of system for basic lower-limb self-monitoring at home?** — *Mark only one oval*
- Yes
- No
- Maybe

**Q30. Do you have any other comments or suggestions for improvement?** — *Long answer, optional*

---

## Coverage check against the proposal's requirements (Table 8)

| Proposal requirement | Covered by |
| --- | --- |
| FR — Create accounts and authenticate securely | Observation sheet (Task 1) — deliberately not a survey item; failures surface in Q28 / Q30 |
| FR — Choose between Functional Check and Rehab Grading | Q10 |
| FR — Select exercise, guided with instructions | Q5, Q10 |
| FR — Visual guides for camera alignment and distance | Q6 |
| FR — Manually control initiation / termination of session | Q11 |
| FR — **Display real-time feedback during performance** | **Q13, Q14** (Section 4) |
| FR — View list of past completed sessions | **Q22** |
| FR — Generate post-performance report | Q21, plus Q15–Q20 |
| FR — Visualise progress trends | Q23 |
| FR — Schedule automated reminders | **Q24** |
| NFR — Real-time feedback with minimal delay (motor learning) | Q12 (responsiveness) + Q14 (did it help you adjust) |
| NFR — UI easy to access and use | Q9, Q10, Q11 |
| NFR — Data protected and stored reliably | Observation sheet (data persisted across sessions); not a user-perceivable survey item |
| Non-diagnostic boundary (§6) | Q25 |

---

## How to analyse the results

1. **Component satisfaction ranking** — mean of each Likert, grouped by section. Any item with mean < 3.5 is a weak point; < 3.0 is a priority fix.
2. **Priority fix list** — count Q28 selections, descending. Cross-check against the low-mean items from step 1; anything appearing in both is your top improvement.
3. **What users value** — count Q27 selections; also compare the means within Section 6 (score/band vs confidence vs improvement cues) to see which Module B output carries the most perceived value.
4. **Headline metrics for the report** — Q26 (overall satisfaction mean), Q29 (% Yes / Maybe / No adoption intent), Q7 + Q8 (safety evidence).
5. **Qualitative** — code Q30 free-text into themes; pair with the confusion points recorded on the observation sheets.
6. **Segment analysis** — split by Q3 (prior app experience) and Q4 (prior rehab experience) to see whether comprehension items (Q13, Q15, Q17, Q19) differ by background. With N=10 report this descriptively, **not** as a significance test.
