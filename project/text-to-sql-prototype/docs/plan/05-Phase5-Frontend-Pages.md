# 阶段5：前端页面开发

## 阶段目标
实现所有前端页面，包括核心查询页面、连接管理、评测管理等。本阶段完成后，前端功能基本完整，用户可以完整使用Text-to-SQL功能。

**预计工期**: 2天
**并行度**: 高（各页面可并行开发）

---

## Agent 协作关系

```
frontend-dev (Task 5.1)         frontend-dev (Task 5.2)         frontend-dev (Task 5.3)
    │                               │                               │
    ├── 登录/注册页面                ├── 连接管理页面                 ├── 评测管理页面
    ├── 首页仪表盘                   ├── Schema展示                   ├── 评测详情
    └── 个人设置                     └── 连接CRUD                     └── 评测结果分析

frontend-dev (Task 5.4)
    │
    ├── 查询页面（核心）
    ├── 历史记录页面
    └── 收藏功能
```

**依赖关系**:
- Task 5.1、5.2、5.3、5.4 可并行执行
- 都依赖阶段4的基础架构

---

## 任务分解

### Task 5.1: 登录与首页
**负责人**: `frontend-dev`
**依赖**: 阶段4完成
**参考文档**: `../02-UI-Design.md` (登录页、首页)

#### 工作内容

1. **登录页面** (`src/views/LoginView.vue`)
   - 登录表单（用户名、密码）
   - 表单验证（Element Plus Form）
   - 登录按钮加载状态
   - 错误提示
   - 注册入口链接

2. **注册页面** (`src/views/RegisterView.vue`)
   - 注册表单（用户名、邮箱、密码、确认密码）
   - 表单验证
   - 注册成功跳转登录

3. **首页仪表盘** (`src/views/HomeView.vue`)
   - 快捷查询入口卡片
   - 最近查询历史列表（最近5条）
   - 常用数据库连接
   - 今日查询统计（今日查询数、成功率）
   - 快速导航按钮

4. **个人设置页面** (`src/views/SettingsView.vue`)
   - 个人信息编辑
   - 修改密码
   - API密钥配置
   - 主题切换

#### 检查点
- [ ] 登录功能正常
- [ ] 注册功能正常
- [ ] 首页数据正确显示
- [ ] 设置页面能修改信息

#### 测试点
```typescript
// 登录测试
await userEvent.type(screen.getByLabelText('用户名'), 'test')
await userEvent.type(screen.getByLabelText('密码'), '123456')
await userEvent.click(screen.getByText('登录'))
expect(await screen.findByText('首页')).toBeInTheDocument()
```

---

### Task 5.2: 数据库连接管理
**负责人**: `frontend-dev`
**依赖**: 阶段4完成
**参考文档**: `../02-UI-Design.md` (连接管理页), `../05-API-Documentation.md`

#### 工作内容

1. **连接列表页面** (`src/views/ConnectionsView.vue`)
   - 表格展示连接（名称、类型、状态、创建时间）
   - 分页功能
   - 搜索功能
   - 添加连接按钮
   - 操作列（编辑、删除、测试）

2. **添加/编辑连接对话框** (`src/components/ConnectionFormDialog.vue`)
   - 表单字段：名称、数据库类型、主机、端口、数据库名、用户名、密码
   - 数据库类型选择器（影响显示字段）
   - SQLite隐藏主机/端口/用户名
   - 测试连接按钮
   - 表单验证

3. **Schema展示** (`src/components/SchemaTree.vue`)
   - 树形展示表结构
   - 展开表显示字段
   - 字段类型、注释显示
   - 刷新Schema按钮

#### 检查点
- [ ] 连接列表显示正确
- [ ] 添加连接能成功
- [ ] 测试连接功能正常
- [ ] Schema能正确展示
- [ ] 删除有确认提示

#### 测试点
```typescript
// 添加连接测试
await userEvent.click(screen.getByText('添加连接'))
await userEvent.type(screen.getByLabelText('连接名称'), 'Test DB')
await userEvent.selectOptions(screen.getByLabelText('数据库类型'), 'sqlite')
await userEvent.type(screen.getByLabelText('数据库文件'), './test.db')
await userEvent.click(screen.getByText('保存'))
```

---

