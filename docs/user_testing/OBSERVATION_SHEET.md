# PhysioSense User-Testing — Observation Sheet

**Print one per participant.** This records the **objective** measures your proposal (§3.7) promised — task completion rate, time-on-task, and whether users self-correct after a camera-guidance prompt. The questionnaire only captures opinions; this sheet captures behaviour. Submitting only questionnaire results would leave the promised measures unevidenced.

---

## Participant details

| Field | Value |
| --- | --- |
| Participant ID (e.g. P01) | |
| Date / start time | |
| Age band | |
| Prior fitness-app user? (Y/N) | |
| Prior rehab/physio experience? (Y/N) | |
| Laptop / browser used | |
| Room lighting (good / fair / poor) | |
| Consented to photos? (Y/N) | |

---

## What "time-on-task" means

**Time-on-task** = the number of seconds from the moment you *finish reading the task instruction* to the moment the participant *reaches the task's goal* (or gives up).

Start the stopwatch the instant you stop speaking; stop it the instant the goal state appears on screen. Do not include your explanation time, and do not include the physical exercise duration for tasks where the exercise itself has a fixed length — for those, time only the **navigation and setup** portion (i.e. stop the timer when the live session begins, and note the exercise outcome separately).

**Why it matters:** it is an objective usability signal a rating scale cannot give you. If a participant rates "navigation was easy" as 4/5 but took 3 minutes to find the Progress page, the number reveals a discoverability problem the rating hides. Report it as median seconds per task, with the range.

**Completion status** — score every task as exactly one of:
- **U = Success unaided** — completed with no help from you
- **A = Success with assistance** — completed, but you gave a hint or intervened
- **F = Failed / abandoned** — did not reach the goal

**Task completion rate** = (number of U) ÷ (total tasks) × 100%. Report the unaided rate as the headline; report U+A as the secondary figure.

---

## Part A — Core tasks

| # | Task | Time (s) | U / A / F | Errors or wrong turns (count) | Notes — confusion points, exact quotes |
| --- | --- | --- | --- | --- | --- |
| 1 | Create account and sign in | | | | |
| 2 | Explain what the system does + is it medical? | — | | | **Record their exact words about "medical/diagnosis":** |
| 3 | Sit-to-Stand (Module A) | | | | |
| 4 | Single-Leg Stance, both legs | | | | |
| 5 | Weight-Bearing Lunge Test | | | | |
| 6 | Squat (Module B) | | | | |
| 7 | Find and reopen a past session | | | | |
| 8 | Find progress / squat trend | | | | |
| 9 | Create a reminder + add to calendar | | | | |
| 10 | Start exercise from the reminder | | | | |

---

## System-behaviour counts (fill in as they happen)

| Measure | Count | Notes |
| --- | --- | --- |
| Capture-quality / visibility warnings shown | | |
| **Times the participant self-corrected their position after a warning** ⭐ | | ⭐ *This directly evidences the proposal's §3.7 promise to "observe whether they can alter their adjustment after being prompted with camera setup guidance"* |
| Times a warning was shown but **ignored** | | |
| Squat reps rejected by a fault gate | | Which faults? |
| Sit-to-Stand reps not counted | | |
| Times the participant asked you for help | | |
| Crashes, blank screens, or console errors | | |
| Times the participant misread a result | | e.g. thought "Needs Improvement" meant injury |

---

## Part B — Error scenarios

Record only the ones this participant performed.

| # | Scenario | System behaved as expected? (Y/N) | What actually happened |
| --- | --- | --- | --- |
| E1 | Shallow squat → depth fault | | |
| E2 | Forward lean → lean fault | | |
| E3 | Heels lifting → heel fault | | |
| E4 | Inconsistent tempo | | |
| E5 | Partially out of frame | | |
| E6 | Inactivity (stand still 9s) | | |
| E7 | Facing camera front-on | | |
| E8 | Rep goal of 10 | | |
| E9 | STS — not standing fully | | |
| E10 | STS — half sit | | |
| E11 | STS — step out of frame | | |
| E12 | SLS — foot lifted too low | | |
| E13 | SLS — early foot drop | | |
| E14 | SLS — heavy sway | | |
| E15 | WBLT — heel lift during hold | | |
| E16 | WBLT — wrong orientation | | |
| E17 | WBLT — implausible distance (99 cm) | | |
| E18 | Wrong password | | |
| E19 | Duplicate email | | |
| E20 | Invalid email format | | |
| E21 | Direct URL while logged out | | |
| E22 | Camera permission blocked | | |
| E23 | Browser back mid-session | | |
| E24 | Refresh mid-session | | |
| E25 | Empty reminder title | | |
| E26 | Language switch en/zh/ms | | |
| E27 | Light / dark theme | | |
| E28 | Narrow (mobile) width | | |
| E29 | Data still present on re-login | | |

---

## Post-session notes

**Three things that clearly worked well:**
1.
2.
3.

**Three things that clearly caused difficulty:**
1.
2.
3.

**Any safety concern observed** (loss of balance, discomfort, participant stopping early):

**Any statement suggesting the participant believed the system was giving medical advice** *(critical — quote verbatim)*:

**Verbal comments made during the session that they may not repeat in the form:**

**Tester's overall impression (1–2 sentences):**

---

## After every session — housekeeping

- [ ] Participant submitted the Google Form
- [ ] Observation sheet complete and labelled with the participant ID
- [ ] Any test account/data noted (decide in advance whether you keep or delete participant accounts — keep them if you want to demonstrate data persistence, but say so in the consent form)
- [ ] Camera permission reset for the next participant
- [ ] Room reset (chair, ruler, floor markers)

---

## Summary table (fill in after all participants)

| Participant | Tasks unaided (U) | Tasks assisted (A) | Tasks failed (F) | Unaided completion rate | Total session time |
| --- | --- | --- | --- | --- | --- |
| P01 | | | | | |
| P02 | | | | | |
| P03 | | | | | |
| P04 | | | | | |
| P05 | | | | | |
| P06 | | | | | |
| P07 | | | | | |
| P08 | | | | | |
| P09 | | | | | |
| P10 | | | | | |
| **Median** | | | | | |

**Per-task median time (seconds)** — this table is what goes into your results chapter:

| Task | Median time (s) | Range (s) | Unaided rate (%) |
| --- | --- | --- | --- |
| 1 Account creation | | | |
| 3 Sit-to-Stand | | | |
| 4 Single-Leg Stance | | | |
| 5 WBLT | | | |
| 6 Squat | | | |
| 7 Session history | | | |
| 8 Progress page | | | |
| 9 Create reminder | | | |
| 10 Reminder deep-link | | | |
