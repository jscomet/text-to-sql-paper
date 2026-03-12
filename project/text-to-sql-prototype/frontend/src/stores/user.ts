import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getCurrentUser, type LoginParams, type UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  // Getters
  const isLoggedIn = computed(() => !!token.value)

  // Actions
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const loginAction = async (params: LoginParams) => {
    const res = await login(params)
    setToken(res.access_token)
    await fetchUserInfo()
    return res
  }

  const fetchUserInfo = async () => {
    const res = await getCurrentUser()
    userInfo.value = res
    return res
  }

  const logout = () => {
    clearToken()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    setToken,
    clearToken,
    loginAction,
    fetchUserInfo,
    logout,
  }
})
