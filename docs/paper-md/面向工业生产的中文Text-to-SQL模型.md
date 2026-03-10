文章编号:1001-9081(2022)10-2996-07 DOI:10. 11772/j. issn. 1001-9081. 2021081525

# 面向工业生产的中文Text-to-SQL模型

吕剑清<sup>1</sup> ,王先兵1\* ,陈 刚<sup>1</sup> ,张 华<sup>2</sup> ,王明刚<sup>3</sup>

(1. 空天信息安全与可信计算教育部重点实验室(武汉大学),武汉 430072;

2. 武汉大学 计算机学院,武汉 430072; 3. 遵义铝业股份有限公司,贵州 遵义563100)

(∗ 通信作者电子邮箱xbwang@whu. edu. cn)

摘 要:英文自然语言查询转SQL语句(Text-to-SQL)任务的模型迁移到中文工业Text-to-SQL任务时,由于工业数 据集的可解释差且比较分散,会出现数据库的表名列名等信息与问句中关键信息的表示形式不一致以及问句中的列 名隐含在语义中等问题导致模型精确匹配率变低。针对迁移过程中出现的问题,提出了对应的解决方法并构建修改 后的模型。首先,在数据使用过程中融入工厂元数据信息以解决表示形式不一致以及列名隐含在语义中的问题;然 后,根据中文语言表达方式的特性,使用基于相对位置的自注意力模型直接通过问句以及数据库模式信息识别出 where子句的value值;最后,根据工业问句查询内容的特性,使用微调后的基于变换器的双向编码器表示技术(BERT) 对问句进行分类以提高模型对SQL语句结构预测的准确率。构建了一个基于铝冶炼行业的工业数据集,并在该数据 集上进行实验验证。结果表明所提模型在工业测试集上的精确匹配率为74. 2%,对比英文数据集Spider上各阶段主 流模型的效果后可以看出,所提模型能有效处理中文工业Text-to-SQL任务。

关键词:中文Text-to-SQL任务;工业数据集;元数据;自注意力模型;基于变换器的双向编码器表示技术 中图分类号:TP391. 2 文献标志码:A

## Chinese Text-to-SQL model for industrial production

LYU Jianqing<sup>1</sup> ,WANG Xianbing1\* ,CHEN Gang<sup>1</sup> ,ZHANG Hua<sup>2</sup> ,WANG Minggang<sup>3</sup>

(1*. Key Laboratory of Aerospace Information Security and Trusted Computing*,

*Ministry of Education* (*Wuhan University*), *Wuhan Hubei* 430072, *China*;

2*. School of Computer Science*, *Wuhan University*, *Wuhan Hubei* 430072, *China*;

3*. Zunyi Aluminum Industry Company Limited*, *Zunyi Guizhou* 563100, *China*)

Abstract: When the model of translating English natural language questions into Structured Query Language (SQL) statements (Text-to-SQL) is migrated to Chinese industrial Text-to-SQL task, due to the poor interpretability and strong dispersion of industrial datasets, the representation format of the information of table names and column names in database are often inconsistent with the key information in questions, and the column names in questions are often hidden in the semantics, which leads to a lower exact match accuracy. Aiming at the problems appeared in migration, the corresponding solution was proposed and a modified model was constructed. Firstly, in data use process, factory metadata information was used to solve problem of inconsistency in representation format and the problem that the column names were hidden in the semantics. Then, according to the characteristics of Chinese language expression, a self-attention model based on relative position was used to directly identify the value of where clause by questions and database mode information. Finally, according to the characteristics of the query of industrial questions, the fine-tuned Bidirectional Encoder Representation from Transformers (BERT) was used to classify questions in order to improve the accuracy of SQL statement structure prediction. An industrial dataset based on the aluminum smelting industry was constructed and experimental verification was performed on this dataset. The results show that the exact match accuracy of the proposed model on the industrial test set is 74. 2%. Compared with the effect of the mainstream models on English dataset Spider, it can be seen that the proposed model can effectively deal with the Chinese industrial Text-to-SQL task.

Key words: Chinese Text-to-SQL task; industrial dataset; metadata; self-attention model; Bidirectional Encoder Representation from Transformers (BERT)

收稿日期:2021⁃08⁃27;修回日期:2021⁃11⁃20;录用日期:2021⁃11⁃24。 基金项目:国家自然科学基金资助项目(51977155)。

作者简介:吕剑清(1998—),男,湖北黄冈人,硕士研究生,主要研究方向:大数据、人工智能; 王先兵(1972—),男,湖北江陵人,副教授,博 士,主要研究方向:数据挖掘与分析、计算机视觉; 陈刚(1970—),男,湖北武汉人,教授,博士生导师,博士,主要研究方向:网络安全、人工智 能; 张华(1973—),男,湖北仙桃人,讲师,博士,主要研究方向:大数据挖掘管理与分析; 王明刚(1979—),男,贵州贵阳人,高级工程师,硕 士,主要研究方向:铝冶炼智能制造。

## 0 引言

