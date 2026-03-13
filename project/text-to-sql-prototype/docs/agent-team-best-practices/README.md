# Agent Team 最佳实践指南

**版本**: v1.0
**基于项目**: Text-to-SQL Prototype - 高级推理功能
**编写日期**: 2026-03-13

---

## 目录

1. [概述](#1-概述)
2. [工作流程最佳实践](#2-工作流程最佳实践)
3. [Agent 配置指南](#3-agent-配置指南)
4. [各阶段经验教训](#4-各阶段经验教训)
5. [性能优化建议](#5-性能优化建议)
6. [故障排查指南](#6-故障排查指南)
7. [模板和工具](#7-模板和工具)

---

## 1. 概述

### 1.1 什么是 Agent Team 模式

Agent Team 模式是一种多 Agent 协作开发模式，通过将复杂项目分解为多个任务，由专门的 Agent 负责不同领域，实现并行高效开发。

### 1.2 适用场景

| 适合使用 | 不适合使用 |
|---------|-----------|
| ✅ 大型功能模块 (>20个任务) | ❌ 小型功能修改 (<5个任务) |
| ✅ 多技术栈协作 (前端+后端+数据库) | ❌ 单一技术栈简单任务 |
| ✅ 复杂依赖关系 | ❌ 紧急修复 (协调开销大) |
| ✅ 需要并行开发的场景 | ❌ 概念验证/原型开发 |

### 1.3 成功案例数据

**高级推理功能项目**:
- 任务总数: 38
- 完成率: 100%
- 预期周期: 5周 → 实际: 约1天核心功能
- 效率提升: **5倍**

---

## 2. 工作流程最佳实践

### 2.1 团队创建流程

```
Step 1: 评估项目规模
├── 任务数 > 20? 适合 Agent Team
├── 涉及多个技术栈? 需要专业 Agent
└── 有明确阶段划分? 便于并行执行

Step 2: 定义 Agent 角色
├── 必选: team-lead (统筹协调)
├── 技术栈 Agent: backend-*, frontend-*
├── 质量保证: review, test-*
└── 根据项目特点调整

Step 3: 创建任务依赖图
├── 识别关键路径
├── 设置 blockedBy 关系
└── 标注可并行任务

Step 4: 启动 Agent
├── Phase 1: 基础设施 (并行启动)
├── Phase 2+: 按依赖顺序启动
└── team-lead 始终首先启动
```

### 2.2 任务分解原则

**粒度控制**:
- 每个任务 **2-8 小时** 工作量
- 任务边界清晰，可独立验证
- 避免任务间过度耦合

**示例对比**:

| ❌ 不好的分解 | ✅ 好的分解 |
|-------------|------------|
| "实现 SQLChecker 服务" (太大) | #3 check_syntax() 实现<br>#6 classify_error() 实现<br>#33 check_execution() 实现 |
| "前端所有组件" (太笼统) | #32 推理模式选择器<br>#18 Check-Correct 配置面板<br>#19 候选 SQL 列表 |

### 2.3 依赖关系管理

**关键路径识别**:
```
示例关键路径:
数据库模型(1.1) → PassAtK服务(2.3) → nl2sql扩展(2.4) → API实现(3.1) → 后台任务(4.1) → E2E测试(6.2)
```

**依赖设置最佳实践**:
1. 使用 `TaskUpdate` 设置 `blockedBy`
2. 避免循环依赖
3. 尽量减少依赖链长度
4. 识别可并行执行的任务组

### 2.4 沟通协调机制

**消息传递策略**:

| 场景 | 方式 | 示例 |
|-----|------|------|
| 单点通知 | SendMessage (DM) | 通知下游 Agent 依赖已就绪 |
| 团队同步 | broadcast | 里程碑达成、阻塞升级 |
| 任务状态 | TaskUpdate | 任务完成状态更新 |

**推荐沟通频率**:
- **实时**: 任务完成/阻塞时立即通知
- **定期**: team-lead 每 2-4 小时检查一次 TaskList
- **里程碑**: 阶段完成时广播

---

## 3. Agent 配置指南

### 3.1 标准角色配置

#### team-lead (团队负责人)

```yaml
name: team-lead
description: 项目统筹协调
responsibilities:
  - 任务分配和调度
  - 进度跟踪和同步
  - 阻塞问题升级处理
  - 质量保证把关
workflows:
  - 定期检查 TaskList，识别阻塞任务
  - 广播进度同步消息
  - 协调资源解决冲突
  - 维护项目进度看板
```

#### backend-service (核心服务开发)

```yaml
name: backend-service
description: 后端核心服务开发者
skills:
  - Python 异步编程
  - 业务逻辑实现
  - LLM 调用和 Prompt 工程
assigned_tasks:
  - Phase 2: 核心服务实现
  - Phase 6: 单元测试
deliverables:
  - services/ 目录下的服务模块
  - tests/unit/ 单元测试文件
```

#### backend-api (API 开发)

```yaml
name: backend-api
description: 后端 API 接口开发者
skills:
  - FastAPI / Pydantic
  - RESTful API 设计
  - 前后端接口约定
assigned_tasks:
  - Phase 1: Schema 定义
  - Phase 3: API 实现
deliverables:
  - schemas/ 数据模型
  - api/v1/ API 端点
```

#### frontend-ui (前端开发)

```yaml
name: frontend-ui
description: 前端界面开发者
skills:
  - Vue 3 + TypeScript
  - Element Plus / 组件库
  - Axios / API 调用
assigned_tasks:
  - Phase 5: 前端组件实现
deliverables:
  - components/ 可复用组件
  - views/ 页面组件
  - api/ 前端 API 封装
```

#### review (代码审查)

```yaml
name: review
description: 代码审查员
skills:
  - 代码规范审查
  - 架构一致性检查
  - 技术文档编写
responsibilities:
  - 审查代码变更
  - 确保与设计文档一致
  - 编写用户文档和 API 文档
workflow:
  - 收到审查请求后及时响应
  - 使用 SendMessage 提供反馈
  - 标记阻塞问题并升级
```

### 3.2 Agent 启动顺序

```
启动顺序策略:

Phase 1 (基础设施)
├── team-lead (首先启动)
├── backend-model (数据库模型)
├── backend-api (Schema定义)
└── frontend-ui (组件准备)

Phase 2 (核心服务)
└── backend-service (依赖 Phase 1)

Phase 3 (API层)
└── backend-api 继续 (依赖 Phase 2)

Phase 4 (后台任务)
└── backend-task (依赖 Phase 3)

Phase 5-6 (前端与测试)
├── frontend-ui 继续 (可与 Phase 2-4 并行)
├── test-unit (依赖 Phase 2)
└── test-e2e (依赖 Phase 4)

Phase 7 (文档)
└── review (贯穿全程，最后收尾)
```

### 3.3 Agent Prompt 编写规范

**必备要素**:
1. **角色定位**: 清晰的职责描述
2. **当前任务**: 具体的任务编号和内容
3. **依赖关系**: 上游依赖和下游被依赖
4. **参考文档**: 相关设计文档路径
5. **交付标准**: 完成标准和验收条件
6. **沟通方式**: 如何汇报进度和阻塞

**示例模板**:
```markdown
你是 {agent-name}，负责 {职责描述}。

**当前任务**:
任务 #{id}: {任务名称}
- 状态: {status}
- 优先级: {priority}

**任务详情**:
{详细描述}

**依赖关系**:
- 上游: #{dep-id} (等待/已完成)
- 下游: #{next-id} (完成后通知)

**参考文档**:
- 技术设计: {path}
- API文档: {path}

**交付物**:
- {文件路径1}
- {文件路径2}

**工作流程**:
1. 阅读参考文档
2. 实现功能
3. 自测验证
4. 更新任务状态
5. 通知下游 Agent
```

---

## 4. 各阶段经验教训

### 4.1 Phase 1: 基础设施

**最佳实践**:
- ✅ 数据库模型、Schema、服务初始化可以并行
- ✅ 尽早约定命名规范（避免后续不一致）
- ✅ 设计文档必须先于实现完成

**经验教训**:
- ⚠️ 前后端枚举值命名不一致导致后续修改
  - 解决: 统一采用后端命名，前端适配
- ⚠️ 验证范围前后端不一致
  - 解决: 前期约定统一，后端采用更保守的范围

### 4.2 Phase 2: 核心服务

**最佳实践**:
- ✅ 核心服务实现采用"小而美"的函数分解
- ✅ 每个函数对应一个独立的任务
- ✅ 单元测试与实现同步进行

**经验教训**:
- ✅ SQLChecker、SQLCorrector、PassAtKEvaluator 分离清晰，便于测试
- ✅ 并行开发多个服务模块提高效率

### 4.3 Phase 3-4: API 与后台任务

**最佳实践**:
- ✅ API 实现优先于后台任务
- ✅ 使用 `blockedBy` 明确表达依赖关系

**经验教训**:
- ⚠️ backend-task 启动延迟（等待 API 完成）
  - 改进: 可在 API 接近完成时提前准备

### 4.4 Phase 5-6: 前端与测试

**最佳实践**:
- ✅ 前端开发可与后端并行
- ✅ E2E 测试规范先行，便于统一理解
- ✅ 回归测试覆盖所有核心功能

### 4.5 Phase 7: 文档

**最佳实践**:
- ✅ 文档与开发同步进行（而非最后补）
- ✅ review Agent 负责文档质量保证

**经验教训**:
- ⚠️ 文档任务滞后于开发
  - 改进: 应与对应功能开发同步

---

## 5. 性能优化建议

### 5.1 并行执行策略

**可并行任务组**:
```
Phase 1 并行组:
├── 数据库模型 (backend-model)
├── Schema定义 (backend-api)
├── 服务初始化 (backend-service)
└── 组件准备 (frontend-ui)

Phase 2-3 并行组:
├── 核心服务实现 (backend-service)
└── 前端组件开发 (frontend-ui)
```

### 5.2 阻塞处理优化

**识别阻塞信号**:
- Agent 长时间未更新状态
- TaskList 显示任务停滞
- 依赖任务未按时完成

**升级策略**:
```
Agent 遇到阻塞:
    │
    ├── 技术阻塞 → 发送消息给 team-lead
    ├── 依赖延迟 → 检查上游状态，必要时升级
    └── 架构冲突 → 立即升级，暂停相关任务
```

### 5.3 效率提升技巧

1. **提前启动准备**: 依赖即将完成时，下游 Agent 可提前阅读文档
2. **批量处理**: 同类型任务集中处理（如多个单元测试）
3. **模板复用**: 使用标准化的任务描述和 Prompt 模板

---

## 6. 故障排查指南

### 6.1 常见问题及解决

#### 问题 1: Agent 长时间无响应

**症状**: Agent 状态显示 idle，但任务未完成

**排查步骤**:
1. 检查任务描述是否清晰
2. 确认参考文档是否完整
3. 查看是否有未解除的阻塞

**解决方案**:
- 发送消息询问 Agent 状态
- 提供更明确的任务指引
- 必要时重新分配任务

#### 问题 2: 代码不一致/冲突

**症状**: 前后端接口不匹配，枚举值不一致等

**预防措施**:
- 前期约定接口规范
- review Agent 早期介入审查
- 使用 Schema 驱动开发

**解决方案**:
- 立即修复不一致
- 更新设计文档
- 通知相关 Agent

#### 问题 3: 任务依赖死锁

**症状**: 多个任务互相等待，无法推进

**排查步骤**:
1. 检查 `blockedBy` 设置
2. 确认是否有循环依赖

**解决方案**:
- 打破循环依赖
- 重新设计任务分解

### 6.2 调试技巧

**检查任务状态**:
```bash
TaskList                    # 查看所有任务
TaskGet --taskId="27"       # 查看特定任务
```

**查看 Agent 状态**:
```bash
# 查看团队成员
~/.claude/teams/{team-name}/config.json
```

**发送调试消息**:
```python
SendMessage(
    type="message",
    recipient="agent-name",
    content="[调试] 请报告当前任务状态和阻塞原因"
)
```

---

## 7. 模板和工具

### 7.1 任务创建模板

```python
TaskCreate(
    subject="任务标题",
    description="""
## 任务描述
{详细描述}

## 验收标准
- [ ] 标准1
- [ ] 标准2

## 参考文档
- {文档路径}

## 依赖关系
- 依赖: #{id}
- 被依赖: #{id}
""",
    metadata={
        "phase": "Phase X",
        "priority": "P0/P1/P2",
        "estimated_hours": 4
    }
)
```

### 7.2 Agent 启动命令模板

```python
Agent(
    name="agent-name",
    prompt="""
你是 {role}，负责 {responsibility}。

**当前任务**: #{id} {name}
**参考文档**: {path}
**依赖**: #{dep-id}

任务详情: {description}

完成后:
1. 更新任务状态为 completed
2. 通知 team-lead
3. 如有下游依赖，通知相关 Agent
""",
    team_name="team-name",
    subagent_type="general-purpose"
)
```

### 7.3 进度报告模板

```markdown
## 进度报告

### 已完成任务
- ✅ #{id} {name}

### 进行中任务
- 🔄 #{id} {name} ({progress}%)

### 阻塞项
- 🔴 #{id}: {原因}

### 下一步计划
1. {计划1}
2. {计划2}
```

### 7.4 项目看板模板

```markdown
## 项目进度看板

### Phase X: {名称}
| 任务 | 负责人 | 状态 | 进度 |
|------|--------|------|------|
| #{id} {name} | {agent} | 🟡 进行中 | 80% |

状态说明:
- 🟢 已完成
- 🟡 进行中
- 🔴 阻塞
- ⚪ 未开始
```

---

## 附录 A: 成功项目复盘清单

项目完成后，使用以下清单进行复盘:

- [ ] 所有任务是否按时完成？
- [ ] 是否有未预料的阻塞？原因是什么？
- [ ] Agent 协作是否顺畅？
- [ ] 代码质量是否达标？
- [ ] 文档是否完整？
- [ ] 有哪些可以复用的经验？
- [ ] 有哪些需要改进的地方？

---

## 附录 B: 参考资源

- [Agent Team 启动指南](../feat/advanced-inference/plan/Agent-Team-Launch.md)
- [工作流程分析](../feat/advanced-inference/AGENT-TEAM-WORKFLOW-ANALYSIS.md)
- [执行总结报告](../feat/advanced-inference/AGENT-TEAM-EXECUTION-SUMMARY.md)

---

*本文档基于 Text-to-SQL Prototype 高级推理功能项目的实际经验编写。*
*最后更新: 2026-03-13*
