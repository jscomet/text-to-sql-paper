# Agent Team 启动指南

## 1. 启动前准备

### 1.1 确认文档完整

在启动 Agent Team 之前，请确认以下文档已准备就绪：

- [x] `../README.md` - 功能索引
- [x] `../PRD.md` - 产品需求
- [x] `../Business-Logic.md` - 业务逻辑
- [x] `../Technical-Design.md` - 技术设计
- [x] `../API-Documentation.md` - API 文档
- [x] `./Implementation-Plan.md` - 实施计划（本文档的父文档）

### 1.2 确认开发环境

```bash
# 后端环境检查
cd D:/Working/paper/project/text-to-sql-prototype/backend
python --version  # 3.11+
pip list | grep -E "fastapi|sqlalchemy|celery"

# 前端环境检查
cd D:/Working/paper/project/text-to-sql-prototype/frontend
node --version  # 18+
npm list | grep -E "vue|element-plus"

# 数据库检查
# - SQLite (开发环境)
# - 确认 alembic 可正常使用
```

---

## 2. Agent Team 启动步骤

### Step 1: 创建团队

```bash
# 使用 TeamCreate 创建团队
teambuilder create --name="advanced-inference-impl" \
                   --description="高级推理功能实现团队" \
                   --lead="team-lead"
```

### Step 2: 创建任务列表

按照 `Implementation-Plan.md` 中的任务分解，创建所有任务：

**Phase 1 任务（示例）:**

```json
[
  {
    "id": "1.1.1",
    "subject": "EvalTask 新增字段",
    "description": "在 EvalTask 模型中添加 max_iterations, sampling_count, correction_strategy 字段",
    "assignee": "backend-model",
    "priority": "P0",
    "estimated_hours": 4
  },
  {
    "id": "1.1.2",
    "subject": "EvalResult 新增字段",
    "description": "在 EvalResult 模型中添加 iteration_count, correction_history, candidate_sqls, confidence_score 字段",
    "assignee": "backend-model",
    "priority": "P0",
    "estimated_hours": 4
  }
  // ... 更多任务
]
```

### Step 3: 启动 Agents

按照以下顺序启动 Agents：

```
启动顺序:
1. team-lead (首先启动，负责协调)
2. backend-model, backend-api (Phase 1 可同时启动)
3. backend-service (等待 Phase 1 完成)
4. backend-task (等待 Phase 2 完成)
5. frontend-ui (可与 Phase 2-4 并行)
6. test-unit, test-e2e (等待 Phase 4 完成)
7. review (贯穿全程)
```

---

## 3. Agent 启动配置

### 3.1 team-lead

```yaml
name: team-lead
description: 高级推理功能实现团队负责人
team: advanced-inference-impl
responsibilities:
  - 任务分配和调度
  - 进度跟踪和同步
  - 质量保证检查
  - 风险管理和升级
workflows:
  - 每日检查 TaskList，识别阻塞任务
  - 组织每日 Standup（通过 SendMessage）
  - 审查关键代码变更
  - 更新项目进度看板
```

### 3.2 backend-model

```yaml
name: backend-model
description: 后端数据模型开发者
team: advanced-inference-impl
skills:
  - SQLAlchemy ORM
  - Alembic 迁移
  - PostgreSQL/SQLite
assigned_tasks:
  - Task 1.1.x (数据库模型扩展)
deliverables:
  - backend/app/models/eval_task.py (修改)
  - backend/app/models/eval_result.py (修改)
  - alembic/versions/xxx_advanced_inference.py (新建)
```

### 3.3 backend-service

```yaml
name: backend-service
description: 后端核心服务开发者
team: advanced-inference-impl
skills:
  - Python 异步编程
  - LLM 调用和 Prompt 工程
  - SQL 执行和验证
assigned_tasks:
  - Task 2.1.x (SQLChecker)
  - Task 2.2.x (SQLCorrector)
  - Task 2.3.x (PassAtKEvaluator)
  - Task 2.4.x (nl2sql 扩展)
deliverables:
  - backend/app/services/sql_checker.py (新建)
  - backend/app/services/sql_corrector.py (新建)
  - backend/app/services/pass_at_k.py (新建)
  - backend/app/services/nl2sql.py (修改)
```

### 3.4 backend-api

```yaml
name: backend-api
description: 后端 API 接口开发者
team: advanced-inference-impl
skills:
  - FastAPI
  - Pydantic Schema
  - RESTful API 设计
assigned_tasks:
  - Task 1.2.x (Schema 定义)
  - Task 3.x (API 实现)
deliverables:
  - backend/app/schemas/query.py (修改)
  - backend/app/schemas/evaluation.py (修改)
  - backend/app/api/v1/queries.py (修改)
  - backend/app/api/v1/evaluations.py (修改)
```

