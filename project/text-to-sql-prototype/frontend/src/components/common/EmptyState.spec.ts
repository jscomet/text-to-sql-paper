import { describe, it, expect, vi } from 'vitest'
import { mountWithPinia } from '@/test/utils'
import EmptyState from './EmptyState.vue'

describe('EmptyState', () => {
  it('should render with default props', () => {
    const wrapper = mountWithPinia(EmptyState)
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.title').text()).toBe('暂无数据')
  })

  it('should render custom title', () => {
    const wrapper = mountWithPinia(EmptyState, {
      props: { title: 'Custom Title' },
    })
    expect(wrapper.find('.title').text()).toBe('Custom Title')
  })

  it('should render description when provided', () => {
    const wrapper = mountWithPinia(EmptyState, {
      props: { description: 'Custom Description' },
    })
    expect(wrapper.find('.sub-title').exists()).toBe(true)
    expect(wrapper.find('.sub-title').text()).toBe('Custom Description')
  })

  it('should not render description when not provided', () => {
    const wrapper = mountWithPinia(EmptyState)
    expect(wrapper.find('.sub-title').exists()).toBe(false)
  })

  it('should render action button when showAction is true', () => {
    const wrapper = mountWithPinia(EmptyState, {
      props: { showAction: true },
    })
    expect(wrapper.find('.el-button').exists()).toBe(true)
    expect(wrapper.find('.el-button').text()).toBe('新建')
  })

  it('should not render action button when showAction is false', () => {
    const wrapper = mountWithPinia(EmptyState, {
      props: { showAction: false },
    })
    expect(wrapper.find('.el-button').exists()).toBe(false)
  })

  it('should emit action event when button is clicked', async () => {
    const wrapper = mountWithPinia(EmptyState, {
      props: { showAction: true },
    })
    await wrapper.find('.el-button').trigger('click')
    expect(wrapper.emitted('action')).toBeTruthy()
    expect(wrapper.emitted('action')!.length).toBe(1)
  })

  it('should render custom action slot', () => {
    const wrapper = mountWithPinia(EmptyState, {
      props: { showAction: true },
      slots: {
        action: 'Custom Action',
      },
    })
    expect(wrapper.find('.el-button').text()).toBe('Custom Action')
  })

  it('should apply custom icon size', () => {
    const wrapper = mountWithPinia(EmptyState, {
      props: { iconSize: 100 },
    })
    const icon = wrapper.find('.el-icon')
    expect(icon.exists()).toBe(true)
  })
})
