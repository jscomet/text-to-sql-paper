# E2E 测试规范 - 高级推理功能模块

## 模块概述

- **模块名称**: 高级推理功能 (Advanced Inference)
- **页面路由**: `/query` (扩展), `/evaluation` (扩展)
- **依赖模块**: Auth, Connection, Query, Evaluation
- **优先级**: P0
- **测试用例数**: 10
- **预计耗时**: 4 小时

## 功能简介

高级推理功能支持三种组合策略：

| 组合策略 | 推理手段 | 评测手段 | 说明 |
|----------|----------|----------|------|
| **vote@k** | Sampling (n=K) | Majority Voting | K次采样后投票选择最佳SQL |
| **pass@k** | Sampling (n=K) | Pass@K | K次采样中任一正确即算成功 |
| **Check-Correct** | Check-Correct | Greedy Search | 迭代修正直到正确或达到最大迭代 |

## 测试环境

### 前置条件

1. 用户已登录
2. 已配置有效的数据库连接
3. 后端 LLM 服务可用
4. 已配置有效的 API Key
5. 测试数据集已准备

### 测试数据

```sql
-- 测试表结构
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2),
    hire_date DATE
);

CREATE TABLE sales (
    id INT PRIMARY KEY,
    product_name VARCHAR(100),
    quantity INT,
    amount DECIMAL(10,2),
    sale_date DATE
);

-- 插入测试数据
INSERT INTO employees VALUES
    (1, '张三', '技术部', 15000.00, '2020-01-15'),
    (2, '李四', '销售部', 12000.00, '2021-03-20'),
    (3, '王五', '技术部', 18000.00, '2019-06-10');

INSERT INTO sales VALUES
    (1, '产品A', 100, 50000.00, '2024-01-15'),
    (2, '产品B', 200, 80000.00, '2024-02-20'),
    (3, '产品C', 150, 60000.00, '2024-03-10');
```

## 测试用例详情

---

### TC-ADV-001: vote@k 推理流程

**优先级**: P0
**测试类型**: 功能测试
**对应功能**: vote@k (Sampling + Majority Voting)

#### 前置条件
- 用户已登录
- 已选择有效数据库连接
- 已配置 LLM API Key

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择数据库连接 | 连接被选中，Schema 加载 | `browser_select_option` |
| 3 | 输入自然语言问题 | 问题显示在输入框 | `browser_type` |
| 4 | 打开高级选项 | 显示推理模式选择 | `browser_click` |
| 5 | 选择"多数投票 (vote@k)"模式 | 模式被选中 | `browser_select_option` |
| 6 | 设置 K=5 | K值显示为5 | `browser_type` |
| 7 | 点击"生成 SQL" | 显示进度指示器 | `browser_click` |
| 8 | 等待生成完成 | 显示候选 SQL 列表 | `browser_wait_for` |
| 9 | 验证投票结果 | 显示最佳 SQL 和投票数 | `browser_snapshot` |
| 10 | 验证置信度分数 | 显示置信度分数 | `browser_snapshot` |

#### 验收标准
- [ ] 可选择 vote@k 推理模式
- [ ] 可配置 K 值 (1-16)
- [ ] 生成过程中显示进度
- [ ] 显示所有候选 SQL 列表
- [ ] 显示每个候选的投票数
- [ ] 高亮显示最佳 SQL
- [ ] 显示置信度分数
- [ ] 响应时间 < 15s (K=8)

#### 截图记录点
- 推理模式选择界面
- 候选 SQL 列表
- 投票结果展示

---

### TC-ADV-002: pass@k 推理流程

