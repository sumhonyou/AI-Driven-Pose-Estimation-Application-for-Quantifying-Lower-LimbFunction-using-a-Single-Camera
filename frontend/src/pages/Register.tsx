import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useRef, useState, type FormEvent } from "react";
import { useAuth } from "../auth";
import { Alert } from "../components/Icons";
import { isValidEmailFormat } from "../utils/format";

type InvalidFields = { email: boolean; password: boolean };

export default function Register() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { register } = useAuth();
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [formAlert, setFormAlert] = useState("");
  const [invalid, setInvalid] = useState<InvalidFields>({ email: false, password: false });
  const [shaking, setShaking] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const triggerShake = () => {
    setShaking(false);
    requestAnimationFrame(() => {
      setShaking(true);
      window.setTimeout(() => setShaking(false), 450);
    });
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setEmailError("");
    setPasswordError("");
    setFormAlert("");
    setInvalid({ email: false, password: false });

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");

    const emailOk = isValidEmailFormat(email);
    const passwordOk = password.length >= 8;

    if (!emailOk || !passwordOk) {
      if (!emailOk) setEmailError(t("auth.invalidEmailFormat"));
      if (!passwordOk) setPasswordError(t("auth.passwordTooShort"));
      setInvalid({ email: !emailOk, password: !passwordOk });
      triggerShake();
      (emailOk ? passwordRef : emailRef).current?.focus();
      return;
    }

    setSubmitting(true);
    try {
      await register({
        full_name: String(form.get("full_name")),
        email,
        password,
        age_group: String(form.get("age_group")),
        gender: String(form.get("gender")),
        user_type: String(form.get("user_type")),
        focus_area: String(form.get("focus_area")),
      });
      nav("/dashboard");
    } catch (err) {
      setFormAlert(err instanceof Error ? err.message : t("auth.registerError"));
      setInvalid({ email: true, password: false });
    } finally {
      setSubmitting(false);
    }
  };

  const emailClass =
    "input" + (invalid.email ? " input-error" : "") + (invalid.email && shaking ? " shake" : "");
  const passwordClass =
    "input" +
    (invalid.password ? " input-error" : "") +
    (invalid.password && shaking ? " shake" : "");

  return (
    <div className="auth">
      <div className="auth-card reveal" style={{ maxWidth: 520 }}>
        <h1>{t("auth.registerTitle")}</h1>
        <p className="sub">{t("auth.registerSub")}</p>
        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="name">{t("auth.fullName")}</label>
            <input
              id="name"
              name="full_name"
              className="input"
              placeholder={t("auth.fullNamePh")}
              autoComplete="name"
            />
          </div>
          <div className="field">
            <label htmlFor="email">{t("auth.email")}</label>
            <input
              id="email"
              name="email"
              ref={emailRef}
              className={emailClass}
              type="email"
              placeholder={t("auth.emailPh")}
              autoComplete="email"
              aria-invalid={invalid.email || undefined}
              aria-describedby={emailError ? "email-error" : undefined}
            />
            {emailError && (
              <p className="field-error" id="email-error">
                <Alert />
                {emailError}
              </p>
            )}
          </div>
          <div className="field">
            <label htmlFor="pw">{t("auth.password")}</label>
            <input
              id="pw"
              name="password"
              ref={passwordRef}
              className={passwordClass}
              type="password"
              autoComplete="new-password"
              aria-invalid={invalid.password || undefined}
              aria-describedby={passwordError ? "password-error" : undefined}
            />
            {passwordError && (
              <p className="field-error" id="password-error">
                <Alert />
                {passwordError}
              </p>
            )}
          </div>
          <div className="field-row">
            <div className="field">
              <label htmlFor="age">
                {t("auth.ageGroup")} <span className="muted">({t("auth.optional")})</span>
              </label>
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
              <label htmlFor="gender">
                {t("auth.gender")} <span className="muted">({t("auth.optional")})</span>
              </label>
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
          <p className="muted" style={{ fontSize: "0.8rem", margin: "4px 0 18px" }}>
            {t("auth.agree")}
          </p>
          {formAlert && (
            <div className="form-alert" role="alert">
              <Alert />
              <span>{formAlert}</span>
            </div>
          )}
          <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={submitting}>
            {submitting ? t("auth.loading") : t("auth.register")}
          </button>
        </form>
        <p className="auth-alt">
          {t("auth.haveAccount")} <Link to="/login">{t("auth.logIn")}</Link>
        </p>
      </div>
    </div>
  );
}
