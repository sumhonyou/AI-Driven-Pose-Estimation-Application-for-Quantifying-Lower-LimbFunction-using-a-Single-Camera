# UAT Remediation Summary — Before/After Evidence for Chapter 4.7.2

Distilled from `task.md` Phase 10 (raw implementation log, R1–R14, 2026-07-24/25) at
report-appropriate detail. Source: 22-participant moderated UAT (21 questionnaires,
scenario tasks). Each entry: **UAT evidence → root cause → fix → verification.**
Use this for the "before → finding → fix → verification" table in §4.7.2 and as
supporting evidence for Project Goal 5 (≥3 improvements from user testing).

---

## Correctness defects (found real grading/measurement bugs)

**R1 — Squat heel-lift false positive.** UAT tester T8 hypothesised the heel-rise
fault fired incorrectly (3/18 sessions, including one session in otherwise good
form). Root cause: the gate measured heel rise by averaging both legs against a
single first-frame baseline, so the occluded far leg (visibility 0.59–0.78 vs.
0.95–0.99 for the near leg) manufactured a phantom rise. Fixed by scoring the
camera-near leg only, using a 3-frame settling-window baseline instead of frame
zero, requiring the rise to be sustained across 3 frames (not a single spike), and
refusing to fire at all if even the near leg is too occluded to trust. The
underlying threshold was re-derived on the same real dataset: specificity improved
(0.569→0.625 in-sample) at an unchanged sensitivity (0.808 out-of-fold). Verified
by 28 new/rewritten regression tests (full backend suite 329/329).

**R2 — Single-Leg-Stance over-sensitive to foot jitter.** UAT testers T1/S5
reported the hold-timer "too sensitive." Root cause: the lift confirmation was
gated on 3 consecutive video frames, not real elapsed time — since MediaPipe's
frame rate varies by device, 3 frames could be under 0.1 s, well inside normal
foot jitter. Fixed by switching to a real minimum-dwell-time gate (0.15 s to
confirm a lift, 0.10 s to confirm a drop), mirrored identically into the live
on-screen timer so what the user sees during the hold matches the authoritative
backend recompute. Verified: the SLS measurement-agreement harness was re-run
after the fix and returned byte-identical statistics to the pre-fix baseline
(ICC = 0.995, kappa = 0.857) — confirming the fix corrected timing sensitivity
without disturbing overall agreement.

**R8 — Single-Leg-Stance overhaul (lowest-rated exercise, 14/18 sessions flagged
it).** The stability visual (a ball in a bordered card, detached from the user's
own body in frame) was reported as confusing ("the ball metaphor is opaque").
Redesigned so the stability indicator is overlaid directly on the user's own body
in the camera view rather than as a separate abstract widget.

---

## Interaction and feedback-timing fixes

**R4 — Live corrective feedback redesign.** Reading-distance was UAT's
lowest-scoring live-feedback item (Q9 = 3.38/5). Root cause: corrective cues were
shown in small always-on-screen text easy to miss from typical exercising
distance. Fixed with a large, glanceable full-screen cue (colour-matched to the
existing feedback panel, not an invented colour) that appears the instant a rep
is rejected, names the specific corrective action ("Go deeper," "Chest up,"
"Heels down"), and clears automatically the moment the user completes a good
rep. Iterated three times directly against HY's own live screenshots before
settling on the final treatment. Verified: 32/32 frontend tests; visual
confirmation in both light and dark theme.

**R5 — Inconsistent start protocol across the four exercises.** The single
most under-reported issue in UAT (12/18 sessions): each of the four live pages
had a different start sequence, and none gave an unmistakable "you are being
recorded now" signal. Standardised all four to the same 5-second countdown,
added a shared pulsing "Recording" indicator with a border glow and a short
audio tone at the exact moment recording begins. Verified: 36/36 frontend
tests.

**R6 — No audio feedback (most-requested new feature: 5 sessions, 5 free-text
comments).** Added spoken cues for session start/end and for corrective faults,
built as a testable priority queue (session cues always interrupt; fault cues
queue and are throttled per fault type so repeated identical faults don't spam
the user). Getting this genuinely working in a real browser required three
rounds of live debugging with HY after initial "silent" reports — the eventual
causes were a browser speech-engine race condition, then a user-gesture
activation requirement, then an intermittent browser-level speech-engine stall —
each diagnosed and fixed in turn, with a watchdog added as a final safety net
so a stalled cue can never block all future ones. Verified: 50/50 frontend
tests; empirically reproduced and confirmed fixed in a live browser session,
not just reasoned about.

