# API接口文档

## 1. 概述

### 1.1 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `/api/v1` |
| 协议 | HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | JWT Token |

### 1.2 认证方式

所有需要认证的接口需在请求头中携带 JWT Token：

```http
Authorization: Bearer {token}
```

### 1.3 通用响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | integer | 状态码，200表示成功 |
| message | string | 提示信息 |
| data | object/array | 响应数据 |

### 1.4 通用分页参数

列表接口支持以下分页参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码，从1开始 |
| page_size | integer | 否 | 20 | 每页数量，最大100 |

分页响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

### 1.5 通用错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权，Token无效或过期 |
| 403 | 禁止访问，权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 请求实体无法处理 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 2. 用户认证模块

### 2.1 用户注册

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/auth/register` |
| 方法 | POST |
| 认证 | 否 |
| 说明 | 新用户注册 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名，3-20字符，字母开头 |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码，8-32字符，需包含字母和数字 |

**请求示例**

```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "Pass1234"
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| role | string | 用户角色：admin/user |
| status | string | 状态：active/disabled |
| created_at | string | 创建时间，ISO 8601格式 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "role": "user",
    "status": "active",
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

**错误响应**

```json
{
  "code": 409,
  "message": "用户名已存在",
  "data": null
}
```

---

### 2.2 用户登录

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/auth/login` |
| 方法 | POST |
| 认证 | 否 |
| 说明 | 用户登录获取Token |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

**请求示例**

```json
{
  "username": "zhangsan",
  "password": "Pass1234"
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| access_token | string | JWT访问令牌 |
| refresh_token | string | 刷新令牌 |
| expires_in | integer | 访问令牌有效期（秒） |
| user | object | 用户信息 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "zhangsan",
      "email": "zhangsan@example.com"
    }
  }
}
```

**错误响应**

```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

---

### 2.3 用户登出

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/auth/logout` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 用户登出，使Token失效 |

**请求参数**

无

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 2.4 获取当前用户

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/auth/me` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取当前登录用户信息 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| role | string | 用户角色：admin/user |
| status | string | 状态：active/disabled |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "role": "user",
    "status": "active",
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-01-15T08:30:00Z"
  }
}
```

---

### 2.5 修改密码

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/auth/password` |
| 方法 | PUT |
| 认证 | 是 |
| 说明 | 修改当前用户密码 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 原密码 |
| new_password | string | 是 | 新密码，8-32字符 |

**请求示例**

```json
{
  "old_password": "Pass1234",
  "new_password": "NewPass5678"
}
```

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 3. 数据库连接管理模块

### 3.1 获取连接列表

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取当前用户的数据库连接列表 |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |
| name | string | 连接名称 |
| db_type | string | 数据库类型 |
| host | string | 主机地址 |
| port | integer | 端口号 |
| database | string | 数据库名 |
| status | string | 连接状态：active/inactive/error |
| created_at | string | 创建时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "生产数据库",
        "db_type": "mysql",
        "host": "192.168.1.100",
        "port": 3306,
        "database": "production",
        "is_active": true,
        "created_at": "2024-01-15T08:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

---

### 3.2 创建连接

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 添加新的数据库连接 |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| name | string | 是 | - | 连接名称 |
| db_type | string | 是 | - | 数据库类型：mysql/postgresql/sqlite/sqlserver/oracle |
| host | string | 是 | - | 主机地址 |
| port | integer | 是 | - | 端口号 |
| database | string | 是 | - | 数据库名 |
| username | string | 是 | - | 数据库用户名 |
| password | string | 是 | - | 数据库密码 |
| options | object | 否 | {} | 额外连接参数 |

**请求示例**

