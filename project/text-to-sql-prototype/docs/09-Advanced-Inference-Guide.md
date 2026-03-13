# 高级推理功能用户指南

> **文档信息**
> - 版本: v1.0.0
> - 更新日期: 2026-03-13
> - 文档路径: `docs/09-Advanced-Inference-Guide.md`
> - 关联功能: feat/advanced-inference

## 目录

1. [功能介绍](#1-功能介绍)
2. [快速开始](#2-快速开始)
3. [推理模式详解](#3-推理模式详解)
4. [配置参数说明](#4-配置参数说明)
5. [最佳实践](#5-最佳实践)
6. [常见问题](#6-常见问题)

---

## 1. 功能介绍

### 1.1 什么是高级推理功能

高级推理功能是 Text-to-SQL 系统的增强特性，通过引入多种推理策略，显著提高 SQL 生成的准确率和可靠性。

### 1.2 核心概念

在使用高级推理功能前，需要理解以下核心概念：

#### 推理手段 vs 评测手段

| 层次 | 说明 | 具体选项 |
|------|------|----------|
| **推理手段** | 如何生成 SQL | Single/Greedy、Sampling、Check-Correct |
| **评测手段** | 如何评估结果 | Greedy Search、Pass@K、Majority Voting |

#### 四种推理模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `single` | 单次生成（默认行为） | 快速查询，对响应时间敏感 |
| `pass_at_k` | K次采样，任一通过即成功 | 提高成功率，评估模型潜力 |
| `majority_vote` | K次采样，多数投票选择 | 稳定输出，减少随机性 |
| `check_correct` | 生成-检查-修正迭代 | 复杂查询，需要高可靠性 |

### 1.3 功能优势

- **提高准确率**：Pass@K 模式通过多次采样显著提高成功率
- **自我修正**：Check-Correct 模式自动识别和修复错误
- **灵活配置**：根据场景选择最适合的推理策略
- **完全兼容**：与现有 API 向后兼容，无需修改现有代码

---

## 2. 快速开始

### 2.1 基本使用

#### Single 模式（默认）

与现有 API 行为一致，单次生成 SQL：

```json
{
  "question": "查询销售额最高的5个产品",
  "connection_id": 1,
  "reasoning_mode": "single"
}
```

#### Pass@K 模式

生成 K 个候选 SQL，返回第一个执行成功的：

```json
{
  "question": "查询销售额最高的5个产品",
  "connection_id": 1,
  "reasoning_mode": "pass_at_k",
  "k_candidates": 8,
  "temperature": 0.8
}
```

#### Majority Vote 模式

生成 K 个候选 SQL，按执行结果投票选择：

```json
{
  "question": "统计2024年每个季度的订单数量",
  "connection_id": 1,
  "reasoning_mode": "majority_vote",
  "k_candidates": 5,
  "temperature": 0.8
}
```

#### Check-Correct 模式

迭代生成-检查-修正，直到获得正确 SQL：

```json
{
  "question": "查询每个部门的平均工资",
  "connection_id": 1,
  "reasoning_mode": "check_correct",
  "max_iterations": 3,
  "temperature": 0.7,
  "enable_self_correction": true
}
```

### 2.2 API 调用示例

**Python 示例：**

```python
import requests

# Pass@K 模式
response = requests.post(
    "http://localhost:8000/api/v1/queries/generate-advanced",
    headers={
        "Authorization": "Bearer <your_token>",
        "Content-Type": "application/json"
    },
    json={
        "question": "查询销售额最高的5个产品",
        "connection_id": 1,
        "reasoning_mode": "pass_at_k",
        "k_candidates": 8,
        "temperature": 0.8
    }
)

data = response.json()
print(f"Generated SQL: {data['data']['sql']}")
print(f"Pass@K Score: {data['data']['pass_at_k_score']}")
```

**cURL 示例：**

```bash
curl -X POST http://localhost:8000/api/v1/queries/generate-advanced \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "查询销售额最高的5个产品",
    "connection_id": 1,
    "reasoning_mode": "pass_at_k",
    "k_candidates": 8,
    "temperature": 0.8
  }'
```

---

## 3. 推理模式详解

### 3.1 Single 模式

**说明**：单次生成 SQL，与现有 API 行为完全一致。

**工作流程**：

```
用户问题 → 生成 SQL → 返回结果
```

**适用场景**：
- 对响应时间敏感的场景
- 简单查询，单次生成成功率已足够高
- 需要与现有系统保持完全一致的行为

**配置参数**：

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `question` | 是 | - | 自然语言问题 |
| `connection_id` | 是 | - | 数据库连接ID |
| `provider` | 否 | null | LLM提供商 |
| `temperature` | 否 | 0.8 | 采样温度 |

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sql": "SELECT product_name, SUM(sales) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 5",
    "reasoning_mode": "single",
    "execution_time_ms": 2500,
    "confidence_score": 0.85
  }
}
```

---

### 3.2 Pass@K 模式

**说明**：并行生成 K 个候选 SQL，执行后返回第一个成功的结果。

**工作流程**：

```
用户问题 → 并行生成 K 个 SQL → 并行执行 → 返回第一个成功的
```

**适用场景**：
- 需要提高 SQL 生成成功率
- 评估模型在多次尝试中的最佳表现
- 对响应时间有一定容忍度（约 5-15 秒）

**配置参数**：

| 参数 | 必填 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `question` | 是 | - | - | 自然语言问题 |
| `connection_id` | 是 | - | - | 数据库连接ID |
| `k_candidates` | 否 | 5 | 1-16 | 候选数量 |
| `temperature` | 否 | 0.8 | 0.0-2.0 | 采样温度，建议 >0.5 |
| `return_all_candidates` | 否 | false | - | 是否返回所有候选详情 |

**K 值选择建议**：

| K 值 | 适用场景 | 预期耗时 |
|------|----------|----------|
| 1 | 与 Single 等效，用于对比 | ~3s |
| 4 | 快速评估，资源消耗适中 | ~6s |
| 8 | 标准 Pass@K 评估 | ~10s |
| 16 | 深度评估，资源消耗较高 | ~18s |

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sql": "SELECT product_name, SUM(sales) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 5",
    "reasoning_mode": "pass_at_k",
    "candidates": [
      {
        "sql": "SELECT product_name, SUM(sales) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 5",
        "is_valid": true,
        "execution_result": [["Product A", 150000], ["Product B", 120000]],
        "vote_count": null
      },
      {
        "sql": "SELECT * FROM sales ORDER BY sales DESC LIMIT 5",
        "is_valid": false,
        "execution_result": null,
        "vote_count": null
      }
    ],
    "pass_at_k_score": 0.625,
    "execution_time_ms": 8500,
    "confidence_score": 0.75
  }
}
```

**Pass@K 得分计算**：

```
Pass@K = 成功候选数 / K

例如：K=8，5个候选执行成功
Pass@K = 5/8 = 0.625
```

---

### 3.3 Majority Vote 模式

**说明**：并行生成 K 个候选 SQL，按执行结果进行多数投票，选择得票最多的结果。

**工作流程**：

```
用户问题 → 并行生成 K 个 SQL → 并行执行 → 按结果分组 → 选择票数最多的
```

**适用场景**：
- 需要稳定的输出结果
- 减少模型随机性带来的影响
- 对准确率要求较高的生产环境

**配置参数**：

| 参数 | 必填 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `question` | 是 | - | - | 自然语言问题 |
| `connection_id` | 是 | - | - | 数据库连接ID |
| `k_candidates` | 否 | 5 | 1-16 | 候选数量，建议 >=5 |
| `temperature` | 否 | 0.8 | 0.0-2.0 | 采样温度 |

**投票算法**：

1. 过滤执行成功的候选
2. 按执行结果分组（相同结果为一组）
3. 选择票数最多的组
4. 返回该组中第一个 SQL

**置信度计算**：

```
confidence = (最高票数 / 有效候选数) * (成功数 / 总采样数)

例如：
- 8 个采样，6 个执行成功
- 结果 A: 4 票，结果 B: 2 票
- confidence = (4/6) * (6/8) = 0.50
```

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sql": "SELECT quarter, COUNT(*) as order_count FROM orders WHERE year = 2024 GROUP BY quarter",
    "reasoning_mode": "majority_vote",
    "candidates": [
      {
        "sql": "SELECT quarter, COUNT(*) as order_count FROM orders WHERE year = 2024 GROUP BY quarter",
        "is_valid": true,
        "execution_result": [["Q1", 150], ["Q2", 200]],
        "vote_count": 3
      },
      {
        "sql": "SELECT quarter, COUNT(*) FROM orders WHERE year = 2024 GROUP BY quarter",
        "is_valid": true,
        "execution_result": [["Q1", 150], ["Q2", 200]],
        "vote_count": 3
      }
    ],
    "execution_time_ms": 6800,
    "confidence_score": 0.9
  }
}
```

---

### 3.4 Check-Correct 模式

**说明**：迭代执行生成-检查-修正循环，直到获得正确的 SQL 或达到最大迭代次数。

**工作流程**：

```
用户问题 → 生成 SQL → 执行 → 检查正确性 → 如不正确则修正 → 循环
```

**适用场景**：
- 复杂查询，需要高可靠性
- 生产环境关键业务场景
- 需要理解模型修正过程

**配置参数**：

| 参数 | 必填 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `question` | 是 | - | - | 自然语言问题 |
| `connection_id` | 是 | - | - | 数据库连接ID |
| `max_iterations` | 否 | 3 | 1-5 | 最大迭代次数 |
| `temperature` | 否 | 0.7 | 0.0-2.0 | 采样温度，建议 0.5-0.8 |
| `enable_self_correction` | 否 | false | - | 是否启用自我修正 |

**错误分类**：

| 错误类型 | 说明 | 示例 |
|----------|------|------|
| `syntax_error` | SQL 语法错误 | 缺少括号、关键字拼写错误 |
| `execution_error` | 执行时错误 | 表不存在、字段不存在 |
| `semantic_error` | 语义错误 | 逻辑错误、条件错误、使用了错误的函数 |

**终止条件**：

1. Checker 返回通过（SQL 正确）
2. 达到最大迭代次数
3. 超时（单次迭代 30 秒）

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sql": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
    "reasoning_mode": "check_correct",
    "iteration_count": 2,
    "correction_history": [
      {
        "iteration": 1,
        "sql": "SELECT department, COUNT(salary) as avg_salary FROM employees GROUP BY department",
        "error_type": "semantic_error",
        "error_message": "使用了 COUNT 而不是 AVG",
        "correction_prompt": "请修正：应该使用 AVG 函数计算平均工资，而不是 COUNT 函数"
      },
      {
        "iteration": 2,
        "sql": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
        "error_type": null,
        "error_message": null,
        "correction_prompt": null
      }
    ],
    "execution_time_ms": 8500,
    "confidence_score": 0.95
  }
}
```

---

## 4. 配置参数说明

### 4.1 通用参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `question` | string | 是 | - | 自然语言问题，1-2000字符 |
| `connection_id` | integer | 是 | - | 数据库连接ID |
| `provider` | string | 否 | null | LLM提供商（openai/dashscope等） |
| `reasoning_mode` | string | 否 | "single" | 推理模式 |
| `temperature` | float | 否 | 0.8 | 采样温度，0.0-2.0 |

### 4.2 Pass@K/Majority Vote 专用参数

| 参数 | 类型 | 必填 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| `k_candidates` | integer | 否 | 5 | 1-16 | 候选数量 |
| `return_all_candidates` | boolean | 否 | false | - | 是否返回所有候选详情 |

### 4.3 Check-Correct 专用参数

| 参数 | 类型 | 必填 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| `max_iterations` | integer | 否 | 3 | 1-5 | 最大迭代次数 |
| `enable_self_correction` | boolean | 否 | false | - | 是否启用自我修正 |

### 4.4 参数调优建议

#### Temperature 设置

| 场景 | 建议值 | 说明 |
|------|--------|------|
| Pass@K | 0.7-0.9 | 需要一定随机性产生多样候选 |
| Majority Vote | 0.7-0.9 | 同上 |
| Check-Correct | 0.5-0.8 | 平衡探索与稳定 |
| 确定性场景 | 0.0-0.3 | 减少随机性 |

#### K 值选择

| 场景 | 建议 K 值 | 说明 |
|------|-----------|------|
| 快速评估 | 4 | 平衡速度与准确率 |
| 标准评估 | 8 | 行业通行标准 |
| 深度评估 | 16 | 追求最高准确率 |
| 生产环境 | 5-8 | 平衡性能与效果 |

#### Max Iterations 选择

| 场景 | 建议值 | 说明 |
|------|--------|------|
| 简单查询 | 2 | 通常一次修正即可 |
| 复杂查询 | 3-4 | 标准配置 |
| 极复杂查询 | 5 | 最大迭代次数 |

---

## 5. 最佳实践

### 5.1 模式选择指南

根据使用场景选择合适的推理模式：

```
是否需要高可靠性？
├── 是 → 使用 Check-Correct 模式
│        └── 配置：max_iterations=3, enable_self_correction=true
│
└── 否 → 是否需要最高成功率？
         ├── 是 → 使用 Pass@K 模式
         │        └── 配置：k_candidates=8, temperature=0.8
         │
         └── 否 → 是否需要稳定输出？
                  ├── 是 → 使用 Majority Vote 模式
                  │        └── 配置：k_candidates=5, temperature=0.8
                  │
                  └── 否 → 使用 Single 模式（默认）
                           └── 配置：temperature=0.8
```

### 5.2 场景推荐

| 场景 | 推荐模式 | 配置建议 |
|------|----------|----------|
| **日常查询** | Single | temperature=0.8 |
| **数据分析** | Pass@K | k=8, temperature=0.8 |
| **报表生成** | Majority Vote | k=5, temperature=0.8 |
| **生产系统** | Check-Correct | iterations=3, self_correction=true |
| **模型评测** | Pass@K | k=8/16, temperature=0.8 |
| **教学演示** | Check-Correct | iterations=3, 查看修正历史 |

### 5.3 性能优化

#### 减少响应时间

1. **降低 K 值**：从 8 降至 4 或 5
2. **降低迭代次数**：从 3 降至 2
3. **使用 Single 模式**：对简单查询使用默认模式
4. **启用缓存**：避免重复执行相同查询

#### 提高准确率

1. **增加 K 值**：从 5 增至 8 或 16
2. **使用 Check-Correct**：启用自我修正
3. **调整 Temperature**：适当增加随机性（0.8-1.0）
4. **优化问题描述**：更清晰的自然语言描述

### 5.4 错误处理

#### 全部候选失败（Pass@K）

```json
{
  "code": 422,
  "message": "All candidates failed",
  "data": {
    "error_code": "ADV_004",
    "suggestions": [
      "检查数据库 Schema 是否正确",
      "尝试重新描述问题",
      "增加 temperature 以获得更大多样性",
      "使用 Check-Correct 模式进行修正"
    ]
  }
}
```

**处理建议**：
1. 检查数据库连接和 Schema
2. 重新表述自然语言问题
3. 增加 temperature 值
4. 切换到 Check-Correct 模式

#### 达到最大迭代次数（Check-Correct）

```json
{
  "code": 422,
  "message": "Max iterations reached without success",
  "data": {
    "error_code": "ADV_005",
    "iteration_count": 3,
    "last_error": "semantic_error",
    "suggestions": [
      "增加 max_iterations 到 4 或 5",
      "简化问题描述",
      "检查数据库 Schema 是否包含所需字段"
    ]
  }
}
```

**处理建议**：
1. 增加 max_iterations
2. 简化问题描述
3. 检查数据库 Schema
4. 考虑人工介入

---

## 6. 常见问题

### Q1: 高级推理功能是否向后兼容？

**答**：完全兼容。默认使用 `single` 模式，与现有 API 行为完全一致。现有代码无需修改即可使用。

### Q2: 各种模式的响应时间如何？

| 模式 | 预期响应时间 | 说明 |
|------|--------------|------|
| Single | ~3s | 单次生成 |
| Pass@K (K=8) | ~10s | 8次并行采样 |
| Majority Vote (K=5) | ~8s | 5次并行采样+投票 |
| Check-Correct (3轮) | ~20s | 最多3轮迭代 |

### Q3: 如何选择合适的 K 值？

**答**：
- **K=1**：与 Single 等效，用于对比测试
- **K=4-5**：快速评估，适合生产环境
- **K=8**：标准 Pass@K 评估，平衡效果与性能
- **K=16**：深度评估，追求最高准确率

### Q4: Check-Correct 能修复哪些类型的错误？

**答**：
- **语法错误**：缺少括号、关键字拼写等
- **执行错误**：表/字段不存在、类型错误等
- **语义错误**：逻辑错误、条件错误、函数使用错误等

### Q5: 是否支持流式输出？

**答**：当前版本暂不支持流式输出。后续版本将通过 WebSocket 提供实时进度更新。

### Q6: 如何查看推理过程的详细信息？

**答**：
- **Pass@K**：设置 `return_all_candidates=true` 查看所有候选
- **Check-Correct**：响应中包含 `correction_history` 字段，显示每轮迭代详情

### Q7: 高级推理功能是否消耗更多 Token？

**答**：是的。Token 消耗与模式相关：
- **Pass@K (K=8)**：约 8 倍于 Single 模式
- **Check-Correct (3轮)**：约 3-6 倍于 Single 模式（取决于实际迭代次数）
- **Majority Vote (K=5)**：约 5 倍于 Single 模式

### Q8: 是否支持在评测任务中使用高级推理？

**答**：支持。创建评测任务时可通过 `eval_mode` 参数指定：
- `greedy_search`：贪婪搜索（默认）
- `pass_at_k`：Pass@K 评估
- `majority_vote`：多数投票
- `check_correct`：Check-Correct 迭代修正

示例：

```json
{
  "name": "Pass@8 Evaluation",
  "dataset_type": "spider",
  "connection_id": 1,
  "api_key_id": 1,
  "eval_mode": "pass_at_k",
  "sampling_count": 8
}
```

### Q9: 温度过高或过低有什么影响？

| Temperature | 影响 | 建议场景 |
|-------------|------|----------|
| 0.0-0.3 | 输出确定性强，多样性低 | 简单查询、确定性场景 |
| 0.4-0.7 | 平衡确定性与多样性 | Check-Correct 模式 |
| 0.8-1.0 | 多样性高，适合采样 | Pass@K、Majority Vote |
| 1.0+ | 随机性很强，可能不稳定 | 探索性场景 |

### Q10: 如何调试推理过程？

**答**：
1. **查看响应字段**：`reasoning_mode`、`execution_time_ms`、`confidence_score`
2. **Pass@K**：启用 `return_all_candidates` 查看每个候选的详情
3. **Check-Correct**：查看 `correction_history` 了解每轮迭代情况
4. **日志分析**：后端日志记录详细推理过程

---

## 附录

### A. 错误码速查表

| 错误码 | HTTP状态 | 说明 | 处理建议 |
|--------|----------|------|----------|
| ADV_001 | 400 | 推理模式不合法 | 检查 reasoning_mode 参数 |
| ADV_002 | 400 | K值超出范围 | K 应在 1-16 之间 |
| ADV_003 | 400 | 迭代次数超出范围 | max_iterations 应在 1-5 之间 |
| ADV_004 | 422 | 全部候选失败 | 检查 Schema 或问题描述 |
| ADV_005 | 422 | 达到最大迭代仍未正确 | 增加迭代次数或简化问题 |
| ADV_009 | 429 | 请求频率超限 | 降低请求频率 |
| ADV_010 | 503 | 推理超时 | 简化问题或增加超时时间 |

### B. 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v1.0.0 | 2026-03-13 | 初始版本，支持四种推理模式 |

---

*文档结束*
