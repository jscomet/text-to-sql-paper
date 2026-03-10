# 面向研究生招生咨询的中文 Text-to-SQL 模型

王庆丰1,李旭2\*,姚春龙1,程腾腾1

(1. 大连工业大学信息科学与工程学院,辽宁 大连 116034; 2. 大连工业大学工程训练中心,辽宁 大连 116034)

摘 要: 研究生招生咨询是一种具有代表性的短时间高频次问答应用场景。针对现有基于词向量等方法的招生问答系统返回答案不够精确,以及每年需要更新问题库的问题,引入了基于文本转结构化查询语言(Text-to-SQL)技术的 RESDSQL 模型,可将自然语言问题转化为 SQL语句后到结构化数据库中查询答案并返回。搜集了研究生招生场景中的高频咨询问题,根据 3 所高校真实招生数据,构建问题与 SQL语句模板,通过填充模板的方式构建数据集,共有训练集 1 501 条、测试集 386 条。将 RESDSQL的 RoBERTa 模型替换为具有更强多语言生成能力的 XLM-RoBERTa 模型、T5 模型替换为 mT5 模型,并在目标领域数据集上进行微调,在招生领域问题上取得了较高的准确率,在 mT5-large 模型上执行正确率为 0.95,精确匹配率为 1。与基于 ChatGPT3.5 模型、使用零样本提示的 C3SQL 方法对比,该模型性能与成本均更优。

关键词:中文文本转结构化查询语言;自然语言查询;中文 SQL 语句生成;预训练模型;Text-to-SQL 数据集中图分类号:TP183 文献标志码: A DOI: 10.19678/j. issn. 1000-3428.0068504

# Chinese Text-to-SQL Model for Postgraduate Admissions Consultation

WANG Qingfeng<sup>1</sup>, LI Xu<sup>2\*</sup>, YAO Chunlong<sup>1</sup>, CHENG Tengteng<sup>1</sup>

(1. School of Information Science and Engineering, Dalian Polytechnic University, Dalian 116034, Liaoning, China; 2. Innovation and Entrepreneurship Center, Dalian Polytechnic University, Dalian 116034, Liaoning, China)

[Abstract] Postgraduate admissions consultation is a representative short-term and high-frequency Question-and-Answer (Q&A) application scenario. In response to the problem that the enrollment Q&A system based on the word vector method is not precise enough to return answers, and the problem of needing to update the question database every year, this paper introduces the RESDSQL model based on Text-to-Structured Query Language (SQL) technology to convert questions into SQL statements and then query answers in a structured database. This study collects high-frequency counseling questions in postgraduate admissions scenarios, establishes question and SQL statement templates based on real admissions data from three universities, and constructs a dataset by filling the templates, getting a dataset with a total of 1 501 training sets and 386 validation sets. The RoBERTa model is replaced with the XLM-RoBERTa model that has a stronger multi-language generative capability, the T5 model is replaced with mT5 model, and the models are fine-tuned on the target domain dataset, achieving high accuracy on the enrollment domain problem, with execution accuracy of 0.95 and exact match of 1 on the RESDSQL model base on mT5-large. Compared with the C3SQL method based on ChatGPT3.5 model and zero-shot prompting, both performance and cost of the proposed method are better.

**[Key words]** Chinese Text-to-Structured Query Language (SQL); natural language query; SQL statement generation in Chinese; pre-trained models; Text-to-SQL datasets

## 0 引言

近年来,由于数据量的迅速增长,有大量交互需求需要到结构化数据库中查询数据,研究自然语言查询的结构化语言生成问题[文本转结构化查询语言(Text-to-SQL),也称 NL2SQL]成为了一大热门。以往的中文 Text-to-SQL 研究往往针对数据量非常大的场景,例如工业信息查询、金融信息查询

等,忽视了小数据量场景下的需求。

本文所研究的研究生招生咨询是一种具有代表性的短时间高频次应用,需求主要集中在每年学校发布招生公告到考研报名结束的这段时间。在此期间,学校会接到大量的咨询请求,人工往往难以应对,因此有必要借助人工智能技术开发问答系统以减轻工作人员负担。现有的招生领域问答系统中有基于词向量的方法,也有基于 Seq2Seq 的方法,此两

