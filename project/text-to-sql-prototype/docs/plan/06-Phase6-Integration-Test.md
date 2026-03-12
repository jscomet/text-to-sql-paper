# 阶段6：集成测试与优化

## 阶段目标

进行全面测试，包括后端单元测试、API测试、前端单元测试、E2E测试，修复Bug并优化性能，确保项目质量达到生产环境标准。

**预计工期**: 1.5天
**并行度**: **高**（前后端测试完全并行，独立执行）

---

## Agent 协作架构

### 执行模式

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Leader (You)                                   │
│                     任务分配 → 验收 → 阶段推进                            │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ backend-dev   │ │ frontend-dev  │ │    tester     │
│  (后端测试)    │ │  (前端测试)    │ │   (E2E测试)    │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ Task 6.1      │ │ Task 6.4      │ │ Task 6.6      │
│ Task 6.2      │ │ Task 6.5      │ │ Task 6.7      │
│ Task 6.3      │ │               │ │ (Bug验证)      │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │   测试-反馈-修复循环  │
              │  (tester主导的质量门) │
              └─────────────────────┘
```

### 角色职责

| 角色 | 核心职责 | 本阶段任务 |
|------|----------|-----------|
| **backend-dev** | 后端测试开发 | 编写后端单元测试、API测试，确保后端代码质量 |
| **frontend-dev** | 前端测试开发 | 编写前端组件测试、Store测试，确保前端代码质量 |
| **tester** | E2E测试 + 质量门禁 | 执行E2E测试，发现Bug并创建报告，验证修复，控制阶段出口 |

### 任务依赖与并行策略

```
并行执行组A (backend-dev)          并行执行组B (frontend-dev)
┌─────────────────────────┐        ┌─────────────────────────┐
│ Task 6.1 测试基础设施    │        │ Task 6.4 测试基础设施    │
│    ↓                    │        │    ↓                    │
│ Task 6.2 服务层测试      │        │ Task 6.5 组件/Store测试  │
│    ↓                    │        └─────────────────────────┘
│ Task 6.3 API测试         │
└─────────────────────────┘              ↓
         ↓                        两组都完成后
         ↓                    ┌─────────────────┐
    后端测试完成 ───────────→│  Task 6.6 E2E   │
                             │  (tester执行)   │
                             └────────┬────────┘
                                      ↓
                             ┌─────────────────┐
                             │ Task 6.7 Bug修复 │
                             │ (tester主导循环) │
                             └─────────────────┘
```

**关键规则**:
1. **组内串行**: 每个 Agent 内部任务有依赖，按顺序执行
2. **组间并行**: 前后端测试完全独立，可同时启动
3. **E2E后置**: tester 需等待前后端测试完成后启动
4. **质量门禁**: 只有 tester 可以批准阶段完成

---

## 任务分解（Agent 执行版）

---

### Task 6.1: 后端测试基础设施

**执行者**: `backend-dev`
**依赖**: Phase 2-3 已完成
**预估耗时**: 2-3小时

#### 任务目标
搭建完整的后端测试基础设施，为后续测试提供基础环境。

#### 输入
- 后端代码: `backend/app/` 目录
- 数据库模型: `backend/app/models/`
- API 路由: `backend/app/api/`

#### 输出
- `backend/tests/conftest.py` - pytest 配置和 fixtures
- `backend/pytest.ini` - pytest 配置文件
- `backend/.coveragerc` - 覆盖率配置
- 测试数据库可正常运行

#### 验收标准
- [ ] `pytest --version` 可正常执行
- [ ] `pytest backend/tests -v` 能运行（无测试也OK，不报错）
- [ ] fixtures 包含: `client`, `db_session`, `auth_headers`, `test_user`
- [ ] 测试数据库使用 SQLite in-memory

#### 执行步骤
1. 检查现有测试目录结构
2. 创建/更新 `conftest.py` 配置核心 fixtures
3. 创建 `pytest.ini` 配置文件
4. 验证测试环境可运行

#### Agent 指令模板
```
作为 backend-dev，完成任务：后端测试基础设施搭建

目标：配置 pytest 测试环境，创建基础 fixtures

需要创建的文件：
1. backend/tests/conftest.py - 包含以下 fixtures:
   - client: FastAPI TestClient
   - db_session: 数据库会话
   - test_user: 测试用户数据
   - auth_headers: 认证请求头