```json
{
  "name": "生产数据库",
  "db_type": "mysql",
  "host": "192.168.1.100",
  "port": 3306,
  "database": "production",
  "username": "admin",
  "password": "db_password",
  "options": {
    "charset": "utf8mb4",
    "ssl": false
  }
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |
| name | string | 连接名称 |
| db_type | string | 数据库类型 |
| status | string | 连接状态：active/inactive/error |
| created_at | string | 创建时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "生产数据库",
    "db_type": "mysql",
    "status": "active",
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

---

### 3.3 测试连接

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections/test` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 测试数据库连接是否可用 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| db_type | string | 是 | 数据库类型 |
| host | string | 是 | 主机地址 |
| port | integer | 是 | 端口号 |
| database | string | 是 | 数据库名 |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| options | object | 否 | 额外参数 |

**请求示例**

```json
{
  "db_type": "mysql",
  "host": "192.168.1.100",
  "port": 3306,
  "database": "production",
  "username": "admin",
  "password": "db_password"
}
```

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "connected": true,
    "message": "连接成功",
    "server_version": "8.0.32"
  }
}
```

**错误响应**

```json
{
  "code": 400,
  "message": "连接失败",
  "data": {
    "connected": false,
    "message": "无法连接到数据库：Connection refused"
  }
}
```

---

### 3.4 获取连接详情

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections/{id}` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取单个连接详情 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |
| name | string | 连接名称 |
| db_type | string | 数据库类型 |
| host | string | 主机地址（脱敏） |
| port | integer | 端口号 |
| database | string | 数据库名 |
| username | string | 用户名（脱敏） |
| status | string | 连接状态：active/inactive/error |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "生产数据库",
    "db_type": "mysql",
    "host": "192.168.1.***",
    "port": 3306,
    "database": "production",
    "username": "ad***",
    "status": "active",
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-01-15T08:30:00Z"
  }
}
```

---

### 3.5 更新连接

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections/{id}` |
| 方法 | PUT |
| 认证 | 是 |
| 说明 | 更新连接信息 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 连接名称 |
| host | string | 否 | 主机地址 |
| port | integer | 否 | 端口号 |
| database | string | 否 | 数据库名 |
| username | string | 否 | 用户名 |
| password | string | 否 | 密码 |
| options | object | 否 | 额外参数 |

**请求示例**

```json
{
  "name": "生产数据库-更新",
  "host": "192.168.1.101"
}
```

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "生产数据库-更新",
    "updated_at": "2024-01-15T09:00:00Z"
  }
}
```

---

### 3.6 删除连接

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections/{id}` |
| 方法 | DELETE |
| 认证 | 是 |
| 说明 | 删除数据库连接 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 3.7 获取Schema

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections/{id}/schema` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取数据库Schema信息 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| refresh | boolean | 否 | false | 是否强制刷新缓存 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| tables | array | 表列表 |
| tables[].name | string | 表名 |
| tables[].columns | array | 字段列表 |
| tables[].columns[].name | string | 字段名 |
| tables[].columns[].type | string | 字段类型 |
| tables[].columns[].nullable | boolean | 是否可空 |
| tables[].columns[].default | string | 默认值 |
| tables[].columns[].comment | string | 字段注释 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tables": [
      {
        "name": "users",
        "comment": "用户表",
        "columns": [
          {
            "name": "id",
            "type": "INT",
            "nullable": false,
            "default": null,
            "comment": "主键ID"
          },
          {
            "name": "username",
            "type": "VARCHAR(50)",
            "nullable": false,
            "default": null,
            "comment": "用户名"
          }
        ]
      }
    ]
  }
}
```

---

### 3.8 刷新Schema

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/connections/{id}/schema/refresh` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 强制刷新Schema缓存 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 连接ID |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "refreshed_at": "2024-01-15T09:30:00Z",
    "table_count": 15
  }
}
```

---

## 4. Text-to-SQL核心模块

