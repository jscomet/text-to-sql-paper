<script setup lang="ts">
import { computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ref } from 'vue'

/**
 * 推理模式类型
 * 与后端 eval_mode 保持一致: greedy_search|majority_vote|pass_at_k|check_correct
 */
export type InferenceMode = 'greedy_search' | 'majority_vote' | 'pass_at_k' | 'check_correct'

/**
 * 修正策略类型
 * 与后端 correction_strategy 保持一致: none|self_correction|execution_feedback|multi_agent
 */
export type CorrectionStrategy = 'none' | 'self_correction' | 'execution_feedback' | 'multi_agent'

/**
 * 推理配置接口
 */
export interface InferenceConfig {
  /** 推理模式 */
  mode: InferenceMode
  /** majority_vote / pass_at_k 模式的采样次数 (K值) */
  samplingCount?: number
  /** majority_vote / pass_at_k 模式的温度参数 */
  temperature?: number
  /** majority_vote 模式的投票次数 */
  voteCount?: number
  /** Check-Correct 模式的最大迭代次数 */
  maxIterations?: number
  /** Check-Correct 模式的修正策略 */
  correctionStrategy?: CorrectionStrategy
}

interface Props {
  /** v-model 绑定值 */
  modelValue: InferenceConfig
  /** 是否禁用 */
  disabled?: boolean
  /** 标签宽度 */
  labelWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  labelWidth: '120px'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: InferenceConfig): void
}>()

const formRef = ref<FormInstance>()

/** 推理模式选项 */
const modeOptions = [
  { label: 'Greedy Search (贪婪搜索)', value: 'greedy_search', description: '每次选择概率最高的token，生成单一最优结果' },
  { label: 'Majority Vote (多数投票)', value: 'majority_vote', description: '生成多个候选结果，通过多数投票选择最终SQL' },
  { label: 'Pass@K (K次采样评估)', value: 'pass_at_k', description: '生成K个候选结果，评估至少有一个正确的概率' },
  { label: 'Check-Correct (自检修正)', value: 'check_correct', description: '迭代生成-检查-修正循环，直到结果正确或达到最大迭代次数' }
]

/** 修正策略选项 */
const correctionStrategyOptions = [
  { label: '无 (None)', value: 'none', description: '不进行自动修正' },
  { label: '自我修正 (Self Correction)', value: 'self_correction', description: '模型自我检查并修正错误' },
  { label: '执行反馈 (Execution Feedback)', value: 'execution_feedback', description: '基于SQL执行错误反馈进行修正' },
  { label: '多智能体 (Multi Agent)', value: 'multi_agent', description: '多智能体协作修正方案' }
]

/** 默认值配置 - 与后端保持一致 */
const defaultValues: Record<InferenceMode, Partial<InferenceConfig>> = {
  greedy_search: {},
  majority_vote: {
    samplingCount: 5,
    temperature: 0.7,
    voteCount: 5
  },
  pass_at_k: {
    samplingCount: 8,
    temperature: 0.7
  },
  check_correct: {
    maxIterations: 3,
    correctionStrategy: 'self_correction'
  }
}

/** 当前模式 */
const currentMode = computed(() => props.modelValue.mode)

/** 是否显示 Majority Vote 配置 (需要 samplingCount, voteCount, temperature) */
const showMajorityVoteConfig = computed(() => currentMode.value === 'majority_vote')

/** 是否显示 Pass@K 配置 (需要 samplingCount, temperature) */
const showPassAtKConfig = computed(() => currentMode.value === 'pass_at_k')

/** 是否显示 Check-Correct 配置 */
const showCheckCorrectConfig = computed(() => currentMode.value === 'check_correct')

