import request from '@/utils/request'
import type {
  CreateEvalTaskRequest,
  EvalTask,
  EvalTaskDetail,
  EvalResult,
  EvalStats,
  PaginationParams,
  PaginationData,
} from '@/types'

// ==================== 类型导出 ====================

export type { CreateEvalTaskRequest, EvalTask, EvalTaskDetail, EvalResult, EvalStats }
export type DatasetType = 'bird' | 'spider' | 'custom'
export type EvalMode = 'greedy_search' | 'major_voting' | 'pass@k'
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type ErrorType = 'syntax' | 'execution' | 'logic' | 'timeout' | 'generation'
export type CreateEvalTaskParams = CreateEvalTaskRequest
export type EvalResultItem = EvalResult
export type EvalTaskResponse = PaginationData<EvalTask>
export type EvalResultsResponse = PaginationData<EvalResult>
export interface EvalTaskParams extends PaginationParams {
  status?: TaskStatus
}

// ==================== API 函数 ====================

/**
 * 创建评测任务
 * @param data 任务参数，支持 FormData（文件上传）或普通对象
 */
export const createEvalTask = (data: CreateEvalTaskParams | FormData): Promise<EvalTask> => {
  const isFormData = data instanceof FormData
  return request.post('/eval/tasks', data, {
    headers: isFormData ? { 'Content-Type': 'multipart/form-data' } : undefined,
  }) as Promise<EvalTask>
}

/**
 * 获取评测任务列表
 * @param params 查询参数
 */
export const getEvalTasks = (params?: EvalTaskParams): Promise<EvalTaskResponse> => {
  return request.get('/eval/tasks', { params }) as Promise<EvalTaskResponse>
}

/**
 * 获取评测任务详情
 * @param id 任务ID
 */
export const getEvalTask = (id: number): Promise<EvalTaskDetail> => {
  return request.get(`/eval/tasks/${id}`) as Promise<EvalTaskDetail>
}

/**
 * 获取评测结果列表
 * @param id 任务ID
 * @param params 查询参数
 */
export const getEvalResults = (
  id: number,
  params?: PaginationParams & { is_correct?: boolean }
): Promise<EvalResultsResponse> => {
  return request.get(`/eval/tasks/${id}/results`, { params }) as Promise<EvalResultsResponse>
}

/**
 * 获取评测统计信息
 * @param id 任务ID
 */
export const getEvalStats = (id: number): Promise<EvalStats> => {
  return request.get(`/eval/tasks/${id}/stats`) as Promise<EvalStats>
}

/**
 * 取消评测任务
 * @param id 任务ID
 */
export const cancelEvalTask = (id: number): Promise<{ id: number; status: TaskStatus }> => {
  return request.post(`/eval/tasks/${id}/cancel`) as Promise<{ id: number; status: TaskStatus }>
}

/**
 * 删除评测任务
 * @param id 任务ID
 */
export const deleteEvalTask = (id: number): Promise<void> => {
  return request.delete(`/eval/tasks/${id}`) as Promise<void>
}
