# BUG-007: 前端创建评测任务时缺少 dataset_path 参数

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-007 |
| **标题** | 前端创建评测任务时缺少 dataset_path 参数 |
| **严重级别** | 🔴 Critical |
| **优先级** | P0 |
| **状态** | 🟡 待修复 |
| **发现日期** | 2026-03-13 |
| **发现人** | e2e-lead |
| **所属模块** | Evaluation Frontend |
| **相关测试** | TC-EVAL-REAL-002 |

## 问题描述

通过前端界面创建评测任务时，`dataset_path` 参数未传递给后端 API，导致任务创建后立即失败，状态变为 `failed`，错误信息显示数据集加载失败。

## 复现步骤

1. 访问评测管理页 `/evaluations`
2. 点击"新建评测"按钮
3. 在弹窗中填写以下信息：
   - 评测名称: "E2E验证-debit_card"
   - 数据集类型: BIRD
   - 数据库连接: BIRD - debit_card_specializing
   - 评测模式: 单模型 (Greedy Search)
   - Temperature: 0.1
4. 点击"开始评测"

## 期望行为

评测任务创建成功，状态为 `pending`，`dataset_path` 正确设置为 BIRD 数据集路径（例如：`D:/Working/paper/project/text-to-sql-prototype/backend/data/bird/bird_dev.json`）。

## 实际行为

评测任务创建但状态立即变为 `failed`，数据库记录显示：
- `dataset_path` = `None`
- `total_questions` = 0
- `error_message` = "Failed to load dataset: expected str, bytes or os.PathLike object, not NoneType"

## 根本原因

前端创建评测任务的表单提交时，未包含 `dataset_path` 字段。后端期望该字段指定数据集文件路径，但收到 `None`，导致数据集加载失败。

**对比正确的 API 调用** (来自 `create_eval_tasks.py`):
```python
payload = {
    "name": f"BIRD Dev - {db_id}",
    "dataset_type": "bird",
    "dataset_path": "D:/Working/paper/project/text-to-sql-prototype/backend/data/bird/bird_dev.json",  # ← 前端缺少此字段
    "connection_id": connection_id,
    "api_key_id": api_key_id,
    "eval_mode": "greedy_search",
    "temperature": 0.1
}
```

## 修复方案

### 方案一：自动推导数据集路径（推荐）

在前端根据 `dataset_type` 自动填充 `dataset_path`：

```typescript
// 提交表单前处理
const handleSubmit = () => {
  const payload = {
    ...formData,
    // 根据数据集类型自动设置路径
    dataset_path: getDatasetPath(formData.dataset_type)
  };
  await api.createEvalTask(payload);
};

const getDatasetPath = (type: string) => {
  const dataDir = "/path/to/backend/data"; // 可配置
  switch (type) {
    case 'bird':
      return `${dataDir}/bird/bird_dev.json`;
    case 'spider':
      return `${dataDir}/spider/dev.json`;
    default:
      return formData.dataset_path; // 自定义数据集
  }
};
```

### 方案二：添加数据集路径输入字段

在创建评测表单中添加 `dataset_path` 输入字段，允许用户手动指定或使用默认路径。

### 建议修改文件

- **前端**: `frontend/src/views/evaluation/components/CreateEvalDialog.vue` (假设路径)
- **位置**: 表单提交前的数据处理逻辑

## 验证方法

修复后，按以下步骤验证：

1. 访问评测管理页
2. 创建新的评测任务（选择 BIRD 数据集）
3. 检查数据库记录：
   ```sql
   SELECT dataset_path, status FROM eval_tasks ORDER BY id DESC LIMIT 1;
   ```
4. 验证 `dataset_path` 不为 `None`
5. 验证任务状态为 `pending` 或 `running`

## 临时解决方案

在修复前，使用脚本创建评测任务代替前端界面：

```bash
cd feat/iced-dataset-import/scripts
export JWT_TOKEN="your_token_here"
python create_eval_tasks.py --api-key-id 1 --db-filter debit_card_specializing
```

## 影响分析

| 影响项 | 描述 |
|--------|------|
| **功能影响** | 无法通过前端界面创建有效的评测任务 |
| **用户体验** | 用户创建任务后看到失败状态，体验差 |
| **测试阻塞** | 阻塞 E2E 评测执行验证测试 |

## 修复记录

| 日期 | 操作人 | 更新内容 |
|------|--------|----------|
| 2026-03-13 | e2e-lead | 创建 Bug 报告 |

## 相关文件

| 文件路径 | 说明 |
|---------|------|
| `feat/iced-dataset-import/scripts/create_eval_tasks.py` | 正确的 API 调用示例 |
| `e2e/specs/11-Evaluation-Real-Execution-Test-Spec.md` | 相关测试规范 |
| `e2e/reports/2026-03-13/report-11-evaluation-real-execution.md` | 测试报告 |

## 后续建议

1. 在创建评测表单中添加数据集路径配置项
2. 为内置数据集（BIRD/Spider）提供默认路径
3. 添加表单验证，确保 `dataset_path` 不为空
4. 优化错误提示，明确告知用户失败原因
