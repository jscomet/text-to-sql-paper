<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

/**
 * 修正策略类型
 * 与后端 correction_strategy 保持一致
 */
export type CorrectionStrategy = 'none' | 'self_correction' | 'execution_feedback' | 'multi_agent'

/**
 * 错误分类类型
 */
export type ErrorCategory = 'syntax' | 'execution' | 'logic' | 'schema' | 'timeout' | 'unknown'

/**
 * Check-Correct 配置接口
 */
export interface CheckCorrectConfig {
  /** 最大迭代次数 */
  maxIterations: number
  /** 修正策略 */
  correctionStrategy: CorrectionStrategy
  /** 是否在每次迭代后执行SQL验证 */
  validateOnEachIteration: boolean
  /** 错误分类过滤 (空数组表示处理所有类型) */
  errorCategories: ErrorCategory[]
  /** 是否启用详细日志 */
  enableDetailedLog: boolean
  /** 超时时间 (秒) */
  timeoutSeconds: number
}

interface Props {
  /** v-model 绑定值 */
  modelValue: CheckCorrectConfig
  /** 是否禁用 */
  disabled?: boolean
  /** 标签宽度 */
  labelWidth?: string
  /** 是否显示高级选项 */
  showAdvanced?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  labelWidth: '140px',
  showAdvanced: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: CheckCorrectConfig): void
}>()

const formRef = ref<FormInstance>()
const advancedExpanded = ref(props.showAdvanced)

/** 修正策略选项 */
const correctionStrategyOptions = [
  {
    label: '自我修正',
    value: 'self_correction',
    description: '模型基于错误信息自我检查和修正',
    icon: 'User'
  },
  {
    label: '执行反馈',
    value: 'execution_feedback',
    description: '基于SQL执行错误反馈进行针对性修正',
    icon: 'VideoPlay'
  },
  {
    label: '多智能体',
    value: 'multi_agent',
    description: '多智能体协作生成修正方案',
    icon: 'UserFilled'
  },
  {
    label: '无修正',
    value: 'none',
    description: '仅检查不修正，用于调试',
    icon: 'CircleClose'
  }
]

/** 错误分类选项 */
const errorCategoryOptions = [
  { label: '语法错误', value: 'syntax', description: 'SQL语法解析错误' },
  { label: '执行错误', value: 'execution', description: 'SQL执行时异常' },
  { label: '逻辑错误', value: 'logic', description: '结果与预期不符' },
  { label: 'Schema错误', value: 'schema', description: '表/列不存在' },
  { label: '超时错误', value: 'timeout', description: '执行超时' },
  { label: '未知错误', value: 'unknown', description: '其他未分类错误' }
]

/** 表单验证规则 */
const rules: FormRules = {
  maxIterations: [
    { required: true, message: '请输入最大迭代次数', trigger: 'blur' },
    { type: 'number', min: 1, max: 5, message: '迭代次数范围 1-5', trigger: 'blur' }
  ],
  correctionStrategy: [{ required: true, message: '请选择修正策略', trigger: 'change' }],
  timeoutSeconds: [
    { required: true, message: '请输入超时时间', trigger: 'blur' },
    { type: 'number', min: 10, max: 300, message: '超时时间范围 10-300秒', trigger: 'blur' }
  ]
}

/** 当前选中的策略信息 */
const selectedStrategy = computed(() => {
  return correctionStrategyOptions.find(s => s.value === props.modelValue.correctionStrategy)
})

/**
 * 更新字段值
 */
const updateField = <K extends keyof CheckCorrectConfig>(field: K, value: CheckCorrectConfig[K]) => {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

/**
 * 处理策略选择
 */
const handleStrategyChange = (strategy: CorrectionStrategy) => {
  updateField('correctionStrategy', strategy)
}

/**
 * 处理错误分类变化
 */
const handleErrorCategoriesChange = (categories: ErrorCategory[]) => {
  updateField('errorCategories', categories)
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
    maxIterations: 3,
    correctionStrategy: 'self_correction',
    validateOnEachIteration: true,
    errorCategories: [],
    enableDetailedLog: false,
    timeoutSeconds: 60
  })
}

/**
 * 获取策略图标
 */
const getStrategyIcon = (iconName: string) => {
  return iconName
}

// 暴露方法给父组件
defineExpose({
  validate,
  resetForm
})
</script>

