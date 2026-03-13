# 技术架构设计文档

## 1. 技术栈选型

### 1.1 整体技术栈概览

| 层级 | 技术选型 | 版本建议 | 选型理由 |
|------|----------|----------|----------|
| 前端框架 | Vue 3 | ^3.4.x | 组合式API、更好的TypeScript支持、性能优化 |
| 构建工具 | Vite | ^5.x | 快速冷启动、HMR、现代化构建 |
| UI组件库 | Element Plus | ^2.5.x | 成熟稳定、丰富的组件、良好的文档 |
| 状态管理 | Pinia | ^2.1.x | Vue官方推荐、TypeScript友好、简洁API |
| 后端框架 | FastAPI | ^0.109.x | 异步支持、自动API文档、高性能 |
| ORM | SQLAlchemy | ^2.0.x | 强大的ORM、异步支持、迁移工具 |
| 任务队列 | Celery + Redis | ^5.3.x | 成熟的异步任务处理、定时任务支持 |
| 缓存 | Redis | ^7.x | 高性能、支持多种数据结构 |
| 检索引擎 | Whoosh / BM25 | ^2.7.x | 轻量级全文检索，支持表内容索引 |
| LLM服务 | OpenAI / Anthropic / vLLM | - | 通用格式支持，可接入任意提供商 |
| 数据库 | PostgreSQL / SQLite | 15+ / 3.x | 开发用SQLite，生产用PostgreSQL |

### 1.2 选型理由详解

#### 前端技术选型

**Vue 3 + Composition API**
- 更好的代码组织和逻辑复用
- 完整的TypeScript支持
- 更小的包体积和更好的性能
- 官方长期支持

**Element Plus**
- 企业级UI组件库，组件丰富
- 完善的表单、表格、对话框等组件
- 支持暗黑模式和主题定制
- 中文文档完善

**Pinia**
- 替代Vuex的官方状态管理方案
- 更简洁的API设计
- 完整的TypeScript支持
- 支持组合式函数风格

#### 后端技术选型

**FastAPI**
- 原生异步支持（async/await）
- 自动生成OpenAPI/Swagger文档
- 基于Pydantic的数据验证
- 性能接近Node.js和Go
- 内置依赖注入系统

**SQLAlchemy 2.0**
- 统一的ORM接口支持多种数据库
- 原生异步查询支持
- Alembic集成数据库迁移
- 强大的查询构建器

**Celery + Redis**
- 处理耗时任务（SQL评测、批量导入）
- 支持定时任务调度
- 任务结果持久化
- 监控和管理界面

**Whoosh (BM25索引)**
- 纯Python实现，无需外部依赖
- 支持全文检索和相似度排序
- 轻量级，适合表内容索引场景
- 支持增量更新

---

## 2. 系统架构图

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户层 (Client)                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Web浏览器      │  │   移动端浏览器   │  │   桌面浏览器     │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
└───────────┼────────────────────┼────────────────────┼──────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │ HTTPS
┌────────────────────────────────▼────────────────────────────────────────────┐
│                           前端层 (Frontend)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Vue 3 + Vite                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│  │  │  查询页面    │  │  评测页面    │  │  连接管理    │  │  设置页面  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│  │  │  Pinia Store│  │  Vue Router │  │  Axios HTTP │  │Element Plus│ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ REST API / WebSocket
┌────────────────────────────────▼────────────────────────────────────────────┐
│                           后端层 (Backend)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application                           │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    API Gateway                               │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │   │
│  │  │  │  认证中间件  │  │  日志中间件  │  │  异常处理中间件      │  │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    业务服务层                                │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │   │
│  │  │  │ SQL生成服务  │  │ 评测服务    │  │ 数据库连接服务       │  │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │   │
│  │  │  │ 用户服务    │  │ 历史服务    │  │ Schema管理服务      │  │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    数据访问层 (DAL)                          │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │   │
│  │  │  │ SQLAlchemy  │  │  Redis Client│  │  Celery Worker      │  │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────┬─────────────────────┬─────────────────────┬──────────────────────┘
           │                     │                     │
    ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
    │ PostgreSQL  │       │    Redis    │       │  LLM Service│
    │   (主数据库) │       │  (缓存/队列) │       │  (vLLM/API) │
    └─────────────┘       └─────────────┘       └─────────────┘
