"""Connection API Integration Tests

Tests for connection management API endpoints, including pagination format validation.
"""
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.db_connection import DBConnection


class TestConnectionListAPI:
    """Test GET /api/v1/connections endpoint with pagination format."""

    @pytest.mark.asyncio
    async def test_list_connections_pagination_format(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test that list connections returns proper pagination format."""
        response = await client.get("/api/v1/connections", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify pagination format
        assert "list" in data, "Response should contain 'list' field"
        assert "pagination" in data, "Response should contain 'pagination' field"

        # Verify pagination structure
        pagination = data["pagination"]
        assert "total" in pagination, "Pagination should contain 'total'"
        assert "total_pages" in pagination, "Pagination should contain 'total_pages'"

        # Verify types
        assert isinstance(data["list"], list), "list should be an array"
        assert isinstance(pagination["total"], int), "total should be an integer"
        assert isinstance(pagination["total_pages"], int), "total_pages should be an integer"

    @pytest.mark.asyncio
    async def test_list_connections_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        """Test list connections returns created connections in paginated format."""
        # Create a test connection
        connection = DBConnection(
            name="Test Connection",
            db_type="sqlite",
            database="test.db",
            user_id=test_user.id,
            status="active",
        )
        db_session.add(connection)
        await db_session.commit()

        response = await client.get("/api/v1/connections", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify pagination values
        assert data["pagination"]["total"] == 1
        assert data["pagination"]["total_pages"] == 1
        assert len(data["list"]) == 1

        # Verify connection data
        conn_data = data["list"][0]
        assert conn_data["name"] == "Test Connection"
        assert conn_data["db_type"] == "sqlite"
        assert conn_data["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_list_connections_empty(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test list connections returns empty list with zero pagination."""
        response = await client.get("/api/v1/connections", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["list"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["total_pages"] == 1  # Still 1 page even if empty

    @pytest.mark.asyncio
    async def test_list_connections_unauthorized(self, client: AsyncClient):
        """Test list connections without authentication returns 401."""
        response = await client.get("/api/v1/connections")

        assert response.status_code == 401


class TestConnectionCreateAPI:
    """Test POST /api/v1/connections endpoint."""

    @pytest.mark.asyncio
    async def test_create_connection_sqlite(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test creating a SQLite connection."""
        connection_data = {
            "name": "SQLite Test DB",
            "db_type": "sqlite",
            "database": "test.db",
        }

        response = await client.post(
            "/api/v1/connections",
            json=connection_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == connection_data["name"]
        assert data["db_type"] == connection_data["db_type"]
        assert data["database"] == connection_data["database"]
        assert data["user_id"] == test_user.id
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_connection_postgresql(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test creating a PostgreSQL connection."""
        connection_data = {
            "name": "PostgreSQL Test DB",
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "password": "testpass",
        }

        response = await client.post(
            "/api/v1/connections",
            json=connection_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == connection_data["name"]
        assert data["db_type"] == connection_data["db_type"]
        assert data["host"] == connection_data["host"]
        assert data["port"] == connection_data["port"]

    @pytest.mark.asyncio
    async def test_create_connection_invalid_type(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test creating connection with invalid db_type returns 422."""
        connection_data = {
            "name": "Invalid DB",
            "db_type": "oracle",  # Not supported
            "database": "test.db",
        }

        response = await client.post(
            "/api/v1/connections",
            json=connection_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_connection_missing_required_fields(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test creating PostgreSQL connection without required fields returns 422."""
        connection_data = {
            "name": "Incomplete DB",
            "db_type": "postgresql",
            # Missing host, database, username
        }

        response = await client.post(
            "/api/v1/connections",
            json=connection_data,
            headers=auth_headers,
        )

        assert response.status_code == 422


class TestConnectionUpdateAPI:
    """Test PUT /api/v1/connections/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_connection(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        """Test updating an existing connection."""
        # Create a connection first
        connection = DBConnection(
            name="Original Name",
            db_type="sqlite",
            database="test.db",
            user_id=test_user.id,
            status="active",
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)

        update_data = {
            "name": "Updated Name",
            "database": "updated.db",
        }

        response = await client.put(
            f"/api/v1/connections/{connection.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == update_data["name"]
        assert data["database"] == update_data["database"]
        assert data["db_type"] == "sqlite"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_connection_not_found(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test updating non-existent connection returns 404."""
        update_data = {"name": "New Name"}

        response = await client.put(
            "/api/v1/connections/99999",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_other_user_connection(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_data_2: dict,
        auth_headers: dict,
    ):
        """Test updating another user's connection returns 404."""
        from app.core.security import get_password_hash
        from datetime import datetime

        # Create another user
        other_user = User(
            username=test_user_data_2["username"],
            email=test_user_data_2["email"],
            password_hash=get_password_hash(test_user_data_2["password"]),
            role="user",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        # Create connection for other user
        connection = DBConnection(
            name="Other User Connection",
            db_type="sqlite",
            database="test.db",
            user_id=other_user.id,
            status="active",
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)

        # Try to update as first user
        update_data = {"name": "Hacked Name"}
        response = await client.put(
            f"/api/v1/connections/{connection.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestConnectionDeleteAPI:
    """Test DELETE /api/v1/connections/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_connection(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        """Test deleting an existing connection."""
        # Create a connection
        connection = DBConnection(
            name="To Delete",
            db_type="sqlite",
            database="test.db",
            user_id=test_user.id,
            status="active",
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)

        response = await client.delete(
            f"/api/v1/connections/{connection.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/v1/connections/{connection.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_connection_not_found(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test deleting non-existent connection returns 404."""
        response = await client.delete(
            "/api/v1/connections/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestConnectionGetAPI:
    """Test GET /api/v1/connections/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_connection(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict,
    ):
        """Test getting a specific connection."""
        connection = DBConnection(
            name="Test Connection",
            db_type="sqlite",
            database="test.db",
            user_id=test_user.id,
            status="active",
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)

        response = await client.get(
            f"/api/v1/connections/{connection.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == connection.id
        assert data["name"] == connection.name
        assert data["db_type"] == connection.db_type

    @pytest.mark.asyncio
    async def test_get_connection_not_found(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test getting non-existent connection returns 404."""
        response = await client.get(
            "/api/v1/connections/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
