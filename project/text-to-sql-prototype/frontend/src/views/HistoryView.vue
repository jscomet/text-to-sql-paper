<script setup lang="ts">
import { ref } from 'vue'

// 历史记录列表
interface HistoryItem {
  id: number
  question: string
  sql: string
  database: string
  status: 'success' | 'failed' | 'pending'
  executionTime: number
  createdAt: string
}

const historyList = ref<HistoryItem[]>([
  {
    id: 1,
    question: '查询最近30天内销售额排名前10的商品',
    sql: 'SELECT * FROM products ORDER BY sales DESC LIMIT 10;',
    database: 'test_db',
    status: 'success',
    executionTime: 125,
    createdAt: '2024-01-15 14:30:25',
  },
])

// 搜索关键词
const searchKeyword = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(100)

// 处理搜索
const handleSearch = () => {
  // TODO: 调用后端 API 搜索历史记录
  console.log('搜索:', searchKeyword.value)
}

// 处理查看详情
const handleView = (row: HistoryItem) => {
  // TODO: 显示详情对话框
  console.log('查看详情:', row.id)
}

// 处理重新执行
const handleReexecute = (row: HistoryItem) => {
  // TODO: 重新执行该查询
  console.log('重新执行:', row.id)
}

// 处理删除
const handleDelete = (row: HistoryItem) => {
  // TODO: 调用后端 API 删除历史记录
  console.log('删除:', row.id)
  historyList.value = historyList.value.filter((item) => item.id !== row.id)
}

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  // TODO: 加载对应页数据
}

// 获取状态标签类型
const getStatusType = (status: HistoryItem['status']) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    pending: 'warning',
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: HistoryItem['status']) => {
  const textMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    pending: '执行中',
  }
  return textMap[status] || '未知'
}
</script>

<template>
  <div class="history-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>查询历史</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索问题或SQL"
              style="width: 250px"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="handleSearch">
              <el-icon class="el-icon--left"><Search /></el-icon>
              搜索
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="historyList" style="width: 100%" border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="question" label="问题" min-width="250" show-overflow-tooltip />
        <el-table-column prop="sql" label="生成的SQL" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="sql-preview">{{ row.sql }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="database" label="数据库" width="120" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executionTime" label="执行时间" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.executionTime">{{ row.executionTime }}ms</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">
              查看
            </el-button>
            <el-button type="primary" link size="small" @click="handleReexecute(row)">
              重新执行
            </el-button>
            <el-popconfirm
              title="确定删除该记录吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
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
        />
      </div>

      <!-- 空状态 -->
      <el-empty v-if="historyList.length === 0" description="暂无查询历史" />
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.history-page {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  span {
    font-weight: bold;
    font-size: 16px;
  }
}

.header-actions {
  display: flex;
  gap: 10px;
}

.sql-preview {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #606266;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
