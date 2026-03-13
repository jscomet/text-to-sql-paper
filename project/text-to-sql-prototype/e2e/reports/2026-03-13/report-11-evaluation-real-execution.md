# 评测真实执行验证 E2E 测试报告

**执行日期**: 2026-03-13
**执行人**: e2e-lead
**总用例数**: 3
**通过**: 1
**失败**: 1
**阻塞**: 1
**通过率**: 33%

---

## 摘要

本次 E2E 测试旨在验证评测任务能够真正执行推理流程。测试过程中发现：
1. ✅ 成功清空所有现有评测任务
2. ❌ 前端创建评测任务时缺少 `dataset_path` 参数，导致任务立即失败
3. 🟡 需要有效的 API Key 才能执行真实评测

---

## 详细结果

### TC-EVAL-REAL-001: 清空现有评测任务

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 访问评测列表页 | ✅ 通过 | 页面正常加载 |
| 清空 17 个现有任务 | ✅ 通过 | 通过数据库直接删除 |
| 验证列表为空 | ✅ 通过 | 显示"暂无评测任务" |

**截图**:
- TC-EVAL-REAL-001-01-initial-eval-list.png (初始状态，17个任务)
- TC-EVAL-REAL-001-02-empty-eval-list.png (清空后状态)

**状态**: ✅ **通过**

---

### TC-EVAL-REAL-002: 创建小型验证评测任务

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 打开新建评测弹窗 | ✅ 通过 | 弹窗正常显示 |
| 填写评测名称 | ✅ 通过 | "E2E验证-debit_card" |
| 选择 BIRD 数据集类型 | ✅ 通过 | BIRD 已选中 |
| 选择数据库连接 | ✅ 通过 | "BIRD - debit_card_specializing" |
| 设置 temperature | ✅ 通过 | 0.1 |
| 创建评测任务 | ⚠️ 部分通过 | 任务创建但状态为"失败" |

**问题分析**:
- 任务创建成功，但 `status` = `failed`
- `total_questions` = 0
- `error_message`: "Failed to load dataset: expected str, bytes or os.PathLike object, not NoneType"
- `dataset_path` = `None`

**根因**: 前端界面创建评测任务时未传递 `dataset_path` 参数

**截图**: TC-EVAL-REAL-002-01-task-created-failed.png

**状态**: ❌ **失败** (发现 BUG-007)

---

### TC-EVAL-REAL-003: 验证评测真正执行推理

**状态**: 🟡 **阻塞**

由于 TC-EVAL-REAL-002 失败，无法执行真实评测验证。

前置条件未满足：
1. 需要修复 BUG-007 (dataset_path 缺失)
2. 需要配置有效的 API Key

---

## 发现的问题

### BUG-007: 前端创建评测任务时缺少 dataset_path 参数

**严重级别**: 🔴 Critical
**优先级**: P0
**状态**: 🟡 待修复
**发现人**: e2e-lead
**所属模块**: Evaluation / Frontend
**相关测试**: TC-EVAL-REAL-002

#### 问题描述

通过前端界面创建评测任务时，`dataset_path` 参数未传递给后端 API，导致任务创建后立即失败。

#### 复现步骤

1. 访问评测管理页 `/evaluations`
2. 点击"新建评测"
3. 填写表单：
   - 评测名称: "E2E验证-debit_card"
   - 数据集类型: BIRD
   - 数据库连接: BIRD - debit_card_specializing
   - 评测模式: 单模型
4. 点击"开始评测"

#### 期望行为

评测任务创建成功，状态为 `pending`，`dataset_path` 正确设置为 BIRD 数据集路径。

#### 实际行为

评测任务创建但状态为 `failed`，`dataset_path` 为 `None`。

错误信息：
```
Failed to load dataset: expected str, bytes or os.PathLike object, not NoneType
```

#### 数据库记录

```sql
SELECT id, name, dataset_path, status, error_message
FROM eval_tasks
WHERE id = 1;
```

结果：
| 字段 | 值 |
|------|-----|
| id | 1 |
| name | E2E验证-debit_card |
| dataset_path | None |
| status | failed |
| error_message | Failed to load dataset: expected str, bytes or os.PathLike object, not NoneType |

#### 根本原因

前端创建评测任务的表单提交时，未包含 `dataset_path` 字段。

**脚本正确调用方式** (参考 `create_eval_tasks.py`):
```python
payload = {
    "name": f"BIRD Dev - {db_id}",
    "dataset_type": "bird",
    "dataset_path": "/path/to/bird_dev.json",  # ← 前端缺少此字段
    "connection_id": connection_id,
    "api_key_id": api_key_id,
    ...
}
```

#### 修复方案

修改前端评测任务创建逻辑：

1. **当选择 BIRD 数据集类型时**，自动设置 `dataset_path` 为后端数据目录下的 `bird_dev.json` 路径
2. 或者添加数据集路径选择/输入字段

**建议修复位置**:
- 前端: `frontend/src/views/evaluation/EvaluationCreateDialog.vue` (假设路径)
- 在提交表单前，根据 `dataset_type` 自动填充 `dataset_path`

```typescript
// 伪代码
const submitForm = () => {
  const payload = {
    ...formData,
    // 如果是 BIRD 类型，自动添加 dataset_path
    dataset_path: formData.dataset_type === 'bird'
      ? '/path/to/backend/data/bird/bird_dev.json'
      : formData.dataset_path
  };
  await api.createEvalTask(payload);
};
```

#### 临时解决方案

使用脚本创建评测任务代替前端界面：

```bash
cd feat/iced-dataset-import/scripts
python create_eval_tasks.py --token "YOUR_TOKEN" --api-key-id 1 --db-filter debit_card_specializing
```

---

## 测试环境信息

| 项目 | 值 |
|------|-----|
| 前端版本 | Vue 3 + Element Plus |
| 后端版本 | FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| 浏览器 | Chromium (Playwright) |
| 测试日期 | 2026-03-13 |

---

## 建议后续操作

1. **P0**: 修复 BUG-007 (前端缺少 dataset_path 参数)
2. **P1**: 配置有效的 API Key 以执行真实评测
3. **P1**: 重新执行 TC-EVAL-REAL-003 验证真实推理
4. **P2**: 添加前端表单验证，确保必要参数完整

---

## 附录

### 数据库验证 SQL

```sql
-- 验证最新评测任务
SELECT
    id,
    name,
    dataset_type,
    dataset_path,
    status,
    total_questions,
    processed_questions,
    error_message
FROM eval_tasks
ORDER BY id DESC
LIMIT 1;
```

### API 测试命令

```bash
# 创建评测任务 (正确方式)
curl -X POST http://localhost:8000/api/v1/eval/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Task",
    "dataset_type": "bird",
    "dataset_path": "/path/to/bird_dev.json",
    "connection_id": 11,
    "api_key_id": 1,
    "eval_mode": "greedy_search",
    "temperature": 0.1
  }'
```

---

*报告生成时间: 2026-03-13*
*报告版本: v1.0*
