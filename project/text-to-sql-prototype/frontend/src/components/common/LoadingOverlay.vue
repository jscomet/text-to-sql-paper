<script setup lang="ts">
interface Props {
  loading: boolean
  text?: string
  fullscreen?: boolean
  background?: string
}

withDefaults(defineProps<Props>(), {
  text: '加载中...',
  fullscreen: false,
  background: 'rgba(255, 255, 255, 0.8)',
})
</script>

<template>
  <div
    v-if="!fullscreen"
    v-loading="loading"
    :element-loading-text="text"
    :element-loading-background="background"
    class="loading-overlay"
  >
    <slot />
  </div>
  <div v-else class="fullscreen-wrapper">
    <slot />
  </div>
</template>

<style scoped lang="scss">
.loading-overlay {
  position: relative;
  min-height: 100px;
}

.fullscreen-wrapper {
  :deep(.el-loading-mask) {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 2000;
  }
}
</style>
