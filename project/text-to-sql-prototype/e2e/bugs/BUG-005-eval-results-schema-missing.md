# BUG-005: eval_results 表缺少高级推理功能所需列

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-005 |
| **标题** | eval_results 表缺少高级推理功能所需列 |
| **严重级别** | 🔴 Critical |
| **优先级** | P0 |
| **状态** | ✅ 已修复 |
| **发现日期** | 2026-03-13 |
| **发现人** | e2e-lead |
| **所属模块** | Evaluation |
| **相关测试** | TC-ICED-004 |

## 问题描述

在 ICED 数据集导入 E2E 测试过程中，访问评测详情页面时，评测结果 API 返回 500 错误。原因是 `eval_results` 数据库表缺少高级推理功能（Pass@K, Check-Correct）所需的列。

## 复现步骤

1. 访问评测详情页 `/evaluations/{task_id}`
2. 页面调用 `GET /api/v1/eval/tasks/{task_id}/results`
3. API 返回 500 错误

## 期望行为

评测结果 API 正常返回结果列表。

## 实际行为

API 返回 500 错误：
```json
{
  "code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred",
  "error": {
    "details": {
      "error": "(sqlite3.OperationalError) no such column: eval_results.iteration_count"
    }
  }
}
```

## 根本原因

实施高级推理功能时，只迁移了 `eval_tasks` 表，遗漏了 `eval_results` 表的迁移。

缺少的列：
- `iteration_count` - Check-Correct 迭代次数
- `correction_history` - 修正历史记录
- `candidate_sqls` - Pass@K 候选 SQL 列表
- `confidence_score` - 置信度分数

## 修复方案

执行数据库迁移，添加缺失的列：

```python
import sqlite3

conn = sqlite3.connect('backend/app.db')
cursor = conn.cursor()

# Add missing columns
new_columns = [
    ('iteration_count', 'INTEGER'),
    ('correction_history', 'TEXT'),
    ('candidate_sqls', 'TEXT'),
    ('confidence_score', 'REAL')
]

for col_name, col_type in new_columns:
    cursor.execute(f'ALTER TABLE eval_results ADD COLUMN {col_name} {col_type}')

conn.commit()
conn.close()
```

## 验证结果

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 数据库列已添加 | ✅ 通过 | 4个列全部添加 |
| API 正常返回 | ✅ 通过 | 200 OK |
| 详情页无错误 | ✅ 通过 | Console 0 errors |

## 修复记录

| 日期 | 操作人 | 更新内容 |
|------|--------|----------|
| 2026-03-13 | e2e-lead | 创建 Bug 报告 |
| 2026-03-13 | e2e-lead | 执行数据库迁移修复 |
| 2026-03-13 | e2e-lead | 验证修复完成 |

## 后续建议

1. 检查是否有其他表也需要迁移
2. 建立数据库迁移版本控制机制
3. 在 CI/CD 中添加数据库 schema 检查
