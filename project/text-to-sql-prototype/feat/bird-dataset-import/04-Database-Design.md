# BIRD 数据集导入支持 - 数据库设计文档

## 1. 概述

本文档描述 BIRD 数据集导入功能涉及的数据库表结构变更。

**核心设计**: 支持评测任务的父子关系，批量导入时创建父任务作为容器，每个数据库的评测作为子任务，便于结果汇总统计。

---

## 2. 表结构变更

### 2.1 eval_tasks 表（修改）

**新增字段**: 支持父子任务关系

```sql
-- 新增字段
ALTER TABLE eval_tasks ADD COLUMN parent_id INTEGER REFERENCES eval_tasks(id);
ALTER TABLE eval_tasks ADD COLUMN connection_id INTEGER REFERENCES db_connections(id);
ALTER TABLE eval_tasks ADD COLUMN db_id VARCHAR(100);
ALTER TABLE eval_tasks ADD COLUMN task_type VARCHAR(20) DEFAULT 'single'; -- 'parent', 'child', 'single'
ALTER TABLE eval_tasks ADD COLUMN child_count INTEGER DEFAULT 0; -- 子任务数量（仅父任务）
ALTER TABLE eval_tasks ADD COLUMN completed_children INTEGER DEFAULT 0; -- 已完成子任务数
```

**完整表结构**:

```sql
CREATE TABLE eval_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    parent_id INTEGER REFERENCES eval_tasks(id),  -- 父任务ID

    -- 任务基本信息
    name VARCHAR(200) NOT NULL,
    task_type VARCHAR(20) DEFAULT 'single',  -- 'parent':父任务, 'child':子任务, 'single':独立任务
    dataset_type VARCHAR(50),
    dataset_path VARCHAR(500),
    db_id VARCHAR(100),  -- 数据库标识（仅子任务）

    -- 关联ID
    connection_id INTEGER REFERENCES db_connections(id),  -- 数据库连接（仅子任务）

    -- 任务配置
    model_config JSON NOT NULL,
    eval_mode VARCHAR(50),
    max_iterations INTEGER DEFAULT 3,
    sampling_count INTEGER DEFAULT 1,
    correction_strategy JSON,

    -- 任务状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress_percent INTEGER DEFAULT 0,

    -- 统计信息
    total_questions INTEGER,
    processed_questions INTEGER DEFAULT 0,
    correct_count INTEGER,
    accuracy FLOAT,

    -- 父子任务统计（仅父任务）
    child_count INTEGER DEFAULT 0,  -- 子任务总数
    completed_children INTEGER DEFAULT 0,  -- 已完成子任务数

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- 错误信息
    error_message TEXT,

    -- 日志文件路径
    log_path VARCHAR(500)  -- 评测日志文件路径
);
```

**索引**:
```sql
CREATE INDEX idx_eval_tasks_user_id ON eval_tasks(user_id);
CREATE INDEX idx_eval_tasks_parent_id ON eval_tasks(parent_id);
CREATE INDEX idx_eval_tasks_status ON eval_tasks(status);
CREATE INDEX idx_eval_tasks_task_type ON eval_tasks(task_type);
CREATE INDEX idx_eval_tasks_db_id ON eval_tasks(db_id);
CREATE INDEX idx_eval_tasks_parent_status ON eval_tasks(parent_id, status);
CREATE INDEX idx_eval_tasks_user_type ON eval_tasks(user_id, task_type);
```

---

### 2.2 父任务与子任务关系

