<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const userStore = useUserStore()

// 当前激活的标签页
const activeTab = ref('profile')

// 个人信息表单
const profileForm = reactive({
  username: userStore.userInfo?.username || '',
  email: userStore.userInfo?.email || '',
})

// 密码表单
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// 表单引用
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// 个人信息验证规则
const profileRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
}

// 密码验证规则
const passwordRules: FormRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 系统设置
const systemSettings = reactive({
  theme: 'light',
  language: 'zh-CN',
  autoSave: true,
  notification: true,
})

// 处理更新个人信息
const handleUpdateProfile = async (formEl: FormInstance | undefined) => {
  if (!formEl) return

  await formEl.validate(async (valid) => {
    if (valid) {
      // TODO: 调用后端 API 更新个人信息
      console.log('更新个人信息:', profileForm)
    }
  })
}

// 处理修改密码
const handleChangePassword = async (formEl: FormInstance | undefined) => {
  if (!formEl) return

  await formEl.validate(async (valid) => {
    if (valid) {
      // TODO: 调用后端 API 修改密码
      console.log('修改密码:', passwordForm)
      // 清空表单
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    }
  })
}

// 处理保存系统设置
const handleSaveSettings = () => {
  // TODO: 调用后端 API 保存系统设置
  console.log('保存系统设置:', systemSettings)
}
</script>

<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 个人信息 -->
      <el-tab-pane label="个人信息" name="profile">
        <el-form
          ref="profileFormRef"
          :model="profileForm"
          :rules="profileRules"
          label-width="100px"
          style="max-width: 500px"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="profileForm.username" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="profileForm.email" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleUpdateProfile(profileFormRef)">
              保存修改
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 修改密码 -->
      <el-tab-pane label="修改密码" name="password">
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
          style="max-width: 500px"
        >
          <el-form-item label="原密码" prop="oldPassword">
            <el-input v-model="passwordForm.oldPassword" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="passwordForm.newPassword" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleChangePassword(passwordFormRef)">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 系统设置 -->
      <el-tab-pane label="系统设置" name="system">
        <el-form label-width="100px" style="max-width: 500px">
          <el-form-item label="主题">
            <el-radio-group v-model="systemSettings.theme">
              <el-radio-button label="light">
                <el-icon><Sunny /></el-icon>
                浅色
              </el-radio-button>
              <el-radio-button label="dark">
                <el-icon><Moon /></el-icon>
                深色
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="语言">
            <el-select v-model="systemSettings.language" style="width: 200px">
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </el-form-item>
          <el-form-item label="自动保存">
            <el-switch v-model="systemSettings.autoSave" />
          </el-form-item>
          <el-form-item label="消息通知">
            <el-switch v-model="systemSettings.notification" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSaveSettings">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 关于 -->
      <el-tab-pane label="关于" name="about">
        <div class="about-section">
          <h3>Text2SQL</h3>
          <p>版本: 1.0.0</p>
          <p>智能 SQL 生成平台</p>
          <el-divider />
          <p>技术栈:</p>
          <ul>
            <li>前端: Vue 3 + TypeScript + Element Plus</li>
            <li>后端: FastAPI + SQLAlchemy</li>
          </ul>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped lang="scss">
.settings-page {
  max-width: 900px;
  margin: 0 auto;
}

.about-section {
  padding: 20px;

  h3 {
    margin: 0 0 10px 0;
    font-size: 24px;
    color: #409eff;
  }

  p {
    margin: 5px 0;
    color: #606266;
  }

  ul {
    margin: 10px 0;
    padding-left: 20px;
    color: #606266;

    li {
      margin: 5px 0;
    }
  }
}
</style>
