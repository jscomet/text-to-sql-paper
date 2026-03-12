import request from '@/utils/request'
import type {
  Connection,
  ConnectionDetail,
  CreateConnectionRequest,
  UpdateConnectionRequest,
  TestConnectionRequest,
  TestConnectionResponse,
  SchemaResponse,
  PaginationParams,
  PaginationData,
} from '@/types'

// ==================== 类型导出 ====================

export type DbType = 'mysql' | 'postgresql' | 'sqlite' | 'sqlserver' | 'oracle'
export type ConnectionStatus = 'active' | 'inactive' | 'error'
export type CreateConnectionParams = CreateConnectionRequest
export type UpdateConnectionParams = UpdateConnectionRequest
export type TestConnectionParams = TestConnectionRequest
export type TestConnectionResult = TestConnectionResponse
export type SchemaInfo = SchemaResponse
export interface RefreshSchemaResult {
  refreshed_at: string
  table_count: number
}
export type ConnectionListResponse = PaginationData<Connection>

// ==================== API 函数 ====================

/**
 * 获取数据库连接列表
 * @param params 分页参数
 */
export const getConnections = (params?: PaginationParams): Promise<ConnectionListResponse> => {
  return request.get('/connections', { params }) as Promise<ConnectionListResponse>
}

/**
 * 获取单个连接详情
 * @param id 连接ID
 */
export const getConnection = (id: number): Promise<ConnectionDetail> => {
  return request.get(`/connections/${id}`) as Promise<ConnectionDetail>
}

/**
 * 创建数据库连接
 * @param data 连接参数
 */
export const createConnection = (data: CreateConnectionParams): Promise<Connection> => {
  return request.post('/connections', data) as Promise<Connection>
}

/**
 * 更新数据库连接
 * @param id 连接ID
 * @param data 更新参数
 */
export const updateConnection = (id: number, data: UpdateConnectionParams): Promise<Connection> => {
  return request.put(`/connections/${id}`, data) as Promise<Connection>
}

/**
 * 删除数据库连接
 * @param id 连接ID
 */
export const deleteConnection = (id: number): Promise<void> => {
  return request.delete(`/connections/${id}`) as Promise<void>
}

/**
 * 测试数据库连接
 * @param data 连接测试参数
 */
export const testConnection = (data: TestConnectionParams): Promise<TestConnectionResult> => {
  return request.post('/connections/test', data) as Promise<TestConnectionResult>
}

/**
 * 获取数据库Schema
 * @param id 连接ID
 * @param refresh 是否强制刷新缓存
 */
export const getSchema = (id: number, refresh?: boolean): Promise<SchemaInfo> => {
  return request.get(`/connections/${id}/schema`, {
    params: { refresh }
  }) as Promise<SchemaInfo>
}

/**
 * 刷新数据库Schema缓存
 * @param id 连接ID
 */
export const refreshSchema = (id: number): Promise<RefreshSchemaResult> => {
  return request.post(`/connections/${id}/schema/refresh`) as Promise<RefreshSchemaResult>
}
