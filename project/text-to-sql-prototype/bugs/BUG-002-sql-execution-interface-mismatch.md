# BUG-002: SQL 执行接口前后端不匹配

## 基本信息

| 字段 | 内容 |
|------|------|
| **Bug ID** | BUG-002 |
| **模块** | 查询功能 (Query Module) |
| **页面** | `/query` |
| **严重级别** | 🔴 High |
| **优先级** | P0 |
| **发现日期** | 2026-03-13 |
| **发现人** | E2E Tester (Claude Code) |
| **修复日期** | 2026-03-13 |
| **修复人** | Claude Code |
| **状态** | ✅ Closed (Fixed) |

---

## 问题描述

SQL 执行成功后，前端无法正确显示结果，报错 `Cannot read properties of undefined (reading 'map')`。

---

## 复现步骤

1. 登录系统并访问查询页面 `/query`
2. 选择数据库连接（如 PG-Test）
3. 输入自然语言问题，例如："查询所有用户的信息"
4. 点击"生成 SQL"按钮，等待 SQL 生成成功
5. 点击"执行"按钮
6. 观察页面报错

---

## 期望行为

- SQL 执行成功
- 显示结果表格，包含用户数据
- 显示执行元信息（行数、时间）

---

## 实际行为

- 后端 SQL 执行成功
- 前端报错：`Cannot read properties of undefined (reading 'map')`
- 结果表格未显示

---

## 根本原因分析

### 后端响应格式 (实际)

```json
{
  "success": true,
  "query_id": 1,
  "sql": "SELECT * FROM users;",
  "result": {
    "columns": ["id", "name", "email", "age", "department_id"],
    "rows": [
      {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 28, "department_id": 1},
      {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 32, "department_id": 2},
      {"id": 3, "name": "王五", "email": "wangwu@example.com", "age": 25, "department_id": 1}
    ],
    "total_rows": 3,
    "truncated": false,
    "displayed_rows": 3
  },
  "execution_time_ms": 45.23
}
```

### 前端期望格式

```typescript
interface ExecuteSQLResponse {
  columns: string[]
  rows: unknown[][]  // 二维数组，不是对象数组
  row_count: number
  execution_time: number
}
```

### 不匹配点

| 字段 | 后端 | 前端 | 问题 |
|------|------|------|------|
| 数据结构 | `result` 对象包裹 | 根级别 | ❌ 不匹配 |
| rows 格式 | 对象数组 `Dict[]` | 二维数组 `unknown[][]` | ❌ 不匹配 |
| 时间字段 | `execution_time_ms` | `execution_time` | ⚠️ 命名不同 |
| 行数字段 | `result.total_rows` | `row_count` | ❌ 不匹配 |

---

## 相关代码

### 后端代码

**文件**: `backend/app/schemas/query.py`
```python
class QueryExecuteResponse(BaseModel):
    success: bool
    query_id: int
    sql: str
    result: Optional[QueryResultData] = None  # 包裹在 result 中
    execution_time_ms: float = 0
    error: Optional[str] = None
```

### 前端代码

**文件**: `frontend/src/types/index.ts`
```typescript
export interface ExecuteSQLResponse {
  columns: string[]
  rows: unknown[][]
  row_count: number
  execution_time: number
}
```

**文件**: `frontend/src/views/QueryView.vue`
```typescript
const response = await queryApi.executeSQL({...})
const rows = response.rows.map((row: unknown[]) => {  // 直接访问 response.rows
  // ...
})
```

---

## 修复方案

### 方案 1: 修改后端响应格式 (推荐)

修改 `backend/app/schemas/query.py` 和 `backend/app/api/v1/queries.py`，使响应格式与前端期望一致：

```python
class QueryExecuteResponse(BaseModel):
    success: bool
    query_id: int
    sql: str
    columns: List[str] = []  # 提升到根级别
    rows: List[List[Any]] = []  # 改为二维数组
    row_count: int = 0
    execution_time: float = 0  # 改名
    error: Optional[str] = None
```

### 方案 2: 修改前端处理逻辑

修改 `frontend/src/views/QueryView.vue`，适配后端格式：