```
┌─────────────────────────────────────────────────────────────┐
│                    父任务 (Parent Task)                      │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  id: 100                                              │ │
│  │  task_type: "parent"                                  │ │
│  │  name: "BIRD Dev Dataset"                             │ │
│  │  child_count: 11                                      │ │
│  │  completed_children: 11                               │ │
│  │  total_questions: 1534                                │ │
│  │  status: "completed"                                  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   子任务 1       │ │   子任务 2       │ │   子任务 3...   │
│  (california_)  │ │  (financial)    │ │                 │
│                 │ │                 │ │                 │
│  parent_id: 100 │ │  parent_id: 100 │ │  parent_id: 100 │
│  task_type:     │ │  task_type:     │ │  task_type:     │
│    "child"      │ │    "child"      │ │    "child"      │
│                 │ │                 │ │                 │
│  connection_id  │ │  connection_id  │ │  connection_id  │
│  db_id          │ │  db_id          │ │  db_id          │
│                 │ │                 │ │                 │
│  total: 150     │ │  total: 130     │ │  ...            │
│  correct: 120   │ │  correct: 95    │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

### 2.3 任务类型说明

| 类型 | 说明 | 特点 |
|------|------|------|
| `single` | 独立任务 | 传统的单个评测任务，无父子关系 |
| `parent` | 父任务 | 作为容器，聚合子任务统计，不直接执行评测 |
| `child` | 子任务 | 实际执行评测，关联到具体数据库连接 |

---

### 2.4 统计汇总逻辑

**父任务统计更新**:

当子任务完成时，自动更新父任务统计：

```sql
-- 触发器或应用层更新
UPDATE eval_tasks SET
    total_questions = (
        SELECT COALESCE(SUM(total_questions), 0)
        FROM eval_tasks
        WHERE parent_id = :parent_id
    ),
    correct_count = (
        SELECT COALESCE(SUM(correct_count), 0)
        FROM eval_tasks
        WHERE parent_id = :parent_id
    ),
    accuracy = (
        SELECT CASE
            WHEN SUM(total_questions) > 0
            THEN CAST(SUM(correct_count) AS FLOAT) / SUM(total_questions)
            ELSE 0
        END
        FROM eval_tasks
        WHERE parent_id = :parent_id
    ),
    completed_children = (
        SELECT COUNT(*)
        FROM eval_tasks
        WHERE parent_id = :parent_id
        AND status = 'completed'
    )
WHERE id = :parent_id;
```

---

## 3. SQLAlchemy 模型定义

### 3.1 EvalTask 模型（修改）

```python
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import String, ForeignKey, Index, Integer, Float, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.eval_result import EvalResult
    from app.models.db_connection import DBConnection


