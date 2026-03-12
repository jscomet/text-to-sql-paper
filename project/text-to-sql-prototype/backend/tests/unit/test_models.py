"""Tests for database models."""
import pytest
from datetime import datetime

from app.models.user import User
from app.models.db_connection import DBConnection
from app.models.query_history import QueryHistory
from app.models.eval_task import EvalTask
from app.models.eval_result import EvalResult
from app.models.api_key import APIKey


class TestUserModel:
    """Tests for User model."""

    @pytest.mark.asyncio
    async def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role="user",
            status="active",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active() is True
        assert user.is_admin() is False

    @pytest.mark.asyncio
    async def test_user_is_active_inactive(self, db_session):
        """Test is_active method for inactive user."""
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash="hashed_password",
            role="user",
            status="inactive",
        )
        db_session.add(user)
        await db_session.commit()

        assert user.is_active() is False

    @pytest.mark.asyncio
    async def test_user_is_admin(self, db_session):
        """Test is_admin method."""
        user = User(
            username="adminuser",
            email="admin@example.com",
            password_hash="hashed_password",
            role="admin",
            status="active",
        )
        db_session.add(user)
        await db_session.commit()

        assert user.is_admin() is True

    @pytest.mark.asyncio
    async def test_user_to_dict(self, db_session):
        """Test user to_dict method."""
        user = User(
            username="dictuser",
            email="dict@example.com",
            password_hash="hashed_password",
            role="user",
            status="active",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        user_dict = user.to_dict()
        assert user_dict["username"] == "dictuser"
        assert user_dict["email"] == "dict@example.com"
        assert "password_hash" in user_dict


class TestDBConnectionModel:
    """Tests for DBConnection model."""

    @pytest.mark.asyncio
    async def test_db_connection_creation(self, db_session, test_user):
        """Test creating a database connection."""
        conn = DBConnection(
            user_id=test_user.id,
            name="Test Connection",
            db_type="mysql",
            host="localhost",
            port=3306,
            database="test_db",
            username="dbuser",
            password_encrypted="encrypted_pass",
        )
        db_session.add(conn)
        await db_session.commit()
        await db_session.refresh(conn)

        assert conn.id is not None
        assert conn.name == "Test Connection"
        assert conn.db_type == "mysql"
        assert conn.user_id == test_user.id


class TestQueryHistoryModel:
    """Tests for QueryHistory model."""

    @pytest.mark.asyncio
    async def test_query_history_creation(self, db_session, test_user):
        """Test creating a query history entry."""
        query = QueryHistory(
            user_id=test_user.id,
            connection_id=None,
            question="How many users?",
            generated_sql="SELECT COUNT(*) FROM users",
            execution_status="success",
            execution_time_ms=150.5,
        )
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)

        assert query.id is not None
        assert query.question == "How many users?"
        assert query.execution_status == "success"
        assert query.execution_time_ms == 150.5


class TestEvalTaskModel:
    """Tests for EvalTask model."""

    @pytest.mark.asyncio
    async def test_eval_task_creation(self, db_session, test_user):
        """Test creating an evaluation task."""
        task = EvalTask(
            user_id=test_user.id,
            name="Test Eval Task",
            description="Test description",
            connection_id=None,
            status="pending",
            total_samples=10,
            processed_samples=0,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.id is not None
        assert task.name == "Test Eval Task"
        assert task.status == "pending"
        assert task.total_samples == 10

    @pytest.mark.asyncio
    async def test_eval_task_progress(self, db_session, test_user):
        """Test evaluation task progress calculation."""
        task = EvalTask(
            user_id=test_user.id,
            name="Progress Test",
            description="Test",
            connection_id=None,
            status="running",
            total_samples=100,
            processed_samples=50,
        )
        db_session.add(task)
        await db_session.commit()

        # Check progress percentage
        progress = (task.processed_samples / task.total_samples) * 100
        assert progress == 50.0


class TestEvalResultModel:
    """Tests for EvalResult model."""

    @pytest.mark.asyncio
    async def test_eval_result_creation(self, db_session, test_user):
        """Test creating an evaluation result."""
        # First create a task
        task = EvalTask(
            user_id=test_user.id,
            name="Result Test Task",
            description="Test",
            connection_id=None,
            status="completed",
            total_samples=1,
            processed_samples=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        result = EvalResult(
            task_id=task.id,
            question_id="q1",
            question="Test question?",
            gold_sql="SELECT 1",
            pred_sql="SELECT 1",
            execution_success=True,
            is_correct=True,
            error_type=None,
            execution_time_ms=100.0,
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.id is not None
        assert result.is_correct is True
        assert result.execution_success is True

    @pytest.mark.asyncio
    async def test_eval_result_with_error(self, db_session, test_user):
        """Test evaluation result with error."""
        task = EvalTask(
            user_id=test_user.id,
            name="Error Test Task",
            description="Test",
            connection_id=None,
            status="completed",
            total_samples=1,
            processed_samples=1,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        result = EvalResult(
            task_id=task.id,
            question_id="q2",
            question="Bad question?",
            gold_sql="SELECT 1",
            pred_sql="INVALID SQL",
            execution_success=False,
            is_correct=False,
            error_type="syntax_error",
            error_message="Syntax error near 'INVALID'",
            execution_time_ms=0.0,
        )
        db_session.add(result)
        await db_session.commit()

        assert result.execution_success is False
        assert result.error_type == "syntax_error"
        assert result.error_message is not None


class TestAPIKeyModel:
    """Tests for APIKey model."""

    @pytest.mark.asyncio
    async def test_api_key_creation(self, db_session, test_user):
        """Test creating an API key."""
        api_key = APIKey(
            user_id=test_user.id,
            name="Test API Key",
            provider="openai",
            key_encrypted="encrypted_key_value",
            is_active=True,
        )
        db_session.add(api_key)
        await db_session.commit()
        await db_session.refresh(api_key)

        assert api_key.id is not None
        assert api_key.name == "Test API Key"
        assert api_key.provider == "openai"
        assert api_key.is_active is True

    @pytest.mark.asyncio
    async def test_api_key_deactivation(self, db_session, test_user):
        """Test deactivating an API key."""
        api_key = APIKey(
            user_id=test_user.id,
            name="Inactive Key",
            provider="dashscope",
            key_encrypted="encrypted_key",
            is_active=True,
        )
        db_session.add(api_key)
        await db_session.commit()

        # Deactivate
        api_key.is_active = False
        await db_session.commit()

        assert api_key.is_active is False
