# Text-to-SQL 原型系统 - 业务功能描述文档

## 1. 业务流程图

### 1.1 核心业务流程总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Text-to-SQL 核心业务流程                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   用户输入    │───▶│   意图识别    │───▶│  Schema检索   │───▶│  Prompt构建   │
│  自然语言问题 │    │  (Query理解)  │    │ (BM25+MinHash)│    │ (模板填充)    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                                                                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   结果返回    │◀───│   SQL执行    │◀───│   SQL解析    │◀───│   LLM生成    │
│ (格式化展示)  │    │ (执行+验证)   │    │ (提取+校验)   │    │ (vLLM推理)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### 1.2 数据库连接流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据库连接管理流程                                 │
└─────────────────────────────────────────────────────────────────────────────┘

用户填写连接信息 ──▶ 测试连接 ──▶ 获取Schema ──▶ 构建索引 ──▶ 存储连接
       │               │             │              │            │
       │               │             │              │            ▼
       │               │             │              │      ┌──────────────┐
       │               │             │              │      │  连接池管理   │
       │               │             │              │      │  - 连接复用   │
       │               │             │              │      │  - 超时检测   │
       │               │             │              │      │  - 健康检查   │
       │               │             │              │      └──────────────┘
       │               │             │              ▼
       │               │             │       ┌──────────────┐
       │               │             │       │  BM25索引    │
       │               │             │       │  MinHash计算 │
       │               │             │       └──────────────┘
       │               │             ▼
       │               │       ┌──────────────┐
       │               │       │  表结构提取   │
       │               │       │  字段类型识别 │
       │               │       │  外键关系发现 │
       │               │       └──────────────┘
       │               ▼
       │       ┌──────────────┐
       │       │  连接验证    │
       │       │  - 网络可达  │
       │       │  - 认证通过  │
       │       │  - 权限检查  │
       │       └──────────────┘
       ▼
┌──────────────┐
│  连接信息表单 │
│  - 数据库类型 │
│  - 主机/端口  │
│  - 用户名/密码│
│  - 数据库名   │
└──────────────┘
```

### 1.3 SQL生成与执行流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SQL生成与执行流程                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  用户确认/   │◀─────────────────────────────────────────────────────────────┐
│  编辑SQL     │                                                              │
└──────┬───────┘                                                              │
       │                                                                      │
       ▼                                                                      │
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│   执行SQL    │───▶│  获取结果集   │───▶│  格式化展示   │───▶│  存储历史    │─┘
│              │    │              │    │              │    │              │
│ - 语法检查   │    │ - 数据提取   │    │ - 表格渲染   │    │ - 问题记录   │
│ - 权限验证   │    │ - 类型转换   │    │ - 分页显示   │    │ - SQL记录    │
│ - 超时控制   │    │ - 结果限制   │    │ - 导出功能   │    │ - 执行结果   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │
       ▼ (执行异常)
┌──────────────┐
│   错误处理    │
│ - 语法错误提示│
│ - 自动修复建议│
│ - 人工介入   │
└──────────────┘
```

### 1.4 评测流程（参考ICED-2026）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            评测流程 (Evaluation)                             │
└─────────────────────────────────────────────────────────────────────────────┘

上传评测数据集 ──▶ 配置模型参数 ──▶ 批量生成SQL ──▶ 执行对比 ──▶ 计算准确率
       │                │               │              │            │
       │                │               │              │            ▼
       │                │               │              │      ┌──────────────┐
       │                │               │              │      │  EX准确率    │
       │                │               │              │      │  (执行结果   │
       │                │               │              │      │   集合对比)  │
       │                │               │              │      └──────────────┘
       │                │               │              ▼
       │                │               │       ┌──────────────┐
       │                │               │       │  预测SQL执行  │
       │                │               │       │  黄金SQL执行  │
       │                │               │       │  结果集合比较 │
       │                │               │       └──────────────┘
       │                │               ▼
       │                │       ┌──────────────┐    ┌──────────────┐
       │                │       │ Greedy Search│    │  Majority    │
       │                │       │ (单次生成)   │    │   Voting     │
       │                │       └──────────────┘    └──────────────┘
       │                │       ┌──────────────┐
       │                │       │   Pass@K     │
       │                │       │ (K次采样)    │
       │                │       └──────────────┘
       │                ▼
       │       ┌──────────────┐
       │       │  温度参数    │
       │       │  采样数量(n) │
       │       │  超时时间    │
       │       └──────────────┘
       ▼
