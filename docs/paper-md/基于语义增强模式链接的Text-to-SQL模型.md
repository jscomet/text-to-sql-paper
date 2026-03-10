计算机应用,

文章编号:1001-9081(2024)09-2689-07 DOI:10. 11772/j. issn. 1001-9081. 2023091360

# 基于语义增强模式链接的Text-to-SQL模型

吴相岚,肖 洋,刘梦莹,刘明铭\*

(南开大学 软件学院,天津 300457)

(∗ 通信作者电子邮箱liumingming@nankai. edu. cn)

摘 要:为优化基于异构图编码器的 Text-to-SQL生成效果,提出 SELSQL模型。首先,模型采用端到端的学习框 架,使用双曲空间下的庞加莱距离度量替代欧氏距离度量,以此优化使用探针技术从预训练语言模型中构建的语义 增强的模式链接图;其次,利用 *K*头加权的余弦相似度以及图正则化方法学习相似度度量图使得初始模式链接图在 训练中迭代优化;最后,使用改良的关系图注意力网络(RGAT)图编码器以及多头注意力机制对两个模块的联合语义 模式链接图进行编码,并且使用基于语法的神经语义解码器和预定义的结构化语言进行结构化查询语言(SQL)语句 解码。在Spider数据集上的实验结果表明,使用ELECTRA-large预训练模型时,SELSQL模型比最佳基线模型的准确 率提升了2. 5个百分点,对于复杂SQL语句生成的提升效果很大。

关键词:模式链接;图结构学习;预训练语言模型;Text-to-SQL;异构图

中图分类号:TP183 文献标志码:A

# Text-to-SQL model based on semantic enhanced schema linking

WU Xianglan,XIAO Yang,LIU Mengying,LIU Mingming\* (*College of Software*, *Nankai University*, *Tianjin* 300457, *China*)

Abstract: To optimize Text-to-SQL generation performance based on heterogeneous graph encoder, SELSQL model was proposed. Firstly, an end-to-end learning framework was employed by the model, and the Poincaré distance metric in hyperbolic space was used instead of the Euclidean distance metric to optimize semantically enhanced schema linking graph constructed by the pre-trained language model using probe technology. Secondly,*K*-head weighted cosine similarity and graph regularization method were used to learn the similarity metric graph so that the initial schema linking graph was iteratively optimized during training. Finally, the improved Relational Graph ATtention network (RGAT) graph encoder and multi-head attention mechanism were used to encode the joint semantic schema linking graphs of the two modules, and Structured Query Language (SQL) statement decoding was solved using a grammar-based neural semantic decoder and a predefined structured language. Experimental results on Spider dataset show that when using ELECTRA-large pre-training model, the accuracy of SELSQL model is increased by 2. 5 percentage points compared with the best baseline model, which has a great improvement effect on the generation of complex SQL statements.

Key words: schema linking; graph structure learning; pre-trained language model; Text-to-SQL; heterogeneous graph

# 0 引言

Text-to-SQL 解析的目的是在关系数据库上下文中将自 然语言(Natural Language,NL)问题转换为相应的结构化查 询语言(Structured Query Language,SQL)。为解决更多的非 技术型用户可以访问关系数据和使用关系数据库查询的问 题,将 NL 转化为 SQL 语句的专业工具必不可少,而这就依赖 于 Text-to-SQL 的语义解析。因此,能更好地进行 Text-to-SQL 语义解析的方法是当前学术界和业界的关注焦点。

由于大型跨域多表数据集 Spider 的开发,这要求模型能 够应对复杂环境以及拥有稳定泛化性。因此,如何更好地编 码问题词和模式项之间的关系,以获得问题词和模式项之间 更精确和完整的模式链接成了重中之重。为了应对上述问 题,基于图神经网络(Graph Neural Network,GNN)的编码器 和更精确的模式链接组件必不可少。

之前的基于图的部分工作[1-5] 都是以节点为中心的 GNN 从相邻节点中聚合信息,这解决了模式项的表示问题,并通 过边的特征表示模式项之间的关系(主键和外键等)。但这 有两个问题:1)问题词和模式项表示没有上下文信息,使得 模型很难推理建立好的模式链接;2)由于元路径的存在,图 的信息传播被固定在预定义关系中而无法全局推理。

为了解决这两个问题,RAT-SQL[6] 首先引入了总计 33 种 元路径来表示问题词和模式项之间的关系;其次,RAT-SQL 中 引 入 了 用 于 图 表 示 学 习 的 关 系 感 知 自 注 意 力 机 制 (relation-aware self-attention)[7] ,将对模式实体的全局推理和 问题词与对预定义的模式关系的结构化推理结合起来;而 LGESQL(Line Graph Enhanced text-to-SQL model)[8] 从节点中 心图构造了一个边中心图,它同时考虑节点之间的连接和有 向边的拓扑结构,使得信息的传播效率更高。LGESQL 中设 计 了 两 个 关 系 图 注 意 力 网 络(Relational Graph ATtention

收稿日期:2023⁃10⁃09;修回日期:2023⁃12⁃24;录用日期:2023⁃12⁃26。

network, RGAT)<sup>[9]</sup>,分别对节点中心图和边中心图的结构建模,这种方法同时兼顾了全局和局部边的特征。

除了基于图的编码器,模式链接也是Text-to-SQL任务的重要子任务,它包含问题词和模式项之间的链接<sup>[10]</sup>。之前的部分工作<sup>[11-13]</sup>并没有重视模式链接本身的重要作用,然而RAT-SQL的消融实验结果表明,去掉模式链接部分比移除其他模块造成的性能下降更多。

然而,如RAT-SQL一般基于完全匹配的模式链接方法可能会导致一些问题。例如,用同义词或近义词对模式项名进行替换或需要根据语义信息推断模式项,模型难以推断出正确的模式链接。因此,基于字符串匹配的完全匹配的模式链接方法并不可靠。对此,ISESL<sup>[14]</sup>中利用预训练语言模型(Pre-trained Language Model, PLM)构建语义增强的模式链接,而语义关系信息就包含在PLM的连续表示中。

### 表 1 LGESQL SQL语句生成错误比例

Tab. 1 LGESQL SQL sentence generation error ratio

| 错误类型     | 错误占比/% | 错误类型      | 错误占比/% |
|----------|--------|-----------|--------|
| 模式链接     | 44. 7  | condition | 11. 1  |
| JOIN     | 23. 3  | 嵌套        | 11.3   |
| GROUG BY | 9. 6   |           |        |

