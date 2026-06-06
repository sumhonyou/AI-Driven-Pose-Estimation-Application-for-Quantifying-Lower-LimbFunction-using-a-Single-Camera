/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark";
type FontScale = 1 | 2 | 3;

interface Prefs {
  theme: Theme;
  toggleTheme: () => void;
  fontScale: FontScale;
  setFontScale: (s: FontScale) => void;
}

const PreferencesContext = createContext<Prefs | null>(null);

const THEME_KEY = "physiofit-theme";
const FS_KEY = "physiofit-fontscale";

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return "light"; // light is the default mode
}

function getInitialFontScale(): FontScale {
  const stored = Number(localStorage.getItem(FS_KEY));
  return stored === 2 || stored === 3 ? (stored as FontScale) : 1;
}

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [fontScale, setFontScaleState] = useState<FontScale>(getInitialFontScale);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute("data-fs", String(fontScale));
    localStorage.setItem(FS_KEY, String(fontScale));
  }, [fontScale]);

  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"));
  const setFontScale = (s: FontScale) => setFontScaleState(s);

  return (
    <PreferencesContext.Provider value={{ theme, toggleTheme, fontScale, setFontScale }}>
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  const ctx = useContext(PreferencesContext);
  if (!ctx) throw new Error("usePreferences must be used within PreferencesProvider");
  return ctx;
}
