# 高级推理功能 - 业务逻辑文档

## 0. 核心概念区分

在使用高级推理功能前，需要明确区分**推理手段**（生成 SQL 的方式）和**评测手段**（评估结果的方式）这两个层次：

### 0.1 推理手段（Inference Methods）

推理手段定义了**如何生成** SQL 查询：

| 推理手段 | 说明 | 参数 |
|----------|------|------|
| **Single/Greedy** | temperature=0，单次确定性生成，输出最可能的 SQL | `temperature=0`, `n=1` |
| **Sampling** | temperature>0，并行生成 K 个候选 SQL，引入随机性 | `temperature>0`, `n=K` |
| **Check-Correct** | Generator-Checker-Corrector 迭代循环，自我修正 | `max_iterations>1` |

### 0.2 评测手段（Evaluation Methods）

评测手段定义了**如何评估**生成的 SQL 是否正确：

| 评测手段 | 说明 | 适用场景 |
|----------|------|----------|
| **Greedy Search** | 评估单次生成结果 | 快速评估、生产查询 |
| **Pass@K** | K 次采样中任一正确即算成功 | 评估模型潜力上限 |
| **Majority Voting** | K 次采样中按执行结果投票选择 | 提高输出稳定性 |

### 0.3 组合策略（Composite Strategies）

在实际应用中，我们通常使用**组合策略**来完成特定任务。组合策略 = 推理手段 + 评测手段：

| 组合策略 | 推理手段 | 评测手段 | ICED-2026 命令行示例 | 说明 |
|----------|----------|----------|---------------------|------|
| **vote@k** | Sampling (n=K) | Majority Voting | `infer.py --n 8` + `evaluate_bird.py --mode major_voting` | K次采样后投票选择最佳SQL |
| **pass@k** | Sampling (n=K) | Pass@K | `infer.py --n 8` + `evaluate_bird.py --mode pass_at_k` | K次采样中任一正确即算成功 |
| Single/Greedy | Single/Greedy | Greedy Search | `infer.py --n 1` + `evaluate_bird.py --mode greedy_search` | 单次生成单次评测 |
| Check-Correct | Check-Correct | Greedy Search | `lc_text_to_sql_pipeline.py --rounds 3` | 迭代修正后评测最终结果 |

**关键理解**：
- `vote@k` 和 `pass@k` **不是**独立的手段，而是 **Sampling 推理**配合不同**评测手段**的组合
- `--n` 参数控制推理阶段的采样次数
- `--mode` 参数控制评测阶段的评估方式
- 两者配合形成完整的组合策略

### 0.4 推理与评测的组合关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      推理手段 × 评测手段 组合矩阵                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Single/Greedy  │  │    Sampling     │  │  Check-Correct  │         │
│  │   (推理手段)     │  │   (推理手段)     │  │   (推理手段)     │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                  │
│           ▼                    ▼                    ▼                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Greedy Search  │  │    Pass@K       │  │  Greedy Search  │         │
│  │   (评测手段)     │  │   (评测手段)     │  │   (评测手段)     │         │
│  │                 │  │                 │  │                 │         │
│  │  结果: 单次结果  │  │  结果: 任一通过  │  │  结果: 迭代收敛  │         │
│  │  用途: 生产查询  │  │  用途: 评估潜力  │  │  用途: 高精度输出│         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐                              │
│  │  Single/Greedy  │  │    Sampling     │                              │
│  │   (推理手段)     │  │   (推理手段)     │                              │
│  └────────┬────────┘  └────────┬────────┘                              │
│           │                    │                                       │
│           ▼                    ▼                                       │
│  ┌─────────────────┐  ┌─────────────────┐                              │
│  │      N/A        │  │ Majority Voting │                              │
│  │   (评测手段)     │  │   (评测手段)     │                              │
│  │                 │  │                 │                              │
│  │  (无需投票)      │  │  结果: 多数表决  │                              │
│  │                 │  │  用途: 稳定输出  │                              │
│  └─────────────────┘  └─────────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**典型组合示例**：

| 组合策略 | 推理手段 | 评测手段 | 输出 | 适用场景 |
|----------|----------|----------|------|----------|
| **pass@8** | Sampling (n=8) | Pass@K | 准确率指标 | 评估模型潜力上限 |
| **vote@8** | Sampling (n=8) | Majority Voting | 最稳定的 SQL | 提高生产环境稳定性 |
| Check-Correct | Check-Correct (iter=3) | Greedy Search | 修正后的 SQL | 高精度单条查询 |
| Single/Greedy | Single/Greedy | Greedy Search | 单次 SQL | 快速响应场景 |

> **命名约定**：
> - `vote@k`：ICED-2026 中常用的组合策略简称，表示 K 次采样 + 多数投票
> - `pass@k`：ICED-2026 中常用的组合策略简称，表示 K 次采样 + 通过任一即成功

---

## 1. 业务流程图

### 1.1 Pass@K 评测流程（基于 Sampling 推理）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Pass@K 推理流程                                      │
└─────────────────────────────────────────────────────────────────────────────┘

用户输入
    │
    ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   配置参数      │───▶│   K次采样生成   │───▶│   并行执行候选  │
│  (K,Temperature)│    │  (并行调用LLM)  │    │  (并发执行SQL)  │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   返回最佳结果  │◀───│   结果对比      │◀───│   正确性验证    │
│  (首个正确SQL)  │    │  (EX指标验证)   │    │  (与黄金SQL对比)│
└─────────────────┘    └─────────────────┘    └─────────────────┘

详细流程:
=========

输入阶段:
┌──────────────┐
│   用户问题    │
│  数据库连接   │
│ Schema信息   │
└──────┬───────┘
       │
       ▼
配置阶段:
┌─────────────────────────────────────┐
│  k_candidates: 1/4/8/16            │
│  temperature: 0.0 - 1.0            │
│  max_tokens: 2048                  │
│  timeout_per_sql: 30s              │
└─────────────────────────────────────┘
       │
       ▼
采样阶段 (并行):
┌──────────┐  ┌──────────┐  ┌──────────┐       ┌──────────┐
│ 采样 #1  │  │ 采样 #2  │  │ 采样 #3  │  ...  │ 采样 #K  │
│ SQL_1    │  │ SQL_2    │  │ SQL_3    │       │ SQL_K    │
└────┬─────┘  └────┬─────┘  └────┬─────┘       └────┬─────┘
     │             │             │                  │
     └─────────────┴─────────────┴──────────────────┘
                          │
                          ▼
