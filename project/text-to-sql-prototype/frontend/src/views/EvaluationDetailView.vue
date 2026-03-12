<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEvalTask,
  getEvalResults,
  getEvalStats,
  cancelEvalTask,
  deleteEvalTask,
} from '@/api/evaluations'
import type { EvalTaskDetail, EvalResult, EvalStats } from '@/types'

const route = useRoute()
const router = useRouter()

// 任务ID
const taskId = computed(() => Number(route.params.id))

// 任务详情
const taskDetail = ref<EvalTaskDetail | null>(null)
const loading = ref(false)

// 评测结果
const results = ref<EvalResult[]>([])
const resultsLoading = ref(false)

// 统计数据
const stats = ref<EvalStats | null>(null)
const statsLoading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选
const filterType = ref<'all' | 'correct' | 'incorrect'>('all')
const errorTypeFilter = ref<string>('')

// 定时刷新器
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 是否进行中
const isRunning = computed(() => {
  return taskDetail.value?.status === 'running' || taskDetail.value?.status === 'pending'
})

// 准确率
const accuracy = computed(() => {
  if (stats.value) {
    return (stats.value.accuracy * 100).toFixed(2)
  }
  if (taskDetail.value?.progress) {
    const { correct, processed } = taskDetail.value.progress
    if (processed > 0) {
      return ((correct / processed) * 100).toFixed(2)
    }
  }
  return '0.00'
})

// 加载任务详情
const loadTaskDetail = async () => {
  try {
    const res = await getEvalTask(taskId.value)
    taskDetail.value = res
  } catch (error) {
    console.error('加载任务详情失败:', error)
    ElMessage.error('加载任务详情失败')
  }
}

// 加载评测结果
const loadResults = async () => {
  resultsLoading.value = true
  try {
    const params: {
      page: number
      page_size: number
      is_correct?: boolean
      error_type?: string
    } = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    if (filterType.value === 'correct') {
      params.is_correct = true
    } else if (filterType.value === 'incorrect') {
      params.is_correct = false
    }

    if (errorTypeFilter.value) {
      params.error_type = errorTypeFilter.value
    }

    const res = await getEvalResults(taskId.value, params)
    results.value = res.list
    total.value = res.pagination.total
  } catch (error) {
    console.error('加载评测结果失败:', error)
    ElMessage.error('加载评测结果失败')
  } finally {
    resultsLoading.value = false
  }
}

// 加载统计数据
const loadStats = async () => {
  statsLoading.value = true
  try {
    const res = await getEvalStats(taskId.value)
    stats.value = res
  } catch (error) {
    console.error('加载统计数据失败:', error)
  } finally {
    statsLoading.value = false
  }
}

// 刷新所有数据
const refreshAll = async () => {
  loading.value = true
  await Promise.all([loadTaskDetail(), loadResults(), loadStats()])
  loading.value = false
}

// 处理返回
const handleBack = () => {
  router.push('/evaluations')
}

// 处理取消任务
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消该评测任务吗？', '提示', {
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

// 处理删除任务
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定删除该评测任务吗？删除后无法恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
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

// 处理导出结果
const handleExport = () => {
  // TODO: 实现导出功能
  ElMessage.info('导出功能开发中...')
}

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadResults()
}

// 处理每页条数变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadResults()
}

// 处理筛选变化
const handleFilterChange = () => {
  currentPage.value = 1
  loadResults()
}

// 获取状态标签类型
const getStatusType = (status: string): string => {
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
const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    pending: '待执行',
    running: '进行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return textMap[status] || '未知'
}

// 获取错误类型文本
const getErrorTypeText = (type?: string): string => {
  const textMap: Record<string, string> = {
    syntax: '语法错误',
    execution: '执行错误',
    logic: '逻辑错误',
    timeout: '超时',
    generation: '生成错误',
  }
  return type ? textMap[type] || type : '-'
}

// 格式化日期
const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 计算持续时间
const getDuration = (): string => {
  if (!taskDetail.value?.started_at) return '-'
  const start = new Date(taskDetail.value.started_at)
  const end = taskDetail.value.completed_at
    ? new Date(taskDetail.value.completed_at)
    : new Date()
  const diff = Math.floor((end.getTime() - start.getTime()) / 1000)
  const minutes = Math.floor(diff / 60)
  const seconds = diff % 60
  return `${minutes}分${seconds}秒`
}

