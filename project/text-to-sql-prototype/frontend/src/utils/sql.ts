/**
 * SQL 工具函数
 */

/**
 * 格式化 SQL 语句
 * @param sql - 原始 SQL 字符串
 * @returns 格式化后的 SQL 字符串
 */
export function formatSQL(sql: string): string {
  if (!sql.trim()) return ''

  const keywords = [
    'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
    'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',
    'GROUP', 'ORDER', 'BY', 'HAVING', 'LIMIT', 'OFFSET',
    'UNION', 'ALL', 'DISTINCT', 'AND', 'OR', 'NOT',
    'NULL', 'IS', 'IN', 'EXISTS', 'BETWEEN', 'LIKE',
    'CREATE', 'TABLE', 'DROP', 'ALTER', 'INDEX',
    'VALUES', 'SET', 'AS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
  ]

  let formatted = sql

  // 标准化关键字大小写
  keywords.forEach((kw) => {
    const regex = new RegExp(`\\b${kw}\\b`, 'gi')
    formatted = formatted.replace(regex, kw)
  })

  // 添加换行和缩进
  formatted = formatted
    .replace(/\s*SELECT\s+/gi, '\nSELECT ')
    .replace(/\s*FROM\s+/gi, '\nFROM ')
    .replace(/\s*WHERE\s+/gi, '\nWHERE ')
    .replace(/\s*JOIN\s+/gi, '\nJOIN ')
    .replace(/\s*LEFT\s+/gi, '\nLEFT ')
    .replace(/\s*RIGHT\s+/gi, '\nRIGHT ')
    .replace(/\s*INNER\s+/gi, '\nINNER ')
    .replace(/\s*OUTER\s+/gi, '\nOUTER ')
    .replace(/\s*ON\s+/gi, '\n  ON ')
    .replace(/\s*GROUP\s+BY\s+/gi, '\nGROUP BY ')
    .replace(/\s*ORDER\s+BY\s+/gi, '\nORDER BY ')
    .replace(/\s*HAVING\s+/gi, '\nHAVING ')
    .replace(/\s*LIMIT\s+/gi, '\nLIMIT ')
    .replace(/\s*OFFSET\s+/gi, '\nOFFSET ')
    .replace(/\s*UNION\s+/gi, '\nUNION ')
    .replace(/\s*INSERT\s+INTO\s+/gi, '\nINSERT INTO ')
    .replace(/\s*VALUES\s+/gi, '\nVALUES ')
    .replace(/\s*UPDATE\s+/gi, '\nUPDATE ')
    .replace(/\s*SET\s+/gi, '\nSET ')
    .replace(/\s*DELETE\s+FROM\s+/gi, '\nDELETE FROM ')
    .trim()

  return formatted
}

/**
 * 验证 SQL 语句是否为 SELECT 查询
 * @param sql - SQL 字符串
 * @returns 是否为 SELECT 查询
 */
export function isSelectQuery(sql: string): boolean {
  if (!sql.trim()) return false
  return /^\s*SELECT\s+/i.test(sql)
}

/**
 * 提取 SQL 中的表名
 * @param sql - SQL 字符串
 * @returns 表名数组
 */
export function extractTableNames(sql: string): string[] {
  const tables: string[] = []
  if (!sql.trim()) return tables

  // 匹配 FROM 子句后的表名
  const fromRegex = /FROM\s+(\w+)(?:\s+AS\s+\w+)?/gi
  let match
  while ((match = fromRegex.exec(sql)) !== null) {
    tables.push(match[1])
  }

  // 匹配 JOIN 子句后的表名
  const joinRegex = /JOIN\s+(\w+)(?:\s+AS\s+\w+)?/gi
  while ((match = joinRegex.exec(sql)) !== null) {
    tables.push(match[1])
  }

  // 匹配 UPDATE 后的表名
  const updateRegex = /UPDATE\s+(\w+)/gi
  while ((match = updateRegex.exec(sql)) !== null) {
    tables.push(match[1])
  }

  // 匹配 INTO 后的表名
  const intoRegex = /INTO\s+(\w+)/gi
  while ((match = intoRegex.exec(sql)) !== null) {
    tables.push(match[1])
  }

  return [...new Set(tables)] // 去重
}

/**
 * 截断 SQL 语句用于显示
 * @param sql - SQL 字符串
 * @param maxLength - 最大长度
 * @returns 截断后的字符串
 */
export function truncateSQL(sql: string, maxLength = 100): string {
  if (!sql) return ''
  const normalized = sql.replace(/\s+/g, ' ').trim()
  if (normalized.length <= maxLength) return normalized
  return normalized.slice(0, maxLength) + '...'
}

/**
 * 转义 SQL 字符串中的特殊字符
 * @param str - 需要转义的字符串
 * @returns 转义后的字符串
 */
export function escapeSQLString(str: string): string {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t')
}

/**
 * 检查 SQL 是否为 DDL 语句
 * @param sql - SQL 字符串
 * @returns 是否为 DDL
 */
export function isDDL(sql: string): boolean {
  if (!sql.trim()) return false
  return /^\s*(CREATE|ALTER|DROP|TRUNCATE)\s+/i.test(sql)
}

/**
 * 检查 SQL 是否为 DML 语句
 * @param sql - SQL 字符串
 * @returns 是否为 DML
 */
export function isDML(sql: string): boolean {
  if (!sql.trim()) return false
  return /^\s*(INSERT|UPDATE|DELETE|MERGE|CALL)\s+/i.test(sql)
}

/**
 * 获取 SQL 语句类型
 * @param sql - SQL 字符串
 * @returns SQL 类型
 */
export function getSQLType(sql: string): 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'CREATE' | 'ALTER' | 'DROP' | 'OTHER' {
  if (!sql.trim()) return 'OTHER'

  const upperSQL = sql.trim().toUpperCase()

  if (upperSQL.startsWith('SELECT')) return 'SELECT'
  if (upperSQL.startsWith('INSERT')) return 'INSERT'
  if (upperSQL.startsWith('UPDATE')) return 'UPDATE'
  if (upperSQL.startsWith('DELETE')) return 'DELETE'
  if (upperSQL.startsWith('CREATE')) return 'CREATE'
  if (upperSQL.startsWith('ALTER')) return 'ALTER'
  if (upperSQL.startsWith('DROP')) return 'DROP'

  return 'OTHER'
}
