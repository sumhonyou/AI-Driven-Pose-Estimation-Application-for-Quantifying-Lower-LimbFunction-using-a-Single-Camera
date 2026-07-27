# UAT Observation Notes — Rephrased, Categorized, and Cross-Referenced Against Fixes

**Basis:** raw handwritten/typed observation notes from 18 UAT sessions (21 participants —
3 sessions were pairs). **Counting convention:** every count below is **"X / 18 sessions"**,
not individual mentions — if a session raised the same issue more than once, or two
paired participants raised it together, it counts once. This matches the counting
convention already used in `UAT_REMEDIATION_SUMMARY.md` (e.g. "12/18 sessions").

**Methodology note:** categorization is manual thematic coding by the researcher — the
standard approach for qualitative UAT free-text (see `TESTING_PROTOCOL.md` §5, "themes
coded from free text"). A few raw notes were ambiguous or partially garbled in the
original; where the intended meaning was not fully certain, the rephrased version is
marked *(interpreted)* rather than silently resolved.

**Sessions, numbered for cross-reference:**
S1 Yuffy · S2 Joddy · S3 Natalie · S4 Zoe · S5 Chloe · S6 Sia Jia Le · S7 Cleve ·
S8 Jasmine · S9 Tony · S10 Dad · S11 Mom · S12 Tung · S13 Jiayi + 1 friend · S14 Wenchi ·
S15 Daphne & Chow Ern · S16 Harry · S17 Angel · S18 Aniq & Jihan

---



## Part 1 — Rephrased Observation Notes

Meaning preserved from the original notes; wording cleaned up into complete sentences.

### S1 — Yuffy

- The sign-in/login screen does not clearly direct the user where to go.
- The post-session report charts should be more colourful and interactive.
- Instructions are not clear enough, and the UI feels messy.
- The reminder feature should ask whether to add the reminder to a calendar right after it's created.
- Suggested adding social/gamification features — adding friends and a leaderboard.



### S2 — Joddy

- Instructions need to be clearer.
- Instructions are too long.
- Pictures used in the instructions could be nicer.
- SLS: the threshold/lift-line indicator is not obvious.
- *(interpreted)* During the deliberate error tests, the below-threshold behaviour and the ball/circle error behaviour performed as expected.
- WBLT: instructions are not clear enough — the participant did not realise they needed to adjust the camera.
- Prefers a video demonstration over the current instruction format.
- Squat: the live feedback text is too small, and it's unclear what "side" (view) means.
- The error tags were confusing; the green colour looked like "no error" rather than a real issue.



### S3 — Natalie

- Did not understand the band-distribution chart.
- The ML confidence score shown during grading was unclear.
- Instinctively looked for and clicked a "Start Session" button.
- The feedback text font is too small to read.
- Suggested that being fully prepared/ready before the session starts would be better (i.e. a clearer "get ready" step).
- Had to think about it before realising the Sit-to-Stand attempt count is fixed at 5 reps.
- The camera-setup auto-start trigger activates very easily.
- The post-session report should explain every metric.
- SLS: the live feedback should show the threshold/bar level more clearly — the current feedback is not enough.
- WBLT has too much text.
- Squat: wants more explanation of *why* an error occurred, shown live during the session, not just afterward.
- Squat: noticed the ML prediction and the confidence score are effectively the same number shown twice.
- On the Progress page, the different colours used for common error tags (squat) were confusing.
- The "add to calendar" prompt should pop up automatically when a reminder is scheduled.



### S4 — Zoe

- On the home page, the "not medical advice" statement needs to be more visually obvious (e.g. a different colour); the "See how it works" button was confusing — unclear if it's just an acknowledgement.
- The reminder recurrence display ("Mon/Wed/Fri") was confusing.
- Camera setup page instructions and view guidance need to be clearer and more obvious.
- Suggested adding a picture showing the required side-view position.
- Instinctively pressed a "Start Session" button.
- STS auto-ended while a new user kept re-attempting.
- Wording is too long in general.
- Prefers the session not to start automatically.
- SLS: did not realise the hold had started.
- SLS: did not understand the purpose of the stability ball; suggested adding an instruction for it and positioning the ball centrally.
- Was not aware that 45 seconds is the hold time limit.
- Could not see the feedback text at all.
- *(interpreted)* Unclear what the different colours are meant to signify for the error tags.
- Liked the error tags for being short and colour-coded. *(positive)*
- Suggested an additional progress chart showing a more concrete per-session metric (e.g. seconds per rep) instead of just the score.
- The sort order of the trend data was confusing.
- Suggested adding a font-size increase/decrease control.
- The logo is not visible in dark theme.



### S5 — Chloe

- Terms/terminology are not understood and need explanations.
- Did not understand the score-trend chart on the dashboard.
- The valid-rep count is hard to see from a distance while exercising — suggested visualising it as a progress bar.
- STS: did not realise the camera could/should be adjusted to capture the full body.
- Feedback text needs a more visible/legible colour.
- Suggested changing the score to a percentage, since it's unclear whether the current number represents reps or something else.
- Suggested presenting report metrics more visually to reduce reading effort.
- Coaching feedback text is harder to read than it should be.
- Suggested the "compare to last session" text could state the completion-time difference directly (e.g. "12 seconds slower").
- SLS: the leg-lift detection is too sensitive.
- WBLT: the positioning/view guidance should be more visible; the "before you start" text could be smaller.
- Instructions should explicitly state where to place the camera.
- Squat: camera setup should not auto-start, because the user then thinks the next stage is starting.
- Suggested a video thumbnail instead of an autoplaying video.
- In the post-session report, the "movement improvement" section should be more readable; the pass-mark detail is secondary and could be dropped.
- The Progress page also needs term explanations placed beside metrics.
- Functional Checking mode provides too little information overall.
- Reminders: the user thought opening/selecting a reminder marked it complete; no due-reminder notification banner was shown.
- Placing Reminders under "Account" was confusing — read as a notification feature rather than where it belonged.
- The dashboard heading's line spacing is too large, making it look like separate/new words.
- Suggested adding a count badge to the error tags (e.g. showing "6").
- The "New session" sidebar item could include a picture for clarity.
- The toggle/dropdown arrow should change direction so its open/closed state is understandable.
- Spacing between a toggle control and the dashboard content is too tight.
- The "New session" item shows no visible outline when clicked/focused.



### S6 — Sia Jia Le

- Dashboard needs explanations — did not understand what it was showing.
- Wants a back button on the Profile page.
- When editing the full name field, the cursor should default to the end of the existing text.
- The flow should show instructions first; only cancelling from there should lead to camera setup.
- Wants a back button on the report page that returns to the exercise.
- STS: feedback text is too small.
- The session comparison information needs to be more visible/prominent.
- SLS: did not understand the stability ball shown during camera setup.
- Assumed the session would auto-start even before camera setup finished.
- The per-leg result breakdown (SLS) was confusing — a summary would be clearer.
- WBLT: wording should be shortened.
- The Cancel action should behave asynchronously rather than blocking the UI.
- Suggested "New session" be the first/default tab instead of the Dashboard.
- The "compare to last session" information is of secondary importance.
- Suggested designing the progress chart like iPhone's screen-time usage graph — date only when zoomed out, date and time only when zoomed in.
- Commented on the number shown in the capture-quality trend (implying it was unclear or unhelpful).
- Overall the UI is clean. *(positive)*



### S7 — Cleve

- Did not realise the camera position needed to be adjusted to fit inside the frame.
- Tends to watch the demo video only, so written instructions get ignored.
- Sit-to-Stand and Single-Leg Stance were both fine overall. *(positive)*
- Suggested attaching a reference picture for camera placement.
- Tested creating a reminder with an attached exercise and confirmed it correctly navigated to that exercise. *(positive/confirmation)*
- Overall user experience is good. *(positive)*



### S8 — Jasmine

- The "not clinical advice" disclaimer needs to be more obvious.
- Wants metric explanations on the dashboard.
- The recent-sessions table on the dashboard is good. *(positive)*
- STS: feedback text too small; rep count not visible; unsure when the session started.
- Prefers a longer countdown before the session starts.
- Prefers video demonstrations. *(duplicate theme)*
- WBLT results could be presented in a table; 
- Squat: the wording describing body position relative to the camera was confusing.
- Squat needs a maximum time/rep limit — unclear what happens with a very high rep count.
- Terms are not understood and need explanation.
- *(interpreted)* The displayed count (rep/attempt number) was not clearly well presented.
- Wants more detail shown for rep volume.
- The common error tags give a useful at-a-glance view. *(positive)*
- Wants a custom date option when scheduling reminders.
- Reminders are otherwise all good. *(positive)*



### S9 — Tony

- Understood the dashboard. *(positive)*
- Noted the rep count and angle displayed for STS. *(observation)*
- Feedback was easy to reference. *(positive)*
- On camera setup, could not find/see the "Watch Demo" option.
- Suggested offering either a manual button or auto-start as a choice.
- SLS: unclear which leg ("right leg") should be lifted.
- Suggested drawing a visible line in the camera view showing the required lift height.
- WBLT camera placement and instructions were understood. *(positive)*
- Wants explanation before/while testing, in general.
- Squat overall was okay. *(positive)*
- The score-trend chart needs a Y-axis label.
- Suggested placing the log-out button under Profile.
- Suggested Functional Checking's progress trend should also show an error-tag-style chart, like Rehab Grading has.
- The capture-quality trend chart is confusing, including its hover behaviour.
- The "repeats: once" recurrence chip does not wrap properly; reminder times should be sorted.



### S10 — Dad

- Dashboard is mostly fine but needs explanations for some items.
- Camera setup: unmet requirements should flash/highlight, and it's unclear how the user will know requirements are satisfied before being redirected.
- Instructions need to include camera-adjustment guidance.
- STS: unsure when the session started; could not read the feedback.
- Post-session report needs metric explanations.
- SLS: feedback text needs to be larger; unclear whether "right leg" means the leg to lift or the leg to balance on.
- SLS: instructions are hard to read; suggested audio guidance would help; did not understand the stability ball's meaning, and could not see the lift-line.
- WBLT: did not think to adjust the camera to a different position; instructions should show how to position the camera.
- Observed navigating via the sidebar rather than a back button.
- Instinctively looked for a "Start Session" button.
- Squat: unclear which way to face the camera (followed the video instead); the rep-target goal was not obviously displayed and was overlooked.
- Feature request: Progressive Web App (installable app) support.
- Considers the reminder feature valuable. *(positive)*
- Did not understand the band-distribution chart.
- Considers the capture-quality trend useless.
- The reminder-scheduling form should clarify which fields are required.
- A newly created reminder should be highlighted; wants a "created time" column, sortable by both created time and scheduled time.



### S11 — Mom

- Dashboard overall is fine. *(positive)*
- STS: did not know a chair was required; feedback text too small; suggested the fixed 5-rep count could be made longer/adjustable.
- SLS: unclear which leg to start with.
- WBLT camera placement was understood. *(positive)*
- No comment on Squat.
- Generally unsure how to perform the exercises; suggested a tutorial session for the future.
- The AI-generated coaching feedback is only in English, not the other supported languages.
- Progress trend overall is fine. *(positive)*



### S12 — Tung

- Dashboard needs some explanation.
- Error-tag colours on the dashboard need a legend explaining what each colour means.
- Was aware in advance that a chair was needed. *(positive/neutral — contrasts with S11)*
- Suggested placing a small reference video alongside the live session view.
- Needs explanation, in general.
- Suggested an audio cue should play when an error/wrong rep occurs.
- Error-tag colours are confusing and need explanation.
- Wants a reference exercise video available during the live session.
- Considers the capture-quality information unnecessary.



### S13 — Jiayi + 1 friend

- Wants the dashboard's common-error-tags panel to show a count of how many times each error occurred.
- Suggested moving the Reminders section higher up in the navigation.
- Instinctively clicked a button in the top-right corner.
- Suggested this flow order: instructions → camera setup → countdown → live session.
- Suggested instructions be shown in a dedicated pop-out page/window.
- Wants explanations for each metric.
- Unsure whether a reminder was set by the system automatically or created by themselves.
- Suggested a gesture-based way to start the session.
- SLS: suggested the live feedback should explicitly instruct "lift your leg higher."
- Suggested each performance band (Good/Fair/Poor) include an example video of what it looks like.
- Squat: the reference video should better demonstrate the desired angle.
- Feature request: voice feedback during squats.
- Suggested showing rep count with both a progress bar and a number.
- Considers the capture-quality trend on Progress useless.
- Reminder: the exercise name was missing from the exported Google Calendar event.
- The home page feels generic/unpolished ("vibe coded").



### S14 — Wenchi

- The home page has too much text.
- Suggested the dashboard's score-trend chart have a hover interaction showing more detail.
- Suggested being able to drill down into the band-distribution chart by exercise.
- Wants to filter the common-error-tags panel by exercise.
- STS: expected a step-by-step flow and could not clearly see the instructions.
- STS: rep number and feedback were not clearly visible.
- STS: expected a large, obvious visual change when a valid rep is counted.
- SLS: wants all instructions consolidated onto a single page, since they could not see them otherwise.
- Suggested adding a picture showing which side to face the camera.
- Suggested adding a reference view of the exercise during the live session, plus a tutorial.
- WBLT overall is fine. *(positive)*
- Squat: did not notice the angle number — only noticed the feedback text and rep number.
- Considers the ML prediction and confidence in the report unimportant/redundant.
- Feature request: streak tracking.



### S15 — Daphne & Chow Ern

- Suggested the home page logo/icon be made larger and more visually obvious.
- STS: feedback should include corrective guidance, not just status; a button was confusing; suggested adding a gesture-based start and a countdown timer.
- Suggested voice-based rep counting, and a sound cue hinting when a rep is wrong.
- Wants metric explanations.
- Suggested adding tempo/pacing music to help follow the STS rhythm.
- Suggested rewording "vs last session" to "compare to last session" for clarity.
- Prefers video demonstrations.
- Understood that the camera needed adjusting. *(positive — contrasts with several other sessions)*
- SLS: wants a reference photo shown before the session starts, explaining the ball and the threshold.
- Suggested being able to do a Functional Check after Rehab Grading, to see whether functional performance has improved.
- WBLT: wants the demo video to match the exact required camera angle.
- Squat: after a few attempts, learned how to adjust the camera correctly. *(observation — learning curve, not a persistent block)*
- Suggested changing the 0.5-point scoring increments to a percentage format.
- The error tags' green colour was confusing (looked like "no error").
- Suggested colour-coding the coaching-feedback panel green and the error-tags panel red.
- Suggested sorting error tags by colour/severity.
- Session History needs a back button after viewing a record.
- Wants a "Retry" button on the post-session report to avoid re-navigating the whole flow.
- Wants the capture-quality trend removed from Progress.
- Wants a Y-axis label added to the score-trend graph.
- The "low confidence" error tag should either be excluded, reworded, or explained.
- New reminders should appear at the top of the list.
- The "mark complete" tick in reminders should be more flexible.
- Reminders should automatically be marked complete once the associated exercise is finished.



### S16 — Harry

- Was not aware of the non-medical-advice disclaimer.
- Dashboard needs explanations.
- STS: knew to adjust the camera but skipped reading the instructions; the instructions did not cover what happens if the user isn't fully in frame, nor mention live feedback.
- Wants explanations on metrics stating which direction is better (e.g. "a higher degree is better").
- SLS: as soon as camera setup appeared satisfied, the session started immediately — felt too abrupt.
- Wants a "why this exercise" explanation describing its purpose and benefit.
- WBLT camera placement was understood. *(positive)*
- Squat: questioned whether both legs are properly detected, and whether a wider stance is required to register as a squat; also, report generation takes a long time.
- Suggested an AI-generated summary of the progress trend, and that Functional Checking should show the same three graphs as Rehab Grading for every option.
- Wants a calendar-add pop-up when creating a reminder.



### S17 — Angel

- Wants metric explanations.
- Suggested adding images to exercises on the dashboard for more context.
- Went straight to camera setup without reading the instructions first.
- Camera setup instructions are not obvious.
- STS: live feedback is not visible.
- Report metrics need descriptions.
- SLS: assumed that lifting the leg would automatically start the hold/timer.
- WBLT: the positioning guidance was confusing on the first attempt.
- Deliberately tested leaning too far forward during squats (error-scenario test). *(observation/confirmation)*
- Could not read the feedback or the angle display — mainly relied on the rep count.
- Progress page was informative and understandable. *(positive)*
- The error-tag colour coding is confusing.
- Reminders are all good. *(positive)*
- Suggested rewording all status labels throughout the app.



### S18 — Aniq & Jihan

- The non-diagnostic/clinical disclaimer is not obvious.
- The score-trend chart could be more specific/detailed; Session History needs a back button, since navigation currently relies on the sidebar.
- Reminders page needs a back button.
- STS: was aware of adjusting the camera; feedback text too small; suggested a distinct sound for incorrect reps.
- Wants metric explanations.
- SLS: believed the timer starts based on elapsed time rather than crossing the lift-line threshold.
- Suggested a sound cue when camera-setup requirements are met.
- Squat: once aware of the required pattern, knew how to set up, but positioning relative to the camera was sometimes wrong.
- The live-feedback panel does not use the full available page space.
- Suggested this flow: instructions first, then camera setup, then start the session.
- Created a reminder but could not find it afterward in the list; assumed it would automatically sync to Google Calendar.
- The current reminder button/action is fine, but in future wants the ability to add to an *existing* calendar event by pressing on it too.

---



## Part 2 — Categorized Issues and Frequency

Grouped by area. **Count = number of sessions (out of 18) that raised the issue.**

### A. Home Page / Non-Diagnostic Disclaimer


| Issue                                                 | Sessions         | Count    |
| ----------------------------------------------------- | ---------------- | -------- |
| Non-diagnostic disclaimer not visually obvious enough | S4, S8, S16, S18 | **4/18** |
| Home page has too much text                           | S14              | 1/18     |
| Home page feels generic/unpolished                    | S13              | 1/18     |
| Home page logo/branding not prominent enough          | S15              | 1/18     |




### B. Instructions and Camera Setup Flow


| Issue                                                                         | Sessions             | Count    |
| ----------------------------------------------------------------------------- | -------------------- | -------- |
| Instructions/wording too long across the app                                  | S2, S3, S4, S6, S14  | **5/18** |
| Camera setup: unclear that the camera can/should be adjusted                  | S2, S5, S7, S10, S16 | **5/18** |
| Prefer video demonstration over text instructions                             | S2, S7, S8, S14, S15 | **5/18** |
| Wants a dedicated "instructions before camera setup" flow                     | S6, S13, S14, S18    | **4/18** |
| Instructions not clear enough (general wording)                               | S1, S2, S16          | 3/18     |
| Wants a reference picture of the required camera view/angle                   | S4, S7, S14          | 3/18     |
| Instructions get skipped in favour of jumping straight to the task or video   | S7, S9, S17          | 3/18     |
| Camera setup: unclear whether requirements are satisfied before auto-redirect | S10                  | 1/18     |
| Demo video not discoverable ("Watch Demo")                                    | S9                   | 1/18     |




### C. Auto-Start / Session-Start Behaviour


| Issue                                                   | Sessions        | Count    |
| ------------------------------------------------------- | --------------- | -------- |
| Instinctively looks for a manual "Start Session" button | S3, S4, S9, S10 | **4/18** |
| Unclear when the session/recording has actually started | S4, S8, S10     | 3/18     |
| Auto-start confusing about what stage is beginning      | S5, S6, S17     | 3/18     |
| Auto-start triggers too easily / feels too abrupt       | S3, S16         | 2/18     |




### D. Live Feedback Readability (cross-exercise)


| Issue                                                    | Sessions                                    | Count     |
| -------------------------------------------------------- | ------------------------------------------- | --------- |
| **Live feedback text/font too small to read**            | S2, S3, S5, S6, S8, S10, S11, S14, S17, S18 | **10/18** |
| Live feedback panel underutilises available screen space | S18                                         | 1/18      |




### E. Sit-to-Stand (STS)


| Issue                                                             | Sessions | Count |
| ----------------------------------------------------------------- | -------- | ----- |
| Fixed rep count (5) not intuitive/adjustable                      | S3, S11  | 2/18  |
| Chair requirement not communicated upfront                        | S11      | 1/18  |
| Session auto-ends unexpectedly for new/repeat attempts            | S4       | 1/18  |
| No countdown before recording starts                              | S15      | 1/18  |
| Wants a prominent visual confirmation when a valid rep is counted | S14      | 1/18  |




### F. Single-Leg Stance (SLS)


| Issue                                                                        | Sessions                  | Count    |
| ---------------------------------------------------------------------------- | ------------------------- | -------- |
| **Lift-line/threshold indicator not obvious**                                | S2, S3, S9, S10, S15, S18 | **6/18** |
| **Stability ball's purpose/meaning unclear**                                 | S4, S6, S10, S12, S15     | **5/18** |
| Which leg to lift/start with is unclear                                      | S9, S11                   | 2/18     |
| 45-second time limit not communicated                                        | S4                        | 1/18     |
| Leg-lift detection over-sensitive to jitter                                  | S5                        | 1/18     |
| Per-leg result presentation confusing (wants a summary)                      | S6                        | 1/18     |
| Unclear that the timer starts on crossing the threshold, not on elapsed time | S18                       | 1/18     |




### G. Weight-Bearing Lunge Test (WBLT)


| Issue                                                 | Sessions | Count |
| ----------------------------------------------------- | -------- | ----- |
| Positioning/view guidance confusing                   | S5, S17  | 2/18  |
| Reference video should match the exact required angle | S15      | 1/18  |


*(WBLT wording length and camera-adjustment confusion are counted under areas B/D above, since those sessions raised them as general points that happened to occur during WBLT.)*

### H. Squat


| Issue                                                                              | Sessions        | Count    |
| ---------------------------------------------------------------------------------- | --------------- | -------- |
| **Heel-rise false positive (incl. with shoes / possible bilateral-leg averaging)** | S2, S4, S8, S16 | **4/18** |
| Unclear wording describing body position relative to the camera                    | S8, S10, S18    | 3/18     |
| Angle metric not noticed/visible                                                   | S14, S17        | 2/18     |
| Live feedback too small / unclear what "side" view means                           | S2              | 1/18     |
| Rep-target goal not obviously displayed                                            | S10             | 1/18     |
| No maximum time/rep cap — unclear behaviour for long sets                          | S8              | 1/18     |
| Wants explanation of *why* an error occurred, live (not only after)                | S3              | 1/18     |
| Report generation takes a long time                                                | S16             | 1/18     |




### I. Report / Scoring


| Issue                                                        | Sessions                                          | Count     |
| ------------------------------------------------------------ | ------------------------------------------------- | --------- |
| **Metrics and terminology lack explanation (app-wide)**      | S3, S5, S6, S8, S10, S12, S13, S15, S16, S17, S18 | **11/18** |
| ML prediction and confidence score redundant/duplicated      | S3, S14                                           | 2/18      |
| Score format unclear (0–10 vs rep count vs percentage)       | S5, S15                                           | 2/18      |
| Report metrics should be more visual (reduce reading effort) | S1, S5                                            | 2/18      |
| "Compare to last session" could be more direct/visible       | S5, S6                                            | 2/18      |
| AI coaching feedback frequently falls back to the template   | S5                                                | 1/18      |
| AI feedback is English-only, not localised                   | S11                                               | 1/18      |
| Coaching feedback text hard to read                          | S5                                                | 1/18      |
| Retry button missing on report                               | S15                                               | 1/18      |
| Back button missing on report page                           | S6                                                | 1/18      |
| "Valid reps" hard to see from typical exercising distance    | S5                                                | 1/18      |




### J. Error Tags / Colour Semantics


| Issue                                                               | Sessions              | Count    |
| ------------------------------------------------------------------- | --------------------- | -------- |
| **Error-tag colours confusing, esp. green looking like "no issue"** | S2, S3, S12, S15, S17 | **5/18** |
| Wants a count indicator on error tags                               | S5, S13               | 2/18     |
| "Low confidence" tag wording/inclusion unclear                      | S15                   | 1/18     |
| Wants per-exercise filter on the dashboard error-tags panel         | S14                   | 1/18     |
| Wants error tags sorted by severity                                 | S15                   | 1/18     |




### K. Dashboard / Progress


| Issue                                                                         | Sessions              | Count    |
| ----------------------------------------------------------------------------- | --------------------- | -------- |
| **Capture-quality trend seen as confusing/useless**                           | S6, S9, S10, S12, S15 | **5/18** |
| Dashboard needs more explanation (general)                                    | S6, S10, S12, S16     | 4/18     |
| Score-trend chart not understood                                              | S3, S5                | 2/18     |
| Score-trend chart missing a Y-axis label                                      | S9, S15               | 2/18     |
| Band-distribution chart not understood                                        | S3, S10               | 2/18     |
| Functional Checking wants the same chart richness as Rehab Grading            | S9, S16               | 2/18     |
| Wants per-exercise drill-down on band distribution                            | S14                   | 1/18     |
| Wants an additional meaningful per-exercise chart (time/reps, not just score) | S4                    | 1/18     |
| Progress trend sort order confusing                                           | S4                    | 1/18     |
| Score-trend chart wants hover/interactive detail                              | S14                   | 1/18     |
| Suggests adaptive date/time display (iPhone-usage-style)                      | S6                    | 1/18     |
| Dashboard heading line-spacing issue                                          | S5                    | 1/18     |
| Dashboard exercise cards could include images                                 | S17                   | 1/18     |




### L. Navigation / General UI


| Issue                                                                  | Sessions | Count |
| ---------------------------------------------------------------------- | -------- | ----- |
| Missing back button (Session History)                                  | S15, S18 | 2/18  |
| Missing back button (Profile)                                          | S6       | 1/18  |
| Missing back button (Reminders)                                        | S18      | 1/18  |
| "New session" nav item unclear/no visual cue                           | S5       | 1/18  |
| "New session" nav item has no focus/click outline                      | S5       | 1/18  |
| Profile name-edit field doesn't place cursor at end of text            | S6       | 1/18  |
| Toggle/dropdown arrow doesn't indicate open/closed state               | S5       | 1/18  |
| Spacing issue between a toggle control and dashboard content           | S5       | 1/18  |
| Suggests "New session" as the default landing tab instead of Dashboard | S6       | 1/18  |
| Cancel action should not block the UI (should be asynchronous)         | S6       | 1/18  |
| Dark theme: logo not visible                                           | S4       | 1/18  |
| General request to reword status labels throughout the app             | S17      | 1/18  |
| Log-out button requested under Profile                                 | S9       | 1/18  |




### M. Reminders


| Issue                                                          | Sessions         | Count    |
| -------------------------------------------------------------- | ---------------- | -------- |
| **Wants a prompt to add to calendar at time of creation**      | S1, S3, S16, S18 | **4/18** |
| Newly created reminder hard to find / not shown at top         | S10, S15, S18    | 3/18     |
| Ambiguous whether opening/selecting a card marks it complete   | S5, S18          | 2/18     |
| Reminder navigation placement confusing (under "Account")      | S5, S13          | 2/18     |
| Reminder recurrence display confusing or wraps badly           | S4, S9           | 2/18     |
| Exercise name missing from the exported calendar event         | S13              | 1/18     |
| Due-notification banner not shown/noticed                      | S5               | 1/18     |
| Scheduling form doesn't clarify required fields                | S10              | 1/18     |
| Wants a created-time column and separate sort options          | S10              | 1/18     |
| Unclear whether a reminder is system-generated or self-created | S13              | 1/18     |
| Wants auto-complete when the associated exercise is finished   | S15              | 1/18     |
| Wants custom/flexible reminder date options                    | S8               | 1/18     |
| Wants the ability to add to an existing calendar event         | S18              | 1/18     |




### N. Feature Requests (forward-looking, not defects)


| Issue                                                               | Sessions                | Count    |
| ------------------------------------------------------------------- | ----------------------- | -------- |
| **Audio/voice feedback (session cues, rep counting, error sounds)** | S10, S12, S13, S15, S18 | **5/18** |
| Wants a reference video visible during the live session itself      | S12, S14                | 2/18     |
| Wants a tutorial/onboarding session                                 | S11, S14                | 2/18     |
| Gamification: add friends / leaderboard                             | S1                      | 1/18     |
| Audio cue when camera-setup requirements are met                    | S18                     | 1/18     |
| PWA (installable app) support                                       | S10                     | 1/18     |
| Streak tracking                                                     | S14                     | 1/18     |
| Tempo/pacing music during exercise                                  | S15                     | 1/18     |
| "Why this exercise" explanation of purpose/benefit                  | S16                     | 1/18     |
| Example demonstration video per performance band                    | S13                     | 1/18     |
| Gesture-based session start                                         | S13                     | 1/18     |
| Cross-module comparison (test functional performance after rehab)   | S15                     | 1/18     |
| AI-generated progress summary                                       | S16                     | 1/18     |




### Positive / confirmed-working observations (not issues)

For completeness — these are not problems, but are part of the honest record:

- STS and SLS "all good" (S7); WBLT camera placement understood (S9, S11, S16); Squat
"overall okay" (S9); overall UX/UI described as good or clean (S6, S7).
- Reminder-to-exercise deep link tested and confirmed working (S7).
- WBLT heel-lift detection confirmed firing correctly (S7, S8).
- Error tags liked for being short and colour-coded (S4); common error tags liked as an
at-a-glance view (S8); Progress page called informative and understandable (S17);
recent-sessions table on dashboard liked (S8); dashboard understood without difficulty
(S9); reminders "all good" (S8, S17); progress trend "overall okay" (S11).

---



## Part 3 — Development Status (cross-referenced against `UAT_REMEDIATION_SUMMARY.md`)



### 3a. Addressed


| Issue (from Part 2)                                     | Count        | Fix stage              | Note                                                                                                                                                             |
| ------------------------------------------------------- | ------------ | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Live feedback text/font too small                       | 10/18        | **R4, R5**             | R4's large glanceable cue + R5's font-size increase across all four HUDs                                                                                         |
| Metrics/terminology lack explanation                    | 11/18        | **R10**                | Shared glossary wired into the report at every technical term                                                                                                    |
| Capture-quality trend confusing/useless                 | 5/18         | **R12**                | Removed and replaced with a meaningful per-exercise chart                                                                                                        |
| SLS lift-line/threshold not obvious                     | 6/18         | **partially — R9**     | Reference photo + overlay explainer folded into the new instructions page; the live in-frame line itself (as literally requested in S9) not separately confirmed |
| SLS stability ball purpose unclear                      | 5/18         | **R8, R9**             | Overlay redesigned onto the user's own body (R8); explainer folded into instructions (R9)                                                                        |
| Squat heel-rise false positive                          | 4/18         | **R1**                 | Near-leg-only scoring, settle-window baseline, debounce, occlusion guard — this is the exact root cause S8/S16 hypothesised (bilateral averaging)                |
| Error-tag colours confusing (green = "no issue")        | 5/18         | **R11**                | Distinct colour + distinct icon shape per severity, plus a legend                                                                                                |
| Instinctively looks for a manual "Start Session" button | 4/18         | **partially — R5**     | Uniform recording-start signal (badge/tone/border) added; auto-start itself was kept, not made optional                                                          |
| Unclear when session/recording started                  | 3/18         | **R5**                 | Shared `RecordingBadge` + start tone + border glow on all 4 live pages                                                                                           |
| Wants an "instructions before camera setup" flow        | 4/18         | **R9**                 | New shared instructions page inserted ahead of camera setup for all 4 exercises                                                                                  |
| Wants a reference picture of the camera view/angle      | 3/18         | **R9**                 | Reference photo added per exercise on the instructions page                                                                                                      |
| ML prediction and confidence redundant                  | 2/18         | **R11**                | ML-prediction row dropped from the main view; confidence kept                                                                                                    |
| Wants a count indicator on error tags                   | 2/18         | **R11**                | Count badge added                                                                                                                                                |
| Score-trend chart missing Y-axis label                  | 2/18         | **R12 follow-up**      | Y-axis label added, axis gutter widened                                                                                                                          |
| Band distribution: wants per-exercise drill-down        | 1/18         | **R12 follow-up**      | Exercise filter dropdown added                                                                                                                                   |
| Error tags: wants per-exercise filter                   | 1/18         | **R12 follow-up**      | Filter dropdown added                                                                                                                                            |
| Reminder: prompt to add to calendar on creation         | 4/18         | **R13**                | Save flow now shows a calendar-add prompt immediately                                                                                                            |
| Reminder: exercise name missing from calendar event     | 1/18         | **R13**                | Exercise name now included in the exported event title                                                                                                           |
| Reminder: newly created item hard to find               | 3/18         | **R13**                | List now sorts newest-first                                                                                                                                      |
| Reminder: ambiguous select-vs-complete                  | 2/18         | **R13**                | Distinct "Open" action added, separate from the completion tick                                                                                                  |
| Reminder navigation placement confusing                 | 2/18         | **R13**                | Moved out of "Account" into "Overview"                                                                                                                           |
| Reminder recurrence chip wraps badly                    | part of 2/18 | **R13**                | Text-wrapping fixed (comprehension of the pattern itself not separately re-tested)                                                                               |
| Reminder: auto-complete when exercise finished          | 1/18         | **R13**                | Auto-tick scoped to the launched reminder                                                                                                                        |
| Dashboard heading line-spacing issue                    | 1/18         | **R14**                | `line-height` corrected                                                                                                                                          |
| Profile name-edit cursor position                       | 1/18         | **R14**                | Cursor now placed at end of existing text                                                                                                                        |
| Toggle/dropdown arrow doesn't rotate                    | 1/18         | **R14**                | Chevron rotation added                                                                                                                                           |
| "New session" has no focus/click outline                | 1/18         | **R14**                | Converted to a real link; global focus-visible styling now applies                                                                                               |
| Back button missing on report page                      | 1/18         | **R11**                | Added, using browser history back                                                                                                                                |
| Retry button missing on report                          | 1/18         | **R11**                | Added                                                                                                                                                            |
| Wants a reference video during the live session         | 2/18         | **R7**                 | Looping demo clip/photo pinned to the camera view on all 4 live pages                                                                                            |
| Audio/voice feedback requests                           | 5/18         | **R6**                 | Spoken session/fault cues added to all 4 live pages, after extensive live debugging                                                                              |
| Audio cue when camera-setup requirements are met        | 1/18         | **R5**                 | Recording-start tone plays at that transition                                                                                                                    |
| AI coaching feedback falls back to template too often   | 1/18         | **R3**                 | Fallback-reason telemetry added + prompt tightened (diagnostic fix; live-confirmed reduction not yet verified)                                                   |
| "Why this exercise" explanation                         | 1/18         | **R10**                | Added to every exercise's instructions                                                                                                                           |
| SLS per-leg result presentation confusing               | 1/18         | **R8**                 | Folded into the broader SLS overhaul                                                                                                                             |
| Wants error tags sorted by severity                     | 1/18         | **already true — R11** | Tags are ranked by severity as part of R11's redesign                                                                                                            |




### 3b. Not addressed / future work


| Issue (from Part 2)                                                   | Count | Status                                                                                                                                                                                      |
| --------------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI feedback is English-only                                           | 1/18  | **Documented limitation, not fixed** — deliberate scope decision (R3)                                                                                                                       |
| Log-out button requested under Profile                                | 1/18  | **Explicitly descoped** in R14 (HY edited it out of scope)                                                                                                                                  |
| Dark theme logo not visible                                           | 1/18  | **Explicitly descoped** in R14                                                                                                                                                              |
| Missing back button — Session History (as its own tab)                | 2/18  | **Explicitly descoped** in R14 — the tab itself was decided not to need one; only the Report "detail" view does (and has one, R11)                                                          |
| Missing back button — Profile                                         | 1/18  | Not found addressed in R1–R14                                                                                                                                                               |
| Missing back button — Reminders                                       | 1/18  | Not found addressed in R1–R14                                                                                                                                                               |
| PWA (installable app) support                                         | 1/18  | Not addressed                                                                                                                                                                               |
| Streak tracking                                                       | 1/18  | **Explicitly not built** — R14 in fact *removed* a misleading UI element that implied a streak feature existed                                                                              |
| Gamification (friends / leaderboard)                                  | 1/18  | Not addressed                                                                                                                                                                               |
| Tempo/pacing music                                                    | 1/18  | Not addressed                                                                                                                                                                               |
| Gesture-based session start                                           | 1/18  | Not addressed                                                                                                                                                                               |
| Example demonstration video per performance band                      | 1/18  | Not addressed                                                                                                                                                                               |
| Cross-module comparison (functional check after rehab)                | 1/18  | Not addressed                                                                                                                                                                               |
| AI-generated progress summary                                         | 1/18  | Not addressed                                                                                                                                                                               |
| Tutorial/onboarding session                                           | 2/18  | Not addressed                                                                                                                                                                               |
| Custom/flexible reminder date options                                 | 1/18  | Not addressed                                                                                                                                                                               |
| Reminder: link to an existing calendar event                          | 1/18  | Not addressed                                                                                                                                                                               |
| Reminder: created-time column + extra sort options                    | 1/18  | **Explicitly flagged optional, not built** (R13)                                                                                                                                            |
| "Low confidence" tag wording/inclusion                                | 1/18  | Not addressed                                                                                                                                                                               |
| Score/percentage format ambiguity                                     | 2/18  | Not addressed                                                                                                                                                                               |
| STS: chair requirement not communicated upfront                       | 1/18  | Not addressed                                                                                                                                                                               |
| STS: fixed rep count not adjustable                                   | 2/18  | Not addressed (5-rep count is a fixed clinical protocol choice, per the implementation plan — worth stating as a deliberate design constraint rather than an oversight)                     |
| STS: session auto-ends unexpectedly                                   | 1/18  | Not addressed                                                                                                                                                                               |
| STS: wants a prominent visual confirmation on valid rep               | 1/18  | Not addressed                                                                                                                                                                               |
| SLS: which leg to lift is unclear                                     | 2/18  | Not addressed                                                                                                                                                                               |
| SLS: 45-second limit not communicated                                 | 1/18  | Not addressed                                                                                                                                                                               |
| SLS: timer-start trigger misunderstood                                | 1/18  | Not addressed                                                                                                                                                                               |
| WBLT: positioning guidance confusing                                  | 2/18  | Not addressed                                                                                                                                                                               |
| WBLT: reference video angle accuracy                                  | 1/18  | Not addressed                                                                                                                                                                               |
| Squat: unclear camera-facing wording                                  | 3/18  | Not addressed                                                                                                                                                                               |
| Squat: angle metric not noticed                                       | 2/18  | Not addressed                                                                                                                                                                               |
| Squat: rep-target goal not obvious                                    | 1/18  | Not addressed                                                                                                                                                                               |
| Squat: no max time/rep cap                                            | 1/18  | Not addressed                                                                                                                                                                               |
| Squat: wants live "why" explanation for errors                        | 1/18  | Not addressed                                                                                                                                                                               |
| Squat: report generation is slow                                      | 1/18  | Not addressed                                                                                                                                                                               |
| Report: score format / visual presentation                            | 2/18  | Not addressed                                                                                                                                                                               |
| Report: coaching feedback readability                                 | 1/18  | Not addressed                                                                                                                                                                               |
| Report: "valid reps" hard to see from distance                        | 1/18  | Partially — the underlying figure was added to the report (R12), but not specifically as a distance-readable visual element                                                                 |
| Functional Checking wants parity of chart richness with Rehab Grading | 2/18  | Not addressed                                                                                                                                                                               |
| Score-trend chart not understood / wants hover detail                 | 3/18  | Not addressed beyond the Y-axis label fix                                                                                                                                                   |
| Band distribution not understood                                      | 2/18  | Not addressed beyond the drill-down filter                                                                                                                                                  |
| Dashboard exercise cards could include images                         | 1/18  | Not addressed                                                                                                                                                                               |
| Progress: adaptive date/time display suggestion                       | 1/18  | Not addressed                                                                                                                                                                               |
| Instructions too long/wordy                                           | 5/18  | **Partially** — the content was restructured into a dedicated page (R9), but not independently confirmed as shorter                                                                         |
| Instructions skipped in favour of video/task                          | 3/18  | Not addressed as a standalone item (indirectly touched by R9's restructuring)                                                                                                               |
| Demo video not discoverable                                           | 1/18  | **Partially** — R9 removed the separate "Watch Demo" panel and folded its content into the new instructions page, which changes the interaction rather than directly fixing discoverability |
| Camera setup: unclear when requirements are satisfied                 | 1/18  | Not addressed                                                                                                                                                                               |
| "New session" item unclear / wants a picture                          | 1/18  | Not addressed                                                                                                                                                                               |
| Suggests "New session" as default tab                                 | 1/18  | Not addressed                                                                                                                                                                               |
| Cancel action should be asynchronous                                  | 1/18  | Not addressed                                                                                                                                                                               |
| Reword all status labels app-wide                                     | 1/18  | Not addressed                                                                                                                                                                               |
| Home page too wordy / feels generic / logo not prominent              | 3/18  | Not addressed                                                                                                                                                                               |




---



## Summary for Chapter 4.7

- **Highest-frequency issues** (candidates for the report's headline findings table):
live feedback text too small (10/18), metrics/terminology unexplained (11/18),
capture-quality trend confusing (5/18), error-tag colour semantics (5/18), audio
feedback requests (5/18), SLS lift-line not obvious (6/18), SLS stability-ball
confusion (5/18), squat heel-rise false positive (4/18).
- Of these, **every single one above 4/18 was addressed** by a Phase 10 stage —
strong evidence for Project Goal 5 ("≥3 improvements based on findings"), several
times over.
- The **squat heel-rise false positive (R1)** is the standout finding: two independent
sessions (S8, S16) correctly guessed the technical root cause (bilateral leg
averaging) before the code was even inspected — worth quoting directly in the report
as evidence of a genuine, non-trivial defect only surfaced by real users.
- The **"not addressed" list is long but mostly low-frequency (1/18) individual
feature requests** — appropriate material for Chapter 5's Future Work, not evidence
against the remediation effort. The exceptions worth naming explicitly as scope
decisions (not oversights) in Chapter 5: AI feedback being English-only, the fixed
STS rep count, and the deliberately-descoped items (log-out placement, dark-theme
logo, streak tracking, Session-History back button).

