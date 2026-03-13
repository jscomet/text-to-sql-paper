# BUG-008: API Key 前后端数据模型不匹配

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-008 |
| **标题** | API Key 前后端数据模型不匹配 |
| **严重级别** | 🔴 Critical |
| **优先级** | P0 |
| **状态** | ✅ 已修复 |
| **修复时间** | 2026-03-13 |
| **发现日期** | 2026-03-13 |
| **发现人** | e2e-lead |
| **所属模块** | API Key Management |
| **相关测试** | TC-EVAL-REAL-002, TC-SET-003 |

## 问题描述

API Key 功能的后端数据模型经过重构后，前端代码没有相应更新，导致前后端字段不匹配。前端创建 API Key 时发送的字段与后端期望的字段不一致，造成 API 调用失败。

## 字段对比分析

### 后端期望字段 (backend/app/schemas/api_key.py)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `provider` | string | ✅ | 提供商名称 (deepseek, openai, etc.) |
| `key` | string | ✅ | API 密钥 (创建时) |
| `base_url` | string | ❌ | 自定义基础 URL |
| `model` | string | ❌ | 模型名称 |
| `format_type` | string | ✅ | API 格式: openai, anthropic, vllm |
| `description` | string | ❌ | 描述 |
| `is_default` | boolean | ✅ | 是否默认 |

### 前端实际发送字段 (frontend/src/types/index.ts)

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | ✅ | 名称 |
| `key_type` | KeyType | ✅ | 类型 (openai, alibaba, anthropic, azure_openai, local) |
| `api_key` | string | ✅ | API 密钥 |
| `model` | string | ❌ | 模型 |
| `is_default` | boolean | ❌ | 是否默认 |
| `base_url` | string | ❌ | 基础 URL |

### 字段映射不匹配

| 问题 | 前端字段 | 后端字段 | 影响 |
|------|----------|----------|------|
| ❌ 名称不匹配 | `name` | `provider` | 后端无法获取提供商名称 |
| ❌ 类型字段缺失 | `key_type` | - | 前端类型无法映射到后端 |
| ❌ 密钥字段名不同 | `api_key` | `key` | 后端无法获取密钥值 |
| ❌ 缺少 format_type | - | `format_type` | 后端使用默认值 |
| ❌ 缺少 description | - | `description` | 无法添加描述 |

## 复现步骤

1. 访问设置页面 `/settings`
2. 切换到 "API Key" 标签
3. 点击"添加 API Key"
4. 填写表单：
   - 名称: "Test Key"
   - 类型: "OpenAI"
   - API Key: "sk-test123"
   - 模型: "gpt-4"
5. 点击"确定"

## 期望行为

API Key 创建成功，数据正确保存到数据库。

## 实际行为

API 调用可能失败或数据保存不完整，因为字段名不匹配：
- 前端发送 `name`，后端期望 `provider`
- 前端发送 `api_key`，后端期望 `key`

## 根本原因

后端 API Key 模型经过重构（增加了 `format_type`, `base_url`, `description` 等字段，将 `name` 改为 `provider`），但前端代码未同步更新。

## 修复方案

### 方案一：修改前端适配后端（推荐）

更新前端类型定义和表单，使其与后端模型一致：

**1. 更新 types/index.ts**
```typescript
export interface CreateApiKeyRequest {
  provider: string        // 改为 provider
  key: string            // 改为 key
  base_url?: string
  model?: string
  format_type?: 'openai' | 'anthropic' | 'vllm'
  description?: string
  is_default?: boolean
}

export interface ApiKey {
  id: number
  provider: string        // 改为 provider
  base_url?: string
  model?: string
  format_type: string
  description?: string
  is_default: boolean
  created_at: string
  last_used_at?: string
}
```

**2. 更新 SettingsView.vue**
- 表单字段从 `name` 改为 `provider`
- 表单字段从 `api_key` 改为 `key`
- 添加 `format_type` 选择
- 添加 `base_url` 输入
- 添加 `description` 输入
- 将 `key_type` 映射到 `format_type`

### 方案二：修改后端兼容前端

在后端创建 API 时进行字段映射：
```python
@router.post("/keys", ...)
def create_api_key(
    data: dict,  # 接收原始字典
    ...
):
    # 字段映射
    provider = data.get("name") or data.get("provider")
    key = data.get("api_key") or data.get("key")
    format_type = map_key_type_to_format(data.get("key_type"))
    ...
```

## 建议修改文件

### 前端修改
1. `frontend/src/types/index.ts` - 更新类型定义
2. `frontend/src/views/SettingsView.vue` - 更新表单和提交逻辑
3. `frontend/src/api/apiKeys.ts` - 更新 API 调用（如需要）

### 后端修改（如采用方案二）
1. `backend/app/api/v1/api_keys.py` - 添加字段映射

## 临时解决方案

在修复完成前，手动通过 API 创建 API Key：

```bash
curl -X POST http://localhost:8000/api/v1/keys \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "key": "sk-your-api-key",
    "model": "gpt-4",
    "format_type": "openai",
    "is_default": true
  }'
```

## 影响分析

| 影响项 | 描述 |
|--------|------|
| **功能影响** | 无法通过前端界面正确创建 API Key |
| **用户体验** | 用户添加 API Key 后可能无法使用 |
| **测试阻塞** | 阻塞需要 API Key 的评测功能测试 |

## 修复记录

| 日期 | 操作人 | 更新内容 |
|------|--------|----------|
| 2026-03-13 | e2e-lead | 创建 Bug 报告 |
| 2026-03-13 | e2e-lead | 修复前端类型定义和表单字段 |

## 修复详情

### 修改文件

1. **frontend/src/types/index.ts**
   - `ApiKey` 接口: `name` → `provider`, 新增 `base_url`, `format_type`, `description`
   - `CreateApiKeyRequest` 接口: 字段名同步更新

2. **frontend/src/views/SettingsView.vue**
   - 表单字段: `name` → `provider`, `api_key` → `key`, 新增 `format_type`, `base_url`, `description`
   - 表格列: `name` → `provider`, `key_type` → `format_type`
   - 辅助函数: 更新为 `getFormatTypeLabel` 和 `getFormatTypeTag`

### 字段映射表

| 前端旧字段 | 前端新字段 | 后端字段 | 说明 |
|-----------|-----------|----------|------|
| `name` | `provider` | `provider` | 提供商名称 |
| `api_key` | `key` | `key` | API 密钥 |
| `key_type` | `format_type` | `format_type` | 格式类型 |
| - | `base_url` | `base_url` | 自定义 URL |
| - | `description` | `description` | 描述 |

## 相关文件

| 文件路径 | 说明 |
|---------|------|
| `backend/app/models/api_key.py` | 后端 API Key 模型 |
| `backend/app/schemas/api_key.py` | 后端 API Key Schema |
| `frontend/src/types/index.ts` | 前端类型定义 |
| `frontend/src/views/SettingsView.vue` | 前端 API Key 管理页面 |
| `frontend/src/api/apiKeys.ts` | 前端 API Key API |

## 关联 Bug

- BUG-007: 前端创建评测任务时缺少 dataset_path 参数（同样原因 - 前后端模型不匹配）

## 后续建议

1. 建立前后端接口契约文档，明确字段定义
2. 使用 OpenAPI/Swagger 自动生成前端类型
3. 在 CI/CD 中添加接口兼容性检查
