<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ref, computed } from 'vue'

const route = useRoute()
const router = useRouter()

const isCollapse = ref(false)
const activeMenu = computed(() => route.path)

interface MenuItem {
  path: string
  name: string
  icon: string
  children?: MenuItem[]
}

const menuItems: MenuItem[] = [
  { path: '/', name: '首页', icon: 'HomeFilled' },
  { path: '/query', name: '智能查询', icon: 'ChatDotRound' },
  { path: '/connections', name: '连接管理', icon: 'Connection' },
  { path: '/history', name: '历史记录', icon: 'Clock' },
  { path: '/evaluation', name: '评测中心', icon: 'TrendCharts' },
  { path: '/settings', name: '系统设置', icon: 'Setting' },
]

const handleSelect = (path: string) => {
  router.push(path)
}

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed: isCollapse }">
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :collapse-transition="false"
      router
      class="sidebar-menu"
      @select="handleSelect"
    >
      <el-menu-item
        v-for="item in menuItems"
        :key="item.path"
        :index="item.path"
      >
        <el-icon>
          <component :is="item.icon" />
        </el-icon>
        <template #title>{{ item.name }}</template>
      </el-menu-item>
    </el-menu>
    <div class="collapse-btn" @click="toggleCollapse">
      <el-icon>
        <Fold v-if="!isCollapse" />
        <Expand v-else />
      </el-icon>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.app-sidebar {
  width: $sidebar-width;
  height: calc(100vh - #{$header-height});
  background: #fff;
  border-right: 1px solid var(--border-light);
  position: fixed;
  left: 0;
  top: $header-height;
  z-index: 99;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;

  &.collapsed {
    width: 64px;
  }
}

.sidebar-menu {
  flex: 1;
  border-right: none;

  :deep(.el-menu-item) {
    height: 50px;
    line-height: 50px;

    &.is-active {
      background: var(--primary-color);
      color: #fff;

      .el-icon {
        color: #fff;
      }
    }

    &:hover {
      background: var(--border-extra-light);
    }

    &.is-active:hover {
      background: var(--primary-color);
    }
  }
}

.collapse-btn {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-top: 1px solid var(--border-light);
  color: var(--text-secondary);
  transition: all 0.3s;

  &:hover {
    background: var(--border-extra-light);
    color: var(--primary-color);
  }
}
</style>
