# ICED 数据集导入支持

将 ICED-2026-paper-code 项目的 BIRD/Spider 评测数据集导入到 Text-to-SQL Prototype 系统进行评测。

---

## 功能介绍

本特性提供一套完整的工具和文档，帮助用户将 ICED 项目的评测数据无缝迁移到 Text-to-SQL Prototype 的 Web 界面中进行评测。

**核心能力**:
- 一键复制 ICED 数据集文件
- 自动创建数据库连接
- 批量生成评测任务
- 支持 BIRD 和 Spider 数据集

---

## 前置条件

### 1. 环境要求
- Python 3.8+
- Text-to-SQL Prototype 后端服务已启动 (http://localhost:8000)
- ICED-2026-paper-code 项目数据文件可访问

### 2. 获取 JWT Token

在运行脚本前，需要先获取访问令牌：

```bash
# 使用 curl 登录获取 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 响应示例：
# {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "token_type": "bearer"}
```

将获取的 `access_token` 保存到环境变量：

```bash
# Windows (PowerShell)
$env:JWT_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Windows (CMD)
set JWT_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...

# Linux/Mac
export JWT_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 3. 配置 API Key

在 Text-to-SQL Prototype Web 界面中配置 LLM API Key：
1. 访问 http://localhost:5173/settings
2. 添加 API Key 配置
3. 记录 `api_key_id`（通常为 1）

---

## 快速开始

### 步骤 1: 复制数据文件

```bash
cd feat/iced-dataset-import/scripts
python copy_bird_data.py
```

**功能**：
- 创建数据目录 `backend/data/bird/`
- 复制 `bird_dev.json` 数据集
- 复制所有 SQLite 数据库文件 (11个)

### 步骤 2: 创建数据库连接

```bash
python create_connections.py --token $JWT_TOKEN
```

**功能**：
- 为每个数据库创建连接
- 生成 `db_id_mapping.json` 映射文件

### 步骤 3: 创建评测任务

```bash
python create_eval_tasks.py --token $JWT_TOKEN --api-key-id 1
```

**功能**：
- 为每个数据库创建评测任务
- 自动使用对应的 connection_id

---

## 详细使用步骤

### 完整流程示例

```bash
# 1. 进入脚本目录
cd feat/iced-dataset-import/scripts

# 2. 复制数据
python copy_bird_data.py \
  --iced-dir "D:/Working/paper/project/ICED-2026-paper-code/data/bird" \
  --output-dir "D:/Working/paper/project/text-to-sql-prototype/backend/data/bird"

# 3. 创建连接
python create_connections.py \
  --token "eyJ0eXAiOiJKV1QiLCJhbGc..." \
  --base-url "http://localhost:8000" \
  --data-dir "D:/Working/paper/project/text-to-sql-prototype/backend/data/bird"

# 4. 创建评测任务
python create_eval_tasks.py \
  --token "eyJ0eXAiOiJKV1QiLCJhbGc..." \
  --api-key-id 1 \
  --base-url "http://localhost:8000" \
  --eval-mode "greedy_search" \
  --temperature 0.7
```

### 参数说明

#### copy_bird_data.py

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--iced-dir` | ICED 数据目录 | `D:/Working/paper/project/ICED-2026-paper-code/data/bird` |
| `--output-dir` | 输出目录 | `D:/Working/paper/project/text-to-sql-prototype/backend/data/bird` |

#### create_connections.py

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--token` | JWT Token | 从环境变量 `JWT_TOKEN` 读取 |
| `--base-url` | API 基础 URL | `http://localhost:8000` |
| `--data-dir` | 数据目录 | `D:/Working/paper/project/text-to-sql-prototype/backend/data/bird` |

#### create_eval_tasks.py

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--token` | JWT Token | 从环境变量 `JWT_TOKEN` 读取 |
| `--api-key-id` | API Key ID | `1` |
| `--base-url` | API 基础 URL | `http://localhost:8000` |
| `--eval-mode` | 评测模式 | `greedy_search` |
| `--temperature` | 采样温度 | `0.7` |
| `--max-tokens` | 最大 Token 数 | `2000` |

---

## 数据集格式说明

### 支持的格式

本特性支持 ICED 项目的标准数据格式：

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

字段映射关系：
| ICED 字段 | Prototype 字段 | 兼容性 |
|-----------|----------------|--------|
| `question_id` | `question_id` | 完全匹配 |
| `db_id` | `db_id` | 完全匹配 |
| `question` | `question` | 完全匹配 |
| `SQL` | `SQL` | 完全匹配 |
| `evidence` | - | 忽略 |
| `difficulty` | - | 忽略 |

---

## 数据库列表

BIRD Dev 数据集包含以下 11 个数据库：

| db_id | 说明 | 数据量 |
|-------|------|--------|
| california_schools | 加州学校数据 | ~150条 |
| card_games | 卡牌游戏数据 | ~150条 |
| codebase_community | 代码库社区 | ~150条 |
| debit_card_specializing | 借记卡专业数据 | ~150条 |
| european_football_2 | 欧洲足球数据 | ~150条 |
| financial | 金融数据 | ~150条 |
| formula_1 | F1赛车数据 | ~150条 |
| student_club | 学生社团 | ~150条 |
| superhero | 超级英雄 | ~150条 |
| thrombosis_prediction | 血栓预测 | ~150条 |
| toxicology | 毒理学 | ~150条 |

---

## 常见问题

### Q1: 为什么每个数据库需要单独创建评测任务？

**A**: 当前版本的 Text-to-SQL Prototype 每个评测任务只支持单个数据库连接。由于 BIRD 数据集包含 11 个独立的数据库，需要为每个数据库创建独立的评测任务。

### Q2: 如何处理 Windows 路径问题？

**A**: 脚本会自动处理路径格式。如果遇到问题，请确保：
- 使用正斜杠 `/` 或双反斜杠 `\\`
- 使用绝对路径

### Q3: 评测任务创建失败怎么办？

**A**: 请检查：
1. 后端服务是否正常运行
2. JWT Token 是否有效
3. API Key ID 是否正确配置
4. 数据文件路径是否正确

### Q4: 如何验证导入是否成功？

**A**: 可以通过以下方式验证：
```bash
# 查看连接列表
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/connections

# 查看评测任务列表
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/eval/tasks
```

或在 Web 界面中查看：
- 连接管理页面: http://localhost:5173/connections
- 评测任务页面: http://localhost:5173/evaluation

---

## 参考文档

- [PRD.md](./PRD.md) - 产品需求文档
- [Technical-Design.md](./Technical-Design.md) - 技术设计文档
- [ICED 项目文档](../../ICED-2026-paper-code/README.md)

---

## 更新日志

### v1.0.0 (2026-03-13)
- 初始版本
- 支持 BIRD Dev 数据集导入
- 提供数据复制、连接创建、任务创建脚本

---

*最后更新: 2026-03-13*
