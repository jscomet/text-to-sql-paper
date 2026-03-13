# BIRD 数据集导入 - E2E 测试执行计划

## 1. 执行概览

### 当前状态
| 组件 | 状态 | 说明 |
|------|------|------|
| 后端服务层 | ✅ 已完成 | 82 个测试通过（验证、解析、任务服务） |
| 后端 API | 🟡 已实现 | 23 个测试失败（认证模拟问题待修复） |
| 前端组件 | ✅ 已完成 | ImportDialog、ProgressDialog 就绪 |
| 前端页面集成 | 🟡 进行中 | EvaluationsView.vue 需集成对话框 |
| E2E 测试 | 🔴 待执行 | 本计划重点 |

### 执行策略
采用**分层递进**策略：先验证后端 API → 再验证前端组件 → 最后端到端流程

```
Phase 1: API 基础验证（30分钟）
Phase 2: 前端组件验证（30分钟）
Phase 3: 端到端流程测试（2小时）
Phase 4: 回归测试（1小时）
```

---

## 2. 环境准备

### 2.1 服务启动检查清单

```bash
# 1. 启动后端服务
cd D:\Working\paper\project\text-to-sql-prototype\backend
python -m app.main
# 检查: http://localhost:8000/docs 可访问

# 2. 启动前端服务
cd D:\Working\paper\project\text-to-sql-prototype\frontend
npm run dev
# 检查: http://localhost:5173 可访问

# 3. 验证 ICED 数据可访问
ls D:\Working\paper\project\ICED-2026-paper-code\data\bird\dev.json
ls D:\Working\paper\project\ICED-2026-paper-code\data\bird\dev_databases\
```

### 2.2 测试数据准备

| 数据 | 位置 | 用途 |
|------|------|------|
| ICED BIRD 数据 | `D:\Working\paper\project\ICED-2026-paper-code\data\bird` | 本地目录导入测试 |
| 小型 Zip 数据集 | `e2e/fixtures/sample-bird-dataset.zip` | Zip 上传测试 |
| 无效数据集 | `e2e/fixtures/invalid-dataset.zip` | 错误处理测试 |

### 2.3 测试账号
- 用户名: `admin`
- 密码: `admin123`

---

## 3. Phase 1: API 基础验证（30分钟）

### 3.1 数据集导入 API 测试

#### TC-API-001: Zip 导入接口
```bash
# 使用 curl 或 Postman 测试
curl -X POST http://localhost:8000/api/v1/datasets/import/zip \
  -H "Authorization: Bearer {token}" \
  -F "file=@e2e/fixtures/sample-bird-dataset.zip" \
  -F "api_key_id=1" \
  -F "eval_mode=greedy_search"
```

**验证点**:
- [ ] 接口返回 200
- [ ] 返回包含 parent_task_id
- [ ] 返回包含 connections 和 tasks 统计
- [ ] 返回包含 total_questions

#### TC-API-002: 本地目录导入接口
```bash
curl -X POST http://localhost:8000/api/v1/datasets/import/local \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "local_path": "D:\\Working\\paper\\project\\ICED-2026-paper-code\\data\\bird",
    "api_key_id": 1,
    "eval_mode": "greedy_search"
  }'
```

**验证点**:
- [ ] 接口返回 200
- [ ] 正确解析 11 个数据库
- [ ] 正确统计 1534 条问题

#### TC-API-003: 错误处理测试
```bash
# 测试无效路径
curl -X POST http://localhost:8000/api/v1/datasets/import/local \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"local_path": "/invalid/path", "api_key_id": 1}'
# 期望: 400 Bad Request
```

**验证点**:
- [ ] 无效路径返回 400
- [ ] 错误信息清晰

### 3.2 评测任务 API 测试

#### TC-API-004: 任务列表接口
```bash
curl "http://localhost:8000/api/v1/eval/tasks?task_type=parent"
curl "http://localhost:8000/api/v1/eval/tasks?task_type=child"
```

**验证点**:
- [ ] task_type 筛选有效
- [ ] 父任务显示 child_count
- [ ] 子任务显示 parent_id 和 db_id

#### TC-API-005: 批量操作接口
```bash
# 批量开始
curl -X POST "http://localhost:8000/api/v1/eval/tasks/{parent_id}/start-all"

# 重试失败
curl -X POST "http://localhost:8000/api/v1/eval/tasks/{parent_id}/retry-failed"
```

**验证点**:
- [ ] 批量开始返回成功计数
- [ ] 重试失败返回重试计数

---

## 4. Phase 2: 前端组件验证（30分钟）

