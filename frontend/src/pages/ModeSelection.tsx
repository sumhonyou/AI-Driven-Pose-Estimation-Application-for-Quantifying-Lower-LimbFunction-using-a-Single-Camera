import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Activity, Stretch, ArrowRight } from "../components/Icons";
import { useSessionFlow } from "../session";

export default function ModeSelection() {
  const { t } = useTranslation();
  const { setMode, resetSession } = useSessionFlow();
  const choose = (mode: "functional" | "rehab") => {
    resetSession();
    setMode(mode);
  };
  return (
    <>
      <DashTopbar title={t("mode.title")} subtitle={t("mode.desc")} />
      <div className="choice-grid">
        <Link className="choice reveal" to="/exercise?mode=functional" onClick={() => choose("functional")}>
          <span className="ci"><Activity width={28} height={28} /></span>
          <h3>{t("mode.funcTitle")}</h3>
          <p>{t("mode.funcDesc")}</p>
          <span className="go">{t("mode.choose")}<ArrowRight /></span>
        </Link>
        <Link className="choice reveal" to="/exercise?mode=rehab" onClick={() => choose("rehab")}>
          <span className="ci"><Stretch width={28} height={28} /></span>
          <h3>{t("mode.rehabTitle")}</h3>
          <p>{t("mode.rehabDesc")}</p>
          <span className="go">{t("mode.choose")}<ArrowRight /></span>
        </Link>
      </div>
    </>
  );
}
