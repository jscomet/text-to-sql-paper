# 高级推理功能 - 产品需求文档 (PRD)

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| **功能名称** | 高级推理功能 (Advanced Inference) |
| **版本** | v0.1.0 |
| **日期** | 2026-03-13 |
| **编写人** | doc-lead |
| **文档状态** | 草稿 |
| **目标阶段** | v1.1.0 增强功能 |

---

## 2. 功能概述

### 2.1 功能背景

当前 Text-to-SQL 系统采用 **Greedy Search**（贪婪搜索）模式进行 SQL 生成，该模式虽然响应快速，但存在以下局限：

1. **准确率受限**：单次采样容易受模型随机性影响，无法充分发挥模型的最佳潜力
2. **缺乏自我修正能力**：生成错误 SQL 后无法自动识别和修复，需要人工介入
3. **评估维度单一**：仅用 Greedy Search 评估会低估模型真实能力，无法全面反映模型潜力

**重要概念区分**：

| 概念层级 | 说明 | 具体手段/策略 |
|----------|------|---------------|
| **推理手段** | 如何生成 SQL | Single/Greedy、Sampling、Check-Correct |
| **评测手段** | 如何评估结果 | Greedy Search、Pass@K、Majority Voting |
| **组合策略** | 推理+评测的完整方案 | vote@k、pass@k |

**组合策略说明**：
- `vote@k` = Sampling (推理，n=K) + Majority Voting (评测)
- `pass@k` = Sampling (推理，n=K) + Pass@K (评测)

参考 ICED-2026 论文代码中的实现：
- `infer.py` - 推理控制：`--n` 参数设置采样次数，`--temperature` 控制随机性
- `evaluate_bird.py` - 评测控制：`--mode` 参数设置评测模式（greedy_search/major_voting/pass_at_k）
- `pipeline.py` - Generator + Corrector 双阶段架构
- `lc_text_to_sql_pipeline.py` - Generate-Check-Correct 迭代修正流程

**示例**：
```bash
# vote@8 组合策略：8次采样 + 多数投票
python infer.py --n 8 --temperature 0.8 ...
python evaluate_bird.py --mode major_voting ...

# pass@8 组合策略：8次采样 + 任一通过即成功
python infer.py --n 8 --temperature 0.8 ...
python evaluate_bird.py --mode pass_at_k ...
```

本功能将上述先进组合策略产品化，为用户提供 vote@k、pass@k 和 Check-Correct 等高级推理能力。

### 2.2 目标用户

| 用户角色 | 核心需求 | 使用场景 |
|----------|----------|----------|
| **评测人员** | 全面评估模型性能 | 使用 Pass@K 模式评估模型潜力上限 |
| **开发者** | 提高 SQL 生成准确率 | 使用 Check-Correct 模式获得更可靠的 SQL |
| **研究人员** | 对比不同推理策略效果 | 对比 Greedy/Pass@K/Check-Correct 的效果差异 |
| **业务用户** | 获取准确的查询结果 | 在重要场景下使用高级推理模式 |

### 2.3 解决的问题

| 问题 | 解决方案 |
|------|----------|
| 单次采样准确率不稳定 | Pass@K 多采样策略，任一通过即算成功 |
| 生成错误无法自动修复 | Check-Correct 迭代修正，自动识别和修复错误 |
| 模型能力评估不全面 | 支持多种推理模式对比，全面评估模型潜力 |
| 生产环境可靠性不足 | Check-Correct 提供自我纠错能力，提高可靠性 |

---

## 3. 用户故事

### 3.1 作为评测人员

> **故事 1**: 作为评测人员，我希望使用 Pass@K 模式评估模型潜力，以便更准确地了解模型在多次尝试中的最佳表现。

**验收标准**：
- 可以配置 K 值（1, 4, 8, 16）
- 系统执行 K 次独立采样
- 任一采样通过即算该问题成功
- 输出 Pass@K 准确率报告

**优先级**: P0

---

> **故事 2**: 作为评测人员，我希望查看每个问题的采样详情，以便分析模型在不同采样中的表现差异。

**验收标准**：
- 可以查看每个问题的 K 个候选 SQL
- 显示每个候选的执行结果（正确/错误）
- 支持对比候选 SQL 的差异

**优先级**: P1

