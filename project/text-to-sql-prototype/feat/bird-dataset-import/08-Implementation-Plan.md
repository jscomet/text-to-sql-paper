# BIRD 数据集导入支持 - 实施文档

## 1. 概述

本文档描述 BIRD 数据集导入特性的详细实施计划，包括任务分解、依赖关系、并行策略和 Agent Team 配置。

---

## 2. 任务分解 (WBS)

### 2.1 任务总览

```
BIRD 数据集导入实施
├── Phase 1: 基础架构 (P0)
│   ├── Task 1.1: 数据库迁移 - 添加父子任务字段
│   ├── Task 1.2: 后端模型更新 - EvalTask 模型
│   └── Task 1.3: Pydantic Schemas 更新
├── Phase 2: 后端核心功能 (P0)
│   ├── Task 2.1: 数据集验证服务
│   ├── Task 2.2: 数据集解析服务
│   ├── Task 2.3: 数据库连接批量创建服务
│   ├── Task 2.4: 父子任务创建服务
│   └── Task 2.5: 父任务统计更新服务
├── Phase 3: API 层 (P0)
│   ├── Task 3.1: 数据集导入 API (Zip/Local)
│   ├── Task 3.2: 评测任务 API 增强
│   └── Task 3.3: 批量操作 API
├── Phase 4: 前端基础组件 (P0)
│   ├── Task 4.1: 类型定义更新
│   ├── Task 4.2: API 服务层更新
│   └── Task 4.3: 父子任务列表组件
├── Phase 5: 前端业务组件 (P1)
│   ├── Task 5.1: 导入对话框
│   ├── Task 5.2: 导入进度对话框
│   ├── Task 5.3: 父任务详情页
│   └── Task 5.4: 子任务详情页增强
└── Phase 6: 测试与验证 (P0)
    ├── Task 6.1: 单元测试
    ├── Task 6.2: API 集成测试
    └── Task 6.3: E2E 测试
```

### 2.2 任务详细说明

#### Phase 1: 基础架构

| 任务                  | 优先级 | 估算工时 | 关键文件                                                  |
| --------------------- | ------ | -------- | --------------------------------------------------------- |
| 1.1 数据库迁移        | P0     | 2h       | `backend/alembic/versions/xxx_add_parent_child_task.py` |
| 1.2 EvalTask 模型更新 | P0     | 3h       | `backend/app/models/eval_task.py`                       |
| 1.3 Schemas 更新      | P0     | 2h       | `backend/app/schemas/eval_task.py`                      |

#### Phase 2: 后端核心功能

| 任务                 | 优先级 | 估算工时 | 关键文件                                       |
| -------------------- | ------ | -------- | ---------------------------------------------- |
| 2.1 数据集验证服务   | P0     | 4h       | `backend/app/services/dataset_validator.py`  |
| 2.2 数据集解析服务   | P0     | 3h       | `backend/app/services/dataset_parser.py`     |
| 2.3 连接批量创建服务 | P0     | 3h       | `backend/app/services/connection_service.py` |
| 2.4 父子任务创建服务 | P0     | 5h       | `backend/app/services/eval_task_service.py`  |
| 2.5 父任务统计更新   | P0     | 3h       | `backend/app/services/eval_task_service.py`  |

#### Phase 3: API 层

| 任务                  | 优先级 | 估算工时 | 关键文件                                    |
| --------------------- | ------ | -------- | ------------------------------------------- |
| 3.1 数据集导入 API    | P0     | 5h       | `backend/app/api/v1/endpoints/dataset.py` |
| 3.2 评测任务 API 增强 | P0     | 4h       | `backend/app/api/v1/endpoints/eval.py`    |
| 3.3 批量操作 API      | P1     | 3h       | `backend/app/api/v1/endpoints/eval.py`    |

#### Phase 4: 前端基础组件

| 任务             | 优先级 | 估算工时 | 关键文件                                      |
| ---------------- | ------ | -------- | --------------------------------------------- |
| 4.1 类型定义更新 | P0     | 2h       | `frontend/src/types/eval.ts`                |
| 4.2 API 服务层   | P0     | 3h       | `frontend/src/api/eval.ts`                  |
| 4.3 父子任务列表 | P0     | 5h       | `frontend/src/components/eval/TaskList.vue` |

