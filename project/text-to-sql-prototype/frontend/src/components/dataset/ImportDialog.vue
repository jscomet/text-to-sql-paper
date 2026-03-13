<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import type { ApiKey, DatasetType, EvalMode, ImportConfig } from '@/types'
import { getApiKeys } from '@/api/apiKeys'
import { validateDatasetZip, validateDatasetLocal } from '@/api/dataset'

type ImportType = 'zip' | 'local'

interface FormData {
  importType: ImportType
  // ZIP 上传
  zipFile?: File
  // 本地路径
  localPath: string
  // 通用配置
  dataset_type: DatasetType
  eval_mode: EvalMode
  api_key_id: number | undefined
  temperature: number
  max_tokens: number | undefined
}

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'submit', data: { type: ImportType; file?: File; path?: string; config: ImportConfig }): void
}>()

// ==================== 状态 ====================

const formRef = ref<FormInstance>()
const activeTab = ref<ImportType>('zip')
const loading = ref(false)
const validating = ref(false)

// 表单数据
const formData = reactive<FormData>({
  importType: 'zip',
  localPath: '',
  dataset_type: 'bird',
  eval_mode: 'greedy_search',
  api_key_id: undefined,
  temperature: 0.0,
  max_tokens: undefined,
})

// 上传的文件列表
const fileList = ref<UploadFile[]>([])

// 验证结果
const validationResult = ref<{
  valid: boolean
  message?: string
  db_count?: number
  total_questions?: number
} | null>(null)

// API Keys 列表
const apiKeys = ref<ApiKey[]>([])
const loadingApiKeys = ref(false)

// ==================== 计算属性 ====================

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

const canSubmit = computed(() => {
  if (activeTab.value === 'zip') {
    return formData.zipFile && formData.api_key_id && validationResult.value?.valid
  } else {
    return formData.localPath && formData.api_key_id
  }
})

// ==================== 选项数据 ====================

const datasetOptions = [
  { value: 'bird', label: 'BIRD' },
  { value: 'spider', label: 'Spider' },
  { value: 'custom', label: '自定义数据集' },
]

const evalModeOptions = [
  { value: 'greedy_search', label: '单模型 (Greedy Search)' },
  { value: 'majority_vote', label: '多数投票 (Majority Vote)' },
  { value: 'pass_at_k', label: 'Pass@K' },
  { value: 'check_correct', label: '自检修正 (Check-Correct)' },
]

// ==================== 方法 ====================