本文针对LGESQL模型的SQL语句生成结果进行了错误分析,如表1所示,将错误类型分为模式链接、JOIN、GROUP BY、嵌套和 condition 5个主要类型。错误分析结果表明,模式链接虽然会对SQL语句生成产生正向影响,但它本身也是模型预测SQL语句错误的最主要因素,大部分错误SQL语句生成都与模式链接有关。从具体错误样例来看,模式链接的错误原因主要有3个:链接到错误的表或列、链接了多余的表或列和缺失部分表或列。而从错误数量来看,前两个造成的错误数量远远多于第3个。基于完全匹配的模式链接显然很难解决上述问题。与此相对,语义增强的模式链接则可以很好地解决第1个问题,在此基础上,对链接的模式项进行合理的裁剪则可以解决第2个问题。同时,本文在解码器端使用中间表示(Intermediate Representation,IR)作为SQL语句生成的过渡,IR的语法减少了需要链接的模式项数量,从而减少模式链接导致的错误。

因此,为了解决以上问题,在LGESQL的基础上,本文优化了ISESL方法<sup>[14]</sup>。并且本文将模型分为以下几个模块:初始图生成模块、相似度度量图学习模块、图编码器模块、解码器模块和图正则化模块。

### 1 相关工作

近些年,异构图神经网络的研究被越来越多人注意。从异构图的数据探索[15-16]到异构图上的各种算法[17-18]等。异构图包含不同类型的边和节点,而Text-to-SQL数据集自然包含不同类型的节点。因此,异构图本身的数据传递和性能提升也值得关注。HAN(Heterogeneous Attention Network)[19]中将初始图转换为多个齐次图,并在齐次图中应用了层次注意力机制。对于边结构,关系图卷积网络(Relational Graph Convolutional Network,RGCN)和RGAT已经被提出以参数化不同的边的关系。从消息传递的角度来看,RGCN会在消息传递时同时考虑到边的类型(关系)和方向,并为每个关系类型进行转换从而更新节点表示;RGAT改变了邻居集(邻居节点的集合)的定义,从单跳到多跳邻居,再对不同的邻居分别进行自适应的消息聚合和层间的消息传递以此处理聚合

和更新函数。因此,在本文的工作中,模型使用带有多头注意力机制的RGAT作为输入图。

图神经网络是处理复杂数据结构图的网络模型[20]。图 的结构通常会进行标记,用阈值法进行预处理,或用 k-最近 邻算法[21]进行预计算。这两种方法都首先使用核函数计算 节点特征的成对距离;然而,这些方法生成的图结构可能包 含缺失或有噪声的边,从而对下游学习任务造成影响。为了 缓解这一问题,一些无监督的修复图结构的方法被提了出 来。第一种是基于度量的方法,例如余弦相似度:第二种是 基于注意力网络的自注意力机制优化边的权值。但这些图 结构学习的方法通常只会执行一次,而这不能很好地优化图 结构。为了更好地联合优化图的结构和下游任务, Chen 等[22]提出了一个迭代的深度图学习模型,让图学习模型和 下游任务一起优化,最后通过LDS (Learning Discrete Structures)方法[23]对图结构进行离散抽样完成学习,这样可 以更灵活地获得最终的图结构属性。但是,这些模型是在同 构图上进行优化的,所以并不能直接用于基于异构图的本文 模型中。因此,本文根据 Zhao 等[24]提出的异构图图结构学 习方法进行相似度度量图学习,并结合图神经网络[20]将图 结构学习网络引入一个改进版本的关系感知图注意力网络 中,以优化Text-to-SQL模型。

## 2 问题定义和模型架构

#### 2.1 模型架构

由图 1 可以看到本文整个模型的细节。模型首先从PLM 中通过无监督的探针探测技术获得初始模式链接图;其次,在训练过程中,通过图结构学习方法得到的相似度度量链接图不断对初始模式链接图进行迭代优化;再次,联合初始图和相似度度量链接图得到最后的语义增强的模式链接图,使用 RGAT 图编码器对联合模式链接图进行编码;最后由使用 IR 的基于语法的 Text-to-SQL 解码器生成 SQL 语句。

![](_page_1_Picture_16.jpeg)

Fig. 1 Framework of SELSQL model

### 2.2 问题定义

Text-to-SQL 的问题定义表述如下: 给定一个自然语言问题  $Q = (q_1, q_2, \cdots, q_{(Q)})$  和数据库模式 S, S 包含多个表  $T = (t_1, t_2, \cdots, t_{(T)})$  和多列  $C = (c_1, c_2, \cdots, c_{(C)})$ , 对应的表和列都由单词短语构成, 每个列都有一个字段来限制它的单元值的存储类型(例如 TEXT 和 NUMBER)。整个任务的目标是根据相应信息生成对应的 SQL查询 Y。

本文使用异构图数据结构,因此定义问题-模式项异构图为 G=(V,E),其中节点集  $V=Q\cup T\cup C$ ,图的节点数为 |V|=|Q|+|T|+|C|。本文使用  $S=T\cup C$ 表示所有的模式项节点。边集  $E=E_Q\cup E_S\cup E_{Q\leftrightarrow S}$ 包含3种边: $E_Q,E_S$ 和  $E_{Q\leftrightarrow S}$ 。 定<sub>Q</sub>表示问题词内部的边,由问题序列的节点关系定义; $E_S$ 表示模式项内部的边,由数据集表格内部的主外键以及表列所

属关系构成; $E_{0\leftrightarrow s}$ 表示问题词节点与模式项节点之间的边, 由模型的模式链接组件生成。其中,|S| = |C| + |T| 是模式项 节点的数量。由于图是由3种类型的节点以及不同类型的 边构成的异构图,因此E中的值表示不同的边类型(例如1 表示模式链接关系,2表示主键关系)。

### 3 模型设计

#### 3.1 初始图生成

### 3.1.1 初始图构建

初始图生成部分的任务是使用数据集获得一个语义增 强的初始模式链接图。通过问题词和模式项的语义信息相 关性构建模式链接,再通过预训练模型保有语义信息,这种 方法可以减少问题词和模式项之间难以匹配的情况。受到 Wu等[25]的启发,本文使用无监督的无参数探针技术获取初 始图。大体的思路是:每次屏蔽(mask)一个问题词,观察模 式项的 PLM (如 BERT (Bidirectional Encoder Representations from Transformers)[26])嵌入是如何受到影响的。通过这种方 法,模型在问题词和模式项之间构建边。与精确匹配的方法 不同,这种方法不利用问题词和模式项的表面形式相关性进 行匹配,因此问题词被替换为同义词也不会影响模型的最终 输出。总体来说,模型的目标是为异构图 $E_{0\leftrightarrow s}$ 生成语义增 强的模式链接边rse。首先将问题令牌和模式项的向量表示

