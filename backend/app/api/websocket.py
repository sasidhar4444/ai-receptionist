"""WebSocket endpoint for real-time voice and conversation session."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config.settings import settings
from app.config.logging import logger
from app.services.voice_service import VoiceSessionBridge

router = APIRouter()


@router.websocket("/ws/receptionist/{session_id}")
async def receptionist_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket session bridge for real-time voice and audio streaming.
    Streams customer voice/events to OpenAI Realtime API and handles tool calling.
    Falls back gracefully to text/chat mode if Realtime API is offline.
    """
    await websocket.accept()
    logger.info("client_websocket_connected", session_id=session_id)

    bridge = VoiceSessionBridge(
        session_id=session_id,
        client_ws=websocket,
        restaurant_id=settings.restaurant_id,
    )

    try:
        await bridge.start()
    except WebSocketDisconnect:
        logger.info("client_websocket_disconnected", session_id=session_id)
    except Exception as exc:
        logger.error("client_websocket_error", session_id=session_id, error=str(exc))
    finally:
        await bridge.close()
