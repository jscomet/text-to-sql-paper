# Project: paper

## 简介

工作论文项目

## 目录结构

```
.
├── .claude/              # Claude Code 配置
│   ├── memory/           # 记忆文件
│   └── skills/           # Claude Skills
│       └── marker-converter/  # 文档转换 Skill
├── src/                  # 源代码
├── docs/                 # 文档
└── CLAUDE.md             # 本项目文件
```

## 常用命令

### Marker 文档转换

阿里云配置已内置，可直接使用：

```bash
# 基础转换（本地快速转换，推荐用于 PDF）
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf

# LLM 增强转换（使用阿里云 qwen3.5-plus）
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf --alibaba

# 扫描件专用（OCR + LLM）
python .claude/skills/marker-converter/scripts/convert_single.py docs/扫描件.pdf --alibaba --force_ocr

# 批量转换
python .claude/skills/marker-converter/scripts/batch_convert.py ./input ./output --alibaba

# 切换模型（如使用 qwen3.5-max）
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf --alibaba --llm_model qwen3.5-max

# 指定页码范围
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf --page_range "0,5-10"
```

**环境变量配置（可选）**：
```bash
set DASHSCOPE_API_KEY=sk-xxx           # 覆盖默认 API Key
set DASHSCOPE_MODEL=qwen3.5-plus       # 覆盖默认模型
set DASHSCOPE_BASE_URL=xxx             # 覆盖默认 Endpoint
```

## 注意事项

### MCP MarkItDown 文档转换

**支持格式**: `.docx`, `.pdf`, `.pptx`, `.xlsx` 等（不支持旧版 `.doc`）

**URI 格式**: `file://localhost/workdir/<路径>`（基于 Docker 挂载）

**示例**:

```json
mcp__markitdown__convert_to_markdown
uri: file://localhost/workdir/docs/文件.docx
```

### MCP Open WebSearch 搜索建议

**中文搜索**: 优先使用 `csdn` 或 `baidu`

- CSDN 技术文章覆盖率高
- 百度适合中文内容和国内资源

**英文搜索**: 使用默认引擎（DuckDuckGo 等）

- 适合国际技术文档、论文、官方文档

**示例**:

```json
// 中文搜索
mcp__open-websearch__search
engines: ["baidu", "csdn"]
query: "PDF转Markdown工具"

// 英文搜索（使用默认引擎）
mcp__open-websearch__search
query: "best PDF to Markdown converter"
```

---

## 当前项目目录

### 项目位置

```
工作根目录: D:\Working\paper\
项目目录:   D:\Working\paper\project\text-to-sql-prototype\
相对路径:   project\text-to-sql-prototype\
```

### 项目结构

```
D:\Working\paper\
├── CLAUDE.md                           # 本项目配置
├── project\                            # 项目目录
│   └── text-to-sql-prototype\          # Text-to-SQL 原型项目
│       ├── backend\                    # 后端代码 (FastAPI)
│       │   └── ...
│       ├── frontend\                   # 前端代码 (Vue3)
│       │   └── ...
│       └── docs\                       # 项目文档
│           ├── 01-PRD.md               # 产品需求文档
│           ├── 02-UI-Design.md         # UI设计文档
│           ├── 03-Business-Logic.md    # 业务逻辑文档
│           ├── 04-Database-Design.md   # 数据库设计文档
│           ├── 05-API-Documentation.md # API接口文档
│           ├── 06-Technical-Architecture.md # 技术架构文档
│           ├── 07-README-Deployment.md # 部署文档
│           ├── plan\                   # 开发计划目录
│           │   ├── 00-Master-Plan.md
│           │   ├── 01-Phase1-Project-Setup.md
│           │   └── ...
│           └── report\                 # 阶段报告目录 (开发中生成)
│               └── ...
└── ...
```

### 快速导航

