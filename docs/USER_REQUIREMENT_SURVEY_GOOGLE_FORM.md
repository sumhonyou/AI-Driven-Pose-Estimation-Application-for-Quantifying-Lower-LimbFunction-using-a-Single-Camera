# User Requirement Survey Google Form Design

## Researcher-only notes

> **Ethics alignment:** The current ethics application describes task-based prototype testing followed by a usability survey involving approximately 5-10 adult participants. The form below is a pre-use user-requirements survey for the general adult public. Confirm with the supervisor or School Ethics whether an amendment or separate approval is required before distributing it.

> **Research integrity:** The 20 records at the end of this document are synthetic test data for checking the form, spreadsheet, and charts only. They are not participant responses and must not be submitted to the live form, included in the study sample, or reported as research findings.

## Recommended Google Form settings

- Do not collect email addresses.
- Do not request names, student IDs, phone numbers, or other identifiers.
- Do not limit the form to Sunway accounts.
- Show a progress bar.
- Do not shuffle the questions because the rating-grid and test-data orders must remain fixed.
- Make every question required except Questions 2 and 3, which contain a "Prefer not to say" option and may be left optional.
- For Question 1, use answer-based section navigation:
  - "I agree and wish to proceed" -> Section 2.
  - "I do not agree" -> Submit/end the form.

---

## Form title

User Requirements Survey for an AI-Based Lower-Limb Movement Feedback Web Application

---

## Section 1 - Introduction and Consent

### Section description to paste into the first page

This questionnaire is conducted as part of a Final Year Project for the BSc (Hons) Computer Science programme at Sunway University.

The project, titled **"AI-Driven Pose-Estimation Application for Quantifying Lower-Limb Function using a Single Camera,"** aims to develop a web application that uses one webcam to support lower-limb functional checking and rehabilitation exercise feedback at home. The proposed application will guide users through simple movements, provide easy-to-understand movement feedback, and show reports and progress over time.

The system is an academic, non-diagnostic application. It will not diagnose an injury or medical condition, prescribe treatment, provide medical clearance, or replace advice from a doctor or physiotherapist.

The purpose of this questionnaire is to understand what general users expect from the proposed application and which features should be prioritised. You do not need technical or medical knowledge to participate, and you will not be asked to perform any physical movement. The questionnaire contains only option-based questions and takes approximately 5-7 minutes.

Participation is voluntary. The form does not collect your name, email address, student ID, phone number, or raw video. Your anonymous responses will be used only for academic research and project improvement. You may stop at any time before submitting the form.

**Principal Investigator:**

- **Name:** Sum Hon You
- **Designation:** Final Year Students BSc (Hons) Computer Science Programme
- **Email:** 22089262@imail.sunway.edu.my

**Supervisor:**

- **Name:** Dr. Teoh Yun Xin
- **Designation:** Lecturer
- **Email:** yunxint@imail.sunway.edu.my

Should participants have any concerns regarding their rights as a research participant, they may contact School Ethics at fet_ethics@sunway.edu.my.

### Question 1 - Consent declaration

- **Question type:** Multiple choice
- **Required:** Yes
- **Question:** I confirm that I am 18 years old or above, have read and understood the information above, and voluntarily consent to participate in this survey.
- **Options:**
  - I agree and wish to proceed
  - I do not agree
- **Navigation:** If "I do not agree" is selected, direct the respondent to the end of the form.

---

## Section 2 - About You and Your Current Experience

**Section description:** This section asks about everyday exercise and movement-checking experiences. No detailed medical information is requested.

### Question 2 - Age group

- **Question type:** Multiple choice
- **Required:** No
- **Question:** What is your age group?
- **Options:**
  - 18-24 years old
  - 25-34 years old
  - 35-44 years old
  - 45-59 years old
  - 60 years old or above
  - Prefer not to say

### Question 3 - User background

- **Question type:** Checkboxes
- **Required:** No
- **Question:** Which option(s) best describe you? Select all that apply.
- **Options:**
  - General adult user
  - Athlete or physically active person
  - Person currently doing or interested in home rehabilitation exercise
  - Healthcare, physiotherapy, fitness, or sports professional/student
  - Caregiver or family member supporting another person
  - Prefer not to say

### Question 4 - Exercise frequency

- **Question type:** Multiple choice
- **Required:** Yes
- **Question:** How often do you normally exercise or do mobility or rehabilitation activities?
- **Options:**
  - Daily
  - Several times a week
  - About once a week
  - Less than once a week
  - Never

