// ─── Conversation State Machine ───────────────────────────────────────────
export type ConversationState =
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'error'
  | 'staff_assistance';

// ─── Avatar Visual State (maps 1:1 with ConversationState for now) ────────
export type AvatarState = ConversationState;

// ─── Conversation Message ─────────────────────────────────────────────────
export type MessageRole = 'customer' | 'receptionist' | 'system';

export interface ConversationMessage {
  id: string;
  role: MessageRole;
  text: string;
  timestamp: Date;
}

// ─── System Status ────────────────────────────────────────────────────────
export type SystemStatusLevel = 'healthy' | 'degraded' | 'error' | 'connecting';

export interface SystemStatus {
  voice: SystemStatusLevel;
  backend: SystemStatusLevel;
  database: SystemStatusLevel;
}

// ─── Session ──────────────────────────────────────────────────────────────
export interface Session {
  id: string;
  startedAt: Date;
}