自然语言查询转 SQL(Structured Query Language)语句 (Text-to-SQL)任务就是将自然语言描述转化成对应的 SQL 查询语句。随着工业自动化水平和信息化水平不断发展,工业生产领域早已积累了大量的生产数据。但工业领域与传统商业领域不同,工业领域产生的数据可解释性差且比较分散,这就使得目前工业生产领域所产生的大部分数据还停留在数据仓库层面,仅仅只是将历史数据保存起来,并没有有效发挥这些数据的价值。利用Text-to-SQL模型,工厂管理人员不再需要去了解具体数据库配置信息和数据表信息等底层存储细节,仅仅需要通过自然语言的交互方式便可获取想要的数据。

Text-to-SQL任务的历史悠久,自20世纪70年代以来,自然语言数据库接口任务就开始受到人们关注<sup>[1-5]</sup>,受限于当时的技术发展,这些方法无法适用于复杂多变的自然语言查询场景,只能应用在简单的单表查询任务中。直到近几年,随着语义分析高级神经方法的发展以及大规模、跨领域的Text-to-SQL数据集WikiSQL<sup>[6]</sup>和Spider<sup>[7]</sup>的发布,它才渐渐回归人们的视线。

目前 Text-to-SOL 任务主要分为单表查询和多表查询两 种场景。单表查询由于其事先明确了SQL查询所对应的表 格以及自然语言查询问句对应的 SQL语句结构, 早在 2019 年英文单表查询数据集 WikiSQL 和中文单表查询数据集 TableQA 上最优模型[8-9]的准确率就已经达到了普通人类水 平,因此当前研究人员的目标在于多表查询的Text-to-SQL任 务。在真实的查询场景中,用户查询的数据往往包含了数据 库中的多个表,SOL语句的复杂程度也大大提升,因此Yu 等[7]发布了大规模、跨领域的英文多表查询数据集Spider,研 究人员提出了很多新颖的处理策略和模型使得 Spider 数据 集任务的准确率得到了显著提升[10-15]。相较之下中文多表 Text-to-SQL任务的研究相对较少,虽然目前已经发布了中文 多表查询数据集 Cspider<sup>[16]</sup>和 DuSQL<sup>[17]</sup>,但当前 Text-to-SQL 任务相关的研究都聚焦于英文数据集,中文多表查询任务在 推出数据集后仍有待研究。本文借鉴英文的模型和处理方 法并结合实际查询需求对模型进行微调后,构建了新的模型 用于处理中文工业数据集查询任务。

本文使用基于铝冶炼行业的工业生产数据集,在对英文模型进行迁移的过程中,主要存在以下几点问题:

- 1)自然语言查询的描述与数据库中表名和列名等数据库对象信息的描述不一致,即数据库中表名和列名一般为缩略语等简略化表达形式,例如自然语言问句中的"出铝量",在数据库中的对应列名描述为"AlCnt"。
- 2)SQL语句的列名未明显出现在问句中,而是包含在该 列所存储的数据中,很常见的一类就是记录时间信息的列。
- 3)目前英文模型在识别自然语言问句的 where 子句中列名对应的 value 值时使用的方法难以应用于大型的工业数据表。文献 [18] 通过基于变换器的双向编码器表示技术 (Bidirectional Encoder Representation from Transformers, BERT)计算出自然语言问句与数据库表中该列存储的所有

数据的注意力分数,这种方法适用于Spider这种单表数据量小的数据集,但实际工业数据集中大部分数据表都存储上万条数据,所以实际工业数据集的 value 识别需要寻求其他解决方法。

英文模型识别自然语言问句关键信息时所用的是指针 网络(pointer network)[19], pointer network 最后的输出结果会 指向输入序列,即输出只能从输入序列中选择,导致最终英 文模型迁移后会产生前两类问题。根据文献[15],Spider任 务中50%的错误都是由这两类问题导致。针对这两个问题, 本文模型选择在数据库模式标记的过程中添加元数据。第 一类问题本文选择将工厂元数据信息添加到具体的数据使 用中,通过元数据对自然语言中的描述进行规范化。第二类 问题主要分为两种情况:1)时间短语的识别,90%以上的工 业报表都包含存储时间信息的列,同时由于时间短语的表达 形式多种多样,本文使用BERT+双向长短期记忆(Bidirectional Long Short-Term Memory, BiLSTM)+条件随机场 (Condition Random Field, CRF)模型提取自然语言问句中的 时间实体。2)时间短语以外的情况,本文将自然语言中能暗 含对应列名的序列称为标签项。例如"武汉"这个标签项暗 含了它对应的列名"city",即生成的SQL语句中会存在 "city='武汉'"。这种情况在工业查询中也经常存在,例如氧 化铝生产中"锅炉煤耗"这个标签项暗含了对应的列名 "tagname"。但是不同于时间短语,这种标签项的数量是有 限的,数据仓库设计等工业元数据中会记录表格中的标签项 信息,本文通过N元语言(N-Gram)模型即可标记出自然语言 中的标签项和对应的列实体。