2. backend/pytest.ini - pytest 配置

3. backend/.coveragerc - 覆盖率配置（排除不需要统计的文件）

完成后验证：
- cd backend && pytest -v 能正常执行
- fixtures 能被正确加载

输出：报告创建的文件列表和验证结果
```

---

### Task 6.2: 后端服务层单元测试

**执行者**: `backend-dev`
**依赖**: Task 6.1 完成
**预估耗时**: 4-6小时

#### 任务目标
测试核心业务逻辑层，确保服务功能正确。

#### 输入
- 服务层代码: `backend/app/services/`
- 模型层代码: `backend/app/models/`
- Task 6.1 的测试基础设施

#### 输出
- `backend/tests/services/test_security.py` - 安全服务测试
- `backend/tests/services/test_nl2sql.py` - SQL生成测试（Mock LLM）
- `backend/tests/services/test_sql_executor.py` - SQL执行测试
- `backend/tests/services/test_evaluator.py` - 评测服务测试
- `backend/tests/unit/test_models.py` - 模型层测试

#### 验收标准
- [ ] 所有服务层测试文件创建完成
- [ ] 测试覆盖率 > 70%
- [ ] 所有测试通过: `pytest backend/tests/services -v`
- [ ] Mock 外部依赖（LLM、数据库连接）

#### 测试重点

| 服务 | 测试内容 |
|------|----------|
| security | 密码哈希、JWT编码解码、token验证 |
| nl2sql | SQL生成逻辑（Mock LLM响应）、参数处理 |
| sql_executor | SQL执行、结果格式化、错误处理 |
| evaluator | EX准确率计算、结果对比逻辑 |
| models | CRUD操作、关系映射、约束验证 |

#### Agent 指令模板
```
作为 backend-dev，完成任务：后端服务层单元测试

目标：为核心业务服务编写单元测试

依赖：Task 6.1 已完成（测试基础设施就绪）

需要测试的模块（位于 backend/app/services/）：
1. security.py - 认证相关功能
2. nl2sql.py - SQL生成（需要Mock LLM调用）
3. sql_executor.py - SQL执行器
4. evaluator.py - 评测计算

需要创建的测试文件：
- backend/tests/services/test_security.py
- backend/tests/services/test_nl2sql.py
- backend/tests/services/test_sql_executor.py
- backend/tests/services/test_evaluator.py
- backend/tests/unit/test_models.py

要求：
- 使用 pytest 语法
- Mock 外部调用（LLM API、真实数据库连接）
- 测试正常路径和异常路径
- 每个测试函数有明确的名字和docstring

验证命令：
cd backend && pytest tests/services tests/unit -v --cov=app/services --cov=app/models

输出：测试覆盖率报告和通过情况
```

---

### Task 6.3: 后端 API 集成测试

**执行者**: `backend-dev`
**依赖**: Task 6.2 完成
**预估耗时**: 4-5小时

#### 任务目标
测试 API 端点的完整流程，确保接口行为符合文档。

#### 输入
- API 路由: `backend/app/api/`
- API 文档: `docs/05-API-Documentation.md`
- Task 6.2 的服务层测试

#### 输出
- `backend/tests/integration/test_auth_api.py` - 认证API测试
- `backend/tests/integration/test_connection_api.py` - 连接管理API测试
- `backend/tests/integration/test_query_api.py` - 查询API测试
- `backend/tests/integration/test_evaluation_api.py` - 评测API测试
- `backend/tests/integration/test_flows.py` - 完整流程测试

#### 验收标准
- [ ] 所有 API 测试文件创建完成
- [ ] 完整流程测试覆盖：注册→登录→创建连接→查询→执行
- [ ] 边界情况测试：空参数、越权访问、无效token
- [ ] 所有测试通过: `pytest backend/tests/integration -v`

#### API 测试覆盖表

| 模块 | 端点 | 测试场景 |
|------|------|----------|
| auth | POST /auth/register | 正常注册、重复用户、弱密码 |
| auth | POST /auth/login | 正常登录、错误密码、token刷新 |
| auth | POST /auth/refresh | token刷新、过期token |
| connections | CRUD | 创建、查询、更新、删除、权限验证 |
| queries | POST /queries | 生成SQL、执行SQL、历史记录 |
| evaluations | CRUD | 创建任务、执行、进度查询、结果 |

#### Agent 指令模板
```
作为 backend-dev，完成任务：后端 API 集成测试

