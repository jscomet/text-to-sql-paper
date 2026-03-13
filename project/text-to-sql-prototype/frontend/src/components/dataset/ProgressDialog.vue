<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { ImportProgress, ImportStatus } from '@/types'
import { getImportStatus, cancelImport } from '@/api/dataset'

interface Props {
  visible: boolean
  importId: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'completed', result: { parent_task_id: number; connection_count: number; task_count: number }): void
  (e: 'failed', error: string): void
  (e: 'cancelled'): void
}>()

// ==================== 状态 ====================

const loading = ref(false)
const progress = ref<ImportProgress | null>(null)
const logContainerRef = ref<HTMLDivElement | null>(null)

// 轮询定时器
let pollTimer: ReturnType<typeof setInterval> | null = null

// ==================== 计算属性 ====================

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

const isCompleted = computed(() => {
  return progress.value?.status === 'completed'
})

const isFailed = computed(() => {
  return progress.value?.status === 'failed'
})

const isCancelled = computed(() => {
  return progress.value?.status === 'cancelled'
})

const isRunning = computed(() => {
  return !isCompleted.value && !isFailed.value && !isCancelled.value
})

const canCancel = computed(() => {
  return isRunning.value && progress.value?.status !== 'cancelled'
})

// 步骤列表
const steps = computed(() => {
  const status = progress.value?.status
  const step = progress.value?.step || 0

  return [
    {
      title: '验证',
      description: '验证数据集格式',
      status: getStepStatus('validating', status, step, 1),
      icon: getStepIcon('validating', status, step, 1),
    },
    {
      title: '解析',
      description: '解析数据集内容',
      status: getStepStatus('parsing', status, step, 2),
      icon: getStepIcon('parsing', status, step, 2),
    },
    {
      title: '创建连接',
      description: '创建数据库连接',
      status: getStepStatus('creating_connections', status, step, 3),
      icon: getStepIcon('creating_connections', status, step, 3),
    },
    {
      title: '创建任务',
      description: '创建评测任务',
      status: getStepStatus('creating_tasks', status, step, 4),
      icon: getStepIcon('creating_tasks', status, step, 4),
    },
  ]
})

// 获取步骤状态
function getStepStatus(
  stepStatus: ImportStatus,
  currentStatus: ImportStatus | undefined,
  currentStep: number,
  stepNumber: number
): 'wait' | 'process' | 'finish' | 'error' {
  if (!currentStatus) return 'wait'

  // 如果整体失败
  if (currentStatus === 'failed') {
    return currentStep === stepNumber ? 'error' : currentStep > stepNumber ? 'finish' : 'wait'
  }

  // 如果整体完成
  if (currentStatus === 'completed') {
    return 'finish'
  }

  // 如果整体取消
  if (currentStatus === 'cancelled') {
    return currentStep > stepNumber ? 'finish' : 'wait'
  }

  // 当前步骤
  if (currentStatus === stepStatus) {
    return 'process'
  }

  // 已完成的步骤
  if (currentStep > stepNumber) {
    return 'finish'
  }

  return 'wait'
}

// 获取步骤图标
function getStepIcon(
  stepStatus: ImportStatus,
  currentStatus: ImportStatus | undefined,
  currentStep: number,
  stepNumber: number
): string {
  const status = getStepStatus(stepStatus, currentStatus, currentStep, stepNumber)
  const iconMap: Record<string, string> = {
    wait: 'CircleCheck',
    process: 'Loading',
    finish: 'CircleCheck',
    error: 'CircleClose',
  }
  return iconMap[status]
}

// ==================== 方法 ====================

// 获取导入状态
const fetchStatus = async () => {
  if (!props.importId) return

  try {
    const data = await getImportStatus(props.importId)
    progress.value = data

    // 自动滚动日志
    scrollToBottom()

    // 处理完成状态
    if (data.status === 'completed') {
      stopPolling()
      if (data.result) {
        emit('completed', data.result)
      }
    } else if (data.status === 'failed') {
      stopPolling()
      emit('failed', data.message || '导入失败')
    } else if (data.status === 'cancelled') {
      stopPolling()
      emit('cancelled')
    }
  } catch (error) {
    console.error('获取导入状态失败:', error)
  }
}

// 处理取消
const handleCancel = async () => {
  if (!props.importId) return

  try {
    loading.value = true
    await cancelImport(props.importId)
    ElMessage.success('已取消导入')
    stopPolling()
    emit('cancelled')
  } catch (error) {
    console.error('取消导入失败:', error)
    ElMessage.error('取消导入失败')
  } finally {
    loading.value = false
  }
}

