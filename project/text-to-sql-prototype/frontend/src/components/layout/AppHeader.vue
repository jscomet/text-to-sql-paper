<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo">
        <el-icon size="28" color="var(--primary-color)"><DataAnalysis /></el-icon>
        <span class="title">Text-to-SQL</span>
      </div>
    </div>
    <div class="header-right">
      <template v-if="userStore.isLoggedIn">
        <el-dropdown>
          <span class="user-info">
            <el-avatar :size="32" :icon="User" />
            <span class="username">{{ userStore.userInfo?.username || '用户' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/settings')">
                <el-icon><Setting /></el-icon> 个人设置
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
      <template v-else>
        <el-button type="primary" @click="router.push('/login')">登录</el-button>
      </template>
    </div>
  </header>
</template>

<style scoped lang="scss">
.app-header {
  height: $header-height;
  background: #fff;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.header-left {
  .logo {
    display: flex;
    align-items: center;
    gap: 10px;

    .title {
      font-size: 20px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
}

.header-right {
  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    padding: 6px 12px;
    border-radius: 4px;
    transition: background 0.3s;

    &:hover {
      background: var(--border-extra-light);
    }

    .username {
      font-size: 14px;
      color: var(--text-regular);
    }
  }
}
</style>
