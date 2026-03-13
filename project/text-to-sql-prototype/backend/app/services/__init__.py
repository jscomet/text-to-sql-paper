"""Services package."""
from app.services.connection import ConnectionService
from app.services.eval_task import EvalTaskService
from app.services.evaluator import MajorityVoter, SQLEvaluator, determine_error_type
from app.services.llm import AnthropicClient, OpenAIClient, VLLMClient, get_llm_client
from app.services.nl2sql import (
    NL2SQLError,
    SQLGenerationError,
    SQLExtractionError,
    extract_sql_from_response,
    generate_sql,
    generate_sql_pass_at_k,
    generate_sql_with_check_correct,
    generate_sql_with_retry,
    get_sql_dialect,
    validate_sql_syntax,
)
from app.services.pass_at_k import (
    CandidateSQL,
    PassAtKEvaluator,
    PassAtKMetrics,
    PassAtKResult,
)
from app.services.query_history import QueryHistoryService
from app.services.schema import SchemaService
from app.services.sql_checker import (
    ErrorType,
    ExecutionCheckResult,
    SQLChecker,
    SyntaxCheckResult,
)
from app.services.sql_corrector import (
    CorrectionAttempt,
    CorrectionResult,
    SQLCorrector,
)
from app.services.sql_executor import SQLExecutorService

__all__ = [
    "OpenAIClient",
    "AnthropicClient",
    "VLLMClient",
    "get_llm_client",
    "ConnectionService",
    "SchemaService",
    "generate_sql",
    "generate_sql_with_retry",
    "generate_sql_pass_at_k",
    "generate_sql_with_check_correct",
    "extract_sql_from_response",
    "validate_sql_syntax",
    "get_sql_dialect",
    "NL2SQLError",
    "SQLGenerationError",
    "SQLExtractionError",
    "SQLExecutorService",
    "QueryHistoryService",
    "SQLEvaluator",
    "MajorityVoter",
    "determine_error_type",
    "EvalTaskService",
    # Advanced Inference
    "SQLChecker",
    "SyntaxCheckResult",
    "ExecutionCheckResult",
    "ErrorType",
    "SQLCorrector",
    "CorrectionResult",
    "CorrectionAttempt",
    "PassAtKEvaluator",
    "PassAtKResult",
    "PassAtKMetrics",
    "CandidateSQL",
]
