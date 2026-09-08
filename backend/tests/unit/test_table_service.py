"""
Unit tests for table_service.py.
Validates:
- Party size matching
- Zone filtering
- Smallest suitable table selection
- Error recovery when database fails
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.db.models import RestaurantTable, TableStatus
from app.services import table_service


@pytest.mark.asyncio
async def test_find_available_table_exact_match():
    """Should find smallest table with capacity >= party_size."""
    mock_db = AsyncMock()
    mock_table = RestaurantTable(
        id=2,
        restaurant_id=1,
        table_number=2,
        capacity=2,
        zone="indoor",
        status=TableStatus.AVAILABLE,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_table
    mock_db.execute.return_value = mock_result

    result = await table_service.find_available_table(
        db=mock_db,
        restaurant_id=1,
        party_size=2,
        zone="indoor",
    )

    assert result["success"] is True
    assert result["available"] is True
    assert result["table_number"] == 2
    assert result["capacity"] == 2
    assert result["zone"] == "indoor"


@pytest.mark.asyncio
async def test_find_available_table_none_available():
    """Should return available=False when no table fits or is free."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    result = await table_service.find_available_table(
        db=mock_db,
        restaurant_id=1,
        party_size=12,
        zone="outdoor",
    )

    assert result["success"] is True
    assert result["available"] is False


@pytest.mark.asyncio
async def test_find_available_table_db_failure():
    """Should return success=False and error_code on DB exception."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("DB Connection Timeout")

    result = await table_service.find_available_table(
        db=mock_db,
        restaurant_id=1,
        party_size=4,
    )

    assert result["success"] is False
    assert result["error_code"] == "DATABASE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_get_all_tables():
    """Should return list of all tables with their live statuses."""
    mock_db = AsyncMock()
    mock_tables = [
        RestaurantTable(id=1, table_number=1, capacity=2, zone="indoor", status=TableStatus.OCCUPIED),
        RestaurantTable(id=2, table_number=2, capacity=4, zone="outdoor", status=TableStatus.AVAILABLE),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_tables
    mock_db.execute.return_value = mock_result

    tables = await table_service.get_all_tables(db=mock_db, restaurant_id=1)
    assert len(tables) == 2
    assert tables[0]["table_number"] == 1
    assert tables[0]["status"] == TableStatus.OCCUPIED
    assert tables[1]["table_number"] == 2
    assert tables[1]["status"] == TableStatus.AVAILABLE