### 4.1 自然语言转SQL

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/queries/generate` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 将自然语言转换为SQL |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| connection_id | integer | 是 | - | 数据库连接ID |
| question | string | 是 | - | 自然语言问题 |
| model | string | 否 | "default" | 使用的AI模型 |
| context | object | 否 | {} | 额外上下文信息 |

**请求示例**

```json
{
  "connection_id": 1,
  "question": "查询最近7天注册的用户数量",
  "model": "gpt-4",
  "context": {
    "time_range": "last_7_days"
  }
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| sql | string | 生成的SQL语句 |
| explanation | string | SQL解释说明 |
| confidence | float | 置信度，0-1之间 |
| execution_time | integer | 生成耗时（毫秒） |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sql": "SELECT COUNT(*) FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
    "explanation": "查询用户表中创建时间在过去7天内的记录数量",
    "confidence": 0.95,
    "execution_time": 1250
  }
}
```

---

### 4.2 执行SQL

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/queries/execute` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 执行SQL并返回结果 |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| connection_id | integer | 是 | - | 数据库连接ID |
| sql | string | 是 | - | 要执行的SQL |
| limit | integer | 否 | 1000 | 结果行数限制 |
| timeout | integer | 否 | 30 | 超时时间（秒） |

**请求示例**

```json
{
  "connection_id": 1,
  "sql": "SELECT COUNT(*) as count FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
  "limit": 1000,
  "timeout": 30
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| columns | array | 列名列表 |
| rows | array | 数据行 |
| row_count | integer | 返回行数 |
| execution_time | integer | 执行耗时（毫秒） |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "columns": ["count"],
    "rows": [[156]],
    "row_count": 1,
    "execution_time": 45
  }
}
```

**错误响应**

```json
{
  "code": 400,
  "message": "SQL执行错误",
  "data": {
    "error": "Unknown column 'create_at' in 'where clause'",
    "sql": "SELECT COUNT(*) FROM users WHERE create_at >= ..."
  }
}
```

---

### 4.3 生成并执行

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/queries/run` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 一站式生成SQL并执行 |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| connection_id | integer | 是 | - | 数据库连接ID |
| question | string | 是 | - | 自然语言问题 |
| model | string | 否 | "default" | AI模型 |
| limit | integer | 否 | 1000 | 结果限制 |

**请求示例**

```json
{
  "connection_id": 1,
  "question": "查询最近7天注册的用户数量",
  "model": "gpt-4",
  "limit": 1000
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| sql | string | 生成的SQL |
| explanation | string | SQL解释 |
| confidence | float | 置信度 |
| result | object | 执行结果 |
| result.columns | array | 列名 |
| result.rows | array | 数据行 |
| result.row_count | integer | 行数 |
| total_time | integer | 总耗时（毫秒） |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sql": "SELECT COUNT(*) FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
    "explanation": "查询过去7天内注册的用户数量",
    "confidence": 0.95,
    "result": {
      "columns": ["count"],
      "rows": [[156]],
      "row_count": 1
    },
    "total_time": 1295
  }
}
```

---

## 5. 查询历史模块

### 5.1 获取历史列表

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/history` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 分页获取查询历史 |

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |
| connection_id | integer | 否 | - | 按连接筛选 |
| is_favorite | boolean | 否 | - | 按收藏筛选 |
| keyword | string | 否 | - | 关键词搜索 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 历史记录ID |
| connection_id | integer | 连接ID |
| connection_name | string | 连接名称 |
| question | string | 自然语言问题 |
| sql | string | 生成的SQL |
| execution_status | string | 执行状态：pending/success/failed |
| execution_status | string | 执行状态：pending/success/failed |
| is_favorite | boolean | 是否收藏 |
| created_at | string | 创建时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "connection_id": 1,
        "connection_name": "生产数据库",
        "question": "查询最近7天注册的用户数量",
        "sql": "SELECT COUNT(*) FROM users...",
        "execution_status": "success",
        "is_favorite": true,
        "created_at": "2024-01-15T08:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 50,
      "total_pages": 3
    }
  }
}
```

---

### 5.2 获取历史详情

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/history/{id}` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取单个查询详情 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 历史记录ID |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 历史记录ID |
| connection_id | integer | 连接ID |
| question | string | 自然语言问题 |
| sql | string | 生成的SQL |
| explanation | string | SQL解释 |
| confidence | float | 置信度 |
| result_preview | object | 结果预览 |
| execution_status | string | 执行状态：pending/success/failed |
| error_message | string | 错误信息（如执行失败） |
| is_favorite | boolean | 是否收藏 |
| created_at | string | 创建时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "connection_id": 1,
    "question": "查询最近7天注册的用户数量",
    "sql": "SELECT COUNT(*) FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
    "explanation": "查询过去7天内注册的用户数量",
    "confidence": 0.95,
    "result_preview": {
      "columns": ["count"],
      "rows": [[156]]
    },
    "execution_status": "success",
    "error_message": null,
    "is_favorite": true,
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

