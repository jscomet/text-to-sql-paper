<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import SchemaTree from '@/components/business/SchemaTree.vue'
import SqlEditor from '@/components/business/SqlEditor.vue'
import QueryResult from '@/components/business/QueryResult.vue'
import * as connectionApi from '@/api/connections'
import * as queryApi from '@/api/queries'
import type { Connection, SchemaResponse, QueryHistory } from '@/types'

const router = useRouter()

// ==================== State ====================

// 连接列表
const connections = ref<Connection[]>([])
const connectionsLoading = ref(false)

// 当前选中的连接
const selectedConnectionId = ref<number | null>(null)
const selectedConnection = computed(() => {
  return connections.value.find(c => c.id === selectedConnectionId.value) || null
})

// Schema 数据
const schemaData = ref<SchemaResponse>({ tables: [] })
const schemaLoading = ref(false)

// 查询表单
const queryForm = reactive({
  question: '',
})

// 生成的 SQL
const generatedSQL = ref('')
const generatedExplanation = ref('')
const generatedConfidence = ref(0)

// 查询结果
const queryResult = ref<{
  columns: string[]
  rows: Record<string, unknown>[]
  rowCount: number
  executionTime: number
} | null>(null)

// 加载状态
const generating = ref(false)
const executing = ref(false)

// 错误信息
const errorMessage = ref<string | null>(null)

// 历史记录
const recentHistory = ref<QueryHistory[]>([])
const historyLoading = ref(false)

// 示例问题
const sampleQuestions: string[] = [
  '查询所有用户的信息',
  '统计每个部门的员工数量',
  '查询最近30天内注册的活跃用户',
  '找出销售额排名前10的商品',
]

// ==================== Computed ====================

const canGenerate = computed(() => {
  return selectedConnectionId.value && queryForm.question.trim() && !generating.value
})

const canExecute = computed(() => {
  return selectedConnectionId.value && generatedSQL.value.trim() && !executing.value
})

const schemaForTree = computed(() => {
  if (!selectedConnection.value || schemaData.value.tables.length === 0) {
    return []
  }
  return [{
    name: selectedConnection.value.database || 'default',
    tables: schemaData.value.tables,
  }]
})

// ==================== Methods ====================

// 加载连接列表
const loadConnections = async () => {
  connectionsLoading.value = true
  try {
    const response = await connectionApi.getConnections({ page: 1, page_size: 100 })
    connections.value = response.list || []

    // 如果有连接且未选择，默认选择第一个
    if (connections.value.length > 0 && !selectedConnectionId.value) {
      selectedConnectionId.value = connections.value[0]?.id ?? null
    }
  } catch (error) {
    console.error('Failed to load connections:', error)
    ElMessage.error('加载数据库连接失败')
  } finally {
    connectionsLoading.value = false
  }
}

// 加载 Schema
const loadSchema = async () => {
  if (!selectedConnectionId.value) {
    schemaData.value = { tables: [] }
    return
  }

  schemaLoading.value = true
  try {
    const response = await connectionApi.getSchema(selectedConnectionId.value)
    schemaData.value = response
  } catch (error) {
    console.error('Failed to load schema:', error)
    ElMessage.error('加载数据库结构失败')
    schemaData.value = { tables: [] }
  } finally {
    schemaLoading.value = false
  }
}

// 刷新 Schema
const handleRefreshSchema = async () => {
  if (!selectedConnectionId.value) return

  schemaLoading.value = true
  try {
    await connectionApi.refreshSchema(selectedConnectionId.value)
    await loadSchema()
    ElMessage.success('Schema 已刷新')
  } catch (error) {
    console.error('Failed to refresh schema:', error)
    ElMessage.error('刷新 Schema 失败')
  } finally {
    schemaLoading.value = false
  }
}

