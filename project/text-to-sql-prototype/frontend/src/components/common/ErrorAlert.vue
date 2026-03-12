<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  error?: Error | string | null
  title?: string
  type?: 'error' | 'warning' | 'info' | 'success'
  closable?: boolean
  showIcon?: boolean
  center?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  error: null,
  title: '',
  type: 'error',
  closable: true,
  showIcon: true,
  center: false,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'retry'): void
}>()

const errorMessage = computed(() => {
  if (!props.error) return ''
  if (typeof props.error === 'string') return props.error
  return props.error.message || '发生未知错误'
})

const hasError = computed(() => !!props.error)

const handleClose = () => {
  emit('close')
}

const handleRetry = () => {
  emit('retry')
}
</script>

<template>
  <el-alert
    v-if="hasError"
    :title="title || errorMessage"
    :type="type"
    :closable="closable"
    :show-icon="showIcon"
    :center="center"
    class="error-alert"
    @close="handleClose"
  >
    <template #default>
      <div v-if="title && errorMessage !== title" class="error-detail">{{ errorMessage }}</div>
      <div v-if="$slots.default || $slots.retry" class="alert-content">
        <slot />
        <el-button
          v-if="$slots.retry || $attrs.onRetry"
          link
          type="primary"
          size="small"
          @click="handleRetry"
        >
          <slot name="retry">重试</slot>
        </el-button>
      </div>
    </template>
  </el-alert>
</template>

<style scoped lang="scss">
.error-alert {
  margin-bottom: 16px;

  .error-detail {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  .alert-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
}
</style>