**收稿日期**: 2023-10-07 **修回日期**: 2024-01-22

**基金项目**: 辽宁省教育厅青年科技人才"育苗"项目(J2020113);辽宁省教育厅科学研究项目(LJKZ0537);2024年度辽宁省属本科高校基本科研业务费专项资金资助项目(LJ212410152070)。

类方法均需要每年更新内容库或重新训练模型。考虑到招生数据通常存在于结构化数据库中,本文尝试将 Text-to-SQL 技术引入招生咨询问答系统中。考虑在小规模单一领域数据库上构建单轮多表查询数据集,利用 RESDSQL<sup>[1]</sup>方法在 mT5 模型<sup>[2]</sup>上微调,以取得较高的执行正确率。

在中文招生问答领域,目前有陈思彤<sup>[3]</sup>提出的基于词向量的方法,丁怡心<sup>[4]</sup>基于 Word2Vec 的 CBOW 模型提出的 W-Sen2Vec 方法,以及刘连喜<sup>[5]</sup>提出的基于 CNN\_BiGRU、k-max 池化 Bi-LSTM、Attention\_BiGRU 的方法。以上研究所使用的方法较为老旧,无法满足当前需求,每年更新的成本高,且需要专业技术人员维护。

早期 Text-to-SQL 研究使用基于流水线的方法,将自然语言转化为一种中间表达,再将这些中间表达转化为结构化查询语言(SQL)语句。此类方法目前已被完全抛弃。现有的主流 Text-to-SQL 模型可以分为基于 Seq2Seq 架构和非 Seq2Seq 架构两类。非 Seq2Seq 模型大多为基于 BERT<sup>[6]</sup>的编码器-解码器(Encoder-Decoder)架构,为了提高准确率需要引入图结构,例如 LGESQL<sup>[7]</sup>、SADGA等<sup>[8]</sup>基于 RAT-SQL<sup>[9]</sup>衍生的方法,利用图神经网络来编码数据库和问题之间的关系结构。另一种常见方法是通过知识图谱嵌入引入外部领域知识。尽管该方法取得了不错的成绩,但是构建并使用知识图谱带来了额外的成本与性能开销。

BRIDGE模型<sup>[10]</sup>在 BERT模型的基础上通过模糊匹配从数据库中选中对应列中的值。RaSaP模型<sup>[11]</sup>是沿 RAT-SQL 路线发展下来的最新变体,也利用相对注意力机制编码问题与数据库范式,引入了半自动渐进自下而上解析器(SmBoP<sup>[12]</sup>)作为模型解码器。基于 BRIDGE,引入数据库列值的方法显著提高了模型执行正确率。

由谷歌提出,基于 Seq2SQL 架构的大规模预训练语言模型 T5<sup>[13]</sup>,在 Text-to-SQL 这一领域优势突出。自 PICARD 方法<sup>[14]</sup>提出以来,T5 模型在英文 Text-to-SQL 研究领域已经得到大量应用。观察 Spider 数据集<sup>[15]</sup>的排行榜可知,虽然在精确匹配率评价标准上基于 BERT 及 ELECTRA 的模型与基于 T5 的模型性能接近,但基于 T5 的模型在执行正确率上表现出了无可比拟的优势。

近期 ChatGPT4 等大语言模型非常火热,基于 其的方法在 Spider 数据集执行正确率排行榜占据 前 7 名。排名第 6 的 C3SQL<sup>[16]</sup>与排名第 4 的 DIN-SQL<sup>[17]</sup>都是基于零样本提示的方法。 RESDSQL模型在 Spider 数据集排行榜上排名 靠前,是当前执行正确率排行榜上未以大语言模型 为基础的方案中准确率最高的模型。RESDSQL模型对数据库模式(Schema)进行解耦,采用主干分析的方法生成 SQL。

