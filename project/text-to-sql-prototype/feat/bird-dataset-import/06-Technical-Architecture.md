# BIRD 数据集导入支持 - 技术架构文档

## 1. 概述

本文档描述 BIRD 数据集导入功能的技术架构、组件设计和数据流。

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户层 (Web UI)                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Evaluation Page                                          │ │
│  │  ├── Import Button                                        │ │
│  │  ├── Import Dialog (Zip/Local)                            │ │
│  │  ├── Progress Dialog                                      │ │
│  │  └── Result Dialog                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API 层 (FastAPI)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ /datasets/import│  │ /datasets/import│  │ /datasets/      │  │
│  │ /zip            │  │ /local          │  │ imports         │  │
│  │     POST        │  │     POST        │  │     GET         │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┴────────────────────┘           │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ DatasetImportService                                      │ │
│  │ ├── validate_dataset()                                    │ │
│  │ ├── extract_databases()                                   │ │
│  │ ├── create_connections()                                  │ │
│  │ └── create_eval_tasks()                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     数据层 (File System + DB)                   │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐   │
│  │   Data Directory        │  │   SQLite Database           │   │
│  │   /data/bird/           │  │   ┌─────────────────────┐   │   │
│  │   ├── {import_id}/      │  │   │ dataset_imports     │   │   │
│  │   │   ├── dev.json      │  │   │ dataset_import_logs │   │   │
│  │   │   └── databases/    │  │   │ db_connection       │   │   │
│  │   │       └── *.sqlite  │  │   │ eval_tasks          │   │   │
│  │   └── ...               │  │   └─────────────────────┘   │   │
│  └─────────────────────────┘  └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 组件清单

| 组件 | 类型 | 职责 |
|------|------|------|
| DatasetImportDialog | Vue Component | 导入对话框UI |
| dataset.ts | API Client | 前端API调用 |
| datasets.py | FastAPI Router | API路由处理 |
| DatasetImportService | Service | 业务逻辑处理 |
| DatasetImport | Model | 导入记录数据模型 |
| eval_tasks.py | Background Task | 评测任务执行 |

---

## 3. 核心组件设计

### 3.1 后端服务层

#### DatasetImportService

```python
class DatasetImportService:
    """数据集导入服务"""

    async def import_from_zip(
        self,
        file: UploadFile,
        config: ImportConfig,
        user: User
    ) -> ImportResult:
        """从 zip 文件导入数据集"""
        pass

    async def import_from_local(
        self,
        local_path: str,
        config: ImportConfig,
        user: User
    ) -> ImportResult:
        """从本地目录导入数据集"""
        pass

    async def validate_dataset(self, data_dir: Path) -> ValidationResult:
        """验证数据集格式"""
        pass

    async def extract_databases(self, data_dir: Path) -> List[str]:
        """提取 db_id 列表"""
        pass

    async def create_connections(
        self,
        db_ids: List[str],
        data_dir: Path,
        user: User
    ) -> ConnectionResult:
        """创建数据库连接"""
        pass

    async def create_eval_tasks(
        self,
        connections: List[Connection],
        data_dir: Path,
        config: ImportConfig,
        user: User
    ) -> TaskResult:
        """创建评测任务"""
        pass
```

#### 关键方法流程

**import_from_zip**:
```
1. 生成 import_id
2. 创建数据目录
3. 解压 zip 文件
4. 调用 validate_dataset
5. 调用 extract_databases
6. 调用 create_connections
7. 调用 create_eval_tasks
8. 返回 ImportResult
```

**import_from_local**:
```
1. 验证本地路径存在
2. 生成 import_id
3. 创建数据目录
4. 复制/链接数据文件
5. 后续步骤同 import_from_zip
```

### 3.2 数据集验证器

```python
class DatasetValidator:
    """数据集格式验证器"""

    def validate_bird_format(self, data_dir: Path) -> ValidationResult:
        """验证 BIRD 数据集格式"""
        checks = [
            self._check_dev_json_exists(),
            self._check_databases_directory(),
            self._check_json_format(),
            self._check_required_fields(),
            self._check_database_files(),
        ]
        return ValidationResult(checks)

    def _check_required_fields(self, data: List[Dict]) -> bool:
        """检查必需的字段"""
        required = ['question_id', 'db_id', 'question', 'SQL']
        return all(
            all(field in item for field in required)
            for item in data
        )
```

### 3.3 前端组件

#### ImportDialog.vue

导入对话框组件，支持 Zip 文件上传和本地目录两种方式。

```vue
<template>
  <el-dialog title="导入 BIRD 数据集">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="上传 Zip 文件" name="zip">
        <ZipUpload @file-selected="handleFileSelected" />
      </el-tab-pane>
      <el-tab-pane label="本地目录" name="local">
        <LocalPathInput @path-validated="handlePathValidated" />
      </el-tab-pane>
    </el-tabs>

    <ImportConfigForm v-model="config" />

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" @click="startImport">开始导入</el-button>
    </template>
  </el-dialog>
</template>
```

**Props:**

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| visible | boolean | 是 | 对话框显示状态 |

**Events:**

| 事件名 | 参数 | 说明 |
|--------|------|------|
| import-started | ImportResult | 导入开始，返回导入结果 |
| closed | - | 对话框关闭 |

---

#### EvaluationList.vue

评测任务列表组件，支持父子任务层级展示。

