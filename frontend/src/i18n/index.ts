import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import en from "./en";
import zh from "./zh";
import ms from "./ms";

export const LANGUAGES = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "zh", label: "中文", flag: "🇨🇳" },
  { code: "ms", label: "Bahasa Malaysia", flag: "🇲🇾" },
] as const;

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zh: { translation: zh },
      ms: { translation: ms },
    },
    fallbackLng: "en",
    supportedLngs: ["en", "zh", "ms"],
    interpolation: { escapeValue: false },
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: "physiofit-lang",
      caches: ["localStorage"],
    },
  });

export default i18n;
