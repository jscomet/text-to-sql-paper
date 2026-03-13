# BIRD 数据集导入支持 - UI 设计文档

## 1. 概述

本文档描述 BIRD 数据集导入功能的用户界面设计，包括页面布局、交互流程和组件规范。

---

## 2. 页面布局

### 2.1 评测页面添加导入入口

在评测列表页面（`/evaluation`）右上角添加导入按钮。

```
┌─────────────────────────────────────────────────────────────┐
│  评测任务列表                                    [+ 新建任务] │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 搜索...  │ 状态 ▼ │ 类型 ▼ │            [导入 BIRD 数据] │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 任务名称          状态      进度    创建时间      操作 │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ ...                                               ... │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**按钮样式**:
- 位置：新建任务按钮左侧
- 文本："导入 BIRD 数据"
- 图标：Upload 图标
- 类型：默认按钮（非主要按钮）

---

### 2.2 父子任务列表展示

BIRD 数据集导入后创建父任务和多个子任务，任务列表支持层级展示。

#### 2.2.1 列表布局

```
┌──────────────────────────────────────────────────────────────────────────┐
│  评测任务列表                                                 [+ 新建任务] │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 搜索... │ 状态 ▼ │ 类型 ▼ │ 任务类型 ▼ │           [导入 BIRD 数据] │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ ▼ │ 任务名称              │ 类型   │ 状态   │ 进度    │ 操作       │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │ ▼ │ BIRD-dev-20260314     │ [父任务] │ 进行中 │ ████░░░ │ [详情][开始]│ │
│  │     └─ 11个子任务                                        45%        │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │   │   ├─ california_schools │ [子任务] │ 完成   │ 100%    │ [查看][重试]│ │
│  │   │   ├─ financial          │ [子任务] │ 完成   │ 100%    │ [查看][重试]│ │
│  │   │   ├─ formula_1          │ [子任务] │ 进行中 │ 60%     │ [查看][重试]│ │
│  │   │   ├─ codebase_community │ [子任务] │ 等待中 │ --      │ [查看][重试]│ │
│  │   │   └─ ... (7 more)       │ [子任务] │ ...    │ ...     │ ...        │ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │ ▶ │ 单表查询测试          │ [独立任务]│ 完成   │ 100%    │ [详情][删除]│ │
│  ├────────────────────────────────────────────────────────────────────┤ │
│  │ ▶ │ BIRD-mini-20260310    │ [父任务] │ 完成   │ 100%    │ [详情][开始]│ │
│  │     └─ 5个子任务                                          完成       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 树形列表组件详细设计

**组件选择**: Element Plus `el-table` 展开行 (`expand-row`) 实现层级展示

**表格列定义**:

| 列名 | 字段 | 宽度 | 说明 |
|------|------|------|------|
| 展开图标 | expand | 50px | 自定义展开/折叠图标 |
| 任务名称 | name | auto | 任务显示名称 |
| 类型标签 | type | 100px | 父任务/子任务/独立任务标签 |
| 状态 | status | 100px | 任务当前状态 |
| 进度 | progress | 150px | 进度条 + 百分比 |
| 操作 | actions | 180px | 操作按钮组 |

**核心实现代码结构**:

```vue
<el-table
  :data="taskList"
  row-key="id"
  :expand-row-keys="expandedRows"
  @row-click="handleRowClick"
  :row-class-name="getRowClassName"
>
  <!-- 展开列 -->
  <el-table-column type="expand" width="50">
    <template #default="{ row }">
      <!-- 子任务内嵌表格 -->
      <el-table
        v-if="row.isParent && row.children"
        :data="row.children"
        :show-header="false"
        class="sub-task-table"
      >
        <!-- 子任务列定义 -->
      </el-table>
    </template>
  </el-table-column>

  <!-- 展开图标列 -->
  <el-table-column width="50">
    <template #default="{ row }">
      <el-icon
        v-if="row.isParent"
        :class="['expand-icon', { 'is-expanded': isExpanded(row.id) }]"
        @click.stop="toggleExpand(row)"
      >
        <CaretRight v-if="!isExpanded(row.id)" />
        <CaretBottom v-else />
      </el-icon>
    </template>
  </el-table-column>

  <!-- 任务名称列 -->
  <el-table-column label="任务名称" min-width="200">
    <template #default="{ row }">
      <span :class="{ 'parent-task-name': row.isParent }">
        {{ row.name }}
      </span>
      <span v-if="row.isParent" class="sub-task-count">
        {{ row.children?.length }}个子任务
      </span>
    </template>
  </el-table-column>

  <!-- 其他列... -->
</el-table>
```

**CSS 样式代码**:

```css
/* 父任务行样式 */
.parent-task-row {
  background-color: #ecf5ff !important;
  border-left: 4px solid #409eff;
}

.parent-task-row .cell {
  font-weight: 600;
}

/* 展开图标样式 */
.expand-icon {
  color: #409eff;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.3s;
}

.expand-icon.is-expanded {
  transform: rotate(0deg);
}

/* 子任务行样式 */
.sub-task-row {
  background-color: #ffffff;
}

.sub-task-row .cell {
  padding-left: 32px;
}

/* 树形连接线 */
.tree-connector {
  color: #c0c4cc;
  font-family: monospace;
  margin-right: 8px;
}

/* 独立任务行样式 */
.standalone-task-row {
  background-color: #ffffff;
}

/* 子任务表格样式 */
.sub-task-table {
  width: 100%;
}

.sub-task-table .el-table__row {
  background-color: #fafafa;
}

.sub-task-table .el-table__row:hover {
  background-color: #f5f7fa;
}
```

#### 2.2.3 父任务行设计

**视觉样式**:
- 背景色：`#ecf5ff`（浅蓝色背景）
- 左边框：4px solid `#409eff`（蓝色边框标识）
- 字体：任务名称加粗 (font-weight: 600)

```css
.parent-task-row {
  background-color: #ecf5ff !important;
  border-left: 4px solid #409eff;
}

.parent-task-row .cell {
  font-weight: 600;
}
```

**显示内容**:

| 字段 | 说明 | 示例 |
|------|------|------|
| 展开图标 | ▼ 展开 / ▶ 折叠 | 点击切换子任务显示 |
| 任务名称 | 父任务名称 | BIRD-dev-20260314 |
| 类型标签 | [父任务] 蓝色标签 | `el-tag type="primary"` |
| 子任务数量 | 显示子任务总数 | "11个子任务" |
| 状态 | 总体状态 | 等待中/进行中/完成/失败 |
| 总体进度 | 所有子任务的平均进度 | 45% |
| 操作按钮 | 详情、开始评测 | 详情按钮始终可用 |

**状态计算规则**:
- 所有子任务完成 -> 完成
- 任一子任务失败 -> 失败（显示重试按钮）
- 任一子任务进行中 -> 进行中
- 全部等待中 -> 等待中

#### 2.2.4 子任务行设计

**视觉样式**:
- 缩进：左侧 32px 缩进
- 背景色：白色（与父任务区分）
- 字体：正常字重
- 连接符号：使用树形连接线 `├─` `└─`

```css
.sub-task-row {
  background-color: #ffffff;
  padding-left: 32px;
}

.sub-task-row .tree-connector {
  color: #c0c4cc;
  font-family: monospace;
  margin-right: 8px;
}
```

**显示内容**:

| 字段 | 说明 | 示例 |
|------|------|------|
| 树形连接符 | `├─` 或 `└─` | 标识层级关系 |
| db_id | 数据库ID | california_schools |
| 类型标签 | [子任务] 灰色标签 | `el-tag type="info"` |
| 状态 | 子任务状态 | 等待中/进行中/完成/失败 |
| 进度 | 该子任务的进度 | 60% |
| 操作按钮 | 查看详情、重新评测、查看日志 | 失败时显示重试 |

#### 2.2.5 独立任务行设计

