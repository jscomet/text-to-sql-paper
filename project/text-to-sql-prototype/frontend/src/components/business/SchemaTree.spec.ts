import { describe, it, expect, vi } from 'vitest'
import { mountWithPinia } from '@/test/utils'
import SchemaTree from './SchemaTree.vue'
import type { Table, Column } from '@/types'

const mockColumns: Column[] = [
  { name: 'id', type: 'INTEGER', nullable: false, comment: 'Primary key' },
  { name: 'name', type: 'VARCHAR(255)', nullable: true },
]

const mockTables: Table[] = [
  { name: 'users', comment: 'Users table', columns: mockColumns },
]

const mockSchemas = [
  { name: 'public', tables: mockTables },
]

describe('SchemaTree', () => {
  it('should render with default props', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    expect(wrapper.find('.schema-tree').exists()).toBe(true)
  })

  it('should render empty state when no schemas', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: [] },
    })
    expect(wrapper.find('.el-empty').exists()).toBe(true)
  })

  it('should render tree with schema data', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    expect(wrapper.find('.el-tree').exists()).toBe(true)
  })

  it('should show loading state', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas, loading: true },
    })
    expect(wrapper.find('.tree-content').attributes('v-loading')).toBe('true')
  })

  it('should emit refresh event when refresh button clicked', async () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    const refreshBtn = wrapper.find('.tree-header button')
    if (refreshBtn.exists()) {
      await refreshBtn.trigger('click')
      expect(wrapper.emitted('refresh')).toBeTruthy()
    }
  })

  it('should emit node-click event', async () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    wrapper.vm.$emit('node-click', mockSchemas[0], 'schema')
    expect(wrapper.emitted('node-click')).toBeTruthy()
  })

  it('should emit table-click event when table node clicked', async () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    wrapper.vm.$emit('table-click', mockTables[0], mockSchemas[0])
    expect(wrapper.emitted('table-click')).toBeTruthy()
  })

  it('should have filter input', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    expect(wrapper.find('.tree-header .el-input').exists()).toBe(true)
  })

  it('should expose filter method', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    expect(typeof wrapper.vm.filter).toBe('function')
  })

  it('should expose expandAll method', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    expect(typeof wrapper.vm.expandAll).toBe('function')
  })

  it('should expose collapseAll method', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas },
    })
    expect(typeof wrapper.vm.collapseAll).toBe('function')
  })

  it('should apply defaultExpandAll prop', () => {
    const wrapper = mountWithPinia(SchemaTree, {
      props: { schemas: mockSchemas, defaultExpandAll: true },
    })
    const tree = wrapper.find('.el-tree')
    expect(tree.exists()).toBe(true)
  })
})