// 生成 SQL
const handleGenerateSQL = async () => {
  if (!canGenerate.value) return

  generating.value = true
  errorMessage.value = null
  generatedSQL.value = ''
  generatedExplanation.value = ''
  generatedConfidence.value = 0
  queryResult.value = null

  try {
    const response = await queryApi.generateSQL({
      connection_id: selectedConnectionId.value!,
      question: queryForm.question.trim(),
    })

    generatedSQL.value = response.sql
    generatedExplanation.value = response.explanation || ''
    generatedConfidence.value = response.confidence || 0

    ElMessage.success('SQL 生成成功')
  } catch (error: unknown) {
    console.error('Failed to generate SQL:', error)
    const msg = error instanceof Error ? error.message : '生成 SQL 失败'
    errorMessage.value = msg
    ElMessage.error(msg)
  } finally {
    generating.value = false
  }
}

// 执行 SQL
const handleExecuteSQL = async () => {
  if (!canExecute.value) return

  executing.value = true
  errorMessage.value = null
  queryResult.value = null

  try {
    const response = await queryApi.executeSQL({
      connection_id: selectedConnectionId.value!,
      sql: generatedSQL.value.trim(),
    })

    // 转换行数据格式
    const rows = response.rows.map((row: unknown[]) => {
      const obj: Record<string, unknown> = {}
      response.columns.forEach((col, index) => {
        obj[col] = row[index]
      })
      return obj
    })

    queryResult.value = {
      columns: response.columns,
      rows,
      rowCount: response.row_count,
      executionTime: response.execution_time,
    }

    // 刷新历史记录
    loadRecentHistory()

    ElMessage.success('查询执行成功')
  } catch (error: unknown) {
    console.error('Failed to execute SQL:', error)
    const msg = error instanceof Error ? error.message : '执行 SQL 失败'
    errorMessage.value = msg
    ElMessage.error(msg)
  } finally {
    executing.value = false
  }
}

// 一键运行（生成+执行）
const handleRunQuery = async () => {
  if (!canGenerate.value) return

  await handleGenerateSQL()
  if (generatedSQL.value && !errorMessage.value) {
    await handleExecuteSQL()
  }
}

// 使用示例问题
const useSampleQuestion = (question: string) => {
  queryForm.question = question
}

// 处理表点击（插入表名到输入框）
const handleTableClick = (table: { name: string }) => {
  const text = ` ${table.name} `
  const textarea = document.querySelector('.question-input textarea') as HTMLTextAreaElement
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const value = queryForm.question
    queryForm.question = value.substring(0, start) + text + value.substring(end)

    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + text.length
      textarea.focus()
    }, 0)
  } else {
    queryForm.question += text
  }
}

// 清空查询
const handleClear = () => {
  ElMessageBox.confirm('确定要清空当前查询吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    queryForm.question = ''
    generatedSQL.value = ''
    generatedExplanation.value = ''
    generatedConfidence.value = 0
    queryResult.value = null
    errorMessage.value = null
    ElMessage.success('已清空')
  }).catch(() => {})
}

