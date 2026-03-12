<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import * as authApi from '@/api/auth'
import * as apiKeysApi from '@/api/apiKeys'
import type { ApiKey, KeyType } from '@/types'

const userStore = useUserStore()

// 当前激活的标签页
const activeTab = ref('profile')

// 加载状态
const loading = ref({
  profile: false,
  password: false,
  apiKeys: false,
})

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

// 处理更新个人信息
const handleUpdateProfile = async (formEl: FormInstance | undefined) => {
  if (!formEl) return

  await formEl.validate(async (valid) => {
    if (valid) {
      loading.value.profile = true
      try {
        // 更新本地用户信息
        userStore.updateUserInfo({
          username: profileForm.username,
          email: profileForm.email,
        })
        ElMessage.success('个人信息更新成功')
      } catch (error) {
        console.error('更新个人信息失败:', error)
        ElMessage.error('更新失败')
      } finally {
        loading.value.profile = false
      }
    }
  })
}

// 处理修改密码
const handleChangePassword = async (formEl: FormInstance | undefined) => {
  if (!formEl) return

  await formEl.validate(async (valid) => {
    if (valid) {
      loading.value.password = true
      try {
        await authApi.changePassword({
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword,
        })
        ElMessage.success('密码修改成功，请重新登录')
        // 清空表单
        passwordForm.oldPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
        // 延迟登出
        setTimeout(() => {
          userStore.logout()
        }, 1500)
      } catch (error) {
        console.error('修改密码失败:', error)
        ElMessage.error('原密码错误，修改失败')
      } finally {
        loading.value.password = false
      }
    }
  })
}

// ==================== API Key 管理 ====================

// API Key 列表
const apiKeys = ref<ApiKey[]>([])

// 添加 API Key 对话框
const apiKeyDialogVisible = ref(false)
const apiKeyForm = reactive({
  name: '',
  key_type: 'openai' as KeyType,
  api_key: '',
  model: '',
  is_default: false,
})

const keyTypeOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: '阿里云', value: 'alibaba' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Azure OpenAI', value: 'azure_openai' },
  { label: '本地模型', value: 'local' },
]

// 获取 API Key 列表
const fetchApiKeys = async () => {
  loading.value.apiKeys = true
  try {
    const response = await apiKeysApi.getApiKeys()
    apiKeys.value = response
  } catch (error) {
    console.error('获取 API Keys 失败:', error)
    ElMessage.error('获取 API Keys 失败')
  } finally {
    loading.value.apiKeys = false
  }
}

// 打开添加对话框
const openAddApiKeyDialog = () => {
  apiKeyForm.name = ''
  apiKeyForm.key_type = 'openai'
  apiKeyForm.api_key = ''
  apiKeyForm.model = ''
  apiKeyForm.is_default = false
  apiKeyDialogVisible.value = true
}

// 添加 API Key
const handleAddApiKey = async () => {
  if (!apiKeyForm.name || !apiKeyForm.api_key) {
    ElMessage.warning('请填写完整信息')
    return
  }

  try {
    await apiKeysApi.createApiKey({
      name: apiKeyForm.name,
      key_type: apiKeyForm.key_type,
      api_key: apiKeyForm.api_key,
      model: apiKeyForm.model || undefined,
      is_default: apiKeyForm.is_default,
    })
    ElMessage.success('API Key 添加成功')
    apiKeyDialogVisible.value = false
    fetchApiKeys()
  } catch (error) {
    console.error('添加 API Key 失败:', error)
    ElMessage.error('添加失败')
  }
}

// 删除 API Key
const handleDeleteApiKey = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个 API Key 吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await apiKeysApi.deleteApiKey(id)
    ElMessage.success('删除成功')
    fetchApiKeys()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除 API Key 失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 设置默认 API Key
const handleSetDefault = async (id: number) => {
  try {
    await apiKeysApi.setDefaultApiKey(id)
    ElMessage.success('设置成功')
    fetchApiKeys()
  } catch (error) {
    console.error('设置默认 API Key 失败:', error)
    ElMessage.error('设置失败')
  }
}

// 获取 Key Type 标签
const getKeyTypeLabel = (type: KeyType) => {
  const map: Record<string, string> = {
    openai: 'OpenAI',
    alibaba: '阿里云',
    anthropic: 'Anthropic',
    azure_openai: 'Azure',
    local: '本地',
  }
  return map[type] || type
}

// 获取 Key Type 标签样式
const getKeyTypeTag = (type: KeyType) => {
  const map: Record<string, string> = {
    openai: '',
    alibaba: 'success',
    anthropic: 'warning',
    azure_openai: 'info',
    local: 'info',
  }
  return map[type] || ''
}

// ==================== 主题设置 ====================

// 当前主题
const currentTheme = ref(localStorage.getItem('theme') || 'light')

// 切换主题
const toggleTheme = (theme: string) => {
  currentTheme.value = theme
  localStorage.setItem('theme', theme)
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
  ElMessage.success(`已切换到${theme === 'dark' ? '深色' : '浅色'}主题`)
}

onMounted(() => {
  fetchApiKeys()
})
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
            <el-button
              type="primary"
              :loading="loading.profile"
              @click="handleUpdateProfile(profileFormRef)"
            >
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
            <el-button
              type="primary"
              :loading="loading.password"
              @click="handleChangePassword(passwordFormRef)"
            >
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- API Key 配置 -->
      <el-tab-pane label="API Key" name="apikeys">
        <div class="apikeys-section">
          <div class="section-header">
            <el-button type="primary" @click="openAddApiKeyDialog">
              <el-icon><Plus /></el-icon>添加 API Key
            </el-button>
          </div>

          <el-table :data="apiKeys" v-loading="loading.apiKeys" style="width: 100%">
            <el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column prop="key_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getKeyTypeTag(row.key_type)">
                  {{ getKeyTypeLabel(row.key_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="model" label="模型" width="150">
              <template #default="{ row }">
                {{ row.model || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="is_default" label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success" size="small">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ new Date(row.created_at).toLocaleString('zh-CN') }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="!row.is_default"
                  link
                  type="primary"
                  size="small"
                  @click="handleSetDefault(row.id)"
                >
                  设为默认
                </el-button>
                <el-button link type="danger" size="small" @click="handleDeleteApiKey(row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="apiKeys.length === 0 && !loading.apiKeys" description="暂无 API Key" />
        </div>
      </el-tab-pane>

      <!-- 主题设置 -->
      <el-tab-pane label="主题" name="theme">
        <el-form label-width="100px" style="max-width: 500px">
          <el-form-item label="界面主题">
            <el-radio-group v-model="currentTheme" @change="toggleTheme">
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

    <!-- 添加 API Key 对话框 -->
    <el-dialog v-model="apiKeyDialogVisible" title="添加 API Key" width="500px">
      <el-form :model="apiKeyForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="apiKeyForm.name" placeholder="例如：OpenAI GPT-4" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="apiKeyForm.key_type" style="width: 100%">
            <el-option
              v-for="opt in keyTypeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input
            v-model="apiKeyForm.api_key"
            type="password"
            show-password
            placeholder="输入您的 API Key"
          />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="apiKeyForm.model" placeholder="例如：gpt-4（可选）" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="apiKeyForm.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="apiKeyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddApiKey">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.settings-page {
  max-width: 900px;
  margin: 0 auto;
}

.apikeys-section {
  .section-header {
    margin-bottom: 20px;
    display: flex;
    justify-content: flex-end;
  }
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
