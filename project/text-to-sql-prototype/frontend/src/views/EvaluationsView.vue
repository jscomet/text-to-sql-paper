<script setup lang="ts">
import { ref } from 'vue'

// 评测任务列表
interface EvaluationTask {
  id: number
  name: string
  datasetName: string
  modelName: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  accuracy: number | null
  createdAt: string
  completedAt: string | null
}

const evaluationList = ref<EvaluationTask[]>([
  {
    id: 1,
    name: 'Spider 数据集评测',
    datasetName: 'spider',
    modelName: 'gpt-4',
    status: 'completed',
    accuracy: 0.856,
    createdAt: '2024-01-15 10:00:00',
    completedAt: '2024-01-15 10:30:00',
  },
])

// 对话框显示状态
const dialogVisible = ref(false)

// 表单数据
const formData = ref({
  name: '',
  datasetId: '',
  connectionId: '',
})

// 数据集选项
const datasetOptions = ref([
  { value: 'spider', label: 'Spider' },
  { value: 'bird', label: 'BIRD' },
  { value: 'custom', label: '自定义数据集' },
])

// 连接选项
const connectionOptions = ref([
  { value: '1', label: '本地 MySQL' },
])

// 处理新建评测
const handleCreate = () => {
  formData.value = {
    name: '',
    datasetId: '',
    connectionId: '',
  }
  dialogVisible.value = true
}

// 处理查看结果
const handleViewResult = (row: EvaluationTask) => {
  // TODO: 显示评测结果详情
  console.log('查看结果:', row.id)
}

// 处理删除
const handleDelete = (row: EvaluationTask) => {
  // TODO: 调用后端 API 删除评测任务
  console.log('删除:', row.id)
  evaluationList.value = evaluationList.value.filter((item) => item.id !== row.id)
}

// 处理提交表单
const handleSubmit = async () => {
  // TODO: 调用后端 API 创建评测任务
  console.log('创建评测:', formData.value)
  dialogVisible.value = false
}

// 获取状态标签类型
const getStatusType = (status: EvaluationTask['status']) => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: EvaluationTask['status']) => {
  const textMap: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
  }
  return textMap[status] || '未知'
}
</script>

<template>
  <div class="evaluations-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>评测管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon class="el-icon--left"><Plus /></el-icon>
            新建评测
          </el-button>
        </div>
      </template>

      <el-table :data="evaluationList" style="width: 100%" border>
        <el-table-column prop="name" label="评测名称" min-width="200" />
        <el-table-column prop="datasetName" label="数据集" width="150" />
        <el-table-column prop="modelName" label="模型" width="150" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="accuracy" label="准确率" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.accuracy !== null" :class="{ 'high-accuracy': row.accuracy >= 0.8 }">
              {{ (row.accuracy * 100).toFixed(1) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" min-width="180" />
        <el-table-column prop="completedAt" label="完成时间" min-width="180">
          <template #default="{ row }">
            {{ row.completedAt || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :disabled="row.status !== 'completed'"
              @click="handleViewResult(row)"
            >
              查看结果
            </el-button>
            <el-popconfirm
              title="确定删除该评测任务吗？"
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

      <!-- 空状态 -->
      <el-empty v-if="evaluationList.length === 0" description="暂无评测任务" />
    </el-card>

    <!-- 新建评测对话框 -->
    <el-dialog v-model="dialogVisible" title="新建评测任务" width="500px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="评测名称" required>
          <el-input v-model="formData.name" placeholder="请输入评测名称" />
        </el-form-item>
        <el-form-item label="数据集" required>
          <el-select v-model="formData.datasetId" placeholder="请选择数据集" style="width: 100%">
            <el-option
              v-for="item in datasetOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据库连接" required>
          <el-select
            v-model="formData.connectionId"
            placeholder="请选择数据库连接"
            style="width: 100%"
          >
            <el-option
              v-for="item in connectionOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.evaluations-page {
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

.high-accuracy {
  color: #67c23a;
  font-weight: bold;
}
</style>