针对 value 问题,本文发现中文自然语言查询中 value 经常出现在对应 column 相近的位置,根据这一特性本文使用基于相对位置的注意力机制来识别问句中的 value。针对实际工业数据集中 SQL语句的结构问题,本文从 SQLNet<sup>[20]</sup>所用到的 sketch 中得到灵感,同时不同于 SQLNet 仅仅只有一种标准形式,在详细分析工业自然语言问句的特征后将问句进行分类,每种类别设置不同的标准形式,这几个类别足以涵括绝大部分查询场景。

本文主要研究中文Text-to-SQL的工业应用,直接将英文的主流模型迁移到中文工业Text-to-SQL任务后得到的SQL语句精确匹配率都不高。本文在分析错误原因后发现当前主流模型难以处理列名描述不一致和列名未明显出现在问句中等问题,然后针对这些问题构建了新的模型。本文模型在关键信息标记过程中添加元数据信息解决以上两个问题,然后结合中文问句中value值的特性,改用相对位置的注意力机制识别where子句的value值,最后在处理SQL语句结构时结合了工业自然语言问句自身的特点,对问句进行分类后通过槽填充的方式提高SQL语句结构预测的准确率。

#### 1 数据集

由于缺乏工业领域的标准数据集,本文根据工厂业务人员的实际需求通过人工扩充的方式获取用于训练和测试的Text-to-SQL数据集,这些问句囊括绝大部分的查询场景。本次实验的自然语言问句共2836条,测试集问句350条。为

了验证最终的精确匹配率,本文为测试集中的 350 条问句设 计了准确的 SQL 语句,即 Gold SQL。数据库方面使用部分氧 化铝和电解铝的数据表,共包含数据表格 27个。

本文总结了工业数据集和其他 Text-to-SQL 数据集的统 计 数 据 ,结 果 如 表 1 所 示 。 其 中 :ATIS[21]、GeoQuery[22]和 Spider 均为英文数据集;Cspider 和 DuSQL 均为中文数据集且 Cspider 是对 Spider 进行中文翻译后得到的。表 1 中,Q 表示 自然语言查询的数量,DB 表示该数据集中包含的数据库数 量,Domain 代表数据集涉及的领域数量,Table/DB 表示平均 每个数据库中数据表的数量。

图 1 为 Spider 数据集和本文数据集中数据库表格的样 例 ,其 中 数 据 表 mill 来 源 于 Spider 数 据 集 ,数 据 表 fact\_pot\_dailymeasure 来源于本文构建的铝冶炼数据集。可 以看出工业数据集中列名和表名的描述都不会与自然语言 描述一致,例如"PotNo"表示电解槽槽号。对比两张数据表 可以看出 Spider、CSpider和 DuSQL 三个数据集中存储的数据 都属于主数据,在企业中是用来定义业务对象的、具有持续 性和稳定性的数据,而工业生产中常用的是会随着时间迁移 数据量越来越多的业务数据。

表1 Text-to-SQL数据集的比较

Tab. 1 Comparison of Text-to-SQL datasets

| 数据集      | Q      | DB  | Domain | Table/DB |
|----------|--------|-----|--------|----------|
| ATIS     | 5 280  | 1   | 1      | 32. 0    |
| GeoQuery | 877    | 1   | 1      | 6. 0     |
| Spider   | 10 181 | 200 | 138    | 5. 1     |
| CSpider  | 9 691  | 166 | ―      | 5. 3     |
| DuSQL    | 23 797 | 200 | ―      | 4. 1     |
| 本文数据集    | 2 836  | 1   | 1      | 27. 0    |

| (aliman) M H |    |                       |                   |             |            |                   |  |  |
|--------------|----|-----------------------|-------------------|-------------|------------|-------------------|--|--|
| Architect_id | id | location              | name type         |             | built_year | notes             |  |  |
| 1            | 1  | Coswarem              | Le Vieux Molen    | Grondzeiler | 1840       | Molenechos(Dutch) |  |  |
| 1            | 2  | Donceel               | Moulin Bertrand   | Grondzeiler | 1890       | Molenechos(Dutch) |  |  |
| 2            | 3  | Fexhe-le-haut-Clocher | Moulin de Fexhe   | Grondzeiler | 1843       | Molenechos(Dutch) |  |  |
| 3            | 4  | Momalle               | Moulin de Momalle | Bergmolen   | 1850       | Molenechos(Dutch) |  |  |
| 4            | 5  | Othee                 | Moulin du Chateau | Grondzeiler | 1856       | Molenechos(Dutch) |  |  |
| 4            | 6  | Pousset               | Moulin de Pousset | Grondzeiler | 1819       | Molenechos(Dutch) |  |  |

| PotNo | DDate      | AlCnt | Lsp | Djzsp | Fzb | Djwd | FeCnt | SiCnt | AlOCnt |
|-------|------------|-------|-----|-------|-----|------|-------|-------|--------|
| 2102  | 2021-02-26 | 2970  | 280 | 170   |     | 957  | 0.08  | 0.04  |        |
| 2103  | 2021-02-26 | 2840  | 320 | 160   |     | 950  | 0.13  | 0.05  |        |
| 2104  | 2021-02-26 | 3000  | 280 | 150   |     | 943  | 0.08  | 0.04  |        |
| 2105  | 2021-02-26 | 2970  | 260 | 160   |     | 950  | 0.09  | 0.04  |        |
| 2106  | 2021-02-26 | 3000  | 290 | 150   |     | 959  | 0.08  | 0.04  |        |
| 2107  | 2021-02-26 | 2980  | 280 | 150   |     | 953  | 0.09  | 0.06  |        |

