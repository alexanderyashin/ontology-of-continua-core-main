import type { Concept } from "../types";

export function MiniVisual({ concept, intensity = 0.7 }: { concept: Concept; intensity?: number }) {
  const radius = 38 + intensity * 18;
  const gap = 26 - intensity * 10;
  return (
    <svg viewBox="0 0 180 130" className="mini-visual" role="img" aria-label={`${concept.title} diagram`}>
      <defs>
        <radialGradient id={`glow-${concept.id}`} cx="50%" cy="50%" r="70%">
          <stop offset="0%" stopColor={concept.color} stopOpacity="0.26" />
          <stop offset="100%" stopColor={concept.color} stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect x="0" y="0" width="180" height="130" fill={`url(#glow-${concept.id})`} />
      <circle cx="90" cy="65" r={radius} fill="none" stroke={concept.color} strokeWidth="3" />
      <circle cx="90" cy="65" r={radius - gap} fill="rgba(255,255,255,0.72)" stroke="#dbe4ee" />
      <path d={`M34 82 C62 ${26 + gap}, 91 ${105 - gap}, 146 43`} fill="none" stroke={concept.color} strokeWidth="4" strokeLinecap="round" />
      <circle cx="52" cy="79" r="8" fill={concept.color} />
      <circle cx="91" cy="65" r="8" fill={concept.color} />
      <circle cx="128" cy="47" r="8" fill={concept.color} />
    </svg>
  );
}
