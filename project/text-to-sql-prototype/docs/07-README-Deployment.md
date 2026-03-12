# Text-to-SQL Prototype

## 项目简介

Text-to-SQL Prototype 是一个将自然语言转换为 SQL 查询语句的智能工具原型。该项目旨在帮助非技术用户通过自然语言与数据库进行交互，降低数据查询的技术门槛。

### 核心功能

| 功能模块 | 描述 |
|---------|------|
| **自然语言转 SQL** | 用户输入自然语言问题，系统自动生成对应的 SQL 查询语句 |
| **数据库查询执行** | 支持连接多种数据库（PostgreSQL、MySQL、SQLite），执行生成的 SQL 并返回结果 |
| **查询历史管理** | 保存用户的查询记录，支持查看、复用和导出 |
| **评测管理** | 支持使用标准数据集（如 BIRD）对 Text-to-SQL 模型进行评测 |
| **多模型支持** | 支持 OpenAI、阿里云通义千问等多种 LLM 服务 |

### 技术栈

| 层级 | 技术 |
|-----|------|
| **前端** | Vue 3 + TypeScript + Element Plus |
| **后端** | Python 3.10+ + FastAPI |
| **数据库** | PostgreSQL（生产）/ SQLite（开发） |
| **任务队列** | Celery + Redis（可选） |
| **部署** | Docker + Docker Compose |

### 项目结构

```
text-to-sql-prototype/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 测试用例
│   ├── main.py             # 应用入口
│   └── requirements.txt    # 依赖列表
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── api/            # API 接口
│   │   ├── stores/         # 状态管理
│   │   └── utils/          # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml      # Docker 编排配置
└── docs/                   # 项目文档
```

---

## 环境依赖

### 系统要求

| 依赖 | 版本要求 | 说明 |
|-----|---------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端构建环境 |
| Git | 任意 | 版本控制 |

### 可选依赖

| 依赖 | 版本要求 | 说明 |
|-----|---------|------|
| PostgreSQL | 14+ | 生产环境数据库 |
| Redis | 6+ | Celery 任务队列 |
| Docker | 20.10+ | 容器化部署 |
| Docker Compose | 2.0+ | 多容器编排 |

---

## 开发环境搭建

### 1. 克隆仓库

```bash
git clone <repository-url>
cd text-to-sql-prototype
```

### 2. 后端环境配置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置数据库和 LLM API
# 详见下文"环境变量配置"章节
```

### 3. 数据库初始化

```bash
# 执行数据库迁移
alembic upgrade head

# （可选）创建初始管理员账号
python scripts/create_admin.py --username admin --password admin123
```

### 4. 启动后端服务

```bash
# 开发模式（热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或者直接运行
python main.py
```

后端服务启动后，访问 http://localhost:8000/docs 查看 API 文档。

### 5. 前端环境配置

```bash
# 进入前端目录
cd ../frontend

# 安装依赖
npm install

# 复制环境变量模板
cp .env.example .env.local

# 编辑 .env.local 文件（如需修改 API 地址）
```

### 6. 启动前端服务

```bash
# 开发模式
npm run dev
```

前端服务默认运行在 http://localhost:5173

---

## 环境变量配置

### 后端环境变量 (.env)

```bash
# ==========================================
# 数据库配置
# ==========================================
# SQLite（开发环境）
DATABASE_URL=sqlite:///./app.db

# PostgreSQL（生产环境）
# DATABASE_URL=postgresql://user:password@localhost:5432/text2sql

# 数据库连接池配置（可选）
# DB_POOL_SIZE=10
# DB_MAX_OVERFLOW=20

# ==========================================
# JWT 认证配置
# ==========================================
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

# ==========================================
# LLM API 配置（至少配置一个）
# ==========================================

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 阿里云 DashScope（通义千问）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key
DASHSCOPE_MODEL=qwen2.5-coder-32b-instruct
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ==========================================
# Redis 配置（可选，用于 Celery）
# ==========================================
REDIS_URL=redis://localhost:6379/0

# ==========================================
# Celery 配置（可选）
# ==========================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ==========================================
# 应用配置
# ==========================================
# 环境: development / production
ENVIRONMENT=development

# 日志级别: DEBUG / INFO / WARNING / ERROR
LOG_LEVEL=INFO

# CORS 允许来源（开发环境可设为 *）
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# ==========================================
# 评测配置
# ==========================================
# 评测任务超时时间（秒）
EVALUATION_TIMEOUT=3600
# 最大并发评测数
MAX_CONCURRENT_EVALUATIONS=5
```

### 前端环境变量 (.env.local)

```bash
# API 基础地址
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 应用标题
VITE_APP_TITLE=Text-to-SQL Prototype
```

---

## 数据库初始化

### 自动迁移

项目使用 Alembic 进行数据库版本管理：

```bash
# 执行所有迁移（升级到最新版本）
alembic upgrade head

# 回滚到上一个版本
alembic downgrade -1

# 回滚到初始版本
alembic downgrade base

# 查看当前版本
alembic current

