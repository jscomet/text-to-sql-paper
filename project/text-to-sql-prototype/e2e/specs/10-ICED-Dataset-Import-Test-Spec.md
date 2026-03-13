# E2E 测试规范 - ICED 数据集导入验证

## 模块概述

- **模块名称**: ICED 数据集导入验证
- **页面路由**: `/connections`, `/evaluation`
- **依赖模块**: Auth, Connection, Evaluation
- **优先级**: P0
- **测试用例数**: 6
- **预计耗时**: 35 分钟

## 测试环境

### 前置条件

1. 用户已登录
2. ICED 数据集导入已完成（11 个连接 + 11 个评测任务）
3. API Key 已配置
4. 服务运行中

### 测试数据

已导入的 BIRD 数据集：
- 数据集文件: `bird_dev.json` (1534 条数据)
- 数据库: 11 个 SQLite 数据库
- 连接: 11 个 (connection_id: 10-20)
- 评测任务: 11 个 (task_id: 8-18)

## 测试用例详情

### TC-ICED-001: BIRD 数据库连接列表验证

**优先级**: P0
**测试类型**: UI 验证
**页面**: `/connections`

#### 前置条件
- 用户已登录
- ICED 数据集导入已完成

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 访问连接管理页 | 显示连接列表 | `browser_navigate` |
| 2 | 验证 BIRD 连接存在 | 显示 11 个 BIRD 连接 | `browser_snapshot` |
| 3 | 验证连接名称 | 显示 "BIRD - {db_id}" 格式 | `browser_evaluate` |
| 4 | 验证连接状态 | 所有连接状态为 "active" | `browser_snapshot` |
| 5 | 截图记录 | 保存连接列表截图 | `browser_take_screenshot` |

#### 验收标准
- [ ] 页面显示 11 个 BIRD 数据库连接
- [ ] 连接名称格式正确
- [ ] 连接类型显示为 "sqlite"
- [ ] 连接状态显示为 "active"

#### 预期连接列表
| db_id | 预期显示名称 |
|-------|-------------|
| california_schools | BIRD - california_schools |
| card_games | BIRD - card_games |
| codebase_community | BIRD - codebase_community |
| debit_card_specializing | BIRD - debit_card_specializing |
| european_football_2 | BIRD - european_football_2 |
| financial | BIRD - financial |
| formula_1 | BIRD - formula_1 |
| student_club | BIRD - student_club |
| superhero | BIRD - superhero |
| thrombosis_prediction | BIRD - thrombosis_prediction |
| toxicology | BIRD - toxicology |

---

### TC-ICED-002: BIRD 数据库 Schema 验证

**优先级**: P1
**测试类型**: 功能测试
**页面**: `/connections/{id}`

#### 前置条件
- TC-ICED-001 通过

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 点击 california_schools 连接 | 跳转连接详情 | `browser_click` |
| 2 | 等待 Schema 加载 | 显示表结构 | `browser_wait_for` |
| 3 | 验证表存在 | 显示数据库表列表 | `browser_snapshot` |
| 4 | 展开一个表 | 显示字段详情 | `browser_click` |
| 5 | 截图记录 | 保存 Schema 截图 | `browser_take_screenshot` |

#### 验收标准
- [ ] 连接详情页正确加载
- [ ] Schema 已刷新（非空）
- [ ] 显示数据库表列表
- [ ] 显示表字段详情

---

### TC-ICED-003: BIRD 评测任务列表验证

**优先级**: P0
**测试类型**: UI 验证
**页面**: `/evaluation`

#### 前置条件
- 用户已登录
- 11 个评测任务已创建

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 访问评测管理页 | 显示评测列表 | `browser_navigate` |
| 2 | 验证 BIRD 任务存在 | 显示 11 个 BIRD 评测任务 | `browser_snapshot` |
| 3 | 验证任务名称 | 显示 "BIRD Dev - {db_id}" 格式 | `browser_evaluate` |
| 4 | 验证任务状态 | 显示为 "pending" 或 "completed" | `browser_snapshot` |
| 5 | 截图记录 | 保存任务列表截图 | `browser_take_screenshot` |

