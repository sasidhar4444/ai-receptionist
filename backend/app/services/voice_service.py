"""
Voice Service — OpenAI Realtime API integration and session bridge.

Handles:
- Bidirectional streaming between client WebSocket and OpenAI Realtime WebSocket
- Audio streaming, transcription events, turn detection, barge-in
- Function/tool calling interception, server-side dispatch against PostgreSQL
- Graceful text fallback / mock mode when Realtime API is not configured or fails
"""
import asyncio
import json
from typing import Callable, Optional
import websockets

from app.config.settings import settings
from app.config.logging import logger
from app.agents.prompts import RECEPTIONIST_SYSTEM_PROMPT
from app.agents.receptionist_agent import receptionist_agent, TOOLS
from app.db.database import AsyncSessionLocal


OPENAI_REALTIME_WS_URL = "wss://api.openai.com/v1/realtime"


class VoiceSessionBridge:
    """
    Manages an active real-time voice session between a browser client and OpenAI Realtime API.
    """

    def __init__(self, session_id: str, client_ws, restaurant_id: int = 1) -> None:
        self.session_id = session_id
        self.client_ws = client_ws
        self.restaurant_id = restaurant_id
        self.openai_ws = None
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the bridge. Connects to OpenAI Realtime if API key is provided."""
        self._running = True

        if not settings.openai_api_key:
            logger.warn("voice_service_no_api_key", session_id=self.session_id)
            await self._send_to_client({
                "type": "state_change",
                "payload": {"state": "idle", "mode": "text_fallback"},
            })
            await self._run_fallback_loop()
            return

        try:
            url = f"{OPENAI_REALTIME_WS_URL}?model={settings.realtime_model}"
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "OpenAI-Beta": "realtime=v1",
            }
            self.openai_ws = await websockets.connect(url, additional_headers=headers)
            logger.info("openai_realtime_connected", session_id=self.session_id)

            # Initialize OpenAI session configuration
            await self._init_openai_session()

            # Launch concurrent listener tasks
            t1 = asyncio.create_task(self._listen_to_client())
            t2 = asyncio.create_task(self._listen_to_openai())
            self._tasks = [t1, t2]

            await asyncio.gather(t1, t2, return_exceptions=True)

        except Exception as exc:
            logger.error("openai_realtime_connection_error", session_id=self.session_id, error=str(exc))
            await self._send_to_client({
                "type": "state_change",
                "payload": {"state": "idle", "mode": "text_fallback"},
            })
            await self._run_fallback_loop()

    async def _init_openai_session(self) -> None:
        """Configures the OpenAI Realtime session with tools and system prompt."""
        # Convert Chat Completion tool definitions to Realtime tool definitions
        realtime_tools = []
        for t in TOOLS:
            fn = t["function"]
            realtime_tools.append({
                "type": "function",
                "name": fn["name"],
                "description": fn["description"],
                "parameters": fn["parameters"],
            })

        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": RECEPTIONIST_SYSTEM_PROMPT,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                },
                "tools": realtime_tools,
                "tool_choice": "auto",
            },
        }
        await self.openai_ws.send(json.dumps(session_update))

    async def _listen_to_client(self) -> None:
        """Receives frames from client WebSocket and forwards to OpenAI."""
        try:
            while self._running:
                raw = await self.client_ws.receive_text()
                event = json.loads(raw)

                event_type = event.get("type")
                payload = event.get("payload", {})

                if event_type == "audio_chunk":
                    # Audio chunk from client (base64 pcm16)
                    base64_audio = payload.get("audio")
                    if base64_audio and self.openai_ws:
                        await self.openai_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": base64_audio,
                        }))

                elif event_type == "text_message":
                    # Text message over WebSocket
                    user_text = payload.get("text", "")
                    if self.openai_ws:
                        await self.openai_ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": user_text}],
                            },
                        }))
                        await self.openai_ws.send(json.dumps({"type": "response.create"}))
                    else:
                        await self._process_text_fallback(user_text)

                elif event_type == "cancel":
                    if self.openai_ws:
                        await self.openai_ws.send(json.dumps({"type": "response.cancel"}))

        except Exception as exc:
            logger.debug("client_listener_closed", session_id=self.session_id, reason=str(exc))
        finally:
            await self.close()

    async def _listen_to_openai(self) -> None:
        """Receives events from OpenAI Realtime and forwards or executes tools."""
        try:
            async for raw in self.openai_ws:
                event = json.loads(raw)
                event_type = event.get("type")

                # 1. State changes
                if event_type == "input_audio_buffer.speech_started":
                    await self._send_to_client({
                        "type": "state_change",
                        "payload": {"state": "listening"},
                    })

                elif event_type == "input_audio_buffer.speech_stopped":
                    await self._send_to_client({
                        "type": "state_change",
                        "payload": {"state": "thinking"},
                    })

                elif event_type == "response.audio.delta":
                    # Forward streaming audio to client
                    await self._send_to_client({
                        "type": "state_change",
                        "payload": {"state": "speaking"},
                    })
                    await self._send_to_client({
                        "type": "audio",
                        "payload": {"delta": event.get("delta")},
                    })

                # 2. Transcriptions
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    await self._send_to_client({
                        "type": "transcript",
                        "payload": {"role": "customer", "text": transcript},
                    })

                elif event_type == "response.audio_transcript.done":
                    transcript = event.get("transcript", "")
                    await self._send_to_client({
                        "type": "transcript",
                        "payload": {"role": "receptionist", "text": transcript},
                    })
                    await self._send_to_client({
                        "type": "state_change",
                        "payload": {"state": "idle"},
                    })

                # 3. Server-side Tool Calling
                elif event_type == "response.function_call_arguments.done":
                    call_id = event.get("call_id")
                    name = event.get("name")
                    arguments = json.loads(event.get("arguments", "{}"))

                    await self._send_to_client({
                        "type": "state_change",
                        "payload": {"state": "thinking", "tool": name},
                    })

                    # Execute tool via our deterministic backend services
                    async with AsyncSessionLocal() as db:
                        tool_result = await receptionist_agent.dispatch_tool(
                            tool_name=name,
                            tool_args=arguments,
                            db=db,
                            restaurant_id=self.restaurant_id,
                        )

                    # Send tool result back to OpenAI to resume generation
                    await self.openai_ws.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": tool_result,
                        },
                    }))
                    await self.openai_ws.send(json.dumps({"type": "response.create"}))

                elif event_type == "error":
                    logger.error("openai_realtime_error", event=event)
                    await self._send_to_client({
                        "type": "error",
                        "payload": {"message": event.get("error", {}).get("message", "Error in voice processing")},
                    })

        except Exception as exc:
            logger.debug("openai_listener_closed", session_id=self.session_id, reason=str(exc))
        finally:
            await self.close()

    async def _run_fallback_loop(self) -> None:
        """Loop for text/fallback mode when OpenAI Realtime WS is unavailable."""
        try:
            while self._running:
                raw = await self.client_ws.receive_text()
                event = json.loads(raw)
                event_type = event.get("type")
                payload = event.get("payload", {})

                if event_type == "text_message":
                    user_text = payload.get("text", "")
                    await self._process_text_fallback(user_text)

        except Exception as exc:
            logger.debug("fallback_loop_ended", session_id=self.session_id, reason=str(exc))
        finally:
            await self.close()

    async def _process_text_fallback(self, user_text: str) -> None:
        """Process user text through receptionist_agent and emit WS events."""
        if not user_text.strip():
            return

        await self._send_to_client({
            "type": "state_change",
            "payload": {"state": "thinking"},
        })
        await self._send_to_client({
            "type": "transcript",
            "payload": {"role": "customer", "text": user_text},
        })

        async with AsyncSessionLocal() as db:
            result = await receptionist_agent.chat(
                session_id=self.session_id,
                user_message=user_text,
                history=[],
                db=db,
                restaurant_id=self.restaurant_id,
            )

        await self._send_to_client({
            "type": "transcript",
            "payload": {"role": "receptionist", "text": result.response},
        })
        await self._send_to_client({
            "type": "response",
            "payload": {"text": result.response},
        })
        await self._send_to_client({
            "type": "state_change",
            "payload": {"state": "idle"},
        })

    async def _send_to_client(self, message: dict) -> None:
        """Helper to send JSON message to client WebSocket."""
        try:
            await self.client_ws.send_text(json.dumps(message))
        except Exception:
            pass

    async def close(self) -> None:
        """Cleans up sockets and tasks."""
        self._running = False
        for t in self._tasks:
            if not t.done():
                t.cancel()
        if self.openai_ws:
            try:
                await self.openai_ws.close()
            except Exception:
                pass
            self.openai_ws = None