### Question 5 - Previous application experience

- **Question type:** Multiple choice
- **Required:** Yes
- **Question:** Have you used a fitness, movement-tracking, or rehabilitation application before?
- **Options:**
  - Yes, regularly
  - Yes, occasionally
  - I have tried one once or twice
  - No, never

### Question 6 - Current sources of guidance

- **Question type:** Checkboxes
- **Required:** Yes
- **Question:** Where do you currently get guidance for exercise or body movement? Select all that apply.
- **Options:**
  - Online videos or social media
  - Written instructions or exercise sheets
  - A physiotherapist, doctor, trainer, or coach
  - Family members or friends
  - A fitness application or smartwatch
  - I do not currently use any guidance

### Question 7 - Current difficulties

- **Question type:** Checkboxes
- **Required:** Yes
- **Question:** What difficulties do you face when exercising or checking your movement at home? Select up to three.
- **Options:**
  - I am unsure whether I am performing a movement correctly
  - I do not receive feedback while exercising alone
  - It is difficult to track my progress over time
  - I forget my planned exercise sessions
  - Some exercise applications are difficult to understand
  - I do not always have enough space or a suitable camera position
  - I am concerned about privacy when a camera is used
  - I do not face any of these difficulties
- **Response validation:** Select at most three options.

### Question 8 - Comfort with webcam use

- **Question type:** Linear scale
- **Required:** Yes
- **Question:** How comfortable would you feel using a webcam that analyses your movement and gives feedback at home?
- **Scale:** 1 to 5
- **Left label:** Very uncomfortable
- **Right label:** Very comfortable

---

## Section 3 - What You Expect from the Application

**Section description:** Imagine a web application that uses one webcam to guide lower-limb movements and provide simple feedback. Choose the options that would matter most to you.

### Question 9 - Needs during home exercise

- **Question type:** Multiple-choice grid
- **Required:** Yes; require one response in each row
- **Question:** Please rate how much you agree with each statement.
- **Description:** Scale: 1 = Strongly disagree, 2 = Disagree, 3 = Neutral, 4 = Agree, 5 = Strongly agree. On a phone, scroll sideways to view all columns.
- **Columns:**
  - 1 - Strongly disagree
  - 2 - Disagree
  - 3 - Neutral
  - 4 - Agree
  - 5 - Strongly agree
- **Rows, in this order:**
  1. I would find step-by-step guidance useful before starting a movement.
  2. I would find simple feedback useful while exercising alone.
  3. I would like to see whether my movement improves across different sessions.
  4. Reminders would help me follow an exercise routine more consistently.
  5. I would like to add some gamification to increase my motivation to do it.
### Question 10 - Most useful features

- **Question type:** Checkboxes
- **Required:** Yes
- **Question:** Which five features would be most useful to you? Select up to five.
- **Options:**
  - Clear step-by-step instructions before an exercise
  - Guidance for camera position and distance
  - Easy start, pause, stop, and finish controls
  - Simple feedback while performing the movement
  - A summary report after each session
  - A list of previously completed sessions
  - A chart showing progress over time
  - Exercise reminders
  - A personal account to keep results private
  - Background music during exercise
  - Sharing results directly on social media
  - Badges, points, or a leaderboard
- **Response validation:** Select at most five options.

### Question 11 - Information shown during movement

- **Question type:** Checkboxes
- **Required:** Yes
- **Question:** What would you like to see while performing a movement? Select up to three.
- **Options:**
  - Repetition count or hold timer
  - A simple result such as Good, Fair, or Needs Improvement
  - One short correction or instruction at a time
  - A warning when the camera cannot see the body clearly
  - Progress towards the session target
  - An animated character copying the movement
  - No feedback until the movement session is finished
- **Response validation:** Select at most three options.

### Question 12 - Information shown after a session

- **Question type:** Checkboxes
- **Required:** Yes
- **Question:** What should be included in the report after a session? Select up to four.
- **Options:**
  - An overall result such as Good, Fair, or Needs Improvement
  - An overall score
  - Simple movement measurements such as movement range, stability, or time
  - The number of repetitions completed
  - Movement issues noticed by the application
  - Short suggestions for improvement
  - A comparison with previous sessions
  - A shareable picture for social media
- **Response validation:** Select at most four options.

### Question 13 - Preferred use of the application