#### Phase 5: 前端业务组件

| 任务               | 优先级 | 估算工时 | 关键文件                                               |
| ------------------ | ------ | -------- | ------------------------------------------------------ |
| 5.1 导入对话框     | P1     | 6h       | `frontend/src/components/dataset/ImportDialog.vue`   |
| 5.2 进度对话框     | P1     | 4h       | `frontend/src/components/dataset/ProgressDialog.vue` |
| 5.3 父任务详情页   | P1     | 5h       | `frontend/src/views/eval/ParentTaskDetail.vue`       |
| 5.4 子任务详情增强 | P1     | 3h       | `frontend/src/views/eval/TaskDetail.vue`             |

#### Phase 6: 测试

| 任务             | 优先级 | 估算工时 | 关键文件                   |
| ---------------- | ------ | -------- | -------------------------- |
| 6.1 单元测试     | P0     | 6h       | `backend/app/tests/`     |
| 6.2 API 集成测试 | P0     | 4h       | `backend/app/tests/api/` |
| 6.3 E2E 测试     | P1     | 6h       | `e2e/specs/`             |

---

## 3. 依赖关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              依赖关系图                                       │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1: 基础架构
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Task 1.1   │───→│  Task 1.2   │───→│  Task 1.3   │
│   DB迁移    │    │  模型更新   │    │  Schemas   │
└─────────────┘    └─────────────┘    └─────────────┘
        │
        ▼
Phase 2: 后端核心 (可并行)
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Task 2.1   │    │  Task 2.2   │    │  Task 2.3   │
│  数据验证   │───→│  数据解析   │    │ 连接创建    │
└─────────────┘    └─────────────┘    └─────────────┘
        │                                    │
        └────────────┬───────────────────────┘
                     ▼
              ┌─────────────┐
              │  Task 2.4   │
              │ 任务创建    │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │  Task 2.5   │
              │ 统计更新    │
              └─────────────┘

Phase 3: API 层 (依赖 Phase 1 & 2)
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Task 3.1   │    │  Task 3.2   │    │  Task 3.3   │
│  导入API    │    │ 任务API增强 │    │ 批量操作API │
└─────────────┘    └─────────────┘    └─────────────┘

Phase 4: 前端基础 (依赖 Phase 3)
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Task 4.1   │───→│  Task 4.2   │───→│  Task 4.3   │
│  类型定义   │    │  API服务    │    │ 列表组件    │
└─────────────┘    └─────────────┘    └─────────────┘

Phase 5: 前端业务 (依赖 Phase 4)
┌─────────────┐    ┌─────────────┐
│  Task 5.1   │    │  Task 5.2   │
│  导入对话框 │    │ 进度对话框  │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│  Task 5.3   │    │  Task 5.4   │
│ 父任务详情  │    │ 子任务详情  │
└─────────────┘    └─────────────┘

Phase 6: 测试 (依赖所有实现)
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Task 6.1   │    │  Task 6.2   │    │  Task 6.3   │
│  单元测试   │    │ 集成测试    │    │  E2E测试    │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## 4. 并行策略

### 4.1 并行组划分

```
┌─────────────────────────────────────────────────────────────────┐
│                     并行执行组 (Parallel Groups)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Group 1: 数据库层 (顺序执行)                                     │
│  ├── Task 1.1: DB 迁移                                           │
│  ├── Task 1.2: 模型更新                                          │
│  └── Task 1.3: Schemas 更新                                      │
│                                                                 │
│  Group 2: 后端核心服务 (Phase 1 完成后并行)                        │
│  ├── Task 2.1: 数据验证服务  ──┐                                 │
│  ├── Task 2.2: 数据解析服务  ──┼──→ Task 2.4: 任务创建服务        │
│  └── Task 2.3: 连接创建服务  ──┘                                 │
│                                │                                 │
│                                ↓                                 │
│                         Task 2.5: 统计更新                       │
│                                                                 │
│  Group 3: API 层 (Phase 2 完成后并行)                             │
│  ├── Task 3.1: 导入 API                                          │
│  ├── Task 3.2: 任务 API 增强                                     │
│  └── Task 3.3: 批量操作 API                                      │
│                                                                 │
│  Group 4: 前端基础 (Phase 3 完成后顺序)                           │
│  ├── Task 4.1: 类型定义                                          │
│  ├── Task 4.2: API 服务                                          │
│  └── Task 4.3: 列表组件                                          │
│                                                                 │
│  Group 5: 前端业务 (Phase 4 完成后并行)                           │
│  ├── Task 5.1: 导入对话框      ──┐                               │
│  ├── Task 5.2: 进度对话框      ──┤                               │
│  ├── Task 5.3: 父任务详情页    ──┤                               │
│  └── Task 5.4: 子任务详情增强  ──┘                               │
│                                                                 │
│  Group 6: 测试 (所有实现完成后并行)                                │
│  ├── Task 6.1: 单元测试                                          │
│  ├── Task 6.2: 集成测试                                          │
│  └── Task 6.3: E2E 测试                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 关键路径

```
关键路径 (Critical Path):
Task 1.1 → Task 1.2 → Task 1.3 → Task 2.4 → Task 2.5 → Task 3.1 → Task 4.1 → Task 4.2 → Task 4.3 → Task 5.1

