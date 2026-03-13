# BUG-004: 评测模块 API 请求格式不匹配

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-004 |
| **标题** | 评测模块 API 请求格式不匹配导致创建评测任务失败 |
| **严重级别** | 🔴 **Critical** |
| **优先级** | P0 |
| **状态** | ✅ 已修复 |
| **发现日期** | 2026-03-13 |
| **发现人** | E2E Tester (Claude Code) |
| **所属模块** | 评测功能 (Evaluation) |
| **相关测试** | TC-EVAL-002 |

---

## 问题描述

在评测管理页面点击"新建评测"并填写表单后，点击"开始评测"按钮，后端返回 **422 Unprocessable Entity** 错误，评测任务创建失败。

---

## 复现步骤

1. 登录系统，访问评测页面 `/evaluations`
2. 点击"新建评测"按钮
3. 填写表单：
   - 评测名称：Test-Spider-001
   - 数据库连接：Test SQLite
   - 数据集类型：Spider
   - 模型：GPT-4
   - 评测模式：单模型 (Greedy Search)
4. 点击"开始评测"按钮
5. 观察错误提示："创建评测任务失败"

---

## 期望行为

- 评测任务创建成功
- 跳转到评测详情页或显示在列表中
- 任务状态显示为"待执行"或"进行中"

---

## 实际行为

- 后端返回 422 错误
- 显示"创建评测任务失败"提示
- 评测任务未创建

---

## 根本原因分析

### 前端发送的数据结构

```json
{
  "name": "Test-Spider-001",
  "connection_id": 1,
  "dataset_type": "spider",
  "model_config": {
    "model": "gpt-4",
    "temperature": 0.0
  },
  "eval_mode": "greedy_search"
}
```

### 后端期望的数据结构 (EvalTaskCreate)

```python
class EvalTaskCreate(BaseModel):
    name: str                           # ✅ 匹配
    dataset_type: str                   # ✅ 匹配 (spider|bird|custom)
    dataset_path: Optional[str]         # ⚪ 可选
    connection_id: int                  # ✅ 匹配
    provider: str                       # ❌ 缺失! (必需, openai|dashscope)
    model: Optional[str]                # ❌ 前端: model_config.model
    temperature: float                  # ❌ 前端: model_config.temperature
    max_tokens: int                     # ⚪ 有默认值 2000
    eval_mode: str                      # ✅ 匹配 (greedy_search|majority_vote)
    vote_count: int                     # ⚪ 有默认值 5
```

### 问题汇总

| 字段 | 前端 | 后端 | 问题 |
|------|------|------|------|
| `provider` | ❌ 缺失 | ✅ 必需 | **关键缺失字段** |
| `model` | `model_config.model` | 平铺字段 | 结构不匹配 |
| `temperature` | `model_config.temperature` | 平铺字段 | 结构不匹配 |
| `max_tokens` | ❌ 缺失 | 默认 2000 | 可接受 |
| `vote_count` | ❌ 缺失 | 默认 5 | 可接受 |

---

## 截图证据

- `TC-EVAL-002-create-evaluation-dialog.png` - 新建评测对话框
- `TC-EVAL-002-form-filled.png` - 表单填写完成
- `TC-EVAL-002-create-failed-422.png` - 创建失败错误提示

---

## 修复方案

采用架构重构方案：前端只传递 `api_key_id`，后端根据 ID 获取完整的模型配置（provider, model, api_key, base_url, format_type）。

### 后端修改

#### 1. Schema 更新 (`backend/app/schemas/evaluation.py`)

```python
class EvalTaskCreate(BaseModel):
    """Schema for creating an evaluation task."""
    name: str
    dataset_type: str
    dataset_path: Optional[str] = None
    connection_id: int
    api_key_id: int                    # 新增：API Key ID（替代 provider/model）
    temperature: float = 0.7           # 可选，默认 0.7
    max_tokens: int = 2000             # 可选，默认 2000
    eval_mode: str = "greedy_search"
    vote_count: int = 5
```

#### 2. 新增辅助函数 (`backend/app/api/v1/api_keys.py`)

```python
async def get_user_api_key_by_id(
    user_id: int,
    key_id: int,
    db: AsyncSession,
) -> dict | None:
    """Get a user's API key by ID."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None

    return {
        "api_key": decrypt_api_key(api_key.key_encrypted),
        "provider": api_key.provider,
        "base_url": api_key.base_url,
        "model": api_key.model,
        "format_type": api_key.format_type,
    }
```

#### 3. API 处理更新 (`backend/app/api/v1/evaluations.py`)

```python
@router.post("/tasks", ...)
async def create_eval_task(
    request: EvalTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalTaskResponse:
    # 1. 获取 API Key 配置
    api_config = await get_user_api_key_by_id(
        user_id=current_user.id,
        key_id=request.api_key_id,
        db=db
    )
    if not api_config:
        raise HTTPException(status_code=400, detail="API key not found")

    # 2. 构建 model_config
    model_config = {
        "provider": api_config["provider"],
        "model": api_config["model"],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    # 3. 创建任务
    task = await EvalTaskService.create_eval_task(...)

    # 4. 启动后台任务（传递 format_type 和 api_key）
    background_tasks.add_task(
        run_evaluation_task,
        task_id=task.id,
        user_id=current_user.id,
        connection_id=request.connection_id,
        dataset_path=request.dataset_path,
        api_key=api_config["api_key"],           # 解密的 key
        provider=api_config["provider"],
        model_config=model_config,
        format_type=api_config["format_type"],   # 用于选择 Client
        base_url=api_config.get("base_url"),
        eval_mode=request.eval_mode,
        vote_count=request.vote_count,
    )
```

