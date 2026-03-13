# 高级推理功能 - 技术设计文档

## 1. 架构设计

### 1.1 组件关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Advanced Inference Module                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  PassAtK        │    │  SQLChecker     │    │  SQLCorrector   │         │
│  │  Evaluator      │    │                 │    │                 │         │
│  │                 │    │  ┌───────────┐  │    │  ┌───────────┐  │         │
│  │  - generate_k() │    │  │  Syntax   │  │    │  │  Error    │  │         │
│  │  - evaluate()   │    │  │  Checker  │  │    │  │  Analyzer │  │         │
│  │  - aggregate()  │    │  └───────────┘  │    │  └───────────┘  │         │
│  │                 │    │  ┌───────────┐  │    │  ┌───────────┐  │         │
│  └────────┬────────┘    │  │  Execution│  │    │  │  Prompt   │  │         │
│           │             │  │  Checker  │  │    │  │  Builder  │  │         │
│           │             │  └───────────┘  │    │  └───────────┘  │         │
│           │             └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                  │
│           │                      └──────────┬───────────┘                  │
│           │                                 │                              │
│           │                    ┌────────────▼────────────┐                 │
│           │                    │   CheckCorrectPipeline  │                 │
│           │                    │                         │                 │
│           │                    │  ┌─────────────────┐    │                 │
│           └───────────────────►│  │  Iteration Loop │    │                 │
│                                │  │  - Generate     │    │                 │
│                                │  │  - Check        │    │                 │
│                                │  │  - Correct      │    │                 │
│                                │  └─────────────────┘    │                 │
│                                └────────────┬────────────┘                 │
│                                             │                              │
└─────────────────────────────────────────────┼──────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Existing System Integration                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │   nl2sql.py  │◄─────┤  Advanced    │◄─────┤  eval_tasks  │              │
│  │              │      │  Inference   │      │   .py        │              │
│  │ generate_sql │      │   Module     │      │              │              │
│  │   _retry()   │      │              │      │ _run_eval()  │              │
│  └──────────────┘      └──────┬───────┘      └──────────────┘              │
│                               │                                             │
│                               ▼                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │ evaluator.py │◄─────┤  Majority    │      │   API Layer  │              │
│  │              │      │   Voter      │      │              │              │
│  │ majority_    │      │              │      │ /queries.py  │              │
│  │  voting()    │      │              │      │ /evaluations │              │
│  └──────────────┘      └──────────────┘      └──────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 与现有系统的集成点

| 组件 | 集成方式 | 说明 |
|------|----------|------|
| `nl2sql.py` | 复用 `generate_sql()` | 基础SQL生成功能，用于Generate阶段 |
| `evaluator.py` | 复用 `majority_voting()` | 多数投票算法，用于Pass@K结果聚合 |
| `eval_tasks.py` | 扩展 `_run_evaluation()` | 新增推理模式分支处理 |
| `models/eval_task.py` | 新增字段 | 支持高级推理配置存储 |
| `models/eval_result.py` | 新增字段 | 支持详细结果存储 |
| `api/v1/queries.py` | 新增端点 | 提供高级查询接口 |
| `api/v1/evaluations.py` | 扩展端点 | 支持高级评测模式 |

---

## 2. 数据模型设计

### 2.1 EvalTask 模型扩展

```python
# backend/app/models/eval_task.py

from typing import Optional
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

class EvalTask(Base):
    """Evaluation task model with advanced inference support."""

    # ... 现有字段保持不变 ...

    # ==================== 新增字段 ====================

    # Pass@K 配置
    sampling_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=1,
        comment="Pass@K 的 K 值，表示采样数量"
    )

    # Check-Correct 配置
    max_iterations: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=1,
        comment="Generate-Check-Correct 最大迭代次数"
    )
    correction_strategy: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="none",
        comment="修正策略: none, self_correction, execution_feedback"
    )

    # 推理模式
    reasoning_mode: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="greedy_search",
        comment="推理模式: greedy_search, pass_at_k, check_correct, combined"
    )

    # 温度参数（用于控制采样随机性）
    temperature: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0,
        comment="采样温度，用于Pass@K生成"
    )
```

### 2.2 EvalResult 模型扩展

```python
# backend/app/models/eval_result.py

from typing import Optional, Dict, List
from sqlalchemy import JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

class EvalResult(Base):
    """Evaluation result model with advanced inference details."""

    # ... 现有字段保持不变 ...

    # ==================== 新增字段 ====================

    # Pass@K 结果
    candidate_sqls: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True,
        comment="所有候选SQL（Pass@K生成的K个候选）"
    )

    # Check-Correct 结果
    iteration_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="实际迭代次数（Check-Correct完成时的迭代数）"
    )

    correction_history: Mapped[Optional[List[Dict]]] = mapped_column(
        JSON, nullable=True,
        comment="修正历史记录，包含每次迭代的SQL和错误信息"
    )

    # 置信度分数
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="置信度分数（Pass@K通过率或投票置信度）"
    )

    # 详细执行信息
    execution_details: Mapped[Optional[Dict]] = mapped_column(
        JSON, nullable=True,
        comment="详细执行信息，包含每个候选的执行结果"
    )
```

