<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEvalTasks,
  createEvalTask,
  deleteEvalTask,
  cancelEvalTask,
  getEvalTask,
  type EvalTaskParams,
  type TaskStatus,
} from '@/api/evaluations'
import { importDatasetZip, importDatasetLocal } from '@/api/dataset'
import type { EvalTask, CreateEvalTaskRequest, ImportConfig } from '@/types'
import { getConnections } from '@/api/connections'
import type { Connection } from '@/types'
import EvalTaskFormDialog from '@/components/EvalTaskFormDialog.vue'
import ImportDialog from '@/components/dataset/ImportDialog.vue'
import ProgressDialog from '@/components/dataset/ProgressDialog.vue'

const router = useRouter()

// 评测任务列表
const taskList = ref<EvalTask[]>([])
const loading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 状态筛选
const statusFilter = ref<TaskStatus | ''>('')

// 对话框显示状态
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const progressDialogVisible = ref(false)

// 导入状态
const currentImportId = ref<string | null>(null)
const importCompleted = ref(false)

// 连接列表（用于表单）
const connections = ref<Connection[]>([])

// 定时刷新器
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 是否有进行中的任务
const hasRunningTasks = computed(() => {
  return taskList.value.some(
    (task) => task.status === 'pending' || task.status === 'running'
  )
})

// 加载评测任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const params: EvalTaskParams = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const res = await getEvalTasks(params)
    taskList.value = res.list
    total.value = res.pagination.total
  } catch (error) {
    console.error('加载评测任务失败:', error)
    ElMessage.error('加载评测任务失败')
  } finally {
    loading.value = false
  }
}

// 加载连接列表
const loadConnections = async () => {
  try {
    const res = await getConnections({ page: 1, page_size: 100 })
    connections.value = res.list || []
  } catch (error) {
    console.error('加载连接列表失败:', error)
  }
}

// 刷新单个任务进度
const refreshTaskProgress = async () => {
  if (!hasRunningTasks.value) return

  for (const task of taskList.value) {
    if (task.status === 'pending' || task.status === 'running') {
      try {
        const updated = await getEvalTask(task.id)
        const index = taskList.value.findIndex((t) => t.id === task.id)
        if (index !== -1) {
          taskList.value[index] = updated
        }
      } catch (error) {
        console.error(`刷新任务 ${task.id} 进度失败:`, error)
      }
    }
  }
}

// 处理新建评测
const handleCreate = () => {
  dialogVisible.value = true
}

// 处理导入数据集
const handleImportDataset = () => {
  importDialogVisible.value = true
}

// 处理导入提交
const handleImportSubmit = async (data: {
  type: 'zip' | 'local'
  file?: File
  path?: string
  config: ImportConfig
}) => {
  try {
    let response
    if (data.type === 'zip' && data.file) {
      response = await importDatasetZip(data.file, data.config)
    } else if (data.type === 'local' && data.path) {
      response = await importDatasetLocal(data.path, data.config)
    } else {
      ElMessage.error('无效的导入参数')
      return
    }

    // 关闭导入对话框，显示进度对话框
    importDialogVisible.value = false
    currentImportId.value = response.import_id
    importCompleted.value = false
    progressDialogVisible.value = true

    ElMessage.success('导入任务已启动')
  } catch (error) {
    console.error('启动导入失败:', error)
    ElMessage.error('启动导入失败')
  }
}

// 处理导入完成
const handleImportCompleted = (result: { parent_task_id: number; connection_count: number; task_count: number }) => {
  importCompleted.value = true
  ElMessage.success(`导入完成！创建了 ${result.connection_count} 个连接和 ${result.task_count} 个子任务`)
  progressDialogVisible.value = false

  // 跳转到父任务详情页
  if (result.parent_task_id) {
    router.push(`/evaluations/parent/${result.parent_task_id}`)
  }

  // 刷新任务列表
  loadTasks()
}

// 处理导入失败
const handleImportFailed = (error: string) => {
  importCompleted.value = true
  ElMessage.error(`导入失败: ${error}`)
  progressDialogVisible.value = false
}

// 处理导入取消
const handleImportCancelled = () => {
  importCompleted.value = true
  ElMessage.info('导入已取消')
  progressDialogVisible.value = false
  loadTasks()
}

// 处理提交表单
const handleSubmit = async (formData: {
  name: string
  connection_id: number
  dataset_type: string
  dataset_file?: File
  api_key_id: number
  temperature: number
  max_tokens?: number
  eval_mode: string
}) => {
  try {
    // 如果有文件上传，需要使用 FormData
    let submitData: FormData | CreateEvalTaskRequest

    if (formData.dataset_file) {
      submitData = new FormData()
      submitData.append('name', formData.name)
      submitData.append('connection_id', String(formData.connection_id))
      submitData.append('dataset_type', formData.dataset_type)
      submitData.append('dataset_file', formData.dataset_file)
      submitData.append('api_key_id', String(formData.api_key_id))
      submitData.append('temperature', String(formData.temperature))
      if (formData.max_tokens) {
        submitData.append('max_tokens', String(formData.max_tokens))
      }
      submitData.append('eval_mode', formData.eval_mode)
    } else {
      submitData = {
        name: formData.name,
        connection_id: formData.connection_id,
        dataset_type: formData.dataset_type as 'bird' | 'spider' | 'custom',
        api_key_id: formData.api_key_id,
        temperature: formData.temperature,
        max_tokens: formData.max_tokens,
        eval_mode: formData.eval_mode as 'greedy_search' | 'major_voting' | 'pass@k',
      }
    }

    await createEvalTask(submitData as CreateEvalTaskRequest)
    ElMessage.success('评测任务创建成功')
    dialogVisible.value = false
    loadTasks()
  } catch (error) {
    console.error('创建评测任务失败:', error)
    ElMessage.error('创建评测任务失败')
  }
}

