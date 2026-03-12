# Text-to-SQL Prototype

基于大语言模型的自然语言转 SQL 查询系统原型。

## 项目简介

本项目是一个 Text-to-SQL 系统原型，允许用户使用自然语言描述查询需求，系统自动转换为 SQL 语句并执行，返回可视化结果。

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLAlchemy (支持 SQLite/PostgreSQL/MySQL)
- **认证**: JWT
- **LLM**: OpenAI / DashScope

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 20+

### 1. 克隆项目

```bash
git clone <repository-url>
cd text-to-sql-prototype
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 文件，配置数据库和 LLM API 密钥

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 启动，API 文档访问 http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:5173 启动

## 项目结构

```
text-to-sql-prototype/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── core/          # 核心配置
│   │   ├── api/           # API 路由
│   │   ├── models/        # 数据库模型
│   │   ├── schemas/       # Pydantic 模型
│   │   └── utils/         # 工具函数
│   ├── alembic/           # 数据库迁移
│   ├── tests/             # 测试
│   └── requirements.txt   # Python 依赖
├── frontend/               # Vue3 前端
│   ├── src/
│   │   ├── api/           # API 接口
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面视图
│   │   ├── stores/        # Pinia 状态管理
│   │   └── utils/         # 工具函数
│   └── package.json       # Node 依赖
└── docs/                   # 项目文档
    ├── plan/              # 开发计划
    └── report/            # 阶段报告
```

## 文档

- [产品需求文档](docs/01-PRD.md)
- [UI 设计文档](docs/02-UI-Design.md)
- [业务逻辑文档](docs/03-Business-Logic.md)
- [数据库设计](docs/04-Database-Design.md)
- [API 接口文档](docs/05-API-Documentation.md)
- [技术架构文档](docs/06-Technical-Architecture.md)
- [部署文档](docs/07-README-Deployment.md)

## 开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段1 | 项目初始化 | 进行中 |
| 阶段2 | 后端基础 | 待开始 |
| 阶段3 | 后端核心功能 | 待开始 |
| 阶段4 | 前端基础 | 待开始 |
| 阶段5 | 前端页面 | 待开始 |
| 阶段6 | 集成测试 | 待开始 |
| 阶段7 | 部署 | 待开始 |

## 贡献

请参考 [开发计划文档](docs/plan/00-Master-Plan.md) 了解项目结构和开发流程。

## License

MIT