$$X = (q_1, q_2, \dots, q_{|Q|}, s_1, s_2, \dots, s_{(|T|+|C|)})$$
 (1)

PLM 将输入的文本序列 X 映射为隐藏表示 X。问题和 模式嵌入可以分别表示为 $Q=(q_1,q_2,\cdots,q_{|0|})$ 和S= $(s_1, s_2, \dots, s_{(|T|+|C|)})_{\circ}$ 

获得表示X后,即可利用一个探测函数 $f(q_i,s_i)$ 捕获任 意一对问题标记q,和模式项s之间的相关性,灵感来源于一 个观察的现象: 当句子中最相关的词被删除后, 语义的变化 是最大的。因此受之前的工作启发,本文使用了一个两阶段 的屏蔽语言模型(Masked Language Model, MLM)过程,首先, 模型用特殊标记[MASK]替换一个问题标记 $q_i$ ,并再次将被 更改的序列  $X \setminus \{q_i\}$  输入 PLM 中; 然后,将模式项 $s_i$ 的表示更改 为 $s_i \setminus q_i$ ,如此,被更改的模式项就会受到被[MASK]的 $q_i$ 的影 响。随后,模型通过一个距离测量函数 $f(q_i, s_i)$ 定义标记 $s_i$ 和  $s_i \setminus q_i$ 之间的变化:

$$f(\mathbf{q}_i, \mathbf{s}_i) = d(\mathbf{s}_i \backslash \mathbf{q}_i, \mathbf{s}_i) \tag{2}$$

其中,d(,)是度量两个向量之差的距离度量。

### 3.1.2 庞加莱距离

向量之间的距离度量通常情况下可以使用欧氏距离实 现,但欧氏距离在复杂数据(如图形数据)建模中效果一般, 因此,本文使用在双曲空间下的庞加莱探针进行PLM中间 题词和模式项的距离度量[27]。双曲空间的树相似性特性已 被广泛研究,并且已被用于异构图神经网络。与欧几里得空 间相比,在双曲空间下的距离度量失真要小得多。此外,最 近的一些成果证明了双曲空间能自然地反映图的一些性质。

为了更好地测量 $s_i$ 和 $s_i \setminus q_i$ 之间的差异,本文引入了庞加 莱球[28]的概念。对于双曲空间系中的点x,定义庞加莱球为  $(D^{n}, g_{x}^{D})$ ,其中 $D^{n} = \{x \in \mathbb{R}^{n}: ||x|| < 1\}$ 是一个黎曼流形,黎曼度 规和欧氏度规的关系如下:

$$g_x^D = \lambda_x^2 g^E \tag{3}$$

$$\lambda_{x} = 2/(1 - \|\mathbf{x}\|^{2}) \tag{4}$$

其中: $g^{E} = I_{n}$ 是欧氏度规张量; $\lambda_{x}$ 是一个系数因子。

为了比较由 g, 在双曲空间中学习到的特征向量, 首先使 用指数映射函数 $g_{\bullet}(\cdot)$ 将嵌入投影到双曲空间中。与欧氏空 间中的向量运算不同,在双曲空间中,本文使用旋转向量空 间(Gyrovector spaces)框架进行代数运算。假设 m ∈ Z<sub>n</sub>是切 线空间中相对于双曲空间中的点x的输入向量。m将被实例 化为 $\tilde{m}_s$ 和 $\tilde{m}_{s \setminus q}$ 。映射函数 $g_x(\cdot)$ :  $\mathbf{Z}_n^x \to D^n$ 可以计算为:

$$g_{x}(\mathbf{m}) = \mathbf{x} \oplus_{c} \left( \tanh \left( \frac{\lambda_{x} \| \mathbf{m} \|}{2} \right) \frac{\mathbf{m}}{\| \mathbf{m} \|} \right)$$
 (5)

其中,操作 $\oplus$ 。是 Mobius 的加法。对于任意  $u, v \in D^n$ , 它们的 计算方法为:

$$\boldsymbol{u} \oplus_{c} \boldsymbol{v} = \frac{\left(1 + 2c\langle \boldsymbol{u}, \boldsymbol{v} \rangle + c \|\boldsymbol{v}\|^{2}\right)\boldsymbol{u} + \left(1 - c \|\boldsymbol{u}\|^{2}\right)\boldsymbol{v}}{1 + 2c\langle \boldsymbol{u}, \boldsymbol{v} \rangle + c^{2}\|\boldsymbol{u}\|^{2}\|\boldsymbol{v}\|^{2}}$$
(6)

模型使用标准的庞加莱球形,因此,c=1。当c=0时, 可视为欧氏空间下的向量相加。

通过特征映射函数 $g_{x}(\cdot)$ 获得双曲空间中的特征表示 后,首先计算m在x = 0的切空间的双曲表示 $\tilde{m}$ ,由此可以通 过计算双曲空间中 $\tilde{m}$ 。和 $\tilde{m}$ 。」。之间的庞加莱距离衡量模式项 s和问题词q之间的相关性如下:

$$\tilde{\boldsymbol{m}} = g_0(\boldsymbol{m}) = \frac{1}{\sqrt{c}} \tanh\left(\sqrt{c} \|\boldsymbol{m}\|\right) \frac{\boldsymbol{m}}{\|\boldsymbol{m}\|}$$
 (7)

$$d_{P}(\boldsymbol{q}_{i}, \boldsymbol{s}_{j}) = \frac{2}{\sqrt{c}} \tanh^{-1} \left( \sqrt{c} \left\| -\tilde{\boldsymbol{m}}_{\boldsymbol{s}_{j} \setminus \boldsymbol{q}_{i}} \bigoplus_{c} \tilde{\boldsymbol{m}}_{\boldsymbol{s}_{j}} \right\| \right)$$
(8)

通过衡量每对问题词和模式项标记,得到了初始的模式 链接矩阵 $M_{init} \in \mathbb{R}^{|Q| \times (|T| + |C|)}$ 。为了避免引入权重很低的噪声 边以及降低模型整体的计算量,引入一个预定义的阈值τ稀 疏初始的模式链接矩阵:

M<sub>init</sub> = 
$$\begin{cases} 0, & f(q_i, s_j) < \tau \\ f(q_i, s_j), & f(q_i, s_j) \geqslant \tau \end{cases}$$
相似 庶 庶 景 恩 学 习

#### 3.2 相似度度量图学习

由于初始的模式链接图直接从数据集中生成,并目使用 语义信息的相关性构建模式链接,可能带有噪声从而对后续 的编码结果产生影响,这会导致问题词和模式项之间产生多 余的模式链接,根据表1的错误分析的结果可知,它并不能 准确地反映真实的数据集中的模式链接情况。因此本文利 用相似度度量图学习模块在训练过程中通过图结构学习方 法学习图结构信息并迭代细化初始模式链接图。