### 4.1 导入对话框组件测试

#### TC-UI-001: 对话框显示
**步骤**:
1. 登录系统
2. 导航到 `/evaluations`
3. 点击"导入 BIRD 数据"按钮

**验证点**:
- [ ] 对话框正常显示
- [ ] 标签页切换正常（Zip/本地）
- [ ] 默认显示 Zip 标签页

#### TC-UI-002: Zip 上传功能
**步骤**:
1. 在导入对话框选择 Zip 标签页
2. 拖拽或选择 zip 文件
3. 观察验证结果

**验证点**:
- [ ] 文件选择正常
- [ ] 自动验证触发
- [ ] 验证结果显示（数据库数量、问题数量）

#### TC-UI-003: 本地路径功能
**步骤**:
1. 切换到本地路径标签页
2. 输入 `D:\Working\paper\project\ICED-2026-paper-code\data\bird`
3. 点击验证按钮

**验证点**:
- [ ] 路径输入正常
- [ ] 验证按钮触发 API 调用
- [ ] 验证结果显示正确

#### TC-UI-004: 配置表单
**验证点**:
- [ ] API Key 下拉列表加载
- [ ] 评测模式选择正常
- [ ] Temperature 滑块正常
- [ ] 提交按钮状态管理（未验证前禁用）

### 4.2 进度对话框组件测试

#### TC-UI-005: 进度显示
**步骤**:
1. 完成导入配置
2. 点击开始导入
3. 观察进度对话框

**验证点**:
- [ ] 进度对话框显示
- [ ] 进度条更新
- [ ] 步骤指示器变化
- [ ] 日志输出显示

---

## 5. Phase 3: 端到端流程测试（2小时）

### 5.1 E2E-001: 完整 Zip 导入流程

**前置条件**:
- 服务已启动
- 已登录
- 已配置 API Key

**执行步骤**:
```typescript
// 使用 MCP Playwright Tools
await mcp__playwright__browser_navigate({ url: "http://localhost:5173/login" });

// 1. 登录
await mcp__playwright__browser_fill_form({
  fields: [
    { name: "用户名", type: "textbox", ref: "username_ref", value: "admin" },
    { name: "密码", type: "textbox", ref: "password_ref", value: "admin123" }
  ]
});
await mcp__playwright__browser_click({ element: "登录按钮", ref: "login_btn_ref" });

// 2. 导航到评测页面
await mcp__playwright__browser_navigate({ url: "http://localhost:5173/evaluations" });
await sleep(2000);

// 3. 点击导入按钮
const snapshot1 = await mcp__playwright__browser_snapshot();
const importBtn = findElement(snapshot1, "导入 BIRD 数据");
await mcp__playwright__browser_click({ element: "导入按钮", ref: importBtn.ref });

// 4. 上传文件
await mcp__playwright__browser_file_upload({
  paths: ["e2e/fixtures/sample-bird-dataset.zip"]
});
await sleep(2000);

// 5. 选择 API Key
const snapshot2 = await mcp__playwright__browser_snapshot();
const apiKeySelect = findElement(snapshot2, "API Key");
await mcp__playwright__browser_select_option({
  element: "API Key 选择",
  ref: apiKeySelect.ref,
  values: ["1"]
});

// 6. 点击导入
const snapshot3 = await mcp__playwright__browser_snapshot();
const submitBtn = findElement(snapshot3, "开始导入");
await mcp__playwright__browser_click({ element: "开始导入", ref: submitBtn.ref });

// 7. 验证进度对话框
await sleep(3000);
const snapshot4 = await mcp__playwright__browser_snapshot();
assertContains(snapshot4, "导入进度");

// 8. 等待完成
await sleep(10000);

// 9. 验证任务创建
await mcp__playwright__browser_navigate({ url: "http://localhost:5173/evaluations" });
await sleep(2000);
const snapshot5 = await mcp__playwright__browser_snapshot();
assertContains(snapshot5, "BIRD");
```

**验证点**:
- [ ] 导入成功提示
- [ ] 父任务出现在列表中
- [ ] 子任务数量正确
- [ ] 截图记录每个关键步骤

### 5.2 E2E-002: 本地目录导入流程

**执行步骤**:
1. 登录并导航到评测页面
2. 点击导入按钮
3. 切换到本地路径标签页
4. 输入路径 `D:\Working\paper\project\ICED-2026-paper-code\data\bird`
5. 点击验证
6. 配置参数
7. 点击导入
8. 验证结果

**验证点**:
- [ ] 路径验证成功
- [ ] 显示 11 个数据库
- [ ] 显示 1534 条问题
- [ ] 导入成功创建任务

