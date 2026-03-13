<script setup lang="ts">
import { computed, ref } from 'vue'

/**
 * 候选SQL状态
 */
export type CandidateStatus = 'pending' | 'checking' | 'correct' | 'incorrect' | 'selected'

/**
 * 候选SQL项接口
 */
export interface CandidateSqlItem {
  /** 唯一标识 */
  id: string
  /** SQL内容 */
  sql: string
  /** 置信度分数 (0-1) */
  confidenceScore?: number
  /** 票数 (用于多数投票) */
  voteCount?: number
  /** 状态 */
  status: CandidateStatus
  /** 错误信息 */
  errorMessage?: string
  /** 执行时间 (ms) */
  executionTime?: number
  /** 是否为最终结果 */
  isFinal?: boolean
  /** 迭代次数 (Check-Correct模式) */
  iterationCount?: number
  /** 修正历史 */
  correctionHistory?: CorrectionRecord[]
}

/**
 * 修正记录
 */
export interface CorrectionRecord {
  iteration: number
  errorType: string
  errorMessage: string
  correctedSql: string
}

interface Props {
  /** 候选SQL列表 */
  candidates: CandidateSqlItem[]
  /** 是否加载中 */
  loading?: boolean
  /** 是否可展开详情 */
  expandable?: boolean
  /** 显示模式: list-列表, card-卡片 */
  displayMode?: 'list' | 'card'
  /** 是否显示投票数 */
  showVotes?: boolean
  /** 是否显示置信度 */
  showConfidence?: boolean
  /** 选中的候选ID */
  selectedId?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  expandable: true,
  displayMode: 'list',
  showVotes: true,
  showConfidence: true
})

const emit = defineEmits<{
  (e: 'select', candidate: CandidateSqlItem): void
  (e: 'expand', candidate: CandidateSqlItem): void
  (e: 'copy', sql: string): void
  (e: 'execute', candidate: CandidateSqlItem): void
}>()

/** 展开的候选ID集合 */
const expandedIds = ref<Set<string>>(new Set())

/** 排序后的候选列表 (按票数/置信度降序) */
const sortedCandidates = computed(() => {
  return [...props.candidates].sort((a, b) => {
    // 优先按选中状态排序
    if (a.isFinal !== b.isFinal) return a.isFinal ? -1 : 1
    // 其次按票数排序
    if (props.showVotes && a.voteCount !== b.voteCount) {
      return (b.voteCount || 0) - (a.voteCount || 0)
    }
    // 最后按置信度排序
    if (props.showConfidence && a.confidenceScore !== b.confidenceScore) {
      return (b.confidenceScore || 0) - (a.confidenceScore || 0)
    }
    return 0
  })
})

/** 正确的候选数量 */
const correctCount = computed(() => {
  return props.candidates.filter(c => c.status === 'correct').length
})

/** 状态标签映射 */
const statusMap: Record<CandidateStatus, { label: string; type: 'success' | 'warning' | 'danger' | 'info' | 'primary' } > = {
  pending: { label: '待检查', type: 'info' },
  checking: { label: '检查中', type: 'primary' },
  correct: { label: '正确', type: 'success' },
  incorrect: { label: '错误', type: 'danger' },
  selected: { label: '已选中', type: 'success' }
}

/**
 * 切换展开状态
 */
const toggleExpand = (candidate: CandidateSqlItem) => {
  if (!props.expandable) return

  if (expandedIds.value.has(candidate.id)) {
    expandedIds.value.delete(candidate.id)
  } else {
    expandedIds.value.add(candidate.id)
  }
  emit('expand', candidate)
}

/**
 * 是否已展开
 */
const isExpanded = (id: string) => expandedIds.value.has(id)

/**
 * 选择候选
 */
const handleSelect = (candidate: CandidateSqlItem) => {
  emit('select', candidate)
}

/**
 * 复制SQL
 */
const handleCopy = (sql: string) => {
  emit('copy', sql)
}

/**
 * 执行SQL
 */
const handleExecute = (candidate: CandidateSqlItem) => {
  emit('execute', candidate)
}

/**
 * 截断SQL显示
 */
const truncateSql = (sql: string, maxLength: number = 80) => {
  if (sql.length <= maxLength) return sql
  return sql.substring(0, maxLength) + '...'
}

/**
 * 格式化置信度
 */
const formatConfidence = (score?: number) => {
  if (score === undefined) return '-'
  return `${(score * 100).toFixed(1)}%`
}
</script>

