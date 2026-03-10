DOI: 10. 19884/j. 1672-5220. 202207003

# TSCL-SQL: Two-Stage Curriculum Learning Framework for Text-to-SQL

YIN Feng(尹 枫), CHENG Luyi (程路易), WANG Qiuyue(王秋月), WANG Zhijun(王志军), DU Ming (杜 明), XU Bo(徐 波)\*

School of Computer Science and Technology, Donghua University, Shanghai 201620, China

Abstract: Text-to-SQL is the task of translating a natural language query into a structured query language. Existing text-to-SQL approaches focus on improving the model's architecture while ignoring the relationship between queries and table schemas and the differences in difficulty between examples in the dataset. To tackle these challenges, a twostage curriculum learning framework for text-to-SQL (TSCL-SQL) is proposed in this paper. To exploit the relationship between the queries and the table schemas, a schema identification pre-training task is proposed to make the model choose the correct table schema from a set of candidates for a specific query. To leverage the differences in difficulty between examples, curriculum learning is applied to the text-to-SQL task, accompanied by an automatic curriculum learning solution, including a difficulty scorer and a training scheduler. Experiments show that the framework proposed in this paper is effective.

**Key words**: text-to-SQL; curriculum learning; semantic parsing **CLC number**: TP391. 1 **Document code**: A **Article ID**: 1672-5220(2023)04-0421-07

Open Science Identity
(OSID)

![](_page_0_Picture_9.jpeg)

# Introduction

Text-to-SQL is the task of mapping a natural language query to a structured query language, which enables general users to query relational databases with natural languages. Limited by the scale of the dataset, early work can only complete the task on a single database with a few tables  $^{[1]}$ . Recently, the release of the WikiSQL  $^{[2]}$  dataset, which consists of more than 20 000 tables and about 80 000 natural language queries, presents a new challenge. The model is required to be generalized to unseen table schemas  $^{[2]}$  and different kinds of queries.

To tackle this challenge, existing text-to-SQL approaches cast the problem as a slot-filling [3] task. Xu *et al.* [4] utilized a multi-task model to fill the predicted values into a pre-defined grammar template. He *et al.* [5] and Lyu *et al.* [6] further improved the

model architecture and achieved better performance. However, the current text-to-SQL models still suffer from two challenges.

The first challenge is that current approaches do not leverage the differences in difficulty between examples in the dataset. As shown in Fig.  $1\,(a)$ , a simple query is related to fewer columns in the table, and the names of all related columns are mentioned in the query. In the simple example, the Winner and Runner-up columns are directly mentioned in the query. A complex query is shown in Fig.  $1\,(b)$ . It is related to more columns, and some of the columns' names are not mentioned in the query. In this complex example, the query is related to the Goals, Matches, Average and Team columns. However, the Team column is not mentioned in the query. The model must infer the column name from potential cell values. It makes sense that we can use the differences in difficulty to guide the training process.

The second challenge is that current approaches do not utilize the relationship between queries and table schemas. As shown in Fig. 1, a column name might be mentioned directly or indirectly in the query. The model is required to ground these potential mentions to the table schema. However, existing methods only consider the query's corresponding table schema, which makes it difficult for the model to learn query-schema alignment.

To address these shortcomings, a two-stage curriculum learning framework for text-to-SQL is proposed. Specifically, to leverage the differences in difficulty between examples, curriculum learning [7] is applied to the text-to-SQL task and an automatic curriculum learning solution is designed, including a difficulty scorer and a training scheduler. To exploit the relationship between queries and table schemas, a schema identification pre-training task is proposed to make the model choose the correct table schema from a set of candidates for a specific query. Experiments, including comprehensive ablation studies conducted on the WikiSQL dataset would demonstrate the effectiveness of the proposed method.

Received date: 2022-07-22

Foundation item: Fundamental Research Funds for the Central Universities, China (No. 2232023D-19)

<sup>\*</sup> Correspondence should be addressed to XU Bo, email: xubo@dhu.edu.cn

