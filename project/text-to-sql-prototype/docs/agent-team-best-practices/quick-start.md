# Agent Team 快速启动指南

本文档帮助你在 10 分钟内启动一个 Agent Team。

---

## 前置条件

1. 项目规划文档已完成
2. 任务分解清单已准备
3. 开发环境已就绪

---

## 5 分钟快速启动

### Step 1: 创建团队 (1分钟)

```python
TeamCreate(
    team_name="your-project-name",
    description="项目描述"
)
```

### Step 2: 创建任务列表 (2分钟)

```python
# Phase 1 任务
TaskCreate(subject="数据库模型", description="...")
TaskCreate(subject="API Schema", description="...")

# Phase 2 任务
TaskCreate(subject="核心服务", description="...", addBlockedBy=["1"])
```

### Step 3: 启动核心 Agent (2分钟)

```python
# 1. 先启动 team-lead
Agent(
    name="team-lead",
    team_name="your-project-name",
    prompt="你是 team-lead，负责协调...",
    subagent_type="general-purpose"
)

# 2. 启动 Phase 1 Agent (并行)
Agent(
    name="backend-dev",
    team_name="your-project-name",
    prompt="负责后端开发...",
    subagent_type="general-purpose"
)

Agent(
    name="frontend-dev",
    team_name="your-project-name",
    prompt="负责前端开发...",
    subagent_type="general-purpose"
)
```

---

## 任务依赖设置示例

```python
# 任务 A (无依赖)
task_a = TaskCreate(subject="任务A")

# 任务 B (依赖任务A)
task_b = TaskCreate(
    subject="任务B",
    addBlockedBy=[task_a]  # 使用任务ID
)

# 任务 C (依赖多个任务)
task_c = TaskCreate(
    subject="任务C",
    addBlockedBy=[task_a, task_b]
)
```

---

## 常见错误避免

### ❌ 错误: 忘记设置任务依赖

**后果**: Agent 尝试执行未准备好的任务

**正确做法**:
```python
TaskCreate(
    subject="API实现",
    addBlockedBy=["schema-task-id"]  # 明确依赖
)
```

### ❌ 错误: Agent 不加入团队

**后果**: Agent 无法看到团队任务列表

**正确做法**:
```python
Agent(
    name="agent-name",
    team_name="your-team",  # 必须指定
    # ...
)
```

### ❌ 错误: 任务描述不清晰

**后果**: Agent 理解偏差，产出不符合预期

**正确做法**:
```python
TaskCreate(
    subject="实现用户登录API",
    description="""
## 需求
实现用户登录接口

## 接口定义
POST /api/v1/auth/login

## 验收标准
- [ ] 验证用户名密码
- [ ] 返回 JWT token
- [ ] 错误处理

## 参考
- 设计文档: docs/design.md
"""
)
```

---

## 监控命令

```python
# 查看所有任务
TaskList()

# 查看特定任务
TaskGet(taskId="任务ID")

# 更新任务状态
TaskUpdate(taskId="任务ID", status="completed")

# 发送消息给 Agent
SendMessage(
    type="message",
    recipient="agent-name",
    content="消息内容"
)

# 广播给所有 Agent
SendMessage(
    type="broadcast",
    content="团队消息"
)
```

---

## 下一步

- 详细指南: [完整最佳实践](./README.md)
- 项目示例: [高级推理功能实现](../feat/advanced-inference/)

---

*最后更新: 2026-03-13*
