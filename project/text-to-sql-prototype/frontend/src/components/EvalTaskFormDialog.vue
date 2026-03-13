<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import type { Connection, ApiKey } from '@/types'
import { getApiKeys } from '@/api/apiKeys'

interface FormData {
  name: string
  connection_id: number | undefined
  dataset_type: string
  dataset_file?: File
  api_key_id: number | undefined
  temperature: number
  max_tokens: number | undefined
  eval_mode: string
}

const props = defineProps<{
  visible: boolean
  connections: Connection[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (
    e: 'submit',
    data: {
      name: string
      connection_id: number
      dataset_type: string
      dataset_file?: File
      api_key_id: number
      temperature: number
      max_tokens?: number
      eval_mode: string
    }
  ): void
}>()

const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<FormData>({
  name: '',
  connection_id: undefined,
  dataset_type: 'spider',
  api_key_id: undefined,
  temperature: 0.0,
  max_tokens: undefined,
  eval_mode: 'greedy_search',
})

// API Keys 列表
const apiKeys = ref<ApiKey[]>([])
const loadingApiKeys = ref(false)

// 上传的文件列表
const fileList = ref<UploadFile[]>([])

// 是否显示文件上传
const showFileUpload = computed(() => formData.dataset_type === 'custom')

// 数据集选项
const datasetOptions = [
  { value: 'spider', label: 'Spider' },
  { value: 'bird', label: 'BIRD' },
  { value: 'custom', label: '自定义数据集' },
]

// 加载 API Keys
const loadApiKeys = async () => {
  loadingApiKeys.value = true
  try {
    const res = await getApiKeys()
    apiKeys.value = res.list || []
    // 如果有默认的 API Key，自动选择
    const defaultKey = apiKeys.value.find(key => key.is_default)
    if (defaultKey) {
      formData.api_key_id = defaultKey.id
    }
  } catch (error) {
    console.error('加载 API Keys 失败:', error)
    ElMessage.error('加载 API Keys 失败')
  } finally {
    loadingApiKeys.value = false
  }
}

// 评测模式选项
const evalModeOptions = [
  { value: 'greedy_search', label: '单模型 (Greedy Search)' },
  { value: 'major_voting', label: '多数投票 (Major Voting)' },
  { value: 'pass@k', label: 'Pass@k' },
]

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入评测名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' },
  ],
  connection_id: [
    { required: true, message: '请选择数据库连接', trigger: 'change' },
  ],
  dataset_type: [
    { required: true, message: '请选择数据集类型', trigger: 'change' },
  ],
  api_key_id: [
    { required: true, message: '请选择 API Key', trigger: 'change' },
  ],
  eval_mode: [
    { required: true, message: '请选择评测模式', trigger: 'change' },
  ],
}

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

// 监听对话框显示状态，重置表单并加载 API Keys
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      resetForm()
      loadApiKeys()
    }
  }
)

// 监听数据集类型变化，清空文件
watch(
  () => formData.dataset_type,
  (newVal) => {
    if (newVal !== 'custom') {
      formData.dataset_file = undefined
      fileList.value = []
    }
  }
)

// 重置表单
const resetForm = () => {
  formData.name = ''
  formData.connection_id = undefined
  formData.dataset_type = 'spider'
  formData.dataset_file = undefined
  formData.api_key_id = undefined
  formData.temperature = 0.0
  formData.max_tokens = undefined
  formData.eval_mode = 'greedy_search'
  fileList.value = []
  formRef.value?.resetFields()
}

// 处理文件上传
const handleFileChange = (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    // 验证文件类型
    const validTypes = ['.json', '.jsonl', '.zip']
    const fileName = uploadFile.name.toLowerCase()
    const isValidType = validTypes.some((type) => fileName.endsWith(type))

    if (!isValidType) {
      ElMessage.error('请上传 JSON、JSONL 或 ZIP 格式的文件')
      fileList.value = []
      return
    }

    // 验证文件大小（最大 100MB）
    const maxSize = 100 * 1024 * 1024
    if (uploadFile.size && uploadFile.size > maxSize) {
      ElMessage.error('文件大小不能超过 100MB')
      fileList.value = []
      return
    }

    formData.dataset_file = uploadFile.raw
  }
}

// 处理文件移除
const handleFileRemove = () => {
  formData.dataset_file = undefined
  fileList.value = []
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (valid) {
      // 验证自定义数据集是否上传了文件
      if (formData.dataset_type === 'custom' && !formData.dataset_file) {
        ElMessage.error('请上传自定义数据集文件')
        return
      }

      emit('submit', {
        name: formData.name,
        connection_id: formData.connection_id as number,
        dataset_type: formData.dataset_type,
        dataset_file: formData.dataset_file,
        api_key_id: formData.api_key_id as number,
        temperature: formData.temperature,
        max_tokens: formData.max_tokens,
        eval_mode: formData.eval_mode,
      })
    }
  })
}