```vue
<template>
  <div class="evaluation-list">
    <el-table
      :data="displayTasks"
      row-key="id"
      :expand-row-keys="expandedRows"
      @expand-change="handleExpandChange"
    >
      <!-- 展开列 -->
      <el-table-column type="expand" width="40">
        <template #default="{ row }">
          <div v-if="row.task_type === 'parent'" class="child-tasks-container">
            <el-table
              :data="row.children || []"
              :show-header="false"
              class="child-table"
            >
              <el-table-column width="60" />
              <el-table-column prop="name" label="任务名称">
                <template #default="{ row: child }">
                  <span class="tree-line">├─</span>
                  <span>{{ child.name }}</span>
                  <el-tag size="small" type="info">子任务</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态">
                <template #default="{ row: child }">
                  <TaskStatus :status="child.status" />
                </template>
              </el-table-column>
              <el-table-column prop="progress" label="进度">
                <template #default="{ row: child }">
                  <el-progress
                    :percentage="calculateProgress(child)"
                    :status="getProgressStatus(child)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="操作">
                <template #default="{ row: child }">
                  <el-button
                    link
                    type="primary"
                    @click="$emit('viewDetail', child)"
                  >
                    查看
                  </el-button>
                  <el-button
                    v-if="child.status === 'failed'"
                    link
                    type="warning"
                    @click="$emit('retryTask', child)"
                  >
                    重试
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>

      <!-- 任务名称 -->
      <el-table-column prop="name" label="任务名称" min-width="200">
        <template #default="{ row }">
          <span :class="{ 'parent-task-name': row.task_type === 'parent' }">
            {{ row.name }}
          </span>
          <el-tag
            v-if="row.task_type === 'parent'"
            size="small"
            type="primary"
          >
            父任务
          </el-tag>
          <el-tag
            v-else-if="row.task_type === 'single'"
            size="small"
            type="success"
          >
            独立任务
          </el-tag>
          <span v-if="row.task_type === 'parent'" class="child-count">
            {{ row.child_count }}个子任务
          </span>
        </template>
      </el-table-column>

      <!-- 状态 -->
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <TaskStatus :status="row.status" />
        </template>
      </el-table-column>

      <!-- 进度 -->
      <el-table-column prop="progress" label="进度" width="180">
        <template #default="{ row }">
          <el-progress
            v-if="row.task_type === 'parent'"
            :percentage="calculateParentProgress(row)"
            :status="getProgressStatus(row)"
          />
          <el-progress
            v-else
            :percentage="calculateProgress(row)"
            :status="getProgressStatus(row)"
          />
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="$emit('viewDetail', row)"
          >
            详情
          </el-button>
          <el-button
            v-if="row.task_type === 'parent' && row.status === 'pending'"
            link
            type="success"
            @click="$emit('startTask', row)"
          >
            开始评测
          </el-button>
          <el-button
            v-if="row.task_type === 'child' && row.status === 'failed'"
            link
            type="warning"
            @click="$emit('retryTask', row)"
          >
            重试
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
```

**Props:**

```typescript
interface EvaluationListProps {
  tasks: EvalTask[];           // 任务列表数据
  showHierarchy: boolean;      // 是否显示层级结构
  defaultExpanded: number[];   // 默认展开的父任务ID列表
}

interface EvalTask {
  id: number;
  name: string;
  task_type: 'single' | 'parent' | 'child';
  parent_id?: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  child_count?: number;
  completed_children?: number;
  total_questions?: number;
  processed_questions?: number;
  children?: EvalTask[];
  // ... 其他字段
}
```

**Events:**

```typescript
interface EvaluationListEvents {
  expand: (taskId: number) => void;           // 展开父任务
  collapse: (taskId: number) => void;         // 折叠父任务
  viewDetail: (task: EvalTask) => void;       // 查看任务详情
  startTask: (task: EvalTask) => void;        // 开始父任务评测
  retryTask: (task: EvalTask) => void;        // 重试任务
}
```

**样式规范:**

```scss
.evaluation-list {
  .parent-task-name {
    font-weight: 600;
  }

  .child-tasks-container {
    padding-left: 32px;
    background-color: #fafafa;

    .child-table {
      background-color: transparent;

      .tree-line {
        color: #c0c4cc;
        margin-right: 8px;
      }
    }
  }

  .child-count {
    margin-left: 8px;
    color: #909399;
    font-size: 12px;
  }

  // 父任务行样式
  :deep(.el-table__row--level-0) {
    &.parent-row {
      background-color: #ecf5ff;
      border-left: 4px solid #409eff;
    }
  }
}
```

---

#### ParentTaskDetail.vue

父任务详情组件，展示父任务的总体统计和子任务列表。

```vue
<template>
  <el-dialog
    :title="`父任务详情 - ${task?.name}`"
    width="900px"
    class="parent-task-detail"
  >
    <!-- 顶部信息区 -->
    <div class="task-header">
      <h2>{{ task?.name }}</h2>
      <el-tag type="primary" size="large">父任务</el-tag>
      <TaskStatus :status="task?.status" />
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-value">{{ totalQuestions }}</div>
        <div class="stat-label">总问题数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ overallAccuracy }}%</div>
        <div class="stat-label">总体正确率</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ completedChildren }}/{{ task?.child_count }}</div>
        <div class="stat-label">完成进度</div>
      </el-card>
    </div>

    <!-- 总体进度条 -->
    <div class="overall-progress">
      <div class="progress-label">总体进度</div>
      <el-progress
        :percentage="overallProgress"
        :color="progressColors"
        :stroke-width="20"
        striped
      />
    </div>

    <!-- 子任务状态分布 -->
    <div class="status-distribution">
      <h4>子任务状态分布</h4>
      <div class="status-cards">
        <div
          v-for="(count, status) in statusDistribution"
          :key="status"
          class="status-card"
          :class="status"
          @click="filterByStatus(status)"
        >
          <div class="status-name">{{ statusNameMap[status] }}</div>
          <div class="status-count">{{ count }}</div>
        </div>
      </div>
    </div>

    <!-- 子任务列表 -->
    <div class="children-list">
      <h4>子任务列表</h4>
      <el-table :data="filteredChildren" stripe>
        <el-table-column prop="name" label="数据库ID" min-width="150">
          <template #default="{ row }">
            <el-link
              type="primary"
              @click="navigateToConnection(row.connection_id)"
            >
              {{ row.db_id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="connection_name" label="连接名称" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <TaskStatus :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="问题数" width="120">
          <template #default="{ row }">
            {{ row.processed_questions || 0 }}/{{ row.total_questions || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="accuracy" label="正确率" width="100">
          <template #default="{ row }">
            {{ row.accuracy ? (row.accuracy * 100).toFixed(1) + '%' : '--' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewChildDetail(row)">
              详情
            </el-button>
            <el-button link type="primary" @click="viewChildLogs(row)">
              日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 底部操作 -->
    <template #footer>
      <el-button
        v-if="hasFailedChildren"
        type="warning"
        @click="retryFailedChildren"
      >
        批量重试失败任务
      </el-button>
      <el-button
        v-if="hasPendingChildren"
        type="primary"
        @click="startAllChildren"
      >
        开始全部
      </el-button>
      <el-button @click="close">关闭</el-button>
    </template>
  </el-dialog>
</template>
```

**Props:**

```typescript
interface ParentTaskDetailProps {
  task: EvalTask | null;       // 父任务数据
  visible: boolean;            // 对话框显示状态
}
```

**Events:**

```typescript
interface ParentTaskDetailEvents {
  close: () => void;                          // 关闭对话框
  viewChild: (child: EvalTask) => void;       // 查看子任务详情
  startAll: (parentId: number) => void;       // 开始所有子任务
  retryFailed: (parentId: number) => void;    // 重试失败子任务
  viewLogs: (child: EvalTask) => void;        // 查看子任务日志
}
```

