<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { EvalTask, TaskType, TaskStatus } from '@/types'
import {
  getEvalTasks,
  getEvalTask,
  cancelEvalTask,
  deleteEvalTask,
  startAllChildren,
  retryFailedChildren,
  type EvalTaskParams,
} from '@/api/evaluations'

// ==================== 类型定义 ====================

interface ExpandedTask {
  [key: number]: boolean
}

// ==================== Props & Emits ====================

const props = defineProps<{
  initialTaskType?: TaskType | ''
  showParentActions?: boolean
}>()

const emit = defineEmits<{
  (e: 'view-detail', task: EvalTask): void
  (e: 'view-parent', parentId: number): void
}>()

// ==================== 状态 ====================

const taskList = ref<EvalTask[]>([])
const loading = ref(false)
const expandedRows = ref<ExpandedTask>({})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 筛选
const statusFilter = ref<TaskStatus | ''>('')
const taskTypeFilter = ref<TaskType | ''>(props.initialTaskType || '')

// 定时刷新器
let refreshTimer: ReturnType<typeof setInterval> | null = null

// ==================== 计算属性 ====================

const hasRunningTasks = computed(() => {
  return taskList.value.some(
    (task) => task.status === 'pending' || task.status === 'running'
  )
})

// 获取父任务的进度百分比
const getParentProgress = (task: EvalTask): number => {
  if (!task.child_count || task.child_count === 0) return 0
  return Math.round(((task.completed_children || 0) / task.child_count) * 100)
}

// ==================== 方法 ====================

// 加载任务列表
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
    if (taskTypeFilter.value) {
      params.task_type = taskTypeFilter.value
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

// 处理展开/折叠
const handleExpandChange = (row: EvalTask, expandedRows: EvalTask[]) => {
  expandedRows.value[row.id] = expandedRows.length > 0
}

// 处理查看详情
const handleViewDetail = (row: EvalTask) => {
  emit('view-detail', row)
}

// 处理查看父任务
const handleViewParent = (parentId: number) => {
  emit('view-parent', parentId)
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

// 处理批量启动子任务
const handleStartAll = async (row: EvalTask) => {
  try {
    await ElMessageBox.confirm(
      `确定要启动父任务 "${row.name}" 下的所有子任务吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    const res = await startAllChildren(row.id)
    ElMessage.success(`成功启动 ${res.success} 个子任务`)
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('启动子任务失败:', error)
      ElMessage.error('启动子任务失败')
    }
  }
}

// 处理重试失败任务
const handleRetryFailed = async (row: EvalTask) => {
  try {
    const res = await retryFailedChildren(row.id)
    if (res.success > 0) {
      ElMessage.success(`成功重试 ${res.success} 个失败任务`)
    } else {
      ElMessage.info('没有需要重试的失败任务')
    }
    loadTasks()
  } catch (error) {
    console.error('重试失败任务失败:', error)
    ElMessage.error('重试失败任务失败')
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

// 处理任务类型筛选
const handleTaskTypeFilterChange = () => {
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

// 获取任务类型标签
const getTaskTypeLabel = (taskType?: TaskType): string => {
  const labelMap: Record<string, string> = {
    single: '单任务',
    parent: '父任务',
    child: '子任务',
  }
  return labelMap[taskType || 'single'] || '单任务'
}

// 获取任务类型标签样式
const getTaskTypeType = (taskType?: TaskType): string => {
  const typeMap: Record<string, string> = {
    single: 'info',
    parent: 'success',
    child: 'warning',
  }
  return typeMap[taskType || 'single'] || 'info'
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadTasks()

  // 设置定时刷新（每3秒刷新一次进行中任务的进度）
  refreshTimer = setInterval(() => {
    if (hasRunningTasks.value) {
      refreshTaskProgress()
    }
  }, 3000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})

// 暴露方法给父组件
defineExpose({
  refresh: loadTasks,
})
</script>

<template>
  <div class="task-list-component">
    <!-- 筛选栏 -->
    <div class="filter-bar">
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
      <el-select
        v-model="taskTypeFilter"
        placeholder="任务类型"
        clearable
        style="width: 120px"
        @change="handleTaskTypeFilterChange"
      >
        <el-option label="单任务" value="single" />
        <el-option label="父任务" value="parent" />
        <el-option label="子任务" value="child" />
      </el-select>
    </div>

    <!-- 任务列表表格 -->
    <el-table
      :data="taskList"
      style="width: 100%"
      border
      v-loading="loading"
      row-key="id"
      :expand-row-keys="Object.keys(expandedRows).filter(k => expandedRows[Number(k)])"
      @expand-change="handleExpandChange"
    >
      <!-- 展开列（仅父任务） -->
      <el-table-column type="expand" width="50">
        <template #default="{ row }">
          <div v-if="row.task_type === 'parent'" class="parent-task-detail">
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item label="子任务数量">
                {{ row.child_count || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="已完成">
                {{ row.completed_children || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="整体进度">
                <el-progress
                  :percentage="getParentProgress(row)"
                  :status="row.status === 'completed' ? 'success' : ''"
                  :stroke-width="8"
                  style="width: 150px"
                />
              </el-descriptions-item>
            </el-descriptions>
            <!-- 父任务操作按钮 -->
            <div v-if="showParentActions && row.task_type === 'parent'" class="parent-actions">
              <el-button
                type="primary"
                size="small"
                :disabled="row.status === 'running' || row.status === 'pending'"
                @click="handleStartAll(row)"
              >
                <el-icon><VideoPlay /></el-icon>
                全部开始
              </el-button>
              <el-button
                type="warning"
                size="small"
                :disabled="row.status === 'running' || row.status === 'pending'"
                @click="handleRetryFailed(row)"
              >
                <el-icon><RefreshRight /></el-icon>
                重试失败
              </el-button>
            </div>
          </div>
          <div v-else-if="row.task_type === 'child'" class="child-task-detail">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="父任务">
                <el-button
                  v-if="row.parent_id"
                  type="primary"
                  link
                  size="small"
                  @click="handleViewParent(row.parent_id!)"
                >
                  查看父任务 #{{ row.parent_id }}
                </el-button>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="数据库ID">
                {{ row.db_id || '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </el-table-column>

      <el-table-column type="index" label="#" width="60" align="center" />

      <el-table-column prop="name" label="评测名称" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="task-name-cell">
            <span>{{ row.name }}</span>
            <el-tag
              size="small"
              :type="getTaskTypeType(row.task_type)"
              effect="plain"
              class="task-type-tag"
            >
              {{ getTaskTypeLabel(row.task_type) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="dataset_type" label="数据集" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ row.dataset_type.toUpperCase() }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="eval_mode" label="模式" width="100" align="center">
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
            v-if="row.status === 'completed' && row.progress?.processed > 0"
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
  </div>
</template>

<style scoped lang="scss">
.task-list-component {
  .filter-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
  }

  .task-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .task-type-tag {
      flex-shrink: 0;
    }
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

  .parent-task-detail {
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 4px;

    .parent-actions {
      margin-top: 12px;
      display: flex;
      gap: 8px;
    }
  }

  .child-task-detail {
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 4px;
  }
}
</style>