### 2.3 数据字典

#### EvalTask 新增字段

| 字段名 | 类型 | 默认值 | 说明 | 示例值 |
|--------|------|--------|------|--------|
| `sampling_count` | Integer | 1 | Pass@K的K值 | 8, 16, 32 |
| `max_iterations` | Integer | 1 | 最大迭代次数 | 3, 5 |
| `correction_strategy` | String(50) | "none" | 修正策略类型 | "self_correction", "execution_feedback" |
| `reasoning_mode` | String(50) | "greedy_search" | 推理模式 | "pass_at_k", "check_correct", "combined" |
| `temperature` | Float | 0.0 | 采样温度 | 0.7, 0.8 |

#### EvalResult 新增字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `candidate_sqls` | JSON | 候选SQL列表 | `["SELECT * FROM users", "SELECT id FROM users"]` |
| `iteration_count` | Integer | 实际迭代次数 | 2 |
| `correction_history` | JSON | 修正历史 | `[{"iteration": 1, "sql": "...", "error": "..."}]` |
| `confidence_score` | Float | 置信度分数 | 0.75 |
| `execution_details` | JSON | 执行详情 | `{"candidates": [{"sql": "...", "success": true}]}` |

#### correction_history 结构示例

```json
[
  {
    "iteration": 1,
    "sql": "SELECT name FROM users WHERE age > ",
    "error_type": "syntax_error",
    "error_message": "Syntax error at end of input",
    "correction_prompt": "...",
    "corrected_sql": "SELECT name FROM users WHERE age > 18"
  },
  {
    "iteration": 2,
    "sql": "SELECT name FROM users WHERE age > 18",
    "error_type": null,
    "error_message": null,
    "execution_result": "success",
    "is_correct": true
  }
]
```

---

## 3. 核心类设计

### 3.1 SQLChecker 类

```python
# backend/app/services/sql_checker.py

from enum import Enum
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncEngine

class ErrorType(Enum):
    """SQL错误类型枚举."""
    SYNTAX_ERROR = "syntax_error"
    TABLE_NOT_FOUND = "table_not_found"
    COLUMN_NOT_FOUND = "column_not_found"
    TYPE_MISMATCH = "type_mismatch"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT = "timeout"
    EXECUTION_ERROR = "execution_error"
    SEMANTIC_ERROR = "semantic_error"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """SQL检查结果."""
    is_valid: bool
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    execution_success: bool = False
    execution_result: Optional[Any] = None
    execution_time_ms: Optional[float] = None
    suggestions: Optional[list] = None


class SQLChecker:
    """SQL正确性检查器，提供语法和执行检查."""

    @staticmethod
    def check_syntax(sql: str, dialect: str = "mysql") -> CheckResult:
        """检查SQL语法正确性.

        Args:
            sql: 待检查的SQL语句
            dialect: SQL方言 (mysql, postgresql, sqlite)

        Returns:
            CheckResult 包含检查结果
        """
        # 使用 sqlparse 或 sqlglot 进行语法解析
        # 返回语法检查结果
        pass

    @staticmethod
    async def check_execution(
        engine: AsyncEngine,
        sql: str,
        gold_sql: Optional[str] = None,
        timeout: int = 30
    ) -> CheckResult:
        """执行SQL并检查结果.

        Args:
            engine: 数据库引擎
            sql: 待执行的SQL
            gold_sql: 标准答案SQL（用于结果对比）
            timeout: 执行超时时间

        Returns:
            CheckResult 包含执行结果
        """
        # 在只读事务中执行SQL
        # 对比结果（如果提供gold_sql）
        # 返回执行结果
        pass

    @staticmethod
    def classify_error(error_message: str) -> ErrorType:
        """根据错误消息分类错误类型.

        Args:
            error_message: 错误消息

        Returns:
            ErrorType 错误类型
        """
        error_lower = error_message.lower()

        if "syntax" in error_lower:
            return ErrorType.SYNTAX_ERROR
        elif "table" in error_lower and ("not exist" in error_lower or "not found" in error_lower):
            return ErrorType.TABLE_NOT_FOUND
        elif "column" in error_lower and ("not exist" in error_lower or "not found" in error_lower):
            return ErrorType.COLUMN_NOT_FOUND
        elif "timeout" in error_lower or "timed out" in error_lower:
            return ErrorType.TIMEOUT
        elif "permission" in error_lower or "access" in error_lower:
            return ErrorType.PERMISSION_ERROR
        else:
            return ErrorType.UNKNOWN

    @staticmethod
    def get_suggestions(error_type: ErrorType, sql: str, schema: str) -> list:
        """根据错误类型提供修正建议.

        Args:
            error_type: 错误类型
            sql: 原始SQL
            schema: 数据库Schema

        Returns:
            建议列表
        """
        # 根据错误类型返回针对性的修正建议
        pass
```

