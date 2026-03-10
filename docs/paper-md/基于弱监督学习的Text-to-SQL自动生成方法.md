doi:10. 3969 / j. issn. 1003-3114. 2025. 03. 011

引用格式:向宁. 基于弱监督学习的 Text-to-SQL 自动生成方法[J]. 无线电通信技术,2025,51(3):520-529.

[XIANG Ning. Text-to-SQL Automatic Generation Method Based on Weakly Supervised Learning J . Radio Communications Technology 2025 51 3 520-529. ]

# 基于弱监督学习的 Text-to-SQL 自动生成方法

向 宁

(乐山职业技术学院 人工智能学院,四川 乐山 614013)

摘 要:结构化查询语言( Structured Query Language,SQL) 生成模型对于非专业人员检索情报至关重要。 通常训练 SQL 生成模型需要使用标注的 SQL 以及对应的自然语言问题,现有 SQL 生成模型难以推广到不同的训练数据。 根据 问题分解半结构化表示( Decomposition Semi-structed Representation,DSR) ,提出一种基于弱监督学习的 Text-to-SQL 自动 生成方法( Text-to-SQL Automatic Generation Method Based on Weakly Supervised Learning,TS-WSL) ,给定问题、DSR 和执行 答案,能够自动合成用于训练 Text-to-SQL 模型的 SQL 查询。 使用 DSR 解析器对问题进行解析,通过短语链接、连接路 径推理以及 SQL 映射过程生成候选 SQL;使用候选 SQL 搜索选择最佳的 SQL 查询;使用生成的 SQL 数据对 T5 模型进 行训练。 在 5 个基准数据集上进行实验,结果表明所提方法比基于注释 SQL 数据集上训练的模型更具泛化性,在无域 内 DSR 场景下,仍然可以达到完全监督模型约 90%的性能。

关键词: 结构化查询语言生成模型;分解半结构化表示;弱监督学习;大模型

中图分类号:TP311 文献标志码:A 开放科学(资源服务)标识码(OSID): 文章编号:1003-3114(2025)03-0520-10

![](_page_0_Picture_11.jpeg)

# Text-to-SQL Automatic Generation Method Based on Weakly Supervised Learning

XIANG Ning

School of Artificial Intelligence Leshan Vocational and Technical College Leshan 614013 China

Abstract Structured Query Language SQL generation models are essential for non-specialists to retrieve information. It is usually necessary to use annotated SQL and corresponding natural language problems to train SQL generation model and it is difficult to generalize existing SQL generation model to different training data. According to Decomposition Semi-structed Representation DSR a Text-to-SQL Automatic Generation Method Based on Weakly Supervised Learning TS-WSL is proposed. Given question DSR and execution answer SQL queries can be automatically synthesized to train Text-to-SQL model. The problem is firstly resolved using a DSR parser and candidate SQLs are generated through procedures of phrase linking connection path inference and SQL mapping. Candidate SQL search is then used to select the best SQL query. Lastly a T5 model is trained using the generated SQL data. Experiments on five benchmark datasets show that the proposed method is more generalized than the model trained on annotated SQL datasets. In non-domain DSR scenario about 90% of performance of fully supervised model can still be achieved.

Keywords SQL generation model DSR weak supervised learning big data model

#### 0 引言

近年来,自然语言数据库接口的发展得到了广 泛的研究[1-4] 。 使用人工智能模型将自然语言问题 映射到可执行的 SQL 查询称为 Text-to-SQL 任务[5] 。 现有的绝大多数模型依赖于大规模 SQL 查询标注 的自然语言问题作为监督训练样本,模型训练质量 与训练样本质量强相关。 在真实世界中,大规模

收稿日期:2024-11-28

基金项目:国家自然科学基金(12171159);四川省科技计划资助 (2018TJPT0013)

Foundation Item:National Natural Science Foundation of China (12171159); Sichuan Science and Technology Program (2018TJPT0013)

Text-to-SQL 数据集中 SQL 形式各不相同且标注大 量训练数据的成本很高,每标注一条样本需要熟悉 SQL 和底层数据库结构的专家知识[6] 。 此外,难以 将模型泛化到新的训练数据集,将模型适应新的领 域需要相应的标注训练样本,加剧了成本开销。 因 此,需要一种新的模型在有少量标注数据的场景下 对文本和 SQL 的关系进行学习,并能通过新的文本 生成对应 SQL 查询。

基于上述讨论,本文提出一种 TS-WSL。 TS-WSL 避免使用手动标记的训练样本,而是依赖于非专家提 供的数据。 问题的答案和问题的 DSR 共同组成监督 标记。 这两种监督源的标注都可以众包给非专家[7] 。 文献[8]引入查询形式分解复杂问题,允许对多个信 息源进行查询,有效提高了开放域问答效率。 DSR 是 指用半结构化的表达式代表一系列的推理步骤,这些 表达式与原始问题的语义相匹配。 本文使用 DSR 作 为 SQL 合成的中间表示,实现一个自动转换过程,即 给定一个 DSR,将其映射到 SQL。 DSR 既可以手工标 注,也可以通过训练好的模型进行预测。

综上所述,本文主要贡献如下:① 根据问题分 解 DSR,提出一种 TS-WSL,一定程度上解决了训练 Text-to-SQL 模型需要依赖人工标注 SQL 的问题,兼 顾了跨数据集的泛化性;② 提出了一种 SQL 合成算 法,通过短语链接、连接路径推理以及 SQL 映射过 程,生成一组候选 SQL 查询;③ 在 5 个基准数据集 上进行实验,结果表明所提方法比基于注释 SQL 数 据集上训练的模型更具泛化性。