# 查看历史版本
alembic history
```

### 创建新迁移

当修改数据模型后：

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "描述变更内容"

# 执行迁移
alembic upgrade head
```

### 初始数据

```bash
# 创建管理员账号
python scripts/create_admin.py --username admin --password your-password

# 导入示例数据库连接
python scripts/import_connections.py --file connections.json
```

---

## 运行项目

### 开发模式

需要同时运行前后端服务：

**终端 1 - 后端：**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload
```

**终端 2 - 前端：**
```bash
cd frontend
npm run dev
```

**终端 3 - Celery（可选，用于异步任务）：**
```bash
cd backend
source venv/bin/activate
celery -A app.core.celery worker --loglevel=info
```

访问地址：
- 前端界面：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 生产模式

#### 方式一：手动部署

```bash
# 1. 构建前端
cd frontend
npm install
npm run build

# 2. 配置 Web 服务器（Nginx）
# 将前端 dist 目录作为静态资源
# 配置反向代理到后端服务

# 3. 启动后端（使用 Gunicorn）
cd backend
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 方式二：Docker 部署（推荐）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建
docker-compose up -d --build
```

---

## Docker 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    container_name: text2sql-db
    environment:
      POSTGRES_USER: text2sql
      POSTGRES_PASSWORD: text2sql_password
      POSTGRES_DB: text2sql
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U text2sql"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis 缓存/队列
  redis:
    image: redis:7-alpine
    container_name: text2sql-redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: text2sql-backend
    environment:
      - DATABASE_URL=postgresql://text2sql:text2sql_password@db:5432/text2sql
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    volumes:
      - ./backend/logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000"

  # Celery Worker
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: text2sql-worker
    environment:
      - DATABASE_URL=postgresql://text2sql:text2sql_password@db:5432/text2sql
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    volumes:
      - ./backend/logs:/app/logs
    depends_on:
      - db
      - redis
    command: celery -A app.core.celery worker --loglevel=info

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: text2sql-frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 部署步骤

1. **准备环境变量文件**

```bash
# 创建生产环境变量文件
cat > .env.production << EOF
SECRET_KEY=your-production-secret-key
OPENAI_API_KEY=sk-your-openai-key
DASHSCOPE_API_KEY=sk-your-dashscope-key
EOF
```

2. **启动服务**

```bash
docker-compose --env-file .env.production up -d
```

3. **初始化数据库**

```bash
# 执行迁移
docker-compose exec backend alembic upgrade head

# 创建管理员账号
docker-compose exec backend python scripts/create_admin.py --username admin --password your-password
```

4. **验证部署**

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

---

## 使用指南

### 快速开始

#### 1. 注册账号

1. 访问前端界面 http://localhost:5173
2. 点击"注册"按钮
3. 填写用户名、邮箱和密码
4. 完成注册后自动登录

#### 2. 添加数据库连接

1. 进入"数据库管理"页面
2. 点击"添加连接"
3. 填写连接信息：
   - 连接名称：便于识别的名称
   - 数据库类型：PostgreSQL / MySQL / SQLite
   - 主机地址：数据库服务器地址
   - 端口：数据库端口
   - 数据库名：目标数据库名称
   - 用户名/密码：数据库凭据
4. 点击"测试连接"验证配置
5. 保存连接

#### 3. 开始自然语言查询

1. 进入"查询"页面
2. 选择已配置的数据库连接
3. 在输入框中输入自然语言问题，例如：
   - "查询最近7天的订单总数"
   - "显示销售额最高的前10个产品"
   - "统计每个地区的客户数量"
4. 点击"生成 SQL"
5. 查看生成的 SQL 语句和执行结果

#### 4. 查看查询历史

1. 进入"历史记录"页面
2. 查看所有过往查询
3. 支持：
   - 重新执行查询
   - 复制 SQL 语句
   - 导出结果
   - 删除记录

### 评测功能使用

#### 1. 准备评测数据集

评测数据集使用 JSON 格式，参考 BIRD 数据集格式：

```json
[
  {
    "question": "查询2023年销售额最高的产品",
    "db_id": "sales_db",
    "query": "SELECT product_name FROM sales WHERE year = 2023 ORDER BY amount DESC LIMIT 1",
    "evidence": "销售额最高的产品"
  }
]
```

#### 2. 创建评测任务

1. 进入"评测管理"页面
2. 点击"新建评测"
3. 填写评测信息：
   - 评测名称：便于识别的名称
   - 选择数据库：目标数据库连接
   - 上传数据集：选择准备好的 JSON 文件
   - 选择模型：OpenAI / 通义千问
4. 点击"开始评测"

#### 3. 查看评测结果

1. 在评测列表中查看任务状态
2. 点击"查看详情"查看完整报告
3. 报告包含：
   - 执行准确率（Execution Accuracy）
   - 精确匹配率（Exact Match）
   - 每个样本的详细结果
   - 错误分析

---

## 常见问题

### 数据库连接失败

**问题现象：** 添加数据库连接时提示连接失败

**排查步骤：**

1. **检查网络连通性**
   ```bash
   # 测试数据库端口是否可达
   telnet <db-host> <db-port>
   # 或
   nc -zv <db-host> <db-port>
   ```

2. **验证连接信息**
   - 确认主机地址和端口正确
   - 检查用户名和密码
   - 确认数据库名称存在

3. **检查数据库服务状态**
   - 确认数据库服务已启动
   - 检查防火墙设置

4. **查看后端日志**
   ```bash
   # Docker 部署
