import type { AvatarState } from '../types/receptionist';

// ─── Avatar configuration by state ───────────────────────────────────────
const STATE_CONFIG: Record<AvatarState, { label: string; color: string; glowColor: string }> = {
  idle:             { label: 'Ready',            color: '#7c6dfa', glowColor: 'rgba(124,109,250,0.3)' },
  listening:        { label: 'Listening...',     color: '#34d399', glowColor: 'rgba(52,211,153,0.35)' },
  thinking:         { label: 'Checking...',      color: '#fbbf24', glowColor: 'rgba(251,191,36,0.3)'  },
  speaking:         { label: 'Speaking',         color: '#818cf8', glowColor: 'rgba(129,140,248,0.35)'},
  error:            { label: 'Unavailable',      color: '#f87171', glowColor: 'rgba(248,113,113,0.3)' },
  staff_assistance: { label: 'Calling Staff...', color: '#fb923c', glowColor: 'rgba(251,146,60,0.3)'  },
};

interface ReceptionistAvatarProps {
  state: AvatarState;
  /** Swap this child to replace with Unreal/MetaHuman/3D avatar later */
  children?: React.ReactNode;
}

/**
 * ReceptionistAvatar — abstracted visual state container.
 *
 * The inner visual is intentionally decoupled so it can be swapped
 * from this placeholder to a 3D avatar (Unreal Engine / MetaHuman)
 * without changing any parent component or backend architecture.
 */
export function ReceptionistAvatar({ state, children }: ReceptionistAvatarProps) {
  const cfg = STATE_CONFIG[state];

  return (
    <div
      className="relative flex flex-col items-center gap-5"
      role="img"
      aria-label={`AI Receptionist — ${cfg.label}`}
    >
      {/* ── Outer glow ring ── */}
      <div
        className="relative flex items-center justify-center"
        style={{ width: 200, height: 200 }}
      >
        {/* Animated pulse ring */}
        {(state === 'listening' || state === 'speaking') && (
          <span
            className="absolute inset-0 rounded-full"
            style={{
              border: `2px solid ${cfg.color}`,
              animation: 'pulse-ring 1.8s cubic-bezier(0.4,0,0.6,1) infinite',
            }}
            aria-hidden="true"
          />
        )}

        {/* Glow backdrop */}
        <div
          className="absolute inset-0 rounded-full blur-2xl opacity-40 transition-all duration-700"
          style={{ background: cfg.glowColor }}
          aria-hidden="true"
        />

        {/* Avatar body — replace this div's children with 3D avatar later */}
        <div
          className="relative z-10 flex items-center justify-center rounded-full transition-all duration-700"
          style={{
            width: 160,
            height: 160,
            background: `radial-gradient(circle at 35% 35%, ${cfg.color}22, #111118 70%)`,
            border: `1.5px solid ${cfg.color}55`,
            boxShadow: `0 0 48px ${cfg.glowColor}, inset 0 0 24px ${cfg.color}11`,
            animation: state === 'idle' ? 'breath 4s ease-in-out infinite' : undefined,
          }}
        >
          {children ?? <AvatarSilhouette state={state} color={cfg.color} />}
        </div>
      </div>

      {/* ── State label ── */}
      <span
        className="text-sm font-medium tracking-widest uppercase transition-all duration-300"
        style={{ color: cfg.color, letterSpacing: '0.2em' }}
      >
        {cfg.label}
      </span>
    </div>
  );
}

// ─── Default SVG silhouette placeholder ──────────────────────────────────
function AvatarSilhouette({ state, color }: { state: AvatarState; color: string }) {
  if (state === 'listening') return <WaveVisualizer color={color} />;
  if (state === 'speaking')  return <WaveVisualizer color={color} fast />;
  if (state === 'thinking')  return <ThinkingDots color={color} />;
  if (state === 'error')     return <ErrorIcon color={color} />;
  if (state === 'staff_assistance') return <StaffIcon color={color} />;

  // idle — elegant receptionist silhouette
  return (
    <svg viewBox="0 0 80 80" width={72} height={72} aria-hidden="true" fill="none">
      {/* Head */}
      <circle cx="40" cy="26" r="14" fill={color} fillOpacity={0.85} />
      {/* Shoulders / body */}
      <path
        d="M14 72 Q14 50 40 48 Q66 50 66 72"
        fill={color}
        fillOpacity={0.6}
      />
    </svg>
  );
}

// ─── Sub-visuals ──────────────────────────────────────────────────────────
function WaveVisualizer({ color, fast = false }: { color: string; fast?: boolean }) {
  const bars = [0.4, 0.7, 1, 0.7, 0.5, 0.8, 0.4];
  return (
    <div className="flex items-center gap-[4px]" aria-hidden="true">
      {bars.map((h, i) => (
        <div
          key={i}
          style={{
            width: 4,
            height: 32,
            borderRadius: 99,
            background: color,
            transformOrigin: 'center',
            animation: `wave-bar ${fast ? 0.5 : 0.9}s ease-in-out ${i * 0.1}s infinite`,
            transform: `scaleY(${h})`,
          }}
        />
      ))}
    </div>
  );
}

function ThinkingDots({ color }: { color: string }) {
  return (
    <div className="flex items-center gap-2" aria-hidden="true">
      {[0, 1, 2].map(i => (
        <div
          key={i}
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: color,
            animation: `blink-dot 1.4s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

function ErrorIcon({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 48 48" width={48} height={48} aria-hidden="true" fill="none">
      <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2.5" fillOpacity="0" />
      <line x1="24" y1="14" x2="24" y2="28" stroke={color} strokeWidth="3" strokeLinecap="round" />
      <circle cx="24" cy="35" r="2" fill={color} />
    </svg>
  );
}

function StaffIcon({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 48 48" width={48} height={48} aria-hidden="true" fill="none">
      <circle cx="24" cy="18" r="8" fill={color} fillOpacity={0.8} />
      <path d="M8 42 Q8 30 24 28 Q40 30 40 42" fill={color} fillOpacity={0.5} />
    </svg>
  );
}