### 3.2 SQLCorrector 类

```python
# backend/app/services/sql_corrector.py

from dataclasses import dataclass
from typing import Optional
from app.services.sql_checker import CheckResult, ErrorType


@dataclass
class CorrectionResult:
    """SQL修正结果."""
    corrected_sql: str
    success: bool
    correction_prompt: str
    raw_response: str
    iteration: int


class SQLCorrector:
    """SQL修正器，基于错误类型生成修正后的SQL."""

    CORRECTION_TEMPLATES = {
        ErrorType.SYNTAX_ERROR: """
The following SQL query has a syntax error:

Original Question: {question}
Database Schema:
{schema}

Failed SQL:
```sql
{failed_sql}
```

Error: {error_message}

Please correct the SQL syntax. Common issues include:
- Missing or extra parentheses
- Incorrect keyword order
- Unclosed quotes
- Missing table aliases

Provide ONLY the corrected SQL query without explanation.
""",
        ErrorType.TABLE_NOT_FOUND: """
The following SQL query references a non-existent table:

Original Question: {question}
Database Schema:
{schema}

Failed SQL:
```sql
{failed_sql}
```

Error: {error_message}

Available tables in schema: {available_tables}

Please correct the table names based on the schema.
Provide ONLY the corrected SQL query without explanation.
""",
        ErrorType.COLUMN_NOT_FOUND: """
The following SQL query references a non-existent column:

Original Question: {question}
Database Schema:
{schema}

Failed SQL:
```sql
{failed_sql}
```

Error: {error_message}

Please check column names and table aliases.
Provide ONLY the corrected SQL query without explanation.
""",
        ErrorType.EXECUTION_ERROR: """
The following SQL query failed during execution:

Original Question: {question}
Database Schema:
{schema}

Failed SQL:
```sql
{failed_sql}
```

Error: {error_message}

Please analyze the error and provide a corrected SQL query.
Provide ONLY the corrected SQL query without explanation.
""",
    }

    @staticmethod
    def build_correction_prompt(
        question: str,
        schema: str,
        failed_sql: str,
        check_result: CheckResult,
        iteration: int,
        available_tables: Optional[list] = None
    ) -> str:
        """构建修正提示词.

        Args:
            question: 原始问题
            schema: 数据库Schema
            failed_sql: 失败的SQL
            check_result: 检查结果
            iteration: 当前迭代次数
            available_tables: 可用表列表

        Returns:
            修正提示词
        """
        error_type = check_result.error_type or ErrorType.UNKNOWN

        template = SQLCorrector.CORRECTION_TEMPLATES.get(
            error_type,
            SQLCorrector.CORRECTION_TEMPLATES[ErrorType.EXECUTION_ERROR]
        )

        return template.format(
            question=question,
            schema=schema,
            failed_sql=failed_sql,
            error_message=check_result.error_message,
            available_tables=available_tables or "",
            iteration=iteration
        )

    @staticmethod
    def parse_correction_response(response: str) -> CorrectionResult:
        """解析LLM的修正响应.

        Args:
            response: LLM原始响应

        Returns:
            CorrectionResult 修正结果
        """
        # 从响应中提取SQL
        # 使用与 nl2sql.py 相同的 extract_sql_from_response 逻辑
        from app.services.nl2sql import extract_sql_from_response

        corrected_sql = extract_sql_from_response(response)
        success = bool(corrected_sql)

        return CorrectionResult(
            corrected_sql=corrected_sql,
            success=success,
            correction_prompt="",  # 由调用方填充
            raw_response=response,
            iteration=0  # 由调用方填充
        )
```

### 3.3 PassAtKEvaluator 类

