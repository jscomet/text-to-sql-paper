"""Database connections API routes."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.db_connection import DBConnection
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationInfo
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
    ConnectionUpdate,
    SchemaRefreshResponse,
    SchemaResponse,
)
from app.services.connection import ConnectionService
from app.services.schema import SchemaService

router = APIRouter(prefix="/connections", tags=["Connections"])


@router.get("", response_model=PaginatedResponse[ConnectionResponse])
async def list_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[ConnectionResponse]:
    """Get all database connections for the current user.

    Args:
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Paginated list of database connections.
    """
    result = await db.execute(
        select(DBConnection).where(DBConnection.user_id == current_user.id)
    )
    connections = result.scalars().all()
    connection_list = list(connections)
    total = len(connection_list)

    return PaginatedResponse(
        list=connection_list,
        pagination=PaginationInfo(
            total=total,
            total_pages=1,  # Currently no pagination, all results in one page
        ),
    )


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection_data: ConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DBConnection:
    """Create a new database connection.

    Args:
        connection_data: Connection creation data.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Created database connection.
    """
    connection = await ConnectionService.create_connection(
        db=db,
        user_id=current_user.id,
        connection_data=connection_data,
    )
    return connection


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    test_data: ConnectionTestRequest,
    _: User = Depends(get_current_active_user),
) -> ConnectionTestResponse:
    """Test a database connection without saving it.

    Args:
        test_data: Connection test data.
        _: Current authenticated user (required for authentication).

    Returns:
        Connection test result.
    """
    success, message = await ConnectionService.test_connection_request(test_data)
    return ConnectionTestResponse(success=success, message=message)


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DBConnection:
    """Get a specific database connection.

    Args:
        connection_id: ID of the connection.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Database connection.

    Raises:
        HTTPException: If connection not found or user doesn't have access.
    """
    result = await db.execute(
        select(DBConnection).where(
            DBConnection.id == connection_id,
            DBConnection.user_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    return connection


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: int,
    update_data: ConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DBConnection:
    """Update a database connection.

    Args:
        connection_id: ID of the connection to update.
        update_data: Update data.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Updated database connection.

    Raises:
        HTTPException: If connection not found or user doesn't have access.
    """
    result = await db.execute(
        select(DBConnection).where(
            DBConnection.id == connection_id,
            DBConnection.user_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    # Convert to dict, excluding unset fields
    update_dict = update_data.model_dump(exclude_unset=True)

    updated_connection = await ConnectionService.update_connection(
        db=db,
        connection=connection,
        update_data=update_dict,
    )

    return updated_connection


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a database connection.

    Args:
        connection_id: ID of the connection to delete.
        db: Database session.
        current_user: Current authenticated user.

    Raises:
        HTTPException: If connection not found or user doesn't have access.
    """
    result = await db.execute(
        select(DBConnection).where(
            DBConnection.id == connection_id,
            DBConnection.user_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    await ConnectionService.delete_connection(db=db, connection=connection)


@router.get("/{connection_id}/schema", response_model=SchemaResponse)
async def get_connection_schema(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SchemaResponse:
    """Get cached schema for a database connection.

    Args:
        connection_id: ID of the connection.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Database schema response.

    Raises:
        HTTPException: If connection not found or schema not cached.
    """
    result = await db.execute(
        select(DBConnection).where(
            DBConnection.id == connection_id,
            DBConnection.user_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    # Get cached schema
    schema_cache = ConnectionService.get_cached_schema(connection)

    if not schema_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not cached. Please refresh schema first.",
        )

    tables = ConnectionService.parse_cached_schema(connection)
    last_updated = schema_cache.get("last_updated")

    # Build schema text
    schema_text = SchemaService.build_schema_text(tables)

    return SchemaResponse(
        tables=tables,
        schema_text=schema_text,
        last_updated=datetime.fromisoformat(last_updated) if last_updated else None,
    )


@router.post("/{connection_id}/schema/refresh", response_model=SchemaRefreshResponse)
async def refresh_connection_schema(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SchemaRefreshResponse:
    """Refresh and cache schema for a database connection.

    Args:
        connection_id: ID of the connection.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Schema refresh response.

    Raises:
        HTTPException: If connection not found or schema refresh fails.
    """
    result = await db.execute(
        select(DBConnection).where(
            DBConnection.id == connection_id,
            DBConnection.user_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    try:
        # Sync schema
        schema_cache = await ConnectionService.sync_schema(connection)
        await db.commit()

        tables_count = len(schema_cache.get("tables", []))

        return SchemaRefreshResponse(
            success=True,
            message=f"Schema refreshed successfully. Found {tables_count} tables.",
            tables_count=tables_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh schema: {str(e)}",
        ) from e
