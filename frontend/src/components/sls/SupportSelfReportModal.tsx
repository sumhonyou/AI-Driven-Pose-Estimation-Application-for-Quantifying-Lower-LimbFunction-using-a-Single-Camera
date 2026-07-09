// Post-session self-report: did the user hold a chair/wall for support?
// Stored for the user's own history only — never affects scoring (see sls_router.py).
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import type { UsedSupport } from "../../services/sls/slsApi";

interface Props {
  onSelect: (used: UsedSupport) => void;
  submitting: boolean;
}

export default function SupportSelfReportModal({ onSelect, submitting }: Props) {
  const { t } = useTranslation();

  const options: { value: UsedSupport; label: string }[] = [
    { value: "none", label: t("sls.supportNone") },
    { value: "slight", label: t("sls.supportSlight") },
    { value: "support", label: t("sls.supportFull") },
  ];

  return createPortal(
    <div className="sls-modal-overlay" role="dialog" aria-modal="true">
      <div className="sls-modal-card">
        <h3>{t("sls.supportModalTitle")}</h3>
        <p className="muted">{t("sls.supportModalNote")}</p>
        <div className="sls-modal-actions">
          {options.map((opt) => (
            <button
              key={opt.value}
              className="btn btn-ghost btn-block"
              disabled={submitting}
              onClick={() => onSelect(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>,
    document.body,
  );
}