---

### 5.3 删除历史

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/history/{id}` |
| 方法 | DELETE |
| 认证 | 是 |
| 说明 | 删除查询记录 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 历史记录ID |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 5.4 收藏/取消收藏

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/history/{id}/favorite` |
| 方法 | PUT |
| 认证 | 是 |
| 说明 | 切换收藏状态 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 历史记录ID |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_favorite | boolean | 是 | 收藏状态 |

**请求示例**

```json
{
  "is_favorite": true
}
```

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "is_favorite": true
  }
}
```

---

## 6. 评测管理模块

### 6.1 创建评测任务

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 创建新的评测任务 |

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| name | string | 是 | - | 任务名称 |
| connection_id | integer | 是 | - | 数据库连接ID |
| dataset_type | string | 是 | - | 数据集类型：bird/spider/custom |
| dataset_path | string | 否 | - | 自定义数据集路径 |
| model_config | object | 是 | - | 模型配置（模型名称、参数等） |
| model_config.model | string | 否 | "default" | 模型名称 |
| eval_mode | string | 否 | "greedy_search" | 评估模式：greedy_search/major_voting/pass@k |
| config.voting_count | integer | 否 | 5 | 投票次数 |

**请求示例**

```json
{
  "name": "Spider评测-2024",
  "connection_id": 1,
  "dataset_type": "spider",
  "dataset_path": "spider/dev.json",
  "model_config": {
    "model": "gpt-4",
    "temperature": 0.0
  },
  "eval_mode": "major_voting"
}
```

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |
| name | string | 任务名称 |
| status | string | 状态：pending/running/completed/failed |
| created_at | string | 创建时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "Spider评测-2024",
    "status": "pending",
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

---

### 6.2 获取任务列表

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取评测任务列表 |

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |
| status | string | 否 | - | 按状态筛选 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |
| name | string | 任务名称 |
| status | string | 任务状态：pending/running/completed/failed/cancelled |
| dataset_type | string | 数据集类型 |
| eval_mode | string | 评估模式 |
| progress | object | 进度信息 |
| progress.total | integer | 总问题数 |
| progress.processed | integer | 已处理问题数 |
| progress.correct | integer | 正确数 |
| progress.percentage | integer | 进度百分比（0-100） |
| created_at | string | 创建时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "Spider评测-2024",
        "status": "running",
        "progress": {
          "total": 1000,
          "processed": 350,
          "correct": 280,
          "percentage": 35
        },
        "created_at": "2024-01-15T08:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5,
      "total_pages": 1
    }
  }
}
```

---

### 6.3 获取任务详情

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks/{id}` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取任务详情和进度 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |
| name | string | 任务名称 |
| status | string | 任务状态：pending/running/completed/failed/cancelled |
| connection_id | integer | 连接ID |
| dataset_type | string | 数据集类型 |
| eval_mode | string | 评估模式 |
| model_config | object | 模型配置 |
| progress | object | 进度详情 |
| progress.total | integer | 总问题数 |
| progress.processed | integer | 已处理问题数 |
| progress.correct | integer | 正确数 |
| progress.percentage | integer | 进度百分比 |
| started_at | string | 开始时间 |
| completed_at | string | 完成时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "Spider评测-2024",
    "status": "running",
    "connection_id": 1,
    "dataset_type": "spider",
    "eval_mode": "major_voting",
    "model_config": {
      "model": "gpt-4",
      "temperature": 0.0
    },
    "progress": {
      "total": 1000,
      "processed": 350,
      "correct": 280,
      "percentage": 35
    },
    "started_at": "2024-01-15T08:31:00Z",
    "completed_at": null
  }
}
```