- **Question type:** Multiple choice
- **Required:** Yes
- **Question:** Which part of the application would you be most interested in using?
- **Options:**
  - Functional checking, such as checking balance or simple lower-limb movement
  - Rehabilitation exercise grading, such as checking squat movement quality
  - Both functional checking and rehabilitation exercise grading
  - I am not sure

### Question 14 - Camera privacy preference

- **Question type:** Multiple choice
- **Required:** Yes
- **Question:** Which option would make you feel most comfortable when the application uses a webcam?
- **Options:**
  - The camera view is analysed on my device and the video is not saved
  - The application asks for my permission each time before saving a video
  - I am comfortable with exercise videos being saved automatically
  - I am not sure

### Question 15 - Reminder preference

- **Question type:** Multiple choice
- **Required:** Yes
- **Question:** How would you prefer to receive exercise reminders?
- **Options:**
  - A reminder shown inside the application
  - Email reminder
  - Phone or calendar notification
  - I do not want reminders
  - No preference

### Question 16 - Preferred device

- **Question type:** Multiple choice
- **Required:** Yes
- **Question:** If using the application requires you to read from a distance away from the device, which device would you most likely use?
- **Options:**
  - Laptop or desktop computer with a webcam
  - Smartphone
  - Tablet
  - No preference

### Question 17 - Application quality

- **Question type:** Multiple-choice grid
- **Required:** Yes; require one response in each row
- **Question:** How important would each of the following be to you?
- **Description:** Scale: 1 = Least important, 2 = Slightly important, 3 = Moderately important, 4 = Very important, 5 = Extremely important. On a phone, scroll sideways to view all columns.
- **Columns:**
  - 1 - Least important
  - 2 - Slightly important
  - 3 - Moderately important
  - 4 - Very important
  - 5 - Extremely important
- **Rows, in this order:**
  1. The application is easy to learn without technical knowledge.
  2. The instructions, buttons, and results are clear and easy to read.
  3. Feedback appears quickly after I move.
  4. The application works reliably with a normal webcam.
  5. My personal results are kept private.
  6. My previous results remain available when I return.
  7. The application warns me when the camera cannot see my body clearly.
  8. The application offers colourful themes and custom characters.

### Question 18 - Likelihood of future use

- **Question type:** Linear scale
- **Required:** Yes
- **Question:** If this application worked well, how likely would you be to use it for home movement checking or rehabilitation exercise support?
- **Scale:** 1 to 5
- **Left label:** Very unlikely
- **Right label:** Very likely

---

## Confirmation message

Thank you for completing this questionnaire. Your anonymous feedback will help prioritise the functions and usability expectations of the proposed application. The application is an academic, non-diagnostic project and does not replace professional medical advice.

---

## Synthetic Test Data - Not Participant Responses

> **Do not enter these records into the live research form or present them as collected responses.** They are mock records intended only to test form branching, spreadsheet columns, calculations, and chart layouts. Genuine research findings must come from consenting participants under the approved study procedure.

### Compact codebook

- **Q1:** A = Agree.
- **Q2:** A = 18-24; B = 25-34; C = 35-44; D = 45-59; E = 60 or above; F = Prefer not to say.
- **Q3:** A = General adult; B = Active/athlete; C = Home rehabilitation interest; D = Health/fitness professional or student; E = Caregiver; F = Prefer not to say.
- **Q4:** A = Daily; B = Several times a week; C = Weekly; D = Less than weekly; E = Never.
- **Q5:** A = Regular user; B = Occasional user; C = Tried once or twice; D = Never used.
- **Q6:** A = Online videos; B = Written instructions; C = Professional; D = Family/friends; E = App/smartwatch; F = No guidance.
- **Q7:** A = Unsure about correct movement; B = No feedback alone; C = Hard to track progress; D = Forget sessions; E = Apps difficult; F = Space/camera difficulty; G = Camera privacy concern; H = None.
- **Q8:** 1 = Very uncomfortable; 5 = Very comfortable.
- **Q9:** Five ratings in the exact row order shown in Question 9.
- **Q10:** A = Instructions; B = Camera guidance; C = Session controls; D = Live feedback; E = Session report; F = Session history; G = Progress chart; H = Reminders; I = Private account; J = Music; K = Social sharing; L = Badges/leaderboard.
- **Q11:** A = Rep/hold count; B = Simple result; C = Short correction; D = Camera warning; E = Target progress; F = Animated character; G = No live feedback.
- **Q12:** A = Overall result; B = Overall score; C = Measurements; D = Rep count; E = Movement issues; F = Suggestions; G = Previous-session comparison; H = Social-media picture.
- **Q13:** A = Functional checking; B = Rehabilitation grading; C = Both; D = Not sure.
- **Q14:** A = Analyse on device/no saved video; B = Ask before saving; C = Save automatically; D = Not sure.
- **Q15:** A = In-app; B = Email; C = Phone/calendar; D = No reminders; E = No preference.
- **Q16:** A = Laptop/desktop; B = Smartphone; C = Tablet; D = No preference.
- **Q17:** Eight ratings in the exact row order shown in Question 17.
- **Q18:** 1 = Very unlikely; 5 = Very likely.

