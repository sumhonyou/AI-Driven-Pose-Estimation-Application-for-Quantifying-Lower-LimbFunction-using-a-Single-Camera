/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type SessionFlow = {
  mode: "functional" | "rehab";
  exerciseCode: string | null;
  sessionId: string | null;
  setMode: (mode: "functional" | "rehab") => void;
  setExerciseCode: (code: string) => void;
  setSessionId: (id: string | null) => void;
  resetSession: () => void;
};

const SessionContext = createContext<SessionFlow | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<"functional" | "rehab">("functional");
  const [exerciseCode, setExerciseCode] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const value = useMemo(
    () => ({
      mode,
      exerciseCode,
      sessionId,
      setMode,
      setExerciseCode,
      setSessionId,
      resetSession() {
        setSessionId(null);
        setExerciseCode(null);
      },
    }),
    [mode, exerciseCode, sessionId],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSessionFlow() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSessionFlow must be used inside SessionProvider");
  return context;
}