### 3.5 backend-task

```yaml
name: backend-task
description: 后端后台任务开发者
team: advanced-inference-impl
skills:
  - Celery 异步任务
  - WebSocket 实时通信
  - 任务调度管理
assigned_tasks:
  - Task 4.x (后台任务实现)
deliverables:
  - backend/app/tasks/eval_tasks.py (修改)
  - backend/app/tasks/eval_runner.py (新建，如需)
```

### 3.6 frontend-ui

```yaml
name: frontend-ui
description: 前端界面开发者
team: advanced-inference-impl
skills:
  - Vue 3 + TypeScript
  - Element Plus
  - Axios
assigned_tasks:
  - Task 5.x (前端实现)
deliverables:
  - frontend/src/components/inference/ (新建目录)
  - frontend/src/views/evaluation/ (修改)
  - frontend/src/api/query.ts (修改)
```

### 3.7 test-unit

```yaml
name: test-unit
description: 单元测试工程师
team: advanced-inference-impl
skills:
  - pytest
  - Mock/Patch
  - 测试覆盖率分析
assigned_tasks:
  - Task 6.1.x (单元测试)
deliverables:
  - backend/tests/unit/test_sql_checker.py (新建)
  - backend/tests/unit/test_sql_corrector.py (新建)
  - backend/tests/unit/test_pass_at_k.py (新建)
```

### 3.8 test-e2e

```yaml
name: test-e2e
description: E2E 测试工程师
team: advanced-inference-impl
skills:
  - Playwright
  - MCP Playwright Tools
  - 测试用例设计
assigned_tasks:
  - Task 6.2.x (E2E 测试)
  - Task 6.3.x (性能测试)
deliverables:
  - e2e/specs/08-Advanced-Inference-Test-Spec.md (新建)
  - e2e/reports/TC-ADV-xxx.md (测试报告)
```

### 3.9 review

```yaml
name: review
description: 代码审查员
team: advanced-inference-impl
skills:
  - 代码规范审查
  - 架构一致性检查
  - 安全审查
responsibilities:
  - 审查所有代码变更
  - 确保与 Technical-Design.md 一致
  - 确保代码质量和规范
workflow:
  - 收到审查请求后 4h 内响应
  - 使用 SendMessage 提供反馈
  - 标记阻塞问题并升级给 team-lead
```

---

## 4. 启动命令示例

### 4.1 完整启动脚本

```bash
#!/bin/bash
# Agent Team 启动脚本

TEAM_NAME="advanced-inference-impl"

echo "Step 1: 创建团队..."
teambuilder create --name="$TEAM_NAME" --description="高级推理功能实现" --lead="team-lead"

echo "Step 2: 创建任务..."
# Phase 1
TaskCreate --subject="EvalTask 新增字段" --assignee="backend-model" --priority="P0"
TaskCreate --subject="EvalResult 新增字段" --assignee="backend-model" --priority="P0"
TaskCreate --subject="Alembic 迁移脚本" --assignee="backend-model" --priority="P0"
TaskCreate --subject="QueryGenerateAdvanced Schema" --assignee="backend-api" --priority="P0"
# ... 更多任务

echo "Step 3: 启动 Agents..."
# Phase 1 Agents
Agent --name="team-lead" --team="$TEAM_NAME" --prompt="你是 team-lead，负责协调..."
Agent --name="backend-model" --team="$TEAM_NAME" --prompt="你是 backend-model，负责数据库模型..."
Agent --name="backend-api" --team="$TEAM_NAME" --prompt="你是 backend-api，负责 Schema 定义..."

# 等待 Phase 1 完成后启动 Phase 2
# Agent --name="backend-service" --team="$TEAM_NAME" --prompt="..."
# ...

echo "Agent Team 启动完成!"
```

### 4.2 手动启动示例

```bash
# 1. 创建团队
cd D:/Working/paper/project/text-to-sql-prototype

# 2. 启动 team-lead（首先启动）
claude agent --name="team-lead" \
  --prompt="参考 feat/advanced-inference/plan/Implementation-Plan.md 中的团队负责人职责..."

# 3. 启动 Phase 1 Agents（并行）
claude agent --name="backend-model" \
  --prompt="你的任务是实现数据库模型扩展，参考 ../Technical-Design.md 第2节..."

claude agent --name="backend-api" \
  --prompt="你的任务是定义 API Schema，参考 ../API-Documentation.md..."
```

