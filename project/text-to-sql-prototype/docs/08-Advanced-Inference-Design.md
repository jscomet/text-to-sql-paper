# 高级推理功能 - 技术设计文档

> **文档路径**: `docs/08-Advanced-Inference-Design.md`
> **版本**: v1.1.0
> **创建日期**: 2026-03-13
> **作者**: Text-to-SQL Team
> **状态**: 已完成

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
│           │                    │  - check_correct()      │                 │
│           │                    │  - iterative_correct()  │                 │
│           │                    │  - verify_with_data()   │                 │
│           │                    └────────────┬────────────┘                 │
│           │                                 │                              │
│           │                    ┌────────────▼────────────┐                 │
│           └───────────────────►│   VoteAtK Pipeline      │                 │
│                                │                         │                 │
│                                │  - vote_at_k()          │                 │
│                                │  - consensus_voting()   │                 │
│                                │  - weighted_voting()    │                 │
│                                └─────────────────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件说明

| 组件 | 职责 | 关键方法 |
|------|------|----------|
| **Pass@K Evaluator** | 生成k个候选SQL并评估通过率 | `generate_k()`, `evaluate()`, `aggregate()` |
| **SQL Checker** | 验证SQL正确性（语法+执行） | `check_syntax()`, `execute_verify()` |
| **SQL Corrector** | 分析错误并生成修正SQL | `analyze_error()`, `build_prompt()`, `correct()` |
| **Check-Correct Pipeline** | 检查-修正迭代流程 | `check_correct()`, `iterative_correct()` |
| **Vote@K Pipeline** | 多结果投票机制 | `vote_at_k()`, `consensus_voting()` |

---

## 2. Pass@K 评估器

### 2.1 算法设计

**Pass@K定义**: 从k个候选样本中，至少有一个正确样本的概率

```
Pass@K = 1 - C(k - c, n) / C(k, n)

其中:
- k: 生成的候选总数
- c: 正确的候选数
- n: 评估时抽取的样本数 (通常 n=1)
```

### 2.2 实现方案

```python
class PassAtKEvaluator:
    """Pass@K评估器实现"""

    def __init__(
        self,
        llm_service: LLMService,
        k: int = 5,
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        self.llm = llm_service
        self.k = k
        self.temperature = temperature
        self.max_retries = max_retries

    async def generate_k(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> List[GenerationResult]:
        """
        生成k个候选SQL

        策略:
        1. 使用较高的temperature增加多样性
        2. 并行生成k个候选
        3. 记录每个候选的生成参数
        """
        tasks = [
            self._generate_single(
                prompt=prompt,
                schema=schema,
                seed=i  # 使用不同seed确保多样性
            )
            for i in range(self.k)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            GenerationResult(
                sql=result.sql if not isinstance(result, Exception) else "",
                confidence=result.confidence if not isinstance(result, Exception) else 0.0,
                metadata={
                    "seed": i,
                    "temperature": self.temperature,
                    "error": str(result) if isinstance(result, Exception) else None
                }
            )
            for i, result in enumerate(results)
        ]

    async def evaluate(
        self,
        candidates: List[GenerationResult],
        validator: SQLValidator
    ) -> EvaluationResult:
        """
        评估候选SQL的正确性

        评估维度:
        1. 语法正确性
        2. 可执行性
        3. 结果正确性（如果有标准答案）
        """
        evaluated = []
        correct_count = 0

        for candidate in candidates:
            # 语法检查
            syntax_valid = validator.check_syntax(candidate.sql)

            # 执行检查
            execution_result = None
            if syntax_valid:
                execution_result = await validator.execute(candidate.sql)

            is_correct = syntax_valid and (
                execution_result.is_valid if execution_result else False
            )

            if is_correct:
                correct_count += 1

            evaluated.append(EvaluatedCandidate(
                sql=candidate.sql,
                is_correct=is_correct,
                syntax_valid=syntax_valid,
                execution_result=execution_result,
                confidence=candidate.confidence
            ))

        # 计算Pass@K
        pass_at_k = self._calculate_pass_at_k(correct_count, len(candidates))

        return EvaluationResult(
            pass_at_k=pass_at_k,
            candidates=evaluated,
            correct_count=correct_count,
            total_count=len(candidates)
        )

    def _calculate_pass_at_k(self, correct: int, total: int) -> float:
        """计算Pass@K值"""
        if total == 0:
            return 0.0
        # 简化的Pass@K计算: 1 - (1 - c/k)^k
        return 1 - (1 - correct / total) ** total
```

### 2.3 API接口设计

