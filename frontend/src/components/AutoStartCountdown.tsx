// Large, glanceable countdown shown once Camera Setup detects a stable full body.
// The ring fills smoothly with progress; the number pops with a fresh animation on
// every tick change (keyed remount) so users standing far from the screen get clear,
// dynamic feedback that the session is about to start.
const RADIUS = 26;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

interface AutoStartCountdownProps {
  /** 0–1 progress toward auto-start. */
  progress: number;
  /** Whole seconds remaining, for the big number in the ring. */
  secondsLeft: number;
  /** Supporting label text next to the ring. */
  label: string;
}

export default function AutoStartCountdown({
  progress,
  secondsLeft,
  label,
}: AutoStartCountdownProps) {
  const offset = CIRCUMFERENCE * (1 - Math.min(1, Math.max(0, progress)));

  return (
    <div className="auto-start-countdown" role="status" aria-live="polite">
      <div className="auto-start-ring-wrap">
        <svg className="auto-start-ring" viewBox="0 0 72 72">
          <circle className="auto-start-ring-track" cx="36" cy="36" r={RADIUS} />
          <circle
            className="auto-start-ring-fill"
            cx="36"
            cy="36"
            r={RADIUS}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
          />
        </svg>
        {/* key={secondsLeft} forces a remount on every tick, replaying the pop animation */}
        <span key={secondsLeft} className="auto-start-number">
          {secondsLeft}
        </span>
      </div>
      <span className="auto-start-label">{label}</span>
    </div>
  );
}