```

### 2.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端模块依赖                              │
└─────────────────────────────────────────────────────────────────┘

views/ (页面层)
    ├── components/ (业务组件)
    │       └── 依赖: Element Plus, Pinia Stores
    ├── composables/ (组合式函数)
    │       └── 依赖: Axios, Utils
    ├── stores/ (状态管理)
    │       └── 依赖: api/, localStorage
    └── api/ (API接口)
            └── 依赖: Axios, 后端API

┌─────────────────────────────────────────────────────────────────┐
│                        后端模块依赖                              │
└─────────────────────────────────────────────────────────────────┘

api/v1/ (API路由层)
    ├── deps.py (依赖注入)
    │       └── 依赖: services/, core/security
    └── endpoints/ (端点模块)
            └── 依赖: services/, schemas/

services/ (业务逻辑层)
    ├── llm.py
    │       └── 依赖: LLM API, Prompt模板 (支持openai/anthropic/vllm格式)
    ├── sql_generator.py
    │       └── 依赖: Schema管理, LLM服务
    ├── evaluator.py
    │       └── 依赖: 数据库连接, Celery
    └── db_connector.py
            └── 依赖: SQLAlchemy, 各数据库驱动

models/ (数据模型层)
    └── 依赖: SQLAlchemy Core
```

---

## 3. 前端架构

### 3.1 技术栈详细配置

```javascript
// package.json 核心依赖
{
  "dependencies": {
    "vue": "^3.4.15",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.5.3",
    "axios": "^1.6.5",
    "@element-plus/icons-vue": "^2.3.1",
    "dayjs": "^1.11.10",
    "lodash-es": "^4.17.21"
  },
  "devDependencies": {
    "vite": "^5.0.11",
    "typescript": "^5.3.3",
    "vue-tsc": "^1.8.27",
    "@vitejs/plugin-vue": "^5.0.3",
    "eslint": "^8.56.0",
    "prettier": "^3.2.4"
  }
}
```

### 3.2 目录结构

```
frontend/
├── public/                          # 静态资源
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── api/                         # API接口封装
│   │   ├── index.ts                 # axios实例配置
│   │   ├── query.ts                 # 查询相关API
│   │   ├── evaluation.ts            # 评测相关API
│   │   ├── connection.ts            # 数据库连接API
│   │   └── user.ts                  # 用户相关API
│   │
│   ├── assets/                      # 静态资源
│   │   ├── styles/                  # 全局样式
│   │   │   ├── variables.scss       # SCSS变量
│   │   │   └── global.scss          # 全局样式
│   │   └── images/
│   │
│   ├── components/                  # 公共组件
│   │   ├── common/                  # 通用组件
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppSidebar.vue
│   │   │   └── LoadingSpinner.vue
│   │   ├── query/                   # 查询相关组件
│   │   │   ├── SqlEditor.vue        # SQL编辑器
│   │   │   ├── SchemaViewer.vue     # Schema展示
│   │   │   ├── ResultTable.vue      # 结果表格
│   │   │   └── QueryHistory.vue     # 查询历史
│   │   └── evaluation/              # 评测相关组件
│   │       ├── EvalProgress.vue     # 评测进度
│   │       ├── EvalResults.vue      # 评测结果
│   │       └── MetricCard.vue       # 指标卡片
│   │
│   ├── composables/                 # 组合式函数
│   │   ├── useQuery.ts              # 查询逻辑
│   │   ├── useSqlEditor.ts          # SQL编辑器逻辑
│   │   ├── useEvaluation.ts         # 评测逻辑
│   │   └── useConnection.ts         # 连接管理逻辑
│   │
│   ├── layouts/                     # 布局组件
│   │   ├── DefaultLayout.vue        # 默认布局
│   │   └── AuthLayout.vue           # 认证布局
│   │
│   ├── router/                      # 路由配置
│   │   ├── index.ts                 # 路由入口
│   │   ├── routes.ts                # 路由定义
│   │   └── guards.ts                # 路由守卫
│   │
│   ├── stores/                      # Pinia状态管理
│   │   ├── index.ts                 # Store入口
│   │   ├── user.ts                  # 用户状态
│   │   ├── query.ts                 # 查询状态
│   │   ├── connection.ts            # 连接状态
│   │   └── settings.ts              # 设置状态
│   │
│   ├── types/                       # TypeScript类型
│   │   ├── api.ts                   # API类型
│   │   ├── query.ts                 # 查询类型
│   │   └── index.ts                 # 类型导出
│   │
│   ├── utils/                       # 工具函数
│   │   ├── storage.ts               # 本地存储封装
│   │   ├── format.ts                # 格式化工具
│   │   └── validators.ts            # 验证工具
│   │
│   ├── views/                       # 页面视图
│   │   ├── query/                   # 查询模块
│   │   │   ├── QueryView.vue        # 查询主页面
│   │   │   └── HistoryView.vue      # 历史记录
│   │   ├── evaluation/              # 评测模块
│   │   │   ├── EvalView.vue         # 评测主页面
│   │   │   └── EvalDetailView.vue   # 评测详情
│   │   ├── connection/              # 连接模块
│   │   │   └── ConnectionView.vue   # 连接管理
│   │   └── settings/                # 设置模块
│   │       └── SettingsView.vue     # 系统设置
│   │
│   ├── App.vue                      # 根组件
│   └── main.ts                      # 应用入口
│
├── .env.development                 # 开发环境配置
├── .env.production                  # 生产环境配置
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── eslint.config.js
```