图1 Spider数据集和工业数据集中数据表的比较

Fig. 1 Comparison of data tables in Spider dataset and industrial dataset

图 2 中给出了一些铝冶炼自然语言查询的示例,可以看 出工业需求的自然语言查询更加注重业务数据而不是实体 之间的关系。业务数据具有鲜明的动态时空特性,使得 90% 以上的工业自然语言查询问句中都包含时间实体,因此模型 迁移过程中必须要对时间实体进行准确识别。相较于数据 含义简单明了的 Spider 数据集,本文的铝冶炼数据集是面向 行业的数据集,符合实际工业应用中 SQL查询的分布。

图2 SQL查询示例

Fig. 2 SQL query examples

## 2 本文模型

## 2. 1 时间实体识别

本文模型使用命名实体识别(Named Entity Recognition, NER)来提取自然语言问句中的时间表达式,NER 旨在定位 文本中的命名实体并分类为预先定义的类别,例如文献[23] 中用来识别医学时间短语。时间实体识别板块如图 3 所示, 识别文本中的时间实体采用 BERT+BiLSTM+CRF 模型。首 先,使用 Google BERT 的 Chinese\_L-12\_H-768\_A-12 模型作为 特征表示层,相对于只输出静态词向量的 Word2vec,BERT 采用先进的 Transformer 模型,使得每个词都可以捕获到文本 双向关系;然后,将特征表示层的输出加入 BiLSTM 中学习单 词的上下文语义表示;最后经过 CRF 对 BiLSTM 层的输出进 行优化,充分考虑序列前后的标签信息以获取全局最优的标 签输出。

## 2. 2 表名列名识别

Schema Link[11] 的目标就是实现问句中表述的内容与数 据库的表名和列名等数据库模式信息的映射,然后将得到的 列名和表名的标记信息同自然语言问句和数据表结构信息 一同作为神经网络的输入,以提高模型的准确率。

首先针对自然语言问句于数据表的表名和列名描述不 一致的问题,通过在 Schema Link 的过程中引入包含技术元 数据的数据字典实现列名的映射,之后根据标记的列名来标 记问句中涉及的表名。对于 column 未明确出现在问句中的问题,这类问题出现的原因在于某些标签项能隐性说明它所对应的 column,除了 2.1 节提到的时间序列因其本身表述方式多种多样的特点需要单独处理外,其他情况可以根据数据字典、数据仓库设计等元数据完成映射。图 4是铝冶炼数据集的一个例子,自然语言问句为"氧化铝厂 2020 年 9 月 3 号叶滤精液中苛性化氧化铝的化验量?",其中"叶滤精液"是列名为 tagname 的标签项。在没有其他外部信息输入的情况下当前主流模型难以直接通过"叶滤精液"这个标签项找到对应的 column,但工厂元数据中会存储这些有限的标签项信息,因此"叶滤精液"这类标签项可以通过技术元数据的数据仓库设计构建标签项与其对应列名之间的映射关系来找到

对应的列名。

如图 3 所示,本文使用 N-Gram 模型实现 Schema Link。 N-Gram 模型主要用于评估一个句子是否合理和评估两个字符串之间的差异,后者可以用于进行模式匹配(又称字符串查找)。首先枚举出问句中1到6所有的字符串组合(gram),然后按照长度降序的方式与元数据中的数据字典进行匹配,如果一个gram 被认定为列名,则移除与之重叠的全部gram。通过以上方法识别问句中所有的列名实体,然后通过列名可以确认对应的表名。特别地,氧化铝的化验表中存在不同表中有相同的列项的情况,由于不同的表存储的是不同标签项上的化验信息,因此通过元数据和识别出来的标签项确定对应的表名。

![](_page_3_Figure_6.jpeg)

图 3 本文模型的整体结构

Fig. 3 Overall structure of the proposed model

表名: fact\_ao\_dissolution\_dailyassay

| Tagname         | Nk    | Nt    | ΑO                                                                                                          | Э | αk    | checktime  |  |  |
|-----------------|-------|-------|-------------------------------------------------------------------------------------------------------------|---|-------|------------|--|--|
| 叶滤精液            | 153.9 | 174.9 | 179.0                                                                                                       |   | 1.414 | 2020-09-03 |  |  |
| 蒸发原液            | 161.3 | 182.8 | 95.6                                                                                                        |   | 2.775 | 2020-09-03 |  |  |
| 循环母液            | 231.0 | 262.2 | 137.0                                                                                                       |   | 2.773 | 2020-09-03 |  |  |
| 平底母液            | 158.9 | 181.2 | 91.4                                                                                                        |   | 2.860 | 2020-09-03 |  |  |
| 叶滤精液            | 156.0 | 183.6 | 180.9                                                                                                       |   | 1.418 | 2020-09-04 |  |  |
| 自然语言问句: SQL:    |       |       |                                                                                                             |   |       |            |  |  |
| 氧化铝厂20<br>液中苛性化 |       |       | SELECT αk from fact_ao_<br>dissolution_dailyassay<br>where Tagname = "叶滤精液"<br>and checktime = "2020-09-03" |   |       |            |  |  |