| 目录 | 绝对路径 | 相对路径 |
|------|----------|----------|
| 项目根目录 | `D:\Working\paper\project\text-to-sql-prototype\` | `project\text-to-sql-prototype\` |
| 后端代码 | `D:\Working\paper\project\text-to-sql-prototype\backend\` | `project\text-to-sql-prototype\backend\` |
| 前端代码 | `D:\Working\paper\project\text-to-sql-prototype\frontend\` | `project\text-to-sql-prototype\frontend\` |
| 项目文档 | `D:\Working\paper\project\text-to-sql-prototype\docs\` | `project\text-to-sql-prototype\docs\` |
| 开发计划 | `D:\Working\paper\project\text-to-sql-prototype\docs\plan\` | `project\text-to-sql-prototype\docs\plan\` |
| 阶段报告 | `D:\Working\paper\project\text-to-sql-prototype\docs\report\` | `project\text-to-sql-prototype\docs\report\` |

---

## AI 工作流程（Text-to-SQL 项目）

本项目采用 **Agent Team** 协作模式进行开发，遵循以下标准化工作流程：

### 工作流程图

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. 读取    │───→│  2. 检查    │───→│  3. 规划    │───→│  4. 执行    │───→│  5. 测试    │
│    Plan     │    │  项目状态    │    │    任务     │    │  Agent Team │    │  Test Agent │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘    └──────┬──────┘
                                                                  │                 │
                                                                  │          ┌──────┴──────┐
                                                                  │          │             │
                                                                  │    ┌────→│  测试通过   │
                                                                  │    │     │             │
                                                                  │    │     └──────┬──────┘
                                                                  │    │            │
                                                                  │    │            ▼
                                                                  │    │     ┌─────────────┐
                                                                  │    │     │  6. 更新    │
                                                                  │    │     │  检查点     │
                                                                  │    │     └──────┬──────┘
                                                                  │    │            │
                                                                  │    │            ▼
                                                                  │    │     ┌─────────────┐    ┌─────────────┐
                                                                  │    │     │  7. 输出    │───→│  8. 提交    │
                                                                  │    │     │   Report    │    │    Commit   │
                                                                  │    │     └─────────────┘    └─────────────┘
                                                                  │    │
                                                                  │    └────→┌─────────────┐
                                                                  └────────→│  测试失败   │
                                                                            │  反馈修复   │
                                                                            └──────┬──────┘
                                                                                   │
                                                                                   ▼
                                                                            ┌─────────────┐
                                                                            │  通知开发    │
                                                                            │  Agent修复   │
                                                                            └──────┬──────┘
                                                                                   │
                                                                                   ▼
                                                                            ┌─────────────┐
                                                                            │  重新测试   │────→ (回到测试环节)
                                                                            │  循环直到   │
                                                                            │  测试通过   │
                                                                            └─────────────┘
```

### 详细步骤

#### 1. 读取 Plan
- **输入**: `docs/plan/00-Master-Plan.md` 和当前阶段计划（如 `01-Phase1-Project-Setup.md`）
- **动作**: 理解当前阶段目标、任务分解、Agent 分配、依赖关系
- **输出**: 明确的任务列表和验收标准

#### 2. 检查项目状态
- **检查内容**:
  - 已完成的功能模块
  - 当前的代码结构
  - 已有的测试覆盖
  - 未完成的检查点
- **工具**: `TaskList`, `Read`, `Glob`
- **输出**: 当前状态报告

#### 3. 规划任务
- **动作**:
  - 根据 Plan 分解具体任务
  - 确定任务依赖关系
  - 分配 Agent 角色
  - 设定验收标准
- **输出**: 任务分配表

#### 4. 执行（Agent Team）
- **启动 Agent**: 使用 `Agent` 工具创建专业 Agent
- **并行执行**: 无依赖的任务并行启动
- **监控进度**: 定期检查任务状态
- **协作沟通**: Agents 之间通过 SendMessage 协调

**Agent 角色定义**:

| Agent | 职责 | 适用阶段 |
|-------|------|----------|
| `backend-dev` | 后端业务开发 | 阶段2、3、6 |
| `frontend-dev` | 前端页面开发 | 阶段4、5、6 |
| `database-dev` | 数据库设计与迁移 | 阶段2 |
| `auth-dev` | 认证与权限 | 阶段2 |
| `ui-component-dev` | 前端组件开发 | 阶段4 |
| `tester` | **专用测试Agent**，负责集成测试、向开发Agent反馈问题 | **所有阶段** |
| `devops` | 部署与运维 | 阶段1、7 |

#### 5. 测试（Test Agent 专用环节）

**这是每个阶段的关键质量控制环节**。

**Test Agent 职责**:
1. **执行集成测试**: 按照阶段计划中的集成测试计划执行测试
2. **验证功能**: 验证所有检查点是否通过
3. **问题反馈**: 如果测试失败，向负责的开发Agent发送详细的错误报告
4. **跟踪修复**: 跟踪问题修复情况，重新测试直到通过

**测试反馈机制**:
```
Test Agent 发现测试失败
    │
    ├── 1. 记录详细错误信息（错误类型、位置、复现步骤）
    │
    ├── 2. 通过 SendMessage 通知负责的开发Agent
    │      内容包含：
    │      - 测试项名称
    │      - 预期结果 vs 实际结果
    │      - 错误日志/截图
    │      - 复现步骤
    │
    ├── 3. 开发Agent修复问题，重新提交
    │
    └── 4. Test Agent 重新测试
           ├─ 通过 → 进入下一步
           └─ 失败 → 继续反馈修复（循环）
```

**测试通过标准**:
- [ ] 所有测试用例通过
- [ ] 代码检查通过（ESLint/flake8）
- [ ] 功能检查通过（边界情况处理正确）
- [ ] 测试覆盖率达标

#### 6. 更新检查点
- **动作**:
  - 验证任务完成度
  - 检查功能是否符合预期
  - 更新 Plan 中的检查点状态
- **工具**: `Read`, `Bash` (运行测试)

#### 7. 输出 Report
- **目录**: `docs/report/`
- **命名规范**: `0x-PhaseX-xx/report-taskX.x-xx（feat）.md`
- **内容要求**:
  - 任务完成情况
  - 实现的功能点
  - 测试覆盖情况
  - 遇到的问题及解决方案
  - **Test Agent 的测试报告**
  - 下一步建议

