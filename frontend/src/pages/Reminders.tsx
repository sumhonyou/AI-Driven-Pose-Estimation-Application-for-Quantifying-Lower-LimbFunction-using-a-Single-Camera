import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Plus, Check, Clock } from "../components/Icons";

interface Rem { b: string; s: string; freq: string; time: string; done: boolean; }

export default function Reminders() {
  const { t } = useTranslation();
  const [items, setItems] = useState<Rem[]>([
    { b: t("reminders.r1"), s: t("reminders.r1sub"), freq: t("reminders.daily"), time: "08:00", done: true },
    { b: t("reminders.r2"), s: t("reminders.r2sub"), freq: t("reminders.mwf"), time: "18:30", done: false },
    { b: t("reminders.r3"), s: t("reminders.r3sub"), freq: t("reminders.weekly"), time: "10:00", done: false },
  ]);
  const toggle = (i: number) => setItems((arr) => arr.map((r, idx) => (idx === i ? { ...r, done: !r.done } : r)));

  return (
    <>
      <DashTopbar
        title={t("reminders.title")}
        subtitle={t("reminders.desc")}
        actions={<button className="btn btn-primary"><Plus />{t("reminders.add")}</button>}
      />
      <div className="rem-list">
        {items.map((r, i) => (
          <div className={"rem-card reveal" + (r.done ? " is-done" : "")} key={i}>
            <button className={"rem-check" + (r.done ? " done" : "")} onClick={() => toggle(i)} aria-label={t("reminders.markDone")}><Check /></button>
            <div className="rem-body" style={{ flex: 1 }}><b>{r.b}</b><span>{r.s}</span></div>
            <span className="chip">{r.freq}</span>
            <span className="rem-time" style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><Clock width={15} height={15} />{r.time}</span>
          </div>
        ))}
      </div>
    </>
  );
}