**计算属性:**

```typescript
// 总体进度计算
const overallProgress = computed(() => {
  if (!props.task?.child_count) return 0;
  return Math.round(
    (props.task.completed_children || 0) / props.task.child_count * 100
  );
});

// 总体正确率计算
const overallAccuracy = computed(() => {
  if (!props.task?.children?.length) return 0;
  const completed = props.task.children.filter(c => c.status === 'completed');
  if (!completed.length) return 0;
  const total = completed.reduce((sum, c) => sum + (c.accuracy || 0), 0);
  return (total / completed.length * 100).toFixed(1);
});

// 子任务状态分布
const statusDistribution = computed(() => {
  const distribution = { pending: 0, running: 0, completed: 0, failed: 0 };
  props.task?.children?.forEach(child => {
    distribution[child.status]++;
  });
  return distribution;
});
```

---

#### ChildTaskDetail.vue

子任务详情组件，展示单个数据库的评测详情和问题列表。

```vue
<template>
  <el-dialog
    :title="`子任务详情 - ${task?.db_id}`"
    width="900px"
    class="child-task-detail"
  >
    <!-- 父任务关联区 -->
    <div class="parent-link">
      <span>父任务:</span>
      <el-link
        type="primary"
        :underline="false"
        @click="navigateToParent"
      >
        {{ parentTask?.name }}
      </el-link>
      <el-tag type="primary" size="small">父任务</el-tag>
      <el-tag type="info" size="small">子任务</el-tag>
    </div>

    <!-- 数据库信息区 -->
    <div class="db-info">
      <h2>{{ task?.db_id }}</h2>
      <TaskStatus :status="task?.status" />
      <div class="connection-info">
        <span>数据库连接: {{ connection?.name }} (ID: {{ task?.connection_id }})</span>
        <el-link type="primary" @click="navigateToConnection">
          查看连接 →
        </el-link>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-value">{{ task?.total_questions || 0 }}</div>
        <div class="stat-label">总问题数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ processedQuestions }}/{{ task?.total_questions || 0 }}</div>
        <div class="stat-label">已处理</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ accuracy }}%</div>
        <div class="stat-label">正确率</div>
      </el-card>
    </div>

    <!-- 进度条 -->
    <div class="progress-section">
      <div class="progress-label">当前进度</div>
      <el-progress
        :percentage="taskProgress"
        :color="progressColors"
        :stroke-width="18"
      />
    </div>

    <!-- 问题列表 -->
    <div class="questions-list">
      <h4>评测问题列表</h4>
      <el-table :data="questions" stripe max-height="400">
        <el-table-column type="index" width="50" />
        <el-table-column prop="question" label="问题预览" min-width="250">
          <template #default="{ row }">
            <span class="question-preview">{{ truncate(row.question, 50) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <TaskStatus :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="execution_time" label="执行时间" width="100">
          <template #default="{ row }">
            {{ row.execution_time ? row.execution_time + 's' : '--' }}
          </template>
        </el-table-column>
        <el-table-column label="正确" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.is_correct" color="#67c23a"><Check /></el-icon>
            <el-icon v-else-if="row.is_correct === false" color="#f56c6c"><Close /></el-icon>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              link
              type="primary"
              @click="viewSQLComparison(row)"
            >
              查看SQL
            </el-button>
            <span v-else>--</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 最近日志 -->
    <div class="recent-logs">
      <h4>最近日志</h4>
      <div class="logs-container">
        <div v-for="log in recentLogs" :key="log.id" class="log-item">
          <span class="log-time">[{{ formatTime(log.timestamp) }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <template #footer>
      <el-button type="warning" @click="retryTask">重新评测</el-button>
      <el-button type="primary" @click="viewFullLogs">查看完整日志</el-button>
      <el-button @click="close">关闭</el-button>
    </template>
  </el-dialog>
</template>
```

**Props:**

```typescript
interface ChildTaskDetailProps {
  task: EvalTask | null;           // 子任务数据
  parentTask: EvalTask | null;     // 父任务数据
  connection: DBConnection | null; // 数据库连接信息
  visible: boolean;                // 对话框显示状态
}

interface Question {
  id: number;
  question: string;
  status: 'pending' | 'running' | 'completed';
  execution_time?: number;
  is_correct?: boolean;
  generated_sql?: string;
  expected_sql?: string;
}

interface LogEntry {
  id: number;
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
}
```

**Events:**

```typescript
interface ChildTaskDetailEvents {
  close: () => void;                          // 关闭对话框
  viewParent: (parentId: number) => void;     // 查看父任务
  retry: (taskId: number) => void;            // 重新评测
  viewFullLogs: (taskId: number) => void;     // 查看完整日志
  viewSQL: (question: Question) => void;      // 查看SQL对比
}
```

---

### 3.4 状态管理设计

#### Pinia Store 设计