### 3.3 核心组件设计

#### SQL编辑器组件 (SqlEditor.vue)

```vue
<template>
  <div class="sql-editor">
    <div class="editor-toolbar">
      <el-button @click="formatSql">格式化</el-button>
      <el-button @click="clearEditor">清空</el-button>
      <el-button type="primary" @click="executeQuery">执行</el-button>
    </div>
    <div ref="editorRef" class="editor-content"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSqlEditor } from '@/composables/useSqlEditor'

const props = defineProps<{
  modelValue: string
  readOnly?: boolean
}>()

const emit = defineEmits<['update:modelValue', 'execute']>()

const { editorRef, formatSql, clearEditor } = useSqlEditor({
  onChange: (value) => emit('update:modelValue', value),
  onExecute: (sql) => emit('execute', sql)
})
</script>
```

#### 状态管理示例 (query.ts)

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { QueryResult, QueryHistory } from '@/types/query'

export const useQueryStore = defineStore('query', () => {
  // State
  const currentQuery = ref('')
  const queryResult = ref<QueryResult | null>(null)
  const history = ref<QueryHistory[]>([])
  const isLoading = ref(false)

  // Getters
  const hasResult = computed(() => queryResult.value !== null)
  const recentQueries = computed(() => history.value.slice(0, 10))

  // Actions
  async function executeQuery(sql: string) {
    isLoading.value = true
    try {
      const result = await api.query.execute(sql)
      queryResult.value = result
      addToHistory(sql, result)
    } finally {
      isLoading.value = false
    }
  }

  function addToHistory(sql: string, result: QueryResult) {
    history.value.unshift({
      id: Date.now(),
      sql,
      timestamp: new Date(),
      executionTime: result.executionTime
    })
  }

  return {
    currentQuery,
    queryResult,
    history,
    isLoading,
    hasResult,
    recentQueries,
    executeQuery
  }
})
```

---

## 4. 后端架构

### 4.1 技术栈详细配置

```txt
# requirements.txt
# Web框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# 数据库
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
aiosqlite==0.19.0
asyncpg==0.29.0
aiomysql==0.2.0

# 缓存与队列
redis==5.0.1
celery==5.3.6

# 认证与安全
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# 配置与验证
pydantic==2.5.3
pydantic-settings==2.1.0

# HTTP客户端
httpx==0.26.0
aiohttp==3.9.1

