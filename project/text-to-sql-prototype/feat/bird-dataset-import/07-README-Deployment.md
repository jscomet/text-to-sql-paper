# BIRD 数据集导入支持 - 部署指南

## 1. 概述

本文档描述 BIRD 数据集导入功能的部署步骤和配置要求。

---

## 2. 前置条件

### 2.1 系统要求

| 项目 | 要求 |
|------|------|
| Text-to-SQL Prototype | v1.0.0+ |
| Python | 3.10+ |
| 磁盘空间 | 至少 2GB 可用空间 |
| 内存 | 至少 4GB |

### 2.2 依赖检查

确保以下 Python 包已安装：

```bash
# 检查基础依赖
pip list | grep -E "fastapi|sqlalchemy|pydantic"

# 确保有以下包
# fastapi>=0.100.0
# sqlalchemy>=2.0.0
# pydantic>=2.0.0
# python-multipart  # 用于文件上传
```

---

## 3. 数据库迁移

### 3.1 生成迁移脚本

```bash
cd backend

# 生成迁移脚本（添加父子任务关系字段）
alembic revision --autogenerate -m "add parent-child task relationship"
```

### 3.2 执行迁移

```bash
# 应用迁移
alembic upgrade head

# 验证迁移结果 - eval_tasks 表新增字段
sqlite3 app.db ".schema eval_tasks"
# 应包含: parent_id, task_type, db_id, connection_id, child_count, completed_children
```

### 3.3 回滚迁移（如需要）

```bash
# 回滚到上一版本
alembic downgrade -1

# 或回滚到特定版本
alembic downgrade xxxx
```

---

## 4. 配置更新

### 4.1 后端配置

**文件**: `backend/app/core/config.py`

添加以下配置项：

```python
class Settings(BaseSettings):
    # 现有配置...

    # 数据集导入配置
    DATASET_IMPORT_DIR: Path = Path("/data/bird")
    MAX_UPLOAD_SIZE: int = 1024 * 1024 * 1024  # 1GB
    ALLOWED_IMPORT_PATHS: List[str] = [
        "/data",
        "/opt/data",
    ]

    # 导入任务配置
    IMPORT_MAX_DATABASES: int = 100
    IMPORT_TIMEOUT: int = 300  # 5分钟
```

### 4.2 环境变量

**文件**: `backend/.env`

```bash
# 数据集导入配置
DATASET_IMPORT_DIR=/data/bird
MAX_UPLOAD_SIZE=1073741824
```

### 4.3 创建数据目录

```bash
# 创建导入数据目录
mkdir -p /data/bird
chmod 755 /data/bird

# 确保后端进程有写权限
chown -R www-data:www-data /data/bird  # Linux
# 或
# icacls "D:\data\bird" /grant Users:F  # Windows
```

---

## 5. 文件更新

### 5.1 后端文件

复制以下文件到对应位置：

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py          # 修改：注册 datasets 路由
│   │       └── datasets.py           # 新增：数据集导入 API
│   ├── schemas/
│   │   └── dataset.py                # 新增：导入 Schema
│   ├── services/
│   │   └── dataset_import.py         # 新增：导入服务（含父子任务创建）
│   └── tasks/
│       └── eval_tasks.py             # 修改：添加 db_id 数据集过滤
└── alembic/
    └── versions/
        └── xxxx_add_parent_child_task_relationship.py  # 新增：迁移脚本
```

### 5.2 前端文件

```
frontend/
├── src/
│   ├── api/
│   │   └── dataset.ts                # 新增：数据集 API 客户端
│   ├── components/
│   │   └── DatasetImport/            # 新增：导入组件
│   │       ├── ImportDialog.vue
│   │       ├── ZipUpload.vue
│   │       ├── LocalPathInput.vue
│   │       ├── ImportProgress.vue
│   │       └── ImportResult.vue
│   └── views/
│       └── evaluation/
│           └── index.vue             # 修改：添加导入按钮
```

---

## 6. 服务启动

### 6.1 启动后端服务

```bash
cd backend

# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6.2 启动前端服务

```bash
cd frontend

# 开发模式
npm run dev

# 生产构建
npm run build
```

---

## 7. 功能验证

### 7.1 API 测试

**获取 JWT Token**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin&password=admin123'
```

**测试本地导入**:

```bash
curl -X POST http://localhost:8000/api/v1/datasets/import/local \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "local_path": "/data/bird/dev_20240627",
    "api_key_id": 1
  }'
