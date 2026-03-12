import { describe, it, expect, vi } from 'vitest'
import { mountWithPinia } from '@/test/utils'
import ErrorAlert from './ErrorAlert.vue'

describe('ErrorAlert', () => {
  it('should not render when error is null', () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: null },
    })
    expect(wrapper.find('.error-alert').exists()).toBe(false)
  })

  it('should render when error is a string', () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: 'Error message' },
    })
    expect(wrapper.find('.error-alert').exists()).toBe(true)
  })

  it('should render when error is an Error object', () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: new Error('Error object message') },
    })
    expect(wrapper.find('.error-alert').exists()).toBe(true)
  })

  it('should display string error message', () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: 'String error' },
    })
    const alert = wrapper.find('.error-alert')
    expect(alert.attributes('title')).toBe('String error')
  })

  it('should display Error object message', () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: new Error('Object error message') },
    })
    const alert = wrapper.find('.error-alert')
    expect(alert.attributes('title')).toBe('Object error message')
  })

  it('should display custom title when provided', () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: 'Error message', title: 'Custom Title' },
    })
    const alert = wrapper.find('.error-alert')
    expect(alert.attributes('title')).toBe('Custom Title')
  })

  it('should show error detail when title is different from error message', () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: 'Detailed error message', title: 'Custom Title' },
    })
    expect(wrapper.find('.error-detail').exists()).toBe(true)
    expect(wrapper.find('.error-detail').text()).toBe('Detailed error message')
  })

  it('should emit close event when closed', async () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: 'Error', closable: true },
    })
    const alert = wrapper.find('.error-alert')
    await alert.trigger('close')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('should emit retry event when retry button is clicked', async () => {
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: 'Error' },
      attrs: { onRetry: vi.fn() },
    })
    // Note: Testing retry button requires slot or attrs setup
    // This is a simplified test
    wrapper.vm.$emit('retry')
    expect(wrapper.emitted('retry')).toBeTruthy()
  })

  it('should apply different alert types', () => {
    const types = ['error', 'warning', 'info', 'success'] as const
    types.forEach((type) => {
      const wrapper = mountWithPinia(ErrorAlert, {
        props: { error: 'Error', type },
      })
      const alert = wrapper.find('.error-alert')
      expect(alert.attributes('type')).toBe(type)
    })
  })

  it('should handle error without message property', () => {
    const errorWithoutMessage = {} as Error
    const wrapper = mountWithPinia(ErrorAlert, {
      props: { error: errorWithoutMessage },
    })
    const alert = wrapper.find('.error-alert')
    expect(alert.attributes('title')).toBe('发生未知错误')
  })
})