# 工具库
loguru==0.7.2
orjson==3.9.10
```

### 4.2 目录结构

```
backend/
├── alembic/                         # 数据库迁移
│   ├── versions/                    # 迁移版本
│   ├── env.py
│   └── script.py.mako
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # 应用入口
│   │
│   ├── api/                         # API层
│   │   ├── __init__.py
│   │   ├── deps.py                  # 依赖注入
│   │   └── v1/                      # API版本1
│   │       ├── __init__.py
│   │       ├── router.py            # 路由聚合
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── auth.py          # 认证接口
│   │       │   ├── query.py         # 查询接口
│   │       │   ├── evaluation.py    # 评测接口
│   │       │   ├── connection.py    # 连接接口
│   │       │   ├── schema.py        # Schema接口
│   │       │   └── user.py          # 用户接口
│   │       └── websockets/
│   │           └── eval_progress.py # 评测进度WebSocket
│   │
│   ├── core/                        # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py                # 应用配置
│   │   ├── security.py              # 安全工具
│   │   ├── logging.py               # 日志配置
│   │   └── exceptions.py            # 异常定义
│   │
│   ├── db/                          # 数据库
│   │   ├── __init__.py
│   │   ├── session.py               # 会话管理
│   │   ├── base.py                  # 基类定义
│   │   └── init_db.py               # 初始化脚本
│   │
│   ├── models/                      # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── user.py                  # 用户模型
│   │   ├── query_history.py         # 查询历史
│   │   ├── db_connection.py         # 数据库连接
│   │   ├── evaluation.py            # 评测记录
│   │   └── evaluation_result.py     # 评测结果
│   │
│   ├── schemas/                     # Pydantic模型
│   │   ├── __init__.py
│   │   ├── base.py                  # 基础Schema
│   │   ├── user.py                  # 用户Schema
│   │   ├── query.py                 # 查询Schema
│   │   ├── evaluation.py            # 评测Schema
│   │   └── connection.py            # 连接Schema
│   │
│   ├── services/                    # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── llm.py                   # LLM服务（支持openai/anthropic/vllm格式）
│   │   ├── nl2sql.py                # SQL生成器
│   │   ├── evaluator.py             # 评测器
│   │   ├── db_connector.py          # 数据库连接器
│   │   ├── schema_manager.py        # Schema管理器
│   │   └── auth_service.py          # 认证服务
│   │
│   ├── tasks/                       # Celery任务
│   │   ├── __init__.py
│   │   ├── celery_app.py            # Celery应用
│   │   └── evaluation_tasks.py      # 评测任务
│   │
│   ├── utils/                       # 工具函数
│   │   ├── __init__.py
│   │   ├── prompts.py               # Prompt模板
│   │   ├── sql_parser.py            # SQL解析器
│   │   └── validators.py            # 验证器
│   │
│   └── templates/                   # 模板文件
│       └── prompts/                 # Prompt模板
│           ├── schema_linking.txt
│           ├── sql_generation.txt
│           └── evaluation.txt
│
├── tests/                           # 测试
│   ├── __init__.py
│   ├── conftest.py                  # 测试配置
│   ├── unit/                        # 单元测试
│   └── integration/                 # 集成测试
│
├── .env                             # 环境变量
├── .env.example                     # 环境变量示例
├── alembic.ini                      # Alembic配置
├── celeryconfig.py                  # Celery配置
├── pytest.ini                       # Pytest配置
└── requirements.txt
```

### 4.3 核心服务设计

#### LLM服务 (llm.py)

**架构设计原则**：
- `provider`: 显示名称（如 "deepseek", "openai", "my-custom-llm"），用于标识和日志
- `format_type`: 决定使用哪个Client类实现（openai/anthropic/vllm）
- 任何LLM提供商都可以通过这三种通用格式接入

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any
import httpx
from openai import AsyncOpenAI


class BaseLLMClient(ABC):
    """LLM客户端基类"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """生成文本"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI兼容格式客户端

    支持：OpenAI、DeepSeek、DashScope、vLLM等任何OpenAI兼容API
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = "gpt-3.5-turbo",
    ):
        super().__init__(api_key, base_url)
        self.default_model = default_model
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**client_kwargs)

    async def generate(self, prompt: str, model_config: Optional[Dict] = None) -> str:
        config = model_config or {}
        response = await self.client.chat.completions.create(
            model=config.get("model", self.default_model),
            messages=[{"role": "user", "content": prompt}],
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000),
        )
        return response.choices[0].message.content


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude格式客户端"""

    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_MODEL = "claude-3-sonnet-20240229"

    async def generate(self, prompt: str, model_config: Optional[Dict] = None) -> str:
        config = model_config or {}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": config.get("model", self.DEFAULT_MODEL),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens", 2000),
                },
            )
            data = response.json()
            return data["content"][0]["text"]


class VLLMClient(OpenAIClient):
    """vLLM客户端（继承OpenAIClient，使用兼容格式）"""
    pass


# LLM客户端工厂
def get_llm_client(
    provider: str,
    api_key: str,
    format_type: str = "openai",
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMClient:
    """根据format_type获取对应的LLM客户端

    Args:
        provider: 提供商名称（如 'deepseek', 'openai'）- 用于显示和日志
        api_key: API密钥
        format_type: API格式类型 - 决定使用哪个Client类
        base_url: 自定义API基础URL
        model: 默认模型名称

    Returns:
        BaseLLMClient: 对应的LLM客户端实例
    """
    if not api_key:
        raise ValueError(f"API key not provided for provider: {provider}")

    format_type = format_type.lower()

    if format_type == "openai":
        return OpenAIClient(api_key, base_url, model or "gpt-3.5-turbo")
    elif format_type == "anthropic":
        return AnthropicClient(api_key, base_url, model or "claude-3-sonnet-20240229")
    elif format_type == "vllm":
        return VLLMClient(api_key, base_url, model or "meta-llama/Llama-2-7b-chat-hf")
    else:
        raise ValueError(f"Unsupported format_type: {format_type}")
```

**配置示例**：

