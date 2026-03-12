# 阶段4：前端基础架构

## 阶段目标
搭建前端核心基础设施，包括路由配置、状态管理、HTTP客户端、通用组件和布局。本阶段完成后，前端具备页面开发的基础能力。

**预计工期**: 1天
**并行度**: 中（路由、状态管理、组件可并行）

---

## Agent 协作关系

```
frontend-dev (Task 4.1)         frontend-dev (Task 4.2)         ui-component-dev (Task 4.3)
    │                               │                               │
    ├── 路由配置                     ├── Pinia状态管理                ├── 布局组件
    ├── 路由守卫                     ├── HTTP客户端封装               ├── 通用组件
    └── 页面骨架                     └── 错误处理                     └── 主题配置
```

**依赖关系**:
- Task 4.1、4.2、4.3 可并行执行

---

## 任务分解

### Task 4.1: 路由与页面骨架
**负责人**: `frontend-dev`
**依赖**: 阶段1完成
**参考文档**: `../02-UI-Design.md` (页面跳转逻辑)

#### 工作内容

1. **路由配置** (`src/router/index.ts`)
   ```typescript
   // 路由结构
   const routes = [
     {
       path: '/login',
       name: 'Login',
       component: () => import('@/views/LoginView.vue'),
       meta: { public: true }
     },
     {
       path: '/',
       component: () => import('@/layouts/MainLayout.vue'),
       children: [
         { path: '', name: 'Home', component: () => import('@/views/HomeView.vue') },
         { path: 'query', name: 'Query', component: () => import('@/views/QueryView.vue') },
         { path: 'connections', name: 'Connections', component: () => import('@/views/ConnectionsView.vue') },
         { path: 'history', name: 'History', component: () => import('@/views/HistoryView.vue') },
         { path: 'evaluations', name: 'Evaluations', component: () => import('@/views/EvaluationsView.vue') },
         { path: 'settings', name: 'Settings', component: () => import('@/views/SettingsView.vue') }
       ]
     }
   ]
   ```

2. **路由守卫** (`src/router/guards.ts`)
   - 登录状态检查
   - Token有效性验证
   - 权限检查

3. **页面骨架组件** (`src/views/`)
   - `LoginView.vue` - 登录页（基础框架）
   - `HomeView.vue` - 首页（基础框架）
   - `QueryView.vue` - 查询页（基础框架）
   - `ConnectionsView.vue` - 连接管理页（基础框架）
   - `HistoryView.vue` - 历史记录页（基础框架）
   - `EvaluationsView.vue` - 评测页（基础框架）
   - `SettingsView.vue` - 设置页（基础框架）

4. **布局组件** (`src/layouts/`)
   - `MainLayout.vue` - 主布局（侧边栏 + 顶部导航 + 内容区）
   - `BlankLayout.vue` - 空白布局（用于登录页）

#### 检查点
- [ ] 所有路由配置完成
- [ ] 路由守卫工作正常
- [ ] 未登录用户被重定向到登录页
- [ ] 页面骨架组件能正常显示

#### 测试点
```typescript
// 测试路由跳转
router.push('/query')
expect(router.currentRoute.value.name).toBe('Query')
```

---

### Task 4.2: 状态管理与HTTP客户端
**负责人**: `frontend-dev`
**依赖**: 阶段1完成，需要后端API可用

#### 工作内容

1. **HTTP客户端** (`src/utils/request.ts`)
   ```typescript
   // 基于axios封装
   const request = axios.create({
     baseURL: import.meta.env.VITE_API_BASE_URL,
     timeout: 30000
   })

   // 请求拦截器：添加token
   // 响应拦截器：统一错误处理
   // 支持文件上传
   ```

2. **用户状态管理** (`src/stores/user.ts`)
   ```typescript
   export const useUserStore = defineStore('user', {
     state: () => ({
       token: localStorage.getItem('token'),
       userInfo: null
     }),
     actions: {
       async login(credentials) { /* 登录 */ },
       async logout() { /* 登出 */ },
       async fetchUserInfo() { /* 获取用户信息 */ }
     }
   })
   ```

3. **API模块** (`src/api/`)
   - `auth.ts` - 认证相关API
   - `connections.ts` - 数据库连接API
   - `queries.ts` - 查询相关API
   - `evaluations.ts` - 评测相关API

4. **错误处理**
   - 全局错误提示（使用Element Plus Message）
   - Token过期自动跳转登录
   - 网络错误重试

#### 检查点
- [ ] HTTP请求能正确添加token
- [ ] 401错误能自动跳转登录
- [ ] 用户状态持久化存储
- [ ] 所有API模块定义完成

#### 测试点
```typescript
// 测试登录流程
const userStore = useUserStore()
await userStore.login({ username: 'test', password: '123456' })
expect(userStore.token).toBeTruthy()
```

---

### Task 4.3: 通用组件与主题
**负责人**: `ui-component-dev`
**依赖**: 阶段1完成
**参考文档**: `../02-UI-Design.md` (组件规范)

#### 工作内容

1. **布局组件** (`src/components/layout/`)
   - `AppHeader.vue` - 顶部导航栏
   - `AppSidebar.vue` - 侧边栏菜单
   - `AppFooter.vue` - 底部（可选）

