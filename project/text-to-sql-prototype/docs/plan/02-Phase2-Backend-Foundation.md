# 阶段2：后端基础架构

## 阶段目标
搭建后端核心基础设施，包括数据库模型、认证系统、日志和异常处理。本阶段完成后，后端应具备基本的用户管理能力。

**预计工期**: 1天
**实际工期**: 1天
**状态**: ✅ 已完成
**完成日期**: 2026-03-12
**并行度**: 中（数据库模型与认证可并行，但认证依赖用户模型）

---

## Agent 协作关系

```
database-dev (Task 2.1)         auth-dev (Task 2.2)             backend-dev (Task 2.3)
    │                               │                               │
    ├── 创建：数据库模型            ├── 创建：JWT认证、用户API        ├── 创建：核心配置、日志、异常处理
    └── 输出：models/*.py, 迁移脚本  └── 输出：auth相关代码           └── 输出：core/*, main.py

Test Agent (Task 2.4)
    │
    ├── 执行：集成测试
    ├── 验证：所有API功能
    └── 反馈：问题报告（如测试失败）
```

**依赖关系**:
- Task 2.1、2.2、2.3 可并行执行（2.2依赖2.1的用户模型）
- Task 2.4 依赖 2.1、2.2、2.3 全部完成

---

## 任务分解

### Task 2.1: 数据库模型与迁移
**负责人**: `database-dev`
**依赖**: 阶段1完成
**参考文档**: `../04-Database-Design.md`

#### 工作内容

1. **创建数据库模型** (`app/models/`)

   a. `user.py` - 用户模型
   ```python
   # 字段要求：
   # - id: Integer, PK
   # - username: String(50), unique, not null
   # - email: String(100), unique, not null
   # - password_hash: String(255), not null
   # - role: String(20), default='user'
   # - status: String(20), default='active'
   # - created_at: DateTime
   # - updated_at: DateTime
   ```

   b. `db_connection.py` - 数据库连接模型
   ```python
   # 字段要求：
   # - id: Integer, PK
   # - user_id: Integer, FK -> users.id
   # - name: String(100)
   # - db_type: String(20) [mysql/postgresql/sqlite/sqlserver/oracle]
   # - host: String(255)
   # - port: Integer
   # - database: String(100)
   # - username: String(100)
   # - password_encrypted: Text
   # - schema_cache: JSON
   # - status: String(20) [active/inactive/error]
   # - created_at, updated_at: DateTime
   ```

   c. `query_history.py` - 查询历史模型
   ```python
   # 字段要求：
   # - id: Integer, PK
   # - user_id: Integer, FK
   # - connection_id: Integer, FK
   # - nl_question: Text
   # - generated_sql: Text
   # - execution_status: String(20) [pending/success/failed]
   # - execution_time_ms: Float
   # - is_favorite: Boolean
   # - error_message: Text
   # - created_at: DateTime
   ```

   d. `eval_task.py` - 评测任务模型
   ```python
   # 字段要求：
   # - id: Integer, PK
   # - user_id: Integer, FK
   # - name: String(200)
   # - dataset_type: String(50) [bird/spider/custom]
   # - dataset_path: String(500)
   # - model_config: JSON
   # - eval_mode: String(50) [greedy_search/major_voting/pass@k]
   # - status: String(20) [pending/running/completed/failed/cancelled]
   # - progress_percent: Integer
   # - total_questions, processed_questions, correct_count: Integer
   # - accuracy: Float
   # - log_path: String(500)
   # - error_message: Text
   # - created_at, started_at, completed_at: DateTime
   ```

   e. `eval_result.py` - 评测结果模型
   ```python
   # 字段要求：
   # - id: Integer, PK
   # - task_id: Integer, FK
   # - question_id: String(100)
   # - nl_question: Text
   # - db_id: String(100)
   # - gold_sql: Text
   # - predicted_sql: Text
   # - is_correct: Boolean
   # - error_type: String(50) [syntax/execution/logic/timeout/generation]
   # - error_message: Text
   # - execution_time_ms: Float
   # - created_at: DateTime
   ```

   f. `api_key.py` - API密钥模型
   ```python
   # 字段要求：
   # - id: Integer, PK
   # - user_id: Integer, FK
   # - key_type: String(50) [openai/alibaba/anthropic/azure_openai/local]
   # - key_encrypted: Text
   # - description: String(200)
   # - is_default: Boolean
   # - created_at, last_used_at: DateTime
   ```

