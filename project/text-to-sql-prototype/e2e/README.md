# Text-to-SQL Prototype - E2E 测试套件

## 概述

本项目使用 **MCP Playwright 工具** 进行端到端 (E2E) 测试，验证 Text-to-SQL 系统的完整用户流程。

## 目录结构

```
e2e/
├── README.md                          # 本文件 - 总体说明
├── specs/                             # 测试规范文档
│   ├── 00-E2E-Master-Plan.md          # 总测试计划 (110个用例)
│   ├── 01-Auth-Test-Spec.md           # 认证模块测试 (15个用例)
│   ├── 02-Connection-Test-Spec.md     # 连接管理测试 (20个用例)
│   ├── 03-Query-Test-Spec.md          # 查询功能测试 (30个用例)
│   ├── 04-History-Test-Spec.md        # 历史记录测试 (12个用例)
│   ├── 05-Evaluation-Test-Spec.md     # 评测功能测试 (15个用例)
│   ├── 06-Settings-Test-Spec.md       # 设置页面测试 (10个用例)
│   ├── 07-Regression-Test-Spec.md     # 回归测试套件
│   └── MCP-Playwright-Examples.md     # MCP工具执行示例
├── fixtures/                          # 测试数据和样例
│   ├── test-data.ts                   # TypeScript 测试数据
│   ├── sample-connections.json        # 示例连接配置
│   └── sample-datasets/               # 测试数据集目录
├── reports/                           # 测试报告目录
│   ├── templates/                     # 报告模板
│   │   ├── test-report-template.md    # 测试报告模板
│   │   └── bug-report-template.md     # Bug报告模板
│   ├── YYYY-MM-DD/                    # 按日期组织的报告 (示例结构)
│   │   ├── index.md                   # 报告索引
│   │   ├── screenshots/               # 当日截图
│   │   └── bugs/                      # 当日Bug报告
│   └── latest/                        # 最新报告链接
├── screenshots/                       # 截图目录
│   ├── baseline/                      # 基准截图（预期）
│   ├── actual/                        # 实际截图
│   └── diff/                          # 差异对比
└── agent-team/                        # Agent Team 配置
    └── team-spec.md                   # 团队规格文档
```

## 测试执行方式

### 方式一：MCP Playwright 工具（推荐）

使用系统级 Playwright 工具进行交互式测试：

```
mcp__playwright__browser_navigate
mcp__playwright__browser_type
mcp__playwright__browser_click
mcp__playwright__browser_snapshot
mcp__playwright__browser_take_screenshot
```

### 方式二：本地 Playwright（备选）

如需本地批量执行：

```bash
cd frontend
npm run test:e2e
```

## 测试环境配置

### 前置条件

1. **后端服务**: `http://localhost:8000`
   ```bash
   cd backend && uvicorn app.main:app --reload --port 8000
   ```

2. **前端服务**: `http://localhost:5173`
   ```bash
   cd frontend && npm run dev
   ```

3. **测试数据库**: SQLite 内存数据库

### 浏览器配置

- **默认尺寸**: 1920x1080 (桌面)
- **移动端**: 375x812 (iPhone X)
- **平板**: 768x1024 (iPad)

## 快速开始

### 执行单个测试场景

1. 阅读对应的测试规范（`specs/*.md`）
2. 启动前后端服务
3. 使用 MCP Playwright 工具按步骤执行
4. 截图记录结果
5. 填写测试报告

### 执行完整回归测试

参考 `specs/07-Regression-Test-Spec.md` 中的回归测试清单。

## 报告规范

### 测试报告命名

```
reports/YYYY-MM-DD/
├── report-XX-module-feature.md    # 模块测试报告
├── screenshots/
│   ├── XX-01-step-name.png        # 步骤截图
│   └── XX-02-step-name.png
└── bugs/
    └── BUG-XXX-description.md     # 发现的 Bug 报告
```

### Bug 报告命名

```
bugs/BUG-{序号}-{简短描述}.md

示例:
Bugs/BUG-001-login-button-not-working.md
Bugs/BUG-002-query-result-pagination-error.md
```

## Agent Team 协作

### 团队组成

| 角色 | 职责 | 对应文档 |
|------|------|----------|
| e2e-lead | 测试计划制定、报告汇总 | `agent-team/team-spec.md` |
| test-lead | 测试执行、Bug 跟踪 | `specs/*.md` |
| backend-dev | API 问题修复 | 配合测试 |
| frontend-dev | UI 问题修复 | 配合测试 |

### 执行流程

```
1. e2e-lead 制定测试计划
2. test-lead 执行测试用例
3. 发现问题 → 创建 Bug 报告
4. dev-agents 修复问题
5. test-lead 回归测试
6. e2e-lead 汇总报告
```

## 参考文档

- [UI 设计文档](../docs/02-UI-Design.md)
- [业务逻辑文档](../docs/03-Business-Logic.md)
- [API 文档](../docs/05-API-Documentation.md)
- [Phase 6 测试计划](../docs/plan/06-Phase6-Integration-Test.md)

## 测试用例统计

| 模块 | 用例数 | P0 | P1 | P2 | 预计耗时 |
|------|--------|-----|-----|-----|----------|
| 用户认证 (Auth) | 15 | 5 | 7 | 3 | 2h |
| 连接管理 (Connection) | 20 | 8 | 9 | 3 | 3h |
| 查询功能 (Query) | 30 | 12 | 14 | 4 | 5h |
| 历史记录 (History) | 12 | 0 | 10 | 2 | 2h |
| 评测功能 (Evaluation) | 15 | 0 | 12 | 3 | 3h |
| 个人设置 (Settings) | 10 | 0 | 8 | 2 | 2h |
| **总计** | **102** | **25** | **60** | **17** | **17h** |

## 文档索引

### 必读文档（执行前阅读）
1. [Agent Team 规格](agent-team/team-spec.md) - 团队角色和协作流程
2. [E2E 总计划](specs/00-E2E-Master-Plan.md) - 整体测试策略和规划
3. [MCP Playwright 示例](specs/MCP-Playwright-Examples.md) - 工具使用示例

### 测试规范文档（按模块）
- [认证模块](specs/01-Auth-Test-Spec.md) - 登录/注册/登出
- [连接管理](specs/02-Connection-Test-Spec.md) - 数据库连接 CRUD
- [查询功能](specs/03-Query-Test-Spec.md) - NL2SQL 核心功能
- [历史记录](specs/04-History-Test-Spec.md) - 查询历史管理
- [评测功能](specs/05-Evaluation-Test-Spec.md) - SQL 评测任务
- [个人设置](specs/06-Settings-Test-Spec.md) - 用户设置
- [回归测试](specs/07-Regression-Test-Spec.md) - 回归测试套件

### 测试数据
- [测试数据定义](fixtures/test-data.ts) - TypeScript 测试数据
- [连接配置示例](fixtures/sample-connections.json) - 数据库连接配置

### 报告模板
- [测试报告模板](reports/templates/test-report-template.md)
- [Bug 报告模板](reports/templates/bug-report-template.md)

---

*文档版本: v1.0*
*更新日期: 2026-03-13*
