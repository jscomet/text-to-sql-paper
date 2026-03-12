"""API Regression Test Script

Direct API testing for pagination format validation.
This script starts the FastAPI app and tests endpoints directly.
"""
import asyncio
import sys
from datetime import datetime, timedelta

import httpx
from fastapi.testclient import TestClient

# Import after sys.path setup
from app.main import app
from app.core.auth import create_access_token
from app.core.security import get_password_hash
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.db_connection import DBConnection
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# Test database (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def setup_test_db():
    """Create test database and tables."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine


async def create_test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        role="user",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def create_test_connection(db_session: AsyncSession, user_id: int, name: str = "Test DB") -> DBConnection:
    """Create a test database connection."""
    connection = DBConnection(
        name=name,
        db_type="sqlite",
        database="test.db",
        user_id=user_id,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(connection)
    await db_session.commit()
    await db_session.refresh(connection)
    return connection


def get_auth_headers(user: User) -> dict:
    """Generate auth headers for user."""
    token = create_access_token(data={"sub": user.username})
    return {"Authorization": f"Bearer {token}"}


async def run_tests():
    """Run all API regression tests."""
    print("=" * 60)
    print("API Regression Tests - Starting")
    print("=" * 60)

    # Setup test database
    engine = await setup_test_db()
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    # Override get_db dependency
    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    client = TestClient(app)

    # Create test data
    async with async_session() as db:
        test_user = await create_test_user(db)
        test_conn = await create_test_connection(db, test_user.id, "Test Connection 1")
        await create_test_connection(db, test_user.id, "Test Connection 2")

    auth_headers = get_auth_headers(test_user)

    passed = 0
    failed = 0

    # Test 1: GET /connections - Pagination Format (THE KEY FIX)
    print("\n[Test 1] GET /api/v1/connections - Pagination Format")
    print("-" * 60)
    try:
        response = client.get("/api/v1/connections", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Verify pagination format
        assert "list" in data, "Missing 'list' field in response"
        assert "pagination" in data, "Missing 'pagination' field in response"

        pagination = data["pagination"]
        assert "total" in pagination, "Missing 'total' in pagination"
        assert "total_pages" in pagination, "Missing 'total_pages' in pagination"

        assert isinstance(data["list"], list), "'list' should be an array"
        assert isinstance(pagination["total"], int), "'total' should be an integer"
        assert isinstance(pagination["total_pages"], int), "'total_pages' should be an integer"

        # Verify values
        assert pagination["total"] == 2, f"Expected total=2, got {pagination['total']}"
        assert pagination["total_pages"] == 1, f"Expected total_pages=1, got {pagination['total_pages']}"
        assert len(data["list"]) == 2, f"Expected 2 items in list, got {len(data['list'])}"

        print(f"  Response: {data}")
        print("  PASSED: Pagination format is correct!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 2: GET /connections - Empty list
    print("\n[Test 2] GET /api/v1/connections - Empty List Format")
    print("-" * 60)
    try:
        # Create new user with no connections
        async with async_session() as db:
            new_user = User(
                username="emptyuser",
                email="empty@example.com",
                password_hash=get_password_hash("testpass123"),
                role="user",
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

        empty_auth = get_auth_headers(new_user)
        response = client.get("/api/v1/connections", headers=empty_auth)
        assert response.status_code == 200

        data = response.json()
        assert data["list"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["total_pages"] == 1

        print(f"  Response: {data}")
        print("  PASSED: Empty list format is correct!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 3: GET /connections - Unauthorized
    print("\n[Test 3] GET /api/v1/connections - Unauthorized")
    print("-" * 60)
    try:
        response = client.get("/api/v1/connections")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("  PASSED: Unauthorized request returns 401!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 4: POST /connections - Create
    print("\n[Test 4] POST /api/v1/connections - Create Connection")
    print("-" * 60)
    try:
        conn_data = {
            "name": "New Test DB",
            "db_type": "sqlite",
            "database": "new_test.db",
        }
        response = client.post("/api/v1/connections", json=conn_data, headers=auth_headers)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        data = response.json()
        assert data["name"] == conn_data["name"]
        assert data["db_type"] == conn_data["db_type"]
        assert data["user_id"] == test_user.id

        print(f"  Created: {data}")
        print("  PASSED: Connection created successfully!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 5: POST /connections - Invalid type
    print("\n[Test 5] POST /api/v1/connections - Invalid DB Type")
    print("-" * 60)
    try:
        conn_data = {
            "name": "Invalid DB",
            "db_type": "oracle",  # Not supported
            "database": "test.db",
        }
        response = client.post("/api/v1/connections", json=conn_data, headers=auth_headers)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("  PASSED: Invalid DB type returns 422!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 6: GET /connections/{id} - Get single connection
    print("\n[Test 6] GET /api/v1/connections/{id} - Get Connection")
    print("-" * 60)
    try:
        response = client.get(f"/api/v1/connections/{test_conn.id}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["id"] == test_conn.id
        assert data["name"] == test_conn.name

        print(f"  Connection: {data}")
        print("  PASSED: Connection retrieved successfully!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 7: PUT /connections/{id} - Update
    print("\n[Test 7] PUT /api/v1/connections/{id} - Update Connection")
    print("-" * 60)
    try:
        update_data = {"name": "Updated Name"}
        response = client.put(f"/api/v1/connections/{test_conn.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["name"] == update_data["name"]

        print(f"  Updated: {data}")
        print("  PASSED: Connection updated successfully!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 8: DELETE /connections/{id} - Delete
    print("\n[Test 8] DELETE /api/v1/connections/{id} - Delete Connection")
    print("-" * 60)
    try:
        # Create a connection to delete
        async with async_session() as db:
            conn_to_delete = await create_test_connection(db, test_user.id, "To Delete")

        response = client.delete(f"/api/v1/connections/{conn_to_delete.id}", headers=auth_headers)
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"

        # Verify it's gone
        get_response = client.get(f"/api/v1/connections/{conn_to_delete.id}", headers=auth_headers)
        assert get_response.status_code == 404

        print("  PASSED: Connection deleted successfully!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 9: POST /auth/register
    print("\n[Test 9] POST /api/v1/auth/register - User Registration")
    print("-" * 60)
    try:
        user_data = {
            "username": "newreguser",
            "email": "newreg@example.com",
            "password": "password123",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data

        print(f"  Registered: {data}")
        print("  PASSED: User registered successfully!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 10: POST /auth/login
    print("\n[Test 10] POST /api/v1/auth/login - User Login")
    print("-" * 60)
    try:
        login_data = {
            "username": "testuser",
            "password": "testpass123",
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

        print(f"  Token: {data['access_token'][:20]}...")
        print("  PASSED: Login successful!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 11: GET /auth/me
    print("\n[Test 11] GET /api/v1/auth/me - Get Current User")
    print("-" * 60)
    try:
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

        print(f"  User: {data}")
        print("  PASSED: Current user retrieved!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Test 12: POST /auth/login - Wrong password
    print("\n[Test 12] POST /api/v1/auth/login - Wrong Password")
    print("-" * 60)
    try:
        login_data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("  PASSED: Wrong password returns 401!")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  PASSED: {passed}")
    print(f"  FAILED: {failed}")
    print(f"  TOTAL:  {passed + failed}")

    if failed == 0:
        print("\n ALL TESTS PASSED! ")
        return 0
    else:
        print(f"\n {failed} TEST(S) FAILED ")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