```typescript
// stores/evaluation.ts
import { defineStore } from 'pinia';

interface EvaluationState {
  tasks: EvalTask[];
  parentTasks: Map<number, EvalTask>;
  childTasks: Map<number, EvalTask[]>;
  loading: boolean;
  expandedParents: Set<number>;
  websocketConnected: boolean;
}

export const useEvaluationStore = defineStore('evaluation', {
  state: (): EvaluationState => ({
    tasks: [],
    parentTasks: new Map(),
    childTasks: new Map(),
    loading: false,
    expandedParents: new Set(),
    websocketConnected: false,
  }),

  getters: {
    // 获取所有父任务
    parentTaskList: (state) => {
      return state.tasks.filter(t => t.task_type === 'parent');
    },

    // 获取独立任务
    standaloneTasks: (state) => {
      return state.tasks.filter(t => t.task_type === 'single');
    },

    // 获取子任务（按父任务ID）
    getChildrenByParentId: (state) => (parentId: number) => {
      return state.childTasks.get(parentId) || [];
    },

    // 计算父任务总体进度
    getParentProgress: (state) => (parentId: number) => {
      const parent = state.parentTasks.get(parentId);
      if (!parent?.child_count) return 0;
      return Math.round((parent.completed_children || 0) / parent.child_count * 100);
    },
  },

  actions: {
    // 加载任务列表
    async fetchTasks(params?: TaskQueryParams) {
      this.loading = true;
      try {
        const response = await evaluationApi.getTasks(params);
        this.tasks = response.data;

        // 分类存储父子任务
        this.tasks.forEach(task => {
          if (task.task_type === 'parent') {
            this.parentTasks.set(task.id, task);
          } else if (task.task_type === 'child' && task.parent_id) {
            const siblings = this.childTasks.get(task.parent_id) || [];
            if (!siblings.find(t => t.id === task.id)) {
              siblings.push(task);
              this.childTasks.set(task.parent_id, siblings);
            }
          }
        });
      } finally {
        this.loading = false;
      }
    },

    // 更新任务状态（WebSocket 推送）
    updateTaskStatus(taskId: number, status: TaskStatus, updates?: Partial<EvalTask>) {
      // 更新任务本身
      const taskIndex = this.tasks.findIndex(t => t.id === taskId);
      if (taskIndex > -1) {
        this.tasks[taskIndex] = { ...this.tasks[taskIndex], status, ...updates };
      }

      // 如果是子任务，更新父任务统计
      const task = this.tasks[taskIndex];
      if (task?.task_type === 'child' && task.parent_id) {
        this.updateParentStats(task.parent_id);
      }
    },

    // 更新父任务统计
    async updateParentStats(parentId: number) {
      const children = this.childTasks.get(parentId) || [];
      const parent = this.parentTasks.get(parentId);

      if (!parent) return;

      // 重新计算统计
      const completed = children.filter(c => c.status === 'completed').length;
      const totalQuestions = children.reduce((sum, c) => sum + (c.total_questions || 0), 0);
      const correctCount = children.reduce((sum, c) => sum + (c.correct_count || 0), 0);

      // 更新父任务状态
      let parentStatus: TaskStatus = 'pending';
      if (completed === parent.child_count) {
        parentStatus = 'completed';
      } else if (completed > 0) {
        parentStatus = 'running';
      }
      if (children.some(c => c.status === 'failed')) {
        parentStatus = 'failed';
      }

      // 更新存储
      parent.completed_children = completed;
      parent.total_questions = totalQuestions;
      parent.correct_count = correctCount;
      parent.accuracy = totalQuestions > 0 ? correctCount / totalQuestions : 0;
      parent.status = parentStatus;

      this.parentTasks.set(parentId, { ...parent });
    },

    // 展开/折叠父任务
    toggleParentExpand(parentId: number) {
      if (this.expandedParents.has(parentId)) {
        this.expandedParents.delete(parentId);
      } else {
        this.expandedParents.add(parentId);
      }
    },
  },
});
```

#### WebSocket 实时推送

```typescript
// composables/useTaskWebSocket.ts
import { onMounted, onUnmounted } from 'vue';
import { useEvaluationStore } from '@/stores/evaluation';

export function useTaskWebSocket() {
  const store = useEvaluationStore();
  let ws: WebSocket | null = null;

  const connect = () => {
    const wsUrl = `${import.meta.env.VITE_WS_URL}/ws/tasks`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      store.websocketConnected = true;
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      store.websocketConnected = false;
      // 重连逻辑
      setTimeout(connect, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'task_status_update':
        store.updateTaskStatus(
          message.task_id,
          message.status,
          message.updates
        );
        break;

      case 'parent_stats_update':
        store.updateParentStats(message.parent_id);
        break;

      case 'child_task_created':
        // 新子任务创建，刷新父任务
        store.fetchTasks({ parent_id: message.parent_id });
        break;

      case 'task_progress':
        // 任务进度更新
        store.updateTaskProgress(message.task_id, message.progress);
        break;
    }
  };

  const disconnect = () => {
    ws?.close();
  };

  onMounted(connect);
  onUnmounted(disconnect);

  return { connect, disconnect };
}
```

---

### 3.5 前端 API 模块设计

#### dataset.ts

数据集导入相关 API 模块。

```typescript
// api/dataset.ts
import request from '@/utils/request';

export interface ImportConfig {
  name: string;
  model_config: {
    api_key_id: number;
    model: string;
    temperature: number;
    max_tokens: number;
  };
  eval_mode: 'greedy' | 'sampling';
}

export interface ImportResult {
  import_id: string;
  parent_task_id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message: string;
  connections_created: number;
  tasks_created: number;
  total_questions: number;
}

export interface ImportRecord {
  id: string;
  name: string;
  source_type: 'zip' | 'local';
  source_path: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

export interface ImportDetail extends ImportRecord {
  connections: Array<{
    id: number;
    name: string;
    db_id: string;
    status: string;
  }>;
  tasks: Array<{
    id: number;
    name: string;
    task_type: string;
    status: string;
  }>;
}

export interface ImportProgress {
  import_id: string;
  status: string;
  current_step: number;
  total_steps: number;
  step_name: string;
  progress_percent: number;
  logs: Array<{
    timestamp: string;
    level: string;
    message: string;
  }>;
}

export const datasetApi = {
  /**
   * 从 Zip 文件导入数据集
   */
  importFromZip(file: File, config: ImportConfig): Promise<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));

    return request.post('/datasets/import/zip', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * 从本地目录导入数据集
   */
  importFromLocal(path: string, config: ImportConfig): Promise<ImportResult> {
    return request.post('/datasets/import/local', {
      local_path: path,
      config,
    });
  },

  /**
   * 获取导入历史列表
   */
  getImportHistory(): Promise<ImportRecord[]> {
    return request.get('/datasets/imports');
  },

  /**
   * 获取导入详情
   */
  getImportDetail(id: string): Promise<ImportDetail> {
    return request.get(`/datasets/imports/${id}`);
  },

  /**
   * 获取导入进度
   */
  getImportProgress(id: string): Promise<ImportProgress> {
    return request.get(`/datasets/imports/${id}/progress`);
  },

  /**
   * 删除导入记录
   */
  deleteImport(id: string): Promise<void> {
    return request.delete(`/datasets/imports/${id}`);
  },

  /**
   * 验证本地路径
   */
  validateLocalPath(path: string): Promise<{
    valid: boolean;
    message: string;
    db_count?: number;
    question_count?: number;
  }> {
    return request.post('/datasets/validate-path', { path });
  },
};
```

#### evaluation.ts 更新

扩展 EvalTask 类型和新增 API 方法。