相似度度量图学习模块的目标是在问题标记和模式项 之间学习一个模式链接关系矩阵 $M(t) \in \mathbf{R}^{|Q| \times (|T| + |C|)}$ ,其中t是 训练中的 epoch 数。首先对于特征节点  $x_i$ ,使用一个特征映 射函数将它投影到一个公共的映射层中:

$$\mathbf{x}_i' = \sigma(\mathbf{x}_i \cdot \mathbf{W}_x + \mathbf{b}) \tag{10}$$

其中, $\sigma(\cdot)$ 表示非线性激活函数,本文使用线性整流单元 (Rectified Linear Unit, ReLU)函数,原因是为了保留结果的 正部分,负数部分则直接置0。 W,和b分别代表映射矩阵和 偏置向量。随后,对问题词q和模式项s进行度量学习,最终 得到相似度度量矩阵:

$$\mathbf{M}_{ij}(t) = \begin{cases} \Gamma_{ij}(\mathbf{q}_i, \mathbf{s}_j), & \Gamma_{ij}(\mathbf{q}_i, \mathbf{s}_j) \in \text{Top2}(\Gamma_{ij}(\mathbf{q}_i, \mathbf{s}_j)) \\ 0, & \Gamma_{ij}(\mathbf{q}_i, \mathbf{s}_j) \notin \text{Top2}(\Gamma_{ij}(\mathbf{q}_i, \mathbf{s}_j)) \end{cases}$$
(11)

由于问题词和模式项之间的链接数目一定是有限的,因 此本文使用一个TopK(k=2)方法稀疏图结构,减少模式链接 数量并简化后续的计算。 $\Gamma_{ii}(\cdot)$ 是一个K头加权余弦相似度 函数,具体定义为:

$$\Gamma_{ij}(\boldsymbol{q}_i, \boldsymbol{s}_j) = \frac{1}{K} \sum_{k=1}^{K} \cos(\boldsymbol{W}_i \odot \boldsymbol{q}_i, \boldsymbol{W}_j \odot \boldsymbol{s}_j)$$
 (12)

其中: $\bigcirc$ 为 Hadamard 乘积;  $\mathbf{W}_{i}$ 和  $\mathbf{W}_{i}$ 是可学习的权值矩阵。

### 3.3 图编码器

用初始图生成和相似度度量图学习模块分别获得模式链接矩阵 $M_{ini}$ 和相似度度量矩阵M(t),图编码器使用训练好的初始图和相似度度量图学习更好的问题和模式项节点嵌入,从而提高Text-to-SQL的解码器效果。

联合模式链接图的构造过程表示为:

$$\tilde{\mathbf{M}}_{\text{init}} = \lambda \mathbf{M}_{\text{init}} + (1 - \lambda) \mathbf{M}(t) \tag{13}$$

其中, $\lambda$ 是一个用于调整这两个图的权重的超参数。输入的联合模式链接图是一个包含不同边关系的异构图。因此 $\tilde{M}_{init}$ 是一个具有各类预定义关系 $r^{sc}$ 的加权矩阵。则图 $\tilde{E}_{0\to s}$ 可以表示为:

$$\begin{bmatrix} \boldsymbol{E}_{Q \leftrightarrow S} \end{bmatrix} (t) = \begin{cases} \boldsymbol{\gamma}^{\text{sc}}, & \tilde{\boldsymbol{M}}_{\text{init}} > 0 \\ \boldsymbol{\gamma}^{\text{none}}, & \tilde{\boldsymbol{M}}_{\text{init}} = 0 \end{cases}$$
 (14)

在单个 epoch t 中,将加权矩阵  $\tilde{M}_{init}(t)$  展开得到完整的图,具体的图表示为:

$$N(t) = \begin{bmatrix} 1^{|Q| \times |Q|} & \tilde{M}_{\text{init}}(t) \\ \tilde{M}_{\text{init}}(t)^{\text{T}} & 1^{|S| \times |S|} \end{bmatrix}$$
 (15)

由于模型只计算问题词与模式项节点之间的边权重,因此问题词和模式项内部的边权重全部置1。

为了处理输入的异构图 E,本文延续 LGESQL 的思路,使用 RGAT图编码器进行编码工作。RGAT基于图注意力网络表示自注意力层中的相对位置信息,并使用可学习的关系嵌入表示边类型之间的影响。给定第l层的节点关系嵌入矩阵  $X^l \in \mathbf{R}^{([0]+[C]+[T])\times d}$ ,其中 d 为 GNN 嵌入大小。与 LGESQL 相同,模型使用多头注意力机制计算注意力权重,在迭代过程中,图中的任意一个节点都会聚合邻域信息来更新表示,并且为了进一步优化图结构,模型在每个 epoch 的学习中引入了加权矩阵 N(t)。

给定当前的节点表示  $X^t$ 、图 E(t) 和加权邻接矩阵 N(t),注意力权重  $a_t^h$ 可以通过以下方式计算:

$$\tilde{\boldsymbol{a}}_{ji} = \left(\boldsymbol{x}_{j}\boldsymbol{W}_{k} + \boldsymbol{N}_{ji}(t) \left[\boldsymbol{\omega}\left(\boldsymbol{E}_{ji}\right)\right]\right) \left(\boldsymbol{x}_{i}\boldsymbol{W}_{q}\right) \tag{16}$$

$$a_{ji}^{\rm h} = \operatorname{softmax}_{j} \left( \tilde{a}_{ji}^{\rm h} / \sqrt{d/H} \right)$$
 (17)

其中:矩阵  $\mathbf{W}_q^h$ ,  $\mathbf{W}_k^h$ ,  $\mathbf{W}_v^h \in \mathbf{R}^{d \times dH}$  是可训练的变换矩阵, H 是头数。函数 $\omega(\cdot)$ 构造了一个可学习的矩阵, 它的作用是转换关系类型  $\mathbf{E}_{\mu}(t)$  为 d 维的向量。值得注意的是, 计算注意力值时, 关系特性添加在"查询"侧而非"键"侧。

随后计算下一层 $X_i^{l+1}$ 的输出表示:

$$\tilde{\boldsymbol{x}}_{i}^{l} = \sum a_{ji} \left( \boldsymbol{x}_{j} \boldsymbol{W}_{v} + \boldsymbol{N}_{ji}(t) \left[ \boldsymbol{\omega} \left( \boldsymbol{E}_{ji} \right) \right] \right)$$
 (18)