```python
# 环境变量配置（.env）
LLM_PROVIDER=deepseek                    # 显示名称
LLM_BASE_URL=https://api.deepseek.com/v1 # API端点
LLM_API_KEY=sk-xxxx                      # API密钥
LLM_MODEL=deepseek-chat                  # 默认模型
LLM_FORMAT=openai                        # 格式类型：openai/anthropic/vllm

# 数据库存储（api_keys表）
{
    "provider": "my-custom-llm",         # 任意名称
    "base_url": "https://api.custom.com/v1",
    "model": "custom-model",
    "format_type": "openai",             # 决定使用哪个Client类
    "key_encrypted": "xxx"
}
```

#### SQL生成器 (sql_generator.py)

```python
from typing import List, Dict, Any
from app.services.llm import BaseLLMClient, get_llm_client
from app.utils.prompts import PromptTemplate
from app.services.schema_manager import SchemaManager


class SQLGenerator:
    """Text-to-SQL生成器"""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or get_llm_client()
        self.schema_manager = SchemaManager()
        self.prompt_template = PromptTemplate()

    async def generate(
        self,
        question: str,
        db_connection_id: int,
        few_shot_examples: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成SQL查询

        Args:
            question: 自然语言问题
            db_connection_id: 数据库连接ID
            few_shot_examples: Few-shot示例

        Returns:
            包含生成的SQL和元信息的字典
        """
        # 1. 获取数据库Schema
        schema_info = await self.schema_manager.get_schema(db_connection_id)

        # 2. 构建Prompt
        prompt = self.prompt_template.build_generation_prompt(
            question=question,
            schema=schema_info,
            examples=few_shot_examples
        )

        # 3. 调用LLM生成SQL
        response = await self.llm.generate(
            prompt,
            max_tokens=512,
            temperature=0.1,
            stop=[";", "\n\n"]
        )

        # 4. 解析和验证SQL
        sql = self._extract_sql(response)
        is_valid = await self._validate_sql(sql, db_connection_id)

        return {
            "sql": sql,
            "raw_response": response,
            "is_valid": is_valid,
            "schema_used": schema_info
        }

    def _extract_sql(self, response: str) -> str:
        """从LLM响应中提取SQL"""
        # 去除markdown代码块标记
        sql = response.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        return sql.strip()

    async def _validate_sql(self, sql: str, connection_id: int) -> bool:
        """验证SQL语法"""
        # 使用数据库连接进行语法验证
        # 实际实现中可以使用EXPLAIN或LIMIT 0查询
        return True
```

#### 评测器 (evaluator.py)

```python
from typing import List, Dict, Any
import asyncio
from celery import Celery
from app.core.config import settings
from app.services.sql_generator import SQLGenerator
from app.services.db_connector import DatabaseConnector


celery_app = Celery("text2sql")
celery_app.config_from_object("celeryconfig")


class Text2SQLEvaluator:
    """Text-to-SQL评测器"""

    def __init__(self):
        self.sql_generator = SQLGenerator()
        self.db_connector = DatabaseConnector()

    async def evaluate_single(
        self,
        question: str,
        gold_sql: str,
        db_connection_id: int
    ) -> Dict[str, Any]:
        """评测单个样本"""
        # 1. 生成预测SQL
        result = await self.sql_generator.generate(question, db_connection_id)
        pred_sql = result["sql"]

        # 2. 执行对比
        gold_result = await self._safe_execute(gold_sql, db_connection_id)
        pred_result = await self._safe_execute(pred_sql, db_connection_id)

        # 3. 计算指标
        metrics = self._calculate_metrics(
            gold_sql, pred_sql,
            gold_result, pred_result
        )

        return {
            "question": question,
            "gold_sql": gold_sql,
            "pred_sql": pred_sql,
            "metrics": metrics,
            "execution_results": {
                "gold": gold_result,
                "pred": pred_result
            }
        }

    def _calculate_metrics(
        self,
        gold_sql: str,
        pred_sql: str,
        gold_result: Any,
        pred_result: Any
    ) -> Dict[str, float]:
        """计算评测指标"""
        metrics = {
            "exact_match": self._exact_match(gold_sql, pred_sql),
            "execution_match": self._execution_match(gold_result, pred_result),
        }
        return metrics

    def _exact_match(self, gold: str, pred: str) -> bool:
        """精确匹配"""
        # 规范化后比较
        gold_norm = " ".join(gold.lower().split())
        pred_norm = " ".join(pred.lower().split())
        return gold_norm == pred_norm

    def _execution_match(self, gold_result: Any, pred_result: Any) -> bool:
        """执行结果匹配"""
        if gold_result is None or pred_result is None:
            return False
        return gold_result == pred_result

    async def _safe_execute(self, sql: str, connection_id: int) -> Any:
        """安全执行SQL（带超时和错误处理）"""
        try:
            return await asyncio.wait_for(
                self.db_connector.execute(sql, connection_id),
                timeout=30
            )
        except Exception as e:
            return None


@celery_app.task(bind=True)
def run_evaluation_task(self, eval_config: Dict[str, Any]) -> Dict[str, Any]:
    """Celery评测任务"""
    evaluator = Text2SQLEvaluator()

    total = len(eval_config["samples"])
    results = []

    for i, sample in enumerate(eval_config["samples"]):
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': total, 'percent': int((i + 1) / total * 100)}
        )

        # 执行评测
        result = asyncio.run(evaluator.evaluate_single(
            question=sample["question"],
            gold_sql=sample["sql"],
            db_connection_id=eval_config["connection_id"]
        ))
        results.append(result)

    # 汇总结果
    summary = {
        "total": total,
        "exact_match_acc": sum(r["metrics"]["exact_match"] for r in results) / total,
        "execution_acc": sum(r["metrics"]["execution_match"] for r in results) / total,
    }

    return {
        "summary": summary,
        "details": results
    }
```