**优先级**: P0
**测试类型**: 功能测试
**对应功能**: pass@k (Sampling + Pass@K)

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择数据库连接 | 连接被选中 | `browser_select_option` |
| 3 | 输入测试问题 | 问题显示 | `browser_type` |
| 4 | 打开高级选项 | 显示模式选择 | `browser_click` |
| 5 | 选择"Pass@K"模式 | 模式被选中 | `browser_select_option` |
| 6 | 设置 K=8 | K值显示为8 | `browser_type` |
| 7 | 勾选"返回所有候选" | 选项被勾选 | `browser_click` |
| 8 | 点击"生成 SQL" | 显示进度 | `browser_click` |
| 9 | 等待完成 | 显示候选列表和 Pass@K 分数 | `browser_wait_for` |
| 10 | 验证结果 | 显示 Pass@K 分数和执行结果 | `browser_snapshot` |

#### 验收标准
- [ ] 可选择 pass@k 推理模式
- [ ] 可配置 K 值
- [ ] 可选择是否返回所有候选
- [ ] 显示 Pass@K 分数
- [ ] 显示每个候选的执行状态
- [ ] 标记第一个成功的候选
- [ ] 响应时间 < 15s (K=8)

#### 截图记录点
- Pass@K 配置界面
- 候选执行结果列表
- Pass@K 分数展示

---

### TC-ADV-003: Check-Correct 推理流程

**优先级**: P0
**测试类型**: 功能测试
**对应功能**: Check-Correct (迭代修正)

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择数据库连接 | 连接被选中 | `browser_select_option` |
| 3 | 输入复杂问题 | 问题显示 | `browser_type` |
| 4 | 打开高级选项 | 显示模式选择 | `browser_click` |
| 5 | 选择"Check-Correct"模式 | 模式被选中，显示迭代配置 | `browser_select_option` |
| 6 | 设置最大迭代次数=3 | 显示为3 | `browser_type` |
| 7 | 选择修正策略 | 策略被选中 | `browser_select_option` |
| 8 | 点击"生成 SQL" | 显示进度和迭代状态 | `browser_click` |
| 9 | 等待完成 | 显示最终 SQL 和修正历史 | `browser_wait_for` |
| 10 | 展开修正历史 | 显示每轮迭代详情 | `browser_click` |

#### 验收标准
- [ ] 可选择 Check-Correct 模式
- [ ] 可配置最大迭代次数 (1-5)
- [ ] 可选择修正策略
- [ ] 显示实时迭代进度
- [ ] 显示修正历史时间线
- [ ] 显示每轮的错误类型和修正提示
- [ ] 显示最终迭代次数
- [ ] 响应时间 < 30s (iter=3)

#### 截图记录点
- Check-Correct 配置界面
- 迭代进度显示
- 修正历史时间线

---

### TC-ADV-004: 推理模式切换测试

**优先级**: P0
**测试类型**: 功能测试
**对应功能**: 模式切换和参数联动

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 打开高级选项 | 显示模式选择 | `browser_click` |
| 3 | 选择"单次生成"模式 | 显示基础参数 | `browser_select_option` |
| 4 | 验证参数可见性 | K值和迭代参数隐藏 | `browser_snapshot` |
| 5 | 切换到"Pass@K"模式 | 显示 K值配置 | `browser_select_option` |
| 6 | 验证 K值参数显示 | K值输入框可见 | `browser_snapshot` |
| 7 | 切换到"Check-Correct"模式 | 显示迭代配置 | `browser_select_option` |
| 8 | 验证迭代参数显示 | 迭代次数和策略可见 | `browser_snapshot` |
| 9 | 切换到"多数投票"模式 | 显示 K值配置 | `browser_select_option` |
| 10 | 验证参数联动正确 | 参数正确切换 | `browser_snapshot` |

#### 验收标准
- [ ] 模式切换时参数动态显示/隐藏
- [ ] vote@k/pass@k 显示 K值配置
- [ ] Check-Correct 显示迭代和策略配置
- [ ] 单次生成隐藏高级参数
- [ ] 切换时保留已配置的通用参数
- [ ] 切换时有平滑过渡动画

#### 截图记录点
- 单次生成模式界面
- Pass@K 模式界面
- Check-Correct 模式界面
- 多数投票模式界面

