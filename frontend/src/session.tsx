/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type SessionFlow = {
  mode: "functional" | "rehab";
  exerciseCode: string | null;
  sessionId: string | null;
  // Stage R13 (UAT): set when a session is launched by clicking a specific
  // reminder card (Reminders.tsx `openExercise`), carried through camera
  // setup + the live session, and consumed once at session completion to
  // auto-tick THAT reminder -- never "any active reminder with a matching
  // exercise_code" (HY's explicit spec). null for every other entry point
  // (Exercise Selection, Retry from Report, etc.).
  reminderId: string | null;
  setMode: (mode: "functional" | "rehab") => void;
  setExerciseCode: (code: string) => void;
  setSessionId: (id: string | null) => void;
  setReminderId: (id: string | null) => void;
  resetSession: () => void;
};

const SessionContext = createContext<SessionFlow | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<"functional" | "rehab">("functional");
  const [exerciseCode, setExerciseCode] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [reminderId, setReminderId] = useState<string | null>(null);

  const value = useMemo(
    () => ({
      mode,
      exerciseCode,
      sessionId,
      reminderId,
      setMode,
      setExerciseCode,
      setSessionId,
      setReminderId,
      resetSession() {
        setSessionId(null);
        setExerciseCode(null);
        setReminderId(null);
      },
    }),
    [mode, exerciseCode, sessionId, reminderId],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSessionFlow() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSessionFlow must be used inside SessionProvider");
  return context;
}