总工期估算: 约 40 工时 (5 天)
```

---

## 5. Agent Team 配置

### 5.1 团队结构

```
┌─────────────────────────────────────────────────────────────────┐
│                      BIRD 数据集导入 Agent Team                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                            │
│  │   Team Lead     │ (总体协调，代码审查，集成)                    │
│  │   (你)          │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┴─────┬─────────────┬─────────────┐                   │
│     ▼           ▼             ▼             ▼                   │
│ ┌────────┐ ┌────────┐  ┌──────────┐  ┌──────────┐              │
│ │Backend │ │Backend │  │ Frontend │  │  Tester  │              │
│ │ Dev 1  │ │ Dev 2  │  │   Dev    │  │          │              │
│ └────────┘ └────────┘  └──────────┘  └──────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Agent 角色与职责

|          Agent          | 角色       | 主要职责                                         | 并行任务                          |
| :---------------------: | ---------- | ------------------------------------------------ | --------------------------------- |
|   **Team Lead**   | 团队负责人 | 总体协调、任务分配、代码审查、集成测试、解决阻塞 | -                                 |
| **Backend Dev 1** | 后端开发1  | 数据库层、核心服务层、数据集验证/解析            | 1.1, 1.2, 1.3, 2.1, 2.2, 2.5      |
| **Backend Dev 2** | 后端开发2  | 连接服务、任务服务、API层                        | 2.3, 2.4, 3.1, 3.2, 3.3           |
| **Frontend Dev** | 前端开发   | 所有前端组件和页面                               | 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4 |
|    **Tester**    | 测试工程师 | 编写和执行测试用例                               | 6.1, 6.2, 6.3                     |

### 5.3 任务分配矩阵

```
任务分配矩阵 (RAM - Responsibility Assignment Matrix)
┌────────────────┬─────────┬────────────┬────────────┬──────────┬────────┐
│ 任务           │ Team Lead│ Backend 1  │ Backend 2  │ Frontend │ Tester │
├────────────────┼─────────┼────────────┼────────────┼──────────┼────────┤
│ Task 1.1 DB迁移 │  A      │    R       │     C      │    -     │   -    │
│ Task 1.2 模型   │  A      │    R       │     C      │    -     │   -    │
│ Task 1.3 Schemas│  A      │    R       │     C      │    -     │   -    │
│ Task 2.1 验证   │  C      │    R       │     -      │    -     │   -    │
│ Task 2.2 解析   │  C      │    R       │     -      │    -     │   -    │
│ Task 2.3 连接   │  C      │    -       │     R      │    -     │   -    │
│ Task 2.4 任务   │  C      │    -       │     R      │    -     │   -    │
│ Task 2.5 统计   │  C      │    R       │     -      │    -     │   -    │
│ Task 3.1 导入API│  C      │    -       │     R      │    -     │   -    │
│ Task 3.2 API增强│  C      │    -       │     R      │    -     │   -    │
│ Task 3.3 批量   │  C      │    -       │     R      │    -     │   -    │
│ Task 4.1 类型   │  C      │    C       │     -      │    R     │   -    │
│ Task 4.2 API服务│  C      │    C       │     -      │    R     │   -    │
│ Task 4.3 列表   │  C      │    C       │     -      │    R     │   -    │
│ Task 5.1 对话框 │  I      │    -       │     -      │    R     │   -    │
│ Task 5.2 进度   │  I      │    -       │     -      │    R     │   -    │
│ Task 5.3 父详情 │  I      │    -       │     -      │    R     │   -    │
│ Task 5.4 子详情 │  I      │    -       │     -      │    R     │   -    │
│ Task 6.1 单元   │  A      │    C       │     C      │    C     │   R    │
│ Task 6.2 集成   │  A      │    C       │     C      │    -     │   R    │
│ Task 6.3 E2E    │  A      │    -       │     -      │    C     │   R    │
└────────────────┴─────────┴────────────┴────────────┴──────────┴────────┘

R = Responsible (负责执行)
A = Accountable (最终负责)
C = Consulted ( consulted)
I = Informed (知情)
- = Not involved (不参与)
```

