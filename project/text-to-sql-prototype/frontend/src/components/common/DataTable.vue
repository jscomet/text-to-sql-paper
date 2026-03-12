<script setup lang="ts" generic="T extends Record<string, any>">
import { computed } from 'vue'

export interface Column {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  sortable?: boolean
  fixed?: 'left' | 'right'
  formatter?: (row: unknown, column: unknown, cellValue: unknown, index: number) => string
  slot?: string
  showOverflowTooltip?: boolean
}

interface Props {
  data: T[]
  columns: Column[]
  loading?: boolean
  pagination?: {
    currentPage: number
    pageSize: number
    total: number
  }
  selectable?: boolean
  stripe?: boolean
  border?: boolean
  height?: string | number
  maxHeight?: string | number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  selectable: false,
  stripe: true,
  border: false,
})

const emit = defineEmits<{
  (e: 'page-change', page: number): void
  (e: 'size-change', size: number): void
  (e: 'sort-change', data: { column: unknown; prop: string; order: string | null }): void
  (e: 'selection-change', selection: T[]): void
  (e: 'row-click', row: T): void
}>()

const currentPage = computed({
  get: () => props.pagination?.currentPage || 1,
  set: (val) => emit('page-change', val),
})

const pageSize = computed({
  get: () => props.pagination?.pageSize || 10,
  set: (val) => emit('size-change', val),
})

const handlePageChange = (page: number) => {
  emit('page-change', page)
}

const handleSizeChange = (size: number) => {
  emit('size-change', size)
}

const handleSortChange = (data: { column: unknown; prop: string; order: string | null }) => {
  emit('sort-change', data)
}

const handleSelectionChange = (selection: T[]) => {
  emit('selection-change', selection)
}

const handleRowClick = (row: T) => {
  emit('row-click', row)
}
</script>

<template>
  <div class="data-table-wrapper">
    <el-table
      v-loading="loading"
      :data="data"
      :stripe="stripe"
      :border="border"
      :height="height"
      :max-height="maxHeight"
      class="data-table"
      @sort-change="handleSortChange"
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
    >
      <el-table-column v-if="selectable" type="selection" width="55" />
      <el-table-column v-if="$slots.index" type="index" width="60" label="序号">
        <template #default="scope">
          <slot name="index" :index="scope.$index" :row="scope.row" />
        </template>
      </el-table-column>
      <el-table-column v-else type="index" width="60" label="序号" />

      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :sortable="col.sortable"
        :fixed="col.fixed"
        :formatter="col.formatter"
      >
        <template #default="scope" v-if="$slots[col.slot || col.prop]">
          <slot :name="col.slot || col.prop" :row="scope.row" :index="scope.$index" />
        </template>
      </el-table-column>

      <template #empty>
        <slot name="empty">
          <el-empty description="暂无数据" />
        </slot>
      </template>
    </el-table>

    <div v-if="pagination" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.data-table-wrapper {
  background: #fff;
  border-radius: 4px;
}

.data-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px;
  border-top: 1px solid var(--border-lighter);
}
</style>
