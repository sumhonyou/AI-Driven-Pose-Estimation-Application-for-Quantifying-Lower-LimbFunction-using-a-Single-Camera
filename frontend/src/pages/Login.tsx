import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState, type FormEvent } from "react";
import { useAuth } from "../auth";

export default function Login() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      await login({
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      nav("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.loginError"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth">
      <div className="auth-card reveal">
        <h1>{t("auth.loginTitle")}</h1>
        <p className="sub">{t("auth.loginSub")}</p>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="email">{t("auth.email")}</label>
            <input id="email" name="email" className="input" type="email" placeholder={t("auth.emailPh")} autoComplete="email" required />
          </div>
          <div className="field">
            <label htmlFor="pw">{t("auth.password")}</label>
            <input id="pw" name="password" className="input" type="password" placeholder={t("auth.passwordPh")} autoComplete="current-password" required />
          </div>
          <div style={{ textAlign: "right", marginBottom: 20 }}>
            <a href="#" onClick={(e) => e.preventDefault()} style={{ fontSize: "0.84rem", color: "var(--accent-text)", fontWeight: 600 }}>{t("auth.forgot")}</a>
          </div>
          {error && <p className="muted" style={{ color: "var(--coral)", marginBottom: 14 }}>{error}</p>}
          <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={submitting}>{submitting ? t("auth.loading") : t("auth.login")}</button>
        </form>
        <div className="divider">{t("auth.or")}</div>
        <Link className="btn btn-ghost btn-block" to="/">{t("auth.continueGuest")}</Link>
        <p className="auth-alt">{t("auth.noAccount")} <Link to="/register">{t("auth.signUp")}</Link></p>
      </div>
    </div>
  );
}