// 处理关闭
const handleClose = () => {
  if (isRunning.value) {
    ElMessage.warning('导入正在进行中，请先取消')
    return
  }
  dialogVisible.value = false
}

// 开始轮询
const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(fetchStatus, 1000)
}

// 停止轮询
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 滚动日志到底部
const scrollToBottom = () => {
  if (logContainerRef.value) {
    setTimeout(() => {
      logContainerRef.value!.scrollTop = logContainerRef.value!.scrollHeight
    }, 0)
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  if (props.importId) {
    fetchStatus()
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="导入进度"
    width="700px"
    :close-on-click-modal="false"
    :show-close="!isRunning"
    :before-close="handleClose"
    destroy-on-close
  >
    <div v-if="progress" class="progress-content">
      <!-- 步骤指示器 -->
      <el-steps :active="progress.step" finish-status="success" class="import-steps">
        <el-step
          v-for="(step, index) in steps"
          :key="index"
          :title="step.title"
          :description="step.description"
          :status="step.status"
        >
          <template #icon>
            <el-icon v-if="step.status === 'process'" class="is-loading">
              <component :is="step.icon" />
            </el-icon>
            <el-icon v-else :class="{ 'text-success': step.status === 'finish', 'text-error': step.status === 'error' }">
              <component :is="step.icon" />
            </el-icon>
          </template>
        </el-step>
      </el-steps>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-header">
          <span class="progress-status">{{ progress.message }}</span>
          <span class="progress-percentage">{{ progress.progress_percentage }}%</span>
        </div>
        <el-progress
          :percentage="progress.progress_percentage"
          :status="isFailed ? 'exception' : isCompleted ? 'success' : ''"
          :stroke-width="12"
          striped
          :striped-flow="isRunning"
        />
      </div>

      <!-- 结果信息 -->
      <div v-if="progress.result" class="result-section">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="父任务ID">
            <el-tag type="primary" size="small">#{{ progress.result.parent_task_id }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据库连接">
            {{ progress.result.connection_count }} 个
          </el-descriptions-item>
          <el-descriptions-item label="子任务">
            {{ progress.result.task_count }} 个
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 日志输出 -->
      <div class="log-section">
        <div class="log-header">
          <span class="log-title">导入日志</span>
          <el-tag v-if="progress.logs.length > 0" type="info" size="small">
            {{ progress.logs.length }} 条
          </el-tag>
        </div>
        <div ref="logContainerRef" class="log-container">
          <div
            v-for="(log, index) in progress.logs"
            :key="index"
            class="log-line"
          >
            <span class="log-index">[{{ index + 1 }}]</span>
            <span class="log-content">{{ log }}</span>
          </div>
          <div v-if="progress.logs.length === 0" class="log-empty">
            等待开始...
          </div>
        </div>
      </div>
    </div>

    <div v-else class="loading-content">
      <el-skeleton :rows="6" animated />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button v-if="canCancel" type="danger" :loading="loading" @click="handleCancel">
          <el-icon><CircleClose /></el-icon>
          取消导入
        </el-button>
        <el-button v-else @click="dialogVisible = false">
          {{ isCompleted ? '完成' : '关闭' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.progress-content {
  .import-steps {
    margin-bottom: 24px;
  }

  .progress-section {
    margin-bottom: 24px;
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 8px;

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .progress-status {
        font-weight: 500;
        color: #303133;
      }

      .progress-percentage {
        font-size: 18px;
        font-weight: bold;
        color: #409eff;
      }
    }
  }

  .result-section {
    margin-bottom: 24px;
  }

  .log-section {
    .log-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;

      .log-title {
        font-weight: 500;
        color: #303133;
      }
    }

    .log-container {
      height: 200px;
      overflow-y: auto;
      background-color: #1e1e1e;
      border-radius: 4px;
      padding: 12px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      line-height: 1.6;

      .log-line {
        color: #d4d4d4;
        margin-bottom: 4px;
        word-break: break-all;

        .log-index {
          color: #858585;
          margin-right: 8px;
          user-select: none;
        }

        .log-content {
          color: #d4d4d4;
        }
      }

      .log-empty {
        color: #858585;
        text-align: center;
        padding: 40px 0;
      }
    }
  }
}

.loading-content {
  padding: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.text-success {
  color: #67c23a;
}

.text-error {
  color: #f56c6c;
}
</style>