图 4 中文数据集的例子

Fig. 4 Example of Chinese dataset

#### 2.3 value 值识别

针对 where 子句中 value 的识别,目前的方法大多基于数据库内容(database content)<sup>[18]</sup>,这种方法在 Spider 这类每个数据表内容不够多的数据集上有良好的效果,但是实际工业应用中每张数据表的数据量远比 Spider 上多,所以在实际应用中需要考虑新的处理方法。本研究着眼于实际的工业查询任务,使用了一种基于相对位置的注意力<sup>[24]</sup>模型来实现value 值的识别。

自注意力(self-attention) $^{[25]}$ 模型的结构如图 5 所示。对于 self-attention, Q(Query)、K(Key)、V(value)3 个矩阵均来自同一输入。首先计算 Q 与 K 之间的点乘; 然后为了防止其结

果过大,除以一个尺度标度 $\sqrt{d_z}$ ;再通过Softmax函数将其结果归一化为一个概率分布;最后再乘以矩阵V就得到权重求和向量,这个向量可以很好地考虑问句的上下文信息。

![](_page_3_Figure_17.jpeg)

图 5 自注意力模型的结构

Fig. 5 Structure of self-attention model

相对位置的模型在 self-attention 的基础上,引入了两个与相对位置相关的向量: $a_{ij}^{V}$ 、 $a_{ij}^{K}$ ,两个向量采用 $d_a$ 维向量的表示形式。具体公式如下:

$$z_i = \sum_{i=1}^{n} \boldsymbol{a}_{ij} \left( \boldsymbol{x}_j \boldsymbol{W}^V + \boldsymbol{a}_{ij}^V \right)$$
 (1)

其中权重系数 $a_{ii}$ 通过Softmax计算得到:

$$\boldsymbol{a}_{ij} = \exp(\boldsymbol{e}_{ij}) / \sum_{i=1}^{n} \exp(\boldsymbol{e}_{ik})$$
 (2)

兼容函数 ei 计算方法使用 Scaled dot product:

$$\mathbf{e}_{ii} = \mathbf{x}_i \mathbf{W}^{Q} (\mathbf{x}_i \mathbf{W}^K + \mathbf{a}_{ii}^K)^{\mathrm{T}} / \sqrt{d_z}$$
 (3)

 $z_i$ 是每个输入序列 $x_i$ 通过加权求和得到的输出元素,也就是说,如果 $x_i$ 是 attention的目标词,那么在计算 $x_j$ 对 $x_i$ 的注意力特征时,需要额外考虑 $x_j$ 对 $x_i$ 的两个与位置相关的向量。

$$\boldsymbol{a}_{ii}^{V} = \boldsymbol{w}_{clin(i-i,k)}^{V} \tag{4}$$

$$\boldsymbol{a}_{ii}^{K} = \boldsymbol{w}_{clin(i-i,k)}^{K} \tag{5}$$

$$clip(x,k) = \max(-k,\min(k,x))$$
(6)

本文将最大相对位置裁剪为最大绝对值k,即假设序列中两个元素的距离超过预先设定的k,则判定两元素之间的位置信息就没有意义,裁剪最大距离还能使得模型可以推广到训练期间没见到过的序列长度。本文设置k=4,并且最终只需关注与column最相关的即为对应的value。

#### 2.4 自然语言问句分类

在对铝生产行业进行实际考察后,总结了实际工业需求 的自然语言输入问题的四个特点:

- 1)查询的目标更多注重于业务数据而不是实体之间的 关系或知识,即物品的产量、材料的消耗、机器的运行状态以 及产品的质量检测结果等。
- 2)查询的数据经常包含聚合操作,例如最值问题和平均值问题。
- 3)查询问句中的实体描述一般都较为规范,即所查询的 属性一定是数据库中原本就有的属性。
- 4)工业应用中查询的数据很大部分属于生产业务数据, 所以问句中一般都会包含有时间信息,如"昨天""2021年1 月1日"。由于时间信息的表达方式多种多样,但是在数据 库中时间字段的存储格式均是统一的,因此需要将问句中的 时间段和时间点都进行规范化。

根据以上特点将自然语言问句分为以下几个类别:

#### 1)一般查询类问题。

该类问题主要是查询某个时间或时间段的一个或多个属性值。例如"2021年3月20日槽号为2835的电解槽的出铝量,铝水平?"。可以看到这类问题的查询可以分为槽号、出铝量、铝水平三个关键主体,其中有确定 value 值的2835判定为查询条件,问句中找不到对应 value 的判定为查询目标,所以查询的主体表就应该是包含有电解槽每日出铝信息的数据表。