// 组件挂载时加载数据
onMounted(() => {
  refreshAll()

  // 设置定时刷新（每3秒刷新一次）
  refreshTimer = setInterval(() => {
    if (isRunning.value) {
      loadTaskDetail()
      loadStats()
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
  <div class="evaluation-detail-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <h2 class="page-title">{{ taskDetail?.name || '评测详情' }}</h2>
        <el-tag v-if="taskDetail" :type="getStatusType(taskDetail.status)" size="small">
          {{ getStatusText(taskDetail.status) }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button v-if="isRunning" type="warning" @click="handleCancel">
          <el-icon><VideoPause /></el-icon>
          取消任务
        </el-button>
        <el-button type="primary" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出结果
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 基本信息卡片 -->
    <el-card class="info-card" v-loading="loading">
      <el-descriptions :column="4" border>
        <el-descriptions-item label="数据集类型">
          <el-tag size="small" effect="plain">
            {{ taskDetail?.dataset_type?.toUpperCase() || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="评测模式">
          {{ taskDetail?.eval_mode === 'greedy_search' ? '单模型' : '集成' }}
        </el-descriptions-item>
        <el-descriptions-item label="模型">
          {{ taskDetail?.model_config?.model || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(taskDetail?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="总样本数">
          {{ taskDetail?.progress?.total || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="已处理">
          {{ taskDetail?.progress?.processed || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="正确数">
          {{ taskDetail?.progress?.correct || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="运行时长">
          {{ getDuration() }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card" v-loading="statsLoading">
          <div class="stat-value" :class="{
            'high-accuracy': Number(accuracy) >= 80,
            'medium-accuracy': Number(accuracy) >= 60 && Number(accuracy) < 80,
            'low-accuracy': Number(accuracy) < 60,
          }">
            {{ accuracy }}%
          </div>
          <div class="stat-label">准确率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" v-loading="statsLoading">
          <div class="stat-value success">{{ stats?.correct || 0 }}</div>
          <div class="stat-label">正确数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" v-loading="statsLoading">
          <div class="stat-value error">{{ stats?.incorrect || 0 }}</div>
          <div class="stat-label">错误数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" v-loading="statsLoading">
          <div class="stat-value warning">{{ stats?.failed || 0 }}</div>
          <div class="stat-label">失败数</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 难度分布 -->
    <el-card v-if="stats?.by_difficulty" class="difficulty-card" v-loading="statsLoading">
      <template #header>
        <span>难度分布</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="difficulty-item">
            <div class="difficulty-name">简单</div>
            <el-progress
              :percentage="Math.round(stats.by_difficulty.easy.accuracy * 100)"
              :format="() => `${stats!.by_difficulty.easy.correct}/${stats!.by_difficulty.easy.total}`"
              status="success"
            />
          </div>
        </el-col>
        <el-col :span="8">
          <div class="difficulty-item">
            <div class="difficulty-name">中等</div>
            <el-progress
              :percentage="Math.round(stats.by_difficulty.medium.accuracy * 100)"
              :format="() => `${stats!.by_difficulty.medium.correct}/${stats!.by_difficulty.medium.total}`"
            />
          </div>
        </el-col>
        <el-col :span="8">
          <div class="difficulty-item">
            <div class="difficulty-name">困难</div>
            <el-progress
              :percentage="Math.round(stats.by_difficulty.hard.accuracy * 100)"
              :format="() => `${stats!.by_difficulty.hard.correct}/${stats!.by_difficulty.hard.total}`"
              status="exception"
            />
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 结果表格 -->
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <span>评测结果</span>
          <div class="filter-actions">
            <el-radio-group v-model="filterType" size="small" @change="handleFilterChange">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="correct">正确</el-radio-button>
              <el-radio-button label="incorrect">错误</el-radio-button>
            </el-radio-group>
            <el-select
              v-if="filterType === 'incorrect'"
              v-model="errorTypeFilter"
              placeholder="错误类型"
              clearable
              size="small"
              style="width: 120px"
              @change="handleFilterChange"
            >
              <el-option label="语法错误" value="syntax" />
              <el-option label="执行错误" value="execution" />
              <el-option label="逻辑错误" value="logic" />
              <el-option label="超时" value="timeout" />
              <el-option label="生成错误" value="generation" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="results" v-loading="resultsLoading" border stripe>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="gold_sql" label="标准SQL" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="sql-code">{{ row.gold_sql }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="predicted_sql" label="预测SQL" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="sql-code">{{ row.predicted_sql }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="is_correct" label="结果" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_correct ? 'success' : 'danger'" size="small">
              {{ row.is_correct ? '正确' : '错误' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error_type" label="错误类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.error_type" type="warning" size="small">
              {{ getErrorTypeText(row.error_type) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="execution_time_ms" label="执行时间" width="100" align="center">
          <template #default="{ row }">
            {{ row.execution_time_ms ? `${row.execution_time_ms}ms` : '-' }}
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
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.evaluation-detail-page {
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

.info-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;

  :deep(.el-card__body) {
    padding: 20px;
  }

  .stat-value {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 8px;

    &.high-accuracy {
      color: #67c23a;
    }

    &.medium-accuracy {
      color: #e6a23c;
    }

    &.low-accuracy {
      color: #f56c6c;
    }

    &.success {
      color: #67c23a;
    }

    &.error {
      color: #f56c6c;
    }

    &.warning {
      color: #e6a23c;
    }
  }

  .stat-label {
    color: #909399;
    font-size: 14px;
  }
}

.difficulty-card {
  margin-bottom: 20px;

  .difficulty-item {
    .difficulty-name {
      font-weight: 500;
      margin-bottom: 10px;
    }
  }
}

.results-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    span {
      font-weight: bold;
      font-size: 16px;
    }
  }

  .filter-actions {
    display: flex;
    gap: 10px;
  }
}

.sql-code {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #606266;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