#### 1 相关工作

在实践中,为新任务标记大规模数据集通常成 本过高。 弱监督学习是指一大类减少人工标注大型 训练集的方法[9] 。 目前主流的研究方向是使用问 答对(Question-Answer Pair) 进行弱监督语义分析。 过去的研究表明,非专家能够对知识图谱[10] 和表格 数据[11]的答案进行标注,可以通过对表的子集进行 采样来扩展到数据库。 训练 Text-to-SQL 模型的关 键待解决问题是潜在候选查询的巨大搜索空间。 因 此,现有工作主要集中在限制候选查询的搜索空间, 这可能使单表上的简单问题适用性降低[12] 。 受文 献[13-14]启发,可以使用中间表示约束搜索空间 来处理任意 SQL 查询。

自然语言丰富的表达不仅需要理解句法信息, 还需 要 理 解 语 义 信 息。 预 训 练 模 型 的 最 新 研 究[15-16]产生了准确的词嵌入,代表了更好的语义信 息,有助于隐式映射。 SQL 不仅依赖于问题,还依赖 于数据库的模式。 Bogin 等[17]提出理解数据库模式 的重要性,将数据库内容纳入编码。 RAT-SQL(Rational Aware Transformer-SQL) [18]提出通过自注意机 制将自然语言问题以及模式中的上下文信息整合并 编码。 Lin 等[19]将表模式、问题及其文本匹配关系 表示为单个标记序列,并使用 Transformer [20] 模型来 计算它们之间的关系。 Coarse2Fine [21] 生成一个粗 略的中间表示,然后使用预定义的草图模板对中间 表示进行修改。 Yu 等[22]通过引入实体标签作为外 部知识,提出了一种新的模型 TypeSQL,使用额外的 实体类型信息有益于将问题解析为 SQL。 此外, TypeSQL 通过共享参数来减少编码器的数量。

一些工作将文本映射到 SQL 时使用中间意义 表示。 在之前的工作中,中间表示由专家注释,或者 直接从这些注释中进行推导,作为简化目标中间表 示的一种方式。 而 DSR 源于自然语言问题,可以由 非专家进行注释[8] 。 例如,文献[23]将 DSR 映射到 SPARK SQL 得了成功。 DSR 将问题分解成更简单 的子问题来表达问题的含义。 给定一个问题 x,其 DSR( 用 d 表示) 是一系列推理步骤 d 1 , d 2 , …, d | d | 。 每一步都有一个中间问题,代表一个关系操 作,如投影或聚合。 步骤可以包含来自 x 的短语、表 示查询操作的令牌以及对前面步骤的引用(本文使 用 \$ num 表示,其中 num 为步骤编号)。 操作令牌 表示每一步的结构,而其参数是步骤的引用和短语。

#### 2 TS-WSL

TS-WSL 整体流程为:输入数据包含问题 xi、数 据库 Di、答案 a<sup>i</sup> 和 DSR 的实例 di。 DSR 可由训练 模型 f 进行标注或预测,使 f(xi) = di。 对于每个实 例,合成 SQL 查询 Qi,它匹配 x<sup>i</sup> 的含义并执行得到 查询答案(Qi(Di) = ai)。 再使用合成样本( xi, Qi) 来训练 Text-to-SQL 模型。

图 1 展示了所提 TS-WSL 的执行流程,避免使用 手动标记的训练样本,而是依赖于非专家提供的数 据,输入用于自动合成 SQL 查询,合成的 SQL 用于训 练 Text-to-SQL 模型。 图 1 给出了"哪些作者在 DBLP 中有超过 20 篇文章?"的问题分解示例。 问题分解为 5 个步骤,每个步骤表示一个逻辑操作(如选择论文、 过滤出 DBLP 中的论文等),并且可以引用前面的步 骤(如 \$ 1 表示引用步骤 1)。 DSR 完全来源于问题, 与知识表示的底层形式无关。

所提 TS-WSL 主要包含 3 个阶段:

① SQL 合成阶段将输入的 DSR 转换为相应的 SQL 查询。 首先将 DSR 中的短语与数据库中的相 关列和值进行匹配,然后根据数据库模式结构自动 推断 SQL 连接路径,最后 SQL 映射将 DSR、数据库 链接的列和推理的连接路径转换为 SQL。

- ② SQL 候选阶段进行了问答监督,以过滤掉不 正确的候选 SQL。 以执行结果为导向的 SQL 搜索 将返回执行到正确答案的第一个候选查询。
- ③ 使用生成的最终候选 SQL 作为训练 Text-to-SQL 的样本。

![](_page_2_Figure_4.jpeg)

图 1 TS-WSL 的工作原理

Fig. 1 Working mechanism of TS-WSL

#### 2. 1 SQL 合成

为了解决标注数据不足场景下训练样本合成问 题,提出一种新颖的 SQL 合成算法,主要包含短语 链接、连接路径推理以及 SQL 合成。

给定 d<sup>i</sup> 和 Di,自动将 d<sup>i</sup> 映射为 SQL。 算法 1 描 述了合成过程,其中候选查询 Q<sup>i</sup> 通过迭代 DSR 步 骤来合成。 给定 DSR 步骤 d<sup>i</sup> k ,对应的短语会自动 链接到数据库 D<sup>i</sup> 中的列和值。 在列之间推断出相 关的连接路径,每个步骤都根据其 DSR 操作符及其 参数自动映射到 SQL。