### Twenty mock records, one record per line

```text
T01 | Q1=A | Q2=A | Q3=A,B | Q4=B | Q5=B | Q6=A,E | Q7=A,B,C | Q8=4 | Q9=[5,5,5,4,2] | Q10=A,B,C,D,E | Q11=A,B,D | Q12=A,C,E,F | Q13=C | Q14=A | Q15=C | Q16=A | Q17=[5,5,5,5,5,4,5,2] | Q18=5
T02 | Q1=A | Q2=A | Q3=A | Q4=C | Q5=C | Q6=A | Q7=A,B,D | Q8=3 | Q9=[5,4,4,5,1] | Q10=A,B,D,E,H | Q11=A,C,D | Q12=A,B,E,F | Q13=C | Q14=A | Q15=A | Q16=B | Q17=[5,5,4,4,5,4,5,1] | Q18=4
T03 | Q1=A | Q2=B | Q3=A,C | Q4=D | Q5=D | Q6=B,C | Q7=A,C,D | Q8=3 | Q9=[5,4,5,5,1] | Q10=A,B,E,F,G | Q11=B,C,D | Q12=A,C,F,G | Q13=B | Q14=A | Q15=C | Q16=A | Q17=[5,5,4,5,5,5,5,1] | Q18=4
T04 | Q1=A | Q2=A | Q3=B | Q4=A | Q5=A | Q6=A,E | Q7=B,C | Q8=5 | Q9=[4,5,5,3,3] | Q10=B,C,D,E,K | Q11=A,B,E | Q12=B,C,D,G | Q13=C | Q14=A | Q15=E | Q16=B | Q17=[4,4,5,5,5,5,4,2] | Q18=5
T05 | Q1=A | Q2=C | Q3=A,E | Q4=C | Q5=C | Q6=C,D | Q7=A,B,F | Q8=2 | Q9=[5,5,4,3,1] | Q10=A,B,C,D,E | Q11=A,C,D | Q12=A,C,E,F | Q13=A | Q14=B | Q15=A | Q16=A | Q17=[5,5,5,5,5,4,5,1] | Q18=4
T06 | Q1=A | Q2=B | Q3=A,B | Q4=B | Q5=B | Q6=A,C,E | Q7=A,B,C | Q8=4 | Q9=[5,5,5,4,2] | Q10=A,B,D,E,G | Q11=A,B,C | Q12=A,B,E,G | Q13=C | Q14=A | Q15=C | Q16=A | Q17=[5,5,5,4,5,5,5,2] | Q18=5
T07 | Q1=A | Q2=D | Q3=A,C | Q4=D | Q5=D | Q6=B,C | Q7=A,B,D | Q8=2 | Q9=[5,4,5,5,1] | Q10=A,B,C,E,H | Q11=A,C,D | Q12=A,C,E,F | Q13=B | Q14=A | Q15=B | Q16=C | Q17=[5,5,4,5,5,5,5,1] | Q18=4
T08 | Q1=A | Q2=A | Q3=A,D | Q4=B | Q5=A | Q6=A,C,E | Q7=B,C,G | Q8=4 | Q9=[4,5,5,4,2] | Q10=B,C,D,E,I | Q11=A,B,D | Q12=A,C,E,F | Q13=C | Q14=A | Q15=A | Q16=A | Q17=[5,5,5,5,5,4,5,2] | Q18=5
T09 | Q1=A | Q2=B | Q3=A | Q4=C | Q5=B | Q6=A,D | Q7=A,E,F | Q8=3 | Q9=[5,4,4,3,1] | Q10=A,B,D,E,F | Q11=A,C,D | Q12=A,B,E,F | Q13=A | Q14=B | Q15=E | Q16=B | Q17=[5,5,4,4,5,4,5,1] | Q18=4
T10 | Q1=A | Q2=A | Q3=B,C | Q4=A | Q5=A | Q6=A,C,E | Q7=A,B,C | Q8=5 | Q9=[5,5,5,4,3] | Q10=A,B,D,E,G | Q11=A,B,C | Q12=B,C,E,G | Q13=C | Q14=A | Q15=C | Q16=A | Q17=[5,5,5,5,5,5,5,2] | Q18=5
T11 | Q1=A | Q2=C | Q3=A | Q4=D | Q5=C | Q6=A,B | Q7=A,D,E | Q8=3 | Q9=[5,4,4,5,1] | Q10=A,E,F,G,H | Q11=A,C,E | Q12=A,C,F,G | Q13=A | Q14=A | Q15=A | Q16=C | Q17=[5,5,4,4,5,5,4,1] | Q18=4
T12 | Q1=A | Q2=B | Q3=A,E | Q4=C | Q5=D | Q6=C,D | Q7=A,B,C | Q8=2 | Q9=[5,5,5,4,1] | Q10=A,B,C,D,E | Q11=B,C,D | Q12=A,C,E,F | Q13=C | Q14=B | Q15=B | Q16=A | Q17=[5,5,5,5,5,4,5,1] | Q18=4
T13 | Q1=A | Q2=A | Q3=A,B | Q4=B | Q5=B | Q6=A,E | Q7=C,D | Q8=4 | Q9=[4,4,5,5,2] | Q10=A,D,E,G,H | Q11=A,B,E | Q12=A,B,D,G | Q13=C | Q14=A | Q15=C | Q16=B | Q17=[4,5,5,4,5,5,4,2] | Q18=5
T14 | Q1=A | Q2=D | Q3=A,C,E | Q4=D | Q5=D | Q6=B,C | Q7=A,B,F | Q8=2 | Q9=[5,5,4,4,1] | Q10=A,B,C,D,E | Q11=A,C,D | Q12=A,C,E,F | Q13=B | Q14=A | Q15=A | Q16=A | Q17=[5,5,4,5,5,4,5,1] | Q18=4
T15 | Q1=A | Q2=A | Q3=A | Q4=E | Q5=D | Q6=F | Q7=A,B,D | Q8=3 | Q9=[5,4,3,5,2] | Q10=A,B,D,E,H | Q11=B,C,D | Q12=A,B,E,F | Q13=D | Q14=B | Q15=C | Q16=B | Q17=[5,5,4,4,5,4,5,2] | Q18=3
T16 | Q1=A | Q2=B | Q3=B,D | Q4=A | Q5=A | Q6=A,C,E | Q7=B,C | Q8=5 | Q9=[4,5,5,3,4] | Q10=B,D,E,G,L | Q11=A,B,F | Q12=B,C,D,G | Q13=C | Q14=A | Q15=E | Q16=A | Q17=[4,4,5,5,5,5,4,3] | Q18=5
T17 | Q1=A | Q2=C | Q3=A | Q4=C | Q5=C | Q6=A,D | Q7=A,E,G | Q8=2 | Q9=[5,4,4,3,1] | Q10=A,C,E,F,I | Q11=A,C,D | Q12=A,C,E,F | Q13=A | Q14=B | Q15=B | Q16=C | Q17=[5,5,4,4,5,4,5,1] | Q18=4
T18 | Q1=A | Q2=A | Q3=A,B | Q4=B | Q5=B | Q6=A,E | Q7=B,C,D | Q8=4 | Q9=[4,5,5,5,2] | Q10=A,D,E,G,H | Q11=A,B,E | Q12=A,B,F,G | Q13=C | Q14=A | Q15=C | Q16=B | Q17=[4,5,5,5,5,5,4,2] | Q18=5
T19 | Q1=A | Q2=B | Q3=A,C | Q4=D | Q5=C | Q6=B,C | Q7=A,B,F | Q8=3 | Q9=[5,5,4,4,1] | Q10=A,B,C,D,E | Q11=A,C,D | Q12=A,C,E,F | Q13=B | Q14=A | Q15=A | Q16=A | Q17=[5,5,5,5,5,4,5,1] | Q18=4
T20 | Q1=A | Q2=A | Q3=A,B | Q4=B | Q5=A | Q6=A,E | Q7=C | Q8=5 | Q9=[4,5,5,3,3] | Q10=B,D,E,G,J | Q11=A,B,E | Q12=B,D,G,H | Q13=C | Q14=A | Q15=E | Q16=B | Q17=[4,4,5,5,5,5,4,2] | Q18=5
```
