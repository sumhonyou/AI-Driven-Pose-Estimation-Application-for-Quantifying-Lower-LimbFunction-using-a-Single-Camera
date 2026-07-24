// Immediate hover/focus hint for topbar icon controls. Native `title` tooltips
// are too slow/easy to miss, so these render a visible bubble under the control.
import type { ReactNode } from "react";

interface CtrlHintProps {
  text: string;
  /** Right-align the bubble when the control sits near the viewport edge. */
  align?: "center" | "end";
  children: ReactNode;
}

export default function CtrlHint({ text, align = "center", children }: CtrlHintProps) {
  return (
    <span className={"ctrl-hint" + (align === "end" ? " ctrl-hint--end" : "")}>
      {children}
      <span className="ctrl-hint-bubble" role="tooltip">
        {text}
      </span>
    </span>
  );
}