```
算法 1 SQL 合成算法
输入:d(DSR 序列), D(数据库模式)
输出:SQL 查询
1:M ← [];
2:for d
      k
       in d = (d
               1
                , d
                  2
                   ,…, d
                         n
                          ) do
3: cols ← PCL(D, d
                   k
                    );
4: ref ← RefSteps(d
                  k
                   );
5: join ← [];
6: for d
        t
         in r do
7: oc ← M[t]. cols;
8: join ← join + JoinPath(D, cols, oc);
9: op ← OpType(d
                   k
                    );
```

10: Q ← MapSQL(op, cols, ref, join, M); 11: M[k] ← (d k , cols, Q); 12: return M[n]. Q;

步骤 1 中 M 表示初始化 SQL 映射数组;步骤 2 表示根据 DSR 为迭代步骤进行算法迭代;步骤 3 中 PCL 表示短语-列链接函数,通过输入 DSR 序列和 数据库模式,链接到对应的真实列;步骤 4 表示根据 DSR 序列,生成引用;步骤 5 表示初始化连接数组; 步骤 6~步骤 8 表示生成连接路径;步骤 9 表示生成 操作符;步骤 10~步骤 12 表示生成目标 SQL 查询。 2. 1. 1 短语链接

一个 DSR 步骤可以由来自问题 x<sup>i</sup> 的短语作为参 数。 当 DSR 映射到 SQL 时,将短语链接到数据库 D<sup>i</sup> 中的相应列或值。 为了计算短语-列的相似度,对短 语和列进行标记,再使用 WordNet [24]对标记进行词序 化。 相似度得分使用短语和列标记之间的平均 Glove 词嵌入相似度[25] 代替,根据与短语的单词重叠度和 相似度对 D<sup>i</sup> 中的所有列进行排序。 具体步骤如下: ① 返回与短语中的词法符号相同的列;② 返回与短 语共享(非停止词)标记的列,并按短语-列的相似性 排序;③ 返回其他列,按相似性排序。

假设 D<sup>i</sup> 中的字面值(如字符串或日期)在数据 库中和在问题中保持一致,可使用字符串匹配来识 别包含 d<sup>i</sup> 中提到的所有文字值的列。 如果一个字 面值出现在多个列中,均作为潜在链接返回。 然而, 由于数据库存在特有的规定,这种假设在实践中可 能并不总是成立,例如,women 可能对应于条件 gender = "F"。 案例 1 展示了短语链接过程:

案例1 给定问题 " What is the ship name that caused most total injuries?",如表 1 所示。 短语 ships 和 injuries 分别链接到 ship. id 和 death. injured 列。 通过对数据库 D<sup>i</sup> 中的所有列进行排序,并返回顺序 在最前面的列来自动执行短语链接操作。 然后根据 连接路径推理以及 SQL 映射过程生成候选 SQL。 最终通过候选 SQL 搜索得到最佳 SQL 查询。

#### 表 1 映射 DSR 为 SQL 查询案例

Tab. 1 Cases of mapping DSR to SQL queries

| DSR                          | 短语链接                         | SQL 查询                                                                                                                                       |
|------------------------------|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| ships                        | 1. SELECT(ship. id)          | SELECT ship. id FROM ship;                                                                                                                   |
| injuries                     | 2. SELECT(death. injured)    | SELECT death. injured FROM death;                                                                                                            |
| number of \$ 2 for each \$ 1 | 3. GROUP(count, \$ 2, \$ 1)  | SELECT COUNT( death. injured) FROM ship, death WHERE death. caused_by_<br>ship_id = ship. id GROUP BY ship. id;                              |
| \$ 1 where \$ 3 is highest   | 4. SUPER. (max, \$ 1, \$ 3)  | SELECT ship. id FROM ship, death WHERE death. caused_by_ship_id = ship. id<br>GROUP BY ship. id ORDER BY COUNT(death. injured) DESC LIMIT 1; |
| the name of \$ 4             | 5. PROJECT(ship. name, \$ 4) | SELECT ship. name FROM ship, death WHERE death. caused_by_ship_id = ship.<br>id AND ship. id IN ( \$ 4);                                     |

### 2. 1. 2 连接路径推理

为了生成完整 SQL,在链接的列之间推理连接 路径。 根据文献[13-14],实现一种启发式方法返 回连接两组列的最短连接路径。 为了计算连接路 径,将 D<sup>i</sup> 转换为实体关系图,其中节点是表,对于连 接两个表的每个外键之间都存在边。 算法 1 中的 JoinPath 将步骤 d <sup>k</sup> 中涉及列所对应的表与前面步 骤中涉及列对应的表连接起来。 如果存在多个最短 路径,则返回第一个包含列 ci∈cols 的表作为其开 始节点或包含列 cj∈oc 的表作为其结束节点路径。

### 2. 1. 3 SQL 映射

算法 1 中的 MapSQL 将 DSR 步骤映射为可执行

SQL。 使用 OpType 过程[8] 从其对话模板中推断出 每一步的 DSR 操作。