---

## 5. 数据流图

### 5.1 查询流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户    │────▶│  输入问题    │────▶│  前端校验    │────▶│  API请求    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                │
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│  展示结果 │◀────│  前端渲染    │◀────│  返回结果    │◀────│  后端处理    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                │
                                                       ┌────────▼────────┐
                                                       │  1. 获取Schema   │
                                                       │  2. 构建Prompt   │
                                                       │  3. 调用LLM      │
                                                       │  4. 解析SQL      │
                                                       │  5. 执行验证     │
                                                       └─────────────────┘
```

### 5.2 评测流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户    │────▶│  上传数据集  │────▶│  解析验证    │────▶│  提交评测    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────┐
                                                       │   Celery任务    │
                                                       │   异步执行       │
                                                       └────────┬────────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────┐
                                                       │  WebSocket推送   │
                                                       │  进度更新        │
                                                       └────────┬────────┘
                                                                │
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│  查看报告 │◀────│  展示图表    │◀────│  聚合结果    │◀────│  任务完成    │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 5.3 数据库连接流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户    │────▶│  填写连接信息 │────▶│  加密存储    │────▶│  测试连接    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────┐
                                                       │  1. 解析连接字符串 │
                                                       │  2. 尝试建立连接   │
                                                       │  3. 获取元数据     │
                                                       │  4. 缓存Schema     │
                                                       └────────┬────────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────┐
                                                       │  连接成功/失败   │
                                                       │  返回状态        │
                                                       └─────────────────┘
```

---

## 6. 安全设计

### 6.1 认证与授权

```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
```

### 6.2 数据库连接安全

```python
# app/services/db_connector.py
from cryptography.fernet import Fernet
from app.core.config import settings


class SecureConnectionManager:
    """安全连接管理器"""

    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)

    def encrypt_connection_string(self, connection_string: str) -> str:
        """加密连接字符串"""
        return self.cipher.encrypt(connection_string.encode()).decode()

    def decrypt_connection_string(self, encrypted: str) -> str:
        """解密连接字符串"""
        return self.cipher.decrypt(encrypted.encode()).decode()

    async def create_connection(self, db_config: dict):
        """创建数据库连接（只读权限检查）"""
        # 1. 解密连接信息
        connection_string = self.decrypt_connection_string(
            db_config["encrypted_connection"]
        )

        # 2. 创建连接池
        engine = create_async_engine(connection_string, pool_size=5)

        # 3. 验证只读权限（可选）
        if db_config.get("read_only"):
            await self._verify_read_only(engine)

        return engine
```

### 6.3 SQL注入防护

```python
# app/utils/sql_sanitizer.py
import re
from typing import List


class SQLSanitizer:
    """SQL安全校验器"""

    # 危险操作关键字
    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
        "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC"
    ]

    @classmethod
    def is_safe_query(cls, sql: str) -> bool:
        """检查SQL是否安全"""
        upper_sql = sql.upper()

        # 检查危险关键字
        for keyword in cls.DANGEROUS_KEYWORDS:
            if re.search(rf'\b{keyword}\b', upper_sql):
                return False

        # 检查多语句
        if ";" in sql.rstrip(";"):
            return False

        return True

    @classmethod
    def sanitize_for_display(cls, sql: str) -> str:
        """清理SQL用于展示"""
        # 移除注释
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql.strip()
```