```yaml
# Pass@K评估端点
POST /api/v1/evaluation/pass-at-k

Request:
  {
    "question_id": "q-123",
    "natural_language": "查询2024年销售额最高的前10个产品",
    "schema_id": "schema-001",
    "k": 5,                          # 候选数量
    "temperature": 0.7,              # 采样温度
    "evaluation_config": {
      "check_syntax": true,
      "check_execution": true,
      "timeout": 30
    }
  }

Response:
  {
    "evaluation_id": "eval-456",
    "pass_at_k": 0.672,
    "candidates": [
      {
        "sql": "SELECT ...",
        "is_correct": true,
        "confidence": 0.95,
        "execution_time": 0.123,
        "metadata": {...}
      }
    ],
    "statistics": {
      "total_generated": 5,
      "syntax_valid": 4,
      "execution_valid": 3,
      "correct": 3
    }
  }
```

---

## 3. Check-Correct 检查修正机制

### 3.1 设计原理

**核心思想**: 通过迭代检查-修正循环，逐步提升SQL质量

```
循环直到满足终止条件:
  1. 检查当前SQL的正确性
  2. 如果正确 → 返回结果
  3. 如果错误 → 分析错误原因
  4. 基于错误生成修正SQL
  5. 进入下一轮检查
```

### 3.2 错误分类与处理策略

| 错误类型 | 检测方式 | 修正策略 | 示例 |
|----------|----------|----------|------|
| **语法错误** | SQL解析器 | 语法提示+重生成 | 缺少逗号、括号不匹配 |
| **表/列不存在** | Schema验证 | Schema提示+修正 | 表名拼写错误 |
| **类型不匹配** | 语义分析 | 类型转换建议 | 字符串比较数字 |
| **逻辑错误** | 执行结果验证 | 示例数据对比 | 条件错误导致结果为空 |
| **超时/性能** | 执行监控 | 优化建议+重写 | 缺少索引提示 |

### 3.3 实现方案

```python
class CheckCorrectPipeline:
    """检查-修正流水线"""

    def __init__(
        self,
        llm_service: LLMService,
        sql_checker: SQLChecker,
        sql_corrector: SQLCorrector,
        max_iterations: int = 3
    ):
        self.llm = llm_service
        self.checker = sql_checker
        self.corrector = sql_corrector
        self.max_iterations = max_iterations

    async def check_correct(
        self,
        sql: str,
        natural_language: str,
        schema: Dict[str, Any],
        context: CorrectionContext = None
    ) -> CorrectionResult:
        """
        执行检查-修正流程

        Args:
            sql: 待检查的SQL
            natural_language: 原始自然语言问题
            schema: 数据库Schema
            context: 修正上下文（历史修正记录等）

        Returns:
            CorrectionResult: 包含最终SQL和修正历史
        """
        current_sql = sql
        history = []

        for iteration in range(self.max_iterations):
            # 1. 检查当前SQL
            check_result = await self.checker.check(
                sql=current_sql,
                schema=schema
            )

            if check_result.is_valid:
                # 检查通过，返回结果
                return CorrectionResult(
                    final_sql=current_sql,
                    is_valid=True,
                    iterations=iteration + 1,
                    history=history,
                    final_check=check_result
                )

            # 2. 分析错误
            error_analysis = await self.corrector.analyze_error(
                sql=current_sql,
                error=check_result.error,
                natural_language=natural_language,
                schema=schema
            )

            # 3. 生成修正SQL
            corrected = await self.corrector.correct(
                sql=current_sql,
                error_analysis=error_analysis,
                iteration=iteration,
                context=context
            )

            history.append(CorrectionStep(
                iteration=iteration + 1,
                original_sql=current_sql,
                error_type=error_analysis.error_type,
                error_message=error_analysis.message,
                corrected_sql=corrected.sql,
                confidence=corrected.confidence
            ))

            current_sql = corrected.sql

            # 4. 检查是否收敛（SQL不再变化）
            if len(history) >= 2 and history[-2].corrected_sql == current_sql:
                break

        # 达到最大迭代次数仍未修正成功
        return CorrectionResult(
            final_sql=current_sql,
            is_valid=False,
            iterations=len(history),
            history=history,
            final_check=check_result,
            error="达到最大修正次数仍未成功"
        )

    async def iterative_correct(
        self,
        candidates: List[str],
        natural_language: str,
        schema: Dict[str, Any]
    ) -> List[CorrectionResult]:
        """
        对多个候选SQL并行执行检查-修正
        """
        tasks = [
            self.check_correct(
                sql=candidate,
                natural_language=natural_language,
                schema=schema
            )
            for candidate in candidates
        ]

        return await asyncio.gather(*tasks)
```

### 3.4 SQL检查器详细设计