┌──────────────┐
│ BIRD/Spider  │
│  数据集格式  │
│ - questions  │
│ - gold SQL   │
│ - database   │
└──────────────┘
```

---

## 2. 状态机图

### 2.1 查询任务状态机

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           查询任务状态流转                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
         ┌─────────│   PENDING   │◀────────┐
         │         │  (等待处理)  │         │
         │         └──────┬──────┘         │
         │                │ 开始生成        │
         │                ▼                │
         │         ┌─────────────┐         │
         │         │  GENERATING │         │
         │         │ (正在生成SQL)│         │
         │         └──────┬──────┘         │
         │                │ 生成完成        │
         │                ▼                │
         │         ┌─────────────┐         │
         │    ┌───▶│  EXECUTING  │◀───┐    │
         │    │    │ (正在执行)  │    │    │
         │    │    └──────┬──────┘    │    │
         │    │           │           │    │
    重试 │    │ 执行成功   │   执行失败│重试 │
         │    │           │           │    │
         │    │           ▼           │    │
         │    │    ┌─────────────┐    │    │
         │    └───▶│   SUCCESS   │────┘    │
         │         │  (执行成功)  │         │
         │         └─────────────┘         │
         │                                 │
         │    ┌─────────────┐              │
         └───▶│    ERROR    │──────────────┘
              │  (执行失败)  │
              │ - 语法错误   │
              │ - 执行超时   │
              │ - 权限不足   │
              │ - 连接断开   │
              └─────────────┘
```

**状态说明：**

| 状态 | 说明 | 触发条件 |
|------|------|----------|
| PENDING | 等待处理 | 用户提交查询请求 |
| GENERATING | 正在生成SQL | LLM开始生成SQL |
| EXECUTING | 正在执行SQL | SQL生成完成，开始执行 |
| SUCCESS | 执行成功 | SQL执行成功并返回结果 |
| ERROR | 执行失败 | 发生语法错误、超时或权限问题 |

### 2.2 评测任务状态机

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           评测任务状态流转                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   CREATED   │────────▶│   RUNNING   │────────▶│  COMPLETED  │
│  (已创建)   │  开始评测 │  (运行中)   │  评测完成 │  (已完成)   │
└─────────────┘         └──────┬──────┘         └─────────────┘
                               │
                               │ 评测异常
                               ▼
                        ┌─────────────┐
                        │    FAILED   │
                        │   (失败)    │
                        └─────────────┘
```

### 2.3 数据库连接状态机

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          数据库连接状态流转                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DISCONNECTED│───▶│ CONNECTING  │───▶│  CONNECTED  │───▶│   READY     │
│  (未连接)   │    │  (连接中)   │    │  (已连接)   │    │ (可用状态)  │
└─────────────┘    └─────────────┘    └──────┬──────┘    └─────────────┘
       ▲                                     │
       │                                     │ 连接异常
       │                                     ▼
       │                              ┌─────────────┐
       └──────────────────────────────│    ERROR    │
            重新连接                   │  (连接错误) │
                                      └─────────────┘
```

---

## 3. 核心算法详解

### 3.1 SQL正确性验证算法 (Execution-based Accuracy)

**算法描述：**
通过执行预测SQL和黄金SQL，对比执行结果集合来判断正确性。

**伪代码：**