Citation: YIN F, CHENG L Y, WANG Q Y, et al. TSCL-SQL: two-stage curriculum learning framework for text-to-SQL[J]. Journal of Donghua University (English Edition), 2023, 40(4): 421-427.

![](_page_1_Figure_2.jpeg)

Fig. 1 Examples of text-to-SQL task; (a) simple example; (b) complex example

## 1 Framework Overview

In this section, the text-to-SQL problem is formulated and the two-stage curriculum learning framework for the text-to-SQL problem is introduced.

## 1.1 Problem formulation

Given a natural language query Q and a table schema  $S = \langle C, T \rangle$ , the text-to-SQL task aims to output the corresponding SQL query. The table schema consists of the names of the columns  $C = \{c_1, c_2, \cdots, c_n\}$  and their corresponding types  $T = \{t_1, t_2, \cdots, t_n\}$ .

## 1. 2 Overall architecture

As shown in Fig. 2, the TSCL-SQL framework split the training process of the text-to-SQL task into two

stages. Firstly, the query-schema alignment model was built at the pre-training stage. Specifically, a schema identification task was designed to retrieve the table schema for a specific natural language query. Based on the cross-encoder<sup>[8]</sup> with an in-batch negative<sup>[9]</sup> sampling strategy, the model chose the most similar table schema from the candidates for a specific query. Secondly, the curriculum learning was adopted, and the training process of the text-to-SQL task was re-designed with a difficulty scorer and a training scheduler at the curriculum learning stage. The difficulty scorer scored the difficulty of each training sample. The training scheduler organized training samples according to the score, from simple to complex, and split them into buckets to guide the optimization process.

![](_page_1_Figure_11.jpeg)

Fig. 2 TSCL-SQL framework: (a) pre-training stage; (b) curriculum learning stage

# 2 Pre-training Stage

The objective of the pre-training stage is to enhance the encoder for the text-to-SQL task by establishing a strong alignment between the natural language query and the table schema. In order to build the alignment, a novel schema identification task is proposed to retrieve the relevant table schema for a given query. To facilitate this task, a dataset specifically designed for schema identification is constructed based on the WikiSQL dataset. The schema identification task is completed using

a cross-encoder approach with an in-batch negative sampling strategy, effectively leveraging the power of the model to accurately identify and match query-table schema pairs.

#### 2.1 Dataset construction

As shown in Table 1, the dataset mainly consists of the query and the table schema's meta information. Since Wikipedia is the data source of the WikiSQL dataset, the corresponding table ID, article title, and section title from Wikipedia are concatenated as descriptions for each table schema. Figure 3 shows an example of the data source.

Table 1 Information of schema identification dataset

| Key           | Value                                                                |  |  |  |
|---------------|----------------------------------------------------------------------|--|--|--|
| Query         | If the name is Timo Higgins, what is the total date of birth amount? |  |  |  |
| Table ID      | 1-22344463-2                                                         |  |  |  |
| Article title | Scotland men's national lacrosse team                                |  |  |  |
| Section title | Roster                                                               |  |  |  |
| Table schema  | [ Name, Position, Height, Weight, Date of birth, Home team]          |  |  |  |

![](_page_2_Figure_7.jpeg)

Fig. 3 Data source of descriptions for a table schema

## 2. 2 Query-schema alignment model

The query-schema alignment model aims to build a better encoder representation for the text-to-SQL task. A retrieval-based schema identification task of selecting the most similar table schema from a set of candidates for the given query is proposed. Figure 4 shows the architecture of the query-schema alignment model. It took the query and the description of the table schema as input and output a score representing the semantic consistency between the query and the table schema. The one with the highest score was chosen as the query's corresponding table schema.

Specifically,  $K = \{ (Q_i, D_i) \}_{i=1}^{\kappa}$  denotes the training set, where  $D_i = Concat(P_i, E_i, c_{i_1}, c_{i_2}, \dots, c_{i_n})$  is the description of the table schema  $S_i$ , corresponding to the