---

## 6. 实施阶段详细计划

### Phase 1: 基础架构 (Day 1)

#### Task 1.1: 数据库迁移

**负责人**: Backend Dev 1
**输入**: 04-Database-Design.md
**输出**: Alembic 迁移脚本
**检查点**:

- [ ] 迁移脚本可正常升级
- [ ] 迁移脚本可正常降级
- [ ] 所有新字段已创建
- [ ] 外键约束正确
- [ ] 索引已创建

#### Task 1.2: EvalTask 模型更新

**负责人**: Backend Dev 1
**依赖**: Task 1.1
**输入**: 04-Database-Design.md
**输出**: 更新后的 models/eval_task.py
**检查点**:

- [ ] 所有新字段已添加
- [ ] 关系定义正确
- [ ] 辅助方法已添加 (is_parent, is_child, update_parent_stats)
- [ ] 表参数已更新

#### Task 1.3: Pydantic Schemas 更新

**负责人**: Backend Dev 1
**依赖**: Task 1.2
**输入**: 05-API-Documentation.md
**输出**: 更新后的 schemas/eval_task.py
**检查点**:

- [ ] EvalTaskBase 包含新字段
- [ ] EvalTaskResponse 包含 children/parent
- [ ] 新增 EvalTaskChildren 模型
- [ ] 验证通过

---

### Phase 2: 后端核心 (Day 1-2)

#### Task 2.1: 数据集验证服务

**负责人**: Backend Dev 1
**依赖**: Task 1.3
**输入**: 03-Business-Logic.md
**输出**: services/dataset_validator.py
**检查点**:

- [ ] Zip 文件验证
- [ ] JSON 格式验证
- [ ] 必需字段检查
- [ ] 数据库文件存在检查
- [ ] 单元测试通过

#### Task 2.2: 数据集解析服务

**负责人**: Backend Dev 1
**依赖**: Task 2.1
**输入**: 03-Business-Logic.md
**输出**: services/dataset_parser.py
**检查点**:

- [ ] dev.json 解析
- [ ] db_id 列表提取
- [ ] 问题计数统计
- [ ] 单元测试通过

#### Task 2.3: 数据库连接批量创建服务

**负责人**: Backend Dev 2
**依赖**: Task 1.3
**输入**: 03-Business-Logic.md
**输出**: services/connection_service.py (更新)
**检查点**:

- [ ] 批量创建连接
- [ ] 连接名称生成
- [ ] db_id 到 connection_id 映射
- [ ] 错误处理
- [ ] 单元测试通过

#### Task 2.4: 父子任务创建服务

**负责人**: Backend Dev 2
**依赖**: Task 2.2, Task 2.3
**输入**: 03-Business-Logic.md
**输出**: services/eval_task_service.py (更新)
**检查点**:

- [ ] 父任务创建
- [ ] 子任务批量创建
- [ ] 参数继承
- [ ] 单元测试通过

#### Task 2.5: 父任务统计更新服务

**负责人**: Backend Dev 1
**依赖**: Task 2.4
**输入**: 04-Database-Design.md
**输出**: services/eval_task_service.py (更新)
**检查点**:

- [ ] 子任务完成时更新父任务
- [ ] 统计聚合正确
- [ ] 状态流转正确
- [ ] 单元测试通过

---

### Phase 3: API 层 (Day 2-3)

#### Task 3.1: 数据集导入 API

