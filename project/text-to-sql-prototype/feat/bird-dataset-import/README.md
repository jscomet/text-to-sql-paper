# BIRD 数据集导入支持

## 概述

本特性为 Text-to-SQL Prototype 系统提供标准的 BIRD/Spider 数据集导入能力，支持通过 Web 界面上传或指定本地目录快速导入评测数据。

## 功能特性

- **Zip 文件上传**: 支持上传 BIRD 数据集 zip 文件
- **本地目录导入**: 支持指定服务器本地 BIRD 数据目录
- **自动创建连接**: 为数据集中的每个数据库自动创建连接
- **父子任务结构**: 创建父任务作为容器，每个数据库对应一个子任务，便于管理和统计
- **智能数据过滤**: 每个子任务只运行对应数据库的问题
- **层级进度展示**: 支持展开/折叠查看父子任务层级关系和进度

## 快速开始

### 方式一：Web 界面上传

1. 访问评测页面: http://localhost:5173/evaluation
2. 点击"导入 BIRD 数据集"按钮
3. 选择 BIRD 数据集 zip 文件或输入本地目录路径
4. 选择 API Key 和评测参数
5. 点击导入

### 方式二：API 直接调用

```bash
# 上传 zip 文件导入
curl -X POST http://localhost:8000/api/v1/datasets/import/zip \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@bird_dev.zip" \
  -F "api_key_id=1" \
  -F "eval_mode=greedy_search"

# 指定本地目录导入
curl -X POST http://localhost:8000/api/v1/datasets/import/local \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "local_path": "/data/bird/dev_20240627",
    "api_key_id": 1,
    "eval_mode": "greedy_search"
  }'
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [01-PRD.md](./01-PRD.md) | 产品需求文档 |
| [02-UI-Design.md](./02-UI-Design.md) | UI 设计文档 |
| [03-Business-Logic.md](./03-Business-Logic.md) | 业务逻辑文档 |
| [04-Database-Design.md](./04-Database-Design.md) | 数据库设计 |
| [05-API-Documentation.md](./05-API-Documentation.md) | API 文档 |
| [06-Technical-Architecture.md](./06-Technical-Architecture.md) | 技术架构 |
| [07-README-Deployment.md](./07-README-Deployment.md) | 部署指南 |

## BIRD 数据集格式

支持的 BIRD 数据集结构：

```
bird/
├── dev.json                    # 评测问题集
├── train.json                  # 训练问题集（可选）
├── dev_tables.json             # 表结构信息
├── train_tables.json           # 训练表结构
├── dev_databases/              # 评测数据库
│   ├── california_schools/
│   │   └── california_schools.sqlite
│   ├── financial/
│   │   └── financial.sqlite
│   └── ...
└── train_databases/            # 训练数据库（可选）
    └── ...
```

## 父子任务设计

导入 BIRD 数据集时，系统会自动创建父子任务结构：

- **父任务** (`task_type='parent'`): 作为容器，聚合所有子任务的统计信息
- **子任务** (`task_type='child'`): 每个数据库对应一个子任务，实际执行评测

```
父任务: BIRD-dev-20260314 (11个子任务)
├── 子任务: california_schools (150题)
├── 子任务: financial (130题)
├── 子任务: formula_1 (156题)
└── ...
```

**优势**:
- 清晰的层级关系，便于管理多数据库评测
- 父任务自动汇总所有子任务的统计信息
- 支持单独查看每个数据库的评测结果
- 可批量操作（开始/重试所有子任务）

## 数据格式

`dev.json` 示例：

```json
[
  {
    "question_id": 0,
    "db_id": "california_schools",
    "question": "What is the highest eligible free rate for K-12 students?",
    "evidence": "Eligible free rate for K-12",
    "SQL": "SELECT MAX(eligible_free_rate) FROM frpm WHERE ...",
    "difficulty": "simple"
  }
]
```

## 兼容性

- 支持 BIRD Dev/Train 数据集
- 支持 Spider 数据集
- 兼容 ICED-2026-paper-code 项目数据格式

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-03-14 | 初始版本，支持 zip 上传和本地目录导入 |

## 相关链接

- [BIRD 官方项目](https://bird-bench.github.io/)
- [ICED-2026-paper-code](../../ICED-2026-paper-code/README.md)
- [Text-to-SQL Prototype](../../README.md)