---

### TC-ADV-005: K 值边界测试

**优先级**: P0
**测试类型**: 边界测试
**对应功能**: K值参数验证

#### 测试数据

| K值 | 预期结果 |
|-----|----------|
| 1 | 允许，等效于单次生成 |
| 8 | 允许，常用配置 |
| 16 | 允许，最大值 |
| 0 | 拒绝，提示错误 |
| 17 | 拒绝，提示错误 |

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择 Pass@K 模式 | 模式被选中 | `browser_select_option` |
| 3 | 输入 K=0 | 显示验证错误 | `browser_type` |
| 4 | 验证错误提示 | 提示"K值必须在1-16之间" | `browser_snapshot` |
| 5 | 输入 K=17 | 显示验证错误 | `browser_type` |
| 6 | 验证错误提示 | 提示超出范围 | `browser_snapshot` |
| 7 | 输入 K=1 | 验证通过 | `browser_type` |
| 8 | 执行生成 | 成功执行 | `browser_click` |
| 9 | 输入 K=16 | 验证通过 | `browser_type` |
| 10 | 执行生成 | 成功执行 | `browser_click` |

#### 验收标准
- [ ] K=0 时显示验证错误
- [ ] K=17 时显示验证错误
- [ ] K=1 时允许执行
- [ ] K=16 时允许执行
- [ ] 错误提示清晰明确
- [ ] 边界值处理正确

#### 截图记录点
- K=0 错误提示
- K=17 错误提示
- K=1 成功执行
- K=16 成功执行

---

### TC-ADV-006: 迭代次数边界测试

**优先级**: P0
**测试类型**: 边界测试
**对应功能**: max_iterations 参数验证

#### 测试数据

| 迭代次数 | 预期结果 |
|----------|----------|
| 1 | 允许，最小值 |
| 3 | 允许，常用配置 |
| 5 | 允许，最大值 |
| 0 | 拒绝，提示错误 |
| 6 | 拒绝，提示错误 |

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择 Check-Correct 模式 | 模式被选中 | `browser_select_option` |
| 3 | 输入迭代次数=0 | 显示验证错误 | `browser_type` |
| 4 | 验证错误提示 | 提示"迭代次数必须在1-5之间" | `browser_snapshot` |
| 5 | 输入迭代次数=6 | 显示验证错误 | `browser_type` |
| 6 | 验证错误提示 | 提示超出范围 | `browser_snapshot` |
| 7 | 输入迭代次数=1 | 验证通过 | `browser_type` |
| 8 | 执行生成 | 成功执行 | `browser_click` |
| 9 | 输入迭代次数=5 | 验证通过 | `browser_type` |
| 10 | 执行生成 | 成功执行 | `browser_click` |

#### 验收标准
- [ ] 迭代次数=0 时显示验证错误
- [ ] 迭代次数=6 时显示验证错误
- [ ] 迭代次数=1 时允许执行
- [ ] 迭代次数=5 时允许执行
- [ ] 错误提示清晰明确
- [ ] 边界值处理正确

#### 截图记录点
- 迭代次数=0 错误提示
- 迭代次数=6 错误提示
- 迭代次数=1 成功执行
- 迭代次数=5 成功执行

---

### TC-ADV-007: 错误 SQL 修正流程

**优先级**: P0
**测试类型**: 功能测试
**对应功能**: Check-Correct 错误修正

#### 前置条件
- 使用容易产生错误的问题
- 启用 Check-Correct 模式

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择数据库连接 | 连接被选中 | `browser_select_option` |
| 3 | 输入易错问题 | 问题显示 | `browser_type` |
| 4 | 选择 Check-Correct 模式 | 模式被选中 | `browser_select_option` |
| 5 | 设置迭代次数=3 | 显示为3 | `browser_type` |
| 6 | 点击"生成 SQL" | 开始生成 | `browser_click` |
| 7 | 观察第一轮 | 显示初始 SQL | `browser_wait_for` |
| 8 | 观察修正过程 | 显示错误检测和修正 | `browser_wait_for` |
| 9 | 等待完成 | 显示最终 SQL | `browser_wait_for` |
| 10 | 查看修正历史 | 显示每轮错误和修正 | `browser_click` |

