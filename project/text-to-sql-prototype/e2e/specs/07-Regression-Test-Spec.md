# E2E 测试规范 - 回归测试套件

## 概述

回归测试用于验证 Bug 修复、代码变更后系统的稳定性，确保新改动没有破坏原有功能。

## 触发条件

1. Bug 修复完成后
2. 代码合并到 main 分支前
3. 发布新版本前
4. 每日定时执行（可选）

## 回归测试范围

### P0 级回归（核心功能）

每次回归必须执行，约 30 分钟。

| 模块 | 用例数 | 关键用例 |
|------|--------|----------|
| Auth | 5 | TC-AUTH-001, 002, 003, 006, 007 |
| Connection | 5 | TC-CONN-001, 004, 005, 007, 008 |
| Query | 8 | TC-QUERY-001, 004, 006, 008, 009, 011, 014, 019 |

### P1 级回归（重要功能）

发布前执行，约 1 小时。

| 模块 | 用例数 | 说明 |
|------|--------|------|
| Auth | 3 | TC-AUTH-004, 005, 011 |
| Connection | 5 | TC-CONN-002, 003, 009, 010, 013 |
| Query | 5 | TC-QUERY-003, 005, 007, 012, 020 |
| History | 5 | TC-HIST-001, 002, 005, 006, 007 |
| Evaluation | 3 | TC-EVAL-001, 002, 005 |
| Settings | 3 | TC-SET-001, 003, 006 |
| Advanced Inference | 3 | TC-ADV-001, 002, 003 |

## 回归测试流程

### 1. 冒烟测试（5分钟）

```markdown
## 冒烟测试清单

- [ ] 应用可正常访问
- [ ] 登录功能正常
- [ ] 创建连接成功
- [ ] 执行简单查询
- [ ] 页面无 JavaScript 错误
```

### 2. P0 核心回归（30分钟）

#### Auth 模块

```markdown
## Auth P0 回归

### TC-AUTH-001: 正常登录
- [ ] 访问登录页
- [ ] 输入有效凭证
- [ ] 登录成功跳转
- [ ] 截图记录

### TC-AUTH-002: 表单验证
- [ ] 空值验证
- [ ] 错误提示显示

### TC-AUTH-003: 错误密码
- [ ] 输入错误密码
- [ ] 错误提示正确
- [ ] 页面不跳转

### TC-AUTH-006: 登出功能
- [ ] 点击用户菜单
- [ ] 确认登出
- [ ] 跳转登录页

### TC-AUTH-007: 注册流程
- [ ] 切换到注册
- [ ] 填写新用户
- [ ] 注册成功登录
```

#### Connection 模块

```markdown
## Connection P0 回归

### TC-CONN-001: 创建 MySQL 连接
- [ ] 打开新建弹窗
- [ ] 填写连接信息
- [ ] 测试连接成功
- [ ] 保存连接

### TC-CONN-004: 测试连接成功
- [ ] 填写有效信息
- [ ] 点击测试
- [ ] 显示成功提示

### TC-CONN-005: 测试连接失败
- [ ] 填写无效主机
- [ ] 点击测试
- [ ] 显示错误提示

### TC-CONN-007: 编辑连接
- [ ] 点击编辑
- [ ] 修改信息
- [ ] 保存更新

### TC-CONN-008: 删除连接
- [ ] 点击删除
- [ ] 确认删除
- [ ] 从列表移除
```

#### Query 模块

```markdown
## Query P0 回归

### TC-QUERY-001: 选择数据库
- [ ] 访问查询页
- [ ] 选择连接
- [ ] Schema 加载

### TC-QUERY-004: SQL 生成
- [ ] 输入问题
- [ ] 生成 SQL
- [ ] SQL 正确显示

### TC-QUERY-006: SQL 执行成功
- [ ] 点击执行
- [ ] 结果显示
- [ ] 元信息正确

### TC-QUERY-008: SQL 执行结果
- [ ] 结果表格显示
- [ ] 数据正确
- [ ] 分页正常

### TC-QUERY-009: SQL 执行错误
- [ ] 执行错误 SQL
- [ ] 错误提示显示
- [ ] 不崩溃

### TC-QUERY-011: 结果展示
- [ ] 表格格式
- [ ] 列宽调整
- [ ] 排序功能

### TC-QUERY-014: 多轮对话
- [ ] 第一轮查询
- [ ] 追问
- [ ] 上下文关联

### TC-QUERY-019: 历史保存
- [ ] 执行查询
- [ ] 查看历史
- [ ] 记录存在
```