```typescript
// api/evaluation.ts
import request from '@/utils/request';

// 扩展 EvalTask 类型
export interface EvalTask {
  id: number;
  user_id: number;
  name: string;

  // 任务类型字段
  parent_id?: number;
  task_type: 'single' | 'parent' | 'child';

  // 数据集相关
  dataset_type: string;
  dataset_path?: string;
  db_id?: string;

  // 连接相关
  connection_id?: number;
  connection?: DBConnection;

  // 模型配置
  model_config: ModelConfig;
  eval_mode: 'greedy' | 'sampling';

  // 状态
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;

  // 统计字段
  total_questions?: number;
  processed_questions?: number;
  correct_count?: number;
  accuracy?: number;

  // 父子任务统计
  child_count?: number;
  completed_children?: number;

  // 子任务列表（仅在查询父任务详情时填充）
  children?: EvalTask[];

  // 父任务信息（仅在查询子任务详情时填充）
  parent?: EvalTask;

  // 时间戳
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskQueryParams {
  page?: number;
  page_size?: number;
  status?: string;
  task_type?: 'single' | 'parent' | 'child';
  parent_id?: number;
  search?: string;
}

export const evaluationApi = {
  // ========== 现有方法 ==========

  /**
   * 获取评测任务列表
   */
  getTasks(params?: TaskQueryParams): Promise<PaginatedResponse<EvalTask>> {
    return request.get('/evaluation/tasks', { params });
  },

  /**
   * 获取单个任务详情
   */
  getTask(id: number): Promise<EvalTask> {
    return request.get(`/evaluation/tasks/${id}`);
  },

  /**
   * 创建评测任务
   */
  createTask(data: CreateTaskRequest): Promise<EvalTask> {
    return request.post('/evaluation/tasks', data);
  },

  /**
   * 开始评测任务
   */
  startTask(id: number): Promise<void> {
    return request.post(`/evaluation/tasks/${id}/start`);
  },

  /**
   * 重试失败的评测任务
   */
  retryTask(id: number): Promise<void> {
    return request.post(`/evaluation/tasks/${id}/retry`);
  },

  /**
   * 删除评测任务
   */
  deleteTask(id: number): Promise<void> {
    return request.delete(`/evaluation/tasks/${id}`);
  },

  // ========== 新增父子任务相关方法 ==========

  /**
   * 获取父任务详情（包含子任务列表）
   */
  getParentTaskDetail(id: number): Promise<EvalTask> {
    return request.get(`/evaluation/tasks/${id}/detail`, {
      params: { include_children: true },
    });
  },

  /**
   * 获取子任务详情（包含父任务信息）
   */
  getChildTaskDetail(id: number): Promise<EvalTask> {
    return request.get(`/evaluation/tasks/${id}/detail`, {
      params: { include_parent: true },
    });
  },

  /**
   * 批量开始父任务的所有子任务
   */
  startAllChildren(parentId: number): Promise<void> {
    return request.post(`/evaluation/tasks/${parentId}/start-all`);
  },

  /**
   * 重试父任务中所有失败的子任务
   */
  retryFailedChildren(parentId: number): Promise<void> {
    return request.post(`/evaluation/tasks/${parentId}/retry-failed`);
  },

  /**
   * 获取子任务列表
   */
  getChildrenByParentId(
    parentId: number,
    params?: Omit<TaskQueryParams, 'parent_id'>
  ): Promise<PaginatedResponse<EvalTask>> {
    return request.get(`/evaluation/tasks/${parentId}/children`, { params });
  },

  /**
   * 获取任务日志
   */
  getTaskLogs(
    id: number,
    params?: { limit?: number; offset?: number }
  ): Promise<{
    logs: Array<{
      timestamp: string;
      level: string;
      message: string;
    }>;
    total: number;
  }> {
    return request.get(`/evaluation/tasks/${id}/logs`, { params });
  },

  /**
   * 获取任务结果（问题列表）
   */
  getTaskResults(
    id: number,
    params?: { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<TaskResult>> {
    return request.get(`/evaluation/tasks/${id}/results`, { params });
  },
};
```

---

## 4. 数据流

### 4.1 Zip 导入流程

```
用户选择 zip 文件
        │
        ▼
前端上传文件 + 配置
        │
        ▼
POST /datasets/import/zip
        │
        ▼
┌───────────────┐
│ 接收上传文件   │
│ (multipart)   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 验证文件格式   │
│ - zip 格式    │
│ - 大小限制    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 创建导入目录   │
│ /data/bird/   │
│   {import_id}/│
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 解压 zip 文件 │
│ (流式解压)    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 验证数据集格式 │
│ - dev.json    │
│ - databases/  │
│ - 字段检查    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 提取 db_id    │
│ 列表          │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 创建数据库连接 │
│ (批量创建)    │
└───────┬───────┘
        │
        ▼
┌───────────────────┐
│ 创建父任务        │
│ (task_type=       │
│   "parent")       │
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│ 创建子任务        │
│ (task_type=       │
│   "child")        │
│ - 关联父任务ID    │
│ - 关联连接ID      │
│ - 设置db_id       │
└───────┬───────────┘
        │
        ▼
返回 ImportResult
(包含 parent_task_id)
        │
        ▼
前端显示结果对话框
```

### 4.2 本地导入流程

```
用户输入本地路径
        │
        ▼
前端验证路径格式
        │
        ▼
POST /datasets/import/local
        │
        ▼
┌───────────────┐
│ 验证路径存在   │
│ 和可读性      │
└───────┬───────┘
        │
        ▼
后续流程同 zip 导入
```

### 4.3 父子任务状态管理

**子任务状态变化 → 更新父任务状态流程**:

```
子任务状态变化
        │
        ▼
┌───────────────────────────────────┐
│ 1. 更新子任务状态到数据库          │
│    (EvalTask.status = new_status) │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ 2. 触发父任务统计更新              │
│    (通过 SQLAlchemy event 或      │
│     WebSocket 广播)               │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ 3. 查询所有兄弟子任务状态          │
│    SELECT * FROM eval_tasks       │
│    WHERE parent_id = ?            │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ 4. 计算父任务新状态                │
│    - 统计各状态子任务数量          │
│    - 根据优先级规则确定父状态      │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ 5. 更新父任务统计和状态            │
│    - completed_children            │
│    - total_questions               │
│    - correct_count                 │
│    - accuracy                      │
│    - status                        │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ 6. 广播状态变更                    │
│    - WebSocket 推送到前端          │
│    - 前端实时更新 UI               │
└───────────────────────────────────┘
```

**父任务状态计算逻辑**:

```python
def calculate_parent_status(children: List[EvalTask]) -> Tuple[TaskStatus, Dict]:
    """
    根据子任务状态计算父任务状态

    状态优先级: failed > running > pending > completed
    """
    total = len(children)
    if total == 0:
        return "pending", {"completed_children": 0}

    # 统计各状态数量
    status_counts = {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
    }
    for child in children:
        status_counts[child.status] += 1

    # 计算统计数据
    completed = status_counts["completed"]
    total_questions = sum(c.total_questions or 0 for c in children)
    correct_count = sum(c.correct_count or 0 for c in children)

    stats = {
        "completed_children": completed,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "accuracy": correct_count / total_questions if total_questions > 0 else 0.0,
    }

    # 状态优先级判断
    if status_counts["failed"] > 0:
        # 如果有失败的，且其他都完成，父任务标记为失败
        if status_counts["failed"] + completed == total:
            return "failed", stats
        # 否则根据是否有运行中的判断
        elif status_counts["running"] > 0:
            return "running", stats
        else:
            return "failed", stats
    elif status_counts["running"] > 0:
        return "running", stats
    elif status_counts["pending"] == total:
        return "pending", stats
    elif completed == total:
        return "completed", stats
    else:
        return "running", stats  # 部分完成，部分等待
```

**统计汇总计算逻辑**:

```python
class ParentTaskStatsCalculator:
    """父任务统计计算器"""

    @staticmethod
    def calculate_progress(parent: EvalTask, children: List[EvalTask]) -> float:
        """计算总体进度百分比"""
        if not parent.child_count:
            return 0.0

        # 方法1: 基于子任务完成数量
        completed_based = (parent.completed_children or 0) / parent.child_count * 100

        # 方法2: 基于问题处理数量（更精确）
        total_questions = sum(c.total_questions or 0 for c in children)
        processed_questions = sum(c.processed_questions or 0 for c in children)
        question_based = (processed_questions / total_questions * 100) if total_questions > 0 else 0.0

        # 默认使用基于问题数量的进度
        return round(question_based, 1)

    @staticmethod
    def calculate_accuracy(children: List[EvalTask]) -> float:
        """计算总体正确率"""
        completed_children = [c for c in children if c.status == "completed"]
        if not completed_children:
            return 0.0

        total_correct = sum(c.correct_count or 0 for c in completed_children)
        total_processed = sum(c.processed_questions or 0 for c in completed_children)

        return round(total_correct / total_processed * 100, 1) if total_processed > 0 else 0.0

    @staticmethod
    def get_status_distribution(children: List[EvalTask]) -> Dict[str, int]:
        """获取状态分布统计"""
        distribution = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        for child in children:
            distribution[child.status] = distribution.get(child.status, 0) + 1
        return distribution


def update_parent_task_stats(parent_task_id: int, db: Session):
    """更新父任务统计（完整版）"""
    # 获取父任务
    parent = db.query(EvalTask).get(parent_task_id)
    if not parent or parent.task_type != "parent":
        raise ValueError(f"Invalid parent task: {parent_task_id}")

    # 获取所有子任务
    children = db.query(EvalTask).filter_by(parent_id=parent_task_id).all()

    # 计算统计
    calculator = ParentTaskStatsCalculator()

    # 更新统计字段
    parent.completed_children = sum(1 for c in children if c.status == "completed")
    parent.total_questions = sum(c.total_questions or 0 for c in children)
    parent.correct_count = sum(c.correct_count or 0 for c in children)
    parent.accuracy = calculator.calculate_accuracy(children) / 100

    # 计算并更新状态
    new_status, _ = calculate_parent_status(children)
    parent.status = new_status

    db.commit()

    # 广播更新
    broadcast_parent_update(parent_task_id, {
        "status": new_status,
        "completed_children": parent.completed_children,
        "total_questions": parent.total_questions,
        "correct_count": parent.correct_count,
        "accuracy": parent.accuracy,
        "progress": calculator.calculate_progress(parent, children),
    })

    return parent
```

**WebSocket 实时推送机制**:

```python
# backend/app/websockets/task_updates.py

from fastapi import WebSocket
from typing import Dict, Set

class TaskUpdateManager:
    """任务更新管理器"""

    def __init__(self):
        # 存储活跃连接: {user_id: Set[WebSocket]}
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """建立 WebSocket 连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开 WebSocket 连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

    async def broadcast_to_user(self, user_id: int, message: dict):
        """向指定用户广播消息"""
        if user_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # 清理断开连接
        for conn in disconnected:
            self.active_connections[user_id].discard(conn)

    async def broadcast_task_update(
        self,
        user_id: int,
        task_id: int,
        status: str,
        updates: dict
    ):
        """广播任务状态更新"""
        await self.broadcast_to_user(user_id, {
            "type": "task_status_update",
            "task_id": task_id,
            "status": status,
            "updates": updates,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def broadcast_parent_stats_update(
        self,
        user_id: int,
        parent_id: int,
        stats: dict
    ):
        """广播父任务统计更新"""
        await self.broadcast_to_user(user_id, {
            "type": "parent_stats_update",
            "parent_id": parent_id,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        })


task_manager = TaskUpdateManager()


# 在子任务状态变更时触发
@event.listens_for(EvalTask, 'after_update')
def on_task_update(mapper, connection, target):
    """任务更新后触发"""
    if target.task_type == "child" and target.parent_id:
        # 异步更新父任务统计
        asyncio.create_task(
            update_parent_and_broadcast(target.parent_id, target.user_id)
        )


async def update_parent_and_broadcast(parent_id: int, user_id: int):
    """更新父任务并广播"""
    from sqlalchemy.orm import Session
    db = Session(bind=engine)

    try:
        parent = update_parent_task_stats(parent_id, db)

        # 广播更新
        await task_manager.broadcast_parent_stats_update(
            user_id,
            parent_id,
            {
                "status": parent.status,
                "completed_children": parent.completed_children,
                "total_questions": parent.total_questions,
                "accuracy": parent.accuracy,
            }
        )
    finally:
        db.close()
```

---

## 5. 关键技术点

### 5.1 大文件处理

**Zip 文件上传**:
- 使用流式上传避免内存溢出
- 配置 nginx/uvicorn 允许大文件上传
- 前端显示上传进度

**Zip 解压**:
```python
import zipfile

def extract_zip_stream(zip_path: Path, extract_dir: Path):
    """流式解压 zip 文件"""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # 验证路径安全
            target_path = extract_dir / member.filename
            if not str(target_path).startswith(str(extract_dir)):
                raise ValueError(f"Unsafe path: {member.filename}")

            zf.extract(member, extract_dir)
```

### 5.2 路径安全

**路径遍历防护**:
```python
def safe_extract_path(base_dir: Path, target_path: str) -> Path:
    """安全的文件路径解析"""
    full_path = (base_dir / target_path).resolve()
    base_resolved = base_dir.resolve()

    if not str(full_path).startswith(str(base_resolved)):
        raise ValueError(f"Path traversal detected: {target_path}")

    return full_path
```

