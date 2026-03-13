# BUG-006: 评测结果 API 返回格式与 Schema 不匹配

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-006 |
| **标题** | 评测结果 API 返回格式与 Schema 不匹配 |
| **严重级别** | 🔴 Critical |
| **优先级** | P0 |
| **状态** | ✅ 已修复 |
| **发现日期** | 2026-03-13 |
| **发现人** | e2e-lead |
| **所属模块** | Evaluation API |
| **相关测试** | TC-ICED-004 |

## 问题描述

修复 BUG-005 后，评测结果 API 返回新的错误。API 返回的数据格式与 `EvalResultListResponse` Schema 定义不匹配，导致 Pydantic 验证失败。

## 复现步骤

1. 修复 BUG-005 后，调用 `GET /api/v1/eval/tasks/{task_id}/results`
2. API 返回 500 错误

## 期望行为

API 返回符合 `EvalResultListResponse` Schema 的数据：
```json
{
  "list": [...],
  "pagination": {
    "total": 0,
    "page": 1,
    "page_size": 20,
    "total_pages": 0
  }
}
```

## 实际行为

API 返回格式：
```json
{
  "items": [...],
  "total": 0,
  "limit": 100,
  "offset": 0
}
```

Pydantic 验证错误：
```
2 validation errors for EvalResultListResponse
list
  Field required
pagination
  Field required
```

## 根本原因

`backend/app/api/v1/evaluations.py` 中的 `get_eval_results` 函数返回格式与 `EvalResultListResponse` Schema 定义不一致。

**Schema 期望** (`backend/app/schemas/evaluation.py`):
```python
class EvalResultListResponse(BaseModel):
    list: List[EvalResultResponse]
    pagination: PaginationInfo
```

**PaginationInfo** (`backend/app/schemas/common.py`):
```python
class PaginationInfo(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
```

**API 实际返回**:
```python
return EvalResultListResponse(
    items=[...],      # ❌ 应该是 list
    total=total,      # ❌ 应该在 pagination 中
    limit=limit,      # ❌ 应该是 page_size
    offset=skip,      # ❌ 未使用
)
```

## 修复方案

修改 `backend/app/api/v1/evaluations.py` 中的返回格式：

```python
# 修复后的代码
page = skip // limit + 1 if limit > 0 else 1
total_pages = (total + limit - 1) // limit if limit > 0 else 1

return EvalResultListResponse(
    list=[EvalResultResponse.model_validate(r) for r in results],
    pagination={
        "total": total,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages,
    },
)
```

## 验证结果

| 检查项 | 结果 | 备注 |
|--------|------|------|
| API 返回格式正确 | ✅ 通过 | 符合 Schema |
| 前端正常解析 | ✅ 通过 | 详情页显示正常 |
| Console 无错误 | ✅ 通过 | 0 errors |

修复后的 API 响应：
```json
{
  "list": [],
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total": 0,
    "total_pages": 0
  }
}
```

## 修复记录

| 日期 | 操作人 | 更新内容 |
|------|--------|----------|
| 2026-03-13 | e2e-lead | 创建 Bug 报告 |
| 2026-03-13 | e2e-lead | 修复 API 返回格式 |
| 2026-03-13 | e2e-lead | 重启后端服务 |
| 2026-03-13 | e2e-lead | 验证修复完成 |

## 相关文件

| 文件路径 | 修改内容 |
|---------|----------|
| `backend/app/api/v1/evaluations.py` | 修改 `get_eval_results` 返回格式 |

## 后续建议

1. 统一所有 API 的返回格式规范
2. 使用共享的 PaginatedResponse 基类
3. 添加 API 响应格式自动化测试
