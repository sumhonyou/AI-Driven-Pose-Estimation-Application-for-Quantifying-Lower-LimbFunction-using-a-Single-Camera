# PhysioSense User-Testing — Scenario Tasks and Error-Testing Script

**Purpose:** every participant performs **every feature and every exercise**, so the questionnaire is answered from real experience rather than assumption.
**Basis:** the functional and non-functional requirements in the proposal (Table 8, §3.4.3.1), mapped to the as-built system.

---

## Before the participant arrives — setup checklist

**Physical space**
- [ ] Clear floor area approx. **2 m × 2 m**, with room to stand ~2–2.5 m from the laptop
- [ ] A **stable chair without armrests** (for Sit-to-Stand)
- [ ] A **clear wall** and a **ruler or tape measure** (for the Weight-Bearing Lunge Test's self-measured distance)
- [ ] Even lighting, participant not backlit by a window
- [ ] Plain background if possible

**System**
- [ ] Backend running and reachable; database up
- [ ] Frontend running; test one full session yourself before the first participant
- [ ] Browser: use the **same browser and laptop for every participant** (keeps time-on-task comparable)
- [ ] Camera permission **reset** before each participant (so Task 3's permission prompt is genuine)
- [ ] A fresh, unused email available for the participant to register with

**Paperwork**
- [ ] Printed consent form (with the photo/video opt-in — see the protocol document)
- [ ] Printed observation sheet, one per participant
- [ ] Stopwatch or phone timer
- [ ] Google Form open on a second device or tab

---

## How to run the tasks

- Read each scenario **aloud, exactly as written**, then stop talking.
- Start the timer when you finish reading. Stop it when the participant reaches the task goal or gives up.
- **Do not help** unless they are stuck for more than ~2 minutes or there is a safety concern. If you do help, record it — that task counts as *"Success with assistance"*, not *"Success unaided"*.
- Ask them to **think aloud** ("please say what you're looking for / what you expect to happen").
- **Demonstrate the physical movement** yourself for safety before each exercise. **Do not demonstrate the user interface** — the UI is what you are testing.

---

# Part A — Core Task Scenarios (all participants)

### Task 1 — Create an account and sign in
> *"You have just heard about PhysioSense and want to try it. Starting from the home page, create a new account for yourself and sign in."*

- **Covers FR:** create accounts and authenticate securely
- **Success:** reaches the dashboard, logged in
- **Watch for:** confusion over required profile fields, password rules, whether they notice the non-diagnostic disclaimer on the landing page

### Task 2 — Understand what the system is for
> *"Before exercising, have a look around the site. In your own words, tell me what this system does, and whether it can tell you if you have a medical problem."*

- **Covers:** non-diagnostic boundary (§6), NFR "UI easy to access and use"
- **Success:** describes it as movement-quality self-checking, and states it is **not** medical advice/diagnosis
- **Watch for:** anyone who believes it is diagnosing them — this is a **safety-critical finding**, record the exact wording they use

### Task 3 — Sit-to-Stand (Module A)
> *"You want to check your lower-limb function. Choose the Functional Checking mode, select the Sit-to-Stand test, set up your camera as the system guides you, and complete the test."*

- **Covers FR:** mode selection, exercise selection with instructions, camera alignment guides, manual session start/stop, real-time feedback, post-performance report
- **Success:** completes 5 valid reps and reaches the report page
- **Watch for:** does the camera-permission prompt confuse them? Do they read the side-view guidance? Do they react to the live knee-angle readout and the "rep not counted" reasons? Do they understand the Good/Fair/Poor band on the report?

### Task 4 — Single-Leg Stance (Module A)
> *"Now do the Single-Leg Stance test for **both** legs, and tell me what your result means."*

- **Covers FR:** exercise selection, real-time feedback, report
- **Success:** completes both legs, reaches the per-leg result
- **Watch for:** do they understand the **lift-line** (that timing only starts once the foot is high enough)? Do they notice and react to the **ball-in-circle stability gauge**? Do they understand the combo score is not a clinical score?

### Task 5 — Weight-Bearing Lunge Test (Module A)
> *"Now do the Weight-Bearing Lunge Test. Follow the on-screen guidance, including measuring and entering the distance it asks for."*

- **Covers FR:** camera alignment guides (this exercise has the strictest positioning gate), real-time feedback, report
- **Success:** completes at least one attempt per leg and enters a self-measured distance
- **Watch for:** can they position themselves to satisfy the positioning gate unaided? Do they understand **why** they must measure with a ruler (that the camera cannot do it)? Does the heel-lift detection ending the attempt surprise them?

### Task 6 — Squat (Module B — Rehab Grading)
> *"Now switch to the Rehab Grading mode and do a set of squats. Do about 6 to 8 repetitions with the best form you can, then finish the set and look at your result."*

- **Covers FR:** mode selection, real-time feedback, manual session termination ("Finish Set"), post-performance report
- **Success:** completes a set, presses Finish Set, reaches the report
- **Watch for:** do they use the **live depth gauge** to adjust? Do they understand **Good / Needs Improvement**? Do they understand the **confidence score**? Do they notice the improvement cues (error tags)? Do they find the "Finish Set" button, or expect it to auto-stop?

### Task 7 — Review past sessions
> *"You want to look back at the tests you did today. Find a list of your past sessions and open the report for your Sit-to-Stand test again."*

- **Covers FR:** view a list of past completed sessions
- **Success:** finds Session History, opens the correct past report
- **Watch for:** do they try the filters? Can they tell Module A from Module B sessions in the list?

### Task 8 — Check progress
> *"You want to see whether you are improving over time. Find the part of the system that shows your progress, and look at your squat results specifically."*

- **Covers FR:** visualise progress trends
- **Success:** reaches the Dashboard and/or the Progress page, selects the Rehab Grading category and Squat
- **Watch for:** do they find the **Progress** page in the sidebar, or stop at the Dashboard? Do they understand the category tabs (Functional Checking / Rehab Grading)? Do they try the 14d/30d/All range control? Do they interpret the Good/Fair/Poor band zones on the chart correctly?

### Task 9 — Schedule a reminder
> *"You want to be reminded to do this exercise again. Set up a reminder for your squat exercise for tomorrow morning, and add it to your own calendar."*

- **Covers FR:** schedule automated reminders
- **Success:** creates a reminder with an exercise attached, and uses either the Google Calendar link or the `.ics` download
- **Watch for:** do they find the reminders page? Do they understand the frequency options (once / daily / MWF / weekly)? Do they discover that **clicking a reminder jumps straight into that exercise**?

### Task 10 — Use a reminder as a shortcut
> *"Using the reminder you just created, start that exercise directly from it."*

- **Covers:** the reminder deep-link
- **Success:** clicking the reminder card lands on camera setup with the correct exercise and mode pre-selected
- **Watch for:** whether they realise the card itself is clickable

---

# Part B — Error and Edge-Case Testing

These are **deliberate** failure scenarios. Introduce them as *"now I'd like you to do this deliberately wrong, so we can see how the system reacts."* Participants find this reassuring rather than alarming — it makes clear the fault is intended.

## B1 — Exercise / form errors (the most valuable group)

These map directly to the system's three squat fault gates and Module A's validity rules, so they prove the detection logic works on real people, not just recorded data.

### Squat (Module B)

| # | Instruction to participant | Expected system behaviour | What it tests |
| --- | --- | --- | --- |
| E1 | *"Do 2 squats but only go down about a quarter of the way — deliberately shallow."* | Rep is **rejected**; live panel shows "That rep didn't count" with a **not deep enough** reason; report shows the `insufficient_depth` improvement cue and band **Needs Improvement** | Depth fault gate (< 78.04°) |
| E2 | *"Do 2 squats but lean your chest far forward, like you're bowing."* | Rep flagged with an **excessive forward lean** reason; report shows the forward-lean cue | Lean fault gate (≥ 41.42°) |
| E3 | *"Do 2 squats but let your heels come up off the floor."* | Rep flagged with a **heels lifting** reason; report shows the heel-lift cue | Heel-rise fault gate (≥ 0.084) |
| E4 | *"Do 4 squats, but make some very fast and some very slow."* | Report shows an **inconsistent tempo** cue (low severity — should **not** by itself force Needs Improvement) | Tempo consistency sub-score |
| E5 | *"Stand very close to the laptop so only part of your body is in frame, then try a squat."* | Capture-quality badge drops and turns amber/red; report raises a **low capture quality / low confidence** flag | Capture-quality gate, `low_confidence` tag |
| E6 | *"Start a set, do one squat, then just stand still and wait."* | After ~9 seconds an **inactivity prompt** appears offering Continue / Finish. It must **never auto-submit** | Inactivity safety net |
| E7 | *"Turn to face the camera directly instead of side-on, then squat."* | Detection degrades; angles become unreliable — observe whether the system misleads the user or flags low quality | Side-view assumption / monocular limitation |
| E8 | *"Set a repetition goal of 10, then do 10."* | "Rep X of Y" and progress bar track correctly; hitting the goal **prompts** but does not silently end grading | Rep-goal is display-only, never sent to grading |

### Sit-to-Stand (Module A)

| # | Instruction | Expected behaviour | Tests |
| --- | --- | --- | --- |
| E9 | *"Do 2 reps but don't stand up fully — stay slightly bent."* | Rep **not counted**; on-screen reason indicates you must rise above the stand threshold | Rep validity (>160°) |
| E10 | *"Do 2 reps but only sit down halfway."* | Rep **not counted**; reason indicates you must sit below the threshold | Rep validity (<110°) |
| E11 | *"Step sideways so half your body leaves the frame mid-test."* | Low-visibility warning appears ("Body not fully visible — step back…") | Visibility warning (< 0.6) |

### Single-Leg Stance (Module A)

| # | Instruction | Expected behaviour | Tests |
| --- | --- | --- | --- |
| E12 | *"Lift your foot only slightly off the floor, not high."* | Timing does **not** start — the lift-line is not crossed | Lift-line entry gate |
| E13 | *"Start the hold, then put your foot down after about 5 seconds."* | Hold **stops**; result reflects the short duration | Drop detection |
| E14 | *"Hold the position but sway and wobble a lot on purpose."* | Ball leaves the circle; stability sub-score drops | Ball-in-circle stability |

### Weight-Bearing Lunge Test (Module A)

| # | Instruction | Expected behaviour | Tests |
| --- | --- | --- | --- |
| E15 | *"During the hold, deliberately lift your heel off the floor."* | Attempt **ends immediately** and is flagged as heel-lift invalid | Live heel-lift detection with a control effect |
| E16 | *"Stand facing the camera instead of sideways during setup."* | Positioning guidance blocks progress with an alignment/visibility warning | Strict positioning gate |
| E17 | *"Enter a distance of 99 cm when it asks you to measure."* | Observe: is an implausible self-reported value accepted silently? | Input validation on self-measured data |

## B2 — UI, navigation and account errors

| # | Instruction | Expected behaviour | Tests |
| --- | --- | --- | --- |
| E18 | *"Try to log in with the wrong password."* | Clear, non-technical error message; no crash; no stack trace | Auth error handling |
| E19 | *"Try to register again with the email you already used."* | Clear "already registered" style message | Duplicate-account handling |
| E20 | *"Try to register with 'abc' as the email."* | Client-side validation rejects it before submitting | Input validation |
| E21 | **(Tester does this)** Log out, then paste the dashboard URL directly into the address bar | Redirects to login; protected data is never shown | Route protection / data protection NFR |
| E22 | *"When the browser asks to use the camera, click Block."* | A clear explanation of why the camera is needed and how to re-enable it — **not** a blank screen or silent failure | Permission-denied handling |
| E23 | *"Start a session, then press the browser Back button."* | Session state handled gracefully; no crash; no orphaned/corrupt session | Navigation robustness |
| E24 | *"Refresh the page in the middle of a live session."* | Graceful recovery or a clear message; must not leave a half-saved session | State recovery |
| E25 | *"Try to save a reminder with the title left empty."* | Validation prevents it with a clear message | Form validation |
| E26 | *"Switch the language to Chinese, then to Malay, then back to English."* | All labels translate; no raw keys like `moduleB.tag_…` appear on screen | i18n completeness (en/zh/ms) |
| E27 | *"Switch between light and dark theme."* | Charts, bands and text stay readable in both | Theming |
| E28 | **(Tester does this)** Narrow the browser window to phone width on the Dashboard and Report | Layout stacks; no horizontal scrolling; content still readable | Responsive layout |
| E29 | **(Tester does this)** After the participant leaves, log back into their account | Their sessions, reports and reminders are all still there | Data stored reliably (NFR) |

---

## Session timing — important

Realistically this full protocol takes **45–60 minutes** per participant:

| Stage | Time |
| --- | --- |
| Welcome, brief, consent | 5 min |
| Tasks 1–2 (account, orientation) | 5 min |
| Tasks 3–6 (four exercises) | 20–25 min |
| Tasks 7–10 (history, progress, reminders) | 8 min |
| Part B error scenarios | 8–12 min |
| Questionnaire | 8 min |
| Debrief | 3 min |

> ⚠️ **Your current consent form states the session takes "approximately 20 to 30 minutes."** That is no longer accurate for this protocol. **Update the consent form to "approximately 45 to 60 minutes"** before recruiting — an understated time commitment is an ethics-compliance problem, and participants who expected 30 minutes may rush the last tasks or leave, which would damage your data.
>
> If you must keep sessions to 30 minutes, the defensible way to shorten is to **split Part B across participants** (each participant does the core Tasks 1–10 plus ~4 assigned error scenarios), so every scenario is still covered across the sample even though no single person does all of them. Do **not** shorten by dropping exercises — every participant must do all four.