```

### 7.2 Web 界面测试

1. 访问 http://localhost:5173/evaluation
2. 点击"导入 BIRD 数据集"按钮
3. 验证对话框正常显示
4. 选择本地目录进行导入
5. 验证导入成功

### 7.3 验证检查清单

- [ ] 数据库迁移成功（eval_tasks 表新增父子任务字段）
- [ ] API 端点可访问
- [ ] Zip 上传功能正常
- [ ] 本地目录导入功能正常
- [ ] 导入进度可查看
- [ ] 导入结果正确显示（包含 parent_task_id）
- [ ] 创建的数据库连接正常
- [ ] 父任务创建成功（task_type='parent'）
- [ ] 子任务创建成功（task_type='child'，parent_id 正确）
- [ ] 子任务按 db_id 正确过滤数据集
- [ ] 父任务统计自动汇总子任务
- [ ] 任务列表父子层级展示正常
- [ ] 父任务详情页子任务列表正常
- [ ] 子任务详情页父任务链接正常

---

## 8. 故障排除

### 8.1 数据库迁移失败

**问题**: 迁移脚本执行失败

**解决**:
```bash
# 手动创建表
sqlite3 app.db <<EOF
CREATE TABLE IF NOT EXISTS dataset_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id VARCHAR(64) UNIQUE NOT NULL,
    -- ... 其他字段
);
EOF
```

### 8.2 文件上传失败

**问题**: 上传大文件时失败

**解决**:
```bash
# 检查 nginx 配置（如使用）
# /etc/nginx/nginx.conf
client_max_body_size 1G;

# 检查后端配置
# 确保 MAX_UPLOAD_SIZE 设置正确
```

### 8.3 路径权限错误

**问题**: 无法写入数据目录

**解决**:
```bash
# Linux
chmod 755 /data/bird
chown $(whoami):$(whoami) /data/bird

# Windows
# 以管理员身份运行 PowerShell
icacls "D:\data\bird" /grant $(whoami):F
```

### 8.4 数据集验证失败

**问题**: 导入时提示格式错误

**检查**:
1. dev.json 是否存在
2. JSON 格式是否有效
3. 必需字段是否齐全
4. 数据库文件是否存在

---

## 9. 监控与日志

### 9.1 日志位置

```
backend/logs/
├── app.log              # 应用日志
├── import_*.log         # 导入任务日志
└── error.log            # 错误日志
```

### 9.2 关键指标监控

| 指标 | 正常范围 | 告警阈值 |
|------|---------|---------|
| 导入成功率 | > 95% | < 90% |
| 平均导入时间 | < 2分钟 | > 5分钟 |
| 磁盘使用率 | < 80% | > 90% |

---

## 10. 回滚计划

### 10.1 代码回滚

```bash
# 回滚后端代码
git checkout HEAD~1 -- backend/app/api/v1/datasets.py
git checkout HEAD~1 -- backend/app/schemas/dataset.py
git checkout HEAD~1 -- backend/app/services/dataset_import.py

# 数据库回滚
alembic downgrade -1

# 重启服务
```

### 10.2 数据清理

```bash
# 删除导入的数据
rm -rf /data/bird/*

# 清理导入创建的父子任务（谨慎操作）
# 先删除子任务，再删除父任务
sqlite3 app.db "DELETE FROM eval_tasks WHERE task_type='child';"
sqlite3 app.db "DELETE FROM eval_tasks WHERE task_type='parent';"

# 清理相关的连接（可选）
sqlite3 app.db "DELETE FROM db_connections WHERE name LIKE 'BIRD - %';"

# 注意：这会删除评测任务和结果，但保留数据集文件
```

---

## 11. 附录

### 11.1 常用命令

```bash
# 查看导入历史
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/datasets/imports

# 查看导入详情（含 parent_task_id）
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/datasets/imports/{import_id}

# 查看父任务及其子任务
sqlite3 app.db "SELECT id, name, task_type, parent_id, db_id FROM eval_tasks WHERE task_type IN ('parent', 'child') ORDER BY parent_id, id;"

# 查看父任务汇总统计
sqlite3 app.db "SELECT t.id, t.name, t.child_count, t.completed_children, SUM(c.total_questions) as total, SUM(c.correct_count) as correct FROM eval_tasks t LEFT JOIN eval_tasks c ON c.parent_id = t.id WHERE t.task_type = 'parent' GROUP BY t.id;"

# 删除导入记录
curl -X DELETE \
  -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/datasets/imports/{import_id}
```

### 11.2 参考链接

- [FastAPI 文件上传](https://fastapi.tiangolo.com/tutorial/request-files/)
- [SQLAlchemy 迁移](https://alembic.sqlalchemy.org/)
- [BIRD 数据集](https://bird-bench.github.io/)