natural language query  $Q_i$ ;  $P_i$  and  $E_i$  are the page title and the section title from the Wikipedia entry of the table schema  $S_i$ , respectively;  $Concat(\cdot)$  is a function that concatenates multiple inputs as a single string. The calculation of the similarity score can be formalized as

$$sim(Q_i, D_i) = Linear(red(Encoder ([CLS]Q_i[SEP]D_i[SEP]))), (1)$$

where  $Encoder(\cdot)$  represents the encoder of a pre-trained language model based on transformers [10];  $red(\cdot)$  is a function that takes the representation of the first token from the last layer of the encoder;  $Linear(\cdot)$  is a fully connected layer; [CLS] and [SEP] are special tokens.

![](_page_2_Figure_15.jpeg)

Fig. 4 Architecture of query-schema alignment model

Due to the large number of table schemas in the dataset, it is impractical to use the samples over the whole dataset as negative examples for a single training sample. Therefore, the in-batch negative sampling strategy is used. For each query in the same batch, all the table schema's descriptions of other queries are treated as negative samples. The encoder is trained to maximize the score of the gold query-description pair considering other descriptions sampled from the same batch. Particularly, for each pair ( $Q_i$ ,  $D_i$ ) in a batch of B pairs, the loss  $\mathcal{L}(Q_i, D_i)$  is computed as

$$\mathcal{L}(Q_{i}, D_{i}) = -\sin(Q_{i}, D_{i}) + \log \sum_{j=1}^{B} e^{\sin(Q_{i}, D_{j})}. \quad (2)$$

# 3 Curriculum Learning Stage

The curriculum learning stage aims to use a curriculum learning framework to train a text-to-SQL model. A curriculum learning framework for the text-to-

SQL task is introduced. Then, the implementation of two core components of the framework is described in detail.

#### 3.1 Curriculum learning framework

The curriculum learning framework consists of a difficulty scorer and a training scheduler. The difficulty of each training sample is measured by an automatic difficulty scorer to avoid the uncertainty of hand-crafted rules and consider more about the feedback from the model. The overall process is as follows.

Firstly, the difficulty scorer scores the samples and sorts them from easy to complex. Secondly, the training scheduler initializes an empty subset of the training set as a training stage starts. Sorted samples are split into buckets. For each training stage, a new bucket is added to the subset according to the difficulty. If the training on the subset is converged, the scheduler moves to the next stage until all the buckets are trained. Finally, the full training set is used for training for another few epochs.

#### 3. 2 Difficulty scorer

The difficulty scorer aims to score every training sample based on its difficulty. Due to the lack of existing information about which training samples are more difficult, instead of hand-craft rules, the model's training loss is used as a measurement of the difficulties. A higher loss indicates that the sample is more complex and difficult.

As shown in Fig. 5, existing text-to-SQL approaches cast the problem as a slot-filling task which consists of sixsub-tasks. Therefore, the loss function  $\mathcal{L}_{\text{all}}$  is

$$\mathcal{L}_{all} = \mathcal{L}_{s\text{-agg}} + \mathcal{L}_{s\text{-col}} + \mathcal{L}_{w\text{-num}} + \mathcal{L}_{w\text{-col}} + \mathcal{L}_{w\text{-col}} + \mathcal{L}_{w\text{-vol}},$$
 (3)

where  $\mathcal{L}_{s-agg}$ ,  $\mathcal{L}_{s-col}$ ,  $\mathcal{L}_{w-num}$ ,  $\mathcal{L}_{w-col}$ ,  $\mathcal{L}_{w-op}$  and  $\mathcal{L}_{w-val}$  are the loss functions of select-aggregation (S-AGG) sub-task, the select-column(S-COL) sub-task, the where-number (W-NUM) sub-task, the where-column(W-COL) sub-task, the where-operator (W-OP) sub-task and the where-value (W-VAL) sub-task, respectively.