$$\boldsymbol{X}_{i}^{l+1} = \text{FFN}\left(\text{LayerNorm}\left(\boldsymbol{X}_{i}^{l} + \tilde{\boldsymbol{X}}_{i}^{l}\boldsymbol{W}_{o}\right)\right) \tag{19}$$

其中:矩阵  $\mathbf{W}_{\circ} \in \mathbf{R}^{d \times d}$  为输出转换矩阵; FFN( $\cdot$ )表示一个前 馈神经网络层; LayerNorm( $\cdot$ )则表示层归一化操作。

从编码器架构中可以看出,加权邻接矩阵 N(t) 在训练过程中迭代优化,因此,模式链接图也会在训练中不断更新。图 编 码 器 的 最 终 输 出  $X^t$  可 分 别 表 示 为 问 题 表 示  $\left(q_1^t,q_2^t,\cdots,q_M^t\right)$  和模式表示  $\left(s_1^t,s_2^t,\cdots,s_{lT+G}^t\right)$ ,用于 Text-to-SQL 解码器的解码过程。

## 3.4 解码器

由图编码器模块生成给定问题表示 $\left(q_1^{\scriptscriptstyle \text{I}},q_2^{\scriptscriptstyle \text{I}},\cdots,q_{\scriptscriptstyle |\mathcal{O}|}^{\scriptscriptstyle \text{I}}\right)$ 和模

式表示 $(s_1^{\mathfrak{l}}, s_2^{\mathfrak{l}}, \cdots, s_{|T+C|}^{\mathfrak{l}})$ , Text-to-SQL解码器模块旨在生成相应的SQL语句。

本文采用的Text-to-SQL解码器是基于语法的神经语义解码器<sup>[29]</sup>,给定问题和模式项表示,解码器会按照预定的规则以深度优先搜索的顺序生成目标查询y的抽象语法树(Abstract Syntax Tree, AST)。在此基础上,本文使用NatSQL(Natural SQL)<sup>[30]</sup>作为IR,最终生成SQL查询。NatSQL经过对一系列SQL语法规则的简化,去除了嵌套以及部分SQL关键字和操作符,相较于原始的SQL查询更接近自然语言问题的语法。除此之外,经过语法规则的简化,NatSQL还减少了所需要链接的模式项数量,这也使得SQL语句生成中模式链接本身可能导致的错误减少。

本文使用一个有序神经元LSTM(ON-LSTM)作为自回归解码器,解码操作主要为以下两类:1)基于已经生成的AST生成当前步的非终端节点,即APPLYRULE action;2)从模式表示 $(s_1^{\epsilon}, s_2^{\epsilon}, \cdots, s_{T+ct}^{\epsilon})$ 中选择一个表或列项作为终端节点,即SELECTTABLE或SELECTCOLUMN action。

#### 3.5 图正则化

根据 ISESL 的工作,模型添加了一个图正则化模块来更好地保证相似度度量图学习的质量。具体操作是使用一个二元交叉熵损失  $L_{\rm P}$ 使问题维数中的 M(t) 的和近似于  $S_{\rm SQL}$  。 $S_{\rm SQL} = S_{\rm COL} \cup S_{\rm TBL}$  表示表和列的模式项集合。这样,就可以直接使用  $S_{\rm SQL}$  监督图的正则化损失:

$$\mathcal{L}_{P} = -\sum_{i \in S_{\text{out}}}^{S_{\text{out}}} \log \sum_{i} \mathbf{M}_{ij} (t)$$
 (20)

为了进一步限制无关的模式项对SQL语句生成的影响, 本文应用一个图剪枝的辅助任务对与问题无关的模式项进 行进一步的裁剪。

整个任务的具体做法是:使用多头注意力从问题节点嵌入 $q_i$ 中计算出模式项节点 $s_j$ 的上下文向量 $\tilde{s}_j$ ,随后使用一个双仿射二值分类器确定模式项节点嵌入 $s_j$ 和相应的上下文向量 $\tilde{s}_i$ 的相关性。

如果 $s_j$ 与目标的SQL查询中的模式项一致,则将该模式项的真实标签值设为1。整个训练任务如下:

$$\mathcal{L}_{gp} = -\sum_{s_j} \left[ y_{s_j}^g \log P^{gp} \left( y_{s_j} | \mathbf{s}_j, \mathbf{q}_i \right) + \left( 1 - y_{s_j}^g \right) \log \left( 1 - P^{gp} \left( y_{s_j} | \mathbf{s}_j, \mathbf{q}_i \right) \right) \right]$$
(21)

4 实验与结果分析

#### 4.1 实验设置

### 4.1.1 数据集

Spider<sup>[31]</sup>是一个大规模的跨域Text-to-SQL基准测试集。它包含了来自146个数据库的8659个训练样本和来自20个数据库的1034个评估样本。本文采用不同模型评估了Spider-Dey测试集各组件的精确匹配精度。

### 4.1.2 基线

将本文模型与几个具有代表性的基线进行比较:

- 1)LGESQL<sup>[8]</sup>:基于RGAT的端到端模型,具有原始RGAT和线形图,是较先进的基于图编码器的Text-to-SOL模型。
- 2) RAT-SQL<sup>[6]</sup>: 由关系感知 Transformer 增强的端到端模型。
- 3) SmBoP (Semi-autoregressive Bottom-up semantic Parsing)<sup>[32]</sup>:引入了一个半自回归的自下而上的解码器生成

SQL语句。

4)ISESL[14] :将图结构学习引入 Text-to-SQL领域的框架。 4. 1. 3 超参数

Batch Size 大小设置为 20。初始图生成的模式链接的阈 值 *τ* 设置为 0. 7。在编码器部分,RGAT 的隐藏层大小 *d* 设置 为 512。*K*头加权的余弦相似度函数中 *K*=2。RGAT层数 *L*为 8。使用 RGAT 多头注意力时,RGAT 的头部数为 8,LSTM 的 特征 dropout-rate 设置为 0. 2,*λ* 设置为 0. 2。在解码器部分, 按照之前的工作,将隐藏状态、动作嵌入和节点类型嵌入大 小 的 维 数 分 别 设 置 为 512、128 和 128。 解 码 器 LSTM 的 dropout-rate为 0. 2。对于 AdamW 优化器[33] 的设置为:PLM 的 学 习 率 为 10-4 。 最 后 ,本 文 使 用 了 一 个 线 性 的 warmup scheduler,warmup rate为 0. 1,模型训练的 epoch数为 200。

# 4. 2 对比实验结果

