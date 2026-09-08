"""
Integration tests for FastAPI endpoints using TestClient / AsyncClient.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.db.database import get_db
from app.agents.schemas import TextMessageResponse


@pytest.fixture
def mock_db_session():
    mock = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def test_app(mock_db_session):
    # Override get_db dependency
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint(test_app):
    """GET /health should return 200 and status ok."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "aria-restaurant-receptionist"


@pytest.mark.asyncio
async def test_api_tables_endpoint(test_app):
    """GET /api/tables should return list of tables."""
    with patch("app.api.routes.tables.get_all_tables", new=AsyncMock(return_value=[
        {"id": 1, "table_number": 1, "capacity": 2, "zone": "indoor", "status": "AVAILABLE"}
    ])):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/tables")
            assert resp.status_code == 200
            data = resp.json()
            assert "tables" in data
            assert len(data["tables"]) == 1
            assert data["tables"][0]["table_number"] == 1


@pytest.mark.asyncio
async def test_create_conversation_session(test_app, mock_db_session):
    """POST /api/conversation/session should create and return a session_id."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/conversation/session")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["session_id"].startswith("sess_")
        assert data["state"] == "idle"


@pytest.mark.asyncio
async def test_conversation_text_message(test_app, mock_db_session):
    """POST /api/conversation/message should run LLM agent pipeline and return response."""
    with patch(
        "app.api.routes.conversation.receptionist_agent.chat",
        new=AsyncMock(return_value=TextMessageResponse(
            session_id="sess_123",
            response="Hello! Welcome to Aria Kitchen. How may I assist you?",
            state="idle",
        )),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/conversation/message",
                json={"session_id": "sess_123", "text": "Hello"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["session_id"] == "sess_123"
            assert "Welcome to Aria Kitchen" in data["response"]


@pytest.mark.asyncio
async def test_find_available_table_tool_endpoint(test_app):
    """POST /api/tools/find-available-table should validate input and return tool output."""
    with patch(
        "app.api.routes.tables.execute_find_available_table",
        new=AsyncMock(return_value={
            "success": True,
            "available": True,
            "table_number": 3,
            "capacity": 2,
            "zone": "outdoor",
        }),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/tools/find-available-table",
                json={"party_size": 2, "zone": "outdoor"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["available"] is True
            assert data["table_number"] == 3