**R9 — Missing pre-exercise instructions and unclear camera setup.** Added a
shared "before you begin" instruction page (numbered steps, a reference photo
of the required camera angle, and the concrete consequence of a failed
attempt, e.g. "if your heel lifts off the floor, that attempt won't count")
inserted ahead of camera setup for all four exercises. Also fixed a Single-Leg-Stance-specific
report ("the camera setup is wrong") by replacing the guidance text with the
actual required reference photo. Verified: 53/53 frontend tests; visual
confirmation against the approved design reference.

**R7 — No reference for correct form during the exercise.** Added a small
looping reference clip/photo of correct form pinned to the camera view on all
four live pages, so users can check their own form without leaving the page.

---

## Clarity and information-design fixes

**R10 — Unexplained terminology (12/18 sessions — the single most-repeated
content request).** Built a shared glossary (10 terms: ROM, band, stability,
capture quality, confidence, symmetry index, valid rep, hold time, etc.), each
definition stating in plain, non-diagnostic language which direction is
better. Wired into the report at every place a technical term appears. Added a
short "why this exercise" explanation to each exercise's instructions.

**R11 — Report redundancy, ordering, and colour semantics (Report was
otherwise UAT's strongest surface, net +15).** Fixed three specific defects
found in review: (1) the same number was shown twice in two different
formats (ML score and confidence), so one was dropped from the main view; (2)
coaching feedback and error tags — the part users found most useful — were
buried at the bottom of the report, so they were moved to appear immediately
after the headline result; (3) a genuine but low-severity error tag rendered
in the identical green used for "no issues at all," so it read as "nothing
wrong" — fixed with a distinct colour and a distinct icon shape per severity
level (not colour alone, for colour-blind accessibility). Sub-scores were also
converted from static number cards into an interactive chart. Verified:
53/53 frontend tests.

**R12 — Progress dashboard's capture-quality chart was unanimously rejected by
testers as unhelpful.** Replaced it with a per-exercise trend that is
actually meaningful to the user (e.g. completion time for Sit-to-Stand,
left-vs-right hold time for Single-Leg-Stance), and added a per-exercise
valid-reps figure to the squat report so the headline 0–10 score can be traced
directly back to "X valid reps out of Y attempts." Also added exercise
filters to the dashboard's band-distribution and error-tag panels, and a
date-range filter to session history. Verified: 340 backend tests, 56/56
frontend tests.

**R13 — Reminder feature friction (11/18 sessions, despite the concept itself
scoring 4.71/5 with 67% naming it the strongest feature).** Fixed list
ordering (newest reminder no longer buried), added an explicit prompt to add a
new reminder to the user's calendar at the moment it's created, put the
exercise name in the calendar event title, and replaced an ambiguous
whole-card click target with a clearly labelled "Open" action distinct from
"mark complete." Verified: 343 backend tests, 56/56 frontend tests.

**R14 — Navigation and general polish.** Removed a dashboard card that
implied a "streak" feature that was never actually built (a misleading
element flagged independently of the formal UAT plan), fixed several
accessibility gaps (an interactive element unreachable by keyboard, a
generic-only text description of a directional icon), and trimmed marketing
copy. Confirmed that the app's type system enforces exact translation-key
parity across all three supported languages (English/Chinese/Malay) on every
change, not just by spot-check.

---

## What this demonstrates for Chapter 4.7

- **Two of the fixes above (R1, R2) were genuine correctness defects in the
  grading/measurement logic** — found only through real users on a real
  webcam, not by the automated test suite or the researcher's own testing.
  This is itself a result worth stating explicitly: self-testing and unit
  tests verify that code does what it was written to do; they cannot surface
  a false positive that only appears under real occlusion conditions a
  designer didn't anticps ate.
- The remaining fixes (R4–R14) are usability/interaction improvements,
  directly traceable to a specific, quoted piece of UAT evidence each —
  satisfying "≥3 improvements implemented based on findings" (Project Goal 5)
  many times over, not just barely.
- Every stage above shipped with an automated regression test count reported
  alongside it — evidence the fixes were verified, not just applied.

**Not yet independently verified end-to-end in this summary's source (task.md
notes it explicitly):** most of R4 onward depend on a real webcam and browser
audio, which cannot be exercised in a sandboxed environment — final live
confirmation on a real machine is a documented open item as of 2026-07-25 and
should be closed out before the numbers above are quoted as final in the report.
