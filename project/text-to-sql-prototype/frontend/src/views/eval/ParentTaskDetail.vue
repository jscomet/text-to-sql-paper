<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { EvalTaskWithChildren, EvalTaskChild, TaskStatus } from '@/types'
import {
  getParentTaskDetail,
  startAllChildren,
  retryFailedChildren,
  cancelEvalTask,
  deleteEvalTask,
  getEvalTask,
} from '@/api/evaluations'

const route = useRoute()
const router = useRouter()

// ==================== 状态 ====================

const taskId = computed(() => Number(route.params.id))
const taskDetail = ref<EvalTaskWithChildren | null>(null)
const loading = ref(false)

// 子任务筛选
const statusFilter = ref<TaskStatus | ''>('')

// 定时刷新器
let refreshTimer: ReturnType<typeof setInterval> | null = null

// ==================== 计算属性 ====================

const isRunning = computed(() => {
  return taskDetail.value?.status === 'running' || taskDetail.value?.status === 'pending'
})

// 筛选后的子任务
const filteredChildren = computed(() => {
  if (!taskDetail.value?.children) return []
  if (!statusFilter.value) return taskDetail.value.children
  return taskDetail.value.children.filter(child => child.status === statusFilter.value)
})

// 子任务统计
const childrenStats = computed(() => {
  const children = taskDetail.value?.children || []
  return {
    total: children.length,
    pending: children.filter(c => c.status === 'pending').length,
    running: children.filter(c => c.status === 'running').length,
    completed: children.filter(c => c.status === 'completed').length,
    failed: children.filter(c => c.status === 'failed').length,
    cancelled: children.filter(c => c.status === 'cancelled').length,
  }
})

// 整体进度
const overallProgress = computed(() => {
  if (!taskDetail.value?.total_questions) return 0
  const completed = childrenStats.value.completed
  const failed = childrenStats.value.failed
  const cancelled = childrenStats.value.cancelled
  return Math.round(((completed + failed + cancelled) / childrenStats.value.total) * 100)
})

// ==================== 方法 ====================

// 加载父任务详情
const loadTaskDetail = async () => {
  loading.value = true
  try {
    const res = await getParentTaskDetail(taskId.value)
    taskDetail.value = res
  } catch (error) {
    console.error('加载父任务详情失败:', error)
    ElMessage.error('加载父任务详情失败')
  } finally {
    loading.value = false
  }
}

// 刷新任务进度
const refreshProgress = async () => {
  if (!taskDetail.value) return
  try {
    const updated = await getEvalTask(taskId.value)
    taskDetail.value = { ...taskDetail.value, ...updated }
  } catch (error) {
    console.error('刷新进度失败:', error)
  }
}

// 处理返回
const handleBack = () => {
  router.push('/evaluations')
}

// 处理查看子任务详情
const handleViewChild = (child: EvalTaskChild) => {
  router.push(`/evaluations/${child.id}`)
}

// 处理全部开始
const handleStartAll = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要启动所有待执行的子任务吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    const res = await startAllChildren(taskId.value)
    ElMessage.success(`成功启动 ${res.success} 个子任务`)
    loadTaskDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('启动子任务失败:', error)
      ElMessage.error('启动子任务失败')
    }
  }
}

// 处理重试失败
const handleRetryFailed = async () => {
  try {
    const res = await retryFailedChildren(taskId.value)
    if (res.success > 0) {
      ElMessage.success(`成功重试 ${res.success} 个失败任务`)
    } else {
      ElMessage.info('没有需要重试的失败任务')
    }
    loadTaskDetail()
  } catch (error) {
    console.error('重试失败任务失败:', error)
    ElMessage.error('重试失败任务失败')
  }
}

// 处理取消父任务
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消该父任务吗？所有进行中的子任务也会被取消。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await cancelEvalTask(taskId.value)
    ElMessage.success('任务已取消')
    loadTaskDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error('取消任务失败')
    }
  }
}

// 处理删除父任务
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      '确定删除该父任务吗？所有子任务和相关数据也会被删除，此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'danger',
      }
    )
    await deleteEvalTask(taskId.value)
    ElMessage.success('删除成功')
    router.push('/evaluations')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理取消子任务