```python
# backend/app/services/pass_at_k.py

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncEngine

from app.services.nl2sql import generate_sql
from app.services.evaluator import SQLEvaluator


@dataclass
class PassAtKResult:
    """Pass@K评估结果."""
    k: int
    candidates: List[str]
    passed_count: int
    pass_at_k: float
    best_sql: Optional[str]
    execution_results: List[Dict[str, Any]]
    generation_time_ms: float
    evaluation_time_ms: float


class PassAtKEvaluator:
    """Pass@K评估器，生成K个候选并评估通过率."""

    def __init__(
        self,
        provider: str,
        model_config: Dict[str, Any],
        api_key: Optional[str] = None,
        format_type: str = "openai",
        base_url: Optional[str] = None
    ):
        self.provider = provider
        self.model_config = model_config
        self.api_key = api_key
        self.format_type = format_type
        self.base_url = base_url

    async def generate_candidates(
        self,
        question: str,
        schema_text: str,
        k: int,
        temperature: float = 0.8,
        dialect: str = "mysql"
    ) -> List[str]:
        """生成K个候选SQL.

        Args:
            question: 自然语言问题
            schema_text: Schema文本
            k: 候选数量
            temperature: 采样温度
            dialect: SQL方言

        Returns:
            K个候选SQL列表
        """
        # 使用较高的temperature生成多样化的候选
        candidates = []

        # 并行生成K个候选
        tasks = [
            generate_sql(
                question=question,
                schema_text=schema_text,
                provider=self.provider,
                model_config={
                    **self.model_config,
                    "temperature": temperature,
                },
                dialect=dialect,
                api_key=self.api_key,
                format_type=self.format_type,
                base_url=self.base_url,
            )
            for _ in range(k)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            candidates.append(result)

        return candidates

    async def evaluate_candidates(
        self,
        engine: AsyncEngine,
        candidates: List[str],
        gold_sql: str,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """评估候选SQL.

        Args:
            engine: 数据库引擎
            candidates: 候选SQL列表
            gold_sql: 标准答案SQL
            timeout: 执行超时

        Returns:
            每个候选的评估结果
        """
        results = []

        for sql in candidates:
            is_correct, error = await SQLEvaluator.compare_sql_results_except(
                engine=engine,
                pred_sql=sql,
                gold_sql=gold_sql,
                timeout=timeout
            )

            results.append({
                "sql": sql,
                "is_correct": is_correct,
                "error": error,
            })

        return results

    async def evaluate(
        self,
        engine: AsyncEngine,
        question: str,
        schema_text: str,
        gold_sql: str,
        k: int = 8,
        temperature: float = 0.8,
        dialect: str = "mysql",
        timeout: int = 30
    ) -> PassAtKResult:
        """执行完整的Pass@K评估.

        Args:
            engine: 数据库引擎
            question: 自然语言问题
            schema_text: Schema文本
            gold_sql: 标准答案SQL
            k: 候选数量
            temperature: 采样温度
            dialect: SQL方言
            timeout: 执行超时

        Returns:
            PassAtKResult 评估结果
        """
        import time

        # 生成候选
        gen_start = time.time()
        candidates = await self.generate_candidates(
            question, schema_text, k, temperature, dialect
        )
        gen_time = (time.time() - gen_start) * 1000

        # 评估候选
        eval_start = time.time()
        execution_results = await self.evaluate_candidates(
            engine, candidates, gold_sql, timeout
        )
        eval_time = (time.time() - eval_start) * 1000

        # 计算Pass@K
        passed_count = sum(1 for r in execution_results if r["is_correct"])
        pass_at_k = passed_count / len(candidates) if candidates else 0

        # 选择最佳SQL（第一个通过的）
        best_sql = None
        for r in execution_results:
            if r["is_correct"]:
                best_sql = r["sql"]
                break

        return PassAtKResult(
            k=k,
            candidates=candidates,
            passed_count=passed_count,
            pass_at_k=pass_at_k,
            best_sql=best_sql,
            execution_results=execution_results,
            generation_time_ms=gen_time,
            evaluation_time_ms=eval_time
        )

    @staticmethod
    def calculate_metrics(results: List[PassAtKResult]) -> Dict[str, float]:
        """计算Pass@K指标.

        Args:
            results: Pass@K结果列表

        Returns:
            指标字典
        """
        if not results:
            return {}

        total = len(results)

        return {
            "avg_pass_at_k": sum(r.pass_at_k for r in results) / total,
            "pass_at_1": sum(1 for r in results if r.pass_at_k >= 1/total) / total,
            "any_pass": sum(1 for r in results if r.passed_count > 0) / total,
            "avg_generation_time_ms": sum(r.generation_time_ms for r in results) / total,
            "avg_evaluation_time_ms": sum(r.evaluation_time_ms for r in results) / total,
        }
```

### 3.4 CheckCorrectPipeline 类