### 5.3 E2E-003: 父子任务列表展示

**执行步骤**:
1. 完成数据集导入
2. 查看评测任务列表
3. 验证父任务显示
4. 点击展开父任务
5. 验证子任务列表

**验证点**:
- [ ] 父任务显示类型标签
- [ ] 父任务显示子任务数量
- [ ] 展开后显示子任务列表
- [ ] 子任务显示 db_id
- [ ] 子任务显示状态

### 5.4 E2E-004: 父任务详情与批量操作

**执行步骤**:
1. 点击父任务进入详情
2. 验证统计卡片
3. 验证子任务列表表格
4. 点击"全部开始"
5. 等待任务执行
6. 验证状态更新

**验证点**:
- [ ] 统计卡片显示正确
- [ ] 子任务列表数据正确
- [ ] 批量开始按钮有效
- [ ] 子任务状态变化
- [ ] 父任务统计更新

### 5.5 E2E-005: 错误处理流程

**执行步骤**:
1. 测试无效 Zip 文件上传
2. 验证错误提示
3. 测试无效本地路径
4. 验证错误提示

**验证点**:
- [ ] 错误提示清晰
- [ ] 导入流程正确中断
- [ ] 用户可以重新操作

---

## 6. Phase 4: 回归测试（1小时）

### 6.1 现有功能回归

#### TC-REG-001: 原有评测功能
- [ ] 创建独立评测任务正常
- [ ] 任务执行正常
- [ ] 结果查看正常

#### TC-REG-002: 连接管理
- [ ] 创建连接正常
- [ ] 测试连接正常
- [ ] 删除连接正常

#### TC-REG-003: 历史记录
- [ ] 查询历史正常
- [ ] 收藏功能正常

---

## 7. 测试执行时间表

| 时间 | 内容 | 执行人 |
|------|------|--------|
| 0:00-0:30 | Phase 1: API 基础验证 | Team Leader |
| 0:30-1:00 | Phase 2: 前端组件验证 | Team Leader |
| 1:00-1:30 | E2E-001: Zip 导入流程 | Team Leader |
| 1:30-2:00 | E2E-002: 本地目录导入 | Team Leader |
| 2:00-2:30 | E2E-003: 父子任务列表 | Team Leader |
| 2:30-3:00 | E2E-004: 批量操作 | Team Leader |
| 3:00-3:30 | E2E-005: 错误处理 | Team Leader |
| 3:30-4:30 | Phase 4: 回归测试 | Team Leader |

---

## 8. 通过标准

### 8.1 必须全部通过（P0）
- [ ] TC-API-001: Zip 导入接口
- [ ] TC-API-002: 本地目录导入接口
- [ ] TC-API-004: 任务列表接口
- [ ] TC-UI-001: 对话框显示
- [ ] TC-UI-004: 配置表单
- [ ] E2E-001: 完整 Zip 导入流程
- [ ] E2E-002: 本地目录导入流程
- [ ] E2E-003: 父子任务列表展示
- [ ] E2E-004: 父任务详情与批量操作

### 8.2 允许最多 1 个失败（P1）
- [ ] TC-API-003: 错误处理测试
- [ ] TC-API-005: 批量操作接口
- [ ] TC-UI-002: Zip 上传功能
- [ ] TC-UI-003: 本地路径功能
- [ ] TC-UI-005: 进度显示
- [ ] E2E-005: 错误处理流程

### 8.3 允许最多 2 个失败（P2）
- [ ] TC-REG-001~003: 回归测试

---

## 9. 问题记录模板

```markdown
## BUG-{编号}: {标题}

### 基本信息
| 项目 | 内容 |
|------|------|
| 测试用例 | TC-XXX |
| 严重级别 | 🔴 Critical / 🟡 High / 🟢 Medium |
| 发现时间 | YYYY-MM-DD HH:MM |

### 问题描述
{详细描述}

### 复现步骤
1. {步骤1}
2. {步骤2}

### 期望行为
{期望结果}

### 实际行为
{实际结果}

### 截图
{截图文件名}

### 相关日志
```
{日志内容}
```
```

---

## 10. 执行前检查清单

- [ ] 后端服务启动正常
- [ ] 前端服务启动正常
- [ ] ICED 数据可访问
- [ ] 测试账号可用
- [ ] API Key 已配置
- [ ] 截图目录已创建
- [ ] Playwright MCP 工具可用

---

*文档版本: v1.0.0*
*最后更新: 2026-03-14*
*执行人: Team Leader*
