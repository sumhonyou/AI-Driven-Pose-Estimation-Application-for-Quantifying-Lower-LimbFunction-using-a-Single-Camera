// Stylised pose-skeleton used on hero, camera and live screens.
export default function PoseFigure() {
  return (
    <svg
      className="pose"
      viewBox="0 0 300 260"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <g>
        <line className="bone lime" x1="150" y1="48" x2="150" y2="120" />
        <line className="bone" x1="150" y1="70" x2="112" y2="104" />
        <line className="bone" x1="150" y1="70" x2="188" y2="104" />
        <line className="bone" x1="112" y1="104" x2="100" y2="150" />
        <line className="bone" x1="188" y1="104" x2="200" y2="150" />
        <line className="bone lime" x1="150" y1="120" x2="124" y2="170" />
        <line className="bone lime" x1="150" y1="120" x2="176" y2="170" />
        <line className="bone lime" x1="124" y1="170" x2="116" y2="224" />
        <line className="bone lime" x1="176" y1="170" x2="184" y2="224" />
      </g>
      <g>
        {[
          [150, 40, 9],
          [150, 70, 4.5],
          [112, 104, 4.5],
          [188, 104, 4.5],
          [100, 150, 4.5],
          [200, 150, 4.5],
          [150, 120, 5.5],
          [124, 170, 6.5],
          [176, 170, 6.5],
          [116, 224, 5],
          [184, 224, 5],
        ].map((c, i) => (
          <circle key={i} className="joint" cx={c[0]} cy={c[1]} r={c[2]} />
        ))}
      </g>
    </svg>
  );
}