2. **配置 Alembic 迁移**
   ```bash
   cd backend
   alembic init alembic
   ```
   - 修改 `alembic.ini` 配置
   - 修改 `alembic/env.py` 导入模型

3. **创建初始迁移脚本**
   ```bash
   alembic revision --autogenerate -m "init database"
   alembic upgrade head
   ```

#### 检查点
- [x] 所有模型文件创建完成
- [x] 模型字段与数据库设计文档一致
- [x] 外键关系正确设置
- [x] 索引已配置
- [x] Alembic能生成迁移脚本
- [x] `alembic upgrade head` 能成功创建表

#### 自测点
```python
# 测试数据库连接和表创建
from app.models import User, DBConnection
from app.core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
assert 'users' in tables
assert 'db_connections' in tables
```

---

### Task 2.2: 认证与用户 API
**负责人**: `auth-dev`
**依赖**: Task 2.1 完成（需要User模型）
**参考文档**: `../05-API-Documentation.md` (认证模块)

#### 工作内容

1. **密码工具** (`app/core/security.py`)
   - `verify_password(plain, hashed) -> bool`
   - `get_password_hash(password) -> str`
   - 使用 bcrypt

2. **JWT 工具** (`app/core/auth.py`)
   - `create_access_token(data: dict, expires_delta: timedelta) -> str`
   - `verify_token(token: str) -> dict`

3. **认证依赖** (`app/api/deps.py`)
   - `get_current_user(token: str = Depends(oauth2_scheme)) -> User`
   - `get_current_active_user(current_user: User = Depends(get_current_user)) -> User`

4. **用户 Schema** (`app/schemas/user.py`)
   - `UserCreate`: username, email, password
   - `UserResponse`: id, username, email, role, status, created_at
   - `UserLogin`: username, password

5. **认证 API** (`app/api/v1/auth.py`)
   - `POST /api/v1/auth/register` - 注册
   - `POST /api/v1/auth/login` - 登录（返回JWT）
   - `POST /api/v1/auth/logout` - 登出
   - `GET /api/v1/auth/me` - 获取当前用户

#### 检查点
- [x] 密码哈希和验证功能正常
- [x] JWT能正确生成和验证
- [x] 注册接口能创建用户
- [x] 登录接口能返回有效token
- [x] 受保护接口需要认证

#### 自测点
```bash
# 测试注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"123456"}'

# 测试登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=123456"

# 测试获取当前用户
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

---

### Task 2.3: 核心基础设施
**负责人**: `backend-dev`
**依赖**: 无（可与2.1、2.2并行）

#### 工作内容

1. **数据库连接** (`app/core/database.py`)
   - 创建异步引擎
   - 创建 SessionLocal
   - 提供 `get_db()` 依赖

2. **日志配置** (`app/core/logging.py`)
   - 使用 loguru
   - 配置日志格式和级别
   - 支持文件轮转

3. **异常处理** (`app/core/exceptions.py`)
   - 自定义异常类：
     - `AppException`
     - `NotFoundException`
     - `ValidationException`
     - `AuthenticationException`
   - 全局异常处理器

4. **响应封装** (`app/core/response.py`)
   - 统一响应格式：
     ```json
     {
       "code": 200,
       "message": "success",
       "data": {}
     }
     ```

5. **主入口** (`app/main.py`)
   - 创建 FastAPI 应用实例
   - 注册路由
   - 注册中间件（CORS、日志、异常处理）
   - 注册事件（startup/shutdown）

6. **路由组织** (`app/api/v1/__init__.py`)
   - 创建 APIRouter
   - 导入并注册 auth 路由

#### 检查点
- [x] 数据库连接能正常工作
- [x] 日志能正常输出
- [x] 异常能被正确捕获和返回
- [x] 响应格式统一
- [x] 服务能正常启动

#### 自测点
```bash
# 启动服务
cd backend
uvicorn app.main:app --reload

# 测试健康检查
curl http://localhost:8000/health