#### 8. 提交 Commit
- **规范**: 遵循 Conventional Commits
- **格式**: `<type>(<scope>): <subject>`
- **示例**:
  ```bash
  git commit -m "feat(backend): add user authentication system"
  git commit -m "fix(frontend): resolve routing issue in query page"
  git commit -m "docs(report): add phase 2 completion report"
  ```

### 项目目录结构（开发中）

```
text-to-sql-prototype/
├── backend/              # 后端代码
├── frontend/             # 前端代码
├── docs/
│   ├── 01-PRD.md         # 产品需求文档
│   ├── 02-UI-Design.md   # UI设计文档
│   ├── 03-Business-Logic.md
│   ├── 04-Database-Design.md
│   ├── 05-API-Documentation.md
│   ├── 06-Technical-Architecture.md
│   ├── 07-README-Deployment.md
│   ├── plan/             # 开发计划
│   │   ├── 00-Master-Plan.md
│   │   ├── 01-Phase1-Project-Setup.md
│   │   └── ...
│   └── report/           # 阶段报告（开发过程中生成）
│       ├── 01-Phase1-Setup/
│       ├── 02-Phase2-Backend/
│       └── ...
└── CLAUDE.md             # 本文件
```

### 阶段计划文件

| 阶段 | 计划文件 | 工期 | 关键交付物 |
|------|----------|------|-----------|
| 1 | `docs/plan/01-Phase1-Project-Setup.md` | 0.5天 | 前后端项目骨架 |
| 2 | `docs/plan/02-Phase2-Backend-Foundation.md` | 1天 | 数据库、认证、核心设施 |
| 3 | `docs/plan/03-Phase3-Backend-Core.md` | 2天 | Text-to-SQL、评测系统 |
| 4 | `docs/plan/04-Phase4-Frontend-Foundation.md` | 1天 | 路由、状态管理、组件 |
| 5 | `docs/plan/05-Phase5-Frontend-Pages.md` | 2天 | 所有页面 |
| 6 | `docs/plan/06-Phase6-Integration-Test.md` | 1.5天 | 测试覆盖 > 70% |
| 7 | `docs/plan/07-Phase7-Deployment.md` | 1天 | Docker、CI/CD |

### 检查点更新规范

每个任务完成后必须更新以下检查点：

- [ ] **代码检查**: 代码符合项目规范，通过 ESLint/flake8
- [ ] **功能检查**: 功能按预期工作，边界情况处理正确
- [ ] **测试检查**: 编写了测试用例，测试通过，覆盖率达标
- [ ] **文档检查**: 更新了相关文档，编写了 Report

### 测试-反馈-修复循环（重要）

每个阶段的完整流程必须包含测试循环：

```
┌─────────────────────────────────────────────────────────────┐
│                      阶段开发流程                            │
├─────────────────────────────────────────────────────────────┤
│  1. Leader 读取 Plan，检查项目状态                           │
│                                                             │
│  2. Leader 创建任务，分配开发Agent + Test Agent              │
│     - 开发Agent负责实现功能                                  │
│     - Test Agent负责验证测试（并行或后置）                   │
│                                                             │
│  3. 开发Agent完成任务，提交代码                              │
│                                                             │
│  4. Test Agent 执行集成测试                                  │
│     ├─ 测试通过 → 更新检查点，输出Report，提交Commit        │
│     └─ 测试失败 → 向开发Agent反馈问题，进入修复循环          │
│                                                             │
│  5. 修复循环（直到测试通过）：                               │
│     开发Agent修复 → Test Agent重新测试 → 通过/继续修复      │
│                                                             │
│  6. 阶段完成，进入下一阶段                                   │
└─────────────────────────────────────────────────────────────┘
```

**Test Agent 反馈模板**:
```
【测试反馈】任务 X.X - 测试未通过

测试项: [测试名称]
状态: ❌ 失败

预期结果:
[描述期望的行为]

实际结果:
[描述实际发生的行为]

错误信息:
```
[错误日志]
```

复现步骤:
1. [步骤1]
2. [步骤2]
3. [步骤3]

建议修复方向:
[可选：提供修复建议]

请修复后重新提交测试。
```

### 启动开发示例

```
1. Read docs/plan/00-Master-Plan.md
2. Read docs/plan/01-Phase1-Project-Setup.md
3. TaskList 检查当前状态
4. Glob 检查项目结构
5. 创建 Agent Team:
   - backend-dev → Task 1.1
   - frontend-dev → Task 1.2
   - tester → Task 1.3（集成测试）
6. 并行启动 Agents
7. 监控进度，收集 Report
8. Test Agent 执行测试
   - 通过 → 继续
   - 失败 → 通知对应Agent修复 → 重新测试
9. 更新检查点
10. git commit
```

---

## 参考文档

- **项目文档**: `docs/*.md`
- **开发计划**: `docs/plan/*.md`
- **阶段报告**: `docs/report/*/`
