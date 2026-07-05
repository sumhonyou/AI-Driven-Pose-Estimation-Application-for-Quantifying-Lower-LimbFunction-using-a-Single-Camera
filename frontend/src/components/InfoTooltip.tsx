// Small, accessible info-icon tooltip. Uses position:fixed with JS-calculated
// positioning to stay within viewport and avoid clipping by parent overflow.
// Works on hover and keyboard focus for both mouse and keyboard users.
import { useRef, useEffect, useState } from "react";

interface InfoTooltipProps {
  /** Short explanation shown in the popover. */
  text: string;
  /** Accessible label for the icon button itself. */
  label: string;
}

export default function InfoTooltip({ text, label }: InfoTooltipProps) {
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLSpanElement>(null);
  const [panelStyle, setPanelStyle] = useState<React.CSSProperties>({});
  const [isVisible, setIsVisible] = useState(false);

  const updatePosition = () => {
    if (!triggerRef.current || !panelRef.current || !isVisible) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const panelRect = panelRef.current.getBoundingClientRect();

    // Try positioning above, centered on trigger
    let top = triggerRect.top - panelRect.height - 10;
    let left = triggerRect.left + triggerRect.width / 2 - panelRect.width / 2;
    let arrowLeft = "50%";
    let arrowTop = "100%";

    // Check if tooltip goes off the right edge
    if (left + panelRect.width > window.innerWidth - 12) {
      left = window.innerWidth - panelRect.width - 12;
      // Adjust arrow to point at trigger
      arrowLeft = triggerRect.left + triggerRect.width / 2 - left + "px";
    }

    // Check if tooltip goes off the left edge
    if (left < 12) {
      left = 12;
      arrowLeft = triggerRect.left + triggerRect.width / 2 - 12 + "px";
    }

    // If no room above, try below
    if (top < 0) {
      top = triggerRect.bottom + 10;
      arrowTop = "-6px";
    }

    setPanelStyle({
      position: "fixed",
      top: `${top}px`,
      left: `${left}px`,
      "--arrow-left": arrowLeft,
      "--arrow-top": arrowTop,
    } as React.CSSProperties & { "--arrow-left": string; "--arrow-top": string });
  };

  useEffect(() => {
    if (isVisible) {
      // Small delay to let panel render before calculating
      const timer = setTimeout(updatePosition, 0);
      window.addEventListener("scroll", updatePosition, { passive: true });
      window.addEventListener("resize", updatePosition, { passive: true });
      return () => {
        clearTimeout(timer);
        window.removeEventListener("scroll", updatePosition);
        window.removeEventListener("resize", updatePosition);
      };
    }
  }, [isVisible]);

  return (
    <span className="info-tooltip">
      <button
        ref={triggerRef}
        type="button"
        className="info-tooltip-trigger"
        aria-label={label}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5.5M12 7.5h.01" strokeLinecap="round" />
        </svg>
      </button>
      {isVisible && (
        <span ref={panelRef} className="info-tooltip-panel" role="tooltip" style={panelStyle}>
          {text}
        </span>
      )}
    </span>
  );
}
