/**
 * E2E 测试数据
 *
 * 包含所有测试模块所需的测试数据
 */

// ============================================
// 用户认证模块测试数据
// ============================================
export const authTestData = {
  // 有效用户
  validUser: {
    username: 'testuser',
    password: 'Test@123',
    email: 'testuser@example.com'
  },

  // 无效用户
  invalidUser: {
    username: 'nonexistent',
    password: 'Wrong@123'
  },

  // 新用户（用于注册测试）
  newUser: {
    username: 'newuser',
    password: 'New@123',
    confirmPassword: 'New@123',
    email: 'newuser@example.com'
  },

  // 弱密码测试
  weakPassword: {
    username: 'weakuser',
    password: '123',
    confirmPassword: '123'
  },

  // 边界情况
  edgeCases: {
    longUsername: 'a'.repeat(50),
    specialChars: 'user@#$%',
    sqlInjection: "' OR '1'='1",
    xssAttempt: '<script>alert(1)</script>',
    unicode: '用户测试🎉'
  }
};

// ============================================
// 数据库连接模块测试数据
// ============================================
export const connectionTestData = {
  // 有效的 MySQL 连接
  mysqlValid: {
    name: 'MySQL-Test',
    type: 'mysql',
    host: 'localhost',
    port: 3306,
    database: 'test_db',
    username: 'root',
    password: 'root',
    useSSL: false,
    readOnly: false
  },

  // 有效的 PostgreSQL 连接
  postgresValid: {
    name: 'PG-Test',
    type: 'postgresql',
    host: 'localhost',
    port: 5432,
    database: 'test_db',
    username: 'postgres',
    password: 'postgres',
    useSSL: false,
    readOnly: false
  },

  // 有效的 SQLite 连接
  sqliteValid: {
    name: 'SQLite-Test',
    type: 'sqlite',
    filePath: './test.db'
  },

  // 无效主机
  invalidHost: {
    name: 'Invalid-Host',
    type: 'mysql',
    host: 'invalid_host',
    port: 3306,
    database: 'test',
    username: 'root',
    password: 'root'
  },

  // 无效端口
  invalidPort: {
    name: 'Invalid-Port',
    type: 'mysql',
    host: 'localhost',
    port: 3307,
    database: 'test',
    username: 'root',
    password: 'root'
  },

  // 错误凭证
  invalidCredentials: {
    name: 'Invalid-Cred',
    type: 'mysql',
    host: 'localhost',
    port: 3306,
    database: 'test',
    username: 'wrong_user',
    password: 'wrong_pass'
  },

  // 边界情况
  edgeCases: {
    longName: 'A'.repeat(100),
    specialChars: '连接@#$%^&*()',
    unicode: 'MySQL连接测试🎉',
    emptyName: '',
    negativePort: -1,
    zeroPort: 0,
    maxPort: 65535,
    exceedMaxPort: 65536
  }
};

// ============================================
// 查询功能模块测试数据
// ============================================
export const queryTestData = {
  // 简单查询
  simpleQueries: [
    {
      question: '查询所有用户',
      expectedSQL: 'SELECT * FROM users',
      expectedTable: 'users'
    },
    {
      question: '统计订单数量',
      expectedSQL: 'SELECT COUNT(*) FROM orders',
      expectedFunction: 'COUNT'
    },
    {
      question: '显示最近10条记录',
      expectedSQL: 'SELECT * FROM orders ORDER BY id DESC LIMIT 10',
      expectedLimit: 10
    }
  ],

  // 复杂查询
  complexQueries: [
    {
      question: '查询每个部门工资高于平均值的员工',
      expectedFeatures: ['GROUP BY', 'HAVING', 'subquery', 'AVG']
    },
    {
      question: '找出连续3个月有订单的客户',
      expectedFeatures: ['JOIN', 'DATE', 'GROUP BY', 'COUNT']
    },
    {
      question: '计算各产品类别的销售额占比',
      expectedFeatures: ['SUM', 'GROUP BY', 'percentage', 'OVER']
    }
  ],

  // 聚合查询
  aggregationQueries: [
    {
      question: '统计每个部门的员工数量',
      expectedFeatures: ['COUNT', 'GROUP BY', 'department']
    },
    {
      question: '查询2023年的销售总额',
      expectedFeatures: ['SUM', 'WHERE', 'date']
    },
    {
      question: '计算员工的平均工资',
      expectedFeatures: ['AVG', 'salary']
    }
  ],

  // 条件查询
  conditionalQueries: [
    {
      question: '查询年龄大于25岁的用户',
      expectedFeatures: ['WHERE', '>', 'age']
    },
    {
      question: '查找北京地区的订单',
      expectedFeatures: ['WHERE', '=', 'city']
    },
    {
      question: '查询最近7天内的记录',
      expectedFeatures: ['WHERE', 'DATE', 'BETWEEN']
    }
  ],

  // 边界情况
  edgeCases: [
    { question: '', expected: 'validation_error', description: '空输入' },
    { question: 'a', expected: 'too_short', description: '超短输入' },
    { question: '   ', expected: 'whitespace_only', description: '仅空白' },
    { question: 'SELECT * FROM users', expected: 'sql_input', description: '直接SQL输入' },
    { question: '<script>alert(1)</script>', expected: 'xss_safe', description: 'XSS尝试' },
    { question: 'drop table users', expected: 'security_blocked', description: 'DDL拦截' },
    { question: "' OR '1'='1", expected: 'sql_injection_blocked', description: 'SQL注入' },
    { question: 'A'.repeat(1000), expected: 'too_long', description: '超长输入' }
  ],

  // 多轮对话
  multiTurnConversations: [
    {
      turns: [
        { question: '查询张三的订单', expectedTable: 'orders' },
        { question: '只看已完成的', expectedFeatures: ['WHERE', 'status'] },
        { question: '按金额排序', expectedFeatures: ['ORDER BY', 'amount'] }
      ]
    },
    {
      turns: [
        { question: '统计销售额', expectedFunction: 'SUM' },
        { question: '按月份分组', expectedFeatures: ['GROUP BY', 'MONTH'] },
        { question: '只看2023年', expectedFeatures: ['WHERE', 'YEAR'] }
      ]
    }
  ]
};

