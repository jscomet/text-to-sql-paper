"""Evaluation service for SQL correctness verification and majority voting."""
import asyncio
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import get_logger
from app.services.connection import ConnectionService

logger = get_logger(__name__)


class SQLEvaluator:
    """SQL evaluation service for comparing predicted and gold SQL results."""

    @staticmethod
    async def execute_sql_safely(
        engine: AsyncEngine,
        sql: str,
        timeout: int = 30,
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]], Optional[str]]:
        """Execute SQL with timeout and error handling.

        Args:
            engine: SQLAlchemy async engine.
            sql: SQL query to execute.
            timeout: Execution timeout in seconds.

        Returns:
            Tuple of (success, results, error_message).
        """
        try:
            async with engine.connect() as conn:
                # Set timeout for SQLite
                if "sqlite" in str(engine.url):
                    await conn.execute(text("PRAGMA busy_timeout = 30000"))

                # Execute with timeout
                result = await asyncio.wait_for(
                    conn.execute(text(sql)),
                    timeout=timeout,
                )

                # Fetch results
                rows = result.mappings().all()
                results = [dict(row) for row in rows]
                return True, results, None

        except asyncio.TimeoutError:
            return False, None, f"SQL execution timeout after {timeout} seconds"
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def normalize_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize query results for comparison.

        Args:
            results: List of result dictionaries.

        Returns:
            Normalized results sorted for comparison.
        """
        if not results:
            return []

        # Convert all values to strings for comparison
        normalized = []
        for row in results:
            normalized_row = {}
            for key, value in row.items():
                # Handle None values
                if value is None:
                    normalized_row[key.lower()] = "NULL"
                # Handle floats with precision
                elif isinstance(value, float):
                    normalized_row[key.lower()] = f"{value:.6f}"
                else:
                    normalized_row[key.lower()] = str(value)
            normalized.append(normalized_row)

        # Sort by all columns for consistent comparison
        if normalized:
            sort_keys = sorted(normalized[0].keys())
            normalized.sort(key=lambda x: [x.get(k, "") for k in sort_keys])

        return normalized

    @staticmethod
    async def compare_sql_results(
        engine: AsyncEngine,
        pred_sql: str,
        gold_sql: str,
        timeout: int = 30,
    ) -> Tuple[bool, Optional[str]]:
        """Compare predicted SQL results with gold SQL using EXCEPT.

        Args:
            engine: SQLAlchemy async engine.
            pred_sql: Predicted SQL query.
            gold_sql: Gold/reference SQL query.
            timeout: Execution timeout in seconds.

        Returns:
            Tuple of (is_correct, error_message).
        """
        try:
            # First, check if both SQLs can be executed
            pred_success, pred_results, pred_error = await SQLEvaluator.execute_sql_safely(
                engine, pred_sql, timeout
            )

            if not pred_success:
                return False, f"Predicted SQL error: {pred_error}"

            gold_success, gold_results, gold_error = await SQLEvaluator.execute_sql_safely(
                engine, gold_sql, timeout
            )

            if not gold_success:
                return False, f"Gold SQL error: {gold_error}"

            # Normalize and compare results
            pred_normalized = SQLEvaluator.normalize_results(pred_results or [])
            gold_normalized = SQLEvaluator.normalize_results(gold_results or [])

            # Compare results
            if len(pred_normalized) != len(gold_normalized):
                return False, f"Row count mismatch: {len(pred_normalized)} vs {len(gold_normalized)}"

            # Compare each row
            for pred_row, gold_row in zip(pred_normalized, gold_normalized):
                if pred_row != gold_row:
                    return False, "Result content mismatch"

            return True, None

        except Exception as e:
            return False, f"Comparison error: {str(e)}"

    @staticmethod
    async def compare_sql_results_except(
        engine: AsyncEngine,
        pred_sql: str,
        gold_sql: str,
        timeout: int = 30,
    ) -> Tuple[bool, Optional[str]]:
        """Compare SQL results using EXCEPT operator (more accurate).

        This method uses SQL EXCEPT to compare results, which handles
        column order and sorting automatically.

        Args:
            engine: SQLAlchemy async engine.
            pred_sql: Predicted SQL query.
            gold_sql: Gold/reference SQL query.
            timeout: Execution timeout in seconds.

        Returns:
            Tuple of (is_correct, error_message).
        """
        try:
            async with engine.connect() as conn:
                # Check pred EXCEPT gold
                except_sql_1 = f"""
                    SELECT * FROM ({pred_sql}) AS pred
                    EXCEPT
                    SELECT * FROM ({gold_sql}) AS gold
                """

                # Check gold EXCEPT pred
                except_sql_2 = f"""
                    SELECT * FROM ({gold_sql}) AS gold
                    EXCEPT
                    SELECT * FROM ({pred_sql}) AS pred
                """

                # Execute both EXCEPT queries
                result1 = await asyncio.wait_for(
                    conn.execute(text(except_sql_1)),
                    timeout=timeout,
                )
                diff1 = result1.fetchall()

                result2 = await asyncio.wait_for(
                    conn.execute(text(except_sql_2)),
                    timeout=timeout,
                )
                diff2 = result2.fetchall()

                # If both EXCEPT queries return empty, results are identical
                if len(diff1) == 0 and len(diff2) == 0:
                    return True, None
                else:
                    return False, f"Results differ: {len(diff1)} rows in pred not in gold, {len(diff2)} rows in gold not in pred"

        except asyncio.TimeoutError:
            return False, f"SQL execution timeout after {timeout} seconds"
        except Exception as e:
            return False, f"EXCEPT comparison error: {str(e)}"


def determine_error_type(
    execution_success: bool,
    is_correct: Optional[bool],
    execution_error: Optional[str],
) -> Optional[str]:
    """Determine the error type for an evaluation result.

    Args:
        execution_success: Whether SQL execution succeeded.
        is_correct: Whether the result is correct (None if not compared).
        execution_error: Error message from execution.

    Returns:
        Error type string or None.
    """
    if not execution_success:
        if execution_error:
            error_lower = execution_error.lower()
            if "syntax" in error_lower:
                return "syntax_error"
            elif "timeout" in error_lower or "timed out" in error_lower:
                return "timeout"
            elif "permission" in error_lower or "access" in error_lower:
                return "permission_error"
            elif "table" in error_lower and ("not exist" in error_lower or "not found" in error_lower):
                return "table_not_found"
            elif "column" in error_lower and ("not exist" in error_lower or "not found" in error_lower):
                return "column_not_found"
            else:
                return "execution_error"
        return "execution_error"

    if is_correct is False:
        return "wrong_result"

    return None


class MajorityVoter:
    """Majority voting algorithm for selecting best SQL from multiple candidates."""

    @staticmethod
    async def execute_and_hash(
        engine: AsyncEngine,
        sql: str,
        timeout: int = 30,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Execute SQL and return hash of results.

        Args:
            engine: SQLAlchemy async engine.
            sql: SQL query.
            timeout: Execution timeout.

        Returns:
            Tuple of (result_hash, error_message).
        """
        success, results, error = await SQLEvaluator.execute_sql_safely(
            engine, sql, timeout
        )

        if not success:
            return None, error

        # Normalize and create hashable representation
        normalized = SQLEvaluator.normalize_results(results or [])
        result_str = str(normalized)
        return result_str, None

    @staticmethod
    async def majority_voting(
        engine: AsyncEngine,
        pred_sqls: List[str],
        timeout: int = 30,
    ) -> Tuple[str, int, Dict[str, Any]]:
        """Select best SQL using majority voting.

        Args:
            engine: SQLAlchemy async engine.
            pred_sqls: List of candidate SQL queries.
            timeout: Execution timeout per SQL.

        Returns:
            Tuple of (selected_sql, vote_count, details).
        """
        if not pred_sqls:
            raise ValueError("Empty SQL list for majority voting")

        if len(pred_sqls) == 1:
            return pred_sqls[0], 1, {"votes": {pred_sqls[0]: 1}, "total": 1}

        # Execute all SQLs and collect results
        results_map: Dict[str, List[str]] = {}  # result_hash -> list of SQLs
        errors: Dict[str, str] = {}

        for i, sql in enumerate(pred_sqls):
            result_hash, error = await MajorityVoter.execute_and_hash(
                engine, sql, timeout
            )

            if error:
                errors[f"sql_{i}"] = error
                continue

            if result_hash not in results_map:
                results_map[result_hash] = []
            results_map[result_hash].append(sql)

        if not results_map:
            # All SQLs failed, return the first one with error info
            return pred_sqls[0], 0, {
                "votes": {},
                "total": len(pred_sqls),
                "errors": errors,
                "note": "All SQLs failed execution",
            }

        # Find the result with most votes
        best_result_hash = max(results_map.keys(), key=lambda k: len(results_map[k]))
        best_sqls = results_map[best_result_hash]
        vote_count = len(best_sqls)

        # Return the first SQL with the most votes
        selected_sql = best_sqls[0]

        # Build vote statistics
        votes = {}
        for result_hash, sqls in results_map.items():
            # Use first SQL as representative
            votes[sqls[0]] = len(sqls)

        details = {
            "votes": votes,
            "total": len(pred_sqls),
            "successful": sum(len(sqls) for sqls in results_map.values()),
            "failed": len(errors),
            "errors": errors if errors else None,
        }

        return selected_sql, vote_count, details

    @staticmethod
    async def majority_voting_with_confidence(
        engine: AsyncEngine,
        pred_sqls: List[str],
        confidence_scores: Optional[List[float]] = None,
        timeout: int = 30,
    ) -> Tuple[str, float, Dict[str, Any]]:
        """Select best SQL using weighted majority voting.

        Args:
            engine: SQLAlchemy async engine.
            pred_sqls: List of candidate SQL queries.
            confidence_scores: Optional confidence scores for each SQL.
            timeout: Execution timeout per SQL.

        Returns:
            Tuple of (selected_sql, confidence, details).
        """
        if not pred_sqls:
            raise ValueError("Empty SQL list for majority voting")

        if confidence_scores and len(confidence_scores) != len(pred_sqls):
            raise ValueError("Confidence scores length must match SQL count")

        # Execute all SQLs and collect results with weights
        result_weights: Dict[str, float] = {}  # result_hash -> total weight
        sql_by_hash: Dict[str, str] = {}  # result_hash -> representative SQL
        errors: Dict[str, str] = {}

        for i, sql in enumerate(pred_sqls):
            weight = confidence_scores[i] if confidence_scores else 1.0
            result_hash, error = await MajorityVoter.execute_and_hash(
                engine, sql, timeout
            )

            if error:
                errors[f"sql_{i}"] = error
                continue

            if result_hash not in result_weights:
                result_weights[result_hash] = 0.0
                sql_by_hash[result_hash] = sql
            result_weights[result_hash] += weight

        if not result_weights:
            # All SQLs failed
            return pred_sqls[0], 0.0, {
                "votes": {},
                "total": len(pred_sqls),
                "errors": errors,
                "note": "All SQLs failed execution",
            }

        # Find the result with highest total weight
        best_result_hash = max(result_weights.keys(), key=lambda k: result_weights[k])
        selected_sql = sql_by_hash[best_result_hash]
        total_weight = sum(result_weights.values())
        confidence = result_weights[best_result_hash] / total_weight if total_weight > 0 else 0

        details = {
            "votes": {sql_by_hash[k]: v for k, v in result_weights.items()},
            "total": len(pred_sqls),
            "successful": len(result_weights),
            "failed": len(errors),
            "errors": errors if errors else None,
        }

        return selected_sql, confidence, details