<template>
  <div class="candidate-sql-list" :class="[`mode-${displayMode}`]">
    <!-- 头部统计 -->
    <div class="list-header">
      <div class="header-title">
        <el-icon><List /></el-icon>
        <span>候选 SQL 列表</span>
        <el-tag size="small" type="info">{{ candidates.length }} 个</el-tag>
      </div>
      <div class="header-stats">
        <el-tag v-if="correctCount > 0" size="small" type="success">
          {{ correctCount }} 个正确
        </el-tag>
        <el-tag v-if="showVotes" size="small" type="warning">按票数排序</el-tag>
        <el-tag v-else-if="showConfidence" size="small" type="warning">按置信度排序</el-tag>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="candidates.length === 0" class="empty-state">
      <el-empty description="暂无候选 SQL" />
    </div>

    <!-- 列表模式 -->
    <template v-else-if="displayMode === 'list'">
      <div class="candidate-items">
        <div
          v-for="(candidate, index) in sortedCandidates"
          :key="candidate.id"
          class="candidate-item"
          :class="{
            'is-final': candidate.isFinal,
            'is-selected': selectedId === candidate.id,
            'is-expanded': isExpanded(candidate.id)
          }"
        >
          <!-- 主行 -->
          <div class="item-main" @click="toggleExpand(candidate)">
            <div class="item-rank">
              <span class="rank-number" :class="{ 'top-3': index < 3 }">{{ index + 1 }}</span>
              <el-icon v-if="candidate.isFinal" class="final-icon"><StarFilled /></el-icon>
            </div>

            <div class="item-content">
              <div class="sql-preview">
                <code>{{ truncateSql(candidate.sql) }}</code>
              </div>

              <div class="item-meta">
                <el-tag
                  :type="statusMap[candidate.status].type"
                  size="small"
                  effect="light"
                >
                  {{ statusMap[candidate.status].label }}
                </el-tag>

                <span v-if="showVotes && candidate.voteCount" class="meta-item">
                  <el-icon><User /></el-icon>
                  {{ candidate.voteCount }} 票
                </span>

                <span v-if="showConfidence && candidate.confidenceScore" class="meta-item">
                  <el-icon><TrendCharts /></el-icon>
                  {{ formatConfidence(candidate.confidenceScore) }}
                </span>

                <span v-if="candidate.executionTime" class="meta-item">
                  <el-icon><Timer /></el-icon>
                  {{ candidate.executionTime }}ms
                </span>
              </div>
            </div>

            <div class="item-actions">
              <el-button
                v-if="candidate.status === 'correct'"
                type="primary"
                size="small"
                @click.stop="handleSelect(candidate)"
              >
                选择
              </el-button>

              <el-button
                link
                size="small"
                @click.stop="handleCopy(candidate.sql)"
              >
                <el-icon><DocumentCopy /></el-icon>
              </el-button>

              <el-button
                v-if="expandable"
                link
                size="small"
                @click.stop="toggleExpand(candidate)"
              >
                <el-icon>
                  <ArrowDown v-if="!isExpanded(candidate.id)" />
                  <ArrowUp v-else />
                </el-icon>
              </el-button>
            </div>
          </div>

          <!-- 展开详情 -->
          <div v-if="isExpanded(candidate.id)" class="item-detail">
            <div class="detail-section">
              <div class="section-title">完整 SQL</div>
              <pre class="sql-code"><code>{{ candidate.sql }}</code></pre>
            </div>

            <div v-if="candidate.errorMessage" class="detail-section">
              <div class="section-title">错误信息</div>
              <el-alert :title="candidate.errorMessage" type="error" :closable="false" />
            </div>

            <div v-if="candidate.correctionHistory?.length" class="detail-section">
              <div class="section-title">修正历史</div>
              <el-timeline>
                <el-timeline-item
                  v-for="record in candidate.correctionHistory"
                  :key="record.iteration"
                  :type="record.iteration === candidate.correctionHistory!.length ? 'success' : 'warning'"
                >
                  <div class="timeline-content">
                    <div class="timeline-title">第 {{ record.iteration }} 次迭代</div>
                    <div class="timeline-error">{{ record.errorType }}: {{ record.errorMessage }}</div>
                    <pre class="timeline-sql"><code>{{ record.correctedSql }}</code></pre>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <div class="detail-actions">
              <el-button type="primary" @click="handleExecute(candidate)">
                <el-icon><VideoPlay /></el-icon>
                执行 SQL
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 卡片模式 -->
    <template v-else>
      <div class="candidate-cards">
        <el-row :gutter="16">
          <el-col
            v-for="(candidate, index) in sortedCandidates"
            :key="candidate.id"
            :xs="24"
            :sm="12"
            :md="8"
          >
            <el-card
              class="candidate-card"
              :class="{
                'is-final': candidate.isFinal,
                'is-selected': selectedId === candidate.id
              }"
              shadow="hover"
            >
              <div class="card-header">
                <div class="card-rank">
                  <span class="rank-badge" :class="{ 'top-3': index < 3 }">#{{ index + 1 }}</span>
                  <el-tag :type="statusMap[candidate.status].type" size="small">
                    {{ statusMap[candidate.status].label }}
                  </el-tag>
                </div>

                <el-icon v-if="candidate.isFinal" class="final-icon"><StarFilled /></el-icon>
              </div>

              <div class="card-content">
                <pre class="sql-code"><code>{{ truncateSql(candidate.sql, 100) }}</code></pre>
              </div>

              <div class="card-stats">
                <div v-if="showVotes && candidate.voteCount" class="stat-item">
                  <el-icon><User /></el-icon>
                  <span>{{ candidate.voteCount }} 票</span>
                </div>

                <div v-if="showConfidence && candidate.confidenceScore" class="stat-item">
                  <el-icon><TrendCharts /></el-icon>
                  <span>{{ formatConfidence(candidate.confidenceScore) }}</span>
                </div>

                <div v-if="candidate.executionTime" class="stat-item">
                  <el-icon><Timer /></el-icon>
                  <span>{{ candidate.executionTime }}ms</span>
                </div>
              </div>

              <div class="card-actions">
                <el-button
                  v-if="candidate.status === 'correct'"
                  type="primary"
                  size="small"
                  @click="handleSelect(candidate)"
                >
                  选择
                </el-button>

                <el-button size="small" @click="handleCopy(candidate.sql)">
                  复制
                </el-button>

                <el-button size="small" @click="handleExecute(candidate)">
                  执行
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.candidate-sql-list {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);

  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-light);
    background: var(--el-fill-color-light);

    .header-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
      font-size: 16px;

      .el-icon {
        font-size: 18px;
        color: var(--el-color-primary);
      }
    }

    .header-stats {
      display: flex;
      gap: 8px;
    }
  }

  .loading-state,
  .empty-state {
    padding: 40px;
  }
}