#### 验收标准
- [ ] 检测初始 SQL 错误
- [ ] 显示错误类型分类
- [ ] 显示修正提示
- [ ] 记录每轮迭代结果
- [ ] 最终 SQL 可执行
- [ ] 修正历史完整可追溯

#### 截图记录点
- 初始错误 SQL
- 修正过程状态
- 最终正确 SQL
- 修正历史详情

---

### TC-ADV-008: 并发任务测试

**优先级**: P1
**测试类型**: 性能测试
**对应功能**: 多任务并发执行

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 打开浏览器标签页2 | 新标签页打开 | `browser_tabs` |
| 3 | 在标签页1启动 Pass@K 任务 | 任务开始执行 | `browser_click` |
| 4 | 在标签页2启动 vote@k 任务 | 任务开始执行 | `browser_click` |
| 5 | 观察标签页1 | 进度正常更新 | `browser_wait_for` |
| 6 | 观察标签页2 | 进度正常更新 | `browser_wait_for` |
| 7 | 等待任务1完成 | 显示结果 | `browser_wait_for` |
| 8 | 等待任务2完成 | 显示结果 | `browser_wait_for` |
| 9 | 验证两个结果 | 结果正确 | `browser_snapshot` |
| 10 | 检查系统状态 | 系统稳定 | `browser_snapshot` |

#### 验收标准
- [ ] 支持至少 2 个并发任务
- [ ] 并发任务进度独立更新
- [ ] 并发任务结果正确
- [ ] 系统资源使用正常
- [ ] 无任务互相干扰
- [ ] 响应时间在可接受范围

#### 截图记录点
- 并发任务执行中
- 任务1完成结果
- 任务2完成结果

---

### TC-ADV-009: WebSocket 进度推送测试

**优先级**: P1
**测试类型**: 功能测试
**对应功能**: 实时进度推送

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择 Pass@K 模式 (K=8) | 模式被选中 | `browser_select_option` |
| 3 | 输入测试问题 | 问题显示 | `browser_type` |
| 4 | 打开浏览器开发者工具 | 显示 Network 面板 | - |
| 5 | 点击"生成 SQL" | 开始生成 | `browser_click` |
| 6 | 观察 WebSocket 连接 | 建立 WebSocket 连接 | `browser_wait_for` |
| 7 | 观察进度消息 | 接收进度更新消息 | `browser_wait_for` |
| 8 | 验证进度准确性 | 进度值正确递增 | `browser_snapshot` |
| 9 | 等待完成 | 接收完成消息 | `browser_wait_for` |
| 10 | 验证 WebSocket 关闭 | 连接正常关闭 | `browser_wait_for` |

#### 验收标准
- [ ] WebSocket 连接成功建立
- [ ] 实时接收进度更新
- [ ] 进度值准确反映执行状态
- [ ] 候选生成时显示详细进度
- [ ] 完成时接收完成消息
- [ ] 连接正常关闭无泄漏
- [ ] 网络中断时有降级处理

#### 截图记录点
- WebSocket 连接建立
- 进度消息接收
- 完成消息接收

---

### TC-ADV-010: 超时处理测试

**优先级**: P1
**测试类型**: 异常测试
**对应功能**: 超时机制

#### 测试步骤

