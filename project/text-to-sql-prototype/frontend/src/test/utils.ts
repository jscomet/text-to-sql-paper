import { mount, shallowMount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import type { Component } from 'vue'
import type { Router } from 'vue-router'

// Create a mock router for testing
export function createMockRouter(): Router {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      { path: '/query', name: 'query', component: { template: '<div>Query</div>' } },
      { path: '/connections', name: 'connections', component: { template: '<div>Connections</div>' } },
      { path: '/evaluations', name: 'evaluations', component: { template: '<div>Evaluations</div>' } },
      { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
    ],
  })
}

interface MountOptions {
  props?: Record<string, unknown>
  slots?: Record<string, unknown>
  global?: Record<string, unknown>
  attachTo?: HTMLElement
  shallow?: boolean
}

/**
 * Mount a component with full setup (Pinia + Router + Element Plus)
 */
export function mountComponent(component: Component, options: MountOptions = {}) {
  const { props = {}, slots = {}, global = {}, shallow = false } = options

  // Create fresh Pinia instance
  const pinia = createPinia()
  setActivePinia(pinia)

  // Create mock router
  const router = createMockRouter()

  const mountFn = shallow ? shallowMount : mount

  return mountFn(component, {
    props,
    slots,
    attachTo: options.attachTo,
    global: {
      plugins: [pinia, router, ElementPlus],
      stubs: {
        'router-link': true,
        'router-view': true,
        ...((global.stubs as Record<string, boolean>) || {}),
      },
      mocks: {
        $router: router,
        ...((global.mocks as Record<string, unknown>) || {}),
      },
      ...global,
    },
  })
}

/**
 * Mount a component with only Pinia (no router)
 */
export function mountWithPinia(component: Component, options: MountOptions = {}) {
  const { props = {}, slots = {}, global = {}, shallow = false } = options

  const pinia = createPinia()
  setActivePinia(pinia)

  const mountFn = shallow ? shallowMount : mount

  return mountFn(component, {
    props,
    slots,
    attachTo: options.attachTo,
    global: {
      plugins: [pinia, ElementPlus],
      stubs: {
        'router-link': true,
        'router-view': true,
        ...((global.stubs as Record<string, boolean>) || {}),
      },
      ...global,
    },
  })
}

/**
 * Wait for all promises to resolve
 */
export { flushPromises }

/**
 * Wait for a specified amount of time
 */
export function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Create a mock response for API calls
 */
export function createMockResponse<T>(data: T, status = 200) {
  return {
    data,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: {},
    config: {},
  }
}

/**
 * Type-safe wrapper for finding elements
 */
export function findByTestId(wrapper: ReturnType<typeof mount>, testId: string) {
  return wrapper.find(`[data-testid="${testId}"]`)
}

/**
 * Get all elements by test id
 */
export function findAllByTestId(wrapper: ReturnType<typeof mount>, testId: string) {
  return wrapper.findAll(`[data-testid="${testId}"]`)
}