```python
function verify_sql_correctness(pred_sql, gold_sql, db_file):
    """
    验证预测SQL的正确性

    Args:
        pred_sql: 模型生成的SQL
        gold_sql: 标准答案SQL
        db_file: 数据库文件路径

    Returns:
        correctness: 0 或 1 (1表示正确)
    """
    conn = connect(db_file)
    cursor = conn.cursor()

    try:
        conn.execute("BEGIN TRANSACTION")

        # 使用EXCEPT进行集合差运算
        sql_eq = """
            SELECT CASE
                WHEN EXISTS(SELECT 1 FROM (""" + pred_sql + """)
                            EXCEPT SELECT * FROM (""" + gold_sql + """))
                THEN 0
                WHEN EXISTS(SELECT 1 FROM (""" + gold_sql + """)
                            EXCEPT SELECT * FROM (""" + pred_sql + """))
                THEN 0
                ELSE 1
            END
        """

        cursor.execute(sql_eq)
        row = cursor.fetchone()
        correctness = int(row[0]) if row and row[0] is not None else 0

        conn.rollback()
        return correctness

    except Exception:
        conn.rollback()
        return 0
    finally:
        cursor.close()
```

**算法特点：**
- 基于执行结果集合比较，而非SQL字符串匹配
- 使用SQL的`EXCEPT`运算符进行集合差运算
- 支持多列结果、重复行、NULL值等复杂情况
- 执行超时控制（默认30秒）

### 3.2 多数投票算法 (Majority Voting)

**算法描述：**
对同一问题采样多次生成，统计执行结果的出现频次，选择票数最多的结果。

**伪代码：**

```python
function majority_voting(pred_sqls, db_files, sampling_num):
    """
    多数投票选择最佳SQL

    Args:
        pred_sqls: 所有采样SQL列表 (flattened)
        db_files: 对应的数据库文件列表
        sampling_num: 每个问题的采样次数

    Returns:
        mj_pred_sqls: 投票后的SQL列表
    """
    # 1. 执行所有采样SQL
    execution_results = []
    for i, (sql, db) in enumerate(zip(pred_sqls, db_files)):
        result = execute_sql(db, sql, timeout=30)
        execution_results.append({
            "data_idx": i,
            "sql": sql,
            "query_result": result.data if result.success else None,
            "valid": result.success
        })

    # 2. 按问题分组进行投票
    mj_pred_sqls = []
    for i from 0 to len(execution_results) step sampling_num:
        group = execution_results[i : i + sampling_num]

        # 如果全部无效，返回随机一个或错误标记
        if sum(r.valid for r in group) == 0:
            if return_random_when_all_errors:
                mj_pred_sqls.append(random_choice(group).sql)
            else:
                mj_pred_sqls.append("Error SQL")
            continue

        # 统计各结果出现频次
        vote_count = {}
        for r in group:
            if r.valid:
                if r.query_result in vote_count:
                    vote_count[r.query_result]["votes"] += 1
                else:
                    vote_count[r.query_result] = {"votes": 1, "sql": r.sql}

        # 选择票数最多的结果
        winner = max(vote_count.values(), key=lambda x: x["votes"])
        mj_pred_sqls.append(winner["sql"])

    return mj_pred_sqls
```

**算法特点：**
- 基于执行结果投票，而非SQL文本相似度
- 适用于有多个候选SQL的场景
- 可配置当全部失败时的处理策略

### 3.3 Pass@K 评估算法

**算法描述：**
K次采样中只要有一次正确即算通过。

**伪代码：**

```python
function pass_at_k_evaluate(pred_results, gold_sqls, db_files, k):
    """
    Pass@K评估

    Args:
        pred_results: 预测结果列表，每个包含k个采样
        gold_sqls: 黄金SQL列表
        db_files: 数据库文件列表
        k: 采样次数

    Returns:
        accuracy: Pass@K准确率
    """
    all_scores = []  # 每项为一次采样的0/1列表

    for sample_idx from 0 to k-1:
        # 提取第sample_idx个采样
        sample_sqls = [pred[sample_idx] for pred in pred_results]

        # 评估该采样
        scores = []
        for pred, gold, db in zip(sample_sqls, gold_sqls, db_files):
            correctness = verify_sql_correctness(pred, gold, db)
            scores.append(correctness)

        all_scores.append(scores)

    # 任一采样通过即算正确
    pass_at_k_scores = [
        1 if any(column) else 0
        for column in zip(*all_scores)
    ]

    return sum(pass_at_k_scores) / len(pass_at_k_scores)
```

### 3.4 Schema检索增强算法 (BM25 + MinHash)

**BM25内容检索：**

