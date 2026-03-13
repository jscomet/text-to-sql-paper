<script setup lang="ts">
import { computed } from 'vue'

/**
 * 修正记录接口
 */
export interface CorrectionRecord {
  /** 迭代次数 */
  iteration: number
  /** 原始SQL */
  originalSql: string
  /** 错误类型 */
  errorType: string
  /** 错误信息 */
  errorMessage: string
  /** 修正后的SQL */
  correctedSql: string
  /** 修正说明 */
  correctionNote?: string
  /** 耗时 (ms) */
  duration?: number
  /** 时间戳 */
  timestamp?: string
}

/**
 * 时间线总结信息
 */
export interface TimelineSummary {
  /** 总迭代次数 */
  totalIterations: number
  /** 成功次数 */
  successCount: number
  /** 失败次数 */
  failureCount: number
  /** 总耗时 (ms) */
  totalDuration: number
  /** 最终SQL */
  finalSql: string
  /** 是否成功 */
  isSuccessful: boolean
}

interface Props {
  /** 修正历史记录 */
  records: CorrectionRecord[]
  /** 总结信息 */
  summary?: TimelineSummary
  /** 是否加载中 */
  loading?: boolean
  /** 是否可展开SQL详情 */
  expandableSql?: boolean
  /** 是否显示时间戳 */
  showTimestamp?: boolean
  /** 是否显示耗时 */
  showDuration?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  expandableSql: true,
  showTimestamp: true,
  showDuration: true
})

const emit = defineEmits<{
  (e: 'sql-click', sql: string): void
  (e: 'copy', sql: string): void
  (e: 'compare', record: CorrectionRecord): void
}>()

/** 排序后的记录 (按迭代次数升序) */
const sortedRecords = computed(() => {
  return [...props.records].sort((a, b) => a.iteration - b.iteration)
})

/** 是否有总结信息 */
const hasSummary = computed(() => !!props.summary)

/** 成功率 */
const successRate = computed(() => {
  if (!props.summary || props.summary.totalIterations === 0) return 0
  return Math.round((props.summary.successCount / props.summary.totalIterations) * 100)
})