**视觉样式**:
- 背景色：白色
- 无左边框
- 类型标签：[独立任务] 绿色标签 (`el-tag type="success"`)

#### 2.2.6 展开/折叠交互细节

**交互行为**:

| 操作 | 行为 | 实现方式 |
|------|------|----------|
| 点击父任务行任意位置 | 展开/折叠子任务列表 | `@row-click` 事件处理 |
| 点击展开图标 | 展开/折叠子任务列表 | Element Plus 内置功能 |
| 点击操作按钮 | 不触发展开/折叠 | `@click.stop` 阻止冒泡 |

**自定义展开图标**:

```vue
<template #expand="{ row, expanded }">
  <el-icon v-if="row.isParent" class="expand-icon">
    <CaretBottom v-if="expanded" />
    <CaretRight v-else />
  </el-icon>
</template>
```

**展开图标样式**:
- 展开状态：▼ (CaretBottom / `el-icon-caret-bottom`)
- 折叠状态：▶ (CaretRight / `el-icon-caret-right`)
- 颜色：`#409eff`
- 大小：16px

**Vue 组件实现代码**:

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { CaretRight, CaretBottom } from '@element-plus/icons-vue'

const expandedRows = ref<string[]>([])

const isExpanded = (rowId: string) => {
  return expandedRows.value.includes(rowId)
}

const toggleExpand = (row: any) => {
  const index = expandedRows.value.indexOf(row.id)
  if (index > -1) {
    expandedRows.value.splice(index, 1)
  } else {
    expandedRows.value.push(row.id)
  }
}

const handleRowClick = (row: any) => {
  if (row.isParent) {
    toggleExpand(row)
  }
}

const getRowClassName = ({ row }: { row: any }) => {
  if (row.isParent) return 'parent-task-row'
  if (row.isChild) return 'sub-task-row'
  return 'standalone-task-row'
}
</script>
```

**展开行内容**:
- 使用内嵌表格 (`el-table`) 展示子任务
- 内嵌表格隐藏表头 (`:show-header="false"`)
- 子任务数据通过父任务的 `children` 属性传入

**树形连接线实现**:

```vue
<el-table-column label="任务名称" min-width="200">
  <template #default="{ row, $index }">
    <span v-if="row.isChild" class="tree-connector">
      {{ isLastChild(row) ? '└─' : '├─' }}
    </span>
    <span :class="{ 'parent-task-name': row.isParent }">
      {{ row.name }}
    </span>
  </template>
</el-table-column>
```

#### 2.2.7 任务类型筛选器

**筛选器位置**: 位于列表顶部筛选栏，状态筛选器和类型筛选器之间

**筛选器选项**:

| 选项 | 值 | 显示逻辑 |
|------|-----|----------|
| 全部 | 'all' | 显示所有任务（父任务默认展开显示子任务） |
| 父任务 | 'parent' | 显示所有父任务及其子任务 |
| 子任务 | 'child' | 显示所有子任务（平铺展示，不显示父任务行） |
| 独立任务 | 'standalone' | 仅显示独立任务 |

**筛选逻辑说明**:
- **全部**: 显示父任务和独立任务，父任务行可展开查看子任务
- **父任务**: 仅显示父任务行，子任务作为展开内容显示
- **子任务**: 平铺显示所有子任务，不显示父任务行，增加"所属父任务"列
- **独立任务**: 仅显示 `isParent=false` 且 `parentId=null` 的任务

**筛选器 UI 实现**:

```vue
<template>
  <div class="filter-bar">
    <el-input
      v-model="searchKeyword"
      placeholder="搜索任务名称..."
      clearable
      class="search-input"
    />
    <el-select v-model="statusFilter" placeholder="状态" clearable>
      <el-option label="等待中" value="pending" />
      <el-option label="进行中" value="running" />
      <el-option label="完成" value="completed" />
      <el-option label="失败" value="failed" />
    </el-select>
    <el-select v-model="typeFilter" placeholder="类型" clearable>
      <el-option label="BIRD" value="bird" />
      <el-option label="ICED" value="iced" />
      <el-option label="自定义" value="custom" />
    </el-select>
    <!-- 任务类型筛选器 -->
    <el-radio-group v-model="taskTypeFilter" @change="handleFilterChange" size="small">
      <el-radio-button label="all">全部</el-radio-button>
      <el-radio-button label="parent">父任务</el-radio-button>
      <el-radio-button label="child">子任务</el-radio-button>
      <el-radio-button label="standalone">独立任务</el-radio-button>
    </el-radio-group>
  </div>
</template>
```

**CSS 样式**:

```css
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.filter-bar .search-input {
  width: 240px;
}

.filter-bar .el-radio-group {
  margin-left: auto;
}

/* 筛选器激活状态 */
.el-radio-button__original-radio:checked + .el-radio-button__inner {
  background-color: #409eff;
  border-color: #409eff;
  color: #fff;
}
```

**筛选处理逻辑**:

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const taskTypeFilter = ref('all')
const searchKeyword = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// 组合筛选逻辑
const filteredTaskList = computed(() => {
  let result = taskList.value

  // 任务类型筛选
  switch (taskTypeFilter.value) {
    case 'parent':
      result = result.filter(task => task.isParent)
      break
    case 'child':
      // 平铺所有子任务，添加父任务名称字段
      result = result.flatMap(task =>
        (task.children || []).map(child => ({
          ...child,
          parentName: task.name,
          parentId: task.id
        }))
      )
      break
    case 'standalone':
      result = result.filter(task => !task.isParent && !task.parentId)
      break
    default:
      // 'all' - 显示所有父任务和独立任务
      result = result.filter(task => task.isParent || (!task.isParent && !task.parentId))
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(task =>
      task.name.toLowerCase().includes(keyword) ||
      (task.dbId && task.dbId.toLowerCase().includes(keyword))
    )
  }

  // 状态筛选
  if (statusFilter.value) {
    result = result.filter(task => task.status === statusFilter.value)
  }

  // 类型筛选
  if (typeFilter.value) {
    result = result.filter(task => task.type === typeFilter.value)
  }

  return result
})

const handleFilterChange = (value: string) => {
  // 重置展开状态
  expandedRows.value = []
  // 如果是子任务筛选，需要特殊处理表格列
  if (value === 'child') {
    showParentColumn.value = true
  } else {
    showParentColumn.value = false
  }
  // 重新加载数据
  loadTaskList()
}

// 子任务筛选时显示的"所属父任务"列
const showParentColumn = ref(false)
</script>
```

**子任务平铺模式列定义**:

当选择「子任务」筛选时，表格增加「所属父任务」列：

```vue
<el-table-column
  v-if="showParentColumn"
  label="所属父任务"
  min-width="180"
>
  <template #default="{ row }">
    <el-link type="primary" @click="openParentDetail(row.parentId)">
      {{ row.parentName }}
    </el-link>
  </template>
</el-table-column>
```

#### 2.2.8 父任务行操作

**操作按钮**:

| 按钮 | 图标 | 显示条件 | 行为 |
|------|------|----------|------|
| 详情 | Document | 始终显示 | 打开父任务详情对话框 |
| 开始评测 | VideoPlay | 状态为"等待中"或"失败" | 批量开始所有等待中的子任务 |
| 重试 | RefreshLeft | 状态为"失败" | 批量重试所有失败的子任务 |

**操作按钮组代码**:

```vue
<el-table-column label="操作" width="180">
  <template #default="{ row }">
    <!-- 父任务操作按钮 -->
    <el-button-group v-if="row.isParent">
      <el-button size="small" @click.stop="openParentDetail(row)">
        <el-icon><Document /></el-icon> 详情
      </el-button>
      <el-button
        size="small"
        type="primary"
        v-if="row.status === 'pending' || row.status === 'failed'"
        @click.stop="startParentEvaluation(row)"
      >
        <el-icon><VideoPlay /></el-icon> 开始评测
      </el-button>
      <el-button
        size="small"
        type="warning"
        v-if="row.status === 'failed'"
        @click.stop="retryFailedChildren(row)"
      >
        <el-icon><RefreshLeft /></el-icon> 重试
      </el-button>
    </el-button-group>
  </template>
</el-table-column>
```