**负责人**: Backend Dev 2
**依赖**: Task 2.5
**输入**: 05-API-Documentation.md
**输出**: api/v1/endpoints/dataset.py
**检查点**:

- [ ] POST /datasets/import/zip
- [ ] POST /datasets/import/local
- [ ] GET /datasets/imports
- [ ] GET /datasets/imports/{id}
- [ ] GET /datasets/imports/{id}/progress
- [ ] DELETE /datasets/imports/{id}
- [ ] API 测试通过

#### Task 3.2: 评测任务 API 增强

**负责人**: Backend Dev 2
**依赖**: Task 1.3
**输入**: 05-API-Documentation.md
**输出**: api/v1/endpoints/eval.py (更新)
**检查点**:

- [ ] GET /evaluations 支持 task_type 筛选
- [ ] GET /evaluations/{id} 包含 children/parent
- [ ] API 测试通过

#### Task 3.3: 批量操作 API

**负责人**: Backend Dev 2
**依赖**: Task 3.2
**输入**: 05-API-Documentation.md
**输出**: api/v1/endpoints/eval.py (更新)
**检查点**:

- [ ] POST /evaluations/{id}/start-all
- [ ] POST /evaluations/{id}/retry-failed
- [ ] GET /evaluations/{id}/children
- [ ] API 测试通过

---

### Phase 4: 前端基础 (Day 3)

#### Task 4.1: 类型定义更新

**负责人**: Frontend Dev
**依赖**: Task 1.3
**输入**: 04-Database-Design.md
**输出**: types/eval.ts
**检查点**:

- [ ] EvalTask 类型包含新字段
- [ ] 新增父子任务相关类型
- [ ] 导入相关类型定义

#### Task 4.2: API 服务层更新

**负责人**: Frontend Dev
**依赖**: Task 4.1
**输入**: 05-API-Documentation.md
**输出**: api/eval.ts, api/dataset.ts
**检查点**:

- [ ] 新增 dataset API 服务
- [ ] 更新 eval API 服务
- [ ] 类型正确

#### Task 4.3: 父子任务列表组件

**负责人**: Frontend Dev
**依赖**: Task 4.2
**输入**: 02-UI-Design.md
**输出**: components/eval/TaskList.vue
**检查点**:

- [ ] 支持展开/折叠
- [ ] 任务类型筛选
- [ ] 正确显示父子关系
- [ ] 单元测试通过

---

### Phase 5: 前端业务 (Day 3-4)

#### Task 5.1: 导入对话框

**负责人**: Frontend Dev
**依赖**: Task 4.2
**输入**: 02-UI-Design.md
**输出**: components/dataset/ImportDialog.vue
**检查点**:

- [ ] Zip 上传标签页
- [ ] 本地路径标签页
- [ ] 配置表单
- [ ] 表单验证
- [ ] 调用导入 API

#### Task 5.2: 进度对话框

**负责人**: Frontend Dev
**依赖**: Task 5.1
**输入**: 02-UI-Design.md
**输出**: components/dataset/ProgressDialog.vue
**检查点**:

- [ ] 步骤指示器
- [ ] 进度条
- [ ] 日志显示
- [ ] 取消功能

#### Task 5.3: 父任务详情页

**负责人**: Frontend Dev
**依赖**: Task 4.3
**输入**: 02-UI-Design.md
**输出**: views/eval/ParentTaskDetail.vue
**检查点**:

- [ ] 统计卡片
- [ ] 子任务列表表格
- [ ] 批量操作按钮
- [ ] 状态分布图

#### Task 5.4: 子任务详情增强

**负责人**: Frontend Dev
**依赖**: Task 4.3
**输入**: 02-UI-Design.md
**输出**: views/eval/TaskDetail.vue (更新)
**检查点**:

- [ ] 显示父任务信息
- [ ] 显示 db_id
- [ ] 问题列表

---

### Phase 6: 测试 (Day 4-5)

#### Task 6.1: 单元测试

**负责人**: Tester
**依赖**: Task 2.5, Task 3.3
**输入**: 测试规范
**输出**: 单元测试代码
**检查点**:

- [ ] 验证服务测试
- [ ] 解析服务测试
- [ ] 任务服务测试
- [ ] 覆盖率 > 80%

#### Task 6.2: API 集成测试