// 加载 API Keys
const loadApiKeys = async () => {
  loadingApiKeys.value = true
  try {
    const res = await getApiKeys()
    apiKeys.value = res.list || []
    // 如果有默认的 API Key，自动选择
    const defaultKey = apiKeys.value.find((key) => key.is_default)
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

// 处理标签页切换
const handleTabChange = (tab: ImportType) => {
  activeTab.value = tab
  formData.importType = tab
  validationResult.value = null
}

// 处理文件上传
const handleFileChange = async (uploadFile: UploadFile) => {
  validationResult.value = null

  if (!uploadFile.raw) return

  // 验证文件类型
  const validTypes = ['.zip']
  const fileName = uploadFile.name.toLowerCase()
  const isValidType = validTypes.some((type) => fileName.endsWith(type))

  if (!isValidType) {
    ElMessage.error('请上传 ZIP 格式的文件')
    fileList.value = []
    return
  }

  // 验证文件大小（最大 500MB）
  const maxSize = 500 * 1024 * 1024
  if (uploadFile.size && uploadFile.size > maxSize) {
    ElMessage.error('文件大小不能超过 500MB')
    fileList.value = []
    return
  }

  formData.zipFile = uploadFile.raw

  // 自动验证文件
  await validateZipFile(uploadFile.raw)
}

// 验证 ZIP 文件
const validateZipFile = async (file: File) => {
  validating.value = true
  try {
    const result = await validateDatasetZip(file)
    validationResult.value = result
    if (result.valid) {
      ElMessage.success(`验证通过：包含 ${result.db_count} 个数据库，共 ${result.total_questions} 个问题`)
      // 自动检测数据集类型
      if (result.dataset_type) {
        formData.dataset_type = result.dataset_type as DatasetType
      }
    } else {
      ElMessage.error(result.message || '文件验证失败')
    }
  } catch (error) {
    console.error('验证文件失败:', error)
    ElMessage.error('验证文件失败')
    validationResult.value = { valid: false, message: '验证失败' }
  } finally {
    validating.value = false
  }
}

// 处理文件移除
const handleFileRemove = () => {
  formData.zipFile = undefined
  fileList.value = []
  validationResult.value = null
}

// 验证本地路径
const handleValidatePath = async () => {
  if (!formData.localPath) {
    ElMessage.warning('请输入本地路径')
    return
  }

  validating.value = true
  try {
    const result = await validateDatasetLocal(formData.localPath)
    validationResult.value = result
    if (result.valid) {
      ElMessage.success(`验证通过：包含 ${result.db_count} 个数据库，共 ${result.total_questions} 个问题`)
      // 自动检测数据集类型
      if (result.dataset_type) {
        formData.dataset_type = result.dataset_type as DatasetType
      }
    } else {
      ElMessage.error(result.message || '路径验证失败')
    }
  } catch (error) {
    console.error('验证路径失败:', error)
    ElMessage.error('验证路径失败')
    validationResult.value = { valid: false, message: '验证失败' }
  } finally {
    validating.value = false
  }
}

// 表单验证规则
const rules: FormRules = {
  dataset_type: [{ required: true, message: '请选择数据集类型', trigger: 'change' }],
  eval_mode: [{ required: true, message: '请选择评测模式', trigger: 'change' }],
  api_key_id: [{ required: true, message: '请选择 API Key', trigger: 'change' }],
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (!valid) return

    if (activeTab.value === 'zip' && !formData.zipFile) {
      ElMessage.error('请上传 ZIP 文件')
      return
    }

    if (activeTab.value === 'local' && !formData.localPath) {
      ElMessage.error('请输入本地路径')
      return
    }

    const config: ImportConfig = {
      dataset_type: formData.dataset_type,
      eval_mode: formData.eval_mode,
      api_key_id: formData.api_key_id!,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
    }

    emit('submit', {
      type: activeTab.value,
      file: formData.zipFile,
      path: formData.localPath || undefined,
      config,
    })
  })
}

// 处理取消
const handleCancel = () => {
  dialogVisible.value = false
}

// 重置表单
const resetForm = () => {
  formData.importType = 'zip'
  formData.zipFile = undefined
  formData.localPath = ''
  formData.dataset_type = 'bird'
  formData.eval_mode = 'greedy_search'
  formData.api_key_id = undefined
  formData.temperature = 0.0
  formData.max_tokens = undefined
  fileList.value = []
  validationResult.value = null
  activeTab.value = 'zip'
  formRef.value?.resetFields()
}

