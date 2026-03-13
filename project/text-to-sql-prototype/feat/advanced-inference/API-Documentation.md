# 高级推理功能 - API 接口文档

## 1. 概述

### 1.1 文档信息

| 项目 | 内容 |
|------|------|
| **功能名称** | 高级推理功能 (Advanced Inference) |
| **版本** | v0.1.0 |
| **日期** | 2026-03-13 |
| **编写人** | api-designer |
| **文档状态** | 已发布 |

### 1.2 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `/api/v1` |
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | JWT Token (Bearer) |

### 1.3 认证方式

所有需要认证的接口需在请求头中携带 JWT Token：

```http
Authorization: Bearer {token}
```

### 1.4 通用响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | integer | 状态码，200表示成功 |
| message | string | 提示信息 |
| data | object/array | 响应数据 |

### 1.5 通用错误响应

```json
{
  "code": 400,
  "message": "请求参数错误",
  "data": {
    "error_code": "ADV_001",
    "error_detail": "Invalid reasoning mode: invalid_mode"
  }
}
```

---

## 2. 新增 API 端点

### 2.1 高级 SQL 生成

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/queries/generate-advanced` |
| 方法 | POST |
| 认证 | 是 |
| Content-Type | application/json |
| 说明 | 支持 Pass@K 和 Check-Correct 的高级 SQL 生成 |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| question | string | 是 | - | 自然语言问题，1-2000字符 |
| connection_id | integer | 是 | - | 数据库连接ID |
| provider | string | 否 | null | LLM提供商 |
| reasoning_mode | string | 否 | "single" | 推理模式：single/pass_at_k/check_correct/majority_vote |
| k_candidates | integer | 否 | 5 | 候选数量（Pass@K/MajorityVote），1-16 |
| max_iterations | integer | 否 | 3 | 最大迭代次数（CheckCorrect），1-5 |
| temperature | float | 否 | 0.8 | 采样温度，0.0-2.0 |
| enable_self_correction | boolean | 否 | false | 是否启用自我修正 |
| return_all_candidates | boolean | 否 | false | 是否返回所有候选（仅Pass@K） |

**请求示例 - Pass@K 模式**

```json
{
  "question": "查询销售额最高的5个产品",
  "connection_id": 1,
  "reasoning_mode": "pass_at_k",
  "k_candidates": 8,
  "temperature": 0.8,
  "return_all_candidates": true
}
```

**请求示例 - Check-Correct 模式**

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

**请求示例 - Majority Vote 模式**

```json
{
  "question": "统计2024年每个季度的订单数量",
  "connection_id": 1,
  "reasoning_mode": "majority_vote",
  "k_candidates": 5,
  "temperature": 0.8
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| sql | string | 生成的SQL（最佳结果） |
| reasoning_mode | string | 使用的推理模式 |
| candidates | array | 所有候选（可选，仅Pass@K） |
| candidates[].sql | string | 候选SQL |
| candidates[].is_valid | boolean | 是否执行成功 |
| candidates[].execution_result | array | 执行结果 |
| candidates[].vote_count | integer | 投票数（MajorityVote） |
| pass_at_k_score | float | Pass@K得分，0-1 |
| iteration_count | integer | 实际迭代次数（CheckCorrect） |
| correction_history | array | 修正历史（CheckCorrect） |
| correction_history[].iteration | integer | 迭代轮次 |
| correction_history[].sql | string | 该轮生成的SQL |
| correction_history[].error_type | string | 错误类型 |
| correction_history[].error_message | string | 错误信息 |
| correction_history[].correction_prompt | string | 修正提示 |
| execution_time_ms | float | 执行时间（毫秒） |
| confidence_score | float | 置信度分数，0-1 |

**响应示例 - Pass@K 模式**

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
        "sql": "SELECT product_name, SUM(sales) FROM sales GROUP BY product_name ORDER BY SUM(sales) DESC LIMIT 5",
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
    "execution_time_ms": 4250,
    "confidence_score": 0.75
  }
}
```

**响应示例 - Check-Correct 模式**

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

**响应示例 - Majority Vote 模式**

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
      },
      {
        "sql": "SELECT quarter, COUNT(order_id) FROM orders WHERE year = 2024 GROUP BY quarter",
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

### 2.2 扩展的评测任务创建

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks` |
| 方法 | POST |
| 认证 | 是 |
| Content-Type | application/json |
| 说明 | 创建新的评测任务，支持高级推理模式 |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| name | string | 是 | - | 任务名称，1-200字符 |
| dataset_type | string | 是 | - | 数据集类型：spider/bird/custom |
| dataset_path | string | 否 | null | 自定义数据集路径，最大500字符 |
| connection_id | integer | 是 | - | 数据库连接ID |
| api_key_id | integer | 是 | - | API密钥ID |
| temperature | float | 否 | 0.7 | 采样温度，0.0-2.0 |
| max_tokens | integer | 否 | 2000 | 最大Token数，100-8000 |
| eval_mode | string | 否 | "greedy_search" | 评估模式：greedy_search/majority_vote/pass_at_k/check_correct |
| sampling_count | integer | 否 | 8 | Pass@K的K值，1-16 |
| max_iterations | integer | 否 | 3 | CheckCorrect最大迭代，1-5 |
| correction_strategy | string | 否 | "none" | 修正策略：none/self_correction/execution_feedback/multi_agent |

