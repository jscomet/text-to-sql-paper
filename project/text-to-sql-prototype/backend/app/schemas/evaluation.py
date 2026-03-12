"""Evaluation schemas for request and response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvalTaskCreate(BaseModel):
    """Schema for creating an evaluation task."""
    name: str = Field(..., min_length=1, max_length=200, description="Task name")
    dataset_type: str = Field(..., pattern="^(spider|bird|custom)$", description="Dataset type")
    dataset_path: Optional[str] = Field(None, max_length=500, description="Path to custom dataset")
    connection_id: int = Field(..., description="Database connection ID")
    provider: str = Field(..., pattern="^(openai|dashscope)$", description="LLM provider")
    model: Optional[str] = Field(None, description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(2000, ge=100, le=8000, description="Maximum tokens")
    eval_mode: str = Field("greedy_search", pattern="^(greedy_search|majority_vote)$", description="Evaluation mode")
    vote_count: int = Field(5, ge=3, le=10, description="Number of votes for majority voting")


class EvalTaskUpdate(BaseModel):
    """Schema for updating an evaluation task."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed|cancelled)$")


class EvalTaskResponse(BaseModel):
    """Schema for evaluation task response."""
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    name: str
    dataset_type: str
    dataset_path: Optional[str]
    model_settings: Dict[str, Any]
    eval_mode: str
    status: str
    progress_percent: int
    total_questions: Optional[int]
    processed_questions: int
    correct_count: Optional[int]
    accuracy: Optional[float]
    log_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class EvalTaskListResponse(BaseModel):
    """Schema for evaluation task list response."""
    items: List[EvalTaskResponse]
    total: int
    limit: int
    offset: int


class EvalResultResponse(BaseModel):
    """Schema for evaluation result response."""
    model_config = {"from_attributes": True}

    id: int
    task_id: int
    question_id: str
    nl_question: str
    db_id: Optional[str]
    gold_sql: str
    predicted_sql: Optional[str]
    is_correct: Optional[bool]
    error_type: Optional[str]
    error_message: Optional[str]
    execution_time_ms: Optional[float]
    created_at: datetime


class EvalResultListResponse(BaseModel):
    """Schema for evaluation result list response."""
    items: List[EvalResultResponse]
    total: int
    limit: int
    offset: int


class EvalProgressResponse(BaseModel):
    """Schema for evaluation progress response."""
    task_id: int
    status: str
    progress_percent: int
    total_questions: int
    processed_questions: int
    correct_count: int
    accuracy: float
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")


class EvalStatsResponse(BaseModel):
    """Schema for evaluation statistics response."""
    task_id: int
    total_questions: int
    correct_count: int
    accuracy: float
    error_breakdown: Dict[str, int]
    avg_execution_time_ms: Optional[float]


class EvalTaskStats(BaseModel):
    """Schema for detailed evaluation task statistics."""
    task_id: int
    total_questions: int
    correct_count: int
    incorrect_count: int
    pending_count: int
    accuracy: float
    error_types: Dict[str, int]
    avg_execution_time_ms: Optional[float]


class DatasetQuestion(BaseModel):
    """Schema for a dataset question."""
    question_id: str
    nl_question: str
    db_id: str
    gold_sql: str
    db_path: Optional[str] = None


class DatasetLoadResponse(BaseModel):
    """Schema for dataset load response."""
    questions: List[DatasetQuestion]
    total: int
