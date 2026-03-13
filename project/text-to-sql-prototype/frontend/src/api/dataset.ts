import request from '@/utils/request'
import type {
  ImportConfig,
  ImportResponse,
  ImportProgress,
} from '@/types'

// ==================== 类型导出 ====================

export type { ImportConfig, ImportResponse, ImportProgress }
export type ImportStatus = ImportProgress['status']

// ==================== API 函数 ====================

/**
 * 上传 ZIP 文件导入数据集
 * @param file ZIP 文件
 * @param config 导入配置
 */
export const importDatasetZip = (
  file: File,
  config: ImportConfig
): Promise<ImportResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('dataset_type', config.dataset_type)
  formData.append('eval_mode', config.eval_mode)
  formData.append('api_key_id', String(config.api_key_id))

  if (config.temperature !== undefined) {
    formData.append('temperature', String(config.temperature))
  }
  if (config.max_tokens !== undefined) {
    formData.append('max_tokens', String(config.max_tokens))
  }
  if (config.connection_options) {
    formData.append('connection_options', JSON.stringify(config.connection_options))
  }

  return request.post('/dataset/import/zip', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }) as Promise<ImportResponse>
}

/**
 * 使用本地路径导入数据集
 * @param path 本地绝对路径
 * @param config 导入配置
 */
export const importDatasetLocal = (
  path: string,
  config: ImportConfig
): Promise<ImportResponse> => {
  return request.post('/dataset/import/local', {
    path,
    dataset_type: config.dataset_type,
    eval_mode: config.eval_mode,
    api_key_id: config.api_key_id,
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    connection_options: config.connection_options,
  }) as Promise<ImportResponse>
}

/**
 * 获取导入状态
 * @param importId 导入任务ID
 */
export const getImportStatus = (importId: string): Promise<ImportProgress> => {
  return request.get(`/dataset/import/${importId}/status`) as Promise<ImportProgress>
}

/**
 * 取消导入任务
 * @param importId 导入任务ID
 */
export const cancelImport = (importId: string): Promise<{ success: boolean }> => {
  return request.post(`/dataset/import/${importId}/cancel`) as Promise<{ success: boolean }>
}

/**
 * 验证数据集 ZIP 文件
 * @param file ZIP 文件
 */
export const validateDatasetZip = (file: File): Promise<{
  valid: boolean
  message?: string
  dataset_type?: string
  db_count?: number
  total_questions?: number
}> => {
  const formData = new FormData()
  formData.append('file', file)

  return request.post('/dataset/validate/zip', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }) as Promise<{
    valid: boolean
    message?: string
    dataset_type?: string
    db_count?: number
    total_questions?: number
  }>
}

/**
 * 验证本地数据集路径
 * @param path 本地绝对路径
 */
export const validateDatasetLocal = (path: string): Promise<{
  valid: boolean
  message?: string
  dataset_type?: string
  db_count?: number
  total_questions?: number
}> => {
  return request.post('/dataset/validate/local', { path }) as Promise<{
    valid: boolean
    message?: string
    dataset_type?: string
    db_count?: number
    total_questions?: number
  }>
}