**负责人**: Tester
**依赖**: Task 3.3
**输入**: 05-API-Documentation.md
**输出**: API 测试脚本
**检查点**:

- [ ] 导入 API 测试
- [ ] 任务 API 测试
- [ ] 批量操作 API 测试
- [ ] 所有测试通过

#### Task 6.3: E2E 测试

**负责人**: Tester
**依赖**: Task 5.4
**输入**: e2e/specs/05-Evaluation-Test-Spec.md
**输出**: E2E 测试脚本
**检查点**:

- [ ] 导入流程测试
- [ ] 父子任务列表测试
- [ ] 父任务详情测试
- [ ] 所有测试通过

---

## 7. 关键检查点

### 每日检查点

| 时间       | 检查项                     | 负责人    |
| ---------- | -------------------------- | --------- |
| Day 1 结束 | Phase 1 完成，Phase 2 开始 | Team Lead |
| Day 2 结束 | Phase 2 完成，Phase 3 完成 | Team Lead |
| Day 3 结束 | Phase 4 完成，Phase 5 开始 | Team Lead |
| Day 4 结束 | Phase 5 完成，Phase 6 开始 | Team Lead |
| Day 5 结束 | 所有测试通过，功能交付     | Team Lead |

### 质量门禁

```
┌─────────────────────────────────────────────────────────────────┐
│                        质量门禁 (Quality Gates)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Gate 1: 基础架构完成                                            │
│  ├── [ ] 数据库迁移可正常升级/降级                                │
│  ├── [ ] 模型定义通过 SQLAlchemy 验证                            │
│  └── [ ] Schemas 通过 Pydantic 验证                              │
│                                                                 │
│  Gate 2: 后端核心完成                                            │
│  ├── [ ] 所有服务有单元测试                                       │
│  ├── [ ] 单元测试覆盖率 > 80%                                     │
│  └── [ ] 服务间依赖注入正确                                       │
│                                                                 │
│  Gate 3: API 层完成                                              │
│  ├── [ ] 所有 API 端点可访问                                     │
│  ├── [ ] API 文档正确生成                                        │
│  └── [ ] API 测试全部通过                                        │
│                                                                 │
│  Gate 4: 前端完成                                                │
│  ├── [ ] 所有组件编译通过                                        │
│  ├── [ ] TypeScript 类型检查通过                                 │
│  └── [ ] ESLint 检查通过                                         │
│                                                                 │
│  Gate 5: 最终验收                                                │
│  ├── [ ] E2E 测试全部通过                                        │
│  ├── [ ] 代码审查完成                                            │
│  └── [ ] 功能演示通过                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. 风险缓解

| 风险             | 可能性 | 影响 | 缓解措施                       | 负责人        |
| ---------------- | ------ | ---- | ------------------------------ | ------------- |
| 数据库迁移失败   | 中     | 高   | 先在开发环境测试，准备回滚脚本 | Backend Dev 1 |
| API 性能问题     | 中     | 高   | 增加缓存，优化查询             | Backend Dev 2 |
| 前端组件复杂度高 | 中     | 中   | 组件拆分，增量开发             | Frontend Dev  |
| 测试覆盖不足     | 中     | 高   | 强制单元测试，覆盖率检查       | Tester        |
| 任务间依赖阻塞   | 高     | 中   | 提前识别依赖，准备 Mock 数据   | Team Lead     |

---

## 9. 附录

### 9.1 快速启动命令

```bash
# 启动开发环境
./scripts/start.sh all

# 执行数据库迁移
cd backend && alembic upgrade head

# 运行后端测试
cd backend && pytest

# 运行前端测试
cd frontend && npm run test:unit

# 运行 E2E 测试
cd e2e && npx playwright test
```

### 9.2 参考文档

- [01-PRD.md](./01-PRD.md) - 产品需求文档
- [02-UI-Design.md](./02-UI-Design.md) - UI 设计文档
- [03-Business-Logic.md](./03-Business-Logic.md) - 业务逻辑文档
- [04-Database-Design.md](./04-Database-Design.md) - 数据库设计
- [05-API-Documentation.md](./05-API-Documentation.md) - API 文档
- [06-Technical-Architecture.md](./06-Technical-Architecture.md) - 技术架构

---

*文档版本: v1.0*
*创建日期: 2026-03-14*
*作者: Claude Code*
