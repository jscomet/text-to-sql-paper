// 评测任务相关类型定义

// 任务类型枚举
export type TaskType = 'single' | 'parent' | 'child'

// 评测状态
export type EvalStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

// 数据集类型
export type DatasetType = 'bird' | 'spider' | 'custom'

// 评测模式
export type EvalMode = 'greedy_search' | 'majority_vote' | 'pass_at_k' | 'check_correct'

// 错误类型
export type ErrorType = 'syntax' | 'execution' | 'logic' | 'timeout' | 'generation'

// 评测进度
export interface EvalProgress {
  total: number
  processed: number
  correct: number
  percentage: number
}

// 基础评测任务
export interface EvalTask {
  id: number
  name: string
  status: EvalStatus
  dataset_type: DatasetType
  eval_mode: EvalMode
  progress: EvalProgress
  created_at: string
  // 父子任务相关字段
  task_type: TaskType
  parent_id?: number | null
  db_id?: string | null
  connection_id?: number | null
  child_count?: number
  completed_children?: number
}

// 子任务信息（用于父任务详情展示）
export interface EvalTaskChild {
  id: number
  name: string
  status: EvalStatus
  db_id: string
  progress: EvalProgress
  created_at: string
  started_at?: string
  completed_at?: string
}

// 带子任务的评测任务（父任务详情）
export interface EvalTaskWithChildren extends EvalTask {
  children: EvalTaskChild[]
  total_questions: number
  overall_accuracy: number
}

// 评测任务详情
export interface EvalTaskDetail extends EvalTask {
  connection_id: number
  dataset_path?: string
  model_config: {
    model?: string
    temperature?: number
    [key: string]: unknown
  }
  started_at?: string
  completed_at?: string
  // 父任务信息（如果是子任务）
  parent?: {
    id: number
    name: string
  }
}

// 评测结果
export interface EvalResult {
  id: number
  question_id: string
  question: string
  gold_sql: string
  predicted_sql: string
  is_correct: boolean
  error_type?: ErrorType
  error_message?: string
  execution_time_ms?: number
}

// 评测统计
export interface EvalStats {
  total: number
  correct: number
  incorrect: number
  failed: number
  accuracy: number
  execution_accuracy: number
  by_difficulty: {
    easy: { total: number; correct: number; accuracy: number }
    medium: { total: number; correct: number; accuracy: number }
    hard: { total: number; correct: number; accuracy: number }
  }
}

// 创建评测任务请求
export interface CreateEvalTaskRequest {
  name: string
  connection_id: number
  dataset_type: DatasetType
  dataset_path?: string
  api_key_id: number
  temperature?: number
  max_tokens?: number
  eval_mode?: EvalMode
  config?: {
    voting_count?: number
  }
}

// 批量操作请求
export interface BatchOperationRequest {
  task_ids?: number[]
  parent_id?: number
}

// 批量操作响应
export interface BatchOperationResponse {
  success: number
  failed: number
  errors?: Array<{
    task_id: number
    error: string
  }>
}

// 数据集导入配置
export interface ImportConfig {
  dataset_type: DatasetType
  eval_mode: EvalMode
  api_key_id: number
  temperature?: number
  max_tokens?: number
  connection_options?: {
    use_sqlite?: boolean
    sqlite_path?: string
  }
}

// 导入状态
export type ImportStatus = 'validating' | 'parsing' | 'creating_connections' | 'creating_tasks' | 'completed' | 'failed' | 'cancelled'

// 导入进度
export interface ImportProgress {
  status: ImportStatus
  step: number
  total_steps: number
  progress_percentage: number
  message: string
  logs: string[]
  result?: {
    parent_task_id: number
    connection_count: number
    task_count: number
  }
}

// 导入响应
export interface ImportResponse {
  import_id: string
  status: ImportStatus
}
