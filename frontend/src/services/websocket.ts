/**
 * websocket.ts — WebSocket client for real-time receptionist session.
 * Connects to WS /ws/receptionist/{session_id} (proxied to FastAPI in dev).
 */

export type WSEventType =
  | 'state_change'
  | 'transcript'
  | 'response'
  | 'error'
  | 'session_end';

export interface WSMessage {
  type: WSEventType;
  payload: Record<string, unknown>;
}

export type WSHandler = (msg: WSMessage) => void;

export class ReceptionistSocket {
  private socket: WebSocket | null = null;
  private handlers: WSHandler[] = [];
  private sessionId: string;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      const url = `${protocol}://${location.host}/ws/receptionist/${this.sessionId}`;

      this.socket = new WebSocket(url);

      this.socket.onopen = () => resolve();

      this.socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data as string) as WSMessage;
          this.handlers.forEach(h => h(msg));
        } catch {
          // ignore malformed frames
        }
      };

      this.socket.onerror = () => reject(new Error('WebSocket connection failed'));

      this.socket.onclose = () => {
        this.emit({ type: 'session_end', payload: {} });
      };
    });
  }

  send(data: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  onMessage(handler: WSHandler): () => void {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter(h => h !== handler);
    };
  }

  disconnect(): void {
    this.socket?.close();
    this.socket = null;
  }

  private emit(msg: WSMessage): void {
    this.handlers.forEach(h => h(msg));
  }
}
