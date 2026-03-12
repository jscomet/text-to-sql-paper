import { describe, it, expect } from 'vitest'
import { mountWithPinia } from '@/test/utils'
import LoadingOverlay from './LoadingOverlay.vue'

describe('LoadingOverlay', () => {
  it('should render with default props', () => {
    const wrapper = mountWithPinia(LoadingOverlay, {
      props: { loading: false },
    })
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
  })

  it('should show loading state when loading is true', () => {
    const wrapper = mountWithPinia(LoadingOverlay, {
      props: { loading: true },
    })
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
    expect(wrapper.find('.loading-overlay').attributes('v-loading')).toBe('true')
  })

  it('should render slot content', () => {
    const wrapper = mountWithPinia(LoadingOverlay, {
      props: { loading: false },
      slots: {
        default: '<div class="test-content">Test Content</div>',
      },
    })
    expect(wrapper.find('.test-content').exists()).toBe(true)
    expect(wrapper.find('.test-content').text()).toBe('Test Content')
  })

  it('should apply custom text', () => {
    const wrapper = mountWithPinia(LoadingOverlay, {
      props: { loading: true, text: 'Custom Loading Text' },
    })
    expect(wrapper.find('.loading-overlay').attributes('element-loading-text')).toBe('Custom Loading Text')
  })

  it('should apply custom background', () => {
    const wrapper = mountWithPinia(LoadingOverlay, {
      props: { loading: true, background: 'rgba(0, 0, 0, 0.5)' },
    })
    expect(wrapper.find('.loading-overlay').attributes('element-loading-background')).toBe('rgba(0, 0, 0, 0.5)')
  })

  it('should render fullscreen wrapper when fullscreen is true', () => {
    const wrapper = mountWithPinia(LoadingOverlay, {
      props: { loading: true, fullscreen: true },
    })
    expect(wrapper.find('.fullscreen-wrapper').exists()).toBe(true)
    expect(wrapper.find('.loading-overlay').exists()).toBe(false)
  })
})