```python
class SQLChecker:
    """SQL多维度检查器"""

    def __init__(
        self,
        db_connection: DatabaseConnection,
        timeout: int = 30
    ):
        self.db = db_connection
        self.timeout = timeout

    async def check(
        self,
        sql: str,
        schema: Dict[str, Any]
    ) -> CheckResult:
        """执行完整检查流程"""

        # 1. 语法检查
        syntax_result = self._check_syntax(sql)
        if not syntax_result.valid:
            return CheckResult(
                is_valid=False,
                stage="syntax",
                error=SyntaxError(
                    message=syntax_result.error_message,
                    position=syntax_result.error_position
                )
            )

        # 2. Schema验证
        schema_result = self._validate_schema(sql, schema)
        if not schema_result.valid:
            return CheckResult(
                is_valid=False,
                stage="schema",
                error=SchemaError(
                    message=schema_result.error_message,
                    missing_tables=schema_result.missing_tables,
                    missing_columns=schema_result.missing_columns
                )
            )

        # 3. 执行验证
        execution_result = await self._execute_verify(sql)
        if not execution_result.success:
            return CheckResult(
                is_valid=False,
                stage="execution",
                error=ExecutionError(
                    message=execution_result.error_message,
                    error_type=execution_result.error_type
                )
            )

        # 4. 结果验证（如果有预期结果）
        if execution_result.expected_result is not None:
            result_match = self._compare_results(
                execution_result.actual_result,
                execution_result.expected_result
            )
            if not result_match.is_match:
                return CheckResult(
                    is_valid=False,
                    stage="result",
                    error=ResultMismatchError(
                        message="结果与预期不符",
                        differences=result_match.differences
                    )
                )

        return CheckResult(is_valid=True)

    def _check_syntax(self, sql: str) -> SyntaxCheckResult:
        """
        使用SQL解析器检查语法

        支持的方言:
        - MySQL
        - PostgreSQL
        - SQLite
        - SQL Server
        """
        try:
            parsed = sqlglot.parse(sql, dialect=self.db.dialect)
            return SyntaxCheckResult(valid=True, parsed_tree=parsed)
        except Error as e:
            return SyntaxCheckResult(
                valid=False,
                error_message=str(e),
                error_position=e.position if hasattr(e, 'position') else None
            )

    async def _execute_verify(
        self,
        sql: str,
        limit: int = 100
    ) -> ExecutionResult:
        """
        在受限环境中执行SQL验证

        安全措施:
        1. 只读查询（SELECT）
        2. 结果行数限制
        3. 执行超时控制
        4. 资源使用限制
        """
        # 检查是否为只读查询
        if not self._is_read_only(sql):
            return ExecutionResult(
                success=False,
                error_message="非只读查询不允许执行",
                error_type="SAFETY_VIOLATION"
            )

        try:
            # 添加LIMIT限制
            limited_sql = self._add_limit(sql, limit)

            # 在超时内执行
            result = await asyncio.wait_for(
                self.db.execute(limited_sql),
                timeout=self.timeout
            )

            return ExecutionResult(
                success=True,
                row_count=len(result.rows),
                columns=result.columns,
                sample_data=result.rows[:10],  # 只保留样本
                execution_time=result.execution_time
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error_message=f"执行超时（>{self.timeout}秒）",
                error_type="TIMEOUT"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error_message=str(e),
                error_type="EXECUTION_ERROR"
            )
```

### 3.5 SQL修正器详细设计