Text-to-SQL 模型从基于流水线的方法发展到 基于 BERT 模型的方法,再到基于 T5 模型的方法 和基于大语言模型的方法。虽然目前的 Text-to-SQL模型在公开数据集上已经能够取得较高的准 确率,但模型的泛化性能较差,在公开数据集未包含 的领域内准确度较低。例如, Spider 数据集榜单上 排名较高的 RESDSQL 模型,在 Spider 数据集的鲁 棒性变体 Spider-DK<sup>[18]</sup>上执行准确率只有 66.3%, 这表明现有模型仍然需要迁移学习才能更好地适应 下游任务。在一些不被公开数据集包含的领域,想 要获得公开信息是非常困难的,这就需要用户自行 训练符合自己需求的模型。在以往的研究中,想要 在特定领域达到较高准确率,需要构建大量数据集 进行训练。百度提出了一种跨领域、分层次的由 SQL生成自然语言问题的数据增强方法[19],旨在生 成尽可能多的 SQL 语句结构,要求有 80%的数据 库模式被生成的查询覆盖,但这种方法对于单一领 域小数据集来说太讨复杂。

在中文 Text-to-SQL 领域中, 吕剑清等<sup>[20]</sup>提出了面向工业生产的中文 Text-to-SQL 模型, 何佳壕等<sup>[21]</sup>提出了面向金融领域的 FinSQL 模型。以上两种方法均是基于预训练模型 BERT 构建的, 利用 BERT 作为编码器将自然语言问题与数据库信息编码, 利用 Bi-LSTM 等作为解码器对 SQL 语句的各部分分别解码。面向工业生产的中文 Text-to-SQL模型针对表格行数特别大的场景提出了一种基于注意力机制的键值识别方法。FinSQL 模型是在RYANSQL模型基础上做的改进。以上两种方法准确率都高于 70%, 但均为针对特定领域构建, 很难迁移到其他领域。

## 1 基础模型选择与数据集构建

#### 1.1 任务定义

将一个关系型数据库记为 D,数据库模式记为 S。用  $T = \{t_1, t_2, \dots, t_n\}$  表示一组表格,用  $C = \{c_1^1, \dots, c_{n_1}^1, c_1^2, \dots, c_{n_2}^2, c_1^N, \dots, c_{n_N}^N\}$  表示数据库所有列。用  $R = \{(c_k^i, c_h^i) \mid c_k^i, c_h^i \in C\}$  来表示外键,其中每一对  $(c_k^i, c_h^i)$  表示从  $c_k^i$  到  $c_k^i$  的外键关系。

Text-to-SQL 问题即为,给定一个自然语言问题 Q 和一个有 Schema S 的数据库 D,将 Q 翻译为

一个可以在 D 上执行的 SQL 语句 L ,以回答问 题 Q。

### 1.2 基础模型选择

Text-to-SQL模型的评价指标主要分为两种:精确匹配率(EM, $R_{\rm EM}$ )和执行正确率(EXEC, $R_{\rm EXEC}$ )。精确匹配率反映了生成的 SQL 语句与表、列的匹配程度,不考虑具体的值。执行正确率反映了生成的 SQL 语句的执行结果是否准确,不考虑表、列是否一致。考虑到实际查询场景,执行正确率指标更能体现模型查询的成功率。本文的目标是尽可能提高模型在下游任务上的执行正确率指标。

精确匹配率通过比较真实 SQL 查询语句和预测 SQL 查询语句来计算精确集匹配精度。两条语句被解析为规范化的数据结构,其中包含以下 SQL 子句,例如 SELECT、GROUP BY、WHERE、ORDER BY、KEYWORDS,包括所有的 SQL 关键词但不包括列名与操作符。只有预测的 SQL 语句中所有的子句都正确,才认为预测正确。判断方法见式(1):

$$s(\hat{\mathbf{Y}}, \mathbf{Y}) = \begin{cases} 1, & \hat{\mathbf{Y}} = \mathbf{Y} \\ 0, & \hat{\mathbf{Y}} \neq \mathbf{Y} \end{cases}$$
 (1)

式中:  $\hat{Y} = \{(\hat{k}_i, v_i), i \in (1, m)\}$ ;  $Y = \{(k_i, v_i), i \in (1, m)\}$  分别表示预测 SQL 的各部分与训练集中的正确 SQL 语句。这里的 k 代表一个 SQL 子句,v 是该子句对应的值,m 是组件的数量。

精确匹配率的计算公式见式(2):

$$R_{EM} = \frac{\sum_{n=1}^{N} s(\hat{Y}_n, Y)}{N}$$
 (2)

式中:N表示样本总数。

精确匹配率通过严格比较 SQL 中的差异来评估模型性能,但人类的 SQL 标注往往存在偏差,因为一个自然语言问题可能对应多个 SQL 查询。

