# 高级推理功能 - 实施计划文档

## 1. 项目概述

### 1.1 目标

将 Text-to-SQL Prototype 的高级推理功能从文档阶段推进到实现阶段，支持以下组合策略：

| 组合策略 | 推理手段 | 评测手段 |
|----------|----------|----------|
| **vote@k** | Sampling (n=K) | Majority Voting |
| **pass@k** | Sampling (n=K) | Pass@K |
| Check-Correct | Check-Correct | Greedy Search |

### 1.2 参考实现

- `@project/ICED-2026-paper-code/infer.py` - Sampling 推理
- `@project/ICED-2026-paper-code/evaluate_bird.py` - 评测手段
- `@project/ICED-2026-paper-code/lc_text_to_sql_pipeline.py` - Check-Correct

### 1.3 文档依据

- `../README.md` - 功能索引和概念定义
- `../PRD.md` - 产品需求
- `../Business-Logic.md` - 业务逻辑和算法
- `../Technical-Design.md` - 技术架构设计
- `../API-Documentation.md` - API 接口规范

---

## 2. Agent Team 组织架构

### 2.1 团队配置

```
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Team 组织架构                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                                │
│  │  Team Lead  │  (team-lead)                                   │
│  │  统筹协调    │  - 任务分配                                    │
│  │             │  - 进度跟踪                                    │
│  │             │  - 质量保证                                    │
│  └──────┬──────┘                                                │
│         │                                                       │
│    ┌────┴────┬─────────┬─────────┬─────────┐                   │
│    │         │         │         │         │                   │
│    ▼         ▼         ▼         ▼         ▼                   │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                 │
│ │backend│ │backend│ │backend│ │backend│ │frontend│             │
│ │-model │ │-service│ │-api  │ │-task │ │-ui   │                │
│ │模型层 │ │服务层 │ │接口层 │ │任务层 │ │界面层 │               │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                 │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  test-e2e   │  │  test-unit  │  │   review    │            │
│  │  E2E测试    │  │  单元测试   │  │   代码审查   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent 职责定义

| Agent | 职责 | 技能要求 |
|-------|------|----------|
| **team-lead** | 统筹协调、任务分配、进度跟踪、质量保证 | 全栈理解、项目管理 |
| **backend-model** | 数据库模型扩展（EvalTask/EvalResult） | SQLAlchemy、Alembic |
| **backend-service** | 核心服务实现（SQLChecker/SQLCorrector/PassAtKEvaluator） | Python、异步编程 |
| **backend-api** | API 接口实现（FastAPI 路由、Schema） | FastAPI、Pydantic |
| **backend-task** | 后台任务实现（Celery 任务、EvalTaskRunner） | Celery、异步任务 |
| **frontend-ui** | 前端界面实现（推理模式选择、结果展示） | Vue3、TypeScript |
| **test-e2e** | E2E 测试用例设计和执行 | Playwright、测试设计 |
| **test-unit** | 单元测试编写 | pytest、Mock |
| **review** | 代码审查、文档审查 | 代码规范、最佳实践 |

---

## 3. 任务规划与依赖关系

### 3.1 任务分解结构（WBS）

```
高级推理功能实现
├── Phase 1: 基础设施 (Week 1)
│   ├── Task 1.1: 数据库模型扩展
│   │   ├── 1.1.1: EvalTask 新增字段
│   │   ├── 1.1.2: EvalResult 新增字段
│   │   └── 1.1.3: Alembic 迁移脚本
│   ├── Task 1.2: Schema 定义
│   │   ├── 1.2.1: QueryGenerateAdvancedRequest/Response
│   │   └── 1.2.2: 扩展 EvalTaskCreate Schema
│   └── Task 1.3: 项目结构初始化
│       ├── 1.3.1: 新建服务模块文件
│       └── 1.3.2: 配置更新
│
├── Phase 2: 核心服务实现 (Week 2)
│   ├── Task 2.1: SQLChecker 类实现
│   │   ├── 2.1.1: 语法检查方法
│   │   ├── 2.1.2: 执行验证方法
│   │   └── 2.1.3: 错误分类方法
│   ├── Task 2.2: SQLCorrector 类实现
│   │   ├── 2.2.1: 修正 Prompt 构建
│   │   └── 2.2.2: 响应解析方法
│   ├── Task 2.3: PassAtKEvaluator 类实现
│   │   ├── 2.3.1: 并行执行 K 个候选
│   │   ├── 2.3.2: Pass@K 指标计算
│   │   └── 2.3.3: 多数投票算法
│   └── Task 2.4: nl2sql.py 扩展
│       ├── 2.4.1: generate_sql_pass_at_k()
│       └── 2.4.2: generate_sql_with_check_correct()
│
├── Phase 3: API 层实现 (Week 2-3)
│   ├── Task 3.1: 新增 API 端点
│   │   ├── 3.1.1: POST /queries/generate-advanced
│   │   └── 3.1.2: 扩展 POST /eval/tasks
│   └── Task 3.2: 现有端点兼容
│       └── 3.2.1: 向后兼容处理
│
├── Phase 4: 后台任务实现 (Week 3)
│   ├── Task 4.1: EvalTaskRunner 重构
│   │   ├── 4.1.1: 模式分发逻辑
│   │   ├── 4.1.2: _run_pass_at_k_evaluation()
│   │   └── 4.1.3: _run_check_correct_evaluation()
│   └── Task 4.2: 进度追踪增强
│       └── 4.2.1: WebSocket 实时进度
│
├── Phase 5: 前端实现 (Week 3-4)
│   ├── Task 5.1: 推理模式选择组件
│   │   ├── 5.1.1: vote@k/pass@k 选项
│   │   └── 5.1.2: Check-Correct 配置
│   ├── Task 5.2: 结果展示组件
│   │   ├── 5.2.1: 候选 SQL 列表
│   │   └── 5.2.2: 修正历史时间线
│   └── Task 5.3: 评测任务配置
│       └── 5.3.1: 新增评测模式选项
│
├── Phase 6: 测试验证 (Week 4)
│   ├── Task 6.1: 单元测试
│   │   ├── 6.1.1: SQLChecker 测试
│   │   ├── 6.1.2: SQLCorrector 测试
│   │   └── 6.1.3: PassAtKEvaluator 测试
│   ├── Task 6.2: E2E 测试
│   │   ├── 6.2.1: TC-ADV-001 ~ TC-ADV-010
│   │   └── 6.2.2: 回归测试
│   └── Task 6.3: 性能测试
│       └── 6.3.1: 并发和超时测试
│
└── Phase 7: 文档和发布 (Week 5)
    ├── Task 7.1: API 文档更新
    ├── Task 7.2: 用户指南编写
    └── Task 7.3: 功能发布