#### 2)最值问题。

该类问题主要是以最值为查询条件得到一个或多个查询目标。例如"2020年9月23号出铝量最大的电解槽槽号?"。

#### 3)时间段最值问题。

该类问题主要是查询目标在一段时间内的最值。例如 "氧化铝厂 2021年1月1号到1月30号最大实产氧化铝量?"。

#### 4)均值问题。

该类问题主要是查询某个时间或时间段的属性均值。

例如"今天电解一区电解槽的平均工作电压?""氧化铝厂1月15号到2月15号平均每天的锅炉煤耗?"。

分类方法使用BERT中文预训练模型,对BERT的最后一层进行微调后即可用于本文的分类任务中。重载其中的DataProcessor类并在主函数中添加该类,对输入数据进行预处理后即可用于训练和测试,BERT的标志位CLS接Softmax用于输出分类结果。

## 3 实验与结果分析

#### 3.1 评价标准

按照文献[7]的标准,实验通过精确匹配率对模型进行评估,即自然语言问句生成的 SQL语句与事先准备的 Gold SQL完全一致的百分比,其中各子句中列名出现的顺序不影响准确率的计算。除了测试模型在工业数据集上的表现外,本研究还评估当前主流模型在不添加元数据信息的情形下在工业数据集上的表现。由于英文模型不涉及 value 的识别,所以评判标准是不考虑 where 子句中 value 值的 SQL语句精确匹配率。

精确匹配率的计算公式如下:

$$Score_{qm} = \begin{cases} 1, & P_{SQL} = G_{SQL} \\ 0, & P_{SQL} \neq G_{SQL} \end{cases}$$
 (7)

$$Acc_{qm} = \frac{1}{N} \sum_{i=1}^{N} Score_{qm}^{i}$$
 (8)

其中:N表示自然语言问句的数量; $P_{SQL}$ 、 $G_{SQL}$ 分别代表预测的 SQL 语句、标准的 SQL 语句; $Acc_{qm}$ 代表查询匹配的准确率。

#### 3.2 对比实验

本文把测试集的350条问句进行人工英文翻译后,再将列名进行人工泛化,使得问句中的列与数据库中的表示一致,最后在英文工业测试集上使用目前Spider数据集各阶段的主流模型进行对比实验。由于Spider的实验结果不考虑value,因此对比实验也不考虑value,时间实体也可以不进行处理。实验结果如表2所示。

表 2 不同模型的精确匹配率 单位:% Tab. 2 Exact match accuracies of different models unit:%

本文数据集 模型 Spider 19. 7  $Syntax SQLNet^{[10}$ 7.4 IRNet<sup>[11]</sup> 25 7 46 7 IRNET+BERT 29.4 54.7 RAT-SOL[15] 30. 2 57 2 RAT-SQL+BERT 36.8 65.6 本文模型 74.2

其中 SyntaxSQLNet<sup>[10]</sup>、IRNet<sup>[11]</sup>和 RAT-SQL<sup>[15]</sup>为 Spider 数据集任务各阶段表现最好的基础模型。从表 2 中可以看出,Spider 数据集任务的主流模型在迁移到实际的工业数据集时准确率都偏低。根据文献[7]中所述,Spider 是面向多领域的大规模数据集,并且为了提高模型的泛用性,测试集中30%的问句是训练集中从未见过的;但是从实验结果可以看出这些模型直接用到实际的工业问句中效果并不好,主要原因在于工业数据库的表结构信息远比 Spider 数据集复杂,

同时工业数据库中存储的数据可解释性差,在没有元数据的 情况下机器难以理解自然语言查询问句的语义。另外由于 表结构的差异,测试集中大量问句的列名没有明显出现在问 句中,经统计本文构建的测试集中这类问句有 126 条,占全 部测试集的 40%,导致 Spider 任务的模型找不到正确的列名 或者根本没有识别出标签项处存在列名。对比本文模型的 结果可以看出修改后的模型在处理工业自然语言查询问题 时的有效性,同时也说明本文在迁移过程中提出的修改方法 和处理策略具有一定理论意义和研究价值。

## 3. 3 消融实验

对模型进行消融实验查看各个模块在模型中起到的作 用。首先如果不使用元数据且不对原问句进行人工同义化 处理,依靠现在模型的方法根本不能识别问句中任意一个列 实体;然后评估添加部分元数据消除表述不一致的问题后模 型的准确率;最后添加完整的元数据信息对比显示元数据在 处理列名不会明显出现在问句中的效果。消融实验在本文 构建的测试集上进行且会考虑 value。表 3 显示了消融实验 的结果。

表3 消融实验的结果 单位:%

Tab. 3 Results of ablation experiment unit:%

技术 +元数据(仅同义化) +元数据 精确匹配率 39. 4 66. 8

从表 3 可以看出,添加部分元数据后虽然可以映射到大 部分的列名,但对于问句中仅存在标签项的情况,列实体没 有被识别出来,准确率只有 39. 4%,对比英文模型准确率提 高了 3%,说明单一领域的 Text-to-SQL 问题针对查询问句的 特征设计分类模型效果更好。在添加用于映射标签项的元 数据之后本文模型的准确率提高了 20%以上,说明引入元数 据可以有效地处理列名未出现在问句中的问题。对比表 2 中本文模型的准确率可以看出本文模型在考虑 where 子句 value时精确匹配率降低了 8%,原因在于 value标记错误和匹 配错误。消融结果表明针对数据解释性差且分散的工业数 据集任务,利用存储着数据库配置信息和数据表信息的元数 据能让工业 Text-to-SQL任务的准确率得到显著的提升。

## 3. 4 错误分析

在对比分析了测试集预测的 SQL 语句和用于参照的 Gold SQL后,主要发现以下 3类错误:

- 1)value 匹配错误。主要原因在于工业自然语言问句中 where 子句涉及的列实体较多且这些列实体所存储的数据类 型相似,难以找到合适的特征区分这些 value 导致列实体的 匹配出现错误。
- 2)from 子句的表名匹配错误。主要原因在于工业数据 库中不同表中经常含有相同的字段名,导致在联合查询中会 出现表名识别错误的情况。未来的工作中将尝试使用全局 信息重排序的方法来解决这类问题。
- 3)SQL 语句的结构错误。主要有两方面:一方面问句分 类产生错误;另一方面在于本文的模型难以处理嵌套查询这

