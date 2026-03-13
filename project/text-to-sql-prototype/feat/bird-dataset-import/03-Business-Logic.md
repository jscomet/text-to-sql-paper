# BIRD 数据集导入支持 - 业务逻辑文档

## 1. 概述

本文档描述 BIRD 数据集导入功能的业务逻辑、数据流和处理规则。

---

## 2. 核心业务实体

### 2.1 BIRD 数据集

**定义**: 符合 BIRD 项目标准的数据集，包含问题集和数据库文件。

**组成**:
- `dev.json`: 评测问题集（必需）
- `dev_databases/`: 评测数据库目录（必需）
- `train.json`: 训练问题集（可选）
- `train_databases/`: 训练数据库目录（可选）
- `tables.json`: 表结构信息（可选）

**格式验证规则**:
1. JSON 文件必须有效
2. 每个问题必须包含 `question_id`, `db_id`, `question`, `SQL` 字段
3. 每个 `db_id` 必须在 `dev_databases/` 中有对应的 `.sqlite` 文件
4. SQLite 文件必须可读且有效

### 2.2 导入任务

**定义**: 一次数据集导入操作的执行实例。

**状态**:
- `pending`: 等待执行
- `validating`: 验证数据集格式
- `parsing`: 解析数据库列表
- `creating_connections`: 创建数据库连接
- `creating_tasks`: 创建评测任务
- `completed`: 导入完成
- `failed`: 导入失败
- `cancelled`: 用户取消

---

## 3. 业务规则

### 3.1 数据集验证规则

**BR-001**: Zip 文件验证
- 必须是有效的 zip 格式
- 文件大小不超过 1GB
- 解压后必须包含 `dev.json` 或 `train.json`

**BR-002**: JSON 格式验证
- 必须是有效的 JSON 数组
- 每个元素必须包含必需字段

**BR-003**: 数据库文件验证
- 每个 `db_id` 必须有对应的 `.sqlite` 文件
- SQLite 文件必须可读
- 文件大小不超过 500MB（单个数据库）

**BR-004**: 本地目录验证
- 路径必须是绝对路径
- 路径必须可读
- 路径不能是系统敏感目录（如 /etc, /usr, C:\Windows）

### 3.2 连接创建规则

**BR-005**: 连接名称规范
- 格式: `BIRD - {db_id}`
- 示例: `BIRD - california_schools`

**BR-006**: 连接类型
- 固定为 SQLite 类型

**BR-007**: 数据库路径
- 必须使用绝对路径
- 路径中的反斜杠统一转换为正斜杠

**BR-008**: 重复处理
- 如果同名连接已存在，创建新连接（不覆盖）
- 记录所有创建的 connection_id

### 3.3 评测任务创建规则

**BR-009**: 父子任务结构
- 创建一个父任务作为容器（`task_type='parent'`）
- 为每个数据库创建一个子任务（`task_type='child'`）
- 子任务通过 `parent_id` 关联父任务

**BR-010**: 任务名称规范
- 父任务: `BIRD Dev Dataset` 或 `BIRD Dev - {timestamp}`
- 子任务: `BIRD Dev - {db_id}`
- 示例: `BIRD Dev - california_schools`

**BR-011**: 数据集路径
- 父任务和子任务都使用完整的 `dev.json` 路径
- 后端按 `db_id` 自动过滤

**BR-012**: 参数继承
- 父任务存储用户配置
- 子任务继承父任务的配置
- 使用用户选择的 `api_key_id`
- 使用用户选择的 `eval_mode`
- 使用用户设置的 `temperature`, `max_tokens`

**BR-013**: 任务数量
- 创建一个父任务
- 每个数据库创建一个子任务（11个子任务）
- 子任务与连接一一对应

### 3.4 数据集过滤规则

**BR-016**: 自动过滤
- 后端评测时自动按 `db_id` 过滤数据集
- 只处理当前连接对应数据库的问题

**BR-014**: 过滤逻辑
```python
if item.get("db_id") == connection_db_id:
    process(item)
```

**BR-015**: 无 db_id 处理
- 如果数据集没有 `db_id` 字段，处理所有问题
- 兼容非 BIRD 数据集

---

## 4. 业务流程

### 4.1 完整导入流程

```
开始导入
    ↓
步骤1: 接收数据
    - Zip 文件上传 或
    - 本地目录路径
    ↓
步骤2: 验证数据
    - 验证文件/目录存在
    - 验证格式正确性
    - 提取 db_id 列表
    ↓
步骤3: 保存数据（仅上传模式）
    - 创建导入目录
    - 解压 zip 文件
    - 保存数据集
    ↓
步骤4: 创建数据库连接
    - 遍历 db_id 列表
    - 为每个 db_id 创建连接
    - 保存 connection_id 映射
    ↓
步骤5: 创建评测任务
    - 遍历 connection 映射
    - 为每个连接创建评测任务
    - 保存 task_id 映射
    ↓
步骤6: 返回结果
    - 汇总导入统计
    - 返回成功/失败信息
```