---

### 3.2 作为开发者

> **故事 3**: 作为开发者，我希望使用 Check-Correct 模式提高 SQL 准确率，以便在生产环境获得更可靠的查询结果。

**验收标准**：
- 可以启用 Check-Correct 模式
- 系统执行生成-检查-修正循环
- 最多支持 3-5 轮迭代
- 返回最终修正后的 SQL

**优先级**: P0

---

> **故事 4**: 作为开发者，我希望查看 Check-Correct 的迭代历史，以便理解模型的修正过程。

**验收标准**：
- 显示每轮生成的 SQL
- 显示检查器的判断结果
- 显示错误类型分类（syntax/execution/semantic）
- 显示修正原因说明

**优先级**: P1

---

> **故事 5**: 作为开发者，我希望配置最大迭代次数和停止条件，以便在准确率和性能之间取得平衡。

**验收标准**：
- 可配置最大迭代次数（1-5）
- 可配置提前停止条件（如连续两轮无改进）
- 可配置超时时间

**优先级**: P1

---

### 3.3 作为研究人员

> **故事 6**: 作为研究人员，我希望对比不同推理模式的效果，以便选择最适合特定场景的策略。

**验收标准**：
- 支持 Greedy Search、Pass@K、Check-Correct 三种模式
- 提供对比报告，包含准确率、耗时、资源消耗
- 支持批量评测对比

**优先级**: P1

---

> **故事 7**: 作为研究人员，我希望使用增强的 Majority Voting 功能，以便评估基于执行结果的投票策略效果。

**验收标准**：
- 支持基于执行结果的投票
- 支持置信度评分
- 支持全失败处理策略配置

**优先级**: P2

---

## 4. 功能清单

### 4.1 Pass@K 推理

#### 4.1.1 K 次独立采样

| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 配置采样次数 | 支持 K=1, 4, 8, 16 配置 | P0 |
| 并行采样 | K 次采样并行执行，提高效率 | P0 |
| 温度参数控制 | 支持配置采样温度（0.1-1.0） | P0 |
| 结果去重 | 对语义相同的 SQL 进行去重 | P2 |

**配置示例**：

```json
{
  "inference_mode": "pass_at_k",
  "pass_at_k_config": {
    "k": 8,
    "temperature": 0.8,
    "max_tokens": 2048,
    "top_p": 0.95
  }
}
```

#### 4.1.2 并行执行候选 SQL

| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 并发执行 | 同时执行 K 个候选 SQL | P0 |
| 超时控制 | 单个 SQL 执行超时 30 秒 | P0 |
| 错误隔离 | 单个 SQL 失败不影响其他候选 | P0 |
| 资源限制 | 限制并发数防止资源耗尽 | P1 |

#### 4.1.3 任一通过即算成功

| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 正确性验证 | 使用 EX 指标验证每个候选 | P0 |
| 成功判定 | K 个候选中任一正确即算通过 | P0 |
| 最佳结果选择 | 选择第一个正确的候选作为结果 | P1 |
| 置信度计算 | 基于正确候选比例计算置信度 | P2 |

#### 4.1.4 支持 K=1,4,8,16 等配置

| K 值 | 适用场景 | 预期耗时 |
|------|----------|----------|
| 1 | 与 Greedy 等效，用于对比 | ~3s |
| 4 | 快速评估，资源消耗适中 | ~6s |
| 8 | 标准 Pass@K 评估 | ~10s |
| 16 | 深度评估，资源消耗较高 | ~18s |

### 4.2 Check-Correct 迭代修正

#### 4.2.1 生成-检查-修正循环

```
┌─────────────────────────────────────────────────────────────┐
│                    Check-Correct 流程                        │
└─────────────────────────────────────────────────────────────┘

初始化: 用户问题 + Schema 信息
    │
    ▼
┌──────────┐
│ Generator│ 生成初始 SQL (SQL_0)
└────┬─────┘
     │
     ▼
┌──────────┐
│ Executor │ 执行 SQL_0
└────┬─────┘
     │
     ▼
┌──────────┐      通过      ┌──────────┐
│ Checker  │ ─────────────▶ │ 返回结果 │
│ 检查正确性│                └──────────┘
└────┬─────┘
     │ 未通过
     ▼
┌──────────┐
│Corrector │ 生成修正 SQL (SQL_1)
└────┬─────┘
     │
     └──────────────▶ (进入下一轮循环)

终止条件:
- Checker 返回通过
- 达到最大迭代次数
- 超时
```

| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 初始生成 | Generator 生成初始 SQL | P0 |
| 执行验证 | 执行 SQL 获取结果或错误 | P0 |
| 正确性检查 | Checker 判断 SQL 是否正确 | P0 |
| 错误修正 | Corrector 根据错误生成修正 SQL | P0 |
| 迭代控制 | 管理迭代流程和状态 | P0 |

#### 4.2.2 最多 3-5 轮迭代

| 配置项 | 说明 | 默认值 | 范围 |
|--------|------|--------|------|
| max_iterations | 最大迭代次数 | 3 | 1-5 |
| timeout | 单次迭代超时 | 30s | 10-60s |
| early_stop | 无改进时提前停止 | true | true/false |

**迭代策略**：

```python
iteration_config = {
    "max_iterations": 3,
    "early_stop": True,
    "early_stop_patience": 1,  # 连续 N 轮无改进则停止
    "temperature_schedule": [0.1, 0.3, 0.5]  # 每轮温度递增
}
```

#### 4.2.3 错误分类：syntax, execution, semantic

| 错误类型 | 说明 | 示例 | 修正策略 |
|----------|------|------|----------|
| **Syntax** | SQL 语法错误 | 缺少括号、关键字拼写错误 | 语法修正 Prompt |
| **Execution** | 执行时错误 | 表不存在、字段不存在 | 结合错误信息修正 |
| **Semantic** | 语义错误 | 逻辑错误、条件错误 | 意图理解修正 |

**Checker Prompt 设计**：

```
Task Overview:
You are a SQL expert. Your task is to determine whether the SQL query
 correctly answers the natural language question based on the database schema.

Input:
- Database Schema: {schema}
- Natural Language Question: {question}
- SQL Query: {sql}
- Execution Result: {result}
- Error Message (if any): {error}

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
```

#### 4.2.4 存储修正历史

| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 迭代记录 | 存储每轮生成的 SQL | P0 |
| 检查结果 | 存储每轮检查器的判断 | P0 |
| 错误信息 | 存储错误类型和说明 | P0 |
| 修正原因 | 存储修正的依据和思路 | P1 |
| 可视化展示 | 前端展示修正时间线 | P1 |

**历史记录结构**：

```json
{
  "check_correct_history": [
    {
      "iteration": 0,
      "sql": "SELECT * FROM users",
      "checker_result": "SEMANTIC_ERROR",
      "error_explanation": "Missing WHERE clause for filtering",
      "correction_prompt": "Add WHERE clause to filter active users"
    },
    {
      "iteration": 1,
      "sql": "SELECT * FROM users WHERE status = 'active'",
      "checker_result": "CORRECT",
      "error_explanation": null,
      "correction_prompt": null
    }
  ],
  "total_iterations": 2,
  "final_sql": "SELECT * FROM users WHERE status = 'active'",
  "success": true
}
```

### 4.3 增强的 Majority Voting

#### 4.3.1 基于执行结果的投票

| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 结果哈希 | 对执行结果进行哈希用于比较 | P0 |
| 票数统计 | 统计相同结果的票数 | P0 |
| 胜者选择 | 选择票数最多的结果 | P0 |
| 平票处理 | 平票时选择第一个或随机选择 | P1 |

**投票算法**：

```python
def majority_voting(candidates):
    """
    candidates: List of {sql, result, success}
    """
    # 1. 过滤执行成功的候选
    valid_candidates = [c for c in candidates if c.success]

    # 2. 按执行结果分组
    result_groups = group_by_result(valid_candidates)

    # 3. 选择票数最多的组
    winner_group = max(result_groups, key=lambda g: g.votes)

    # 4. 返回该组中第一个 SQL
    return winner_group.sqls[0]
```

#### 4.3.2 支持置信度评分

| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 投票比例 | 最高票数 / 总有效票数 | P1 |
| 执行成功率 | 成功执行数 / 总采样数 | P1 |
| 综合置信度 | 结合投票比例和执行成功率 | P2 |

**置信度计算**：

