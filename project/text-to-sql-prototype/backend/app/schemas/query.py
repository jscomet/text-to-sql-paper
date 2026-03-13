"""Query schemas for request and response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


# =============================================================================
# Advanced Inference Schemas
# =============================================================================

class CandidateSQL(BaseModel):
    """Schema for candidate SQL in advanced inference."""
    sql: str = Field(..., description="候选SQL语句")
    is_valid: bool = Field(..., description="是否执行成功")
    execution_result: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="执行结果"
    )
    vote_count: Optional[int] = Field(
        None,
        description="投票数（MajorityVote）"
    )


class CorrectionRecord(BaseModel):
    """Schema for correction history record in CheckCorrect mode."""
    iteration: int = Field(..., description="迭代轮次")
    sql: str = Field(..., description="该轮生成的SQL")
    error_type: Optional[str] = Field(
        None,
        description="错误类型"
    )
    error_message: Optional[str] = Field(
        None,
        description="错误信息"
    )
    correction_prompt: Optional[str] = Field(
        None,
        description="修正提示"
    )


class QueryGenerateAdvancedRequest(BaseModel):
    """Schema for advanced SQL generation request.

    Supports Pass@K, CheckCorrect, MajorityVote and single mode inference.
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="自然语言问题"
    )
    connection_id: int = Field(
        ...,
        description="数据库连接ID"
    )
    provider: Optional[str] = Field(
        None,
        description="LLM提供商"
    )
    reasoning_mode: str = Field(
        "single",
        pattern="^(single|pass_at_k|check_correct|majority_vote)$",
        description="推理模式: single/pass_at_k/check_correct/majority_vote"
    )
    k_candidates: int = Field(
        5,
        ge=1,
        le=16,
        description="候选数量（Pass@K/MajorityVote）"
    )
    max_iterations: int = Field(
        3,
        ge=1,
        le=5,
        description="最大迭代次数（CheckCorrect）"
    )
    temperature: float = Field(
        0.8,
        ge=0.0,
        le=2.0,
        description="采样温度"
    )
    enable_self_correction: bool = Field(
        False,
        description="是否启用自我修正"
    )
    return_all_candidates: bool = Field(
        False,
        description="是否返回所有候选（仅Pass@K）"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "查询销售额最高的5个产品",
                "connection_id": 1,
                "reasoning_mode": "pass_at_k",
                "k_candidates": 8,
                "temperature": 0.8,
                "return_all_candidates": True
            }
        }
    )

    @field_validator("k_candidates")
    @classmethod
    def validate_k_candidates(cls, v: int) -> int:
        """Validate k_candidates is within valid range."""
        if v < 1 or v > 16:
            raise ValueError("k_candidates must be between 1 and 16")
        return v

    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v: int) -> int:
        """Validate max_iterations is within valid range."""
        if v < 1 or v > 5:
            raise ValueError("max_iterations must be between 1 and 5")
        return v


class QueryGenerateAdvancedResponse(BaseModel):
    """Schema for advanced SQL generation response."""
    sql: str = Field(..., description="生成的SQL（最佳结果）")
    reasoning_mode: str = Field(..., description="使用的推理模式")

    # Pass@K 相关字段
    candidates: Optional[List[CandidateSQL]] = Field(
        None,
        description="所有候选（可选，仅Pass@K）"
    )
    pass_at_k_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Pass@K得分"
    )

    # CheckCorrect 相关字段
    iteration_count: Optional[int] = Field(
        None,
        description="实际迭代次数"
    )
    correction_history: Optional[List[CorrectionRecord]] = Field(
        None,
        description="修正历史"
    )

    # 通用字段
    execution_time_ms: float = Field(
        ...,
        description="执行时间（毫秒）"
    )
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="置信度分数"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sql": "SELECT product_name, SUM(sales) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 5",
                "reasoning_mode": "pass_at_k",
                "candidates": [
                    {
                        "sql": "SELECT product_name, SUM(sales) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 5",
                        "is_valid": True,
                        "execution_result": [["Product A", 150000], ["Product B", 120000]],
                        "vote_count": None
                    }
                ],
                "pass_at_k_score": 0.625,
                "execution_time_ms": 4250,
                "confidence_score": 0.75
            }
        }
    )
