# 文档目录

本文档目录包含 Text-to-SQL Prototype 项目的所有技术文档、设计文档和用户指南。

## 主文档

### 核心设计文档

| 文档 | 说明 | 路径 |
|------|------|------|
| **01-PRD.md** | 产品需求文档 - 功能需求、用户故事、验收标准 | [01-PRD.md](./01-PRD.md) |
| **02-UI-Design.md** | UI 设计文档 - 界面原型、交互设计、视觉规范 | [02-UI-Design.md](./02-UI-Design.md) |
| **03-Business-Logic.md** | 业务逻辑文档 - 核心业务规则、流程定义 | [03-Business-Logic.md](./03-Business-Logic.md) |
| **04-Database-Design.md** | 数据库设计文档 - ER图、表结构、索引设计 | [04-Database-Design.md](./04-Database-Design.md) |
| **05-API-Documentation.md** | API 接口文档 - RESTful API 定义、请求响应格式 | [05-API-Documentation.md](./05-API-Documentation.md) |
| **06-Technical-Architecture.md** | 技术架构文档 - 系统架构、技术选型、部署方案 | [06-Technical-Architecture.md](./06-Technical-Architecture.md) |
| **07-README-Deployment.md** | 部署指南 - 环境配置、部署步骤、运维手册 | [07-README-Deployment.md](./07-README-Deployment.md) |

### 高级推理功能文档

| 文档 | 说明 | 路径 |
|------|------|------|
| **08-Advanced-Inference-Design.md** | 高级推理技术设计 - 架构设计、算法实现、核心组件 | [08-Advanced-Inference-Design.md](./08-Advanced-Inference-Design.md) |
| **09-Advanced-Inference-Guide.md** | 高级推理用户指南 - 功能介绍、使用说明、最佳实践 | [09-Advanced-Inference-Guide.md](./09-Advanced-Inference-Guide.md) |

---

## 子目录

### 📁 report/ - 项目报告

存放项目各阶段的执行报告、完成报告和分析报告。

#### 阶段报告

| 阶段 | 说明 | 路径 |
|------|------|------|
| **Phase 1** | 项目初始化报告 - 后端/前端初始化、Git配置 | [01-Phase1-Setup/](./report/01-Phase1-Setup/) |
| **Phase 2** | 后端基础报告 - 数据库模型、认证系统、核心基础设施 | [02-Phase2-Backend/](./report/02-Phase2-Backend/) |
| **Phase 3** | 核心功能报告 - 连接管理、Text-to-SQL、评测系统 | [03-Phase3-Core/](./report/03-Phase3-Core/) |
| **Phase 4** | 前端基础报告 - 前端框架、组件库、状态管理 | [04-Phase4-Frontend-Foundation/](./report/04-Phase4-Frontend/) |
| **Phase 5** | 前端页面报告 - 业务页面实现 | [05-Phase5-Frontend-Pages/](./report/05-Phase5-Frontend/) |
| **Phase 6** | 测试阶段报告 - E2E测试、回归测试 | [06-Phase6-Testing/](./report/06-Phase6-E2E-Full-Report.md) |

#### 高级推理功能报告

| 文档 | 说明 | 路径 |
|------|------|------|
| **advanced-inference-completion-report.md** | 项目完成报告 - 高级推理功能整体完成情况 | [advanced-inference-completion-report.md](./report/advanced-inference-completion-report.md) |
| **advanced-inference-agent-execution.md** | Agent执行总结 - 各Agent任务执行情况 | [advanced-inference-agent-execution.md](./report/advanced-inference-agent-execution.md) |
| **advanced-inference-agent-workflow.md** | 工作流程分析 - Agent Team协作流程与效果 | [advanced-inference-agent-workflow.md](./report/advanced-inference-agent-workflow.md) |
| **advanced-inference-release-checklist.md** | 发布检查清单 - 功能验证、测试通过情况 | [advanced-inference-release-checklist.md](./report/advanced-inference-release-checklist.md) |

[查看完整报告目录](./report/README.md)

---

### 📁 plan/ - 项目计划

存放项目各阶段的详细计划和任务分解。

[查看计划目录](./plan/)

---

### 📁 tasks/ - 任务定义

存放可复用的任务定义模板。

[查看任务目录](./tasks/)

---

### 📁 agent-team-best-practices/ - Agent Team 最佳实践

存放 Agent Team 协作的最佳实践和模式总结。

[查看最佳实践目录](./agent-team-best-practices/)

---

## 文档命名规范

### 主文档命名

格式：`{序号}-{文档名称}.md`

示例：
- `01-PRD.md`
- `08-Advanced-Inference-Design.md`

### 报告文档命名

格式：`{主题}-{类型}.md`

示例：
- `advanced-inference-completion-report.md`
- `06-Phase6-E2E-Full-Report.md`

---

## 文档维护

### 新增文档流程

1. 根据文档类型选择合适目录
2. 按照命名规范创建文件
3. 更新本 README.md 添加索引链接
4. 提交代码时包含文档更新

### 文档更新规范

- 修改文档时同步更新版本号和日期
- 重大变更需在文档顶部添加变更说明
- 保持文档间的交叉引用链接有效

---

## 快速导航

### 按角色导航

| 角色 | 推荐文档 |
|------|----------|
| **产品经理** | 01-PRD.md, 03-Business-Logic.md |
| **UI/UX 设计师** | 02-UI-Design.md |
| **后端开发** | 04-Database-Design.md, 05-API-Documentation.md, 06-Technical-Architecture.md, 08-Advanced-Inference-Design.md |
| **前端开发** | 02-UI-Design.md, 05-API-Documentation.md |
| **测试工程师** | 01-PRD.md, report/ 目录下的测试报告 |
| **运维工程师** | 07-README-Deployment.md, 06-Technical-Architecture.md |
| **用户/客户** | 09-Advanced-Inference-Guide.md |

### 按功能导航

| 功能 | 相关文档 |
|------|----------|
| **认证系统** | 03-Business-Logic.md, 05-API-Documentation.md |
| **连接管理** | 03-Business-Logic.md, 04-Database-Design.md |
| **Text-to-SQL** | 03-Business-Logic.md, 08-Advanced-Inference-Design.md |
| **评测系统** | 03-Business-Logic.md, 08-Advanced-Inference-Design.md |
| **高级推理** | 08-Advanced-Inference-Design.md, 09-Advanced-Inference-Guide.md |