**请求示例 - Pass@K 模式**

```json
{
  "name": "BIRD Pass@8 Evaluation",
  "dataset_type": "bird",
  "dataset_path": "/data/bird/dev.json",
  "connection_id": 2,
  "api_key_id": 1,
  "eval_mode": "pass_at_k",
  "sampling_count": 8,
  "temperature": 0.8
}
```

**请求示例 - Check-Correct 模式**

```json
{
  "name": "Spider Check-Correct Evaluation",
  "dataset_type": "spider",
  "dataset_path": "/data/spider/dev.json",
  "connection_id": 1,
  "api_key_id": 1,
  "eval_mode": "check_correct",
  "max_iterations": 3,
  "correction_strategy": "execution_feedback",
  "temperature": 0.7
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |
| name | string | 任务名称 |
| status | string | 状态：pending/running/completed/failed |
| eval_mode | string | 评估模式 |
| sampling_count | integer | 采样数量（Pass@K） |
| max_iterations | integer | 最大迭代次数（CheckCorrect） |
| correction_strategy | string | 修正策略 |
| created_at | string | 创建时间，ISO 8601格式 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "BIRD Pass@8 Evaluation",
    "status": "pending",
    "eval_mode": "pass_at_k",
    "sampling_count": 8,
    "max_iterations": null,
    "correction_strategy": "none",
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

---

## 3. 请求/响应 Schema

### 3.1 QueryGenerateAdvancedRequest

```python
class QueryGenerateAdvancedRequest(BaseModel):
    """高级 SQL 生成请求"""
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

    # 新增字段
    reasoning_mode: str = Field(
        "single",
        pattern="^(single|pass_at_k|check_correct|majority_vote)$",
        description="推理模式"
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
                "temperature": 0.8
            }
        }
    )
```

### 3.2 QueryGenerateAdvancedResponse

```python
class CandidateSQL(BaseModel):
    """候选 SQL"""
    sql: str = Field(..., description="候选SQL语句")
    is_valid: bool = Field(..., description="是否执行成功")
    execution_result: Optional[List[Dict]] = Field(
        None,
        description="执行结果"
    )
    vote_count: Optional[int] = Field(
        None,
        description="投票数（MajorityVote）"
    )


class CorrectionRecord(BaseModel):
    """修正记录"""
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


class QueryGenerateAdvancedResponse(BaseModel):
    """高级 SQL 生成响应"""
    sql: str = Field(..., description="生成的SQL（最佳结果）")
    reasoning_mode: str = Field(..., description="使用的推理模式")

    # Pass@K 相关
    candidates: Optional[List[CandidateSQL]] = Field(
        None,
        description="所有候选（可选）"
    )
    pass_at_k_score: Optional[float] = Field(
        None,
        description="Pass@K得分"
    )

    # CheckCorrect 相关
    iteration_count: Optional[int] = Field(
        None,
        description="实际迭代次数"
    )
    correction_history: Optional[List[CorrectionRecord]] = Field(
        None,
        description="修正历史"
    )

    # 通用
    execution_time_ms: float = Field(
        ...,
        description="执行时间（毫秒）"
    )
    confidence_score: Optional[float] = Field(
        None,
        description="置信度分数"
    )
