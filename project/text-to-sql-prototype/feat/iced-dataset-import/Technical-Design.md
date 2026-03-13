# ICED 数据集导入支持 - 技术设计文档

## 1. 架构概述

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层 (CLI)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ copy_bird_data  │  │ create_conn     │  │ create_eval     │  │
│  │     .py         │  │     .py         │  │     .py         │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       数据层 (文件系统)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ICED 数据目录                                            │   │
│  │  ├── dev.json                                            │   │
│  │  └── dev_databases/                                      │   │
│  │      └── {db_id}/{db_id}.sqlite                          │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │ 复制                                   │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Prototype 数据目录                                       │   │
│  │  ├── bird_dev.json                                       │   │
│  │  └── databases/                                          │   │
│  │      └── {db_id}.sqlite                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │
            │ API 调用
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       服务层 (FastAPI)                          │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐│
│  │ /connections  │  │ /connections  │  │ /eval/tasks           ││
│  │     POST      │  │  /{id}/schema │  │      POST             ││
│  │               │  │    /refresh   │  │                       ││
│  └───────────────┘  └───────────────┘  └───────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
ICED 数据
    │
    ├─── bird_dev.json ─────┐
    │                        │
    └─── dev_databases/      │
              │              │
              ▼              ▼
    ┌─────────────────────────────────┐
    │      copy_bird_data.py          │
    │  - 复制数据集文件                │
    │  - 复制 SQLite 数据库            │
    │  - 生成 db_id 列表               │
    └─────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │     create_connections.py       │
    │  - 调用 POST /connections       │
    │  - 生成 db_id_mapping.json      │
    └─────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │      create_eval_tasks.py       │
    │  - 读取映射文件                  │
    │  - 调用 POST /eval/tasks        │
    │  - 批量创建评测任务              │
    └─────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │      Prototype 系统             │
    │  - 数据库连接                   │
    │  - 评测任务                     │
    └─────────────────────────────────┘