---

### 6.4 获取评测结果

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks/{id}/results` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取评测结果（分页） |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |
| is_correct | boolean | 否 | - | 按正确性筛选 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 结果ID |
| question_id | string | 问题ID |
| question | string | 自然语言问题 |
| gold_sql | string | 标准SQL |
| predicted_sql | string | 预测SQL |
| is_correct | boolean | 是否正确（EX匹配） |
| error_type | string | 错误类型：syntax/execution/logic/timeout/generation |
| error_message | string | 错误详情 |
| execution_time_ms | float | 执行时间（毫秒） |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "question_id": "dev_001",
        "question": "查询所有用户的平均年龄",
        "gold_sql": "SELECT AVG(age) FROM users",
        "predicted_sql": "SELECT AVG(age) FROM users",
        "is_correct": true,
        "error_message": null,
        "execution_time": 1250
      },
      {
        "id": 2,
        "question_id": "dev_002",
        "question": "查询订单数量大于100的客户",
        "gold_sql": "SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*) > 100",
        "predicted_sql": "SELECT customer_id FROM orders WHERE count > 100",
        "is_correct": false,
        "error_message": "SQL执行错误",
        "execution_time": 980
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1000,
      "total_pages": 50
    }
  }
}
```

---

### 6.5 获取统计信息

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks/{id}/stats` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取准确率统计 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| total | integer | 总问题数 |
| correct | integer | 正确数 |
| incorrect | integer | 错误数 |
| failed | integer | 执行失败数 |
| accuracy | float | EX准确率 |
| execution_accuracy | float | 执行准确率 |
| by_difficulty | object | 按难度统计 |
| by_difficulty.easy | object | 简单题统计 |
| by_difficulty.medium | object | 中等题统计 |
| by_difficulty.hard | object | 难题统计 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 1000,
    "correct": 750,
    "incorrect": 230,
    "failed": 20,
    "accuracy": 0.75,
    "execution_accuracy": 0.77,
    "by_difficulty": {
      "easy": {
        "total": 300,
        "correct": 280,
        "accuracy": 0.933
      },
      "medium": {
        "total": 400,
        "correct": 310,
        "accuracy": 0.775
      },
      "hard": {
        "total": 300,
        "correct": 160,
        "accuracy": 0.533
      }
    }
  }
}
```

---

### 6.6 取消评测任务

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks/{id}/cancel` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 取消运行中的任务 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "status": "cancelled"
  }
}
```

---

### 6.7 删除评测任务

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/eval/tasks/{id}` |
| 方法 | DELETE |
| 认证 | 是 |
| 说明 | 删除评测任务 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务ID |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 7. API密钥管理模块

### 7.1 获取密钥列表

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/keys` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取用户的API密钥列表 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 密钥ID |
| name | string | 密钥名称/描述 |
| key_type | string | 密钥类型：openai/alibaba/anthropic/azure_openai/local |
| model | string | 模型名称 |
| is_default | boolean | 是否为默认密钥 |
| created_at | string | 创建时间 |
| last_used_at | string | 最后使用时间 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "阿里云通义",
      "key_type": "alibaba",
      "model": "qwen3.5-plus",
      "is_default": true,
      "created_at": "2024-01-15T08:30:00Z",
      "last_used_at": "2024-01-15T09:00:00Z"
    }
  ]
}
```

---

### 7.2 添加密钥

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/keys` |
| 方法 | POST |
| 认证 | 是 |
| 说明 | 添加新的API密钥 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 密钥名称/描述 |
| key_type | string | 是 | 密钥类型：openai/alibaba/anthropic/azure_openai/local |
| api_key | string | 是 | API密钥（加密存储） |
| model | string | 否 | 默认模型 |
| is_default | boolean | 否 | false | 是否设为默认密钥 |
| base_url | string | 否 | 自定义API地址 |

**请求示例**