```
confidence = (max_votes / total_valid) * (success_count / total_samples)

# 示例:
# - 8 个采样，6 个执行成功
# - 结果 A: 4 票，结果 B: 2 票
# confidence = (4/6) * (6/8) = 0.67 * 0.75 = 0.50
```

#### 4.3.3 全失败处理策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| **返回空** | 返回空结果或错误提示 | 严格场景 |
| **返回随机** | 随机返回一个候选 | 探索性场景 |
| **返回最后** | 返回最后一个候选（可能有部分结果） | 容错场景 |
| **触发修正** | 自动进入 Check-Correct 流程 | 高精度场景 |

---

## 5. 非功能需求

### 5.1 性能需求

| 指标 | 要求 | 说明 |
|------|------|------|
| Pass@K (K=8) | < 15s | 8 次采样并行执行总时间 |
| Check-Correct | < 30s | 最多 3 轮迭代总时间 |
| 单次迭代 | < 10s | 生成+检查+修正一轮时间 |
| 并发任务 | >= 4 | 支持并行的推理任务数 |
| 内存占用 | < 2GB | 单次推理任务内存上限 |

### 5.2 可用性需求

| 需求 | 说明 |
|------|------|
| 进度显示 | 显示 Pass@K 采样进度或 Check-Correct 迭代进度 |
| 取消操作 | 支持用户取消正在进行的推理任务 |
| 超时提示 | 超时后给出友好提示和建议 |
| 结果缓存 | 缓存推理结果，避免重复计算 |

### 5.3 可观测性需求

| 需求 | 说明 |
|------|------|
| 完整日志 | 记录推理过程的详细日志 |
| 性能指标 | 记录耗时、Token 消耗等指标 |
| 错误追踪 | 记录每轮迭代的错误信息 |
| 可视化 | 前端展示推理过程和中间结果 |

### 5.4 兼容性需求

| 需求 | 说明 |
|------|------|
| 向后兼容 | 默认保持 Greedy Search 行为 |
| 配置迁移 | 现有配置无需修改即可使用 |
| API 兼容 | 扩展现有 API，不破坏已有接口 |

---

## 6. 验收标准

### 6.1 Pass@K 功能验收

| 检查项 | 验收标准 | 优先级 |
|--------|----------|--------|
| 基础功能 | Pass@K 推理模式可用，支持配置 K 值 | P0 |
| K 值配置 | 支持 K=1, 4, 8, 16 配置 | P0 |
| 并行执行 | K 次采样并行执行，非串行 | P0 |
| 正确性验证 | 正确实现 Pass@K 指标计算 | P0 |
| 结果展示 | 展示每个候选 SQL 及其执行结果 | P1 |
| 性能达标 | K=8 时总耗时 < 15s | P1 |

### 6.2 Check-Correct 功能验收

| 检查项 | 验收标准 | 优先级 |
|--------|----------|--------|
| 基础功能 | Check-Correct 模式可用 | P0 |
| 迭代控制 | 支持配置最大迭代次数（1-5） | P0 |
| 错误分类 | 正确识别 syntax/execution/semantic 错误 | P0 |
| 修正能力 | 能够修正常见错误类型 | P0 |
| 历史记录 | 存储并展示修正历史 | P1 |
| 性能达标 | 3 轮迭代总耗时 < 30s | P1 |

### 6.3 API 接口验收

| 检查项 | 验收标准 | 优先级 |
|--------|----------|--------|
| 接口文档 | API 接口文档完整，包含参数说明 | P0 |
| 接口测试 | 所有 API 接口通过单元测试 | P0 |
| 错误处理 | 接口返回清晰的错误信息 | P0 |
| 向后兼容 | 现有 API 不受影响 | P0 |

### 6.4 E2E 测试验收

| 检查项 | 验收标准 | 优先级 |
|--------|----------|--------|
| 测试覆盖 | Pass@K 和 Check-Correct 核心流程覆盖 | P0 |
| 测试通过 | 所有 E2E 测试用例通过 | P0 |
| 性能测试 | 性能指标满足非功能需求 | P1 |
| 回归测试 | 现有功能不受影响 | P0 |

---

## 7. 附录