执行正确率是通过比较测试集附带的数据库内容上执行真实 SQL 查询和预测 SQL 查询的输出结果来计算的。仅当执行预测 SQL 查询  $\hat{V}$  和真实 SQL 查询 V 的结果相同时,才将预测查询视为正确,见式(3):

$$s(\hat{V}, V) = \begin{cases} 1, & \hat{V} = V \\ 0, & \hat{V} \neq V \end{cases}$$
 (3)

与精确匹配率相似,执行正确率的计算公式见式(4):

$$R_{\text{EXEC}} = \frac{\sum_{n=1}^{N} s(\hat{V}_n, V)}{N}$$
 (4)

执行正确率作为评价 SQL 语句执行结果的指标,相比精确匹配率更能代表模型在实际任务场景中的能力。本文比较了 Spider 数据集执行正确率排行榜,发现基于 BERT 及其衍生架构的模型在公开数据集上执行正确率指标偏低,很多此类架构模型未公开其执行正确率。最终本文选择比较了BRIDGE v2、RaSaP、RESDSQL 3 款模型的执行正确率,同时比较了基于 ChatGPT 模型的两种方法,具体见表 1。

表 1 主流模型在 Spider 测试集上的准确率 Table 1 Accuracy of models on Spider datasets

| 提交时间       | 模型               | 精确匹配率 | 执行正确率  |
|------------|------------------|-------|--------|
| 2020-11-24 | BRIDGE v2+BERT   | 0.619 | 0. 683 |
| 2021-08-05 | RaSaP+ELECTRA    | 0.690 | 0.700  |
| 2022-04-12 | RESDSQL+NatSQL   | 0.805 | 0.841  |
| 2023-06-01 | C3SQL+ChatGPT3.5 | _     | 0.823  |
| 2023-04-21 | DIN-SQL+ChatGPT4 | _     | 0.853  |

综合考虑成本等因素,本文最终选择了当前最优的 RESDSQL 模型与 C3SQL 方法作为研究基础。RESDSQL 模型结构如图 1 所示。

▼RESDSQL将 Text-to-SQL视为翻译任务,在 输入序列中注入最相关的数据库的组织和结构, 通过一个额外的基于 RoBERTa<sup>[22]</sup>的交叉编码器 (Cross-Encoder)对表格名与列名进行排序,将数据 库信息以"表名:列名"的格式组合,根据分类概率 排序并过滤。这减轻了模型在 SQL 解析期间的 Schema-Linking 的难度,本文称这一部分为数据库 模式排序器。RESDSQL使用"模式项目"来统一 指代数据库中的表和列。每个模式项目都可以用 一个原始名称和一个语义名称来表示,例如 Spider 数据集中"flightno"匹配到了"flight number"作为 语义名称。语义名称可以更精确地表明模式项的 语义,有时语义名称与原始名称相同。RESDSQL 在输出序列中注入 SQL 骨架来扩展现有的 Seq2Seq模型方法。根据 Transformer 模型的特 性, Transformer 解码器输出的第 T 个 Token 除了 根据编码器的输出,还根据 T 之前输出的 Token 输出。因此先生成 SQL 语句的骨架,再生成 SQL 语句对模型能起到提示作用。由于解码器没有 SQL 语法约束,模型会产生一些非法语句。 RESDSQL在解码过程中进行束搜索(Beam Search),选择第一个可执行的 SQL 语句作为最终 输出。对于无法输出结果的情况,模型会输出"sql placeholder"字符串作为占位。

![](_page_3_Figure_2.jpeg)

图 1 RESDSQL 模型结构图

Fig. 1 Structure diagram of RESDSQL model

### 1.3 招生问答数据集构建

本文以大连工业大学、辽宁大学、东北大学 3 所 高校 2023 年的研究生招生信息作为数据来源。辽宁大学和东北大学均为综合类大学,分别侧重不同的领域,学科覆盖全面,涵盖文学、史学、哲学、经济学、法学、教育学、理学、工学、医学、管理学、艺术学、交叉学科等多个学科门类,具有一定的代表性。本文设计了一套数据库表结构,将招生信息提供的数据整理到结构化数据库中。

