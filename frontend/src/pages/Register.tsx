import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState, type FormEvent } from "react";
import { useAuth } from "../auth";

export default function Register() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { register } = useAuth();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      await register({
        full_name: String(form.get("full_name")),
        email: String(form.get("email")),
        password: String(form.get("password")),
        age_group: String(form.get("age_group")),
        gender: String(form.get("gender")),
        user_type: String(form.get("user_type")),
        focus_area: String(form.get("focus_area")),
      });
      nav("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.registerError"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth">
      <div className="auth-card reveal" style={{ maxWidth: 520 }}>
        <h1>{t("auth.registerTitle")}</h1>
        <p className="sub">{t("auth.registerSub")}</p>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="name">{t("auth.fullName")}</label>
            <input id="name" name="full_name" className="input" placeholder={t("auth.fullNamePh")} autoComplete="name" />
          </div>
          <div className="field">
            <label htmlFor="email">{t("auth.email")}</label>
            <input id="email" name="email" className="input" type="email" placeholder={t("auth.emailPh")} autoComplete="email" required />
          </div>
          <div className="field">
            <label htmlFor="pw">{t("auth.password")}</label>
            <input id="pw" name="password" className="input" type="password" minLength={8} placeholder={t("auth.passwordPh")} autoComplete="new-password" required />
          </div>
          <div className="field-row">
            <div className="field">
              <label htmlFor="age">{t("auth.ageGroup")} <span className="muted">({t("auth.optional")})</span></label>
              <select id="age" name="age_group" className="select">
                <option value="under_40">{t("auth.ageUnder40")}</option>
                <option value="40_60">{t("auth.age40_60")}</option>
                <option value="over_60">{t("auth.ageOver60")}</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="type">{t("auth.userType")}</label>
              <select id="type" name="user_type" className="select">
                <option value="general">{t("auth.typeGeneral")}</option>
                <option value="older_adult">{t("auth.typeOlder")}</option>
                <option value="athlete">{t("auth.typeAthlete")}</option>
              </select>
            </div>
          </div>
          <div className="field-row">
            <div className="field">
              <label htmlFor="gender">{t("auth.gender")} <span className="muted">({t("auth.optional")})</span></label>
              <select id="gender" name="gender" className="select">
                <option value="female">{t("auth.genderF")}</option>
                <option value="male">{t("auth.genderM")}</option>
                <option value="prefer_not_to_say">{t("auth.genderOther")}</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="focus">{t("auth.focusArea")}</label>
              <select id="focus" name="focus_area" className="select">
                <option value="knee">{t("auth.focusKnee")}</option>
                <option value="ankle">{t("auth.focusAnkle")}</option>
                <option value="both">{t("auth.focusBoth")}</option>
              </select>
            </div>
          </div>
          <p className="muted" style={{ fontSize: "0.8rem", margin: "4px 0 18px" }}>{t("auth.agree")}</p>
          {error && <p className="muted" style={{ color: "var(--coral)", marginBottom: 14 }}>{error}</p>}
          <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={submitting}>{submitting ? t("auth.loading") : t("auth.register")}</button>
        </form>
        <p className="auth-alt">{t("auth.haveAccount")} <Link to="/login">{t("auth.logIn")}</Link></p>
      </div>
    </div>
  );
}