// ============================================
// 历史记录模块测试数据
// ============================================
export const historyTestData = {
  // 搜索关键词
  searchKeywords: ['用户', '订单', 'SELECT', '统计', '查询', 'SUM', 'COUNT'],

  // 时间范围
  timeRanges: [
    { value: 'today', label: '今天' },
    { value: 'yesterday', label: '昨天' },
    { value: 'week', label: '近7天' },
    { value: 'month', label: '近30天' },
    { value: 'all', label: '全部' }
  ],

  // 状态筛选
  statuses: [
    { value: 'all', label: '全部' },
    { value: 'success', label: '成功' },
    { value: 'error', label: '失败' }
  ],

  // 示例历史记录
  sampleRecords: [
    {
      id: 1,
      question: '查询所有用户',
      sql: 'SELECT * FROM users',
      database: 'MySQL-Test',
      status: 'success',
      executionTime: 0.5,
      rowCount: 10,
      isFavorite: true,
      createdAt: '2024-01-15T10:30:00Z'
    },
    {
      id: 2,
      question: '统计订单数量',
      sql: 'SELECT COUNT(*) FROM orders',
      database: 'PG-Test',
      status: 'success',
      executionTime: 0.3,
      rowCount: 1,
      isFavorite: false,
      createdAt: '2024-01-15T09:15:00Z'
    },
    {
      id: 3,
      question: '查询不存在的表',
      sql: 'SELECT * FROM non_existent_table',
      database: 'MySQL-Test',
      status: 'error',
      errorMessage: 'Table \'test_db.non_existent_table\' doesn\'t exist',
      isFavorite: false,
      createdAt: '2024-01-14T16:45:00Z'
    },
    {
      id: 4,
      question: '删除所有数据',
      sql: 'DELETE FROM users',
      database: 'MySQL-Test',
      status: 'blocked',
      errorMessage: 'DDL/DML operations are not allowed',
      isFavorite: false,
      createdAt: '2024-01-13T11:20:00Z'
    },
    {
      id: 5,
      question: '查找销售额最高的产品',
      sql: 'SELECT product_name, SUM(amount) FROM sales GROUP BY product_name ORDER BY SUM(amount) DESC LIMIT 1',
      database: 'SQLite-Test',
      status: 'success',
      executionTime: 1.2,
      rowCount: 1,
      isFavorite: true,
      createdAt: '2024-01-12T14:00:00Z'
    }
  ]
};

