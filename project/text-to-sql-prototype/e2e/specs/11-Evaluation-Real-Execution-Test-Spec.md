# E2E 测试规范 - 评测真实执行验证

## 模块概述

- **模块名称**: 评测真实执行验证
- **页面路由**: `/evaluation`
- **依赖模块**: Auth, Connection, ICED Dataset Import
- **优先级**: P0
- **测试用例数**: 3
- **预计耗时**: 15 分钟

## 测试目标

验证评测任务能够真正执行推理流程：
1. 清空现有评测任务
2. 创建一个小型、可快速验证的评测任务
3. 验证评测任务真正执行了 LLM 推理
4. 验证评测结果被正确记录

## 测试环境

### 前置条件

1. 用户已登录
2. ICED 数据集已导入（至少有一个数据库连接可用）
3. API Key 已配置
4. 服务运行中

### 测试数据

使用 `debit_card_specializing` 数据库（64 条记录，数据量最小）：
- 数据库: `debit_card_specializing`
- 连接名称: `BIRD - debit_card_specializing`
- 问题数: 64（执行速度快，易于验证）

## 测试用例详情

### TC-EVAL-REAL-001: 清空现有评测任务

**优先级**: P0
**测试类型**: 功能测试
**页面**: `/evaluation`

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 访问评测管理页 | 显示评测列表 | `browser_navigate` |
| 2 | 检查现有任务数量 | 记录当前任务数 | `browser_snapshot` |
| 3 | 逐个删除所有任务 | 每个任务删除成功 | `browser_click` + `browser_handle_dialog` |
| 4 | 验证列表为空 | 显示"暂无评测任务" | `browser_snapshot` |
| 5 | 截图记录 | 保存空列表截图 | `browser_take_screenshot` |

#### 验收标准
- [ ] 能够访问评测列表页
- [ ] 能够删除所有现有评测任务
- [ ] 评测列表显示为空状态

#### 验证点
```javascript
// 验证评测列表为空
const evalCards = document.querySelectorAll('.eval-card');
expect(evalCards.length).toBe(0);
```

---

### TC-EVAL-REAL-002: 创建小型验证评测任务

**优先级**: P0
**测试类型**: 功能测试
**页面**: `/evaluation`

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 访问评测管理页 | 显示空评测列表 | `browser_navigate` |
| 2 | 点击"+ 新建评测" | 弹出创建弹窗 | `browser_click` |
| 3 | 输入任务名称 | 名称显示为 "E2E验证-debit_card" | `browser_type` |
| 4 | 选择数据集 | 选择 `bird_dev.json` | `browser_select_option` |
| 5 | 选择数据库连接 | 选择 `BIRD - debit_card_specializing` | `browser_select_option` |
| 6 | 选择模型 | 选择已配置的模型 | `browser_select_option` |
| 7 | 选择评测模式 | 选择 `greedy_search` | `browser_click` |
| 8 | 配置温度参数 | 设置为 0.1 | `browser_type` |
| 9 | 点击"开始评测" | 创建成功，跳转详情页 | `browser_click` |
| 10 | 截图记录 | 保存创建成功截图 | `browser_take_screenshot` |

#### 验收标准
- [ ] 评测任务创建成功
- [ ] 页面跳转到评测详情页
- [ ] 任务状态显示为 "pending"
- [ ] 显示正确的数据集和数据库信息
- [ ] 显示配置参数（temperature=0.1, mode=greedy）

#### 预期创建的评测任务
| 字段 | 值 |
|------|-----|
| 任务名称 | E2E验证-debit_card |
| 数据集 | bird_dev.json |
| 数据库 | debit_card_specializing |
| 评测模式 | greedy_search |
| 温度参数 | 0.1 |
| 预期问题数 | 64 |

---

### TC-EVAL-REAL-003: 验证评测真正执行推理