目标：测试所有 API 端点的完整行为

依赖：Task 6.2 已完成（服务层测试通过）

API 端点参考：docs/05-API-Documentation.md

需要创建的测试文件：
- backend/tests/integration/test_auth_api.py
- backend/tests/integration/test_connection_api.py
- backend/tests/integration/test_query_api.py
- backend/tests/integration/test_evaluation_api.py
- backend/tests/integration/test_flows.py (完整流程)

测试要求：
1. 每个端点测试以下场景：
   - 正常请求（200）
   - 无效参数（422）
   - 未认证（401）
   - 无权限（403）
   - 资源不存在（404）

2. test_flows.py 包含完整用户流程：
   - 注册 → 登录 → 获取token
   - 创建数据库连接
   - 执行查询（Mock SQL生成）
   - 查看历史记录
   - 创建评测任务

3. 使用测试数据库，不依赖外部服务

验证命令：
cd backend && pytest tests/integration -v --cov=app/api

输出：API测试通过情况和覆盖率
```

---

### Task 6.4: 前端测试基础设施

**执行者**: `frontend-dev`
**依赖**: Phase 4-5 已完成
**预估耗时**: 1-2小时

#### 任务目标
配置前端单元测试环境，为组件和Store测试做准备。

#### 输入
- 前端代码: `frontend/src/`
- 构建配置: `frontend/vite.config.ts`
- 现有依赖: `frontend/package.json`

#### 输出
- `frontend/vitest.config.ts` - Vitest 配置文件
- `frontend/src/test/setup.ts` - 测试初始化文件
- `frontend/src/test/utils.ts` - 测试工具函数
- 测试命令可正常运行

#### 验收标准
- [ ] `npm run test:unit` 命令可执行
- [ ] 测试环境配置完成（jsdom, pinia mock, router mock）
- [ ] 能渲染基础组件不报错
- [ ] 代码覆盖率配置正确

#### Agent 指令模板
```
作为 frontend-dev，完成任务：前端测试基础设施配置

目标：配置 vitest 测试环境

检查 package.json 是否已有：
- vitest
- @vue/test-utils
- jsdom
- @pinia/testing

需要创建的文件：
1. frontend/vitest.config.ts
   - 使用 jsdom 环境
   - 配置路径别名（@ -> src）
   - 配置 coverage

2. frontend/src/test/setup.ts
   - 全局测试初始化
   - Mock 全局对象

3. frontend/src/test/utils.ts
   - 封装 mount 函数（自动配置 pinia、router）
   - 测试辅助函数

验证命令：
cd frontend && npm run test:unit