---

## 5. 协作流程

### 5.1 每日工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        每日工作流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  09:00  ┌─────────────┐                                        │
│         │   Standup   │  team-lead 检查所有任务状态             │
│         │  (Team Lead)│  识别阻塞问题，分配资源                 │
│         └──────┬──────┘                                        │
│                │                                                │
│  09:30  ┌──────▼──────┐                                        │
│         │  任务执行   │  各 Agent 执行任务                      │
│         │  (Agents)   │                                        │
│         └──────┬──────┘                                        │
│                │                                                │
│  12:00  ┌──────▼──────┐                                        │
│         │  午餐同步   │  简单进度同步（如有阻塞）               │
│         │  (Optional) │                                        │
│         └──────┬──────┘                                        │
│                │                                                │
│  14:00  ┌──────▼──────┐                                        │
│         │  代码审查   │  review Agent 审查提交的代码            │
│         │  (Review)   │                                        │
│         └──────┬──────┘                                        │
│                │                                                │
│  17:00  ┌──────▼──────┐                                        │
│         │  日终总结   │  各 Agent 更新任务状态                  │
│         │  (Summary)  │  team-lead 更新进度看板                │
│         └─────────────┘                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 任务完成流程

```
Agent 完成任务:
    │
    ▼
┌─────────────────┐
│ 1. 自测通过     │  - 单元测试通过
│ 2. 代码提交     │  - git commit (遵循规范)
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ SendMessage to  │  - 通知 review Agent
│ review          │  - 通知下游依赖 Agent
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ review 审查     │  - 代码质量检查
│ (4h 内响应)     │  - 架构一致性检查
└───────┬─────────┘
        │
    ┌───┴───┐
    ▼       ▼
┌───────┐ ┌───────┐
│通过   │ │未通过 │
└───┬───┘ └───┬───┘
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│标记完成 │ │返回修改 │
│通知 TL  │ │(循环)   │
└─────────┘ └─────────┘
```

---

## 6. 监控和报告

### 6.1 进度跟踪

team-lead 需要维护以下看板：

```markdown
## 项目进度看板

### Phase 1: 基础设施 (Week 1)
| 任务 | 负责人 | 状态 | 进度 | 阻塞 |
|------|--------|------|------|------|
| 1.1.1 EvalTask 字段 | backend-model | 🟡 进行中 | 80% | - |
| 1.1.2 EvalResult 字段 | backend-model | 🟢 已完成 | 100% | - |
| 1.2.1 Schema 定义 | backend-api | 🟡 进行中 | 60% | - |

### Phase 2: 核心服务 (Week 2)
| 任务 | 负责人 | 状态 | 进度 | 阻塞 |
|------|--------|------|------|------|
| ... | ... | ⚪ 未开始 | 0% | 等待 Phase 1 |

状态说明:
- 🟢 已完成
- 🟡 进行中
- 🔴 阻塞
- ⚪ 未开始
```

### 6.2 风险升级

当 Agent 遇到以下情况时，立即升级给 team-lead：

1. **技术阻塞**: 无法实现设计文档中的功能
2. **依赖延迟**: 上游任务延期超过 1 天
3. **架构冲突**: 实现与 Technical-Design.md 有冲突
4. **性能问题**: 实测性能与目标差距超过 50%

升级方式：
```python
SendMessage(
    type="message",
    recipient="team-lead",
    content="[阻塞升级] Task X.X 遇到 XXX 问题，需要协助决策...",
    summary="Task X.X 阻塞升级"
)
```

---

## 7. 附录

### 7.1 常用命令速查

```bash
# 查看任务列表
TaskList

# 查看特定任务
TaskGet --taskId="1.1.1"

# 更新任务状态
TaskUpdate --taskId="1.1.1" --status="completed"

# 发送消息
SendMessage --type="message" --recipient="backend-service" --content="..."

# 广播消息
SendMessage --type="broadcast" --content="..."
```

### 7.2 参考文档路径

| 文档 | 路径 |
|------|------|
| 实施计划 | `./Implementation-Plan.md` |
| 需求文档 | `../PRD.md` |
| 技术设计 | `../Technical-Design.md` |
| API 文档 | `../API-Documentation.md` |
| 业务逻辑 | `../Business-Logic.md` |

### 7.3 联系信息

- **项目负责人**: team-lead
- **技术负责人**: backend-service
- **测试负责人**: test-e2e

---

*文档版本: v1.0*
*创建日期: 2026-03-13*