```python
# backend/app/services/check_correct_pipeline.py

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncEngine

from app.services.nl2sql import generate_sql
from app.services.sql_checker import SQLChecker, CheckResult
from app.services.sql_corrector import SQLCorrector, CorrectionResult
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """管道执行结果."""
    success: bool
    final_sql: Optional[str]
    iterations: int
    correction_history: List[Dict[str, Any]]
    total_time_ms: float
    error: Optional[str] = None


@dataclass
class IterationRecord:
    """单次迭代记录."""
    iteration: int
    sql: str
    check_result: CheckResult
    correction_result: Optional[CorrectionResult] = None


class CheckCorrectPipeline:
    """Generate-Check-Correct 迭代管道."""

    def __init__(
        self,
        provider: str,
        model_config: Dict[str, Any],
        api_key: Optional[str] = None,
        format_type: str = "openai",
        base_url: Optional[str] = None,
        max_iterations: int = 3,
        dialect: str = "mysql"
    ):
        self.provider = provider
        self.model_config = model_config
        self.api_key = api_key
        self.format_type = format_type
        self.base_url = base_url
        self.max_iterations = max_iterations
        self.dialect = dialect

        self.history: List[IterationRecord] = []

    async def run(
        self,
        question: str,
        schema: str,
        engine: AsyncEngine,
        gold_sql: Optional[str] = None
    ) -> PipelineResult:
        """运行Check-Correct管道.

        Args:
            question: 自然语言问题
            schema: 数据库Schema
            engine: 数据库引擎
            gold_sql: 标准答案SQL（可选，用于验证）

        Returns:
            PipelineResult 执行结果
        """
        import time
        start_time = time.time()

        current_sql = None

        for iteration in range(1, self.max_iterations + 1):
            logger.debug(f"Check-Correct iteration {iteration}/{self.max_iterations}")

            # Generate 或 Correct
            if iteration == 1:
                # 第一次迭代：生成SQL
                current_sql = await self._generate(question, schema)
            else:
                # 后续迭代：基于上一次的错误进行修正
                last_record = self.history[-1]
                current_sql = await self._correct(
                    question=question,
                    schema=schema,
                    failed_sql=last_record.sql,
                    check_result=last_record.check_result,
                    iteration=iteration
                )

            if not current_sql:
                return PipelineResult(
                    success=False,
                    final_sql=None,
                    iterations=iteration,
                    correction_history=self._build_history(),
                    total_time_ms=(time.time() - start_time) * 1000,
                    error="Failed to generate or correct SQL"
                )

            # Check
            check_result = await self._check(engine, current_sql, gold_sql)

            # 记录本次迭代
            record = IterationRecord(
                iteration=iteration,
                sql=current_sql,
                check_result=check_result
            )
            self.history.append(record)

            # 检查是否成功
            if check_result.is_valid and check_result.execution_success:
                # 如果提供了gold_sql，还需要验证结果是否正确
                if gold_sql:
                    from app.services.evaluator import SQLEvaluator
                    is_correct, _ = await SQLEvaluator.compare_sql_results_except(
                        engine, current_sql, gold_sql
                    )
                    if is_correct:
                        return self._build_success_result(start_time)
                else:
                    # 没有gold_sql，只要执行成功就算成功
                    return self._build_success_result(start_time)

            # 如果已达到最大迭代次数，退出
            if iteration >= self.max_iterations:
                break

        # 所有迭代完成但未成功
        return PipelineResult(
            success=False,
            final_sql=current_sql,
            iterations=len(self.history),
            correction_history=self._build_history(),
            total_time_ms=(time.time() - start_time) * 1000,
            error=f"Failed after {self.max_iterations} iterations"
        )

    async def _generate(self, question: str, schema: str) -> Optional[str]:
        """生成初始SQL."""
        try:
            return await generate_sql(
                question=question,
                schema_text=schema,
                provider=self.provider,
                model_config=self.model_config,
                dialect=self.dialect,
                api_key=self.api_key,
                format_type=self.format_type,
                base_url=self.base_url,
            )
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None

    async def _check(
        self,
        engine: AsyncEngine,
        sql: str,
        gold_sql: Optional[str] = None
    ) -> CheckResult:
        """检查SQL."""
        # 先检查语法
        syntax_result = SQLChecker.check_syntax(sql, self.dialect)
        if not syntax_result.is_valid:
            return syntax_result

        # 再执行检查
        return await SQLChecker.check_execution(engine, sql, gold_sql)

    async def _correct(
        self,
        question: str,
        schema: str,
        failed_sql: str,
        check_result: CheckResult,
        iteration: int
    ) -> Optional[str]:
        """修正SQL."""
        from app.services.llm import get_llm_client

        # 构建修正提示词
        prompt = SQLCorrector.build_correction_prompt(
            question=question,
            schema=schema,
            failed_sql=failed_sql,
            check_result=check_result,
            iteration=iteration
        )

        try:
            # 获取LLM客户端
            client = get_llm_client(
                provider=self.provider,
                api_key=self.api_key,
                format_type=self.format_type,
                base_url=self.base_url,
                model=self.model_config.get("model")
            )

            # 生成修正后的SQL
            response = await client.generate(prompt, self.model_config)

            # 解析响应
            correction_result = SQLCorrector.parse_correction_response(response)
            correction_result.iteration = iteration
            correction_result.correction_prompt = prompt

            # 更新最后一条记录的correction_result
            if self.history:
                self.history[-1].correction_result = correction_result

            return correction_result.corrected_sql if correction_result.success else None

        except Exception as e:
            logger.error(f"SQL correction failed: {e}")
            return None

    def _build_history(self) -> List[Dict[str, Any]]:
        """构建历史记录."""
        return [
            {
                "iteration": r.iteration,
                "sql": r.sql,
                "is_valid": r.check_result.is_valid,
                "error_type": r.check_result.error_type.value if r.check_result.error_type else None,
                "error_message": r.check_result.error_message,
                "execution_success": r.check_result.execution_success,
            }
            for r in self.history
        ]

    def _build_success_result(self, start_time: float) -> PipelineResult:
        """构建成功结果."""
        import time
        final_record = self.history[-1]

        return PipelineResult(
            success=True,
            final_sql=final_record.sql,
            iterations=len(self.history),
            correction_history=self._build_history(),
            total_time_ms=(time.time() - start_time) * 1000
        )
```