在前一个链接阶段之后,每个步骤的参数是链 接的列和值,或者是对前一个步骤的引用。 每个操 作都有一个到 SQL 的唯一映射规则,如表 2 所示。 \$ x 表示先前映射的 SQL 查询,而 \$ x[关键字] 表 示与其相关的 SQL 子句。 例如, \$ x[ FROM] 返回 SQL 查询 \$ x 的 FROM 子句中所有表。 SQL 映射根 据增量执行,当引用前面的步骤时,可以重用它们之 前映射的 SQL 部分(存储在映射数组中)。 此外,映 射过程能够处理可能涉及嵌套查询和自连接的复杂 SQL 查询。

表 2 DSR 映射规则

Tab. 2 DSR mapping rules

| DSR 短语链接操作                  | SQL 映射                                                                                                                                                                  |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| SELECT(t. col)              | SELECT t. col FROM t;                                                                                                                                                   |
| FILTER( \$ x, = , val)      | SELECT \$ x[SELECT] FROM \$ x[FROM] WHERE \$ x[WHERE] AND t. col = val;                                                                                                 |
| PROJECT(t. col, \$ x)       | SELECT t. col FROM t, \$ x[FROM] WHERE JOIN(t, \$ x[FROM]) AND \$ x[SELECT] IN ( \$ x);                                                                                 |
| AGGREGATE(count, \$ x)      | SELECT COUNT( \$ x[SELECT]) FROM \$ x[FROM] WHERE \$ x[WHERE];                                                                                                          |
| GROUP(avg, \$ x, \$ y)      | SELECT AVG ( \$ x [ SELECT ]) FROM<br>\$ x [ FROM ],<br>\$ y [ FROM ] WHERE JOIN ( \$ x [ FROM ],<br>\$ y[FROM]) AND \$ x[WHERE] AND \$ y[WHERE] GROUP BY \$ y[SELECT]; |
| SUPER. (max, k, \$ x, \$ y) | SELECT \$ x[SELECT] FROM \$ x[FROM], \$ y[FROM] WHERE JOIN( \$ x[FROM], \$ y[FROM]) AND<br>\$ x[WHERE] AND \$ y[WHERE] ORDER BY \$ y[SELECT] DESC k;                    |

#### 2. 2 SQL 候选搜索

在 SQL 映射之后,得到一个潜在的候选 SQL 查 询。 然而,由于错误的短语 - 列链接或其初始的 DSR 结构,该候选 SQL 可能不正确。 为了解决这些 问题,提出一种 SQL 候选搜索策略,使用答案监督 来搜索准确的候选 SQL。

在短语链接后,每个短语被映射到在 D<sup>i</sup> 中排名 最高的列。 然而,映射可能是错误的。 在图 1 中,短 语 authors 被错误地链接到 author. aid,而不是 author. name,无法获得正确的短语-列链接。 用正确 答案 a<sup>i</sup> 作为弱监督信号,迭代执行短语-列赋值过 程,并合成它们对应的 SQL。 对每个短语只覆盖排 名前 k 的列进行迭代。 当找到执行结果正确的答案 a<sup>i</sup> 所对应的 SQL 查询,将其作为结果返回。

未能生成正确的 SQL 也可能是 DSR 结构错误 导致。 由于 DSR 完全来源于问题,因此可能无法 捕获特定于数据库的表达。 例如,问题" How many students enrolled during the semester?" ,必要的聚合 操作可能会根据数据库结构而变化。 如果 D<sup>i</sup> 有列 course. num\_enrolled(此字段表示每个课程的注册 人数) ,查询应该对学期中所有课程的条目进行求 和。 相反,如果 D<sup>i</sup> 有列 course. student\_id(此字段 表示课程所对应的学生 id) ,对应的查询需要计算 注册学生数量。 通过实现额外的启发式搜索来缓 解结构不匹配问题,修改候选数据结构。 如果候 选对象在修改后执行正确的结果,则由搜索过程 返回。

### 3 实验与分析

实验主要针对两个问题:① 考虑到对问答和 DSR 的弱监督,测试可以自动合成的 SQL 查询百分 比;② 使用合成 SQL 查询来训练 Text-to-SQL 模型, 并将模型性能与在真实 SQL 注释上训练的模型进 行比较。

#### 3. 1 实验设置

数据集 使用 5 个经典数据集来评估 SQL 生成 覆盖范围和 Text-to-SQL 模型的准确性,如表 3 所示。 其中, 4 个 数 据 集 包 含 单 个 数 据 库 上 的 问 题: ① Academic 数据集[26] 包含微软学术搜索数据库问 题;② GEO880 [27] 涉及美国地理问题;③ IMDB [28] 包 含复杂的电影问题;④ Yelp [29] 包含餐馆数据库上的 复杂问题。 Spider 数据集[30] 包含超过 160 个不同数 据库的问题。 此外,使用 Break 数据集[8]测试 DSR。

训练 对 T5 模型[31] 进行微调,用于 Text-to-

SQL 任务和 DSR 分解任务。 对于每个任务,对其特 定数据的预训练模型进行微调。

针 对 Text-to-SQL 任 务, 使 用 映 射 组 合 ( xi; cols(Di))进行微调,其中序列 cols(Di)是以任意顺 序对数据库 D<sup>i</sup> 中的所有列进行序列化。 在 DSR 分 解任务中,输入问题 x<sup>i</sup> 被映射为 DSR 字符串。 使用 Hugging Face 实现 T5 模型[32] ,并使用 AdamW 优化 器[33]进行训练。 将批大小设为 128,将学习率调整 为 1 × 10 -4 。 所有模型都在 NVIDIA GeForce RTX 3090 GPU 上 进 行 了 训 练, 操 作 系 统 为 Ubuntu 20. 04,深度学习框架为 PyTorch。

