// Reusable badge showing live capture quality percentage with a colour band.
import { ShieldCheck } from "./Icons";

interface CaptureQualityBadgeProps {
  /** 0–1 quality score from computeFrameQuality */
  quality: number;
  label?: string;
}

function qualityColor(q: number): string {
  if (q >= 0.75) return "var(--good)";
  if (q >= 0.5) return "var(--fair)";
  return "var(--coral)";
}

export default function CaptureQualityBadge({
  quality,
  label = "Quality",
}: CaptureQualityBadgeProps) {
  const pct = Math.round(quality * 100);
  const color = qualityColor(quality);

  return (
    <div className="q-badge" style={{ color }}>
      <ShieldCheck width={16} height={16} />
      {label} · {pct}%
    </div>
  );
}
