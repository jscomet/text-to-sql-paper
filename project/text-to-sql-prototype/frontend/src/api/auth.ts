import request from '@/utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  email: string
  is_active: boolean
}

// 登录
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

// 获取当前用户信息
export const getCurrentUser = (): Promise<UserInfo> => {
  return request.get('/auth/me') as Promise<UserInfo>
}
