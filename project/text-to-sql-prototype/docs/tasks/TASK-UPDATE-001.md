# Task Update: 模式分发逻辑重构 + Pass@K 评测实现

**Date**: 2026-03-13
**Status**: COMPLETED
**Assignee**: backend-task

## 完成的任务

### 任务 #13: 模式分发逻辑重构 (COMPLETED)

重构 `EvalTaskRunner` 支持多种推理模式，实现以下功能：

#### 1. 抽象基类 `InferenceExecutor`
- 定义统一的执行器接口
- 支持进度报告方法 `report_progress()`
- 所有具体执行器继承此基类

#### 2. 三种执行器实现

| 执行器 | 模式 | 说明 |
|--------|------|------|
| `GreedySearchExecutor` | greedy_search | 确定性生成 (temperature=0) |
| `SamplingExecutor` | sampling / pass_at_k | 采样生成 K 个候选 |
| `CheckCorrectExecutor` | check_correct | 迭代自修正生成 |

#### 3. `EvalTaskRunner` 类
- 根据 `inference_mode` 自动分发到对应执行器
- 统一的任务执行接口 `run()`
- 支持进度回调注册
- 向后兼容旧版 `run_evaluation_task()` 函数

### 任务 #14: `_run_pass_at_k_evaluation()` (COMPLETED)

实现 Pass@K 评测任务执行：

#### 功能特性
1. **候选生成**: 调用 `generate_sql_pass_at_k` 生成 K 个候选 SQL
2. **正确性评估**: 每个候选与 gold SQL 对比
3. **进度报告**: 支持候选生成进度回调 `(current, total)`
4. **详细结果**: 返回完整的候选评估结果

#### 返回值结构
```python
{
    "predicted_sql": str,          # 选中的 SQL
    "is_correct": bool,            # 是否有候选正确
    "candidate_results": List[Dict], # 候选详细结果
    "pass_at_k": float,            # Pass@K 指标
    "correct_count": int,          # 正确候选数
    "confidence_score": float,     # 置信度 (正确率)
    "metrics": Dict,               # 完整指标
}
```

#### WebSocket 进度增强
- 报告候选生成进度: `candidate_progress.current/total`
- 包含当前 SQL 预览和正确性状态

## 代码变更

**文件**: `backend/app/tasks/eval_tasks.py`

### 新增类
1. `InferenceExecutor` - 抽象基类
2. `GreedySearchExecutor` - 贪心搜索执行器
3. `SamplingExecutor` - 采样执行器
4. `CheckCorrectExecutor` - 自修正执行器
5. `EvalTaskRunner` - 任务运行器

### 新增函数
- `_run_pass_at_k_evaluation()` - Pass@K 评测实现

### 修改函数
- `run_evaluation_task()` - 使用新的 `EvalTaskRunner`
- `_run_evaluation()` - 标记为 legacy，保持兼容

## 技术设计符合度

根据 `Technical-Design.md` 第5节要求：

| 要求 | 实现状态 |
|------|----------|
| 模式分发逻辑 | ✅ 通过 `EXECUTORS` 注册表实现 |
| 支持 greedy_search | ✅ `GreedySearchExecutor` |
| 支持 sampling | ✅ `SamplingExecutor` |
| 支持 check_correct | ✅ `CheckCorrectExecutor` |
| 统一进度报告 | ✅ `report_progress()` 接口 |
| Pass@K 评测 | ✅ `_run_pass_at_k_evaluation()` |
| 候选生成进度 | ✅ `progress_callback` 参数 |
| 详细结果记录 | ✅ 返回完整候选结果 |

## 依赖关系更新

```
任务 #13 (COMPLETED)
    └── 任务 #14 (COMPLETED)
            └── 任务 #31 (待开始 - _run_check_correct_evaluation)
                    └── 任务 #21 (待开始 - WebSocket 实时进度增强)
```

## 后续任务

### 任务 #31: `_run_check_correct_evaluation()` (PENDING)
实现 Check-Correct 评测任务执行：
- 调用 `generate_sql_with_check_correct` 生成 SQL
- 记录迭代历史和修正过程
- 保存详细结果

### 任务 #21: WebSocket 实时进度增强 (PENDING)
增强实时进度报告：
- 报告候选生成进度 (1/K, 2/K, ...)
- 报告 Check-Correct 迭代进度
- 详细的中间状态信息

## 测试建议

1. **单元测试**: 测试每个执行器的 `execute()` 方法
2. **集成测试**: 测试 `EvalTaskRunner` 的完整流程
3. **模式切换**: 验证不同 inference_mode 的正确分发
4. **进度报告**: 验证 WebSocket 进度回调
5. **Pass@K 计算**: 验证指标计算准确性
