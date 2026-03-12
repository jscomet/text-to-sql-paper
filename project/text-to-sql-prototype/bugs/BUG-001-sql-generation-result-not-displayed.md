# BUG-001: SQL 生成结果未在页面显示

## 基本信息

| 字段 | 内容 |
|------|------|
| **Bug ID** | BUG-001 |
| **模块** | 查询功能 (Query Module) |
| **页面** | `/query` |
| **严重级别** | 🔴 High |
| **优先级** | P0 |
| **发现日期** | 2026-03-13 |
| **发现人** | E2E Tester (Claude Code) |
| **状态** | 🟡 Open |

---

## 问题描述

点击"生成 SQL"或"一键运行"后，系统提示"SQL 生成成功"，但生成的 SQL 代码和查询结果未在页面上显示。

---

## 复现步骤

1. 登录系统并访问查询页面 `/query`
2. 选择数据库连接（如 PG-Test）
3. 等待 Schema 加载完成
4. 在输入框中输入自然语言问题，例如："查询所有用户的姓名和邮箱"
5. 点击"生成 SQL"按钮或"一键运行"按钮
6. 观察页面显示

---

## 期望行为

- [ ] 显示生成的 SQL 代码块（带语法高亮）
- [ ] 显示 SQL 执行结果表格
- [ ] 显示执行元信息（行数、执行时间）
- [ ] 查询自动保存到历史记录

---

## 实际行为

- [x] 显示成功提示 "SQL 生成成功"
- [x] 页面中间区域保持空白
- [x] 查询历史未记录该查询
- [ ] SQL 代码块未显示
- [ ] 执行结果表格未显示

---

## 截图

![SQL 生成页面](../e2e/reports/2026-03-13/screenshots/QUERY-004-sql-generation.png)

---

## 环境信息

| 项目 | 版本/地址 |
|------|----------|
| 前端 | http://localhost:5173 |
| 后端 | http://localhost:8000 |
| 浏览器 | Playwright Chromium |
| 数据库 | PostgreSQL (localhost:5432) |
| 测试用户 | e2e_tester |

---

## 可能原因分析

### 原因 1: 后端 LLM 服务未配置
- 后端未配置 LLM API Key
- 后端未配置模型端点
- 环境变量缺失

### 原因 2: API 响应格式问题
- 后端返回格式与前端期望不符
- 字段名不匹配
- 数据结构错误

### 原因 3: 前端渲染问题
- Vue 组件状态管理错误
- 响应数据处理逻辑错误
- 条件渲染判断错误

---

## 调试信息

### 浏览器控制台
```
[ERROR] Failed to load resource: the server responded with a status of 500
@ http://localhost:8000/api/v1/query/generate
```

### 后端日志（需检查）
```bash
# 检查后端日志
cd backend && tail -f app.log
```

---

## 影响范围

### 阻塞的测试用例 (26个)

| 用例 ID | 描述 | 优先级 |
|---------|------|--------|
| TC-QUERY-004 | SQL 生成 - 简单查询 | P0 |
| TC-QUERY-005 | SQL 生成 - 聚合查询 | P0 |
| TC-QUERY-006 | SQL 生成 - 条件查询 | P0 |
| TC-QUERY-007 | SQL 编辑 | P1 |
| TC-QUERY-008 | SQL 执行 - 成功 | P0 |
| TC-QUERY-009 | SQL 执行 - 语法错误 | P0 |
| TC-QUERY-010 | SQL 执行 - 超时处理 | P1 |
| TC-QUERY-011 | 结果表格展示 | P0 |
| TC-QUERY-012 | 结果导出 CSV | P1 |
| TC-QUERY-013 | 结果导出 JSON | P1 |
| TC-QUERY-014 | 多轮对话 | P1 |
| TC-QUERY-015 | SQL 复制功能 | P1 |
| TC-QUERY-019 | 查询历史自动保存 | P1 |
| TC-QUERY-020 | 快捷示例问题 | P1 |
| TC-QUERY-021 | 结果分页功能 | P1 |
| TC-QUERY-022 | 输入敏感词过滤 | P1 |
| TC-QUERY-023 | 大数据量结果处理 | P1 |
| TC-QUERY-024 | 特殊字符处理 | P1 |
| TC-QUERY-025 | SQL 语法高亮 | P1 |
| TC-QUERY-026 | 查询性能统计 | P2 |
| TC-QUERY-027 | 查询结果图表展示 | P2 |
| TC-QUERY-028 | 离线模式处理 | P1 |

---

## 建议修复方案

### 方案 1: 检查 LLM 配置
1. 检查 `backend/app/core/config.py` 中的 LLM 配置
2. 确认环境变量 `.env` 中是否配置了 API Key
3. 检查模型端点是否可访问

### 方案 2: 检查 API 响应
1. 打开浏览器开发者工具
2. 查看 Network 标签页的 `/api/v1/query/generate` 请求
3. 检查响应状态码和数据格式

### 方案 3: 检查前端渲染
1. 检查 `frontend/src/views/QueryView.vue`
2. 验证响应数据处理逻辑
3. 检查 SQL 显示组件的渲染条件

---

## 相关代码

### 前端关键代码位置
```
frontend/src/views/QueryView.vue
frontend/src/components/SqlEditor/
frontend/src/components/ResultTable/
```

### 后端关键代码位置
```
backend/app/api/v1/endpoints/query.py
backend/app/services/llm_service.py
backend/app/core/config.py
```

---

## 相关文档

- [查询模块测试规范](../e2e/specs/03-Query-Test-Spec.md)
- [查询模块测试报告](../e2e/reports/2026-03-13/report-03-query-module.md)

---

## 修复验证清单

修复后需验证以下功能：

- [ ] SQL 生成后正确显示代码块
- [ ] SQL 执行后正确显示结果表格
- [ ] 执行元信息正确显示（行数、时间）
- [ ] 查询自动保存到历史记录
- [ ] 历史页面可查看已执行的查询

---

*创建时间: 2026-03-13*
*最后更新: 2026-03-13*
*版本: v1.0*
