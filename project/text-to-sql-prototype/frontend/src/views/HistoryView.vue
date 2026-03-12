<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import * as queryApi from '@/api/queries'
import * as connectionApi from '@/api/connections'
import type { QueryHistory, Connection, QueryHistoryParams } from '@/types'

const router = useRouter()

// ==================== State ====================

// 历史记录列表
const historyList = ref<QueryHistory[]>([])
const loading = ref(false)
const total = ref(0)

// 连接列表（用于筛选）
const connections = ref<Connection[]>([])

// 搜索和筛选
const searchForm = reactive({
  keyword: '',
  connection_id: undefined as number | undefined,
  is_favorite: undefined as boolean | undefined,
  date_range: [] as Date[],
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
})

// 详情弹窗
const detailVisible = ref(false)
const detailData = ref<QueryHistory | null>(null)

// ==================== Computed ====================

const columns = computed(() => [
  { prop: 'question', label: '问题', minWidth: 200, showOverflowTooltip: true },
  { prop: 'sql', label: '生成的SQL', minWidth: 250, showOverflowTooltip: true },
  { prop: 'connection_name', label: '数据库', width: 120 },
  { prop: 'execution_status', label: '状态', width: 100, slot: 'status' },
  { prop: 'is_favorite', label: '收藏', width: 80, slot: 'favorite' },
  { prop: 'created_at', label: '创建时间', width: 180 },
  { prop: 'actions', label: '操作', width: 200, slot: 'actions', fixed: 'right' as const },
])

// ==================== Methods ====================

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  try {
    const params: QueryHistoryParams = {
      page: pagination.page,
      page_size: pagination.page_size,
    }

    if (searchForm.keyword) {
      params.keyword = searchForm.keyword
    }
    if (searchForm.connection_id) {
      params.connection_id = searchForm.connection_id
    }
    if (searchForm.is_favorite !== undefined) {
      params.is_favorite = searchForm.is_favorite
    }

    const response = await queryApi.getQueryHistory(params)
    historyList.value = response.list || []
    total.value = response.pagination?.total || 0
  } catch (error) {
    console.error('Failed to load history:', error)
    ElMessage.error('加载查询历史失败')
  } finally {
    loading.value = false
  }
}