本文采用模板法构建数据集<sup>[23-24]</sup>。首先,根据学校招生资料以及多个相关网站上的常见问题,总结归纳出3个问题类别,包含初试及复试的考试内容、招生名额与报录比、学制以及学费等。由于不同院校提供的招生材料所包含的信息略有不同,针对每个问题类别设计多个子问题,并根据不同院校的实际情况进行细化处理,添加具有学校特点的问题,构建问题模板与 SQL 语句模板。例如,东北大学的研究生教育有多个办学地点,针对这一问题设计了"查询 XX 专业 XX 方向所在的办学地点"问题。对于考试内容,可以分别咨询初试与复试的专业课考试科目,可以针对专业大类

咨询,也可以根据某个具体的研究方向咨询。此外,为了适应一个问题的多种提问方式,每条 SQL 模板会对应多个表述不同的问题模板,随机抽选其中一个问题与 SQL 模板组合。从招生数据库中检索所有的学院、专业、方向等信息,注入问题与 SQL 模板中。构建完成后,按 8:2的比例将数据集分割为训练集与测试集。

以大连工业大学研究生招生数据库为例,数据库结构如图 2 所示。其中,唯一编码由院系代码、专业代码、研究方向代码、学习方式代码组成。由于各学校在编制招生计划时数据处理粒度不同,通常按专业制定,因此在招生计划表格中,取唯一代码中的院系代码与专业代码组成"院系专业代码"列。本文在 SQL 语句中引入 SUBSTR 命令,从唯一编码中截取对应的段与院系专业代码列匹配,使模型掌握表格间的对应关系。

最终得到的数据集共有1501条训练集、386条测试集,在测试集中不包含与训练集重复的专业或方向名称。为了便于开展研究,本文采用了Sqlite数据库,并利用Spider数据集构建工具,构造出与Spider数据集一致的数据结构。

![](_page_4_Figure_2.jpeg)

图 2 招生数据库结构图

Fig. 2 Structure diagram of the postgraduate admissions database

### 2 实验

模型全部训练过程在一张 NVIDIA RTX2080Ti(22 GB)显卡上进行,运行 mT5-large 需要的最低显存为 18 GB。其他配置为 AMD 5600X CPU,48 GB RAM, Debian 10 操作系统。

由于 mT5 模型以一个中文字作为 Token,直接输出的 SQL 语句中操作对象内部有空格,本模型对解码器部分做了改进,合并了 Schema 项内部空格,并对以数字为开头的表名称使用反引号包裹。

RESDSQL的训练分为两个阶段。第一阶段,先训练模式分类器对数据库 Schema 中的列名进行排序。第二阶段,将排序后的数据库 Schema 与问题一并送入 mT5 模型中。实验的超参数除批处理大小外全部沿用了 RESDSQL 的参数,这些参数已在PICARD和 RESDSQL模型的训练中被证明为最佳参数。在模式分类器中,列增强层中的头数h=8。设定批处理大小为 16,学习率为  $1\times10^{-5}$  进行优化。在 Focal Loss 中,焦点参数  $\gamma$  和加权因子  $\alpha$  分别设定为 2 和 0. 75。超参数  $k_1$  和  $k_2$  分别设置为 4 和 5。在第二阶段中,由于硬件的限制,在训练 mT5-large 模型时本文设置批处理大小为 1,mT5-large 的学习率为  $1\times10^{-5}$ 。解码部分中束搜索的 Beam Size 设置为 8。

对于模式分类器,本文将 RESDSQL 原方案中的 RoBERTa-large 更换为多语言版本 XLM-RoBERTa-large。生成的数据准确率见表 2。

表 2 模式分类器生成数据的准确率 Table 2 Accuracy of Schema-classifier

| 指标                    | 数值    |
|-----------------------|-------|
| Table AUC             | 0.999 |
| Column AUC            | 0.999 |
| Total AUC             | 1.999 |
| Table top-4 coverage  | 0.953 |
| Column top-5 coverage | 0.837 |

本文使用基于 ChatGPT 3.5-turbo 模型的 C3SQL 方法作为对比。C3SQL 方法在预处理阶段使用了与 RESDSQL 一致的数据抽取方式,具有较

强的对比价值。相关实验结果见表 3。

表3 模型在招生数据集上的准确率

Table 3 Accuracy of models on admissions datasets