| 步骤 | 操作 | 预期结果 | MCP Playwright 工具 |
|------|------|----------|---------------------|
| 1 | 访问查询页面 | 显示查询界面 | `browser_navigate` |
| 2 | 选择 Check-Correct 模式 | 模式被选中 | `browser_select_option` |
| 3 | 设置较大迭代次数 | 迭代次数=5 | `browser_type` |
| 4 | 输入复杂问题 | 问题显示 | `browser_type` |
| 5 | 点击"生成 SQL" | 开始生成 | `browser_click` |
| 6 | 模拟网络延迟/等待 | 任务执行中 | `browser_wait_for` |
| 7 | 观察超时处理 | 显示超时提示或部分结果 | `browser_wait_for` |
| 8 | 验证错误处理 | 显示友好的超时提示 | `browser_snapshot` |
| 9 | 验证恢复机制 | 可重新发起请求 | `browser_click` |
| 10 | 重新执行 | 新任务正常执行 | `browser_click` |

#### 验收标准
- [ ] 超时有明确提示
- [ ] 显示部分结果（如有）
- [ ] 提供重试选项
- [ ] 超时后系统状态正常
- [ ] 可立即重新发起请求
- [ ] 超时时间可配置（如支持）

#### 截图记录点
- 任务执行中
- 超时提示
- 重试界面

---

## 测试数据

### 高级推理测试数据

```typescript
// e2e/fixtures/test-data.ts
export const advancedInferenceTestData = {
  reasoningModes: [
    {
      id: 'single',
      name: '单次生成',
      description: '单次确定性生成',
      params: []
    },
    {
      id: 'pass_at_k',
      name: 'Pass@K',
      description: 'K次采样，返回第一个正确结果',
      params: ['k_candidates']
    },
    {
      id: 'majority_vote',
      name: '多数投票',
      description: 'K次采样，投票选择最佳结果',
      params: ['k_candidates']
    },
    {
      id: 'check_correct',
      name: 'Check-Correct',
      description: '迭代修正直到正确',
      params: ['max_iterations', 'correction_strategy']
    }
  ],
  correctionStrategies: [
    { id: 'self_correction', name: '自我修正' },
    { id: 'execution_feedback', name: '执行反馈修正' },
    { id: 'multi_agent', name: '多代理协作' }
  ],
  testQuestions: {
    simple: '查询所有员工',
    moderate: '查询每个部门的平均工资',
    complex: '查询2024年销售额最高的前3个产品及其对应的销售人员',
    errorProne: '查询每个部门的员工数量和总工资，按总工资降序排列'
  },
  boundaryValues: {
    k: { min: 1, max: 16, invalid: [0, 17] },
    iterations: { min: 1, max: 5, invalid: [0, 6] }
  }
};
```

## 报告模板

### TC-ADV-xxx 测试报告模板

```markdown
# TC-ADV-xxx: [测试用例名称] - 测试报告

## 执行信息

| 项目 | 内容 |
|------|------|
| 测试用例 | TC-ADV-xxx |
| 执行人 | test-e2e |
| 执行日期 | YYYY-MM-DD |
| 执行环境 | localhost |
| 浏览器 | Chrome 120 |

## 执行结果

| 步骤 | 操作 | 预期结果 | 实际结果 | 状态 | 截图 |
|------|------|----------|----------|------|------|
| 1 | ... | ... | ... | ✅/❌ | xxx.png |

## 问题记录

### 问题 #1 (如有)

**描述**: ...
**严重程度**: P0/P1/P2
**复现步骤**: ...
**期望结果**: ...
**实际结果**: ...
**截图**: xxx.png

## 结论

- [ ] 测试通过
- [ ] 测试失败，需修复
- [ ] 部分通过

## 附件

- 截图目录: ./screenshots/
```

## 相关文档

- [高级推理功能 - 业务逻辑](../feat/advanced-inference/Business-Logic.md)
- [高级推理功能 - API 文档](../feat/advanced-inference/API-Documentation.md)
- [高级推理功能 - 技术设计](../feat/advanced-inference/Technical-Design.md)
- [E2E 测试总计划](./00-E2E-Master-Plan.md)

---

*文档版本: v1.0*
*创建日期: 2026-03-13*
*更新日期: 2026-03-13*