```

### 3.2 任务依赖关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         任务依赖关系图                                   │
└─────────────────────────────────────────────────────────────────────────┘

Phase 1: 基础设施
┌─────────┐    ┌─────────┐    ┌─────────┐
│ 1.1 模型 │───▶│ 1.2 Schema│───▶│ 1.3 结构 │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     └──────────────┴──────────────┘
                    │
                    ▼
Phase 2: 核心服务 (可并行)
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 2.1     │    │ 2.2     │    │ 2.3     │    │ 2.4     │
│SQLChecker│    │SQLCorrector│   │PassAtK   │    │nl2sql   │
│         │    │         │    │Evaluator│    │扩展     │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                    │
                    ▼
Phase 3: API 层
┌─────────┐    ┌─────────┐
│ 3.1 新增 │───▶│ 3.2 兼容 │
│ API    │    │ 处理   │
└────┬────┘    └────┬────┘
     │              │
     └──────────────┘
            │
            ▼
Phase 4: 后台任务 ────────┐
┌─────────┐             │
│ 4.1     │             │
│ TaskRunner│            │
└────┬────┘             │
     │                  │
     ▼                  ▼
Phase 5: 前端实现 (与 Phase 2-4 部分并行)
┌─────────┐    ┌─────────┐    ┌─────────┐
│ 5.1 选择 │───▶│ 5.2 展示 │───▶│ 5.3 配置 │
│ 组件   │    │ 组件   │    │ 组件   │
└─────────┘    └─────────┘    └─────────┘
            │
            ▼
Phase 6: 测试验证
┌─────────┐    ┌─────────┐    ┌─────────┐
│ 6.1 单元 │───▶│ 6.2 E2E │───▶│ 6.3 性能 │
│ 测试   │    │ 测试   │    │ 测试   │
└─────────┘    └─────────┘    └─────────┘
            │
            ▼
Phase 7: 文档发布
┌─────────┐    ┌─────────┐    ┌─────────┐
│ 7.1 API │───▶│ 7.2 用户 │───▶│ 7.3 功能 │
│ 文档   │    │ 指南   │    │ 发布   │
└─────────┘    └─────────┘    └─────────┘
```

