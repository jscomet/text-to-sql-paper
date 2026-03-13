# Features 目录

本目录用于存放 Text-to-SQL Prototype 项目的新增特性文档。

---

## 特性列表

### advanced-inference

**路径**: `./advanced-inference/`

**说明**: Text-to-SQL 高级推理功能，通过引入多种推理策略（Pass@K、Majority Vote、Check-Correct）显著提高 SQL 生成的准确率和可靠性。

**核心能力**:
- **Single 模式**: 单次 SQL 生成（默认行为）
- **Pass@K 模式**: K次采样，任一通过即成功，提高成功率
- **Majority Vote 模式**: K次采样，多数投票选择，减少随机性
- **Check-Correct 模式**: 生成-检查-修正迭代，适合复杂查询

**文档索引**:
| 文档 | 说明 |
|------|------|
| `README.md` | 用户指南，包含使用示例和最佳实践 |
| `PRD.md` | 产品需求文档 |
| `Technical-Design.md` | 技术设计文档 |
| `Business-Logic.md` | 业务逻辑详细设计 |
| `API-Documentation.md` | API 接口文档 |
| `Release-Checklist.md` | 发布检查清单 |
| `PROJECT-COMPLETION-REPORT.md` | 项目完成报告 |
| `AGENT-TEAM-EXECUTION-SUMMARY.md` | Agent Team 执行总结 |
| `AGENT-TEAM-WORKFLOW-ANALYSIS.md` | Agent Team 工作流分析 |
| `plan/` | 开发计划目录 |

**状态**: ✅ 已完成 (2026-03-13)

**版本**: v1.0.0

---

### iced-dataset-import

**路径**: `./iced-dataset-import/`

**说明**: ICED (BIRD/Spider) 数据集导入支持，提供完整的工具和文档，帮助用户将 ICED-2026-paper-code 项目的评测数据集导入到 Text-to-SQL Prototype 系统中进行评测。

**核心能力**:
- **数据复制**: 一键复制 ICED 数据集文件到 Prototype 目录
- **连接创建**: 自动通过 API 创建数据库连接
- **任务创建**: 批量生成评测任务，支持多种评测模式
- **格式兼容**: 零数据转换，ICED 格式与 Prototype 完全兼容

**文档索引**:
| 文档 | 说明 |
|------|------|
| `README.md` | 用户指南，包含使用示例和常见问题 |
| `PRD.md` | 产品需求文档 |
| `Technical-Design.md` | 技术设计文档 |
| `Implementation-Plan.md` | 实施计划与执行记录 |
| `scripts/copy_bird_data.py` | 数据复制脚本 |
| `scripts/create_connections.py` | 连接创建脚本 |
| `scripts/create_eval_tasks.py` | 评测任务创建脚本 |
| `example/db_id_mapping.json` | 映射文件示例 |

**使用步骤**:
```bash
# 1. 复制数据
cd feat/iced-dataset-import/scripts
python copy_bird_data.py

# 2. 创建连接
python create_connections.py --token $JWT_TOKEN

# 3. 创建评测任务
python create_eval_tasks.py --token $JWT_TOKEN --api-key-id 1
```

**状态**: ✅ 已完成 (2026-03-13)

**版本**: v1.0.0

**实施结果**:
- ✅ 11 个 BIRD 数据库已导入 (1534 条数据)
- ✅ 11 个数据库连接已创建 (ID: 10-20)
- ✅ 11 个评测任务已创建 (ID: 8-18)
- ✅ 数据格式完全兼容，零转换

---

## 目录结构

```
feat/
├── README.md                   # 本文件 - 特性目录索引
├── advanced-inference/         # 高级推理功能
│   ├── README.md
│   ├── PRD.md
│   ├── Technical-Design.md
│   ├── Business-Logic.md
│   ├── API-Documentation.md
│   ├── Release-Checklist.md
│   ├── PROJECT-COMPLETION-REPORT.md
│   ├── AGENT-TEAM-EXECUTION-SUMMARY.md
│   ├── AGENT-TEAM-WORKFLOW-ANALYSIS.md
│   └── plan/
└── iced-dataset-import/        # ICED 数据集导入支持
    ├── README.md
    ├── PRD.md
    ├── Technical-Design.md
    ├── scripts/
    │   ├── copy_bird_data.py
    │   ├── create_connections.py
    │   └── create_eval_tasks.py
    └── example/
        └── db_id_mapping.json
```

---

*最后更新: 2026-03-13*

---

## 新增特性流程

如需添加新特性，请遵循以下步骤：

1. **创建特性目录**: `mkdir feat/your-feature-name`
2. **编写文档**:
   - `README.md` - 用户指南
   - `PRD.md` - 产品需求文档
   - `Technical-Design.md` - 技术设计文档
3. **实现代码**: 添加必要的脚本和代码
4. **更新索引**: 在本文档中添加特性说明
5. **测试验证**: 确保功能正常可用
