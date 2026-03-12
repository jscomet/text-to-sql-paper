"""Authentication API Integration Tests

Tests for authentication endpoints: register, login, and user info.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestAuthRegisterAPI:
    """Test POST /api/v1/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        client: AsyncClient,
    ):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()

        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "password" not in data  # Password should not be in response
        assert data["role"] == "user"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test registration with duplicate username returns 400."""
        user_data = {
            "username": test_user.username,  # Already exists
            "email": "different@example.com",
            "password": "password123",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test registration with duplicate email returns 400."""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,  # Already exists
            "password": "password123",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_email(
        self,
        client: AsyncClient,
    ):
        """Test registration with invalid email returns 422."""
        user_data = {
            "username": "testuser",
            "email": "not-an-email",
            "password": "password123",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(
        self,
        client: AsyncClient,
    ):
        """Test registration with short password returns 422."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",  # Too short
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(
        self,
        client: AsyncClient,
    ):
        """Test registration with missing fields returns 422."""
        user_data = {
            "username": "testuser",
            # Missing email and password
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422


class TestAuthLoginAPI:
    """Test POST /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_user: User,
    ):
        """Test successful login."""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"]
        assert data["user"]["email"] == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_user: User,
    ):
        """Test login with wrong password returns 401."""
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword",
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self,
        client: AsyncClient,
    ):
        """Test login with non-existent user returns 401."""
        login_data = {
            "username": "nonexistent",
            "password": "password123",
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_data: dict,
    ):
        """Test login with inactive user returns 401."""
        from app.core.security import get_password_hash
        from datetime import datetime

        # Create inactive user
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            role="user",
            status="inactive",  # Inactive
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(inactive_user)
        await db_session.commit()

        login_data = {
            "username": "inactiveuser",
            "password": "password123",
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401


class TestAuthMeAPI:
    """Test GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_user: User,
        auth_headers: dict,
    ):
        """Test getting current user info."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(
        self,
        client: AsyncClient,
    ):
        """Test getting current user without token returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        client: AsyncClient,
        invalid_auth_headers: dict,
    ):
        """Test getting current user with invalid token returns 401."""
        response = await client.get("/api/v1/auth/me", headers=invalid_auth_headers)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(
        self,
        client: AsyncClient,
        expired_token: str,
    ):
        """Test getting current user with expired token returns 401."""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401


class TestAuthLogoutAPI:
    """Test POST /api/v1/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test successful logout."""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Successfully logged out"

    @pytest.mark.asyncio
    async def test_logout_no_token(
        self,
        client: AsyncClient,
    ):
        """Test logout without token returns 401."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