各模型实验设置与实验结果与原文一致,本文模型实验 设置如 4. 1 节所示。从表 2 可以看出,本文模型可以在 PLM 上得到最优的精确匹配结果,准确率达到了 78. 3%,比最优 的基线模型 ISESL+ELECTRA-large 提升了 2. 5 个百分点。本 文使用的预训练模型为 ELECTRA-large。与之前的一些模型 对比可以看到,SELSQL模型的性能得到了不小的提升。

表2 Spider数据集上不同模型的匹配准确率 单位:% Tab. 2 Matching accuracies of different models on

|                    | Spider dataset       | unit:% |
|--------------------|----------------------|--------|
| 预训练模型              | 模型                   | 准确率    |
|                    | RAT-SQL              | 69. 7  |
|                    | SMOP                 | —      |
| BERT-large         | LGESQL               | 74. 1  |
|                    | ISESL                | 74. 7  |
|                    | SELSQL               | 77. 1  |
|                    | RAT-SQL+Grappa       | 73. 4  |
|                    | SMOP+Grappa          | 74. 1  |
| Model Adaptive PLM | LGESQL+ELECTRA-large | 75. 1  |
|                    | ISESL+ELECTRA-large  | 75. 8  |
|                    | SELSQL+ELECTRA-large | 78. 3  |

从使用的预训练模型可以看出,不同的预训练模型也对 模型最终的 SQL 语句生成结果有不小的影响。一个更好更 复杂的预训练模型会生成语义信息更丰富的词嵌入向量,从 而为模型的训练带来积极的影响。

# 4. 3 消融实验结果

为详细研究各模块对本文模型整体性能的影响,进行了 消融实验。从表 3 可以看出,所有模块都提升了模型的性 能。从 PLM 中运用探测技术得到的初始图是其中最重要的 一环,移除了初始图生成模块使得模型性能下降了 1. 8 个百 分点;同时,迭代地进行相似度度量图学习也起到了不小的 作用,使得模型性能提升了 1. 6 个百分点;而当语义模式链 接(语义增强的模式链接)边被删除时,模型的准确率下降了 2. 7个百分点,因为在较为复杂的 SQL语句生成情况下,语义 模式链接起到了至关重要的作用;最后当初始图生成时的距 离度量不是庞加莱距离而是欧氏距离时,模型的性能下降了 0. 8 个百分点,可见使用双曲空间下的庞加莱距离计算问题 词与模式项之间的语义模式链接比欧氏距离更加准确,生成 的初始语义模式链接图质量更高。同理,使用 NatSQL 作为 中间表示也对模型的准确率产生了正面的影响。

### 表3 各模块的消融测试结果

Tab. 3 Ablation test results of various modules

| 模型        | 准确率/% | 下降百分点 |
|-----------|-------|-------|
| SELSQL    | 78. 3 | —     |
| 移除初始图生成   | 76. 5 | 1. 8  |
| 移除相似度度量图  | 76. 7 | 1. 6  |
| 移除语义模式链接  | 75. 5 | 2. 7  |
| 移除庞加莱距离度量 | 77. 5 | 0. 8  |
| 移除NatSQL  | 77. 5 | 0. 8  |

注:下降百分点代表移除不同模块后模型的准确率相较于SELSQL 下降的百分点。

# 4. 4 组件分析

为了更直观地看出本文模型的准确率变化的具体原因, 表 4 分析了在 Spider 基准数据集上 SQL 组件的匹配精度变 化。F1 分数上升最多的是 Group by(no having)、Group by、 SELECT(no AGG)、SELECT 这些包含模式项的组件,最大甚 至提高了 5. 2 个百分点,这表示本文优化的高质量的语义模 式链接图确实起到了极大的作用;此外,只有在 hard 和 extra 等级下才存在的 IUEN 组件的提升幅度也很大,说明本文模 型在复杂环境下的 SQL 语句生成也有很好的鲁棒性。而其 他 组 件 也 可 以 略 微 提 高 性 能 ,例 如 WHERE(NO OP)和 WHERE组件。

表4 Spider数据集上各组件匹配的F1分数

Tab. 4 F1 scores matched by components on Spider dataset

|                     | 不同模型的F1分数/% |        |        | 提升   |
|---------------------|-------------|--------|--------|------|
| 组件                  | RAT-SQL     | LGESQL | SELSQL | 百分点  |
| SELECT              | 82. 2       | 92. 2  | 93. 4  | 1. 2 |
| SELECT(no AGG)      | 84. 5       | 93. 5  | 95. 0  | 1. 5 |
| WHERE               | 82. 5       | 81. 2  | 81. 4  | 0. 2 |
| WHERE(NO OP)        | 86. 1       | 84. 9  | 85. 5  | 0. 6 |
| Group by(no having) | 60. 1       | 84. 6  | 88. 6  | 4. 0 |
| Group by            | 64. 2       | 80. 8  | 86. 0  | 5. 2 |
| Order by            | 81. 4       | 85. 0  | 86. 8  | 1. 8 |
| And/or              | 98. 4       | 98. 2  | 98. 4  | 0. 2 |
| IUEN                | 37. 5       | 62. 7  | 64. 2  | 1. 5 |
| keywords            | 91. 3       | 91. 1  | 91. 4  | 0. 3 |

注:提升百分点指SELSQL的F1相较于LGESQL提升的百分点。

# 4. 5 难度等级分析

Spider 数据集将 SQL 语句生成难度分成 4 个等级,为了 更准确地分析本文模型在各难度 SQL语句生成下的表现,将 本文模型与 RAT-SQL 和 LGESQL 进行比较。从表 5 可以看 到,本文模型在各难度下的准确率最优。easy 等级下的准确 率仅上升 1. 0 个百分点,可见该等级下基于精确匹配方法生 成模式链接的方法也能得到较好结果,语义模式链接对简单 SQL 语句生成帮助有限;medium 和 hard 难度下本文模型的 准确率分别上升了 2. 2 和 5. 4 个百分点,可见高质量的语义 模式链接对于较复杂 SQL 语句生成的巨大作用;同时,extra 难度下准确率上升了 4. 8 个百分点,提升幅度并不如 hard 难 度,可见在更复杂的环境中,语义模式链接不能解决所有 问题。

# 4. 6 案例分析

