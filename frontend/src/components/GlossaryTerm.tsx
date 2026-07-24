// UAT remediation (Stage R10): icon-only tooltip trigger for a shared glossary
// term (config/glossary.ts) -- reuses InfoTooltip rather than reimplementing it.
// Sits next to an existing label (e.g. "Stability") rather than repeating the
// term's own name, since the surrounding UI copy already names the metric.
import { useTranslation } from "react-i18next";
import InfoTooltip from "./InfoTooltip";
import { GLOSSARY, type GlossaryTermId } from "../config/glossary";

export default function GlossaryTerm({ id }: { id: GlossaryTermId }) {
  const { t } = useTranslation();
  const entry = GLOSSARY[id];
  return <InfoTooltip text={t(entry.defKey)} label={t(entry.termKey)} />;
}