| SELECT   |                           |
|----------|---------------------------|
| I        | \$AGG(\$COLUMN)           |
| FROM     |                           |
| ! WHERE  | TABLE                     |
| 1        | \$COLUMN \$OP \$VALUE     |
| 1        | AND \$COLUMN \$OP \$VALUE |
| <u>i</u> |                           |

Fig. 5 Template used for slot-filling task

## 3.3 Training scheduler

The training scheduler aims to arrange the scored training samples for curriculum learning. As shown in Fig. 6, the scheduler first sorts the training samples from easy to difficult and splits them into N buckets. Then it starts training with the easiest one. If the training process reaches convergence or a pre-defined number of epochs, a more difficult bucket will be merged. The scheduler will shuffle the data in the bucket and start training. After all the bucket is merged, it will train for several extra epochs on the complete training set.

```
Input: D is the training set, B is the number of bucket, M is the encoder initialized by the
pre-training stage, N is the number of epochs for each training stage, E, is the number of epochs
for training the difficulty scorer, and E_2 is the number of extra training epochs
Output: Optimized model M
1: Train model M for E_1 epochs with training set D to learn a difficult scorer C
2: Score all the samples of training set D with difficulty scorer C, and sort them from easy
    to hard to get the training set D'
3: Split D' into B buckets according to the difficulty score of the samples
   D' = \{D_1, D_2, \dots, D_B\}
4: Initialize subset D_{\text{train}} = \phi
5: For bucket = 1, 2, \cdots, B do
6: D_{\text{train}} = D_{\text{train}} \cup D_{\text{bucket}}
7: While epoch = 1, 2, \dots, N do
8: train(M, D_{train})
9: End while
10: End for
11: Train on the training set D for E_2 epochs
```

Fig. 6 Training scheduler

# 4 Experiments

## 4. 1 Dataset and metrics

The proposed framework is evaluated on the WikiSQL dataset. It consists of tables from Wikipedia, natural language queries and their corresponding SQL statements. The basic characteristic of the WikiSQL dataset is shown in Table 2.

 Table 2
 Basic characteristics of WikiSQL dataset

| Dataset split | Number of tables | Number of samples |
|---------------|------------------|-------------------|
| Train         | 18 585           | 56 355            |
| Development   | 2 761            | 8 421             |
| Test          | 5 230            | 15 878            |

Specifically, the natural language queries and their corresponding SQL statements are stored with JavaScript object notation. The tables are managed

with SQLite database. Figure 7 shows an example of the training set.

```
{
    "table_id":"1-1000181-1",
    "question":"Tell me what the notes are for South Australia ",
    "sql":{
        "sel":5,
        "conds":[[3,0,"SOUTH AUSTRALIA"]],
        "agg":0
}
```

Fig. 7 Example of training sample

In Fig. 7, table\_id represents the corresponding table of a query; question is the natural language query, sql is the annotated SQL statement; agg and sel represent the column name and the aggregate function of the SELECT statement, respectively; conds are triplets (columnname, operator, value) of the WHERE statement.

Logic form accuracy  $Acc_1$  and execution accuracy  $Acc_e$  are used to evaluate the performance. Logic form accuracy considers whether the predicted SQL statement matches the ground truth. Execution accuracy considers if the execution result of the predicted SQL statement is the same as the execution result of the ground truth one. The formulas are as follows.

$$Score_{1} = \begin{cases} 1, & \text{if } SQL' = SQL, \\ 0, & \text{if } SQL' \neq SQL, \end{cases}$$
 (4)

$$Acc_1 = \frac{1}{N} \sum_{n=1}^{N} Score_1^n, \qquad (5)$$

$$Score_{e} = \begin{cases} 1, & \text{if } Y' = Y, \\ 0, & \text{if } Y' \neq Y, \end{cases}$$
 (6)

$$Acc_e = \frac{1}{N} \sum_{n=1}^{N} Score_e^n \tag{7}$$

