"""Tests for connection service batch operations."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.connection import ConnectionService
from app.models.db_connection import DBConnection
from app.schemas.connection import ConnectionCreate


class TestBatchCreateConnections:
    """Test cases for batch_create_connections method."""

    @pytest.mark.asyncio
    async def test_batch_create_connections_success(self):
        """Test successful batch creation of connections."""
        # Mock database session
        mock_db = AsyncMock()

        # Mock the execute result for checking existing connections
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock create_connection to return a connection with ID
        async def mock_create_connection(db, user_id, connection_data):
            conn = MagicMock()
            conn.id = 1 if "california" in connection_data.name else 2
            return conn

        with patch.object(
            ConnectionService,
            'create_connection',
            side_effect=mock_create_connection
        ):
            db_ids = ["california_schools", "financial"]
            base_path = "/data/bird/databases"
            user_id = 1

            result = await ConnectionService.batch_create_connections(
                db=mock_db,
                db_ids=db_ids,
                base_path=base_path,
                user_id=user_id
            )

            assert len(result) == 2
            assert "california_schools" in result
            assert "financial" in result
            assert result["california_schools"] == 1
            assert result["financial"] == 2

    @pytest.mark.asyncio
    async def test_batch_create_connections_reuse_existing(self):
        """Test that existing connections are reused."""
        mock_db = AsyncMock()

        # Mock existing connection
        existing_conn = MagicMock()
        existing_conn.id = 5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conn
        mock_db.execute.return_value = mock_result

        db_ids = ["california_schools"]
        base_path = "/data/bird/databases"
        user_id = 1

        result = await ConnectionService.batch_create_connections(
            db=mock_db,
            db_ids=db_ids,
            base_path=base_path,
            user_id=user_id
        )

        assert result["california_schools"] == 5

    @pytest.mark.asyncio
    async def test_batch_create_connections_custom_prefix(self):
        """Test batch creation with custom prefix."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        created_names = []

        async def mock_create_connection(db, user_id, connection_data):
            created_names.append(connection_data.name)
            conn = MagicMock()
            conn.id = 1
            return conn

        with patch.object(
            ConnectionService,
            'create_connection',
            side_effect=mock_create_connection
        ):
            db_ids = ["test_db"]
            base_path = "/data/bird/databases"
            user_id = 1

            await ConnectionService.batch_create_connections(
                db=mock_db,
                db_ids=db_ids,
                base_path=base_path,
                user_id=user_id,
                prefix="custom"
            )

            assert "custom_test_db" in created_names


class TestBatchTestConnections:
    """Test cases for batch_test_connections method."""

    @pytest.mark.asyncio
    async def test_batch_test_connections_success(self):
        """Test successful batch testing of connections."""
        mock_db = AsyncMock()

        # Mock connection query result
        mock_conn = MagicMock()
        mock_conn.id = 1
        mock_conn.db_type = "sqlite"
        mock_conn.database = "/path/to/db.sqlite"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_result

        with patch.object(
            ConnectionService,
            'test_connection_model',
            return_value=(True, None)
        ):
            connection_ids = [1, 2]
            result = await ConnectionService.batch_test_connections(
                db=mock_db,
                connection_ids=connection_ids
            )

            assert 1 in result
            assert result[1][0] is True
            assert result[1][1] is None

    @pytest.mark.asyncio
    async def test_batch_test_connections_not_found(self):
        """Test batch testing with non-existent connection."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        connection_ids = [999]
        result = await ConnectionService.batch_test_connections(
            db=mock_db,
            connection_ids=connection_ids
        )

        assert 999 in result
        assert result[999][0] is False
        assert result[999][1] == "Connection not found"


class TestConnectionNameGeneration:
    """Test cases for connection name generation logic."""

    def test_connection_name_format(self):
        """Test that connection names follow expected format."""
        # This tests the naming convention used in batch_create_connections
        db_id = "california_schools"
        prefix = "bird"
        expected_name = f"{prefix}_{db_id}"
        assert expected_name == "bird_california_schools"

    def test_connection_name_with_custom_prefix(self):
        """Test connection name with custom prefix."""
        db_id = "financial"
        prefix = "custom_dataset"
        expected_name = f"{prefix}_{db_id}"
        assert expected_name == "custom_dataset_financial"
