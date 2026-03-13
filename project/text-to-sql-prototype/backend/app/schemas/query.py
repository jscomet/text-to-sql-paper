"""Query schemas for request and response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryGenerateRequest(BaseModel):
    """Schema for SQL generation request."""
    question: str = Field(..., min_length=1, max_length=2000, description="Natural language question")
    connection_id: int = Field(..., description="Database connection ID")
    provider: Optional[str] = Field(None, description="LLM provider (openai, dashscope)")


class QueryExecuteRequest(BaseModel):
    """Schema for SQL execution request."""
    sql: str = Field(..., min_length=1, description="SQL query to execute")
    connection_id: int = Field(..., description="Database connection ID")


class QueryRunRequest(BaseModel):
    """Schema for end-to-end query request (generate + execute)."""
    question: str = Field(..., min_length=1, max_length=2000, description="Natural language question")
    connection_id: int = Field(..., description="Database connection ID")
    provider: Optional[str] = Field(None, description="LLM provider (openai, dashscope)")
    execute: bool = Field(True, description="Whether to execute the generated SQL")


class QueryResultData(BaseModel):
    """Schema for query execution result data."""
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    total_rows: int = 0
    truncated: bool = False
    displayed_rows: int = 0


class QueryGenerateResponse(BaseModel):
    """Schema for SQL generation response."""
    success: bool
    query_id: int
    question: str
    generated_sql: Optional[str] = None
    formatted_sql: Optional[str] = None
    error: Optional[str] = None
    # Frontend compatibility fields
    sql: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.9
    execution_time: float = 0


class QueryExecuteResponse(BaseModel):
    """Schema for SQL execution response."""
    success: bool
    query_id: int
    sql: str
    # Root-level fields for frontend compatibility
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time: float = 0  # Frontend expects this field name (in ms)
    # Legacy fields for backward compatibility
    result: Optional[QueryResultData] = None
    execution_time_ms: float = 0
    error: Optional[str] = None


class QueryRunResponse(BaseModel):
    """Schema for end-to-end query response."""
    success: bool
    query_id: int
    question: str
    generated_sql: Optional[str] = None
    formatted_sql: Optional[str] = None
    # Root-level fields for frontend compatibility
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time: float = 0
    # Legacy fields for backward compatibility
    result: Optional[QueryResultData] = None
    execution_time_ms: float = 0
    generation_time_ms: float = 0
    error: Optional[str] = None
    # Frontend compatibility fields
    sql: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.9
    execution_time: float = 0


class QueryHistoryItem(BaseModel):
    """Schema for query history item."""
    id: int
    user_id: int
    connection_id: Optional[int]
    nl_question: str
    generated_sql: Optional[str]
    execution_status: str
    execution_time_ms: Optional[float]
    is_favorite: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryListResponse(BaseModel):
    """Schema for query history list response."""
    items: List[QueryHistoryItem]
    total: int
    limit: int
    offset: int


class QueryFavoriteRequest(BaseModel):
    """Schema for toggling favorite status."""
    is_favorite: bool


class ToggleFavoriteResponse(BaseModel):
    """Response schema for toggle favorite."""
    success: bool
    is_favorite: bool
    message: str