---

## 4. 接口设计

### 4.1 服务层接口

```python
# backend/app/services/nl2sql.py 新增接口

async def generate_sql_pass_at_k(
    question: str,
    schema_text: str,
    k: int = 8,
    temperature: float = 0.8,
    provider: str = "openai",
    model_config: Optional[dict] = None,
    dialect: str = "MySQL",
    api_key: Optional[str] = None,
    format_type: str = "openai",
    base_url: Optional[str] = None,
) -> PassAtKResult:
    """使用Pass@K策略生成SQL.

    生成K个候选SQL，评估每个候选的正确性，返回通过率统计。
    """
    pass


async def generate_sql_with_check_correct(
    question: str,
    schema_text: str,
    max_iterations: int = 3,
    provider: str = "openai",
    model_config: Optional[dict] = None,
    dialect: str = "MySQL",
    api_key: Optional[str] = None,
    format_type: str = "openai",
    base_url: Optional[str] = None,
    engine: Optional[AsyncEngine] = None,
) -> PipelineResult:
    """使用Check-Correct策略生成SQL.

    迭代生成-检查-修正，直到生成正确的SQL或达到最大迭代次数。
    """
    pass
```

### 4.2 内部 API 约定

#### 统一返回格式

```python
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """统一的结果封装."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None

    @classmethod
    def ok(cls, data: T, metadata: Optional[dict] = None) -> "Result[T]":
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, metadata: Optional[dict] = None) -> "Result[T]":
        return cls(success=False, error=error, metadata=metadata)
```

#### 异步与超时约定

```python
import asyncio
from typing import TypeVar

T = TypeVar('T')

async def with_timeout(
    coro: asyncio.Coroutine[Any, Any, T],
    timeout: int,
    timeout_message: str = "Operation timed out"
) -> T:
    """带超时的异步执行.

    Args:
        coro: 异步协程
        timeout: 超时时间（秒）
        timeout_message: 超时错误消息

    Returns:
        协程结果

    Raises:
        TimeoutError: 超时
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(timeout_message)
```

---

## 5. 实现规划

### 5.1 文件修改清单

| 文件路径 | 修改类型 | 说明 |
|----------|----------|------|
| `backend/app/models/eval_task.py` | 修改 | 新增5个字段：sampling_count, max_iterations, correction_strategy, reasoning_mode, temperature |
| `backend/app/models/eval_result.py` | 修改 | 新增5个字段：candidate_sqls, iteration_count, correction_history, confidence_score, execution_details |
| `backend/app/services/nl2sql.py` | 修改 | 新增2个函数：generate_sql_pass_at_k, generate_sql_with_check_correct |
| `backend/app/services/evaluator.py` | 修改 | 复用现有MajorityVoter，无需修改 |
| `backend/app/services/sql_checker.py` | 新增 | SQLChecker类实现 |
| `backend/app/services/sql_corrector.py` | 新增 | SQLCorrector类实现 |
| `backend/app/services/pass_at_k.py` | 新增 | PassAtKEvaluator类实现 |
| `backend/app/services/check_correct_pipeline.py` | 新增 | CheckCorrectPipeline类实现 |
| `backend/app/tasks/eval_tasks.py` | 修改 | 扩展_run_evaluation支持新推理模式 |
| `backend/app/api/v1/queries.py` | 修改 | 新增/generate-advanced端点 |
| `backend/app/api/v1/evaluations.py` | 修改 | 扩展现有端点支持高级推理参数 |
| `backend/app/schemas/evaluation.py` | 修改 | 扩展EvalTask schema |
| `backend/app/schemas/query.py` | 修改 | 新增高级查询schema |

### 5.2 依赖关系图

```
                    ┌─────────────────┐
                    │   API Layer     │
                    │  (queries.py)   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Service Layer  │
                    │   (nl2sql.py)   │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  PassAtKEvaluator│ │CheckCorrectPipe │ │  SQLChecker     │
│  (pass_at_k.py) │ │ (check_correct_  │ │ (sql_checker.py)│
│                 │ │   pipeline.py)  │ │                 │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         │                   ▼                   │
         │          ┌─────────────────┐          │
         │          │  SQLCorrector   │          │
         │          │(sql_corrector.py│◄─────────┘
         │          └─────────────────┘
         │                   │
         └───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Model Layer   │
                    │ (eval_task.py)  │
                    │(eval_result.py) │
                    └─────────────────┘
```

### 5.3 数据库迁移脚本

