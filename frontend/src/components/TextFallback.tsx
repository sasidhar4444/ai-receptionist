import { useState, type FormEvent } from 'react';

interface TextFallbackProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

/**
 * TextFallback — developer text-input that feeds the SAME agent pipeline as voice.
 * Visible only in dev mode (import.meta.env.DEV) or when voice is unavailable.
 */
export function TextFallback({ onSend, disabled }: TextFallbackProps) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-2 items-center"
      aria-label="Text input fallback"
    >
      <label htmlFor="text-input" className="sr-only">
        Type your message (development fallback)
      </label>
      <input
        id="text-input"
        type="text"
        value={value}
        onChange={e => setValue(e.target.value)}
        disabled={disabled}
        placeholder="Type a message (dev fallback)…"
        autoComplete="off"
        className="flex-1 rounded-xl px-4 py-2.5 text-sm transition-all duration-200 focus:outline-none"
        style={{
          background:    'rgba(255,255,255,0.06)',
          border:        '1px solid rgba(255,255,255,0.1)',
          color:         'var(--color-text)',
          caretColor:    'var(--color-accent)',
        }}
        onFocus={e => {
          e.currentTarget.style.borderColor = 'rgba(124,109,250,0.5)';
          e.currentTarget.style.boxShadow   = '0 0 0 3px rgba(124,109,250,0.15)';
        }}
        onBlur={e => {
          e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
          e.currentTarget.style.boxShadow   = 'none';
        }}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        className="flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200 focus-visible:outline focus-visible:outline-2"
        style={{
          background:  value.trim() ? 'var(--color-accent)' : 'rgba(255,255,255,0.06)',
          color:       value.trim() ? '#fff' : 'var(--color-text-muted)',
          border:      '1px solid transparent',
          cursor:      disabled || !value.trim() ? 'not-allowed' : 'pointer',
          minWidth:    72,
        }}
      >
        Send
      </button>
    </form>
  );
}
