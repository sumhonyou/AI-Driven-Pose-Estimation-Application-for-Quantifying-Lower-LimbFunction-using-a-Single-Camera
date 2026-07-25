# PhysioSense User-Testing Protocol — recruitment, session flow, and ethics

Companion to `SCENARIO_TASKS.md` (what participants do), `OBSERVATION_SHEET.md` (what you record), and `QUESTIONNAIRE_V3.md` (what they fill in).

---

## 1. Who to recruit

### Scope decision to state explicitly in your report

Older adults are **deliberately excluded** from this testing round. Write this in the report as a scope decision with a reason, not as an oversight:

> *"User testing was conducted with general healthy adults. Older adults with knee conditions — although named as a priority group in the proposal — were excluded from this evaluation round because testing a movement-based prototype with a clinically vulnerable group requires physiotherapist supervision and a higher level of ethics approval than was available within the project timeframe. Evaluation with older adults under professional supervision is identified as future work."*

That is a **strength**, not a weakness: it shows you understood the risk boundary rather than ignoring it.

### Do you need athletes or a special user type?

**No.** Your system's primary target is general users doing home-based self-checking; athletes were a secondary group in the proposal. Recruiting specifically for athletes would not improve your usability findings.

What actually matters for usability testing is **variation in the factors that affect how someone uses the system**, not job title. For 10 participants, aim for a spread across:

| Factor | Why it matters | Target for N=10 |
| --- | --- | --- |
| Prior fitness/health-app experience (Q3) | Experienced users navigate faster; novices reveal discoverability problems | ~5 yes / ~5 no |
| Prior rehab or physio experience (Q4) | Affects whether they understand terms like "range of motion" | ~3 with, ~7 without |
| Knee/ankle discomfort history (Q2) | Your actual target need; also a safety consideration | 2–3 with some history |
| Gender | Body proportions affect pose detection and framing | Mixed, roughly balanced |
| Height | Directly affects camera distance and whether the full body fits in frame | Include at least one notably tall and one notably short participant |
| Activity level | A sedentary participant may squat very differently from an active one | 2–3 active, 2–3 sedentary |
| Tech confidence | Reveals whether the UI works for non-technical users | At least 2–3 who are not confident with new apps |

Your friends aged 18–24 are a perfectly acceptable sample **as long as you report it honestly** as a convenience sample. Recruiting 10 people who are all confident tech users from the same course would be the real weakness — so deliberately include a few who are *not* confident with new apps.

### Is 10 enough?

Yes, for usability evaluation. The established finding (Nielsen & Landauer) is that around **5 users surface roughly 85% of usability problems**, and returns diminish sharply after that; **10 is a solid, defensible number** for an FYP usability study. State N=10 plainly and frame it correctly:

> *"N=10 is appropriate for identifying usability problems and describing user perception. It is **not** sufficient for statistical inference, so results are reported descriptively (means, counts, medians) without significance testing."*

That sentence protects you in the viva. An examiner will accept a well-reported N=10; they will attack an N=10 that claims statistical significance.

### On "manipulating some data" — do not do this

You asked whether you should manipulate some of the data. **No — and please don't.** This matters more than the marks:

1. **It is research misconduct.** Fabricating or altering participant data is one of the few things that can escalate beyond a bad grade into an academic-integrity case, even in an undergraduate project.
2. **It is detectable.** Fabricated Likert data has recognisable signatures — unnaturally uniform distributions, no straight-lining, means clustered too tightly, free-text comments that don't match the ratings. Supervisors and examiners have seen a lot of real data.
3. **You don't need to.** A modest, honestly-reported result is worth more than an impressive fake one. If 4 out of 10 people struggle to find the Progress page, that is a genuine finding you can *act on and discuss* — which is exactly what the marking criteria reward. A uniform sea of 5/5 ratings is actually a *weaker* report because it gives you nothing to analyse or improve.
4. **The honest version is more defensible in a viva.** "Users rated live feedback 3.2 and I traced it to X, so I would change Y" is a far stronger answer than "everything scored 4.8."

If your concern is that 10 responses feels thin, the legitimate fixes are: recruit a couple more people, report the behavioural measures from the observation sheets alongside the questionnaire (this roughly doubles your evidence base), and state the sample limitation clearly.

---

## 2. Session flow — run this identically for every participant

### Stage 1 — Welcome and brief (3 min)

Read this **verbatim** so every participant receives the same framing:

> *"Thank you for helping me test PhysioSense. This is a prototype web application for lower-limb functional checking and rehabilitation exercise grading using just a webcam.*
>
> *Two important things. First, **I am testing the system, not you.** If anything is confusing or hard to find, that is a problem with my design, and finding those problems is exactly why you are here. Please don't worry about doing anything wrong.*
>
> *Second, this system is **not a medical device**. It does not diagnose anything. If at any point you feel pain, discomfort, or you're unsteady, please stop immediately — just say so.*
>
> *I'll ask you to do some tasks. Please **think aloud** as you go: tell me what you're looking for, what you expect to happen, and if anything surprises you. I won't help unless you're really stuck, because I need to see where people get stuck naturally.*
>
> *Later I'll also ask you to do a few things deliberately wrong, so I can check the system reacts sensibly. That part is intentional — don't worry about it.*
>
> *The whole session takes about 45 to 60 minutes. You can stop at any time for any reason. Any questions before we start?"*

### Stage 2 — Consent (3 min)

- Hand over the printed consent form; let them read it, don't summarise it for them.
- Point out the **separate photo/video opt-in** (see §4) and make clear that declining it does not affect participation.
- Collect the signature before anything else begins.