// ============================================
// 评测功能模块测试数据
// ============================================
export const evaluationTestData = {
  // 可用模型
  models: [
    { id: 'gpt-4', name: 'GPT-4', provider: 'openai' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'openai' },
    { id: 'qwen-7b', name: 'Qwen 2.5 Coder 7B', provider: 'dashscope' },
    { id: 'qwen-14b', name: 'Qwen 2.5 Coder 14B', provider: 'dashscope' },
    { id: 'local-model', name: 'Local vLLM', provider: 'local' }
  ],

  // 数据集
  datasets: [
    { id: 'spider-dev', name: 'Spider Dev', count: 1034, difficulty: 'medium' },
    { id: 'spider-test', name: 'Spider Test', count: 2147, difficulty: 'medium' },
    { id: 'bird-dev', name: 'BIRD Dev', count: 1534, difficulty: 'hard' },
    { id: 'bird-test', name: 'BIRD Test', count: 1534, difficulty: 'hard' },
    { id: 'custom-test', name: 'Custom Test', count: 10, difficulty: 'easy' }
  ],

  // 评估模式
  evaluationModes: [
    { id: 'greedy', name: '标准 (Greedy)', description: '单次生成，温度0.1' },
    { id: 'pass@k', name: 'Pass@K', description: 'K次采样，任一正确即算通过' },
    { id: 'voting', name: '多数投票', description: '多次采样，按结果投票' }
  ],

  // 默认配置
  defaultConfig: {
    temperature: 0.8,
    samplingNum: 8,
    parallelNum: 4,
    useSchemaEnhancement: true,
    includeFewShot: false,
    maxExecutionTime: 30
  },

  // 测试数据集样例
  sampleDataset: {
    name: 'Test-Spider-Subset',
    description: 'Spider 数据集子集，用于测试',
    questions: [
      {
        question_id: 1,
        question: '查询所有用户',
        gold_sql: 'SELECT * FROM users',
        db_id: 'test_db',
        difficulty: 'easy'
      },
      {
        question_id: 2,
        question: '统计订单数量',
        gold_sql: 'SELECT COUNT(*) FROM orders',
        db_id: 'test_db',
        difficulty: 'easy'
      },
      {
        question_id: 3,
        question: '查询每个部门的平均工资',
        gold_sql: 'SELECT department_id, AVG(salary) FROM employees GROUP BY department_id',
        db_id: 'test_db',
        difficulty: 'medium'
      }
    ]
  },

  // 预期结果样例
  expectedResults: {
    greedy: {
      accuracy: 0.65,
      correct: 2,
      total: 3
    },
    passAt8: {
      accuracy: 0.85,
      passRate: 0.85
    }
  }
};

// ============================================
// 个人设置模块测试数据
// ============================================
export const settingsTestData = {
  // 有效密码
  validPassword: {
    current: 'OldPass@123',
    new: 'NewPass@456',
    confirm: 'NewPass@456'
  },

  // 无效密码
  invalidPassword: {
    short: '123',
    weak: 'password',
    noUpper: 'password123',
    noLower: 'PASSWORD123',
    noNumber: 'Password@',
    mismatch: {
      new: 'NewPass@456',
      confirm: 'Different@789'
    }
  },

  // API Keys
  apiKeys: {
    openai: {
      valid: 'sk-test1234567890abcdef1234567890abcdef',
      invalid: 'invalid-key',
      masked: 'sk-test**********************'
    },
    dashscope: {
      valid: 'sk-test0987654321fedcba0987654321fedcba',
      invalid: 'invalid-key',
      masked: 'sk-test**********************'
    }
  },

  // 主题设置
  themes: [
    { value: 'light', label: '浅色', className: 'light-theme' },
    { value: 'dark', label: '深色', className: 'dark-theme' },
    { value: 'auto', label: '跟随系统', className: 'auto-theme' }
  ],

  // 语言设置
  languages: [
    { value: 'zh-CN', label: '简体中文' },
    { value: 'en', label: 'English' }
  ],

  // 用户信息
  userProfile: {
    username: '张三',
    email: 'zhangsan@example.com',
    role: '数据分析师',
    avatar: '/avatar.png'
  }
};

// ============================================
// 测试环境配置
// ============================================
export const testEnvironment = {
  // 前端地址
  frontend: {
    baseUrl: 'http://localhost:5173',
    timeout: 30000
  },

  // 后端地址
  backend: {
    baseUrl: 'http://localhost:8000',
    apiPrefix: '/api/v1',
    timeout: 30000
  },

  // 浏览器配置
  browser: {
    viewport: {
      desktop: { width: 1920, height: 1080 },
      tablet: { width: 768, height: 1024 },
      mobile: { width: 375, height: 812 }
    }
  },

  // 等待时间配置
  waits: {
    short: 1000,
    medium: 3000,
    long: 10000,
    sqlGeneration: 15000,
    evaluation: 60000
  }
};

// ============================================
// 辅助函数
// ============================================

/**
 * 生成随机用户名
 */
export function generateRandomUsername(): string {
  const timestamp = Date.now();
  return `testuser_${timestamp}`;
}

/**
 * 生成随机连接名
 */
export function generateRandomConnectionName(): string {
  const timestamp = Date.now();
  return `Test-Conn-${timestamp}`;
}

/**
 * 生成随机评测任务名
 */
export function generateRandomEvalName(): string {
  const timestamp = Date.now();
  return `Eval-Test-${timestamp}`;
}

/**
 * 等待指定时间
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 格式化日期
 */
export function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

/**
 * 获取测试数据副本（避免修改原始数据）
 */
export function getTestData<T>(data: T): T {
  return JSON.parse(JSON.stringify(data));
}

export default {
  authTestData,
  connectionTestData,
  queryTestData,
  historyTestData,
  evaluationTestData,
  settingsTestData,
  testEnvironment,
  generateRandomUsername,
  generateRandomConnectionName,
  generateRandomEvalName,
  sleep,
  formatDate,
  getTestData
};