where N denotes the size of a specific split of the dataset; SQL' and SQL denote the predicted SQL statement and the ground truth one, respectively; Y' and Y represent the execution result of the predicted SQL statement and the ground truth one, respectively.

## 4. 2 Execution-guided decoding

Execution-guided decoding [11] uses beam search to expand the search space of candidate SQL statements and uses the execution result to filter the candidates. The main idea of execution-guided decoding is as follows. If the execution result of the predicted SQL statement is empty or the SQL parser cannot parse the statement, it is believed that the predicted SQL statement is wrong and another SQL statement will be selected from the candidates. In the following experiments, execution-guided decoding is used to further improve the performance.

## 4.3 Parameter settings

All the experiments were conducted on an entry-level server. Hardware and software configurations are shown in Table 3.

 Table 3
 Hardware and software configurations

| Item                     | Value                                         |  |
|--------------------------|-----------------------------------------------|--|
| Operating system         | CentOS Linux release 7. 7. 1908               |  |
| Central processing unit  | Intel(R) Xeon(R) Silver 4208<br>CPU @ 2.10GHz |  |
| Graphics processing unit | GeForce GTX 2080 Ti 11GB                      |  |
| Programming environment  | Python 3. 6, Pytorch 1. 7                     |  |

Due to the limitation of the hardware, the implementation is based on  $RoBERTa_{\rm base}$   $^{[13]}$ . At the pretraining stage, the encoder was trained for three epochs. The initial learning rate was  $3\times 10^{-6}$ . At the curriculum learning stage, the model was first trained on the full training set for two epochs to get the difficulty scorer. Then the scored training samples were split into four buckets. After that the model was trained for three epochs for each training stage until all buckets were trained. Finally, the model was further trained on the full training set until converge.

#### 4. 4 Baselines

In order to establish a comprehensive performance comparison, multiple baseline methods for the text-to-SQL task are implemented and evaluated.

- 1) HydraNet: HydraNet<sup>[6]</sup> proposes a hybrid ranking network, which casts the text-to-SQL problem as a column-wise ranking and decoding problem. It uses RoBERTa<sup>[12]</sup> as the encoder.
- 2) HydraNet+Pt: the query-schema alignment pretraining method is implemented on that of the original HydraNet.
- 3) HydraNet+CL: curriculum learning is applied to the original HydraNet.
- 4) TSCL-SQL: the proposed method utilizes both query-schema alignment pre-training and curriculum learning.

#### 4.5 Results and analyses

The results are shown in Tables 4 and 5, which demonstrate the framework's performance under two scenarios, namely with execution-guided decoding (EG) and without EG.

- 1) When EG is not applied, the logic form accuracy and the execution accuracy of the re-produced HydraNet model on the test set are 80.8% and 86.4%, respectively. The proposed model, TSCL-SQL, improves performance by 1.5% and 1.4%, respectively.
- $2\,)$  When EG is applied, although the execution accuracy on the test set is already  $91.\,0\%$ , TSCL-SQL still improves the logic form accuracy and the execution accuracy by  $0.\,9\%$  and  $0.\,5\%$ , respectively.
- 3) Ablation studies are conducted to investigate the effectiveness of the pre-training stage and the curriculum learning stage. If the pre-training stage is removed, the logic form accuracy and the execution accuracy will drop 0.5% and 0.6%, respectively, on the test set when EG is not applied. When EG is applied, there is still a slight

decrease on the logic form and the execution accuracy if the pre-training stage is removed. It demonstrates that the pre-training stage would help the model initialize a better representation.

Table 4 Performance of TSCL-SQL framework without EG