### Task 5.3: 评测管理
**负责人**: `frontend-dev`
**依赖**: 阶段4完成
**参考文档**: `../02-UI-Design.md` (评测管理页)

#### 工作内容

1. **评测任务列表** (`src/views/EvaluationsView.vue`)
   - 表格展示任务（名称、数据集、模式、状态、进度、创建时间）
   - 状态标签（进行中/已完成/失败）
   - 进度条显示
   - 新建评测按钮
   - 操作列（查看详情、取消、删除）

2. **新建评测对话框** (`src/components/EvalTaskFormDialog.vue`)
   - 表单字段：评测名称、数据集类型、数据集文件上传、模型选择、评测模式
   - 模型配置（temperature等）
   - 开始评测按钮

3. **评测详情页面** (`src/views/EvaluationDetailView.vue`)
   - 基本信息卡片（名称、状态、准确率等）
   - 统计图表（正确率饼图、错误类型分布）
   - 结果表格（问题、标准SQL、预测SQL、是否正确、错误类型）
   - 分页功能
   - 筛选功能（只看错误、按错误类型筛选）
   - 导出结果按钮

#### 检查点
- [ ] 任务列表显示正确
- [ ] 新建评测能提交
- [ ] 进度实时更新
- [ ] 详情页统计数据正确
- [ ] 结果表格分页正常

#### 测试点
```typescript
// 创建评测任务测试
await userEvent.click(screen.getByText('新建评测'))
await userEvent.type(screen.getByLabelText('评测名称'), 'Test Eval')
await userEvent.upload(screen.getByLabelText('数据集'), file)
await userEvent.click(screen.getByText('开始评测'))
```

---

### Task 5.4: 查询页面（核心）
**负责人**: `frontend-dev`
**依赖**: 阶段4完成
**参考文档**: `../02-UI-Design.md` (查询页面)

#### 工作内容

1. **查询页面布局** (`src/views/QueryView.vue`)
   - 三栏布局：左侧Schema、中间查询区、右侧历史
   - 或上下布局：查询区在上，结果在下

2. **数据库选择器**
   - 下拉选择已有连接
   - 显示连接状态
   - 刷新Schema按钮

3. **自然语言输入区**
   - 大文本输入框
   - 示例问题提示
   - 生成SQL按钮
   - 加载状态

4. **SQL展示区**
   - SQL代码显示（语法高亮）
   - 编辑功能
   - 复制按钮
   - 执行按钮

5. **结果展示区**
   - 数据表格
   - 结果统计（行数、耗时）
   - 导出按钮（CSV/JSON）
   - 错误提示（如有）

6. **历史记录侧边栏**
   - 最近查询列表
   - 点击加载历史
   - 收藏功能

7. **查询历史页面** (`src/views/HistoryView.vue`)
   - 完整的查询历史列表
   - 搜索功能
   - 筛选（时间范围、收藏）
   - 分页
   - 重新执行、删除操作

#### 检查点
- [ ] 数据库选择正常
- [ ] Schema正确显示
- [ ] SQL生成正常
- [ ] SQL编辑和执行正常
- [ ] 结果正确展示
- [ ] 历史记录保存和加载正常
- [ ] 收藏功能正常

#### 测试点
```typescript
// 查询流程测试
await userEvent.selectOptions(screen.getByLabelText('数据库'), '1')
await userEvent.type(screen.getByPlaceholderText('输入问题'), '查询所有用户')
await userEvent.click(screen.getByText('生成SQL'))
expect(await screen.findByText('SELECT')).toBeInTheDocument()
await userEvent.click(screen.getByText('执行'))
expect(await screen.findByRole('table')).toBeInTheDocument()
```

---

## 阶段交付物

| 交付物 | 位置 | 验收标准 |
|--------|------|----------|
| 登录/注册页面 | `src/views/LoginView.vue`, `RegisterView.vue` | 功能完整，验证正确 |
| 首页 | `src/views/HomeView.vue` | 数据展示正确，快捷入口可用 |
| 连接管理 | `src/views/ConnectionsView.vue` | CRUD完整，Schema展示正确 |
| 评测管理 | `src/views/EvaluationsView.vue`, `EvaluationDetailView.vue` | 任务管理和结果展示完整 |
| 查询页面 | `src/views/QueryView.vue` | 核心功能完整，体验流畅 |
| 历史记录 | `src/views/HistoryView.vue` | 列表、搜索、筛选、收藏功能完整 |
| 设置页面 | `src/views/SettingsView.vue` | 信息修改、API密钥配置正常 |