```json
{
  "name": "阿里云通义",
  "key_type": "alibaba",
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "model": "qwen3.5-plus",
  "is_default": true,
  "base_url": "https://dashscope.aliyuncs.com/api/v1"
}
```

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "阿里云通义",
    "key_type": "alibaba",
    "is_default": true,
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

---

### 7.3 删除密钥

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/keys/{id}` |
| 方法 | DELETE |
| 认证 | 是 |
| 说明 | 删除API密钥 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 密钥ID |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 8. 系统模块

### 8.1 健康检查

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/health` |
| 方法 | GET |
| 认证 | 否 |
| 说明 | 系统健康状态检查 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态：healthy/degraded/unhealthy |
| version | string | 系统版本 |
| timestamp | string | 检查时间 |
| services | object | 各服务状态 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-01-15T08:30:00Z",
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "ai_service": "healthy"
    }
  }
}
```

---

### 8.2 获取配置

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/config` |
| 方法 | GET |
| 认证 | 是 |
| 说明 | 获取系统配置 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| version | string | 系统版本 |
| features | object | 功能开关 |
| limits | object | 限制配置 |
| limits.max_connections | integer | 最大连接数 |
| limits.max_query_timeout | integer | 最大查询超时 |
| limits.max_result_rows | integer | 最大结果行数 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "version": "1.0.0",
    "features": {
      "text_to_sql": true,
      "evaluation": true,
      "api_keys": true
    },
    "limits": {
      "max_connections": 10,
      "max_query_timeout": 60,
      "max_result_rows": 10000
    }
  }
}
```

---

### 8.3 获取数据库类型列表

**接口信息**

| 项目 | 内容 |
|------|------|
| 路径 | `/api/v1/db-types` |
| 方法 | GET |
| 认证 | 否 |
| 说明 | 获取支持的数据库类型 |

**响应参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 类型标识：mysql/postgresql/sqlite/sqlserver/oracle |
| name | string | 显示名称 |
| default_port | integer | 默认端口 |
| icon | string | 图标标识 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "mysql",
      "name": "MySQL",
      "default_port": 3306,
      "icon": "mysql"
    },
    {
      "id": "postgresql",
      "name": "PostgreSQL",
      "default_port": 5432,
      "icon": "postgresql"
    },
    {
      "id": "sqlite",
      "name": "SQLite",
      "default_port": null,
      "icon": "sqlite"
    }
  ]
}
```

---

## 9. 附录

### 9.1 完整错误码表

| 错误码 | 英文标识 | 说明 |
|--------|----------|------|
| 200 | OK | 成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权，Token无效或过期 |
| 403 | Forbidden | 禁止访问，权限不足 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如用户名已存在） |
| 422 | Unprocessable Entity | 请求实体无法处理 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务不可用 |
| 1001 | Invalid Credentials | 用户名或密码错误 |
| 1002 | Token Expired | Token已过期 |
| 1003 | Invalid Token | Token无效 |
| 2001 | Connection Failed | 数据库连接失败 |
| 2002 | SQL Syntax Error | SQL语法错误 |
| 2003 | Query Timeout | 查询超时 |
| 3001 | AI Service Error | AI服务调用失败 |
| 3002 | Rate Limit Exceeded | AI调用频率超限 |
| 4001 | Evaluation In Progress | 评测任务进行中 |
| 4002 | Evaluation Cancelled | 评测任务已取消 |
| 4003 | Evaluation Failed | 评测任务执行失败 |

### 9.2 数据类型对照表

| JSON类型 | 说明 | 示例 |
|----------|------|------|
| string | 字符串 | "hello" |
| integer | 整数 | 42 |
| float | 浮点数 | 3.14 |
| boolean | 布尔值 | true/false |
| array | 数组 | [1, 2, 3] |
| object | 对象 | {"key": "value"} |
| null | 空值 | null |

### 9.3 时间格式说明

所有时间字段均采用 ISO 8601 格式：

```
YYYY-MM-DDTHH:mm:ssZ
```

示例：`2024-01-15T08:30:00Z`
