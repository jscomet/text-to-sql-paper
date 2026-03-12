<script setup lang="ts">
import { ref } from 'vue'

interface FormItem {
  prop: string
  label: string
  type: 'input' | 'select' | 'date' | 'daterange' | 'number' | 'switch'
  placeholder?: string
  options?: { label: string; value: unknown }[]
  width?: string
  clearable?: boolean
  disabled?: boolean
}

interface Props {
  items: FormItem[]
  modelValue: Record<string, unknown>
  loading?: boolean
  showReset?: boolean
  inline?: boolean
  labelWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  showReset: true,
  inline: true,
  labelWidth: '80px',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, unknown>): void
  (e: 'search'): void
  (e: 'reset'): void
}>()

const formRef = ref()

const handleSearch = () => {
  emit('search')
}

const handleReset = () => {
  formRef.value?.resetFields()
  emit('reset')
}

const handleInputChange = (prop: string, value: unknown) => {
  emit('update:modelValue', { ...props.modelValue, [prop]: value })
}
</script>

<template>
  <el-form
    ref="formRef"
    :model="modelValue"
    :inline="inline"
    :label-width="labelWidth"
    class="search-form"
  >
    <el-form-item
      v-for="item in items"
      :key="item.prop"
      :label="item.label"
      :prop="item.prop"
    >
      <!-- 输入框 -->
      <el-input
        v-if="item.type === 'input'"
        :model-value="modelValue[item.prop]"
        :placeholder="item.placeholder || `请输入${item.label}`"
        :clearable="item.clearable !== false"
        :disabled="item.disabled"
        :style="{ width: item.width || '200px' }"
        @update:model-value="(val: unknown) => handleInputChange(item.prop, val)"
      />

      <!-- 数字输入 -->
      <el-input-number
        v-else-if="item.type === 'number'"
        :model-value="modelValue[item.prop]"
        :placeholder="item.placeholder"
        :disabled="item.disabled"
        :style="{ width: item.width || '200px' }"
        @update:model-value="(val: unknown) => handleInputChange(item.prop, val)"
      />

      <!-- 下拉选择 -->
      <el-select
        v-else-if="item.type === 'select'"
        :model-value="modelValue[item.prop]"
        :placeholder="item.placeholder || `请选择${item.label}`"
        :clearable="item.clearable !== false"
        :disabled="item.disabled"
        :style="{ width: item.width || '200px' }"
        @update:model-value="(val: unknown) => handleInputChange(item.prop, val)"
      >
        <el-option
          v-for="opt in item.options"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>

      <!-- 日期选择 -->
      <el-date-picker
        v-else-if="item.type === 'date'"
        :model-value="modelValue[item.prop]"
        type="date"
        :placeholder="item.placeholder || '选择日期'"
        :clearable="item.clearable !== false"
        :disabled="item.disabled"
        :style="{ width: item.width || '200px' }"
        @update:model-value="(val: unknown) => handleInputChange(item.prop, val)"
      />

      <!-- 日期范围 -->
      <el-date-picker
        v-else-if="item.type === 'daterange'"
        :model-value="modelValue[item.prop]"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :clearable="item.clearable !== false"
        :disabled="item.disabled"
        :style="{ width: item.width || '240px' }"
        @update:model-value="(val: unknown) => handleInputChange(item.prop, val)"
      />

      <!-- 开关 -->
      <el-switch
        v-else-if="item.type === 'switch'"
        :model-value="modelValue[item.prop]"
        :disabled="item.disabled"
        @update:model-value="(val: unknown) => handleInputChange(item.prop, val)"
      />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" :loading="loading" @click="handleSearch">
        <el-icon><Search /></el-icon>搜索
      </el-button>
      <el-button v-if="showReset" @click="handleReset">
        <el-icon><Refresh /></el-icon>重置
      </el-button>
    </el-form-item>

    <!-- 额外操作按钮 -->
    <el-form-item v-if="$slots.actions">
      <slot name="actions" />
    </el-form-item>
  </el-form>
</template>

<style scoped lang="scss">
.search-form {
  padding: 16px;
  background: #fff;
  border-radius: 4px;
  margin-bottom: 16px;

  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}
</style>
