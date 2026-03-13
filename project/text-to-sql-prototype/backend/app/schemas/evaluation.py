"""Evaluation schemas for request and response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvalTaskCreate(BaseModel):
    """Schema for creating an evaluation task.

    Supports advanced inference modes including Pass@K and CheckCorrect.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Task name")
    dataset_type: str = Field(..., pattern="^(spider|bird|custom)$", description="Dataset type")
    dataset_path: Optional[str] = Field(None, max_length=500, description="Path to custom dataset")
    connection_id: int = Field(..., description="Database connection ID")
    api_key_id: int = Field(..., description="API Key ID")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(2000, ge=100, le=8000, description="Maximum tokens")

    # 扩展的评估模式枚举值
    eval_mode: str = Field(
        "greedy_search",
        pattern="^(greedy_search|majority_vote|pass_at_k|check_correct)$",
        description="Evaluation mode: greedy_search/majority_vote/pass_at_k/check_correct"
    )

    # 保留的现有字段（用于 majority_vote 模式）
    vote_count: int = Field(5, ge=3, le=10, description="Number of votes for majority voting")

    # 新增字段 - 用于 Pass@K 模式
    sampling_count: int = Field(
        8,
        ge=1,
        le=16,
        description="Pass@K的K值，采样数量"
    )

    # 新增字段 - 用于 CheckCorrect 模式
    max_iterations: int = Field(
        3,
        ge=1,
        le=5,
        description="CheckCorrect最大迭代次数"
    )
    correction_strategy: str = Field(
        "none",
        description="修正策略: none/self_correction/execution_feedback/multi_agent"
    )

    # 配置对象 - 用于存储采样和修正的详细配置
    sampling_config: Optional[Dict[str, Any]] = Field(
        None,
        description="采样参数配置，如temperature_schedule, top_p等"
    )
    correction_config: Optional[Dict[str, Any]] = Field(
        None,
        description="修正策略配置，如error_threshold, retry_policy等"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "BIRD Pass@8 Evaluation",
                "dataset_type": "bird",
                "dataset_path": "/data/bird/dev.json",
                "connection_id": 2,
                "api_key_id": 1,
                "eval_mode": "pass_at_k",
                "sampling_count": 8,
                "temperature": 0.8
            }
        }
    )

    @field_validator("sampling_count")
    @classmethod
    def validate_sampling_count(cls, v: int) -> int:
        """Validate sampling_count is within valid range."""
        if v < 1 or v > 16:
            raise ValueError("sampling_count must be between 1 and 16")
        return v

    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v: int) -> int:
        """Validate max_iterations is within valid range."""
        if v < 1 or v > 5:
            raise ValueError("max_iterations must be between 1 and 5")
        return v

    @field_validator("correction_strategy")
    @classmethod
    def validate_correction_strategy(cls, v: str) -> str:
        """Validate correction_strategy is valid."""
        valid_strategies = ["none", "self_correction", "execution_feedback", "multi_agent"]
        if v not in valid_strategies:
            raise ValueError(f"correction_strategy must be one of: {', '.join(valid_strategies)}")
        return v


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
    model_settings: Dict[str, Any] = Field(alias="model_config")
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


class PaginationInfo(BaseModel):
    """Pagination information."""
    page: int
    page_size: int
    total: int
    total_pages: int


class EvalTaskListResponse(BaseModel):
    """Schema for evaluation task list response."""
    list: List[EvalTaskResponse]
    pagination: PaginationInfo


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
    list: List[EvalResultResponse]
    pagination: PaginationInfo


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