**批量操作实现**:

```typescript
// 批量开始所有等待中的子任务
const startParentEvaluation = async (parentTask: Task) => {
  const pendingChildren = parentTask.children?.filter(
    child => child.status === 'pending'
  ) || []

  if (pendingChildren.length === 0) {
    ElMessage.warning('没有等待中的子任务')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要开始评测 ${pendingChildren.length} 个子任务吗？`,
      '确认开始评测',
      { type: 'info' }
    )

    // 批量启动子任务
    for (const child of pendingChildren) {
      await startEvaluation(child.id)
    }

    ElMessage.success('已开始批量评测')
    loadTaskList()
  } catch (error) {
    // 用户取消
  }
}

// 批量重试失败的子任务
const retryFailedChildren = async (parentTask: Task) => {
  const failedChildren = parentTask.children?.filter(
    child => child.status === 'failed'
  ) || []

  if (failedChildren.length === 0) {
    ElMessage.warning('没有失败的子任务需要重试')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要重试 ${failedChildren.length} 个失败的子任务吗？`,
      '确认重试',
      { type: 'warning' }
    )

    for (const child of failedChildren) {
      await retryEvaluation(child.id)
    }

    ElMessage.success('已重新启动失败的子任务')
    loadTaskList()
  } catch (error) {
    // 用户取消
  }
}
```

#### 2.2.9 子任务行操作

**操作按钮**:

| 按钮 | 图标 | 显示条件 | 行为 |
|------|------|----------|------|
| 查看详情 | Document | 始终显示 | 打开子任务详情对话框 |
| 重新评测 | RefreshLeft | 状态为"失败"或"完成" | 仅重新执行该子任务 |
| 查看日志 | List | 状态不为"等待中" | 展开行内日志或打开日志抽屉 |

**操作按钮组代码**:

```vue
<el-table-column label="操作" width="180">
  <template #default="{ row }">
    <!-- 子任务操作按钮 -->
    <el-button-group v-if="row.isChild">
      <el-button size="small" @click.stop="openChildDetail(row)">
        <el-icon><Document /></el-icon> 查看详情
      </el-button>
      <el-button
        size="small"
        type="warning"
        v-if="row.status === 'failed' || row.status === 'completed'"
        @click.stop="retryChildEvaluation(row)"
      >
        <el-icon><RefreshLeft /></el-icon> 重新评测
      </el-button>
      <el-button
        size="small"
        v-if="row.status !== 'pending'"
        @click.stop="toggleChildLogs(row)"
      >
        <el-icon><List /></el-icon> 查看日志
      </el-button>
    </el-button-group>
  </template>
</el-table-column>
```

**子任务操作实现**:

```typescript
// 打开子任务详情
const openChildDetail = (childTask: Task) => {
  childDetailVisible.value = true
  currentChildTask.value = childTask
}

// 重新评测子任务
const retryChildEvaluation = async (childTask: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新评测子任务 "${childTask.name}" 吗？当前结果将被覆盖。`,
      '确认重新评测',
      { type: 'warning' }
    )

    await retryEvaluation(childTask.id)
    ElMessage.success('已重新启动评测')
    loadTaskList()
  } catch (error) {
    // 用户取消
  }
}

// 切换行内日志显示
const toggleChildLogs = (childTask: Task) => {
  if (currentLogTaskId.value === childTask.id) {
    currentLogTaskId.value = null
  } else {
    currentLogTaskId.value = childTask.id
    loadTaskLogs(childTask.id)
  }
}
```

**行内日志展示**:

```vue
<el-table-column type="expand" v-if="showInlineLogs">
  <template #default="{ row }">
    <div class="inline-logs" v-if="currentLogTaskId === row.id">
      <el-timeline>
        <el-timeline-item
          v-for="log in row.logs"
          :key="log.id"
          :type="log.type"
          :timestamp="log.time"
        >
          {{ log.message }}
        </el-timeline-item>
      </el-timeline>
    </div>
  </template>
</el-table-column>
```

**CSS 样式**:

```css
.inline-logs {
  padding: 16px 32px;
  background-color: #f5f7fa;
  border-left: 3px solid #409eff;
}
```

#### 2.2.10 交互汇总

| 操作 | 行为 |
|------|------|
| 点击父任务行 | 展开/折叠子任务列表 |
| 点击父任务"详情" | 打开父任务详情对话框 |
| 点击父任务"开始评测" | 批量开始所有等待中的子任务 |
| 点击子任务"查看详情" | 打开子任务详情对话框 |
| 点击子任务"重新评测" | 仅重新执行该子任务 |
| 点击子任务"查看日志" | 展开行内日志或打开日志抽屉 |
| 点击子任务 db_id | 跳转到对应数据库连接详情 |
| 切换任务类型筛选 | 按筛选条件重新渲染列表 |

---

## 3. 导入对话框设计

### 3.1 对话框整体布局

```
┌─────────────────────────────────────────────────────────────┐
│  导入 BIRD 数据集                                    [X]    │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│  [上传 Zip 文件]  [本地目录]                                │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  [Tab 内容区域]                                            │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  评测配置                                                  │
│  ─────────────────────────────────────────────────────    │
│  API Key:    [选择 API Key                    ▼]          │
│  评测模式:   [贪婪搜索                        ▼]          │
│  Temperature: [====●====] 0.7                               │
│  Max Tokens: [2000        ]                                 │
│                                                            │
├─────────────────────────────────────────────────────────────┤
│                                         [取消]  [开始导入]  │
└─────────────────────────────────────────────────────────────┘
```

**尺寸**:
- 宽度：600px
- 最大高度：80vh
- 可滚动内容区域

---

### 3.2 Tab 1: 上传 Zip 文件

```
┌─────────────────────────────────────────────────────────────┐
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                                                      │ │
│  │              [Upload 图标]                            │ │
│  │                                                      │ │
│  │         拖拽 zip 文件到此处，或点击上传                │ │
│  │                                                      │ │
│  │         支持 BIRD 数据集 zip 文件（最大 1GB）          │ │
│  │                                                      │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  已选择文件: bird_dev.zip (156 MB)                         │
│                                                            │
│  [移除]                                                    │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

**拖拽区域样式**:
- 边框：2px dashed #dcdfe6
- 圆角：8px
- 背景：#f5f7fa（hover 时 #ecf5ff）
- 高度：200px

**文件信息显示**:
- 文件名
- 文件大小
- 移除按钮

---

### 3.3 Tab 2: 本地目录