// 监听对话框显示
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      resetForm()
      loadApiKeys()
    }
  }
)
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="导入数据集"
    width="700px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="import-tabs">
      <!-- ZIP 上传标签页 -->
      <el-tab-pane label="ZIP 上传" name="zip">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-width="120px"
          class="import-form"
        >
          <!-- 文件上传 -->
          <el-form-item label="数据集文件" required>
            <el-upload
              v-model:file-list="fileList"
              action="#"
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              accept=".zip"
              drag
              class="upload-area"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 ZIP 格式，文件大小不超过 500MB
                </div>
              </template>
            </el-upload>
          </el-form-item>

          <!-- 验证结果 -->
          <el-form-item v-if="validationResult" label="验证结果">
            <el-alert
              :title="validationResult.valid ? '验证通过' : '验证失败'"
              :type="validationResult.valid ? 'success' : 'error'"
              :description="validationResult.message"
              :closable="false"
              show-icon
            >
              <template v-if="validationResult.valid && validationResult.db_count" #default>
                <div class="validation-detail">
                  数据库数量: {{ validationResult.db_count }} |
                  问题总数: {{ validationResult.total_questions }}
                </div>
              </template>
            </el-alert>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 本地路径标签页 -->
      <el-tab-pane label="本地路径" name="local">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-width="120px"
          class="import-form"
        >
          <!-- 本地路径输入 -->
          <el-form-item label="数据集路径" required>
            <el-input
              v-model="formData.localPath"
              placeholder="请输入数据集的绝对路径，如 /path/to/bird/dataset"
              clearable
            >
              <template #append>
                <el-button @click="handleValidatePath" :loading="validating">
                  验证
                </el-button>
              </template>
            </el-input>
            <div class="input-hint">支持 BIRD、Spider 等标准数据集格式</div>
          </el-form-item>

          <!-- 验证结果 -->
          <el-form-item v-if="validationResult" label="验证结果">
            <el-alert
              :title="validationResult.valid ? '验证通过' : '验证失败'"
              :type="validationResult.valid ? 'success' : 'error'"
              :description="validationResult.message"
              :closable="false"
              show-icon
            >
              <template v-if="validationResult.valid && validationResult.db_count" #default>
                <div class="validation-detail">
                  数据库数量: {{ validationResult.db_count }} |
                  问题总数: {{ validationResult.total_questions }}
                </div>
              </template>
            </el-alert>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- 通用配置表单 -->
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      class="import-form"
    >
      <el-divider content-position="left">导入配置</el-divider>

      <!-- 数据集类型 -->
      <el-form-item label="数据集类型" prop="dataset_type">
        <el-select v-model="formData.dataset_type" placeholder="请选择数据集类型" style="width: 100%">
          <el-option
            v-for="option in datasetOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>

      <!-- 评测模式 -->
      <el-form-item label="评测模式" prop="eval_mode">
        <el-select v-model="formData.eval_mode" placeholder="请选择评测模式" style="width: 100%">
          <el-option
            v-for="mode in evalModeOptions"
            :key="mode.value"
            :label="mode.label"
            :value="mode.value"
          />
        </el-select>
      </el-form-item>

      <!-- API Key 选择 -->
      <el-form-item label="API Key" prop="api_key_id">
        <el-select
          v-model="formData.api_key_id"
          placeholder="请选择 API Key"
          style="width: 100%"
          :loading="loadingApiKeys"
        >
          <el-option
            v-for="key in apiKeys"
            :key="key.id"
            :label="key.provider + (key.is_default ? ' (默认)' : '')"
            :value="key.id"
          >
            <span>{{ key.provider }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">
              {{ key.model || key.format_type }}
            </span>
          </el-option>
        </el-select>
        <div v-if="apiKeys.length === 0 && !loadingApiKeys" class="api-key-hint">
          <el-link type="primary" @click="$router.push('/settings')">
            还没有 API Key，去设置页面添加
          </el-link>
        </div>
      </el-form-item>

      <!-- Temperature -->
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
          <el-tooltip content="控制输出的随机性，0 表示最确定，越高越随机" placement="top">
            <el-icon class="help-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </el-form-item>

      <!-- Max Tokens -->
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
        style="margin-top: 20px; margin-left: 120px"
      />
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button
          type="primary"
          :disabled="!canSubmit"
          :loading="loading"
          @click="handleSubmit"
        >
          <el-icon class="el-icon--left"><Upload /></el-icon>
          开始导入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.import-tabs {
  margin-bottom: 20px;
}

.import-form {
  :deep(.el-form-item__label) {
    font-weight: 500;
  }
}

.upload-area {
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 150px;
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

.input-hint {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.api-key-hint {
  margin-top: 8px;
  font-size: 12px;
}

.validation-detail {
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
}
</style>
