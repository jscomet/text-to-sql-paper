// 通用响应类型
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 分页响应类型
export interface PaginationData<T> {
  list: T[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

// 分页请求参数
export interface PaginationParams {
  page?: number
  page_size?: number
}

// 用户类型
export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  status: 'active' | 'disabled'
  created_at: string
  updated_at?: string
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  user: {
    id: number
    username: string
    email: string
  }
}

// 注册请求
export interface RegisterRequest {
  username: string
  email: string
  password: string
}

// 注册响应
export interface RegisterResponse {
  id: number
  username: string
  email: string
  role: string
  status: string
  created_at: string
}

// 修改密码请求
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

// 数据库连接类型
export type DBType = 'mysql' | 'postgresql' | 'sqlite' | 'sqlserver' | 'oracle'

export interface Connection {
  id: number
  name: string
  db_type: DBType
  host: string
  port: number
  database: string
  username?: string
  status: 'active' | 'inactive' | 'error'
  is_active?: boolean
  created_at: string
  updated_at?: string
}

export interface ConnectionDetail extends Connection {
  password?: string
  options?: Record<string, unknown>
}

// 创建连接请求
export interface CreateConnectionRequest {
  name: string
  db_type: DBType
  host: string
  port: number
  database: string
  username: string
  password: string
  options?: Record<string, unknown>
}

// 更新连接请求
export interface UpdateConnectionRequest {
  name?: string
  host?: string
  port?: number
  database?: string
  username?: string
  password?: string
  options?: Record<string, unknown>
}

// 测试连接请求
export interface TestConnectionRequest {
  db_type: DBType
  host: string
  port: number
  database: string
  username: string
  password: string
  options?: Record<string, unknown>
}

// 测试连接响应
export interface TestConnectionResponse {
  connected: boolean
  message: string
  server_version?: string
}

// Schema 类型
export interface Column {
  name: string
  type: string
  nullable: boolean
  default: string | null
  comment: string
}

export interface Table {
  name: string
  comment?: string
  columns: Column[]
}

export interface SchemaResponse {
  tables: Table[]
}

// 查询相关类型
export interface GenerateSQLRequest {
  connection_id: number
  question: string
  model?: string
  context?: Record<string, unknown>
}

export interface GenerateSQLResponse {
  sql: string
  explanation: string
  confidence: number
  execution_time: number
}

export interface ExecuteSQLRequest {
  connection_id: number
  sql: string
  limit?: number
  timeout?: number
}

export interface ExecuteSQLResponse {
  // 后端直接返回的字段
  success?: boolean
  query_id?: number
  sql?: string
  error?: string
  execution_time_ms?: number

  // 兼容字段（根级别或 result 内部）
  columns?: string[]
  rows?: unknown[] | unknown[][]
  row_count?: number
  execution_time?: number
  total_rows?: number

  // 嵌套结果对象
  result?: {
    columns: string[]
    rows: unknown[] | unknown[][]
    total_rows: number
    truncated: boolean
    displayed_rows: number
  }
}

export interface RunQueryRequest {
  connection_id: number
  question: string
  model?: string
  limit?: number
}

export interface RunQueryResponse {
  sql: string
  explanation: string
  confidence: number
  result: {
    columns: string[]
    rows: unknown[][]
    row_count: number
  }
  total_time: number
}

// 查询历史类型
export interface QueryHistory {
  id: number
  connection_id: number
  connection_name?: string
  question: string
  sql: string
  explanation?: string
  confidence?: number
  result_preview?: {
    columns: string[]
    rows: unknown[][]
  } | null
  execution_status: 'pending' | 'success' | 'failed'
  error_message?: string | null
  is_favorite: boolean
  created_at: string
}

export interface QueryHistoryParams extends PaginationParams {
  connection_id?: number
  is_favorite?: boolean
  keyword?: string
}

export interface ToggleFavoriteRequest {
  is_favorite: boolean
}

// 从 eval.ts 重新导出评测相关类型
export * from './eval'

// API Key 类型
export type FormatType = 'openai' | 'anthropic' | 'vllm'
export type KeyType = 'openai' | 'alibaba' | 'anthropic' | 'azure_openai' | 'local'

export interface ApiKey {
  id: number
  provider: string
  base_url?: string
  model?: string
  format_type: FormatType
  description?: string
  is_default: boolean
  created_at: string
  last_used_at?: string
}

export interface CreateApiKeyRequest {
  provider: string
  key: string
  base_url?: string
  model?: string
  format_type?: FormatType
  description?: string
  is_default?: boolean
}

// 系统配置类型
export interface SystemConfig {
  version: string
  features: {
    text_to_sql: boolean
    evaluation: boolean
    api_keys: boolean
  }
  limits: {
    max_connections: number
    max_query_timeout: number
    max_result_rows: number
  }
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  timestamp: string
  services: Record<string, string>
}

export interface DBTypeInfo {
  id: DBType
  name: string
  default_port: number | null
  icon: string
}
