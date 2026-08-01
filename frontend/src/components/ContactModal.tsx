// Small pop-out shown from the footer "Contact" link: student + supervisor
// contact details for this Final Year Project prototype.
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import { PROJECT_CONTACTS } from "../config/projectContact";
import { Close, Mail, MessageSquare } from "./Icons";

interface Props {
  onClose: () => void;
}

export default function ContactModal({ onClose }: Props) {
  const { t } = useTranslation();

  // Close on Escape; the backdrop click is handled below.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return createPortal(
    <div className="contact-modal-overlay" onClick={onClose}>
      <div
        className="contact-modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="contact-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="contact-modal-head">
          <div className="contact-modal-title-group">
            <span className="contact-modal-badge" aria-hidden="true">
              <MessageSquare />
            </span>
            <h3 id="contact-modal-title">{t("contact.title")}</h3>
          </div>
          <button className="contact-modal-close" onClick={onClose} aria-label={t("contact.close")}>
            <Close />
          </button>
        </div>
        <p className="contact-modal-intro">{t("contact.intro")}</p>

        <ul className="contact-people">
          {PROJECT_CONTACTS.map((p) => (
            <li key={p.email}>
              <span className="contact-person-label">{t(p.labelKey)}</span>
              <b>{p.name}</b>
              <span className="contact-person-role">{t(p.roleKey)}</span>
              <a href={`mailto:${p.email}`} className="contact-person-mail">
                <Mail />
                {p.email}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>,
    document.body,
  );
}