// 复制 SQL
const handleCopySQL = async () => {
  if (!generatedSQL.value) return
  try {
    await navigator.clipboard.writeText(generatedSQL.value)
    ElMessage.success('SQL 已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 导出结果
const handleExport = (format: 'csv' | 'json') => {
  if (!queryResult.value || queryResult.value.rows.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const { columns, rows } = queryResult.value
  let content = ''
  let filename = `query_result_${Date.now()}`
  let mimeType = ''

  if (format === 'csv') {
    // CSV 格式
    const header = columns.join(',')
    const dataRows = rows.map(row =>
      columns.map(col => {
        const value = row[col]
        if (value === null || value === undefined) return ''
        const str = String(value)
        // 如果包含逗号或换行，用引号包裹
        if (str.includes(',') || str.includes('\n') || str.includes('"')) {
          return `"${str.replace(/"/g, '""')}"`
        }
        return str
      }).join(',')
    )
    content = [header, ...dataRows].join('\n')
    filename += '.csv'
    mimeType = 'text/csv;charset=utf-8;'
  } else {
    // JSON 格式
    content = JSON.stringify(rows, null, 2)
    filename += '.json'
    mimeType = 'application/json;charset=utf-8;'
  }

  // 创建下载链接
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success(`已导出为 ${format.toUpperCase()}`)
}

// 加载最近历史
const loadRecentHistory = async () => {
  historyLoading.value = true
  try {
    const response = await queryApi.getQueryHistory({
      page: 1,
      page_size: 10,
    })
    recentHistory.value = response.list || []
  } catch (error) {
    console.error('Failed to load history:', error)
  } finally {
    historyLoading.value = false
  }
}

// 加载历史记录到查询
const loadHistoryItem = (item: QueryHistory) => {
  if (item.connection_id) {
    selectedConnectionId.value = item.connection_id
  }
  queryForm.question = item.question
  generatedSQL.value = item.sql
  generatedExplanation.value = item.explanation || ''
  generatedConfidence.value = item.confidence || 0
  queryResult.value = null
  errorMessage.value = null

  // 如果历史记录有结果预览，尝试恢复
  if (item.result_preview) {
    const rows = item.result_preview.rows.map((row: unknown[]) => {
      const obj: Record<string, unknown> = {}
      item.result_preview!.columns.forEach((col, index) => {
        obj[col] = row[index]
      })
      return obj
    })
    queryResult.value = {
      columns: item.result_preview.columns,
      rows,
      rowCount: rows.length,
      executionTime: 0,
    }
  }

  ElMessage.success('已加载历史查询')
}

// 切换收藏
const toggleFavorite = async (item: QueryHistory, event: MouseEvent) => {
  event.stopPropagation()
  try {
    await queryApi.toggleFavorite(item.id, !item.is_favorite)
    item.is_favorite = !item.is_favorite
    ElMessage.success(item.is_favorite ? '已收藏' : '已取消收藏')
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
    ElMessage.error('操作失败')
  }
}

// 跳转到历史页面
const goToHistory = () => {
  router.push('/history')
}

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 小于7天
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}天前`
  }

  return date.toLocaleDateString('zh-CN')
}

// ==================== Watch ====================

watch(selectedConnectionId, () => {
  loadSchema()
})

// 监听路由查询参数
watch(
  () => router.currentRoute.value.query,
  (query) => {
    if (query.connection_id) {
      selectedConnectionId.value = Number(query.connection_id)
    }
    if (query.question) {
      queryForm.question = String(query.question)
    }
  },
  { immediate: true },
)

// ==================== Lifecycle ====================

onMounted(() => {
  loadConnections()
  loadRecentHistory()
})
</script>

<template>
  <div class="query-view">
    <el-row :gutter="16" class="query-row">
      <!-- 左侧：Schema 树 -->
      <el-col :xs="24" :sm="8" :md="6" :lg="5" class="schema-col">
        <el-card shadow="never" class="schema-card">
          <template #header>
            <div class="card-header">
              <span>数据库结构</span>
              <el-button
                v-if="selectedConnectionId"
                link
                size="small"
                :loading="schemaLoading"
                @click="handleRefreshSchema"
              >
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <div class="connection-select-wrapper">
            <el-select
              v-model="selectedConnectionId"
              placeholder="选择数据库连接"
              class="connection-select"
              :loading="connectionsLoading"
            >
              <el-option
                v-for="conn in connections"
                :key="conn.id"
                :label="conn.name"
                :value="conn.id"
              >
                <div class="connection-option">
                  <el-icon><Connection /></el-icon>
                  <span>{{ conn.name }}</span>
                  <el-tag
                    size="small"
                    :type="conn.status === 'active' ? 'success' : 'danger'"
                    class="status-tag"
                  >
                    {{ conn.status === 'active' ? '在线' : '离线' }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>

            <el-button
              v-if="connections.length === 0"
              type="primary"
              link
              @click="router.push('/connections')"
            >
              <el-icon><Plus /></el-icon>
              添加连接
            </el-button>
          </div>

          <div class="schema-tree-wrapper">
            <SchemaTree
              :schemas="schemaForTree"
              :loading="schemaLoading"
              @table-click="handleTableClick"
              @refresh="handleRefreshSchema"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 中间：查询区域 -->
      <el-col :xs="24" :sm="16" :md="13" :lg="14" class="query-col">
        <!-- 自然语言输入 -->
        <el-card shadow="never" class="query-input-card">
          <template #header>
            <div class="card-header">
              <span>自然语言查询</span>
              <el-button link size="small" @click="handleClear">
                <el-icon><Delete /></el-icon>
                清空
              </el-button>
            </div>
          </template>

          <div class="question-section">
            <el-input
              v-model="queryForm.question"
              type="textarea"
              :rows="3"
              placeholder="输入您的问题，例如：查询最近30天内销售额排名前10的商品"
              class="question-input"
              resize="none"
            />

            <!-- 示例问题 -->
            <div class="sample-questions">
              <span class="sample-label">示例：</span>
              <el-tag
                v-for="(q, index) in sampleQuestions"
                :key="index"
                size="small"
                class="sample-tag"
                @click="useSampleQuestion(q)"
              >
                {{ q }}
              </el-tag>
            </div>

            <!-- 操作按钮 -->
            <div class="query-actions">
              <el-button
                type="primary"
                size="large"
                :loading="generating"
                :disabled="!canGenerate"
                @click="handleGenerateSQL"
              >
                <el-icon><MagicStick /></el-icon>
                生成 SQL
              </el-button>
              <el-button
                type="success"
                size="large"
                :loading="generating || executing"
                :disabled="!canGenerate"
                @click="handleRunQuery"
              >
                <el-icon><VideoPlay /></el-icon>
                一键运行
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- SQL 编辑器 -->
        <el-card v-if="generatedSQL" shadow="never" class="sql-card">
          <template #header>
            <div class="card-header">
              <div class="sql-header-left">
                <span>生成的 SQL</span>
                <el-tag v-if="generatedConfidence > 0" size="small" :type="generatedConfidence > 0.8 ? 'success' : generatedConfidence > 0.5 ? 'warning' : 'danger'">
                  置信度: {{ (generatedConfidence * 100).toFixed(1) }}%
                </el-tag>
              </div>
              <div class="sql-header-actions">
                <el-button link size="small" @click="handleCopySQL">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  :loading="executing"
                  :disabled="!canExecute"
                  @click="handleExecuteSQL"
                >
                  <el-icon><VideoPlay /></el-icon>
                  执行
                </el-button>
              </div>
            </div>
          </template>

          <div class="sql-section">
            <SqlEditor
              v-model="generatedSQL"
              height="150px"
              placeholder="生成的 SQL 将显示在这里..."
              @run="handleExecuteSQL"
            />

            <div v-if="generatedExplanation" class="sql-explanation">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ generatedExplanation }}</span>
            </div>
          </div>
        </el-card>

        <!-- 查询结果 -->
        <el-card v-if="generatedSQL" shadow="never" class="result-card">
          <template #header>
            <div class="card-header">
              <span>查询结果</span>
              <div v-if="queryResult" class="result-actions">
                <el-button link size="small" @click="handleExport('csv')">
                  <el-icon><Download /></el-icon>
                  导出 CSV
                </el-button>
                <el-button link size="small" @click="handleExport('json')">
                  <el-icon><Document /></el-icon>
                  导出 JSON
                </el-button>
              </div>
            </div>
          </template>

          <div class="result-section">
            <QueryResult
              :data="queryResult?.rows || []"
              :columns="queryResult?.columns.map(col => ({ prop: col, label: col })) || []"
              :loading="executing"
              :error="errorMessage"
              :execution-time="queryResult?.executionTime || 0"
              :row-count="queryResult?.rowCount || 0"
              :sql="generatedSQL"
              @export="handleExport"
              @retry="handleExecuteSQL"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：历史记录 -->
      <el-col :xs="24" :sm="24" :md="5" :lg="5" class="history-col">
        <el-card shadow="never" class="history-card">
          <template #header>
            <div class="card-header">
              <span>最近查询</span>
              <el-button link size="small" @click="goToHistory">
                查看全部
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>

          <div v-loading="historyLoading" class="history-list">
            <div
              v-for="item in recentHistory"
              :key="item.id"
              class="history-item"
              @click="loadHistoryItem(item)"
            >
              <div class="history-header">
                <span class="history-question" :title="item.question">
                  {{ item.question.length > 30 ? item.question.slice(0, 30) + '...' : item.question }}
                </span>
                <el-icon
                  class="favorite-icon"
                  :class="{ 'is-favorite': item.is_favorite }"
                  @click="toggleFavorite(item, $event)"
                >
                  <Star v-if="item.is_favorite" />
                  <StarFilled v-else />
                </el-icon>
              </div>
              <div class="history-meta">
                <span class="meta-db">{{ item.connection_name || '未知数据库' }}</span>
                <span class="meta-time">{{ formatTime(item.created_at) }}</span>
              </div>
              <div class="history-status">
                <el-tag
                  size="small"
                  :type="item.execution_status === 'success' ? 'success' : item.execution_status === 'failed' ? 'danger' : 'info'"
                >
                  {{ item.execution_status === 'success' ? '成功' : item.execution_status === 'failed' ? '失败' : '待执行' }}
                </el-tag>
              </div>
            </div>

            <el-empty v-if="recentHistory.length === 0" description="暂无查询记录" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.query-view {
  height: 100%;
  padding: 16px;
  background: var(--bg-color, #f5f7fa);

  .query-row {
    height: 100%;
    margin: 0 !important;

    .schema-col,
    .query-col,
    .history-col {
      height: 100%;
      padding: 0 8px;

      > .el-card {
        height: 100%;
        display: flex;
        flex-direction: column;

        :deep(.el-card__body) {
          flex: 1;
          overflow: auto;
          padding: 16px;
        }
      }
    }

    .schema-col {
      .schema-card {
        .connection-select-wrapper {
          margin-bottom: 16px;

          .connection-select {
            width: 100%;
            margin-bottom: 8px;
          }

          .connection-option {
            display: flex;
            align-items: center;
            gap: 8px;

            .status-tag {
              margin-left: auto;
            }
          }
        }

        .schema-tree-wrapper {
          flex: 1;
          overflow: auto;
          border: 1px solid var(--el-border-color-light);
          border-radius: 4px;
        }
      }
    }

    .query-col {
      display: flex;
      flex-direction: column;
      gap: 16px;

      .query-input-card,
      .sql-card,
      .result-card {
        flex: none;

        :deep(.el-card__body) {
          overflow: visible;
        }
      }

      .result-card {
        flex: 1;
        min-height: 300px;

        .result-section {
          height: 100%;
        }
      }

      .question-section {
        .question-input {
          margin-bottom: 12px;
        }

        .sample-questions {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;

          .sample-label {
            font-size: 13px;
            color: var(--el-text-color-secondary);
          }

          .sample-tag {
            cursor: pointer;

            &:hover {
              color: var(--el-color-primary);
            }
          }
        }

        .query-actions {
          display: flex;
          gap: 12px;

          .el-button {
            flex: 1;
          }
        }
      }

      .sql-section {
        .sql-explanation {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          margin-top: 12px;
          padding: 12px;
          background: var(--el-color-info-light-9);
          border-radius: 4px;
          font-size: 13px;
          color: var(--el-text-color-regular);

          .el-icon {
            margin-top: 2px;
            color: var(--el-color-info);
          }
        }
      }
    }

    .history-col {
      .history-card {
        .history-list {
          .history-item {
            padding: 12px;
            border-bottom: 1px solid var(--el-border-color-light);
            cursor: pointer;
            transition: background 0.2s;

            &:hover {
              background: var(--el-fill-color-light);
            }

            &:last-child {
              border-bottom: none;
            }

            .history-header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              margin-bottom: 8px;

              .history-question {
                font-size: 14px;
                color: var(--el-text-color-primary);
                font-weight: 500;
                flex: 1;
                margin-right: 8px;
              }

              .favorite-icon {
                font-size: 16px;
                color: var(--el-text-color-placeholder);
                cursor: pointer;
                transition: color 0.2s;

                &:hover,
                &.is-favorite {
                  color: var(--el-color-warning);
                }
              }
            }

            .history-meta {
              display: flex;
              justify-content: space-between;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 8px;
            }

            .history-status {
              .el-tag {
                font-size: 11px;
              }
            }
          }
        }
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;

    .sql-header-left {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .sql-header-actions,
    .result-actions {
      display: flex;
      gap: 8px;
    }
  }
}

// 响应式适配
@media (max-width: 992px) {
  .query-view {
    .query-row {
      .schema-col,
      .query-col,
      .history-col {
        height: auto;
        margin-bottom: 16px;

        > .el-card {
          height: auto;
          max-height: 500px;
        }
      }
    }
  }
}
</style>