---

## 7. 性能优化

### 7.1 缓存策略

```python
# app/core/cache.py
import json
from typing import Optional, Any
from redis.asyncio import Redis
from app.core.config import settings


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, expire: int = 3600):
        """设置缓存"""
        await self.redis.setex(key, expire, json.dumps(value))

    async def delete(self, key: str):
        """删除缓存"""
        await self.redis.delete(key)


# 缓存装饰器
from functools import wraps

def cached(expire: int = 3600, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = CacheManager()
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 尝试获取缓存
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 设置缓存
            await cache.set(cache_key, result, expire)
            return result
        return wrapper
    return decorator
```

### 7.2 数据库优化

```python
# app/db/optimization.py
from sqlalchemy import Index, text
from app.models.query_history import QueryHistory


class DatabaseOptimizer:
    """数据库优化器"""

    @staticmethod
    def create_indexes():
        """创建性能索引"""
        indexes = [
            # 查询历史索引
            Index("idx_query_history_user_time",
                  QueryHistory.user_id, QueryHistory.created_at),
            Index("idx_query_history_connection",
                  QueryHistory.connection_id),

            # 评测结果索引
            Index("idx_eval_result_eval_id",
                  EvaluationResult.evaluation_id),
            Index("idx_eval_result_status",
                  EvaluationResult.status),
        ]
        return indexes

    @staticmethod
    async def optimize_query_execution(conn, sql: str, limit: int = 100):
        """优化查询执行（添加LIMIT）"""
        # 自动添加LIMIT防止大数据量查询
        if "LIMIT" not in sql.upper():
            sql = f"{sql} LIMIT {limit}"
        return sql
```

### 7.3 异步处理

```python
# app/services/async_processor.py
import asyncio
from typing import List, Callable, Any
from concurrent.futures import ThreadPoolExecutor


class AsyncProcessor:
    """异步处理器"""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_batch(
        self,
        items: List[Any],
        processor: Callable,
        batch_size: int = 10
    ) -> List[Any]:
        """批量异步处理"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            tasks = [processor(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

        return results

    async def run_in_thread(self, func: Callable, *args) -> Any:
        """在线程池中运行同步函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)
```

---

## 8. 可扩展性

### 8.1 水平扩展设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        负载均衡器 (Nginx)                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼───┐  ┌────▼───┐  ┌─────▼────┐
│ FastAPI   │  │FastAPI │  │ FastAPI  │
│ 实例 1    │  │ 实例 2 │  │  实例 3  │
└─────┬─────┘  └───┬────┘  └────┬─────┘
      │            │            │
      └────────────┼────────────┘
                   │
          ┌────────▼────────┐
          │   Redis集群      │
          │  (共享状态/队列) │
          └────────┬────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
┌─────▼───┐  ┌────▼───┐  ┌─────▼────┐
│Celery   │  │Celery  │  │ Celery   │
│Worker 1 │  │Worker 2│  │ Worker 3 │
└─────────┘  └────────┘  └──────────┘
```

### 8.2 微服务拆分思路

```
当前单体架构                    未来微服务架构
┌─────────────────┐            ┌─────────────────────────────────────┐
│   Text2SQL App  │            │  API Gateway                        │
│                 │     ──▶    │  (Kong / Nginx)                     │
│  ┌───────────┐  │            └──────────┬──────────────────────────┘
│  │ Query     │  │                       │
│  │ Service   │  │         ┌─────────────┼─────────────┐
│  ├───────────┤  │         │             │             │
│  │ Eval      │  │    ┌────▼────┐  ┌────▼────┐  ┌─────▼────┐
│  │ Service   │  │    │ Query   │  │ Eval    │  │ Schema   │
│  ├───────────┤  │    │ Service │  │ Service │  │ Service  │
│  │ Schema    │  │    └────┬────┘  └────┬────┘  └─────┬────┘
│  │ Service   │  │         │            │             │
│  ├───────────┤  │         └────────────┼─────────────┘
│  │ LLM       │  │                      │
│  │ Service   │  │              ┌───────▼────────┐
│  └───────────┘  │              │  Message Queue │
│                 │              │  (RabbitMQ)    │
└─────────────────┘              └────────────────┘
```

### 8.3 插件化设计

```python
# app/core/plugin.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, List

T = TypeVar('T')