2. **通用组件** (`src/components/common/`)
   - `DataTable.vue` - 数据表格（支持分页、排序）
   - `SearchForm.vue` - 搜索表单
   - `LoadingOverlay.vue` - 加载遮罩
   - `EmptyState.vue` - 空状态提示
   - `ErrorAlert.vue` - 错误提示

3. **业务组件** (`src/components/business/`)
   - `ConnectionForm.vue` - 数据库连接表单
   - `SqlEditor.vue` - SQL编辑器（使用 Monaco Editor 或简单textarea）
   - `QueryResult.vue` - 查询结果展示
   - `SchemaTree.vue` - Schema树形展示

4. **主题配置** (`src/styles/`)
   - `variables.scss` - SCSS变量
   - `element-plus.scss` - Element Plus主题覆盖
   - `global.scss` - 全局样式

5. **图标配置**
   - 注册Element Plus图标
   - 配置自动导入

#### 检查点
- [ ] 布局组件显示正常
- [ ] 通用组件功能完整
- [ ] 主题色正确应用
- [ ] 图标能正常显示

#### 测试点
```vue
<!-- 测试组件 -->
<template>
  <DataTable :data="testData" :columns="columns" />
</template>
```

---

## 阶段交付物

| 交付物 | 位置 | 验收标准 |
|--------|------|----------|
| 路由配置 | `src/router/` | 所有页面路由可用，守卫正常 |
| 布局组件 | `src/layouts/`, `src/components/layout/` | 主布局显示正常 |
| 状态管理 | `src/stores/` | Pinia状态正常工作 |
| HTTP客户端 | `src/utils/request.ts` | API调用正常，错误处理完善 |
| API模块 | `src/api/` | 所有后端API封装完成 |
| 通用组件 | `src/components/common/` | 组件可复用，文档完整 |
| 主题配置 | `src/styles/` | 主题色正确应用 |

---

## 阶段检查清单

### 功能检查
- [ ] 路由跳转正常
- [ ] 未登录用户被正确拦截
- [ ] 登录后token正确存储
- [ ] API请求自动携带token
- [ ] 401错误自动跳转登录
- [ ] 布局组件显示正常

### 代码检查
- [ ] 组件命名规范
- [ ] 代码格式符合ESLint配置
- [ ] TypeScript类型定义完整
- [ ] 组件props有默认值

### 测试检查
- [ ] 路由测试通过
- [ ] 状态管理测试通过
- [ ] 组件基本功能测试通过

---

## 集成测试计划

### 测试目标
验证前端基础架构完整：路由、状态管理、HTTP 客户端、布局组件。

### 测试方式
**浏览器访问 + 开发者工具检查**

#### 测试 1: 路由系统
```
1. 访问 http://localhost:5173/login
   → 显示登录页面
2. 未登录访问 http://localhost:5173/query
   → 重定向到 /login
3. 登录后访问 http://localhost:5173/query
   → 正常显示查询页面
```

#### 测试 2: 状态管理
```typescript
// 在浏览器控制台测试
// 1. 登录后检查 Pinia store
import { useUserStore } from '@/stores/user'
const store = useUserStore()
console.log(store.token)  // 应有值
console.log(store.userInfo)  // 应有用户信息

// 2. 刷新页面
// 3. 检查 token 是否持久化（localStorage）
```

#### 测试 3: HTTP 客户端
```typescript
// 在浏览器控制台测试
import request from '@/utils/request'
request.get('/health').then(r => console.log(r))
// 应自动携带 Authorization header
```

#### 测试 4: 布局组件
```
1. 登录后查看主布局
   → Sidebar 显示导航菜单
   → Header 显示用户信息
   → Content 区域显示页面内容
2. 点击 Sidebar 菜单
   → 路由跳转正确
   → 菜单高亮正确
```

### 真实运行验证
- [ ] 前端开发服务器启动无报错
- [ ] 浏览器访问各页面正常渲染
- [ ] 登录后 token 存储到 localStorage
- [ ] API 请求自动携带 token
- [ ] 401 响应自动跳转登录页

### 验收标准
| 功能 | 测试方法 | 预期结果 |
|------|----------|----------|
| 路由守卫 | 直接访问需要登录的页面 | 跳转到登录页 |
| 登录流程 | 输入账号密码点击登录 | 登录成功，跳转首页，存储 token |
| Token 持久化 | 刷新页面 | 保持登录状态 |
| API 请求 | 调用需要认证的接口 | 自动携带 Authorization header |
| 布局显示 | 查看主布局 | Sidebar + Header + Content 正常显示 |
| 响应式 | 调整浏览器窗口大小 | 布局自适应 |

### 测试报告
- [ ] 已生成 `docs/report/04-Phase4-Frontend/report-task4.x-xxx.md`
- [ ] 包含各页面截图
- [ ] 包含开发者工具 Network 面板截图（验证请求头）

---

## 进入下一阶段条件

1. ✅ 路由、状态管理、组件全部完成
2. ✅ 能正常登录并访问各页面
3. ✅ 能正常调用后端API
4. ✅ 代码通过review
5. ✅ 集成测试全部通过（浏览器访问验证）

---

## 风险与应对

| 风险 | 应对措施 |
|------|----------|
| 前后端API不一致 | 使用swagger/openapi生成前端类型 |
| 跨域问题 | 配置Vite代理，后端开放CORS |
| 组件props复杂 | 使用TypeScript接口定义 |

---

*依赖文档: ../02-UI-Design.md, ../05-API-Documentation.md*
