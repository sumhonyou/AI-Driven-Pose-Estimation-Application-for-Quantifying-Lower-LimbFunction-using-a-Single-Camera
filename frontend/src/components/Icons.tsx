// Inline SVG icon set for PhysioFit. Stroke icons inherit currentColor.
import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;
const base = (p: P) => ({
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  ...p,
});

export const Check = (p: P) => (
  <svg {...base(p)}>
    <path d="M5 12l4 4L19 6" />
  </svg>
);
export const ArrowRight = (p: P) => (
  <svg {...base(p)} strokeWidth={2.4}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);
export const ArrowLeft = (p: P) => (
  <svg {...base(p)}>
    <path d="M19 12H5M11 18l-6-6 6-6" />
  </svg>
);
export const Sun = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </svg>
);
export const Moon = (p: P) => (
  <svg {...base(p)}>
    <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
  </svg>
);
export const Globe = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18" />
  </svg>
);
export const Play = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M10 8l6 4-6 4z" fill="currentColor" stroke="none" />
  </svg>
);
export const Activity = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 12h4l3 8 4-16 3 8h4" />
  </svg>
);
export const Camera = (p: P) => (
  <svg {...base(p)}>
    <path d="M23 7l-7 5 7 5V7z" />
    <rect x="1" y="5" width="15" height="14" rx="2" />
  </svg>
);
export const User = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21a8 8 0 0 1 16 0" />
  </svg>
);
export const Mail = (p: P) => (
  <svg {...base(p)}>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="m3 7 9 6 9-6" />
  </svg>
);
export const Lock = (p: P) => (
  <svg {...base(p)}>
    <rect x="4" y="10" width="16" height="10" rx="2" />
    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
  </svg>
);
export const Eye = (p: P) => (
  <svg {...base(p)}>
    <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);
export const EyeOff = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 3l18 18" />
    <path d="M10.6 10.6a3 3 0 0 0 4.2 4.2" />
    <path d="M9.9 5.2A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a18.6 18.6 0 0 1-3.1 4.1" />
    <path d="M6.6 6.8C3.7 8.8 2 12 2 12s3.5 7 10 7c1.2 0 2.4-.2 3.4-.6" />
  </svg>
);
export const ShieldCheck = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 2a10 10 0 1 0 10 10" />
    <path d="M22 4 12 14l-3-3" />
  </svg>
);
export const Alert = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 9v4M12 17h.01" />
    <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
  </svg>
);
export const Info = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5.5M12 7.5h.01" />
  </svg>
);
export const Chart = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 3v18h18" />
    <path d="M7 14l4-4 3 3 5-6" />
  </svg>
);
export const Clock = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v4l3 2" />
  </svg>
);
export const Plus = (p: P) => (
  <svg {...base(p)} strokeWidth={2.4}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);
export const Menu = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </svg>
);
export const Close = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);
export const Bell = (p: P) => (
  <svg {...base(p)}>
    <path d="M18 8A6 6 0 1 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.7 21a2 2 0 0 1-3.4 0" />
  </svg>
);
export const Grid = (p: P) => (
  <svg {...base(p)}>
    <rect x="3" y="3" width="7" height="9" rx="1.5" />
    <rect x="14" y="3" width="7" height="5" rx="1.5" />
    <rect x="14" y="12" width="7" height="9" rx="1.5" />
    <rect x="3" y="16" width="7" height="5" rx="1.5" />
  </svg>
);
export const CirclePlus = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v8M8 12h8" />
  </svg>
);
export const History = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
    <path d="M3 4v4h4M12 8v4l3 2" />
  </svg>
);
export const Balance = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="6" r="3" />
    <path d="M12 9v7M9 22l3-6 3 6" />
  </svg>
);
export const Stretch = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 20l6-6M14 4l6 6M9 9l6 6" />
  </svg>
);
export const Target = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="5" />
    <circle cx="12" cy="12" r="1.5" fill="currentColor" />
  </svg>
);
export const Lightbulb = (p: P) => (
  <svg {...base(p)}>
    <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A7 7 0 0 0 12 2z" />
  </svg>
);

export const Pencil = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 20h9" />
    <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
  </svg>
);

export const ChevronDown = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 9l6 6 6-6" />
  </svg>
);

export const LogoMark = (p: P) => (
  <svg viewBox="0 0 24 24" fill="none" {...p}>
    <path
      d="M5 13l3.5 3.5L19 6"
      stroke="#04160A"
      strokeWidth={2.6}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle cx="6" cy="6" r="2" fill="#04160A" />
  </svg>
);