```

---

## 2. 详细设计

### 2.1 数据复制脚本 (copy_bird_data.py)

#### 功能
- 创建数据目录结构
- 复制数据集 JSON 文件
- 复制 SQLite 数据库文件
- 生成 db_id 列表

#### 输入
- `iced_dir`: ICED 数据目录路径
- `output_dir`: 输出目录路径

#### 输出
- `bird_dev.json`: 数据集文件
- `databases/*.sqlite`: 数据库文件
- 控制台输出: 复制的文件列表

#### 核心逻辑
```python
def copy_bird_data(iced_dir: Path, output_dir: Path):
    # 1. 创建目录
    (output_dir / "databases").mkdir(parents=True, exist_ok=True)

    # 2. 复制数据集文件
    shutil.copy(iced_dir / "dev.json", output_dir / "bird_dev.json")

    # 3. 获取所有 db_id
    with open(iced_dir / "dev.json") as f:
        dataset = json.load(f)
    db_ids = sorted(set(item["db_id"] for item in dataset))

    # 4. 复制数据库文件
    for db_id in db_ids:
        source = iced_dir / "dev_databases" / db_id / f"{db_id}.sqlite"
        dest = output_dir / "databases" / f"{db_id}.sqlite"
        shutil.copy(source, dest)
```

### 2.2 连接创建脚本 (create_connections.py)

#### 功能
- 通过 API 创建数据库连接
- 为每个数据库生成 connection_id
- 保存 db_id 到 connection_id 的映射

#### 输入
- `token`: JWT Token
- `base_url`: API 基础 URL
- `data_dir`: 数据目录路径

#### 输出
- `db_id_mapping.json`: 映射文件
- 控制台输出: 创建的连接列表

#### API 调用
```http
POST /api/v1/connections
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "BIRD - {db_id}",
  "db_type": "sqlite",
  "database": "{absolute_path}/{db_id}.sqlite"
}
```

#### 核心逻辑
```python
def create_connection(db_id: str, token: str, base_url: str, data_dir: Path) -> int:
    sqlite_path = str(data_dir / "databases" / f"{db_id}.sqlite")

    payload = {
        "name": f"BIRD - {db_id}",
        "db_type": "sqlite",
        "database": sqlite_path
    }

    response = requests.post(
        f"{base_url}/api/v1/connections",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )

    return response.json()["id"]  # connection_id
```

### 2.3 评测任务创建脚本 (create_eval_tasks.py)

#### 功能
- 读取 db_id 到 connection_id 的映射
- 为每个数据库创建评测任务
- 支持自定义评测参数

#### 输入
- `token`: JWT Token
- `api_key_id`: API Key ID
- `base_url`: API 基础 URL
- `eval_mode`: 评测模式
- `temperature`: 采样温度
- `max_tokens`: 最大 Token 数

#### 输出
- 控制台输出: 创建的任务列表

#### API 调用
```http
POST /api/v1/eval/tasks
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "BIRD Dev - {db_id}",
  "dataset_type": "bird",
  "dataset_path": "{absolute_path}/bird_dev.json",
  "connection_id": {connection_id},
  "api_key_id": {api_key_id},
  "temperature": 0.7,
  "max_tokens": 2000,
  "eval_mode": "greedy_search"
}
```

#### 核心逻辑
```python
def create_eval_task(db_id: str, connection_id: int, token: str,
                     api_key_id: int, base_url: str, data_dir: Path) -> int:
    payload = {
        "name": f"BIRD Dev - {db_id}",
        "dataset_type": "bird",
        "dataset_path": str(data_dir / "bird_dev.json"),
        "connection_id": connection_id,
        "api_key_id": api_key_id,
        "temperature": 0.7,
        "max_tokens": 2000,
        "eval_mode": "greedy_search"
    }

    response = requests.post(
        f"{base_url}/api/v1/eval/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )

    return response.json()["id"]  # task_id
```

---

## 3. 数据格式

### 3.1 ICED 数据格式

**文件**: `dev.json`

```json
[
  {
    "question_id": 0,
    "db_id": "california_schools",
    "question": "What is the highest eligible free rate...",
    "evidence": "Eligible free rate...",
    "SQL": "SELECT ...",
    "difficulty": "simple"
  }
]
```

### 3.2 Prototype 数据格式

**文件**: `bird_dev.json` (与 ICED 格式相同)

### 3.3 映射文件格式

**文件**: `db_id_mapping.json`

```json
{
  "california_schools": 1,
  "card_games": 2,
  "codebase_community": 3,
  "debit_card_specializing": 4,
  "european_football_2": 5,
  "financial": 6,
  "formula_1": 7,
  "student_club": 8,
  "superhero": 9,
  "thrombosis_prediction": 10,
  "toxicology": 11
}
```

---

## 4. 错误处理

### 4.1 常见错误及处理

| 错误类型 | 错误信息 | 处理方式 |
|----------|----------|----------|
| 文件不存在 | "Source file not found" | 检查 ICED 数据目录路径 |
| API 认证失败 | "401 Unauthorized" | 检查 JWT Token 是否有效 |
| API Key 无效 | "Invalid API key ID" | 检查 API Key ID 是否正确 |
| 路径格式错误 | "Invalid path" | 使用绝对路径，避免相对路径 |
| 网络错误 | "Connection refused" | 检查后端服务是否启动 |

### 4.2 日志输出

所有脚本都会输出执行日志：
```
[INFO] Copying california_schools.sqlite...
[INFO] ✓ Copied california_schools
[INFO] Creating connection for california_schools...
[INFO] ✓ Created connection 1 for california_schools
[INFO] Creating eval task for california_schools...
[INFO] ✓ Created task 1 for california_schools
```

---

## 5. 安全考虑

### 5.1 Token 安全
- JWT Token 通过命令行参数或环境变量传递
- 不在日志中记录 Token 内容
- 建议使用后立即清除环境变量

### 5.2 路径安全
- 使用 `pathlib.Path` 处理路径，避免路径注入
- 验证源文件存在性
- 确保目标目录可写

---

## 6. 性能考虑

### 6.1 复制性能
- 数据库文件总大小约 500MB
- 复制时间取决于磁盘 I/O 性能
- 预计复制时间 < 1 分钟

### 6.2 API 调用性能
- 每个数据库需要 1 次 API 调用创建连接
- 每个数据库需要 1 次 API 调用创建任务
- 11 个数据库共需 22 次 API 调用
- 预计总时间 < 10 秒（本地 API）

---

## 7. 依赖项

### 7.1 Python 依赖

```
requests >= 2.25.0
```

### 7.2 系统依赖
- Python 3.8+
- Text-to-SQL Prototype 后端服务
- ICED-2026-paper-code 数据文件

---

## 8. 测试策略

### 8.1 单元测试
- 测试路径处理逻辑
- 测试 API 调用封装
- 测试错误处理

### 8.2 集成测试
- 完整流程测试（复制 → 创建连接 → 创建任务）
- 多数据库场景测试
- 错误恢复测试

### 8.3 手动测试
- 验证 Web 界面中的连接和任务
- 验证评测任务可以正常执行

---

## 9. 参考文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Requests 文档](https://docs.python-requests.org/)
- [Prototype API 文档](../../docs/api.md)
