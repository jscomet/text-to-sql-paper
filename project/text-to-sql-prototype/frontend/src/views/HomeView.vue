<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as queriesApi from '@/api/queries'
import * as connectionsApi from '@/api/connections'
import type { QueryHistory, Connection } from '@/types'

const userStore = useUserStore()
const router = useRouter()

const username = computed(() => userStore.userInfo?.username || '用户')

// 加载状态
const loading = ref({
  queries: false,
  connections: false,
  stats: false,
})

// 最近查询历史
const recentQueries = ref<QueryHistory[]>([])

// 常用数据库连接
const recentConnections = ref<Connection[]>([])

// 今日统计
const todayStats = ref({
  queryCount: 0,
  successRate: 0,
})

// 快捷操作
const quickActions = [
  {
    title: '开始查询',
    icon: 'ChatDotRound',
    desc: '输入自然语言，生成SQL查询',
    route: '/query',
    color: '#409eff',
  },
  {
    title: '管理连接',
    icon: 'Connection',
    desc: '配置数据库连接信息',
    route: '/connections',
    color: '#67c23a',
  },
  {
    title: '查看历史',
    icon: 'Clock',
    desc: '浏览历史查询记录',
    route: '/history',
    color: '#e6a23c',
  },
  {
    title: '运行评测',
    icon: 'TrendCharts',
    desc: '评测SQL生成质量',
    route: '/evaluations',
    color: '#f56c6c',
  },
]

// 获取最近查询历史
const fetchRecentQueries = async () => {
  loading.value.queries = true
  try {
    const response = await queriesApi.getQueryHistory({ page: 1, page_size: 5 })
    recentQueries.value = response.list.slice(0, 5)
  } catch (error) {
    console.error('获取查询历史失败:', error)
  } finally {
    loading.value.queries = false
  }
}

// 获取常用连接
const fetchRecentConnections = async () => {
  loading.value.connections = true
  try {
    const response = await connectionsApi.getConnections({ page: 1, page_size: 5 })
    recentConnections.value = response.list
      .filter((conn) => conn.status === 'active')
      .slice(0, 5)
  } catch (error) {
    console.error('获取连接列表失败:', error)
  } finally {
    loading.value.connections = false
  }
}

// 获取今日统计
const fetchTodayStats = async () => {
  loading.value.stats = true
  try {
    const response = await queriesApi.getQueryHistory({ page: 1, page_size: 100 })
    const today = new Date().toDateString()
    const todayQueries = response.list.filter((q) => {
      const queryDate = new Date(q.created_at).toDateString()
      return queryDate === today
    })

    todayStats.value.queryCount = todayQueries.length
    const successCount = todayQueries.filter((q) => q.execution_status === 'success').length
    todayStats.value.successRate =
      todayQueries.length > 0 ? Math.round((successCount / todayQueries.length) * 100) : 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    loading.value.stats = false
  }
}

// 处理快捷操作
const handleAction = (route: string) => {
  router.push(route)
}

// 跳转到查询历史详情
const viewQueryDetail = (query: QueryHistory) => {
  router.push(`/history?id=${query.id}`)
}

// 跳转到连接管理
const viewConnections = () => {
  router.push('/connections')
}

// 格式化时间
const formatTime = (time: string) => {
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    pending: 'warning',
  }
  return map[status] || 'info'
}

// 截断文本
const truncateText = (text: string, length: number) => {
  if (!text) return '-'
  return text.length > length ? text.substring(0, length) + '...' : text
}

onMounted(() => {
  fetchRecentQueries()
  fetchRecentConnections()
  fetchTodayStats()
})
</script>