const handleCancelChild = async (child: EvalTaskChild) => {
  try {
    await ElMessageBox.confirm(`确定要取消子任务 "${child.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await cancelEvalTask(child.id)
    ElMessage.success('子任务已取消')
    loadTaskDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消子任务失败:', error)
      ElMessage.error('取消子任务失败')
    }
  }
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

// 格式化日期
const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 计算持续时间
const getDuration = (child: EvalTaskChild): string => {
  if (!child.started_at) return '-'
  const start = new Date(child.started_at)
  const end = child.completed_at ? new Date(child.completed_at) : new Date()
  const diff = Math.floor((end.getTime() - start.getTime()) / 1000)
  const minutes = Math.floor(diff / 60)
  const seconds = diff % 60
  return `${minutes}分${seconds}秒`
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadTaskDetail()

  // 设置定时刷新
  refreshTimer = setInterval(() => {
    if (isRunning.value) {
      refreshProgress()
    }
  }, 3000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<template>
  <div class="parent-task-detail-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <h2 class="page-title">{{ taskDetail?.name || '父任务详情' }}</h2>
        <el-tag v-if="taskDetail" :type="getStatusType(taskDetail.status)" size="small">
          {{ getStatusText(taskDetail.status) }}
        </el-tag>
        <el-tag type="success" size="small" effect="plain">父任务</el-tag>
      </div>
      <div class="header-actions">
        <el-button
          v-if="!isRunning && childrenStats.pending > 0"
          type="primary"
          @click="handleStartAll"
        >
          <el-icon><VideoPlay /></el-icon>
          全部开始
        </el-button>
        <el-button
          v-if="!isRunning && childrenStats.failed > 0"
          type="warning"
          @click="handleRetryFailed"
        >
          <el-icon><RefreshRight /></el-icon>
          重试失败
        </el-button>
        <el-button v-if="isRunning" type="warning" @click="handleCancel">
          <el-icon><VideoPause /></el-icon>
          取消任务
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-value">{{ childrenStats.total }}</div>
          <div class="stat-label">子任务总数</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-value info">{{ childrenStats.pending }}</div>
          <div class="stat-label">待执行</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-value warning">{{ childrenStats.running }}</div>
          <div class="stat-label">进行中</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-value success">{{ childrenStats.completed }}</div>
          <div class="stat-label">已完成</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-value error">{{ childrenStats.failed }}</div>
          <div class="stat-label">失败</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card" v-loading="loading">
          <div
            class="stat-value"
            :class="{
              'high-accuracy': (taskDetail?.overall_accuracy || 0) >= 80,
              'medium-accuracy': (taskDetail?.overall_accuracy || 0) >= 60 && (taskDetail?.overall_accuracy || 0) < 80,
              'low-accuracy': (taskDetail?.overall_accuracy || 0) < 60,
            }"
          >
            {{ ((taskDetail?.overall_accuracy || 0) * 100).toFixed(1) }}%
          </div>
          <div class="stat-label">整体准确率</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 整体进度 -->
    <el-card class="progress-card" v-loading="loading">
      <template #header>
        <span>整体进度</span>
      </template>
      <div class="overall-progress">
        <el-progress
          :percentage="overallProgress"
          :status="taskDetail?.status === 'completed' ? 'success' : ''"
          :stroke-width="16"
          striped
          :striped-flow="isRunning"
        />
        <div class="progress-detail">
          <span>已完成: {{ childrenStats.completed + childrenStats.failed + childrenStats.cancelled }} / {{ childrenStats.total }}</span>
          <span>总问题数: {{ taskDetail?.total_questions || 0 }}</span>
        </div>
      </div>
    </el-card>

    <!-- 子任务列表 -->
    <el-card class="children-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>子任务列表</span>
          <div class="header-actions">
            <el-select
              v-model="statusFilter"
              placeholder="筛选状态"
              clearable
              size="small"
              style="width: 120px"
            >
              <el-option label="待执行" value="pending" />
              <el-option label="进行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="filteredChildren" border stripe>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="name" label="任务名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="db_id" label="数据库ID" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.db_id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="150" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress?.percentage || 0"
              :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : ''"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="准确率" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.status === 'completed' && row.progress?.processed > 0">
              {{ ((row.progress.correct / row.progress.processed) * 100).toFixed(0) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="150" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ getDuration(row) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewChild(row)">
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'running' || row.status === 'pending'"
              type="warning"
              link
              size="small"
              @click="handleCancelChild(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="filteredChildren.length === 0 && !loading" description="暂无子任务" />
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.parent-task-detail-page {
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 15px;

    .page-title {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }

  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;

  :deep(.el-card__body) {
    padding: 16px;
  }

  .stat-value {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 6px;

    &.info {
      color: #909399;
    }

    &.warning {
      color: #e6a23c;
    }

    &.success {
      color: #67c23a;
    }

    &.error {
      color: #f56c6c;
    }

    &.high-accuracy {
      color: #67c23a;
    }

    &.medium-accuracy {
      color: #e6a23c;
    }

    &.low-accuracy {
      color: #f56c6c;
    }
  }

  .stat-label {
    color: #909399;
    font-size: 13px;
  }
}

.progress-card {
  margin-bottom: 20px;

  .overall-progress {
    .progress-detail {
      margin-top: 12px;
      display: flex;
      justify-content: space-between;
      color: #606266;
      font-size: 14px;
    }
  }
}

.children-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    span {
      font-weight: bold;
      font-size: 16px;
    }
  }
}
</style>