输出：测试环境配置结果和验证情况
```

---

### Task 6.5: 前端组件与 Store 测试

**执行者**: `frontend-dev`
**依赖**: Task 6.4 完成
**预估耗时**: 5-7小时

#### 任务目标
测试前端组件和状态管理，确保UI行为正确。

#### 输入
- 组件代码: `frontend/src/components/`
- Store代码: `frontend/src/stores/`
- 工具函数: `frontend/src/utils/`

#### 输出
- `frontend/src/components/common/*.spec.ts` - 通用组件测试
- `frontend/src/components/business/*.spec.ts` - 业务组件测试
- `frontend/src/stores/*.spec.ts` - Store测试
- `frontend/src/utils/*.spec.ts` - 工具函数测试

#### 验收标准
- [ ] 所有关键组件有测试文件
- [ ] 所有 Store 有测试文件
- [ ] 工具函数测试覆盖
- [ ] 测试覆盖率 > 60%
- [ ] 所有测试通过: `npm run test:unit`

#### 测试覆盖表

| 类型 | 文件 | 测试内容 |
|------|------|----------|
| 通用组件 | DataTable.spec.ts | 渲染、分页、排序、事件 |
| 通用组件 | LoadingOverlay.spec.ts | 显示/隐藏状态 |
| 通用组件 | ErrorAlert.spec.ts | 错误信息展示 |
| 通用组件 | EmptyState.spec.ts | 空状态渲染 |
| 业务组件 | SqlEditor.spec.ts | SQL编辑、格式化 |
| 业务组件 | QueryResult.spec.ts | 结果展示、导出 |
| 业务组件 | SchemaTree.spec.ts | 树形渲染、展开 |
| Store | user.spec.ts | 登录状态、用户信息 |
| Store | query.spec.ts | 查询状态、历史记录 |
| 工具 | date.spec.ts | 日期格式化 |
| 工具 | sql.spec.ts | SQL格式化、验证 |

#### Agent 指令模板
```
作为 frontend-dev，完成任务：前端组件与 Store 测试

目标：为关键组件和 Store 编写单元测试

依赖：Task 6.4 已完成（测试环境就绪）

需要创建的测试文件：

通用组件 (frontend/src/components/common/)：
- DataTable.spec.ts - 表格组件
- LoadingOverlay.spec.ts - 加载遮罩
- ErrorAlert.spec.ts - 错误提示
- EmptyState.spec.ts - 空状态

业务组件 (frontend/src/components/business/)：
- SqlEditor.spec.ts - SQL编辑器
- QueryResult.spec.ts - 查询结果
- SchemaTree.spec.ts - Schema树

Store (frontend/src/stores/)：
- user.spec.ts - 用户状态
- query.spec.ts - 查询状态

工具函数 (frontend/src/utils/)：
- date.spec.ts - 日期处理
- sql.spec.ts - SQL处理

测试要求：
1. 组件测试：
   - 正确渲染
   - props 传递
   - 事件触发
   - slots 内容

2. Store测试：
   - state 修改
   - actions 执行
   - getters 计算

3. 工具函数：
   - 正常输入输出
   - 边界情况
   - 错误处理

验证命令：
cd frontend && npm run test:unit -- --coverage

输出：组件测试覆盖率和通过情况
```

---

### Task 6.6: E2E 端到端测试

**执行者**: `tester`
**依赖**: Task 6.3 和 Task 6.5 完成
**预估耗时**: 4-6小时

#### 任务目标
使用 MCP Playwright 工具执行端到端测试，验证完整用户流程，发现集成问题。

#### 输入
- 前端页面: `frontend/src/views/`
- 后端 API: `backend/app/api/`
- 现有 E2E 文件: `frontend/e2e/`

#### 输出
- `frontend/e2e/evaluation.spec.ts` - 评测流程测试（新增）
- E2E 测试执行报告
- `docs/report/06-Phase6-Test/e2e-report.md` - E2E测试报告
- Bug 报告（如发现问题）

#### 验收标准
- [ ] 所有核心用户流程有测试用例
- [ ] 使用 MCP Playwright 工具执行测试
- [ ] 测试能发现实际问题（如有）
- [ ] Bug 报告（如有）已创建

#### E2E 测试场景

| 场景 | 步骤 |
|------|------|
| 用户登录 | 访问首页 → 输入凭证 → 登录 → 验证跳转 |
| 创建连接 | 进入连接页 → 填写表单 → 保存 → 验证列表 |
| 执行查询 | 选择连接 → 输入问题 → 生成SQL → 执行 → 查看结果 |
| 评测流程 | 创建评测 → 上传数据 → 执行 → 查看报告 |
| 历史记录 | 查看历史 → 收藏 → 再次执行 |

#### MCP Playwright 执行方式

本阶段使用 **MCP Playwright 工具** 执行 E2E 测试，而不是本地安装的 Playwright。

**优势**:
- 无需安装浏览器依赖
- 使用系统级 Playwright 能力
- 更好的集成和报告

**执行方式对比**:

| 方式 | 命令 | 适用场景 |
|------|------|----------|
| MCP 工具 | `mcp__playwright__browser_*` | 本阶段主要使用方式 |
| 本地 Playwright | `npm run test:e2e` | 保留作为备选 |

#### Agent 指令模板
```
作为 tester，完成任务：E2E 端到端测试

目标：使用 MCP Playwright 工具验证完整用户流程

依赖：
- Task 6.3 完成（后端 API 测试通过）
- Task 6.5 完成（前端单元测试通过）
- 前后端服务已启动

现有 E2E 文件在 frontend/e2e/：
- auth.spec.ts - 登录流程
- connection.spec.ts - 连接管理
- query.spec.ts - 查询流程
- fixtures.ts - 测试数据
- helpers.ts - 辅助函数

需要添加：
- evaluation.spec.ts - 评测流程

测试执行步骤：
1. 确保服务运行:
   - 后端: cd backend && uvicorn app.main:app --reload --port 8000
   - 前端: cd frontend && npm run dev

2. 使用 MCP Playwright 工具执行测试:
   - mcp__playwright__browser_navigate (访问页面)
   - mcp__playwright__browser_type (输入内容)
   - mcp__playwright__browser_click (点击元素)
   - mcp__playwright__browser_snapshot (获取页面状态)
   - mcp__playwright__browser_take_screenshot (截图记录)

3. 按照测试场景执行：
   - 场景1: 用户登录流程
   - 场景2: 创建数据库连接
   - 场景3: 执行 NL2SQL 查询
   - 场景4: 评测任务流程

4. 发现问题时：
   - 立即截图保存
   - 记录复现步骤
   - 创建 Bug 报告

Bug 处理流程：
- 发现问题 → 截图 → 创建 Bug 报告
- 报告位置: docs/report/06-Phase6-Test/bugs/BUG-XXX.md
- 分配给对应开发人员

输出：
1. E2E 测试报告 (docs/report/06-Phase6-Test/e2e-report.md)
   - 测试场景覆盖情况
   - 执行结果（通过/失败）
   - 截图记录
2. Bug 报告列表（如有）
3. 测试覆盖率统计
```

#### 手动 E2E 测试清单（MCP 工具执行）

| # | 测试项 | 操作步骤 | 预期结果 | 实际结果 | 状态 |
|---|--------|----------|----------|----------|------|
| 1 | 登录页面 | 访问 /login | 显示登录表单 | | |
| 2 | 登录成功 | 输入正确凭证 | 跳转到 dashboard | | |
| 3 | 登录失败 | 输入错误密码 | 显示错误提示 | | |
| 4 | 注册页面 | 访问 /register | 显示注册表单 | | |
| 5 | 创建连接 | 填写连接信息并保存 | 连接出现在列表 | | |
| 6 | Schema 展示 | 选择连接 | 显示表结构 | | |
| 7 | SQL 生成 | 输入自然语言问题 | 生成 SQL | | |
| 8 | SQL 执行 | 点击执行按钮 | 显示结果 | | |
| 9 | 历史记录 | 查看历史页面 | 显示查询历史 | | |
| 10 | 个人设置 | 修改用户信息 | 保存成功 | | |

---

### Task 6.7: Bug 修复与回归测试

**执行者**: `tester` 主导 + `backend-dev`/`frontend-dev` 响应
**依赖**: Task 6.6 发现的 Bug
**预估耗时**: 视 Bug 数量而定（循环任务）

#### 任务目标
修复 E2E 测试中发现的 Bug，执行回归测试，确保质量。

#### 输入
- Bug 报告: `docs/report/06-Phase6-Test/bugs/`
- 前后端代码

#### 输出
- 修复的代码
- 回归测试报告
- 更新的检查点状态

#### Bug 处理流程

```
发现Bug (tester)
    ↓
创建Bug报告 (tester)
    ↓
分配给开发人员 (tester)
    ↓
修复实现 (backend-dev / frontend-dev)
    ↓
本地验证 (开发人员)
    ↓
通知 tester 回归测试
    ↓
执行回归测试 (tester)
    ↓
  ├─ 通过 → 关闭Bug
  └─ 失败 → 重新打开，继续修复
```

#### 优先级定义

| 级别 | 定义 | 响应时间 |
|------|------|----------|
| P0 | 阻塞流程，核心功能不可用 | 立即修复 |
| P1 | 功能缺陷，有 workaround | 24小时内 |
| P2 | 体验问题，非阻塞 | 可选修复 |

#### Agent 指令模板（tester 用）
```
作为 tester，完成任务：Bug 管理与回归测试

目标：管理 Bug 生命周期，执行回归测试

当前 Bug 列表（位于 docs/report/06-Phase6-Test/bugs/）：
[列出所有待修复和待验证的 Bug]

任务清单：
1. 检查新提交的 Bug 报告，确认信息完整
2. 按优先级排序，分配给对应开发人员
3. 跟踪修复进度
4. 修复完成后执行回归测试：
   - 验证原 Bug 不再复现
   - 执行相关模块的测试用例
   - 确认未引入新 Bug
5. 更新 Bug 状态（verified / reopened）

回归测试范围：
- P0 Bug: 全量测试 + 专项测试
- P1 Bug: 相关模块 + 专项测试
- P2 Bug: 专项测试

输出：
1. Bug 状态更新报告
2. 回归测试结果
3. 质量门禁决策（是否进入下一阶段）
```

#### Agent 指令模板（backend-dev/frontend-dev 用）
```
作为 [backend-dev/frontend-dev]，完成任务：Bug 修复

目标：修复 tester 指派的 Bug

被指派的 Bug：
- ID: [BUG-XXX]
- 标题: [标题]
- 优先级: [P0/P1/P2]
- 问题描述: [描述]

修复步骤：
1. 阅读 Bug 报告，理解问题
2. 本地复现问题
3. 定位根本原因
4. 实现修复
5. 本地验证修复有效
6. 运行相关测试确保通过
7. 更新 Bug 报告添加修复说明
8. 通知 tester 进行回归测试

修复说明格式：
## 修复说明
- 修复者: [你的名字]
- 修复时间: [日期]
- 修复提交: [commit hash]

### 原因分析
[根本原因]

### 修复内容
[修改的文件和代码]

### 本地验证
- [x] 复现步骤测试通过
- [x] 单元测试通过
- [x] 集成测试通过

@tester 请进行回归测试

输出：修复完成的代码和 Bug 报告更新
```

---

## 阶段检查清单

### 后端测试检查点（backend-dev 负责）

- [ ] **Task 6.1** 测试基础设施
  - [ ] pytest 配置正确
  - [ ] fixtures 完整可用

- [ ] **Task 6.2** 服务层测试
  - [ ] 所有服务有测试
  - [ ] 覆盖率 > 70%
  - [ ] 测试全部通过

- [ ] **Task 6.3** API 测试
  - [ ] 所有端点有测试
  - [ ] 流程测试完整
  - [ ] 边界情况覆盖

### 前端测试检查点（frontend-dev 负责）

- [ ] **Task 6.4** 测试基础设施
  - [ ] vitest 配置正确
  - [ ] 测试环境可用

- [ ] **Task 6.5** 组件/Store 测试
  - [ ] 关键组件有测试
  - [ ] 所有 Store 有测试
  - [ ] 覆盖率 > 60%
  - [ ] 测试全部通过

### E2E 与质量门禁（tester 负责）

- [ ] **Task 6.6** E2E 测试
  - [ ] MCP Playwright 工具可用
  - [ ] 核心流程测试覆盖
  - [ ] 手动测试清单完成

- [ ] **Task 6.7** Bug 修复
  - [ ] 无 P0 Bug
  - [ ] P1 Bug < 5 个
  - [ ] 所有修复已验证

### 性能检查点

- [ ] 页面加载 < 2s
- [ ] SQL 生成 < 5s
- [ ] 查询执行 < 3s
- [ ] 内存使用正常

---

## Agent 启动命令参考

### 启动 backend-dev（串行执行 6.1 → 6.2 → 6.3）
```
Agent: backend-dev
Tasks: 6.1, 6.2, 6.3（按顺序）
说明：完成后端所有测试开发
```

### 启动 frontend-dev（串行执行 6.4 → 6.5）
```
Agent: frontend-dev
Tasks: 6.4, 6.5（按顺序）
说明：完成前端所有测试开发
```

### 启动 tester（后置执行 6.6 → 6.7）
```
Agent: tester
Tasks: 6.6, 6.7
说明：前后端测试完成后启动，执行E2E并管理Bug修复循环
前置条件：backend-dev 和 frontend-dev 已完成
```

---

## 阶段交付物

| 交付物 | 位置 | 验收标准 | 负责 Agent |
|--------|------|----------|-----------|
| 后端测试代码 | `backend/tests/` | 覆盖率>70%，全部通过 | backend-dev |
| 前端测试代码 | `frontend/src/**/*.spec.ts` | 覆盖率>60%，全部通过 | frontend-dev |
| E2E 测试 | MCP Playwright 执行 | 核心流程覆盖 | tester |
| E2E 测试报告 | `docs/report/06-Phase6-Test/e2e-report.md` | 详细记录 | tester |
| Bug 报告 | `docs/report/06-Phase6-Test/bugs/` | 完整跟踪 | tester |
| Bug 修复记录 | Bug 报告中的修复说明 | 所有P0修复 | 全部 |
| 测试覆盖率报告 | `htmlcov/` + 前端 coverage | 达标 | 全部 |

---

## 进入下一阶段条件

1. ✅ backend-dev 完成 Task 6.1-6.3
2. ✅ frontend-dev 完成 Task 6.4-6.5
3. ✅ tester 完成 Task 6.6，E2E 测试通过
4. ✅ 无 P0 Bug（tester 确认）
5. ✅ 所有修复已通过回归测试（tester 确认）
6. ✅ 性能指标达标

---

## 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 测试编写耗时超预期 | 中 | 中 | 优先核心功能，逐步补充 |
| 发现大量 Bug | 中 | 高 | 按优先级修复，P0优先 |
| E2E测试不稳定 | 中 | 中 | MCP 工具提供稳定环境 |
| 测试覆盖率不达标 | 低 | 中 | 调整目标或补充测试 |
| 前后端测试进度不一致 | 中 | 低 | 独立并行，互不阻塞 |
| MCP Playwright 学习成本 | 低 | 低 | 使用直观的浏览器操作工具 |

## E2E 测试特别说明

### 为什么使用 MCP Playwright 而非本地 Playwright

1. **无需安装**: 不需要 `npm install @playwright/test` 和浏览器下载
2. **系统级集成**: MCP 工具与 Claude Code 深度集成
3. **实时交互**: 可以实时查看页面状态、截图、诊断问题
4. **灵活执行**: 结合 AI 判断，不只是固定脚本执行

### 保留的本地 Playwright 配置

前端 `package.json` 中保留 `test:e2e` 命令作为备选方案：
- 用于 CI/CD 环境自动化
- 用于回归测试批量执行
- 用于测试脚本版本控制

### MCP Playwright 工具使用示例

```
# 1. 导航到登录页
mcp__playwright__browser_navigate
url: http://localhost:5173/login