// 列表模式样式
.candidate-items {
  .candidate-item {
    border-bottom: 1px solid var(--el-border-color-light);
    transition: background-color 0.2s;

    &:last-child {
      border-bottom: none;
    }

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    &.is-final {
      background-color: var(--el-color-success-light-9);
    }

    &.is-selected {
      border-left: 4px solid var(--el-color-primary);
    }

    .item-main {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      cursor: pointer;
    }

    .item-rank {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      min-width: 40px;

      .rank-number {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-secondary);

        &.top-3 {
          color: var(--el-color-warning);
        }
      }

      .final-icon {
        font-size: 16px;
        color: var(--el-color-success);
      }
    }

    .item-content {
      flex: 1;
      min-width: 0;

      .sql-preview {
        code {
          font-family: 'Fira Code', 'Consolas', monospace;
          font-size: 13px;
          color: var(--el-text-color-primary);
          word-break: break-all;
        }
      }

      .item-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 8px;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: var(--el-text-color-secondary);

          .el-icon {
            font-size: 14px;
          }
        }
      }
    }

    .item-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .item-detail {
      padding: 0 16px 16px 72px;
      border-top: 1px dashed var(--el-border-color-light);

      .detail-section {
        margin-top: 16px;

        .section-title {
          font-size: 12px;
          font-weight: 500;
          color: var(--el-text-color-secondary);
          margin-bottom: 8px;
          text-transform: uppercase;
        }

        .sql-code {
          margin: 0;
          padding: 12px;
          background: #f5f5f5;
          border-radius: 4px;
          font-family: 'Fira Code', 'Consolas', monospace;
          font-size: 13px;
          overflow-x: auto;
          white-space: pre-wrap;
          word-break: break-all;
        }
      }

      .timeline-content {
        .timeline-title {
          font-weight: 500;
          margin-bottom: 4px;
        }

        .timeline-error {
          font-size: 12px;
          color: var(--el-color-danger);
          margin-bottom: 8px;
        }

        .timeline-sql {
          margin: 0;
          padding: 8px;
          background: #f5f5f5;
          border-radius: 4px;
          font-family: 'Fira Code', 'Consolas', monospace;
          font-size: 12px;
          overflow-x: auto;
        }
      }

      .detail-actions {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--el-border-color-light);
      }
    }
  }
}

// 卡片模式样式
.candidate-cards {
  padding: 16px;

  .candidate-card {
    margin-bottom: 16px;

    &.is-final {
      border: 2px solid var(--el-color-success);
    }

    &.is-selected {
      border: 2px solid var(--el-color-primary);
    }

    :deep(.el-card__body) {
      padding: 16px;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .card-rank {
        display: flex;
        align-items: center;
        gap: 8px;

        .rank-badge {
          font-size: 14px;
          font-weight: 600;
          color: var(--el-text-color-secondary);
          background: var(--el-fill-color);
          padding: 2px 8px;
          border-radius: 4px;

          &.top-3 {
            color: #fff;
            background: var(--el-color-warning);
          }
        }
      }

      .final-icon {
        font-size: 20px;
        color: var(--el-color-success);
      }
    }

    .card-content {
      .sql-code {
        margin: 0;
        padding: 12px;
        background: #f5f5f5;
        border-radius: 4px;
        font-family: 'Fira Code', 'Consolas', monospace;
        font-size: 12px;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-all;
        max-height: 120px;
        overflow-y: auto;
      }
    }

    .card-stats {
      display: flex;
      gap: 16px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--el-border-color-light);

      .stat-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: var(--el-text-color-secondary);

        .el-icon {
          font-size: 14px;
        }
      }
    }

    .card-actions {
      display: flex;
      gap: 8px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--el-border-color-light);
    }
  }
}
</style>