#### 4. 后台任务更新 (`backend/app/tasks/eval_tasks.py`)

```python
async def run_evaluation_task(
    task_id: int,
    user_id: int,
    connection_id: int,
    dataset_path: str,
    api_key: str,              # 新增：解密的 API key
    provider: str,
    model_config: Dict[str, Any],
    format_type: str,          # 新增：用于选择 Client
    eval_mode: str = "greedy_search",
    vote_count: int = 5,
    base_url: Optional[str] = None,
) -> None:
```

#### 5. 数据库迁移

创建迁移文件添加缺失的 `updated_at` 列：
- `backend/alembic/versions/c3d4e5f6a7b8_add_updated_at_to_eval_tasks.py`

### 前端修改

#### 1. Types 更新 (`frontend/src/types/index.ts`)

```typescript
export interface CreateEvalTaskRequest {
  name: string
  connection_id: number
  dataset_type: DatasetType
  dataset_path?: string
  api_key_id: number           // 新增
  temperature?: number
  max_tokens?: number
  eval_mode?: EvalMode
  vote_count?: number
}
```

#### 2. 表单组件更新 (`frontend/src/components/EvalTaskFormDialog.vue`)

- 添加 API Key 选择器下拉框
- 添加 temperature 滑块（范围 0-2，步长 0.1）
- 添加 max_tokens 数字输入
- 自动选择默认 API Key

#### 3. View 更新 (`frontend/src/views/EvaluationsView.vue`)

```typescript
const handleSubmit = async (formData: {...}) => {
  const submitData = {
    name: formData.name,
    connection_id: formData.connection_id,
    dataset_type: formData.dataset_type,
    api_key_id: formData.api_key_id,     // 直接传 ID
    temperature: formData.temperature,
    max_tokens: formData.max_tokens,
    eval_mode: formData.eval_mode,
    vote_count: formData.vote_count,
  }
  await createEvalTask(submitData)
}
```

---

## 影响范围

### 阻塞的测试用例

| 用例 ID | 描述 | 优先级 |
|---------|------|--------|
| TC-EVAL-002 | 创建评测任务 | P1 |
| TC-EVAL-003 | 上传自定义数据集 | P1 |
| TC-EVAL-004 | 评测执行进度展示 | P1 |
| TC-EVAL-005 | 评测结果详情查看 | P1 |
| TC-EVAL-006 | 正确样例查看 | P1 |
| TC-EVAL-007 | 错误样例分析 | P2 |
| TC-EVAL-008 | 评测报告导出 | P2 |
| TC-EVAL-009 | 评测任务删除 | P1 |
| TC-EVAL-010 | 评测任务对比 | P2 |
| TC-EVAL-011 | Pass@K 评估模式 | P1 |
| TC-EVAL-012 | 多数投票模式 | P1 |
| TC-EVAL-013 | 评测配置参数验证 | P1 |
| TC-EVAL-014 | 评测取消功能 | P1 |
| TC-EVAL-015 | 评测失败处理 | P1 |

**影响**: 几乎所有评测模块的测试用例都被阻塞（14/15）。

---

## 验证结果

### 验证日期
2026-03-13

### 验证步骤

1. ✅ 启动后端服务 (端口 8000)
2. ✅ 启动前端服务 (端口 5173)
3. ✅ 访问评测管理页面 `/evaluations`
4. ✅ 点击"新建评测"按钮
5. ✅ 填写表单：
   - 评测名称：Spider Test 001
   - 数据库连接：Test SQLite
   - 数据集类型：Spider
   - API Key：选择默认的 DeepSeek Key
   - 评测模式：单模型 (Greedy Search)
   - Temperature：0.0
   - Max Tokens：2000
6. ✅ 点击"开始评测"按钮

### 验证结果

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 表单提交成功 | ✅ 通过 | 无 422 错误 |
| API Key 选择器加载 | ✅ 通过 | 正确显示用户配置的 API Keys |
| 默认 API Key 自动选择 | ✅ 通过 | 自动选中标记为默认的 Key |
| 任务创建成功 | ✅ 通过 | 返回 201 状态码 |
| 对话框关闭 | ✅ 通过 | 创建成功后自动关闭 |
| 列表显示新任务 | ✅ 通过 | 任务正确显示在列表中 |
| 响应格式正确 | ✅ 通过 | 返回 `list` 和 `pagination` 格式 |

### 截图证据

- `TC-EVAL-002-create-evaluation-dialog.png` - 新建评测对话框
- `TC-EVAL-002-form-filled.png` - 表单填写完成（含 API Key 选择器）
- `TC-EVAL-002-create-success.png` - 创建成功，列表显示新任务

---

## 相关代码

- `frontend/src/views/EvaluationsView.vue:106-147` - 前端提交处理
- `frontend/src/components/EvalTaskFormDialog.vue` - 表单组件
- `frontend/src/api/evaluations.ts` - API 接口
- `backend/app/schemas/evaluation.py:8-19` - 后端 Schema
- `backend/app/api/v1/evaluations.py:31-92` - 后端 API 处理

---

## 更新记录

| 日期 | 操作人 | 更新内容 |
|------|--------|----------|
| 2026-03-13 | E2E Tester | 创建 Bug 报告 |
| 2026-03-13 | Claude Code | 修复完成：重构评测模块架构，使用 api_key_id 替代模型配置 |
| 2026-03-13 | Claude Code | 验证通过：成功创建评测任务，所有检查项通过 |

---

*文档版本: v2.0 (已修复)*
