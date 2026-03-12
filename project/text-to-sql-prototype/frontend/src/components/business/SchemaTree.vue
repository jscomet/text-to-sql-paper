<script setup lang="ts">
import { computed, ref } from "vue"

interface Column {
  name: string
  type: string
  nullable: boolean
  default?: string
  comment?: string
}

interface Table {
  name: string
  comment?: string
  columns: Column[]
}

interface Schema {
  name: string
  tables: Table[]
}

interface Props {
  schemas: Schema[]
  loading?: boolean
  defaultExpandAll?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  defaultExpandAll: false,
})

interface TreeNodeData {
  id: string
  label: string
  type: 'schema' | 'table' | 'column'
  data: Schema | Table | Column
  schema?: Schema
  isLeaf?: boolean
  children?: TreeNodeData[]
}

const emit = defineEmits<{
  (e: 'node-click', data: Schema | Table | Column, nodeType: 'schema' | 'table' | 'column'): void
  (e: 'table-click', table: Table, schema: Schema): void
  (e: 'refresh'): void
}>()

const filterText = ref("")
const treeRef = ref()

const treeData = computed((): TreeNodeData[] => {
  return props.schemas.map((schema): TreeNodeData => ({
    id: `schema-${schema.name}`,
    label: schema.name,
    type: 'schema' as const,
    data: schema,
    children: schema.tables.map((table): TreeNodeData => ({
      id: `table-${schema.name}-${table.name}`,
      label: table.name,
      type: 'table' as const,
      data: table,
      schema: schema,
      children: table.columns.map((col): TreeNodeData => ({
        id: `col-${schema.name}-${table.name}-${col.name}`,
        label: col.name,
        type: 'column' as const,
        data: col,
        isLeaf: true,
      })),
    })),
  }))
})

const filterNode = (value: string, data: TreeNodeData) => {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

const handleFilter = () => {
  treeRef.value?.filter(filterText.value)
}

const handleNodeClick = (data: TreeNodeData) => {
  emit('node-click', data.data, data.type)
  if (data.type === 'table' && data.schema) {
    emit('table-click', data.data as Table, data.schema)
  }
}

const handleRefresh = () => {
  emit('refresh')
}

const getNodeIcon = (data: TreeNodeData) => {
  switch (data.type) {
    case 'schema':
      return 'FolderOpened'
    case 'table':
      return 'Grid'
    case 'column':
      return (data.data as Column).nullable ? 'Minus' : 'Key'
    default:
      return 'Document'
  }
}

const getColumnTypeClass = (type: string) => {
  const lowerType = type.toLowerCase()
  if (lowerType.includes("int") || lowerType.includes("serial")) {
    return "type-int"
  }
  if (lowerType.includes("char") || lowerType.includes("text")) {
    return "type-string"
  }
  if (lowerType.includes("date") || lowerType.includes("time")) {
    return "type-date"
  }
  if (lowerType.includes("bool")) {
    return "type-bool"
  }
  if (lowerType.includes("float") || lowerType.includes("double") || lowerType.includes("decimal") || lowerType.includes("numeric")) {
    return "type-float"
  }
  return "type-default"
}

defineExpose({
  filter: handleFilter,
  expandAll: () => treeRef.value?.expandAll(),
  collapseAll: () => treeRef.value?.collapseAll(),
})
</script>

<template>
  <div class="schema-tree">
    <div class="tree-header">
      <el-input v-model="filterText" placeholder="搜索表或字段..." clearable size="small" @input="handleFilter">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button link size="small" :loading="loading" @click="handleRefresh">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <div v-loading="loading" class="tree-content">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="{ label: 'label', children: 'children' }"
        :filter-node-method="filterNode"
        :default-expand-all="defaultExpandAll"
        node-key="id"
        highlight-current
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <span class="tree-node" :class="`node-${data.type}`">
            <el-icon :size="14">
              <component :is="getNodeIcon(data)" />
            </el-icon>
            <span class="node-label">{{ node.label }}</span>
            <span v-if="data.type === 'column'" class="column-type" :class="getColumnTypeClass(data.data.type)">
              {{ data.data.type }}
            </span>
            <span v-if="data.type === 'column' && !data.data.nullable" class="not-null">NOT NULL</span>
          </span>
        </template>
      </el-tree>

      <el-empty v-if="!loading && schemas.length === 0" description="暂无Schema数据" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.schema-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid var(--border-light);

  .tree-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-bottom: 1px solid var(--border-light);

    .el-input {
      flex: 1;
    }
  }

  .tree-content {
    flex: 1;
    overflow: auto;
    padding: 8px 0;

    :deep(.el-tree) {
      .el-tree-node__content {
        height: 32px;
        padding-right: 12px;
      }
    }

    .tree-node {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;

      &.node-schema {
        font-weight: 500;
        color: var(--text-primary);
      }

      &.node-table {
        color: var(--text-regular);
      }

      &.node-column {
        color: var(--text-secondary);
        font-size: 12px;
      }

      .node-label {
        flex: 1;
      }

      .column-type {
        font-size: 11px;
        padding: 1px 6px;
        border-radius: 3px;
        font-family: monospace;

        &.type-int {
          background: #e6f7ff;
          color: #1890ff;
        }

        &.type-string {
          background: #f6ffed;
          color: #52c41a;
        }

        &.type-date {
          background: #fff7e6;
          color: #fa8c16;
        }

        &.type-bool {
          background: #f9f0ff;
          color: #722ed1;
        }

        &.type-float {
          background: #fff2f0;
          color: #f5222d;
        }

        &.type-default {
          background: var(--bg-color);
          color: var(--text-secondary);
        }
      }

      .not-null {
        font-size: 10px;
        color: var(--danger-color);
        font-weight: 500;
      }
    }
  }
}
</style>