**本地目录白名单**:
```python
ALLOWED_IMPORT_PATHS = [
    "/data",
    "/opt/data",
    "/home/*/data",
    "D:/data",
    "D:/Working/paper/project/ICED-2026-paper-code/data",
]

def validate_local_path(path: str) -> bool:
    """验证本地路径是否允许导入"""
    path_obj = Path(path).resolve()

    # 检查系统敏感目录
    forbidden_paths = ["/etc", "/usr", "/bin", "C:/Windows"]
    for forbidden in forbidden_paths:
        if str(path_obj).startswith(forbidden):
            return False

    return True
```

### 5.3 数据集过滤

**后端按 db_id 过滤**:
```python
# backend/app/tasks/eval_tasks.py

def filter_dataset_by_db_id(
    dataset: List[Dict],
    connection_db_id: str
) -> List[Dict]:
    """按 db_id 过滤数据集"""
    # 检查是否有 db_id 字段
    has_db_id = any(item.get("db_id") for item in dataset)

    if not has_db_id:
        return dataset

    # 过滤匹配当前连接的数据
    filtered = [
        item for item in dataset
        if item.get("db_id", connection_db_id) == connection_db_id
    ]

    return filtered if filtered else dataset
```

### 5.4 父子任务创建

**创建父任务**:

```python
async def create_parent_task(
    db: Session,
    name: str,
    dataset_path: str,
    config: ImportConfig,
    user: User
) -> EvalTask:
    """创建父任务（容器）"""
    parent = EvalTask(
        user_id=user.id,
        name=name,
        task_type="parent",  # 标记为父任务
        dataset_type="bird",
        dataset_path=dataset_path,
        model_config=config.model_config,
        eval_mode=config.eval_mode,
        status="pending",
        child_count=0,  # 将在创建子任务后更新
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent
```

**创建子任务**:

```python
async def create_child_task(
    db: Session,
    parent: EvalTask,
    db_id: str,
    connection_id: int,
    config: ImportConfig,
    user: User
) -> EvalTask:
    """创建子任务（实际执行评测）"""
    child = EvalTask(
        user_id=user.id,
        parent_id=parent.id,  # 关联父任务
        name=f"{parent.name} - {db_id}",
        task_type="child",  # 标记为子任务
        dataset_type="bird",
        dataset_path=parent.dataset_path,  # 使用完整数据集路径
        db_id=db_id,  # 设置 db_id 用于过滤
        connection_id=connection_id,
        model_config=parent.model_config,  # 继承父任务配置
        eval_mode=parent.eval_mode,
        status="pending",
    )
    db.add(child)
    return child
```

**批量创建子任务**:

```python
async def create_child_tasks_batch(
    db: Session,
    parent: EvalTask,
    connections: List[DBConnection],
    user: User
) -> List[EvalTask]:
    """批量创建子任务"""
    children = []
    for conn in connections:
        child = await create_child_task(
            db, parent, conn.db_id, conn.id, None, user
        )
        children.append(child)

    # 更新父任务的子任务数量
    parent.child_count = len(children)
    db.commit()
    return children
```

---

## 6. 错误处理

### 6.1 错误分类

| 错误类型 | 处理方式 | 响应码 |
|---------|---------|--------|
| 文件格式错误 | 立即返回，前端提示 | 400 |
| 数据集验证失败 | 返回详细错误信息 | 400 |
| 部分连接创建失败 | 继续处理，返回部分成功 | 200 |
| 权限不足 | 返回权限错误 | 403 |
| 服务器错误 | 返回错误，记录日志 | 500 |

### 6.2 事务处理

**数据库操作**:
- 使用 SQLAlchemy 事务
- 导入记录创建失败时回滚
- 连接/任务创建失败记录但不回滚

**文件操作**:
- 解压失败清理临时文件
- 导入成功保留数据文件
- 导入失败可选清理数据

---

## 7. 性能优化

### 7.1 异步处理

```python
async def create_connections_parallel(
    db_ids: List[str],
    data_dir: Path,
    user: User
) -> List[Connection]:
    """并行创建数据库连接"""
    tasks = [
        create_single_connection(db_id, data_dir, user)
        for db_id in db_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### 7.2 缓存策略

- 数据集解析结果缓存（短时间）
- 连接创建后缓存 connection_id
- 避免重复验证相同数据集

---

## 8. 安全考虑

### 8.1 文件上传安全

- 限制文件类型（仅 zip）
- 限制文件大小（1GB）
- 验证 zip 内容（防止 zip bomb）

### 8.2 路径安全

- 禁止路径遍历
- 禁止访问系统目录
- 使用绝对路径验证

### 8.3 权限控制

- 验证用户权限
- 资源隔离（仅访问自己的导入）
- 操作审计日志

---

## 9. 扩展性

### 9.1 支持其他数据集

```python
class DatasetImporter(ABC):
    """数据集导入器抽象基类"""

    @abstractmethod
    def validate(self, data_dir: Path) -> bool:
        pass

    @abstractmethod
    def extract_databases(self, data_dir: Path) -> List[str]:
        pass

class BirdImporter(DatasetImporter):
    """BIRD 数据集导入器"""
    pass

class SpiderImporter(DatasetImporter):
    """Spider 数据集导入器"""
    pass
```

### 9.2 插件机制

- 支持自定义数据集格式验证器
- 支持自定义导入后处理
- 支持第三方数据源

---

## 10. 文档检查报告

### 10.1 已补充的内容

本次检查针对第 3.3 节「前端组件」进行了全面补充，确保技术架构文档与 UI 设计文档 (02-UI-Design.md) 保持一致。

| 章节 | 补充内容 | 对应 UI 设计 |
|------|----------|--------------|
| 3.3.1 | ImportDialog.vue 完整 Props/Events 定义 | 3.1 导入对话框设计 |
| 3.3.2 | **EvaluationList.vue** 树形展示组件 | 2.2 父子任务列表展示、6.5 树形列表组件规范 |
| 3.3.3 | **ParentTaskDetail.vue** 父任务详情组件 | 5.3 父任务详情页面 |
| 3.3.4 | **ChildTaskDetail.vue** 子任务详情组件 | 5.4 子任务详情页面 |
| 3.4 | **状态管理设计** - Pinia Store + WebSocket | 2.2.2 状态计算规则 |
| 3.5.1 | **dataset.ts** API 模块完整定义 | 3.1-3.3 导入功能 |
| 3.5.2 | **evaluation.ts** 扩展 API 方法 | 5.3-5.4 详情页面交互 |
| 4.3 | **父子任务状态管理** 完整流程 | 2.2.2 状态计算规则、7.2 状态转换 |

### 10.2 组件 Props/Events 汇总

#### EvaluationList 组件

```typescript
// Props
interface EvaluationListProps {
  tasks: EvalTask[];
  showHierarchy: boolean;
  defaultExpanded: number[];
}

