<script setup lang="ts">
interface Props {
  title?: string
  description?: string
  icon?: string
  iconSize?: number
  showAction?: boolean
}

withDefaults(defineProps<Props>(), {
  title: '暂无数据',
  description: '',
  icon: 'Box',
  iconSize: 64,
  showAction: false,
})

const emit = defineEmits<{
  (e: 'action'): void
}>()

const handleAction = () => {
  emit('action')
}
</script>

<template>
  <div class="empty-state">
    <el-empty :description="title">
      <template #image>
        <div class="custom-icon">
          <el-icon :size="iconSize" color="var(--text-placeholder)">
            <component :is="icon" />
          </el-icon>
        </div>
      </template>
      <template #description>
        <div class="description">
          <p class="title">{{ title }}</p>
          <p v-if="description" class="sub-title">{{ description }}</p>
        </div>
      </template>
      <el-button v-if="showAction || $slots.action" type="primary" @click="handleAction">
        <slot name="action">新建</slot>
      </el-button>
    </el-empty>
  </div>
</template>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;

  .custom-icon {
    margin-bottom: 16px;
  }

  .description {
    text-align: center;

    .title {
      font-size: 16px;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .sub-title {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }
}
</style>