```python
function build_bm25_index(db_path, output_dir):
    """
    构建BM25索引用于内容检索

    流程：
    1. 遍历数据库所有表
    2. 对每行数据创建文档
    3. 使用Pyserini构建倒排索引
    4. 支持关键词检索相关记录
    """
    for table in get_tables(db_path):
        documents = []
        for row in query_all_rows(table):
            doc = {
                "id": f"{table}_{row['id']}",
                "contents": format_row_as_text(row)
            }
            documents.append(doc)

        build_index(documents, output_dir)
```

**MinHash外键发现：**

```python
function find_foreign_key_candidates(db_path):
    """
    使用MinHash发现潜在外键关系

    流程：
    1. 为每列创建MinHash签名 (128个hash函数)
    2. 计算列间Jaccard相似度
    3. 相似度>0.85的视为候选外键
    4. 根据唯一值数量推断方向(FK->PK)
    """
    NUM_HASH_FUNCTIONS = 128
    SIMILARITY_THRESHOLD = 0.85

    # 为每列创建MinHash签名
    sketches = {}
    for (table, column) in get_all_columns(db_path):
        sketch = create_minhash_sketch(db_path, table, column)
        sketches[f"{table}.{column}"] = sketch

    # 比较所有列对
    candidates = []
    for (field1, sketch1), (field2, sketch2) in combinations(sketches, 2):
        similarity = estimate_jaccard_similarity(sketch1, sketch2)

        if similarity >= SIMILARITY_THRESHOLD:
            # 根据唯一值数量推断方向
            count1 = count_distinct(field1)
            count2 = count_distinct(field2)

            if count1 <= count2:
                candidates.append((field1, field2, similarity))
            else:
                candidates.append((field2, field1, similarity))

    return sorted(candidates, key=lambda x: x[2], reverse=True)

function create_minhash_sketch(db_path, table, column):
    """为列创建MinHash签名"""
    sketch = [infinity] * NUM_HASH_FUNCTIONS

    for value in get_distinct_values(table, column, limit=10000):
        processed = str(value).lower().encode('utf-8')
        for i in range(NUM_HASH_FUNCTIONS):
            hash_val = mmh3.hash(processed, seed=i, signed=False)
            sketch[i] = min(sketch[i], hash_val)

    return sketch
```

### 3.5 生成-检查-修正流程 (Generator-Checker-Corrector)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     生成-检查-修正迭代流程                                   │
└─────────────────────────────────────────────────────────────────────────────┘

第1轮：
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Generator│─────▶│  Checker │─────▶│Corrector │
│  生成SQL  │      │ 检查正确性│      │ 修正SQL  │
└──────────┘      └────┬─────┘      └────┬─────┘
                       │                 │
                       ▼                 │
                 ┌──────────┐            │
                 │ 结果=YES │────────────┘ (结束)
                 │ 结果=NO  │────────────▶ (继续)
                 └──────────┘

第N轮：
重复上述流程直到：
- Checker返回YES (通过)
- 达到最大迭代次数
- 用户手动终止
```

**Checker Prompt设计：**

```
Task Overview:
You are a data science expert. Below, you are provided with a database schema,
natural language question and a SQL query written by the developer. Your task
is to understand the schema and determine whether the SQL query written by the
developer can correctly answer the natural language question.

Output format:
<think>
(Your step-by-step reasoning in natural language here)
</think>
<answer>
YES or NO
</answer>
```

---

## 4. 边界情况处理

### 4.1 SQL生成异常

| 异常类型 | 触发条件 | 处理策略 |
|----------|----------|----------|
| 非有效SQL | LLM输出不包含```sql代码块 | 1. 重新生成<br>2. 提示用户检查输入 |
| Schema信息不足 | 相关表/字段缺少注释 | 1. 提示用户完善数据库注释<br>2. 使用通用描述替代 |
| 用户意图不明确 | 问题描述模糊/歧义 | 1. 询问澄清<br>2. 提供可能的解释选项 |
| Prompt超长 | Token数超过模型限制 | 1. 截断非关键Schema信息<br>2. 使用简化Schema描述 |

### 4.2 SQL执行异常