```
┌─────────────────────────────────────────────────────────────┐
│                                                            │
│  数据目录路径:                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │ /data/bird/dev_20240627                            │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  [验证路径]                                                │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  目录验证结果:                                             │
│  ✅ dev.json 存在 (1534 条问题)                             │
│  ✅ dev_databases/ 目录存在                                │
│  ✅ 发现 11 个数据库:                                       │
│     - california_schools                                   │
│     - financial                                            │
│     - ...                                                  │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

**路径输入框**:
- 占位符：请输入 BIRD 数据集的绝对路径
- 验证按钮：检查路径有效性

**验证结果样式**:
- 成功：绿色勾选 + 详细信息
- 失败：红色错误 + 错误原因

---

## 4. 导入进度对话框

### 4.1 进度展示

```
┌─────────────────────────────────────────────────────────────┐
│  正在导入 BIRD 数据集...                           [X]    │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│  步骤进度:                                                 │
│                                                            │
│  1. ✅ 验证数据集格式                                       │
│  2. ✅ 解析数据库列表 (11 个数据库)                         │
│  3. 🔄 创建数据库连接 (7/11)                                │
│  4. ⏳ 创建评测任务                                         │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │████████████████████████████░░░░░░░░░░░░░░░░░░░░░░│   │
│  └────────────────────────────────────────────────────┘   │
│  总体进度: 65%                                             │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  日志:                                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │ [10:23:45] 验证数据集格式完成                          │   │
│  │ [10:23:46] 发现 11 个数据库...                         │   │
│  │ [10:23:47] 创建连接 california_schools (ID: 21)        │   │
│  │ ...                                                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
├─────────────────────────────────────────────────────────────┤
│                                                    [取消]   │
└─────────────────────────────────────────────────────────────┘
```

**步骤指示器**:
- 已完成：绿色勾选图标
- 进行中：蓝色旋转图标
- 待开始：灰色圆点

**日志区域**:
- 带滚动条的文本区域
- 时间戳 + 日志内容
- 自动滚动到最新

---

## 5. 任务详情对话框设计

### 5.1 对话框通用规范

**尺寸规范**:

| 对话框类型 | 宽度 | 最大高度 | 说明 |
|-----------|------|----------|------|
| 父任务详情 | 900px | 85vh | 宽屏展示子任务列表 |
| 子任务详情 | 800px | 85vh | 标准宽度展示问题列表 |
| 导入结果 | 600px | 80vh | 标准对话框 |

**通用样式**:

```css
/* 父任务详情对话框 */
.parent-task-dialog .el-dialog {
  width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.parent-task-dialog .el-dialog__body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

/* 子任务详情对话框 */
.child-task-dialog .el-dialog {
  width: 800px;
  max-height: 85vh;
}

/* 对话框头部 */
.task-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-bottom: 1px solid #e4e7ed;
  border-radius: 8px 8px 0 0;
}
```

---

## 6. 导入结果对话框

### 5.1 成功状态

```
┌─────────────────────────────────────────────────────────────┐
│  导入完成                                          [X]    │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│                      [Success 图标]                         │
│                                                            │
│                    BIRD 数据集导入成功                      │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  父任务信息:                                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 父任务 ID:   42                                      │   │
│  │ 任务名称:    BIRD-dev-20260314                      │   │
│  │ 任务类型:    [父任务]                                │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  导入统计:                                                 │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 数据库连接:  11 个                                   │   │
│  │ 子任务数量:  11 个                                   │   │
│  │ 总问题数:    1534 条                                 │   │
│  │ 数据目录:    /data/bird/bird_20260314_143052        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  子任务概览:                                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 数据库ID              │ 状态   │ 问题数  │ 操作    │   │
│  ├────────────────────────────────────────────────────┤   │
│  │ california_schools    │ ✅ 完成 │ 120    │ [查看]  │   │
│  │ financial             │ ✅ 完成 │ 98     │ [查看]  │   │
│  │ formula_1             │ ⏳ 等待 │ 156    │ [查看]  │   │
│  │ ...                   │ ...    │ ...    │ ...     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  接下来您可以:                                             │
│                                                            │
│  [查看父任务详情]  [查看评测任务]  [查看数据库连接]  [开始评测] │
│                                                            │
├─────────────────────────────────────────────────────────────┤
│                                                    [关闭]   │
└─────────────────────────────────────────────────────────────┘
```

**新增元素说明**:

| 元素 | 说明 |
|------|------|
| 父任务信息区块 | 显示父任务ID和名称，标识为父任务类型 |
| 子任务概览表格 | 列出所有创建的子任务及其状态 |
| 子任务"查看"按钮 | 点击跳转到对应子任务详情页 |
| "查看父任务详情"按钮 | 打开父任务详情对话框 |

**交互说明**:
- 点击子任务行或"查看"按钮：打开子任务详情对话框
- 点击"查看父任务详情"：打开父任务详情对话框
- 点击"开始评测"：批量启动所有子任务评测

---

### 5.3 父任务详情页面

父任务详情使用对话框形式展示，包含总体统计、进度可视化和子任务列表。

#### 5.3.1 对话框布局

```
┌────────────────────────────────────────────────────────────────────────────┐
│  父任务详情                                                    [X] [↗]    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                                                                      │ │
│  │   BIRD-dev-20260314                                    [父任务]      │ │
│  │   状态: [进行中 ●]                                                    │ │
│  │                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────┬──────────────────┬──────────────────┐               │
│  │   总问题数        │   总体正确率      │   完成进度        │               │
│  │                  │                  │                  │               │
│  │    1,534        │     68.5%        │    7/11 个子任务  │               │
│  │                  │                  │                  │               │
│  └──────────────────┴──────────────────┴──────────────────┘               │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  总体进度:  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░  58%        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  子任务状态分布:                                                      │ │
│  │                                                                      │ │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │   │   完成   │  │  进行中  │  │  等待中  │  │   失败   │            │ │
│  │   │    5     │  │    1     │  │    4     │  │    1     │            │ │
│  │   │  #67c23a │  │ #409eff  │  │ #909399  │  │ #f56c6c  │            │ │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘            │ │
│  │                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│  子任务列表:                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 数据库ID           │ 连接名称    │ 状态   │ 问题数    │ 正确率 │ 操作 │   │
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │ california_schools │ schools_db  │ ✅完成 │ 120/120   │ 72.5%  │详情日志│   │
│  │ financial          │ finance_db  │ ✅完成 │ 98/98     │ 81.2%  │详情日志│   │
│  │ formula_1          │ f1_db       │ 🔄进行 │ 45/156    │ --     │详情日志│   │
│  │ codebase_community │ code_db     │ ⏳等待 │ 0/234     │ --     │详情日志│   │
│  │ european_football  │ football_db │ ❌失败 │ 89/167    │ 53.3%  │详情日志│   │
│  │ ...                │ ...         │ ...    │ ...       │ ...    │ ...  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│                              [批量重试失败任务]  [开始全部]  [关闭]         │
└────────────────────────────────────────────────────────────────────────────┘
```

**对话框尺寸**:
- 宽度：900px
- 最大高度：85vh
- 内容区域可滚动

**Vue 组件结构**:

```vue
<template>
  <el-dialog
    v-model="visible"
    title="父任务详情"
    width="900px"
    :close-on-click-modal="false"
    class="parent-task-dialog"
    destroy-on-close
  >
    <div class="parent-task-detail">
      <!-- 顶部信息区 -->
      <div class="header-section">
        <div class="task-title">
          <h2>{{ parentTask.name }}</h2>
          <el-tag type="primary" size="large">父任务</el-tag>
        </div>
        <div class="task-status">
          <status-indicator :status="parentTask.status" />
        </div>
      </div>

      <!-- 统计卡片区 -->
      <div class="stats-section">
        <stat-card
          title="总问题数"
          :value="totalQuestions"
          icon="Document"
        />
        <stat-card
          title="总体正确率"
          :value="overallAccuracy"
          :suffix="'%'"
          icon="CircleCheck"
        />
        <stat-card
          title="完成进度"
          :value="completedChildren"
          :suffix="`/${totalChildren} 个子任务`"
          icon="TrendCharts"
        />
      </div>

      <!-- 总体进度条 -->
      <div class="progress-section">
        <div class="progress-label">总体进度</div>
        <el-progress
          :percentage="overallProgress"
          :stroke-width="20"
          :color="progressColor"
          show-text
        />
      </div>

      <!-- 子任务状态分布 -->
      <div class="status-distribution">
        <div class="distribution-label">子任务状态分布</div>
        <div class="status-cards">
          <status-count-card
            v-for="item in statusDistribution"
            :key="item.status"
            :status="item.status"
            :count="item.count"
            :active="activeStatusFilter === item.status"
            @click="filterByStatus(item.status)"
          />
        </div>
      </div>

      <!-- 子任务列表 -->
      <div class="children-list-section">
        <div class="section-title">子任务列表</div>
        <el-table
          :data="filteredChildren"
          stripe
          size="small"
          class="children-table"
        >
          <!-- 表格列定义 -->
        </el-table>
      </div>
    </div>

    <!-- 底部操作区 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button
          type="warning"
          :disabled="failedCount === 0"
          @click="batchRetryFailed"
        >
          <el-icon><RefreshLeft /></el-icon>
          批量重试失败任务 ({{ failedCount }})
        </el-button>
        <el-button
          type="primary"
          :disabled="pendingCount === 0"
          @click="startAllPending"
        >
          <el-icon><VideoPlay /></el-icon>
          开始全部 ({{ pendingCount }})
        </el-button>
        <el-button @click="visible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>