表 3 SQL 合成覆盖率评分 Tab. 3 SQL synthesis coverage scores

| 数据集        | 数据库数量 | 样本数   | 合成数   | 覆盖率/ % |
|------------|-------|-------|-------|--------|
| Academic   | 1     | 195   | 155   | 79. 48 |
| GEO880     | 1     | 877   | 736   | 83. 92 |
| IMDB       | 1     | 131   | 116   | 88. 54 |
| Yelp       | 1     | 128   | 100   | 78. 12 |
| Spider 开发集 | 20    | 1 027 | 793   | 77. 21 |
| Spider 训练集 | 140   | 6 955 | 5 349 | 76. 90 |
| 总计         | 164   | 9 313 | 7 249 | 77. 83 |

#### 3. 2 SQL 合成覆盖率

本实验的目标是评估合成 SQL 的能力,将覆盖 率定义为成功生成 SQL 并执行得到正确答案的百 分比。 为了确保合成过程不依赖于任何数据集特 征,在 5 个不同的数据集 Academic、GEO880、IMDB、 Yelp 以及 Spider 上进行测试。 表 3 给出了使用 Break 人工注释 DSR 时的 SQL 合成覆盖率( Academic、GEO880、 IMDB、 Yelp、 Spider 开发集、 Spider 训练集以及混合集)。 总的来说,评估了 9 313 个人 工注释 DSR 的样本,覆盖率达到 77. 83%。 单数据 库的数据集合成覆盖率往往略高于 Spider 数据集, 将其归因于其更大的规模和多样性。

虽然 DSR 注释可以众包给非专家标注,但转移 到一个新领域可能会导致注释新的域内样本。 解决 这个问题的关键是评估合成 SQL 在预测 DSR 上的 覆盖率。 由于 Spider 开发集中的问题域不同于其训 练集中的问题域,因此选择其作为初始测试数据集 (记为 Spider-P,用于测试预测的 DSR)。 DSR 解析 器在 Break 数据集上进行微调,epoch 设为 10,选择 具有最高精确度的字符串匹配模型。 使用预测的 DSR 以及(xi, ai, Di)样本用于 SQL 合成。 表 4 展 示了 Spider-P(预测 DSR, 77. 60%)的覆盖率几乎与 表 3 展示的人工注释 DSR(77. 21%)相同。

表 4 Spider-P 合成覆盖率评分 Tab. 4 Spider-P synthesis coverage scores

| 数据集      | 数据库数量 | 样本数   | 合成数 | 覆盖率/ % |
|----------|-------|-------|-----|--------|
| Spider-P | 20    | 1 027 | 797 | 77. 60 |

由于 SQL 合成依赖于答案监督,丢弃带有空标 记的样本消除了偶然执行到空集的虚假 SQL。 对包 含 100 个随机错误样本的集合进行了占比分析,如 表 5 所示。

表 5 合成 SQL 误差分析 Tab. 5 Synthetic SQL error analysis

| 错误名称        | 描述                             | 占比/ % |
|-------------|--------------------------------|-------|
| DSR 有误差     | 注释 DSR 包含不遵循任何预<br>定义模板的步骤     | 42    |
| 特定于 DB 的表达  | 表达包含隐含条件                       | 23    |
| 短语-列链接错误    | 正确 的 短 语 列 分 配 不 在 前<br>k 个候选中 | 13    |
| 真实 SQL 标记错误 | 由于错误标记的真实 SQL 而<br>导致的错误       | 6     |

SQL 合成失败主要是由于 DSR 注释错误或隐 式数据库特定条件造成的。 例如,在 GEO880 中,短 语 major river 应该隐式地映射到条件 river. length > 750。 由于 SQL 合成是域通用的,所以并不储存任 何特定于域的术语或规则。

#### 3. 3 模型训练

使用合成的 SQL 样本训练 Text-to-SQL 模型,并 与使用专家注释 SQL 训练的 Text-to-SQL 模型比较。 给定的样本(xi, Di),测试以下设置:

- ① 使用一个包含真实 SQL 注释的完全监督训 练集;
- ② 使用一个弱监督的训练集,其中给定答案 ai、DSR d<sup>i</sup> 以及合成的 SQL 查询 Qi。

在 Spider 和 GEO880 数据集上训练 T5-large 模 型。 选择 T5-large 模型作为 Text-to-SQL 模型是因 为它的性能与输入序列的结构无关,该特性有益于 跨数据库测试。

训练及测试如下模型:

- ① T5-SQL-G 表示 T5-large 模型使用专家标注 的真实 SQL 作为训练集训练的模型;
- ② T5-DSR-G 表示使用人工注释的 DSR 训练的 模型;
  - ③ T5-DSR-P 表示使用预测的 DSR 训练的模型;

④ T5-SQL-P 表示部分使用真实 SQL 作为训练 集训练的模型。 该模型评估合成训练数据的规模及 其不同的查询结构对性能的影响程度。

由于所提 TS-WSL 中的 SQL 是自动合成的,语法 通常与真实 SQL 不同,对比二者的形式作为评估标 准不可取。 相反,使用 SQL 查询的执行准确率用于 模型性能评估是可行的。 将执行准确率定义为在数 据库上执行时产生与答案 a<sup>i</sup> 相同的元组(行)集百 分比。

