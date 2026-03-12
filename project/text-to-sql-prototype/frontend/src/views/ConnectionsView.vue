<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Connection } from '@element-plus/icons-vue'
import type { Connection as ConnectionType, PaginationParams } from '@/types'
import {
  getConnections,
  createConnection,
  updateConnection,
  deleteConnection,
  testConnection,
  type CreateConnectionParams,
  type UpdateConnectionParams,
} from '@/api/connections'
import ConnectionFormDialog from '@/components/ConnectionFormDialog.vue'

// 加载状态
const loading = ref(false)
const testLoading = ref<number | null>(null)

// 连接列表数据
const connections = ref<ConnectionType[]>([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0,
})

// 搜索关键词
const searchKeyword = ref('')

// 对话框状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentConnection = ref<ConnectionType | null>(null)

// 获取错误消息
const getErrorMessage = (error: unknown): string => {
  if (error && typeof error === 'object' && 'response' in error) {
    const errWithResponse = error as { response?: { data?: { message?: string } } }
    return errWithResponse.response?.data?.message || ''
  }
  return ''
}

// 加载连接列表
const loadConnections = async () => {
  loading.value = true
  try {
    const params: PaginationParams & { keyword?: string } = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    // 如果有搜索关键词，添加到请求参数
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value.trim()
    }
    const res = await getConnections(params)
    connections.value = res.list
    pagination.total = res.pagination.total
    pagination.total_pages = res.pagination.total_pages
  } catch (error) {
    ElMessage.error('加载连接列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索连接
const handleSearch = () => {
  pagination.page = 1
  loadConnections()
}

// 处理分页变化
const handlePageChange = (page: number) => {
  pagination.page = page
  loadConnections()
}

// 处理每页条数变化
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  loadConnections()
}

// 处理添加连接
const handleAdd = () => {
  isEdit.value = false
  currentConnection.value = null
  dialogVisible.value = true
}

// 处理编辑连接
const handleEdit = (row: ConnectionType) => {
  isEdit.value = true
  currentConnection.value = row
  dialogVisible.value = true
}

// 处理删除连接
const handleDelete = async (row: ConnectionType) => {
  try {
    await ElMessageBox.confirm(
      `确定删除连接 "${row.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteConnection(row.id)
    ElMessage.success('删除成功')
    loadConnections()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

// 处理测试连接
const handleTest = async (row: ConnectionType) => {
  testLoading.value = row.id
  try {
    const res = await testConnection({
      db_type: row.db_type,
      host: row.host,
      port: row.port,
      database: row.database,
      username: row.username || '',
      password: '', // 测试现有连接不需要密码
    })

    if (res.connected) {
      ElMessage.success(`连接成功${res.server_version ? ` (${res.server_version})` : ''}`)
    } else {
      ElMessage.error(res.message || '连接失败')
    }
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error) || '测试连接失败')
  } finally {
    testLoading.value = null
  }
}

// 处理表单提交
const handleSubmit = async (formData: CreateConnectionParams | UpdateConnectionParams) => {
  try {
    if (isEdit.value && currentConnection.value) {
      await updateConnection(currentConnection.value.id, formData as UpdateConnectionParams)
      ElMessage.success('更新成功')
    } else {
      await createConnection(formData as CreateConnectionParams)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadConnections()
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error) || (isEdit.value ? '更新失败' : '创建失败'))
    throw error
  }
}

// 获取状态标签类型
const getStatusType = (status: ConnectionType['status']) => {
  const typeMap: Record<string, 'success' | 'info' | 'danger' | 'warning'> = {
    active: 'success',
    inactive: 'info',
    error: 'danger',
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: ConnectionType['status']) => {
  const textMap: Record<string, string> = {
    active: '正常',
    inactive: '未激活',
    error: '错误',
  }
  return textMap[status] || '未知'
}

// 获取数据库类型标签
const getDbTypeLabel = (dbType: ConnectionType['db_type']) => {
  const labelMap: Record<string, string> = {
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    sqlite: 'SQLite',
    sqlserver: 'SQL Server',
    oracle: 'Oracle',
  }
  return labelMap[dbType] || dbType
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadConnections()
})
</script>

<template>
  <div class="connections-page">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="title">数据库连接管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon class="el-icon--left"><Plus /></el-icon>
            添加连接
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索连接名称..."
          clearable
          style="width: 300px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
      </div>

      <!-- 连接列表表格 -->
      <el-table :data="connections" style="width: 100%" border>
        <el-table-column prop="name" label="连接名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="数据库类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">
              {{ getDbTypeLabel(row.db_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="host" label="主机" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.host || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="port" label="端口" width="80">
          <template #default="{ row }">
            {{ row.port || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="database" label="数据库" min-width="120" show-overflow-tooltip />
        <el-table-column prop="username" label="用户名" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :loading="testLoading === row.id"
              @click="handleTest(row)"
            >
              <el-icon v-if="testLoading !== row.id"><Connection /></el-icon>
              测试
            </el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="!loading && connections.length === 0" description="暂无数据库连接" />

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑连接对话框 -->
    <ConnectionFormDialog
      v-model:visible="dialogVisible"
      :is-edit="isEdit"
      :connection="currentConnection"
      @submit="handleSubmit"
    />
  </div>
</template>

<style scoped lang="scss">
.connections-page {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title {
    font-weight: bold;
    font-size: 16px;
  }
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
