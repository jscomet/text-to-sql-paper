import type { Router, NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 白名单路由（不需要登录）
const whiteList = ['/login']

// 设置路由守卫
export function setupRouterGuard(router: Router) {
  // 全局前置守卫
  router.beforeEach(
    async (
      to: RouteLocationNormalized,
      from: RouteLocationNormalized,
      next: NavigationGuardNext,
    ) => {
      // 设置页面标题
      const title = to.meta.title as string
      if (title) {
        document.title = `${title} - Text2SQL`
      } else {
        document.title = 'Text2SQL'
      }

      const userStore = useUserStore()

      // 初始化认证状态（从localStorage恢复token和用户信息）
      await userStore.initAuth()

      // 检查是否有token
      const hasToken = userStore.isLoggedIn

      if (hasToken) {
        // 已登录
        if (to.path === '/login') {
          // 已登录用户访问登录页，重定向到首页
          next({ path: '/' })
        } else {
          // 检查用户信息是否存在
          if (!userStore.userInfo) {
            try {
              // 获取用户信息
              await userStore.fetchUserInfo()
              next()
            } catch (error) {
              // 获取用户信息失败，清除token并重定向到登录页
              userStore.logout()
              next(`/login?redirect=${to.path}`)
            }
          } else {
            next()
          }
        }
      } else {
        // 未登录
        if (to.meta.public || whiteList.includes(to.path)) {
          // 访问的是公开页面或白名单页面
          next()
        } else {
          // 访问的是受保护页面，重定向到登录页
          next(`/login?redirect=${to.path}`)
        }
      }
    },
  )

  // 全局后置钩子
  router.afterEach((to: RouteLocationNormalized) => {
    // 可以在这里添加页面访问日志等
    console.log(`[Router] Navigated to: ${to.path}`)
  })

  // 错误处理
  router.onError((error: Error) => {
    console.error('[Router] Navigation error:', error)
  })
}