```python
class SQLCorrector:
    """智能SQL修正器"""

    # 修正提示词模板
    CORRECTION_PROMPT_TEMPLATE = """
    你是一个SQL专家。请修正以下错误的SQL查询。

    ## 原始问题
    {natural_language}

    ## 数据库Schema
    {schema_description}

    ## 当前SQL（有错误）
    ```sql
    {current_sql}
    ```

    ## 错误信息
    类型: {error_type}
    位置: {error_position}
    详情: {error_message}

    ## 修正建议
    {correction_hints}

    ## 要求
    1. 只返回修正后的SQL，不要解释
    2. 确保SQL语法正确
    3. 保持原始查询的意图
    4. 使用标准SQL，必要时使用{dialect}方言

    ## 输出格式
    ```sql
    -- 修正后的SQL
    ```
    """

    async def analyze_error(
        self,
        sql: str,
        error: SQLError,
        natural_language: str,
        schema: Dict[str, Any]
    ) -> ErrorAnalysis:
        """深度分析错误原因"""

        error_type = self._classify_error(error)

        # 根据错误类型生成针对性提示
        hints = self._generate_hints(error_type, error, schema)

        return ErrorAnalysis(
            error_type=error_type,
            message=error.message,
            position=getattr(error, 'position', None),
            hints=hints,
            severity=self._assess_severity(error_type)
        )

    def _classify_error(self, error: SQLError) -> ErrorType:
        """错误分类"""
        error_msg = error.message.lower()

        patterns = {
            ErrorType.SYNTAX: [
                r"syntax error",
                r"unexpected",
                r"missing",
                r"expected"
            ],
            ErrorType.TABLE_NOT_FOUND: [
                r"table.*not found",
                r"relation.*does not exist",
                r"unknown table"
            ],
            ErrorType.COLUMN_NOT_FOUND: [
                r"column.*not found",
                r"unknown column",
                r"field.*doesn't exist"
            ],
            ErrorType.TYPE_MISMATCH: [
                r"type mismatch",
                r"cannot compare",
                r"incompatible types"
            ],
            ErrorType.PERMISSION: [
                r"permission denied",
                r"access denied"
            ],
            ErrorType.TIMEOUT: [
                r"timeout",
                r"canceling statement"
            ]
        }

        for error_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, error_msg):
                    return error_type

        return ErrorType.UNKNOWN

    async def correct(
        self,
        sql: str,
        error_analysis: ErrorAnalysis,
        iteration: int,
        context: CorrectionContext = None
    ) -> CorrectedSQL:
        """生成修正后的SQL"""

        # 构建提示词
        prompt = self.CORRECTION_PROMPT_TEMPLATE.format(
            natural_language=context.natural_language if context else "",
            schema_description=self._format_schema(context.schema if context else {}),
            current_sql=sql,
            error_type=error_analysis.error_type.value,
            error_position=error_analysis.position or "未知",
            error_message=error_analysis.message,
            correction_hints="\n".join(f"- {h}" for h in error_analysis.hints),
            dialect=context.dialect if context else "标准SQL"
        )

        # 调用LLM生成修正
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,  # 较低温度确保准确性
            max_tokens=500
        )

        # 提取SQL
        corrected_sql = self._extract_sql(response.text)

        # 计算置信度
        confidence = self._calculate_confidence(
            response,
            error_analysis,
            iteration
        )

        return CorrectedSQL(
            sql=corrected_sql,
            confidence=confidence,
            reasoning=response.reasoning if hasattr(response, 'reasoning') else None
        )

    def _generate_hints(
        self,
        error_type: ErrorType,
        error: SQLError,
        schema: Dict[str, Any]
    ) -> List[str]:
        """生成修正提示"""

        hints = {
            ErrorType.SYNTAX: [
                "检查SQL语法，特别是关键字拼写",
                "确认括号、引号是否成对",
                "检查逗号分隔是否正确"
            ],
            ErrorType.TABLE_NOT_FOUND: [
                f"可用表: {', '.join(schema.get('tables', []))}",
                "检查表名拼写",
                "确认表是否在正确的schema中"
            ],
            ErrorType.COLUMN_NOT_FOUND: [
                "检查列名拼写",
                "确认列属于正确的表",
                f"可用列: {self._get_available_columns(schema)}"
            ],
            ErrorType.TYPE_MISMATCH: [
                "使用CAST或CONVERT进行类型转换",
                "检查比较操作两边的类型",
                "确保函数参数类型正确"
            ]
        }

        return hints.get(error_type, ["请仔细检查SQL语法和逻辑"])
```

### 3.6 API接口设计

```yaml
# Check-Correct端点
POST /api/v1/evaluation/check-correct

Request:
  {
    "question_id": "q-123",
    "natural_language": "查询2024年销售额最高的前10个产品",
    "generated_sql": "SELECT product_name FROM sales WHERE year=2024 ORDER BY amount DESC LIMIT 10",
    "schema_id": "schema-001",
    "max_iterations": 3,
    "execution_config": {
      "timeout": 30,
      "row_limit": 100
    }
  }

Response:
  {
    "correction_id": "corr-789",
    "final_sql": "SELECT p.product_name FROM products p JOIN sales s ON p.id = s.product_id WHERE s.sale_year = 2024 ORDER BY s.sale_amount DESC LIMIT 10",
    "is_valid": true,
    "iterations": 2,
    "history": [
      {
        "iteration": 1,
        "error_type": "TABLE_NOT_FOUND",
        "error_message": "Table 'sales' not found",
        "corrected_sql": "...",
        "confidence": 0.85
      },
      {
        "iteration": 2,
        "error_type": "COLUMN_NOT_FOUND",
        "error_message": "Column 'year' not found in table 'sales'",
        "corrected_sql": "...",
        "confidence": 0.92
      }
    ],
    "final_check": {
      "syntax_valid": true,
      "execution_valid": true,
      "execution_time": 0.234,
      "row_count": 10
    }
  }
```

