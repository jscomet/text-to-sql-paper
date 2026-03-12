<script setup lang="ts" generic="T extends Record<string, any>">
import { computed } from "vue"
import DataTable from "@/components/common/DataTable.vue"

interface Props {
  data: T[]
  columns: { prop: string; label: string }[]
  loading?: boolean
  error?: string | null
  executionTime?: number
  rowCount?: number
  sql?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: null,
  executionTime: 0,
  rowCount: 0,
  sql: "",
})

const emit = defineEmits<{
  (e: "export", format: "csv" | "json"): void
  (e: "retry"): void
}>()

const hasData = computed(() => props.data.length > 0)

const handleExportCSV = () => {
  emit("export", "csv")
}

const handleExportJSON = () => {
  emit("export", "json")
}

const handleRetry = () => {
  emit("retry")
}
</script>

<template>
  <div class="query-result">
    <div class="result-header">
      <div class="result-info">
        <template v-if="loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>查询中...</span>
        </template>
        <template v-else-if="error">
          <el-icon color="var(--danger-color)"><CircleClose /></el-icon>
          <span class="error-text">查询失败</span>
        </template>
        <template v-else-if="hasData">
          <el-icon color="var(--success-color)"><CircleCheck /></el-icon>
          <span>查询成功</span>
          <el-tag size="small" type="info">{{ rowCount }} 行</el-tag>
          <el-tag size="small" type="info">{{ executionTime }}ms</el-tag>
        </template>
        <template v-else>
          <el-icon><InfoFilled /></el-icon>
          <span>暂无数据</span>
        </template>
      </div>
      <div v-if="hasData && !loading" class="result-actions">
        <el-button link size="small" @click="handleExportCSV">
          <el-icon><Download /></el-icon>导出 CSV
        </el-button>
        <el-button link size="small" @click="handleExportJSON">
          <el-icon><Document /></el-icon>导出 JSON
        </el-button>
      </div>
    </div>

    <div v-if="sql" class="sql-preview">
      <div class="sql-label">执行SQL:</div>
      <pre class="sql-code">{{ sql }}</pre>
    </div>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon class="error-alert">
      <template #default>
        <el-button link type="primary" @click="handleRetry">重试</el-button>
      </template>
    </el-alert>

    <div v-else-if="hasData" class="result-table">
      <DataTable :data="data" :columns="columns.map(col => ({ ...col, minWidth: 120 }))" :loading="loading" :max-height="400" border />
    </div>

    <div v-else-if="!loading" class="empty-result">
      <el-empty description="查询结果为空" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.query-result {
  background: #fff;
  border-radius: 4px;
  border: 1px solid var(--border-light);

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-light);
    background: var(--bg-color);

    .result-info {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: var(--text-regular);

      .error-text {
        color: var(--danger-color);
      }

      .el-tag {
        margin-left: 4px;
      }
    }

    .result-actions {
      display: flex;
      gap: 8px;
    }
  }

  .sql-preview {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-light);
    background: #fafafa;

    .sql-label {
      font-size: 12px;
      color: var(--text-secondary);
      margin-bottom: 4px;
    }

    .sql-code {
      margin: 0;
      padding: 8px 12px;
      background: #f5f5f5;
      border-radius: 4px;
      font-family: "Fira Code", "Consolas", monospace;
      font-size: 13px;
      color: var(--text-primary);
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
  }

  .error-alert {
    margin: 16px;
  }

  .result-table {
    padding: 16px;
  }

  .empty-result {
    padding: 40px 0;
  }
}
</style>