<template>
  <div class="check-correct-config-panel">
    <el-form
      ref="formRef"
      :model="modelValue"
      :rules="rules"
      :label-width="labelWidth"
      class="config-form"
    >
      <!-- 基础配置 -->
      <el-row :gutter="20">
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
          <el-form-item label="超时时间 (秒)" prop="timeoutSeconds">
            <el-input-number
              :model-value="modelValue.timeoutSeconds"
              :min="10"
              :max="300"
              :step="10"
              :disabled="disabled"
              controls-position="right"
              style="width: 100%"
              @update:model-value="(val: number) => updateField('timeoutSeconds', val)"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 修正策略选择 -->
      <el-form-item label="修正策略" prop="correctionStrategy" class="strategy-selector">
        <el-radio-group
          :model-value="modelValue.correctionStrategy"
          :disabled="disabled"
          @update:model-value="(val: CorrectionStrategy) => handleStrategyChange(val)"
        >
          <el-radio-button
            v-for="strategy in correctionStrategyOptions"
            :key="strategy.value"
            :label="strategy.value"
          >
            <el-icon class="strategy-icon">
              <component :is="strategy.icon" />
            </el-icon>
            <span>{{ strategy.label }}</span>
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- 策略说明 -->
      <el-form-item v-if="selectedStrategy" class="strategy-description">
        <el-alert
          :title="selectedStrategy.description"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form-item>

      <!-- 高级选项折叠面板 -->
      <el-collapse v-model="advancedExpanded" class="advanced-collapse">
        <el-collapse-item name="advanced">
          <template #title>
            <span class="collapse-title">
              <el-icon><Setting /></el-icon>
              高级选项
            </span>
          </template>

          <!-- 每次迭代验证 -->
          <el-form-item label="迭代验证">
            <el-switch
              :model-value="modelValue.validateOnEachIteration"
              :disabled="disabled"
              active-text="每次迭代后执行SQL验证"
              inactive-text="仅在最后验证"
              @update:model-value="(val: boolean) => updateField('validateOnEachIteration', val)"
            />
          </el-form-item>

          <!-- 详细日志 -->
          <el-form-item label="详细日志">
            <el-switch
              :model-value="modelValue.enableDetailedLog"
              :disabled="disabled"
              active-text="记录详细修正过程"
              inactive-text="仅记录结果"
              @update:model-value="(val: boolean) => updateField('enableDetailedLog', val)"
            />
          </el-form-item>

          <!-- 错误分类过滤 -->
          <el-form-item label="处理错误类型">
            <el-select
              :model-value="modelValue.errorCategories"
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="全部类型 (不选则处理所有错误)"
              :disabled="disabled"
              style="width: 100%"
              @update:model-value="(val: ErrorCategory[]) => handleErrorCategoriesChange(val)"
            >
              <el-option
                v-for="cat in errorCategoryOptions"
                :key="cat.value"
                :label="cat.label"
                :value="cat.value"
              >
                <div class="error-category-option">
                  <span class="category-label">{{ cat.label }}</span>
                  <span class="category-desc">{{ cat.description }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-collapse-item>
      </el-collapse>

      <!-- 配置提示 -->
      <el-form-item class="config-hint">
        <div class="hint-content">
          <el-icon><InfoFilled /></el-icon>
          <div class="hint-text">
            <p>Check-Correct 模式将迭代执行以下流程：</p>
            <ol>
              <li>生成候选 SQL</li>
              <li>检查 SQL 正确性（语法 + 执行）</li>
              <li>如不正确，根据策略生成修正版本</li>
              <li>重复直到正确或达到最大迭代次数</li>
            </ol>
          </div>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped lang="scss">
.check-correct-config-panel {
  width: 100%;
  padding: 16px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
}

.config-form {
  :deep(.el-form-item__label) {
    font-weight: 500;
  }
}

.strategy-selector {
  :deep(.el-radio-group) {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  :deep(.el-radio-button__inner) {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 8px 16px;
  }

  .strategy-icon {
    font-size: 14px;
  }
}

.strategy-description {
  margin-bottom: 16px;

  :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }

  :deep(.el-alert) {
    padding: 8px 12px;
  }
}

.advanced-collapse {
  margin: 16px 0;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;

  :deep(.el-collapse-item__header) {
    padding: 0 16px;
    font-weight: 500;
  }

  :deep(.el-collapse-item__content) {
    padding: 16px;
  }

  .collapse-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.error-category-option {
  display: flex;
  flex-direction: column;
  padding: 4px 0;

  .category-label {
    font-weight: 500;
    font-size: 14px;
  }

  .category-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
  }
}

.config-hint {
  margin-top: 16px;

  :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }
}

.hint-content {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background-color: var(--el-color-info-light-9);
  border-radius: 4px;
  border-left: 4px solid var(--el-color-info);

  .el-icon {
    font-size: 16px;
    color: var(--el-color-info);
    margin-top: 2px;
    flex-shrink: 0;
  }

  .hint-text {
    font-size: 13px;
    color: var(--el-text-color-regular);
    line-height: 1.6;

    p {
      margin: 0 0 8px 0;
      font-weight: 500;
    }

    ol {
      margin: 0;
      padding-left: 16px;

      li {
        margin: 4px 0;
      }
    }
  }
}

:deep(.el-input-number) {
  width: 100%;
}
</style>