```sql
-- backend/alembic/versions/xxx_add_advanced_inference_fields.py

"""Add advanced inference fields to eval_tasks and eval_results

Revision ID: xxx
Revises: previous_revision
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'xxx'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade():
    # EvalTask 新增字段
    op.add_column('eval_tasks', sa.Column('sampling_count', sa.Integer(), nullable=True))
    op.add_column('eval_tasks', sa.Column('max_iterations', sa.Integer(), nullable=True))
    op.add_column('eval_tasks', sa.Column('correction_strategy', sa.String(length=50), nullable=True))
    op.add_column('eval_tasks', sa.Column('reasoning_mode', sa.String(length=50), nullable=True))
    op.add_column('eval_tasks', sa.Column('temperature', sa.Float(), nullable=True))

    # EvalResult 新增字段
    op.add_column('eval_results', sa.Column('candidate_sqls', sa.JSON(), nullable=True))
    op.add_column('eval_results', sa.Column('iteration_count', sa.Integer(), nullable=True))
    op.add_column('eval_results', sa.Column('correction_history', sa.JSON(), nullable=True))
    op.add_column('eval_results', sa.Column('confidence_score', sa.Float(), nullable=True))
    op.add_column('eval_results', sa.Column('execution_details', sa.JSON(), nullable=True))

    # 创建索引
    op.create_index('ix_eval_tasks_reasoning_mode', 'eval_tasks', ['reasoning_mode'])
    op.create_index('ix_eval_results_confidence_score', 'eval_results', ['confidence_score'])


def downgrade():
    # 删除索引
    op.drop_index('ix_eval_results_confidence_score', table_name='eval_results')
    op.drop_index('ix_eval_tasks_reasoning_mode', table_name='eval_tasks')

    # 删除EvalResult字段
    op.drop_column('eval_results', 'execution_details')
    op.drop_column('eval_results', 'confidence_score')
    op.drop_column('eval_results', 'correction_history')
    op.drop_column('eval_results', 'iteration_count')
    op.drop_column('eval_results', 'candidate_sqls')

    # 删除EvalTask字段
    op.drop_column('eval_tasks', 'temperature')
    op.drop_column('eval_tasks', 'reasoning_mode')
    op.drop_column('eval_tasks', 'correction_strategy')
    op.drop_column('eval_tasks', 'max_iterations')
    op.drop_column('eval_tasks', 'sampling_count')
```

---

## 6. 性能考虑

### 6.1 并行执行

```python
# Pass@K 候选并行生成
async def generate_candidates_parallel(
    self, question: str, schema: str, k: int
) -> List[str]:
    """并行生成K个候选."""
    tasks = [
        self._generate_single(question, schema, temperature=0.8)
        for _ in range(k)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# Pass@K 候选并行评估
async def evaluate_candidates_parallel(
    self, engine: AsyncEngine, candidates: List[str], gold_sql: str
) -> List[Dict]:
    """并行评估候选（使用连接池）."""
    semaphore = asyncio.Semaphore(5)  # 限制并发数

    async def eval_with_limit(sql: str) -> Dict:
        async with semaphore:
            return await self._evaluate_single(engine, sql, gold_sql)

    tasks = [eval_with_limit(sql) for sql in candidates]
    return await asyncio.gather(*tasks)
```

### 6.2 连接池管理

```python
# 使用专用连接池进行评测
from sqlalchemy.ext.asyncio import create_async_engine

# 创建评测专用引擎，限制连接数
eval_engine = create_async_engine(
    database_url,
    pool_size=5,           # 连接池大小
    max_overflow=10,       # 最大溢出连接
    pool_timeout=30,       # 获取连接超时
    pool_recycle=3600,     # 连接回收时间
)
```

### 6.3 超时控制策略

```python
# 多层超时控制
TIMEOUT_CONFIG = {
    "single_sql_execution": 30,      # 单条SQL执行超时
    "single_iteration": 60,          # 单次迭代超时（Check-Correct）
    "pass_at_k_generation": 120,     # Pass@K生成超时
    "pass_at_k_evaluation": 60,      # Pass@K评估超时
    "single_question": 300,          # 单问题总超时
}
```

### 6.4 缓存策略

```python
# 候选结果缓存（避免重复执行相同SQL）
from functools import lru_cache

class CachedEvaluator:
    """带缓存的评估器."""

    def __init__(self):
        self._execution_cache: Dict[str, Dict] = {}

    async def evaluate_with_cache(
        self, engine: AsyncEngine, sql: str, gold_sql: str
    ) -> Dict:
        """带缓存的评估."""
        cache_key = f"{sql}::{gold_sql}"

        if cache_key in self._execution_cache:
            return self._execution_cache[cache_key]

        result = await self._evaluate(engine, sql, gold_sql)
        self._execution_cache[cache_key] = result
        return result
```

---

## 7. 安全考虑

### 7.1 SQL 注入防护