```

### 3.3 扩展的 EvalTaskCreate

```python
class EvalTaskCreate(BaseModel):
    """扩展的评测任务创建请求"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="任务名称"
    )
    dataset_type: str = Field(
        ...,
        pattern="^(spider|bird|custom)$",
        description="数据集类型"
    )
    dataset_path: Optional[str] = Field(
        None,
        max_length=500,
        description="数据集路径"
    )
    connection_id: int = Field(
        ...,
        description="数据库连接ID"
    )
    api_key_id: int = Field(
        ...,
        description="API密钥ID"
    )
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="采样温度"
    )
    max_tokens: int = Field(
        2000,
        ge=100,
        le=8000,
        description="最大Token数"
    )

    # 扩展的枚举值
    eval_mode: str = Field(
        "greedy_search",
        pattern="^(greedy_search|majority_vote|pass_at_k|check_correct)$",
        description="评估模式"
    )

    # 新增字段
    sampling_count: int = Field(
        8,
        ge=1,
        le=16,
        description="Pass@K的K值"
    )
    max_iterations: int = Field(
        3,
        ge=1,
        le=5,
        description="CheckCorrect最大迭代"
    )
    correction_strategy: str = Field(
        "none",
        pattern="^(none|self_correction|execution_feedback|multi_agent)$",
        description="修正策略"
    )
```

---

## 4. 枚举值定义

### 4.1 ReasoningMode 枚举

| 值 | 说明 | 适用场景 |
|----|------|----------|
| single | 单次生成（现有行为） | 快速查询 |
| pass_at_k | K次采样，返回第一个正确 | 提高成功率 |
| check_correct | 生成-检查-修正迭代 | 复杂查询 |
| majority_vote | K次采样，多数投票 | 稳定输出 |

### 4.2 EvalMode 枚举

| 值 | 说明 |
|----|------|
| greedy_search | 贪婪搜索（默认） |
| majority_vote | 多数投票 |
| pass_at_k | Pass@K 评估 |
| check_correct | Check-Correct 迭代修正 |

### 4.3 CorrectionStrategy 枚举

| 值 | 说明 |
|----|------|
| none | 不修正 |
| self_correction | 模型自我修正 |
| execution_feedback | 基于执行错误修正 |
| multi_agent | 多代理协作修正 |

### 4.4 ErrorType 枚举

| 值 | 说明 |
|----|------|
| syntax_error | SQL语法错误 |
| execution_error | 执行错误（表不存在等） |
| semantic_error | 语义错误（结果不正确） |
| timeout_error | 执行超时 |
| generation_error | 生成错误 |

---

## 5. 错误码定义

### 5.1 新增错误码

| 错误码 | HTTP状态 | 英文标识 | 说明 | 场景 |
|--------|----------|----------|------|------|
| ADV_001 | 400 | InvalidReasoningMode | 推理模式不合法 | reasoning_mode 不在枚举值中 |
| ADV_002 | 400 | InvalidKValue | K值超出范围 | k_candidates 不在 1-16 范围内 |
| ADV_003 | 400 | InvalidMaxIterations | 迭代次数超出范围 | max_iterations 不在 1-5 范围内 |
| ADV_004 | 422 | AllCandidatesFailed | 全部候选失败 | Pass@K 所有采样都失败 |
| ADV_005 | 422 | MaxIterationsReached | 达到最大迭代仍未正确 | CheckCorrect 达到最大迭代次数 |
| ADV_006 | 500 | CorrectionFailed | 修正过程失败 | CheckCorrect 修正过程异常 |
| ADV_007 | 400 | InvalidCorrectionStrategy | 修正策略不合法 | correction_strategy 不在枚举值中 |
| ADV_008 | 400 | InvalidEvalMode | 评估模式不合法 | eval_mode 不在枚举值中 |
| ADV_009 | 429 | RateLimitExceeded | 请求频率超限 | 高级推理请求过于频繁 |
| ADV_010 | 503 | InferenceTimeout | 推理超时 | 高级推理超过最大等待时间 |

### 5.2 错误响应示例

**ADV_001 - 无效推理模式**

```json
{
  "code": 400,
  "message": "Invalid reasoning mode",
  "data": {
    "error_code": "ADV_001",
    "error_detail": "reasoning_mode must be one of: single, pass_at_k, check_correct, majority_vote",
    "received": "invalid_mode"
  }
}
```

**ADV_004 - 全部候选失败**

```json
{
  "code": 422,
  "message": "All candidates failed",
  "data": {
    "error_code": "ADV_004",
    "error_detail": "All 8 candidates failed to generate valid SQL",
    "failed_count": 8,
    "suggestions": [
      "Check your database schema",
      "Try rephrasing your question",
      "Increase temperature for more diversity"
    ]
  }
}
```

**ADV_005 - 达到最大迭代次数**

```json
{
  "code": 422,
  "message": "Max iterations reached without success",
  "data": {
    "error_code": "ADV_005",
    "error_detail": "Check-Correct reached max iterations (3) without producing correct SQL",
    "iteration_count": 3,
    "last_error": "semantic_error",
    "last_error_message": "Missing WHERE clause for date filter"
  }
}
```

---

## 6. 调用示例

### 6.1 Pass@K 调用示例

**cURL 请求**

```bash
curl -X POST http://localhost:8000/api/v1/queries/generate-advanced \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "查询销售额最高的5个产品",
    "connection_id": 1,
    "reasoning_mode": "pass_at_k",
    "k_candidates": 8,
    "temperature": 0.8,
    "return_all_candidates": true
  }'
```

**Python 示例**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/queries/generate-advanced",
    headers={
        "Authorization": "Bearer <token>",
        "Content-Type": "application/json"
    },
    json={
        "question": "查询销售额最高的5个产品",
        "connection_id": 1,
        "reasoning_mode": "pass_at_k",
        "k_candidates": 8,
        "temperature": 0.8,
        "return_all_candidates": True
    }
)

data = response.json()
print(f"Generated SQL: {data['data']['sql']}")
print(f"Pass@K Score: {data['data']['pass_at_k_score']}")
```

### 6.2 Check-Correct 调用示例

**cURL 请求**

```bash
curl -X POST http://localhost:8000/api/v1/queries/generate-advanced \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "查询每个部门的平均工资",
    "connection_id": 1,
    "reasoning_mode": "check_correct",
    "max_iterations": 3,
    "temperature": 0.7,
    "enable_self_correction": true
  }'
```

**Python 示例**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/queries/generate-advanced",
    headers={
        "Authorization": "Bearer <token>",
        "Content-Type": "application/json"
    },
    json={
        "question": "查询每个部门的平均工资",
        "connection_id": 1,
        "reasoning_mode": "check_correct",
        "max_iterations": 3,
        "temperature": 0.7,
        "enable_self_correction": True
    }
)

data = response.json()
print(f"Generated SQL: {data['data']['sql']}")
print(f"Iterations: {data['data']['iteration_count']}")
for record in data['data']['correction_history']:
    print(f"Iteration {record['iteration']}: {record.get('error_type', 'OK')}")
```

### 6.3 评测任务创建示例（Pass@K 模式）

**cURL 请求**

```bash
curl -X POST http://localhost:8000/api/v1/eval/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "BIRD Pass@8 Evaluation",
    "dataset_type": "bird",
    "dataset_path": "/data/bird/dev.json",
    "connection_id": 2,
    "api_key_id": 1,
    "eval_mode": "pass_at_k",
    "sampling_count": 8,
    "temperature": 0.8
  }'
```

### 6.4 评测任务创建示例（Check-Correct 模式）

**cURL 请求**

```bash
curl -X POST http://localhost:8000/api/v1/eval/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spider Check-Correct Evaluation",
    "dataset_type": "spider",
    "dataset_path": "/data/spider/dev.json",
    "connection_id": 1,
    "api_key_id": 1,
    "eval_mode": "check_correct",
    "max_iterations": 3,
    "correction_strategy": "execution_feedback",
    "temperature": 0.7
  }'
```

---

## 7. WebSocket 实时进度（可选）

### 7.1 连接端点

```
ws://localhost:8000/api/v1/ws/advanced-inference/{task_id}
```

### 7.2 消息格式

**进度更新消息**

```json
{
  "type": "progress",
  "task_id": 123,
  "current": 45,
  "total": 100,
  "detail": {
    "question_id": "dev_45",
    "reasoning_mode": "pass_at_k",
    "candidate_index": 3,
    "status": "executing"
  }
}
```

**Check-Correct 迭代消息**

```json
{
  "type": "iteration",
  "task_id": 123,
  "detail": {
    "question_id": "dev_45",
    "iteration": 2,
    "max_iterations": 3,
    "status": "correcting",
    "error_type": "semantic_error"
  }
}
```

**完成消息**

```json
{
  "type": "completed",
  "task_id": 123,
  "detail": {
    "total_processed": 100,
    "success_count": 85,
    "failed_count": 15,
    "pass_at_k_score": 0.85
  }
}
```

---

## 8. 与现有 API 的对比

| 特性 | 现有 API (/generate) | 新增 API (/generate-advanced) |
|------|---------------------|------------------------------|
| 端点 | /api/v1/queries/generate | /api/v1/queries/generate-advanced |
| 推理模式 | single | single/pass_at_k/check_correct/majority_vote |
| 返回候选 | 否 | 可选 |
| 迭代历史 | 否 | 是 |
| 置信度评分 | 基础 | 增强 |
| 适用场景 | 快速查询 | 高精度/评测场景 |
| 响应时间 | ~3s | 5-30s（取决于模式） |
| 向后兼容 | - | 完全兼容，single 模式等效于现有 API |

---

## 9. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| Pass@K (K=8) | < 15s | 8次采样并行执行总时间 |
| Check-Correct (3轮) | < 30s | 最多3轮迭代总时间 |
| 单次迭代 | < 10s | 生成+检查+修正一轮时间 |
| 并发任务 | >= 4 | 支持并行的推理任务数 |
| 内存占用 | < 2GB | 单次推理任务内存上限 |

---

## 10. EvalTask 扩展字段说明

### 10.1 新增字段概览

EvalTask 模型扩展了以下字段以支持高级推理功能：

| 字段 | 类型 | 说明 | 适用模式 |
|------|------|------|----------|
| `eval_mode` | string | 评估模式：greedy_search/majority_vote/pass_at_k/check_correct | 所有模式 |
| `sampling_count` | integer | Pass@K的K值，采样数量 | pass_at_k, majority_vote |
| `max_iterations` | integer | CheckCorrect最大迭代次数 | check_correct |
| `correction_strategy` | string | 修正策略：none/self_correction/execution_feedback/multi_agent | check_correct |
| `vote_count` | integer | 多数投票的票数（保留字段） | majority_vote |
| `sampling_config` | object | 采样参数配置，如temperature_schedule, top_p等 | pass_at_k, majority_vote |
| `correction_config` | object | 修正策略配置，如error_threshold, retry_policy等 | check_correct |

### 10.2 EvalTaskResponse 扩展字段

```python
class EvalTaskResponse(BaseModel):
    """评测任务响应 Schema"""
    id: int
    user_id: int
    name: str
    dataset_type: str
    dataset_path: Optional[str]
    model_settings: Dict[str, Any] = Field(alias="model_config")
    eval_mode: str                          # 新增：评估模式
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
```

### 10.3 EvalResultResponse 扩展字段

```python
class EvalResultResponse(BaseModel):
    """评测结果响应 Schema"""
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

    # 新增字段
    iteration_count: Optional[int]          # CheckCorrect实际迭代次数
    correction_history: Optional[List[Dict]] # CheckCorrect修正历史
    candidate_sqls: Optional[List[str]]     # Pass@K所有候选SQL
    confidence_score: Optional[float]       # 置信度分数

    created_at: datetime
```

### 10.4 修正历史结构

```json
{
  "correction_history": [
    {
      "iteration": 1,
      "sql": "SELECT department, COUNT(salary) as avg_salary FROM employees GROUP BY department",
      "error_type": "semantic_error",
      "error_message": "使用了 COUNT 而不是 AVG",
      "correction_prompt": "请修正：应该使用 AVG 函数计算平均工资"
    },
    {
      "iteration": 2,
      "sql": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
      "error_type": null,
      "error_message": null,
      "correction_prompt": null
    }
  ]
}
```

### 10.5 候选 SQL 结构

```json
{
  "candidate_sqls": [
    "SELECT product_name, SUM(sales) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 5",
    "SELECT product_name, SUM(sales) FROM sales GROUP BY product_name ORDER BY SUM(sales) DESC LIMIT 5",
    "SELECT * FROM sales ORDER BY sales DESC LIMIT 5"
  ]
}
```

---

## 11. 版本历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v0.1.0 | 2026-03-13 | 初始版本，定义高级推理 API 接口 | api-designer |
| v1.0.0 | 2026-03-13 | 更新为正式版本，添加 EvalTask 扩展字段说明 | review |

---

*文档结束*
