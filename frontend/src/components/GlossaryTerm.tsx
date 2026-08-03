// Icon-only tooltip trigger for a shared glossary term.
import { useTranslation } from "react-i18next";
import InfoTooltip from "./InfoTooltip";
import { GLOSSARY, type GlossaryTermId } from "../config/glossary";

export default function GlossaryTerm({ id }: { id: GlossaryTermId }) {
  const { t } = useTranslation();
  const entry = GLOSSARY[id];
  return <InfoTooltip text={t(entry.defKey)} label={t(entry.termKey)} />;
}