```

#### 5.3.2 顶部信息区

**布局结构**:

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   BIRD-dev-20260314                                    [父任务]      │
│   状态: [进行中 ●]                                                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**显示内容**:

| 字段 | 说明 | 样式 |
|------|------|------|
| 任务名称 | 父任务完整名称 | 20px, font-weight: 600, color: #303133 |
| 任务类型标签 | [父任务] 蓝色标签 | el-tag type="primary" size="large" |
| 状态 | 实时状态 + 状态图标 | 状态颜色对应 |

**CSS 样式**:

```css
.header-section {
  background: linear-gradient(135deg, #ecf5ff 0%, #f5f7fa 100%);
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 20px;
  border-left: 4px solid #409eff;
}

.task-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-title h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: 500;
}

.status-indicator.pending {
  color: #909399;
  background-color: #f4f4f5;
}

.status-indicator.running {
  color: #409eff;
  background-color: #ecf5ff;
}

.status-indicator.completed {
  color: #67c23a;
  background-color: #f0f9eb;
}

.status-indicator.failed {
  color: #f56c6c;
  background-color: #fef0f0;
}
```

#### 5.3.3 统计卡片区

**布局结构**:

```
┌──────────────────┬──────────────────┬──────────────────┐
│   总问题数        │   总体正确率      │   完成进度        │
│                  │                  │                  │
│    1,534        │     68.5%        │    7/11 个子任务  │
│                  │                  │                  │
└──────────────────┴──────────────────┴──────────────────┘
```

**三个统计卡片**:

| 卡片 | 字段 | 内容 | 计算方式 |
|------|------|------|----------|
| 总问题数 | total_questions | 所有子任务的 question_count 总和 | `sum(child.question_count)` |
| 总体正确率 | overall_accuracy | 已完成子任务的平均正确率 | `avg(completed_child.accuracy)` |
| 完成进度 | completion_progress | 完成子任务数 / 总子任务数 | `completed_count / total_count` |

**Vue 组件实现**:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { Document, CircleCheck, TrendCharts } from '@element-plus/icons-vue'

const props = defineProps<{
  parentTask: ParentTask
}>()

// 总问题数
const totalQuestions = computed(() => {
  return props.parentTask.children?.reduce(
    (sum, child) => sum + (child.questionCount || 0), 0
  ) || 0
})

// 总体正确率
const overallAccuracy = computed(() => {
  const completedChildren = props.parentTask.children?.filter(
    child => child.status === 'completed' && child.accuracy != null
  ) || []

  if (completedChildren.length === 0) return 0

  const totalAccuracy = completedChildren.reduce(
    (sum, child) => sum + (child.accuracy || 0), 0
  )
  return (totalAccuracy / completedChildren.length).toFixed(1)
})

// 完成进度
const completedChildren = computed(() => {
  return props.parentTask.children?.filter(
    child => child.status === 'completed'
  ).length || 0
})

const totalChildren = computed(() => {
  return props.parentTask.children?.length || 0
})
</script>
```

**CSS 样式**:

```css
.stats-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: box-shadow 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card .stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

.stat-card .stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-card .stat-suffix {
  font-size: 14px;
  color: #909399;
  margin-left: 4px;
}
```

#### 5.3.4 总体进度条

**组件**: Element Plus `el-progress`

**配置参数**:

| 属性 | 值 | 说明 |
|------|-----|------|
| :percentage | overallProgress | 进度百分比 (0-100) |
| :stroke-width | 20 | 进度条高度 |
| :color | progressColor | 根据进度动态变化颜色 |
| show-text | true | 显示百分比文本 |

**进度条颜色规则**:

```typescript
const progressColor = computed(() => {
  const progress = overallProgress.value
  if (progress < 30) return '#f56c6c'  // 红色
  if (progress < 70) return '#e6a23c'  // 黄色
  return '#67c23a'  // 绿色
})

const overallProgress = computed(() => {
  if (totalQuestions.value === 0) return 0
  const processed = props.parentTask.children?.reduce(
    (sum, child) => sum + (child.processedCount || 0), 0
  ) || 0
  return Math.round((processed / totalQuestions.value) * 100)
})
```

**CSS 样式**:

```css
.progress-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 500;
}

.progress-section .el-progress {
  margin-top: 8px;
}

.progress-section .el-progress__text {
  font-size: 16px;
  font-weight: 600;
}
```

#### 5.3.5 子任务状态分布区

**布局结构**:

```
┌──────────────────────────────────────────────────────────────────────┐
│  子任务状态分布:                                                      │
│                                                                      │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│   │   完成   │  │  进行中  │  │  等待中  │  │   失败   │            │
│   │    5     │  │    1     │  │    4     │  │    1     │            │
│   │  #67c23a │  │ #409eff  │  │ #909399  │  │ #f56c6c  │            │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**状态分布卡片**:

| 状态 | 颜色 | 图标 | 说明 |
|------|------|------|------|
| 完成 | #67c23a (绿色) | CircleCheck | 已完成的子任务数量 |
| 进行中 | #409eff (蓝色) | Loading | 正在执行的子任务数量 |
| 等待中 | #909399 (灰色) | Timer | 等待执行的子任务数量 |
| 失败 | #f56c6c (红色) | CircleClose | 执行失败的子任务数量 |

**Vue 组件实现**:

```vue
<script setup lang="ts">
const statusDistribution = computed(() => {
  const children = props.parentTask.children || []
  return [
    { status: 'completed', label: '完成', count: countByStatus(children, 'completed'), color: '#67c23a', icon: 'CircleCheck' },
    { status: 'running', label: '进行中', count: countByStatus(children, 'running'), color: '#409eff', icon: 'Loading' },
    { status: 'pending', label: '等待中', count: countByStatus(children, 'pending'), color: '#909399', icon: 'Timer' },
    { status: 'failed', label: '失败', count: countByStatus(children, 'failed'), color: '#f56c6c', icon: 'CircleClose' }
  ]
})

const countByStatus = (children: ChildTask[], status: string) => {
  return children.filter(child => child.status === status).length
}

const activeStatusFilter = ref<string | null>(null)

