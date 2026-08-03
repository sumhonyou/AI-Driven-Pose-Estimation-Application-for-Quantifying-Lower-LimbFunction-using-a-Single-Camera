import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { profileService } from "../services/profileService";
import { useAuth } from "../auth";
import { useReveal } from "../useReveal";
import { Pencil } from "../components/Icons";
import type { Profile } from "../types/api";

const MAX_AVATAR_FILE_BYTES = 2 * 1024 * 1024;
const MIN_AGE = 1;
const MAX_AGE = 120;

function ageLabel(t: (k: string) => string, age: number | null) {
  return age != null ? String(age) : t("profile.notSet");
}

function genderLabel(t: (k: string) => string, code: string | null) {
  switch (code) {
    case "female":
      return t("auth.genderF");
    case "male":
      return t("auth.genderM");
    case "prefer_not_to_say":
      return t("auth.genderOther");
    default:
      return t("profile.notSet");
  }
}

function userTypeLabel(t: (k: string) => string, code: string | null) {
  switch (code) {
    case "older_adult":
      return t("auth.typeOlder");
    case "athlete":
      return t("auth.typeAthlete");
    case "general":
      return t("auth.typeGeneral");
    default:
      return t("profile.notSet");
  }
}

function focusAreaLabel(t: (k: string) => string, code: string | null) {
  switch (code) {
    case "knee":
      return t("auth.focusKnee");
    case "ankle":
      return t("auth.focusAnkle");
    case "both":
      return t("auth.focusBoth");
    default:
      return t("profile.notSet");
  }
}

function focusAreaTagLabel(t: (k: string) => string, code: string | null) {
  switch (code) {
    case "knee":
      return t("profile.focusTagKnee");
    case "ankle":
      return t("profile.focusTagAnkle");
    case "both":
      return t("profile.focusTagBoth");
    default:
      return t("profile.focusTagUnset");
  }
}

type DetailRow = {
  label: string;
  value: string;
  wide?: boolean;
};

