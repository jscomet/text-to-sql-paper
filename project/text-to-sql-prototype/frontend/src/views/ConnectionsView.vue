<script setup lang="ts">
import { ref } from 'vue'

// 连接列表
interface Connection {
  id: number
  name: string
  host: string
  port: number
  database: string
  username: string
  password?: string
  status: 'connected' | 'disconnected' | 'error'
  createdAt: string
}

const connections = ref<Connection[]>([
  {
    id: 1,
    name: '本地 MySQL',
    host: 'localhost',
    port: 3306,
    database: 'test_db',
    username: 'root',
    status: 'connected',
    createdAt: '2024-01-15 10:30:00',
  },
])

// 对话框显示状态
const dialogVisible = ref(false)
const isEdit = ref(false)

// 表单数据
const formData = ref<Partial<Connection>>({
  name: '',
  host: '',
  port: 3306,
  database: '',
  username: '',
})

// 处理添加连接
const handleAdd = () => {
  isEdit.value = false
  formData.value = {
    name: '',
    host: '',
    port: 3306,
    database: '',
    username: '',
  }
  dialogVisible.value = true
}

// 处理编辑连接
const handleEdit = (row: Connection) => {
  isEdit.value = true
  formData.value = { ...row }
  dialogVisible.value = true
}

// 处理删除连接
const handleDelete = (row: Connection) => {
  // TODO: 调用后端 API 删除连接
  console.log('删除连接:', row.id)
  connections.value = connections.value.filter((item) => item.id !== row.id)
}

// 处理测试连接
const handleTest = async (row: Connection) => {
  // TODO: 调用后端 API 测试连接
  console.log('测试连接:', row.id)
}

// 处理提交表单
const handleSubmit = async () => {
  // TODO: 调用后端 API 保存连接
  console.log('保存连接:', formData.value)
  dialogVisible.value = false
}

// 获取状态标签类型
const getStatusType = (status: Connection['status']) => {
  const typeMap: Record<string, string> = {
    connected: 'success',
    disconnected: 'info',
    error: 'danger',
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: Connection['status']) => {
  const textMap: Record<string, string> = {
    connected: '已连接',
    disconnected: '未连接',
    error: '连接错误',
  }
  return textMap[status] || '未知'
}
</script>

<template>
  <div class="connections-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>数据库连接管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon class="el-icon--left"><Plus /></el-icon>
            添加连接
          </el-button>
        </div>
      </template>

      <el-table :data="connections" style="width: 100%" border>
        <el-table-column prop="name" label="连接名称" min-width="150" />
        <el-table-column prop="host" label="主机" min-width="150" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="database" label="数据库" min-width="150" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleTest(row)">
              测试
            </el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-popconfirm
              title="确定删除该连接吗？"
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
      <el-empty v-if="connections.length === 0" description="暂无数据库连接" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑连接' : '添加连接'"
      width="500px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="连接名称" required>
          <el-input v-model="formData.name" placeholder="请输入连接名称" />
        </el-form-item>
        <el-form-item label="主机地址" required>
          <el-input v-model="formData.host" placeholder="例如: localhost" />
        </el-form-item>
        <el-form-item label="端口" required>
          <el-input-number v-model="formData.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="数据库" required>
          <el-input v-model="formData.database" placeholder="请输入数据库名" />
        </el-form-item>
        <el-form-item label="用户名" required>
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
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
.connections-page {
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
</style>
