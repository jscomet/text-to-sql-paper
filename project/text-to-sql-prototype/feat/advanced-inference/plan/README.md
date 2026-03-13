# 高级推理功能 - 计划文档索引

## 目录结构

```
plan/
├── README.md                          # 本文件 - 计划文档索引
├── Implementation-Plan.md             # 实施计划 - 详细任务分解和依赖关系
├── Agent-Team-Launch.md              # Agent Team 启动指南 - 如何启动和协调 Agents
└── status/                           # 状态跟踪目录 (实施过程中创建)
    ├── daily/                        # 每日状态更新
    ├── weekly/                       # 周报
    └── blockers.md                   # 阻塞问题跟踪
```

---

## 文档说明

### 1. Implementation-Plan.md (实施计划)

**目标读者**: Team Lead, 各 Agent

**内容概要**:
- 项目概述和目标
- Agent Team 组织架构
- 详细任务分解 (WBS)
- 任务依赖关系图
- 关键路径分析
- 任务分配表
- 风险管理
- 验收标准

**使用场景**:
- 项目启动前整体规划
- 任务分配参考
- 进度跟踪依据
- 风险评估

### 2. Agent-Team-Launch.md (Agent Team 启动指南)

**目标读者**: Team Lead

**内容概要**:
- 启动前准备检查清单
- Agent Team 启动步骤
- Agent 配置说明
- 启动命令示例
- 协作流程
- 监控和报告机制

**使用场景**:
- 启动 Agent Team
- 配置新 Agents
- 日常协调参考

---

## 实施阶段路线图

```
Week 1                    Week 2                    Week 3                    Week 4                    Week 5
│                         │                         │                         │                         │
├─ Phase 1: 基础设施 ─────┼─────────────────────────┼─────────────────────────┼─────────────────────────┤
│  Task 1.1: 数据库模型   │                         │                         │                         │
│  Task 1.2: Schema 定义  │                         │                         │                         │
│  Task 1.3: 项目结构     │                         │                         │                         │
│                         ├─ Phase 2: 核心服务 ─────┼─────────────────────────┤                         │
│                         │  Task 2.1: SQLChecker   │                         │                         │
│                         │  Task 2.2: SQLCorrector │                         │                         │
│                         │  Task 2.3: PassAtKEval  │                         │                         │
│                         │  Task 2.4: nl2sql 扩展  │                         │                         │
│                         │                         ├─ Phase 3-4: API & Task ─┤                         │
│                         │                         │  Task 3.x: API 层       │                         │
│                         │                         │  Task 4.x: 后台任务     │                         │
├─────────────────────────┼─────────────────────────┼─ Phase 5: 前端 ─────────┤                         │
│                         │                         │                         │  Task 5.x: 前端实现     │
│                         │                         │                         ├─ Phase 6: 测试 ─────────┤
│                         │                         │                         │  Task 6.x: 测试验证     │
│                         │                         │                         │                         ├─ Phase 7: 发布 ─┤
│                         │                         │                         │                         │  Task 7.x: 发布  │
▼                         ▼                         ▼                         ▼                         ▼
里程碑 M1                 里程碑 M2                 里程碑 M3                 里程碑 M4                 里程碑 M5
基础设施完成              核心服务完成              API & 前端完成            测试完成                  功能发布
```

---

## 快速开始

### 1. 查看详细计划

```bash
# 阅读实施计划
cat plan/Implementation-Plan.md

# 阅读启动指南
cat plan/Agent-Team-Launch.md
```

### 2. 启动 Agent Team

参考 `Agent-Team-Launch.md` 中的步骤：

1. **Step 1**: 确认文档完整性和开发环境
2. **Step 2**: 创建团队 `advanced-inference-impl`
3. **Step 3**: 创建任务列表
4. **Step 4**: 按顺序启动 Agents

### 3. 跟踪进度

```bash
# 查看任务列表
TaskList

# 查看项目状态
# (状态文件将在实施过程中创建)
cat plan/status/weekly/week1.md
```

---

## Agent 角色速查

| Agent | 负责 Phase | 核心任务 | 参考文档 |
|-------|-----------|----------|----------|
| team-lead | 全部 | 统筹协调、进度跟踪、质量保证 | Implementation-Plan.md 第2节 |
| backend-model | Phase 1 | 数据库模型扩展 | Implementation-Plan.md 第4.1节 |
| backend-api | Phase 1, 3 | Schema 定义、API 实现 | Implementation-Plan.md 第4.1, 4.3节 |
| backend-service | Phase 2 | 核心服务实现 | Implementation-Plan.md 第4.2节 |
| backend-task | Phase 4 | 后台任务实现 | Implementation-Plan.md 第4.4节 |
| frontend-ui | Phase 5 | 前端界面实现 | Implementation-Plan.md 第4.5节 |
| test-unit | Phase 6 | 单元测试 | Implementation-Plan.md 第4.6节 |
| test-e2e | Phase 6 | E2E 测试 | Implementation-Plan.md 第4.6节 |
| review | 全部 | 代码审查 | Implementation-Plan.md 第4.7节 |

---

## 关键参考文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 功能索引 | `../README.md` | 功能总览和概念定义 |
| 产品需求 | `../PRD.md` | 详细功能规格 |
| 业务逻辑 | `../Business-Logic.md` | 算法和流程 |
| 技术设计 | `../Technical-Design.md` | 架构和类设计 |
| API 文档 | `../API-Documentation.md` | 接口规范 |
| ICED-2026 infer.py | `../../../ICED-2026-paper-code/infer.py` | 参考实现 |
| ICED-2026 evaluate_bird.py | `../../../ICED-2026-paper-code/evaluate_bird.py` | 参考实现 |

---

## 重要概念

### 三层概念体系

```
┌─────────────────────────────────────────────────────┐
│                    组合策略                          │
├─────────────────────────────────────────────────────┤
│  vote@k = Sampling + Majority Voting                │
│  pass@k = Sampling + Pass@K                         │
└─────────────────────────────────────────────────────┘
                    ↓ 分解为
┌─────────────────────────┐    ┌──────────────────────┐
│       推理手段          │    │       评测手段        │
├─────────────────────────┤    ├──────────────────────┤
│  Single/Greedy          │    │  Greedy Search       │
│  Sampling (n=K)         │    │  Majority Voting     │
│  Check-Correct          │    │  Pass@K              │
└─────────────────────────┘    └──────────────────────┘
```

### ICED-2026 对应关系

```bash
# vote@k 组合策略
infer.py --n 8 --temperature 0.8          # Sampling 推理
evaluate_bird.py --mode major_voting      # Majority Voting 评测

# pass@k 组合策略
infer.py --n 8 --temperature 0.8          # Sampling 推理（同上）
evaluate_bird.py --mode pass_at_k         # Pass@K 评测
```

---

## 联系和反馈

- **项目路径**: `D:/Working/paper/project/text-to-sql-prototype/feat/advanced-inference/`
- **计划路径**: `D:/Working/paper/project/text-to-sql-prototype/feat/advanced-inference/plan/`
- **状态跟踪**: `plan/status/` (实施过程中创建)

如有问题，请联系 **team-lead**。

---

*最后更新: 2026-03-13*
