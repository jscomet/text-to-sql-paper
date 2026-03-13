"""Database connection service for managing database connections."""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import decrypt_api_key, encrypt_api_key
from app.models.db_connection import DBConnection
from app.schemas.connection import ConnectionCreate, ConnectionTestRequest, TableSchema
from app.services.schema import SchemaService

logger = get_logger(__name__)

# Connection pool cache: connection_id -> AsyncEngine
_connection_pool: Dict[int, AsyncEngine] = {}


class ConnectionService:
    """Service for managing database connections."""

    @staticmethod
    def _build_connection_url(
        db_type: str,
        host: Optional[str],
        port: Optional[int],
        database: Optional[str],
        username: Optional[str],
        password: Optional[str],
    ) -> str:
        """Build SQLAlchemy connection URL.

        Args:
            db_type: Database type (mysql, postgresql, sqlite).
            host: Database host.
            port: Database port.
            database: Database name or file path.
            username: Database username.
            password: Database password.

        Returns:
            SQLAlchemy connection URL string.
        """
        if db_type == "sqlite":
            # For SQLite, database is the file path
            return f"sqlite+aiosqlite:///{database}"
        elif db_type == "postgresql":
            return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "mysql":
            return f"mysql+aiomysql://{username}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    async def test_connection_request(test_data: ConnectionTestRequest) -> tuple[bool, str]:
        """Test a database connection from request data.

        Args:
            test_data: Connection test request data.

        Returns:
            Tuple of (success: bool, message: str).
        """
        try:
            url = ConnectionService._build_connection_url(
                db_type=test_data.db_type,
                host=test_data.host,
                port=test_data.port,
                database=test_data.database,
                username=test_data.username,
                password=test_data.password or "",
            )

            # Create temporary engine for testing
            # SQLite doesn't support pool_size and max_overflow
            engine_kwargs = {"pool_pre_ping": True, "echo": False}
            if test_data.db_type != "sqlite":
                engine_kwargs["pool_size"] = 1
                engine_kwargs["max_overflow"] = 0

            engine = create_async_engine(url, **engine_kwargs)

            # Test connection
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            await engine.dispose()
            return True, "Connection successful"

        except SQLAlchemyError as e:
            logger.error(f"Connection test failed: {e}")
            return False, f"Database connection failed: {str(e)}"
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, f"Connection test failed: {str(e)}"

    @staticmethod
    async def test_connection_model(connection: DBConnection) -> tuple[bool, Optional[str]]:
        """Test if a database connection model is valid.

        Args:
            connection: The connection to test.

        Returns:
            Tuple of (success, error_message).
        """
        try:
            password = ConnectionService._decrypt_password(connection.password_encrypted)
            url = ConnectionService._build_connection_url(
                db_type=connection.db_type,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password or "",
            )
            engine = create_async_engine(url, echo=False, future=True)

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            await engine.dispose()
            return True, None

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e)

    @staticmethod
    def _encrypt_password(password: Optional[str]) -> Optional[str]:
        """Encrypt password for storage.

        Args:
            password: Plain text password.

        Returns:
            Encrypted password string.
        """
        if not password:
            return None
        return encrypt_api_key(password)

    @staticmethod
    def _decrypt_password(encrypted_password: Optional[str]) -> Optional[str]:
        """Decrypt password from storage.

        Args:
            encrypted_password: Encrypted password string.

        Returns:
            Decrypted plain text password.
        """
        if not encrypted_password:
            return None
        return decrypt_api_key(encrypted_password)

    @staticmethod
    async def create_connection(
        db: Any,
        user_id: int,
        connection_data: ConnectionCreate,
    ) -> DBConnection:
        """Create a new database connection.

        Args:
            db: Database session.
            user_id: User ID who owns the connection.
            connection_data: Connection creation data.

        Returns:
            Created DBConnection object.
        """
        # Encrypt password
        encrypted_password = ConnectionService._encrypt_password(connection_data.password)

        db_connection = DBConnection(
            user_id=user_id,
            name=connection_data.name,
            db_type=connection_data.db_type,
            host=connection_data.host,
            port=connection_data.port,
            database=connection_data.database,
            username=connection_data.username,
            password_encrypted=encrypted_password,
            status="active",
        )

        db.add(db_connection)
        await db.commit()
        await db.refresh(db_connection)

        return db_connection

    @staticmethod
    async def update_connection(
        db: Any,
        connection: DBConnection,
        update_data: Dict[str, Any],
    ) -> DBConnection:
        """Update an existing database connection.

        Args:
            db: Database session.
            connection: Existing DBConnection object.
            update_data: Dictionary of fields to update.

        Returns:
            Updated DBConnection object.
        """
        # Handle password update
        if "password" in update_data:
            password = update_data.pop("password")
            if password:
                connection.password_encrypted = ConnectionService._encrypt_password(password)

        # Update other fields
        for field, value in update_data.items():
            if hasattr(connection, field) and value is not None:
                setattr(connection, field, value)

        connection.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(connection)

        # Close cached engine if connection details changed
        if connection.id in _connection_pool:
            await _connection_pool[connection.id].dispose()
            del _connection_pool[connection.id]

        return connection

    @staticmethod
    async def delete_connection(
        db: Any,
        connection: DBConnection,
    ) -> None:
        """Delete a database connection.

        Args:
            db: Database session.
            connection: DBConnection object to delete.
        """
        # Close cached engine
        if connection.id in _connection_pool:
            await _connection_pool[connection.id].dispose()
            del _connection_pool[connection.id]

        await db.delete(connection)
        await db.commit()

    @staticmethod
    def get_async_engine(connection: DBConnection) -> AsyncEngine:
        """Get async database engine for a connection (alias for get_db_engine).

        Args:
            connection: DBConnection object.

        Returns:
            AsyncEngine instance.
        """
        return ConnectionService.get_db_engine(connection)

    @staticmethod
    def get_db_engine(connection: DBConnection) -> AsyncEngine:
        """Get or create database engine for a connection.

        Args:
            connection: DBConnection object.

        Returns:
            AsyncEngine instance.
        """
        if connection.id not in _connection_pool:
            password = ConnectionService._decrypt_password(connection.password_encrypted)
            url = ConnectionService._build_connection_url(
                db_type=connection.db_type,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password or "",
            )

            # SQLite doesn't support pool_size and max_overflow
            engine_kwargs = {
                "pool_pre_ping": True,
                "echo": settings.is_development,
            }
            if connection.db_type != "sqlite":
                engine_kwargs["pool_size"] = 5
                engine_kwargs["max_overflow"] = 10
                engine_kwargs["pool_recycle"] = 3600

            engine = create_async_engine(url, **engine_kwargs)

            _connection_pool[connection.id] = engine

        return _connection_pool[connection.id]

    @staticmethod
    async def close_connection(connection_id: int) -> None:
        """Close a cached database connection.

        Args:
            connection_id: ID of the connection to close.
        """
        if connection_id in _connection_pool:
            await _connection_pool[connection_id].dispose()
            del _connection_pool[connection_id]

    @staticmethod
    async def close_all_connections() -> None:
        """Close all cached database connections."""
        for engine in _connection_pool.values():
            await engine.dispose()
        _connection_pool.clear()

    @staticmethod
    async def sync_schema(connection: DBConnection) -> Dict[str, Any]:
        """Synchronize and cache database schema.

        Args:
            connection: DBConnection object.

        Returns:
            Dictionary containing schema cache data.
        """
        engine = ConnectionService.get_db_engine(connection)

        # Get all schemas
        tables = await SchemaService.get_all_schemas(engine)

        # Build schema cache
        schema_cache = {
            "tables": [table.model_dump() for table in tables],
            "last_updated": datetime.utcnow().isoformat(),
        }

        # Update connection with schema cache
        connection.schema_cache = schema_cache
        connection.updated_at = datetime.utcnow()

        return schema_cache

    @staticmethod
    def get_cached_schema(connection: DBConnection) -> Optional[Dict[str, Any]]:
        """Get cached schema for a connection.

        Args:
            connection: DBConnection object.

        Returns:
            Cached schema dictionary or None.
        """
        return connection.schema_cache

    @staticmethod
    def parse_cached_schema(connection: DBConnection) -> list[TableSchema]:
        """Parse cached schema into TableSchema objects.

        Args:
            connection: DBConnection object.

        Returns:
            List of TableSchema objects.
        """
        if not connection.schema_cache:
            return []

        tables_data = connection.schema_cache.get("tables", [])
        return [TableSchema(**table) for table in tables_data]

    @staticmethod
    def build_schema_text(connection: DBConnection) -> str:
        """Build CREATE TABLE text from cached schema.

        Args:
            connection: DBConnection object.

        Returns:
            String containing CREATE TABLE statements.
        """
        tables = ConnectionService.parse_cached_schema(connection)
        return SchemaService.build_schema_text(tables)

    @staticmethod
    async def batch_create_connections(
        db: Any,
        db_ids: List[str],
        base_path: str,
        user_id: int,
        prefix: str = "bird"
    ) -> Dict[str, int]:
        """Batch create database connections for multiple databases.

        This method creates connection configurations for multiple SQLite databases
        typically used in BIRD dataset import scenarios.

        Args:
            db: Database session.
            db_ids: List of database identifiers (e.g., ["california_schools", "financial"]).
            base_path: Base directory path containing the SQLite database files.
            user_id: User ID who owns the connections.
            prefix: Prefix for connection names (default: "bird").

        Returns:
            Dictionary mapping db_id to connection_id.

        Example:
            >>> db_ids = ["california_schools", "financial"]
            >>> base_path = "/data/bird/databases"
            >>> mapping = await ConnectionService.batch_create_connections(
            ...     db, db_ids, base_path, user_id=1
            ... )
            >>> print(mapping)
            {"california_schools": 1, "financial": 2}
        """
        mapping: Dict[str, int] = {}

        for db_id in db_ids:
            # Generate connection name
            connection_name = f"{prefix}_{db_id}"

            # Build database file path
            # BIRD dataset structure: base_path/db_id/db_id.sqlite
            db_file_path = os.path.join(base_path, db_id, f"{db_id}.sqlite")

            # Alternative: try .db extension if .sqlite doesn't exist
            if not os.path.exists(db_file_path):
                db_file_path = os.path.join(base_path, db_id, f"{db_id}.db")

            # Check if connection already exists for this user and name
            result = await db.execute(
                select(DBConnection).where(
                    DBConnection.user_id == user_id,
                    DBConnection.name == connection_name
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Reuse existing connection
                mapping[db_id] = existing.id
                logger.info(f"Reusing existing connection {existing.id} for {db_id}")
                continue

            # Create new connection
            connection_data = ConnectionCreate(
                name=connection_name,
                db_type="sqlite",
                host=None,
                port=None,
                database=db_file_path,
                username=None,
                password=None
            )

            try:
                connection = await ConnectionService.create_connection(
                    db=db,
                    user_id=user_id,
                    connection_data=connection_data
                )
                mapping[db_id] = connection.id
                logger.info(f"Created connection {connection.id} for {db_id}")
            except Exception as e:
                logger.error(f"Failed to create connection for {db_id}: {e}")
                # Continue with other databases even if one fails
                continue

        return mapping

    @staticmethod
    async def batch_test_connections(
        db: Any,
        connection_ids: List[int]
    ) -> Dict[int, Tuple[bool, Optional[str]]]:
        """Test multiple database connections.

        Args:
            db: Database session.
            connection_ids: List of connection IDs to test.

        Returns:
            Dictionary mapping connection_id to (success, error_message) tuple.
        """
        results: Dict[int, Tuple[bool, Optional[str]]] = {}

        for conn_id in connection_ids:
            result = await db.execute(
                select(DBConnection).where(DBConnection.id == conn_id)
            )
            connection = result.scalar_one_or_none()

            if not connection:
                results[conn_id] = (False, "Connection not found")
                continue

            success, error = await ConnectionService.test_connection_model(connection)
            results[conn_id] = (success, error)

        return results