---

## 4. Vote@K 投票机制

### 4.1 设计原理

**核心思想**: 利用多个候选结果的共识，提高最终答案的可靠性

```
生成k个候选SQL → 执行获取结果 → 结果标准化 → 投票聚合 → 选出最佳结果
```

### 4.2 投票策略

#### 4.2.1 共识投票 (Consensus Voting)

```python
async def consensus_voting(
    self,
    candidates: List[ExecutionResult],
    threshold: float = 0.6
) -> VoteResult:
    """
    基于结果相似度的共识投票

    算法:
    1. 对所有结果进行两两比较
    2. 计算相似度矩阵
    3. 找出最大共识集群
    4. 返回集群代表作为最终结果
    """

    # 标准化结果以便比较
    normalized = [self._normalize_result(r) for r in candidates]

    # 构建相似度矩阵
    n = len(normalized)
    similarity_matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i, n):
            sim = self._calculate_similarity(normalized[i], normalized[j])
            similarity_matrix[i][j] = sim
            similarity_matrix[j][i] = sim

    # 找出共识集群（相似度>threshold的结果组）
    clusters = self._find_clusters(similarity_matrix, threshold)

    # 选择最大的集群
    best_cluster = max(clusters, key=len)

    # 计算每个候选的得分（在集群中的平均相似度）
    scores = []
    for i in best_cluster:
        avg_sim = sum(similarity_matrix[i][j] for j in best_cluster) / len(best_cluster)
        scores.append((i, avg_sim))

    # 选择得分最高的作为代表
    winner_idx = max(scores, key=lambda x: x[1])[0]

    return VoteResult(
        winner=candidates[winner_idx],
        confidence=len(best_cluster) / len(candidates),
        consensus_size=len(best_cluster),
        alternative_candidates=[candidates[i] for i in best_cluster if i != winner_idx]
    )
```

#### 4.2.2 加权投票 (Weighted Voting)

```python
async def weighted_voting(
    self,
    candidates: List[ExecutionResult],
    weights: VoteWeights
) -> VoteResult:
    """
    基于多维度权重的投票

    权重维度:
    - 执行成功: 0.3
    - 结果非空: 0.2
    - 执行时间: 0.15
    - SQL简洁性: 0.15
    - LLM置信度: 0.2
    """

    scored_candidates = []

    for candidate in candidates:
        score = 0.0

        # 1. 执行成功权重
        if candidate.execution_success:
            score += weights.execution_success * 1.0

        # 2. 结果非空权重
        if candidate.row_count > 0:
            score += weights.non_empty_result * min(candidate.row_count / 10, 1.0)

        # 3. 执行时间权重（越快越好）
        if candidate.execution_time < 1.0:
            time_score = 1.0
        elif candidate.execution_time < 5.0:
            time_score = 0.7
        elif candidate.execution_time < 10.0:
            time_score = 0.4
        else:
            time_score = 0.1
        score += weights.execution_time * time_score

        # 4. SQL简洁性权重
        complexity_score = self._assess_complexity(candidate.sql)
        score += weights.simplicity * complexity_score

        # 5. LLM置信度权重
        score += weights.llm_confidence * candidate.llm_confidence

        scored_candidates.append((candidate, score))

    # 按得分排序
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    winner, winning_score = scored_candidates[0]

    # 计算置信度（与第二名的差距）
    if len(scored_candidates) > 1:
        second_score = scored_candidates[1][1]
        confidence = min((winning_score - second_score) / winning_score, 1.0)
    else:
        confidence = 1.0

    return VoteResult(
        winner=winner,
        confidence=confidence,
        score_breakdown={
            "total_score": winning_score,
            "rank": 1,
            "score_gap": winning_score - scored_candidates[1][1] if len(scored_candidates) > 1 else 0
        }
    )
```

### 4.3 结果标准化与比较