### 4.2 异常处理流程

```
开始导入
    ↓
验证失败
    → 返回验证错误
    → 提供错误详情
    → 结束导入
    ↓
部分连接创建失败
    → 继续创建其他连接
    → 记录失败原因
    → 继续后续步骤
    ↓
部分任务创建失败
    → 继续创建其他任务
    → 记录失败原因
    → 部分成功返回
```

### 4.3 状态流转规则

**父任务状态由子任务状态决定**

| 子任务状态组合 | 父任务状态 | 说明 |
|----------------|------------|------|
| 所有子任务 pending | pending | 初始状态，等待执行 |
| 任一子任务 running | running | 有任务正在执行中 |
| 所有子任务 completed | completed | 全部成功完成 |
| 任一子任务 failed + 其他 completed | completed (with errors) | 部分失败，整体完成 |
| 所有子任务 failed | failed | 全部执行失败 |
| 任一子任务 cancelled | cancelled | 用户取消操作 |

**状态转换规则**:

```
pending
  ↓ (任一子任务开始执行)
running
  ↓ (所有子任务执行完毕)
  ├─→ completed (全部成功)
  ├─→ completed (with errors) (部分失败)
  ├─→ failed (全部失败)
  └─→ cancelled (用户取消)
```

---

## 5. 数据模型

### 5.1 导入请求

```typescript
interface DatasetImportRequest {
  dataset_type: 'bird' | 'spider';
  api_key_id: number;
  eval_mode: 'greedy_search' | 'pass_at_k' | 'majority_vote' | 'check_correct';
  temperature: number;
  max_tokens: number;
  sampling_count?: number;      // for pass_at_k
  max_iterations?: number;      // for check_correct
}

interface DatasetZipImportRequest extends DatasetImportRequest {
  file: File;  // multipart/form-data
}

interface DatasetLocalImportRequest extends DatasetImportRequest {
  local_path: string;
}
```

### 5.2 导入响应

```typescript
interface DatasetImportResponse {
  success: boolean;
  message: string;
  import_id: string;
  data_directory: string;
  parent_task_id: number;

  connections: {
    total: number;
    success: number;
    failed: number;
    items: Array<{
      db_id: string;
      connection_id: number;
      status: 'success' | 'failed';
      error?: string;
    }>;
  };

  tasks: {
    total: number;
    success: number;
    failed: number;
    parent_task: {
      id: number;
      name: string;
      task_type: string;
      child_count: number;
    };
    children: Array<{
      db_id: string;
      task_id: number;
      connection_id: number;
      status: string;
      error?: string;
    }>;
  };

  total_questions: number;
}
```

### 5.3 导入进度

```typescript
interface DatasetImportProgress {
  import_id: string;
  status: 'pending' | 'validating' | 'parsing' | 'creating_connections' |
          'creating_tasks' | 'completed' | 'failed' | 'cancelled';

  current_step: number;
  total_steps: number;
  step_name: string;

  progress_percent: number;

  connections_created: number;
  total_connections: number;

  tasks_created: number;
  total_tasks: number;

  logs: Array<{
    timestamp: string;
    level: 'info' | 'warning' | 'error';
    message: string;
  }>;
}
```

---

## 6. 业务校验

### 6.1 前置条件校验

| 校验项 | 规则 | 错误信息 |
|--------|------|----------|
| 用户认证 | 必须已登录 | "请先登录" |
| API Key | 必须已配置 | "请先配置 API Key" |
| 后端权限 | 必须有文件写入权限 | "服务器权限不足" |

### 6.2 数据校验

| 校验项 | 规则 | 错误信息 |
|--------|------|----------|
| Zip 格式 | 必须是有效 zip | "无效的 zip 文件" |
| 文件大小 | 不超过 1GB | "文件超过大小限制" |
| JSON 格式 | 必须是有效 JSON | "JSON 格式错误" |
| 必需字段 | 包含 question, SQL, db_id | "缺少必需字段" |
| 数据库文件 | db_id 对应文件存在 | "数据库文件缺失" |

---

## 7. 性能考虑

### 7.1 大文件处理

- 使用流式解压，避免内存溢出
- 大文件上传使用分片上传
- 异步处理导入任务

### 7.2 批量操作

- 数据库连接批量创建
- 评测任务批量创建
- 使用事务保证数据一致性

---

## 8. 安全考虑

### 8.1 路径安全

- 验证 zip 内文件路径，防止路径遍历
- 限制本地目录导入范围
- 禁止访问系统敏感目录

### 8.2 数据安全

- 导入数据存储在隔离目录
- 不覆盖已有数据
- 定期清理临时文件
