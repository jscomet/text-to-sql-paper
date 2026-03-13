# BIRD 数据集导入支持 - API 文档

## 1. 概述

本文档描述 BIRD 数据集导入功能的 API 接口规范。

**基础 URL**: `http://localhost:8000/api/v1`

**认证方式**: JWT Token (Bearer)

---

## 2. API 端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/datasets/import/zip` | 上传 zip 文件导入 |
| POST | `/datasets/import/local` | 指定本地目录导入 |
| GET | `/datasets/imports` | 获取导入历史列表 |
| GET | `/datasets/imports/{import_id}` | 获取导入详情 |
| GET | `/datasets/imports/{import_id}/progress` | 获取导入进度 |
| DELETE | `/datasets/imports/{import_id}` | 删除导入记录 |

---

## 3. 详细接口

### 3.1 上传 zip 文件导入

**端点**: `POST /datasets/import/zip`

**Content-Type**: `multipart/form-data`

**请求头**:
```http
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| file | File | 是 | BIRD 数据集 zip 文件 |
| dataset_type | string | 否 | 数据集类型，默认 "bird" |
| api_key_id | integer | 是 | API Key ID |
| eval_mode | string | 否 | 评测模式，默认 "greedy_search" |
| temperature | float | 否 | 温度参数，默认 0.7 |
| max_tokens | integer | 否 | 最大 token 数，默认 2000 |
| sampling_count | integer | 否 | Pass@K 的 K 值（eval_mode=pass_at_k 时） |
| max_iterations | integer | 否 | 最大迭代次数（eval_mode=check_correct 时） |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/datasets/import/zip \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -F "file=@bird_dev.zip" \
  -F "api_key_id=1" \
  -F "eval_mode=greedy_search" \
  -F "temperature=0.7"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Successfully imported BIRD dataset",
  "import_id": "bird_20260314_143052",
  "data_directory": "/data/bird/bird_20260314_143052",
  "parent_task_id": 100,
  "connections": {
    "total": 11,
    "success": 11,
    "failed": 0,
    "items": [
      {
        "db_id": "california_schools",
        "connection_id": 21,
        "status": "success"
      }
    ]
  },
  "tasks": {
    "total": 11,
    "success": 11,
    "failed": 0,
    "parent_task": {
      "id": 100,
      "name": "BIRD Dev Dataset",
      "task_type": "parent",
      "child_count": 11
    },
    "children": [
      {
        "db_id": "california_schools",
        "task_id": 25,
        "connection_id": 21,
        "status": "success"
      }
    ]
  },
  "total_questions": 1534
}
```

**部分失败响应** (200 OK):
```json
{
  "success": true,
  "message": "Partially imported BIRD dataset",
  "import_id": "bird_20260314_143052",
  "data_directory": "/data/bird/bird_20260314_143052",
  "parent_task_id": 100,
  "connections": {
    "total": 11,
    "success": 10,
    "failed": 1,
    "items": [
      {
        "db_id": "california_schools",
        "connection_id": 21,
        "status": "success"
      },
      {
        "db_id": "financial",
        "connection_id": null,
        "status": "failed",
        "error": "Database file not found"
      }
    ]
  },
  "tasks": {
    "total": 10,
    "success": 10,
    "failed": 0,
    "parent_task": {
      "id": 100,
      "name": "BIRD Dev Dataset",
      "task_type": "parent",
      "child_count": 10
    },
    "children": [
      {
        "db_id": "california_schools",
        "task_id": 25,
        "connection_id": 21,
        "status": "success"
      }
    ]
  },
  "total_questions": 1395
}
```

**错误响应** (400 Bad Request):
```json
{
  "detail": "Invalid file format. Only zip files are supported."
}
```

