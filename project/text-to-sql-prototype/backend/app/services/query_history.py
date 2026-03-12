"""Query history service for managing query records."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.query_history import QueryHistory

logger = get_logger(__name__)


class QueryHistoryService:
    """Service for managing query history."""

    def __init__(self, db_session: AsyncSession):
        """Initialize query history service.

        Args:
            db_session: Database session.
        """
        self.db = db_session

    async def create_query(
        self,
        user_id: int,
        nl_question: str,
        connection_id: Optional[int] = None,
    ) -> QueryHistory:
        """Create a new query history record.

        Args:
            user_id: User ID.
            nl_question: Natural language question.
            connection_id: Optional database connection ID.

        Returns:
            Created QueryHistory record.
        """
        query = QueryHistory(
            user_id=user_id,
            connection_id=connection_id,
            nl_question=nl_question,
            execution_status="pending",
        )

        self.db.add(query)
        await self.db.commit()
        await self.db.refresh(query)

        logger.debug(f"Created query history record: {query.id}")
        return query

    async def update_query_result(
        self,
        query_id: int,
        generated_sql: Optional[str] = None,
        execution_status: str = "completed",
        execution_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> Optional[QueryHistory]:
        """Update query with results.

        Args:
            query_id: Query history ID.
            generated_sql: Generated SQL query.
            execution_status: Execution status.
            execution_time_ms: Execution time in milliseconds.
            error_message: Error message if failed.

        Returns:
            Updated QueryHistory record or None if not found.
        """
        result = await self.db.execute(
            select(QueryHistory).where(QueryHistory.id == query_id)
        )
        query = result.scalar_one_or_none()

        if not query:
            logger.warning(f"Query history not found: {query_id}")
            return None

        if generated_sql is not None:
            query.generated_sql = generated_sql
        query.execution_status = execution_status
        if execution_time_ms is not None:
            query.execution_time_ms = execution_time_ms
        if error_message is not None:
            query.error_message = error_message

        await self.db.commit()
        await self.db.refresh(query)

        logger.debug(f"Updated query history record: {query_id}")
        return query

    async def get_query(
        self,
        query_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[QueryHistory]:
        """Get a query history record.

        Args:
            query_id: Query history ID.
            user_id: Optional user ID for access control.

        Returns:
            QueryHistory record or None if not found.
        """
        stmt = select(QueryHistory).where(QueryHistory.id == query_id)

        if user_id is not None:
            stmt = stmt.where(QueryHistory.user_id == user_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_queries(
        self,
        user_id: int,
        connection_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
        favorites_only: bool = False,
    ) -> tuple[List[QueryHistory], int]:
        """List query history for a user.

        Args:
            user_id: User ID.
            connection_id: Optional connection ID filter.
            limit: Maximum number of records.
            offset: Offset for pagination.
            favorites_only: Only return favorite queries.

        Returns:
            Tuple of (list of queries, total count).
        """
        # Build base query
        base_stmt = select(QueryHistory).where(QueryHistory.user_id == user_id)

        if connection_id is not None:
            base_stmt = base_stmt.where(QueryHistory.connection_id == connection_id)

        if favorites_only:
            base_stmt = base_stmt.where(QueryHistory.is_favorite == True)

        # Get total count
        count_stmt = select(QueryHistory).where(QueryHistory.user_id == user_id)
        if connection_id is not None:
            count_stmt = count_stmt.where(QueryHistory.connection_id == connection_id)
        if favorites_only:
            count_stmt = count_stmt.where(QueryHistory.is_favorite == True)

        count_result = await self.db.execute(count_stmt)
        total = len(count_result.scalars().all())

        # Get paginated results
        stmt = base_stmt.order_by(desc(QueryHistory.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        queries = list(result.scalars().all())

        return queries, total

    async def toggle_favorite(
        self,
        query_id: int,
        user_id: int,
    ) -> Optional[QueryHistory]:
        """Toggle favorite status for a query.

        Args:
            query_id: Query history ID.
            user_id: User ID.

        Returns:
            Updated QueryHistory record or None if not found.
        """
        result = await self.db.execute(
            select(QueryHistory).where(
                QueryHistory.id == query_id,
                QueryHistory.user_id == user_id,
            )
        )
        query = result.scalar_one_or_none()

        if not query:
            return None

        query.is_favorite = not query.is_favorite
        await self.db.commit()
        await self.db.refresh(query)

        logger.debug(f"Toggled favorite for query {query_id}: {query.is_favorite}")
        return query

    async def delete_query(
        self,
        query_id: int,
        user_id: int,
    ) -> bool:
        """Delete a query history record.

        Args:
            query_id: Query history ID.
            user_id: User ID.

        Returns:
            True if deleted, False if not found.
        """
        result = await self.db.execute(
            select(QueryHistory).where(
                QueryHistory.id == query_id,
                QueryHistory.user_id == user_id,
            )
        )
        query = result.scalar_one_or_none()

        if not query:
            return False

        await self.db.delete(query)
        await self.db.commit()

        logger.debug(f"Deleted query history record: {query_id}")
        return True

    def to_dict(self, query: QueryHistory) -> Dict[str, Any]:
        """Convert QueryHistory to dictionary.

        Args:
            query: QueryHistory record.

        Returns:
            Dictionary representation.
        """
        return {
            "id": query.id,
            "user_id": query.user_id,
            "connection_id": query.connection_id,
            "nl_question": query.nl_question,
            "generated_sql": query.generated_sql,
            "execution_status": query.execution_status,
            "execution_time_ms": query.execution_time_ms,
            "is_favorite": query.is_favorite,
            "error_message": query.error_message,
            "created_at": query.created_at.isoformat() if query.created_at else None,
        }