```python
class ResultNormalizer:
    """执行结果标准化器"""

    def normalize(self, result: ExecutionResult) -> NormalizedResult:
        """
        标准化执行结果以便比较

        标准化步骤:
        1. 列名统一小写
        2. 数值精度统一
        3. 空值表示统一
        4. 行排序标准化
        """
        if not result.success or not result.rows:
            return NormalizedResult(is_empty=True)

        # 列名标准化
        columns = [col.lower().strip() for col in result.columns]

        # 数据标准化
        normalized_rows = []
        for row in result.rows:
            normalized_row = {}
            for col, val in zip(columns, row):
                normalized_row[col] = self._normalize_value(val)
            normalized_rows.append(normalized_row)

        # 行排序（按所有列的字典序）
        normalized_rows.sort(key=lambda r: json.dumps(r, sort_keys=True))

        return NormalizedResult(
            columns=columns,
            rows=normalized_rows,
            row_count=len(normalized_rows)
        )

    def _normalize_value(self, value: Any) -> Any:
        """标准化单个值"""
        if value is None:
            return "__NULL__"

        if isinstance(value, (int, float)):
            # 统一浮点数精度
            return round(float(value), 6)

        if isinstance(value, str):
            # 字符串清理
            return value.strip().lower()

        if isinstance(value, datetime):
            # 时间格式统一
            return value.isoformat()

        return str(value)

    def calculate_similarity(
        self,
        result1: NormalizedResult,
        result2: NormalizedResult
    ) -> float:
        """
        计算两个结果集的相似度

        算法:
        - 列集合的Jaccard相似度: 30%
        - 行数据的重叠度: 70%
        """
        if result1.is_empty and result2.is_empty:
            return 1.0

        if result1.is_empty or result2.is_empty:
            return 0.0

        # 列相似度
        cols1, cols2 = set(result1.columns), set(result2.columns)
        col_jaccard = len(cols1 & cols2) / len(cols1 | cols2)

        # 行相似度（使用集合交集）
        rows1 = set(json.dumps(r, sort_keys=True) for r in result1.rows)
        rows2 = set(json.dumps(r, sort_keys=True) for r in result2.rows)

        if not rows1 and not rows2:
            row_similarity = 1.0
        elif not rows1 or not rows2:
            row_similarity = 0.0
        else:
            row_similarity = len(rows1 & rows2) / max(len(rows1), len(rows2))

        # 加权组合
        return 0.3 * col_jaccard + 0.7 * row_similarity
```

### 4.4 API接口设计

```yaml
# Vote@K端点
POST /api/v1/evaluation/vote-at-k

Request:
  {
    "question_id": "q-123",
    "natural_language": "查询2024年销售额最高的前10个产品",
    "schema_id": "schema-001",
    "k": 5,
    "voting_strategy": "consensus",  # 或 "weighted"
    "voting_config": {
      "consensus_threshold": 0.6,
      "weights": {
        "execution_success": 0.3,
        "non_empty_result": 0.2,
        "execution_time": 0.15,
        "simplicity": 0.15,
        "llm_confidence": 0.2
      }
    }
  }

Response:
  {
    "vote_id": "vote-456",
    "winner": {
      "sql": "SELECT p.product_name, SUM(s.amount) as total_sales FROM products p JOIN sales s ON p.id = s.product_id WHERE s.year = 2024 GROUP BY p.product_name ORDER BY total_sales DESC LIMIT 10",
      "execution_time": 0.156,
      "row_count": 10,
      "llm_confidence": 0.94
    },
    "confidence": 0.8,
    "consensus_size": 3,
    "all_candidates": [
      {
        "sql": "...",
        "score": 0.92,
        "rank": 1,
        "in_consensus": true
      }
    ],
    "voting_metadata": {
      "strategy": "consensus",
      "total_candidates": 5,
      "execution_success_rate": 0.8,
      "average_execution_time": 0.234
    }
  }
```

---

## 5. 完整流程整合

### 5.1 高级推理完整流程图

