"""Query API routes for NL2SQL operations."""
import time
from typing import List, Optional

import sqlparse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.v1.api_keys import get_user_api_key_config
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.db_connection import DBConnection
from app.models.query_history import QueryHistory
from app.models.user import User
from app.schemas.query import (
    CandidateSQL,
    CorrectionRecord,
    QueryExecuteRequest,
    QueryExecuteResponse,
    QueryGenerateAdvancedRequest,
    QueryGenerateAdvancedResponse,
    QueryGenerateRequest,
    QueryGenerateResponse,
    QueryHistoryItem,
    QueryHistoryListResponse,
    QueryResultData,
    QueryRunRequest,
    QueryRunResponse,
    ToggleFavoriteResponse,
)
from app.services.connection import ConnectionService
from app.services.llm import get_llm_client
from app.services.nl2sql import generate_sql, get_sql_dialect, validate_sql_syntax
from app.services.prompts import build_nl2sql_prompt
from app.services.query_history import QueryHistoryService
from app.services.schema import SchemaService
from app.services.sql_executor import SQLExecutorService

logger = get_logger(__name__)
router = APIRouter(prefix="/queries", tags=["Queries"])


async def get_connection_with_access_check(
    connection_id: int,
    user_id: int,
    db: AsyncSession,
) -> DBConnection:
    """Get connection and verify user has access.

    Args:
        connection_id: Connection ID.
        user_id: User ID.
        db: Database session.

    Returns:
        DBConnection if found and accessible.

    Raises:
        HTTPException: If connection not found or access denied.
    """
    result = await db.execute(
        select(DBConnection).where(
            DBConnection.id == connection_id,
            DBConnection.user_id == user_id
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    return connection


@router.post("/generate", response_model=QueryGenerateResponse)
async def generate_sql_endpoint(
    request: QueryGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QueryGenerateResponse:
    """Generate SQL from natural language question.

    Args:
        request: Generation request with question and connection ID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Generated SQL and query ID.
    """
    start_time = time.time()

    # Get connection
    connection = await get_connection_with_access_check(
        request.connection_id, current_user.id, db
    )

    # Create query history record
    history_service = QueryHistoryService(db)
    query_record = await history_service.create_query(
        user_id=current_user.id,
        nl_question=request.question,
        connection_id=request.connection_id,
    )

    try:
        # Get schema
        engine = ConnectionService.get_db_engine(connection)
        schema_service = SchemaService()
        tables = await schema_service.get_all_schemas(engine)
        schema_text = SchemaService.build_schema_text(tables)

        # Get API key configuration for provider
        provider = request.provider or settings.llm_provider
        api_key_config = await get_user_api_key_config(
            current_user.id, provider, db, prefer_default=True
        )

        # Fall back to environment variable if no user-specific key
        if not api_key_config:
            api_key_config = {
                "api_key": settings.llm_api_key,
                "base_url": settings.llm_base_url,
                "model": settings.llm_model,
                "format_type": settings.llm_format,
            }

        # Check if API key is configured
        if not api_key_config or not api_key_config.get("api_key"):
            error_msg = f"未配置 {provider} API Key。请在系统设置中添加 API Key。"
            await history_service.update_query_result(
                query_id=query_record.id,
                execution_status="failed",
                error_message=error_msg,
            )
            return QueryGenerateResponse(
                success=False,
                query_id=query_record.id,
                question=request.question,
                error=error_msg,
                sql=None,
                explanation="",
                confidence=0.0,
                execution_time=0,
            )

        # Generate SQL
        dialect = get_sql_dialect(connection.db_type)

        # Get LLM client based on format_type
        client = get_llm_client(
            provider=provider,
            api_key=api_key_config["api_key"],
            format_type=api_key_config["format_type"],
            base_url=api_key_config["base_url"],
            model=api_key_config["model"],
        )

        generated_sql = await generate_sql(
            question=request.question,
            schema_text=schema_text,
            provider=provider,
            model_config={"model": api_key_config["model"]},
            dialect=dialect,
            api_key=api_key_config["api_key"],
            format_type=api_key_config["format_type"],
            base_url=api_key_config["base_url"],
        )

        # Format SQL
        formatted_sql = sqlparse.format(generated_sql, reindent=True, keyword_case="upper")

        # Update query record
        await history_service.update_query_result(
            query_id=query_record.id,
            generated_sql=generated_sql,
            execution_status="generated",
        )

        generation_time_ms = (time.time() - start_time) * 1000

        return QueryGenerateResponse(
            success=True,
            query_id=query_record.id,
            question=request.question,
            generated_sql=generated_sql,
            formatted_sql=formatted_sql,
            sql=generated_sql,
            explanation="",
            confidence=0.9,
            execution_time=generation_time_ms,
        )

    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        await history_service.update_query_result(
            query_id=query_record.id,
            execution_status="failed",
            error_message=str(e),
        )
        return QueryGenerateResponse(
            success=False,
            query_id=query_record.id,
            question=request.question,
            error=str(e),
            sql=None,
            explanation="",
            confidence=0.0,
            execution_time=0,
        )


@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_sql_endpoint(
    request: QueryExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QueryExecuteResponse:
    """Execute SQL query.

    Args:
        request: Execution request with SQL and connection ID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Execution results.
    """
    start_time = time.time()

    # Get connection
    connection = await get_connection_with_access_check(
        request.connection_id, current_user.id, db
    )

    # Validate SQL syntax
    if not validate_sql_syntax(request.sql):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SQL syntax"
        )

    # Create executor
    executor = SQLExecutorService(timeout_seconds=30.0)

    # Execute SQL
    result = await executor.execute_sql(
        sql=request.sql,
        db_session=db,
    )

    execution_time_ms = (time.time() - start_time) * 1000

    if result["success"]:
        # Convert object array rows to 2D array format for frontend
        columns = result["columns"]
        rows_2d = []
        for row_obj in result["rows"]:
            row_list = [row_obj.get(col) for col in columns]
            rows_2d.append(row_list)

        return QueryExecuteResponse(
            success=True,
            query_id=0,  # No history record for direct execution
            sql=request.sql,
            # Root-level fields for frontend
            columns=columns,
            rows=rows_2d,
            row_count=result["row_count"],
            execution_time=execution_time_ms,
            # Legacy fields for backward compatibility
            result=QueryResultData(
                columns=columns,
                rows=result["rows"],
                total_rows=result["row_count"],
                truncated=result.get("truncated", False),
                displayed_rows=len(result["rows"]),
            ),
            execution_time_ms=execution_time_ms,
        )
    else:
        return QueryExecuteResponse(
            success=False,
            query_id=0,
            sql=request.sql,
            error=result["error"],
            execution_time=execution_time_ms,
            execution_time_ms=execution_time_ms,
        )


@router.post("/run", response_model=QueryRunResponse)
async def run_query_endpoint(
    request: QueryRunRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QueryRunResponse:
    """Generate and execute SQL in one request.

    Args:
        request: Run request with question and connection ID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Generated SQL and execution results.
    """
    gen_start_time = time.time()

    # Get connection
    connection = await get_connection_with_access_check(
        request.connection_id, current_user.id, db
    )

    # Create query history record
    history_service = QueryHistoryService(db)
    query_record = await history_service.create_query(
        user_id=current_user.id,
        nl_question=request.question,
        connection_id=request.connection_id,
    )

    generated_sql = None
    formatted_sql = None

    try:
        # Get schema
        engine = ConnectionService.get_db_engine(connection)
        schema_service = SchemaService()
        tables = await schema_service.get_all_schemas(engine)
        schema_text = SchemaService.build_schema_text(tables)

        # Get API key configuration for provider
        provider = request.provider or settings.llm_provider
        api_key_config = await get_user_api_key_config(
            current_user.id, provider, db, prefer_default=True
        )

        # Fall back to environment variable if no user-specific key
        if not api_key_config:
            api_key_config = {
                "api_key": settings.llm_api_key,
                "base_url": settings.llm_base_url,
                "model": settings.llm_model,
                "format_type": settings.llm_format,
            }

        # Check if API key is configured
        if not api_key_config or not api_key_config.get("api_key"):
            error_msg = f"未配置 {provider} API Key。请在系统设置中添加 API Key。"
            await history_service.update_query_result(
                query_id=query_record.id,
                execution_status="failed",
                error_message=error_msg,
            )
            return QueryRunResponse(
                success=False,
                query_id=query_record.id,
                question=request.question,
                error=error_msg,
                generation_time_ms=(time.time() - gen_start_time) * 1000,
            )

        # Generate SQL
        dialect = get_sql_dialect(connection.db_type)

        generated_sql = await generate_sql(
            question=request.question,
            schema_text=schema_text,
            provider=provider,
            model_config={"model": api_key_config["model"]},
            dialect=dialect,
            api_key=api_key_config["api_key"],
            format_type=api_key_config["format_type"],
            base_url=api_key_config["base_url"],
        )

        formatted_sql = sqlparse.format(generated_sql, reindent=True, keyword_case="upper")
        generation_time_ms = (time.time() - gen_start_time) * 1000

        # Execute if requested
        if request.execute:
            exec_start_time = time.time()
            executor = SQLExecutorService(timeout_seconds=30.0)
            exec_result = await executor.execute_sql(
                sql=generated_sql,
                db_session=db,
            )
            execution_time_ms = (time.time() - exec_start_time) * 1000

            # Update query record
            if exec_result["success"]:
                await history_service.update_query_result(
                    query_id=query_record.id,
                    generated_sql=generated_sql,
                    execution_status="completed",
                    execution_time_ms=execution_time_ms,
                )

                # Convert object array rows to 2D array format for frontend
                columns = exec_result["columns"]
                rows_2d = []
                for row_obj in exec_result["rows"]:
                    row_list = [row_obj.get(col) for col in columns]
                    rows_2d.append(row_list)

                return QueryRunResponse(
                    success=True,
                    query_id=query_record.id,
                    question=request.question,
                    generated_sql=generated_sql,
                    formatted_sql=formatted_sql,
                    # Root-level fields for frontend compatibility
                    columns=columns,
                    rows=rows_2d,
                    row_count=exec_result["row_count"],
                    execution_time=execution_time_ms,
                    # Legacy result field
                    result=QueryResultData(
                        columns=columns,
                        rows=exec_result["rows"],
                        total_rows=exec_result["row_count"],
                        truncated=exec_result.get("truncated", False),
                        displayed_rows=len(exec_result["rows"]),
                    ),
                    execution_time_ms=execution_time_ms,
                    generation_time_ms=generation_time_ms,
                    sql=generated_sql,
                    explanation="",
                    confidence=0.9,
                )
            else:
                await history_service.update_query_result(
                    query_id=query_record.id,
                    generated_sql=generated_sql,
                    execution_status="failed",
                    error_message=exec_result["error"],
                )

                return QueryRunResponse(
                    success=False,
                    query_id=query_record.id,
                    question=request.question,
                    generated_sql=generated_sql,
                    formatted_sql=formatted_sql,
                    error=exec_result["error"],
                    execution_time_ms=execution_time_ms,
                    generation_time_ms=generation_time_ms,
                    sql=generated_sql,
                    explanation="",
                    confidence=0.0,
                    execution_time=execution_time_ms,
                )
        else:
            # Only generated, not executed
            await history_service.update_query_result(
                query_id=query_record.id,
                generated_sql=generated_sql,
                execution_status="generated",
            )

            return QueryRunResponse(
                success=True,
                query_id=query_record.id,
                question=request.question,
                generated_sql=generated_sql,
                formatted_sql=formatted_sql,
                generation_time_ms=generation_time_ms,
                sql=generated_sql,
                explanation="",
                confidence=0.9,
                execution_time=0,
            )

    except Exception as e:
        logger.error(f"Query run failed: {e}")
        generation_time_ms = (time.time() - gen_start_time) * 1000

        await history_service.update_query_result(
            query_id=query_record.id,
            generated_sql=generated_sql,
            execution_status="failed",
            error_message=str(e),
        )

        return QueryRunResponse(
            success=False,
            query_id=query_record.id,
            question=request.question,
            generated_sql=generated_sql,
            formatted_sql=formatted_sql,
            error=str(e),
            generation_time_ms=generation_time_ms,
            sql=generated_sql,
            explanation="",
            confidence=0.0,
            execution_time=0,
        )


@router.get("/history", response_model=QueryHistoryListResponse)
async def list_query_history(
    connection_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    favorites_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QueryHistoryListResponse:
    """List query history for the current user.

    Args:
        connection_id: Optional connection ID filter.
        limit: Maximum number of records.
        offset: Offset for pagination.
        favorites_only: Only return favorite queries.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        List of query history records.
    """
    history_service = QueryHistoryService(db)
    queries, total = await history_service.list_queries(
        user_id=current_user.id,
        connection_id=connection_id,
        limit=limit,
        offset=offset,
        favorites_only=favorites_only,
    )

    items = [QueryHistoryItem.model_validate(q) for q in queries]

    return QueryHistoryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/history/{query_id}/favorite", response_model=ToggleFavoriteResponse)
async def toggle_favorite(
    query_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ToggleFavoriteResponse:
    """Toggle favorite status for a query.

    Args:
        query_id: Query history ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Updated favorite status.
    """
    history_service = QueryHistoryService(db)
    query = await history_service.toggle_favorite(query_id, current_user.id)

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found",
        )

    return ToggleFavoriteResponse(
        success=True,
        is_favorite=query.is_favorite,
        message=f"Query {'added to' if query.is_favorite else 'removed from'} favorites",
    )


@router.delete("/history/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_query_history(
    query_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a query history record.

    Args:
        query_id: Query history ID.
        db: Database session.
        current_user: Current authenticated user.
    """
    history_service = QueryHistoryService(db)
    deleted = await history_service.delete_query(query_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found",
        )


@router.post("/generate-advanced", response_model=QueryGenerateAdvancedResponse)
async def generate_sql_advanced_endpoint(
    request: QueryGenerateAdvancedRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QueryGenerateAdvancedResponse:
    """Generate SQL using advanced inference modes.

    Supports Pass@K, CheckCorrect, MajorityVote and single mode inference.

    Args:
        request: Advanced generation request with reasoning mode and configuration.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Generated SQL with candidates, confidence score and metadata.
    """
    start_time = time.time()

    # Get connection
    connection = await get_connection_with_access_check(
        request.connection_id, current_user.id, db
    )

    try:
        # Get schema
        engine = ConnectionService.get_db_engine(connection)
        schema_service = SchemaService()
        tables = await schema_service.get_all_schemas(engine)
        schema_text = SchemaService.build_schema_text(tables)

        # Get API key configuration for provider
        provider = request.provider or settings.llm_provider
        api_key_config = await get_user_api_key_config(
            current_user.id, provider, db, prefer_default=True
        )

        # Fall back to environment variable if no user-specific key
        if not api_key_config:
            api_key_config = {
                "api_key": settings.llm_api_key,
                "base_url": settings.llm_base_url,
                "model": settings.llm_model,
                "format_type": settings.llm_format,
            }

        # Check if API key is configured
        if not api_key_config or not api_key_config.get("api_key"):
            error_msg = f"未配置 {provider} API Key。请在系统设置中添加 API Key。"
            return QueryGenerateAdvancedResponse(
                sql="",
                reasoning_mode=request.reasoning_mode,
                execution_time_ms=0,
                confidence_score=0.0,
            )

        # Build model config
        dialect = get_sql_dialect(connection.db_type)
        model_config = {
            "model": api_key_config["model"],
            "temperature": request.temperature,
        }

        # Initialize result variables
        predicted_sql = ""
        candidates: list[CandidateSQL] = []
        correction_history: list[CorrectionRecord] = []
        iteration_count = 0
        confidence = 0.9

        # Generate SQL based on reasoning mode
        if request.reasoning_mode == "single":
            # Single generation (same as /generate)
            predicted_sql = await generate_sql(
                question=request.question,
                schema_text=schema_text,
                provider=provider,
                model_config=model_config,
                dialect=dialect,
                api_key=api_key_config["api_key"],
                format_type=api_key_config["format_type"],
                base_url=api_key_config["base_url"],
            )

        elif request.reasoning_mode == "pass_at_k":
            # Pass@K: Generate K candidates, return first correct one
            k = request.k_candidates
            pred_sqls = []

            for i in range(k):
                sql = await generate_sql(
                    question=request.question,
                    schema_text=schema_text,
                    provider=provider,
                    model_config=model_config,
                    dialect=dialect,
                    api_key=api_key_config["api_key"],
                    format_type=api_key_config["format_type"],
                    base_url=api_key_config["base_url"],
                )
                pred_sqls.append(sql)

            # Evaluate each candidate
            valid_count = 0
            for sql in pred_sqls:
                # Execute to check validity
                executor = SQLExecutorService(timeout_seconds=10.0)
                exec_result = await executor.execute_sql(
                    sql=sql,
                    db_session=db,
                )
                is_valid = exec_result["success"]
                if is_valid:
                    valid_count += 1

                candidate = CandidateSQL(
                    sql=sql,
                    is_valid=is_valid,
                    execution_result=exec_result.get("rows") if is_valid else None,
                    vote_count=None,
                )
                candidates.append(candidate)

                # Use first valid SQL as the result
                if is_valid and not predicted_sql:
                    predicted_sql = sql

            # If no valid SQL, use the first one
            if not predicted_sql and pred_sqls:
                predicted_sql = pred_sqls[0]

            # Calculate confidence based on valid ratio
            confidence = valid_count / k if k > 0 else 0.0

            # If not returning all candidates, clear the list
            if not request.return_all_candidates:
                candidates = []

        elif request.reasoning_mode == "majority_vote":
            # MajorityVote: Generate K candidates, vote for best
            k = request.k_candidates
            pred_sqls = []

            for i in range(k):
                sql = await generate_sql(
                    question=request.question,
                    schema_text=schema_text,
                    provider=provider,
                    model_config=model_config,
                    dialect=dialect,
                    api_key=api_key_config["api_key"],
                    format_type=api_key_config["format_type"],
                    base_url=api_key_config["base_url"],
                )
                pred_sqls.append(sql)

            # Execute and group by results for voting
            from app.services.evaluator import MajorityVoter

            predicted_sql, voting_info = await MajorityVoter.majority_voting(
                engine=engine,
                pred_sqls=pred_sqls,
                timeout=30,
            )

            # Build candidates with vote counts
            for sql in pred_sqls:
                vote_count = voting_info.get("votes", {}).get(sql, 0)
                is_winner = sql == predicted_sql

                candidate = CandidateSQL(
                    sql=sql,
                    is_valid=True,  # All were executed successfully
                    execution_result=None,
                    vote_count=vote_count,
                )
                candidates.append(candidate)

            confidence = voting_info.get("confidence", 0.9)

        elif request.reasoning_mode == "check_correct":
            # CheckCorrect: Iterative generation with self-correction
            max_iter = request.max_iterations
            enable_correction = request.enable_self_correction

            for iteration in range(max_iter):
                iteration_count = iteration + 1

                sql = await generate_sql(
                    question=request.question,
                    schema_text=schema_text,
                    provider=provider,
                    model_config=model_config,
                    dialect=dialect,
                    api_key=api_key_config["api_key"],
                    format_type=api_key_config["format_type"],
                    base_url=api_key_config["base_url"],
                )

                # Execute to check validity
                executor = SQLExecutorService(timeout_seconds=10.0)
                exec_result = await executor.execute_sql(
                    sql=sql,
                    db_session=db,
                )
                is_valid = exec_result["success"]

                error_type = None
                error_message = None
                correction_prompt = None

                if not is_valid:
                    error_type = "execution_error"
                    error_message = exec_result.get("error", "Unknown error")

                    if enable_correction and iteration < max_iter - 1:
                        correction_prompt = f"The SQL execution failed with error: {error_message}. Please fix it."
                        # Add correction context to model_config for next iteration
                        if "messages" not in model_config:
                            model_config["messages"] = []
                        model_config["messages"].append({
                            "role": "user",
                            "content": correction_prompt,
                        })

                # Record correction history
                correction_record = CorrectionRecord(
                    iteration=iteration + 1,
                    sql=sql,
                    error_type=error_type,
                    error_message=error_message,
                    correction_prompt=correction_prompt,
                )
                correction_history.append(correction_record)

                if is_valid:
                    predicted_sql = sql
                    break

            # If no valid SQL found, use the last one
            if not predicted_sql and correction_history:
                predicted_sql = correction_history[-1].sql

            # Calculate confidence based on iterations needed
            if predicted_sql and is_valid:
                confidence = 0.95
            else:
                confidence = max(0.5, 1.0 - (iteration_count * 0.15))

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid reasoning mode: {request.reasoning_mode}",
            )

        execution_time_ms = (time.time() - start_time) * 1000

        # Format the final SQL
        if predicted_sql:
            predicted_sql = sqlparse.format(predicted_sql, reindent=True, keyword_case="upper")

        return QueryGenerateAdvancedResponse(
            sql=predicted_sql,
            reasoning_mode=request.reasoning_mode,
            candidates=candidates if candidates else None,
            pass_at_k_score=confidence if request.reasoning_mode == "pass_at_k" else None,
            iteration_count=iteration_count if request.reasoning_mode == "check_correct" else None,
            correction_history=correction_history if correction_history else None,
            execution_time_ms=execution_time_ms,
            confidence_score=confidence,
        )

    except Exception as e:
        logger.error(f"Advanced SQL generation failed: {e}")
        execution_time_ms = (time.time() - start_time) * 1000

        return QueryGenerateAdvancedResponse(
            sql="",
            reasoning_mode=request.reasoning_mode,
            execution_time_ms=execution_time_ms,
            confidence_score=0.0,
            error=str(e),
        )
# DEEPSEEK_FIXED_20240313