| Model       | Develop               | Development set      |                       | Test set             |  |
|-------------|-----------------------|----------------------|-----------------------|----------------------|--|
|             | Logic form accuracy/% | Execution accuracy/% | Logic form accuracy/% | Execution accuracy/% |  |
| HydraNet    | 81. 3                 | 86. 9                | 80.8                  | 86. 4                |  |
| HydraNet+Pt | 79. 7                 | 85. 2                | 79. 4                 | 85. 0                |  |
| HydraNet+CL | 82. 0                 | 87. 5                | 81.8                  | 87. 2                |  |
| TSCL-SQL    | 82. 5                 | 88. 2                | 82. 3                 | 87.8                 |  |

 Table 5
 Performance of TSCL-SQL framework with EG

| Model          | Develop               | Development set      |                       | Test set             |  |
|----------------|-----------------------|----------------------|-----------------------|----------------------|--|
|                | Logic form accuracy/% | Execution accuracy/% | Logic form accuracy/% | Execution accuracy/% |  |
| HydraNet+EG    | 85. 2                 | 91. 2                | 84. 9                 | 91.0                 |  |
| HydraNet+Pt+EG | 84. 3                 | 90. 2                | 83. 9                 | 90. 1                |  |
| HydraNet+CL+EG | 85. 7                 | 91.6                 | 85. 4                 | 91. 2                |  |
| TSCL-SQL+EG    | 86. 1                 | 92. 1                | 85. 6                 | 91. 5                |  |

Tables 6 and 7 show the performance comparison on all sub-tasks. TSCL-SQL achieves a performance improvement of 0.4% on the S-AGG sub-task compared

to the baseline on the test set. On the other sub-tasks, the performance is still comparable. Therefore, TSCL-SQL is effective.

Table 6 Development accuracy and test accuracy of various sub-tasks on Wiki SQL dataset without EG

| Model       | Development accuracy/% |       |       |       |       |       |       | Test accuracy/% |       |       |       |       |  |  |
|-------------|------------------------|-------|-------|-------|-------|-------|-------|-----------------|-------|-------|-------|-------|--|--|
|             | S-COL                  | S-AGG | W-NUM | W-COL | W-OP  | W-VAL | S-COL | S-AGG           | W-NUM | W-COL | W-OP  | W-VAL |  |  |
| HydraNet    | 97. 5                  | 90. 5 | 98. 5 | 94. 6 | 97. 4 | 95. 2 | 97. 4 | 90.6            | 97. 8 | 94. 0 | 96. 7 | 94. 6 |  |  |
| HydraNet+Pt | 97. 2                  | 90. 2 | 98. 1 | 93. 5 | 96. 7 | 94.0  | 97. 2 | 90. 2           | 97. 7 | 92.8  | 96. 0 | 93. 7 |  |  |
| HydraNet+CL | 97. 5                  | 90. 7 | 98. 3 | 94. 5 | 97. 3 | 95. 2 | 97. 3 | 91.0            | 97. 7 | 93.8  | 96. 5 | 95. 0 |  |  |
| TSCL-SQL    | 97.7                   | 90. 9 | 98. 5 | 94.8  | 97. 6 | 95. 6 | 97. 4 | 91.0            | 98. 0 | 94. 4 | 97. 0 | 95. 4 |  |  |

Table 7 Development accuracy and test accuracy of various sub-tasks on Wiki SQL dataset with EG

| Model          | Development accuracy/% |       |       |       |       |       | Test accuracy/% |       |       |       |       |       |  |
|----------------|------------------------|-------|-------|-------|-------|-------|-----------------|-------|-------|-------|-------|-------|--|
| Model          | S-COL                  | S-AGG | W-NUM | W-COL | W-OP  | W-VAL | S-COL           | S-AGG | W-NUM | W-COL | W-OP  | W-VAL |  |
| HydraNet+EG    | 97. 5                  | 90. 5 | 98.7  | 97. 3 | 97. 7 | 97. 6 | 97. 4           | 90. 6 | 97. 9 | 96.8  | 97. 0 | 96. 9 |  |
| HydraNet+Pt+EG | 97. 2                  | 90. 2 | 98.3  | 96. 7 | 97. 1 | 97. 2 | 97. 2           | 90. 2 | 97.6  | 96. 1 | 96. 5 | 96. 3 |  |
| HydraNet+CL+EG | 97. 5                  | 90. 7 | 98. 5 | 97. 2 | 97. 6 | 97. 6 | 97. 3           | 91.0  | 98. 0 | 96. 7 | 96. 9 | 97. 1 |  |
| TSCL-SQL+EG    | 97.7                   | 90. 9 | 98.7  | 97. 4 | 97. 9 | 97.8  | 97.4            | 91.0  | 98. 1 | 96. 9 | 97.3  | 97. 2 |  |