const filterByStatus = (status: string) => {
  activeStatusFilter.value = activeStatusFilter.value === status ? null : status
}
</script>
```

**CSS 样式**:

```css
.status-distribution {
  margin-bottom: 20px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.distribution-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 500;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.status-count-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.status-count-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.status-count-card.active {
  border-color: currentColor;
}

.status-count-card .status-label {
  font-size: 14px;
  margin-bottom: 8px;
}

.status-count-card .status-count {
  font-size: 24px;
  font-weight: 600;
}

.status-count-card.completed {
  background-color: #f0f9eb;
  color: #67c23a;
}

.status-count-card.running {
  background-color: #ecf5ff;
  color: #409eff;
}

.status-count-card.pending {
  background-color: #f4f4f5;
  color: #909399;
}

.status-count-card.failed {
  background-color: #fef0f0;
  color: #f56c6c;
}
```

#### 5.3.6 子任务列表表格

**表格列定义**:

| 列名 | 字段 | 宽度 | 说明 |
|------|------|------|------|
| 数据库ID | db_id | 160px | 可点击跳转连接详情 |
| 连接名称 | connection_name | 120px | 数据库连接名称 |
| 状态 | status | 100px | 带图标的文本 |
| 问题数 | progress | 120px | processed/total 格式 |
| 正确率 | accuracy | 100px | 仅完成/失败任务显示 |
| 操作 | actions | 150px | 查看详情、查看日志 |

**Vue 组件实现**:

```vue
<template>
  <el-table
    :data="filteredChildren"
    stripe
    size="small"
    class="children-table"
    v-loading="loading"
  >
    <!-- 数据库ID列 -->
    <el-table-column label="数据库ID" min-width="160">
      <template #default="{ row }">
        <el-link
          type="primary"
          @click="goToConnection(row.connectionId)"
        >
          {{ row.dbId }}
        </el-link>
      </template>
    </el-table-column>

    <!-- 连接名称列 -->
    <el-table-column label="连接名称" min-width="120">
      <template #default="{ row }">
        {{ row.connectionName || '-' }}
      </template>
    </el-table-column>

    <!-- 状态列 -->
    <el-table-column label="状态" width="100">
      <template #default="{ row }">
        <status-tag :status="row.status" />
      </template>
    </el-table-column>

    <!-- 问题数列 -->
    <el-table-column label="问题数" width="120">
      <template #default="{ row }">
        <span class="progress-text">
          {{ row.processedCount || 0 }}/{{ row.questionCount || 0 }}
        </span>
      </template>
    </el-table-column>

    <!-- 正确率列 -->
    <el-table-column label="正确率" width="100">
      <template #default="{ row }">
        <span v-if="row.accuracy != null" :class="['accuracy-text', getAccuracyClass(row.accuracy)]">
          {{ row.accuracy.toFixed(1) }}%
        </span>
        <span v-else class="accuracy-empty">--</span>
      </template>
    </el-table-column>

    <!-- 操作列 -->
    <el-table-column label="操作" width="150" fixed="right">
      <template #default="{ row }">
        <el-button-group>
          <el-button
            size="small"
            @click="openChildDetail(row)"
          >
            <el-icon><Document /></el-icon>
            详情
          </el-button>
          <el-button
            size="small"
            v-if="row.status !== 'pending'"
            @click="openChildLogs(row)"
          >
            <el-icon><List /></el-icon>
            日志
          </el-button>
        </el-button-group>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
const filteredChildren = computed(() => {
  let children = props.parentTask.children || []
  if (activeStatusFilter.value) {
    children = children.filter(child => child.status === activeStatusFilter.value)
  }
  return children
})

const getAccuracyClass = (accuracy: number) => {
  if (accuracy >= 80) return 'accuracy-high'
  if (accuracy >= 60) return 'accuracy-medium'
  return 'accuracy-low'
}

const goToConnection = (connectionId: number) => {
  router.push(`/connections/${connectionId}`)
}

const openChildDetail = (child: ChildTask) => {
  emit('openChild', child)
}

const openChildLogs = (child: ChildTask) => {
  emit('openLogs', child)
}
</script>
```

**CSS 样式**:

```css
.children-list-section {
  margin-top: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.children-table {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.progress-text {
  font-family: monospace;
  color: #606266;
}

.accuracy-text {
  font-weight: 600;
}

.accuracy-high {
  color: #67c23a;
}

.accuracy-medium {
  color: #e6a23c;
}

.accuracy-low {
  color: #f56c6c;
}

.accuracy-empty {
  color: #c0c4cc;
}
```

#### 5.3.7 底部批量操作区

**按钮布局**:

```
┌────────────────────────────────────────────────────────────────────────────┤
│                              [批量重试失败任务]  [开始全部]  [关闭]         │
└────────────────────────────────────────────────────────────────────────────┘
```

**按钮规格**:

| 按钮 | 类型 | 禁用条件 | 说明 |
|------|------|----------|------|
| 批量重试失败任务 | el-button type="warning" | failedCount === 0 | 仅重试状态为失败的子任务 |
| 开始全部 | el-button type="primary" | pendingCount === 0 | 开始所有等待中的子任务 |
| 关闭 | el-button | 无 | 关闭对话框 |

**Vue 组件实现**:

```vue
<template #footer>
  <div class="dialog-footer">
    <el-button
      type="warning"
      :disabled="failedCount === 0"
      :loading="retryLoading"
      @click="batchRetryFailed"
    >
      <el-icon><RefreshLeft /></el-icon>
      批量重试失败任务
      <el-tag v-if="failedCount > 0" type="danger" size="small" effect="dark">
        {{ failedCount }}
      </el-tag>
    </el-button>

    <el-button
      type="primary"
      :disabled="pendingCount === 0"
      :loading="startLoading"
      @click="startAllPending"
    >
      <el-icon><VideoPlay /></el-icon>
      开始全部
      <el-tag v-if="pendingCount > 0" type="info" size="small" effect="dark">
        {{ pendingCount }}
      </el-tag>
    </el-button>

    <el-button @click="visible = false">关闭</el-button>
  </div>
</template>

<script setup lang="ts">
const failedCount = computed(() => {
  return props.parentTask.children?.filter(
    child => child.status === 'failed'
  ).length || 0
})

const pendingCount = computed(() => {
  return props.parentTask.children?.filter(
    child => child.status === 'pending'
  ).length || 0
})

const batchRetryFailed = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要批量重试 ${failedCount.value} 个失败的子任务吗？`,
      '确认批量重试',
      { type: 'warning' }
    )

    retryLoading.value = true
    const failedChildren = props.parentTask.children?.filter(
      child => child.status === 'failed'
    ) || []

    for (const child of failedChildren) {
      await retryEvaluation(child.id)
    }

    ElMessage.success('已批量重试失败的子任务')
    emit('refresh')
  } catch (error) {
    // 用户取消
  } finally {
    retryLoading.value = false
  }
}

const startAllPending = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要开始 ${pendingCount.value} 个等待中的子任务吗？`,
      '确认开始评测',
      { type: 'info' }
    )

    startLoading.value = true
    await startParentEvaluation(props.parentTask.id)

    ElMessage.success('已开始批量评测')
    emit('refresh')
  } catch (error) {
    // 用户取消
  } finally {
    startLoading.value = false
  }
}
</script>
```

**CSS 样式**:

```css
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
}