```typescript
const response = await queryApi.executeSQL({...})
const rows = response.result?.rows?.map((row: Record<string, unknown>) => {
  return response.result!.columns.map(col => row[col])
}) ?? []
```

同时更新类型定义：

```typescript
export interface ExecuteSQLResponse {
  success: boolean
  query_id: number
  sql: string
  result?: {
    columns: string[]
    rows: Record<string, unknown>[]
    total_rows: number
    truncated: boolean
    displayed_rows: number
  }
  execution_time_ms: number
  error?: string
}
```

---

## 修复记录

| 字段 | 内容 |
|------|------|
| **修复日期** | 2026-03-13 |
| **修复人** | backend-fixer (Agent Team) |
| **修复方案** | 修改后端 API 响应格式，添加前端期望的根级别字段 |

### 修改的文件

1. **backend/app/schemas/query.py**
   - 修改 `QueryExecuteResponse` - 添加前端兼容字段
   - 修改 `QueryRunResponse` - 添加前端兼容字段

2. **backend/app/api/v1/queries.py**
   - 修改 `execute_sql_endpoint` - 添加 rows 转换逻辑
   - 修改 `run_query_endpoint` - 添加 rows 转换逻辑

### 核心修改

**后端 Schema 修改：**
```python
# QueryExecuteResponse 和 QueryRunResponse 新增字段
columns: List[str] = Field(default_factory=list)
rows: List[List[Any]] = Field(default_factory=list)  # 二维数组
row_count: int = 0
execution_time: float = 0
```

**Rows 转换逻辑：**
```python
# 将后端的对象数组转换为前端的二维数组
columns = result["columns"]
rows_2d = []
for row_obj in result["rows"]:
    row_list = [row_obj.get(col) for col in columns]
    rows_2d.append(row_list)
```

---

## 修复验证状态

| 验证项 | 状态 | 说明 |
|--------|------|------|
| 后端代码修复 | ✅ 完成 | 已修改 schema 和 endpoint |
| 后端单元测试 | ✅ 通过 | SQL 执行服务正常 |
| 前端代码修复 | ✅ 完成 | 已修改 QueryView.vue 和 types |
| E2E 测试 | ✅ 通过 | 2026-03-13 验证成功 |

### 2026-03-13 更新 - BUG 修复完成

**E2E 验证结果**:
- SQL 生成成功: `SELECT * FROM users;`
- SQL 执行成功: "查询成功，9 行"
- 结果表格正确显示所有列和数据
- 执行时间正确显示: 3.87ms
- 导出按钮（CSV/JSON）正常显示

**修复文件总结**:

1. **后端**: `backend/app/schemas/query.py`
   - `QueryExecuteResponse` 添加根级别 `rows`, `columns` 字段
   - `QueryRunResponse` 添加相同字段

2. **后端**: `backend/app/api/v1/queries.py`
   - `execute_sql_endpoint` 添加 rows 转换逻辑
   - `run_query_endpoint` 添加相同转换

3. **前端**: `frontend/src/views/QueryView.vue`
   - 从 `response.result` 或 `response` 中提取数据
   - 支持二维数组和对象数组两种 rows 格式
   - 兼容 `execution_time_ms` 和 `execution_time` 两种时间字段

4. **前端**: `frontend/src/types/index.ts`
   - 更新 `ExecuteSQLResponse` 接口，添加可选字段
   - 支持嵌套 `result` 对象格式

5. **前端**: `frontend/src/utils/request.ts`
   - 修复响应拦截器，正确处理没有 `code` 字段的响应

---

## 修复验证清单

- [ ] SQL 执行后正确显示结果表格
- [ ] 结果数据正确（行数、列数）
- [ ] 列名正确显示
- [ ] 执行时间显示正确
- [ ] 大数据量结果分页正常

---

## 相关文档

- [BUG-001: SQL 生成结果未显示](./BUG-001-sql-generation-result-not-displayed.md)
- [查询模块测试规范](../e2e/specs/03-Query-Test-Spec.md)

---

*创建时间: 2026-03-13*
*版本: v1.0*