<template>
  <div class="home-view">
    <!-- 欢迎区域 -->
    <el-card class="welcome-card">
      <div class="welcome-content">
        <h1>欢迎使用 Text2SQL 👋</h1>
        <p class="welcome-text">
          你好，<strong>{{ username }}</strong
          >！Text2SQL 是一个智能文本转SQL查询系统， 帮助您通过自然语言快速生成SQL查询语句。
        </p>
      </div>
    </el-card>

    <!-- 统计数据卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="12">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon" style="background-color: #409eff20; color: #409eff">
              <el-icon :size="24"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ todayStats.queryCount }}</div>
              <div class="stat-label">今日查询</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon" style="background-color: #67c23a20; color: #67c23a">
              <el-icon :size="24"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ todayStats.successRate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <el-row :gutter="20">
        <el-col
          v-for="action in quickActions"
          :key="action.title"
          :xs="24"
          :sm="12"
          :md="12"
          :lg="6"
          class="action-col"
        >
          <el-card class="action-card" shadow="hover" @click="handleAction(action.route)">
            <div
              class="action-icon"
              :style="{ backgroundColor: action.color + '20', color: action.color }"
            >
              <el-icon :size="32">
                <component :is="action.icon" />
              </el-icon>
            </div>
            <h4>{{ action.title }}</h4>
            <p>{{ action.desc }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 最近查询和常用连接 -->
    <el-row :gutter="20" class="data-row">
      <!-- 最近查询 -->
      <el-col :xs="24" :md="14">
        <el-card class="data-card" v-loading="loading.queries">
          <template #header>
            <div class="card-header">
              <span>最近查询</span>
              <el-link type="primary" @click="router.push('/history')">查看全部</el-link>
            </div>
          </template>
          <div v-if="recentQueries.length === 0" class="empty-data">
            <el-empty description="暂无查询记录" :image-size="80" />
          </div>
          <div v-else class="query-list">
            <div
              v-for="query in recentQueries"
              :key="query.id"
              class="query-item"
              @click="viewQueryDetail(query)"
            >
              <div class="query-main">
                <div class="question">{{ truncateText(query.question, 30) }}</div>
                <div class="sql">{{ truncateText(query.sql, 40) }}</div>
              </div>
              <div class="query-meta">
                <el-tag :type="getStatusType(query.execution_status)" size="small">
                  {{ query.execution_status === 'success' ? '成功' : '失败' }}
                </el-tag>
                <span class="time">{{ formatTime(query.created_at) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 常用连接 -->
      <el-col :xs="24" :md="10">
        <el-card class="data-card" v-loading="loading.connections">
          <template #header>
            <div class="card-header">
              <span>数据库连接</span>
              <el-link type="primary" @click="viewConnections">管理连接</el-link>
            </div>
          </template>
          <div v-if="recentConnections.length === 0" class="empty-data">
            <el-empty description="暂无活跃连接" :image-size="80">
              <el-button type="primary" size="small" @click="viewConnections">添加连接</el-button>
            </el-empty>
          </div>
          <div v-else class="connection-list">
            <div
              v-for="conn in recentConnections"
              :key="conn.id"
              class="connection-item"
              @click="router.push('/query')"
            >
              <div class="connection-icon">
                <el-icon :size="20"><Connection /></el-icon>
              </div>
              <div class="connection-info">
                <div class="connection-name">{{ conn.name }}</div>
                <div class="connection-detail">
                  {{ conn.db_type }} | {{ conn.host }}:{{ conn.port }}/{{ conn.database }}
                </div>
              </div>
              <el-tag v-if="conn.status === 'active'" type="success" size="small">正常</el-tag>
              <el-tag v-else-if="conn.status === 'error'" type="danger" size="small">错误</el-tag>
              <el-tag v-else type="info" size="small">未激活</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.home-view {
  .welcome-card {
    margin-bottom: 20px;

    .welcome-content {
      h1 {
        margin: 0 0 16px;
        font-size: 28px;
        color: #303133;
      }

      .welcome-text {
        margin: 0;
        font-size: 16px;
        color: #606266;
        line-height: 1.6;
      }
    }
  }

  .stats-row {
    margin-bottom: 20px;

    .stat-card {
      margin-bottom: 20px;

      .stat-item {
        display: flex;
        align-items: center;
        gap: 16px;

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-info {
          .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #303133;
          }

          .stat-label {
            font-size: 14px;
            color: #909399;
            margin-top: 4px;
          }
        }
      }
    }
  }

  .quick-actions {
    margin-bottom: 20px;

    h3 {
      margin: 0 0 16px;
      font-size: 18px;
      color: #303133;
    }

    .action-col {
      margin-bottom: 20px;
    }

    .action-card {
      cursor: pointer;
      text-align: center;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
      }

      .action-icon {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
      }

      h4 {
        margin: 0 0 8px;
        font-size: 16px;
        color: #303133;
      }

      p {
        margin: 0;
        font-size: 14px;
        color: #909399;
      }
    }
  }

  .data-row {
    margin-bottom: 20px;

    .data-card {
      margin-bottom: 20px;
      min-height: 300px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 16px;
        font-weight: bold;
        color: #303133;
      }

      .empty-data {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 200px;
      }

      .query-list {
        .query-item {
          padding: 12px 0;
          border-bottom: 1px solid #ebeef5;
          cursor: pointer;
          transition: background-color 0.2s;

          &:last-child {
            border-bottom: none;
          }

          &:hover {
            background-color: #f5f7fa;
          }

          .query-main {
            margin-bottom: 8px;

            .question {
              font-size: 14px;
              color: #303133;
              font-weight: 500;
              margin-bottom: 4px;
            }

            .sql {
              font-size: 12px;
              color: #909399;
              font-family: monospace;
              background-color: #f5f7fa;
              padding: 4px 8px;
              border-radius: 4px;
            }
          }

          .query-meta {
            display: flex;
            align-items: center;
            gap: 12px;

            .time {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }

      .connection-list {
        .connection-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: 8px;
          cursor: pointer;
          transition: background-color 0.2s;

          &:hover {
            background-color: #f5f7fa;
          }

          .connection-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            background-color: #409eff20;
            color: #409eff;
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .connection-info {
            flex: 1;
            min-width: 0;

            .connection-name {
              font-size: 14px;
              font-weight: 500;
              color: #303133;
              margin-bottom: 4px;
            }

            .connection-detail {
              font-size: 12px;
              color: #909399;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
          }
        }
      }
    }
  }
}
</style>
