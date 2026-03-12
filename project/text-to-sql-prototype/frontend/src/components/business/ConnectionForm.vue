<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

export interface ConnectionFormData {
  name: string
  db_type: 'mysql' | 'postgresql' | 'sqlite' | 'mssql'
  host: string
  port: number
  database: string
  username: string
  password: string
  description?: string
}

interface Props {
  modelValue: ConnectionFormData
  loading?: boolean
  isEdit?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  isEdit: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: ConnectionFormData): void
  (e: 'submit'): void
  (e: 'test'): void
  (e: 'cancel'): void
}>()

const formRef = ref<FormInstance>()

const defaultPorts: Record<string, number> = {
  mysql: 3306,
  postgresql: 5432,
  sqlite: 0,
  mssql: 1433,
}

const rules: FormRules = {
  name: [
    { required: true, message: '请输入连接名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  db_type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围 1-65535', trigger: 'blur' },
  ],
  database: [{ required: true, message: '请输入数据库名', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const dbTypeOptions = [
  { label: 'MySQL', value: 'mysql' },
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'SQLite', value: 'sqlite' },
  { label: 'SQL Server', value: 'mssql' },
]

const isSQLite = computed(() => props.modelValue.db_type === 'sqlite')

watch(
  () => props.modelValue.db_type,
  (newType) => {
    if (newType && defaultPorts[newType]) {
      emit('update:modelValue', {
        ...props.modelValue,
        port: defaultPorts[newType],
      })
    }
  }
)

const updateField = <K extends keyof ConnectionFormData>(field: K, value: ConnectionFormData[K]) => {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate((valid) => {
    if (valid) {
      emit('submit')
    }
  })
}

const handleTest = async () => {
  if (!formRef.value) return
  await formRef.value.validate((valid) => {
    if (valid) {
      emit('test')
    }
  })
}

const handleCancel = () => {
  emit('cancel')
}

const resetForm = () => {
  formRef.value?.resetFields()
}

defineExpose({
  resetForm,
  validate: () => formRef.value?.validate(),
})
</script>

<template>
  <el-form ref="formRef" :model="modelValue" :rules="rules" label-width="100px" class="connection-form">
    <el-form-item label="连接名称" prop="name">
      <el-input
        :model-value="modelValue.name"
        placeholder="请输入连接名称"
        maxlength="50"
        show-word-limit
        @update:model-value="(val: string) => updateField('name', val)"
      />
    </el-form-item>

    <el-form-item label="数据库类型" prop="db_type">
      <el-select
        :model-value="modelValue.db_type"
        placeholder="请选择数据库类型"
        style="width: 100%"
        @update:model-value="(val: ConnectionFormData['db_type']) => updateField('db_type', val)"
      >
        <el-option v-for="opt in dbTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>

    <template v-if="!isSQLite">
      <el-row :gutter="16">
        <el-col :span="16">
          <el-form-item label="主机地址" prop="host">
            <el-input
              :model-value="modelValue.host"
              placeholder="例如：localhost 或 127.0.0.1"
              @update:model-value="(val: string) => updateField('host', val)"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="端口" prop="port" label-width="50px">
            <el-input-number
              :model-value="modelValue.port"
              :min="1"
              :max="65535"
              controls-position="right"
              style="width: 100%"
              @update:model-value="(val: number) => updateField('port', val)"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="数据库名" prop="database">
        <el-input
          :model-value="modelValue.database"
          placeholder="请输入数据库名称"
          @update:model-value="(val: string) => updateField('database', val)"
        />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="用户名" prop="username">
            <el-input
              :model-value="modelValue.username"
              placeholder="请输入用户名"
              @update:model-value="(val: string) => updateField('username', val)"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="密码" prop="password">
            <el-input
              :model-value="modelValue.password"
              type="password"
              placeholder="请输入密码"
              show-password
              @update:model-value="(val: string) => updateField('password', val)"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </template>

    <template v-else>
      <el-form-item label="数据库文件" prop="database">
        <el-input
          :model-value="modelValue.database"
          placeholder="请输入SQLite数据库文件路径"
          @update:model-value="(val: string) => updateField('database', val)"
        />
      </el-form-item>
    </template>

    <el-form-item label="描述" prop="description">
      <el-input
        :model-value="modelValue.description"
        type="textarea"
        :rows="3"
        placeholder="请输入连接描述（可选）"
        maxlength="200"
        show-word-limit
        @update:model-value="(val: string) => updateField('description', val)"
      />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ isEdit ? '保存修改' : '创建连接' }}
      </el-button>
      <el-button :disabled="loading" @click="handleTest">
        <el-icon><Connection /></el-icon>测试连接
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<style scoped lang="scss">
.connection-form {
  max-width: 600px;

  :deep(.el-input__wrapper) {
    width: 100%;
  }
}
</style>