| 异常类型 | 触发条件 | 处理策略 |
|----------|----------|----------|
| 语法错误 | SQL语法不正确 | 1. 捕获错误信息<br>2. 使用错误修正Prompt重新生成<br>3. 提示用户手动编辑 |
| 执行超时 | 执行时间>30秒 | 1. 提示优化SQL<br>2. 建议添加LIMIT<br>3. 检查索引 |
| 权限不足 | 用户无查询权限 | 1. 提示检查数据库权限<br>2. 记录审计日志 |
| 连接断开 | 数据库连接丢失 | 1. 自动重连(最多3次)<br>2. 提示重新连接 |
| 表/字段不存在 | Schema与数据库不一致 | 1. 刷新Schema缓存<br>2. 重新生成SQL |

### 4.3 系统异常

| 异常类型 | 触发条件 | 处理策略 |
|----------|----------|----------|
| LLM服务不可用 | vLLM推理失败 | 1. 降级到备用模型<br>2. 队列延迟处理<br>3. 提示服务暂时不可用 |
| 连接池耗尽 | 并发连接过多 | 1. 限流提示<br>2. 排队等待<br>3. 建议稍后重试 |
| 内存不足 | 结果集过大 | 1. 限制返回行数<br>2. 流式返回<br>3. 提示导出到文件 |
| 磁盘空间不足 | 日志/缓存占满 | 1. 自动清理旧日志<br>2. 提示管理员 |

### 4.4 评测异常

| 异常类型 | 触发条件 | 处理策略 |
|----------|----------|----------|
| 数据集格式错误 | JSON解析失败 | 1. 提示检查文件格式<br>2. 提供格式示例 |
| 数据库文件缺失 | 评测数据库不存在 | 1. 提示下载数据集<br>2. 跳过缺失项继续 |
| 评测超时 | 整体评测时间过长 | 1. 增加并行度<br>2. 分批评测 |
| 结果不一致 | 同一SQL多次执行结果不同 | 1. 标记为不稳定<br>2. 使用事务隔离 |

---

## 5. 业务规则

### 5.1 约束条件

#### 5.1.1 数据库连接约束

| 约束项 | 规则 | 说明 |
|--------|------|------|
| 连接超时 | 10秒 | 建立连接的最大等待时间 |
| 执行超时 | 30秒 | 单条SQL执行的最大时间 |
| 最大连接数 | 100 | 单用户最大并发连接数 |
| 连接复用 | 启用 | 相同连接信息复用已有连接 |
| 空闲断开 | 300秒 | 空闲连接自动断开时间 |

#### 5.1.2 SQL生成约束

| 约束项 | 规则 | 说明 |
|--------|------|------|
| 最大Prompt长度 | 6144 tokens | 超过则使用简化Schema |
| 最大生成长度 | 2048 tokens | SQL语句最大长度 |
| 温度参数 | 0.1-1.0 | Greedy: 0.1, Sampling: 0.8 |
| 采样数量 | 1-16 | Greedy: 1, Voting: 8 |
| 迭代轮数 | 1-3 | 生成-检查-修正的最大轮数 |

#### 5.1.3 结果返回约束

| 约束项 | 规则 | 说明 |
|--------|------|------|
| 最大行数 | 1000 | 单次查询最大返回行数 |
| 最大列数 | 100 | 单次查询最大返回列数 |
| 单元格长度 | 1000字符 | 超长内容截断显示 |
| 结果缓存 | 5分钟 | 相同查询结果缓存时间 |

### 5.2 校验规则

#### 5.2.1 连接信息校验

```python
validation_rules = {
    "host": {
        "required": True,
        "format": "hostname_or_ip",
        "max_length": 255
    },
    "port": {
        "required": True,
        "type": "integer",
        "range": [1, 65535],
        "default": {
            "mysql": 3306,
            "postgresql": 5432,
            "sqlite": None
        }
    },
    "username": {
        "required": True,
        "max_length": 128,
        "pattern": "^[a-zA-Z0-9_]+$"
    },
    "password": {
        "required": True,
        "max_length": 256,
        "min_length": 1
    },
    "database": {
        "required": True,
        "max_length": 128,
        "pattern": "^[a-zA-Z0-9_]+$"
    }
}
```

#### 5.2.2 SQL安全校验