#### 3. 4 人工注释的 DSR 性能

实验中使用人工注释的 DSR 训练的模型( T5- DSR-G)与使用真实 SQL 训练的模型(T5-SQL-G)进 行比较。 表 6 展示了不同模型在 Spider 训练集上的 设置,所有模型均训练 150 epoch,并使用 1 034 个 样本的开发集进行测试。 其中,T5-DSR-P 包含了 700 个 Spider 训练集标注的 DSR。 所有实验基于 3 组随机数种子重复执行。

表 6 不同模型在 Spider 训练集上的设置

| Tab. 6 | Different model settings on Spider training set |  |  |  |  |
|--------|-------------------------------------------------|--|--|--|--|
|--------|-------------------------------------------------|--|--|--|--|

| 模型       | 监督信号             | 训练集样本数量 |  |
|----------|------------------|---------|--|
| T5-SQL-G | (xi, Qi, Di)     | 7 000   |  |
| T5-SQL-P | (xi, Qi, Di)     | 5 349   |  |
| T5-DSR-G | (xi, ai, di, Di) | 5 349   |  |
| T5-DSR-P | (xi, ai, Di)     | 5 075   |  |
|          |                  |         |  |

不同设置的模型在 Spider 开发集上的执行准确 率如图 2 所示,分别展示最低和最高执行准确率。 将 T5-DSR-G 与 T5-SQL-G 进行比较时,T5-DSR-G 的执 行准确率最高达到 66. 1%,而 T5-SQL-G 最低能达到 67. 7%,说明使用人工注释的 DSR 效果与使用真实 SQL 的效果相近。 T5-SQL-P 与 T5-DSR-G 在相同的 5 349 个样本上进行训练,执行准确率大致相同。

![](_page_5_Figure_24.jpeg)

图 2 Spider 训练集训练的模型在开发集上的执行准确率 Fig. 2 Execution accuracy of Spider training model on development set

实验进一步测试了模型在跨数据库语义解析方 面的性能,具体测试了 4 个额外的 Text-to-SQL 数据 集 Academic、GEO880、IMDB 和 Yelp。

对于 Academic、IMDB 和 Yelp 删除了执行结果 为空的样本,结果如图 3 所示。 经过 Spider 训练的 模型难以推广到跨数据库语义解析(Cross-database Semantic Parsing,XSP) 任务,执行准确率较低。 然 而,T5-DSR-G 的性能在 XSP 任务中通常更好,进一 步表明与真实 SQL 相比, DSR 和答案监督是 有 效的。

![](_page_6_Figure_4.jpeg)

图 3 不同模型的跨数据集执行准确率

Fig. 3 Execution accuracy of different models on cross-datasets

表 7 列出了在 GEO880 上的 SQL 平均执行准确 率。 模型训练了 300 epoch,在开发集上进行了微 调,在 280 个测试样本上进行了测试。 其中, T5- DSR-G 的性能达到了 T5-SQL-G 的 91. 03%(74. 77 / 82. 13)。 与使用 Spider 数据集的模型相比,性能差 距是因数据集的大小差异导致。

表 7 使用 GEO880 训练的模型测试结果 Tab. 7 Testing results of model trained with GEO880

| 模型       | 监督信号             | 训练集样本 | 平均执行准确率/ % |
|----------|------------------|-------|------------|
| T5-SQL-G | (xi, Qi, Di)     | 547   | 82. 13     |
| T5-SQL-P | (xi, Qi, Di)     | 454   | 79. 56     |
| T5-DSR-G | (xi, ai, di, Di) | 454   | 74. 77     |
| T5-DSR-P | (xi, ai, Di)     | 432   | 70. 61     |

#### 3. 5 预测的 DSR 性能

用 DSR 解析器所预测的 DSR 替换人工注释的 DSR。 基于此,现有两组问题:① 用于训练 DSR 解 析器的问题;② 用于合成 SQL 数据的问题。 将这 两个问题集合尽可能地分开,训练 DSR 解析器不需 要新的域内注释。

DSR 解析器必须泛化到 Text-to-SQL 域中的问 题,同时尽可能少地训练这些问题。 然而,由于 Spider 包含了用于训练 DSR 解析器的 Break 训练集的 大部分问题。 因此,拟采用两种备选方案来最小化 Text-to-SQL 问题的域内 DSR 注释。 第一种方法是 使用针对 Spider 的少量 DSR 注释来训练解析器。 第二种方法是将 Spider 数据集进行拆分,一部分用 作 Text-to-SQL 数据, 其余部分用于训练 DSR 解 析器。

在表 6 和图 2 中,T5-DSR-P 在 5 075 个 SQL 查询上进行训练,这些查询使用基于 Spider 训练 集预 测 的 DSR 和 答 案 监 督 进 行 合 成。 预 测 的 DSR 由在 Break 子集上训练的 DSR 解析器生成, 排除了大部分 Spider 问题,保留 700 个 Spider 训 练集样本。 保留少量域内样本可以在保持预测 质量的同时最小化额外的 DSR 注释。 在预测的 DSR 上进行训练,与人工注释的 DSR 相比,准确 率下降。 在 XSP 任务中,T5-DSR-P 与 T5-DSR-G 具有竞争力。

