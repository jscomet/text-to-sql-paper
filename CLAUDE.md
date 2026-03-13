# Claude.md - Text-to-SQL Prototype 项目指南

## 项目信息

**项目路径**: `D:\Working\paper\project\text-to-sql-prototype`

这是一个基于 Vue.js + FastAPI 的 Text-to-SQL 智能数据库查询系统，支持自然语言转换为 SQL 查询。

## 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus + Vite
- **后端**: FastAPI + SQLAlchemy + Alembic
- **数据库**: SQLite (开发) / PostgreSQL / MySQL
- **LLM**: OpenAI / DeepSeek API
- **E2E 测试**: MCP Playwright Tools

## 服务管理脚本

脚本位置: `@project\text-to-sql-prototype\scripts`

### 前端脚本

```bash
./scripts/frontend-start.sh    # 启动前端 (端口 5173)
./scripts/frontend-stop.sh     # 停止前端
./scripts/frontend-restart.sh  # 重启前端
```

### 后端脚本

```bash
./scripts/backend-start.sh     # 启动后端 (端口 8000)
./scripts/backend-stop.sh      # 停止后端
./scripts/backend-restart.sh   # 重启后端
```

### 统一脚本

```bash
./scripts/start.sh   [frontend|backend|all]  # 启动服务
./scripts/stop.sh    [frontend|backend|all]  # 停止服务
./scripts/restart.sh [frontend|backend|all]  # 重启服务
./scripts/status.sh                           # 查看状态
```

### 快速启动

```bash
# 开发模式 - 启动所有服务
./scripts/start.sh all

# API 文档
http://localhost:8000/docs

# 前端应用
http://localhost:5173
```

## E2E 测试流程

E2E 测试使用 **MCP Playwright Tools** 进行浏览器自动化测试。

**详细文档**: `@project\text-to-sql-prototype\e2e\README.md`

### 测试架构

```
e2e/
├── specs/                          # 测试规范文档
│   ├── 00-E2E-Master-Plan.md       # 总测试计划 (110个用例)
│   ├── 01-Auth-Test-Spec.md        # 认证模块测试 (15个用例)
│   ├── 02-Connection-Test-Spec.md  # 连接管理测试 (20个用例)
│   ├── 03-Query-Test-Spec.md       # 查询功能测试 (30个用例)
│   ├── 04-History-Test-Spec.md     # 历史记录测试 (12个用例)
│   ├── 05-Evaluation-Test-Spec.md  # 评测功能测试 (15个用例)
│   ├── 06-Settings-Test-Spec.md    # 设置页面测试 (10个用例)
│   ├── 07-Regression-Test-Spec.md  # 回归测试套件
│   └── MCP-Playwright-Examples.md  # MCP工具执行示例
├── fixtures/                       # 测试数据
│   ├── test-data.ts
│   └── sample-connections.json
├── reports/                        # 测试报告
│   └── templates/
├── screenshots/                    # 截图目录
└── agent-team/                     # Agent Team 配置
    └── team-spec.md
```

### 测试流程

#### 1. 准备工作

确保服务已启动：

```bash
./scripts/start.sh all
```

#### 2. Playwright MCP 使用

在 Claude Code 中使用 Playwright MCP 进行交互式 E2E 测试：

```typescript
// 导航到应用
await mcp__playwright__browser_navigate({ url: "http://localhost:5173" });

// 获取页面快照
await mcp__playwright__browser_snapshot();

// 点击元素
await mcp__playwright__browser_click({
  element: "登录按钮",
  ref: "e123"
});

// 填写表单
await mcp__playwright__browser_fill_form({
  fields: [
    { name: "用户名", type: "textbox", ref: "e456", value: "admin" },
    { name: "密码", type: "textbox", ref: "e789", value: "admin123" }
  ]
});

// 截图
await mcp__playwright__browser_take_screenshot({ filename: "result.png" });
```

#### 3. 核心测试场景

| 场景               | 测试内容                                        | 规范文档                             |
| ------------------ | ----------------------------------------------- | ------------------------------------ |
| **登录流程** | 验证用户名/密码登录、Token 存储、登录状态保持   | `specs/01-Auth-Test-Spec.md`       |
| **连接管理** | 创建数据库连接、测试连接、刷新 Schema、删除连接 | `specs/02-Connection-Test-Spec.md` |
| **SQL 查询** | 自然语言转 SQL、执行查询、结果展示、导出功能    | `specs/03-Query-Test-Spec.md`      |
| **历史记录** | 查询历史查看、搜索、收藏、删除                  | `specs/04-History-Test-Spec.md`    |
| **评测功能** | SQL 评测任务执行、评分、排行榜                  | `specs/05-Evaluation-Test-Spec.md` |
| **个人设置** | API 密钥配置、个人信息修改                      | `specs/06-Settings-Test-Spec.md`   |
| **回归测试** | 全量回归测试套件                                | `specs/07-Regression-Test-Spec.md` |

#### 4. 测试数据

默认测试账号：

- 用户名: `admin`
- 密码: `admin123`

测试数据库连接：

- 类型: SQLite
- 文件: `backend/app.db`

## 开发工作流

### 1. 启动开发环境

```bash
./scripts/start.sh all
```

### 2. 运行测试

```bash
# 单元测试
cd frontend && npm run test:unit
cd backend && pytest

# E2E 测试
npx playwright test
```

### 3. 代码提交

```bash
# 前端代码规范
cd frontend && npm run lint && npm run format

# 后端代码规范
cd backend && black app/ && isort app/
```

## 常见问题

### 端口占用

```bash
# 检查端口占用
lsof -i:8000  # 后端端口
lsof -i:5173  # 前端端口

# 强制停止所有服务
./scripts/stop.sh all
```

### 依赖安装

```bash
# 前端
npm install

# 后端
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

## 相关链接

- [Playwright 文档](https://playwright.dev/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue.js 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
