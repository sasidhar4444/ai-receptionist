import { useEffect, useRef } from 'react';
import type { ConversationMessage } from '../types/receptionist';

interface ConversationPanelProps {
  messages: ConversationMessage[];
}

const ROLE_LABEL: Record<ConversationMessage['role'], string> = {
  customer:     'You',
  receptionist: 'Aria',
  system:       'System',
};

const ROLE_STYLE: Record<ConversationMessage['role'], string> = {
  customer:     'text-right',
  receptionist: 'text-left',
  system:       'text-center',
};

const BUBBLE_STYLE: Record<ConversationMessage['role'], React.CSSProperties> = {
  customer: {
    background:   'rgba(124,109,250,0.18)',
    border:       '1px solid rgba(124,109,250,0.3)',
    borderRadius: '1rem 1rem 0.25rem 1rem',
    marginLeft:   'auto',
    maxWidth:     '78%',
  },
  receptionist: {
    background:   'rgba(255,255,255,0.05)',
    border:       '1px solid rgba(255,255,255,0.08)',
    borderRadius: '1rem 1rem 1rem 0.25rem',
    marginRight:  'auto',
    maxWidth:     '78%',
  },
  system: {
    background:   'transparent',
    border:       'none',
    borderRadius: '0',
    margin:       '0 auto',
    maxWidth:     '90%',
  },
};

/**
 * ConversationPanel — scrollable transcript of the conversation.
 * Auto-scrolls to the latest message. Handles empty state.
 */
export function ConversationPanel({ messages }: ConversationPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <section
      aria-label="Conversation transcript"
      aria-live="polite"
      aria-atomic="false"
      className="flex flex-col gap-3 overflow-y-auto px-4 py-3"
      style={{
        height: 220,
        background:   'rgba(10,10,15,0.6)',
        border:       '1px solid rgba(255,255,255,0.07)',
        borderRadius: '1rem',
        backdropFilter: 'blur(12px)',
      }}
    >
      {messages.length === 0 ? (
        <div
          className="flex h-full items-center justify-center"
          role="status"
        >
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Start speaking to begin the conversation…
          </p>
        </div>
      ) : (
        messages.map(msg => (
          <div
            key={msg.id}
            className={`flex flex-col gap-0.5 animate-fade-in-up ${ROLE_STYLE[msg.role]}`}
          >
            {msg.role !== 'system' && (
              <span
                className="px-2 text-xs font-semibold tracking-wide uppercase"
                style={{ color: 'var(--color-text-muted)' }}
              >
                {ROLE_LABEL[msg.role]}
              </span>
            )}
            <div
              className="px-4 py-2.5 text-sm leading-relaxed"
              style={{
                ...BUBBLE_STYLE[msg.role],
                color: msg.role === 'system'
                  ? 'var(--color-text-muted)'
                  : 'var(--color-text)',
                fontSize: msg.role === 'system' ? '0.75rem' : '0.875rem',
              }}
            >
              {msg.text}
            </div>
          </div>
        ))
      )}
      <div ref={bottomRef} aria-hidden="true" />
    </section>
  );
}
