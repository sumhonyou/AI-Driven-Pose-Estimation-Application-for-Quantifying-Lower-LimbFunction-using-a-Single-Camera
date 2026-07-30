# REPORT WRITING PLAN — Chapters 3, 4 and 5

**Project:** AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera (PhysioFit)
**Plan version:** 1.0 — 2026-07-26
**Purpose:** the single reference used when drafting. Section numbers here are the _final report_ numbers. Saying "write 4.3.2" is unambiguous.

## Table of Content

- [0. How to use this plan](#0-how-to-use-this-plan)
  - [0.1 Numbering contract](#01-numbering-contract)
  - [0.2 Status labels (Chapter 3 only)](#02-status-labels-chapter-3-only)
  - [0.3 Standing instructions for every drafting request](#03-standing-instructions-for-every-drafting-request)
  - [0.4 Emphasis budget](#04-emphasis-budget)
- [1. LOCKED FACTS REGISTER](#1-locked-facts-register)
  - [1.1 Participants and testing](#11-participants-and-testing)
  - [1.2 UAT sample profile (n = 21)](#12-uat-sample-profile-n-21)
  - [1.3 UAT questionnaire — all 22 items, ranked worst to best](#13-uat-questionnaire-all-22-items-ranked-worst-to-best)
  - [1.4 UAT observation themes (X / 18) — ⚠️ SUPERSEDED](#14-uat-observation-themes-x-18-superseded)
  - [1.5 Requirements survey (n = 20) — findings that drove design](#15-requirements-survey-n-20-findings-that-drove-design)
  - [1.6 Dataset and model](#16-dataset-and-model)
  - [1.7 Deployed grading configuration](#17-deployed-grading-configuration)
  - [1.8 Module A evaluation (SLS and WBLT)](#18-module-a-evaluation-sls-and-wblt)
  - [1.9-A Module A per-check metrics that actually convert to a label — VERIFIED (from Table 6 revision, 2026-07-29)](#19-a-module-a-per-check-metrics-that-actually-convert-to-a-label-verified-from-table-6-revision-2026-07-29)
  - [1.9 Normalisation and the capture pipeline — VERIFIED (S10 resolved)](#19-normalisation-and-the-capture-pipeline-verified-s10-resolved)
- [2. WHAT YOU STILL NEED TO SUPPLY](#2-what-you-still-need-to-supply)
- [CHAPTER 3 — METHODOLOGY](#chapter-3-methodology)
  - [3.1 Methodology Overview and Research Approach — REVISE + ADD](#31-methodology-overview-and-research-approach-revise-add)
    - [What to retain, revise and cut from your current §3.1](#what-to-retain-revise-and-cut-from-your-current-31)
  - [3.2 Dataset Selection and Preparation — REVISE](#32-dataset-selection-and-preparation-revise)
    - [What to retain, revise and cut from your current §3.2](#what-to-retain-revise-and-cut-from-your-current-32)
  - [3.3 Pose Estimation and Data Preprocessing — REVISE (3.3.1–3.3.3, 3.3.5) + DELETE 3.3.4](#33-pose-estimation-and-data-preprocessing-revise-331333-335-delete-334)
    - [Subsection-by-subsection action table](#subsection-by-subsection-action-table)
    - [§3.4.2 addition — Feature-scale normalisation (relocated from §3.3.4)](#342-addition-feature-scale-normalisation-relocated-from-334)
  - [3.4 System Development](#34-system-development)
    - [3.4.1 Module A: Rule-Based Functional Quantification — REVISE](#341-module-a-rule-based-functional-quantification-revise)
    - [3.4.2 Module B: Hybrid Rehabilitation Grading — REWRITE](#342-module-b-hybrid-rehabilitation-grading-rewrite)
    - [Subsection-by-subsection action table](#subsection-by-subsection-action-table-1)
    - [§3.4.2.3 rewrite guidance — what the shipped system actually does](#3423-rewrite-guidance-what-the-shipped-system-actually-does)
    - [Naming note — why not "Model Deployment and Inference"](#naming-note-why-not-model-deployment-and-inference)
    - [Replacement band table (supersedes proposal Table 6)](#replacement-band-table-supersedes-proposal-table-6)
    - [F3.5 — Module B pipeline (redraws proposal Figure 8)](#f35-module-b-pipeline-redraws-proposal-figure-8)
    - [F3.9 — ML training pipeline (revises proposal Figure 9)](#f39-ml-training-pipeline-revises-proposal-figure-9)
    - [3.4.3 Web Application Development](#343-web-application-development)
  - [3.4.4 Tools and Technology Stack — NEW (promoted, not nested)](#344-tools-and-technology-stack-new-promoted-not-nested)
  - [3.5 Implementation Environment and Deployment — ADD](#35-implementation-environment-and-deployment-add)
  - [3.6 Evaluation Design — MERGE (3.5 + 3.6 + 3.7) + REVISE](#36-evaluation-design-merge-35-36-37-revise)
    - [3.6.1 Module A: Measurement-Agreement Evaluation — ADD](#361-module-a-measurement-agreement-evaluation-add)
    - [3.6.2 Machine-Learning Evaluation — REVISE](#362-machine-learning-evaluation-revise)
    - [3.6.3 Application Testing — ADD](#363-application-testing-add)
    - [3.6.4 User Acceptance Testing Design — REVISE](#364-user-acceptance-testing-design-revise)
  - [3.7 Ethical Considerations and the Non-Diagnostic Boundary — DROPPED (2026-07-26)](#37-ethical-considerations-and-the-non-diagnostic-boundary-dropped-2026-07-26)
- [CHAPTER 4 — RESULTS AND DISCUSSION](#chapter-4-results-and-discussion)
  - [4.1 Project Overview](#41-project-overview)
  - [4.2 Pose-Grading Machine-Learning Model](#42-pose-grading-machine-learning-model)
    - [4.2.1 Dataset Characteristics and Feature Validity](#421-dataset-characteristics-and-feature-validity)
    - [4.2.2 Model Training and Evaluation Results](#422-model-training-and-evaluation-results)
    - [4.2.3 Fusion Weight and Threshold Selection](#423-fusion-weight-and-threshold-selection)
    - [4.2.4 Detection Examples](#424-detection-examples)
    - [4.2.5 Model Limitations and Discussion](#425-model-limitations-and-discussion)
  - [4.3 Web Application](#43-web-application)
    - [4.3.1 Implemented System and User Interface](#431-implemented-system-and-user-interface)
    - [4.3.2 System and Grading Test Results](#432-system-and-grading-test-results)
    - [4.3.3 User Acceptance Testing Results](#433-user-acceptance-testing-results)
    - [§1.4-R Top observation findings — out of 21 sessions, ranked by frequency](#14-r-top-observation-findings-out-of-21-sessions-ranked-by-frequency)
    - [4.3.4 Enhancements Implemented After UAT](#434-enhancements-implemented-after-uat)
    - [4.3.5 Design-Science Contribution and Discussion](#435-design-science-contribution-and-discussion)
  - [4.4 Synthesis Against the Reviewed Literature — (optional but recommended)](#44-synthesis-against-the-reviewed-literature-optional-but-recommended)
- [CHAPTER 5 — CONCLUSION](#chapter-5-conclusion)
  - [5.1 Conclusion](#51-conclusion)
  - [5.2 Limitations](#52-limitations)
  - [5.3 Future Work](#53-future-work)
- [APPENDIX A — FIGURE AND TABLE REGISTER](#appendix-a-figure-and-table-register)
- [APPENDIX B — DEVIATIONS REGISTER](#appendix-b-deviations-register)
- [APPENDIX C — DRAFTING ORDER](#appendix-c-drafting-order)

---

## 0. How to use this plan

### 0.1 Numbering contract

Every heading below carries its final report number. Do not renumber during drafting. If a section is cut, leave a `— CUT` marker rather than closing the gap, so earlier references stay valid.

**Warning:** `UAT_PROCEDURE_CONDUCTED.md` and `UAT_REMEDIATION_SUMMARY.md` internally reference "§3.6.5", "§4.7" and "§4.7.2". Those belong to an older scheme. Under this plan, UAT design is **3.6.4** and UAT results are **4.3.3**. Do not copy those cross-references across.

### 0.2 Status labels (Chapter 3 only)

| Label       | Meaning                                                       |
| ----------- | ------------------------------------------------------------- |
| **RETAIN**  | Proposal text stands. Tense pass only.                        |
| **REVISE**  | Substance holds, specifics changed. Edit, don't restart.      |
| **REWRITE** | Proposal describes something that was not built. Start fresh. |
| **MERGE**   | Fold into another section.                                    |
| **ADD**     | New section, no proposal counterpart.                         |
| **MOVE**    | Content relocates to another chapter.                         |

### 0.3 Standing instructions for every drafting request

**Read this section before drafting anything.** It applies to every request of the form "write §X", without needing to be restated each time.

**Role.** Write as a critical-thinking research paper writer specialising in computer science. Where a claim needs support, go and find it in a legitimate source — peer-reviewed journals, Google Scholar, or equivalent — rather than asserting it or attributing it vaguely. Verify before citing; if a claim cannot be supported, say so instead of softening it into something unsourced. All citations in **APA 7th edition**. Follow the voice contract below, humanised into university-student academic prose rather than polished machine prose.

**Figure titling convention.** In the report _text_, refer to figures as `Figure Y` placeholders for the user to fill in. **Inside the generated visualisation itself, do NOT print "Figure Y" or any figure number** — the image carries only its descriptive title (e.g. "Session-entry flow before and after Stages R5, R7 and R9"). The user adds the numbered caption beneath the image in Word.

**Length.** Target **300–450 words per subsection**. Concise and meaningful, not padded to fill the range. Exceeding 450 words is acceptable where the content genuinely demands it — §4.3.3 and §4.3.4 will almost certainly run longer — but the range is the default, and a subsection that drifts well past it without cause should be tightened rather than justified.

**Voice contract (applies to all three chapters).** Matched to `PS_22089262.pdf`, past tense throughout.

- **Sentence length.** Split. One idea per sentence. If a sentence carries two clauses joined by "which" or "while", break it.
- **Your existing connectors** — keep using them, they are your fingerprint: _In addition,_ / _Apart from that,_ / _Hence,_ / _For further clarity,_ / _Thus,_ / _Last but not least,_ / _Looking at X,_ / _Coming to,_ / _Talking about X,_.
- **Tense.** Everything is past. "The system was built", not "the system will be built". Chapter 2's forward-looking closers ("this project should include X") become "this motivated including X, implemented in §3.X".
- **Do not import the Phase 5 draft's register.** `PHASE5_CHAPTER_DRAFT.md` is written in a dense analytical style that does not match your voice. Use it for _facts and numbers only_. Re-say every sentence in your own words.
- **Avoid:** em-dash chains, "delve", "leverage", "robust", "seamless", "it is worth noting that", tricolon lists ("faster, cheaper, and more reliable").
- **Hedge honestly.** "This suggests", "in this dataset", "for this sample" — these are not weakness, they are the difference between a defensible claim and one an examiner dismantles.

### 0.4 Emphasis budget

Target proportions, since the web application is the stronger contribution:

| Chapter                | Share                                   |
| ---------------------- | --------------------------------------- |
| 3 Methodology          | ~30%                                    |
| 4 Results & Discussion | ~55% (of which ML ≈ 35%, web app ≈ 65%) |
| 5 Conclusion           | ~15%                                    |

---

## 1. LOCKED FACTS REGISTER

Use these exact figures everywhere. Never let a number vary between chapters.

### 1.1 Participants and testing

| Fact                            | Value                                                                                                                                                                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Requirements survey respondents | **20**                                                                                                                                                                                                                                                 |
| UAT questionnaires returned     | **21**                                                                                                                                                                                                                                                 |
| UAT observation sessions        | **21** (corrected 2026-07-26 — see note)                                                                                                                                                                                                               |
| Counting convention             | Questionnaire stats = _n = 21_. Observation frequencies = _X / 21 sessions_.                                                                                                                                                                           |
| Former "paired" sessions        | S13, S15 and S18 were **not** joint sessions. Participants were tested separately and converged on the same observations. Notes are split into independent records for the appendix; a theme raised in a former pair entry counts as **two** sessions. |
| Exercise coverage               | **All participants completed all four exercises.**                                                                                                                                                                                                     |
| Note-taking caveat              | Sessions ran in real time, so notes prioritised significant observations rather than recording every remark. Full per-session notes attached as an appendix.                                                                                           |
| Testing dates                   | 2026-07-18 to 2026-07-23                                                                                                                                                                                                                               |
| Setting                         | One quiet, spacious room, researcher's laptop, moderated one-on-one                                                                                                                                                                                    |
| Tasks                           | 10 guided tasks in fixed order                                                                                                                                                                                                                         |

### 1.2 UAT sample profile (n = 21)

| Attribute                       | Breakdown                                   |
| ------------------------------- | ------------------------------------------- |
| Age                             | 18–24: **19** · 45–54: **1** · 55–59: **1** |
| Gender                          | Female **14** (66.7%) · Male **7**          |
| Knee/ankle discomfort           | None **13** · Ankle **4** · Knee **4**      |
| Prior fitness/health app use    | No **15** · Yes **4** · Not sure **2**      |
| Rehab/physio experience         | No **20** · Yes **1**                       |
| Would consider using it at home | **21 / 21 (100%)**                          |

### 1.3 UAT questionnaire — all 22 items, ranked worst to best

| Q   | Item (short)                                        | Mean     | SD   | ≥4    |
| --- | --------------------------------------------------- | -------- | ---- | ----- |
| 9   | Live on-screen feedback understandable while moving | **3.38** | 0.92 | 12/21 |
| 2   | Camera-placement warning helped fix position        | **3.71** | 1.10 | 15/21 |
| 10  | Live feedback helped me correct my movement         | **3.71** | 1.15 | 12/21 |
| 1   | Movement instructions clear before starting         | **3.90** | 0.62 | 16/21 |
| 15  | Confidence score understandable                     | 4.10     | 0.89 | 16/21 |
| 7   | Easy to start, perform, complete a session          | 4.19     | 0.75 | 17/21 |
| 5   | Interface clean, buttons/labels/icons clear         | 4.29     | 0.56 | 20/21 |
| 13  | Module B grading result easy to understand          | 4.48     | 0.68 | 19/21 |
| 22  | **Overall satisfaction**                            | **4.48** | 0.60 | 20/21 |
| 8   | Smooth and responsive                               | 4.52     | 0.51 | 21/21 |
| 11  | Module A band easy to understand                    | 4.52     | 0.75 | 20/21 |
| 12  | Module A summary aided understanding                | 4.52     | 0.68 | 19/21 |
| 14  | Score/label/band useful                             | 4.52     | 0.68 | 19/21 |
| 16  | Improvement cues useful                             | 4.52     | 0.68 | 19/21 |
| 21  | Non-diagnostic boundary was clear                   | 4.52     | 0.81 | 19/21 |
| 17  | Post-performance report clear and useful            | 4.57     | 0.51 | 21/21 |
| 6   | Navigation easy to follow                           | 4.71     | 0.46 | 21/21 |
| 19  | Progress charts would be useful over time           | 4.71     | 0.56 | 20/21 |
| 20  | Reminder feature would aid adherence                | 4.71     | 0.46 | 21/21 |
| 3   | Felt physically safe                                | 4.81     | 0.40 | 21/21 |
| 18  | Could find and review past sessions                 | **4.90** | 0.44 | 20/21 |

Discomfort (Q4): No discomfort **19**, mild discomfort **2**.

**The headline pattern:** every item covering the _pre-session and during-session_ phase sits at 3.38–3.90. Every item covering the _post-session_ phase sits at 4.48–4.90. State this once, early, in 4.3.3. It is the organising finding of the whole evaluation.

### 1.4 UAT observation themes (X / 18) — ⚠️ SUPERSEDED

> **Do not use this table.** Denominators corrected to 21 on 2026-07-26. Use **§1.4-R**, located in the 4.3.3 plan section below. Retained only for traceability.

| Theme                                                            | Freq  | Type                   |
| ---------------------------------------------------------------- | ----- | ---------------------- |
| SLS task comprehension (ball, lift-line, which leg, 45 s cap)    | 14/18 | UX + comprehension     |
| Movement instructions (too long, unread, wrong position in flow) | 14/18 | UX + content           |
| Session-start ambiguity                                          | 12/18 | Interaction model      |
| Terminology / metrics unexplained                                | 12/18 | Content                |
| Live feedback illegible at distance                              | 11/18 | Visual design          |
| Reminder feature gaps                                            | 11/18 | Feature polish         |
| Camera setup / framing                                           | 10/18 | UX                     |
| Dashboard & progress chart comprehension                         | 9/18  | Data viz               |
| Video demo preferred over text                                   | 8/18  | Content                |
| Error-tag colour semantics (green read as "no error")            | 7/18  | Visual design          |
| Capture-quality trend seen as useless                            | 6/18  | Data viz               |
| **Audio / voice feedback requested**                             | 5/18  | Missing feature        |
| Navigation — missing back buttons                                | 5/18  | UX                     |
| Report — visualise, reorder by importance                        | 5/18  | Data viz               |
| ML prediction / confidence low-value or duplicated               | 4/18  | Content hierarchy      |
| **Non-diagnostic disclaimer not noticed**                        | 4/18  | Ethics / safety        |
| **Squat heel-lift false positives**                              | 3/18  | **Correctness defect** |
| Gamification requested                                           | 3/18  | Feature                |
| **LLM stuck on template fallback / English-only**                | 2/18  | **Correctness defect** |

### 1.5 Requirements survey (n = 20) — findings that drove design

| Finding                                | Value                                                                                                                                     |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Age groups                             | 20–24: 12 · 25–34: 3 · 35–44: 3 · 45–59: 2                                                                                                |
| Self-description                       | General adult 18 (90%) · Athlete/active 9 (45%) · Home-rehab interest 6 (30%) · Caregiver 6 (30%) · Healthcare/physio 2 (10%)             |
| Current guidance source                | Online video/social 15 (75%) · Physio/doctor/coach 10 (50%) · Fitness app/watch 8 (40%) · Family/friends 7 (35%) · Written sheets 6 (30%) |
| **Webcam comfort option**              | **On-device analysis, video not saved: 16/20** · ask permission before saving: 4/20                                                       |
| **Reminder delivery**                  | **Phone or calendar notification: 17/20** · in-app: 3/20                                                                                  |
| Module interest                        | **Both modules: 18/20**                                                                                                                   |
| Device                                 | **Laptop/desktop with webcam: 18/20** · tablet 2/20                                                                                       |
| **Gamification** (mean 2.55)           | Strongly disagree 1 · **Disagree 9** · **Neutral 8** · Agree 2 · Strongly agree 0 → **10 opposed vs 10 not opposed**                      |
| Themes / custom characters importance  | Moderately 11 · Slightly 5 · Very 3 · Least 1                                                                                             |
| Step-by-step guidance before movement  | Strongly agree 14 · Agree 6 (**20/20 positive**)                                                                                          |
| Simple feedback while exercising alone | Agree 11 · Strongly agree 9 (**20/20 positive**)                                                                                          |
| See improvement across sessions        | Agree 10 · Strongly agree 9 · Neutral 1                                                                                                   |
| Reminders aid consistency              | Agree 9 · Strongly agree 6 · Neutral 5                                                                                                    |
| Likelihood to use if it worked well    | 5: 8 · 4: 11 · 3: 1                                                                                                                       |

Non-functional importance (all rated 4–5 by ≥18/20): easy to learn without technical knowledge (11×5, 9×4); clear instructions/buttons/results (10×5, 10×4); fast feedback (11×5, 9×4); works with a normal webcam (9×5, 11×4); results kept private (11×5, 9×4); results persist between visits (5×5, 15×4); warns when camera cannot see the body (9×5, 11×4). **Colourful themes / custom characters is the only item that did not reach "very important" for the majority** — it maps to the gamification finding above.

### 1.6 Dataset and model

| Fact                               | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dataset                            | REHAB24-6, exercise Ex6 (squat)                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Before view filter                 | 195 reps, 9 subjects, 134 Good / 61 Poor (69% / 31%)                                                                                                                                                                                                                                                                                                                                                                                                        |
| After side-view filter             | **98 reps** (50.3%), **72 Good / 26 Poor** (73% / 27%)                                                                                                                                                                                                                                                                                                                                                                                                      |
| Subjects contributing Poor reps    | **6 of 9** (subject 1 contributes 1)                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Cross-validation                   | **Nested subject-grouped CV** — `StratifiedGroupKFold(5, groups=person_id)`. Outer five-fold generally trained on 7 participants and tested on 2 different held-out participants, rotating across folds. Within each outer training set, 3 further subject-grouped folds selected hyperparameters. All repetitions from one participant stayed in the same partition, preventing participant-level leakage. **Not literal LOSO, and not random splitting.** |
| Out-of-fold ROC AUC                | **0.832**                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Brier score after calibration      | **0.149**                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Feature vector                     | **13 dimensions**. Full named list with code identifiers now exists as **Table 7: List of Features** in the user's drafted §3.4.2.2 — use those exact 13 names/codes (e.g. `knee_flex_peak_deg`, `hip_mid_jitter_norm`) everywhere else in the report that refers to individual features, including Chapter 4's feature-importance discussion, so naming stays consistent.                                                                                  |
| Runtime parity (Python vs browser) | Pearson **0.9996**; mean abs diff **5.5 mm**; knee flexion mean diff **0.90°**, max **4.6°**                                                                                                                                                                                                                                                                                                                                                                |
| Far-limb occlusion                 | far-**knee** visibility **0.59–0.78**; far-**ankle** **0.68–0.87**; near-side **0.95–0.99**. If writing "far limb" generally, the correct combined range is **0.59–0.87**. Do not quote 0.59–0.78 as a whole-limb figure.                                                                                                                                                                                                                                   |

### 1.7 Deployed grading configuration

| Fact                             | Value                                                 |
| -------------------------------- | ----------------------------------------------------- |
| Fusion weights                   | **w_rule = 0.0, w_ml = 1.0**                          |
| Decision threshold               | **8.447974**                                          |
| Squat band output                | **Binary: Good / Needs Improvement** (no Fair)        |
| Headline score                   | **10 × good_reps ÷ total_reps** (Stage 5.18)          |
| Set aggregation                  | Strict majority vote of per-rep verdicts (Stage 5.13) |
| Recall (Poor) at operating point | **1.000** — see labelling note below                  |
| Good reps flagged Poor           | **22 / 72 (31%)** — see labelling note below          |

> **⚠️ Labelling correction — do NOT write these as "in-sample".** Both figures are **out-of-fold** predictions from the subject-disjoint 5-fold, so no repetition was scored by a model trained on its own subject. However, **the decision threshold was selected on these same out-of-fold predictions**, so this confusion matrix is _consistent with_ that choice rather than independent evidence _for_ it. A genuinely held-out estimate would need a subject set untouched by both training and threshold selection; with only 9 subjects, that was not available. Write it exactly this way in 4.2.2 — it is a more precise and more defensible statement than either "in-sample" or a bare "out-of-fold".
> | Gate-clean reps ML-rejected, **live** | **17 / 21 (81%)** |
> | Depth gate | **< 78.04°** — the 90° clinical parallel adjusted downward by the measured 11.96° under-read. Clinically anchored, not learned from these labels. |

> **Cross-reference:** this same −11.96° bias (from the mocap validation of bilateral `knee_flex_peak_deg`) is also the primary evidence behind the new bilateral-mean feature-noise limitation in §5.2. Here it justifies a threshold adjustment; there it is additionally read as partial evidence of far-leg noise entering the trained features. **Same measurement, two consistent uses — state both the same way, do not let one contradict the other.**
> | Trunk lean gate | **41.42°** (data-driven, Youden-J) |
> | Heel-rise gate | **0.07098** after Stage R1 (was 0.08399) — data-driven, Youden-J |
> | R1 threshold re-derivation | specificity **0.569 → 0.625** in-sample; sensitivity **0.885 → 0.846** in-sample; sensitivity **0.808** out-of-fold unchanged. Quote all three — the in-sample sensitivity did drop slightly. |

### 1.8 Module A evaluation (SLS **and WBLT**)

> **Corrected 2026-07-28.** Coverage is **two** exercises, not one. **STS is the only check with no agreement harness.**

**SLS — hold time**

| Fact                                    | Value                                                                                                                                                       |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Corpus                                  | Fixed-seed **synthetic** replay corpus, **10 single-leg samples total (6 right leg, 4 left leg)** — _not real pilot recordings_. Do not write "10 per-leg". |
| ICC(2,1), absolute agreement, hold time | **0.995**                                                                                                                                                   |
| Cohen's kappa, hold-time band           | **0.857**                                                                                                                                                   |
| Bland–Altman bias (system − manual)     | **−0.753 s**                                                                                                                                                |
| 95% limits of agreement                 | **[−4.08 s, 2.57 s]**                                                                                                                                       |

**WBLT — toe-to-wall distance**

| Fact                         | Value                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------ |
| Corpus                       | **10 synthetic per-attempt samples, both legs, plus 1 heel-lift-invalid case** |
| ICC(2,1), distance           | **0.9771**                                                                     |
| Bland–Altman bias            | **−0.228 cm**                                                                  |
| 95% limits of agreement      | **[−1.135, 0.678] cm**                                                         |
| Cohen's kappa (McBride band) | **0.7143**                                                                     |
| Additional check             | Angle-vs-distance standardised corroboration check                             |

| Coverage | **SLS and WBLT** have agreement harnesses. **STS has none** — state this as the gap. |
| -------- | ------------------------------------------------------------------------------------ |

> **Both corpora are synthetic.** The word _synthetic_ must appear wherever either set of numbers appears, in both the methodology and the results. WBLT's kappa (0.7143) is also noticeably lower than SLS's (0.857) — worth one sentence of interpretation rather than reporting it bare.

### 1.9-A Module A per-check metrics that actually convert to a label — VERIFIED (from Table 6 revision, 2026-07-29)

> **Source:** user-supplied corrected table, superseding the proposal's version. The proposal's Table 6 listed metrics that were _reported_; the corrected version lists only metrics that _feed the grade_, per explicit instruction: "Key Outputs" means what converts into the band label, not everything the report shows.

| Exercise          | View                 | Reps/Duration                       | What actually converts to the grade                                                           |
| ----------------- | -------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------- |
| **STS**           | Side view            | 5 reps                              | Completion-time band **+** trunk-lean threshold (**>25°**) **+** wobble count → overall grade |
| **Supported SLS** | Front view preferred | **Both legs, 45s hold cap per leg** | Hold score + stability score → **combined score** → grade (**per leg**)                       |
| **WBLT**          | Side view            | **3 trials per leg**                | Distance-to-wall vs. **McBride age/sex norms** → grade                                        |

**Corrections this makes to the proposal's version:**

- STS: "knee ROM band" is **dropped** — not part of the grading path. **Wobble count** and the **>25° trunk-lean threshold** are added — these were not in the proposal at all.
- SLS: hold duration corrected from the proposal's **30s** to the shipped **45s cap per leg** — this also matches the 45s cap already used in the UAT task table (§1.4) and the observation theme table, so this is a real correction, not a new invention. "Hold stability proxy, sway proxy" is replaced with the actual **hold score + stability score → combined score** language, matching the 50/50 weighting already recorded in the 3.4.1 plan below.
- WBLT: "Dorsiflexion ROM band, symmetry proxy" is **dropped from the grading path**. The shipped grade comes from **distance-to-wall vs. McBride norms only**. This is consistent with — not a contradiction of — the existing plan bullet on WBLT's dual output: dorsiflexion angle is a **secondary corroboration signal**, so it correctly does not appear in a "what converts to the grade" table.

> **⚠️ Do not confuse two different trunk-lean thresholds.** STS's own trunk-lean threshold is **>25°**, a Module A metric. This is unrelated to the Module B squat trunk-lean **fault gate** at **41.42°** (§1.7), which is Youden-J data-driven and belongs to an entirely different exercise and module. Keep these clearly separated wherever either is written — using one figure where the other belongs is an easy, examiner-visible slip.

> **Non-negotiable:** the word _synthetic_ must appear wherever these numbers appear, in both the methodology and the results. An examiner who discovers it themselves will treat everything else as suspect.
>
> **⚠️ Already-drafted text needs updating.** Section 3.6.1 (your live report's 3.5.1) was drafted when coverage was believed to be SLS-only. It states "This evaluation method was applied to SLS only; the Sit-to-Stand and Weight-Bearing Lunge Test checks did not have an equivalent agreement harness." **That is now wrong** — WBLT does have one. Fix that sentence and add the WBLT metrics, or the methodology will contradict the results.

---

### 1.9 Normalisation and the capture pipeline — VERIFIED (S10 resolved)

Source: `NORMALISATION_BRIEFING_FOR_AI.md`, verified directly against source code. **This supersedes the proposal's §3.3.4 entirely.**

**What normalisation is for now.** World landmarks are already in real metres, so **camera distance is no longer a reason normalisation is needed** — MediaPipe solves that at the source, before any project code runs. The only remaining job is **cancelling genuine body-size differences between people**: a taller person really does have a longer trunk and a naturally wider stance, in real metres.

| Fact                                                              | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reference length shipped                                          | **`trunk_length`** = distance(shoulder_mid, hip_mid), in metres, averaged across the rep                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Proposal's example (`thigh_length`, hip-to-knee)                  | **Lost the bake-off.** Computed in code only as the losing candidate. **Not** a shipped feature, **not** the reference used. The proposal's worked example must be replaced.                                                                                                                                                                                                                                                                                                                                                            |
| Bake-off method                                                   | Cross-subject **coefficient of variation**, not raw variance (raw variance is scale-confounded — a longer reference shrinks feature and variance together, flattering the longer one for a trivial reason)                                                                                                                                                                                                                                                                                                                              |
| `hip_mid_jitter_norm` CV                                          | trunk **0.1938** vs thigh 0.2130                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `stance_width_norm` CV                                            | trunk **0.1654** vs thigh 0.1881                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Features actually normalised                                      | **Only 2 of 13** — `hip_mid_jitter_norm` (a displacement) and `stance_width_norm` (a length)                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Why only 2                                                        | The other 11 are angles, times, ratios or percentages — they carry no absolute-scale information and were never candidates under either representation                                                                                                                                                                                                                                                                                                                                                                                  |
| Third, non-ML use                                                 | The heel-rise fault gate (`fault_heel_rise_peak_norm`) uses the same trunk-length reference — rule-only, not one of the 13                                                                                                                                                                                                                                                                                                                                                                                                              |
| Honest caveat to keep                                             | World landmarks are themselves an **estimate** from a learned body model, partly regressed toward a canonical body shape. Normalising by a trunk length measured on _that same person in that same session_ cancels whatever per-person scale MediaPipe assigned — which is why the step still measurably helps even though the input is already metric.                                                                                                                                                                                |
| Depth-axis detail                                                 | `hip_mid_jitter_norm` uses `in_plane=True`, deliberately dropping the z-axis — consistent with treating depth as the least reliable axis even under the metric representation                                                                                                                                                                                                                                                                                                                                                           |
| **Mocap validation, bilateral `knee_flex_peak_deg` vs OptiTrack** | **Bias −11.96°; 95% LoA [−21.00°, −2.94°]; Pearson r = 0.956.** Same measurement used in two places: justifies the depth gate's 90°→78.04° adjustment (§1.7), and is the primary evidence for the bilateral-mean feature-noise limitation (§5.2). Some of the ~18°-wide spread is plausibly attributable to far-leg noise entering the bilateral mean, though this has not been isolated from other error sources (e.g. definitional differences between MediaPipe's and OptiTrack's joint centres) — do not overclaim the attribution. |

> **⚠️ Structural finding: normalisation is NOT a preprocessing step.** `_norm_ref()` lives in `features.py` and runs at **feature-extraction** time, using a per-rep average. The proposal places it as stage 4 of the preprocessing pipeline (§3.3.4), which is now incorrect. **Recommendation:** keep a short §3.3.4 explaining the concept, but state plainly that it is applied during feature extraction rather than in the preprocessing pass, and cross-reference §3.4.2. This avoids restructuring the existing table of contents.

**Verified capture pipeline — the actual order.** The proposal's §3.3 order (filter → interpolate → smooth → normalise) is _substantially_ right but imprecise in three places.

| Step                              | Verified mechanics                                                                                                                                                                                                                                                                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. Image-space `landmarks`        | Smoothed by a **4-frame rolling mean** (`createLandmarkSmoother(4)`). Used **only** for skeleton rendering and capture-quality checks. Never for angles.                                                                                                                                                                                   |
| 2. `worldLandmarks`               | Taken **raw** from MediaPipe, with **no client-side smoothing at all**                                                                                                                                                                                                                                                                     |
| 3. Module B payload               | **Only** `{timestampMs, worldLandmarks}` sent to the backend. No image-space landmarks on the wire.                                                                                                                                                                                                                                        |
| 4. Backend preprocessing          | Docstring order: **"Confidence filter → gap fill → One Euro."** `MIN_VISIBILITY = 0.6`; `interpolation_max_gap_frames = 5`                                                                                                                                                                                                                 |
| 4a. Gap fill                      | Runs of ≤5 low-visibility frames linearly interpolated between anchors                                                                                                                                                                                                                                                                     |
| 4b. Release persistent occlusions | For runs **longer** than 5 frames, visibility is raised to _exactly_ `MIN_VISIBILITY` so the smoother treats the landmark as barely-valid and smooths its own uncertain trajectory, **rather than freezing it** at a stale position for the rest of a rep. Justification: a persistently occluded landmark "is low-confidence, not wrong." |
| 4c. One Euro                      | Shared `LandmarkSmoother` reused from Module A — **not forked**, so the two pipelines cannot silently drift apart. By this point nothing is below `MIN_VISIBILITY`, so its hold-last branch never fires; it purely smooths.                                                                                                                |
| 5–6. Downstream                   | Preprocessed world stream → rep segmentation → 13 features + 3 fault gates                                                                                                                                                                                                                                                                 |

> **Precision point worth writing:** "releases long occlusions" is **not** a fourth stage after One Euro. It runs _between_ gap-fill and One Euro, specifically so that One Euro's smoothing — rather than a freeze — is what happens to long-occluded landmarks.

> **Capture-quality integrity — a good detail to include.** The session capture-quality score is computed on the **raw** frames upstream, _before_ any gap-fill, release or smoothing runs. This is deliberate: it means the preprocessing pipeline's own occlusion handling can never inflate the quality number a user sees. Stating this pre-empts an obvious examiner question about whether the system flatters its own capture metric.

---

## 2. WHAT YOU STILL NEED TO SUPPLY

| #       | Item                                                                                                                                                                                                                                                                                                                                                                 | Blocks       | Status                                                                                                                                |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| S1      | Four squat detection screenshots (§4.2.4 — capture protocol in this plan)                                                                                                                                                                                                                                                                                            | 4.2.4        | Outstanding                                                                                                                           |
| S2      | Frontal-view phone photo proving valgus in the S1 quadrant-4 set                                                                                                                                                                                                                                                                                                     | 4.2.4        | Outstanding                                                                                                                           |
| S3      | UI screenshots: landing, dashboard, instruction page, camera setup, live session (all 4 exercises), report, history, progress, reminders                                                                                                                                                                                                                             | 4.3.1        | Outstanding                                                                                                                           |
| S4      | Before/after screenshot pairs for R4, R8, R9, R11, R12, R13                                                                                                                                                                                                                                                                                                          | 4.3.4        | Outstanding                                                                                                                           |
| S5      | Live deployment URLs (Vercel / Render) + confirmation of demo LLM state (on or off)                                                                                                                                                                                                                                                                                  | 3.5, 4.3.1   | Outstanding                                                                                                                           |
| S6      | Final backend/frontend test counts as of submission                                                                                                                                                                                                                                                                                                                  | 4.3.2        | Have 343 backend / 56 frontend at Stage R13 — confirm final                                                                           |
| S7      | Live-quoted figures from `SLS_EVALUATION_REPORT.md` and `SQUAT_EVALUATION_REPORT_2BAND.md`                                                                                                                                                                                                                                                                           | 4.2.2, 4.3.2 | Re-run done — need the numbers pasted                                                                                                 |
| S8      | Whether Chapter 2 §2.5.2 (Moamen et al.) has full APA details in your reference list                                                                                                                                                                                                                                                                                 | 4.4          | Outstanding                                                                                                                           |
| S9      | Which proposal reference the Transformer deviation row should cite (Table 7 is _Libraries and Tools_; the claim sits in §3.4.2.1 body text)                                                                                                                                                                                                                          | 3.4.3.4      | Needs your check                                                                                                                      |
| ~~S11~~ | ~~EC3D in F3.9~~                                                                                                                                                                                                                                                                                                                                                     | F3.9         | ✅ **RESOLVED 2026-07-29 — dropped entirely.** Included in the supplied flow by mistake. No external-validation step appears in F3.9. |
| S10     | ~~Segment-length normalisation role~~                                                                                                                                                                                                                                                                                                                                | 3.3          | ✅ **RESOLVED 2026-07-28** via `NORMALISATION_BRIEFING_FOR_AI.md` — see §1.9 below                                                    |
| **S12** | **New citation in your written 3.4.2.3: "Straub & Powers, 2024," cited to justify the 90° knee-flexion parallel-squat reference for the depth gate.** I have not verified this citation — I don't know if it's a real, correctly-dated source or a placeholder. **Verify before submission**, since an unverifiable or incorrect citation is worse than no citation. | 3.4.2.3      | **Needs your verification**                                                                                                           |

---

# CHAPTER 3 — METHODOLOGY

Seven major sections. Proposal 3.5/3.6/3.7 collapse into a single 3.6.

---

## 3.1 Methodology Overview and Research Approach — **REVISE + ADD**

**Why:** the proposal's overview is sound in intent but written in future tense and describes a system that changed in four material ways. The _ADD_ part is the design-science framing, which currently appears nowhere. If DSRM first shows up in Chapter 4 it reads as retrofitted; introduced here, Chapter 4 can legitimately close the loop.

**Content to write:**

- Restate project purpose and the non-diagnostic boundary in past tense. Retain the proposal's reasoning about monocular limitations (self-occlusion, viewpoint sensitivity, imperfect depth) — it aged well and is confirmed by your own measurements.
- **New:** name Design Science Research Methodology (Peffers et al., 2007) as the research approach and map its six activities onto what you actually did:

| DSRM activity                          | What this project did                                                                           |
| -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 1. Problem identification & motivation | Ch1 problem statement + Ch2 gaps (2.2.3 self-monitoring gap, 2.3.3 limits of existing tools)    |
| 2. Define objectives of a solution     | Project goals §1.3.3 + **requirements survey, n = 20** (§3.4.3.1)                               |
| 3. Design & development                | Modules A and B, web application (§3.3–§3.5)                                                    |
| 4. Demonstration                       | Working deployed system, 4 exercises end-to-end (§4.1, §4.3.1)                                  |
| 5. Evaluation                          | Measurement agreement, ML evaluation, application testing, UAT with 21 users (§3.6, §4.2, §4.3) |
| 6. Communication                       | This report; findings fed back into twelve implemented enhancements (§4.3.4)                    |

- **Two-track evidence design.** State explicitly that evaluation used two independent streams — structured self-report and direct behavioural observation — so findings could be triangulated rather than resting on self-report alone. This is a methodological strength; name it as one.

**Figures:** **F3.1 (NEW)** DSRM six-step cycle annotated with this project's activities. **F3.2 (REDRAW)** high-level system workflow — replaces proposal **Figure 6**.

### What to retain, revise and cut from your current §3.1

| Current passage                                                                     | Action                                                                                                                                                                                                                                                            |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Opening paragraph (non-diagnostic helper, conservative explainable outputs)         | **RETAIN**, tense-fix. Strong framing that aged well.                                                                                                                                                                                                             |
| "a 2D angle and a single-camera setup will have unavoidable limitations"            | **REVISE** — the limitations (self-occlusion, viewpoint sensitivity, imperfect depth) are all still correct and now _measured_. But "2D angle" is wrong: angles come from world landmarks. Reword to "single-camera monocular capture" and keep every limitation. |
| "MediaPipe Pose to extract 2D body landmarks"                                       | **REVISE** → world landmarks                                                                                                                                                                                                                                      |
| "normalisation to minimize scale differences across users **and camera distances**" | **REVISE** — camera distance is no longer the reason (D13). Body size only.                                                                                                                                                                                       |
| "the Transformer model will function as a rewriting layer"                          | **REVISE** → hosted LLM API, Module B only, **off by default** (D3)                                                                                                                                                                                               |
| Module A / Module B walkthrough                                                     | **RETAIN**, tense-fix — the pipeline description is still accurate                                                                                                                                                                                                |
| _(missing)_                                                                         | **ADD** — the DSRM six-activity framing and mapping table                                                                                                                                                                                                         |

**Figure 6 must be redrawn — but stays high-level, same granularity as before.** Your uploaded version is the proposal original. Four label-level corrections are needed, each a swap within the existing box structure, not a restructuring: (1) "MediaPipe Pose (**2D landmarks**)" → world landmarks; (2) "Rewrite polished feedback using **Transformer model**" → hosted LLM, default off; (3) "**Weighted score**" → relabel to reflect the shipped gated fusion (w_rule = 0), not the planned 60/40 split; (4) Module B's box scope → **squat only**, not a generic exercise. Keep the existing visual language — the colour-banded swimlanes (blue shared, green Module A, orange Module B, yellow metrics) read well and should be preserved.

**The browser/backend split and preprocessing internals do NOT belong in Figure 6.** That level of detail — where MediaPipe runs, the confidence filter/gap-fill/release/One Euro chain, where normalisation actually happens — is covered by text in §3.3.1–§3.3.4, not by a diagram. Figure 6's "Shared Pre-processing" block can stay as a single box, unchanged in granularity; only its label needs to be accurate in the ways listed above. Do not expand Figure 6 to show this level of detail.

---

## 3.2 Dataset Selection and Preparation — **REVISE**

**Why:** the proposal's _criteria_ were correct and were genuinely applied. What changed is that a specific dataset was chosen, a camera-view filter was applied, and one planned exercise was dropped.

**Placement decision (locked):** Chapter 3 carries the _method_ — the criteria, why REHAB24-6 satisfied them, the view-filter procedure, label mapping, and the subject-level split rule. Chapter 4 carries the _outcome_ — 98 reps, the per-subject table, the class imbalance, and the feature-validity findings. Rationale: a reader must be able to reproduce the selection from Chapter 3 alone, and the inverted-depth finding is a _result_, not a method.

**Content to write:**

- Retain the three selection criteria (biomechanical chain visible; single consistent exercise; labels mappable to the project's grading output). They held up.
- Name REHAB24-6 and Ex6 (squat). State the side-view filter and _why_: the system is designed around one true sagittal view, and mixing camera geometries would break the feature contract.
- Record the deliberate trade-off: a smaller, geometrically consistent cohort was preferred over a larger, mixed one.
- Label mapping: binary correct/incorrect → Good/Poor, straightforward here.
- Subject-level splitting rule, and _why_ (pose patterns are person-specific; mixing subjects across splits inflates accuracy).
- **External validation attempt.** One short paragraph, past tense: a comparison against an independent dataset was attempted and abandoned, because the two sources were incompatible in coordinate format and in how each defined a faulty squat. No external validity claim is therefore made in either direction, and the remaining effort was directed at live webcam evidence, which does not carry that problem. **Do not name the dataset. Do not present it as validation.**

**Figures:** none required. A one-line criteria table is optional.

### What to retain, revise and cut from your current §3.2

Your live §3.2 is still the proposal version — entirely future tense, and it describes a _search strategy_ rather than the dataset you actually used.

| Current passage                                                                                | Action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Opening ("functional checking relies on deterministic rules and requires no training data...") | **RETAIN**, tense-fix. Still true and a good framing.                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Public-dataset-first rationale                                                                 | **RETAIN**, tense-fix                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| The three criteria                                                                             | **RETAIN** — they held up and were genuinely applied                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Offline MediaPipe conversion pipeline                                                          | **REVISE** — keep the reasoning, but state it as what was done, and note the extraction ran on world landmarks                                                                                                                                                                                                                                                                                                                                                                                              |
| "Picture-based datasets... MediaPipe to extract keypoints from each image offline"             | **CUT** — no image-based dataset was used. This is unrealised planning.                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| "Kinect/Vicon skeleton coordinates are inconsistent with MediaPipe coordinates"                | **REPURPOSE — decision confirmed.** Rewrite this from a hypothetical worry into **the actual reason the external comparison was abandoned**. The proposal already anticipated the problem; the honest move is to say the anticipated incompatibility is exactly what materialised in practice, alongside a second incompatibility in how each source defined a faulty squat. **Do not name the dataset.** This turns an unrealised planning paragraph into a documented negative result, which is stronger. |
| Label alignment discussion                                                                     | **REVISE** — replace the generic multi-format discussion with the single mapping actually used: binary correct/incorrect → Good/Poor                                                                                                                                                                                                                                                                                                                                                                        |
| _(missing)_                                                                                    | **ADD** — name REHAB24-6 Ex6; the side-view filter and its effect; the nested subject-grouped CV split rule from §1.6                                                                                                                                                                                                                                                                                                                                                                                       |

---

## 3.3 Pose Estimation and Data Preprocessing — **REVISE (3.3.1–3.3.3, 3.3.5) + DELETE 3.3.4**

**Why:** the pipeline stages are substantially as planned, and 3.3.1–3.3.3 need only tense and precision fixes. **§3.3.4 Normalisation is removed from this section entirely** — it runs at feature-extraction time, not in preprocessing (D16), so its content relocates to §3.4.2.

> **TOC consequence:** §3.3 drops from five subsections to four. Old §3.3.5 "Output of preprocessing" becomes **§3.3.4**. Renumber accordingly.

### Subsection-by-subsection action table

| Existing subsection                                 | Action                      | What changes                                                                                                                                                                                                                                                                                                                    |
| --------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| §3.3 intro                                          | **REVISE**                  | "2D landmark coordinates" → world landmarks for all angle/length computation. Keep the MediaPipe-vs-MoveNet-vs-YOLOv8 justification (it aged well). Add the runtime-parity result (Pearson 0.9996) as new empirical support the proposal did not have.                                                                          |
| Figure 7 (33 landmarks)                             | **RETAIN, recaption**       | Caption must note that **world landmarks**, not the normalised image coordinates shown, feed angle and feature computation                                                                                                                                                                                                      |
| §3.3.1 Confidence filtering                         | **REVISE**                  | Threshold 0.6 confirmed as shipped (`MIN_VISIBILITY = 0.6`). Keep Equations 1–2 and Tables 3–4. Add: capture quality is computed on **raw** frames upstream, so preprocessing cannot inflate it. **Fix the two broken "Error! Reference source not found." cross-references.**                                                  |
| §3.3.2 Missing keypoint handling                    | **REVISE**                  | 5-frame cap confirmed (`interpolation_max_gap_frames = 5`). Keep Equation 3. **Add the release mechanism** — runs longer than 5 frames have visibility raised to exactly 0.6 so the smoother smooths their real trajectory rather than freezing a stale position.                                                               |
| §3.3.3 Smoothing                                    | **RETAIN**                  | One Euro and Casiez et al. (2012) confirmed as shipped. Equations 4–6 stand. Add one line: the smoother is **shared** with Module A, not forked, so the two pipelines cannot drift apart. Note separately that image-space landmarks get a different, simpler 4-frame rolling mean used only for rendering and capture quality. |
| §3.3.4 Normalisation                                | **DELETE — move to §3.4.2** | See the §3.4.2 entry below for what to write there                                                                                                                                                                                                                                                                              |
| §3.3.5 Output of preprocessing → **becomes §3.3.4** | **REVISE**                  | Keep the shared-backbone argument, it is good. Fix tense and the broken cross-reference. Remove any mention of normalisation from the output description, since it no longer happens here.                                                                                                                                      |

**No new figure for this section.** F3.3 (preprocessing pipeline diagram) is not needed — text description in §3.3.1–§3.3.4 is sufficient.

---

### §3.4.2 addition — Feature-scale normalisation (relocated from §3.3.4)

All facts from §1.9. Write as a short subsection inside Module B's feature design, since that is where it actually runs.

1. **What it does and why.** World landmarks arrive in real metres, so camera distance is already solved at source by MediaPipe before any project code runs. The remaining job is **cancelling genuine body-size differences between people** — a taller person really does have a longer trunk and a naturally wider stance, in real metres.
2. **The reference and the bake-off.** `trunk_length` = distance(shoulder_mid, hip_mid), averaged across the rep. Thigh length — the proposal's original worked example — was tested and **lost** on cross-subject coefficient of variation (`hip_mid_jitter_norm` 0.2130 vs **0.1938**; `stance_width_norm` 0.1881 vs **0.1654**). Report the losing candidate; it is stronger than silently swapping the example. Note the method choice too: CV rather than raw variance, because raw variance is scale-confounded — a longer reference shrinks feature and variance together and would flatter the longer reference for a trivial reason.
3. **Scope.** Only **2 of the 13** features are normalised — `hip_mid_jitter_norm` (a displacement) and `stance_width_norm` (a length). The other 11 are angles, times, ratios or percentages, which carry no absolute-scale information and were never candidates. A third, non-ML signal — the heel-rise fault gate — uses the same reference.
4. **The honest caveat.** World landmarks are themselves a learned estimate, partly regressed toward a canonical body shape. Normalising by a trunk length measured on _that same person in that same session_ cancels whatever per-person scale MediaPipe assigned, which is why the step still measurably helps even though the input is already metric.
5. **Depth-axis detail.** `hip_mid_jitter_norm` uses `in_plane=True`, deliberately dropping the z-axis — consistent with treating depth as the least reliable axis even under the metric representation.

**Also handle D14 and D15 here**, since both were §3.3.4 claims and both concern feature design:

- **D14 — exact degrees.** State the shipped behaviour and justify it rather than treating it as a slip. The Report displays exact values _alongside_ their bands, which is more informative than a band alone; the non-diagnostic boundary is carried by the disclaimer and the always-visible badge rather than by withholding numbers.
- **D15 — viewpoint.** Use this framing: the proposal expected relative features that remain stable _under_ viewpoint changes. The build instead enforces one required viewpoint (`required_view: "side_view"`) and gates out any frame failing a positioning check. So rather than tolerating a varying viewpoint, it prevents a non-compliant viewpoint being captured at all — **same goal, opposite mechanism: restrict rather than absorb.** This connects directly to the side-view dataset filter in §3.2.

---

## 3.4 System Development

### 3.4.1 Module A: Rule-Based Functional Quantification — **REVISE**

**Why:** built substantially as planned. Additions rather than reversals.

**Content:**

- The three checks: Sit-to-Stand, Single-Leg Stance, Weight-Bearing Lunge Test. **Replace the protocol table with the corrected version** (§1.9-A) — this is a content change, not just a tense fix, since the proposal's version listed metrics that are reported but do not feed the grade.

_Table 6 (corrected): Functional Exercise Checking Protocol_

| Testing Exercise    | View Guidance        | Reps / Duration                 | Key Outputs (→ label)                                                             |
| ------------------- | -------------------- | ------------------------------- | --------------------------------------------------------------------------------- |
| Sit-to-Stand (STS)  | Side View            | 5 reps                          | Completion-time band + trunk-lean threshold (>25°) + wobble count → overall grade |
| Supported SLS       | Front view preferred | Both legs, 45s hold cap per leg | Hold score + stability score → combined score → grade (per leg)                   |
| WBLT (knee-to-wall) | Side View            | 3 trials per leg                | Distance-to-wall vs. McBride age/sex norms → grade                                |

**Rewrite the surrounding prose to match, not just the table.** Specifically: (1) drop any mention of an STS knee-ROM band feeding the grade — it does not; (2) name the STS wobble count and the >25° trunk-lean threshold explicitly, since neither appeared in the proposal; (3) correct SLS's hold duration from the proposal's 30s to the shipped 45s cap, and describe it as per-leg; (4) for WBLT, describe the grade as coming from distance-to-wall banded against McBride norms, and do **not** describe dorsiflexion ROM as feeding the grade — it is a secondary corroboration signal only (see the WBLT dual-output bullet below), which is why it is correctly absent from the "Key Outputs" column.

- Metric computation per check, conservative banding, and the capture-quality gate Q. Retain the reasoning: rather than issue a misleading band on poor capture, the system flags low confidence and prompts a camera fix.
- **ADD — WBLT dual output.** User-measured toe-to-wall distance banded against McBride et al. (2026) age/sex percentile norms, plus camera-measured dorsiflexion angle as a secondary corroboration signal. State the dependency: this requires the account's exact age, and accuracy depends on the user measuring correctly.
- **ADD — SLS combined scoring.** Hold time and stability weighted 50/50, chosen because a proportion-only stability score would reward a short perfect hold over a longer imperfect one. This is a good design-reasoning paragraph; write it.
- **ADD — symmetry index is report-only.** Kept out of graded sub-scores because it measures longitudinal balance rather than per-rep quality, and would penalise the asymmetry that is clinically expected during rehabilitation. **This is also why symmetry does not appear in the corrected Table 6** — it is reported, but it does not convert into any exercise's grade.
- Session summary and trend summary generation, stored via backend APIs.

**Figures:** **F3.4 (NEW)** Module A per-check flow — capture → preprocess → metric → capture-quality gate → band → store → trend. **Mermaid source only — no PNG needed for this figure.**

---

### 3.4.2 Module B: Hybrid Rehabilitation Grading — **REWRITE**

**Why:** the largest divergence in the chapter. Four planned elements did not survive contact with the data: Good/Fair/Poor output, the 60/40 fusion weighting, the headline-score definition, and two exercises. The pipeline shape survived; the decision logic did not.

### Subsection-by-subsection action table

The proposal has 3.4.2.1–3.4.2.7. Per decision (revised 2026-07-29), **3.4.2.7 (Libraries and Tools) moves out to become part of §3.4.4**, a new capstone section, rather than §3.4.3 — see §3.4.4 below for why. That leaves six subsections here.

| Proposal subsection                                         | Action                                  | What changes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **3.4.2.1** Hybrid Model Architecture                       | **REVISE**                              | **Retain** the explicit exercise-selection justification (avoids viewpoint-sensitive detection under a monocular camera) — it aged well and is now empirically backed by D15. **Change:** "MediaPipe will extract 2D landmarks" → world landmarks. **Change:** "the Transformer rewriting layer" → hosted LLM API, Module B only, **off by default**. **Retain** the point that the rewriting layer is not a decision layer and runs only after the set — that is still exactly true and is a good design argument. Figure 8 → **F3.5 redraw**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **3.4.2.2** Interpretable Feature Design                    | **REVISE + ABSORB**                     | **Retain** the whole justification paragraph (traceable, less sensitive to visual noise than raw pixels). **Change:** "extracted consistently from 2D landmarks" → world landmarks. **ADD:** the 13 features by family. **ABSORB the relocated normalisation content from §3.3.4** here (D13, D16) plus **D14** (exact degrees) and **D15** (fixed viewpoint, restrict-not-absorb) — all three were §3.3.4 claims and all three concern feature design, so this is their new home.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **3.4.2.3** Rule-based Sub-score Design                     | **REVISE — see rewrite guidance below** | The three sub-scores survive, but the proposal's stated _purpose_ for them is wrong. See the dedicated rewrite block after this table.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **3.4.2.4** Machine Learning Workflow _(offline training)_  | **REWRITE**                             | Largest single rewrite in the section. **Change:** three-band Good/Fair/Poor label normalisation → binary Good/Poor. **Change:** "participant-level splitting" → the nested subject-grouped CV wording from §1.6. **⚠️ MOVED (2026-07-29):** class-imbalance handling (`class_weight="balanced"`, no SMOTE, and the reasoning against synthetic oversampling) is **discussed in Chapter 4, not here** — Chapter 3 states the method was used; the discussion of _why_ belongs with the results. **REMOVE:** any standardisation step — Extra Trees does not require it. **Retain** the Extra Trees justification and the UI-PRMD/KIMORE precedent — **but state the correlated-features tolerance as a general property of the algorithm only, without asserting the specific r = 0.97 finding, which belongs in §4.2.1.** **Add the no-bake-off decision** as a method-level statement, forward-referencing §4.2.1 for the exact sample composition rather than restating 98 reps / 26 Poor / 6 subjects here. **ADD:** probability calibration after fitting; **ADD:** threshold and fusion-weight selection on out-of-fold predictions. Figure 9 → **F3.9 revision**. |
| **3.4.2.5** Machine Learning Workflow _(runtime inference)_ | **REVISE + RENAME**                     | **⚠️ The proposal gives 3.4.2.4 and 3.4.2.5 the identical title, "Machine Learning Workflow."** They must be distinguishable. **Recommended: "Runtime Model Inference."** Avoid "Model Deployment" — see the naming note below. **Retain** the exercise-specific model design and the argument against automatic exercise recognition — both still hold. **Change:** the three predicted outputs are still label, confidence and error tags, but state that **only the squat model ships**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **3.4.2.6** Grading Output Design                           | **REWRITE**                             | **Change:** Equation 6's weighted fusion (`w_rule + w_ml = 1`) → the shipped **gated** fusion with `w_rule = 0`; explain that the rule contribution was _relocated_ to the independent fault gates rather than removed. **Change:** Table 6's three bands → **the two-band table below**. **ADD:** set aggregation by strict majority vote, and the headline score `10 × good_reps ÷ total_reps`. **Change:** "Transformer rewriting layer" → hosted LLM, default off.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **3.4.2.7** Libraries and Tools                             | **MOVE → §3.4.4**                       | Tech stack, not grading model, and its scope spans both modules plus the web app — too broad for a subsection nested inside §3.4.3. See §3.4.4.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

### §3.4.2.3 rewrite guidance — what the shipped system actually does

The proposal states that the three sub-scores act as a safety net: _"if the camera angle is bad and leads to the machine learning model being unable to grade, these hard-coded rules will ensure the user still receives immediate, safe, and accurate feedback."_ **No part of that describes the shipped system.** Write it as follows instead.

**1. What the three sub-scores are.** Retain the definitions unchanged — they are still computed on every repetition:

- **Completeness (ROM):** did the user reach the required depth?
- **Consistency (Tempo):** was repetition speed steady?
- **Control (Stability):** was there excessive sway or jitter?

**2. What they actually do now.** They are computed and **reported for transparency**, so a user can see which aspect of technique the system measured. They **do not** contribute to the deployed squat verdict, because the fusion weight resolved to `w_rule = 0`. Forward-reference §4.2.3 for the evidence, but do not explain the inversion here — that is a result, not a method.

**3. The correction that matters — the protective role moved, it did not disappear.** This is the paragraph to get right, because it turns an apparent contradiction into a coherent design story. Three separate mechanisms now cover what the proposal assigned to the sub-scores:

| Concern the proposal gave to sub-scores | What actually handles it                                                                                                                   |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Camera angle bad, pose unreliable       | **Capture-quality gate `Q`** (§3.3.1) — flags low confidence and asks the user to retry, rather than grading on bad input                  |
| Unsafe or clearly faulty technique      | **Fault gates** — insufficient depth, excessive forward lean, heel lift. These run **independently of the classifier and can override it** |
| Traceability of the grade               | The **sub-scores themselves**, now reported rather than weighted                                                                           |

So the honest framing is that **the rule-based contribution was relocated, not removed.** A rule layer still constrains the final verdict; it simply does so through gates that can veto a repetition outright, rather than through a weighted term inside a fused score. State this explicitly — it is also the answer to the obvious examiner question of whether `w_rule = 0` abandons the hybrid architecture, and §4.2.3 makes the same argument from the results side.

**4. What not to write.** Do not describe the sub-scores as a fallback, a safety net, or a guarantee of accurate feedback when the model fails. Do not imply they influence the band. Both claims are contradicted by §4.2.3.

### Naming note — why not "Model Deployment and Inference"

In machine-learning usage, _model deployment_ means putting a trained model into a running system so it can serve predictions, which this project genuinely did — the backend loads the versioned `model.joblib` artifact at runtime. So the term would not be factually wrong.

It is still the weaker choice here, for two reasons. Firstly, **"deployment" in this report already means something else.** §3.5 covers infrastructure deployment to Vercel, Render and Neon. Using the same word for a subsection about model inference invites a reader to expect hosting content and find prediction logic instead. Secondly, **the subsection's actual content is inference**, not deployment: the frontend sends the exercise type, the backend loads the matching artifact, and the model returns a label, a confidence value and error tags. Nothing in it describes shipping the system anywhere.

**Recommended: "Runtime Model Inference."** Unambiguous, describes exactly what the subsection covers, and does not collide with §3.5. Acceptable alternatives are "Exercise-Specific Model Inference" or "Model Loading and Inference." **To be explicit: renaming this subsection does not create any new deployment work.** It is a heading change only.

### Replacement band table (supersedes proposal Table 6)

> **Numbering confirmed 2026-07-29.** In the live report this is **Table 7: Threshold for Each Band** (page 53). No placeholder needed.

_Table 7: Threshold for each band_

| Displayed band        | Internal band | Condition                                                                         |
| --------------------- | ------------- | --------------------------------------------------------------------------------- |
| **Needs Improvement** | `Poor`        | `0 ≤ final score ≤ 5` — half or fewer of the reps passed both ML and fault gates  |
| **Good**              | `Good`        | `5 < final score ≤ 10` — a strict majority of reps passed both ML and fault gates |

**Two points to write alongside this table.** First, the boundary sits at exactly 5 because the score is a rate — `10 × good_reps ÷ total_reps` — so 5 is the arithmetic midpoint and a **tie resolves to Poor**, which is the conservative direction. Second, state plainly that the planned Fair band was removed, and forward-reference §4.2.3 for the evidence.

**Content to write, in this order:**

1. **Pipeline.** User selects mode and exercise explicitly rather than the model detecting it — retain this justification, it is good (avoids viewpoint-sensitive misclassification and keeps the architecture simple). Then: capture → MediaPipe world landmarks → shared preprocessing → repetition segmentation → 13-feature vector per rep → rule sub-scores + calibrated classifier → fault gates → per-rep verdict → set aggregation.
2. **Interpretable feature design.** Retain the proposal's justification (traceable, less sensitive to visual noise than raw pixels). State the 13 features by family: peak and ROM knee flexion, hip flexion, trunk lean, angular velocity, rep timing, normalised jitter, stance width.
3. **Rule-based sub-scores.** ROM completeness, tempo consistency, stability control. **Say here that they are retained for transparency but carry zero fusion weight in the deployed squat verdict**, and forward-reference 4.2.3 for why. Do not explain the inversion here — that is a result.
4. **Classifier choice.** Extra Trees. Justify on: small tabular feature set, subject-independent CV feasible at this size, feature importances are reportable as evidence, tree ensembles tolerate correlated inputs in general (do not assert the specific correlated-pair finding — that is Chapter 4's). Cite the Ch2 §2.5.2 precedent. **State the no-bake-off decision** as a method-level fact, forward-referencing §4.2.1 for the exact sample composition (98 reps / 26 Poor / 6 subjects) rather than restating those numbers in Chapter 3.
5. **Calibration and threshold.** Subject-independent 5-fold; calibration applied; single decision threshold selected on out-of-fold predictions by maximising macro-F1.
6. **Fault gates.** Depth, trunk lean, heel-rise. State which are data-driven (lean, heel-rise; Youden-J) and which is clinically anchored (depth), and that depth could not be learned from this dataset. Describe R1's near-leg-only construction: camera-side leg by visibility, 3-frame settling-window baseline, sustained across 3 frames, refuses to fire under occlusion.
7. **Set aggregation and headline score.** Strict majority vote across per-rep verdicts. Score = 10 × good_reps ÷ total_reps. State _why voting rather than averaging_: the threshold was calibrated on individual reps, and a mean across reps has a much narrower spread, so the same cut would mean something different.
8. **Binary output.** Squat commits to Good / Needs Improvement with no Fair band. State that this was a revision from the planned three-band design and forward-reference 4.2.3.
9. **Live feedback strategy.** Lightweight client-side estimators mirror the backend gates for immediate cues; the authoritative recompute happens server-side at set end. No heavy backend round-trip during the set.

### F3.5 — Module B pipeline (redraws proposal Figure 8)

Seventeen steps, verified against the shipped implementation. Steps marked **ADD** are not in the proposal's Figure 8 and must be introduced.

| #   | Step                                                       | Note                                                                                            |
| --- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 1   | User explicitly selects **Rehabilitation Grading → Squat** | Matches proposal. Avoids viewpoint-sensitive exercise detection.                                |
| 2   | Webcam capture                                             | Matches. Video stays in the browser.                                                            |
| 3   | MediaPipe Pose → **world landmarks**                       | Corrected from 2D.                                                                              |
| 4   | Live capture-quality and lightweight cues                  | **ADD.** Frontend shows framing, visibility, rep count, rough cues only.                        |
| 5   | Finish set → send buffered landmarks to backend            | **ADD.** Full grading occurs after the set, in one request.                                     |
| 6   | Assess **raw** capture quality `Q`                         | **ADD, before preprocessing.** Quality measured on the original capture — consistent with §1.9. |
| 7   | Shared preprocessing                                       | Confidence filter → gap-fill (≤5 frames) → One Euro.                                            |
| 8   | Repetition segmentation                                    | Knee-angle FSM separates complete reps.                                                         |
| 9   | Extract **13 features** per rep                            | Matches.                                                                                        |
| 10  | Rule sub-scores: ROM, tempo, stability                     | Reported for transparency; `w_rule = 0`.                                                        |
| 11  | Calibrated Extra Trees → `P(Good)` per rep                 | Every rep classified independently.                                                             |
| 12  | Fault gates per rep                                        | Insufficient depth, excessive forward lean, heel lift.                                          |
| 13  | Per-rep verdict                                            | `Good` only when ML passes **and** no fault gate fails.                                         |
| 14  | Set aggregation                                            | Strict majority vote. **A tie becomes Poor.**                                                   |
| 15  | Final score and band                                       | `10 × good ÷ total`; Good or Needs Improvement.                                                 |
| 16  | Error tags and feedback                                    | **ADD.** Ranked tags → template feedback → optional safety-checked LLM rewrite.                 |
| 17  | Store result, display report/trend                         | Stored in PostgreSQL, returned to the report page.                                              |

### F3.9 — ML training pipeline (revises proposal Figure 9)

| Proposal element         | Current implementation                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| Public dataset           | REHAB24-6 videos, repetition metadata, labels, subject IDs                                             |
| Landmark/pose data       | MediaPipe **world landmarks** from side-view squat videos                                              |
| Preprocessing            | Same runtime pipeline: confidence filter → short-gap interpolation → One Euro                          |
| Feature extraction       | 13 ordered features per labelled repetition                                                            |
| General train/test split | **Replace with** subject-grouped nested cross-validation                                               |
| LOSO                     | **Not literally used.** `StratifiedGroupKFold(5)`, because some subjects contain only Good samples     |
| Standardisation          | **Remove.** Extra Trees does not require it                                                            |
| Oversampling / SMOTE     | **Remove if shown.** Uses `class_weight="balanced"`, no SMOTE                                          |
| Model training           | Extra Trees with inner subject-grouped grid search on ROC AUC                                          |
| Calibration              | **ADD after fitting:** sigmoid/Platt probability calibration                                           |
| Testing                  | Outer out-of-fold predictions → ROC AUC, macro-F1, recall, Brier, calibration checks                   |
| Band selection           | **ADD after calibration:** tune binary fusion weight and decision threshold on out-of-fold predictions |
| Fault gates              | Developed and validated **separately**; combined with the model at runtime, not during fitting         |
| External testing         | **REMOVE — no such step.** No external validation was performed. Do not draw this box.                 |
| Model artifact           | Export `model.joblib`, `calibrator.joblib`, feature schema, label map, model card                      |
| Deployment               | Backend loads versioned artifacts and checks feature-schema compatibility                              |

> **Resolved 2026-07-29 — no external-validation step in F3.9.** An earlier version of this flow listed "external EC3D validation"; that was included by mistake and is **dropped entirely**. The diagram ends at the model artifact and deployment. This keeps F3.9 consistent with §3.2 (comparison attempted and abandoned, dataset not named) and §5.2 (no external generalisation estimate exists).

**Figures:** **F3.5 (REDRAW)** Module B hybrid grading pipeline — replaces proposal Figure 8. **F3.9 (REVISE)** ML training pipeline — replaces proposal Figure 9.

---

### 3.4.3 Web Application Development

#### 3.4.3.1 Requirements Specification — **REWRITE**

**Why:** the proposal's Table 8 lists reasonable requirements, but they were asserted rather than derived. You now have 20 survey responses that justify them. This subsection converts an assumption list into evidence-based requirements engineering — a real Grade-A differentiator.

**Structure to write:**

1. **Survey method, briefly.** Online questionnaire, n = 20, adults 20–59, consent item, distributed before development. Mixed multiple-choice, multi-select, and 5-point Likert.
2. **Respondent profile.** Use §1.5. Note that 90% self-described as general adult users, 45% as physically active, 30% as interested in home rehabilitation — the target population was reached, but only partially.
3. **Findings → requirements table.** This is the centrepiece:

| Survey finding                                                                  | Requirement derived                                                              | Where implemented                   |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------- |
| 20/20 wanted step-by-step guidance before a movement                            | FR: instruction page before each exercise                                        | §3.4.3.3 / R9                       |
| 20/20 wanted simple feedback while exercising alone                             | FR: live on-screen corrective feedback                                           | §3.4.2 / §11.3                      |
| 19/20 wanted to see improvement across sessions                                 | FR: session history + progress trend                                             | §3.4.3.3                            |
| 15/20 positive on reminders; **17/20 preferred phone or calendar delivery**     | FR: reminders with external calendar hand-off (not in-app only)                  | §3.4.3.3                            |
| **16/20 chose on-device analysis with no video saved**                          | NFR: browser-side pose estimation, derived metrics only stored                   | §3.3, §3.4.3.2                      |
| 20/20 rated "easy to learn without technical knowledge" 4–5                     | NFR: usability for non-technical first-time users                                | §3.4.3.3                            |
| 20/20 rated fast feedback 4–5                                                   | NFR: low-latency live path                                                       | §3.4.2 item 9                       |
| 20/20 rated privacy of results 4–5                                              | NFR: authenticated accounts, backend-mediated data access                        | §3.4.3.2                            |
| 20/20 rated camera-visibility warning 4–5                                       | FR: capture-quality gate and warning                                             | §3.4.1                              |
| 18/20 would use a laptop/desktop at reading distance                            | Design constraint: outputs must be legible from standing distance                | _Missed at design time — see 4.3.3_ |
| **Gamification split evenly: 10 opposed, 10 not opposed (8 neutral + 2 agree)** | **Deferred, not rejected — not built in this prototype, carried to future work** | Ch 5 Future Work                    |

4. **Consolidated FR/NFR tables.** Rewrite the proposal's Table 8 with a source column pointing at the survey evidence.
5. **Two honest notes.**
   - The laptop-at-reading-distance row is the one requirement the survey implied and the design did not act on. UAT then found exactly that problem (Q9 = 3.38). **Say so.** A requirement that was elicited, missed, and later caught by evaluation is a stronger story than a clean sheet — it demonstrates the evaluation had teeth.
   - **Gamification — frame as deferred, not rejected.** The split was exactly even: 10 of 20 opposed it (1 strongly disagree, 9 disagree), while the other 10 were not opposed (8 neutral, 2 agree). Read the 8 neutral respondents as willing to accept gamification rather than wanting it, so the honest reading is that it had no clear mandate rather than active rejection. Because half the sample was not in favour, it was **not built into this prototype**, and was instead carried forward as a candidate for future development once core functionality was complete. Do **not** write this as a rejection. Note also that the accompanying non-functional item, colourful themes and custom characters, was the single lowest-rated item at mean 2.80, which points the same way. Carry to Chapter 5 Future Work.

**Figures:** the pre-use survey chart file supplies raw Google Forms charts. **Regenerate the four or five charts you actually use** from the spreadsheet in a consistent house style — the default Forms output is low-resolution and inconsistently formatted. Suggested: age group, difficulties faced, top-5 features, gamification distribution, non-functional importance grid.

---

#### 3.4.3.2 System Architecture — **REWRITE**

**Why:** proposal §3.4.3.2 states the backend receives webcam frames and runs pose estimation. That is not what was built, and it is the most examiner-visible contradiction in the proposal.

**Content:**

- Client–server, three tiers: React + TypeScript frontend, FastAPI backend, PostgreSQL.
- **The corrected data flow, stated plainly, with evidence.** Webcam video never leaves the browser. MediaPipe (`@mediapipe/tasks-vision`) runs entirely client-side via `requestAnimationFrame`. **Concrete evidence to cite:** the backend has no MediaPipe, `opencv-python`, or `cv2` anywhere in `requirements.txt`, and no image-upload endpoint exists anywhere in the API. The backend only ever receives already-extracted numeric landmarks, as `{timestampMs, worldLandmarks}` JSON. This level of specificity is worth keeping — it is what makes the correction verifiable rather than asserted.
- **Justify it on four grounds:** privacy (and cite the survey's 16/20 on-device preference — this is user evidence, not just an engineering preference), latency, storage cost, and deployment simplicity.
- **Acknowledge the deviation explicitly** and give the reason. Do not resolve it silently.
- **Backend responsibilities — corrected, not uniform across modules.** Auth, session management, rule scoring, ML inference (Module B only), fusion, report generation, LLM call, data access — **plus routing, which must be stated precisely rather than implied as one system.** Only **Module B** uses a plugin registry (`module_b/core/registry.py`). **Module A has no single generic dispatcher** — each exercise (STS/SLS/WBLT) gets its own dedicated router, precisely because their result contracts differ from one another. Write this as **"registry (Module B) / per-exercise routers (Module A)"** rather than implying one uniform registry across both modules.
- Separation of concerns: frontend has no direct database access.
- **⚠️ "Two processing paths" was wrong as a uniform claim — replace entirely.** The proposal-era plan described one "low-latency live path" and one "heavier after-set path" as if both modules worked the same way. They do not, and the difference is a real architectural fact worth stating precisely:
  - **Module A (STS/SLS/WBLT) has a genuine live backend round-trip.** Once per detected repetition boundary (STS) or once per completed leg (SLS/WBLT), the frontend calls the **same `/analyze` endpoint**, gated by a `forceFinalize`/threshold flag that distinguishes an in-progress check (live progress, **not persisted**) from a completed one (**persisted**).
  - **Module B (squat) has zero backend calls during the set.** Everything shown live during a squat set is a **client-side cosmetic estimate only** — a local rep FSM and a client-side fault-gate preview, neither of which is authoritative and neither of which touches the backend. The entire buffered set is POSTed **once**, at "Finish Set," to `/api/module-b/analyze`.
  - State plainly why this difference exists if you can — Module A's per-check results are simple enough to compute and persist incrementally; Module B's grading (segmentation, 13-feature extraction, rule scores, ML inference, fusion, majority vote) is a single atomic computation over the whole set, so partial results mid-set would not be meaningful.

**Figures:**

**F3.6 (REDRAW)** web application architecture — replaces proposal Figure 10. **Four corrections, verified 2026-07-29 against the user's own redrawn diagram:**

1. **No separate "AI Inference Service" box.** There is no distinct Python pipeline service that the Backend API calls over a `process frames/windows` arrow. MediaPipe runs in the browser; everything else — segmentation, feature extraction, rule scoring, the Extra Trees `.joblib` model — runs as plain Python functions/modules **inside the same FastAPI process**. Collapse this into one backend box. This is a real architectural correction, not a relabelling — do not draw two backend-side boxes.
2. **Label the Browser → Backend arrow explicitly:** "landmarks + features only, never raw video" — this is the single most important fact the diagram needs to communicate, and the proposal's version got it backwards.
3. **Database detail, corrected:** not one generic "Module Results" cylinder and one generic "Error Tags" cylinder. The actual schema has **two separate tables** — `module_a_results` and `module_b_results` — and `module_b_error_tags` exists **only for Module B**. Module A's warning tags live as **embedded JSON within `module_a_results`**, not a normalised table. Draw four cylinders (or a labelled sub-group), not two.
4. **Add a thin deployment band** (Vercel / Render / Neon) against the three tiers — confirmed as the actual deployment, not the proposal's planned Google Cloud stack. One diagram, no separate hosting figure.

**F3.7 (REVISE)** sequence diagram — proposal Figure 11. **Corrected to show the genuinely different call patterns per module, verified 2026-07-29:**

- **Module A (STS/SLS/WBLT):** a real `loop` of backend calls — once per detected rep boundary for STS, once per completed leg for SLS/WBLT — each hitting the same `/analyze` endpoint. Show an `alt` block inside the loop distinguishing the not-yet-finished branch (live progress result, **not persisted**) from the finished branch (**persisted**, triggers session end).
- **Module B (squat):** **no loop at all** during the set. Show only a local-only FSM (client-side, no messages to backend), then **one** `POST /api/module-b/analyze` at "Finish Set." Everything after that POST — registration → segmentation → feature extraction → rule scores → ML inference → fusion → fault gates → majority vote → optional LLM rewrite → persistence — is drawn as **backend self-messages within a single request/response**, not as a loop. The optional LLM rewrite step should be its own `opt` block, **Module B only**.
- Do not draw Module A and Module B with the same call pattern. The whole point of this correction is that they are genuinely different, and a reader should be able to see that difference at a glance.

---

#### 3.4.3.3 Application Pages and Database Design — **REVISE + MERGE**

**Why:** merges the proposal's scattered page/table content into one section, so 3.4.3 does not sprawl.

**Content:**

- **Feature inventory — replaced 2026-07-30 with the verified current implementation, organised into eight categories.** Use this instead of the earlier flat page list.

  1. **Account & Profile** — Register/Login (JWT-based authentication); user profile (age, gender, height/weight, user type, focus area).
  2. **Exercise Selection & Guidance** — Mode selection (Functional Checking vs. Rehab Grading); exercise selection (4 exercises, catalog-driven); step-by-step instructions page before each exercise (demo clip, camera angle guide, equipment note); camera setup with live pose overlay and body-visibility check, **auto-starts when framing is stable**.
  3. **Exercise Modules** — Module A (rule-based): STS, SLS, WBLT. Module B (hybrid rule + ML): Squat, graded by rule-based sub-scores plus an Extra Trees classifier, fused into a binary Good / Needs Improvement verdict.
  4. **Live Session Feedback** — real-time skeleton overlay (MediaPipe, in-browser); rep/hold counter and progress tracking; recording indicator (visual + audio cue); instant corrective feedback pop-ups on faults; spoken (TTS) coaching cues with mute toggle; on-screen exercise demo reference clip.
  5. **Post-Session Report** — score, band, confidence; rule-based sub-scores (ROM, tempo, stability); error tags; AI-generated coaching feedback (LLM-rewritten for squat, template-based for others); glossary tooltips.
  6. **Progress Tracking** — session history (filterable by exercise, date range); dashboard (recent sessions, scores, common errors); progress deep-dive (per-exercise trend charts).
  7. **Reminders** — create/manage; export to Google Calendar / `.ics`; in-app due-reminder alerts.
  8. **Accessibility & Trust** — multi-language support (English/Chinese/Malay); non-diagnostic disclaimers throughout; privacy-by-design (video never leaves the browser, only numeric landmarks sent to the server).

  > **⚠️ Reconcile with Table 12 in §4.3.1.** This is a more detailed, apparently more current version of the same feature set already tabulated in §4.3.1 as Table 12. The two should describe the same system. **One discrepancy worth resolving before drafting either section:** Table 12 (from the earlier feature dump) describes camera setup as "auto-start countdown, no manual start button." This list describes it as "auto-starts when framing is stable." These are not necessarily contradictory — a plausible reconciliation is that stable framing is the _trigger condition_ that begins the already-documented 5-second countdown (§4.3.4, Stage R5) — but that reconciliation is **my inference, not a confirmed fact**. Confirm which is accurate before both sections go final, so they don't quietly disagree with each other.

- **Database schema — replaced 2026-07-30 with the verified ERD.** Nine tables. Full field list below for F3.8; the prose only needs to name each table and its purpose, not repeat every column.

  | Table                 | Purpose                                                              | Notable fields                                                                                                                                                                                              |
  | --------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `users`               | Core account record                                                  | `email` (UK), `password_hash`, `full_name`, `avatar_image`                                                                                                                                                  |
  | `user_profiles`       | Extended profile, **1:1 with `users`** via the `has` relationship    | `exact_age`, `gender`, `height_cm`, `weight_kg`, `user_type`, `focus_area`, `self_reported_note`                                                                                                            |
  | `exercise_catalog`    | Data-driven exercise list, **categorises** sessions                  | `code` (UK), `mode`, `view_guidance`, `is_active` (retired exercises excluded without deletion)                                                                                                             |
  | `sessions`            | One row per attempt, **user performs, exercise_catalog categorises** | `mode`, `exercise_type`, `status`, `capture_quality`, `valid_frame_ratio`, `score`, `band`, `rep_count`, `target_rep_count`, `device_info`                                                                  |
  | `module_a_results`    | Rule-based results, **session produces Module A** (0..1)             | `completion_time_sec`, `hold_duration_sec`, `rom_band`, `stability_proxy`, `sway_proxy`, `symmetry_proxy`, `trunk_lean_proxy`, `final_band`, `confidence_level`, `metrics_json` (JSONB), `is_partial_score` |
  | `module_b_results`    | ML/hybrid results, **session produces Module B** (0..1)              | `exercise_code`, `score`, `band`, `confidence`, `model_version`, `feature_schema_version`, `q`, `metrics_json` (JSONB)                                                                                      |
  | `module_b_error_tags` | **Module B only** — `module_b_results` **flags** 0..many tags        | `tag`, `severity`, `source`, `message`                                                                                                                                                                      |
  | `feedback_texts`      | **Session has** 0..1 feedback record                                 | `structured_feedback`, `rewritten_feedback`, `feedback_source`, `llm_attempted`, `provider`, `model_version`, `fallback_reason`, `disclaimer_version`                                                       |
  | `reminders`           | **User sets** 0..many reminders                                      | `title`, `reminder_time`, `frequency`, `is_active`, `exercise_code`, `last_completed_at`                                                                                                                    |

  **Three things surfaced by the ERD worth flagging, not silently resolving:**
  1. **Profile data is split across two tables, not one.** `avatar_image` lives on `users` itself; every other profile field (age, gender, height/weight, user type, focus area, self-reported note) lives on the separate `user_profiles` table, joined 1:1. Minor, but worth getting right if the schema is discussed at field level.
  2. **Capture quality appears to be tracked in two places.** `sessions.capture_quality` and `sessions.valid_frame_ratio` sit alongside a separate `module_b_results.q`. Section 3.3.1 defines a single session-level quality metric $Q$. Whether these are the same value stored twice, or two genuinely different measurements, isn't something I can determine from the ERD alone — **confirm before writing**, since describing this incorrectly would create a contradiction with §3.3.1's own equation.
  3. **`feedback_texts.disclaimer_version` is a new fact**, not previously documented anywhere in this plan. It implies the specific disclaimer version a user was shown is recorded per feedback record. This could strengthen the R11/R14 disclaimer discussion in §4.3.4 with a concrete versioning mechanism — flagging it here so it isn't lost, not asserting how to use it yet.

- **Justify JSONB** for variable-shape result data across four exercises with different metric sets — both `module_a_results.metrics_json` and `module_b_results.metrics_json` confirm this pattern directly.
- Multilingual support: English / Chinese / Malay, with translation-key parity enforced by the type system.

**Figures:** **F3.8 (NEW)** ER diagram — draw directly from the verified table above (9 tables, PK/FK, and the six named relationships: `has` [users↔user_profiles], `performs` [users→sessions], `sets` [users→reminders], `categorises` [exercise_catalog→sessions], `produces Module A` / `produces Module B` [sessions→module_a_results / module_b_results], `has` [sessions→feedback_texts], `flags` [module_b_results→module_b_error_tags]). **No page-navigation figure** — cut per instruction; F3.10 is removed from this plan.

---

#### 3.4.3.4 Feedback Generation Layer — **REWRITE**

**Why:** the proposal named a "Transformer" rewriting layer. Use your deviation row.

**Framing — decided 2026-07-30.** Describe this component throughout as an **optional hosted LLM rewriting layer**, not a Transformer. Do not lead with "this is technically a Transformer architecture" as the framing device — that reads as defending the proposal's wording rather than describing what was built. State plainly what it is (a rewriting layer calling a hosted LLM) and only mention the Transformer-architecture technicality once, briefly, as a footnote-level aside if at all.

**Content:**

- Deterministic template feedback is generated **first** and assigned as the **default** feedback output, always produced regardless of whether the LLM path is enabled.
- When the optional LLM is enabled, its rewritten response **replaces** the template, but only **after** passing the safety filter.
- An optional rewrite layer calls a third-party pre-trained LLM (Groq, Llama 3.3 70B) via API. **No transformer was trained, fine-tuned, or built in this project.** The component is off-the-shelf inference behind a prompt and a safety filter.
- **Why:** training a custom coaching-text generator needs labelled coaching-text data that does not exist for this domain.
- **Provider choice:** Groq over Gemini free tier on the no-training-on-user-data policy.
- **Safety filter — state all five rejection conditions, not just "changes the grade."** The filter rejects a rewritten response if it: alters the band; alters the score; introduces an error tag that was not actually detected; contains prohibited clinical language; exceeds the permitted length; or violates the required JSON format. **When rejected, or when the API call fails outright, the original deterministic template remains unchanged** — the user never sees a broken or partial rewrite.
- **⚠️ Fallback tracking is now three-field, not two — correct this everywhere it is described.** The system records **`feedback_source`**, **`llm_attempted`**, and **`fallback_reason`**. The third field is new since the fallback mechanism was first documented, and it is what turns "a fallback happened" into "here is specifically why": distinguishing an LLM-disabled template, an accepted LLM rewrite, and an attempted rewrite that fell back because of an API failure or a specific safety-filter rejection reason (e.g. `guard_rejected:<reason>`, `invented_tag:<tag>`, `grade_mismatch_band`, `grade_mismatch_score`).
- **Default state, stated honestly:** `feedback_llm_enabled=False` by default, Module B only. Module A reports are never rewritten. **With default configuration no AI-rewritten text appears at all.** Decide S5 before the viva.
- Resolve the S9 cross-reference before writing.

**Code snippets to include — both verified, use as-is.** Two short snippets carry this section better than one, since they show two different moments: the acceptance/fallback branch, and what the safety filter is actually checking.

_Snippet 1 — acceptance and fallback-reason branch:_

```python
safety = check_llm_feedback(result.text, structured=structured)
if safety.accepted:
    rewritten_text = result.text
    feedback_source = "llm"
    fallback_reason = "llm_used"
else:
    fallback_reason = f"guard_rejected:{safety.reason}"
```

_Snippet 2 — inside the safety filter itself, showing the specific checks:_

```python
if _contradicts_band(lowered, structured.band):
    return SafetyCheckResult(False, "grade_mismatch_band")
if _contradicts_score(lowered, structured.score):
    return SafetyCheckResult(False, "grade_mismatch_score")
invented_tag = _find_invented_tag(lowered, structured)
if invented_tag is not None:
    return SafetyCheckResult(False, f"invented_tag:{invented_tag}")
return SafetyCheckResult(True)
```

**Write the explanation around these two snippets along these lines** (your own wording, keep it close to this): the deterministic template is generated first and assigned as the default feedback output; when the optional LLM is enabled, its rewritten response replaces the template only after passing the safety filter; the filter rejects responses that alter the band or score, introduce an undetected error tag, contain prohibited clinical language, exceed the permitted length, or violate the required JSON format; when rejected, or when the API fails, the original deterministic template remains unchanged; the system records `feedback_source`, `llm_attempted`, and `fallback_reason`, distinguishing between an LLM-disabled template, an accepted LLM rewrite, and an attempted rewrite that fell back because of an API failure or safety-filter rejection.

**Figures:** none. The two code snippets above replace the earlier single-snippet plan.

**§3.4.3 ends here.** No 3.4.3.5 — see 3.4.4 below.

---

## 3.4.4 Tools and Technology Stack — **NEW (promoted, not nested)**

> **Structural decision, 2026-07-29.** This section **merges two tables that otherwise would have sat in two disconnected places**:
>
> - The proposal's `3.4.2.7 Libraries and Tools` (Table 8) — AI-pipeline tools covering **both** Module A and Module B: MediaPipe Pose, NumPy, One Euro Filter, custom feature functions, the rule engine, scikit-learn, Extra Trees, the multi-label error-tag setup, and the rewriting layer.
> - The live document's existing `3.4.3.5 Tools and Technology Stack` (Table 11) — web infrastructure: React/TypeScript, the browser MediaDevices API, FastAPI, PostgreSQL, Google Forms.
>
> **Why promoted to 3.4.4 rather than left at 3.4.3.5:** the merged table's scope is the _entire_ §3.4 chapter — Module A, Module B, and the web application — not just the web application. Nesting it under "3.4.3 Web Application Development" would misstate its scope, since a reader would find MediaPipe and Extra Trees inside a subsection titled Web Application Development. Promoting it to a sibling of 3.4.1–3.4.3 makes it read as the intended capstone: _here is everything §3.4 was built with_, closing the chapter before §3.5 covers where it was deployed.
>
> **Consequence:** §3.4.3 now ends at **3.4.3.4**. Its planned fifth subsection never happens — its content moves here instead. **§3.5 is unaffected and still follows directly.**

**Content to write:**

- One merged table, organised so AI-pipeline tools and web-infrastructure tools are visually grouped (e.g., a grouping column or two labelled blocks within one table), not two separate tables.
- **Fix the "Transformer" row while merging** — same correction as §3.4.3.4: hosted LLM API, not a model trained in this project.
- One framing sentence per group: the AI-pipeline half is selected for real-time single-camera performance and for fitting together (shared preprocessing feeding both rule-based and ML paths); the web half is selected to support session management, real-time feedback delivery, secure data storage, and dashboard-based progress tracking.
- Do not re-justify individual choices already argued elsewhere (MediaPipe vs MoveNet vs YOLOv8 belongs in §3.3, Extra Trees vs alternatives belongs in §3.4.2.4) — this section is a consolidated reference table, not a re-argument.

### Source content — AI pipeline half (verified 2026-07-29, supersedes any earlier draft of this table)

_Table 9a: AI Pipeline Libraries and Tools_

| Component               | Library / Tool                               | Used in | Purpose                                                                                                                                                                                               |
| ----------------------- | -------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pose estimation         | MediaPipe Tasks Vision Pose Landmarker       | A and B | Extracts normalized pose landmarks and 3D world landmarks from webcam frames in the browser                                                                                                           |
| Browser application     | React and TypeScript                         | A and B | Handles webcam capture, MediaPipe execution, live quality checks, lightweight cues and landmark buffering                                                                                             |
| Geometric processing    | Custom Python and TypeScript functions       | A and B | Calculates joint angles, distances, movement timing, symmetry and stability measurements                                                                                                              |
| Numerical processing    | NumPy                                        | B       | Supports model inference and offline ML data processing, evaluation and numerical analysis                                                                                                            |
| Confidence filtering    | Custom visibility-based filtering            | A and B | Detects unreliable landmarks using MediaPipe visibility values                                                                                                                                        |
| Gap handling            | Custom hold-last and interpolation functions | A and B | Module A holds the previous value during brief landmark loss; Module B also interpolates gaps of up to five frames                                                                                    |
| Smoothing               | Custom One Euro Filter                       | A and B | Reduces landmark jitter while remaining responsive to movement                                                                                                                                        |
| Feature extraction      | Custom feature functions                     | A and B | Converts landmark sequences into interpretable movement metrics. Module B creates a 13-feature vector for each squat repetition                                                                       |
| Repetition segmentation | Custom finite-state machine                  | A and B | Detects movement phases and separates complete repetitions using joint-angle thresholds and hysteresis                                                                                                |
| Rule-based grading      | Custom rule engine                           | A and B | Produces Module A scores and bands; produces Module B ROM, tempo and stability sub-scores and fault gates                                                                                             |
| ML framework            | Scikit-learn                                 | B       | Trains, validates, calibrates and executes the squat classification model                                                                                                                             |
| Primary classifier      | Extra Trees Classifier                       | B       | Learns non-linear relationships between the 13 features and binary Good/Poor labels                                                                                                                   |
| Probability calibration | Scikit-learn sigmoid calibration             | B       | Converts classifier output into calibrated `P(Good)` probabilities                                                                                                                                    |
| Model serialisation     | Joblib                                       | B       | Stores and loads the trained Extra Trees model and sigmoid calibrator                                                                                                                                 |
| Error tags              | Custom deterministic tag rules               | B       | Generates named issues from fault gates, movement rules, confidence and capture-quality flags. **It is not a multi-label ML classifier** — a correction from any earlier draft that implied otherwise |
| Feedback generation     | Custom templates                             | B       | Always produces structured, non-diagnostic coaching feedback from the grade and error tags                                                                                                            |
| Optional rewriting      | Groq-hosted LLM through HTTPX                | B       | Rewrites after-set feedback for clarity without changing the score, band or detected issues                                                                                                           |
| Feedback safety         | Custom validation filter                     | B       | Rejects unsafe or inconsistent LLM responses and falls back to deterministic template feedback                                                                                                        |
| API layer               | FastAPI and Pydantic                         | A and B | Validates analysis requests and connects the frontend with the backend processing pipelines                                                                                                           |
| Data storage            | PostgreSQL, SQLAlchemy and Alembic           | A and B | Stores session summaries, scores, bands, metrics, confidence, tags and feedback                                                                                                                       |
| Offline ML evaluation   | Pandas, SciPy, Matplotlib and Seaborn        | B       | Supports dataset analysis, feature checks, statistical evaluation and training-report figures                                                                                                         |

> **Note on "Error tags":** this row confirms error tags are produced by **deterministic rules**, not learned by the classifier. Keep this distinction sharp when writing 3.4.2.5/3.4.2.6 — the classifier outputs label + confidence only; tags are rule-derived.

### Source content — web infrastructure half (verified 2026-07-29)

_Table 9b: Web Application Technology Stack_

| Layer                       | Technology / Tools                     | Purpose                                                                                                 |
| --------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Frontend                    | React and TypeScript                   | Builds the browser-based user interface for exercise selection, guided sessions, reports and dashboards |
| Frontend build and styling  | Vite and Tailwind CSS                  | Provides frontend development, production builds and responsive interface styling                       |
| Frontend navigation         | React Router                           | Handles navigation between authentication, exercise, live-session, report and progress pages            |
| Localisation                | i18next and React-i18next              | Provides English, Malay and Chinese interface translations                                              |
| Charts and animation        | Recharts and Framer Motion             | Displays progress charts and supports interface animations and transitions                              |
| Browser platform            | HTML5, MediaDevices API and Canvas API | Provides webcam access, video display and pose-overlay rendering in the browser                         |
| Backend                     | Python, FastAPI, Uvicorn and Pydantic  | Implements the REST API, request validation, session management and processing endpoints                |
| Database                    | PostgreSQL                             | Stores users, exercises, sessions, results, metrics, tags, feedback and historical data                 |
| Database access             | SQLAlchemy and Psycopg                 | Connects the Python backend to PostgreSQL and performs database operations                              |
| Database migration          | Alembic                                | Manages version-controlled database schema changes                                                      |
| Authentication and security | OAuth2 bearer tokens, PyJWT and bcrypt | Handles login authentication, access tokens and secure password hashing                                 |
| API communication           | REST and JSON                          | Transfers session data, pose landmarks and analysis results between the frontend and backend            |
| Frontend testing            | Vitest and React Testing Library       | Tests frontend utilities, components and user-interface behaviour                                       |
| Backend testing             | Python `unittest`                      | Tests backend processing, API behaviour, persistence and grading logic                                  |
| User evaluation             | Google Forms                           | Collects structured participant feedback during user testing                                            |
| Supporting design tools     | Canva, Draw.io and/or Visual Paradigm  | Creates report graphics, prototypes and system diagrams, where applicable                               |

> **Overlap check:** PostgreSQL, SQLAlchemy, Alembic and FastAPI/Pydantic appear in **both** halves (Table 9a and 9b), since they serve both modules and the general web application equally. **Do not duplicate these rows when merging** — list each once, and if a grouping column is used, mark it "A and B / Web" rather than repeating the row.

**Figures:** none. One table only.

---

## 3.5 Implementation Environment and Deployment — **ADD**

**Why:** short but necessary. The proposal committed to Google Cloud; you shipped elsewhere.

**Content (half a page):**

- Development stack, languages, key libraries (retain proposal Tables 7 and 9, updated).
- Deployment: frontend on Vercel, backend on Render, PostgreSQL on Neon. Free-tier, git-push-to-deploy platforms suited to a student-scale full-stack application, chosen over the planned Google Cloud stack to avoid infrastructure-management overhead inside the project timeline.
- **One caveat to state now** so it is not a surprise in Chapter 5: free-tier backend instances cold-start after inactivity, so first-request latency after an idle period is not representative of warm performance.

**Figures:** none — deployment is annotated on F3.6.

---

## 3.6 Evaluation Design — **MERGE (3.5 + 3.6 + 3.7) + REVISE**

**Why:** the proposal has 3.5 "Evaluation" and 3.6 "Machine Learning Evaluation" at the same level, which is a numbering error. Merge into one section with four subsections. Also: the proposal specified no evaluation method for Module A at all.

### 3.6.1 Module A: Measurement-Agreement Evaluation — **ADD**

- Framing: Module A checks are deterministic rule-based measurements, not trained classifiers, so classifier-accuracy metrics do not apply. The correct framing is method comparison — how closely does the system's measurement agree with a human reference?
- Statistics and why each: ICC(2,1) two-way random, single measurement, absolute agreement (Shrout & Fleiss, 1979) because seconds must literally match; Bland–Altman (Bland & Altman, 1986) for bias and limits of agreement; Cohen's kappa (Cohen, 1960) for chance-corrected band agreement.
- Kappa is computed on the hold-time band only, because a human with a stopwatch can reproduce that dimension but cannot judge the stability sub-score without a separate rater protocol.
- **State the corpus is synthetic and fixed-seed, here in the method, not only in the results.** Explain why: no real pilot recordings existed for this prototype.
- **Scope: SLS and WBLT. STS alone has no harness.**
- **WBLT harness — what to explain.** It measures the same three agreement statistics against a different quantity: **toe-to-wall distance in centimetres**, rather than a duration. The band compared is the **McBride age/sex percentile band**, not a hold-time band. The corpus is **10 synthetic per-attempt samples covering both legs, plus one heel-lift-invalid case** included so the harness exercises the rejection path as well as the measurement path. An additional **angle-versus-distance standardised corroboration check** tests whether the camera-measured dorsiflexion angle moves consistently with the user-measured distance — a cross-signal sanity check that the hold-time harness has no equivalent of, because SLS produces only one measured quantity.
- **Why STS has none:** state it plainly as a coverage gap, not an oversight to be explained away.

### 3.6.2 Machine-Learning Evaluation — **REVISE**

- Subject-independent 5-fold cross-validation, and why (person-specific movement patterns).
- Metrics: ROC AUC, Brier score, per-class precision and recall, macro-F1, confusion matrix. Retain the proposal's Table 10 equations and Figure 12 concept, but **Figure 12 must be redrawn as a 2×2 binary matrix**, not multi-class.
- Threshold and fusion-weight selection procedure: swept on out-of-fold predictions, macro-F1 objective, weight swept 0.0→1.0 in 0.1 steps with the threshold re-optimised at each point.
- **State the stakeholder priority that governed selection:** rating a genuinely incorrect repetition as correct was designated the most serious failure mode, ahead of the reverse error and ahead of overall accuracy.
- Replay determinism: the harness reproduces byte-identical results across runs.

### 3.6.3 Application Testing — **ADD**

- Automated regression suite: backend and frontend test counts, run on every change.
- Module B grading test cases: deterministic fixtures exercising each fault gate, the majority-vote aggregation, and the score formula.
- Runtime-parity check between the offline Python extraction pipeline and the production browser runtime, and why it mattered (training and inference must see the same signal).

### 3.6.4 User Acceptance Testing Design — **REVISE**

Source: `UAT_PROCEDURE_CONDUCTED.md` §1–§3 and §5, in past tense.

- Moderated, in-person, one-on-one. 21 sessions, 21 participants, 21 questionnaires, 2026-07-18 to 2026-07-23, one quiet room, researcher's laptop.
- Participants: coursemates, friends, family. Convenience sample. Mostly no rehabilitation experience.
- Two evidence streams: Google Form questionnaire (22 Likert + 2 multi-select + 2 open) and researcher observation notes written up immediately after each session.
- Procedure: briefing → ten guided tasks in fixed order → questionnaire completed independently → notes written up.
- **The ten tasks table** — retain from source, it is good and shows deliberate design. Highlight that Task 1 tests non-diagnostic comprehension and was placed first _because a user who believes a webcam self-check is a medical diagnosis is a genuine safety risk_, not an incidental usability finding.
- **Why this method** — the three reasons: self-report alone under-reports usability problems; physical presence allowed safety supervision during real movement; the non-diagnostic boundary is a safety requirement needing direct comprehension testing.
- Analysis method: descriptive statistics on the Likert items; manual thematic coding of the observation notes into themes with per-session frequency; triangulation of the two streams.
- **State that testing ran on the local development build before deployment.** This bounds what Q8 (responsiveness) measures.

**Figures:** none required. The ten-task table carries this section.

---

## 3.7 Ethical Considerations and the Non-Diagnostic Boundary — **DROPPED (2026-07-26)**

> **Not included in the report.** Drafted, reviewed, and cut by decision on 2026-07-26. The original plan text is retained below for traceability only.
>
> **Consequences to manage elsewhere:** (1) the non-diagnostic boundary and its three enforcement points must now be covered where they naturally arise — the landing-page disclaimer in **4.3.1**, the report badge in **4.3.4** (R11), and the LLM safety filter in **3.4.3.4**; (2) the disclaimer-comprehension finding (5 of 21) moves to **4.3.3** item 8; (3) participant consent and the Q3 safety result (4.81/5) move into **3.6.4**, which already covers UAT design. Chapter 3 therefore ends at **3.6**.

**Why:** you tested on human participants performing physical movement, you handle personal health-adjacent data, and your system makes judgements about people's bodies. A short section here is disproportionately valuable to an examiner. Half a page to one page.

**Content:**

- Non-diagnostic boundary: what the system must not provide (diagnosis, injury confirmation, prescription, medical clearance, return-to-sport decisions) and what it may provide (movement-quality indicator, band, capture warning, general technique cue, progress trend, prompt to seek professional advice).
- How the boundary is enforced in the product: landing-page disclaimer, an always-visible badge beside the band chip on every report, and the LLM safety filter that forbids any change to grade or tags.
- Participant safety: informed consent item on the form, voluntary participation, researcher present throughout, right to stop. Record the outcome — 19/21 reported no discomfort, 2 mild, and Q3 (felt physically safe) scored 4.81/5.
- Data handling: video never leaves the browser, derived metrics only, authenticated accounts, backend-mediated access.
- **One honest note:** 5 of 21 sessions did not notice the non-diagnostic disclaimer. Record it here as an ethics finding and forward-reference the R11 fix.

---

# CHAPTER 4 — RESULTS AND DISCUSSION

Structure follows your supervisor's 4.1 / 4.2 / 4.3, with an added short 4.4 for the literature synthesis. Web application gets roughly twice the space of the ML model.

---

## 4.1 Project Overview

**Purpose:** orient the reader before the detailed results. Two to three pages.

**Content:**

- What was delivered: a deployed web application with user accounts, two modules, four exercises, live feedback, post-session reports, session history, progress tracking, reminders, and three-language support.
- A short walkthrough of one complete user journey, from landing page to report, so a reader who never uses the system can follow everything that comes after.
- Deployment state: live on Vercel / Render / Neon.
- A short "how to read this chapter" paragraph: 4.2 evaluates the grading model, 4.3 evaluates the application, and the application is the stronger contribution.
- **Set expectations honestly and early.** One paragraph saying the model works within a narrow, well-characterised envelope and that the chapter reports where it does not. Front-loading this is much stronger than letting it emerge in 4.2.5.

**Visuals:** **F4.1** annotated user-journey screenshot strip (5–6 screens). **T4.1** delivered features against project goals §1.3.3, as a preview of Chapter 5's fuller check.

**Source:** implementation plan §1–§2, §8.1; S3 screenshots.

---

## 4.2 Pose-Grading Machine-Learning Model

Roughly 35% of Chapter 4.

### 4.2.1 Dataset Characteristics and Feature Validity

**Purpose:** report what the Chapter 3 selection procedure actually yielded, and what the data revealed about the features.

**Content:**

- Post-filter composition: 98 reps, 9 subjects, 72 Good / 26 Poor. Per-subject table. Three subjects retained only Good reps.
- **The class-imbalance problem, stated as a constraint rather than hidden:** 26 Poor examples from 6 subjects, one of whom contributes a single rep. Every figure in this section should be read against that.
- **How the imbalance was handled, and why (moved here from §3.4.2.4 on 2026-07-29):** `class_weight="balanced"` was used during fitting; no synthetic oversampling (SMOTE) was applied. State the reasoning as a result-level discussion point, not a bare method statement: generating synthetic repetitions from only 6 Poor-contributing subjects risked manufacturing examples that did not correspond to any real movement pattern, which would have been a worse problem than the imbalance itself.
- **Far-limb occlusion result:** far-knee visibility 0.59–0.78 against near-side 0.95–0.99. This is a measured property of monocular side-view capture, and it later caused a real defect (R1).
- **The inverted-depth finding.** The single most important result in 4.2. In this dataset, repetitions labelled incorrect were systematically _deeper_ than correct ones. The rule-based score, which rewards depth, therefore scored Poor reps higher than Good ones (median 8.83 vs 7.71).
- **Scope it carefully.** State that this is a property measured _in this dataset_, and that it may reflect that cohort's fault taxonomy rather than a general truth about depth rules. Do not claim it generalises.
- Feature importance: report the ranking. Note that symmetry index ranked 11th of 13, consistent with the independent finding that it does not measure genuine asymmetry from a single side view — the model reached the same conclusion the direct comparison did.
- Correlated feature pairs (peak knee flexion and ROM at r = 0.97, ranked 2nd and 3rd) were both retained, because tree ensembles are not destabilised by correlated inputs and removing either would change the deployed feature contract for no measurable gain.
- Runtime parity result.

**Visuals:** **T4.2** per-subject rep breakdown. **F4.2** feature importance bar chart. **F4.3** depth distribution by class — the visual proof of the inversion, and worth the space. **F4.4** knee flexion angle, Python vs browser, one repetition.

**Ch2 link:** §2.4.1 (viewpoint sensitivity, occlusion, jitter as known PE limitations) → the occlusion measurement gives concrete numbers where the literature is qualitative.

**Limitations to state:** 98 reps, 9 subjects, one cohort, one camera geometry. Nothing here estimates generalisation.

---

### 4.2.2 Model Training and Evaluation Results

**Purpose:** report classifier performance honestly.

**Content:**

- Out-of-fold ROC AUC 0.832; Brier 0.149 after calibration.
- Confusion matrix at the deployed operating point.
- Per-class precision and recall. Recall on Poor = 1.000 in-sample; 22 of 72 Good reps flagged Poor (31%).
- **The live measurement, which is your most important number here:** across real webcam sessions, 21 reps passed every rule gate and 17 of them (81%) were still rejected by the classifier alone. The real-world false-alarm rate runs well above the in-sample figure.
- **Explain why**, don't just report it: per-rep errors are not independent within one subject, camera placement and session, so an independence assumption understates the whole-set failure rate.
- Replay determinism.

**Visuals:** **F4.5** confusion matrix (2×2). **F4.6** ROC curve. **F4.7** calibration plot. **T4.3** per-class metrics.

**Ch2 link:** §2.5.2 → the Extra Trees choice, with the literature precedent and the no-bake-off justification carried over from §3.4.2.

**Limitations:** all figures internal to one dataset. No external generalisation estimate exists.

---

### 4.2.3 Fusion Weight and Threshold Selection

**Purpose:** justify w_rule = 0.0 with comparative evidence, and pre-empt the obvious objection.

**Content:**

- The selection procedure: weight swept across the full admissible range 0.0 → 1.0 in 0.1 steps, threshold re-optimised at each weight for macro-F1.
- **The results table** (from the full-range sweep): macro-F1 flat at maximum for rule weights 0.0 through 0.3; first repetition changes hands at 0.4; monotonic degradation after; at rule weight 1.0, recall on the incorrect class falls to zero and 26 severe errors occur.
- **The tie-break reasoning:** rule weights 0.0–0.3 are not four independent ties — each selects the identical set of 48 repetitions, so the figures are identical by construction. Zero was chosen because the rule's relationship to ground truth is inverted for this population, so the smallest weight consistent with the evidence was preferred.
- **Head off the objection directly, in its own paragraph.** A reader will ask whether w_rule = 0 abandons the hybrid architecture. Two answers. First, the weight was _measured_, not assumed — it came from the same procedure used for every other parameter. Second, the rule contribution was **relocated, not removed**: the interpretable fault gates run independently of the fused score and can override it. The deployed verdict is still a function of both components, combined by a gated rather than a linear rule.
- The binary revision: the earlier three-band design abstained on nearly half of all repetitions, which meant the system could almost never say a repetition was incorrect. State the trade plainly — committing to binary made the incorrect verdict reachable (recall 0.077 → 1.000) but gave up the abstention that guaranteed no severe misclassification.
- **Do not quote the superseded 0.2 / 0.8 weighting or the 0.85 confidence threshold as if they were deployed.** If mentioned at all, label them as an intermediate configuration that was later replaced.

**Visuals:** **F4.8** fusion-weight sweep: macro-F1 and per-class recall against rule weight, plus severe-error count. **T4.4** the full sweep table.

**Ch2 link:** §2.5.1 → rule-based grading's known weakness. **Use the scoped wording:** the literature identifies rule-based grading as coarse; in this dataset the rule failed differently, by pointing the wrong way, and no threshold adjustment repairs an inverted ordering.

---

### 4.2.4 Detection Examples

**Purpose:** make the model's behaviour visible. Four squat repetitions, one per quadrant.

**Figure F4.9** — a 2×2 grid. Each cell: a still frame at the bottom of the repetition with the skeleton overlay, plus the report region showing band, score, attempts, valid reps, and any error tags.

**Capture protocol — follow this exactly:**

| Cell                   | Perform                                                                                                                                                | Expect                                                                                                                                                    | Difficulty                                                                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Good → Good**        | Normal squat, feet shoulder-width, comfortably past parallel, torso upright, heels flat, steady tempo. **10 reps**, matching the app's default target. | Band Good, no fault tags, most reps counted valid.                                                                                                        | **Hardest.** Given the 81% ML-rejection rate on gate-clean reps, expect several attempts before a set bands Good. Keep the successful take.                                     |
| **Bad → Bad**          | Clear half-squat that stops visibly above parallel.                                                                                                    | Depth gate trips; band forced to Needs Improvement with a named depth reason.                                                                             | Easy. **Trap:** if you go too shallow, rep segmentation may not register a repetition at all and you get zero attempts. Confirm the Attempts count is non-zero before stopping. |
| **Good → flagged Bad** | Several genuinely deep, controlled, upright reps. Heels down, no lean.                                                                                 | At least one rep rejected by the ML alone with no gate fired — tag `model_only_rejection`, "flagged by the movement model, no specific fault identified". | Easy. **This is your strongest figure** — a direct visual demonstration of your headline finding. Capture the Attempts / Valid reps row beside it so the arithmetic is legible. |
| **Bad → passed Good**  | Knees caving inward (valgus) while keeping good depth, upright trunk and heels down. **15–20 reps.**                                                   | At _repetition_ level: several reps with `failed_gates: []` and `counted_good: true`.                                                                     | **Hardest to obtain cleanly — read the note below.**                                                                                                                            |

**Critical note on the fourth cell.** Your reasoning about valgus is correct — it is deliberately excluded from features, rules, tags and evaluation, so no gate can fire on it. But the classifier rejects roughly 81% of gate-clean reps anyway, so a valgus _set_ will most likely still band Needs Improvement: right verdict, wrong reason, blind spot undemonstrated. Three requirements:

1. **Capture at repetition level, not set level.** With 15–20 reps at a ~19% pass rate, expect three or four reps returning gate-clean and counted good. _Those individual reps_ are quadrant four. Caption them, not the set band.
2. **Take a second photo from the front**, on your phone, outside the application. A reader cannot see valgus in a side-view screenshot, and that is the whole point of the example. Without a frontal frame proving the fault existed, the figure proves nothing.
3. **Bodyweight only. Stop at any knee discomfort.** Deliberate valgus is a known loading mechanism you do not want to rehearse under load. If it will not cooperate after two attempts, use excessive stance width instead — same frontal-plane category, same documented exclusion, easier on the knee.

**Discussion to write alongside the figure:**

- Walk through how a verdict is produced, using cell 1 as the worked example: features → gates → per-rep classifier verdict → majority vote → score.
- Cell 3 is where the system fails most often, and it fails in the safer direction.
- Cell 4 is a documented scope boundary, not a bug. Frontal-plane faults are excluded by design because they are ill-posed from a sagittal view.
- **Write the masking paragraph.** A high false-alarm rate can conceal a blind spot, because the wrong answer arrives for an unrelated reason. A system that rejects most repetitions will appear to catch a fault it cannot actually see. This is your own observation and it is a good one — give it its own paragraph.

---

### 4.2.5 Model Limitations and Discussion

**Purpose:** bound the claims. Balanced, not apologetic.

**Content — the honest list:**

1. Sample size: 98 reps, 9 subjects, 26 Poor from 6 subjects. Every figure inherits this.
2. **No external generalisation estimate exists.** An external comparison was attempted and abandoned because the datasets were incompatible in coordinate format and in how each defined a faulty squat. This is a limitation of the available evidence, not a measurement of poor generalisation — the model may or may not generalise, and this work cannot say which. _(Do not name the dataset.)_
3. The classifier no longer determines the headline score, only which repetitions enter it. The figure a user sees is produced by the rule layer, and the trained classifier's contribution to it is indirect.
4. The score is a rate of acceptable repetitions, not a continuous quality index. Its resolution is bounded by set length — a three-rep set can report only four distinct values.
5. High false-alarm rate: 31% in-sample, ~81% live on gate-clean reps.
6. Frontal-plane faults are undetectable by design.
7. The depth gate is a clinical assumption expressed on this pipeline's scale, not a threshold learned from these labels — it could not be, because the dataset's depth signal is inverted.
8. Set aggregation by majority is a reasoned choice, not a measured optimum. No set-level ground truth exists in this dataset.
9. No published MDC exists for the 0–10 composite score, so no "meaningful change" claim is made on the progress trend.

**The balance paragraph — write this carefully.** The model is not accurate enough to be relied on as the sole judge of movement quality, and the report does not claim otherwise. What the architecture does provide is honest degradation: interpretable fault gates run independently and can override the classifier, uncertain outputs are surfaced rather than hidden, and every threshold is traceable. The stronger contribution of this project is the application built around that model, evaluated in 4.3.

**Ch2 link:** §2.5.1 and §2.5.2 → both rule-based and ML grading approaches showed limits under a monocular single-camera constraint, consistent with what the review anticipated.

---

## 4.3 Web Application

Roughly 65% of Chapter 4. This is the strongest section — give it the most detail and the most figures.

### 4.3.1 Implemented System and User Interface

**Purpose:** show what was built.

**Content:**

- Page-by-page walkthrough with screenshots: landing (with disclaimer), auth, dashboard, mode select, instruction page, camera setup with reference photo, live session for each of the four exercises, report, session history, progress, reminders.
- **Design decisions worth calling out — corrected 2026-07-29 to match §3.4.3.2:** the plugin registry that made **Module B's** exercises pluggable (**Module A uses per-exercise routers, not a shared registry** — do not describe one uniform registry across both modules); the **genuinely different processing models per module** (Module A's real per-check/per-leg live round-trips vs Module B's single after-set POST — not a single "two-path" model applied uniformly); JSONB for variable-shape results; three-language support with enforced key parity.
- Live feedback as built: capture-quality badge, live angle/depth gauge, rep counter, rejection reasons, corrective cue overlay, reference clip pinned to the camera view, countdown and recording indicator.
- **State the deployment**, and note that free-tier backend cold-starts affect first-request latency after idle.

### Full feature inventory (verified 2026-07-29) — use this to structure the page-by-page walkthrough

_Table 12: Implemented Web Application Features_

| Category                                                                                                                                             | Feature                                 | Detail                                                                                                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Account & access**                                                                                                                                 | Login / Register                        | JWT auth, bcrypt                                                                                                                                                           |
|                                                                                                                                                      | Profile view/edit                       | Age, gender, height/weight, user type, focus area, avatar                                                                                                                  |
| **Exercise flow**                                                                                                                                    | Mode selection                          | Functional Checking vs. Rehab Grading                                                                                                                                      |
|                                                                                                                                                      | Exercise selection                      | **Data-driven from `exercise_catalog`, not hardcoded.** Retired exercises (e.g. the removed Leg Lunge) stay excluded via `is_active`, not deletion                         |
|                                                                                                                                                      | Exercise Instructions page              | Per-exercise steps, demo clip, camera-angle reference, equipment note                                                                                                      |
|                                                                                                                                                      | Camera Setup                            | Webcam preview, pose overlay, auto-start countdown, **no manual start button**                                                                                             |
| **Live-session exercises (4)**                                                                                                                       | Sit-to-Stand (STS)                      | Module A, 5 reps, rule-based                                                                                                                                               |
|                                                                                                                                                      | Supported Single-Leg Stance (SLS)       | Module A, both legs, up to 45s hold, rule-based                                                                                                                            |
|                                                                                                                                                      | Weight-Bearing Lunge Test (WBLT)        | Module A, both legs, dual output (self-measured distance + camera angle)                                                                                                   |
|                                                                                                                                                      | Squat                                   | Module B, unlimited reps to a user-set goal, hybrid rule + Extra Trees ML grading                                                                                          |
|                                                                                                                                                      | _(Leg Lunge)_                           | Existed in Module B; **removed from the product 2026-07-19**; confirmed gone from the registry; catalog marks it `is_active=False`. Do not present as currently available. |
| **Live-session UX** _(cross-cutting across all 4 exercises — substantial build effort, worth its own paragraph even though not separate "features")_ | Real-time pose overlay                  |                                                                                                                                                                            |
|                                                                                                                                                      | RECORDING state indicator               |                                                                                                                                                                            |
|                                                                                                                                                      | Large corrective-cue pop-out on faults  |                                                                                                                                                                            |
|                                                                                                                                                      | Spoken (TTS) cues with mute toggle      | Cross-reference §4.3.4.5                                                                                                                                                   |
|                                                                                                                                                      | Exercise demo reference overlay         |                                                                                                                                                                            |
|                                                                                                                                                      | Capture-quality / body-visibility check | Cross-reference §3.3.1's Q metric                                                                                                                                          |
| **Post-session**                                                                                                                                     | Post-Performance Report                 | Score, band, sub-scores, confidence, error tags, coaching feedback (template or LLM-rewritten for squat), glossary tooltips                                                |
|                                                                                                                                                      | Session History                         | Filterable by mode/exercise, date range                                                                                                                                    |
|                                                                                                                                                      | Progress deep-dive                      | Per-exercise trend charts, band zones, error-tag ranking                                                                                                                   |
| **Supporting features**                                                                                                                              | Dashboard                               | Summary cards, multi-exercise trend/band overview, error-tag panel                                                                                                         |
|                                                                                                                                                      | Reminders                               | Add/view/complete, Google Calendar link + `.ics` export, in-app due badge, deep-links into the exercise                                                                    |
|                                                                                                                                                      | Multi-language UI                       | English / 中文 / Bahasa Malaysia                                                                                                                                           |
|                                                                                                                                                      | Non-diagnostic disclaimers              | Landing page + report badge                                                                                                                                                |

> **Use this table to drive the F4.10–F4.16 screenshot selection** — pick screens that between them touch every row, rather than choosing screens first and describing whatever they happen to show.

**Visuals:** **F4.10–F4.16**, one per major screen. Annotate them — an unlabelled screenshot tells an examiner nothing.

**Ch2 link:** §2.3.1 and §2.3.2 → features the literature associates with adherence (structured guidance, progress visibility, reminders) were implemented and can be pointed at individually.

---

### 4.3.2 System and Grading Test Results

**Purpose:** show the system was verified, not just built.

**Content:**

- Automated regression suite counts (S6). Report backend and frontend separately.
- Module B grading test cases: a table of fixture → expected verdict → observed verdict, covering each fault gate, the majority-vote boundary, and the score formula.
- Runtime parity result, if not already used in 4.2.1.
- **Module A measurement agreement**, with the synthetic caveat carried forward from 3.6.1: ICC 0.995, kappa 0.857, bias −0.753 s, LoA [−4.08, 2.57].
- **Interpret the bias, don't just report it.** The system reads about 0.75 s shorter than a stopwatch, and this is explained by the drop-hysteresis persistence frames in the state machine — a known mechanism, not an unexplained discrepancy.
- Explain the single band disagreement (1 of 10) as a genuine edge case: the system correctly reported `invalid` for a leg that never validly crossed the lift line, while the naive time-based reference called a small positive duration `poor`.

**Visuals:** **T4.5** grading test-case matrix. **F4.17** Bland–Altman plot for SLS hold time.

**Limitations:** synthetic corpus, SLS only, STS and WBLT unvalidated.

---

### 4.3.3 User Acceptance Testing Results

**Purpose:** report what 21 users found. This is the heart of the chapter.

> **Counting convention (corrected 2026-07-26):** **21 sessions, 21 participants, 21 questionnaires.** The three previously-paired entries (S13, S15, S18) were _not_ joint sessions — participants were tested separately and simply converged on the same observations. Those notes are therefore split into independent records for the appendix, and every observation frequency is denominated **out of 21**, with a theme raised in a former pair entry counted as **two** sessions. All "X/18" figures in §1.4 of this plan are superseded.

**Content, in this order:**

1. **Sample profile**, with the skew stated up front: 21 participants across 21 sessions, 14 female / 7 male, and 19 of 21 aged 18–24 with one participant each in 45–54 and 55–59. State plainly that this does not represent the older-adult priority user group named in Chapter 1. Note that every participant completed all four exercises.
2. **The headline finding, stated once and early:** _the application explained results well and guided movement poorly._ Every questionnaire item covering the pre-session and during-session phase sits at 3.38–3.90; every item covering the post-session phase sits at 4.48–4.90. The observation notes say the same thing from the other direction — users could not read the live feedback, did not know when the session had started, and could not interpret the SLS ball or lift line, yet understood the band and liked the report.
3. **Full Likert results**, ranked worst to best (§1.3), with a ranked horizontal bar chart.
4. **Multi-select results:** strongest components against those needing most improvement. Camera setup guidance, movement instructions and real-time feedback dominate "needs improvement"; report, dashboard, reminders and session history dominate "strongest".
5. **Observation themes** with per-session frequencies, recomputed out of 21 (see §1.4-R below).
6. **Observation-recording caveat — keep to one or two sentences.** State plainly that because sessions ran in real time, the notes prioritised the more significant observations rather than recording every remark, and that the complete per-session notes are attached as an appendix. **Do not over-explain or apologise for this** — a long justification invites more scrutiny than the limitation itself warrants.
7. **Triangulation.** Where the two streams converge, the finding is high-confidence — instructions, live feedback legibility, camera setup and SLS comprehension all appear in both. Where they diverge, say so: participants rated overall satisfaction 4.48/5 and all 21 said they would use the system, while the observation notes recorded substantial task friction. That gap is the social-desirability effect the two-stream design was built to catch. **Naming it is a methodological strength — write it as one.**
8. **The ethics finding:** 5 of 21 sessions did not register the non-diagnostic disclaimer, despite Q21 scoring 4.52/5. Divergence again, and the more serious reading is the observational one.
9. **Open-ended responses**, presented as a coded table (see **T4.9** below). The dominant cluster is reading distance and font size.

> **Removed from this section (2026-07-26):** the former item 7, "two correctness defects surfaced by users, not by tests" (heel-lift false positive, LLM template fallback). Rationale: the system caught faults correctly in the majority of trials, and foregrounding two exceptions overstated them. **Consequence to manage:** R1 (heel-lift) and the LLM fallback fix still appear in **4.3.4** as remediation entries. They should be presented there as refinements arising from user testing, without the "tests could not have caught this" framing that was removed here.

**Visuals:**

- **F4.18** ranked Likert bar chart, worst to best, with pre-session/during-session and post-session phases colour-coded — this single chart carries the headline finding.
- **F4.19** observation theme frequency chart, top ~12 themes, out of 21.
- **T4.6** strongest vs needs-improvement multi-select counts.
- **T4.9 (NEW)** coded open-response table — **three** columns: _Category_ | _Participant verbatim (unedited)_ | _Response ID_. Group rows by category so repeated categories read as a block. Filter to constructive responses only; non-substantive entries ("none", "nil", "good") are excluded and the exclusion stated once beneath the table. If the table runs past roughly 12 rows, move the full version to an appendix and keep a condensed _Category | Count | One representative verbatim_ table in the chapter body.

**Ch2 link:** §2.2.3 (self-monitoring and feedback gaps) → the survey's difficulties question confirms the literature's stated gap in your own sample. §2.3.3 (limitations of existing tools) → your headline finding locates the weakness in the interaction layer, not the analysis layer.

**Limitations:** convenience sample; age skew; testing ran on the local development build before deployment. For the progress-trend task, participants viewed a **pre-populated tester account** carrying accumulated development-phase history rather than their own data, so the task measured whether the charts were _interpretable_, not whether the feature sustained engagement for a user over time.

---

### §1.4-R Top observation findings — out of 21 sessions, ranked by frequency

Supersedes §1.4. Every frequency is denominated out of 21 sessions, and a theme raised in a former pair entry (S13, S15, S18) counts as two sessions.

**The concluded top findings.** The most frequent observation across all 21 sessions was that metrics and terminology went unexplained, raised in **14 of 21 sessions (67%)**. Second was live feedback text being too small to read at exercising distance, in **11 of 21 (52%)**. These two are the headline observational findings and should open the observation discussion in §4.3.3. Below them sit two joint-third themes at 8 of 21 (38%), and a cluster of five themes at 6 of 21 (29%).

| Rank | Observation theme                                       | Sessions | % of 21 | Addressed by |
| ---- | ------------------------------------------------------- | -------- | ------- | ------------ |
| 1    | Metrics and terminology lack explanation (app-wide)     | **14**   | 67%     | R10          |
| 2    | Live feedback text/font too small to read               | **11**   | 52%     | R4           |
| 3=   | SLS lift-line/threshold indicator not obvious           | **8**    | 38%     | R8           |
| 3=   | Audio/voice feedback requested                          | **8**    | 38%     | R6           |
| 5=   | Prefer video demonstration over text instructions       | 6        | 29%     | R7           |
| 5=   | Wants dedicated "instructions before camera setup" flow | 6        | 29%     | R9           |
| 5=   | SLS stability ball's purpose unclear                    | 6        | 29%     | R8           |
| 5=   | Error-tag colours confusing (green reads as "no issue") | 6        | 29%     | R11          |
| 5=   | Capture-quality trend seen as confusing/useless         | 6        | 29%     | R12          |
| 10=  | Non-diagnostic disclaimer not visually obvious          | 5        | 24%     | R11          |
| 10=  | Instructions/wording too long across the app            | 5        | 24%     | R9           |
| 10=  | Camera setup: unclear the camera can be adjusted        | 5        | 24%     | R9           |
| 10=  | Reminder: wants calendar prompt at creation             | 5        | 24%     | R13          |
| 10=  | Newly created reminder hard to find                     | 5        | 24%     | R13          |
| 15=  | Looks for a manual "Start Session" button               | 4        | 19%     | R5           |
| 15=  | Squat heel-rise false positive                          | 4        | 19%     | R1           |
| 15=  | Dashboard needs more explanation                        | 4        | 19%     | R10, R12     |

**Two points to make in the text.** First, **every theme at 4 of 21 or above was addressed** by a Phase 10 remediation stage — direct evidence for Project Goal 5, and the natural bridge into §4.3.4. Second, the **ranking is stable under either denominator**: terminology and live-feedback legibility were the top two findings before and after the correction to 21 sessions, so the headline conclusion does not depend on the counting change.

Themes below 4 of 21 were mostly single-session feature requests. They belong in Chapter 5's Future Work rather than in the results discussion.

---

### 4.3.4 Enhancements Implemented After UAT

**Purpose:** demonstrate the full design-science loop — evidence to change to verification. This satisfies Project Goal 5 many times over.

> **Scope correction (2026-07-27):** **R2 is removed from the report entirely by decision.** The stages presented are **R1, R4–R14 = 12 stages**. (R3 does not exist in the source log.) R2's dwell-time fix and its byte-identical ICC 0.995 / kappa 0.857 re-run are **not written anywhere**, including 4.3.2 (already removed from that section's plan).
>
> **Consequence to manage:** every "fourteen enhancements" claim elsewhere becomes **twelve**. Affected: 4.3.5 item 2, Chapter 5 goals table (Goal 5), and the closing statement of this section. Also, the plan's earlier "two correctness defects" framing becomes **one** (R1 only), since R2 is the other one.

---

#### Structure — eight numbered subchapters

| §       | Heading                                  | Stages covered                 |
| ------- | ---------------------------------------- | ------------------------------ |
| 4.3.4.1 | Overview of Improvements                 | intro + summary table (all 12) |
| 4.3.4.2 | Grading Correctness Fix                  | R1 — **keep short**            |
| 4.3.4.3 | Session Start and Pre-Exercise Guidance  | R5, R7, R9                     |
| 4.3.4.4 | Live Feedback Redesign                   | R4, R8                         |
| 4.3.4.5 | Audio Feedback                           | R6                             |
| 4.3.4.6 | Report and Terminology Clarity           | R10, R11                       |
| 4.3.4.7 | Dashboard, Session History and Reminders | R12, R13                       |
| 4.3.4.8 | Landing Page and Disclaimer Visibility   | R14                            |

> **Note on R14's placement.** R14 was reassigned from "navigation and polish" to a landing-page redesign addressing disclaimer visibility. It therefore no longer belongs with the dashboard group, so it takes its own short subchapter. This also lets the section close on the safety finding, which is a strong note to end on. Overrule if you would rather fold it into 4.3.4.6 alongside R11's report badge, since both address the same non-diagnostic finding.

---

#### 4.3.4.1 Overview of Improvements

**Write first, before any subchapter.** Two short paragraphs, then the summary table.

- Paragraph 1: state that the UAT findings in 4.3.3 were converted into twelve implemented improvement stages, each traceable to a specific piece of evidence and each shipped with an automated regression-test count. State that the improvements are grouped into one correctness fix and eleven usability and information-design improvements.
- Paragraph 2: state the selection rule — every observation theme appearing in four or more sessions was addressed. This is the bridge from Figure 19 (which already carries the R-code mapping) into this section.

**Summary table (Table X).** Columns: _Stage | UAT evidence | Improvement implemented_. One row per stage, one line each. Keep it tight — the detail belongs in the subchapters. Verification counts are reported **per stage in the subchapter prose**, not in this table.

| Stage | UAT evidence                                                       | Improvement implemented                                                                                     |
| ----- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| R1    | Heel-rise false positive, 4 of 21 sessions                         | Near-leg-only scoring, 3-frame settling baseline, sustained-rise requirement, occlusion guard               |
| R4    | Q9 = 3.38/5; illegible live feedback, 11 of 21                     | Large glanceable full-screen corrective cue, clears on next good rep                                        |
| R5    | Inconsistent start protocol, 9 of 21                               | Standard 5-second countdown, pulsing recording indicator, audio tone at capture start                       |
| R6    | Audio requested, 8 of 21 sessions + 5 free-text                    | Spoken session and corrective cues via testable priority queue with watchdog                                |
| R7    | No in-session form reference                                       | Looping reference clip pinned to camera view, all four exercises                                            |
| R8    | SLS worst-rated, 13 of 21                                          | Stability indicator overlaid on the user's body in-frame; lift line drawn across frame                      |
| R9    | Missing pre-exercise instructions; camera setup unclear, 6 of 21   | Shared "before you begin" page: numbered steps, reference photo, consequence of a failed attempt            |
| R10   | Terminology unexplained, 14 of 21 — most repeated theme            | 10-term glossary wired in wherever a technical term appears                                                 |
| R11   | Report ordering, redundancy, colour semantics, 6 of 21             | Duplicate figure removed; coaching and tags moved up; distinct icon + colour per severity; disclaimer badge |
| R12   | Capture-quality chart rejected, 6 of 21                            | Replaced with per-exercise trends; valid-reps figure added; exercise and date filters                       |
| R13   | Reminder friction, 14 of 21 (concept scored 4.71/5)                | Newest-first ordering, calendar prompt at creation, exercise name in event title, explicit "Open" action    |
| R14   | Non-diagnostic disclaimer not noticed on the landing page, 5 of 21 | Landing page redesigned so the non-diagnostic notice is visually prominent rather than easily missed        |

---

#### 4.3.4.2 Grading Correctness Fix (R1)

**Keep this short — roughly 150–200 words, one or two paragraphs.** It is the only correctness fix, so it must be reported, but it does not carry the section.

**Content, compressed:** the finding (heel-rise fired on otherwise good form, 4 of 21 sessions) → the root cause (the gate averaged both legs against a single first-frame baseline, so the occluded far leg at 0.59–0.78 visibility manufactured a phantom rise) → the fix (near-leg-only scoring with a settling-window baseline, a sustained-rise requirement and an occlusion guard) → the verification (threshold re-derived 0.084 → 0.071; specificity 0.569 → 0.625 in-sample at unchanged 0.808 out-of-fold sensitivity; 28 new/rewritten tests, 329/329 backend suite).

**Frame the outcome honestly, and do not overclaim.** The fix reduced the false positive but did not eliminate the underlying problem, because the root cause is the far-limb visibility limitation of single-camera capture, which no amount of gate logic can remove. What this stage really demonstrates is that the limitation was **located and bounded** rather than solved. Say this plainly in one sentence and move on.

**Cross-reference** 4.2.1's far-limb visibility measurement, and forward-reference Chapter 5's limitations, where this becomes a stated boundary of the approach rather than an open defect.

---

#### 4.3.4.3 Session Start and Pre-Exercise Guidance (R5, R7, R9)

**This is where the workflow figure goes.** Write the prose around it: the three stages together changed the entire path from exercise selection to the first repetition, so a single before/after flow diagram carries them more efficiently than three separate descriptions.

**Content:** R9's shared instruction page inserted ahead of camera setup, with numbered steps, a reference photo of the required camera angle, and the concrete consequence of a failed attempt. R5's standardised 5-second countdown, pulsing recording indicator and audio tone, replacing four different start sequences. R7's looping reference clip pinned to the camera view so users can check form without leaving the page.

**Tie it back:** all three address the pre-session and in-session band that scored 3.38–3.90 in 4.3.3.

---

#### 4.3.4.4 Live Feedback Redesign (R4, R8)

**Content:** R4's replacement of small always-on-screen text with a large glanceable full-screen cue that names the corrective action ("Go deeper", "Chest up", "Heels down") and clears the moment a good rep is completed. Note it was iterated three times against live screenshots before settling. R8's redesign of the single-leg stance stability indicator from an abstract ball in a bordered card into an overlay on the user's own body in the camera view, with the lift line drawn across the frame.

**The connecting argument:** both fixes share one root cause — the original designs asked the user to look away from their own body to an abstract widget, at a distance where reading was already difficult. Both fixes moved the information onto the video itself.

---

#### 4.3.4.5 Audio Feedback (R6)

Keep as its own subchapter — it was the most-requested new feature and has the most interesting development story.

- **Why it was added.** Requested in 8 of 21 sessions and in 5 free-text responses. **State the primary driver correctly:** the dominant evidence is a reading-distance problem, not a general preference for voice. Q9 was the worst item at 3.38/5, and participants described standing too far from the laptop to read the cues. Audio addressed the same problem through a channel that does not depend on visual distance.
- **The accessibility rationale is a design argument, not a finding.** You may state that spoken cues make feedback friendlier and more accessible, including for older adults, but attribute it to design reasoning with a citation. **Your sample cannot support it** — 19 of 21 participants were aged 18–24 and nobody over 59 took part.
- **What it covers:** session start and end cues, and corrective fault cues during movement.
- **What it does not cover:** it does not read the post-session report, does not replace on-screen feedback, does not alter grading in any way, and is English-dependent in its current form.
- **How it was built:** a testable priority queue. Session cues always interrupt; fault cues queue and are throttled per fault type so a repeated identical fault does not spam the user. A watchdog prevents a stalled cue blocking all subsequent ones.
- **The honest development story, worth telling:** getting it working in a real browser took three rounds of live debugging — a speech-engine race condition, a user-gesture activation requirement, and an intermittent engine stall. Verified by 50/50 frontend tests and reproduced live in a browser, not only reasoned about.

---

#### 4.3.4.6 Report and Terminology Clarity (R10, R11)

**Content:** R10's 10-term glossary (ROM, band, stability, capture quality, confidence, symmetry index, valid rep, hold time and others), each definition written in plain non-diagnostic language and stating which direction is better, wired in wherever a technical term appears. R11's three specific report defects: a duplicated number shown in two formats, coaching feedback and error tags buried at the bottom despite being what users valued most, and a genuine low-severity error tag rendered in the same green used for "no issues at all". Note the colour-blind accessibility reasoning — distinct icon shape _and_ colour per severity, not colour alone.

**Tie back to 4.3.3.3 explicitly.** This is the subchapter that answers the "result explanation" finding you added there. Say so.

**Also note** the non-diagnostic disclaimer's promotion to an always-visible badge, answering the 5-of-21 finding in 4.3.3.5.

---

#### 4.3.4.7 Dashboard, Session History and Reminders (R12, R13)

**Content:** R12's replacement of the unanimously rejected capture-quality chart with per-exercise trends that mean something to a user, plus the valid-reps figure that lets the headline 0–10 score be traced back to "X valid reps of Y attempts", plus exercise and date-range filters. R13's reminder fixes — newest-first ordering, calendar prompt at creation, exercise name in the event title, and an explicit "Open" action replacing an ambiguous whole-card click target.

**Note the R13 contrast worth drawing:** the reminder _concept_ scored 4.71/5 and was named among the strongest components, yet the reminder _interaction_ drew friction in 14 of 21 sessions. A well-received feature can still be poorly executed, and separating the two is what made the fix targeted.

**Verification:** R12 at 340 backend and 56/56 frontend; R13 at 343 backend and 56/56 frontend.

> **Do not write the gamification story here.** Gamification is carried to Chapter 5 Future Work only. No descoping narrative in this section.

---

#### 4.3.4.8 Landing Page and Disclaimer Visibility (R14)

Short subchapter, roughly 150–200 words, closing the section on the safety finding.

**Content:** the finding from 4.3.3.5 — in 5 of 21 sessions the participant did not register the non-diagnostic disclaimer at all when asked to describe what the system did, despite Q21 scoring 4.52/5. The landing page was redesigned so the non-diagnostic notice is visually prominent rather than something a first-time user scrolls past.

**Make the pairing explicit.** This finding was addressed in two places: R11 added the always-visible badge beside the band chip on the report, and R14 redesigned the landing page itself. One covers the moment a user reads a result, the other the moment they first arrive. Say this, so the two subchapters read as one coordinated response rather than a repeated fix.

**Close on why it matters:** a user who believes a webcam self-check is a medical diagnosis is a safety concern, not a usability detail, which is why this was treated as a required change rather than an optional polish item.

**Closing paragraph for the whole section:** Project Goal 5 required at least three improvements implemented from user testing. Twelve were implemented, each traceable to specific evidence and each shipped with a regression-test count.

---

#### Visual and evidence requirements

**Workflow figure — F4.20 (NEW, priority).** A **before/after session-entry flow**, placed in 4.3.4.3.

- _Before:_ Exercise selection → Camera setup → (four different start sequences, no clear recording signal) → Session
- _After:_ Exercise selection → **Instruction page** (numbered steps + reference photo + failure consequence) → Camera setup → **5-second countdown + pulsing recording indicator + audio tone** → Session (**live full-screen cue + pinned reference clip**)
- Render as two parallel vertical flows, side by side, with the three new steps highlighted. Deliverable: PNG generated directly, **plus** Mermaid source so it can be regenerated or edited independently.

**Before/after screenshot pairs — the five most persuasive.** Priority order:

| Fig   | Stage | Before                                                               | After                                                        |
| ----- | ----- | -------------------------------------------------------------------- | ------------------------------------------------------------ |
| F4.21 | R4    | Small side-panel live feedback text                                  | Large full-screen corrective cue                             |
| F4.22 | R8    | Stability ball in a bordered card, detached from body                | Stability indicator overlaid on body, lift line across frame |
| F4.23 | R11   | Report with duplicate figure, tags at bottom, green low-severity tag | Reordered report, distinct icon + colour, disclaimer badge   |
| F4.24 | R12   | Capture-quality chart on dashboard                                   | Per-exercise trend + valid-reps figure + filters             |
| F4.25 | R14   | Landing page with easily-missed disclaimer                           | Redesigned landing page with prominent non-diagnostic notice |

**After-only screenshots** (no "before" needed, or "before" is simply absence): R9 instruction page, R5 countdown/recording indicator, R7 pinned reference clip, R13 reminder list with calendar prompt. Use two or three of these at most — pick the ones that photograph best.

**Verification reporting — per stage, in prose.** Report each stage's own test count where it belongs, not as a table column: R1 at 329/329 backend with 28 new tests; R4 at 32/32 frontend; R5 at 36/36; R6 at 50/50 plus live browser confirmation; R9, R10, R11 within 53/53; R12 at 340 backend and 56/56 frontend; R13 at 343 backend and 56/56 frontend. Where a stage shipped inside a shared suite run rather than its own, say so plainly rather than inventing a separate figure.

**Code snippets — only where a screenshot cannot carry the evidence.**

- **R6 audio priority queue — necessary.** 10–15 lines showing the interrupt-versus-queue branch and the per-fault throttle. A screenshot cannot show audio behaviour, so this is the only way to evidence it.
- **R1 near-leg selection — optional.** ~8 lines showing the visibility-based leg choice and the sustained-rise requirement. Include only if 4.3.4.2 feels thin without it; the threshold numbers may be sufficient on their own.
- **Nothing else needs a snippet.** Resist adding more — code in a results chapter reads as padding unless it is the only available evidence.

**Numbering note.** Chapter 4's body currently ends at **Figure 20** and **Table 13**. Figures 21–22 and Tables 14–17 are already assigned to the Work Plan chapter, which comes later. New 4.3.4 figures and tables therefore take **Figure 21 onward** and **Table 14 onward**, and the Work Plan chapter's figures and tables must be renumbered downward accordingly.

---

### 4.3.5 Design-Science Contribution and Discussion

**Purpose:** the argument that this project did more than build software. Position it as the chapter's closing strength.

**Content:**

1. **What design science is, briefly.** A research approach aimed at producing innovative artefacts that solve real-world problems, evaluated for utility rather than only for truth.
2. **The six activities, evidenced.** Reuse the F3.1 mapping and fill each cell with an actual output: problem from Ch2's identified gaps; objectives from a 20-respondent requirements survey; design and development across two modules and four exercises; demonstration via a deployed working system; evaluation through measurement agreement, ML metrics and a 21-participant moderated UAT; communication through this report _and_ through twelve implemented enhancements that closed the loop.
3. **The argument to make:** the project did not stop at building. Potential users were consulted before design, the built system was tested with real users performing real movement, findings were analysed with two independent evidence streams and triangulated, and the system was then changed in response — including a genuine correctness fix that automated testing could not have found. That full cycle, not the classifier, is the contribution.
4. **Balance it.** Acknowledge the model's limits again, briefly, and argue that the architecture around it is designed for exactly that situation: interpretable gates independent of the classifier, uncertainty surfaced rather than hidden, thresholds traceable to their source.
5. **Participant demographics context.** Most participants were female (14 of 21). Contextualise with evidence:
   - **Supported:** women have substantially higher knee OA prevalence and incidence than men, with pooled odds ratios around 1.69 for prevalence and 1.39 for incidence, and greater knee OA severity particularly after menopausal age (Srikanth et al., 2005; Hame & Alexander, 2013 — verify final citations before submission).
   - **Not supported as stated:** the claim that men's knee pain relates more to heavy workload than to genetic factors. Occupational kneeling, squatting and heavy lifting are well-established knee OA risk factors, but the evidence applies to both sexes and does not establish a male-specific workload-over-genetics mechanism. **Drop the comparative genetic claim.**
   - **How to use it:** one short paragraph noting that the female-majority sample is not unhelpful for a lower-limb tool, since knee OA burden falls disproportionately on women. Then immediately state the real limitation — the age skew, not the sex ratio, is what limits generalisability here, since 19 of 21 participants were aged 18–24 and the priority user group named in Chapter 1 was older adults with knee problems.

**Visuals:** **F4.24** the design-science cycle annotated with this project's evidence — a strong closing figure for the chapter.

---

## 4.4 Synthesis Against the Reviewed Literature — _(optional but recommended)_

**Purpose:** your supervisor asked specifically whether the discussion connects back to Chapter 2. Threading it through each subsection is necessary; a consolidated table at the end makes it unmissable to an examiner. One to two pages.

**T4.8 — Literature to results mapping:**

| Ch2 section     | What the review established                                                   | What this project found                                                                                                                             | Relationship                                                                                               |
| --------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| §2.1.2 / §2.4.1 | Monocular pose estimation suffers viewpoint sensitivity, occlusion and jitter | Far-knee visibility 0.59–0.78 vs near-side 0.95–0.99; this caused the R1 heel-lift false positive                                                   | **Confirms and quantifies** — gives measured numbers where the review was qualitative                      |
| §2.2.1          | Adherence is limited by behavioural and psychological barriers                | Reminders scored 4.71/5; 17/20 survey respondents wanted phone or calendar delivery, not in-app                                                     | **Confirms**, and specifies the delivery channel                                                           |
| §2.2.3          | Home users lack objective self-monitoring and feedback                        | Survey's dominant difficulties were "unsure whether I am performing correctly" and "no feedback while exercising alone"                             | **Confirms** in this project's own sample                                                                  |
| §2.3.2          | Structured guidance, progress visibility and reminders improve adherence      | All three implemented; progress charts 4.71/5, session history 4.90/5, reminders 4.71/5                                                             | **Confirms** — these were the highest-rated features                                                       |
| §2.3.3          | Existing digital tools have limitations                                       | Headline UAT finding locates the weakness in the interaction layer while the analysis layer holds up                                                | **Extends** — identifies _where_ the weakness sits                                                         |
| §2.4.2          | MediaPipe vs MoveNet vs YOLOv8-Pose comparison                                | MediaPipe selected; runtime parity Pearson 0.9996 between offline and browser pipelines                                                             | **Applies**, with new empirical support                                                                    |
| §2.5.1          | Rule-based grading from pose landmarks is coarse                              | In this dataset the rule failed _differently_ — its direction was inverted, and no threshold adjustment repairs an inverted ordering                | **Adds a scoped observation** — a distinct failure mode, measured in one cohort, not claimed to generalise |
| §2.5.2          | Moamen et al. report Extra Trees performing well on UI-PRMD / KIMORE          | Extra Trees selected on that precedent; no bake-off run, because 98 reps across 9 subjects cannot separate two classifiers at meaningful confidence | **Applies**, with an explicit justification for not comparing                                              |

**Write one paragraph after the table** stating overall: most of what the review anticipated was confirmed in practice, the monocular limitations proved to be the binding constraint exactly as predicted, and the one place this project's evidence went beyond the review was in how the rule-based component failed.

---

# CHAPTER 5 — CONCLUSION

Three sections. Concise — around 15% of the report.

---

## 5.1 Conclusion

**Content:**

1. **What was built**, in one paragraph. A deployed, non-diagnostic, single-webcam web application for home lower-limb functional self-checking and rehabilitation exercise grading, covering four exercises across two modules, with live feedback, post-session reports, progress tracking, reminders and three-language support.

2. **Achievement against Project Goals §1.3.3 — the answer is yes for all five.** Write this as a table, then a short paragraph. Do not just assert it; cite the evidence.

| Goal | Requirement                                                                                                         | Outcome                                                                                                        | Evidence               |
| ---- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1    | Working interactive web application, frontend and backend                                                           | **Achieved** — deployed on Vercel / Render / Neon                                                              | §4.1, §4.3.1           |
| 2    | ≥3 lower-limb functional checks with banded results and stored session summaries                                    | **Achieved** — STS, SLS, WBLT, all banded and persisted                                                        | §3.4.1, §4.3.1         |
| 3    | Real-time pose estimation pipeline with capture-quality gating                                                      | **Achieved** — browser-side MediaPipe with capture-quality gate Q                                              | §3.3, §4.3.1           |
| 4    | ≥1 exercise-specific model trained and deployed, outputting quality labels, confidence and interpretable error tags | **Achieved** — calibrated Extra Trees squat classifier, deployed, with confidence and named fault tags         | §3.4.2, §4.2           |
| 5    | User testing with 5–10 target users, then ≥3 improvements implemented                                               | **Exceeded** — 21 participants across 21 sessions; **12 improvement stages** implemented and regression-tested | §3.6.4, §4.3.3, §4.3.4 |

3. **The main contribution**, stated in one or two sentences. Not the classifier. The contribution is a complete, evaluated design-science cycle: a working system built from elicited user requirements, tested with real users performing real movement, and demonstrably improved in response — including two correctness defects that automated testing could not have found.

4. **A short honest closing paragraph.** The grading model works within a narrow and well-characterised envelope, and this report says so rather than overstating it. The application built around that model is the stronger result.

---

## 5.2 Limitations

Grouped and concise. Each entry: what it is, why it exists, and where relevant what would reverse it.

**Monocular single-camera (whole system)**

- The camera-depth axis is the least reliable axis. Every feature living on it was dropped or down-weighted. This is the root cause of several items below.
- Frontal-plane faults, including knee valgus, are excluded by design and are not measured at all. Excluded, not unimplemented.
- Far-limb occlusion is systematic, measured at 0.59–0.78 visibility against 0.95–0.99 near-side.
- World landmarks improve angle stability but do not remove the depth limitation — depth is inferred by the model, not measured.

**Squat model and grading**

- 98 repetitions, 9 subjects, 26 Poor examples from 6 subjects.
- No external generalisation estimate exists. The attempted comparison was abandoned because the data formats and the definitions of a faulty squat were incompatible. The model may or may not generalise; this work cannot say which.
- High false-alarm rate: 31% in-sample, approximately 81% live on gate-clean repetitions. The safer direction is preserved — no poor repetition was labelled good in-sample — but a well-performed repetition being told "Needs Improvement" is a real and expected failure mode.
- **Bilateral-mean features carry far-leg noise. (Self-identified by the researcher; the plan treats this as a priority item — write it in full, not as a one-line bullet.)** The 13 trained features are computed as bilateral means across both legs, so the far leg's noisier, lower-confidence tracking (visibility 0.59–0.78 vs 0.95–0.99 near-side) is averaged directly into the same angle-based features — knee flexion, hip flexion, ankle dorsiflexion proxy — that the classifier is trained and predicted on. The system's own motion-capture validation shows a systematic bias of −11.96° with wide 95% limits of agreement [−21.00°, −2.94°] on bilateral knee flexion, though correlation with true motion remains strong (r = 0.956): a noisier signal, not a broken one.
  - **Frame as a deliberate trade-off, not an oversight.** Bilateral averaging was originally adopted to sidestep a _different_ problem — leg-identity ambiguity. Early in development, MediaPipe's left/right labels could not be reliably matched to the true near/far leg (a left-right difference signal correlated with the equivalent mocap signal at only r ≈ −0.05, essentially no relationship). Averaging both legs sidesteps that identity problem entirely, since it no longer matters which leg is which.
  - **Why it was not corrected once the noise cost became visible.** The 13-feature schema is frozen for the shipped model. Changing any feature that feeds the classifier requires a full retrain and recalibration, a substantially larger and riskier change than adjusting one standalone rule, and this was out of scope given the project timeline.
  - **Connect explicitly to the heel-rise precedent (§4.3.4.2 / R1).** Switching that rule-based gate from a bilateral average to near-leg-only computation, selecting the camera-side leg by visibility, measurably improved its specificity. This is real, in-project evidence that near-leg-only computation reduces far-leg-noise-driven error — it simply has not yet been extended to the trained classifier's frozen feature schema.
  - **Do not confuse with the existing far-limb-occlusion bullet above.** That bullet is about the symmetry feature/tag becoming untaggable under occlusion. This limitation is about noise entering the _core angle features_ the classifier actually trains and predicts on — a related but distinct consequence of the same occlusion fact.
- The headline score is a rate of acceptable repetitions, not a continuous quality index, and its resolution is bounded by set length.
- The depth gate is a clinical assumption on this pipeline's scale, not a learned threshold.
- Only one Module B exercise ships.
- No published MDC exists for the composite score, so no meaningful-change claim is made on trends.

**Module A**

- SLS agreement statistics come from a fixed-seed **synthetic** replay corpus, not real pilot recordings, with a systematic bias of about −0.75 s.
- SLS stability is scored in the frontal plane only; sway toward or away from the camera is not captured.
- STS and WBLT have no measurement-agreement harness.
- WBLT's banded output depends on user self-measurement and requires exact age.
- All Module A thresholds are prototype heuristics, not clinically validated cut points.

**Evaluation and sample**

- Convenience sample of 21, recruited from coursemates, friends and family.
- **Age skew is the binding limitation:** 19 of 21 aged 18–24, none over 59. The older-adult priority group named in Chapter 1 is effectively unrepresented.
- 20 of 21 had no rehabilitation or physiotherapy experience.
- Single session per participant. For the progress-trend task, participants viewed a pre-populated tester account carrying development-phase history rather than their own accumulated data, so the task measured whether the charts were interpretable, not whether the feature sustained engagement over time.
- **No second UAT round was conducted.** The twelve enhancement stages were verified by regression tests and live confirmation, but their usability impact was not re-measured with users. Every questionnaire score reported describes the pre-remediation system.
- Testing ran on a local build before deployment, so Q8 (responsiveness) does not describe free-tier hosting behaviour.

**Feedback layer**

- The LLM rewrite is disabled by default and Module B only. Under default configuration, no AI-rewritten text appears.
- LLM output is best-effort and can fall back to the template silently on timeout, rate limit or safety rejection.
- Audio cues are English-dependent in their current form.

**Deployment**

- Free-tier hosting cold-starts after inactivity, so first-request latency after idle is not representative.

---

## 5.3 Future Work

Ordered by value, each with a reason rather than a bare list.

1. **Collect real pilot recordings for Module A agreement.** The strongest single improvement available. It converts the SLS statistics from synthetic to real and extends the same framing to STS and WBLT.
2. **Re-derive the squat feature set with near-leg-only computation and retrain.** Select the camera-side leg per repetition by visibility, exactly as already implemented for the heel-rise fault gate, then re-run the full training, calibration and validation pipeline against the changed schema. This project already has direct internal evidence that this class of fix reduces far-leg-noise-driven error, since the same redesign measurably improved the heel-rise gate's specificity; it has not yet been extended to the trained classifier, because doing so requires a full retrain rather than a standalone rule change. Pairs directly with the bilateral-mean feature-noise limitation in §5.2.
3. **Expand the training data for squat, prioritising Poor examples.** The class imbalance is the binding constraint on the classifier. More Poor examples across more subjects would allow the false-alarm rate to be reduced without giving up recall.
4. **Run a second UAT round on the remediated system.** Twelve improvements were implemented and verified for correctness but not re-measured for usability. A repeat round would close the design-science loop properly and produce a before/after comparison.
5. **Recruit older adults and participants with existing knee conditions.** The priority user group named in Chapter 1 was not represented in testing. This is the clearest gap between intent and evidence.
6. **Add a second camera view or a frontal-plane check.** Would bring valgus and stance-width faults into scope — roughly half of what an independent fault taxonomy considers worth labelling sits outside this system's current reach.
7. **Improve calibration and the operating point.** Reduce the false-alarm rate on gate-clean repetitions, which was the model's dominant real-world failure.
8. **Extend Module B to more exercises.** The plugin registry already supports it; only data and time were missing.
9. **Build and evaluate gamification.** The requirements survey split evenly, with 10 of 20 opposed and 10 not opposed, so it was deferred from this prototype rather than rejected outright. Some UAT participants later asked for it. Building it and evaluating it directly would resolve a question the survey alone could not settle.
10. **Improve audio-cue language coverage.** Spoken cues already map English, Chinese and Malay to BCP-47 tags, but audibility depends on the host system exposing an installed voice, which was a real gap for Malay during testing. Bundling or falling back to a hosted voice would close it.
11. **Explore sequence models** such as LSTM or CNN-LSTM once sufficient data exists, since the current design discards temporal structure by summarising each repetition into a fixed feature vector.

---

# APPENDIX A — FIGURE AND TABLE REGISTER

| ID       | Title                                          | Status                          | Source / how produced                                     |
| -------- | ---------------------------------------------- | ------------------------------- | --------------------------------------------------------- |
| F3.1     | DSRM six-step cycle mapped to project          | **NEW**                         | Diagram — I can generate                                  |
| F3.2     | High-level system workflow                     | **REDRAW** (was proposal Fig 6) | Diagram — I can generate                                  |
| ~~F3.3~~ | ~~Preprocessing pipeline~~                     | **CUT (2026-07-29)**            | Not needed — text sufficient                              |
| F3.4     | Module A per-check flow                        | **NEW**                         | **Mermaid source only, no PNG**                           |
| F3.5     | Module B hybrid grading pipeline               | **REDRAW** (was Fig 8)          | Diagram — I can generate                                  |
| F3.6     | Web application architecture + deployment band | **REDRAW** (was Fig 10)         | Diagram — I can generate                                  |
| F3.7     | Sequence diagram                               | **REVISE** (was Fig 11)         | Diagram — I can generate                                  |
| F3.8     | ER diagram                                     | **NEW**                         | Diagram — I can generate                                  |
| F3.9     | ML training pipeline                           | **REVISE** (was Fig 9)          | Diagram — I can generate                                  |
| F3.10    | Page navigation map                            | **NEW, optional**               | Diagram — I can generate                                  |
| —        | 33 MediaPipe landmarks                         | **RETAIN, recaption**           | Proposal Fig 7                                            |
| —        | Survey charts (4–5 selected)                   | **REGENERATE**                  | From `PhysioFit_User_Requirements_Survey__Responses.xlsx` |
| F4.1     | User journey screenshot strip                  | **NEW**                         | **S3**                                                    |
| F4.2     | Feature importance                             | **EXISTS**                      | `ml/reports/figures/`                                     |
| F4.3     | Depth distribution by class                    | **EXISTS/REGEN**                | `ml/reports/figures/`                                     |
| F4.4     | Knee flexion, Python vs browser                | **EXISTS**                      | `parity_check_knee_flexion.png`                           |
| F4.5     | Confusion matrix (2×2)                         | **REDRAW**                      | Proposal Fig 12 was multi-class                           |
| F4.6     | ROC curve                                      | **EXISTS**                      | `ml/reports/figures/`                                     |
| F4.7     | Calibration plot                               | **EXISTS**                      | `ml/reports/figures/`                                     |
| F4.8     | Fusion weight sweep, full range                | **EXISTS**                      | `fusion_weight_sweep_full_range.png`                      |
| F4.9     | **Four squat detection examples (2×2)**        | **NEW**                         | **S1 + S2** — capture protocol in §4.2.4                  |
| F4.10–16 | UI screenshots, annotated                      | **NEW**                         | **S3**                                                    |
| F4.17    | Bland–Altman, SLS hold time                    | **EXISTS/REGEN**                | `SLS_EVALUATION_REPORT.md`                                |
| F4.18    | **Ranked Likert chart, phase-coded**           | **NEW**                         | Regenerate from feedback xlsx                             |
| F4.19    | Observation theme frequency                    | **NEW**                         | `UAT_OBSERVATION_ANALYSIS.md` §1.2                        |
| F4.20–23 | Before/after remediation pairs                 | **NEW**                         | **S4**                                                    |
| F4.24    | Design-science cycle with evidence             | **NEW**                         | Diagram — I can generate                                  |

**Tables:** T4.1 goals preview · T4.2 per-subject reps · T4.3 per-class metrics · T4.4 fusion sweep · T4.5 grading test cases · T4.6 strongest vs needs-improvement · T4.7 finding→fix→verification · T4.8 literature mapping · plus Ch3's FR/NFR tables and the requirements-derivation table.

---

# APPENDIX B — DEVIATIONS REGISTER

Every deviation must appear in Chapter 3 where it belongs _and_ be summarised in one consolidated table. An examiner reads a named deviation as rigour and an unnamed one as an oversight.

| #       | Planned                                                                                                                    | Built                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Section       |
| ------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| D1      | Backend receives frames and runs pose estimation                                                                           | Browser-side MediaPipe; landmarks and features only sent to backend                                                                                                                                                                                                                                                                                                                                                                                                    | 3.4.3.2       |
| D2      | 2D normalised image coordinates                                                                                            | MediaPipe world landmarks (metric, hip-centred, monocular 3D)                                                                                                                                                                                                                                                                                                                                                                                                          | 3.3           |
| D3      | Transformer rewriting layer built in-project                                                                               | Third-party pre-trained LLM via API; no model trained or fine-tuned                                                                                                                                                                                                                                                                                                                                                                                                    | 3.4.3.4       |
| D4      | Google Cloud Run + Cloud SQL                                                                                               | Vercel + Render + Neon                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 3.5           |
| D6      | Good / Fair / Poor for squat                                                                                               | Binary Good / Needs Improvement                                                                                                                                                                                                                                                                                                                                                                                                                                        | 3.4.2         |
| D7      | Fusion 60% rule / 40% ML                                                                                                   | w_rule = 0.0 after empirical sweep; rule contribution relocated to gates                                                                                                                                                                                                                                                                                                                                                                                               | 3.4.2, 4.2.3  |
| D8      | Headline score = fused weighted value                                                                                      | 10 × good_reps ÷ total_reps (Stage 5.18)                                                                                                                                                                                                                                                                                                                                                                                                                               | 3.4.2         |
| D9      | ML scored one repetition per set                                                                                           | Every repetition scored; strict majority vote (Stage 5.13)                                                                                                                                                                                                                                                                                                                                                                                                             | 3.4.2         |
| D10     | Heel-rise gate on bilateral average                                                                                        | Near-leg-only with settling baseline and occlusion guard (Stage R1)                                                                                                                                                                                                                                                                                                                                                                                                    | 3.4.2, 4.3.4  |
| D11     | No evaluation method specified for Module A                                                                                | Measurement-agreement framing added                                                                                                                                                                                                                                                                                                                                                                                                                                    | 3.6.1         |
| D12     | ASP.NET Core + SignalR considered                                                                                          | FastAPI-only backend                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 3.4.3.2       |
| **D13** | §3.3.4: normalisation needed because of **user height AND camera distance**; worked example **hip-to-knee (thigh) length** | Camera distance solved at source by world landmarks; only body-size remains. Reference is **trunk_length**, chosen by cross-subject CV bake-off. Thigh length lost. Only 2 of 13 features normalised.                                                                                                                                                                                                                                                                  | 3.3.4         |
| **D14** | §3.3.4: system will use **"banding only, never exact degrees"**                                                            | **Superseded by design.** The shipped Report displays exact degree values (`knee_rom_deg`, `avg_trunk_lean_deg`, `leg_angle_deg`) **alongside** their bands. **Decision: state the shipped behaviour and justify it** — a value shown next to its band is more informative than a band alone, and the non-diagnostic boundary is carried by the disclaimer and badge rather than by withholding numbers. Do not write this as an unintended slip.                      | 3.4.2 / 4.3.1 |
| **D15** | §3.3.4: the system would use relative features that **"remain stable under viewpoint changes"**                            | The build instead **enforces one single required viewpoint** (`required_view: "side_view"` in `squat/config.py`) and **gates out any frame that fails a positioning check** (e.g. WBLT's `lateral_alignment_max_hip_x_norm`). So rather than tolerating a varying viewpoint, it prevents a non-compliant viewpoint from being captured at all — **same underlying goal** (do not let camera angle corrupt the numbers), **opposite mechanism** (restrict, not absorb). | 3.4.2         |
| **D16** | §3.3.4 places normalisation as a **preprocessing stage**                                                                   | Normalisation runs at **feature-extraction** time (`features.py::_norm_ref`), on a per-rep average — not in the preprocessing pass. **Decision: §3.3.4 is removed from §3.3 entirely and its content moves into §3.4.2**, where feature design is described.                                                                                                                                                                                                           | 3.3 → 3.4.2   |

---

# APPENDIX C — DRAFTING ORDER

Recommended sequence. Each stage produces something reviewable before the next begins.

| Stage | Write                  | Why this order                                                                          |
| ----- | ---------------------- | --------------------------------------------------------------------------------------- |
| 1     | **3.6 + 3.7**          | Fully evidenced already; builds momentum; no dependency on outstanding items            |
| 2     | **4.3.3**              | Data is complete; it is the chapter's heart; drafting it clarifies what 4.3.4 must show |
| 3     | **4.3.4**              | Source material is nearly report-ready                                                  |
| 4     | **3.4.3.1**            | Requirements — converts survey data into the evidence base for everything else          |
| 5     | **3.1–3.3**            | Needs S10 resolved                                                                      |
| 6     | **3.4.1–3.4.2, 3.5**   | The heaviest rewrite; do it once the voice is established                               |
| 7     | **4.2.1–4.2.3, 4.2.5** | Numbers exist; needs S7 pasted                                                          |
| 8     | **4.3.1, 4.3.2**       | Needs S3 and S6                                                                         |
| 9     | **4.2.4**              | Blocked on S1 and S2 — start capturing early, it needs retakes                          |
| 10    | **4.1, 4.3.5, 4.4**    | Written last, because they summarise everything before them                             |
| 11    | **Chapter 5**          | Written once Chapter 4 is final                                                         |
| 12    | **All figures**        | Generated once section content is locked                                                |
| 13    | **Consistency pass**   | Check every number in this plan's Facts Register against the final text                 |

---

_End of plan. Version 1.0._
