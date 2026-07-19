import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown } from "./Icons";

export type DropdownOption = { value: string; label: string };

// Generic single-select dropdown, styled to match the existing LanguageSwitcher
// popover pattern (Controls.tsx) but not exercise/language-specific -- reused
// for the exercise pickers on Progress and Session History.
export default function Dropdown({
  options,
  value,
  onChange,
  placeholder,
  ariaLabel,
}: {
  options: DropdownOption[];
  value: string | null;
  onChange: (value: string) => void;
  placeholder: string;
  ariaLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  return (
    <div className="dropdown" ref={ref}>
      <button
        type="button"
        className="ctrl dropdown-trigger"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
      >
        <span className="dropdown-trigger-label">{current?.label ?? placeholder}</span>
        <ChevronDown className="dropdown-chevron" />
      </button>
      {open && (
        <div className="dropdown-menu" role="listbox">
          {options.map((o) => (
            <button
              key={o.value}
              type="button"
              className={o.value === value ? "on" : ""}
              role="option"
              aria-selected={o.value === value}
              onClick={() => {
                onChange(o.value);
                setOpen(false);
              }}
            >
              {o.label}
              <Check className="check" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