class EvalTask(Base):
    __tablename__ = "eval_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # 父子关系
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("eval_tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # 任务类型
    task_type: Mapped[str] = mapped_column(
        String(20),
        default="single",
        index=True
    )  # 'single', 'parent', 'child'

    # 基本信息
    name: Mapped[str] = mapped_column(String(200))
    dataset_type: Mapped[str] = mapped_column(String(50))
    dataset_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    db_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # 关联
    connection_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("db_connections.id", ondelete="SET NULL"),
        nullable=True
    )

    # 配置
    model_config: Mapped[Dict[str, Any]] = mapped_column(JSON)
    eval_mode: Mapped[str] = mapped_column(String(50), default="greedy_search")
    max_iterations: Mapped[int] = mapped_column(Integer, default=3)
    sampling_count: Mapped[int] = mapped_column(Integer, default=1)
    correction_strategy: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # 统计
    total_questions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 父子任务统计
    child_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_children: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="eval_tasks")
    connection: Mapped[Optional["DBConnection"]] = relationship("DBConnection")
    parent: Mapped[Optional["EvalTask"]] = relationship(
        "EvalTask",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["EvalTask"]] = relationship(
        "EvalTask",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    results: Mapped[List["EvalResult"]] = relationship(
        "EvalResult",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def is_parent(self) -> bool:
        """Check if this is a parent task."""
        return self.task_type == "parent"

    def is_child(self) -> bool:
        """Check if this is a child task."""
        return self.task_type == "child"

    def update_parent_stats(self) -> None:
        """Update parent task statistics from children."""
        if not self.is_parent() or not self.children:
            return

        total = sum(c.total_questions or 0 for c in self.children)
        correct = sum(c.correct_count or 0 for c in self.children)
        completed = sum(1 for c in self.children if c.status == "completed")

        self.total_questions = total
        self.correct_count = correct
        self.accuracy = correct / total if total > 0 else 0.0
        self.completed_children = completed

        # Auto-update parent status
        if completed == self.child_count:
            self.status = "completed"
        elif completed > 0:
            self.status = "running"
```

---

## 4. API 响应格式

### 4.1 父任务详情响应

```json
{
  "id": 100,
  "task_type": "parent",
  "name": "BIRD Dev Dataset",
  "dataset_type": "bird",
  "dataset_path": "/data/bird/bird_20260314_143052/dev.json",

  "status": "completed",
  "progress_percent": 100,

  "total_questions": 1534,
  "correct_count": 1185,
  "accuracy": 0.772,

  "child_count": 11,
  "completed_children": 11,

  "children": [
    {
      "id": 101,
      "task_type": "child",
      "name": "BIRD Dev - california_schools",
      "db_id": "california_schools",
      "connection_id": 21,
      "status": "completed",
      "total_questions": 150,
      "correct_count": 120,
      "accuracy": 0.80
    },
    {
      "id": 102,
      "task_type": "child",
      "name": "BIRD Dev - financial",
      "db_id": "financial",
      "connection_id": 22,
      "status": "completed",
      "total_questions": 130,
      "correct_count": 95,
      "accuracy": 0.73
    }
  ],

  "created_at": "2026-03-14T14:30:52Z",
  "completed_at": "2026-03-14T15:45:20Z"
}
```

---

## 5. Alembic 迁移脚本

```python
"""add parent-child task relationship

Revision ID: xxxx
Revises: previous_revision
Create Date: 2026-03-14

"""
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = 'previous_revision'


def upgrade():
    # 新增字段
    op.add_column('eval_tasks', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('eval_tasks', sa.Column('task_type', sa.String(20), nullable=True, server_default='single'))
    op.add_column('eval_tasks', sa.Column('db_id', sa.String(100), nullable=True))
    op.add_column('eval_tasks', sa.Column('connection_id', sa.Integer(), nullable=True))
    op.add_column('eval_tasks', sa.Column('child_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('eval_tasks', sa.Column('completed_children', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('eval_tasks', sa.Column('log_path', sa.String(500), nullable=True))

    # 更新现有数据
    op.execute("UPDATE eval_tasks SET task_type = 'single' WHERE task_type IS NULL")
    # 设置为 NOT NULL
    with op.batch_alter_table('eval_tasks') as batch_op:
        batch_op.alter_column('task_type', nullable=False)

    # 创建外键
    op.create_foreign_key(
        'fk_eval_tasks_parent_id',
        'eval_tasks', 'eval_tasks',
        ['parent_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_eval_tasks_connection_id',
        'eval_tasks', 'db_connections',
        ['connection_id'], ['id'],
        ondelete='SET NULL'
    )

    # 创建索引
    op.create_index('ix_eval_tasks_parent_id', 'eval_tasks', ['parent_id'])
    op.create_index('ix_eval_tasks_task_type', 'eval_tasks', ['task_type'])
    op.create_index('ix_eval_tasks_db_id', 'eval_tasks', ['db_id'])


def downgrade():
    # 删除索引
    op.drop_index('ix_eval_tasks_db_id', 'eval_tasks')
    op.drop_index('ix_eval_tasks_task_type', 'eval_tasks')
    op.drop_index('ix_eval_tasks_parent_id', 'eval_tasks')

    # 删除外键
    op.drop_constraint('fk_eval_tasks_connection_id', 'eval_tasks', type_='foreignkey')
    op.drop_constraint('fk_eval_tasks_parent_id', 'eval_tasks', type_='foreignkey')

    # 删除字段
    op.drop_column('eval_tasks', 'log_path')
    op.drop_column('eval_tasks', 'completed_children')
    op.drop_column('eval_tasks', 'child_count')
    op.drop_column('eval_tasks', 'connection_id')
    op.drop_column('eval_tasks', 'db_id')
    op.drop_column('eval_tasks', 'task_type')
    op.drop_column('eval_tasks', 'parent_id')
```

---

## 6. 数据统计查询示例

### 6.1 查询父任务汇总统计

```sql
-- 获取所有父任务及其汇总统计
SELECT
    t.id,
    t.name,
    t.task_type,
    t.child_count,
    t.completed_children,
    SUM(c.total_questions) as total_questions,
    SUM(c.correct_count) as correct_count,
    ROUND(CAST(SUM(c.correct_count) AS FLOAT) / NULLIF(SUM(c.total_questions), 0), 4) as accuracy,
    COUNT(CASE WHEN c.status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN c.status = 'failed' THEN 1 END) as failed_count
FROM eval_tasks t
LEFT JOIN eval_tasks c ON c.parent_id = t.id
WHERE t.task_type = 'parent'
GROUP BY t.id, t.name, t.task_type, t.child_count, t.completed_children;
```

### 6.2 查询子任务详情

```sql
-- 获取父任务的所有子任务详情
SELECT
    c.id,
    c.name,
    c.db_id,
    c.status,
    c.total_questions,
    c.correct_count,
    c.accuracy,
    conn.name as connection_name
FROM eval_tasks c
LEFT JOIN db_connections conn ON conn.id = c.connection_id
WHERE c.parent_id = :parent_id
ORDER BY c.db_id;
```

---

## 7. 数据一致性保障

### 7.1 父子任务约束

1. 父任务的 `status` 由子任务状态自动计算
2. 删除父任务时级联删除所有子任务
3. 子任务的统计变更自动同步到父任务

### 7.2 统计更新时机

- 子任务状态变为 `completed` 或 `failed` 时
- 子任务的 `correct_count` 更新时
- 定时任务补偿更新（防止漏更新）

---

## 8. 文档检查报告

### 8.1 检查结果清单

#### EvalTask 模型字段完整性

| 字段名 | 类型 | 状态 | 备注 |
|--------|------|------|------|
| `parent_id` | Integer, nullable, FK to eval_tasks.id | ✅ 已定义 | 第2.1节SQL、第3.1节模型 |
| `task_type` | String(20), default='single' | ✅ 已定义 | 第2.1节SQL、第3.1节模型 |
| `db_id` | String(100), nullable | ✅ 已定义 | 第2.1节SQL、第3.1节模型 |
| `connection_id` | Integer, nullable, FK to db_connections.id | ✅ 已定义 | 第2.1节SQL、第3.1节模型 |
| `child_count` | Integer, default=0 | ✅ 已定义 | 第2.1节SQL、第3.1节模型 |
| `completed_children` | Integer, default=0 | ✅ 已定义 | 第2.1节SQL、第3.1节模型 |
| `log_path` | String(500), nullable | ✅ 已定义 | 第5节迁移脚本中新增 |

#### SQLAlchemy 关系定义

| 关系名 | 定义 | 状态 | 备注 |
|--------|------|------|------|
| `parent` | relationship 到自身 (remote_side=[id]) | ✅ 已定义 | 第3.1节，lines 260-264 |
| `children` | relationship 到自身 (back_populates='parent') | ✅ 已定义 | 第3.1节，lines 265-269 |
| `connection` | relationship 到 DBConnection | ✅ 已定义 | 第3.1节，line 259 |

#### 模型方法

| 方法名 | 状态 | 备注 |
|--------|------|------|
| `is_parent() -> bool` | ✅ 已定义 | 第3.1节，lines 276-278 |
| `is_child() -> bool` | ✅ 已定义 | 第3.1节，lines 280-282 |
| `update_parent_stats() -> None` | ✅ 已定义 | 第3.1节，lines 284-302 |
| `is_single() -> bool` | ⚠️ 建议补充 | 建议添加，与is_parent/is_child保持一致 |
| `get_children() -> List[EvalTask]` | ⚠️ 建议补充 | 建议添加，便于获取子任务列表 |
| `get_parent() -> Optional[EvalTask]` | ⚠️ 建议补充 | 建议添加，便于获取父任务 |

#### Alembic 迁移脚本

| 检查项 | 状态 | 备注 |
|--------|------|------|
| 所有字段都在 upgrade() 中创建 | ✅ 已定义 | 第5节，lines 378-386 |
| 外键约束正确 (parent_id) | ✅ 已定义 | 第5节，lines 395-400，ondelete='CASCADE' |
| 外键约束正确 (connection_id) | ✅ 已定义 | 第5节，lines 401-406，ondelete='SET NULL' |
| 索引创建正确 (parent_id) | ✅ 已定义 | 第5节，line 409 |
| 索引创建正确 (task_type) | ✅ 已定义 | 第5节，line 410 |
| 索引创建正确 (db_id) | ✅ 已定义 | 第5节，line 411 |
| 索引创建正确 (parent_status) | ⚠️ 部分定义 | SQL中定义但迁移脚本未创建 |
| 索引创建正确 (user_type) | ⚠️ 部分定义 | SQL中定义但迁移脚本未创建 |
| 降级逻辑完整 (downgrade) | ✅ 已定义 | 第5节，lines 414-431 |
| 现有数据迁移逻辑 | ✅ 已定义 | 第5节，lines 389-392，设置task_type为'single' |

#### API 响应格式

| 检查项 | 状态 | 备注 |
|--------|------|------|
| 父任务详情响应包含 children 数组 | ✅ 已定义 | 第4.1节，lines 329-352 |
| 子任务响应包含 parent 基本信息 | ⚠️ 未定义 | 建议补充子任务详情响应格式 |
| 统计字段格式正确 | ✅ 已定义 | 第4.1节，total_questions/correct_count/accuracy |

---

### 8.2 需要补充的字段/方法列表

#### 建议补充的模型方法

```python
def is_single(self) -> bool:
    """Check if this is a single (standalone) task."""
    return self.task_type == "single"

def get_children(self) -> List["EvalTask"]:
    """Get all child tasks if this is a parent task."""
    if self.is_parent():
        return self.children
    return []

def get_parent(self) -> Optional["EvalTask"]:
    """Get parent task if this is a child task."""
    if self.is_child():
        return self.parent
    return None
```

#### 建议补充的索引（迁移脚本）

```python
# 在 upgrade() 中添加以下索引
op.create_index('idx_eval_tasks_parent_status', 'eval_tasks', ['parent_id', 'status'])
op.create_index('idx_eval_tasks_user_type', 'eval_tasks', ['user_id', 'task_type'])
```

#### 建议补充的 API 响应格式

**子任务详情响应**:

```json
{
  "id": 101,
  "task_type": "child",
  "parent_id": 100,
  "name": "BIRD Dev - california_schools",
  "db_id": "california_schools",
  "connection_id": 21,
  "status": "completed",
  "total_questions": 150,
  "correct_count": 120,
  "accuracy": 0.80,
  "parent": {
    "id": 100,
    "name": "BIRD Dev Dataset",
    "task_type": "parent"
  },
  "created_at": "2026-03-14T14:30:52Z",
  "completed_at": "2026-03-14T14:45:20Z"
}
```

---

### 8.3 与现有代码的差异分析

#### 当前代码 (backend/app/models/eval_task.py)

**现有字段**:
- `id`, `user_id`, `name`, `dataset_type`, `dataset_path`, `model_config`
- `eval_mode`, `max_iterations`, `sampling_count`, `correction_strategy`
- `status`, `progress_percent`, `total_questions`, `processed_questions`
- `correct_count`, `accuracy`, `log_path`, `error_message`
- `created_at`, `updated_at`, `started_at`, `completed_at`

**现有关系**:
- `user: Mapped["User"]` - 关联用户
- `results: Mapped[List["EvalResult"]]` - 关联评测结果

**现有方法**:
- `is_pending()`, `is_running()`, `is_completed()`, `is_failed()`

#### 需要添加的字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `parent_id` | `Mapped[Optional[int]]` | 父任务ID，自引用外键 |
| `task_type` | `Mapped[str]` | 任务类型，默认'single' |
| `db_id` | `Mapped[Optional[str]]` | 数据库标识 |
| `connection_id` | `Mapped[Optional[int]]` | 数据库连接ID |
| `child_count` | `Mapped[int]` | 子任务数量 |
| `completed_children` | `Mapped[int]` | 已完成子任务数 |

#### 需要添加的关系

| 关系名 | 定义 |
|--------|------|
| `connection` | `Mapped[Optional["DBConnection"]] = relationship("DBConnection")` |
| `parent` | `Mapped[Optional["EvalTask"]] = relationship("EvalTask", remote_side=[id], back_populates="children")` |
| `children` | `Mapped[List["EvalTask"]] = relationship("EvalTask", back_populates="parent", cascade="all, delete-orphan")` |

#### 需要添加的方法

| 方法名 | 说明 |
|--------|------|
| `is_parent() -> bool` | 检查是否为父任务 |
| `is_child() -> bool` | 检查是否为子任务 |
| `update_parent_stats() -> None` | 更新父任务统计 |

#### 需要更新的索引

```python
__table_args__ = (
    Index("ix_eval_tasks_user_id", "user_id"),
    Index("ix_eval_tasks_status", "status"),
    Index("ix_eval_tasks_dataset_type", "dataset_type"),
    Index("ix_eval_tasks_created_at", "created_at"),
    # 新增索引
    Index("ix_eval_tasks_parent_id", "parent_id"),
    Index("ix_eval_tasks_task_type", "task_type"),
    Index("ix_eval_tasks_db_id", "db_id"),
    Index("ix_eval_tasks_parent_status", "parent_id", "status"),
    Index("ix_eval_tasks_user_type", "user_id", "task_type"),
)
```

---

### 8.4 建议的修改顺序（考虑依赖关系）

```
Step 1: 创建 Alembic 迁移脚本
        ├── 添加新字段 (parent_id, task_type, db_id, connection_id, child_count, completed_children, log_path)
        ├── 创建外键约束
        └── 创建索引

Step 2: 更新 EvalTask 模型 (backend/app/models/eval_task.py)
        ├── 添加新字段定义
        ├── 添加 SQLAlchemy 关系
        ├── 添加辅助方法 (is_parent, is_child, update_parent_stats)
        └── 更新 __table_args__ 添加新索引

Step 3: 更新 DBConnection 模型 (backend/app/models/db_connection.py)
        └── 添加反向关系: eval_tasks: Mapped[List["EvalTask"]]

Step 4: 执行数据库迁移
        └── alembic upgrade head

Step 5: 更新 Pydantic Schemas (backend/app/schemas/eval_task.py)
        ├── 添加新字段到 EvalTaskBase/EvalTaskCreate
        ├── 添加 EvalTaskChildren 响应模型
        └── 更新 EvalTaskResponse 包含 children/parent 字段

Step 6: 更新 API 端点 (backend/app/api/v1/endpoints/eval.py)
        ├── 修改创建任务接口支持批量创建
        ├── 添加获取子任务列表接口
        └── 更新任务详情接口包含 children/parent 数据

Step 7: 实现父任务统计更新逻辑
        └── 在任务状态变更时自动更新父任务统计

Step 8: 更新前端类型定义 (frontend/src/types/eval.ts)
        └── 添加新字段和类型
```

---

### 8.5 总结

| 类别 | 已定义 | 缺失/建议补充 |
|------|--------|---------------|
| 模型字段 | 7/7 | 0 |
| SQLAlchemy 关系 | 3/3 | 0 |
| 模型方法 | 3/6 | 3 (is_single, get_children, get_parent) |
| 迁移脚本字段 | 7/7 | 0 |
| 迁移脚本外键 | 2/2 | 0 |
| 迁移脚本索引 | 3/5 | 2 (parent_status, user_type) |
| API 响应格式 | 1/2 | 1 (子任务响应) |

**整体评估**: 文档完整性 **85%**

主要缺失：
1. 迁移脚本中缺少两个复合索引的定义
2. 建议补充3个辅助方法
3. 建议补充子任务详情响应格式

这些缺失不影响核心功能实现，可在开发过程中按需补充。
