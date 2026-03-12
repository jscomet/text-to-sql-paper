import request from '@/utils/request'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
  ChangePasswordRequest,
} from '@/types'

// ==================== 类型导出 ====================

export type LoginParams = LoginRequest
export type LoginResult = LoginResponse
export type RegisterParams = RegisterRequest
export type RegisterResult = RegisterResponse
export type UserInfo = User
export type ChangePasswordParams = ChangePasswordRequest

// ==================== API 函数 ====================

/**
 * 用户登录
 * @param data 登录参数
 */
export const login = (data: LoginParams): Promise<LoginResult> => {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('password', data.password)
  return request.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }) as Promise<LoginResult>
}

/**
 * 用户注册
 * @param data 注册参数
 */
export const register = (data: RegisterParams): Promise<RegisterResult> => {
  return request.post('/auth/register', data) as Promise<RegisterResult>
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = (): Promise<UserInfo> => {
  return request.get('/auth/me') as Promise<UserInfo>
}

/**
 * 用户登出
 */
export const logout = (): Promise<void> => {
  return request.post('/auth/logout') as Promise<void>
}

/**
 * 修改密码
 * @param data 密码修改参数
 */
export const changePassword = (data: ChangePasswordParams): Promise<void> => {
  return request.put('/auth/password', data) as Promise<void>
}
