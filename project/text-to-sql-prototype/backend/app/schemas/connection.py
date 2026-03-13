"""Database connection schemas for request and response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ColumnSchema(BaseModel):
    """Schema for table column information."""
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    comment: Optional[str] = None


class ForeignKeySchema(BaseModel):
    """Schema for foreign key relationship."""
    column: str
    referenced_table: str
    referenced_column: str


class TableSchema(BaseModel):
    """Schema for table information."""
    name: str
    columns: List[ColumnSchema]
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[ForeignKeySchema] = Field(default_factory=list)
    comment: Optional[str] = None


class ConnectionBase(BaseModel):
    """Base connection schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=100)
    db_type: str = Field(..., pattern="^(mysql|postgresql|sqlite)$")
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = None
    database: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=100)

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate port number."""
        if v is not None and not (1 <= v <= 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v


class ConnectionCreate(ConnectionBase):
    """Schema for creating a new database connection."""
    password: Optional[str] = Field(None, max_length=255)

    @field_validator('host', 'port', 'database', 'username', 'password')
    @classmethod
    def validate_required_fields(cls, v: Any, info) -> Any:
        """Validate that required fields are present for non-SQLite databases."""
        # Get all values from the model
        values = info.data
        db_type = values.get('db_type')

        if db_type != 'sqlite':
            field_name = info.field_name
            if field_name in ['host', 'database', 'username'] and v is None:
                raise ValueError(f'{field_name} is required for {db_type} connections')

        return v


class ConnectionUpdate(BaseModel):
    """Schema for updating a database connection."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = None
    database: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, max_length=255)

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate port number."""
        if v is not None and not (1 <= v <= 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v


class ConnectionInDB(ConnectionBase):
    """Schema for connection stored in database."""
    id: int
    user_id: int
    password_encrypted: Optional[str] = None
    schema_cache: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ConnectionResponse(ConnectionBase):
    """Schema for connection response data."""
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ConnectionTestRequest(BaseModel):
    """Schema for testing a database connection."""
    db_type: str = Field(..., pattern="^(mysql|postgresql|sqlite)$")
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = None
    database: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, max_length=255)


class ConnectionTestResponse(BaseModel):
    """Schema for connection test response."""
    success: bool
    message: str


class SchemaResponse(BaseModel):
    """Schema for database schema response."""
    tables: List[TableSchema]
    schema_text: str
    last_updated: Optional[datetime] = None


class SchemaRefreshResponse(BaseModel):
    """Schema for schema refresh response."""
    success: bool
    message: str
    tables_count: int