### 3.3 关键路径

```
关键路径（决定总工期）:

Task 1.1 (模型扩展)
    ↓
Task 2.3 (PassAtKEvaluator)
    ↓
Task 2.4 (nl2sql 扩展)
    ↓
Task 3.1 (API 实现)
    ↓
Task 4.1 (TaskRunner)
    ↓
Task 6.2 (E2E 测试)
    ↓
Task 7.3 (功能发布)

预计总工期: 5 周
```

---

## 4. 任务分配表

### 4.1 Phase 1: 基础设施 (Week 1)

| 任务 ID | 任务描述 | 负责 Agent | 依赖 | 预计工时 | 优先级 |
|---------|----------|------------|------|----------|--------|
| 1.1.1 | EvalTask 新增字段 (max_iterations, sampling_count, correction_strategy) | backend-model | - | 4h | P0 |
| 1.1.2 | EvalResult 新增字段 (iteration_count, correction_history, candidate_sqls, confidence_score) | backend-model | - | 4h | P0 |
| 1.1.3 | Alembic 迁移脚本 | backend-model | 1.1.1, 1.1.2 | 2h | P0 |
| 1.2.1 | QueryGenerateAdvancedRequest/Response Schema | backend-api | - | 4h | P0 |
| 1.2.2 | 扩展 EvalTaskCreate Schema | backend-api | - | 2h | P0 |
| 1.3.1 | 新建服务模块文件 (sql_checker.py, sql_corrector.py, pass_at_k.py) | backend-service | - | 2h | P1 |
| 1.3.2 | 配置更新 (settings.py, 依赖) | backend-service | - | 2h | P1 |

### 4.2 Phase 2: 核心服务 (Week 2)

| 任务 ID | 任务描述 | 负责 Agent | 依赖 | 预计工时 | 优先级 |
|---------|----------|------------|------|----------|--------|
| 2.1.1 | SQLChecker.check_syntax() | backend-service | 1.3.1 | 4h | P0 |
| 2.1.2 | SQLChecker.check_execution() | backend-service | 2.1.1 | 4h | P0 |
| 2.1.3 | SQLChecker.classify_error() | backend-service | 2.1.2 | 2h | P0 |
| 2.2.1 | SQLCorrector.build_correction_prompt() | backend-service | 2.1.3 | 4h | P0 |
| 2.2.2 | SQLCorrector.parse_correction_response() | backend-service | 2.2.1 | 2h | P0 |
| 2.3.1 | PassAtKEvaluator.evaluate() - 并行执行 | backend-service | 1.3.1 | 6h | P0 |
| 2.3.2 | PassAtKEvaluator.calculate_metrics() | backend-service | 2.3.1 | 2h | P0 |
| 2.3.3 | 多数投票算法 (基于 evaluator.py 扩展) | backend-service | 2.3.2 | 4h | P0 |
| 2.4.1 | generate_sql_pass_at_k() | backend-service | 2.3.3 | 4h | P0 |
| 2.4.2 | generate_sql_with_check_correct() | backend-service | 2.2.2, 2.4.1 | 6h | P0 |

