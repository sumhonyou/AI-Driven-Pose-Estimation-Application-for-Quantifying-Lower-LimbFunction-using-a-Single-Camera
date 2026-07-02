import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { profileService } from "../services/profileService";
import type { Profile } from "../types/api";

export default function Profile() {
  const { t } = useTranslation();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    profileService
      .get()
      .then((data) => {
        if (!cancelled) setProfile(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : t("profile.loadError"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [t]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    const form = new FormData(event.currentTarget);
    const height = String(form.get("height_cm") || "");
    const weight = String(form.get("weight_kg") || "");

    try {
      const updated = await profileService.update({
        full_name: String(form.get("full_name") || ""),
        age_group: String(form.get("age_group") || ""),
        gender: String(form.get("gender") || ""),
        height_cm: height ? Number(height) : null,
        weight_kg: weight ? Number(weight) : null,
        user_type: String(form.get("user_type") || ""),
        focus_area: String(form.get("focus_area") || ""),
        self_reported_note: String(form.get("self_reported_note") || ""),
      });
      setProfile(updated);
      setMessage(t("profile.saved"));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("profile.saveError"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <DashTopbar title={t("profile.title")} subtitle={t("profile.desc")} />
      <div className="panel reveal" style={{ maxWidth: 760 }}>
        {loading && <p className="muted">{t("common.loading")}</p>}
        {!loading && profile && (
          <form onSubmit={handleSubmit}>
            <div className="field-row">
              <div className="field">
                <label htmlFor="full_name">{t("auth.fullName")}</label>
                <input
                  id="full_name"
                  name="full_name"
                  className="input"
                  defaultValue={profile.full_name || ""}
                />
              </div>
              <div className="field">
                <label htmlFor="user_type">{t("auth.userType")}</label>
                <select
                  id="user_type"
                  name="user_type"
                  className="select"
                  defaultValue={profile.user_type || "general"}
                >
                  <option value="general">{t("auth.typeGeneral")}</option>
                  <option value="older_adult">{t("auth.typeOlder")}</option>
                  <option value="athlete">{t("auth.typeAthlete")}</option>
                </select>
              </div>
            </div>
            <div className="field-row">
              <div className="field">
                <label htmlFor="age_group">{t("auth.ageGroup")}</label>
                <select
                  id="age_group"
                  name="age_group"
                  className="select"
                  defaultValue={profile.age_group || "under_40"}
                >
                  <option value="under_40">{t("auth.ageUnder40")}</option>
                  <option value="40_60">{t("auth.age40_60")}</option>
                  <option value="over_60">{t("auth.ageOver60")}</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="gender">{t("auth.gender")}</label>
                <select
                  id="gender"
                  name="gender"
                  className="select"
                  defaultValue={profile.gender || "prefer_not_to_say"}
                >
                  <option value="female">{t("auth.genderF")}</option>
                  <option value="male">{t("auth.genderM")}</option>
                  <option value="prefer_not_to_say">{t("auth.genderOther")}</option>
                </select>
              </div>
            </div>
            <div className="field-row">
              <div className="field">
                <label htmlFor="height_cm">{t("profile.height")}</label>
                <input
                  id="height_cm"
                  name="height_cm"
                  className="input"
                  type="number"
                  step="0.1"
                  min="0"
                  defaultValue={profile.height_cm ?? ""}
                />
              </div>
              <div className="field">
                <label htmlFor="weight_kg">{t("profile.weight")}</label>
                <input
                  id="weight_kg"
                  name="weight_kg"
                  className="input"
                  type="number"
                  step="0.1"
                  min="0"
                  defaultValue={profile.weight_kg ?? ""}
                />
              </div>
            </div>
            <div className="field">
              <label htmlFor="focus_area">{t("auth.focusArea")}</label>
              <select
                id="focus_area"
                name="focus_area"
                className="select"
                defaultValue={profile.focus_area || "both"}
              >
                <option value="knee">{t("auth.focusKnee")}</option>
                <option value="ankle">{t("auth.focusAnkle")}</option>
                <option value="both">{t("auth.focusBoth")}</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="self_reported_note">{t("profile.note")}</label>
              <textarea
                id="self_reported_note"
                name="self_reported_note"
                className="input"
                rows={4}
                defaultValue={profile.self_reported_note || ""}
              />
            </div>
            {message && (
              <p className="muted" style={{ color: "var(--accent-text)" }}>
                {message}
              </p>
            )}
            {error && (
              <p className="muted" style={{ color: "var(--coral)" }}>
                {error}
              </p>
            )}
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? t("profile.saving") : t("profile.save")}
            </button>
          </form>
        )}
        {!loading && !profile && <p className="muted">{error || t("profile.loadError")}</p>}
      </div>
    </>
  );
}
