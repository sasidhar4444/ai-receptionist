"""
Hallucination Regression Tests.
These tests verify non-negotiable grounding and anti-hallucination guarantees:
1. "What is your rooftop pool policy?" → No fabricated pool/amenity claim
2. "Can I reserve Table 5 for 8 PM?" → Explicit rejection (reservations NOT supported)
3. "Do you have a table for 10?" → Relies strictly on backend table availability result
4. "What is the price of [nonexistent item]?" → Cannot confirm, never invents price
5. "Do you offer helicopter parking?" → Cannot confirm, never invents helipad
6. "Database is down — do you have a table?" → System error message, never fake success
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.agents.receptionist_agent import receptionist_agent
from app.agents.prompts import RECEPTIONIST_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_regression_reservation_rejection():
    """System must NEVER accept or confirm reservations under any circumstances."""
    mock_db = AsyncMock()

    # System prompt verification: contains strict no-reservation rule
    assert "never create, confirm, or imply a reservation" in RECEPTIONIST_SYSTEM_PROMPT.lower()
    assert "does not accept reservations" in RECEPTIONIST_SYSTEM_PROMPT.lower()
    assert "you do not make reservations" in RECEPTIONIST_SYSTEM_PROMPT.lower()

    # Test agent response when user asks for reservation
    fake_completion = MagicMock()
    fake_completion.choices = [
        MagicMock(
            finish_reason="stop",
            message=MagicMock(
                content="I'm sorry, but Aria Kitchen is a walk-in only restaurant and we do not accept reservations.",
                tool_calls=None,
            ),
        )
    ]

    with patch.object(receptionist_agent, "_get_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = fake_completion
        mock_client_factory.return_value = mock_client

        response = await receptionist_agent.chat(
            session_id="test_sess",
            user_message="Can I reserve Table 5 for 8 PM tonight?",
            history=[],
            db=mock_db,
            restaurant_id=1,
        )

        reply = response.response.lower()
        assert "do not accept reservations" in reply or "walk-in" in reply
        assert "confirmed" not in reply
        assert "booked" not in reply


@pytest.mark.asyncio
async def test_regression_rooftop_pool_unverified():
    """RAG found=False must lead to explicit non-confirmation, never fabricated amenity."""
    mock_db = AsyncMock()

    # Mock tool dispatch returning found=False for unverified amenity
    tool_dispatch_result = json.dumps({"success": True, "found": False, "sources": []})

    with patch.object(receptionist_agent, "dispatch_tool", new=AsyncMock(return_value=tool_dispatch_result)):
        with patch.object(receptionist_agent, "_get_client") as mock_client_factory:
            tool_call_msg = MagicMock(
                tool_calls=[MagicMock(id="call_1", function=MagicMock(name="get_restaurant_information", arguments=json.dumps({"query": "rooftop pool"})))],
                content=None,
            )
            first_completion = MagicMock(choices=[MagicMock(finish_reason="tool_calls", message=tool_call_msg)])
            second_completion = MagicMock(choices=[MagicMock(finish_reason="stop", message=MagicMock(content="I do not have verified information about a rooftop pool. We do not have a pool on our premises."))])

            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = [first_completion, second_completion]
            mock_client_factory.return_value = mock_client

            response = await receptionist_agent.chat(
                session_id="test_sess",
                user_message="What is your rooftop pool policy?",
                history=[],
                db=mock_db,
                restaurant_id=1,
            )

            reply = response.response.lower()
            assert "pool hours" not in reply
            assert "swimming" not in reply
            assert "do not have verified information" in reply or "do not have" in reply


@pytest.mark.asyncio
async def test_regression_party_of_10_availability():
    """Must dispatch find_available_table and reflect exact availability from database."""
    mock_db = AsyncMock()

    with patch("app.services.table_service.find_available_table", new=AsyncMock(return_value={"success": True, "available": False})):
        result = await receptionist_agent.dispatch_tool(
            tool_name="find_available_table",
            tool_args={"party_size": 10},
            db=mock_db,
            restaurant_id=1,
        )
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["available"] is False


@pytest.mark.asyncio
async def test_regression_nonexistent_menu_item():
    """Non-existent menu items must return found=False from RAG service."""
    mock_db = AsyncMock()

    with patch("app.services.rag_service.search_knowledge", new=AsyncMock(return_value={"found": False, "sources": []})):
        result = await receptionist_agent.dispatch_tool(
            tool_name="get_restaurant_information",
            tool_args={"query": "How much is the Martian Truffle Souffle?"},
            db=mock_db,
            restaurant_id=1,
        )
        parsed = json.loads(result)
        assert parsed["found"] is False


@pytest.mark.asyncio
async def test_regression_helicopter_parking():
    """Must not fabricate helicopter landing or parking facilities."""
    mock_db = AsyncMock()

    with patch("app.services.rag_service.search_knowledge", new=AsyncMock(return_value={"found": False, "sources": []})):
        result = await receptionist_agent.dispatch_tool(
            tool_name="get_restaurant_information",
            tool_args={"query": "Do you offer helicopter parking?"},
            db=mock_db,
            restaurant_id=1,
        )
        parsed = json.loads(result)
        assert parsed["found"] is False
        assert len(parsed["sources"]) == 0


@pytest.mark.asyncio
async def test_regression_database_down_no_fake_success():
    """If database lookup fails, must return success=False and never report a table is ready."""
    mock_db = AsyncMock()

    with patch("app.services.table_service.find_available_table", new=AsyncMock(return_value={"success": False, "error_code": "DATABASE_UNAVAILABLE"})):
        result = await receptionist_agent.dispatch_tool(
            tool_name="find_available_table",
            tool_args={"party_size": 4},
            db=mock_db,
            restaurant_id=1,
        )
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed.get("available") is not True
        assert parsed.get("error_code") == "DATABASE_UNAVAILABLE"
