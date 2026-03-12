<script setup lang="ts">
import { ref, reactive } from 'vue'

// 查询表单
const queryForm = reactive({
  question: '',
  connectionId: null as number | null,
})

// 加载状态
const loading = ref(false)

// 生成的SQL
const generatedSQL = ref('')

// 查询结果
const queryResult = ref<{
  columns: string[]
  rows: Record<string, unknown>[]
}> | null>(null)

// 执行历史
const executionHistory = ref<
  {
    id: number
    question: string
    sql: string
    status: 'success' | 'error'
    time: string
  }[]
>([])

// 模拟连接列表
const connections = ref([
  { id: 1, name: 'MySQL - 生产环境' },
  { id: 2, name: 'PostgreSQL - 测试环境' },
])

// 提交查询
const handleSubmit = async () => {
  if (!queryForm.question.trim()) return

  loading.value = true
  try {
    // TODO: 调用后端API生成SQL
    await new Promise((resolve) => setTimeout(resolve, 1500))
    generatedSQL.value = `SELECT * FROM users WHERE name LIKE '%${queryForm.question}%'`

    // 添加到历史
    executionHistory.value.unshift({
      id: Date.now(),
      question: queryForm.question,
      sql: generatedSQL.value,
      status: 'success',
      time: new Date().toLocaleTimeString(),
    })
  } finally {
    loading.value = false
  }
}

// 执行SQL
const handleExecute = async () => {
  if (!generatedSQL.value) return

  loading.value = true
  try {
    // TODO: 调用后端API执行SQL
    await new Promise((resolve) => setTimeout(resolve, 1000))
    queryResult.value = {
      columns: ['id', 'name', 'email', 'created_at'],
      rows: [
        { id: 1, name: '张三', email: 'zhangsan@example.com', created_at: '2024-01-01' },
        { id: 2, name: '李四', email: 'lisi@example.com', created_at: '2024-01-02' },
      ],
    }
  } finally {
    loading.value = false
  }
}

// 复制SQL
const handleCopy = () => {
  navigator.clipboard.writeText(generatedSQL.value)
}

// 重新生成
const handleRegenerate = () => {
  generatedSQL.value = ''
  queryResult.value = null
}
</script>

<template>
  <div class="query-view">
    <el-row :gutter="20">
      <!-- 左侧：查询输入 -->
      <el-col :xs="24" :sm="24" :md="16">
        <el-card class="query-card">
          <template #header>
            <div class="card-header">
              <span>📝 自然语言查询</span>
            </div>
          </template>

          <div class="query-input-section">
            <!-- 数据库连接选择 -->
            <div class="connection-select">
              <label>选择数据库连接：</label>
              <el-select
                v-model="queryForm.connectionId"
                placeholder="请选择数据库连接"
                style="width: 300px"
              >
                <el-option
                  v-for="conn in connections"
                  :key="conn.id"
                  :label="conn.name"
                  :value="conn.id"
                />
              </el-select>
            </div>

            <!-- 问题输入 -->
            <div class="question-input">
              <label>输入您的问题：</label>
              <el-input
                v-model="queryForm.question"
                type="textarea"
                :rows="4"
                placeholder="例如：查询最近30天内注册的所有用户，按注册时间倒序排列"
                resize="none"
              />
            </div>

            <!-- 提交按钮 -->
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              :disabled="!queryForm.question.trim()"
              @click="handleSubmit"
            >
              <el-icon><Magic /></el-icon>
              生成SQL
            </el-button>
          </div>
        </el-card>

        <!-- 生成的SQL -->
        <el-card v-if="generatedSQL" class="result-card">
          <template #header>
            <div class="card-header">
              <span>⚡ 生成的SQL</span>
              <div class="header-actions">
                <el-button type="primary" size="small" @click="handleExecute">
                  <el-icon><VideoPlay /></el-icon>
                  执行
                </el-button>
                <el-button size="small" @click="handleCopy">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <el-button size="small" @click="handleRegenerate">
                  <el-icon><Refresh /></el-icon>
                  重新生成
                </el-button>
              </div>
            </div>
          </template>

          <pre class="sql-code"><code>{{ generatedSQL }}</code></pre>
        </el-card>

        <!-- 查询结果 -->
        <el-card v-if="queryResult" class="result-card">
          <template #header>
            <div class="card-header">
              <span>📊 查询结果</span>
            </div>
          </template>

          <el-table :data="queryResult.rows" border stripe style="width: 100%">
            <el-table-column
              v-for="col in queryResult.columns"
              :key="col"
              :prop="col"
              :label="col"
            />
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：历史记录 -->
      <el-col :xs="24" :sm="24" :md="8">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <span>🕐 执行历史</span>
            </div>
          </template>

          <div v-if="executionHistory.length === 0" class="empty-history">
            <el-empty description="暂无执行记录" />
          </div>

          <el-timeline v-else>
            <el-timeline-item
              v-for="item in executionHistory"
              :key="item.id"
              :type="item.status === 'success' ? 'success' : 'danger'"
            >
              <div class="history-item">
                <p class="history-question">{{ item.question }}</p>
                <pre class="history-sql">{{ item.sql }}</pre>
                <span class="history-time">{{ item.time }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.query-view {
  .query-card {
    margin-bottom: 20px;

    .query-input-section {
      .connection-select {
        margin-bottom: 20px;

        label {
          display: block;
          margin-bottom: 8px;
          font-size: 14px;
          color: #606266;
        }
      }

      .question-input {
        margin-bottom: 20px;

        label {
          display: block;
          margin-bottom: 8px;
          font-size: 14px;
          color: #606266;
        }
      }
    }
  }

  .result-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }

    .sql-code {
      margin: 0;
      padding: 16px;
      background-color: #f5f7fa;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 14px;
      overflow-x: auto;
    }
  }

  .history-card {
    .empty-history {
      padding: 40px 0;
    }

    .history-item {
      .history-question {
        margin: 0 0 8px;
        font-size: 14px;
        color: #303133;
        font-weight: 500;
      }

      .history-sql {
        margin: 0 0 8px;
        padding: 8px;
        background-color: #f5f7fa;
        border-radius: 4px;
        font-size: 12px;
        color: #606266;
        overflow-x: auto;
      }

      .history-time {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}
</style>
