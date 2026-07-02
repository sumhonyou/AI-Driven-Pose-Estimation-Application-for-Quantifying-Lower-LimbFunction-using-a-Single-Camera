import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useRef, useState, type FormEvent } from "react";
import { useAuth } from "../auth";
import { ApiError } from "../services/apiClient";
import { Alert } from "../components/Icons";
import { isValidEmailFormat } from "../utils/format";

type InvalidFields = { email: boolean; password: boolean };

export default function Login() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { login } = useAuth();
  const emailRef = useRef<HTMLInputElement>(null);

  const [emailError, setEmailError] = useState("");
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
    setFormAlert("");
    setInvalid({ email: false, password: false });

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");

    if (!isValidEmailFormat(email)) {
      setEmailError(t("auth.invalidEmailFormat"));
      setInvalid({ email: true, password: false });
      triggerShake();
      emailRef.current?.focus();
      return;
    }

    setSubmitting(true);
    try {
      await login({ email, password });
      nav("/dashboard");
    } catch (err) {
      const isBadCredentials = err instanceof ApiError && err.status === 401;
      setFormAlert(
        isBadCredentials
          ? t("auth.invalidCredentials")
          : err instanceof Error
            ? err.message
            : t("auth.loginError"),
      );
      if (isBadCredentials) {
        setInvalid({ email: true, password: true });
        triggerShake();
      }
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
      <div className="auth-card reveal">
        <h1>{t("auth.loginTitle")}</h1>
        <p className="sub">{t("auth.loginSub")}</p>
        <form onSubmit={handleSubmit} noValidate>
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
              className={passwordClass}
              type="password"
              autoComplete="current-password"
              aria-invalid={invalid.password || undefined}
            />
          </div>
          <div style={{ textAlign: "right", marginBottom: 20 }}>
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              style={{ fontSize: "0.84rem", color: "var(--accent-text)", fontWeight: 600 }}
            >
              {t("auth.forgot")}
            </a>
          </div>
          {formAlert && (
            <div className="form-alert" role="alert">
              <Alert />
              <span>{formAlert}</span>
            </div>
          )}
          <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={submitting}>
            {submitting ? t("auth.loading") : t("auth.login")}
          </button>
        </form>
        <div className="divider">{t("auth.or")}</div>
        <Link className="btn btn-ghost btn-block" to="/">
          {t("auth.continueGuest")}
        </Link>
        <p className="auth-alt">
          {t("auth.noAccount")} <Link to="/register">{t("auth.signUp")}</Link>
        </p>
      </div>
    </div>
  );
}
