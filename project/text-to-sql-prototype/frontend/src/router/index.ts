import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { setupRouterGuard } from './guards'

// 布局组件
const MainLayout = () => import('@/layouts/MainLayout.vue')
const BlankLayout = () => import('@/layouts/BlankLayout.vue')

// 页面组件
const LoginView = () => import('@/views/LoginView.vue')
const HomeView = () => import('@/views/HomeView.vue')
const QueryView = () => import('@/views/QueryView.vue')
const ConnectionsView = () => import('@/views/ConnectionsView.vue')
const HistoryView = () => import('@/views/HistoryView.vue')
const EvaluationsView = () => import('@/views/EvaluationsView.vue')
const SettingsView = () => import('@/views/SettingsView.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: {
      layout: 'blank',
      public: true,
      title: '登录',
    },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: HomeView,
        meta: {
          title: '首页',
          icon: 'HomeFilled',
        },
      },
      {
        path: 'query',
        name: 'Query',
        component: QueryView,
        meta: {
          title: '查询',
          icon: 'ChatDotRound',
        },
      },
      {
        path: 'connections',
        name: 'Connections',
        component: ConnectionsView,
        meta: {
          title: '连接管理',
          icon: 'Connection',
        },
      },
      {
        path: 'history',
        name: 'History',
        component: HistoryView,
        meta: {
          title: '历史记录',
          icon: 'Clock',
        },
      },
      {
        path: 'evaluations',
        name: 'Evaluations',
        component: EvaluationsView,
        meta: {
          title: '评测',
          icon: 'TrendCharts',
        },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: SettingsView,
        meta: {
          title: '设置',
          icon: 'Setting',
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// 设置路由守卫
setupRouterGuard(router)

export default router
