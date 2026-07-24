// UAT remediation (Stage R10): one shared glossary of app-wide terms, reused by
// <GlossaryTerm> wherever a metric/label needs an inline definition -- instead of
// each page inventing its own ad hoc explanation text (T4, the most-repeated
// content request in UAT). Every definition includes a plain "which direction is
// better" statement (S16), and stays non-diagnostic (functional language only).
export type GlossaryTermId =
  | "rom"
  | "dorsiflexion"
  | "band"
  | "goodFairPoor"
  | "stability"
  | "captureQuality"
  | "confidence"
  | "symmetryIndex"
  | "validRep"
  | "holdTime";

export interface GlossaryEntry {
  /** i18n key for the term's short name (used as the tooltip trigger's a11y label). */
  termKey: string;
  /** i18n key for the plain-language definition, incl. direction-of-good. */
  defKey: string;
}

export const GLOSSARY: Record<GlossaryTermId, GlossaryEntry> = {
  rom: { termKey: "glossary.rom.term", defKey: "glossary.rom.def" },
  dorsiflexion: { termKey: "glossary.dorsiflexion.term", defKey: "glossary.dorsiflexion.def" },
  band: { termKey: "glossary.band.term", defKey: "glossary.band.def" },
  goodFairPoor: { termKey: "glossary.goodFairPoor.term", defKey: "glossary.goodFairPoor.def" },
  stability: { termKey: "glossary.stability.term", defKey: "glossary.stability.def" },
  captureQuality: {
    termKey: "glossary.captureQuality.term",
    defKey: "glossary.captureQuality.def",
  },
  confidence: { termKey: "glossary.confidence.term", defKey: "glossary.confidence.def" },
  symmetryIndex: {
    termKey: "glossary.symmetryIndex.term",
    defKey: "glossary.symmetryIndex.def",
  },
  validRep: { termKey: "glossary.validRep.term", defKey: "glossary.validRep.def" },
  holdTime: { termKey: "glossary.holdTime.term", defKey: "glossary.holdTime.def" },
};