### Stage 3 — Physical safety demo (2 min)

- **Physically demonstrate each movement yourself** (sit-to-stand, single-leg stance, lunge, squat) so they know what is being asked and don't injure themselves.
- **Do NOT demonstrate the user interface.** Navigation, button locations, and where results appear are precisely what you are measuring. Showing them destroys your time-on-task and completion data.

### Stage 4 — Tasks 1–10 (40 min)

Follow `SCENARIO_TASKS.md` Part A in order. Time each task, score U/A/F, record confusion points and verbatim quotes.

**Rules for you as the observer:**
- Silence is your job. Resist filling pauses — that is where the usability data lives.
- If they ask "what do I do now?", reply neutrally: *"What would you try?"*
- Only step in after ~2 minutes of being stuck, or for any safety concern. Record every intervention.
- Never defend the design or explain why something is the way it is until the debrief.

### Stage 5 — Error scenarios (10 min)

Follow `SCENARIO_TASKS.md` Part B. Introduce with: *"Now I'd like you to do a few things deliberately wrong so I can check how the system reacts."*

### Stage 6 — Questionnaire (8 min)

- Have them fill the Google Form **on their own**, without you watching over their shoulder — hovering biases ratings upward.
- Step away or sit across the room. Say: *"Please be honest — critical feedback is more useful to me than polite feedback."*

### Stage 7 — Debrief (3 min)

- Ask the two questions worth more than most of the form: *"What was the most frustrating moment?"* and *"If you could change one thing, what would it be?"* Write the answers down verbatim.
- Now you may answer any questions they had about how the system works.
- Thank them; confirm how to withdraw their data if they later change their mind.

---

## 3. Practical scheduling advice

- **Run a pilot with 1 person first** (a friend who won't be in your final sample, or your supervisor). You will find broken tasks, unclear wording, and timing problems. Fix them, then start the real 10. Report the pilot separately, or exclude it — don't silently merge it in.
- Schedule **no more than 3–4 participants per day**. Observation is tiring and your notes degrade.
- Keep the **same laptop, browser, and room** for all sessions so time-on-task is comparable.
- Reset camera permissions between participants.
- Leave 15 minutes between sessions for resetting and writing up notes while they are fresh.

---

## 4. Photographs and video — recommendation

**Short answer: yes, take images — but mostly of the system and the setup, not of participants' faces.**

Your current consent form covers questionnaire responses and states data will be anonymised. **It does not clearly cover photography, and a recognisable photo breaks the anonymity you promised.** So do not photograph participants under the existing form as written.

### What to capture, in priority order

| Priority | What | Consent needed | Value in the report |
| --- | --- | --- | --- |
| **1 — definitely do** | **Screenshots of the system**: camera setup guidance, live session with the depth gauge, a report page, dashboard, progress charts, reminders | None (no personal data — use your own test account) | Highest. This is the standard appendix material and shows the examiner the working system |
| **2 — definitely do** | **Setup / environment photos**: the room, camera distance, chair placement, the ruler for WBLT — **with you as the subject**, not participants | None (it's you) | Documents the test conditions in your methodology chapter; reproducible setup |
| **3 — optional** | Photos of a participant mid-exercise, **framed from behind or side so the face is not identifiable**, or with the face blurred | **Yes — separate written opt-in** | Moderate. Adds realism but the same point can be made with a photo of yourself |
| **4 — avoid** | Identifiable face photos or video of participants | Yes, and it conflicts with your anonymity promise | Low value, high privacy cost. Not worth it |

### If you do want participant photos, add this to the consent form as a separate item

> **Photography (optional — you may take part without agreeing to this):**
> ☐ I consent to photographs being taken during the session and used in the researcher's academic project report.
> ☐ I do **not** consent to photographs.
>
> *If you consent, images will be cropped or blurred so that you are not identifiable, will be used only in the academic report, and will not be published online or shared beyond the university assessment process.*

Also amend the confidentiality paragraph, which currently promises full anonymity, to note that any images are used only in de-identified form with separate consent.

**My recommendation:** do priorities 1 and 2 only. Screenshots plus setup photos of yourself give you everything you need for the appendix with zero privacy risk and no consent-form rewrite. Add priority 3 only if your supervisor specifically wants evidence of real users in the room.

---

## 5. What to report in your results chapter

Combine the three evidence streams — this is what makes the evaluation credible:

1. **Questionnaire (perception)** — mean and distribution per item; component ranking; Q27/Q28 counts for the priority-fix list; Q29 adoption intent.
2. **Observation sheet (behaviour)** — unaided task completion rate, median time-on-task per task, error counts, and the camera-self-correction count (the §3.7 promise).
3. **Qualitative** — themes coded from Q30 free text plus the verbatim quotes and debrief answers from your observation sheets.

Then close with an **improvement list**: for each weakness found, state the evidence, the diagnosis, and what you would change. That section is usually where the marks are, and it is impossible to write convincingly from fabricated data — one more reason to keep it real.

### Limitations to state explicitly

- Convenience sample of N=10, predominantly aged 18–24, recruited from the researcher's own university network.
- No older adults and no clinical population (see §1 — deliberate, with reason and future work).
- Single-session testing: the dashboard and progress-trend features were evaluated on **perceived** usefulness, since genuine multi-session trends require repeated use over weeks.
- Testing was conducted in a controlled room rather than participants' actual homes, so real home lighting, space, and camera-placement problems are likely under-represented.
- The researcher was present throughout, which may have produced more favourable ratings than unsupervised home use (social-desirability bias).