如表 8 所示,在没有域内 DSR 注释的情况下训 练 T5-DSR-P。 避免用于训练 DSR 解析器和 SQL 合 成的问题和域之间包含重叠。 从 Spider 数据集中随 机抽取 30~40 个数据库,并使用它们对应的问题作 为 Text-to-SQL 数据。 使用 Spider 训练集的 3 组随 机样本进行实验(小括号中数字代表组别),分别包 含 1 348、2 028、2 076 个样本,其中,合成的训练数 据分别为 1 129、1 440、1 552 个样本。

表 8 Spider 训练集设置(无域内 DSR 注释) Tab. 8 Settings of Spider training set (no in-domain DSR comments)

| 模型          | 监督信号         | 训练集样本数量 | 数据库数量 |
|-------------|--------------|---------|-------|
| T5-SQL-G(1) | (xi, Qi, Di) | 1 348   | 30    |
| T5-SQL-P(1) | (xi, Qi, Di) | 1 129   | 30    |
| T5-DSR-P(1) | (xi, ai, Di) | 1 129   | 30    |
| T5-SQL-G(2) | (xi, Qi, Di) | 2 028   | 40    |
| T5-SQL-P(2) | (xi, Qi, Di) | 1 440   | 40    |
| T5-DSR-P(2) | (xi, ai, Di) | 1 440   | 40    |
| T5-SQL-G(3) | (xi, Qi, Di) | 2 076   | 40    |
| T5-SQL-P(3) | (xi, Qi, Di) | 1 552   | 40    |
| T5-DSR-P(3) | (xi, ai, Di) | 1 552   | 40    |

根据表 8 的 3 组数据进行实验。 图 4 表明 T5- DSR-P 接近 T5-SQL-G 的执行准确率。 即使没有任何 域内 DSR 注释,与真实 SQL 相比,答案监督和域外 DSR 引导的数据在训练 Text-to-SQL 模型中是有 效的。

![](_page_7_Figure_6.jpeg)

图 4 不同组别的模型执行准确率 Fig. 4 Model execution accuracy of different groups

### 4 结束语

为了解决非专业人员快速检索情报的难点,本 文提出一种基于弱监督学习的 Text-to-SQL 自动生 成方法,使用答案和 DSR 监督。 实现了一个自动 SQL 合成过程,能够为几十个目标数据库生成有效 的训练数据。 在多个 Text-to-SQL 数据集上的实验 证明了所提模型的有效性,几乎达到了在带注释的 SQL 上训练的完全监督模型性能。 进一步将模型的 监督信号替换为无域内 DSR 场景,仍然可以达到完 全监督模型约 90%的性能。 综上,本文提供了一个 有效的解决方案来训练 Text-to-SQL 的模型,该模型 不需要 SQL 的注释,具有很好的模型泛化性。

#### 参 考 文 献

- [1] XU B, LI S F, JING H Y, et al. Boosting Text-to-SQL Through Multi-grained Error Identification[C]∥Proceedings of the 31st International Conference on Computational Linguistics. Abu Dhabi:ACL,2025:4282-4292.
- [2] ZHANG X L,WANG D Z R,DOU L X,et al. MURRE: Multi-hop Table Retrieval with Removal for Open-domain Text-to-SQL[ C]∥Proceedings of the 31st International Conference on Computational Linguistics. Abu Dhabi: ACL,2025:5789-5806.
- [3] LIU G L,TAN Y Z,ZHONG R C,et al. Solid-SQL:Enhanced Schema-linking Based In-context Learning for Robust Text-to-SQL[ C]∥Proceedings of the 31st International Conference on Computational Linguistics. Abu Dhabi:ACL,2025:9793-9803.
- [4] LI R, CHEN Y, ZHANG H Y, et al. A Question-aware Few-shot Text-to-SQL Neural Model for Industrial Databases [ J]. International Journal of Intelligent Systems, 2025,25(1):1033-1039.
- [5] KIM H, SO B H,HAN W S, et al. Natural Language to SQL:Where Are We Today? [J]. Proceedings of the VLDB Endowment,2020,13(10):1737-1750.
- [6] YU T, ZHANG R,YASUNAGA M, et al. SParC: Cross-Domain Semantic Parsing in Context[C]∥Proceedings of the 57th Conference of the Association for Computational Linguistics. Florence:ACL,2019:4511-4523.
- [7] PASUPAT P,LIANG P. Compositional Semantic Parsing on Semi-structured Tables[C]∥Proceedings of the 53rd Annual Meeting of the Association for Computational Linguistics. Beijing:ACL,2015:1470-1480.
- [8] WOLFSON T,GEVA M,GUPTA A,et al. Break It Down:A Question Understanding Benchmark[J]. Transactions of the Association for Computational Linguistics,2020,8:183-198.