.dialog-footer .el-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dialog-footer .el-tag {
  margin-left: 4px;
}
```

**交互说明**:

| 操作 | 行为 | 确认对话框 |
|------|------|------------|
| 点击 db_id | 跳转到数据库连接详情页 | 否 |
| 点击"详情" | 打开子任务详情对话框 | 否 |
| 点击"日志" | 打开日志查看抽屉 | 否 |
| 点击"批量重试失败任务" | 仅重试状态为失败的子任务 | 是 |
| 点击"开始全部" | 开始所有等待中的子任务 | 是 |
| 点击状态分布卡片 | 筛选对应状态的子任务 | 否 |

---

### 5.4 子任务详情页面

子任务详情对话框展示单个数据库的评测详情，包含父任务关联、数据库信息和问题列表。

#### 5.4.1 对话框布局

```
┌────────────────────────────────────────────────────────────────────────────┐
│  子任务详情                                                    [X] [↗]    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  父任务:  BIRD-dev-20260314  [查看父任务 →]           [子任务]        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                                                                      │ │
│  │   california_schools                                   [进行中 ●]    │ │
│  │                                                                      │ │
│  │   数据库连接: schools_db (ID: 23)                     [查看连接 →]   │ │
│  │                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────┬──────────────────┬──────────────────┐               │
│  │   总问题数        │   已处理          │   正确率          │               │
│  │                  │                  │                  │               │
│  │     120         │     85/120       │     72.5%        │               │
│  │                  │                  │                  │               │
│  └──────────────────┴──────────────────┴──────────────────┘               │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  当前进度:  ████████████████████████░░░░░░░░░░░░░░░░░░░░  71%        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│  评测问题列表:                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 序号 │ 问题预览              │ 状态   │ 执行时间 │ 正确 │ 操作      │   │
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │  1   │ How many schools...   │ ✅完成 │  2.3s   │  ✓   │ [查看SQL] │   │
│  │  2   │ What is the total...  │ ✅完成 │  1.8s   │  ✓   │ [查看SQL] │   │
│  │  3   │ List all students...  │ ✅完成 │  3.1s   │  ✗   │ [查看SQL] │   │
│  │  4   │ Find the average...   │ 🔄进行 │   --    │  --  │ [查看]    │   │
│  │  5   │ Which teacher...      │ ⏳等待 │   --    │  --  │ [查看]    │   │
│  │ ...  │ ...                   │ ...    │  ...    │ ...  │ ...       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│  最近日志:                                                                 │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ [10:23:45] 开始评测问题 #4: Find the average...                     │   │
│  │ [10:23:46] 生成SQL: SELECT AVG(score) FROM ...                      │   │
│  │ [10:23:47] 执行SQL成功，返回结果: 85.6                              │   │
│  │ [10:23:48] 验证结果: 正确                                           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                    [重新评测]  [查看完整日志]  [关闭]       │
└────────────────────────────────────────────────────────────────────────────┘
```

#### 5.4.2 父任务关联区

**显示格式**:
```
父任务: {parent_name} [查看父任务 →]    [子任务]
```

**显示内容**:

| 字段 | 说明 | 样式 | 交互 |
|------|------|------|------|
| 父任务标签 | [父任务] 蓝色标签 | el-tag type="primary" | 标识父任务类型 |
| 子任务标签 | [子任务] 灰色标签 | el-tag type="info" | 标识当前任务类型 |
| 父任务名称 | 所属父任务的完整名称 | 普通文本，可点击 | 点击跳转父任务详情 |
| 查看父任务链接 | [查看父任务 →] | 蓝色链接样式 | 点击打开父任务详情对话框 |

**布局要求**:
- 父任务名称显示在左侧，格式为「父任务: {parent_name}」
- 「查看父任务 →」链接紧跟父任务名称，使用蓝色文字和箭头图标
- [子任务] 标签显示在右侧，用于标识当前对话框类型
- 整体使用分割线或背景色与下方内容区分

**交互说明**:
- 点击「查看父任务 →」链接：关闭当前子任务详情，打开对应父任务详情对话框
- 点击父任务名称：同上，跳转至父任务详情

#### 5.4.3 数据库信息区

**显示格式**:
```
california_schools                                    [进行中 ●]

数据库连接: schools_db (ID: 23)                      [查看连接 →]
```

**显示内容**:

| 字段 | 说明 | 样式 | 交互 |
|------|------|------|------|
| db_id | 数据库ID (如 california_schools) | 24px, 加粗, 大字体突出显示 | 只读 |
| 状态指示器 | 彩色圆点 + 状态文本 | 状态对应颜色 | 实时更新 |
| 连接信息 | 「数据库连接: {connection_name} (ID: {id})」 | 普通文本 | 连接名称可点击 |
| 查看连接链接 | [查看连接 →] | 蓝色链接样式 | 点击跳转连接详情页 |

**状态指示器颜色**:

| 状态 | 圆点颜色 | 文本颜色 |
|------|----------|----------|
| 等待中 | #909399 (灰色) | #909399 |
| 进行中 | #409eff (蓝色) | #409eff |
| 完成 | #67c23a (绿色) | #67c23a |
| 失败 | #f56c6c (红色) | #f56c6c |

**交互说明**:
- 点击连接名称或「查看连接 →」：跳转到数据库连接详情页面 `/connections/{id}`
- 状态指示器实时更新，反映当前子任务的执行状态

#### 5.4.4 统计卡片区

**三个统计卡片布局**:

| 卡片 | 字段 | 内容 | 样式 |
|------|------|------|------|
| 总问题数 | total_questions | 该子任务的 question_count | 24px 加粗数字 |
| 已处理 | processed_questions | processed / total 格式 | 24px 加粗数字 + 分母 |
| 正确率 | accuracy | correct_count / processed 百分比 | 24px 加粗数字 + %符号 |

**卡片样式**:
- 使用 `el-card` 组件或自定义卡片样式
- 卡片宽度：三等分布局
- 卡片内边距：16px
- 数字颜色：#303133
- 标签文字：14px, #606266

**计算规则**:
- 总问题数：直接显示 `question_count` 字段值
- 已处理：格式为 `{processed_questions}/{total_questions}`
- 正确率：`correct_count / processed_questions * 100`，保留1位小数，未处理时显示 "--"

#### 5.4.5 当前进度条

**组件**: 使用 Element Plus `el-progress` 组件

**配置参数**:

| 属性 | 值 | 说明 |
|------|-----|------|
| :percentage | progress_percent | 进度百分比 |
| :stroke-width | 16 | 进度条高度 |
| :color | 自定义颜色方法 | 根据进度变化颜色 |
| show-text | true | 显示百分比文本 |
| status | - | 使用自定义颜色替代 |

**进度条颜色规则**:

| 进度范围 | 颜色 |
|----------|------|
| 0-30% | #f56c6c (红色) |
| 30-70% | #e6a23c (黄色) |
| 70-100% | #67c23a (绿色) |

**显示格式**:
```
当前进度:  ████████████████████████░░░░░░░░░░░░░░░░░░░░  71%
           └─ 已处理: 85 / 120
