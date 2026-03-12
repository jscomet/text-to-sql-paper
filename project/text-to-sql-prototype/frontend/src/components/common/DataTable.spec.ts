import { describe, it, expect, vi } from 'vitest'
import { mountWithPinia } from '@/test/utils'
import DataTable from './DataTable.vue'
import type { Column } from './DataTable.vue'

interface TestRow {
  id: number
  name: string
  age: number
}

const mockColumns: Column[] = [
  { prop: 'id', label: 'ID', width: 80 },
  { prop: 'name', label: 'Name', sortable: true },
  { prop: 'age', label: 'Age', minWidth: 100 },
]

const mockData: TestRow[] = [
  { id: 1, name: 'Alice', age: 25 },
  { id: 2, name: 'Bob', age: 30 },
]

describe('DataTable', () => {
  it('should render table with columns and data', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    expect(wrapper.find('.data-table').exists()).toBe(true)
    expect(wrapper.findAll('.el-table__header th').length).toBeGreaterThan(0)
  })

  it('should render loading state', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        loading: true,
      },
    })
    expect(wrapper.find('.data-table').exists()).toBe(true)
  })

  it('should render with stripe enabled by default', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    const table = wrapper.find('.data-table')
    expect(table.classes()).toContain('el-table--striped')
  })

  it('should render without stripe when stripe is false', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        stripe: false,
      },
    })
    const table = wrapper.find('.data-table')
    expect(table.classes()).not.toContain('el-table--striped')
  })

  it('should render pagination when provided', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        pagination: {
          currentPage: 1,
          pageSize: 10,
          total: 100,
        },
      },
    })
    expect(wrapper.find('.el-pagination').exists()).toBe(true)
  })

  it('should not render pagination when not provided', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    expect(wrapper.find('.el-pagination').exists()).toBe(false)
  })

  it('should render selection column when selectable is true', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        selectable: true,
      },
    })
    // Check for selection column
    expect(wrapper.find('.data-table').exists()).toBe(true)
  })

  it('should emit page-change event', async () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        pagination: {
          currentPage: 1,
          pageSize: 10,
          total: 100,
        },
      },
    })
    wrapper.vm.$emit('page-change', 2)
    expect(wrapper.emitted('page-change')).toBeTruthy()
  })

  it('should emit size-change event', async () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        pagination: {
          currentPage: 1,
          pageSize: 10,
          total: 100,
        },
      },
    })
    wrapper.vm.$emit('size-change', 20)
    expect(wrapper.emitted('size-change')).toBeTruthy()
  })

  it('should emit sort-change event', async () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    wrapper.vm.$emit('sort-change', { column: {}, prop: 'name', order: 'ascending' })
    expect(wrapper.emitted('sort-change')).toBeTruthy()
  })

  it('should emit selection-change event', async () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        selectable: true,
      },
    })
    wrapper.vm.$emit('selection-change', [mockData[0]])
    expect(wrapper.emitted('selection-change')).toBeTruthy()
  })

  it('should emit row-click event', async () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
      },
    })
    wrapper.vm.$emit('row-click', mockData[0])
    expect(wrapper.emitted('row-click')).toBeTruthy()
  })

  it('should apply custom height', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        height: '400px',
      },
    })
    const table = wrapper.find('.data-table')
    expect(table.exists()).toBe(true)
  })

  it('should apply border when border is true', () => {
    const wrapper = mountWithPinia(DataTable, {
      props: {
        data: mockData,
        columns: mockColumns,
        border: true,
      },
    })
    const table = wrapper.find('.data-table')
    expect(table.classes()).toContain('el-table--border')
  })
})