### 4.3 Phase 3: API 层 (Week 2-3)

| 任务 ID | 任务描述 | 负责 Agent | 依赖 | 预计工时 | 优先级 |
|---------|----------|------------|------|----------|--------|
| 3.1.1 | POST /queries/generate-advanced | backend-api | 2.4.2 | 6h | P0 |
| 3.1.2 | 扩展 POST /eval/tasks | backend-api | 1.2.2 | 4h | P0 |
| 3.2.1 | 向后兼容处理 | backend-api | 3.1.1, 3.1.2 | 2h | P1 |

### 4.4 Phase 4: 后台任务 (Week 3)

| 任务 ID | 任务描述 | 负责 Agent | 依赖 | 预计工时 | 优先级 |
|---------|----------|------------|------|----------|--------|
| 4.1.1 | 模式分发逻辑重构 | backend-task | 3.1.2 | 4h | P0 |
| 4.1.2 | _run_pass_at_k_evaluation() | backend-task | 4.1.1, 2.4.1 | 6h | P0 |
| 4.1.3 | _run_check_correct_evaluation() | backend-task | 4.1.2, 2.4.2 | 6h | P0 |
| 4.2.1 | WebSocket 实时进度增强 | backend-task | 4.1.3 | 4h | P1 |

### 4.5 Phase 5: 前端 (Week 3-4)

| 任务 ID | 任务描述 | 负责 Agent | 依赖 | 预计工时 | 优先级 |
|---------|----------|------------|------|----------|--------|
| 5.1.1 | 推理模式选择组件 (vote@k/pass@k/Check-Correct) | frontend-ui | - | 8h | P0 |
| 5.1.2 | Check-Correct 配置面板 | frontend-ui | 5.1.1 | 4h | P0 |
| 5.2.1 | 候选 SQL 列表展示 | frontend-ui | 5.1.1 | 6h | P0 |
| 5.2.2 | 修正历史时间线组件 | frontend-ui | 5.1.2 | 6h | P0 |
| 5.3.1 | 评测任务配置扩展 | frontend-ui | 3.1.2 | 4h | P0 |

### 4.6 Phase 6: 测试 (Week 4)

| 任务 ID | 任务描述 | 负责 Agent | 依赖 | 预计工时 | 优先级 |
|---------|----------|------------|------|----------|--------|
| 6.1.1 | SQLChecker 单元测试 | test-unit | 2.1.3 | 4h | P0 |
| 6.1.2 | SQLCorrector 单元测试 | test-unit | 2.2.2 | 4h | P0 |
| 6.1.3 | PassAtKEvaluator 单元测试 | test-unit | 2.3.3 | 4h | P0 |
| 6.2.1 | TC-ADV-001 ~ TC-ADV-010 E2E 测试 | test-e2e | 4.2.1, 5.3.1 | 16h | P0 |
| 6.2.2 | 回归测试 | test-e2e | 6.2.1 | 4h | P0 |
| 6.3.1 | 并发和超时性能测试 | test-e2e | 4.2.1 | 4h | P1 |

### 4.7 Phase 7: 发布 (Week 5)

| 任务 ID | 任务描述 | 负责 Agent | 依赖 | 预计工时 | 优先级 |
|---------|----------|------------|------|----------|--------|
| 7.1.1 | API 文档更新 | review | 3.2.1 | 4h | P0 |
| 7.2.1 | 用户指南编写 | review | 7.1.1 | 8h | P0 |
| 7.3.1 | 功能发布检查清单 | team-lead | 6.3.1, 7.2.1 | 4h | P0 |

---

## 5. 协作规范

### 5.1 代码规范