docker-compose logs backend

   # 本地部署
   tail -f backend/logs/app.log
   ```

### LLM API 调用失败

**问题现象：** 生成 SQL 时提示 API 错误

**排查步骤：**

1. **检查 API Key**
   - 确认 `.env` 文件中 API Key 已正确配置
   - 验证 API Key 是否有效（余额充足）

2. **检查网络连接**
   ```bash
   # 测试 API 可达性
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. **查看错误日志**
   - 后端日志会显示详细的 API 错误信息
   - 常见错误：429（请求过多）、401（认证失败）、500（服务错误）

4. **切换模型**
   - 如 OpenAI 服务异常，可临时切换到阿里云模型
   - 修改 `DASHSCOPE_API_KEY` 并重启服务

### 评测任务超时

**问题现象：** 评测任务长时间未完成

**解决方案：**

1. **检查 Celery Worker**
   ```bash
   # 查看 Worker 状态
docker-compose ps

   # 查看 Worker 日志
   docker-compose logs worker
   ```

2. **调整超时配置**
   ```bash
   # 修改 .env 中的超时时间
   EVALUATION_TIMEOUT=7200  # 2小时
   ```

3. **分批评测**
   - 将大数据集拆分为多个小数据集
   - 分别创建评测任务

### 前端无法连接后端

**问题现象：** 页面提示"网络错误"或"无法连接服务器"

**排查步骤：**

1. **检查后端服务状态**
   ```bash
   curl http://localhost:8000/health
   ```

2. **检查 CORS 配置**
   - 确认 `.env` 中 `CORS_ORIGINS` 包含前端地址
   - 修改后需重启后端服务

3. **检查前端配置**
   - 确认 `.env.local` 中 `VITE_API_BASE_URL` 正确
   - 修改后需重新启动前端服务

---

## 开发规范

### 代码风格

#### Python（后端）

- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 isort 管理导入排序
- 最大行长度：100 字符

```bash
# 格式化代码
black app/ tests/
isort app/ tests/

# 代码检查
flake8 app/ tests/
mypy app/
```

#### TypeScript（前端）

- 使用 ESLint + Prettier
- 遵循 Vue 3 风格指南
- 使用 Composition API

```bash
# 代码检查
npm run lint

# 自动修复
npm run lint:fix

# 类型检查
npm run type-check
```

### 提交规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型说明：**

| 类型 | 说明 |
|-----|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档更新 |
| `style` | 代码格式调整 |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

**示例：**

```bash
git commit -m "feat(query): 添加查询历史导出功能"
git commit -m "fix(api): 修复数据库连接池泄漏问题"
git commit -m "docs(readme): 更新部署文档"
```

### 分支管理

采用 Git Flow 工作流：

```
main        生产分支，稳定版本
  ↑
develop     开发分支，集成测试
  ↑
feature/*   功能分支，新功能开发
  ↑
hotfix/*    热修复分支，紧急修复
  ↑
release/*   发布分支，版本准备
```

**工作流程：**

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/user-authentication

# 2. 开发完成后提交
git add .
git commit -m "feat(auth): 实现用户认证功能"

# 3. 推送到远程
git push origin feature/user-authentication

# 4. 创建 Pull Request 合并到 develop

# 5. 发布时从 develop 创建 release 分支
git checkout -b release/v1.0.0

# 6. 测试通过后合并到 main 和 develop
```

---

## 附录

### API 端点速查

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/databases` | GET/POST | 数据库连接管理 |
| `/api/v1/queries` | GET/POST | 查询历史管理 |
| `/api/v1/queries/generate` | POST | 生成 SQL |
| `/api/v1/queries/execute` | POST | 执行 SQL |
| `/api/v1/evaluations` | GET/POST | 评测任务管理 |
| `/api/v1/evaluations/{id}/run` | POST | 运行评测 |

### 环境变量完整列表

| 变量名 | 必填 | 默认值 | 说明 |
|-------|------|-------|------|
| `DATABASE_URL` | 是 | - | 数据库连接字符串 |
| `SECRET_KEY` | 是 | - | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | 60 | Token 过期时间 |
| `OPENAI_API_KEY` | 条件 | - | OpenAI API Key |
| `DASHSCOPE_API_KEY` | 条件 | - | 阿里云 API Key |
| `REDIS_URL` | 否 | - | Redis 连接地址 |
| `ENVIRONMENT` | 否 | development | 运行环境 |
| `LOG_LEVEL` | 否 | INFO | 日志级别 |
| `CORS_ORIGINS` | 否 | ["*"] | CORS 白名单 |

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 许可证

[MIT License](../LICENSE)

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至：<your-email@example.com>
