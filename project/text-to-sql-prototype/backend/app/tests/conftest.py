"""Pytest configuration and fixtures."""
import asyncio
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        # Rollback after each test
        await session.rollback()


@pytest.fixture
def sample_dev_json() -> list:
    """Return sample dev.json data."""
    return [
        {
            "question_id": "q1",
            "question": "What is the total enrollment?",
            "SQL": "SELECT SUM(enrollment) FROM schools",
            "db_id": "california_schools",
            "evidence": "Enrollment data is in schools table",
            "difficulty": "simple",
            "category": "aggregation",
        },
        {
            "question_id": "q2",
            "question": "List all schools in Los Angeles",
            "SQL": "SELECT * FROM schools WHERE city = 'Los Angeles'",
            "db_id": "california_schools",
            "evidence": None,
            "difficulty": "simple",
            "category": "selection",
        },
        {
            "question_id": "q3",
            "question": "What is the revenue?",
            "SQL": "SELECT SUM(revenue) FROM financial",
            "db_id": "financial",
            "evidence": "Financial data",
            "difficulty": "moderate",
            "category": "aggregation",
        },
    ]


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_zip_file(temp_dir, sample_dev_json) -> str:
    """Create a sample ZIP file with BIRD dataset structure."""
    zip_path = os.path.join(temp_dir, "bird_dataset.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add dev.json
        dev_json_content = json.dumps(sample_dev_json)
        zf.writestr("dev.json", dev_json_content)

        # Add databases directory with dummy sqlite files
        zf.writestr("databases/california_schools/california_schools.sqlite", b"")
        zf.writestr("databases/financial/financial.sqlite", b"")

    return zip_path


@pytest.fixture
def invalid_zip_file(temp_dir) -> str:
    """Create an invalid ZIP file (not a real zip)."""
    zip_path = os.path.join(temp_dir, "invalid.zip")
    with open(zip_path, "w") as f:
        f.write("This is not a valid zip file")
    return zip_path


@pytest.fixture
def empty_zip_file(temp_dir) -> str:
    """Create an empty ZIP file."""
    zip_path = os.path.join(temp_dir, "empty.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED):
        pass
    return zip_path


@pytest.fixture
def missing_fields_json() -> list:
    """Return JSON data with missing required fields."""
    return [
        {
            "question_id": "q1",
            "question": "What is the total?",
            # Missing SQL and db_id
        },
        {
            # Missing question_id
            "question": "List all items",
            "SQL": "SELECT * FROM items",
            "db_id": "test_db",
        },
    ]