**错误响应** (422 Validation Error):
```json
{
  "detail": [
    {
      "loc": ["body", "api_key_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### 3.2 指定本地目录导入

**端点**: `POST /datasets/import/local`

**Content-Type**: `application/json`

**请求头**:
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**请求体**:

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| local_path | string | 是 | 本地数据目录绝对路径 |
| dataset_type | string | 否 | 数据集类型，默认 "bird" |
| api_key_id | integer | 是 | API Key ID |
| eval_mode | string | 否 | 评测模式，默认 "greedy_search" |
| temperature | float | 否 | 温度参数，默认 0.7 |
| max_tokens | integer | 否 | 最大 token 数，默认 2000 |
| sampling_count | integer | 否 | Pass@K 的 K 值 |
| max_iterations | integer | 否 | 最大迭代次数 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/datasets/import/local \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "local_path": "/data/bird/dev_20240627",
    "api_key_id": 1,
    "eval_mode": "greedy_search",
    "temperature": 0.7
  }'
```

**响应格式**: 同 3.1

**错误响应** (400 Bad Request):
```json
{
  "detail": "Invalid local path. Directory does not exist or is not readable."
}
```

---

### 3.3 获取导入历史列表

**端点**: `GET /datasets/imports`

**请求头**:
```http
Authorization: Bearer {jwt_token}
```