- [9] HOFFMANN R,ZHANG C L,LING X,et al. Knowledge Based Weak Supervision for Information Extraction of Overlapping Relations[C]∥Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies. Oregon: ACL, 2021:541-550.
- [10] BERANT J,CHOU A,FROSTIG R,et al. Semantic Parsing on Freebase from Question-answer Pairs[C]∥Proceedings of the Conference on Empirical Methods in Natural Language Processing. Washington D. C. :ACL,2013:1533-1544.
- [11] JAUHAR S K,TURNEY P D,HOVY E H. Tables as Semistructured Knowledge for Question Answering[C]∥Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics. Berlin:ACL,2016:474-483.
- [12] WANG B L, TITOV I, LAPATA M. Learning Semantic Parsers from Denotations with Latent Structured Alignments and Abstract Programs [ C] ∥Proceedings of the Conference on Empirical Methods in Natural Language Processing. Hong Kong:ACL,2019:3772-3783.
- [13] GUO J Q,ZHAN Z C,GAO Y, et al. Towards Complex Text-to-SQL in Cross-domain Database with Intermediate Representation[C]∥Proceedings of the 57th Conference of the Association for Computational Linguistics. Florence:ACL,2019:4524-4535.
- [14] WOLFSON T,DEUTCH D,BERANT J. Weakly Supervised Text-to-SQL Parsing Through Question Decomposition [C]∥Proceedings of Findings of the Association for Computational Linguistics. Seattle:ACL,2022:2528-2542.
- [15] DEVLIN J,CHANG M W,LEE K,et al. BERT:Pre-training of Deep Bidirectional Transformers for Language Understanding[C]∥Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics:Human Language Technologies. Minneapolis:ACL,2019:4171-4186.
- [16] YIN P C,NEUBIG G,YIH W T,et al. TaBERT:Pretraining for Joint Understanding of Textual and Tabular Data [C]∥Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. New York:ACL, 2020:8413-8426.
- [17] BOGIN B,BERANT J,GARDNER M. Representing Schema Structure with Graph Neural Networks for Text-to-SQL Parsing[C]∥Proceedings of the 57th Conference of the Association for Computational Linguistics. Florence:ACL, 2019:4560-4565.
- [18] WANG B L,SHIN R,LIU X D,et al. RAT-SQL:Relation-Aware Schema Encoding and Linking for Text-to-SQL Parsers[C]∥Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. Amsterdam:ACL,2020:7567-7578.

- [19] LIN X V, SOCHER R, XIONG C M. Bridging Textual and Tabular Data for Cross-domain Text-to-SQL Semantic Parsing[C]∥Proceedings of Findings of the Association for Computational Linguistics. New York: ACL, 2020: 4870-4888.
- [20] VASWANI A,SHAZEER N,PARMAR N,et al. Attention is All You Need[C]∥Proceedings of Advances in Neural Information Processing Systems 30:Annual Conference on Neural Information Processing Systems. Long Beach:NIPS, 2017:5998-6008.
- [21] DONG L,LAPATA M. Coarse-to-fine Decoding for Neural Semantic Parsing [ C]∥Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics. Melbourne:ACL,2018:731-742.
- [22] YU T,LI Z F,ZHANG Z L,et al. TypeSQL:Knowledge-Based Type-aware Neural Text-to-SQL Generation [ C]∥ Proceedings of the Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. New Orleans:ACL,2018: 588-594.
- [23] SAPARINA I, OSOKIN A. SPARQLing Database Queries from Intermediate Question Decompositions [C]∥Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing. New York:ACL,2021:8984-8998.
- [24] BENGOETXEA K,AGIRRE E,NIVRE J,et al. On Wordnet Semantic Classes and Dependency Parsing[C]∥Proceedings of the 52nd Annual Meeting of the Association for Computational Linguistics. Baltimore:ACL,2014:649-655.
- [25] DUTKIEWICZ J,JEDRZEJEK C. Comparison of Paragram and Glove Results for Similarity Benchmarks [ C] ∥Proceedings of the Multimedia and Network Information Systems-The 11th International Conference. Berlin:Springer, 2018:236-248.
- [26] LI F,JAGADISH H V. Nalir:An Interactive Natural Language Interface for Querying Relational Databases[ C]∥ Proceedings of the 2014 ACM SIGMOD International Conference on Management of Data. New York:ACM,2014: 709-712.
- [27] ZELLE M, MOONEY R J. Learning to Parse Database Queries Using Inductive Logic Programming [ C] ∥Proceedings of the Thirteenth National Conference on Artificial Intelligence and Eighth Innovative Applications of Artificial Intelligence Conference. Portland: AAAI, 1996: 1050-1055.
- [28] ALJUNDI R,CHAKRAVARTY P,TUYTELAARS T. Whos That Actor? Automatic Labelling of Actors in TV Series Starting from IMDB Images[C]∥Proceedings of 13th Asian Conference on Computer Vision. Berlin: Springer, 2016: 467-483.

- [29] YAGHMAZADEH N,WANG Y P,DILLIG I,et al. SQLizer:Query Synthesis from Natural Language[J]. Proceedings of the ACM on Programming Languages, 2017, 5(8):63.
- [30] YU T,ZHANG R,YANG K,et al. Spider:A Large-scale Human-labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task[C]∥Proceedings of the Conference on Empirical Methods in Natural Language Processing. Brussels:ACL,2018:3911-3921.
- [31] RAFFEL C,SHAZEER N,ROBERTS A,et al. Exploring the Limits of Transfer Learning with A Unified Text-to-Text Transformer [ J]. Journal of Machine Learning Research,2020,21(1):5485-5551.
- [32] WOLF T,DEBUT L,SANH V,et al. Transformers:State-ofthe-art Natural Language Processing[C]∥Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations. Online: ACL, 2020:38-45.
- [33] GUAN L. Weight Prediction Boosts the Convergence of AdamW[ C]∥Proceedings of 27th Pacific-Asia Conference on Knowledge Discovery and Data Mining. Osaka: Springer,2023:329-340.

#### 作者简介:

向 宁 男,(1978—),硕士, 副教授。 主要研究方向: 人工智能、软件工程。

2025 年第 51 卷第 3 期 无线电通信技术 529