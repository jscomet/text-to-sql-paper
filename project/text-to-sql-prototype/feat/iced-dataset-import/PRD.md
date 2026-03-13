# ICED 数据集导入支持 - 产品需求文档

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| **特性名称** | ICED 数据集导入支持 |
| **版本** | v1.0.0 |
| **状态** | 已完成 |
| **作者** | Claude Code |
| **日期** | 2026-03-13 |

---

## 2. 背景与目标

### 2.1 背景

ICED-2026-paper-code 项目和 Text-to-SQL Prototype 项目都使用 BIRD/Spider 数据集进行 Text-to-SQL 评测，但两者的数据管理方式不同：

- **ICED**: 使用文件系统路径管理 SQLite 数据库 (`dev_databases/{db_id}/{db_id}.sqlite`)
- **Prototype**: 使用数据库连接管理系统，通过 `connection_id` 引用连接

### 2.2 目标

为用户提供一套完整的工具和文档，简化从 ICED 到 Prototype 的数据迁移流程，使用户能够在 Web 界面中对 ICED 数据集进行评测。

### 2.3 成功指标

- 用户能够在 5 分钟内完成数据导入
- 支持完整的 BIRD Dev 数据集 (11个数据库, 1533条问题)
- 零数据格式转换（直接兼容）

---

## 3. 用户故事

### 3.1 目标用户

| 用户类型 | 描述 | 需求 |
|----------|------|------|
| 研究人员 | 需要对比 ICED 和 Prototype 的评测结果 | 快速导入 ICED 数据进行评测 |
| 开发者 | 需要验证 Prototype 的评测功能 | 使用标准数据集测试系统 |
| 数据科学家 | 需要分析不同模型的性能 | 在统一平台查看评测结果 |

### 3.2 用户场景

**场景 1: 研究人员对比评测结果**
> 作为研究人员，我已经在 ICED 项目中获得了评测结果，现在希望在 Prototype 的 Web 界面中进行同样的评测，以便对比分析两个系统的差异。

**场景 2: 开发者验证功能**
> 作为开发者，我需要使用标准的 BIRD 数据集验证 Prototype 的评测功能是否正常工作。

**场景 3: 批量导入数据**
> 作为用户，我希望一键导入所有 ICED 数据，而不是手动创建 11 个数据库连接和评测任务。

---

## 4. 需求描述

### 4.1 功能需求

#### FR-001: 数据文件复制
- **描述**: 自动复制 ICED 的数据集文件到 Prototype 目录
- **优先级**: P0
- **验收标准**:
  - 复制 `bird_dev.json` 数据集文件
  - 复制所有 SQLite 数据库文件 (11个)
  - 保持原始文件结构

#### FR-002: 数据库连接创建
- **描述**: 自动通过 API 创建数据库连接
- **优先级**: P0
- **验收标准**:
  - 为每个数据库创建独立的连接
  - 生成 `db_id` 到 `connection_id` 的映射
  - 支持 SQLite 数据库类型

#### FR-003: 评测任务创建
- **描述**: 自动创建评测任务
- **优先级**: P0
- **验收标准**:
  - 为每个数据库创建独立的评测任务
  - 使用正确的 `connection_id` 和 `dataset_path`
  - 支持自定义评测参数

#### FR-004: 命令行工具
- **描述**: 提供易于使用的命令行脚本
- **优先级**: P1
- **验收标准**:
  - 提供清晰的命令行参数
  - 显示执行进度和结果
  - 提供错误处理和提示

### 4.2 非功能需求

#### NFR-001: 易用性
- 脚本使用简单，参数清晰
- 提供详细的错误提示

#### NFR-002: 可维护性
- 代码结构清晰，易于维护
- 提供完整的文档

#### NFR-003: 兼容性
- 支持 Windows 和 Linux 系统
- 处理路径格式差异

---

## 5. 数据需求

### 5.1 输入数据

**ICED BIRD Dev 数据集**:
- 文件: `data/bird/dev.json`
- 格式: JSON 数组
- 字段: `question_id`, `db_id`, `question`, `evidence`, `SQL`, `difficulty`
- 数据库: 11个 SQLite 数据库

### 5.2 输出数据

**Prototype 数据目录**:
- 文件: `backend/data/bird/bird_dev.json`
- 数据库: `backend/data/bird/databases/*.sqlite`
- 映射: `db_id_mapping.json`

---

## 6. 界面需求

本特性主要提供命令行工具，不涉及 Web 界面修改。

### 6.1 命令行界面

```
Usage: copy_bird_data.py [OPTIONS]

Options:
  --iced-dir PATH     ICED data directory
  --output-dir PATH   Output directory
  --help              Show this message and exit

Usage: create_connections.py [OPTIONS]

Options:
  --token TEXT        JWT Token (or JWT_TOKEN env var)
  --base-url TEXT     API base URL
  --data-dir PATH     Data directory
  --help              Show this message and exit

Usage: create_eval_tasks.py [OPTIONS]

Options:
  --token TEXT        JWT Token (or JWT_TOKEN env var)
  --api-key-id INT    API Key ID
  --base-url TEXT     API base URL
  --eval-mode TEXT    Evaluation mode
  --temperature FLOAT Temperature
  --help              Show this message and exit
```

---

## 7. 约束与限制

### 7.1 技术约束

- Prototype 每个评测任务只支持单个数据库连接
- 需要使用有效的 JWT Token 进行 API 认证
- SQLite 数据库需要使用绝对路径

### 7.2 业务约束

- 用户需要先配置 LLM API Key
- 数据库文件需要可被后端服务访问

---

## 8. 风险分析

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 路径格式问题 | 中 | 中 | 使用 pathlib 处理跨平台路径 |
| API 认证失败 | 中 | 高 | 提供详细的错误提示和解决指南 |
| 数据库文件缺失 | 低 | 高 | 在脚本中进行文件存在性检查 |
| 网络连接问题 | 低 | 中 | 提供重试机制和错误处理 |

---

## 9. 发布标准

- [x] 数据复制脚本完成
- [x] 连接创建脚本完成
- [x] 评测任务创建脚本完成
- [x] 用户文档完成
- [x] 技术文档完成
- [x] 示例文件提供
- [x] 代码审查通过

---

## 10. 附录

### 10.1 术语表

| 术语 | 说明 |
|------|------|
| ICED | 指 ICED-2026-paper-code 项目 |
| Prototype | 指 text-to-sql-prototype 项目 |
| BIRD | A Big Bench for Text-to-SQL 数据集 |
| db_id | 数据库标识符 |
| connection_id | Prototype 中的连接标识符 |

### 10.2 参考文档

- [Text-to-SQL Prototype 项目文档](../../README.md)
- [ICED 项目文档](../../../ICED-2026-paper-code/README.md)
- [BIRD 数据集官方文档](https://bird-bench.github.io/)