### 7.1 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| **组合策略** | **Composite Strategy** | **推理手段 + 评测手段的完整方案** |
| vote@k | Vote at K | K次采样 + 多数投票的组合策略 |
| pass@k | Pass at K | K次采样 + 任一通过的组合策略 |
| **推理手段** | **Inference Method** | **如何生成 SQL 的方式** |
| Single/Greedy | Single/Greedy | temperature=0，单次确定性生成 |
| Sampling | Sampling | temperature>0，并行生成 K 个候选 |
| Check-Correct | Check and Correct | 生成-检查-修正迭代流程 |
| **评测手段** | **Evaluation Method** | **如何评估结果的方式** |
| Pass@K | Pass at K (Metric) | K 次采样中至少有一次正确的概率 |
| Majority Voting | Majority Voting | 多数投票，选择出现最多的结果 |
| Greedy Search | Greedy Search | 贪婪搜索，单次结果评测 |
| **其他术语** | | |
| Generator | Generator | 生成 SQL 的模型/模块 |
| Checker | Checker | 检查 SQL 正确性的模型/模块 |
| Corrector | Corrector | 根据错误修正 SQL 的模型/模块 |
| EX Accuracy | Execution Accuracy | 基于执行结果的准确率 |
| Temperature | Temperature | 采样温度，控制输出的随机性 |

### 7.2 参考实现

本功能参考以下 ICED-2026-paper-code 实现：

| 文件 | 功能 | 参考内容 |
|------|------|----------|
| `infer.py` | vLLM 推理 | `--n` 参数支持多次采样（推理控制） |
| `pipeline.py` | 主流程 | Generator + Corrector 双阶段架构 |
| `lc_text_to_sql_pipeline.py` | LangChain 流程 | Generate-Check-Correct 迭代实现 |
| `evaluate_bird.py` | 评估 | `--mode` 参数控制评测模式（greedy_search/major_voting/pass_at_k） |

**组合策略在 ICED-2026 中的实现**：

```bash
# 1. vote@k 组合策略
# 推理阶段：生成 K 个候选
python infer.py --n 8 --temperature 0.8 --input_file ... --output_file ...
# 评测阶段：多数投票选择最佳
python evaluate_bird.py --mode major_voting --pred ... --gold ... --db_path ...

# 2. pass@k 组合策略
# 推理阶段：生成 K 个候选（与 vote@k 相同）
python infer.py --n 8 --temperature 0.8 --input_file ... --output_file ...
# 评测阶段：任一通过即算成功
python evaluate_bird.py --mode pass_at_k --pred ... --gold ... --db_path ...
```

**关键理解**：
- `infer.py --n 8` 只控制生成 8 个候选（Sampling 推理）
- `evaluate_bird.py --mode` 控制如何评估这 8 个候选
- `vote@k` 和 `pass@k` 的推理阶段完全相同，区别仅在评测阶段 |

### 7.3 接口预览

**Pass@K 推理接口**：

```http
POST /api/v1/query/advanced
Content-Type: application/json

{
  "connection_id": 1,
  "question": "查询销售额最高的前10个客户",
  "inference_mode": "pass_at_k",
  "pass_at_k_config": {
    "k": 8,
    "temperature": 0.8
  }
}
```

**Check-Correct 推理接口**：

```http
POST /api/v1/query/advanced
Content-Type: application/json

{
  "connection_id": 1,
  "question": "计算每个部门的平均工资",
  "inference_mode": "check_correct",
  "check_correct_config": {
    "max_iterations": 3,
    "early_stop": true
  }
}
```

### 7.4 错误码定义

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 4001 | 不支持的推理模式 | 检查 inference_mode 参数 |
| 4002 | K 值超出范围 | K 应在 [1, 4, 8, 16] 中 |
| 4003 | 迭代次数超出范围 | max_iterations 应在 1-5 之间 |
| 5001 | 推理超时 | 增加超时时间或简化问题 |
| 5002 | 所有采样失败 | 检查模型配置或问题表述 |
| 5003 | 迭代未收敛 | 增加 max_iterations 或调整 temperature |

---

## 8. 版本历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v0.1.0 | 2026-03-13 | 初始版本，定义 Pass@K 和 Check-Correct 功能需求 | doc-lead |
| v0.1.1 | 2026-03-13 | 修正概念定义：明确 vote@k、pass@k 是组合策略（推理+评测） | doc-lead |

---

*文档结束*