# 2. 输入用户名
mcp__playwright__browser_type
ref: [用户名输入框引用]
text: testuser

# 3. 输入密码
mcp__playwright__browser_type
ref: [密码输入框引用]
text: password123

# 4. 点击登录按钮
mcp__playwright__browser_click
ref: [登录按钮引用]

# 5. 验证跳转成功
mcp__playwright__browser_wait_for
text: 仪表板

# 6. 截图记录
mcp__playwright__browser_take_screenshot
filename: login-success.png
```

---

## 附录：Bug 报告模板

### 创建 Bug 报告（tester）

```markdown
# Bug Report: BUG-XXX

| 字段 | 值 |
|------|-----|
| ID | BUG-XXX |
| 标题 | [简短描述] |
| 发现者 | tester |
| 优先级 | P0/P1/P2 |
| 模块 | [backend/frontend]/[子模块] |
| 发现时间 | [日期] |
| 关联测试 | [测试用例名] |

## 问题描述
[详细描述]

## 复现步骤
1. [步骤1]
2. [步骤2]

## 期望结果
[期望]

## 实际结果
[实际]

## 环境信息
- 分支: main
- 提交: [hash]

## 状态历史
- [日期]: 创建 (tester)
```

### 修复 Bug（开发人员）

在 Bug 报告末尾添加：

```markdown
## 修复说明
- 修复者: [名字]
- 修复时间: [日期]
- 修复提交: [hash]

### 原因分析
[分析]

### 修复内容
[修改]

### 本地验证
- [x] 复现步骤测试通过
- [x] 单元测试通过

@tester 请进行回归测试
```

### 验证关闭（tester）

```markdown
## 验证结果
- 验证者: tester
- 验证时间: [日期]

### 回归测试
- [x] 原复现步骤通过
- [x] 相关测试通过
- [x] 未引入新Bug

**状态: 已关闭**
```

---

*文档版本: v2.0 - Agent Team 优化版*
*更新: 2026-03-12*
