<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const username = computed(() => userStore.userInfo?.username || '用户')

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

const handleAction = (route: string) => {
  router.push(route)
}
</script>

<template>
  <div class="home-view">
    <!-- 欢迎区域 -->
    <el-card class="welcome-card">
      <div class="welcome-content">
        <h1>欢迎使用 Text2SQL 👋</h1>
        <p class="welcome-text">
          你好，<strong>{{ username }}</strong>！Text2SQL 是一个智能文本转SQL查询系统，
          帮助您通过自然语言快速生成SQL查询语句。
        </p>
      </div>
    </el-card>

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
          <el-card
            class="action-card"
            shadow="hover"
            @click="handleAction(action.route)"
          >
            <div class="action-icon" :style="{ backgroundColor: action.color + '20', color: action.color }">
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

    <!-- 系统介绍 -->
    <el-card class="intro-card">
      <template #header>
        <div class="card-header">
          <span>系统功能</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8">
          <div class="feature-item">
            <el-icon :size="40" color="#409eff"><ChatDotRound /></el-icon>
            <h4>自然语言转SQL</h4>
            <p>输入自然语言描述，系统自动生成对应的SQL查询语句</p>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <div class="feature-item">
            <el-icon :size="40" color="#67c23a"><Connection /></el-icon>
            <h4>多数据库支持</h4>
            <p>支持MySQL、PostgreSQL、SQLite等多种数据库连接</p>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <div class="feature-item">
            <el-icon :size="40" color="#e6a23c"><TrendCharts /></el-icon>
            <h4>SQL质量评测</h4>
            <p>对生成的SQL进行准确性、可读性等多维度评测</p>
          </div>
        </el-col>
      </el-row>
    </el-card>
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

  .intro-card {
    .card-header {
      font-size: 16px;
      font-weight: bold;
      color: #303133;
    }

    .feature-item {
      text-align: center;
      padding: 20px;

      h4 {
        margin: 16px 0 8px;
        font-size: 16px;
        color: #303133;
      }

      p {
        margin: 0;
        font-size: 14px;
        color: #606266;
        line-height: 1.5;
      }
    }
  }
}
</style>