执行阶段 (并行):
┌──────────┐  ┌──────────┐  ┌──────────┐       ┌──────────┐
│ 执行 #1  │  │ 执行 #2  │  │ 执行 #3  │  ...  │ 执行 #K  │
│ 结果/错误│  │ 结果/错误│  │ 结果/错误│       │ 结果/错误│
└────┬─────┘  └────┬─────┘  └────┬─────┘       └────┬─────┘
     │             │             │                  │
     └─────────────┴─────────────┴──────────────────┘
                          │
                          ▼
验证阶段:
┌─────────────────────────────────────────────────────────┐
│  for each candidate:                                    │
│    correctness = verify_with_except(sql_i, gold_sql)    │
│    if correctness == 1:                                 │
│      return sql_i  ← 首个正确的候选                      │
│                                                         │
│  if all failed:                                         │
│    return best_candidate_or_null                        │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Check-Correct 推理流程（搭配 Greedy 评测）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Check-Correct 推理流程（搭配 Greedy 评测）                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   初始生成    │
│  (SQL_0)     │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────┐
│   执行检查    │────▶│  正确?   │
│  (执行+验证)  │     └────┬─────┘
└──────────────┘          │
                          │ 是
                          ▼
                   ┌──────────────┐
                   │   返回结果    │
                   │  (SQL_final) │
                   └──────────────┘
                          │
                          │ 否
                          ▼
                   ┌──────────────┐
                   │   错误分析    │
                   │ - 语法错误   │
                   │ - 执行错误   │
                   │ - 语义错误   │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  生成修正Prompt│
                   │ (基于错误类型) │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   LLM修正    │
                   │  (SQL_n+1)   │
                   └──────┬───────┘
                          │
                          │ (循环)
                          └───────────────────────┐
                                                  │
       ┌──────────────────────────────────────────┘
       │
       ▼
终止条件检查:
┌─────────────────────────────────────────────────────────┐
│  1. Checker 返回 CORRECT? ──▶ 返回结果                  │
│  2. 达到 max_iterations? ───▶ 返回最佳尝试              │
│  3. 超时? ─────────────────▶ 返回当前结果               │
│  4. 连续无改进? ───────────▶ 提前停止                   │
└─────────────────────────────────────────────────────────┘

迭代状态流转:
================

迭代 0: 初始生成
┌──────────┐    ┌──────────┐    ┌──────────┐
│Generator │───▶│ Executor │───▶│ Checker  │
│  SQL_0   │    │ 执行验证  │    │ 判断结果  │
└──────────┘    └──────────┘    └────┬─────┘
                                     │
                        CORRECT ─────┴─────▶ 结束
                        ERROR ─────────────▶ 迭代 1

迭代 N: 修正循环
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Corrector │───▶│ Executor │───▶│ Checker  │───▶│ 终止检查  │
│ SQL_N    │    │ 执行验证  │    │ 判断结果  │    │ 条件判断  │
└──────────┘    └──────────┘    └────┬─────┘    └────┬─────┘
                                     │               │
                        CORRECT ─────┴───────────────┘ 结束
                        ERROR ─────────────────────────▶ 迭代 N+1
```

### 1.3 Majority Voting 评测流程（基于 Sampling 推理）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Majority Voting 评测流程（基于 Sampling 推理）           │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   K次采样    │
│ (SQL_1..K)  │
└──────┬───────┘
       │
       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   执行所有候选  │───▶│  按结果哈希分组  │───▶│   统计票数      │
│  (并行执行)     │    │  (相同结果归组)  │    │  (votes计数)    │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   返回SQL       │◀───│   选择最高票    │◀───│   平票处理      │
│  (winner.sql)   │    │  (max votes)    │    │  (选择策略)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘

详细步骤:
=========

Step 1: 采样与执行
┌────────┐  ┌────────┐  ┌────────┐       ┌────────┐
│ SQL_1  │  │ SQL_2  │  │ SQL_3  │  ...  │ SQL_K  │
└───┬────┘  └───┬────┘  └───┬────┘       └───┬────┘
    │           │           │                │
    ▼           ▼           ▼                ▼
┌────────┐  ┌────────┐  ┌────────┐       ┌────────┐
│执行结果 │  │执行结果 │  │执行结果 │       │执行结果 │
│Result_1│  │Result_2│  │Result_3│  ...  │Result_K│
│成功/失败│  │成功/失败│  │成功/失败│       │成功/失败│
└───┬────┘  └───┬────┘  └───┬────┘       └───┬────┘
    │           │           │                │
    └───────────┴───────────┴────────────────┘
                    │
                    ▼

Step 2: 结果哈希与分组
┌─────────────────────────────────────────────────────────────┐
│  对执行成功的结果进行哈希:                                    │
│  hash_i = hash(result_i.rows + result_i.columns)             │
│                                                             │
│  分组示例:                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Group A (hash=0xABC): SQL_1, SQL_3, SQL_7  → 3票   │   │
│  │ Group B (hash=0xDEF): SQL_2, SQL_5       → 2票     │   │
│  │ Group C (hash=0x123): SQL_4              → 1票     │   │
│  │ Failed: SQL_6, SQL_8                     → 0票     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

Step 3: 胜者与置信度
┌─────────────────────────────────────────────────────────────┐
│  Winner = Group A (最高票数)                                 │
│  Winner SQL = SQL_1 (组内第一个)                             │
│                                                             │
│  置信度计算:                                                │
│  confidence = (max_votes / total_valid) * (success / total) │
│             = (3 / 6) * (6 / 8)                             │
│             = 0.5 * 0.75 = 0.375 (37.5%)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 状态机图

### 2.1 高级推理任务状态机

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        高级推理任务状态流转                                   │
└─────────────────────────────────────────────────────────────────────────────┘

Pass@K 任务状态机 (评测层 - 基于Sampling推理):
================================================

                    ┌─────────────┐
         ┌─────────│   PENDING   │◀────────┐
         │         │  (等待处理)  │         │
         │         └──────┬──────┘         │
         │                │ 开始采样        │
         │                ▼                │
         │         ┌─────────────┐         │
         │         │  SAMPLING   │         │
         │         │ (K次采样中)  │         │
         │         └──────┬──────┘         │
         │                │ 采样完成        │
         │                ▼                │
         │         ┌─────────────┐         │
    重试 │    ┌───▶│  EXECUTING  │◀───┐    │
         │    │    │(并行执行中) │    │    │
         │    │    └──────┬──────┘    │    │
         │    │           │           │    │
         │    │ 部分成功   │   全部失败│重试 │
         │    │           │           │    │
         │    │           ▼           │    │
         │    │    ┌─────────────┐    │    │
         │    └───▶│  VERIFYING  │────┘    │
         │         │(验证正确性) │         │
         │         └──────┬──────┘         │
         │                │                │
         │      通过      │     未通过      │
         │                │                │
         │                ▼                │
         │         ┌─────────────┐         │
         └────────▶│   SUCCESS   │─────────┘
                   │  (任一通过)  │
                   └─────────────┘
                          │
              全部失败     │
                          ▼
                   ┌─────────────┐
                   │    FAILED   │
                   │  (全部失败)  │
                   └─────────────┘

Check-Correct 任务状态机 (推理层 - 迭代修正):
==============================================

                    ┌─────────────┐
         ┌─────────│   PENDING   │◀────────┐
         │         │  (等待处理)  │         │
         │         └──────┬──────┘         │
         │                │ 开始生成        │
         │                ▼                │
         │         ┌─────────────┐         │
         │         │  GENERATING │         │
         │         │ (生成SQL)   │         │
         │         └──────┬──────┘         │
         │                │ 生成完成        │
         │                ▼                │
         │         ┌─────────────┐         │
         │         │  EXECUTING  │         │
         │         │ (执行SQL)   │         │
         │         └──────┬──────┘         │
         │                │ 执行完成        │
         │                ▼                │
         │         ┌─────────────┐         │
         │    ┌───▶│  CHECKING   │◀───┐    │
         │    │    │(检查正确性) │    │    │
         │    │    └──────┬──────┘    │    │
         │    │           │           │    │
    正确  │    │ 不正确    │   超时    │重试 │
         │    │           │           │    │
         │    │           ▼           │    │
         │    │    ┌─────────────┐    │    │
         │    └───▶│ CORRECTING  │────┘    │
         │         │(修正SQL)    │         │
         │         └──────┬──────┘         │
         │                │                │
         │                │ 达到最大迭代    │
         │                ▼                │
         │         ┌─────────────┐         │
         └────────▶│   SUCCESS   │─────────┘
                   │  (检查通过)  │
                   └─────────────┘
                          │
              达到最大迭代  │
              仍未正确      │
                          ▼
                   ┌─────────────┐
                   │   PARTIAL   │
                   │(部分成功/    │
                   │最佳尝试)     │
                   └─────────────┘

状态说明:
=========

| 状态 | 说明 | 触发条件 | 下一状态 |
|------|------|----------|----------|
| PENDING | 等待处理 | 任务创建 | SAMPLING/GENERATING |
| SAMPLING | K次采样中 | Pass@K开始 | EXECUTING |
| GENERATING | 生成SQL | Check-Correct开始 | EXECUTING |
| EXECUTING | 执行SQL | 生成完成 | CHECKING/VERIFYING |
| CHECKING | 检查正确性 | 执行完成 | SUCCESS/CORRECTING |
| VERIFYING | 验证正确性 | 执行完成 | SUCCESS/FAILED |
| CORRECTING | 修正SQL | 检查未通过 | EXECUTING/PARTIAL |
| SUCCESS | 成功完成 | 检查通过/任一通过 | - |
| PARTIAL | 部分成功 | 达到最大迭代 | - |
| FAILED | 全部失败 | 全部采样失败 | - |
```