Through analysis, it is found that both the pretraining stage and the curriculum learning stage are important. The pre-training stage provides a better representation for downstream tasks. The curriculum learning stage lets the model learn from easy tasks to complex tasks. It is beneficial for the model to approach the global minimum gradually and smoothly.

# 5 Conclusions

In this paper, a two-stage curriculum learning framework for text-to-SQL (TSCL-SQL) is proposed. At the pre-training stage, a schema identification pre-training task is proposed to build an alignment between

queries and schemas. At the curriculum learning stage, an automatic curriculum learning solution is proposed for the text-to-SQL task. Experimental results demonstrate the effectiveness of the framework proposed in this paper.

#### References

- [ 1 ] TANG L R, MOONEY R J. Using multiple clause constructors in inductive logic programming for semantic parsing [ C ] // European Conference on Machine Learning. Berlin, Heidelberg: Springer, 2001: 466-477.
- [2] ZHONG V, XIONG C M, SOCHER R. Seq2SQL: generating structured queries from

- natural language using reinforcement learning [J]. *ArXiv preprint*, *ArXiv*: 1709.00103, 2017.
- [ 3 ] TUR G, DE M R. Spoken language understanding: systems for extracting semantic information from speech [ M ]. Hoboken, USA: John Wiley & Sons, Inc., 2011.
- [ 4 ] XU X J, LIU C, SONG D. SQLNet: generating structured queries from natural language without reinforcement learning [ J ]. *ArXiv preprint*, *ArXiv*:1711.04436, 2017.
- [5] HE P C, MAO Y, CHAKRABARTI K, et al. X-SQL: reinforce schema representation with context[J]. ArXiv preprint, ArXiv:1908.08113, 2019.
- [ 6 ] LYU Q, CHAKRABARTI K, HATHI S, et al. Hybrid ranking network for text-to-SQL [ J ]. ArXiv preprint, ArXiv:2008.04759, 2020.
- [7] BENGIO Y, LOURADOUR J, COLLOBERT R, et al. Curriculum learning [C] // Proceedings of the 26th Annual International Conference on Machine Learning, New York, USA. New York: Association for Computing Machinery, 2009: 41-48.
- [8] HUMEAU S, SHUSTER K, LACHAUX M A, et al. Poly-encoders: architectures and pre-training strategies for fast and accurate multi-

- sentence scoring [ C ]// International Conference on Learning Representations. [ S. 1. : s. n. ], 2019.
- [9] MAZARE P E, HUMEAU S, RAISON M, et al. Training millions of personalized dialogue agents [C] // Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing. Brussels, Belgium: Association for Computational Linguistics, 2018: 2775-2779.
- [10] VASWANI A, SHAZEER N, PARMAR N, et al. Attention is all you need [C] // Proceedings of the 31st International Conference on Neural Information Processing Systems. Red Hook, USA: Curran Associates Inc., 2017: 6000-6010.
- [11] WANG C, TATWAWADI K, BROCKSCHMIDT M, et al. Robust text-to-SQL generation with execution-guided decoding [J]. ArXiv preprint, ArXiv: 1807. 03100, 2018.
- [12] LIU Y, OTT M, GOYAL N, et al. Roberta: a robustly optimized bert pretraining approach [J]. ArXiv preprint, ArXiv: 1907. 11692, 2019.
- [13] Hugging face. RoBERTa base model [EB/OL]. [2022-07-01]. https://huggingface.co/roberta-base.