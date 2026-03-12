<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Connection } from '@element-plus/icons-vue'
import type { Connection as ConnectionType, CreateConnectionRequest, UpdateConnectionRequest } from '@/types'
import { testConnection, type TestConnectionParams } from '@/api/connections'

interface Props {
  visible: boolean
  isEdit?: boolean
  connection?: ConnectionType | null
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  isEdit: false,
  connection: null,
})

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'submit', data: CreateConnectionRequest | UpdateConnectionRequest): void
}>()

// 表单引用
const formRef = ref<FormInstance>()

// 测试连接加载状态
const testLoading = ref(false)

// 提交加载状态
const submitLoading = ref(false)

// 数据库类型选项
const dbTypeOptions = [
  { label: 'MySQL', value: 'mysql' },
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'SQLite', value: 'sqlite' },
  { label: 'SQL Server', value: 'sqlserver' },
  { label: 'Oracle', value: 'oracle' },
]

// 默认端口映射
const defaultPorts: Record<string, number> = {
  mysql: 3306,
  postgresql: 5432,
  sqlite: 0,
  sqlserver: 1433,
  oracle: 1521,
}

// 表单数据
const formData = reactive<CreateConnectionRequest>({
  name: '',
  db_type: 'mysql',
  host: '',
  port: 3306,
  database: '',
  username: '',
  password: '',
})

// 是否为 SQLite
const isSQLite = computed(() => formData.db_type === 'sqlite')

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入连接名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  db_type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
  host: [
    {
      required: true,
      message: '请输入主机地址',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (!isSQLite.value && !value) {
          callback(new Error('请输入主机地址'))
        } else {
          callback()
        }
      },
    },
  ],
  port: [
    {
      required: true,
      message: '请输入端口号',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (!isSQLite.value) {
          if (!value || value < 1 || value > 65535) {
            callback(new Error('端口号范围 1-65535'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
    },
  ],
  database: [{ required: true, message: '请输入数据库名', trigger: 'blur' }],
  username: [
    {
      required: true,
      message: '请输入用户名',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (!isSQLite.value && !value) {
          callback(new Error('请输入用户名'))
        } else {
          callback()
        }
      },
    },
  ],
  password: [{ required: !props.isEdit, message: '请输入密码', trigger: 'blur' }],
}

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      if (props.isEdit && props.connection) {
        // 编辑模式：填充表单数据
        formData.name = props.connection.name
        formData.db_type = props.connection.db_type
        formData.host = props.connection.host || ''
        formData.port = props.connection.port || 3306
        formData.database = props.connection.database
        formData.username = props.connection.username || ''
        formData.password = '' // 编辑时密码为空，表示不修改
      } else {
        // 新增模式：重置表单
        resetForm()
      }
    }
  }
)

// 监听数据库类型变化，自动设置默认端口
watch(
  () => formData.db_type,
  (newType) => {
    if (newType && defaultPorts[newType] !== undefined && !props.isEdit) {
      formData.port = defaultPorts[newType]
    }
  }
)

// 重置表单
const resetForm = () => {
  formData.name = ''
  formData.db_type = 'mysql'
  formData.host = ''
  formData.port = 3306
  formData.database = ''
  formData.username = ''
  formData.password = ''
  formRef.value?.resetFields()
}

// 关闭对话框
const handleClose = () => {
  emit('update:visible', false)
}

// 处理测试连接
const handleTest = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  testLoading.value = true
  try {
    const testData: TestConnectionParams = {
      db_type: formData.db_type,
      host: formData.host,
      port: formData.port,
      database: formData.database,
      username: formData.username,
      password: formData.password,
    }

    const res = await testConnection(testData)

    if (res.connected) {
      ElMessage.success(`连接成功${res.server_version ? ` (${res.server_version})` : ''}`)
    } else {
      ElMessage.error(res.message || '连接失败')
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : '测试连接失败'
    ElMessage.error(message)
  } finally {
    testLoading.value = false
  }
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    // 构建提交数据
    const submitData: CreateConnectionRequest | UpdateConnectionRequest = {
      name: formData.name,
      db_type: formData.db_type,
      host: formData.host,
      port: formData.port,
      database: formData.database,
      username: formData.username,
    }

    // 只有输入了密码才提交（编辑模式下密码为空表示不修改）
    if (formData.password) {
      (submitData as CreateConnectionRequest).password = formData.password
    }

    // SQLite 特殊处理
    if (isSQLite.value) {
      submitData.host = ''
      submitData.port = 0
      submitData.username = ''
    }

    emit('submit', submitData)
  } finally {
    submitLoading.value = false
  }
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑连接' : '添加连接'"
    width="560px"
    :close-on-click-modal="false"
    :destroy-on-close="true"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      class="connection-form"
    >
      <!-- 连接名称 -->
      <el-form-item label="连接名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入连接名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <!-- 数据库类型 -->
      <el-form-item label="数据库类型" prop="db_type">
        <el-select v-model="formData.db_type" placeholder="请选择数据库类型" style="width: 100%">
          <el-option
            v-for="opt in dbTypeOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </el-form-item>

      <!-- 非 SQLite 的字段 -->
      <template v-if="!isSQLite">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="主机地址" prop="host">
              <el-input v-model="formData.host" placeholder="例如：localhost 或 127.0.0.1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="端口" prop="port" label-width="50px">
              <el-input-number
                v-model="formData.port"
                :min="1"
                :max="65535"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="数据库名" prop="database">
          <el-input v-model="formData.database" placeholder="请输入数据库名称" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="formData.username" placeholder="请输入用户名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="formData.password"
                type="password"
                placeholder="请输入密码"
                show-password
              />
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- SQLite 专用字段 -->
      <template v-else>
        <el-form-item label="数据库文件" prop="database">
          <el-input
            v-model="formData.database"
            placeholder="请输入 SQLite 数据库文件路径，例如：/path/to/database.db"
          />
        </el-form-item>
      </template>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button :loading="testLoading" @click="handleTest">
          <el-icon v-if="!testLoading"><Connection /></el-icon>
          测试连接
        </el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '创建连接' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.connection-form {
  :deep(.el-input__wrapper) {
    width: 100%;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