为了展示本文模型的效果,从 hard 和 extra 难度等级上 选择 4 个案例,前 3 个是 positive 案例,最后 1 个是 negative 案 例。从表 6 可以看出,本文模型的表现优于基线模型。在问 题中没有明确提到模式项时,本文模型依然可以正确生成 SQL 语句。案例 1 中,LGESQL 无法推导出正确表中的模式 项,而本文模型正确识别了模式项 Treatments. dog\_id,这个错 误的原因是 LGESQL 是基于精确匹配下选择的问题词与模 式项来构造模式链接,这是基于字符串匹配的方法,而本文 模型是基于查询问题语义的进一步推导得到的结果;案例 2 中,LGESQL 是由于错误理解了问题的语义导致错误,在问 题 中 包 含 多 个 实 体 词 的 情 况 下 ,问 题 要 查 询 的 主 语 是 dog\_id,而 LGESQL 选择了 owner\_id,而本文模型基于语义的 方法则选出了正确的选项;案例 3 中,问题中并没有出现要 查询的实体词短语,但问题中表达出了查询花费总费用的语 义,结合多个问题可以进一步确定是查询治疗总费用,这导 致了 LGESQL 引入了错误的表格 Charge,而本文模型则根据 语义选择了正确的表格 Treatments;而案例 4 中则是本文模

型根据语义链接了错误的值,可见在复杂 SQL语句生成的情 况下,语义模式链接也并不能保证完全正确。

## 表5 Spider数据集上各难度等级精确匹配准确率

Tab. 5 Exact matching accuracy of each difficulty level on Spider dataset

| 难度等级   | 不同模型的准确率/% |        |        | 提升   |
|--------|------------|--------|--------|------|
|        | RAT-SQL    | LGESQL | SELSQL | 百分点  |
| easy   | 87. 9      | 91. 9  | 92. 9  | 1. 0 |
| medium | 74. 6      | 78. 3  | 80. 5  | 2. 2 |
| hard   | 60. 3      | 64. 9  | 70. 3  | 5. 4 |
| extra  | 48. 7      | 52. 4  | 57. 2  | 4. 8 |
| all    | 71. 2      | 75. 1  | 78. 3  | 3. 2 |

注:提升百分点指SELSQL的准确率相较于LGESQL提升的百分点。

表6 不同模型在Spider数据集上生成的SQL语句对比

Tab. 6 Comparison of SQL statements generated by different models on Spider dataset

| 样本<br>序号 | 难度<br>等级 | 案例                                                                                                                    | LGESQL                                                                                                                                                                                       | SELSQL                                                                                                                                                                                                                                             |
|----------|----------|-----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1        | hard     | Find the average age of<br>the dogs who went<br>through treatments.                                                   | SELECT AVG(Dogs. age)<br>FROM Dogs JOIN Treatments                                                                                                                                           | SELECT AVG(Dogs. age) FROM Dogs WHERE Dogs.<br>dog_id IN ( SELECT Treatments. dog_id FROM<br>Treatments )                                                                                                                                          |
| 2        | hard     | What are the names of<br>the dogs for which the<br>owner has not spend<br>more than 1000 for<br>treatment ?           | SELECT Dogs. name FROM Dogs WHERE Dogs.<br>owner_id NOT IN ( SELECT Treatments. dog_id FROM<br>Treatments GROUP BY Dogs. owner_id HAVING<br>COUNT(Treatments. cost_of_treatment) > "value" ) | SELECT Dogs. name FROM Dogs WHERE Dogs.<br>dog_id NOT IN ( SELECT Treatments. dog_id FROM<br>Treatments GROUP BY Treatments. dog_id HAVING<br>SUM(Treatments. cost_of_treatment) > "value" )                                                       |
| 3        | extra    | Which owner has paid<br>the largest amount of<br>money in total for their<br>dogs? Show the owner<br>id and zip code. | SELECT Owners. owner_id , Owners. zip_code FROM<br>Owners JOIN Dogs JOIN Charges GROUP BY Owners.<br>owner_id ORDER BY SUM(Charges. charge_amount)<br>DESC LIMIT 1                           | SELECT Owners. owner_id , Owners. zip_code FROM<br>Owners JOIN Dogs JOIN Treatments GROUP BY<br>Owners. owner_id ORDER BY SUM(Treatments.<br>cost_of_treatment) DESC LIMIT 1                                                                       |
| 4        | hard     | Find the name,<br>population and expected<br>life length of asian<br>country with the largest<br>area?                | SELECT country. Name , country. Population , country.<br>LifeExpectancy FROM country WHERE country.<br>Continent = "value" ORDER BY country. SurfaceArea<br>DESC LIMIT 1                     | SELECT country. Name , country. Population ,<br>country. LifeExpectancy FROM country WHERE<br>country. SurfaceArea = "value" AND country.<br>SurfaceArea = ( SELECT MAX(country. SurfaceArea)<br>FROM country WHERE country. Continent = "value" ) |

# 5 结语

本文优化 ISESL 的框架,为 Text-to-SQL 任务构建一个更 佳的语义模式链接图。与利用精确匹配构建模式链接的方 法相比,利用 PLM 进行无参数探针的方法鲁棒性更好,能应 对问题中同义词被替换等环境;使用图正则化以及 NatSQL 作为解码的中间表示,减少了模式链接导致的 SQL语句生成 错误。本文优化了探测模式链接的方法,获得了更优的模式 链接探测图结构;同时,优化了相似度度量图学习方法,获得 了更准确的语义模式链接图结构,减少了模式链接数,提高 了方法的准确率。从实验结果可以看出语义模式链接对于 复杂 SQL 语句生成的巨大作用。未来的研究重点依然在增 强语义模式链接上。下一步的研究方向是导入外部知识图 谱与问题词实体进行链接,帮助模型更好地理解问题语义, 从而生成更精确的 SQL语句。

# 参考文献(References)

- [1] BOGIN B, BERANT J, GARDNER M. Representing schema structure with graph neural networks for Text-to-SQL parsing [C]// Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics. Stroudsburg: ACL,2019:4560-4565.
- [2] SCHLICHTKRULL M, KIPF T N, BLOEM P, et al. Modeling relational data with graph convolutional networks [C]// Proceedings of the 15th International Conference on Semantic Web. Berlin:

Springer,2018:593-607.

- [3] BOGIN B, GARDNER M, BERANT J. Global reasoning over database structures for Text-to-SQL parsing [C]// Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing. Stroudsburg: ACL,2019:3659-3664.
- [4] 黄君扬,王振宇,梁家卿,等. 基于自裁剪异构图的NL2SQL模型 [J]. 计算机工程,2022,48(9):71-77.(HUANG J Y, WANG Z Y, LIANG J Q, et al. NL2SQL model based on self-pruning heterogeneous graph [J]. Computer Engineering,2022,48(9): 71-77.)
- [5] 王秋月,程路易,徐波,等. 基于知识增强的NL2SQL方法[J]. 智 能计算机与应用,2022,12(7):1-7.(WANG Q Y, CHENG L Y, XU B, et al. NL2SQL method based on knowledge enhancement [J]. Intelligent Computer and Applications,2022,12(7):1-7.)
- [6] WANG B, SHIN R, LIU X, et al. RAT-SQL: relation-aware schema encoding and linking for Text-to-SQL parsers [C]// Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. Stroudsburg: ACL,2020:7567-7578.
- [7] SHAW P, USZKOREIT J, VASWANI A. Self-attention with relative position representations [C]// Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 2(Short Papers). Stroudsburg: ACL,2018:464-468.