// 处理取消
const handleCancel = () => {
  dialogVisible.value = false
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="新建评测任务"
    width="600px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      class="eval-form"
    >
      <!-- 评测名称 -->
      <el-form-item label="评测名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入评测名称" clearable />
      </el-form-item>

      <!-- 数据库连接 -->
      <el-form-item label="数据库连接" prop="connection_id">
        <el-select
          v-model="formData.connection_id"
          placeholder="请选择数据库连接"
          style="width: 100%"
          clearable
        >
          <el-option
            v-for="conn in connections"
            :key="conn.id"
            :label="conn.name"
            :value="conn.id"
          >
            <span>{{ conn.name }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">
              {{ conn.db_type }}
            </span>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 数据集类型 -->
      <el-form-item label="数据集类型" prop="dataset_type">
        <el-radio-group v-model="formData.dataset_type">
          <el-radio-button
            v-for="option in datasetOptions"
            :key="option.value"
            :label="option.value"
          >
            {{ option.label }}
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- 自定义数据集文件上传 -->
      <el-form-item
        v-if="showFileUpload"
        label="数据集文件"
        :rules="[
          {
            required: showFileUpload,
            message: '请上传数据集文件',
            trigger: 'change',
          },
        ]"
      >
        <el-upload
          v-model:file-list="fileList"
          action="#"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          accept=".json,.jsonl,.zip"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            选择文件
          </el-button>
          <template #tip>
            <div class="el-upload__tip">
              支持 JSON、JSONL、ZIP 格式，文件大小不超过 100MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <!-- API Key 选择 -->
      <el-form-item label="API Key" prop="api_key_id">
        <el-select
          v-model="formData.api_key_id"
          placeholder="请选择 API Key"
          style="width: 100%"
          clearable
          :loading="loadingApiKeys"
        >
          <el-option
            v-for="key in apiKeys"
            :key="key.id"
            :label="key.name + (key.is_default ? ' (默认)' : '')"
            :value="key.id"
          >
            <span>{{ key.name }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">
              {{ key.key_type }}
            </span>
          </el-option>
        </el-select>
        <div v-if="apiKeys.length === 0 && !loadingApiKeys" class="api-key-hint">
          <el-link type="primary" @click="$router.push('/settings')">
            还没有 API Key，去设置页面添加
          </el-link>
        </div>
      </el-form-item>

      <!-- 评测模式 -->
      <el-form-item label="评测模式" prop="eval_mode">
        <el-select
          v-model="formData.eval_mode"
          placeholder="请选择评测模式"
          style="width: 100%"
        >
          <el-option
            v-for="mode in evalModeOptions"
            :key="mode.value"
            :label="mode.label"
            :value="mode.value"
          />
        </el-select>
      </el-form-item>

      <!-- Temperature 滑块 -->
      <el-form-item label="Temperature">
        <div class="slider-wrapper">
          <el-slider
            v-model="formData.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            show-input
            :show-input-controls="false"
          />
          <el-tooltip
            content="控制输出的随机性，0 表示最确定，越高越随机"
            placement="top"
          >
            <el-icon class="help-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </el-form-item>

      <!-- Max Tokens 输入 -->
      <el-form-item label="Max Tokens">
        <el-input-number
          v-model="formData.max_tokens"
          :min="1"
          :max="8192"
          :step="1"
          placeholder="不限制"
          style="width: 100%"
        />
        <div class="input-hint">留空表示不限制最大 token 数</div>
      </el-form-item>

      <!-- 提示信息 -->
      <el-alert
        v-if="formData.eval_mode !== 'greedy_search'"
        :title="`当前选择 ${evalModeOptions.find((m) => m.value === formData.eval_mode)?.label} 模式，将消耗更多 API 调用次数`"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 20px; margin-left: 120px"
      />
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          <el-icon class="el-icon--left"><VideoPlay /></el-icon>
          开始评测
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.eval-form {
  :deep(.el-form-item__label) {
    font-weight: 500;
  }
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;

  :deep(.el-slider) {
    flex: 1;
  }

  :deep(.el-input-number) {
    width: 80px;
  }
}

.help-icon {
  color: #909399;
  cursor: help;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-upload__tip) {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.api-key-hint {
  margin-top: 8px;
  font-size: 12px;
}

.input-hint {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}
</style>
