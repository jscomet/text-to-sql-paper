import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as authApi from '@/api/auth'
import type { User } from '@/types'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<User | null>(null)
  const loading = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const username = computed(() => userInfo.value?.username || '')
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  // Actions

  /**
   * 初始化认证状态
   * 从 localStorage 恢复 token，并获取用户信息
   */
  async function initAuth(): Promise<boolean> {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      token.value = storedToken
      try {
        await fetchUserInfo()
        return true
      } catch {
        // 获取用户信息失败，清除 token
        clearAuth()
        return false
      }
    }
    return false
  }

  /**
   * 用户登录
   */
  async function login(credentials: authApi.LoginParams): Promise<boolean> {
    loading.value = true
    try {
      const response = await authApi.login(credentials)

      // 保存 token
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)

      // 获取完整用户信息
      await fetchUserInfo()

      ElMessage.success('登录成功')
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户登录（兼容旧接口）
   * 返回登录响应数据
   */
  async function loginAction(credentials: authApi.LoginParams): Promise<authApi.LoginResult> {
    loading.value = true
    try {
      const response = await authApi.login(credentials)

      // 保存 token
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)

      // 获取完整用户信息
      await fetchUserInfo()

      ElMessage.success('登录成功')
      return response
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取当前用户信息
   */
  async function fetchUserInfo(): Promise<void> {
    if (!token.value) return

    try {
      const user = await authApi.getCurrentUser()
      userInfo.value = user as User
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      throw error
    }
  }

  /**
   * 用户登出
   * @param callApi 是否调用后端登出接口
   */
  async function logout(callApi = true): Promise<void> {
    if (callApi && token.value) {
      try {
        await authApi.logout()
      } catch (error) {
        console.error('Logout API failed:', error)
        // 即使API调用失败，也继续清除本地状态
      }
    }

    clearAuth()
    ElMessage.success('已退出登录')
    // 使用 window.location 进行跳转，避免 useRouter 在 store 中的问题
    window.location.href = '/login'
  }

  /**
   * 清除认证状态
   */
  function clearAuth(): void {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  /**
   * 更新用户信息
   */
  function updateUserInfo(info: Partial<User>): void {
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, ...info }
    }
  }

  return {
    // State
    token,
    userInfo,
    loading,
    // Getters
    isLoggedIn,
    username,
    isAdmin,
    // Actions
    initAuth,
    login,
    loginAction,
    logout,
    fetchUserInfo,
    clearAuth,
    updateUserInfo,
  }
})