类 SQL语句结构非常复杂的自然语言查询问题,这也是当前 国内外 Text-to-SQL任务面临的最大挑战,将在未来的工作中 尝试解决这类问题。

## 4 结语

本文主要研究中文 Text-to-SQL 的工业应用,针对英文模 型迁移到中文工业 Text-to-SQL 任务过程中遇到的问题提出 了一套完整的解决方案。首先针对自然语言查询的描述与 数据库中表名和列名等数据库对象信息的描述不一致的问 题,将工厂元数据信息融入到具体的数据使用中,通过元数 据对自然语言中的描述进行规范化。其次针对列名未明显 出现在文句中的问题:一方面通过 BERT+BiLSTM+CRF 命名 实体识别模型完成时间实体的识别;另一方面通过元数据中 的数据仓库设计完成时间实体以外的标签项的映射,从而得 出对应列名的标记。再次针对工业数据表中数据存储量过 大难以直接套用英文模型的问题,利用中文问句中 value 和 column位置特性选择使用相对位置的注意力模型,这样仅需 问句和数据库模式信息即可完成 value 的识别。最后对自然 语言问句的查询特征进行归纳后使用添加问句分类模板槽 填充的方式进一步提高 SQL语句结构预测的准确率。

本文根据实际需求构建了一个中文的工业 Text-to-SQL 数据集,并在该数据集上评估了目前 Spider 任务的主流模型 以及本文改进后的模型的效果。实验结果表明修改后的模 型能有效处理工业自然语言查询问题,同时也表明本文在迁 移过程中提出的修改方法和处理策略具有一定的理论意义 和研究价值。对于嵌套查询这种非常复杂的 SQL 语句, Spider 任务上的模型和本文的模型都没能得到很好的结果。 在未来的工作中,将考虑构建严格的语法结构并通过递归的 方式来处理嵌套查询这类复杂 SQL语句的查询问题,从而进 一步提高中文工业 Text-to-SQL任务的准确率。

## 参考文献(References)

- [1] WARREN D H D, PEREIRA F C N. An efficient easily adaptable system for interpreting natural language queries[J]. American Journal of Computational Linguistics,1982,8(3/4):110-122.
- [2] ANDROUTSOPOULOS I, RITCHIE G D, THANISCH P. Natural language interfaces to databases-an introduction [J]. Natural Language Engineering,1995,1(1):29-81.
- [3] POPESCU A M, ARMANASU A, ETZIONI O, et al. Modern natural language interfaces to databases: composing statistical parsing with semantic tractability[C]// Proceedings of the 20th International Conference on Computational Linguistics. [S. l.]: COLING,2004:141-147.
- [4] HALLET C. Generic querying of relational databases using natural language generation techniques [C]// Proceedings of the 4th International Natural Language Generation Conference. Stroudsburg, PA: Association for Computational Linguistics, 2006:95-102.
- [5] GIORDANI A, MOSCHITTI A. Generating SQL queries using natural language syntactic dependencies and metadata [C]// Proceedings of the 2012 International Conference on Applications of Natural Language Processing to Information Systems, LNCS 7337.