class Plugin(ABC, Generic[T]):
    """插件基类"""

    name: str
    version: str

    @abstractmethod
    async def initialize(self):
        """初始化插件"""
        pass

    @abstractmethod
    async def process(self, data: T) -> T:
        """处理数据"""
        pass


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin):
        """注册插件"""
        self._plugins[plugin.name] = plugin

    async def execute_pipeline(self, data: T, plugin_names: List[str]) -> T:
        """执行插件流水线"""
        result = data
        for name in plugin_names:
            if name in self._plugins:
                result = await self._plugins[name].process(result)
        return result


# 示例：自定义LLM提供商插件
class CustomLLMPlugin(Plugin[str]):
    """自定义LLM插件"""

    name = "custom_llm"
    version = "1.0.0"

    async def initialize(self):
        # 加载自定义模型
        pass

    async def process(self, prompt: str) -> str:
        # 调用自定义LLM
        return await self.call_custom_api(prompt)
```

---

## 9. 部署方案

### 9.1 开发环境

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./dev.db
      - REDIS_URL=redis://redis:6379
      - LLM_PROVIDER=alibaba
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    command: celery -A app.tasks.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./dev.db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - backend
```

### 9.2 生产环境

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_dist:/usr/share/nginx/html
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/text2sql
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - LLM_PROVIDER=${LLM_PROVIDER}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=text2sql

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app worker --concurrency=4 --loglevel=info
    deploy:
      replicas: 2
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/text2sql
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/text2sql
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
  frontend_dist:
```

### 9.3 部署脚本

```bash
#!/bin/bash
# deploy.sh

ENV=${1:-dev}

case $ENV in
  dev)
    echo "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up --build
    ;;
  prod)
    echo "Starting production environment..."
    # 构建前端
    cd frontend && npm run build && cd ..
    # 启动服务
    docker-compose -f docker-compose.prod.yml up -d --build
    # 执行迁移
    docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
    ;;
  *)
    echo "Usage: ./deploy.sh [dev|prod]"
    exit 1
    ;;
esac
```

---

## 10. 技术风险与应对

| 风险点 | 影响 | 概率 | 应对措施 |
|--------|------|------|----------|
| LLM生成SQL准确率低 | 高 | 中 | 1. Schema感知增强Prompt<br>2. Few-shot示例<br>3. BM25相关表推荐<br>4. 执行结果验证 |
| 复杂SQL生成失败 | 中 | 高 | 1. 分步骤生成（子查询→组合）<br>2. MVP限制SQL复杂度<br>3. 错误提示与手动编辑 |
| 大表查询性能问题 | 高 | 中 | 1. 自动添加LIMIT<br>2. 30秒执行超时<br>3. 只读账号连接<br>4. 查询限流 |
| 数据库连接安全 | 高 | 低 | 1. 连接字符串加密<br>2. 只读权限验证<br>3. SQL注入防护<br>4. 敏感数据脱敏 |
| LLM API不稳定 | 中 | 中 | 1. 多提供商降级<br>2. 本地vLLM备份<br>3. 请求重试机制 |
| Schema变更同步 | 中 | 高 | 1. 定期自动同步<br>2. 手动刷新按钮<br>3. 版本化管理 |

---

## 11. 总结

本技术架构基于PRD需求设计，采用前后端分离架构：

### 核心技术选型
- **前端**: Vue 3 + Vite + Pinia + Element Plus
- **后端**: FastAPI + SQLAlchemy + Celery
- **检索**: Whoosh (BM25索引)
- **LLM**: 支持 OpenAI / Anthropic / vLLM / DeepSeek / DashScope 等（通过 openai/anthropic/vllm 三种通用格式接入）

### 满足PRD关键需求

| PRD需求 | 技术实现 |
|---------|----------|
| SQL生成<3s | 异步LLM调用 + Schema缓存 + BM25预筛选 |
| 查询执行<30s | 异步执行 + 超时控制 + 自动LIMIT |
| SQL注入防护 | SQLSanitizer + 只读权限验证 |
| 数据脱敏 | DataMasker自动识别敏感字段 |
| BIRD评测 | Evaluator引擎 + Celery异步任务 |
| 多轮对话 | ConversationManager维护上下文 |
| BM25检索 | Whoosh索引表内容增强Schema感知 |

### 系统稳定性保障
- **高可用**: 支持水平扩展、多实例部署
- **高性能**: 多级缓存、连接池、异步处理
- **安全性**: 多层防护（注入、权限、脱敏）
- **可维护**: 模块化设计、完整日志、配置化管理

---

## 12. 版本历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2026-03-12 | 初始版本 | System Architect |
| 1.1 | 2026-03-13 | LLM配置重构：统一使用format_type选择Client实现，支持openai/anthropic/vllm三种格式 | Claude Code |