**查询参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 10 |
| status | string | 否 | 按状态过滤 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/datasets/imports?page=1&page_size=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**成功响应** (200 OK):
```json
{
  "list": [
    {
      "id": 1,
      "import_id": "bird_20260314_143052",
      "import_type": "zip",
      "dataset_type": "bird",
      "status": "completed",
      "total_databases": 11,
      "connections_created": 11,
      "tasks_created": 11,
      "total_questions": 1534,
      "created_at": "2026-03-14T14:30:52Z"
    }
  ],
  "pagination": {
    "total": 5,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

---

### 3.4 获取导入详情

**端点**: `GET /datasets/imports/{import_id}`

**请求头**:
```http
Authorization: Bearer {jwt_token}
```

**路径参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| import_id | string | 是 | 导入标识符 |

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/v1/datasets/imports/bird_20260314_143052 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**成功响应** (200 OK):
```json
{
  "id": 1,
  "import_id": "bird_20260314_143052",
  "import_type": "zip",
  "dataset_type": "bird",
  "source_path": "/tmp/bird_dev.zip",
  "data_directory": "/data/bird/bird_20260314_143052",
  "status": "completed",
  "total_databases": 11,
  "connections_created": 11,
  "tasks_created": 11,
  "total_questions": 1534,
  "connection_ids": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
  "task_ids": [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],
  "api_key_id": 1,
  "eval_mode": "greedy_search",
  "temperature": 0.7,
  "max_tokens": 2000,
  "parent_task_id": 100,
  "parent_task": {
    "id": 100,
    "name": "BIRD Dev Dataset",
    "task_type": "parent",
    "child_count": 11,
    "completed_children": 11,
    "status": "completed"
  },
  "child_tasks": [
    {
      "id": 101,
      "name": "BIRD Dev - california_schools",
      "db_id": "california_schools",
      "connection_id": 21,
      "status": "completed"
    }
  ],
  "started_at": "2026-03-14T14:30:52Z",
  "completed_at": "2026-03-14T14:31:15Z",
  "created_at": "2026-03-14T14:30:52Z"
}
```

**错误响应** (404 Not Found):
```json
{
  "detail": "Import record not found"
}
```

---

### 3.5 获取导入进度

**端点**: `GET /datasets/imports/{import_id}/progress`

**请求头**:
```http
Authorization: Bearer {jwt_token}
```

**路径参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| import_id | string | 是 | 导入标识符 |

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/v1/datasets/imports/bird_20260314_143052/progress \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**成功响应** (200 OK):
```json
{
  "import_id": "bird_20260314_143052",
  "status": "creating_connections",
  "current_step": 3,
  "total_steps": 4,
  "step_name": "创建数据库连接",
  "progress_percent": 65,
  "connections_created": 7,
  "total_connections": 11,
  "tasks_created": 0,
  "total_tasks": 11,
  "logs": [
    {
      "timestamp": "2026-03-14T14:30:52Z",
      "level": "info",
      "message": "开始验证数据集格式"
    },
    {
      "timestamp": "2026-03-14T14:30:53Z",
      "level": "info",
      "message": "发现 11 个数据库"
    },
    {
      "timestamp": "2026-03-14T14:30:55Z",
      "level": "info",
      "message": "创建连接 california_schools (ID: 21)"
    }
  ]
}
```

---

### 3.6 删除导入记录

**端点**: `DELETE /datasets/imports/{import_id}`

**请求头**:
```http
Authorization: Bearer {jwt_token}
```

**路径参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| import_id | string | 是 | 导入标识符 |

**查询参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| delete_data | boolean | 否 | 是否同时删除数据文件，默认 false |

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/datasets/imports/bird_20260314_143052?delete_data=true" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**成功响应** (204 No Content)

**错误响应** (400 Bad Request):
```json
{
  "detail": "Cannot delete import while tasks are running"
}
```

---

## 4. 数据模型

### 4.1 请求模型

#### DatasetZipImportRequest
```json
{
  "file": "binary",
  "dataset_type": "bird",
  "api_key_id": 1,
  "eval_mode": "greedy_search",
  "temperature": 0.7,
  "max_tokens": 2000,
  "sampling_count": 8,
  "max_iterations": 3
}
```

#### DatasetLocalImportRequest
```json
{
  "local_path": "/data/bird/dev_20240627",
  "dataset_type": "bird",
  "api_key_id": 1,
  "eval_mode": "greedy_search",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### 4.2 响应模型

#### DatasetImportResponse
```json
{
  "success": true,
  "message": "string",
  "import_id": "string",
  "data_directory": "string",
  "parent_task_id": 100,  // 父任务ID
  "connections": {
    "total": 11,
    "success": 11,
    "failed": 0,
    "items": [
      {
        "db_id": "string",
        "connection_id": 0,
        "status": "success",
        "error": "string"
      }
    ]
  },
  "tasks": {
    "total": 11,
    "success": 11,
    "failed": 0,
    "parent_task": {
      "id": 100,
      "name": "BIRD Dev Dataset",
      "task_type": "parent",
      "child_count": 11
    },
    "children": [
      {
        "db_id": "string",
        "task_id": 0,
        "connection_id": 0,
        "status": "success",
        "error": "string"
      }
    ]
  },
  "total_questions": 1534
}
```

#### DatasetImportProgress
```json
{
  "import_id": "string",
  "status": "creating_connections",
  "current_step": 3,
  "total_steps": 4,
  "step_name": "string",
  "progress_percent": 65,
  "connections_created": 7,
  "total_connections": 11,
  "tasks_created": 0,
  "total_tasks": 11,
  "logs": [
    {
      "timestamp": "2026-03-14T14:30:52Z",
      "level": "info",
      "message": "string"
    }
  ]
}
```

---

## 5. 错误码

| HTTP 状态码 | 错误码 | 描述 |
|-------------|--------|------|
| 400 | INVALID_FILE_FORMAT | 文件格式无效 |
| 400 | INVALID_DATASET_FORMAT | 数据集格式无效 |
| 400 | INVALID_LOCAL_PATH | 本地路径无效 |
| 400 | FILE_TOO_LARGE | 文件超过大小限制 |
| 400 | IMPORT_RATE_LIMITED | 导入频率限制 |
| 401 | UNAUTHORIZED | 未授权或 Token 过期 |
| 403 | FORBIDDEN | 无权访问该资源 |
| 404 | IMPORT_NOT_FOUND | 导入记录不存在 |
| 409 | IMPORT_IN_PROGRESS | 该数据集正在导入中 |
| 409 | TASKS_RUNNING | 评测任务运行中，无法删除 |
| 422 | VALIDATION_ERROR | 请求参数验证失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 6. WebSocket 实时进度（可选）

**连接**: `ws://localhost:8000/api/v1/ws/datasets/imports/{import_id}`

**消息格式**:
```json
{
  "type": "progress",
  "data": {
    "current_step": 3,
    "total_steps": 4,
    "progress_percent": 65,
    "message": "创建数据库连接 (7/11)"
  }
}
```

**推送时机**:
- 导入步骤切换时（验证完成、开始解析、连接创建、任务创建）
- 每创建一个数据库连接时
- 每创建一个评测任务时
- 导入完成或失败时
- 发生错误时

---

## 7. EvalTask 相关 API 扩展

### 7.1 获取评测任务列表（增强）

**端点**: `GET /evaluations`

**新增查询参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| task_type | string | 否 | 按任务类型筛选: `parent`, `child`, `standalone` |
| parent_id | integer | 否 | 获取指定父任务的子任务 |
| db_id | string | 否 | 按数据库ID筛选 |

**响应增强**:
```json
{
  "list": [
    {
      "id": 100,
      "name": "BIRD-dev-20260314",
      "task_type": "parent",
      "status": "running",
      "child_count": 11,
      "completed_children": 7,
      "progress": 65,
      "created_at": "2026-03-14T14:30:52Z"
    },
    {
      "id": 101,
      "name": "BIRD Dev - california_schools",
      "task_type": "child",
      "parent_id": 100,
      "db_id": "california_schools",
      "connection_id": 21,
      "status": "completed",
      "progress": 100,
      "created_at": "2026-03-14T14:30:53Z"
    }
  ],
  "pagination": {
    "total": 12,
    "page": 1,
    "page_size": 10,
    "total_pages": 2
  }
}
```

### 7.2 获取评测任务详情（增强）

**端点**: `GET /evaluations/{id}`

**父任务响应**:
```json
{
  "id": 100,
  "name": "BIRD-dev-20260314",
  "task_type": "parent",
  "status": "running",
  "child_count": 11,
  "completed_children": 7,
  "failed_children": 1,
  "progress": 65,
  "total_questions": 1534,
  "processed_questions": 998,
  "correct_count": 684,
  "accuracy": 68.5,
  "children": [
    {
      "id": 101,
      "name": "BIRD Dev - california_schools",
      "db_id": "california_schools",
      "connection_id": 21,
      "status": "completed",
      "progress": 100,
      "question_count": 120,
      "processed_count": 120,
      "correct_count": 87,
      "accuracy": 72.5
    }
  ],
  "created_at": "2026-03-14T14:30:52Z",
  "started_at": "2026-03-14T14:31:00Z",
  "updated_at": "2026-03-14T14:35:22Z"
}
```

**子任务响应**:
```json
{
  "id": 101,
  "name": "BIRD Dev - california_schools",
  "task_type": "child",
  "parent_id": 100,
  "parent": {
    "id": 100,
    "name": "BIRD-dev-20260314",
    "task_type": "parent",
    "child_count": 11
  },
  "db_id": "california_schools",
  "connection_id": 21,
  "connection_name": "schools_db",
  "status": "running",
  "progress": 71,
  "question_count": 120,
  "processed_count": 85,
  "correct_count": 62,
  "accuracy": 72.9,
  "questions": [
    {
      "index": 1,
      "question": "How many schools are there?",
      "status": "completed",
      "execution_time": 2.3,
      "is_correct": true,
      "generated_sql": "SELECT COUNT(*) FROM schools",
      "gold_sql": "SELECT COUNT(*) FROM schools"
    }
  ],
  "created_at": "2026-03-14T14:30:53Z",
  "started_at": "2026-03-14T14:31:05Z",
  "updated_at": "2026-03-14T14:35:22Z"
}
```

### 7.3 批量开始子任务

**端点**: `POST /evaluations/{parent_id}/start-all`

**描述**: 批量开始父任务下所有等待中的子任务

**请求体**:
```json
{
  "delay_seconds": 0
}
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Started 4 child tasks",
  "started_count": 4,
  "skipped_count": 7,
  "started_tasks": [105, 106, 107, 108]
}
```

**错误响应** (400 Bad Request):
```json
{
  "detail": "Parent task not found"
}
```

**错误响应** (409 Conflict):
```json
{
  "detail": "Parent task is not in pending state"
}
```

### 7.4 重试失败子任务

**端点**: `POST /evaluations/{parent_id}/retry-failed`

**描述**: 重试父任务下所有失败的子任务

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Retried 2 failed child tasks",
  "retried_count": 2,
  "retried_tasks": [109, 110]
}
```

**错误响应** (400 Bad Request):
```json
{
  "detail": "No failed child tasks to retry"
}
```

### 7.5 获取子任务列表

**端点**: `GET /evaluations/{parent_id}/children`

**描述**: 获取父任务下的所有子任务列表

**查询参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| status | string | 否 | 按状态筛选 |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 10 |

**成功响应** (200 OK):
```json
{
  "parent_id": 100,
  "list": [
    {
      "id": 101,
      "name": "BIRD Dev - california_schools",
      "db_id": "california_schools",
      "connection_id": 21,
      "connection_name": "schools_db",
      "status": "completed",
      "progress": 100,
      "question_count": 120,
      "processed_count": 120,
      "correct_count": 87,
      "accuracy": 72.5
    }
  ],
  "pagination": {
    "total": 11,
    "page": 1,
    "page_size": 10,
    "total_pages": 2
  }
}
```

---

## 8. 补充错误码

### 8.1 新增错误码

| HTTP 状态码 | 错误码 | 描述 |
|-------------|--------|------|
| 404 | PARENT_TASK_NOT_FOUND | 父任务不存在 |
| 400 | CHILD_TASK_CANNOT_START | 子任务无法启动（父任务未就绪） |
| 400 | INVALID_TASK_TYPE | 无效的任务类型 |
| 409 | PARENT_NOT_READY | 父任务状态不允许此操作 |
| 400 | NO_CHILDREN_TO_START | 没有可启动的子任务 |
| 400 | NO_FAILED_CHILDREN | 没有失败的子任务需要重试 |

---

## 9. API 文档检查报告

### 9.1 已有端点清单 ✓

| 端点 | 状态 | 备注 |
|------|------|------|
| POST /datasets/import/zip | ✅ 已定义 | 包含完整请求/响应示例 |
| POST /datasets/import/local | ✅ 已定义 | 包含完整请求/响应示例 |
| GET /datasets/imports | ✅ 已定义 | 包含分页参数 |
| GET /datasets/imports/{import_id} | ✅ 已定义 | 包含 parent_task 和 child_tasks |
| GET /datasets/imports/{import_id}/progress | ✅ 已定义 | 包含步骤进度和日志 |
| DELETE /datasets/imports/{import_id} | ✅ 已定义 | 包含 delete_data 参数 |

### 9.2 请求/响应模型检查

| 模型 | 状态 | 备注 |
|------|------|------|
| DatasetZipImportRequest | ✅ 已定义 | 包含所有参数字段 |
| DatasetLocalImportRequest | ✅ 已定义 | 包含所有参数字段 |
| DatasetImportResponse | ✅ 已定义 | 包含 parent_task_id, tasks.parent, tasks.children |
| DatasetImportProgress | ✅ 已定义 | 包含步骤进度和日志 |

### 9.3 缺失端点清单（需要补充）

#### EvalTask 相关 API

| 端点 | 优先级 | 说明 |
|------|--------|------|
| GET /evaluations | 🟡 High | 需要补充 task_type 筛选参数文档 |
| GET /evaluations/{id} | 🟡 High | 需要补充父子任务详情响应格式 |
| POST /evaluations/{parent_id}/start-all | 🔴 Critical | UI 需要批量开始子任务 |
| POST /evaluations/{parent_id}/retry-failed | 🔴 Critical | UI 需要重试失败子任务 |
| GET /evaluations/{parent_id}/children | 🟡 High | 如果不包含在详情中，需要单独端点 |

### 9.4 错误码检查

| 错误码 | 状态 | 备注 |
|--------|------|------|
| INVALID_FILE_FORMAT | ✅ 已定义 | |
| INVALID_DATASET_FORMAT | ✅ 已定义 | |
| INVALID_LOCAL_PATH | ✅ 已定义 | |
| FILE_TOO_LARGE | ✅ 已定义 | |
| IMPORT_RATE_LIMITED | ✅ 已定义 | |
| UNAUTHORIZED | ✅ 已定义 | |
| FORBIDDEN | ✅ 已定义 | |
| IMPORT_NOT_FOUND | ✅ 已定义 | |
| IMPORT_IN_PROGRESS | ✅ 已定义 | |
| TASKS_RUNNING | ✅ 已定义 | |
| VALIDATION_ERROR | ✅ 已定义 | |
| INTERNAL_ERROR | ✅ 已定义 | |
| PARENT_TASK_NOT_FOUND | ❌ 缺失 | 建议补充 |
| CHILD_TASK_CANNOT_START | ❌ 缺失 | 建议补充 |

### 9.5 WebSocket 设计检查

| 检查项 | 状态 | 备注 |
|--------|------|------|
| WebSocket 连接 URL | ✅ 已定义 | `ws://localhost:8000/api/v1/ws/datasets/imports/{import_id}` |
| 消息格式定义 | ✅ 已定义 | 包含 type 和 data 字段 |
| 推送时机说明 | ⚠️ 已补充 | 原文档缺失，已在第6章补充 |

