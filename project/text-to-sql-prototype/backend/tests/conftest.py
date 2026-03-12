"""Pytest fixtures for backend tests."""
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app as fastapi_app
from app.core.config import settings
from app.core.auth import create_access_token
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User
from app.api.deps import get_db

# Import all models to ensure they are registered with Base.metadata
from app.models.db_connection import DBConnection
from app.models.query_history import QueryHistory
from app.models.eval_task import EvalTask
from app.models.eval_result import EvalResult
from app.models.api_key import APIKey
from app.models.system_config import SystemConfig


# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session() as session:
        yield session
        # Rollback any changes after test
        await session.rollback()


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    """Create a test FastAPI app with overridden dependencies."""
    # Override the get_db dependency
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield fastapi_app
    # Clear overrides after test
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data() -> dict:
    """Return test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def test_user_data_2() -> dict:
    """Return second test user data."""
    return {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpassword456",
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict) -> User:
    """Create a test user in the database."""
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password_hash=get_password_hash(test_user_data["password"]),
        role="user",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user in the database."""
    user = User(
        username="adminuser",
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        role="admin",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate authentication headers for test user."""
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(test_admin: User) -> dict:
    """Generate authentication headers for admin user."""
    access_token = create_access_token(data={"sub": test_admin.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def expired_token(test_user: User) -> str:
    """Generate an expired token."""
    expired_time = timedelta(minutes=-1)
    return create_access_token(data={"sub": test_user.username}, expires_delta=expired_time)


@pytest.fixture
def invalid_auth_headers() -> dict:
    """Generate invalid authentication headers."""
    return {"Authorization": "Bearer invalid_token"}


@pytest.fixture
def mock_llm_response() -> str:
    """Return a mock LLM SQL generation response."""
    return """
    Here's the SQL query:

    ```sql
    SELECT * FROM users WHERE id = 1
    ```

    This query selects all columns from the users table where the id is 1.
    """


@pytest.fixture
def mock_schema_text() -> str:
    """Return a mock database schema text."""
    return """
    Table: users
    - id (INT, PRIMARY KEY)
    - username (VARCHAR(50))
    - email (VARCHAR(100))
    - created_at (DATETIME)

    Table: orders
    - id (INT, PRIMARY KEY)
    - user_id (INT, FOREIGN KEY)
    - total_amount (DECIMAL)
    - status (VARCHAR(20))
    """


@pytest.fixture
def sample_query_results() -> list:
    """Return sample query results."""
    return [
        {"id": 1, "username": "alice", "email": "alice@example.com"},
        {"id": 2, "username": "bob", "email": "bob@example.com"},
    ]


@pytest.fixture
def sample_eval_data() -> dict:
    """Return sample evaluation data."""
    return {
        "question": "How many users are there?",
        "gold_sql": "SELECT COUNT(*) FROM users",
        "pred_sql": "SELECT COUNT(*) FROM users",
        "db_name": "test_db",
    }