**优先级**: P0
**测试类型**: 核心功能测试
**页面**: `/evaluation/{task_id}`

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP 工具 |
|------|------|----------|----------|
| 1 | 在详情页点击"开始评测" | 评测启动 | `browser_click` |
| 2 | 验证状态变为 running | 状态更新 | `browser_wait_for` |
| 3 | 验证进度显示 | 显示进度条和百分比 | `browser_snapshot` |
| 4 | 等待 60-120 秒 | 评测执行中 | `browser_wait_for` (time=60) |
| 5 | 验证进度更新 | 已处理数量 > 0 | `browser_snapshot` |
| 6 | 等待评测完成（最多5分钟） | 状态变为 completed | `browser_wait_for` (text="completed") |
| 7 | 验证结果统计 | 显示 EX 分数、正确/错误数 | `browser_snapshot` |
| 8 | 查看评测结果列表 | 显示每个问题的预测 SQL | `browser_click` |
| 9 | 展开单个结果 | 显示问题、预测 SQL、黄金 SQL | `browser_click` |
| 10 | 验证预测 SQL 非空 | 预测 SQL 有内容 | `browser_evaluate` |
| 11 | 验证执行结果 | 显示执行结果匹配/不匹配 | `browser_snapshot` |
| 12 | 截图记录 | 保存结果详情截图 | `browser_take_screenshot` |

#### 验收标准
- [ ] 评测任务能够正常启动
- [ ] 状态从 pending → running → completed 正确流转
- [ ] 进度条实时更新
- [ ] 已处理问题数逐渐增加
- [ ] 评测完成后显示 EX 准确率分数
- [ ] 评测结果中包含预测的 SQL（非空）
- [ ] 评测结果中包含执行结果对比
- [ ] 正确数和错误数之和等于总问题数（64）

#### 关键验证点

**1. 验证推理真正执行**
```javascript
// 检查评测结果中是否有预测 SQL
const predSql = document.querySelector('.pred-sql').textContent;
expect(predSql).not.toBeEmpty();
expect(predSql).not.toBe('');
expect(predSql.toLowerCase()).toContain('select'); // 预测 SQL 应该包含 SELECT
```

**2. 验证状态流转**
```javascript
// 状态应该依次为: pending -> running -> completed
const statusFlow = ['pending', 'running', 'completed'];
```

**3. 验证结果统计**
```javascript
// 总问题数应该为 64
const totalQuestions = 64;
const correctCount + errorCount === totalQuestions;
```

**4. 验证 LLM 调用**
```javascript
// 通过检查预测 SQL 的内容来验证 LLM 被调用
// 预测 SQL 应该是有效的 SQL 语句，不是空的
```

#### API 验证（可选）

通过 API 验证评测结果：
```bash
# 获取评测任务详情
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/eval/tasks/{task_id}

# 验证响应包含：
# - status: "completed"
# - total_questions: 64
# - processed_count: 64
# - correct_count: >= 0
# - accuracy: >= 0

# 获取评测结果列表
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/eval/tasks/{task_id}/results

# 验证响应包含：
# - list[].pred_sql: 非空的预测 SQL
# - list[].is_correct: true/false
# - list[].execution_result: 执行结果
```

---

## 报告模板

```markdown
# 评测真实执行验证 E2E 测试报告

**执行日期**: YYYY-MM-DD
**执行人**: e2e-lead
**总用例数**: 3
**通过**: X
**失败**: X
**通过率**: XX%

## 摘要

[测试执行摘要，是否验证了真实推理]

## 详细结果

| 用例ID | 名称 | 结果 | 耗时 | 备注 |
|--------|------|------|------|------|
| TC-EVAL-REAL-001 | 清空现有评测任务 | - | - | - |
| TC-EVAL-REAL-002 | 创建小型验证评测任务 | - | - | - |
| TC-EVAL-REAL-003 | 验证评测真正执行推理 | - | - | - |

## 关键验证结果

### 评测执行验证
- [ ] 评测任务 ID: {task_id}
- [ ] 数据库: debit_card_specializing
- [ ] 问题数: 64
- [ ] 实际执行时间: {seconds} 秒
- [ ] 最终状态: completed
- [ ] EX 准确率: {accuracy}%

### LLM 推理验证
- [ ] 预测 SQL 非空: ✅/❌
- [ ] 预测 SQL 有效: ✅/❌
- [ ] 执行结果被记录: ✅/❌

## 问题记录

[如有]
```

---

*文档版本: v1.0*
*更新日期: 2026-03-13*