### 9.6 与 UI 设计对比分析

#### 匹配的功能

| UI 需求 | API 支持 | 匹配度 |
|---------|----------|--------|
| 父子任务列表数据获取 | GET /evaluations + task_type 筛选 | ✅ 完全匹配 |
| 父任务详情（包含子任务列表） | GET /evaluations/{id} | ✅ 支持 |
| 子任务详情（包含父任务信息） | GET /evaluations/{id} | ✅ 支持 |

#### 需要 API 支持的 UI 功能

| UI 功能 | 所需 API | 当前状态 |
|---------|----------|----------|
| 批量开始所有子任务 | POST /evaluations/{parent_id}/start-all | ❌ 需要新增 |
| 批量重试失败任务 | POST /evaluations/{parent_id}/retry-failed | ❌ 需要新增 |
| 子任务列表独立分页 | GET /evaluations/{parent_id}/children | ❌ 建议新增 |

### 9.7 API 响应示例检查

| 响应示例 | 状态 | 备注 |
|----------|------|------|
| 导入成功响应 | ✅ 完整 | 包含 parent_task_id, tasks.parent, tasks.children |
| 导入部分失败响应 | ✅ 完整 | 包含失败项的 error 字段 |
| 父任务详情响应（含 children） | ⚠️ 需要补充 | 已在第7章补充 |
| 子任务详情响应（含 parent） | ⚠️ 需要补充 | 已在第7章补充 |

