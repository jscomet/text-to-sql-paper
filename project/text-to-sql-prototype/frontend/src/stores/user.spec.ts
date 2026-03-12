import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from './user'
import * as authApi from '@/api/auth'

// Mock auth API
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  getCurrentUser: vi.fn(),
  logout: vi.fn(),
}))

// Mock ElMessage
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
    },
  }
})

// Mock window.location
const mockLocation = { href: '' }
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
})

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
    mockLocation.href = ''
  })

  it('should have correct initial state', () => {
    const store = useUserStore()
    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.isLoggedIn).toBe(false)
    expect(store.username).toBe('')
    expect(store.isAdmin).toBe(false)
  })

  it('should initialize auth from localStorage', async () => {
    const mockUser = { id: 1, username: 'test', role: 'user' }
    localStorage.setItem('token', 'test-token')
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)

    const store = useUserStore()
    const result = await store.initAuth()

    expect(result).toBe(true)
    expect(store.token).toBe('test-token')
    expect(store.userInfo).toEqual(mockUser)
    expect(store.isLoggedIn).toBe(true)
  })

  it('should return false when no token in localStorage', async () => {
    const store = useUserStore()
    const result = await store.initAuth()

    expect(result).toBe(false)
    expect(store.isLoggedIn).toBe(false)
  })

  it('should clear auth when fetchUserInfo fails', async () => {
    localStorage.setItem('token', 'invalid-token')
    vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Unauthorized'))

    const store = useUserStore()
    const result = await store.initAuth()

    expect(result).toBe(false)
    expect(store.token).toBe('')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('should login successfully', async () => {
    const mockResponse = { access_token: 'new-token', token_type: 'bearer' }
    const mockUser = { id: 1, username: 'testuser', role: 'user' }

    vi.mocked(authApi.login).mockResolvedValue(mockResponse)
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)

    const store = useUserStore()
    const result = await store.login({ username: 'test', password: 'pass' })

    expect(result).toBe(true)
    expect(store.token).toBe('new-token')
    expect(store.userInfo).toEqual(mockUser)
    expect(localStorage.getItem('token')).toBe('new-token')
  })

  it('should handle login failure', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))

    const store = useUserStore()
    const result = await store.login({ username: 'test', password: 'wrong' })

    expect(result).toBe(false)
    expect(store.loading).toBe(false)
  })

  it('should loginAction return response data', async () => {
    const mockResponse = { access_token: 'token', token_type: 'bearer' }
    const mockUser = { id: 1, username: 'test', role: 'user' }

    vi.mocked(authApi.login).mockResolvedValue(mockResponse)
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)

    const store = useUserStore()
    const response = await store.loginAction({ username: 'test', password: 'pass' })

    expect(response).toEqual(mockResponse)
    expect(store.token).toBe('token')
  })

  it('should throw error on loginAction failure', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Login failed'))

    const store = useUserStore()
    await expect(store.loginAction({ username: 'test', password: 'pass' })).rejects.toThrow('Login failed')
    expect(store.loading).toBe(false)
  })

  it('should fetch user info', async () => {
    const mockUser = { id: 1, username: 'test', role: 'user' }
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)

    const store = useUserStore()
    store.token = 'valid-token'
    await store.fetchUserInfo()

    expect(store.userInfo).toEqual(mockUser)
  })

  it('should not fetch user info when no token', async () => {
    const store = useUserStore()
    await store.fetchUserInfo()

    expect(authApi.getCurrentUser).not.toHaveBeenCalled()
  })

  it('should logout and clear auth', async () => {
    vi.mocked(authApi.logout).mockResolvedValue(undefined)

    const store = useUserStore()
    store.token = 'token'
    store.userInfo = { id: 1, username: 'test', role: 'user' }
    localStorage.setItem('token', 'token')

    await store.logout()

    expect(authApi.logout).toHaveBeenCalled()
    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(mockLocation.href).toBe('/login')
  })

  it('should clear auth even when logout API fails', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('Logout failed'))

    const store = useUserStore()
    store.token = 'token'
    store.userInfo = { id: 1, username: 'test', role: 'user' }
    localStorage.setItem('token', 'token')

    await store.logout()

    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(mockLocation.href).toBe('/login')
  })

  it('should logout without calling API when callApi is false', async () => {
    const store = useUserStore()
    store.token = 'token'
    store.userInfo = { id: 1, username: 'test', role: 'user' }

    await store.logout(false)

    expect(authApi.logout).not.toHaveBeenCalled()
    expect(store.token).toBe('')
    expect(mockLocation.href).toBe('/login')
  })

  it('should clear auth', () => {
    const store = useUserStore()
    store.token = 'token'
    store.userInfo = { id: 1, username: 'test', role: 'user' }
    localStorage.setItem('token', 'token')

    store.clearAuth()

    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('should update user info', () => {
    const store = useUserStore()
    store.userInfo = { id: 1, username: 'old', role: 'user' }

    store.updateUserInfo({ username: 'new' })

    expect(store.userInfo?.username).toBe('new')
    expect(store.userInfo?.id).toBe(1)
  })

  it('should not update user info when null', () => {
    const store = useUserStore()
    store.userInfo = null

    store.updateUserInfo({ username: 'new' })

    expect(store.userInfo).toBeNull()
  })

  it('should compute isAdmin correctly', () => {
    const store = useUserStore()

    store.userInfo = { id: 1, username: 'admin', role: 'admin' }
    expect(store.isAdmin).toBe(true)

    store.userInfo = { id: 2, username: 'user', role: 'user' }
    expect(store.isAdmin).toBe(false)
  })

  it('should compute username correctly', () => {
    const store = useUserStore()

    expect(store.username).toBe('')

    store.userInfo = { id: 1, username: 'testuser', role: 'user' }
    expect(store.username).toBe('testuser')
  })
})