// 处理查看详情
const handleViewDetail = (row: EvalTask) => {
  router.push(`/evaluations/${row.id}`)
}

// 处理取消任务
const handleCancel = async (row: EvalTask) => {
  try {
    await ElMessageBox.confirm('确定要取消该评测任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await cancelEvalTask(row.id)
    ElMessage.success('任务已取消')
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error('取消任务失败')
    }
  }
}

// 处理删除
const handleDelete = async (row: EvalTask) => {
  try {
    await ElMessageBox.confirm('确定删除该评测任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteEvalTask(row.id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadTasks()
}

// 处理每页条数变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadTasks()
}

// 处理状态筛选
const handleStatusFilterChange = () => {
  currentPage.value = 1
  loadTasks()
}

// 获取状态标签类型
const getStatusType = (status: TaskStatus): string => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: TaskStatus): string => {
  const textMap: Record<string, string> = {
    pending: '待执行',
    running: '进行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return textMap[status] || '未知'
}

// 获取状态图标
const getStatusIcon = (status: TaskStatus): string => {
  const iconMap: Record<string, string> = {
    pending: 'Timer',
    running: 'Loading',
    completed: 'CircleCheck',
    failed: 'CircleClose',
    cancelled: 'Remove',
  }
  return iconMap[status] || 'QuestionFilled'
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 组件挂载时加载数据
onMounted(() => {
  loadTasks()
  loadConnections()

  // 设置定时刷新（每3秒刷新一次进行中任务的进度）
  refreshTimer = setInterval(() => {
    if (hasRunningTasks.value) {
      refreshTaskProgress()
    }
  }, 3000)
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<template>
  <div class="evaluations-page">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>评测管理</span>
          <div class="header-actions">
            <el-select
              v-model="statusFilter"
              placeholder="筛选状态"
              clearable
              style="width: 120px"
              @change="handleStatusFilterChange"
            >
              <el-option label="待执行" value="pending" />
              <el-option label="进行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
            <el-button type="success" @click="handleImportDataset">
              <el-icon class="el-icon--left"><Upload /></el-icon>
              导入数据集
            </el-button>
            <el-button type="primary" @click="handleCreate">
              <el-icon class="el-icon--left"><Plus /></el-icon>
              新建评测
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="taskList" style="width: 100%" border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="name" label="评测名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="dataset_type" label="数据集" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.dataset_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="eval_mode" label="模式" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info" effect="plain">
              {{ row.eval_mode === 'greedy_search' ? '单模型' : '集成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              <el-icon class="tag-icon">
                <component :is="getStatusIcon(row.status)" />
              </el-icon>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="180" align="center">
          <template #default="{ row }">
            <div class="progress-wrapper">
              <el-progress
                :percentage="row.progress?.percentage || 0"
                :status="
                  row.status === 'completed'
                    ? 'success'
                    : row.status === 'failed'
                      ? 'exception'
                      : ''
                "
                :stroke-width="8"
              />
              <span v-if="row.progress" class="progress-text">
                {{ row.progress.processed }}/{{ row.progress.total }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="准确率" width="100" align="center">
          <template #default="{ row }">
            <span
              v-if="row.status === 'completed' && row.progress"
              :class="{
                'high-accuracy': (row.progress.correct / row.progress.processed) >= 0.8,
                'medium-accuracy': (row.progress.correct / row.progress.processed) >= 0.6 && (row.progress.correct / row.progress.processed) < 0.8,
                'low-accuracy': (row.progress.correct / row.progress.processed) < 0.6,
              }"
            >
              {{ ((row.progress.correct / row.progress.processed) * 100).toFixed(1) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'running' || row.status === 'pending'"
              type="warning"
              link
              size="small"
              @click="handleCancel(row)"
            >
              <el-icon><VideoPause /></el-icon>
              取消
            </el-button>
            <el-button
              v-if="row.status !== 'running' && row.status !== 'pending'"
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>

      <!-- 空状态 -->
      <el-empty v-if="taskList.length === 0 && !loading" description="暂无评测任务" />
    </el-card>

    <!-- 新建评测对话框 -->
    <EvalTaskFormDialog
      v-model:visible="dialogVisible"
      :connections="connections"
      @submit="handleSubmit"
    />

    <!-- 导入数据集对话框 -->
    <ImportDialog
      v-model:visible="importDialogVisible"
      @submit="handleImportSubmit"
    />

    <!-- 导入进度对话框 -->
    <ProgressDialog
      v-model:visible="progressDialogVisible"
      :import-id="currentImportId"
      @completed="handleImportCompleted"
      @failed="handleImportFailed"
      @cancelled="handleImportCancelled"
    />
  </div>
</template>

<style scoped lang="scss">
.evaluations-page {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  span {
    font-weight: bold;
    font-size: 16px;
  }
}

.header-actions {
  display: flex;
  gap: 10px;
}

.tag-icon {
  margin-right: 4px;
  font-size: 12px;
}

.progress-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  :deep(.el-progress) {
    width: 100%;
  }
}

.progress-text {
  font-size: 12px;
  color: #909399;
}

.high-accuracy {
  color: #67c23a;
  font-weight: bold;
}

.medium-accuracy {
  color: #e6a23c;
  font-weight: bold;
}

.low-accuracy {
  color: #f56c6c;
  font-weight: bold;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