// Events
interface EvaluationListEvents {
  expand: (taskId: number) => void;
  collapse: (taskId: number) => void;
  viewDetail: (task: EvalTask) => void;
  startTask: (task: EvalTask) => void;
  retryTask: (task: EvalTask) => void;
}
```

#### ParentTaskDetail 组件

```typescript
// Props
interface ParentTaskDetailProps {
  task: EvalTask | null;
  visible: boolean;
}

// Events
interface ParentTaskDetailEvents {
  close: () => void;
  viewChild: (child: EvalTask) => void;
  startAll: (parentId: number) => void;
  retryFailed: (parentId: number) => void;
  viewLogs: (child: EvalTask) => void;
}
```

#### ChildTaskDetail 组件

```typescript
// Props
interface ChildTaskDetailProps {
  task: EvalTask | null;
  parentTask: EvalTask | null;
  connection: DBConnection | null;
  visible: boolean;
}

// Events
interface ChildTaskDetailEvents {
  close: () => void;
  viewParent: (parentId: number) => void;
  retry: (taskId: number) => void;
  viewFullLogs: (taskId: number) => void;
  viewSQL: (question: Question) => void;
}
```

### 10.3 建议后续实现时需要注意的技术点

#### 1. 树形列表性能优化

**问题**: 当父任务包含大量子任务（如 BIRD 数据集可能有 100+ 数据库）时，el-table 展开行可能导致性能问题。

**建议**:
- 使用虚拟滚动 (virtual scrolling) 处理大量子任务
- 考虑分页加载子任务，初始只加载前 10 条
- 子任务展开时异步获取详情，避免一次性加载所有数据

```typescript
// 建议的分页加载实现
const loadChildren = async (parentId: number, page = 1) => {
  const response = await evaluationApi.getChildrenByParentId(parentId, {
    page,
    page_size: 10
  });
  return response.data;
};
```

#### 2. WebSocket 连接管理

**问题**: 评测页面可能同时打开多个详情对话框，需要确保 WebSocket 消息正确路由到对应组件。

**建议**:
- 使用 Pinia Store 集中管理 WebSocket 连接
- 组件通过订阅 Store 获取更新，而非直接监听 WebSocket
- 实现消息过滤机制，只处理当前关注任务的更新

```typescript
// 建议的订阅模式
const store = useEvaluationStore();

// 组件订阅特定任务更新
watch(() => store.getTaskById(props.taskId), (newTask) => {
  if (newTask) {
    updateUI(newTask);
  }
}, { deep: true });
```

#### 3. 父子任务状态同步

**问题**: 后端更新父任务统计时可能出现竞态条件，多个子任务同时完成导致统计不准确。

**建议**:
- 使用数据库事务确保统计更新原子性
- 考虑使用数据库触发器自动维护父任务统计
- 前端采用乐观更新 + 定期全量同步的策略

```python
# 建议的数据库触发器方案（PostgreSQL）
CREATE OR REPLACE FUNCTION update_parent_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE eval_tasks
    SET completed_children = (
        SELECT COUNT(*) FROM eval_tasks
        WHERE parent_id = NEW.parent_id AND status = 'completed'
    )
    WHERE id = NEW.parent_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### 4. 导入进度实时展示

**问题**: 大文件导入可能需要数分钟，需要实时展示进度给用户。

**建议**:
- 使用 Server-Sent Events (SSE) 或 WebSocket 推送进度更新
- 前端实现进度条动画，提升用户体验
- 支持取消正在进行的导入操作

```typescript
// 建议的 SSE 实现
const eventSource = new EventSource(`/api/datasets/import/${importId}/progress`);
eventSource.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  updateProgressBar(progress.percent);
};
```

#### 5. 错误处理和重试机制

**问题**: 部分子任务可能因网络或数据库连接问题失败，需要提供批量重试功能。

**建议**:
- 实现指数退避重试策略
- 提供失败原因分类展示
- 支持选择性重试（只重试特定失败的子任务）

```typescript
// 建议的重试逻辑
const retryWithBackoff = async (taskId: number, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await evaluationApi.retryTask(taskId);
      return;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await delay(Math.pow(2, i) * 1000); // 指数退避
    }
  }
};
```

#### 6. 移动端适配

**问题**: 详情对话框在移动端可能显示不全。

**建议**:
- 使用响应式布局，小屏幕下改为抽屉 (Drawer) 组件
- 表格列在小屏幕下精简显示
- 考虑使用折叠面板组织详情内容

```vue
<!-- 响应式适配示例 -->
<template>
  <el-dialog v-if="!isMobile" ... />
  <el-drawer v-else ... />
</template>
```

### 10.4 与 UI 设计文档的对应关系

| UI 设计章节 | 技术实现章节 | 实现状态 |
|-------------|--------------|----------|
| 2.1 评测页面导入入口 | 3.3.1 ImportDialog.vue | ✅ 已定义 |
| 2.2 父子任务列表展示 | 3.3.2 EvaluationList.vue | ✅ 已定义 |
| 2.2.2 父任务行设计 | 3.3.2 EvaluationList.vue | ✅ 已定义 |
| 2.2.3 子任务行设计 | 3.3.2 EvaluationList.vue | ✅ 已定义 |
| 3.1 导入对话框设计 | 3.3.1 ImportDialog.vue | ✅ 已定义 |
| 5.3 父任务详情页面 | 3.3.3 ParentTaskDetail.vue | ✅ 已定义 |
| 5.4 子任务详情页面 | 3.3.4 ChildTaskDetail.vue | ✅ 已定义 |
| 6.4 任务类型标签规范 | 各组件 type="primary/info/success" | ✅ 已定义 |
| 6.5 树形列表组件规范 | 3.3.2 EvaluationList.vue | ✅ 已定义 |
| 6.6 状态指示器规范 | TaskStatus 组件 | ✅ 建议实现 |

### 10.5 后续开发建议

1. **组件拆分**: 建议将 TaskStatus、ProgressBar 等通用组件抽离，便于复用
2. **类型定义**: 建议将 EvalTask、ImportConfig 等类型定义集中到 `types/` 目录
3. **API 封装**: 建议使用 axios 拦截器统一处理错误和 loading 状态
4. **单元测试**: 建议为状态计算逻辑编写单元测试，确保父子任务状态流转正确
5. **文档同步**: 实现过程中如有变更，需同步更新本文档和 UI 设计文档