export default function Profile() {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarError, setAvatarError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const reduceMotion = useReducedMotion();

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

  // Re-run reveal after async profile load — panels don't exist on initial nav.
  useReveal([profile]);

  // Focus the name field when entering edit mode, with the caret at the end.
  useEffect(() => {
    if (!isEditing) return;
    const input = nameInputRef.current;
    if (!input) return;
    input.focus();
    const end = input.value.length;
    input.setSelectionRange(end, end);
  }, [isEditing]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setMessage("");
    const form = new FormData(event.currentTarget);
    const height = String(form.get("height_cm") || "");
    const weight = String(form.get("weight_kg") || "");
    const ageValue = Number(form.get("exact_age"));
    // Age is required for WBLT McBride banding — never send null.
    if (!Number.isFinite(ageValue) || ageValue < MIN_AGE || ageValue > MAX_AGE) {
      setError(t("auth.invalidAge"));
      return;
    }

    setSaving(true);
    try {
      const updated = await profileService.update({
        full_name: String(form.get("full_name") || ""),
        exact_age: ageValue,
        gender: String(form.get("gender") || ""),
        height_cm: height ? Number(height) : null,
        weight_kg: weight ? Number(weight) : null,
        user_type: String(form.get("user_type") || ""),
        focus_area: String(form.get("focus_area") || ""),
        self_reported_note: String(form.get("self_reported_note") || ""),
      });
      setProfile(updated);
      await refreshUser();
      setMessage(t("profile.saved"));
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("profile.saveError"));
    } finally {
      setSaving(false);
    }
  };

  const handlePhotoPick = () => fileInputRef.current?.click();

  const handlePhotoChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setAvatarError("");
    if (!file.type.startsWith("image/")) {
      setAvatarError(t("profile.photoInvalidType"));
      return;
    }
    if (file.size > MAX_AVATAR_FILE_BYTES) {
      setAvatarError(t("profile.photoTooLarge"));
      return;
    }

    setAvatarUploading(true);
    try {
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
      const updated = await profileService.update({ avatar_image: dataUrl });
      setProfile(updated);
      await refreshUser();
    } catch (err) {
      setAvatarError(err instanceof Error ? err.message : t("profile.photoUploadError"));
    } finally {
      setAvatarUploading(false);
    }
  };

  const initials = profile?.full_name?.trim().slice(0, 2).toUpperCase() || "PF";
  const panelMotion = reduceMotion
    ? {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: 0.12 },
      }
    : {
        initial: { opacity: 0, x: 18, scale: 0.985, filter: "blur(6px)" },
        animate: { opacity: 1, x: 0, scale: 1, filter: "blur(0px)" },
        exit: { opacity: 0, x: -14, scale: 0.992, filter: "blur(5px)" },
        transition: { duration: 0.24, ease: [0.16, 1, 0.3, 1] as const },
      };

  const detailRows: DetailRow[] = profile
    ? [
        { label: t("auth.fullName"), value: profile.full_name || t("profile.notSet") },
        { label: t("auth.email"), value: user?.email || t("profile.notSet") },
        { label: t("auth.userType"), value: userTypeLabel(t, profile.user_type) },
        { label: t("auth.age"), value: ageLabel(t, profile.exact_age) },
        { label: t("auth.gender"), value: genderLabel(t, profile.gender) },
        {
          label: t("profile.height"),
          value: profile.height_cm != null ? `${profile.height_cm} cm` : t("profile.notSet"),
        },
        {
          label: t("profile.weight"),
          value: profile.weight_kg != null ? `${profile.weight_kg} kg` : t("profile.notSet"),
        },
        { label: t("auth.focusArea"), value: focusAreaLabel(t, profile.focus_area) },
        {
          label: t("profile.note"),
          value: profile.self_reported_note || t("profile.notSet"),
          wide: true,
        },
      ]
    : [];

  return (
    <>
      <DashTopbar title={t("profile.title")} subtitle={t("profile.desc")} />

      {loading && <p className="muted">{t("common.loading")}</p>}

      {!loading && profile && (
        <div className="profile-grid">
          <div className="panel reveal profile-identity-card">
            <div className="profile-avatar-wrap">
              {profile.avatar_image ? (
                <img src={profile.avatar_image} alt="" className="profile-avatar-img" />
              ) : (
                <span className="profile-avatar-fallback">{initials}</span>
              )}
              <button
                type="button"
                className="profile-avatar-upload-btn"
                onClick={handlePhotoPick}
                disabled={avatarUploading}
                aria-label={t("profile.uploadPhoto")}
                title={t("profile.uploadPhoto")}
              >
                <Pencil width={18} height={18} />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="sr-only"
                onChange={handlePhotoChange}
              />
            </div>
            <b className="profile-avatar-name">{profile.full_name || t("profile.notSet")}</b>
            <span className="profile-avatar-role">{userTypeLabel(t, profile.user_type)}</span>
            <span className="pill profile-focus-tag">
              {focusAreaTagLabel(t, profile.focus_area)}
            </span>
            <div className="profile-mini-list" aria-label={t("profile.detailsHeading")}>
              <div>
                <span>{t("auth.age")}</span>
                <b>{ageLabel(t, profile.exact_age)}</b>
              </div>
              <div>
                <span>{t("auth.focusArea")}</span>
                <b>{focusAreaLabel(t, profile.focus_area)}</b>
              </div>
              <div>
                <span>{t("auth.email")}</span>
                <b>{user?.email || t("profile.notSet")}</b>
              </div>
            </div>
            {avatarUploading && (
              <p className="muted profile-avatar-status">{t("profile.uploadingPhoto")}</p>
            )}
            {avatarError && (
              <p className="muted profile-avatar-status" style={{ color: "var(--coral)" }}>
                {avatarError}
              </p>
            )}
          </div>

          <div className="panel reveal profile-details-card">
            <div className="profile-details-head">
              <div>
                <h3>{t("profile.detailsHeading")}</h3>
                <p>{t("profile.detailsSub")}</p>
              </div>
              {!isEditing && (
                <button
                  className="btn btn-ghost profile-edit-toggle"
                  type="button"
                  aria-expanded={isEditing}
                  onClick={() => {
                    setIsEditing(true);
                    setMessage("");
                  }}
                >
                  <Pencil width={16} height={16} />
                  {t("profile.editProfile")}
                </button>
              )}
              {isEditing && <span className="profile-edit-badge">{t("profile.editProfile")}</span>}
            </div>

            <div className="profile-mode-stage">
              <AnimatePresence mode="wait" initial={false}>
                {!isEditing ? (
                  <motion.section
                    key="profile-details"
                    className="profile-mode-panel"
                    {...panelMotion}
                  >
                    <div className="profile-detail-rows">
                      {detailRows.map((row) => (
                        <div
                          className={
                            "profile-detail-row" + (row.wide ? " profile-detail-row--wide" : "")
                          }
                          key={row.label}
                        >
                          <span className="profile-detail-label">{row.label}</span>
                          <span className="profile-detail-value">{row.value}</span>
                        </div>
                      ))}
                    </div>
                    {message && <p className="profile-saved-msg">{message}</p>}
                  </motion.section>
                ) : (
                  <motion.section
                    key="profile-edit"
                    className="profile-mode-panel"
                    {...panelMotion}
                  >
                    <form onSubmit={handleSubmit}>
                      <div className="field-row">
                        <div className="field">
                          <label htmlFor="full_name">{t("auth.fullName")}</label>
                          <input
                            ref={nameInputRef}
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
                          <label htmlFor="exact_age">{t("auth.age")}</label>
                          <input
                            id="exact_age"
                            name="exact_age"
                            className="input"
                            type="number"
                            min={1}
                            max={120}
                            placeholder={t("auth.agePh")}
                            defaultValue={profile.exact_age ?? ""}
                          />
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
                      {error && (
                        <p className="muted" style={{ color: "var(--coral)" }}>
                          {error}
                        </p>
                      )}
                      <div className="profile-edit-actions">
                        <button
                          className="btn btn-cancel"
                          type="button"
                          onClick={() => {
                            setIsEditing(false);
                            setError("");
                          }}
                          disabled={saving}
                        >
                          {t("common.cancel")}
                        </button>
                        <button className="btn btn-primary" type="submit" disabled={saving}>
                          {saving ? t("profile.saving") : t("profile.save")}
                        </button>
                      </div>
                    </form>
                  </motion.section>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      )}

      {!loading && !profile && <p className="muted">{error || t("profile.loadError")}</p>}
    </>
  );
}
