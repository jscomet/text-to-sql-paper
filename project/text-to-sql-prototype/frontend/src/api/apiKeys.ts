import request from '@/utils/request'
import type {
  ApiKey,
  CreateApiKeyRequest,
  KeyType,
} from '@/types'

// ==================== 类型导出 ====================

export type ApiKeyItem = ApiKey
export type CreateApiKeyParams = CreateApiKeyRequest
export type ApiKeyType = KeyType

// ==================== API 函数 ====================

/**
 * 获取API密钥列表
 */
export const getApiKeys = (): Promise<ApiKey[]> => {
  return request.get('/keys').then((res: { list: ApiKey[] }) => res.list) as Promise<ApiKey[]>
}

/**
 * 添加API密钥
 * @param data 密钥参数
 */
export const createApiKey = (data: CreateApiKeyParams): Promise<ApiKey> => {
  return request.post('/keys', data) as Promise<ApiKey>
}

/**
 * 删除API密钥
 * @param id 密钥ID
 */
export const deleteApiKey = (id: number): Promise<void> => {
  return request.delete(`/keys/${id}`) as Promise<void>
}

/**
 * 设置默认密钥
 * @param id 密钥ID
 */
export const setDefaultApiKey = (id: number): Promise<ApiKey> => {
  return request.put(`/keys/${id}/default`) as Promise<ApiKey>
}
