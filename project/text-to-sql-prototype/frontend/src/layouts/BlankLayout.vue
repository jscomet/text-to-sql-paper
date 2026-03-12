<script setup lang="ts">
// 空白布局 - 用于登录页等不需要侧边栏的页面
</script>

<template>
  <div class="blank-layout">
    <router-view />
  </div>
</template>

<style scoped lang="scss">
.blank-layout {
  min-height: 100vh;
  width: 100%;
}
</style>