- **Python**: 遵循 PEP 8，使用 Black 格式化
- **TypeScript**: 遵循项目 ESLint 配置
- **提交规范**: 使用 conventional commits
  - `feat(ADV-XXX): 描述` - 新功能
  - `fix(ADV-XXX): 描述` - Bug 修复
  - `test(ADV-XXX): 描述` - 测试
  - `docs(ADV-XXX): 描述` - 文档

### 5.2 沟通机制

| 场景 | 沟通方式 | 示例 |
|------|----------|------|
| 任务完成 | TaskUpdate + SendMessage | "Task X.X 已完成，通知下游 Agent" |
| 阻塞求助 | SendMessage to team-lead | "遇到 XXX 问题，需要协助" |
| 代码审查 | SendMessage to review | "请求审查 PR #XXX" |
| 进度同步 | 每日 Standup | 通过 TaskList 查看整体进度 |

### 5.3 文档更新

- 实现过程中发现设计文档需要更新时，及时通知 team-lead
- 保持 `../` 目录下文档与实现的一致性
- 代码注释与文档保持同步

---

## 6. 风险管理

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 并行执行性能问题 | 中 | 高 | 早期进行性能基准测试，必要时限流 |
| LLM 调用超时 | 高 | 中 | 实现多级超时机制，优雅降级 |
| 数据库连接池耗尽 | 中 | 高 | 使用连接池管理，限制并发数 |
| 前端后端接口不匹配 | 中 | 中 | 使用 Schema 严格校验，Mock 测试 |
| 测试环境不稳定 | 低 | 中 | 准备 Docker 化测试环境 |

---

## 7. 验收标准

### 7.1 功能验收

- [ ] vote@k 策略可用（Sampling + Majority Voting）
- [ ] pass@k 策略可用（Sampling + Pass@K）
- [ ] Check-Correct 策略可用（迭代修正）
- [ ] 所有策略可通过 API 配置
- [ ] 前端界面支持策略选择

### 7.2 性能验收

- [ ] vote@k (K=8) 平均耗时 < 15s
- [ ] pass@k (K=8) 平均耗时 < 15s
- [ ] Check-Correct (iter=3) 平均耗时 < 30s
- [ ] 并发 4 个任务时系统稳定

### 7.3 测试验收

- [ ] 单元测试覆盖率 > 80%
- [ ] E2E 测试 TC-ADV-001 ~ TC-ADV-010 全部通过
- [ ] 回归测试无失败

---

## 8. 附录

### 8.1 参考链接

- 需求文档: `../PRD.md`
- 技术设计: `../Technical-Design.md`
- API 文档: `../API-Documentation.md`
- 业务逻辑: `../Business-Logic.md`

### 8.2 相关代码路径

```
backend/
├── app/
│   ├── models/
│   │   ├── eval_task.py       # Task 1.1
│   │   └── eval_result.py     # Task 1.1
│   ├── schemas/
│   │   ├── query.py           # Task 1.2
│   │   └── evaluation.py      # Task 1.2
│   ├── services/
│   │   ├── sql_checker.py     # Task 2.1 (新建)
│   │   ├── sql_corrector.py   # Task 2.2 (新建)
│   │   ├── pass_at_k.py       # Task 2.3 (新建)
│   │   └── nl2sql.py          # Task 2.4 (修改)
│   ├── api/v1/
│   │   ├── queries.py         # Task 3.1 (修改)
│   │   └── evaluations.py     # Task 3.2 (修改)
│   └── tasks/
│       └── eval_tasks.py      # Task 4.1 (修改)
└── alembic/
    └── versions/              # Task 1.1.3

frontend/
├── src/
│   ├── components/
│   │   ├── inference/         # Task 5.1
│   │   └── results/           # Task 5.2
│   └── views/
│       └── evaluation/        # Task 5.3
```

---

*文档版本: v1.0*
*创建日期: 2026-03-13*
*最后更新: 2026-03-13*