- Berlin: Springer,2012:164-170.
- [6] ZHONG V, XIONG C M, SOCHER R. Seq2SQL: generating structured queries from natural language using reinforcement learning[EB/OL]. (2017-11-09)[2021-06-20]. https://arxiv. org/ pdf/1709. 00103. pdf.
- [7] YU T, ZHANG R, YANG K, et al. Spider: a large-scale humanlabeled dataset for complex and cross-domain semantic parsing and Text-to-SQL task[C]// Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing. Stroudsburg, PA: Association for Computational Linguistics,2018:3911-3921.
- [8] HE P C, MAO Y, CHAKRABARTI K, et al. X-SQL: reinforce schema representation with context[EB/OL]. (2019-08-21)[2021- 06-20]. https://arxiv. org/pdf/1908. 08113. pdf.
- [9] ZHANG X Y, YIN F J, MA G J, et al. M-SQL: multi-task representation learning for single-table Text2SQL generation[J]. IEEE Access,2020,8:43156-43167.
- [10] YU T, YASUNAGA M, YANG K, et al. SyntaxSQLNet: syntax tree networks for complex and cross-domain text-to-SQL task[C]// Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing. Stroudsburg, PA: Association for Computational Linguistics,2018:1653-1663.
- [11] GUO J Q, ZHAN Z C, GAO Y, et al. Towards complex Text-to-SQL in cross-domain database with intermediate representation [C]// Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics. Stroudsburg, PA: Association for Computational Linguistics,2019:4524-4535.
- [12] YU T, LI Z F, ZHANG Z L, et al. TypeSQL: knowledge-based type-aware neural Text-to-SQL generation[C]// Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. Stroudsburg, PA: Association for Computational Linguistics, 2018:588-594.
- [13] WANG C L, TATWAWADI K, BROCKSCHMIDT M, et al. Robust text-to-SQL generation with execution-guided decoding[EB/ OL]. (2018-09-13) [2021-06-20]. https://arxiv. org/pdf/ 1807. 03100. pdf.
- [14] FINEGAN-DOLLAK C, KUMMERFELD J K, ZHANG L, et al. Improving text-to-SQL evaluation methodology[C]// Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Stroudsburg, PA: Association for Computational Linguistics,2018:351-360.
- [15] WANG B L, SHIN R, LIU X D, et al. RAT-SQL: relation-aware schema encoding and linking for text-to-SQL parsers [C]// Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. Stroudsburg, PA: Association for Computational Linguistics,2020:7567-7578.
- [16] MIN Q K, SHI Y F, ZHANG Y. A pilot study for Chinese SQL semantic parsing[C]// Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing. Stroudsburg, PA: Association for Computational Linguistics, 2019:3652-3658.
- [17] WANG L J, ZHANG A, WU K, et al. DuSQL: a large-scale and

- pragmatic Chinese text-to-SQL dataset[C]// Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing. Stroudsburg, PA: Association for Computational Linguistics,2020:6923-6935.
- [18] LIN X V, SOCHER R, XIONG C M. Bridging textual and tabular data for cross-domain text-to-SQL semantic parsing [C]// Proceedings of the 2020 Findings of the Association for Computational Linguistics: EMNLP 2020. Stroudsburg, PA: Association for Computational Linguistics,2020:4870-4888.
- [19] VINYALS O, FORTUNATO M, JAITLY N. Pointer networks [C]// Proceedings of the 28th International Conference on Neural Information Processing Systems. Cambridge: MIT Press,2015: 2692-2700.
- [20] XU X J, LIU C, SONG D. SQLNet: generating structured queries from natural language without reinforcement learning[EB/OL]. (2017-11-13)[2021-06-20]. https://arxiv. org/pdf/1711. 04436. pdf.
- [21] PRICE P J. Evaluation of spoken language systems: the ATIS domain[C]// Proceedings of the 1990 Workshop on Speech and Natural Language. San Francisco: Morgan Kaufmann Publishers Inc. ,1990:91-95.
- [22] ZELLE J M, MOONEY R J. Learning to parse database queries using inductive logic programming[C]// Proceedings of the 13th National Conference on Artificial Intelligence. Menlo Park, CA: AAAI Press,1996:1050-1055.
- [23] 张顺利,王应军,姬东鸿 . 基于 BLSTM 网络的医学时间短语识 别[J]. 计算机应用研究,2020,37(4):1059-1062.(ZHANG S L, WANG Y J, JI D H. Temporal phrases extraction in clinical text based on bidirectional long-short term memory model[J]. Application Research of Computers,2020,37(4):1059-1062.)
- [24] SHAW P, USZKOREIT J, VASWANI A. Self-attention with relative position representations[C]// Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 2 (Short Papers). Stroudsburg, PA: Association for Computational Linguistics,2018:464-468.
- [25] VASWANI A, SHAZEER N, PARMAR N, et al. Attention is all you need[C]// Proceedings of the 31st International Conference on Neural Information Processing Systems. Red Hook, NY: Curran Associates Inc. ,2017:6000-6010.

This work is partially supported by National Natural Science Foundation of China (51977155).

**LYU Jianqing**, born in 1998, M. S. candidate. His research interests include big data, artificial intelligence.

**WANG Xianbing**, born in 1972, Ph. D. , associate professor. His research interests include data mining and analysis, computer vision.

**CHEN Gang**, born in 1970, Ph. D. , professor. His research interests include cyber security, artificial intelligence.

**ZHANG Hua**, born in 1973, Ph. D. , lecturer. His research interests include management and analysis of big data mining.

**WANG Minggang**, born in 1979, M. S. , senior engineer. His research interests include aluminum smelting intelligent manufacturing.