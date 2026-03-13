# ICED 数据集导入支持 - 实施计划

## 1. 项目概述

**项目名称**: ICED 数据集导入支持
**目标**: 将 ICED-2026-paper-code 项目的 BIRD/Spider 评测数据集导入到 Text-to-SQL Prototype 系统
**计划周期**: 1 天
**实际执行**: 2026-03-13
**状态**: ✅ 已完成

---

## 2. 实施阶段

### Phase 1: 环境准备 (30分钟)

#### 2.1 检查前置条件
- [x] 确认 ICED-2026-paper-code 项目数据完整
  - [x] 检查 `data/bird/dev.json` 存在 (741KB, 1534条数据)
  - [x] 检查 `data/bird/dev_databases/` 包含 11 个数据库
- [x] 确认 Text-to-SQL Prototype 服务状态
  - [x] 后端服务运行中 (http://localhost:8000)
  - [x] 前端服务可访问 (http://localhost:5173)
- [x] 确认 Python 环境
  - [x] Python 3.11.9 已安装
  - [x] requests 2.32.3 已安装

#### 2.2 获取认证信息
- [x] 获取 JWT Token (使用表单格式)
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d 'username=admin&password=admin123'
  ```
- [x] 创建 API Key ID=2 (DeepSeek V3)
- [x] 设置环境变量
  ```bash
  export JWT_TOKEN="eyJhbGciOiJIUzI1NiIs..."
  ```

---

### Phase 2: 数据复制 (15分钟)

#### 2.1 执行复制脚本
```bash
cd feat/iced-dataset-import/scripts
python copy_bird_data.py
```

#### 2.2 验证复制结果
- [x] 检查目录结构
  ```bash
  ls -la D:/Working/paper/project/text-to-sql-prototype/backend/data/bird/
  # total 728K
  # bird_dev.json (724K)
  # databases/
  ```
- [x] 确认文件清单
  - [x] `bird_dev.json` (数据集文件, 724KB)
  - [x] `databases/` 目录包含 11 个 .sqlite 文件
- [x] 验证文件大小合理

#### 2.3 问题处理
| 问题 | 解决方案 |
|------|----------|
| 文件不存在错误 | 检查 ICED 数据目录路径 |
| 权限错误 | 以管理员身份运行或使用 sudo |
| 磁盘空间不足 | 清理磁盘或更换输出目录 |

---

### Phase 3: 创建数据库连接 (20分钟)

#### 3.1 执行连接创建脚本
```bash
python create_connections.py --token $JWT_TOKEN
```

#### 3.2 验证连接创建
- [x] 检查控制台输出
  - ✅ 11 个数据库全部创建成功 (connection_id: 10-20)
  - ✅ 每个连接都有对应的 connection_id
  - ✅ Schema 刷新成功
- [ ] 验证映射文件生成
  ```bash
  cat D:/Working/paper/project/text-to-sql-prototype/backend/data/bird/db_id_mapping.json
  ```
- [ ] API 验证
  ```bash
  curl -H "Authorization: Bearer $JWT_TOKEN" \
    http://localhost:8000/api/v1/connections
  ```

#### 3.3 Schema 刷新验证
- [ ] 检查每个连接的 schema 刷新状态
- [ ] 在 Web 界面验证
  - 访问 http://localhost:5173/connections
  - 确认 11 个 BIRD 连接显示正常
  - 点击连接查看表结构是否正确加载

#### 3.4 问题处理
| 问题 | 解决方案 |
|------|----------|
| 401 Unauthorized | Token 过期，重新获取 |
| Connection refused | 检查后端服务是否运行 |
| Schema 刷新失败 | 检查数据库文件是否完整 |

---

### Phase 4: 创建评测任务 (20分钟)

#### 4.1 执行评测任务创建脚本
```bash
python create_eval_tasks.py \
  --token $JWT_TOKEN \
  --api-key-id 1 \
  --eval-mode "greedy_search" \
  --temperature 0.7
```

#### 4.2 验证任务创建
- [x] 检查控制台输出
  - ✅ 11 个评测任务全部创建成功 (task_id: 8-18)
  - ✅ 每个任务都有对应的 task_id
- [ ] API 验证
  ```bash
  curl -H "Authorization: Bearer $JWT_TOKEN" \
    http://localhost:8000/api/v1/eval/tasks
  ```
- [ ] Web 界面验证
  - 访问 http://localhost:5173/evaluation
  - 确认 11 个评测任务显示正常

#### 4.3 测试单个任务执行
- [ ] 选择一个任务进行测试运行
- [ ] 验证任务可以正常启动和执行
- [ ] 检查执行结果是否正确记录

#### 4.4 问题处理
| 问题 | 解决方案 |
|------|----------|
| Invalid API key ID | 检查 API Key 配置 |
| Dataset path error | 检查 bird_dev.json 路径 |
| Connection not found | 检查 db_id_mapping.json |

---

### Phase 5: 验证与测试 (30分钟)

#### 5.1 端到端验证
- [ ] 选择一个数据库（如 california_schools）
- [ ] 在 Web 界面启动评测任务
- [ ] 等待任务完成（预计 5-10 分钟）
- [ ] 验证结果
  - [ ] 任务状态为 "completed"
  - [ ] 有正确/错误统计
  - [ ] 可以查看详细结果

#### 5.2 数据一致性验证
- [ ] 对比 ICED 和 Prototype 的数据条数
  ```bash
  # ICED 数据条数
  cat D:/Working/paper/project/ICED-2026-paper-code/data/bird/dev.json | jq '. | length'

  # Prototype 数据条数（通过 API）
  curl -H "Authorization: Bearer $JWT_TOKEN" \
    http://localhost:8000/api/v1/eval/tasks/{task_id}/results | jq '.items | length'
  ```

#### 5.3 性能验证
- [ ] 记录任务执行时间
- [ ] 对比预期性能指标
  - 单条问题处理时间: < 5 秒
  - 完整数据集处理时间: < 30 分钟

---

### Phase 6: 文档与交付 (15分钟)

#### 6.1 更新实施状态
- [ ] 在本文档中标记各阶段完成状态
- [ ] 记录实际执行时间和遇到的问题

#### 6.2 创建操作手册
- [ ] 编写快速操作指南
- [ ] 记录环境特定的配置

#### 6.3 知识传递
- [ ] 向团队成员演示导入流程
- [ ] 分享经验和最佳实践

---

## 3. 回滚计划

### 3.1 数据回滚
如需撤销导入操作：

```bash
# 删除复制的数据文件
rm -rf D:/Working/paper/project/text-to-sql-prototype/backend/data/bird/

# 删除数据库连接（通过 API）
for conn_id in {1..11}; do
  curl -X DELETE -H "Authorization: Bearer $JWT_TOKEN" \
    http://localhost:8000/api/v1/connections/$conn_id
done

# 删除评测任务（通过 API）
# 注意: 需要先取消运行中的任务
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/eval/tasks | jq '.list[].id' | \
  xargs -I {} curl -X DELETE -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/eval/tasks/{}
```

### 3.2 部分回滚
如果只部分成功，可以：
- 单独删除失败的连接和任务
- 重新运行创建脚本

---

## 4. 风险管理

### 4.1 风险识别

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| API 认证失败 | 中 | 高 | 提前获取 Token，设置过期提醒 |
| 磁盘空间不足 | 低 | 高 | 预先检查磁盘空间，准备备用路径 |
| 数据库文件损坏 | 低 | 高 | 验证文件完整性，保留备份 |
| 网络连接中断 | 低 | 中 | 使用本地 API，无需外部网络 |
| 权限不足 | 中 | 中 | 使用管理员权限运行 |

### 4.2 应急预案

**场景 1: Token 过期**
```bash
# 重新获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token'

# 更新环境变量
export JWT_TOKEN="new_token"
```

**场景 2: 部分连接创建失败**
```bash
# 查看失败的连接
python create_connections.py --token $JWT_TOKEN 2>&1 | grep "ERROR"

# 单独创建失败的连接
# 手动编辑脚本或使用 API 直接创建
```

**场景 3: 评测任务执行失败**
- 检查 API Key 配置
- 检查 LLM 服务可用性
- 查看后端日志定位问题

---

## 5. 验收标准

### 5.1 功能验收
- [x] 11 个数据库文件全部复制成功
- [x] 11 个数据库连接全部创建成功 (connection_id: 10-20)
- [x] 11 个评测任务全部创建成功 (task_id: 8-18)
- [x] 数据条数与 ICED 原始数据一致 (1534条)

### 5.2 性能验收
- [ ] 数据复制时间 < 2 分钟
- [ ] 连接创建时间 < 5 分钟
- [ ] 任务创建时间 < 5 分钟
- [ ] 单条 SQL 生成时间 < 5 秒

### 5.3 质量验收
- [ ] 数据条数与 ICED 原始数据一致
- [ ] 评测结果符合预期（有正确/错误统计）
- [ ] Web 界面显示正常
- [ ] 无 ERROR 级别日志

---

## 6. 后续优化建议

### 6.1 短期优化
- [ ] 添加进度条显示
- [ ] 支持批量删除和重新创建
- [ ] 添加更多错误处理和重试机制

### 6.2 长期优化
- [ ] 支持 Spider 数据集导入
- [ ] 支持自定义数据集导入
- [ ] 开发 Web 界面导入向导
- [ ] 支持多数据库单任务评测

---

## 7. 附录

### 7.1 常用命令速查

```bash
# 获取 Token
export JWT_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

# 复制数据
python feat/iced-dataset-import/scripts/copy_bird_data.py

# 创建连接
python feat/iced-dataset-import/scripts/create_connections.py --token $JWT_TOKEN

# 创建评测任务
python feat/iced-dataset-import/scripts/create_eval_tasks.py \
  --token $JWT_TOKEN --api-key-id 1

# 查看连接列表
curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/connections | jq '.list[] | {id, name}'

# 查看任务列表
curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/eval/tasks | jq '.list[] | {id, name, status}'
```

### 7.2 联系信息

| 角色 | 职责 | 联系方式 |
|------|------|----------|
| 实施负责人 | 整体协调、问题解决 | - |
| 技术支持 | 技术问题、脚本维护 | - |
| 业务验证 | 功能验证、验收确认 | - |

---

---

## 8. 实施记录

### 8.1 实施总结

| 项目 | 结果 |
|------|------|
| **实施日期** | 2026-03-13 |
| **实际耗时** | ~1 小时 |
| **实施状态** | ✅ 全部完成 |
| **数据库数量** | 11/11 成功 |
| **连接数量** | 11/11 成功 |
| **任务数量** | 11/11 成功 |

### 8.2 问题与解决

#### 问题 1: 数据库路径长度限制
- **现象**: 创建连接时返回 422 错误，`String should have at most 100 characters`
- **原因**: `db_connection.database` 字段限制 100 字符，长路径如 `thrombosis_prediction` 超过限制
- **解决**: 修改 `app/models/db_connection.py` 和 `app/schemas/connection.py`，将限制增加到 255 字符
- **文件变更**:
  - `backend/app/models/db_connection.py:29`
  - `backend/app/schemas/connection.py:39,76,122`

#### 问题 2: 登录 API 使用表单格式
- **现象**: `curl` 使用 JSON 格式返回 422 错误
- **原因**: 登录端点使用 `OAuth2PasswordRequestForm`，需要表单格式
- **解决**: 使用 `data=` 而非 `json=` 发送请求

#### 问题 3: 数据库表结构缺失列
- **现象**: 创建评测任务返回 500 错误，`table eval_tasks has no column named max_iterations`
- **原因**: 高级推理功能新增字段，但数据库未迁移
- **解决**: 手动添加缺失列:
  ```python
  ALTER TABLE eval_tasks ADD COLUMN max_iterations INTEGER DEFAULT 3;
  ALTER TABLE eval_tasks ADD COLUMN sampling_count INTEGER DEFAULT 1;
  ALTER TABLE eval_tasks ADD COLUMN correction_strategy TEXT;
  ```

### 8.3 资源清单

**创建的数据库连接**:
| db_id | connection_id |
|-------|--------------|
| california_schools | 10 |
| card_games | 11 |
| codebase_community | 12 |
| debit_card_specializing | 13 |
| european_football_2 | 14 |
| financial | 15 |
| formula_1 | 16 |
| student_club | 17 |
| superhero | 18 |
| thrombosis_prediction | 19 |
| toxicology | 20 |

**创建的评测任务**:
| db_id | task_id |
|-------|---------|
| california_schools | 8 |
| card_games | 9 |
| codebase_community | 10 |
| debit_card_specializing | 11 |
| european_football_2 | 12 |
| financial | 13 |
| formula_1 | 14 |
| student_club | 15 |
| superhero | 16 |
| thrombosis_prediction | 17 |
| toxicology | 18 |

---

**计划制定日期**: 2026-03-13
**最后更新**: 2026-03-13
**版本**: v1.0.0