```
用户问题
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pass@K Generation                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ SQL #1  │ │ SQL #2  │ │ SQL #3  │ │ SQL #4  │ │ SQL #5 │ │
│  │ t=0.7   │ │ t=0.7   │ │ t=0.7   │ │ t=0.7   │ │ t=0.7  │ │
│  │ seed=1  │ │ seed=2  │ │ seed=3  │ │ seed=4  │ │ seed=5 │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └───┬────┘ │
└───────┼───────────┼───────────┼───────────┼────────────┼──────┘
        │           │           │           │            │
        ▼           ▼           ▼           ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Check-Correct Pipeline                       │
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  Check #1   │───►│   Correct   │───►│  Validate   │      │
│  │  Syntax     │    │   if Error  │    │   Result    │      │
│  └─────────────┘    └─────────────┘    └──────┬──────┘      │
│                                               │              │
│  ┌────────────────────────────────────────────┘              │
│  │ (迭代最多3次)                                              │
│  ▼                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  Check #2   │───►│   Correct   │───►│  Validate   │      │
│  │  Execution  │    │   if Error  │    │   Result    │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
        │           │           │           │            │
        ▼           ▼           ▼           ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Vote@K Aggregation                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              结果标准化与比较                        │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │    │
│  │  │ Result 1│  │ Result 2│  │ Result 3│  ...         │    │
│  │  │ (valid) │  │ (valid) │  │ (valid) │              │    │
│  │  └────┬────┘  └────┬────┘  └────┬────┘              │    │
│  │       └─────────────┴─────────────┘                  │    │
│  │                    │                                 │    │
│  │                    ▼                                 │    │
│  │       ┌─────────────────────────┐                    │    │
│  │       │    相似度矩阵计算        │                    │    │
│  │       │  ┌───┬───┬───┬───┬───┐  │                    │    │
│  │       │  │1.0│0.8│0.3│0.7│0.2│  │                    │    │
│  │       │  ├───┼───┼───┼───┼───┤  │                    │    │
│  │       │  │0.8│1.0│0.4│0.9│0.3│  │                    │    │
│  │       │  └───┴───┴───┴───┴───┘  │                    │    │
│  │       └─────────────────────────┘                    │    │
│  │                    │                                 │    │
│  │                    ▼                                 │    │
│  │       ┌─────────────────────────┐                    │    │
│  │       │    共识集群识别          │                    │    │
│  │       │  集群1: [0, 1, 3] (3个) │                    │    │
│  │       │  集群2: [2] (1个)       │                    │    │
│  │       │  集群3: [4] (1个)       │                    │    │
│  │       └─────────────────────────┘                    │    │
│  │                    │                                 │    │
│  │                    ▼                                 │    │
│  │       ┌─────────────────────────┐                    │    │
│  │       │    选出最佳结果          │                    │    │
│  │       │  Winner: Candidate #1   │                    │    │
│  │       │  Confidence: 0.8        │                    │    │
│  │       └─────────────────────────┘                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   最终输出    │
                    │  SQL + 结果   │
                    │  + 置信度     │
                    └───────────────┘
```

### 5.2 统一API接口

```yaml
POST /api/v1/query/advanced-inference

Request:
  {
    "natural_language": "查询2024年销售额最高的前10个产品",
    "schema_id": "schema-001",
    "connection_id": "conn-001",
    "inference_config": {
      "pass_at_k": {
        "enabled": true,
        "k": 5,
        "temperature": 0.7
      },
      "check_correct": {
        "enabled": true,
        "max_iterations": 3,
        "execution_timeout": 30
      },
      "vote_at_k": {
        "enabled": true,
        "strategy": "consensus",  # consensus | weighted
        "consensus_threshold": 0.6,
        "weights": {
          "execution_success": 0.3,
          "non_empty_result": 0.2,
          "execution_time": 0.15,
          "simplicity": 0.15,
          "llm_confidence": 0.2
        }
      }
    }
  }

Response:
  {
    "query_id": "query-789",
    "status": "success",
    "result": {
      "sql": "SELECT p.product_name, SUM(s.amount) as total_sales FROM products p JOIN sales s ON p.id = s.product_id WHERE s.year = 2024 GROUP BY p.product_name ORDER BY total_sales DESC LIMIT 10",
      "execution_result": {
        "columns": ["product_name", "total_sales"],
        "rows": [...],
        "row_count": 10,
        "execution_time": 0.156
      },
      "confidence": 0.85,
      "inference_metadata": {
        "pass_at_k": {
          "candidates_generated": 5,
          "syntax_valid": 4,
          "execution_valid": 3
        },
        "check_correct": {
          "total_corrections": 2,
          "correction_history": [...]
        },
        "vote_at_k": {
          "strategy": "consensus",
          "consensus_size": 3,
          "alternative_candidates": 2
        }
      }
    },
    "execution_time_ms": 3456
  }
```

---

## 6. 性能优化

### 6.1 并行执行策略

