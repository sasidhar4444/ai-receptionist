import type { ConversationState } from '../types/receptionist';

interface VoiceIndicatorProps {
  state: ConversationState;
  onMicClick: () => void;
  disabled?: boolean;
}

const STATE_LABEL: Record<ConversationState, string> = {
  idle:             'Tap to speak',
  listening:        'Listening…',
  thinking:         'Let me check that for you…',
  speaking:         'Speaking…',
  error:            'Voice unavailable',
  staff_assistance: 'Staff on the way…',
};

const MIC_COLOR: Record<ConversationState, string> = {
  idle:             'var(--color-accent)',
  listening:        '#34d399',
  thinking:         '#fbbf24',
  speaking:         '#818cf8',
  error:            '#f87171',
  staff_assistance: '#fb923c',
};

/**
 * VoiceIndicator — microphone button + state label.
 * Keyboard accessible. Shows animated ring while listening.
 */
export function VoiceIndicator({ state, onMicClick, disabled }: VoiceIndicatorProps) {
  const isActive   = state === 'listening';
  const isDisabled = disabled || state === 'error' || state === 'speaking' || state === 'thinking';
  const color      = MIC_COLOR[state];

  return (
    <div className="flex flex-col items-center gap-3">
      {/* ── Mic button ── */}
      <div className="relative flex items-center justify-center">
        {/* Pulse ring while listening */}
        {isActive && (
          <>
            <span
              className="absolute rounded-full"
              style={{
                inset: -8,
                border: `2px solid ${color}`,
                animation: 'pulse-ring 1.5s ease-out infinite',
              }}
              aria-hidden="true"
            />
            <span
              className="absolute rounded-full"
              style={{
                inset: -16,
                border: `1px solid ${color}`,
                animation: 'pulse-ring 1.5s ease-out 0.4s infinite',
              }}
              aria-hidden="true"
            />
          </>
        )}

        <button
          id="mic-button"
          onClick={onMicClick}
          disabled={isDisabled}
          aria-label={isActive ? 'Stop listening' : 'Start voice input'}
          aria-pressed={isActive}
          className="relative z-10 flex items-center justify-center rounded-full transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
          style={{
            width: 64,
            height: 64,
            background: isActive
              ? `radial-gradient(circle, ${color}44, ${color}22)`
              : 'rgba(255,255,255,0.06)',
            border: `1.5px solid ${isDisabled ? 'rgba(255,255,255,0.1)' : color}`,
            boxShadow: isActive ? `0 0 24px ${color}55` : 'none',
            cursor: isDisabled ? 'not-allowed' : 'pointer',
            opacity: isDisabled ? 0.5 : 1,
            // focus ring color
            '--tw-ring-color': color,
          } as React.CSSProperties}
        >
          <MicIcon color={isDisabled ? 'rgba(255,255,255,0.3)' : color} active={isActive} />
        </button>
      </div>

      {/* ── State label ── */}
      <p
        className="text-xs font-medium tracking-wider text-center transition-all duration-300"
        style={{ color: isDisabled ? 'var(--color-text-muted)' : color }}
        aria-live="polite"
      >
        {STATE_LABEL[state]}
      </p>
    </div>
  );
}

function MicIcon({ color, active }: { color: string; active: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={26}
      height={26}
      fill="none"
      aria-hidden="true"
      style={{ transition: 'transform 0.2s', transform: active ? 'scale(1.1)' : 'scale(1)' }}
    >
      {/* Mic body */}
      <rect x="9" y="2" width="6" height="11" rx="3" fill={color} />
      {/* Mic stand */}
      <path
        d="M5 11a7 7 0 0 0 14 0"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <line x1="12" y1="18" x2="12" y2="22" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <line x1="8"  y1="22" x2="16" y2="22" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