- [8] CAO R, CHEN L, CHEN Z, et al. LGESQL: line graph enhanced Text-to-SQL model with mixed local and non-local relations [C]// Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers). Stroudsburg: ACL,2021:2541-2555.
- [9] WANG K, SHEN W, YANG Y, et al. Relational graph attention network for aspect-based sentiment analysis [C]// Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. Stroudsburg: ACL,2020:3229-3238.
- [10] GAN Y, PURVER M, WOODWARD J R. A review of crossdomain Text-to-SQL models [C]// Proceedings of the 1st Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics and the 10th International Joint Conference on Natural Language Processing: Student Research Workshop. Stroudsburg: ACL,2020:108-115.
- [11] GUO J, ZHAN Z, GAO Y, et al. Towards complex Text-to-SQL in cross-domain database with intermediate representation [C]// Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics. Stroudsburg: ACL,2019:4524-4535.
- [12] LI S, HU X, LIN L, et al. A multi-level supervised contrastive learning framework for low-resource natural language inference [J]. IEEE/ACM Transactions on Audio, Speech, and Language Processing,2023,31:1771-1783.
- [13] XU P, KUMAR D, YANG W, et al. Optimizing deeper Transformers on small datasets [C]// Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers). Stroudsburg: ACL,2021: 2089-2102.
- [14] LIU A, HU X, LIN L, et al. Semantic enhanced Text-to-SQL parsing via iteratively learning schema linking graph [C]// Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. New York: ACM,2022:1021-1030.
- [15] LIM D, HOHNE F, LI X, et al. Large scale learning on nonhomophilous graphs: new benchmarks and strong simple methods [C]// Proceedings of the 35th Conference on Neural Information Processing Systems. Red Hook: Curran Associates Inc. ,2021: 20887-20902.
- [16] LIM D, LI X, HOHNE F, et al. New benchmarks for learning on non-homophilous graphs [EB/OL]. [2023-02-14]. https://arxiv. org/pdf/2104. 01404. pdf.
- [17] BO D, WANG X, SHI C, et al. Beyond low-frequency information in graph convolutional networks [C]// Proceedings of the 2021 AAAI Conference on Artificial Intelligence. Palo Alto: AAAI Press,2021,35(5):3950-3957.
- [18] YANG L, LI M, LIU L, et al. Diverse message passing for attribute with heterophily [C]// Proceedings of the 35th Conference on Neural Information Processing Systems. Red Hook: Curran Associates Inc. ,2021:4751-4763.
- [19] WANG X, JI H, SHI C, et al. Heterogeneous graph attention network [C]// Proceedings of the 2019 World Wide Web Conference. New York: ACM,2019:2022-2032.
- [20] ZHOU J, CUI G, HU S, et al. Graph neural networks: a review of methods and applications [J]. AI Open,2020,1:57-81.
- [21] ANASTASIU D C, KARYPIS G. L2Knng: fast exact *k*-nearest neighbor graph construction with l2-norm pruning [C]// Proceedings of the 24th ACM International on Conference on Information and Knowledge Management. New York: ACM, 2015:791-800.
- [22] CHEN Y, WU L, ZAKI M J. Iterative deep graph learning for

- graph neural networks: better and robust node embeddings [C]// Proceedings of the 34th International Conference on Neural Information Processing Systems. Red Hook: Curran Associates Inc. ,2020:19314-19326.
- [23] FRANCESCHI L, NIEPERT M, PONTIL M, et al. Learning discrete structures for graph neural networks [C]// Proceedings of the 36th International Conference on Machine Learning. New York: PMLR,2019,97:1972-1982.
- [24] ZHAO J, WANG X, SHI C, et al. Heterogeneous graph structure learning for graph neural networks [C]// Proceedings of the 2021 AAAI Conference on Artificial Intelligence. Palo Alto: AAAI Press,2021,35(5):4697-4705.
- [25] WU Z, CHEN Y, KAO B, et al. Perturbed masking: parameterfree probing for analyzing and interpreting BERT [C]// Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. Stroudsburg: ACL,2020:4166-4176.
- [26] DEVLIN J, CHANG M-W, LEE K, et al. BERT: pre-training of deep bidirectional transformers for language understanding [C]// Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1(Long and Short Papers). Stroudsburg: ACL,2019:4171-4186.
- [27] NICKEL M, KIELA D. Poincaré embeddings for learning hierarchical representations [C]// Proceedings of the 31st International Conference on Neural Information Processing Systems. Red Hook: Curran Associates Inc. ,2017:6341-6350.
- [28] CHAMI I, YING R, RE C, et al. Hyperbolic graph convolutional neural networks [C]// Proceedings of the 33rd International Conference on Neural Information Processing Systems. Red Hook: Curran Associates Inc. ,2019:4868-4879.
- [29] YIN P, NEUBIG G. A syntactic neural model for general-purpose code generation [C]// Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Stroudsburg: ACL,2017:440-450.
- [30] GAN Y, CHEN X, XIE J, et al. Natural SQL: making SQL easier to infer from natural language specifications [C]// Proceedings of the 2021 Findings of the Association for Computational Linguistics. Stroudsburg: ACL,2021:2030-2042.
- [31] YU T, ZHANG R, YANG K, et al. Spider: a large-scale humanlabeled dataset for complex and cross-domain semantic parsing and Text-to-SQL task [C]// Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing. Stroudsburg: ACL,2018:3911-3921.
- [32] RUBIN O, BERANT J. SmBoP: semi-autoregressive bottom-up semantic parsing [C]// Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. Stroudsburg: ACL, 2021:311-324.
- [33] LOSHCHILOV I, HUTTER F. Decoupled weight decay regularization [EB/OL]. [2023-10-11]. https://arxiv. org/pdf/ 1711. 05101. pdf.
- **WU Xianglan**, born in 2000, M. S. candidate. His research interests include natural language processing, SQL statement generation.
- **XIAO Yang**, born in 1998, M. S. candidate. His research interests include fake news detection, SQL statement generation.
- **LIU Mengying**, born in 1999, M. S. candidate. Her research interests include intelligent software engineering, fake news detection.
- **LIU Mingming**, born in 1979, Ph. D., lecturer. Her research interests include data mining.