| 模型与数据集           | 精确匹配率 | 执行正确率 |
|------------------|-------|-------|
| mT5-base         | 0.997 | 0.953 |
| mT5-large        | 1.000 | 0.955 |
| C3SQL+ChatGPT3.5 | 0.417 | 0.295 |

通过对比可知,RESDSQL模型能够在较少的数据集上学习到针对下游任务的SQL句式,而C3SQL方法由于未经训练,生成的结果正确率较低。通过对比mT5-base模型与mT5-large模型可知,增加模型参数量可以略微提高模型的准确率,使模型更快收敛,具体如图3和图4所示。

![](_page_4_Figure_18.jpeg)

图 3 mT5-base 模型在招生数据集上微调的准确率变化 Fig. 3 Accuracy changes of fine-tuning the mT5-base model on the admissions dataset

![](_page_4_Figure_20.jpeg)

图 4 mT5-large 模型在招生数据集上微调的准确率变化 Fig. 4 Accuracy changes of fine-tuning the mT5-large model on the admissions dataset

# 3 案例研究

从 386 条测试集中挑选出 3 条作为案例,对比了基于 ChatGPT3. 5-turbo 模型的 C3SQL 方法与基于mT5-large 的 RESDSQL 模型的输出结果。以下案例中 RESDSQL 生成的结果均与正确答案一致。

### 3.1 案例 1

问题:环境工程专业复试科目是?

标准结果:SELECT 学院名称,专业名称,复试考试形式,复试面试考试科目,面试基本内容,复试笔试科目,笔试基本内容 FROM 复试及同等学力加试信息 WHERE 专业名称 ='环境工程'。

C3SQL 答案: SELECT 复试笔试科目 FROM 复试及同等学力加试信息 WHERE 专业名称 ='环境工程专业'。

RESDSQL答案: select 学院名称,专业名称, 复试考试形式,复试面试考试科目,面试基本内容, 复试笔试科目,笔试基本内容 from 复试及同等学 力加试信息 where 专业名称 = '环境工程'。

这一例子显示了本文的模型对信息类别的敏感性,模型准确地将问题中的关键词"环境工程"与专业名称匹配,而基于 ChatGPT3.5-turbo 的 C3SQL方法则未能正确分割词汇,所生成的语句中带有不必要的"专业"二字。在与之类似的问题中,C3SQL多次出现此现象。

### 3.2 案例 2

问题:工商管理专业计划招多少人?

标准结果: SELECT 专业或方向名称,总计划,已录取推免,退役大学生士兵专项计划 FROM '2023 年招生计划 WHERE 院系专业代码 = (SELECT DISTINCT SUBSTR(唯一编码,1,9) FROM 专业目录 WHERE 专业名称 = '工商管理')。

C3SQL 答案: SELECT 总计划 FROM '2023 年 招生计划 WHERE 专业或方向名称 = '工商管理专业'。

RESDSQL 答案: select 专业或方向名称,总计划,已录取推免,退役大学生士兵专项计划 from '2023 年招生计划' where 院系专业代码 = (select distinct substr(唯一编码,1,9) from 专业目录 where 专业名称 = '工商管理')。

本研究在数据集中添加了其他公开数据集不包含的 SUBSTR 命令。C3SQL 方法由于未经微调训练,无法学习这一新指令。而 RESDSQL 经过训练后能够完美匹配正确答案。

### 3.3 案例3

问题:马克思主义理论专业马克思主义中国化研究方向的初试英语考什么?

标准结果: SELECT 考试科目名称 FROM 初试科目 WHERE 科目代码 = (SELECT 外语科目代码 FROM 初试科目代码 WHERE 唯一编码 = (SELECT DISTINCT 唯一编码 FROM 专业目录WHERE 研究方向 = '马克思主义中国化研究'AND 专业名称 = '马克思主义理论'))。

C3SQL 答案: SELECT 考试科目名称 FROM 初试科目 WHERE 科目代码 IN (SELECT 外语科目代码 FROM 初试科目代码 WHERE 唯一编码 IN (SELECT 学习方式 FROM 专业目录 WHERE 研究方向 = '马克思主义中国化研究方向' AND 专业名称 = '马克思主义理论专业' AND 专业代码 = '马克思主义中国化研究方向'))。