### 9.8 建议的 API 扩展

1. **优先级 P0（必须）**:
   - 实现 `POST /evaluations/{parent_id}/start-all` 端点
   - 实现 `POST /evaluations/{parent_id}/retry-failed` 端点
   - 增强 `GET /evaluations` 支持 task_type 筛选

2. **优先级 P1（建议）**:
   - 实现 `GET /evaluations/{parent_id}/children` 端点（独立分页子任务）
   - 补充 PARENT_TASK_NOT_FOUND 等错误码
   - 增强 `GET /evaluations/{id}` 返回 questions 列表（用于子任务详情页）

3. **优先级 P2（可选）**:
   - WebSocket 支持评测任务进度推送（不仅限于导入进度）
   - 批量删除子任务端点

### 9.9 与前端 UI 需求的匹配度分析

| 功能模块 | 匹配度 | 说明 |
|----------|--------|------|
| 数据集导入 | 95% | 基本完整，WebSocket 推送时机已补充 |
| 父子任务列表展示 | 80% | 需要增强列表查询接口支持 task_type 筛选 |
| 父任务详情页 | 70% | 需要补充批量操作 API |
| 子任务详情页 | 70% | 需要补充 questions 列表返回 |
| 批量操作 | 50% | 缺少 start-all 和 retry-failed 端点 |

**总体匹配度**: ~75%

**关键缺口**:
1. 批量操作 API（start-all, retry-failed）
2. 子任务详情中的 questions 列表
3. 任务列表的 task_type 筛选

---

*报告生成时间: 2026-03-14*
*检查人: Claude Code*
*文档版本: v1.1*