// 加载连接列表
const loadConnections = async () => {
  try {
    const response = await connectionApi.getConnections({ page: 1, page_size: 100 })
    connections.value = response.list || []
  } catch (error) {
    console.error('Failed to load connections:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadHistory()
}

// 重置筛选
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.connection_id = undefined
  searchForm.is_favorite = undefined
  searchForm.date_range = []
  pagination.page = 1
  loadHistory()
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.page = page
  loadHistory()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  loadHistory()
}

// 查看详情
const handleViewDetail = (row: QueryHistory) => {
  detailData.value = row
  detailVisible.value = true
}

// 重新执行
const handleReexecute = (row: QueryHistory) => {
  // 跳转到查询页面并携带参数
  router.push({
    path: '/query',
    query: {
      connection_id: row.connection_id,
      question: row.question,
    },
  })
}

// 切换收藏
const handleToggleFavorite = async (row: QueryHistory) => {
  try {
    await queryApi.toggleFavorite(row.id, !row.is_favorite)
    row.is_favorite = !row.is_favorite
    ElMessage.success(row.is_favorite ? '已收藏' : '已取消收藏')
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
    ElMessage.error('操作失败')
  }
}

// 删除历史记录
const handleDelete = (row: QueryHistory) => {
  ElMessageBox.confirm('确定要删除这条查询记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await queryApi.deleteQueryHistory(row.id)
      ElMessage.success('删除成功')
      loadHistory()
    } catch (error) {
      console.error('Failed to delete history:', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 批量删除
const handleBatchDelete = (selection: QueryHistory[]) => {
  if (selection.length === 0) {
    ElMessage.warning('请选择要删除的记录')
    return
  }

  ElMessageBox.confirm(`确定要删除选中的 ${selection.length} 条记录吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      // 并行删除
      await Promise.all(selection.map(item => queryApi.deleteQueryHistory(item.id)))
      ElMessage.success('批量删除成功')
      loadHistory()
    } catch (error) {
      console.error('Failed to batch delete:', error)
      ElMessage.error('批量删除失败')
    }
  }).catch(() => {})
}

// 获取状态类型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    pending: 'warning',
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    pending: '待执行',
  }
  return textMap[status] || '未知'
}

// 格式化 SQL 预览
const formatSQLPreview = (sql: string, maxLength = 100) => {
  const trimmed = sql.replace(/\s+/g, ' ').trim()
  if (trimmed.length <= maxLength) return trimmed
  return trimmed.slice(0, maxLength) + '...'
}

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

// 导出 CSV
const handleExportCSV = () => {
  if (historyList.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const headers = ['问题', 'SQL', '数据库', '状态', '收藏', '创建时间']
  const rows = historyList.value.map(item => [
    item.question,
    item.sql,
    item.connection_name || '未知',
    getStatusText(item.execution_status),
    item.is_favorite ? '是' : '否',
    formatTime(item.created_at),
  ])

  const csvContent = [headers, ...rows]
    .map(row =>
      row
        .map(cell => {
          const str = String(cell || '')
          if (str.includes(',') || str.includes('\n') || str.includes('"')) {
            return `"${str.replace(/"/g, '""')}"`
          }
          return str
        })
        .join(','),
    )
    .join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `query_history_${Date.now()}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('导出成功')
}

// ==================== Lifecycle ====================

onMounted(() => {
  loadHistory()
  loadConnections()
})

// 监听路由查询参数（从其他页面跳转过来）
watch(
  () => router.currentRoute.value.query,
  (query) => {
    if (query.connection_id) {
      searchForm.connection_id = Number(query.connection_id)
      handleSearch()
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="history-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>查询历史</span>
          <el-button type="primary" @click="handleExportCSV">
            <el-icon><Download /></el-icon>
            导出 CSV
          </el-button>
        </div>
      </template>

      <!-- 搜索筛选区 -->
      <div class="search-section">
        <el-form :model="searchForm" inline>
          <el-form-item label="关键词">
            <el-input
              v-model="searchForm.keyword"
              placeholder="搜索问题或SQL"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>

          <el-form-item label="数据库">
            <el-select
              v-model="searchForm.connection_id"
              placeholder="选择数据库"
              clearable
              style="width: 150px"
            >
              <el-option
                v-for="conn in connections"
                :key="conn.id"
                :label="conn.name"
                :value="conn.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="收藏">
            <el-select
              v-model="searchForm.is_favorite"
              placeholder="全部"
              clearable
              style="width: 120px"
            >
              <el-option label="已收藏" :value="true" />
              <el-option label="未收藏" :value="false" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 数据表格 -->
      <DataTable
        :data="historyList"
        :columns="columns"
        :loading="loading"
        :pagination="{
          currentPage: pagination.page,
          pageSize: pagination.page_size,
          total,
        }"
        selectable
        border
        stripe
        @page-change="handlePageChange"
        @size-change="handleSizeChange"
        @selection-change="handleBatchDelete"
      >
        <!-- 状态列 -->
        <template #status="{ row }">
          <el-tag :type="getStatusType(row.execution_status)" size="small">
            {{ getStatusText(row.execution_status) }}
          </el-tag>
        </template>

        <!-- 收藏列 -->
        <template #favorite="{ row }">
          <el-icon
            class="favorite-icon"
            :class="{ 'is-favorite': row.is_favorite }"
            @click="handleToggleFavorite(row)"
          >
            <Star v-if="row.is_favorite" />
            <StarFilled v-else />
          </el-icon>
        </template>

        <!-- SQL 列 -->
        <template #sql="{ row }">
          <code class="sql-preview">{{ formatSQLPreview(row.sql) }}</code>
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <el-button type="primary" link size="small" @click="handleViewDetail(row)">
            <el-icon><View /></el-icon>
            详情
          </el-button>
          <el-button type="success" link size="small" @click="handleReexecute(row)">
            <el-icon><VideoPlay /></el-icon>
            执行
          </el-button>
          <el-button
            :type="row.is_favorite ? 'warning' : 'info'"
            link
            size="small"
            @click="handleToggleFavorite(row)"
          >
            <el-icon>
              <Star v-if="!row.is_favorite" />
              <StarFilled v-else />
            </el-icon>
            {{ row.is_favorite ? '取消收藏' : '收藏' }}
          </el-button>
          <el-popconfirm
            title="确定删除该记录吗？"
            confirm-button-text="确定"
            cancel-button-text="取消"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button type="danger" link size="small">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>

        <!-- 空状态 -->
        <template #empty>
          <el-empty description="暂无查询历史">
            <el-button type="primary" @click="router.push('/query')">
              去查询
            </el-button>
          </el-empty>
        </template>
      </DataTable>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="查询详情"
      width="800px"
      destroy-on-close
    >
      <div v-if="detailData" class="detail-content">
        <div class="detail-section">
          <div class="detail-label">问题</div>
          <div class="detail-value">{{ detailData.question }}</div>
        </div>

        <div class="detail-section">
          <div class="detail-label">生成的 SQL</div>
          <pre class="detail-sql">{{ detailData.sql }}</pre>
        </div>

        <div v-if="detailData.explanation" class="detail-section">
          <div class="detail-label">解释</div>
          <div class="detail-value">{{ detailData.explanation }}</div>
        </div>

        <div class="detail-row">
          <div class="detail-section">
            <div class="detail-label">数据库</div>
            <div class="detail-value">{{ detailData.connection_name || '未知' }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">状态</div>
            <el-tag :type="getStatusType(detailData.execution_status)">
              {{ getStatusText(detailData.execution_status) }}
            </el-tag>
          </div>
          <div class="detail-section">
            <div class="detail-label">置信度</div>
            <div class="detail-value">
              {{ detailData.confidence ? `${(detailData.confidence * 100).toFixed(1)}%` : '-' }}
            </div>
          </div>
        </div>

        <div class="detail-row">
          <div class="detail-section">
            <div class="detail-label">收藏</div>
            <el-icon :class="{ 'is-favorite': detailData.is_favorite }" class="detail-favorite">
              <Star v-if="detailData.is_favorite" />
              <StarFilled v-else />
            </el-icon>
          </div>
          <div class="detail-section">
            <div class="detail-label">创建时间</div>
            <div class="detail-value">{{ formatTime(detailData.created_at) }}</div>
          </div>
        </div>

        <!-- 结果预览 -->
        <div v-if="detailData.result_preview" class="detail-section">
          <div class="detail-label">结果预览</div>
          <el-table :data="detailData.result_preview.rows" border size="small">
            <el-table-column
              v-for="col in detailData.result_preview.columns"
              :key="col"
              :prop="col"
              :label="col"
            />
          </el-table>
        </div>

        <!-- 错误信息 -->
        <div v-if="detailData.error_message" class="detail-section">
          <div class="detail-label">错误信息</div>
          <el-alert :title="detailData.error_message" type="error" :closable="false" />
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleReexecute(detailData!)">
          <el-icon><VideoPlay /></el-icon>
          重新执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.history-page {
  padding: 16px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
  }

  .search-section {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-light);

    .el-form {
      margin-bottom: -16px;
    }
  }

  .sql-preview {
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    background: var(--el-fill-color-light);
    padding: 4px 8px;
    border-radius: 4px;
  }

  .favorite-icon {
    font-size: 18px;
    color: var(--el-text-color-placeholder);
    cursor: pointer;
    transition: color 0.2s;

    &:hover,
    &.is-favorite {
      color: var(--el-color-warning);
    }
  }
}

// 详情弹窗样式
.detail-content {
  .detail-section {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }

    .detail-label {
      font-size: 13px;
      color: var(--el-text-color-secondary);
      margin-bottom: 8px;
    }

    .detail-value {
      font-size: 14px;
      color: var(--el-text-color-primary);
      line-height: 1.5;
    }

    .detail-sql {
      margin: 0;
      padding: 12px;
      background: var(--el-fill-color-light);
      border-radius: 4px;
      font-family: 'Fira Code', 'Consolas', monospace;
      font-size: 13px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }

    .detail-favorite {
      font-size: 20px;
      color: var(--el-text-color-placeholder);

      &.is-favorite {
        color: var(--el-color-warning);
      }
    }
  }

  .detail-row {
    display: flex;
    gap: 40px;
    margin-bottom: 20px;

    .detail-section {
      margin-bottom: 0;
    }
  }
}
</style>