```

**附加信息**:
- 进度条下方显示「已处理: X / Y」文本
- 文本颜色：#909399
- 文本字号：12px

#### 5.4.6 评测问题列表表格

**表格列定义**:

| 列名 | 字段 | 宽度 | 说明 |
|------|------|------|------|
| 序号 | index | 60px | 从1开始的序号 |
| 问题预览 | question_preview | 300px | 问题文本前30字符，超出截断显示... |
| 状态 | status | 100px | 等待中/进行中/完成，带状态图标 |
| 执行时间 | execution_time | 100px | 完成时显示耗时(s)，格式如 "2.3s" |
| 正确 | is_correct | 80px | ✓ (绿色) 或 ✗ (红色) 图标 |
| 操作 | actions | 120px | 查看SQL/结果按钮 |

**行展开功能**:

点击行或「查看SQL」按钮展开，显示以下内容：

```
┌────────────────────────────────────────────────────────────────────────┐
│ 问题详情                                                               │
├────────────────────────────────────────────────────────────────────────┤
│ 完整问题:                                                              │
│ How many schools are there in the state of California?                 │
│                                                                        │
│ 生成的 SQL:                                                            │
│ ┌──────────────────────────────────────────────────────────────────┐  │
│ │ SELECT COUNT(*) FROM schools WHERE state = 'CA'                  │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│ 预期的 SQL:                                                            │
│ ┌──────────────────────────────────────────────────────────────────┐  │
│ │ SELECT COUNT(DISTINCT school_name) FROM schools WHERE state = 'CA'│  │
│ └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│ 执行结果:                                                              │
│ 执行结果: 正确 (预期: 1250, 实际: 1250)                                │
└────────────────────────────────────────────────────────────────────────┘
```

**展开行样式**:
- 背景色：#f5f7fa
- 内边距：16px
- SQL 代码块使用等宽字体，带边框和背景色
- 生成的 SQL 和预期 SQL 并排或上下排列，便于对比

**分页配置**:

| 属性 | 值 |
|------|-----|
| page-size | 20 |
| layout | "total, prev, pager, next, jumper" |
| :total | total_questions |

**操作按钮状态**:

| 状态 | 按钮显示 | 行为 |
|------|----------|------|
| 等待中 | [查看] 禁用 | 点击提示"任务尚未开始" |
| 进行中 | [查看] | 点击展开显示当前进度 |
| 完成 | [查看SQL] | 点击展开显示SQL对比 |

#### 5.4.7 日志区域

**区域标题**: 「最近日志」

**样式规格**:

| 属性 | 值 |
|------|-----|
| 高度 | 固定 200px |
| 背景色 | #f5f7fa |
| 边框 | 1px solid #e4e7ed |
| 圆角 | 4px |
| 内边距 | 12px |
| 溢出处理 | overflow-y: auto |

**日志条目格式**:
```
[HH:MM:SS] [级别] 日志内容
```

**日志级别颜色**:

| 级别 | 颜色 | 示例 |
|------|------|------|
| info | #909399 (灰色) | [10:23:45] 开始评测问题 #4 |
| warning | #e6a23c (黄色) | [10:23:46] 生成SQL超时，使用默认配置 |
| error | #f56c6c (红色) | [10:23:47] 执行SQL失败: Table not found |
| success | #67c23a (绿色) | [10:23:48] 验证结果: 正确 |

**自动滚动**:
- 新日志加入时自动滚动到底部
- 用户手动滚动时暂停自动滚动
- 提供「滚动到最新」按钮

**查看完整日志按钮**:
- 位置：日志区域右上角
- 文本：[查看完整日志]
- 样式：el-button type="text" size="small"
- 点击：打开完整日志查看器对话框

#### 5.4.8 底部操作区

**按钮布局**:

```
┌────────────────────────────────────────────────────────────────────────────┤
│                              [重新评测]  [查看完整日志]  [关闭]             │
└────────────────────────────────────────────────────────────────────────────┘
```

**按钮规格**:

| 按钮 | 类型 | 说明 |
|------|------|------|
| 重新评测 | el-button type="warning" | 重新执行该子任务的所有问题 |
| 查看完整日志 | el-button type="primary" plain | 打开完整日志查看器 |
| 关闭 | el-button | 关闭对话框 |

**交互说明**:

| 按钮 | 行为 | 确认对话框 |
|------|------|------------|
| 重新评测 | 重新执行该子任务的所有问题 | 是，提示"确定要重新评测吗？当前结果将被覆盖" |
| 查看完整日志 | 打开日志查看器对话框，显示完整日志 | 否 |
| 关闭 | 关闭子任务详情对话框 | 否 |

**重新评测流程**:
1. 点击「重新评测」按钮
2. 显示确认对话框
3. 确认后重置子任务状态为「等待中」
4. 清空已处理问题和正确数统计
5. 重新开始评测流程
6. 实时更新进度和日志

#### 5.4.9 与父任务的关联

**面包屑导航**:

```
父任务 > 子任务 (california_schools)
```

**面包屑样式**:
- 使用 Element Plus `el-breadcrumb` 组件
- 位置：对话框标题下方
- 「父任务」可点击，跳转回父任务详情
- 当前子任务 db_id 不可点击

**快速返回父任务**:

| 方式 | 位置 | 行为 |
|------|------|------|
| 面包屑「父任务」 | 顶部 | 关闭子任务，打开父任务详情 |
| 「查看父任务 →」链接 | 父任务关联区 | 同上 |
| 点击父任务名称 | 父任务关联区 | 同上 |

**状态同步**:
- 子任务状态变化实时同步到父任务
- 父任务详情中点击子任务「查看详情」打开此对话框
- 关闭子任务详情返回父任务详情时，父任务数据自动刷新

---

### 5.2 失败状态

```
┌─────────────────────────────────────────────────────────────┐
│  导入失败                                          [X]    │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│                       [Error 图标]                          │
│                                                            │
│                    BIRD 数据集导入失败                      │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  错误信息:                                                 │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 验证失败: dev.json 文件不存在                         │   │
│  │ 请确保选择的目录包含有效的 BIRD 数据集                │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  已成功创建:                                               │
│  - 数据库连接: 3 个                                        │
│  - 评测任务: 3 个                                          │
│                                                            │
├─────────────────────────────────────────────────────────────┤
│                                         [查看详情] [重试]  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 组件规范

### 6.1 颜色规范

| 用途 | 颜色 |
|------|------|
| 主按钮 | #409eff |
| 成功 | #67c23a |
| 警告 | #e6a23c |
| 错误 | #f56c6c |
| 信息 | #909399 |
| 边框 | #dcdfe6 |
| 背景 | #f5f7fa |
| 父任务背景 | #ecf5ff |
| 父任务边框 | #409eff |
| 子任务缩进指示 | #c0c4cc |

### 6.2 字体规范

| 元素 | 字号 | 字重 |
|------|------|------|
| 对话框标题 | 18px | 500 |
| 标签页标题 | 14px | 400 |
| 正文 | 14px | 400 |
| 辅助文字 | 12px | 400 |
| 统计数字 | 24px | 600 |

### 6.3 间距规范

| 元素 | 间距 |
|------|------|
| 对话框内边距 | 24px |
| 组件间距 | 16px |
| 小间距 | 8px |
| 分组间距 | 24px |
| 子任务缩进 | 32px |
| 父任务左边框 | 4px |

---

### 6.4 任务类型标签规范

**标签样式**:

| 任务类型 | 标签样式 | Element Plus 配置 |
|----------|----------|-------------------|
| 父任务 | 蓝色标签 | el-tag type="primary" |
| 子任务 | 灰色标签 | el-tag type="info" |
| 独立任务 | 绿色标签 | el-tag type="success" |

**使用场景**:
- 任务列表中每行显示对应的类型标签
- 详情对话框标题旁显示类型标签
- 导入结果对话框中标识父任务和子任务

**标签尺寸**:
- 列表中：size="small"
- 详情标题旁：默认尺寸
- 筛选器中：默认尺寸

---

### 6.5 树形列表组件规范

**组件选择**: Element Plus `el-table` + 展开行 或 `el-tree`

**推荐方案**: `el-table` 展开行
- 父任务作为主行
- 子任务作为展开行内容
- 支持展开/折叠动画

**样式要求**:
- 父任务行：浅蓝色背景 `#ecf5ff` + 左边框 `#409eff`
- 子任务行：白色背景 + 32px 左缩进
- 展开图标：自定义为三角形 ▼/▶

---

### 6.6 状态指示器规范

**状态图标**:

| 状态 | 图标 | 颜色 |
|------|------|------|
| 等待中 | ⏳ 或 el-icon-timer | #909399 |
| 进行中 | 🔄 或 el-icon-loading | #409eff |
| 完成 | ✅ 或 el-icon-check | #67c23a |
| 失败 | ❌ 或 el-icon-close | #f56c6c |

**进度条颜色**:

| 进度范围 | 颜色 |
|----------|------|
| 0-30% | #f56c6c (红色) |
| 30-70% | #e6a23c (黄色) |
| 70-100% | #67c23a (绿色) |

---

## 7. 交互流程

### 7.1 完整导入流程

```
点击导入按钮
    ↓
显示导入对话框
    ↓
用户选择 Tab（上传/本地）
    ↓
用户填写/选择数据
    ↓
用户点击"开始导入"
    ↓
验证数据有效性
    ↓
显示进度对话框
    ↓
执行导入步骤
    ↓
显示结果对话框
    ↓
用户选择后续操作
```

### 7.2 状态转换

```
[初始状态]
    ↓ 选择文件/输入路径
[已选择状态]
    ↓ 点击开始导入
[验证中] → [验证失败] → [返回编辑]
    ↓ 验证成功
[导入中]
    ↓ 导入完成
[成功/失败]
```

---

## 8. 响应式设计

### 8.1 移动端适配

- 对话框宽度调整为 100%（最大 600px）
- 拖拽区域高度减小到 150px
- 步骤指示器改为垂直布局

---

## 9. 错误处理

### 9.1 前端验证错误

| 场景 | 处理方式 |
|------|----------|
| 未选择文件 | 禁用开始按钮，提示"请选择文件" |
| 文件类型错误 | 上传时提示"仅支持 zip 文件" |
| 文件过大 | 上传时提示"文件超过 1GB 限制" |
| 路径为空 | 输入框边框变红，提示"请输入路径" |

### 9.2 后端错误

| 场景 | 处理方式 |
|------|----------|
| 格式验证失败 | 进度对话框显示错误，提供重试 |
| 连接创建失败 | 部分成功展示，提供重试 |
| 任务创建失败 | 部分成功展示，提供重试 |
