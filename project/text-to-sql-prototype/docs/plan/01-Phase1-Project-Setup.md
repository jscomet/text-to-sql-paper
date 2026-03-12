# 阶段1：项目初始化

## 阶段目标
建立前后端项目基础结构，配置开发环境，确保团队协作规范统一。

**预计工期**: 0.5天
**实际工期**: 0.5天
**状态**: ✅ 已完成
**完成日期**: 2026-03-12
**并行度**: 高（前端/后端可完全并行）

---

## 任务分解与 Agent 分配

### Task 1.1: 后端项目初始化
**负责人**: `backend-dev`
**依赖**: 无

#### 工作内容
1. 创建后端项目目录结构
   ```
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py              # FastAPI入口
   │   ├── core/                # 核心配置
   │   │   ├── __init__.py
   │   │   ├── config.py        # 配置管理
   │   │   └── logging.py       # 日志配置
   │   ├── api/                 # API路由
   │   │   └── __init__.py
   │   ├── models/              # 数据库模型
   │   │   └── __init__.py
   │   ├── schemas/             # Pydantic模型
   │   │   └── __init__.py
   │   └── utils/               # 工具函数
   │       └── __init__.py
   ├── alembic/                 # 数据库迁移
   ├── tests/                   # 测试目录
   ├── .env.example             # 环境变量模板
   ├── .gitignore
   ├── requirements.txt         # 依赖
   └── README.md
   ```

2. 创建 `requirements.txt`
   ```txt
   # Web框架
   fastapi==0.109.0
   uvicorn[standard]==0.27.0
   python-multipart==0.0.6

   # 数据库
   sqlalchemy==2.0.25
   alembic==1.13.1
   aiosqlite==0.19.0
   asyncpg==0.29.0
   aiomysql==0.2.0

   # 认证
   python-jose[cryptography]==3.3.0
   passlib[bcrypt]==1.7.4

   # 配置
   pydantic-settings==2.1.0
   python-dotenv==1.0.0

   # 工具
   loguru==0.7.2
   httpx==0.26.0
   tenacity==8.2.3

   # 开发依赖
   pytest==7.4.4
   pytest-asyncio==0.21.1
   httpx==0.26.0
   black==23.12.1
   isort==5.13.2
   flake8==7.0.0
   mypy==1.8.0
   ```

3. 创建 `.env.example`
   ```bash
   # 数据库
   DATABASE_URL=sqlite:///./app.db

   # JWT
   SECRET_KEY=your-secret-key-change-in-production
   ACCESS_TOKEN_EXPIRE_MINUTES=60

   # LLM API (至少配置一个)
   OPENAI_API_KEY=sk-your-key
   DASHSCOPE_API_KEY=sk-your-key

   # 环境
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   ```

4. 创建 `app/core/config.py`
   - 使用 Pydantic Settings
   - 支持环境变量加载
   - 区分开发/生产配置

#### 检查点
- [x] 目录结构符合规范
- [x] `pip install -r requirements.txt` 能成功安装
- [x] 配置模块能正常加载环境变量

#### 测试点
```bash
# 测试配置加载
cd backend
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

---

### Task 1.2: 前端项目初始化
**负责人**: `frontend-dev`
**依赖**: 无

#### 工作内容
1. 使用 Vite 创建 Vue3 + TypeScript 项目
   ```bash
   npm create vue@latest frontend
   # 选择: TypeScript, Router, Pinia, ESLint, Prettier
   ```

2. 安装依赖
   ```bash
   cd frontend
   npm install
   npm install element-plus
   npm install @element-plus/icons-vue
   npm install axios
   npm install @vueuse/core
   npm install -D sass
   ```

3. 配置目录结构
   ```
   frontend/src/
   ├── api/              # API接口封装
   ├── assets/           # 静态资源
   ├── components/       # 公共组件
   │   ├── common/       # 通用组件
   │   └── layout/       # 布局组件
   ├── composables/      # 组合式函数
   ├── router/           # 路由配置
   ├── stores/           # Pinia状态管理
   ├── styles/           # 全局样式
   ├── utils/            # 工具函数
   └── views/            # 页面视图
   ```

4. 配置 Element Plus 自动导入
   - 安装 `unplugin-vue-components`
   - 安装 `unplugin-auto-import`
   - 配置 `vite.config.ts`

5. 创建 `.env.development` 和 `.env.production`
   ```bash
   # .env.development
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   VITE_APP_TITLE=Text-to-SQL Prototype
   ```

#### 检查点
- [x] `npm install` 成功无报错
- [x] `npm run dev` 能启动开发服务器
- [x] Element Plus 组件能正常显示
- [x] 环境变量能正确读取

#### 测试点
```bash
cd frontend
npm run dev
# 访问 http://localhost:5173 确认页面加载
```

---

### Task 1.3: Git 仓库初始化
**负责人**: `backend-dev` + `frontend-dev` 协作
**依赖**: Task 1.1, Task 1.2 完成

#### 工作内容
1. 创建根目录 `.gitignore`
   ```
   # Python
   __pycache__/
   *.py[cod]
   *$py.class
   .Python
   venv/
   ENV/
   .env
   *.db

   # Node
   node_modules/
   dist/
   dist-ssr/
   .local

   # IDE
   .idea/
   .vscode/
   *.swp
   *.swo

   # OS
   .DS_Store
   Thumbs.db
   ```

2. 创建根目录 README.md（简要说明）

3. 提交初始代码
   ```bash
   git init
   git add .
   git commit -m "chore: init project structure"
   ```

#### 检查点
- [x] `.gitignore` 生效（敏感文件未被提交）
- [x] 初始提交成功

---

## 阶段交付物

| 交付物 | 位置 | 验收标准 |
|--------|------|----------|
| 后端项目骨架 | `backend/` | 目录结构完整，依赖可安装 |
| 前端项目骨架 | `frontend/` | Vite项目可运行，Element Plus配置完成 |
| 环境配置模板 | `.env.example` | 包含所有必要配置项 |
| Git仓库 | `.git/` | 初始提交完成，.gitignore生效 |

---

## 阶段检查清单

### 功能检查
- [x] 后端配置模块能正常加载
- [x] 前端开发服务器能正常启动
- [x] 前端能正确显示Element Plus组件

### 代码检查
- [x] 目录结构符合规范
- [x] .gitignore 配置完整
- [x] 依赖版本明确指定

### 文档检查
- [x] 根目录 README.md 已创建
- [x] 后端 README.md 已创建

---

## 进入下一阶段条件

1. ✅ Task 1.1、1.2、1.3 全部完成
2. ✅ 前后端项目能独立运行
3. ✅ 代码已提交到Git仓库

---

## 风险与应对

| 风险 | 应对措施 |
|------|----------|
| Node/Python版本不兼容 | 明确版本要求，使用nvm/pyenv |
| 依赖安装失败 | 使用国内镜像源，检查网络 |

---

*依赖文档: ../06-Technical-Architecture.md (技术架构)*