RESDSQL 答案: select 考试科目名称 from '初试科目' where 科目代码 = (select 外语科目代码 from 初试科目代码 where 唯一编码 = (select distinct 唯一编码 from 专业目录 where 研究方向 = '马克思主义中国化研究' and 专业名称 = '马克思主义理论'))。

C3SQL 方法生成的 SQL 语句嵌套结构正确, 但其中一条子查询的列名匹配错误,而且在这一案 例中出现了与案例 1 中类似的词汇分割错误,导致 无法正确执行。

#### 3.4 总结分析

通过上述案例对比分析 C3SQL 方法的输出,本 文认为主要的错误原因是 ChatGPT3.5-turbo 模型无 法正确分割专业属性较强且在问题中紧密相连的词 汇,导致语句执行结果出错。主要的性能差距来源是 问题中所提及的词汇与数据库中的表达不完全一致。 RESDSQL 模型借鉴了 BRIDGE 模型提出的方法,能 够寻找最相关的列值填充到生成的语句中,而 ChatGPT 模型无法直接访问数据库,尽管可以通过类 似的方法注人数据,但该部分性能仍然较弱。

受限于成本,本文未测试 ChatGPT4 模型,亦 未对 ChatGPT 模型进行 Fine-Tuning 实验。根据 C3SQL与 DIN-SQL 方法在 Spider 数据集上的性 能差距,相信经过 Fine-Tuning 后的 ChatGPT 模型 一定会有性能提升。但大语言模型仍然表现出了一 定程度的局限性,例如零样本性能在部分领域中性 能较弱,此外还有较高的部署与训练成本等。在 C3SQL的测试过程中,部分问题在第一次生成时得 到了完全失败的结果,需要重复生成,这将耗费更多 的成本。而基于 T5 模型微调的方案,训练与部署 成本均在一个可控制可接受的范围内,在当前是一种更为经济的选择。

# 4 结束语

本文构建了研究生招生问答场景的单轮单领域 多表查询数据集,并在 RESDSQL 模型上进行了相关 的实验。实验表明 RESDSQL 模型在本文构建的数 据集上微调后具有较好的准确率,能够完成查询任 务。RESDSQL模型先输出 SQL 结构再输出完整 SQL语句的输出方式使其具有较高的可迁移能力。 与基于 ChatGPT3. 5-turbo 模型的 C3SQL 方法比较, 基于 T5 的模型在部分领域相比大语言模型仍具有 一定的优势,这对其他下游任务研究具有借鉴意义。 由于真实世界数据集获取非常困难,本文只选取了 3 所学校的招生数据用于实验,专业覆盖及对话场景 还不够广,对于一些特殊场景,当前的模型可能无法 适应。未来将扩大院校覆盖范围,研究针对招生咨询 领域的多轮对话多表查询数据集,开发具有更强对话 能力的模型。由于 RESDSQL 模型本身对话能力较 弱,还将探究基于大语言模型的方案。

#### 参考文献

