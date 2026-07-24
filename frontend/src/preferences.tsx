/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark";
type FontScale = 1 | 2 | 3;

interface Prefs {
  theme: Theme;
  toggleTheme: () => void;
  fontScale: FontScale;
  setFontScale: (s: FontScale) => void;
  /** UAT remediation (Stage R6): spoken live cues during a session. Defaults to ON
   * (HY's call) -- it's the reading-distance fix the feature exists for, so it
   * should be heard immediately rather than requiring discovery of a toggle. */
  audioCues: boolean;
  toggleAudioCues: () => void;
}

const PreferencesContext = createContext<Prefs | null>(null);

const THEME_KEY = "physiofit-theme";
const FS_KEY = "physiofit-fontscale";
const AUDIO_CUES_KEY = "physiofit-audio-cues";

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return "light"; // light is the default mode
}

function getInitialFontScale(): FontScale {
  const stored = Number(localStorage.getItem(FS_KEY));
  return stored === 2 || stored === 3 ? (stored as FontScale) : 1;
}

function getInitialAudioCues(): boolean {
  const stored = localStorage.getItem(AUDIO_CUES_KEY);
  return stored === null ? true : stored === "on";
}

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [fontScale, setFontScaleState] = useState<FontScale>(getInitialFontScale);
  const [audioCues, setAudioCues] = useState<boolean>(getInitialAudioCues);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute("data-fs", String(fontScale));
    localStorage.setItem(FS_KEY, String(fontScale));
  }, [fontScale]);

  useEffect(() => {
    localStorage.setItem(AUDIO_CUES_KEY, audioCues ? "on" : "off");
  }, [audioCues]);

  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"));
  const setFontScale = (s: FontScale) => setFontScaleState(s);
  const toggleAudioCues = () => setAudioCues((v) => !v);

  return (
    <PreferencesContext.Provider
      value={{ theme, toggleTheme, fontScale, setFontScale, audioCues, toggleAudioCues }}
    >
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  const ctx = useContext(PreferencesContext);
  if (!ctx) throw new Error("usePreferences must be used within PreferencesProvider");
  return ctx;
}