/** 表单验证规则 - 与后端保持一致 */
const rules: FormRules = {
  mode: [{ required: true, message: '请选择推理模式', trigger: 'change' }],
  samplingCount: [
    { required: true, message: '请输入采样次数', trigger: 'blur' },
    { type: 'number', min: 1, max: 16, message: '采样次数范围 1-16', trigger: 'blur' }
  ],
  voteCount: [
    { required: true, message: '请输入投票次数', trigger: 'blur' },
    { type: 'number', min: 3, max: 10, message: '投票次数范围 3-10', trigger: 'blur' }
  ],
  temperature: [
    { required: true, message: '请输入温度参数', trigger: 'blur' },
    { type: 'number', min: 0, max: 2, message: '温度范围 0-2', trigger: 'blur' }
  ],
  maxIterations: [
    { required: true, message: '请输入最大迭代次数', trigger: 'blur' },
    { type: 'number', min: 1, max: 5, message: '迭代次数范围 1-5', trigger: 'blur' }
  ],
  correctionStrategy: [{ required: true, message: '请选择修正策略', trigger: 'change' }]
}

/**
 * 更新字段值
 */
const updateField = <K extends keyof InferenceConfig>(field: K, value: InferenceConfig[K]) => {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

/**
 * 处理模式切换
 * 切换时自动设置对应模式的默认值
 */
const handleModeChange = (newMode: InferenceMode) => {
  const defaults = defaultValues[newMode]
  emit('update:modelValue', {
    mode: newMode,
    ...defaults
  } as InferenceConfig)
}

/**
 * 验证表单
 */
const validate = async (): Promise<boolean> => {
  if (!formRef.value) return false
  return formRef.value.validate((valid) => valid)
}

/**
 * 重置表单
 */
const resetForm = () => {
  formRef.value?.resetFields()
  emit('update:modelValue', {
    mode: 'greedy_search'
  } as InferenceConfig)
}

/**
 * 获取当前配置的描述文本
 */
const getConfigDescription = computed(() => {
  const mode = modeOptions.find(m => m.value === currentMode.value)
  if (!mode) return ''

  let desc = mode.description

  if (showMajorityVoteConfig.value && props.modelValue.samplingCount) {
    desc += ` | K=${props.modelValue.samplingCount}, V=${props.modelValue.voteCount}, T=${props.modelValue.temperature}`
  }

  if (showPassAtKConfig.value && props.modelValue.samplingCount) {
    desc += ` | K=${props.modelValue.samplingCount}, T=${props.modelValue.temperature}`
  }

  if (showCheckCorrectConfig.value && props.modelValue.maxIterations) {
    desc += ` | 最大迭代=${props.modelValue.maxIterations}`
  }

  return desc
})

// 暴露方法给父组件
defineExpose({
  validate,
  resetForm,
  getConfigDescription
})
</script>

<template>
  <div class="inference-mode-selector">
    <el-form
      ref="formRef"
      :model="modelValue"
      :rules="rules"
      :label-width="labelWidth"
      class="inference-form"
    >
      <!-- 推理模式选择 -->
      <el-form-item label="推理模式" prop="mode">
        <el-select
          :model-value="modelValue.mode"
          placeholder="请选择推理模式"
          :disabled="disabled"
          style="width: 100%"
          @update:model-value="(val: InferenceMode) => handleModeChange(val)"
        >
          <el-option
            v-for="opt in modeOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          >
            <div class="mode-option">
              <span class="mode-label">{{ opt.label }}</span>
              <span class="mode-desc">{{ opt.description }}</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 配置说明 -->
      <el-form-item v-if="getConfigDescription" class="config-description">
        <el-alert
          :title="getConfigDescription"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form-item>

      <!-- Majority Vote 模式配置 -->
      <template v-if="showMajorityVoteConfig">
        <el-divider content-position="left">Majority Vote 配置</el-divider>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="采样次数 (K)" prop="samplingCount">
              <el-input-number
                :model-value="modelValue.samplingCount"
                :min="1"
                :max="16"
                :disabled="disabled"
                controls-position="right"
                style="width: 100%"
                @update:model-value="(val: number) => updateField('samplingCount', val)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="投票次数 (V)" prop="voteCount">
              <el-input-number
                :model-value="modelValue.voteCount"
                :min="3"
                :max="10"
                :disabled="disabled"
                controls-position="right"
                style="width: 100%"
                @update:model-value="(val: number) => updateField('voteCount', val)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="温度 (T)" prop="temperature">
              <el-input-number
                :model-value="modelValue.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="2"
                :disabled="disabled"
                controls-position="right"
                style="width: 100%"
                @update:model-value="(val: number) => updateField('temperature', val)"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <div class="hint-text">
            <el-icon><InfoFilled /></el-icon>
            <span>生成 K 个候选结果，通过 V 次投票选择最一致的 SQL</span>
          </div>
        </el-form-item>
      </template>

      <!-- Pass@K 模式配置 -->
      <template v-if="showPassAtKConfig">
        <el-divider content-position="left">Pass@K 配置</el-divider>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="采样次数 (K)" prop="samplingCount">
              <el-input-number
                :model-value="modelValue.samplingCount"
                :min="1"
                :max="16"
                :disabled="disabled"
                controls-position="right"
                style="width: 100%"
                @update:model-value="(val: number) => updateField('samplingCount', val)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="温度 (Temperature)" prop="temperature">
              <el-input-number
                :model-value="modelValue.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="2"
                :disabled="disabled"
                controls-position="right"
                style="width: 100%"
                @update:model-value="(val: number) => updateField('temperature', val)"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <div class="hint-text">
            <el-icon><InfoFilled /></el-icon>
            <span>生成 K 个候选结果，评估至少有一个正确的概率 (Pass@K)</span>
          </div>
        </el-form-item>
      </template>

      <!-- Check-Correct 模式配置 -->
      <template v-if="showCheckCorrectConfig">
        <el-divider content-position="left">Check-Correct 配置</el-divider>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大迭代次数" prop="maxIterations">
              <el-input-number
                :model-value="modelValue.maxIterations"
                :min="1"
                :max="5"
                :disabled="disabled"
                controls-position="right"
                style="width: 100%"
                @update:model-value="(val: number) => updateField('maxIterations', val)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="修正策略" prop="correctionStrategy">
              <el-select
                :model-value="modelValue.correctionStrategy"
                placeholder="请选择修正策略"
                :disabled="disabled"
                style="width: 100%"
                @update:model-value="(val: string) => updateField('correctionStrategy', val)"
              >
                <el-option
                  v-for="opt in correctionStrategyOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                >
                  <div class="strategy-option">
                    <span class="strategy-label">{{ opt.label }}</span>
                    <span class="strategy-desc">{{ opt.description }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <div class="hint-text">
            <el-icon><InfoFilled /></el-icon>
            <span>系统将在每次生成后检查SQL正确性，如不正确则根据策略进行修正</span>
          </div>
        </el-form-item>
      </template>
    </el-form>
  </div>
</template>

<style scoped lang="scss">
.inference-mode-selector {
  width: 100%;
}

.inference-form {
  :deep(.el-form-item__label) {
    font-weight: 500;
  }
}

.mode-option {
  display: flex;
  flex-direction: column;
  padding: 4px 0;

  .mode-label {
    font-weight: 500;
    font-size: 14px;
  }

  .mode-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
    line-height: 1.4;
  }
}

.strategy-option {
  display: flex;
  flex-direction: column;
  padding: 4px 0;

  .strategy-label {
    font-weight: 500;
    font-size: 14px;
  }

  .strategy-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
    line-height: 1.4;
  }
}

.config-description {
  margin-bottom: 8px;

  :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }

  :deep(.el-alert) {
    padding: 8px 12px;
  }

  :deep(.el-alert__title) {
    font-size: 13px;
    line-height: 1.5;
  }
}

.hint-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);

  .el-icon {
    font-size: 14px;
    color: var(--el-color-info);
  }
}

:deep(.el-divider__text) {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>