#### 验收标准
- [ ] 页面显示 11 个 BIRD 评测任务
- [ ] 任务名称格式正确
- [ ] 数据集类型显示为 "bird"

---

### TC-ICED-004: 评测任务详情查看

**优先级**: P1
**测试类型**: 功能测试
**页面**: `/evaluation/{id}`

#### 前置条件
- TC-ICED-003 通过

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 点击第一个 BIRD 任务 | 跳转任务详情 | `browser_click` |
| 2 | 验证配置信息 | 显示数据集、模型配置 | `browser_snapshot` |
| 3 | 验证数据文件路径 | 显示 bird_dev.json 路径 | `browser_evaluate` |
| 4 | 验证评测模式 | 显示 greedy_search 模式 | `browser_snapshot` |
| 5 | 截图记录 | 保存详情页截图 | `browser_take_screenshot` |

#### 验收标准
- [ ] 显示评测任务配置
- [ ] 数据集路径指向 bird_dev.json
- [ ] 显示连接信息
- [ ] 显示评测模式

---

### TC-ICED-005: 评测任务启动执行

**优先级**: P0
**测试类型**: 功能测试
**页面**: `/evaluation/{id}`

#### 前置条件
- TC-ICED-004 通过
- 已配置有效的 API Key

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 选择一个 pending 状态任务 | 详情页显示 | - |
| 2 | 点击"开始评测"按钮 | 开始执行 | `browser_click` |
| 3 | 验证状态变化 | 状态变为 running | `browser_wait_for` |
| 4 | 验证进度显示 | 显示进度条 | `browser_snapshot` |
| 5 | 等待 30 秒 | 进度更新 | `browser_wait_for` (time=30) |
| 6 | 截图记录 | 保存执行中截图 | `browser_take_screenshot` |
| 7 | 点击取消 | 取消评测 | `browser_click` |

#### 验收标准
- [ ] 可以启动评测任务
- [ ] 状态正确更新为 running
- [ ] 显示进度条和百分比
- [ ] 已处理数量正确增加
- [ ] 可以取消评测

---

### TC-ICED-006: 数据集数据量验证

**优先级**: P1
**测试类型**: API 验证

#### 前置条件
- 评测任务已创建

#### 测试步骤

使用 API 验证数据量：
```bash
# 获取任务详情并验证 total_questions
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/eval/tasks/{task_id}
```

#### 预期结果
| db_id | 预期问题数 |
|-------|----------|
| california_schools | 89 |
| card_games | 191 |
| codebase_community | 186 |
| debit_card_specializing | 64 |
| european_football_2 | 129 |
| financial | 106 |
| formula_1 | 174 |
| student_club | 158 |
| superhero | 129 |
| thrombosis_prediction | 163 |
| toxicology | 145 |
| **总计** | **1534** |

#### 验收标准
- [ ] 每个任务的问题数与预期一致
- [ ] 总问题数为 1534 条

## 报告模板

```markdown
# ICED 数据集导入 E2E 测试报告

**执行日期**: YYYY-MM-DD
**执行人**: e2e-lead
**总用例数**: 6
**通过**: X
**失败**: X
**通过率**: XX%

## 摘要

[测试执行摘要]

## 详细结果

| 用例ID | 名称 | 结果 | 耗时 | 截图 |
|--------|------|------|------|------|
| TC-ICED-001 | 连接列表验证 | - | - | - |
| TC-ICED-002 | Schema 验证 | - | - | - |
| TC-ICED-003 | 评测任务列表验证 | - | - | - |
| TC-ICED-004 | 评测详情查看 | - | - | - |
| TC-ICED-005 | 评测任务启动 | - | - | - |
| TC-ICED-006 | 数据量验证 | - | - | - |

## 发现问题

[如有]

## 建议

[如有]
```

---

*文档版本: v1.0*
*更新日期: 2026-03-13*