---

## 阶段检查清单

### 功能检查
- [ ] 登录注册流程完整
- [ ] 首页数据正确
- [ ] 连接管理CRUD完整
- [ ] Schema展示正确
- [ ] SQL生成和执行正常
- [ ] 结果展示和导出正常
- [ ] 历史记录保存和加载正常
- [ ] 评测任务创建和查看正常
- [ ] 评测结果统计正确

### 用户体验检查
- [ ] 加载状态明确
- [ ] 错误提示友好
- [ ] 操作反馈及时
- [ ] 响应式布局正常
- [ ] 操作流畅无卡顿

### 代码检查
- [ ] 组件拆分合理
- [ ] 代码复用率高
- [ ] 类型定义完整
- [ ] 无console.log残留

---

## 集成测试计划

### 测试目标
验证所有前端页面功能完整，前后端联调通过，核心业务流程可运行。

### 测试方式
**浏览器端到端测试** + **真实后端 API 调用**

#### 测试 1: 登录 → 查询完整流程
```
1. 打开 http://localhost:5173
2. 输入账号密码登录
3. 进入首页，查看统计数据
4. 进入数据库连接页面
5. 创建 SQLite 连接（选择本地测试数据库）
6. 进入查询页面
7. 选择连接，输入自然语言问题
8. 点击生成 SQL
9. 查看生成的 SQL 和执行结果
10. 保存到历史记录
```

#### 测试 2: 连接管理流程
```
1. 创建新连接（MySQL/PostgreSQL/SQLite）
2. 测试连接有效性
3. 查看 Schema 展示
4. 编辑连接信息
5. 删除连接
```

#### 测试 3: 历史记录功能
```
1. 执行多次查询
2. 进入历史记录页面
3. 查看列表，确认数据正确
4. 点击收藏
5. 使用收藏筛选
6. 重新执行历史查询
```

#### 测试 4: 评测功能
```
1. 进入评测管理页面
2. 上传评测数据集（JSON 格式）
3. 创建评测任务
4. 查看任务执行进度
5. 等待任务完成
6. 查看评测结果和统计
```

#### 测试 5: 个人设置
```
1. 进入设置页面
2. 修改个人信息
3. 添加 LLM API Key
4. 切换主题（如支持）
```

### 真实运行验证
- [ ] 使用真实后端服务（localhost:8000）
- [ ] 使用真实数据库（SQLite/PostgreSQL）
- [ ] 配置真实 LLM API Key 测试 SQL 生成
- [ ] 测试大数据量下的页面性能

### 验收标准
| 页面 | 测试场景 | 预期结果 |
|------|----------|----------|
| 登录页 | 输入正确/错误账号 | 正确跳转/提示错误 |
| 首页 | 查看统计数据 | 数据正确，图表显示正常 |
| 查询页 | NL→SQL→执行→结果 | 完整流程可用，结果正确 |
| 连接管理 | CRUD + Schema | 所有操作正常，Schema 展示完整 |
| 历史记录 | 列表/收藏/重新执行 | 功能完整，分页正常 |
| 评测管理 | 创建/执行/查看结果 | 任务可创建，结果正确 |
| 设置页 | 修改信息/API Key | 保存成功，即时生效 |

### 测试报告
- [ ] 已生成 `docs/report/05-Phase5-Frontend/report-task5.x-xxx.md`
- [ ] 包含各页面功能截图
- [ ] 包含完整业务流程录屏/GIF
- [ ] 包含错误处理截图

---

## 进入下一阶段条件

1. ✅ 所有页面开发完成
2. ✅ 核心功能（查询、评测）可用
3. ✅ 无明显UI/UX问题
4. ✅ 代码通过review
5. ✅ 集成测试全部通过（浏览器端到端测试）

---

## 风险与应对

| 风险 | 应对措施 |
|------|----------|
| 页面复杂度高 | 先实现MVP功能，再优化 |
| 组件状态管理复杂 | 使用Pinia集中管理 |
| 性能问题 | 虚拟列表、懒加载 |
| API响应慢 | 加载状态、骨架屏 |

---

*依赖文档: ../02-UI-Design.md, ../05-API-Documentation.md*