/** 格式化耗时 */
const formatDuration = (ms?: number) => {
  if (ms === undefined) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

/** 格式化时间戳 */
const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/** 截断SQL */
const truncateSql = (sql: string, maxLength: number = 60) => {
  if (sql.length <= maxLength) return sql
  return sql.substring(0, maxLength) + '...'
}

/** 处理SQL点击 */
const handleSqlClick = (sql: string) => {
  emit('sql-click', sql)
}

/** 处理复制 */
const handleCopy = (sql: string) => {
  emit('copy', sql)
}

/** 处理对比 */
const handleCompare = (record: CorrectionRecord) => {
  emit('compare', record)
}

/** 获取错误类型标签样式 */
const getErrorTypeStyle = (errorType: string) => {
  const typeMap: Record<string, { type: 'danger' | 'warning' | 'info'; label: string } > = {
    'syntax': { type: 'danger', label: '语法错误' },
    'execution': { type: 'danger', label: '执行错误' },
    'logic': { type: 'warning', label: '逻辑错误' },
    'schema': { type: 'warning', label: 'Schema错误' },
    'timeout': { type: 'info', label: '超时' },
    'unknown': { type: 'info', label: '未知错误' }
  }
  return typeMap[errorType] || { type: 'info', label: errorType }
}</script>

<template>
  <div class="correction-timeline">
    <!-- 头部总结 -->
    <div v-if="hasSummary" class="timeline-header">
      <div class="header-title">
        <el-icon><Timer /></el-icon>
        <span>修正历史</span>
        <el-tag
          :type="summary!.isSuccessful ? 'success' : 'warning'"
          size="small"
          effect="dark"
        >
          {{ summary!.isSuccessful ? '修正成功' : '部分成功' }}
        </el-tag>
      </div>

      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-label">迭代次数</span>
          <span class="stat-value">{{ summary!.totalIterations }}</span>
        </div>

        <div class="stat-item">
          <span class="stat-label">成功率</span>
          <span class="stat-value" :class="{ 'is-high': successRate >= 80 }">
            {{ successRate }}%
          </span>
        </div>

        <div v-if="showDuration" class="stat-item">
          <span class="stat-label">总耗时</span>
          <span class="stat-value">{{ formatDuration(summary!.totalDuration) }}</span>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="records.length === 0" class="empty-state">
      <el-empty description="暂无修正历史" />
    </div>

    <!-- 时间线 -->
    <div v-else class="timeline-content">
      <el-timeline>
        <!-- 初始版本 -->
        <el-timeline-item type="primary" :hollow="true"
003e
          <div class="timeline-item initial-version">
            <div class="item-header">
              <span class="item-title">初始版本</span>
            </div>
            <div v-if="sortedRecords.length > 0" class="item-sql">
              <pre><code>{{ truncateSql(sortedRecords[0].originalSql) }}</code></pre>
              <el-button
                v-if="expandableSql"
                link
                size="small"
                @click="handleSqlClick(sortedRecords[0].originalSql)"
              >
                查看完整SQL
              </el-button>
            </div>
          </div>
        </el-timeline-item>

        <!-- 修正记录 -->
        <el-timeline-item
          v-for="(record, index) in sortedRecords"
          :key="record.iteration"
          :type="index === sortedRecords.length - 1 ? 'success' : 'warning'"
          :icon="index === sortedRecords.length - 1 ? 'CircleCheck' : 'Warning'"
        >
          <div class="timeline-item correction-record">
            <!-- 记录头部 -->
            <div class="item-header">
              <div class="header-left">
                <span class="item-title">第 {{ record.iteration }} 次修正</span>
                <el-tag
                  :type="getErrorTypeStyle(record.errorType).type"
                  size="small"
                  effect="light"
                >
                  {{ getErrorTypeStyle(record.errorType).label }}
                </el-tag>
              </div>

              <div class="header-right">
                <span v-if="showDuration && record.duration" class="duration">
                  <el-icon><Timer /></el-icon>
                  {{ formatDuration(record.duration) }}
                </span>
                <span v-if="showTimestamp && record.timestamp" class="timestamp">
                  {{ formatTimestamp(record.timestamp) }}
                </span>
              </div>
            </div>

            <!-- 错误信息 -->
            <div class="error-section">
              <div class="section-label">错误信息</div>
              <el-alert
                :title="record.errorMessage"
                :type="getErrorTypeStyle(record.errorType).type"
                :closable="false"
                show-icon
              />
            </div>

            <!-- 修正说明 -->
            <div v-if="record.correctionNote" class="note-section">
              <div class="section-label">修正说明</div>
              <div class="note-content">{{ record.correctionNote }}</div>
            </div>

            <!-- 修正后的SQL -->
            <div class="sql-section">
              <div class="section-label">修正后的SQL</div>
              <div class="sql-box">
                <pre><code>{{ truncateSql(record.correctedSql) }}</code></pre>
                <div class="sql-actions">
                  <el-button
                    v-if="expandableSql"
                    link
                    size="small"
                    @click="handleSqlClick(record.correctedSql)"
                  >
                    查看完整SQL
                  </el-button>
                  <el-button link size="small" @click="handleCopy(record.correctedSql)">
                    复制
                  </el-button>
                  <el-button link size="small" @click="handleCompare(record)">
                    对比
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-timeline-item>

        <!-- 最终结果 -->
        <el-timeline-item
          v-if="hasSummary && summary!.isSuccessful"
          type="success"
          icon="CircleCheckFilled"
        >
          <div class="timeline-item final-result">
            <div class="item-header">
              <span class="item-title">最终结果</span>
              <el-tag type="success" size="small" effect="dark">验证通过</el-tag>
            </div>

            <div class="sql-section">
              <div class="sql-box success">
                <pre><code>{{ truncateSql(summary!.finalSql) }}</code></pre>
                <div class="sql-actions">
                  <el-button
                    v-if="expandableSql"
                    link
                    size="small"
                    @click="handleSqlClick(summary!.finalSql)"
                  >
                    查看完整SQL
                  </el-button>
                  <el-button link size="small" @click="handleCopy(summary!.finalSql)">
                    复制
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>
  </div>
</template>

<style scoped lang="scss">
.correction-timeline {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-light);

  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 500;

    .el-icon {
      font-size: 18px;
      color: var(--el-color-primary);
    }
  }

  .header-stats {
    display: flex;
    gap: 24px;

    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;

      .stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }

      .stat-value {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);

        &.is-high {
          color: var(--el-color-success);
        }
      }
    }
  }
}

.loading-state,
.empty-state {
  padding: 40px;
}

.timeline-content {
  padding: 20px;

  :deep(.el-timeline) {
    padding-left: 8px;
  }

  :deep(.el-timeline-item__node) {
    width: 12px;
    height: 12px;
  }

  :deep(.el-timeline-item__wrapper) {
    padding-bottom: 20px;
  }
}

.timeline-item {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);

  &.initial-version {
    background: var(--el-color-info-light-9);
    border-color: var(--el-color-info-light-5);
  }

  &.correction-record {
    background: var(--el-color-warning-light-9);
    border-color: var(--el-color-warning-light-5);
  }

  &.final-result {
    background: var(--el-color-success-light-9);
    border-color: var(--el-color-success-light-5);
  }
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
    color: var(--el-text-color-secondary);

    .duration {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .item-title {
    font-weight: 600;
    font-size: 14px;
    color: var(--el-text-color-primary);
  }
}

.section-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.error-section,
.note-section,
.sql-section {
  margin-top: 12px;
}

.note-content {
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.sql-box {
  background: #fff;
  border-radius: 4px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;

  &.success {
    border-color: var(--el-color-success-light-3);
    background: var(--el-color-success-light-9);
  }

  pre {
    margin: 0;
    padding: 12px;
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 150px;
    overflow-y: auto;

    code {
      color: var(--el-text-color-primary);
    }
  }

  .sql-actions {
    display: flex;
    gap: 8px;
    padding: 8px 12px;
    border-top: 1px solid var(--el-border-color-light);
    background: var(--el-fill-color-light);
  }
}

.item-sql {
  pre {
    margin: 0 0 8px 0;
    padding: 12px;
    background: #fff;
    border-radius: 4px;
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;

    code {
      color: var(--el-text-color-primary);
    }
  }
}
</style>