### 3. P1 扩展回归（30分钟）

根据时间和变更范围选择性执行。

#### Advanced Inference 模块

```markdown
## Advanced Inference P1 回归

### TC-ADV-001: vote@k 推理流程
- [ ] 选择 vote@k 模式
- [ ] 配置 K=5
- [ ] 生成 SQL
- [ ] 验证候选列表
- [ ] 验证投票结果

### TC-ADV-002: pass@k 推理流程
- [ ] 选择 pass@k 模式
- [ ] 配置 K=8
- [ ] 生成 SQL
- [ ] 验证 Pass@K 分数
- [ ] 验证候选执行结果

### TC-ADV-003: Check-Correct 推理流程
- [ ] 选择 Check-Correct 模式
- [ ] 配置迭代次数=3
- [ ] 生成 SQL
- [ ] 验证修正历史
- [ ] 验证最终 SQL
```

#### 向后兼容性回归

```markdown
## 向后兼容性回归

### 现有 API 兼容性
- [ ] 原有 /generate API 正常工作
- [ ] 原有评测任务创建正常工作
- [ ] 单次生成模式行为不变
- [ ] 现有数据库连接正常

### 数据兼容性
- [ ] 历史评测记录可正常查看
- [ ] 旧格式数据正确显示
- [ ] 新字段默认值正确
```

## 回归测试报告模板

```markdown
# 回归测试报告

**执行日期**: YYYY-MM-DD
**执行人**: [test-lead 名称]
**触发原因**: Bug修复/代码合并/发布前
**测试范围**: P0/P1/全量

## 执行摘要

| 指标 | 数值 |
|------|------|
| 总用例数 | XX |
| 通过 | XX |
| 失败 | XX |
| 跳过 | XX |
| 通过率 | XX% |
| 耗时 | XX分钟 |

## 执行结果

### Auth 模块

| 用例 | 结果 | 截图 | 备注 |
|------|------|------|------|
| TC-AUTH-001 | ✅ | auth-001.png | - |
| TC-AUTH-002 | ❌ | auth-002.png | 见问题 #1 |

### Connection 模块

| 用例 | 结果 | 截图 | 备注 |
|------|------|------|------|
| TC-CONN-001 | ✅ | conn-001.png | - |

## 发现的问题

### 问题 #1

**用例**: TC-AUTH-002
**严重程度**: P0/P1/P2
**描述**: [问题描述]
**复现步骤**:
1. [步骤1]
2. [步骤2]

**期望结果**: [期望]
**实际结果**: [实际]
**截图**: [文件名]

## 结论

- [ ] 回归测试通过，可继续发布
- [ ] 回归测试失败，需修复后重测
- [ ] 部分通过，P0 通过可继续

## 附件

- [截图目录](./screenshots/)
- [详细日志](./logs/)
```

## 自动化回归（可选）

### Playwright 脚本示例

```typescript
// e2e/specs/regression/smoke.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Smoke Test', () => {
  test('应用可访问', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await expect(page).toHaveTitle(/Text2SQL/);
  });

  test('登录功能', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'Test@123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('创建连接', async ({ page }) => {
    // 登录
    await login(page);

    // 创建连接
    await page.goto('http://localhost:5173/connections');
    await page.click('text=新建连接');
    await page.fill('[name="name"]', 'Test-MySQL');
    await page.selectOption('[name="type"]', 'mysql');
    await page.fill('[name="host"]', 'localhost');
    await page.click('text=测试连接');
    await expect(page.locator('text=连接成功')).toBeVisible();
  });
});
```

## 回归测试检查清单

### 环境准备

- [ ] 前后端服务已启动
- [ ] 使用干净的数据库
- [ ] 测试账号可用
- [ ] 测试数据已准备

### 执行前

- [ ] 明确回归范围
- [ ] 准备测试数据
- [ ] 清理浏览器缓存

### 执行中

- [ ] 按优先级执行
- [ ] 及时截图记录
- [ ] 详细记录问题

### 执行后

- [ ] 汇总测试结果
- [ ] 创建问题报告
- [ ] 通知相关人员
- [ ] 归档测试报告

---

*文档版本: v1.0*
*更新日期: 2026-03-13*