| 校验项 | 规则 | 风险等级 |
|--------|------|----------|
| 禁止DDL | 拒绝CREATE/DROP/ALTER | 高危 |
| 禁止DML | 拒绝INSERT/UPDATE/DELETE | 高危 |
| 禁止系统表 | 拒绝访问sqlite_*等系统表 | 中危 |
| 禁止多语句 | 拒绝分号分隔的多条SQL | 中危 |
| 限制复杂度 | 拒绝嵌套超过5层的SQL | 低危 |

### 5.3 性能规则

#### 5.3.1 查询优化建议

| 场景 | 建议 |
|------|------|
| 无WHERE条件 | 提示添加LIMIT限制 |
| 全表扫描 | 提示添加索引 |
| 大表JOIN | 提示检查JOIN条件 |
| 子查询嵌套 | 建议改为JOIN |
| SELECT * | 建议指定具体字段 |

#### 5.3.2 资源限制

| 资源 | 限制 | 超限处理 |
|------|------|----------|
| CPU | 单查询最多4核 | 降级执行 |
| 内存 | 单查询最多2GB |  spill到磁盘 |
| 磁盘IO | 限速100MB/s | 排队等待 |
| 网络带宽 | 限速50MB/s | 压缩传输 |

---

## 6. 数据流图

### 6.1 系统整体数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              系统数据流                                      │
└─────────────────────────────────────────────────────────────────────────────┘

用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│  - 请求认证  - 限流控制  - 参数校验  - 路由分发                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Text-to-SQL Service                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Query Parser│──▶│Schema Engine│──▶│  LLM Client │              │
│  │  (意图解析)  │  │ (Schema管理) │  │  (SQL生成)  │              │
│  └─────────────┘  └─────────────┘  └──────┬──────┘              │
│                                           │                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────▼──────┐              │
│  │Result Formatter│◀│Query Executor│◀│ SQL Parser  │              │
│  │  (结果格式化) │  │  (SQL执行)  │  │ (SQL解析)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Connection │  │   Schema    │  │    Query    │              │
│  │    Pool     │  │   Cache     │  │   Engine    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   History   │  │   BM25      │  │   MinHash   │              │
│  │   Store     │  │   Index     │  │   Cache     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 附录

### 7.1 术语表

| 术语 | 说明 |
|------|------|
| Text-to-SQL | 将自然语言转换为SQL查询的技术 |
| Schema | 数据库结构定义，包括表、字段、关系等 |
| BM25 | 基于概率的排名函数，用于信息检索 |
| MinHash | 用于快速估计集合相似度的算法 |
| EX Accuracy | 基于执行结果的准确率评估指标 |
| Pass@K | K次采样中至少一次正确的概率 |
| Majority Voting | 多数投票机制，选择出现最多的结果 |
| Greedy Search | 贪婪搜索，每次选择概率最高的输出 |

### 7.2 参考实现

本文档基于以下代码实现编写：

- `pipeline.py`: ICED-2026主流程实现
- `evaluate_bird.py`: BIRD数据集评估实现
- `infer.py`: vLLM推理实现
- `minihash.py`: MinHash外键发现实现
- `lc_text_to_sql_pipeline.py`: LangChain流程实现

### 7.3 配置文件示例

```yaml
# config.yaml 示例
paths:
  train:
    db_dir: "./data/train_databases"
    dataset_json: "./data/train.json"
    tables_json: "./data/train_tables.json"
    db_index_dir: "./index/train"
  dev:
    db_dir: "./data/dev_databases"
    dataset_json: "./data/dev.json"
    tables_json: "./data/dev_tables.json"
    db_index_dir: "./index/dev"

bm25_index:
  enabled: true
  threads: 16

minhash:
  enabled: true
  workers: 32
  similarity_threshold: 0.85
  num_hash_functions: 128

inference:
  enabled: true
  model_path: "./models/Qwen2.5-Coder-7B-Instruct"
  tensor_parallel_size: 4
  temperature: 0.8
  n: 8

evaluation:
  enabled: true
  mode: "major_voting"  # greedy_search / major_voting / pass@k
  timeout: 30
  num_cpus: 60
```
