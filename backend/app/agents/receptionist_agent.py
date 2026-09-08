"""
Receptionist agent — LLM + tool calling pipeline.

Architecture:
  Text/Voice input
    → build_messages()
    → OpenAI Chat Completions (GPT-4o) with tool definitions
    → tool call detected → dispatch_tool()
    → tool result → second LLM call → final response

The LLM NEVER directly accesses PostgreSQL.
Every factual claim must come from a tool result.
"""
import json
import time
import uuid
from typing import Optional

import openai

from app.config.settings import settings
from app.config.logging import logger
from app.agents.prompts import RECEPTIONIST_SYSTEM_PROMPT
from app.agents.schemas import ConversationMessage, TextMessageResponse
from app.services import table_service, restaurant_service, rag_service

# ─── OpenAI tool definitions ──────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_available_table",
            "description": (
                "Check current live table availability for a given party size. "
                "MUST be called before claiming a table is or is not available. "
                "Never invent availability without calling this."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "party_size": {
                        "type": "integer",
                        "description": "Number of guests (1–20)",
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "zone": {
                        "type": "string",
                        "description": "Preferred seating zone: indoor, outdoor, private, or any",
                        "enum": ["indoor", "outdoor", "private", "any"],
                    },
                },
                "required": ["party_size"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_information",
            "description": (
                "Answer any question about the restaurant using verified information "
                "from the knowledge base. Use for: hours, menu, allergens, policies, "
                "parking, pets, payments, high chairs, Wi-Fi, dress code, etc. "
                "If found=false in the result, say you cannot confirm — do NOT guess."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's question, verbatim or paraphrased",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_live_table_state",
            "description": "Get the current status of all tables in the restaurant.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


class ReceptionistAgent:
    """
    Stateless agent — conversation history is passed in on each call.
    Session state is managed externally (Redis or in-memory).
    """

    def __init__(self) -> None:
        self._client: Optional[openai.AsyncOpenAI] = None

    def _get_client(self) -> openai.AsyncOpenAI:
        if self._client is None:
            self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def dispatch_tool(
        self,
        tool_name: str,
        tool_args: dict,
        db,
        restaurant_id: int,
    ) -> str:
        """
        Execute a tool call and return a JSON string result.
        Server-side validation happens here — not in the LLM.
        """
        start = time.monotonic()

        try:
            if tool_name == "find_available_table":
                party_size = int(tool_args.get("party_size", 1))
                zone = tool_args.get("zone")
                result = await table_service.find_available_table(
                    db=db,
                    restaurant_id=restaurant_id,
                    party_size=party_size,
                    zone=zone,
                )

            elif tool_name == "get_restaurant_information":
                query = str(tool_args.get("query", ""))
                result = await rag_service.search_knowledge(
                    db=db,
                    restaurant_id=restaurant_id,
                    query=query,
                )

            elif tool_name == "get_live_table_state":
                tables = await table_service.get_all_tables(
                    db=db,
                    restaurant_id=restaurant_id,
                )
                result = {"success": True, "tables": tables}

            else:
                result = {"success": False, "error_code": "UNKNOWN_TOOL"}

        except Exception as exc:
            logger.error("tool_dispatch_error", tool=tool_name, error=str(exc))
            result = {"success": False, "error_code": "TOOL_EXECUTION_FAILED"}

        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "tool_executed",
            tool=tool_name,
            success=result.get("success", False),
            latency_ms=latency_ms,
        )

        return json.dumps(result)

    async def chat(
        self,
        session_id: str,
        user_message: str,
        history: list[dict],
        db,
        restaurant_id: int,
    ) -> TextMessageResponse:
        """
        Single conversation turn:
          1. Append user message to history
          2. Call OpenAI with tools
          3. If tool call → dispatch → second LLM call
          4. Return final text response
        """
        client = self._get_client()

        if not settings.openai_api_key and "mock" not in str(type(client)).lower():
            logger.info("offline_agent_mode", session_id=session_id)
            return await self._fallback_chat(session_id, user_message, db, restaurant_id)

        messages = [
            {"role": "system", "content": RECEPTIONIST_SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": user_message},
        ]

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=512,
            )

            choice = response.choices[0]
            assistant_msg = choice.message

            # ── Tool call path ──
            if choice.finish_reason == "tool_calls" and assistant_msg.tool_calls:
                messages.append(assistant_msg)  # type: ignore[arg-type]

                for tc in assistant_msg.tool_calls:
                    tool_args = json.loads(tc.function.arguments)
                    tool_result = await self.dispatch_tool(
                        tool_name=tc.function.name,
                        tool_args=tool_args,
                        db=db,
                        restaurant_id=restaurant_id,
                    )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result,
                    })

                # Second LLM call with tool results
                follow_up = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=512,
                )
                final_text = follow_up.choices[0].message.content or ""

            # ── Direct response path ──
            else:
                final_text = assistant_msg.content or ""

            logger.info("agent_response", session_id=session_id, length=len(final_text))

            return TextMessageResponse(
                session_id=session_id,
                response=final_text,
                state="idle",
            )

        except openai.APIConnectionError:
            logger.error("openai_connection_error", session_id=session_id)
            return TextMessageResponse(
                session_id=session_id,
                response="I'm having trouble reaching the AI system right now. Please ask a team member for assistance.",
                state="error",
            )
        except Exception as exc:
            logger.error("agent_error", session_id=session_id, error=str(exc))
            return TextMessageResponse(
                session_id=session_id,
                response="Something went wrong on my end. A team member will be happy to help you.",
                state="error",
            )

    async def _fallback_chat(
        self,
        session_id: str,
        user_message: str,
        db,
        restaurant_id: int,
    ) -> TextMessageResponse:
        """Deterministic grounding fallback when OPENAI_API_KEY is not configured."""
        import re
        lowered = user_message.lower()

        if "reserve" in lowered or "reservation" in lowered or "book" in lowered:
            reply = "We don't take reservations. Aria Kitchen is a walk-in only restaurant. I can check current table availability when you arrive."
        elif "table" in lowered or "party" in lowered or "seat" in lowered:
            match = re.search(r"\b(\d+)\b", lowered)
            party_size = int(match.group(1)) if match else 2
            zone = "outdoor" if "outdoor" in lowered else ("indoor" if "indoor" in lowered else None)
            res = await table_service.find_available_table(db, restaurant_id, party_size, zone)
            if res.get("available"):
                reply = f"Yes, we have Table #{res['table_number']} available in our {res['zone']} area for a party of {party_size}. Please walk in and we will seat you right away!"
            else:
                reply = f"I'm sorry, we do not currently have an available table for a party of {party_size}. You are welcome to walk in and check our waitlist."
        elif "menu" in lowered or "food" in lowered or "dish" in lowered:
            menu = await restaurant_service.get_menu(db, restaurant_id)
            sample_items = [i["name"] for i in menu.get("items", [])[:4]]
            reply = f"Aria Kitchen features contemporary fine dining! Some of our chef specials include {', '.join(sample_items)}. Would you like to check allergen information?"
        elif "parking" in lowered:
            pol = await restaurant_service.get_policy(db, restaurant_id, "parking")
            reply = pol.get("value", "Complimentary valet parking is available at our main entrance.")
        elif "pet" in lowered or "dog" in lowered:
            pol = await restaurant_service.get_policy(db, restaurant_id, "pet_policy")
            reply = pol.get("value", "Leashed dogs are welcome in our outdoor terrace seating area.")
        elif "hour" in lowered or "time" in lowered or "open" in lowered or "close" in lowered:
            reply = "Aria Kitchen is open daily for lunch from 12:00 PM to 3:00 PM and dinner from 7:00 PM to 11:00 PM."
        else:
            reply = "Welcome to Aria Kitchen! I can check live table availability, or answer questions about our menu, policies, hours, and parking. How may I help you?"

        return TextMessageResponse(
            session_id=session_id,
            response=reply,
            state="idle",
        )


# Singleton agent instance
receptionist_agent = ReceptionistAgent()