```python
class ParallelExecutor:
    """并行执行管理器"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)

    async def execute_candidates(
        self,
        candidates: List[str],
        executor_func: Callable,
        **kwargs
    ) -> List[ExecutionResult]:
        """并行执行候选SQL"""

        async def _execute_with_limit(candidate):
            async with self.semaphore:
                return await executor_func(candidate, **kwargs)

        tasks = [_execute_with_limit(c) for c in candidates]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### 6.2 缓存策略

```python
class InferenceCache:
    """推理结果缓存"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1小时

    async def get_cached_result(
        self,
        question_hash: str,
        schema_version: str
    ) -> Optional[CachedInferenceResult]:
        """获取缓存的推理结果"""
        key = f"inference:{schema_version}:{question_hash}"
        data = await self.redis.get(key)
        if data:
            return CachedInferenceResult.parse_raw(data)
        return None

    async def cache_result(
        self,
        question_hash: str,
        schema_version: str,
        result: InferenceResult
    ):
        """缓存推理结果"""
        key = f"inference:{schema_version}:{question_hash}"
        await self.redis.setex(
            key,
            self.ttl,
            result.json()
        )
```

### 6.3 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| Pass@K生成 | < 3s (k=5) | 并行生成k个候选 |
| Check-Correct迭代 | < 2s/轮 | 单次检查-修正循环 |
| Vote@K聚合 | < 500ms | 结果比较与投票 |
| 完整流程 | < 10s | 端到端推理时间 |
| 缓存命中率 | > 30% | 相似问题复用 |

---

## 7. 错误处理与降级

### 7.1 降级策略

```python
class InferenceFallback:
    """推理降级处理器"""

    async def execute_with_fallback(
        self,
        natural_language: str,
        schema: Dict[str, Any]
    ) -> InferenceResult:
        """
        带降级的高级推理执行

        降级链:
        1. 完整流程 (Pass@K + Check-Correct + Vote@K)
        2. 简化流程 (Pass@K + Vote@K)
        3. 基础生成 (单次生成)
        4. 错误返回
        """

        try:
            # 尝试完整流程
            return await self._full_pipeline(natural_language, schema)
        except Exception as e:
            logger.warning(f"Full pipeline failed: {e}")

        try:
            # 降级到简化流程
            return await self._simplified_pipeline(natural_language, schema)
        except Exception as e:
            logger.warning(f"Simplified pipeline failed: {e}")

        try:
            # 降级到基础生成
            return await self._basic_generation(natural_language, schema)
        except Exception as e:
            logger.error(f"All pipelines failed: {e}")

            # 返回错误结果
            return InferenceResult(
                success=False,
                error="推理服务暂时不可用，请稍后重试",
                fallback_used=True
            )
```

---

## 8. 监控与日志

### 8.1 关键指标

```python
INFERENCE_METRICS = {
    # 成功率指标
    "inference_success_rate": Gauge("成功率"),
    "pass_at_k_rate": Gauge("Pass@K值"),
    "correction_success_rate": Gauge("修正成功率"),
    "vote_consensus_rate": Gauge("投票共识率"),

    # 性能指标
    "inference_latency": Histogram("推理延迟"),
    "generation_latency": Histogram("生成延迟"),
    "correction_latency": Histogram("修正延迟"),
    "voting_latency": Histogram("投票延迟"),

    # 质量指标
    "candidates_per_query": Counter("每查询候选数"),
    "corrections_per_query": Counter("每查询修正数"),
    "cache_hit_rate": Gauge("缓存命中率")
}
```

### 8.2 日志规范

```python
# 结构化日志记录
logger.info(
    "inference_completed",
    extra={
        "query_id": query_id,
        "inference_type": "advanced",
        "k": config.k,
        "iterations": len(correction_history),
        "winner_confidence": result.confidence,
        "latency_ms": total_time,
        "cache_hit": cache_hit,
        "fallback_used": fallback_used
    }
)
```

---

## 9. 实现里程碑

### 9.1 阶段划分

| 阶段 | 功能 | 预计工期 | 依赖 |
|------|------|----------|------|
| **Phase 1** | Pass@K基础实现 | 3天 | LLM服务 |
| **Phase 2** | SQL Checker实现 | 4天 | 数据库连接 |
| **Phase 3** | SQL Corrector实现 | 5天 | Phase 2 |
| **Phase 4** | Check-Correct整合 | 3天 | Phase 1-3 |
| **Phase 5** | Vote@K实现 | 4天 | Phase 1 |
| **Phase 6** | 完整流程整合 | 3天 | Phase 4-5 |
| **Phase 7** | 性能优化 | 3天 | Phase 6 |
| **Phase 8** | E2E测试与调优 | 5天 | Phase 7 |

**总计**: 约30天

---

## 10. 附录

### 10.1 术语表

| 术语 | 说明 |
|------|------|
| **Pass@K** | 从k个候选中至少有一个正确的概率 |
| **Check-Correct** | 迭代检查-修正机制 |
| **Vote@K** | 多候选结果投票聚合机制 |
| **Consensus** | 共识，指多个结果之间的一致性 |
| **Temperature** | LLM采样温度，控制输出多样性 |

### 10.2 参考资料

1. **Pass@K论文**: Chen, M., et al. "Evaluating Large Language Models Trained on Code." arXiv:2107.03374
2. **Self-Debug**: Chen, X., et al. "Teaching Large Language Models to Self-Debug." arXiv:2304.05128
3. **DiVeRSe**: Li, Y., et al. "Advancing Large Language Model Reasoning via Multi-Agent Diverse Reflection." arXiv:2311.18585
4. **CodiumAI**: https://www.codium.ai/blog/what-is-code-coverage-and-code-coverage-tools/

---

*文档结束*
