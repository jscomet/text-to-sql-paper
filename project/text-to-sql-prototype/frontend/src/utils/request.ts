import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request: AxiosInstance = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') + '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    // 后端返回格式: { code, message, data }
    // 如果响应中有 data 字段且包含 code，说明是标准API响应格式
    const responseData = response.data as { code?: number; data?: unknown; message?: string } | undefined
    if (responseData?.code === 200) {
      return responseData.data
    }
    // 否则直接返回原始响应数据
    return response.data
  },
  (error: AxiosError) => {
    const { response } = error

    if (response) {
      const status = response.status
      const data = response.data as { message?: string; detail?: string } | undefined

      switch (status) {
        case 400:
          ElMessage.error(data?.message || data?.detail || '请求参数错误')
          break
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          // 清除用户状态并跳转到登录页
          localStorage.removeItem('token')
          const currentPath = router.currentRoute.value.path
          if (currentPath !== '/login') {
            router.push(`/login?redirect=${encodeURIComponent(currentPath)}`)
          }
          break
        case 403:
          ElMessage.error(data?.message || data?.detail || '没有权限执行此操作')
          break
        case 404:
          ElMessage.error(data?.message || data?.detail || '请求的资源不存在')
          break
        case 409:
          ElMessage.error(data?.message || data?.detail || '资源冲突')
          break
        case 422:
          ElMessage.error(data?.message || data?.detail || '请求数据验证失败')
          break
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
        case 500:
          ElMessage.error(data?.message || data?.detail || '服务器内部错误')
          break
        case 503:
          ElMessage.error('服务暂时不可用')
          break
        default:
          ElMessage.error(data?.message || data?.detail || `请求失败 (${status})`)
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('网络连接失败，请检查网络设置')
    } else {
      // 请求配置出错
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default request
