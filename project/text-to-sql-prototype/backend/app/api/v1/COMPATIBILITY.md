# API 向后兼容性说明

## 概述
本文档说明高级推理功能引入的 API 变更及向后兼容处理。

## 兼容性保证

### 1. 现有端点行为不变

#### POST /queries/generate
- **行为**: 保持原有单次生成行为
- **Schema**: `QueryGenerateRequest` 未变更
- **响应**: `QueryGenerateResponse` 未变更

#### POST /queries/run
- **行为**: 保持原有生成+执行行为
- **Schema**: `QueryRunRequest` 未变更
- **响应**: `QueryRunResponse` 未变更

#### POST /queries/execute
- **行为**: 保持原有执行行为
- **Schema**: `QueryExecuteRequest` 未变更
- **响应**: `QueryExecuteResponse` 未变更

#### POST /eval/tasks
- **默认模式**: `greedy_search`（原有行为）
- **新增参数**: 均有合理默认值
  - `eval_mode`: `"greedy_search"`
  - `sampling_count`: `8`
  - `max_iterations`: `3`
  - `correction_strategy`: `"none"`
  - `sampling_config`: `None`
  - `correction_config`: `None`
- **向后兼容**: 不传新参数时行为与之前完全一致

### 2. 新增端点

#### POST /queries/generate-advanced
- **用途**: 支持高级推理模式
- **Schema**: `QueryGenerateAdvancedRequest/Response`
- **模式支持**:
  - `single`: 单次生成（与 /generate 相同）
  - `pass_at_k`: K次采样
  - `majority_vote`: 多数投票
  - `check_correct`: 迭代修正

### 3. 数据库兼容性

#### EvalTask 模型扩展
- 新增字段均有默认值
- 现有数据无需迁移即可正常工作
- 新字段在旧任务中为默认值

#### EvalResult 模型扩展
- 新增字段（candidate_sqls, iteration_count, correction_history, confidence_score）
- 旧数据这些字段为 NULL
- 查询时正常处理 NULL 值

### 4. 默认值汇总

| 字段 | 默认值 | 说明 |
|------|--------|------|
| eval_mode | `"greedy_search"` | 贪婪搜索模式 |
| vote_count | `5` | 多数投票次数 |
| sampling_count | `8` | Pass@K采样数 |
| max_iterations | `3` | 最大迭代次数 |
| correction_strategy | `"none"` | 不启用修正 |
| temperature | `0.7` | 采样温度 |
| max_tokens | `2000` | 最大Token数 |

## 迁移指南

### 对于现有 API 调用者
无需任何修改，所有现有调用方式完全兼容。

### 对于新功能使用者
使用 `/queries/generate-advanced` 端点，指定所需的 `reasoning_mode`。

### 对于评测任务
创建任务时可选择：
- 不传 `eval_mode`: 使用默认 `greedy_search`
- 传 `eval_mode="majority_vote"`: 启用多数投票
- 传 `eval_mode="pass_at_k"`: 启用 Pass@K
- 传 `eval_mode="check_correct"`: 启用迭代修正

## 测试验证

### 向后兼容测试用例
1. 使用旧版请求体调用 `/queries/generate` - 应正常工作
2. 使用旧版请求体调用 `/queries/run` - 应正常工作
3. 使用旧版请求体调用 `/eval/tasks` - 应创建 greedy_search 任务
4. 查询旧版任务数据 - 应正常返回

### 新功能测试用例
1. 调用 `/queries/generate-advanced` 各模式 - 应正常工作
2. 创建各模式评测任务 - 应正常工作
3. 查询包含新字段的结果 - 应正常返回