```python
# SQLSanitizer 检查
class SQLSanitizer:
    """SQL安全检查器."""

    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT",
        "ALTER", "CREATE", "TRUNCATE", "EXEC",
        "UNION", "--", "/*", "*/", ";"
    ]

    @staticmethod
    def is_safe(sql: str, allow_write: bool = False) -> Tuple[bool, str]:
        """检查SQL是否安全.

        Args:
            sql: 待检查的SQL
            allow_write: 是否允许写操作

        Returns:
            (是否安全, 错误消息)
        """
        sql_upper = sql.upper()

        # 检查危险关键字
        for keyword in SQLSanitizer.DANGEROUS_KEYWORDS:
            if keyword in sql_upper and not allow_write:
                return False, f"Dangerous keyword detected: {keyword}"

        # 确保是SELECT语句
        if not sql_upper.strip().startswith("SELECT"):
            return False, "Only SELECT statements are allowed"

        return True, ""
```

### 7.2 执行隔离

```python
# 在独立事务中执行并回滚
async def execute_in_isolation(engine: AsyncEngine, sql: str):
    """在隔离事务中执行SQL."""
    async with engine.connect() as conn:
        async with conn.begin() as trans:
            try:
                result = await conn.execute(text(sql))
                rows = result.mappings().all()
                # 回滚所有更改
                await trans.rollback()
                return [dict(row) for row in rows]
            except Exception as e:
                await trans.rollback()
                raise
```

### 7.3 权限控制

```python
# 只读权限验证
async def verify_read_only_permissions(engine: AsyncEngine) -> bool:
    """验证数据库连接是否为只读权限."""
    test_sqls = [
        "INSERT INTO __test_table__ (id) VALUES (1)",
        "UPDATE __test_table__ SET id = 2",
        "DELETE FROM __test_table__ WHERE id = 1",
        "DROP TABLE __test_table__",
    ]

    async with engine.connect() as conn:
        for sql in test_sqls:
            try:
                await conn.execute(text(sql))
                # 如果执行成功，说明有写权限
                return False
            except Exception:
                # 预期会失败
                continue

    return True
```

### 7.4 资源限制

```python
# 结果集大小限制
MAX_RESULT_ROWS = 1000
MAX_RESULT_SIZE_MB = 10

async def execute_with_limits(engine: AsyncEngine, sql: str) -> Tuple[bool, Any]:
    """带资源限制的SQL执行."""
    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        rows = result.mappings().all()

        # 检查行数限制
        if len(rows) > MAX_RESULT_ROWS:
            return False, f"Result exceeds maximum row limit: {MAX_RESULT_ROWS}"

        # 检查结果大小
        result_size = len(str(rows).encode('utf-8')) / (1024 * 1024)
        if result_size > MAX_RESULT_SIZE_MB:
            return False, f"Result exceeds maximum size: {MAX_RESULT_SIZE_MB}MB"

        return True, [dict(row) for row in rows]
```

---

## 8. 测试策略

### 8.1 单元测试

```python
# tests/services/test_sql_checker.py

async def test_sql_checker_syntax_valid():
    """测试语法检查 - 有效SQL."""
    sql = "SELECT * FROM users WHERE id = 1"
    result = SQLChecker.check_syntax(sql)
    assert result.is_valid is True

async def test_sql_checker_syntax_invalid():
    """测试语法检查 - 无效SQL."""
    sql = "SELECT * FROM WHERE id = 1"
    result = SQLChecker.check_syntax(sql)
    assert result.is_valid is False
    assert result.error_type == ErrorType.SYNTAX_ERROR
```

### 8.2 集成测试

```python
# tests/services/test_check_correct_pipeline.py

async def test_pipeline_success_on_first_iteration():
    """测试管道在第一次迭代成功."""
    pipeline = CheckCorrectPipeline(...)
    result = await pipeline.run(
        question="查询所有用户",
        schema="CREATE TABLE users (id INT, name VARCHAR(50))",
        engine=test_engine
    )
    assert result.success is True
    assert result.iterations == 1

async def test_pipeline_success_after_correction():
    """测试管道在修正后成功."""
    pipeline = CheckCorrectPipeline(...)
    result = await pipeline.run(
        question="查询用户数量",
        schema="CREATE TABLE users (id INT)",
        engine=test_engine
    )
    assert result.success is True
    assert result.iterations > 1
```

---

## 9. 附录

### 9.1 术语表

| 术语 | 说明 |
|------|------|
| Pass@K | 生成K个候选SQL，至少有一个正确的概率 |
| Check-Correct | 生成-检查-修正的迭代流程 |
| Majority Voting | 多数投票，选择执行结果相同的SQL |
| Greedy Search | 贪婪搜索，单次生成 |
| Temperature | 采样温度，控制生成的随机性 |

### 9.2 参考资料

1. [Spider: A Large-Scale Human-Labeled Dataset for Text-to-SQL Tasks](https://yale-lily.github.io/spider)
2. [CodeX: Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374)
3. [Self-Debugging: Teaching Large Language Models to Debug Programs](https://arxiv.org/abs/2304.05128)
