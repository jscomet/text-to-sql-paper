import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mountWithPinia, flushPromises } from '@/test/utils'
import SqlEditor from './SqlEditor.vue'
import { ElMessage } from 'element-plus'

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

describe('SqlEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render with default props', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: '' },
    })
    expect(wrapper.find('.sql-editor').exists()).toBe(true)
    expect(wrapper.find('.editor-textarea').exists()).toBe(true)
  })

  it('should display modelValue in textarea', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: 'SELECT * FROM users' },
    })
    const textarea = wrapper.find('.editor-textarea')
    expect((textarea.element as HTMLTextAreaElement).value).toBe('SELECT * FROM users')
  })

  it('should emit update:modelValue on input', async () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: '' },
    })
    const textarea = wrapper.find('.editor-textarea')
    await textarea.setValue('SELECT 1')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual(['SELECT 1'])
  })

  it('should apply custom placeholder', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: {
        modelValue: '',
        placeholder: 'Custom placeholder',
      },
    })
    const textarea = wrapper.find('.editor-textarea')
    expect(textarea.attributes('placeholder')).toBe('Custom placeholder')
  })

  it('should apply readonly attribute', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: {
        modelValue: '',
        readonly: true,
      },
    })
    const textarea = wrapper.find('.editor-textarea')
    expect(textarea.attributes('readonly')).toBeDefined()
  })

  it('should apply disabled attribute', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: {
        modelValue: '',
        disabled: true,
      },
    })
    const textarea = wrapper.find('.editor-textarea')
    expect(textarea.attributes('disabled')).toBeDefined()
  })

  it('should emit run event on Ctrl+Enter', async () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: 'SELECT 1' },
    })
    const textarea = wrapper.find('.editor-textarea')
    await textarea.trigger('keydown', { key: 'Enter', ctrlKey: true })
    expect(wrapper.emitted('run')).toBeTruthy()
  })

  it('should emit format event on format button click', async () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: 'SELECT * FROM users' },
    })
    const formatBtn = wrapper.findAll('.editor-toolbar button').find(b => b.text().includes('格式化'))
    if (formatBtn) {
      await formatBtn.trigger('click')
      expect(wrapper.emitted('format')).toBeTruthy()
    }
  })

  it('should emit update:modelValue with formatted SQL', async () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: 'SELECT id FROM users WHERE id=1' },
    })
    const formatBtn = wrapper.findAll('.editor-toolbar button').find(b => b.text().includes('格式化'))
    if (formatBtn) {
      await formatBtn.trigger('click')
      await flushPromises()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    }
  })

  it('should clear content on clear button click', async () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: 'SELECT 1' },
    })
    const clearBtn = wrapper.findAll('.editor-toolbar button').find(b => b.text().includes('清空'))
    if (clearBtn) {
      await clearBtn.trigger('click')
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')!.slice(-1)[0]).toEqual([''])
    }
  })

  it('should display character count', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: 'SELECT 1' },
    })
    const charCount = wrapper.find('.char-count')
    expect(charCount.text()).toContain('8')
  })

  it('should apply custom height', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: {
        modelValue: '',
        height: '300px',
      },
    })
    const textarea = wrapper.find('.editor-textarea')
    expect((textarea.element as HTMLTextAreaElement).style.height).toBe('300px')
  })

  it('should hide format button when showFormat is false', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: {
        modelValue: '',
        showFormat: false,
      },
    })
    const buttons = wrapper.findAll('.editor-toolbar button')
    const formatBtn = buttons.find(b => b.text().includes('格式化'))
    expect(formatBtn).toBeUndefined()
  })

  it('should hide copy button when showCopy is false', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: {
        modelValue: '',
        showCopy: false,
      },
    })
    const buttons = wrapper.findAll('.editor-toolbar button')
    const copyBtn = buttons.find(b => b.text().includes('复制'))
    expect(copyBtn).toBeUndefined()
  })

  it('should hide clear button when showClear is false', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: {
        modelValue: '',
        showClear: false,
      },
    })
    const buttons = wrapper.findAll('.editor-toolbar button')
    const clearBtn = buttons.find(b => b.text().includes('清空'))
    expect(clearBtn).toBeUndefined()
  })

  it('should expose insertText method', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: '' },
    })
    expect(typeof wrapper.vm.insertText).toBe('function')
  })

  it('should expose focus method', () => {
    const wrapper = mountWithPinia(SqlEditor, {
      props: { modelValue: '' },
    })
    expect(typeof wrapper.vm.focus).toBe('function')
  })
})
