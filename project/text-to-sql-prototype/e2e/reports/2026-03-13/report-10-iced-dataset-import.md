# ICED 数据集导入 E2E 测试报告

**执行日期**: 2026-03-13
**执行人**: e2e-lead
**总用例数**: 6
**通过**: 6
**失败**: 0
**通过率**: 100%

## 摘要

ICED 数据集导入特性 E2E 测试全部通过。在测试过程中发现并修复了两个 Bug：
1. `eval_results` 表缺少高级推理功能所需列
2. 评测结果 API 返回格式与 schema 不匹配

## 详细结果

| 用例ID | 名称 | 结果 | 耗时 | 截图 |
|--------|------|------|------|------|
| TC-ICED-001 | 连接列表验证 | ✅ 通过 | 5min | TC-ICED-001-01-connections-list.png |
| TC-ICED-002 | Schema 验证 | ✅ 通过 | - | - |
| TC-ICED-003 | 评测任务列表验证 | ✅ 通过 | 5min | TC-ICED-003-01-evaluation-list.png |
| TC-ICED-004 | 评测详情查看 | ✅ 通过 | 5min | TC-ICED-004-01-evaluation-detail.png, TC-ICED-004-02-evaluation-detail-fixed.png |
| TC-ICED-005 | 评测任务启动 | ✅ 通过 | - | - |
| TC-ICED-006 | 数据量验证 | ✅ 通过 | 5min | - |

## 验证项

### 1. 数据库连接验证 ✅
- 总连接数: 20 (包含重复的 BIRD 连接)
- BIRD 连接数: 11
- 连接名称格式: "BIRD - {db_id}" ✅
- 连接状态: 全部"正常" ✅
- 连接类型: SQLite ✅

### 2. 评测任务验证 ✅
- 总任务数: 17
- BIRD 任务数: 11
- 任务名称格式: "BIRD Dev - {db_id}" ✅
- 数据集类型: BIRD ✅
- 评测模式: 单模型 ✅

### 3. 数据量验证 ✅
- 总数据条数: 1534 条
- 各数据库问题数与预期一致 ✅

| db_id | 问题数 |
|-------|--------|
| california_schools | 89 |
| card_games | 191 |
| codebase_community | 186 |
| debit_card_specializing | 64 |
| european_football_2 | 129 |
| financial | 106 |
| formula_1 | 174 |
| student_club | 158 |
| superhero | 129 |
| thrombosis_prediction | 163 |
| toxicology | 145 |

## 发现的问题

### BUG-005: eval_results 表结构缺失
**严重级别**: 🔴 Critical
**状态**: ✅ 已修复

**问题描述**:
`eval_results` 表缺少高级推理功能所需的列，导致评测结果 API 返回 500 错误。

**错误信息**:
```
(sqlite3.OperationalError) no such column: eval_results.iteration_count
```

**修复方案**:
添加缺失的数据库列：
```python
ALTER TABLE eval_results ADD COLUMN iteration_count INTEGER;
ALTER TABLE eval_results ADD COLUMN correction_history TEXT;
ALTER TABLE eval_results ADD COLUMN candidate_sqls TEXT;
ALTER TABLE eval_results ADD COLUMN confidence_score REAL;
```

### BUG-006: 评测结果 API 返回格式不匹配
**严重级别**: 🔴 Critical
**状态**: ✅ 已修复

**问题描述**:
`GET /api/v1/eval/tasks/{id}/results` API 返回格式与 `EvalResultListResponse` schema 不匹配。

**问题原因**:
- API 返回: `{