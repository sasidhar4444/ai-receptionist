import { useState, useCallback, useId } from 'react';
import { ReceptionistAvatar }  from '../components/ReceptionistAvatar';
import { ConversationPanel }   from '../components/ConversationPanel';
import { VoiceIndicator }      from '../components/VoiceIndicator';
import { TextFallback }        from '../components/TextFallback';
import { SystemStatusBar }     from '../components/SystemStatus';
import { api }                 from '../services/api';
import type {
  ConversationState,
  ConversationMessage,
  SystemStatus,
} from '../types/receptionist';

// ─── Helpers ──────────────────────────────────────────────────────────────
function makeId() {
  return Math.random().toString(36).slice(2, 10);
}

const INITIAL_STATUS: SystemStatus = {
  voice:    'connecting',
  backend:  'connecting',
  database: 'connecting',
};

// ─── Page ─────────────────────────────────────────────────────────────────
/**
 * Receptionist — full-screen kiosk UI for Aria Kitchen AI Receptionist.
 *
 * Layout:
 *   ┌──────────────────────────────────┐
 *   │  Aria Kitchen (header)           │
 *   │  [Avatar]                        │
 *   │  Status pill                     │
 *   │  [Conversation transcript]       │
 *   │  [Mic button]                    │
 *   │  [Text fallback - dev only]      │
 *   │  [System status bar] (footer)    │
 *   └──────────────────────────────────┘
 */
export default function Receptionist() {
  const [convState, setConvState] = useState<ConversationState>('idle');
  const [messages,  setMessages]  = useState<ConversationMessage[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>(INITIAL_STATUS);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const descId = useId();

  // ─── State label shown below avatar ──────────────────────────────────
  const STATE_SUBTITLE: Record<ConversationState, string> = {
    idle:             'How can I help you today?',
    listening:        'Listening…',
    thinking:         'Let me check that for you…',
    speaking:         'One moment…',
    error:            'I\'m having trouble connecting right now.',
    staff_assistance: 'A team member will be with you shortly.',
  };

  // ─── Add a message to transcript ──────────────────────────────────────
  const addMessage = useCallback((role: ConversationMessage['role'], text: string) => {
    setMessages(prev => [
      ...prev,
      { id: makeId(), role, text, timestamp: new Date() },
    ]);
  }, []);

  // ─── Mic toggle (placeholder — real voice wired in voice integration step) ──
  const handleMicClick = useCallback(async () => {
    if (convState === 'listening') {
      setConvState('idle');
      return;
    }

    // Ensure a session exists
    if (!sessionId) {
      try {
        const { session_id } = await api.createSession();
        setSessionId(session_id);
        setSystemStatus({ voice: 'healthy', backend: 'healthy', database: 'healthy' });
      } catch {
        setConvState('error');
        setSystemStatus(s => ({ ...s, backend: 'error' }));
        return;
      }
    }

    setConvState('listening');
  }, [convState, sessionId]);

  // ─── Text fallback send ────────────────────────────────────────────────
  const handleTextSend = useCallback(async (text: string) => {
    if (!text.trim()) return;

    addMessage('customer', text);
    setConvState('thinking');

    let sid = sessionId;
    if (!sid) {
      try {
        const { session_id } = await api.createSession();
        setSessionId(session_id);
        sid = session_id;
        setSystemStatus({ voice: 'healthy', backend: 'healthy', database: 'healthy' });
      } catch {
        setConvState('error');
        addMessage('system', 'Unable to reach the restaurant system. Please ask a staff member.');
        setSystemStatus(s => ({ ...s, backend: 'error' }));
        return;
      }
    }

    try {
      const { response } = await api.sendMessage(sid, text);
      addMessage('receptionist', response);
      setConvState('idle');
    } catch {
      addMessage('system', 'I\'m having trouble reaching the system right now.');
      setConvState('error');
    }
  }, [sessionId, addMessage]);

  const showDevFallback = import.meta.env.DEV || convState === 'error';

  return (
    <main
      className="relative flex h-full w-full flex-col items-center justify-between overflow-hidden"
      style={{ background: 'var(--color-bg)', padding: '2rem 1.5rem 1.5rem' }}
      aria-label="Aria Kitchen AI Receptionist"
      aria-describedby={descId}
    >
      {/* ── Ambient background gradient ── */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          background:
            'radial-gradient(ellipse 70% 50% at 50% -10%, rgba(124,109,250,0.18) 0%, transparent 70%)',
        }}
      />

      {/* ─────────────── HEADER ─────────────── */}
      <header className="relative z-10 flex flex-col items-center gap-1 text-center">
        <div
          className="mb-1 px-4 py-1 rounded-full text-xs font-semibold tracking-[0.25em] uppercase"
          style={{
            background: 'rgba(124,109,250,0.15)',
            border:     '1px solid rgba(124,109,250,0.3)',
            color:      'var(--color-accent)',
          }}
        >
          AI Receptionist
        </div>
        <h1
          className="text-3xl font-bold tracking-tight"
          style={{ color: 'var(--color-text)' }}
        >
          Aria Kitchen
        </h1>
        <p
          id={descId}
          className="text-sm"
          style={{ color: 'var(--color-text-muted)' }}
        >
          Fine dining in the heart of the city
        </p>
      </header>

      {/* ─────────────── AVATAR ─────────────── */}
      <section
        aria-label="Receptionist status"
        className="relative z-10 flex flex-col items-center gap-4"
      >
        <ReceptionistAvatar state={convState} />

        {/* Subtitle beneath avatar */}
        <p
          key={convState}            /* re-animate on state change */
          className="max-w-xs text-center text-base font-light animate-fade-in-up"
          style={{ color: 'var(--color-text-muted)' }}
          aria-live="polite"
        >
          {STATE_SUBTITLE[convState]}
        </p>
      </section>

      {/* ─────────────── CONVERSATION ─────────────── */}
      <section
        className="relative z-10 w-full"
        style={{ maxWidth: 480 }}
        aria-label="Conversation"
      >
        <ConversationPanel messages={messages} />
      </section>

      {/* ─────────────── MIC + TEXT INPUT ─────────────── */}
      <section
        className="relative z-10 flex w-full flex-col items-center gap-4"
        style={{ maxWidth: 480 }}
        aria-label="Voice and text input"
      >
        <VoiceIndicator
          state={convState}
          onMicClick={handleMicClick}
        />

        {showDevFallback && (
          <div className="w-full">
            <TextFallback
              onSend={handleTextSend}
              disabled={convState === 'thinking' || convState === 'speaking'}
            />
          </div>
        )}
      </section>

      {/* ─────────────── FOOTER ─────────────── */}
      <footer className="relative z-10">
        <SystemStatusBar status={systemStatus} />
      </footer>
    </main>
  );
}
