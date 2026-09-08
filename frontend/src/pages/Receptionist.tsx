import { useState, useCallback, useId, useEffect, useRef } from 'react';
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
  voice:    'healthy',
  backend:  'healthy',
  database: 'healthy',
};

// Cross-browser SpeechRecognition
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const SpeechRecognitionAPI = typeof window !== 'undefined'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ? ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)
  : null;

// ─── Page ─────────────────────────────────────────────────────────────────
/**
 * Receptionist — full-screen kiosk UI for Aria Kitchen AI Receptionist.
 * Features real Web Speech API input + SpeechSynthesis voice response.
 */
export default function Receptionist() {
  const [convState, setConvState] = useState<ConversationState>('idle');
  const [messages,  setMessages]  = useState<ConversationMessage[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>(INITIAL_STATUS);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [interimTranscript, setInterimTranscript] = useState<string>('');

  const descId = useId();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  const finalTextRef   = useRef<string>('');

  // ─── State label shown below avatar ──────────────────────────────────
  const STATE_SUBTITLE: Record<ConversationState, string> = {
    idle:             'How can I help you today?',
    listening:        'Listening… speak naturally',
    thinking:         'Let me check that for you…',
    speaking:         'Speaking…',
    error:            'I\'m having trouble connecting right now.',
    staff_assistance: 'A team member will be with you shortly.',
  };

  // ─── Initial Health Check ─────────────────────────────────────────────
  useEffect(() => {
    api.health()
      .then(res => {
        setSystemStatus({
          backend: res.status === 'ok' ? 'healthy' : 'degraded',
          database: 'healthy',
          voice: SpeechRecognitionAPI ? 'healthy' : 'degraded',
        });
      })
      .catch(() => {
        setSystemStatus({
          backend: 'error',
          database: 'error',
          voice: 'error',
        });
      });
  }, []);

  // ─── Add a message to transcript ──────────────────────────────────────
  const addMessage = useCallback((role: ConversationMessage['role'], text: string) => {
    setMessages(prev => [
      ...prev,
      { id: makeId(), role, text, timestamp: new Date() },
    ]);
  }, []);

  // ─── Speak Receptionist Answer (TTS) ──────────────────────────────────
  const speakResponse = useCallback((text: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setConvState('idle');
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(v =>
      v.lang.startsWith('en') && (
        v.name.includes('Natural') ||
        v.name.includes('Neural') ||
        v.name.includes('Google') ||
        v.name.includes('Samantha') ||
        v.name.includes('Zira')
      )
    ) || voices.find(v => v.lang.startsWith('en'));

    if (naturalVoice) utterance.voice = naturalVoice;

    utterance.onstart = () => setConvState('speaking');
    utterance.onend   = () => setConvState('idle');
    utterance.onerror = () => setConvState('idle');

    window.speechSynthesis.speak(utterance);
  }, []);

  // ─── Send Text (Both Voice & Text Fallback) ───────────────────────────
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
        setSystemStatus(s => ({ ...s, backend: 'healthy' }));
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
      speakResponse(response);
    } catch {
      addMessage('system', 'I\'m having trouble reaching the system right now.');
      setConvState('error');
    }
  }, [sessionId, addMessage, speakResponse]);

  // ─── Mic Toggle & Real Speech Recognition ─────────────────────────────
  const handleMicClick = useCallback(async () => {
    // If speaking, clicking mic interrupts (barge-in)
    if (convState === 'speaking') {
      window.speechSynthesis?.cancel();
      setConvState('idle');
      return;
    }

    // If already listening, stop
    if (convState === 'listening') {
      recognitionRef.current?.stop();
      setConvState('idle');
      setInterimTranscript('');
      return;
    }

    if (!SpeechRecognitionAPI) {
      addMessage('system', 'Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari, or type below.');
      return;
    }

    // Ensure session exists
    if (!sessionId) {
      try {
        const { session_id } = await api.createSession();
        setSessionId(session_id);
        setSystemStatus(s => ({ ...s, backend: 'healthy' }));
      } catch {
        setConvState('error');
        setSystemStatus(s => ({ ...s, backend: 'error' }));
        return;
      }
    }

    try {
      const recognition = new SpeechRecognitionAPI();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      finalTextRef.current = '';

      recognition.onstart = () => {
        setConvState('listening');
        setInterimTranscript('');
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            final += item[0].transcript;
          } else {
            interim += item[0].transcript;
          }
        }
        if (interim) {
          setInterimTranscript(interim);
        }
        if (final) {
          finalTextRef.current = final;
          setInterimTranscript(final);
        }
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onerror = (event: any) => {
        console.warn('Speech recognition event:', event.error);
        if (event.error === 'not-allowed' || event.error === 'permission-denied') {
          addMessage('system', 'Microphone permission was denied. Please allow microphone access in your browser address bar.');
          setConvState('error');
        } else if (event.error === 'no-speech') {
          setConvState('idle');
        } else {
          setConvState('idle');
        }
        setInterimTranscript('');
      };

      recognition.onend = () => {
        const text = finalTextRef.current?.trim();
        finalTextRef.current = '';
        setInterimTranscript('');

        if (text) {
          handleTextSend(text);
        } else {
          setConvState('idle');
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setConvState('idle');
    }
  }, [convState, sessionId, addMessage, handleTextSend]);

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
          key={convState}
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
        <ConversationPanel
          messages={messages}
          interimTranscript={interimTranscript}
        />
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
