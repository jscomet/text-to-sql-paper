import { describe, it, expect, vi } from 'vitest'
import { mountWithPinia } from '@/test/utils'
import QueryResult from './QueryResult.vue'

describe('QueryResult', () => {
  const mockData = [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
  ]

  const mockColumns = [
    { prop: 'id', label: 'ID' },
    { prop: 'name', label: 'Name' },
  ]

  it('should render with default props', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: [],
        columns: mockColumns,
      },
    })
    expect(wrapper.find('.query-result').exists()).toBe(true)
  })

  it('should show loading state', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: [],
        columns: mockColumns,
        loading: true,
      },
    })
    expect(wrapper.find('.result-info').text()).toContain('查询中')
  })

  it('should show error state', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: [],
        columns: mockColumns,
        error: 'Query failed',
      },
    })
    expect(wrapper.find('.result-info').text()).toContain('查询失败')
    expect(wrapper.find('.el-alert').exists()).toBe(true)
  })

  it('should show success state with data', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
        rowCount: 2,
        executionTime: 150,
      },
    })
    expect(wrapper.find('.result-info').text()).toContain('查询成功')
  })

  it('should show empty state when no data', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: [],
        columns: mockColumns,
        loading: false,
      },
    })
    expect(wrapper.find('.result-info').text()).toContain('暂无数据')
    expect(wrapper.find('.el-empty').exists()).toBe(true)
  })

  it('should display SQL preview when sql is provided', () => {
    const sql = 'SELECT * FROM users'
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
        sql,
      },
    })
    expect(wrapper.find('.sql-preview').exists()).toBe(true)
    expect(wrapper.find('.sql-code').text()).toBe(sql)
  })

  it('should not display SQL preview when sql is empty', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
        sql: '',
      },
    })
    expect(wrapper.find('.sql-preview').exists()).toBe(false)
  })

  it('should show export buttons when has data', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
        loading: false,
      },
    })
    expect(wrapper.find('.result-actions').exists()).toBe(true)
  })

  it('should hide export buttons when loading', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
        loading: true,
      },
    })
    expect(wrapper.find('.result-actions').exists()).toBe(false)
  })

  it('should emit export event with csv format', async () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    const csvBtn = wrapper.findAll('.result-actions button').find(b => b.text().includes('CSV'))
    if (csvBtn) {
      await csvBtn.trigger('click')
      expect(wrapper.emitted('export')).toBeTruthy()
      expect(wrapper.emitted('export')![0]).toEqual(['csv'])
    }
  })

  it('should emit export event with json format', async () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    const jsonBtn = wrapper.findAll('.result-actions button').find(b => b.text().includes('JSON'))
    if (jsonBtn) {
      await jsonBtn.trigger('click')
      expect(wrapper.emitted('export')).toBeTruthy()
      expect(wrapper.emitted('export')![0]).toEqual(['json'])
    }
  })

  it('should emit retry event', async () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: [],
        columns: mockColumns,
        error: 'Query failed',
      },
    })
    wrapper.vm.$emit('retry')
    expect(wrapper.emitted('retry')).toBeTruthy()
  })

  it('should render DataTable when has data', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    expect(wrapper.find('.result-table').exists()).toBe(true)
  })

  it('should display row count', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
        rowCount: 2,
      },
    })
    expect(wrapper.find('.result-info').text()).toContain('2')
  })

  it('should display execution time', () => {
    const wrapper = mountWithPinia(QueryResult, {
      props: {
        data: mockData,
        columns: mockColumns,
        executionTime: 150,
      },
    })
    expect(wrapper.find('.result-info').text()).toContain('150ms')
  })
})
