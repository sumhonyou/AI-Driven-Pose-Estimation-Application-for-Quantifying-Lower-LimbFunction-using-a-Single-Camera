// Project-level external links and contact people for this FYP prototype.
// Kept here so the footer, the landing page, and the contact modal all read the
// same values instead of hardcoding the URL/emails in three places.

/** Pre-use user-requirements survey (Google Form) linked from the footer + landing page. */
export const FEEDBACK_FORM_URL =
  "https://docs.google.com/forms/d/e/1FAIpQLScJI1URnl5VbreUEoNEjY_oXObP6KgmzYm15-MGGm2_UHjPgQ/viewform?usp=header";

export interface ProjectPerson {
  /** i18n key for the row label (Student / Supervisor). */
  labelKey: string;
  name: string;
  /** i18n key for the designation line — translated, unlike name/email. */
  roleKey: string;
  email: string;
}

export const PROJECT_CONTACTS: ProjectPerson[] = [
  {
    labelKey: "contact.studentLabel",
    name: "Sum Hon You",
    roleKey: "contact.studentRole",
    email: "22089262@imail.sunway.edu.my",
  },
  {
    labelKey: "contact.supervisorLabel",
    name: "Dr. Teoh Yun Xin",
    roleKey: "contact.supervisorRole",
    email: "yunxint@imail.sunway.edu.my",
  },
];