- [1] LI H, ZHANG J, LI C, et al. RESDSQL: decoupling schema linking and skeleton parsing for Text-to-SQL [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2302.05965.
- [2] XUE L, CONSTANT N, ROBERTS A, et al. mT5: a massively multilingual pre-trained text-to-text transformer [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2010.11934.
- [3] 陈思彤. 面向高校招生的智能问答系统的研究与实现[D]. 沈阳: 沈阳师范大学, 2019. CHEN S T. Research on intelligent question answering system based on college enrollment[D]. Shenyang: Shenyang Normal University, 2019. (in Chinese)
- [4] 丁怡心、研究生招生咨询智能问答系统的设计与实现[D]、 北京: 北京邮电大学, 2019. DING Y X. Design and implementation of the smart question answering system for postgraduate enrollment consultation[D]. Beijing: Beijing University of Posts and Telecommunications, 2019. (in Chinese)
- [5] 刘连喜. 基于深度学习的高校招生问答服务系统的研究及实现[D]. 重庆: 重庆理工大学, 2020.
  LIU L X. Research and implementation of college enrollment question and answer service system based on deep learning [D]. Chongqing: Chongqing University of Technology, 2020. (in Chinese)
- [6] DEVLIN J, CHANG M W, LEE K, et al. BERT: pretraining of deep bidirectional transformers for language understanding [EB/OL]. [2023-09-09]. http://arxiv.org/ abs/1810.04805.
- [7] CAO R, CHEN L, CHEN Z, et al. LGESQL: line graph enhanced Text-to-SQL model with mixed local and non-local relations [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2106.01093.
- [8] CAIR, YUAN J, XUB, et al. SADGA: structure-aware

- dual graph aggregation network for Text-to-SQL[EB/OL]. [2023-09-09]. http://arxiv.org/abs/2111.00653.
- [9] WANG B, SHIN R, LIU X, et al. RAT-SQL: relation-aware schema encoding and linking for Text-to-SQL parsers [EB/OL]. [2023-09-09]. http://arxiv.org/abs/1911.04942.
- [10] ZHAO C, SU Y, PAULS A, et al. Bridging the generalization gap in Text-to-SQL parsing with schema expansion [C]//Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Dublin, Ireland: Association for Computational Linguistics, 2022: 5568-5578.
- [11] HUANG J, WANG Y, WANG Y, et al. Relation aware semi-autoregressive semantic parsing for NL2SQL[EB/OL]. [2023-09-09]. http://arxiv.org/abs/2108.00804.
- [12] RUBIN O, BERANT J. SmBoP: semi-autoregressive bottom-up semantic parsing [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2010.12412.
- [13] RAFFEL C, SHAZEER N, ROBERTS A, et al. Exploring the limits of transfer learning with a unified text-to-text transformer[EB/OL]. [2023-09-09]. http://arxiv.org/abs/1910.10683.
- [14] SCHOLAK T, SCHUCHER N, BAHDANAU D. PICARD: parsing incrementally for constrained auto-regressive decoding from language models [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2109.05093..
- [15] YU T, ZHANG R, YANG K, et al. Spider: a large-scale human-labeled dataset for complex and cross-domain semantic parsing and Text-to-SQL task [EB/OL]. [2023-09-09]. http://arxiv.org/abs/1809.08887.
- [16] DONG X, ZHANG C, GE Y, et al. C3: zero-shot Text-to-SQL with ChatGPT[EB/OL]. [2023-09-09]. http://arxiv.org/abs/2307.07306.
- [17] POURREZA M, RAFIEI D. DIN-SQL: decomposed incontext learning of Text-to-SQL with self-correction [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2304.11015.
- [18] GAN Y, CHEN X, PURVER M. Exploring underexplored limitations of cross-domain Text-to-SQL generalization [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2109.05157.
- [19] WU K, WANG L, LI Z, et al. Data augmentation with hierarchical SQL-to-Question generation for cross-domain Text-to-SQL parsing[EB/OL]. [2023-09-09]. http://arxiv. org/abs/2103.02227.
- [20] 吕剑清, 王先兵, 陈刚, 等. 面向工业生产的中文 Text-to-SQL模型[J]. 计算机应用, 2022, 42(10): 2996-3002. LÜJQ, WANG XB, CHENG, et al. Chinese Text-to-SQL model for industrial production [J]. Journal of Computer Applications, 2022, 42(10): 2996-3002. (in Chinese)
- [21] 何佳蠔, 刘喜平, 舒晴, 等. 带复杂计算的金融领域自然语言查询的 SQL 生成[J]. 浙江大学学报(工学版), 2023, 47(2): 277-286.

  HE J H, LIU X P, SHU Q, et al. SQL generation from natural language queries with complex calculations on financial data [J]. Journal of Zhejiang University (Engineering Science), 2023, 57(2): 277-286. (in Chinese)
- [22] LIU Y, OTT M, GOYAL N, et al. RoBERTa: a robustly optimized BERT pretraining approach [EB/OL]. [2023-09-09]. http://arxiv.org/abs/1907.11692.
- [23] SUN N, YANG X, LIU Y. TableQA: a large-scale Chinese Text-to-SQL dataset for table-aware SQL generation [EB/OL]. [2023-09-09]. http://arxiv.org/abs/2006.06434.
- [24] WANG L, ZHANG A, WU K, et al. DuSQL: a large-scale and pragmatic Chinese Text-to-SQL dataset[C]//Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP). Online: Association for Computational Linguistics, 2020; 6923-6935.

编辑 陆燕菲