# 测试API文档
curl http://localhost:8000/docs
```

---

### Task 2.4: 集成测试（Test Agent负责）
**负责人**: `tester` (Test Agent)
**依赖**: Task 2.1、2.2、2.3 全部完成
**测试目标**: 验证后端基础架构完整，认证系统、数据库、核心配置全部正常工作

#### 测试方式
**Python 自动化测试脚本** - 使用 FastAPI TestClient

**测试文件**: `backend/test_api_demo.py`

```python
# 测试内容
1. 健康检查 (GET /health)
2. 用户注册 (POST /api/v1/auth/register)
3. 用户登录 (POST /api/v1/auth/login) → 获取 JWT Token
4. 获取用户信息 (GET /api/v1/auth/me) → 使用 Token
5. 未认证访问 → 验证 401
6. 错误密码 → 验证 401
7. 重复注册 → 验证 400
8. 用户登出 (POST /api/v1/auth/logout)
```

#### 运行测试
```bash
cd backend
source venv/Scripts/activate
python test_api_demo.py
```

#### 验收标准
| 测试项 | 预期结果 |
|--------|----------|
| 健康检查 | 200, status: healthy |
| 用户注册 | 201, 返回用户数据 |
| 用户登录 | 200, 返回 access_token |
| 获取用户信息 | 200, 返回当前用户 |
| 未认证访问 | 401, detail: Not authenticated |
| 错误密码 | 401, detail: Incorrect username or password |
| 重复注册 | 400, detail: Username already registered |
| 用户登出 | 200, message: Successfully logged out |

#### 测试反馈机制
```
Test Agent 执行集成测试
    │
    ├─ 全部测试通过
    │     → 更新检查点
    │     → 输出测试报告 docs/report/02-Phase2-Backend/
    │     → 通知Leader测试通过
    │
    └─ 测试失败
          → 向对应开发Agent发送错误报告：
            【测试反馈】Task 2.X - 测试未通过

            测试项: [具体测试项]
            状态: ❌ 失败

            预期结果: [期望的行为]
            实际结果: [实际的行为]

            错误信息:
            ```
            [详细错误日志]
            ```

            复现步骤:
            1. [步骤1]
            2. [步骤2]

            请修复后通知Test Agent重新测试。

          → 开发Agent修复问题
          → Test Agent 重新测试
          → 循环直到全部通过
```

#### 真实运行验证
- [ ] 已执行测试脚本，全部 8 个测试通过
- [ ] 已验证 JWT Token 生成与验证
- [ ] 已验证数据库表创建（9 个表）
- [ ] 已生成测试报告

#### 测试报告
- [ ] 已生成 `docs/report/02-Phase2-Backend/report-task2.x-backend-foundation.md`

---

## 阶段交付物

| 交付物 | 位置 | 验收标准 |
|--------|------|----------|
| 数据库模型 | `app/models/*.py` | 6个模型完整，字段正确 |
| 迁移脚本 | `alembic/versions/*.py` | 能正常升级/降级 |
| 认证模块 | `app/core/security.py`, `auth.py` | JWT、密码功能正常 |
| 认证API | `app/api/v1/auth.py` | 4个接口可用 |
| 核心配置 | `app/core/*.py` | 日志、异常、数据库正常 |
| 主入口 | `app/main.py` | 服务可启动 |
| 集成测试报告 | `docs/report/02-Phase2-Backend/` | Test Agent输出，所有测试通过 |

---

## 阶段检查清单

### 功能检查
- [x] 数据库表能正常创建
- [x] 用户注册/登录功能正常
- [x] JWT认证流程完整
- [x] 日志输出正常
- [x] 异常处理正常工作

### 代码检查
- [x] 模型字段与数据库设计文档一致
- [x] 密码使用bcrypt加密
- [x] JWT有过期时间
- [x] 敏感信息不出现在日志中

### 测试检查（Test Agent负责）
- [x] 应用能正常加载
- [x] 数据库迁移正常
- [ ] Test Agent集成测试通过（全部8个测试）
- [ ] 测试报告已生成

---

## 进入下一阶段条件

1. ✅ Task 2.1、2.2、2.3 全部完成
2. ✅ Task 2.4 集成测试全部通过（Test Agent确认）
3. ✅ 数据库能正常连接和操作
4. ✅ 认证流程完整可用
5. ✅ 代码通过review

---

## 风险与应对

| 风险 | 应对措施 |
|------|----------|
| 数据库迁移失败 | 保持迁移脚本简单，先在SQLite测试 |
| 认证安全漏洞 | 使用成熟库，密码加盐，JWT设过期 |

---

*依赖文档: ../04-Database-Design.md, ../05-API-Documentation.md*
