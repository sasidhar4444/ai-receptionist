import type { SystemStatus, SystemStatusLevel } from '../types/receptionist';

interface SystemStatusProps {
  status: SystemStatus;
}

const LEVEL_COLOR: Record<SystemStatusLevel, string> = {
  healthy:    '#34d399',
  degraded:   '#fbbf24',
  error:      '#f87171',
  connecting: '#818cf8',
};

const LEVEL_LABEL: Record<SystemStatusLevel, string> = {
  healthy:    'Online',
  degraded:   'Degraded',
  error:      'Offline',
  connecting: 'Connecting',
};

interface DotProps { level: SystemStatusLevel; label: string }

function StatusDot({ level, label }: DotProps) {
  const color = LEVEL_COLOR[level];
  const text  = LEVEL_LABEL[level];
  return (
    <div className="flex items-center gap-1.5" title={`${label}: ${text}`}>
      <span
        className="inline-block rounded-full"
        style={{
          width: 7,
          height: 7,
          background: color,
          boxShadow: `0 0 6px ${color}`,
          animation: level === 'connecting' ? 'blink-dot 1.4s ease-in-out infinite' : undefined,
        }}
        aria-hidden="true"
      />
      <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
        {label}
      </span>
    </div>
  );
}

/**
 * SystemStatus — compact status bar showing voice, backend, and DB health.
 * Never exposes internal error messages to the customer-facing screen.
 */
export function SystemStatusBar({ status }: SystemStatusProps) {
  const allHealthy = Object.values(status).every(s => s === 'healthy');

  return (
    <div
      role="status"
      aria-label="System status"
      className="flex items-center justify-center gap-5 px-4 py-2 rounded-full"
      style={{
        background: 'rgba(255,255,255,0.04)',
        border:     '1px solid rgba(255,255,255,0.07)',
        backdropFilter: 'blur(8px)',
      }}
    >
      {allHealthy ? (
        <span className="text-xs font-medium" style={{ color: '#34d399' }}>
          ● All systems operational
        </span>
      ) : (
        <>
          <StatusDot level={status.voice}    label="Voice"    />
          <StatusDot level={status.backend}  label="Backend"  />
          <StatusDot level={status.database} label="Database" />
        </>
      )}
    </div>
  );
}