---

## 3. 核心算法详解

> **算法分类说明**：
> - **推理层算法**：定义如何生成 SQL（Sampling、Check-Correct）
> - **评测层算法**：定义如何评估 SQL 正确性（Pass@K、Majority Voting）

### 3.1 Pass@K 评测算法（评测层）

**算法分类**：评测层算法（基于 Sampling 推理层）

**算法描述：**
K次采样中只要有一次正确即算通过，最终计算所有问题的通过率。

**与推理层的关系：**
```
┌─────────────────────────────────────────────────────────┐
│  Sampling 推理层 (K次并行生成)                           │
│  ┌─────────┐ ┌─────────┐       ┌─────────┐             │
│  │ SQL_1   │ │ SQL_2   │  ...  │ SQL_K   │             │
│  └────┬────┘ └────┬────┘       └────┬────┘             │
│       └───────────┴───────────────────┘                 │
│                   │                                     │
│                   ▼ (输入到评测层)                       │
├─────────────────────────────────────────────────────────┤
│  Pass@K 评测层                                          │
│  ┌─────────────────────────────────────────┐             │
│  │ 验证每个候选的正确性 (vs 黄金SQL)        │             │
│  │ 任一正确即算通过 ✓                      │             │
│  └─────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

**伪代码实现：**

```python
def pass_at_k_evaluate(
    questions: List[str],
    gold_sqls: List[str],
    db_connections: List[int],
    k: int = 8,
    temperature: float = 0.8,
    max_tokens: int = 2048
) -> PassAtKResult:
    """
    Pass@K 评估算法

    Args:
        questions: 自然语言问题列表
        gold_sqls: 黄金SQL列表
        db_connections: 数据库连接ID列表
        k: 采样次数
        temperature: 采样温度
        max_tokens: 最大生成长度

    Returns:
        PassAtKResult: 包含准确率和详细结果
    """
    results = []

    for question, gold_sql, conn_id in zip(questions, gold_sqls, db_connections):
        # 1. K次并行采样生成
        candidates = parallel_generate(
            question=question,
            connection_id=conn_id,
            n=k,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # 2. 并行执行所有候选SQL
        execution_results = parallel_execute(
            sqls=candidates,
            connection_id=conn_id,
            timeout=30
        )

        # 3. 验证每个候选的正确性
        candidate_correctness = []
        for sql, exec_result in zip(candidates, execution_results):
            if not exec_result.success:
                candidate_correctness.append({
                    "sql": sql,
                    "correct": False,
                    "error": exec_result.error
                })
                continue

            # 使用 EXCEPT 进行结果对比
            correctness = verify_with_except(
                pred_sql=sql,
                gold_sql=gold_sql,
                connection_id=conn_id
            )
            candidate_correctness.append({
                "sql": sql,
                "correct": correctness == 1,
                "result_hash": hash_result(exec_result.data)
            })

        # 4. 任一通过即算成功
        is_passed = any(c["correct"] for c in candidate_correctness)

        # 5. 选择首个正确的作为结果
        best_sql = None
        for c in candidate_correctness:
            if c["correct"]:
                best_sql = c["sql"]
                break

        results.append({
            "question": question,
            "passed": is_passed,
            "best_sql": best_sql,
            "candidates": candidate_correctness,
            "pass_at_1": any(c["correct"] for c in candidate_correctness[:1]),
            "pass_at_k": is_passed
        })

    # 6. 计算整体准确率
    pass_at_k_accuracy = sum(r["passed"] for r in results) / len(results)

    return PassAtKResult(
        accuracy=pass_at_k_accuracy,
        total=len(results),
        passed=sum(r["passed"] for r in results),
        details=results
    )


def verify_with_except(pred_sql: str, gold_sql: str, connection_id: int) -> int:
    """
    使用 SQL EXCEPT 验证正确性

    Returns:
        1: 正确
        0: 错误
    """
    conn = get_connection(connection_id)
    cursor = conn.cursor()

    try:
        conn.execute("BEGIN TRANSACTION")

        # 使用 EXCEPT 进行集合差运算
        sql_eq = f"""
            SELECT CASE
                WHEN EXISTS(
                    SELECT 1 FROM ({pred_sql}) EXCEPT SELECT * FROM ({gold_sql})
                ) THEN 0
                WHEN EXISTS(
                    SELECT 1 FROM ({gold_sql}) EXCEPT SELECT * FROM ({pred_sql})
                ) THEN 0
                ELSE 1
            END
        """

        cursor.execute(sql_eq)
        row = cursor.fetchone()
        correctness = int(row[0]) if row and row[0] is not None else 0

        conn.rollback()
        return correctness

    except Exception as e:
        conn.rollback()
        logger.error(f"Verification error: {e}")
        return 0
    finally:
        cursor.close()
```

**并行执行策略：**

```python
def parallel_generate(
    question: str,
    connection_id: int,
    n: int,
    temperature: float,
    max_tokens: int
) -> List[str]:
    """并行生成 K 个候选 SQL"""

    async def generate_one(idx: int) -> str:
        # 添加随机种子确保多样性
        seed = random.randint(0, 10000)
        response = await llm_client.generate(
            prompt=build_prompt(question, connection_id),
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed
        )
        return extract_sql(response)

    # 并发执行 K 次生成
    tasks = [generate_one(i) for i in range(n)]
    return await asyncio.gather(*tasks)


def parallel_execute(
    sqls: List[str],
    connection_id: int,
    timeout: int = 30
) -> List[ExecutionResult]:
    """并行执行多个 SQL"""

    async def execute_one(sql: str) -> ExecutionResult:
        try:
            result = await execute_sql(
                sql=sql,
                connection_id=connection_id,
                timeout=timeout
            )
            return ExecutionResult(success=True, data=result)
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    # 使用信号量限制并发数
    semaphore = asyncio.Semaphore(4)  # 最多4个并发

    async def execute_with_limit(sql: str) -> ExecutionResult:
        async with semaphore:
            return await execute_one(sql)

    tasks = [execute_with_limit(sql) for sql in sqls]
    return await asyncio.gather(*tasks)
```

**结果对比逻辑：**

```python
def hash_result(result: QueryResult) -> str:
    """
    对查询结果进行哈希，用于快速比较
    """
    # 将结果转换为标准化字符串
    result_str = json.dumps({
        "columns": result.columns,
        "rows": [tuple(row) for row in result.rows]
    }, sort_keys=True, default=str)

    return hashlib.md5(result_str.encode()).hexdigest()


def compare_results(result1: QueryResult, result2: QueryResult) -> bool:
    """
    比较两个查询结果是否等价
    """
    # 方法1: 哈希比较 (快速)
    if hash_result(result1) == hash_result(result2):
        return True

    # 方法2: 集合比较 (精确，处理无序情况)
    set1 = set(tuple(row) for row in result1.rows)
    set2 = set(tuple(row) for row in result2.rows)
    return set1 == set2
```

### 3.2 多数投票算法（评测层）

**算法分类**：评测层算法（基于 Sampling 推理层）

**算法描述：**
基于执行结果哈希进行投票，选择票数最多的结果，并计算置信度。

**与 Pass@K 的区别：**
| 对比项 | Pass@K | Majority Voting |
|--------|--------|-----------------|
| **评测目标** | 评估模型潜力 | 选择最稳定输出 |
| **输出** | 准确率指标 | 最佳 SQL |
| **适用场景** | 模型评估 | 生产环境 |
| **黄金SQL** | 需要 | 不需要 |

**伪代码实现：**

```python
def majority_voting_enhanced(
    candidates: List[Candidate],
    all_fail_strategy: str = "trigger_correction"
) -> VotingResult:
    """
    增强的多数投票算法

    Args:
        candidates: 候选列表，每个包含 sql, result, success
        all_fail_strategy: 全失败处理策略
            - "return_empty": 返回空结果
            - "return_random": 随机返回一个候选
            - "return_last": 返回最后一个候选
            - "trigger_correction": 触发 Check-Correct 流程

    Returns:
        VotingResult: 投票结果和置信度
    """
    # 1. 过滤执行成功的候选
    valid_candidates = [c for c in candidates if c.success and c.result is not None]
    total_count = len(candidates)
    success_count = len(valid_candidates)

    # 2. 全部失败处理
    if success_count == 0:
        return handle_all_fail(candidates, all_fail_strategy)

    # 3. 按执行结果哈希分组
    result_groups: Dict[str, ResultGroup] = {}
    for candidate in valid_candidates:
        result_hash = hash_result(candidate.result)

        if result_hash not in result_groups:
            result_groups[result_hash] = ResultGroup(
                hash=result_hash,
                votes=0,
                sqls=[],
                result=candidate.result
            )

        result_groups[result_hash].votes += 1
        result_groups[result_hash].sqls.append(candidate.sql)

    # 4. 选择票数最多的组
    winner_group = max(result_groups.values(), key=lambda g: g.votes)

    # 5. 平票处理
    max_votes = winner_group.votes
    tied_groups = [g for g in result_groups.values() if g.votes == max_votes]

    if len(tied_groups) > 1:
        # 平票时选择第一个出现的
        winner_group = tied_groups[0]
        is_tie = True
    else:
        is_tie = False

    # 6. 置信度计算
    confidence = calculate_confidence(
        max_votes=winner_group.votes,
        total_valid=success_count,
        success_count=success_count,
        total_samples=total_count,
        is_tie=is_tie
    )

    return VotingResult(
        winner_sql=winner_group.sqls[0],  # 返回组内第一个SQL
        winner_result=winner_group.result,
        votes=winner_group.votes,
        total_valid=success_count,
        confidence=confidence,
        is_tie=is_tie,
        all_groups=list(result_groups.values())
    )


def calculate_confidence(
    max_votes: int,
    total_valid: int,
    success_count: int,
    total_samples: int,
    is_tie: bool
) -> float:
    """
    计算置信度

    公式: confidence = vote_ratio * success_ratio * tie_penalty
    """
    # 投票比例
    vote_ratio = max_votes / total_valid if total_valid > 0 else 0

    # 执行成功率
    success_ratio = success_count / total_samples if total_samples > 0 else 0

    # 平票惩罚
    tie_penalty = 0.8 if is_tie else 1.0

    # 综合置信度
    confidence = vote_ratio * success_ratio * tie_penalty

    return round(confidence, 4)


def handle_all_fail(
    candidates: List[Candidate],
    strategy: str
) -> VotingResult:
    """处理全部执行失败的情况"""

    if strategy == "return_empty":
        return VotingResult(
            winner_sql=None,
            winner_result=None,
            votes=0,
            total_valid=0,
            confidence=0.0,
            error="All candidates failed to execute"
        )

    elif strategy == "return_random":
        winner = random.choice(candidates)
        return VotingResult(
            winner_sql=winner.sql,
            winner_result=None,
            votes=0,
            total_valid=0,
            confidence=0.0,
            error=f"Random selection from {len(candidates)} failed candidates"
        )

    elif strategy == "return_last":
        winner = candidates[-1]
        return VotingResult(
            winner_sql=winner.sql,
            winner_result=None,
            votes=0,
            total_valid=0,
            confidence=0.0,
            error="Last candidate selected (all failed)"
        )

    elif strategy == "trigger_correction":
        return VotingResult(
            winner_sql=None,
            winner_result=None,
            votes=0,
            total_valid=0,
            confidence=0.0,
            needs_correction=True,
            candidates=candidates,
            error="All candidates failed, correction needed"
        )

    else:
        raise ValueError(f"Unknown strategy: {strategy}")
```

### 3.3 SQL 检查与修正算法（推理层）

**算法分类**：推理层算法（Generator-Checker-Corrector 迭代）

**算法描述：**
通过 Checker 模块检查 SQL 正确性，通过 Corrector 模块根据错误类型进行修正，支持多轮迭代。

**与 Sampling 的区别：**
| 对比项 | Sampling | Check-Correct |
|--------|----------|---------------|
| **核心思想** | 并行尝试多个候选 | 迭代修正单个候选 |
| **资源消耗** | K倍 LLM 调用 | 最多 iter 倍 LLM 调用 |
| **适用场景** | 评估模型能力 | 高精度生产环境 |
| **输出稳定性** | 依赖投票策略 | 自我收敛 |
| **黄金SQL** | Pass@K需要 | 不需要（自检）|

**伪代码实现：**

```python
class SQLChecker:
    """SQL 正确性检查器"""

    async def check(
        self,
        question: str,
        sql: str,
        schema: SchemaInfo,
        execution_result: Optional[ExecutionResult] = None
    ) -> CheckResult:
        """
        检查 SQL 的正确性

        Returns:
            CheckResult: 检查结果，包含是否正确、错误类型、说明
        """
        # 1. 语法检查
        syntax_error = self._check_syntax(sql)
        if syntax_error:
            return CheckResult(
                is_correct=False,
                error_type=ErrorType.SYNTAX_ERROR,
                explanation=syntax_error
            )

        # 2. 执行检查 (如果有执行结果)
        if execution_result:
            if not execution_result.success:
                return CheckResult(
                    is_correct=False,
                    error_type=ErrorType.EXECUTION_ERROR,
                    explanation=execution_result.error
                )

        # 3. 语义检查 (使用 LLM)
        semantic_result = await self._check_semantic(
            question=question,
            sql=sql,
            schema=schema,
            execution_result=execution_result
        )

        return semantic_result

    def _check_syntax(self, sql: str) -> Optional[str]:
        """语法检查"""
        try:
            # 使用 sqlparse 进行语法解析
            parsed = sqlparse.parse(sql)
            if not parsed or not parsed[0].tokens:
                return "Empty or invalid SQL"
            return None
        except Exception as e:
            return f"Syntax error: {str(e)}"

    async def _check_semantic(
        self,
        question: str,
        sql: str,
        schema: SchemaInfo,
        execution_result: Optional[ExecutionResult]
    ) -> CheckResult:
        """语义检查"""

        prompt = f"""
Task Overview:
You are a SQL expert. Your task is to determine whether the SQL query
correctly answers the natural language question based on the database schema.

Input:
- Database Schema: {schema.to_prompt()}
- Natural Language Question: {question}
- SQL Query: {sql}
- Execution Result: {execution_result.data if execution_result else 'N/A'}
- Error Message (if any): {execution_result.error if execution_result and not execution_result.success else 'None'}

Output format:
<think>
Step-by-step reasoning about the correctness of the SQL
</think>
<answer>
CORRECT / SYNTAX_ERROR / EXECUTION_ERROR / SEMANTIC_ERROR
</answer>
<explanation>
Brief explanation of the error (if incorrect)
</explanation>
"""

        response = await self.llm_client.generate(prompt=prompt)

        # 解析响应
        answer = self._extract_tag(response, "answer")
        explanation = self._extract_tag(response, "explanation")

        if answer == "CORRECT":
            return CheckResult(is_correct=True)
        else:
            error_type = ErrorType.from_string(answer)
            return CheckResult(
                is_correct=False,
                error_type=error_type,
                explanation=explanation
            )


class SQLCorrector:
    """SQL 修正器"""

    async def correct(
        self,
        question: str,
        sql: str,
        check_result: CheckResult,
        schema: SchemaInfo,
        iteration: int,
        history: List[CorrectionHistory]
    ) -> str:
        """
        根据错误类型生成修正后的 SQL
        """
        # 构建修正 Prompt
        prompt = self._build_correction_prompt(
            question=question,
            sql=sql,
            check_result=check_result,
            schema=schema,
            iteration=iteration,
            history=history
        )

        response = await self.llm_client.generate(
            prompt=prompt,
            temperature=min(0.1 + iteration * 0.2, 0.8)  # 温度递增
        )

        return extract_sql(response)

    def _build_correction_prompt(
        self,
        question: str,
        sql: str,
        check_result: CheckResult,
        schema: SchemaInfo,
        iteration: int,
        history: List[CorrectionHistory]
    ) -> str:
        """根据错误类型构建修正 Prompt"""

        base_prompt = f"""
Database Schema:
{schema.to_prompt()}

Natural Language Question:
{question}

Original SQL:
```sql
{sql}
```
"""

        # 根据错误类型添加特定指导
        if check_result.error_type == ErrorType.SYNTAX_ERROR:
            specific_guide = f"""
Error Type: Syntax Error
Error Details: {check_result.explanation}

Please fix the SQL syntax errors. Common issues:
- Missing or mismatched parentheses
- Incorrect keyword spelling
- Missing commas between columns
- Incorrect string quoting

Provide the corrected SQL:
"""

        elif check_result.error_type == ErrorType.EXECUTION_ERROR:
            specific_guide = f"""
Error Type: Execution Error
Error Details: {check_result.explanation}

Please fix the execution errors. Common issues:
- Table or column names may not exist
- Data type mismatches
- Referenced tables may need JOINs
- Check schema for correct table/column names

Provide the corrected SQL:
"""

        elif check_result.error_type == ErrorType.SEMANTIC_ERROR:
            specific_guide = f"""
Error Type: Semantic Error
Error Details: {check_result.explanation}

The SQL executes but does not correctly answer the question. Please:
- Re-read the question carefully
- Check if all conditions are properly applied
- Verify aggregation functions (COUNT, SUM, AVG, etc.)
- Check ORDER BY and LIMIT clauses
- Ensure JOIN conditions are correct

Provide the corrected SQL:
"""

        else:
            specific_guide = f"""
Error Details: {check_result.explanation}

Please analyze the error and provide the corrected SQL:
"""

        # 添加历史记录
        history_prompt = ""
        if history:
            history_prompt = "\nPrevious attempts:\n"
            for h in history:
                history_prompt += f"\nIteration {h.iteration}:\n"
                history_prompt += f"SQL: {h.sql}\n"
                history_prompt += f"Error: {h.error_explanation}\n"

        return base_prompt + specific_guide + history_prompt


class CheckCorrectPipeline:
    """Check-Correct 迭代流程"""

    def __init__(
        self,
        checker: SQLChecker,
        corrector: SQLCorrector,
        max_iterations: int = 3,
        early_stop: bool = True,
        timeout: int = 30
    ):
        self.checker = checker
        self.corrector = corrector
        self.max_iterations = max_iterations
        self.early_stop = early_stop
        self.timeout = timeout
        self.history: List[CorrectionHistory] = []

    async def run(
        self,
        question: str,
        schema: SchemaInfo,
        initial_sql: Optional[str] = None
    ) -> CheckCorrectResult:
        """
        执行 Check-Correct 迭代流程
        """
        start_time = time.time()

        # 初始生成 (如果没有提供初始SQL)
        if initial_sql is None:
            current_sql = await self._generate_initial(question, schema)
        else:
            current_sql = initial_sql

        self.history = []

        for iteration in range(self.max_iterations):
            # 检查是否超时
            if time.time() - start_time > self.timeout:
                return CheckCorrectResult(
                    success=False,
                    final_sql=current_sql,
                    iterations=self.history,
                    error="Timeout"
                )

            # 执行 SQL
            execution_result = await self._execute_sql(current_sql, schema)

            # 检查正确性
            check_result = await self.checker.check(
                question=question,
                sql=current_sql,
                schema=schema,
                execution_result=execution_result
            )

            # 记录历史
            self.history.append(CorrectionHistory(
                iteration=iteration,
                sql=current_sql,
                execution_result=execution_result,
                check_result=check_result
            ))

            # 检查通过，返回结果
            if check_result.is_correct:
                return CheckCorrectResult(
                    success=True,
                    final_sql=current_sql,
                    iterations=self.history,
                    total_iterations=iteration + 1
                )

            # 检查是否提前停止
            if self.early_stop and self._should_stop_early():
                break

            # 生成修正 SQL
            current_sql = await self.corrector.correct(
                question=question,
                sql=current_sql,
                check_result=check_result,
                schema=schema,
                iteration=iteration,
                history=self.history
            )

        # 达到最大迭代次数仍未正确
        return CheckCorrectResult(
            success=False,
            final_sql=current_sql,
            iterations=self.history,
            total_iterations=len(self.history),
            error="Max iterations reached without correct result"
        )

    def _should_stop_early(self) -> bool:
        """判断是否提前停止"""
        if len(self.history) < 2:
            return False

        # 连续两轮无改进则停止
        last_two = self.history[-2:]
        # 检查是否连续两轮都是同样的错误
        if (last_two[0].check_result.error_type == last_two[1].check_result.error_type and
            not last_two[0].check_result.is_correct and
            not last_two[1].check_result.is_correct):
            return True

        return False
```

### 3.4 错误分类与处理策略

| 错误类型 | 检测方式 | 修正策略 |
|----------|----------|----------|
| **syntax_error** | SQL解析失败 | 语法修正Prompt，重点检查括号匹配、关键字拼写 |
| **execution_error** | 执行异常（表/字段不存在等） | 表/字段修正Prompt，结合Schema信息修正引用 |
| **semantic_error** | 结果不匹配（使用LLM判断） | 逻辑修正Prompt，重新理解问题意图 |
| **timeout_error** | 执行超时 | 优化建议Prompt，建议添加LIMIT或优化查询 |

**错误类型定义：**

```python
from enum import Enum, auto

class ErrorType(Enum):
    """错误类型枚举"""
    SYNTAX_ERROR = "syntax_error"
    EXECUTION_ERROR = "execution_error"
    SEMANTIC_ERROR = "semantic_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"

    @classmethod
    def from_string(cls, s: str) -> "ErrorType":
        mapping = {
            "SYNTAX_ERROR": cls.SYNTAX_ERROR,
            "EXECUTION_ERROR": cls.EXECUTION_ERROR,
            "SEMANTIC_ERROR": cls.SEMANTIC_ERROR,
            "TIMEOUT_ERROR": cls.TIMEOUT_ERROR,
        }
        return mapping.get(s.upper(), cls.UNKNOWN_ERROR)


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.handlers = {
            ErrorType.SYNTAX_ERROR: self._handle_syntax_error,
            ErrorType.EXECUTION_ERROR: self._handle_execution_error,
            ErrorType.SEMANTIC_ERROR: self._handle_semantic_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
        }

    def handle(self, error_type: ErrorType, context: ErrorContext) -> CorrectionStrategy:
        """根据错误类型返回处理策略"""
        handler = self.handlers.get(error_type, self._handle_unknown_error)
        return handler(context)

    def _handle_syntax_error(self, context: ErrorContext) -> CorrectionStrategy:
        return CorrectionStrategy(
            prompt_template="syntax_correction",
            focus_areas=["parentheses", "keywords", "quotes"],
            examples=get_syntax_examples()
        )

    def _handle_execution_error(self, context: ErrorContext) -> CorrectionStrategy:
        return CorrectionStrategy(
            prompt_template="execution_correction",
            focus_areas=["table_names", "column_names", "join_conditions"],
            schema_hints=context.schema.get_relevant_hints(context.error_message),
            examples=get_execution_examples()
        )

    def _handle_semantic_error(self, context: ErrorContext) -> CorrectionStrategy:
        return CorrectionStrategy(
            prompt_template="semantic_correction",
            focus_areas=["question_understanding", "conditions", "aggregations"],
            question_rephrase=context.question,
            examples=get_semantic_examples()
        )

    def _handle_timeout_error(self, context: ErrorContext) -> CorrectionStrategy:
        return CorrectionStrategy(
            prompt_template="optimization",
            focus_areas=["limit_clause", "index_usage", "query_structure"],
            suggestions=["Add LIMIT", "Optimize JOIN order", "Check for missing indexes"]
        )
```

---

## 4. 边界情况处理

### 4.1 全部采样失败场景

```
场景描述:
=========
Pass@K: 全部 K 次采样都执行失败
Voting: 全部候选执行失败

处理策略:
=========

策略1: 返回空结果 (strict模式)
┌─────────────────────────────────────────┐
│  当所有候选都失败时，返回空结果和错误信息  │
│  适用场景: 严格的数据分析场景             │
│  返回值: {success: false, error: "..."}  │
└─────────────────────────────────────────┘

策略2: 返回最后尝试 (lenient模式)
┌─────────────────────────────────────────┐
│  返回最后一个候选，即使它执行失败         │
│  适用场景: 探索性分析，需要看到尝试结果   │
│  返回值: {success: false, sql: "...",    │
│          error: "Execution failed"}      │
└─────────────────────────────────────────┘

策略3: 触发 Check-Correct (auto-fix模式)
┌─────────────────────────────────────────┐
│  自动进入 Check-Correct 流程进行修正      │
│  适用场景: 高精度要求的生产环境           │
│  返回值: 经过迭代修正后的结果             │
└─────────────────────────────────────────┘

策略4: 返回随机候选 (exploration模式)
┌─────────────────────────────────────────┐
│  随机返回一个候选供用户检查               │
│  适用场景: 调试和开发阶段                 │
│  返回值: {success: false, sql: "...",    │
│          strategy: "random_selection"}   │
└─────────────────────────────────────────┘
```

### 4.2 迭代不收敛场景

```
场景描述:
=========
达到最大迭代次数仍未获得正确结果

检测方式:
=========
1. 迭代次数达到 max_iterations
2. 连续多轮产生同样的错误
3. SQL 在相邻轮次间无变化

处理策略:
=========

┌─────────────────────────────────────────────────────────┐
│                    迭代不收敛处理                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  检测收敛性:                                             │
│  ┌─────────────┐                                        │
│  │ 迭代次数 >= │──是──▶ 标记为不收敛，执行处理策略      │
│  │ max_iter?   │                                        │
│  └──────┬──────┘                                        │
│         │否                                             │
│         ▼                                               │
│  ┌─────────────┐                                        │
│  │ 连续N轮同样 │──是──▶ 标记为不收敛，执行处理策略      │
│  │ 错误?       │                                        │
│  └──────┬──────┘                                        │
│         │否                                             │
│         ▼                                               │
│  ┌─────────────┐                                        │
│  │ SQL无变化?  │──是──▶ 标记为不收敛，执行处理策略      │
│  └─────────────┘                                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  处理策略:                                               │
│                                                         │
│  1. 返回最佳尝试                                         │
│     - 选择执行最成功的那一轮                             │
│     - 或选择错误最少的那一轮                             │
│                                                         │
│  2. 返回警告信息                                         │
│     - 包含不收敛原因                                     │
│     - 建议用户检查问题表述                               │
│                                                         │
│  3. 降级处理                                             │
│     - 切换到 Greedy Search 模式                          │
│     - 使用更低温度参数重试                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.3 执行超时处理

```
场景描述:
=========
单条 SQL 执行超时（默认30秒）
整体任务超时控制

超时层级:
=========

Level 1: 单条 SQL 执行超时
┌─────────────────────────────────────────┐
│  timeout_per_sql: 30s (可配置 5-60s)    │
│                                         │
│  处理流程:                               │
│  1. 设置 SQL 执行超时                    │
│  2. 超时后取消执行                       │
│  3. 标记该候选为 timeout_error           │
│  4. 继续处理其他候选                     │
│                                         │
│  优化建议:                               │
│  - 提示用户添加 LIMIT 子句               │
│  - 建议检查索引                          │
│  - 建议优化查询条件                      │
└─────────────────────────────────────────┘

Level 2: 单次迭代超时
┌─────────────────────────────────────────┐
│  timeout_per_iteration: 60s             │
│                                         │
│  包含: 生成 + 执行 + 检查                │
│                                         │
│  处理流程:                               │
│  1. 监控迭代总时间                       │
│  2. 超时后终止当前迭代                   │
│  3. 记录已完成的步骤                     │
│  4. 进入下一轮或结束                     │
└─────────────────────────────────────────┘

Level 3: 整体任务超时
┌─────────────────────────────────────────┐
│  Pass@K timeout: 120s                   │
│  Check-Correct timeout: 180s            │
│                                         │
│  处理流程:                               │
│  1. 监控任务总时间                       │
│  2. 超时后优雅终止                       │
│  3. 返回已完成的中间结果                 │
│  4. 标记任务状态为 TIMEOUT               │
└─────────────────────────────────────────┘

超时配置:
=========

| 层级 | 配置项 | 默认值 | 范围 | 说明 |
|------|--------|--------|------|------|
| SQL | timeout_per_sql | 30s | 5-60s | 单条SQL执行超时 |
| 迭代 | timeout_per_iteration | 60s | 30-120s | 单次迭代超时 |
| 任务 | timeout_per_task | 180s | 60-600s | 整体任务超时 |
```

---

## 5. 业务规则

### 5.1 参数约束

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| k_candidates | 1-16 | 8 | 采样数量，支持 1, 4, 8, 16 |
| max_iterations | 1-5 | 3 | 最大迭代次数 |
| temperature | 0.0-1.0 | 0.8 | 采样温度，0 时退化为 Greedy |
| timeout_per_sql | 5-60s | 30s | 单条SQL超时时间 |
| timeout_per_iteration | 10-120s | 60s | 单次迭代超时 |
| max_tokens | 512-4096 | 2048 | 最大生成长度 |
| top_p | 0.1-1.0 | 0.95 | 核采样参数 |

### 5.2 校验规则

```python
class ParameterValidator:
    """参数校验器"""

    VALID_K_VALUES = [1, 4, 8, 16]

    @staticmethod
    def validate_pass_at_k_config(config: PassAtKConfig) -> ValidationResult:
        """校验 Pass@K 配置"""
        errors = []

        # K 值校验
        if config.k not in ParameterValidator.VALID_K_VALUES:
            errors.append(
                f"k must be one of {ParameterValidator.VALID_K_VALUES}, "
                f"got {config.k}"
            )

        # Temperature 校验
        if not 0.0 <= config.temperature <= 1.0:
            errors.append(
                f"temperature must be in [0.0, 1.0], "
                f"got {config.temperature}"
            )

        # Timeout 校验
        if not 5 <= config.timeout_per_sql <= 60:
            errors.append(
                f"timeout_per_sql must be in [5, 60], "
                f"got {config.timeout_per_sql}"
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    @staticmethod
    def validate_check_correct_config(config: CheckCorrectConfig) -> ValidationResult:
        """校验 Check-Correct 配置"""
        errors = []

        # 迭代次数校验
        if not 1 <= config.max_iterations <= 5:
            errors.append(
                f"max_iterations must be in [1, 5], "
                f"got {config.max_iterations}"
            )

        # Temperature 校验 (迭代中温度会递增)
        if not 0.0 <= config.base_temperature <= 1.0:
            errors.append(
                f"base_temperature must be in [0.0, 1.0], "
                f"got {config.base_temperature}"
            )

        # 校验最终温度不超过 1.0
        final_temp = config.base_temperature + (config.max_iterations - 1) * 0.2
        if final_temp > 1.0:
            errors.append(
                f"Final temperature {final_temp:.2f} exceeds 1.0, "
                f"reduce base_temperature or max_iterations"
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### 5.3 性能规则

| 场景 | 规则 | 超限处理 |
|------|------|----------|
| 并发采样 | 最多 4 个并行 | 排队等待 |
| 并发执行 | 最多 4 个并行 | 排队等待 |
| 内存使用 | 单次任务 < 2GB | 流式处理 |
| 结果大小 | 单次结果 < 100MB | 截断 + 警告 |
| Token 消耗 | 记录并告警 | 成本估算 |

---

## 6. 数据流图

### 6.1 高级推理完整数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         高级推理完整数据流                                    │
└─────────────────────────────────────────────────────────────────────────────┘

用户请求
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway                                 │
│  - 请求认证  - 限流控制  - 参数校验  - 路由分发                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Inference Service                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Inference Mode Router                       │    │
│  │  (根据 inference_mode 分发到不同处理器)                   │    │
│  └──────┬────────────────────┬────────────────────┬─────────┘    │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │  Pass@K     │      │  Check-     │      │  Majority   │      │
│  │  Processor  │      │  Correct    │      │  Voting     │      │
│  │             │      │  Processor  │      │  Processor  │      │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘      │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    LLM Client                            │    │
│  │  - 并行生成  - 温度控制  - Token管理  - 重试机制           │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   SQL Executor                           │    │
│  │  - 并行执行  - 超时控制  - 结果缓存  - 错误隔离           │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Result Aggregator                           │    │
│  │  - 结果对比  - 投票统计  - 置信度计算  - 最佳结果选择      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Connection │  │   Schema    │  │   Query     │              │
│  │    Pool     │  │   Cache     │  │   Engine    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   History   │  │   Result    │  │   Metrics   │              │
│  │   Store     │  │   Cache     │  │   Store     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
响应返回

数据流详细说明:
==============

1. 用户请求阶段:
   - 用户提交自然语言问题
   - 选择推理模式 (pass_at_k / check_correct / majority_voting)
   - 配置相应参数

2. 路由分发阶段:
   - API Gateway 校验请求
   - 根据 inference_mode 路由到对应处理器

3. 处理阶段 (以 Pass@K 为例):
   ┌──────────────────────────────────────────────────────────┐
   │  Input: question, connection_id, k, temperature          │
   │                                                          │
   │  Step 1: LLM Client 并行生成 K 个候选 SQL                 │
   │     ├─ Call LLM API with temperature                     │
   │     ├─ Collect K responses                               │
   │     └─ Extract SQL from each response                    │
   │                                                          │
   │  Step 2: SQL Executor 并行执行 K 个 SQL                   │
   │     ├─ Create connection pool                            │
   │     ├─ Execute SQL with timeout                          │
   │     └─ Collect results/errors                            │
   │                                                          │
   │  Step 3: Result Aggregator 验证正确性                     │
   │     ├─ For each successful execution:                    │
   │     │   Compare with gold SQL using EXCEPT               │
   │     ├─ Find first correct candidate                      │
   │     └─ Calculate confidence                              │
   │                                                          │
   │  Output: best_sql, candidates_details, confidence        │
   └──────────────────────────────────────────────────────────┘

4. 存储阶段:
   - 存储推理历史
   - 缓存结果
   - 记录性能指标

5. 响应阶段:
   - 格式化结果
   - 返回给用户
```

---

## 7. 附录

### 7.1 术语表

| 术语 | 说明 |
|------|------|
| Pass@K | K次采样中至少一次正确的概率 |
| Check-Correct | 生成-检查-修正迭代流程 |
| Majority Voting | 基于执行结果的多数投票 |
| EX Accuracy | 基于执行结果的准确率 |
| Candidate | 候选SQL及其执行结果 |
| Iteration | Check-Correct中的迭代轮次 |
| Confidence | 结果置信度 |
| Temperature | 采样温度，控制输出随机性 |
| EXCEPT | SQL集合差运算符 |

### 7.2 配置示例

```yaml
# advanced_inference.yaml

pass_at_k:
  enabled: true
  default_k: 8
  supported_k_values: [1, 4, 8, 16]
  default_temperature: 0.8
  timeout_per_sql: 30
  max_concurrent_generation: 4
  max_concurrent_execution: 4

check_correct:
  enabled: true
  default_max_iterations: 3
  max_allowed_iterations: 5
  default_base_temperature: 0.1
  early_stop: true
  early_stop_patience: 1
  timeout_per_iteration: 60
  timeout_per_task: 180

majority_voting:
  enabled: true
  all_fail_strategy: "trigger_correction"  # return_empty / return_random / return_last / trigger_correction
  confidence_calculation:
    include_success_ratio: true
    tie_penalty: 0.8

error_handling:
  retry_attempts: 2
  retry_delay: 1.0
  timeout_errors:
    suggest_limit: true
    suggest_index: true
```

---

*文档结束*
