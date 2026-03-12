import request from '@/utils/request'
import type {
  GenerateSQLRequest,
  GenerateSQLResponse,
  ExecuteSQLRequest,
  ExecuteSQLResponse,
  RunQueryRequest,
  RunQueryResponse,
  QueryHistory,
  QueryHistoryParams,
  PaginationData,
} from '@/types'

// ==================== 类型导出 ====================

export type GenerateSQLParams = GenerateSQLRequest
export type GenerateSQLResult = GenerateSQLResponse
export type ExecuteSQLParams = ExecuteSQLRequest
export type ExecuteSQLResult = ExecuteSQLResponse
export type RunQueryParams = RunQueryRequest
export type RunQueryResult = RunQueryResponse
export type QueryHistoryItem = QueryHistory
export interface QueryHistoryDetail extends QueryHistory {
  explanation: string
  confidence: number
  result_preview?: {
    columns: string[]
    rows: unknown[][]
  } | null
  error_message?: string | null
}
export type QueryHistoryResponse = PaginationData<QueryHistory>

// ==================== API 函数 ====================

/**
 * 自然语言转SQL
 * @param data 生成参数
 */
export const generateSQL = (data: GenerateSQLParams): Promise<GenerateSQLResult> => {
  return request.post('/queries/generate', data) as Promise<GenerateSQLResult>
}

/**
 * 执行SQL
 * @param data 执行参数
 */
export const executeSQL = (data: ExecuteSQLParams): Promise<ExecuteSQLResult> => {
  return request.post('/queries/execute', data) as Promise<ExecuteSQLResult>
}

/**
 * 生成并执行SQL（一站式）
 * @param data 运行参数
 */
export const runQuery = (data: RunQueryParams): Promise<RunQueryResult> => {
  return request.post('/queries/run', data) as Promise<RunQueryResult>
}

/**
 * 获取查询历史列表
 * @param params 查询参数
 */
export const getQueryHistory = (params?: QueryHistoryParams): Promise<QueryHistoryResponse> => {
  return request.get('/queries/history', { params }) as Promise<QueryHistoryResponse>
}

/**
 * 获取查询历史详情
 * @param id 历史记录ID
 */
export const getQueryHistoryDetail = (id: number): Promise<QueryHistoryDetail> => {
  return request.get(`/history/${id}`) as Promise<QueryHistoryDetail>
}

/**
 * 删除查询历史
 * @param id 历史记录ID
 */
export const deleteQueryHistory = (id: number): Promise<void> => {
  return request.delete(`/history/${id}`) as Promise<void>
}

/**
 * 切换收藏状态
 * @param id 历史记录ID
 * @param is_favorite 收藏状态
 */
export const toggleFavorite = (id: number, is_favorite: boolean): Promise<{ id: number; is_favorite: boolean }> => {
  return request.put(`/history/${id}/favorite`, { is_favorite }) as Promise<{ id: number; is_favorite: boolean }>
}
