import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { Alert, Eye, EyeOff, Lock, Mail, User } from "../components/Icons";
import { ApiError } from "../services/apiClient";
import { isValidEmailFormat } from "../utils/format";

type AuthMode = "login" | "register";
type InvalidFields = { fullName: boolean; email: boolean; password: boolean; age: boolean };

const emptyInvalid: InvalidFields = {
  fullName: false,
  email: false,
  password: false,
  age: false,
};
const MIN_AGE = 1;
const MAX_AGE = 120;

export default function Login() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { login, register } = useAuth();
  const reduceMotion = useReducedMotion();
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const ageRef = useRef<HTMLInputElement>(null);

  const [mode, setMode] = useState<AuthMode>("login");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [ageError, setAgeError] = useState("");
  const [formAlert, setFormAlert] = useState("");
  const [invalid, setInvalid] = useState<InvalidFields>(emptyInvalid);
  const [shaking, setShaking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const clearFeedback = () => {
    setEmailError("");
    setPasswordError("");
    setAgeError("");
    setFormAlert("");
    setInvalid(emptyInvalid);
  };

  const triggerShake = () => {
    setShaking(false);
    requestAnimationFrame(() => {
      setShaking(true);
      window.setTimeout(() => setShaking(false), 450);
    });
  };

  const switchMode = (nextMode: AuthMode) => {
    if (nextMode === mode) return;
    clearFeedback();
    setShowPassword(false);
    setMode(nextMode);
  };

  const getInputClass = (field: keyof InvalidFields) =>
    "input auth-input" +
    (invalid[field] ? " input-error" : "") +
    (invalid[field] && shaking ? " shake" : "");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearFeedback();

    const form = new FormData(event.currentTarget);
    const fullName = String(form.get("full_name") ?? "").trim();
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const ageValue = Number(form.get("exact_age"));
    const emailOk = isValidEmailFormat(email);
    const passwordOk = mode === "login" || password.length >= 8;
    const ageOk =
      mode === "login" || (Number.isFinite(ageValue) && ageValue >= MIN_AGE && ageValue <= MAX_AGE);

    if (!emailOk || !passwordOk || !ageOk) {
      if (!emailOk) setEmailError(t("auth.invalidEmailFormat"));
      if (!passwordOk) setPasswordError(t("auth.passwordTooShort"));
      if (!ageOk) setAgeError(t("auth.invalidAge"));
      setInvalid({ fullName: false, email: !emailOk, password: !passwordOk, age: !ageOk });
      triggerShake();
      (!emailOk ? emailRef : !passwordOk ? passwordRef : ageRef).current?.focus();
      return;
    }

    setSubmitting(true);
    try {
      if (mode === "login") {
        await login({ email, password });
        console.info("Login successful; navigating to dashboard.");
      } else {
        await register({
          full_name: fullName,
          email,
          password,
          exact_age: ageValue,
          gender: String(form.get("gender")),
          user_type: String(form.get("user_type")),
          focus_area: String(form.get("focus_area")),
        });
        console.info("Registration successful; navigating to dashboard.");
      }
      nav("/dashboard");
    } catch (err) {
      const isBadCredentials = err instanceof ApiError && err.status === 401;
      setFormAlert(
        isBadCredentials
          ? t("auth.invalidCredentials")
          : err instanceof Error
            ? err.message
            : mode === "login"
              ? t("auth.loginError")
              : t("auth.registerError"),
      );
      setInvalid({
        fullName: false,
        email: true,
        password: isBadCredentials,
        age: false,
      });
      triggerShake();
      console.info(`${mode === "login" ? "Login" : "Registration"} failed.`);
    } finally {
      setSubmitting(false);
    }
  };

  const formMotion = reduceMotion
    ? {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
      }
    : {
        initial: { opacity: 0, x: mode === "login" ? -24 : 24 },
        animate: { opacity: 1, x: 0 },
        exit: { opacity: 0, x: mode === "login" ? 24 : -24 },
      };

  return (
    <div className="auth auth-flow">
      <div className="auth-reveal-bg" aria-hidden="true" />
      <div className="auth-card auth-flow-card reveal">
        <div className="auth-flow-head">
          <h1>{mode === "login" ? t("auth.loginTitle") : t("auth.registerTitle")}</h1>
          <p className="sub">{mode === "login" ? t("auth.loginSub") : t("auth.registerSub")}</p>
        </div>

        <div className="auth-mode-toggle" role="tablist" aria-label="Authentication mode">
          <motion.span
            className="auth-mode-thumb"
            animate={{ x: mode === "login" ? "0%" : "100%" }}
            transition={{ duration: reduceMotion ? 0 : 0.28, ease: [0.22, 0.61, 0.36, 1] }}
          />
          <button
            type="button"
            role="tab"
            aria-selected={mode === "login"}
            className={mode === "login" ? "active" : ""}
            onClick={() => switchMode("login")}
          >
            {t("auth.logIn")}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "register"}
            className={mode === "register" ? "active" : ""}
            onClick={() => switchMode("register")}
          >
            {t("auth.signUp")}
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={mode}
              {...formMotion}
              transition={{ duration: reduceMotion ? 0.12 : 0.32, ease: "easeOut" }}
            >
              {mode === "register" && (
                <div className="field auth-field">
                  <label htmlFor="name">{t("auth.fullName")}</label>
                  <div className="auth-input-wrap">
                    <User />
                    <input
                      id="name"
                      name="full_name"
                      className={getInputClass("fullName")}
                      placeholder={t("auth.fullNamePh")}
                      autoComplete="name"
                    />
                  </div>
                </div>
              )}

              <div className="field auth-field">
                <label htmlFor="email">{t("auth.email")}</label>
                <div className="auth-input-wrap">
                  <Mail />
                  <input
                    id="email"
                    name="email"
                    ref={emailRef}
                    className={getInputClass("email")}
                    type="email"
                    placeholder={t("auth.emailPh")}
                    autoComplete="email"
                    aria-invalid={invalid.email || undefined}
                    aria-describedby={emailError ? "email-error" : undefined}
                  />
                </div>
                {emailError && (
                  <p className="field-error" id="email-error">
                    <Alert />
                    {emailError}
                  </p>
                )}
              </div>

              <div className="field auth-field">
                <label htmlFor="pw">{t("auth.password")}</label>
                <div className="auth-input-wrap">
                  <Lock />
                  <input
                    id="pw"
                    name="password"
                    ref={passwordRef}
                    className={getInputClass("password")}
                    type={showPassword ? "text" : "password"}
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    aria-invalid={invalid.password || undefined}
                    aria-describedby={passwordError ? "password-error" : undefined}
                  />
                  <button
                    type="button"
                    className="auth-password-toggle"
                    onClick={() => setShowPassword((shown) => !shown)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff /> : <Eye />}
                  </button>
                </div>
                {passwordError && (
                  <p className="field-error" id="password-error">
                    <Alert />
                    {passwordError}
                  </p>
                )}
              </div>

              {mode === "register" ? (
                <>
                  <div className="field-row auth-field-row">
                    <div className="field">
                      <label htmlFor="age">{t("auth.age")}</label>
                      <input
                        id="age"
                        name="exact_age"
                        ref={ageRef}
                        className={getInputClass("age")}
                        type="number"
                        min={MIN_AGE}
                        max={MAX_AGE}
                        placeholder={t("auth.agePh")}
                        aria-invalid={invalid.age || undefined}
                        aria-describedby={ageError ? "age-error" : undefined}
                      />
                      {ageError && (
                        <p className="field-error" id="age-error">
                          <Alert />
                          {ageError}
                        </p>
                      )}
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
                  <div className="field-row auth-field-row">
                    <div className="field">
                      <label htmlFor="gender">{t("auth.gender")}</label>
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
                  <p className="muted auth-agree">{t("auth.agree")}</p>
                </>
              ) : (
                <div className="auth-form-meta">
                  <label className="auth-remember">
                    <input type="checkbox" name="remember" />
                    <span>{t("auth.remember")}</span>
                  </label>
                  <a href="#" onClick={(e) => e.preventDefault()}>
                    {t("auth.forgot")}
                  </a>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {formAlert && (
            <div className="form-alert" role="alert">
              <Alert />
              <span>{formAlert}</span>
            </div>
          )}

          <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={submitting}>
            {submitting
              ? t("auth.loading")
              : mode === "login"
                ? t("auth.login")
                : t("auth.register")}
          </button>
        </form>

        {mode === "login" && (
          <>
            <div className="divider">{t("auth.or")}</div>
            <Link className="btn btn-ghost btn-block" to="/">
              {t("auth.continueGuest")}
            </Link>
          </>
        )}

        <div className="auth-alt">
          {mode === "login" ? t("auth.noAccount") : t("auth.haveAccount")}{" "}
          <button type="button" onClick={() => switchMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? t("auth.signUp") : t("auth.logIn")}
          </button>
        </div>
      </div>
    </div>
  );
}
