/**
 * api.ts — REST client for the FastAPI backend.
 * All calls go through /api/* (proxied to localhost:8000 in dev).
 * The frontend never queries PostgreSQL directly.
 */

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

// ─── Health ───────────────────────────────────────────────────────────────
export const api = {
  health: () => request<{ status: string }>('/health'),

  // ─── Restaurant ────────────────────────────────────────────────────────
  getRestaurant: () =>
    request<{ id: number; name: string; description: string }>('/restaurant'),

  // ─── Tables ────────────────────────────────────────────────────────────
  getTables: () =>
    request<{ tables: Array<{ id: number; table_number: number; capacity: number; zone: string; status: string }> }>('/tables'),

  // ─── Conversation ──────────────────────────────────────────────────────
  createSession: () =>
    request<{ session_id: string }>('/conversation/session', { method: 'POST' }),

  /** Text fallback — same LLM + tool pipeline as voice */
  sendMessage: (session_id: string, text: string) =>
    request<{ response: string }>('/conversation/message', {
      method: 'POST',
      body: JSON.stringify({ session_id, text }),
    }),
};
