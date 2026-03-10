import signal
import sys
import sqlite3
import json
import argparse
import os
from func_timeout import func_timeout, FunctionTimedOut
from tqdm import tqdm
import multiprocessing as mp
import random


prompt = """Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
SQLite

Database Schema:
{db_details}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{question}

Instructions:
- Make sure you only output the information that is asked in the question. If the question asks for a specific column, make sure to only include that column in the SELECT clause, nothing more.
- The generated query should return all of the information asked in the question without any missing or extra information.
- Before generating the final SQL query, please think through the steps of how to write the query.
- Note that while the reasoning process and SQL query need to be enclosed within <think> </think> and <answer> </answer> tags respectively, this should not affect the quality of the SQL generation.
- The answer must contain the SQL query within ```sql ``` tags.

Output Format:
In your answer, please enclose the generated SQL query in a code block:
```sql
-- Your SQL query
```

Take a deep breath and think step by step to find the correct SQL query."""

prompt_no_think = """Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
SQLite

Database Schema:
{db_details}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{question}

Instructions:
- Make sure you only output the information that is asked in the question. If the question asks for a specific column, make sure to only include that column in the SELECT clause, nothing more.
- The generated query should return all of the information asked in the question without any missing or extra information.
- Before generating the final SQL query, please think through the steps of how to write the query.
- The answer must contain the SQL query within ```sql ``` tags.

Output Format:
In your answer, please enclose the generated SQL query in a code block:
```sql
-- Your SQL query
```

Take a deep breath and think step by step to find the correct SQL query."""

prompt_correct="""Task Overview:
You are a data science expert. Now, please follow the instructions and complete the corresponding task, explaining your thought process, just like a human would think step by step.

Database Engine:
SQLite

Database Schema:
{{SCHEMA}}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{{QUESTION}}

The sql written by your colleague:
{{SQL}}

Error message:
{{ERROR}}

Instructions:
- Based on the database schema provided, the error sql written by your colleague and its error messages, generate one SQL query that answers the question銆?- You should try to fix the error of the sql written by your colleague and avoid it from happening again.
- Consider all constraints of each table, including primary keys, foreign keys, and data types.
- Provide your query in standard SQL format with appropriate use of SQL functions, joins, and conditions.
- The answer must contain the SQL query within ```sql ``` tags.

Output Format:
In your answer, please enclose the generated SQL query in a code block:
```sql
-- You SQL query
```
Take a deep breath and think step by step to find the correct SQL query."""
def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def catgory(args):
    data = load_json(args.input_file)
    ans = 0
    correct_data = []
    error_data = []
    mismatch_data = []
    for i in range(0, len(data)):
        if data[i]['correctness'] == 0:
            mismatch_data.append(data[i])
        elif data[i]['correctness'] == 1:
            correct_data.append(data[i])
        elif data[i]['correctness'] == 2:
            error_data.append(data[i])
        else:
            pass

    with open(args.out1, "w", encoding="utf-8") as f:
        json.dump(correct_data, f, ensure_ascii=False, indent=4)
    
    with open(args.out2, "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=4)

    with open(args.out3, "w", encoding="utf-8") as f:
        json.dump(mismatch_data, f, ensure_ascii=False, indent=4)
    
    """
    python construct_sft.py \
        --input_file  /root/autodl-tmp/data/res_32B.json\
        --out1 /root/autodl-fs/tmp/correct_res_bird_trainset/correct_data.json\
        --out2 /root/autodl-fs/tmp/correct_res_bird_trainset/error_data.json\
        --out3 /root/autodl-fs/tmp/correct_res_bird_trainset/mismatch_data.json
    python construct_sft.py \
        --input_file  /data/6B/humnasql/data/res_32B.json\
        --out1 /data/6B/humnasql/data/incorrect_res/correct_data.json\
        --out2 /data/6B/humnasql/data/incorrect_res/error_data.json\
        --out3 /data/6B/humnasql/data/incorrect_res/mismatch_data.json

    python construct_sft.py \
        --input_file /root/autodl-tmp/humansql_data/eval_result/self_trainset_result_for_dpo/res_stage3_60steps_maj.json \
        --out1 /root/autodl-tmp/humansql_data/eval_result/self_trainset_result_for_dpo/correct_data.json\
        --out2 /root/autodl-tmp/humansql_data/eval_result/self_trainset_result_for_dpo/error_data.json\
        --out3 /root/autodl-tmp/humansql_data/eval_result/self_trainset_result_for_dpo/mismatch_data.json

    python construct_sft.py \
        --input_file /root/autodl-fs/tmp/Spider_GEN7Bmaj_results.json \
        --out1 /root/autodl-fs/tmp/train_spider_res/correct_data.json\
        --out2 /root/autodl-fs/tmp/train_spider_res/error_data.json\
        --out3 /root/autodl-fs/tmp/train_spider_res/mismatch_data.json

    python construct_sft.py \
        --input_file /root/autodl-fs/tmp/stage_2_1_midstep_bird/res_stage2_1_mid_step_maj.json \
        --out1 /root/autodl-fs/tmp/stage_2_1_midstep_bird/correct_data.json\
        --out2 /root/autodl-fs/tmp/stage_2_1_midstep_bird/error_data.json\
        --out3 /root/autodl-fs/tmp/stage_2_1_midstep_bird/mismatch_data.json
    
    """
def get_sft_correct(args):
    """
    鎶婄籂姝ｇ殑鏁版嵁鍋氭垚prompt锛屼絾鏄病鏈夋彁绀鸿瘝锛屾彁绀鸿瘝灏辩敤question hash map涓€涓?    """
    """
    python construct_sft.py \
        --out2 /root/autodl-tmp/humansql_data/processed_data/bird_dev_with_schema_groundtruth.json\
        --out1 /root/autodl-tmp/humansql_data/processed_data/correct_data.json \
        --out3 /root/autodl-tmp/humansql_data/processed_data/sft_data_GEN7BCorrect.json
    
    python construct_sft.py \
        --out2 /root/autodl-tmp/humansql_data/processed_data/bird_dev_with_schema_groundtruth_replaced_path.json\
        --out1 /root/autodl-tmp/humansql_data/eval_result/stage3_rseult/correct_data.json \
        --out3 xxx
    
    python construct_sft.py \
        --out2 /root/autodl-fs/tmp/bird_train_with_schema_groundtruth.json\
        --out1 /root/autodl-fs/tmp/correct_res_bird_trainset/correct_data.json  \
        --out3 /root/autodl-fs/tmp/correct_res_bird_trainset/correct_sft_data.json
    """

    
    from datasets import load_dataset
    sft_data = load_json(args.out1)
    data_prompt = load_json(args.out2)
    # data_prompt = load_dataset("parquet", data_files=args.out2, split="train")
    print(len(data_prompt))
    m = {}
    for x in data_prompt:
        if x['question'] in m: print(x['question'])
        m[x['question']] = [x['create_format'], x['text']]
    print(len(list(m)))
    # assert len(list(m)) == 9428
    cnt = set()
    for x in sft_data:
        cnt.add(x['question'])
        # x['prompt'] = prompt_correct.replace("{{QUESTION}}", m[x['question'].replace("\n", " ")][1]).replace("{{SCHEMA}}", m[x['question'].replace("\n", " ")][0]).replace("{{SQL}}", m[x['question'].replace("\n", " ")][0]).replace("{{ERROR}}", x['error_msg'])
    with open(args.out3, "w", encoding="utf-8") as f:
        json.dump(sft_data, f, ensure_ascii=False, indent=4)
    print(len(list(cnt)))

    
def get_sft(args):
    """
    鎶婃纭殑鏁版嵁鍋氭垚prompt锛屼絾鏄病鏈夋彁绀鸿瘝锛屾彁绀鸿瘝灏辩敤question hash map涓€涓?    """
    """
    python construct_sft.py \
        --out2 /root/autodl-tmp/humansql_data/processed_data/bird_dev_with_schema_groundtruth.json\
        --out1 /root/autodl-tmp/humansql_data/processed_data/correct_data.json \
        --out3 /root/autodl-tmp/humansql_data/processed_data/sft_data_GEN7BCorrect.json
    python construct_sft.py \
        --out2 /root/autodl-tmp/humansql_data/processed_data/bird_dev_with_schema_groundtruth.json\
        --out1 /root/autodl-tmp/humansql_data/processed_data/correct_data.json \
        --out3 /root/autodl-tmp/humansql_data/processed_data/sft_data_GEN7BCorrect.json
    python construct_sft.py \
        --out2 /root/autodl-fs/data/spider_data/sft_spider_train_with_schema_fk.json\
        --out1 /root/autodl-fs/tmp/train_spider_res/correct_data.json  \
        --out3 /root/autodl-fs/tmp/sft_spider_train_data_GEN7BCorrect.json
    

        
    """

    
    from datasets import load_dataset
    sft_data = load_json(args.out1)
    data_prompt = load_json(args.out2)
    # data_prompt = load_dataset("parquet", data_files=args.out2, split="train")
    print(len(data_prompt))
    m = {}
    for x in data_prompt:
        if x['question'] in m: print(x['question'])
        m[x['question']] = [x['create_format'], x['text']]
    print(len(list(m)))
    # assert len(list(m)) == 9428
    cnt = set()
    for x in sft_data:
        cnt.add(x['question'])
        x['prompt'] = prompt.replace("{question}", m[x['question'].replace("\n", " ")][1]).replace("{db_details}", m[x['question'].replace("\n", " ")][0])
    with open(args.out3, "w", encoding="utf-8") as f:
        json.dump(sft_data, f, ensure_ascii=False, indent=4)
    print(len(list(cnt)))

   
def get_parquet(args):
    """
    python construct_sft.py \
        --out2 /root/autodl-tmp/humansql_data/processed_data/sft_data_GEN7BCorrect.parquet\
        --out1 /root/autodl-tmp/humansql_data/processed_data/sft_data_GEN7BCorrect.json 
    """
    import datasets
    from pprint import pprint
    train_dataset = datasets.load_dataset(
        "json",
        data_files={
            "train": args.out1,
        }
    )
    def make_map_fn(split):
        def process_fn(example, idx):
            data = {
                "prompt": example['prompt'],
                "response": example['response'],
                "question": example['question']
            }
            return data

        return process_fn
    original_columns = train_dataset['train'].column_names
    train_dataset = train_dataset['train'].map(
        function=make_map_fn("train"),
        with_indices=True,
        remove_columns=original_columns  
    )
    train_dataset = train_dataset.remove_columns(
        [col for col in train_dataset.column_names if col not in ['prompt', 'response', 'question']]
    )
    pprint(train_dataset[0])
    train_dataset.to_parquet(args.out2)
    
def for_llama(args):
    """
    鏋勫缓鏁版嵁llamafactory
    python construct_sft.py \
        --out2 /root/autodl-tmp/humansql_data/processed_data/sft_data_GEN7BCorrect_Alpaca.json\
        --out1 /root/autodl-tmp/humansql_data/processed_data/sft_data_GEN7BCorrect.json

    python construct_sft.py \
        --out2 /root/autodl-fs/tmp/correct_res_bird_trainset/correct_sft_Alpaca.json\
        --out1 /root/autodl-fs/tmp/correct_res_bird_trainset/correct_sft_data.json
    
    """
    data = load_json(args.out1)
    result = []

    for x in data:
        result.append({
            "instruction": x['prompt'],
            "input":"",
            "output" :x['response']
        })
    with open(args.out2, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
   
def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
def extract_sql_from_text(answer_text):
    import re
    schema_pattern = r'```sql(.*?)```'
    sql_str = ""
    matches = list(re.finditer(schema_pattern, answer_text, re.DOTALL))
    if not matches:
        return ""
    try:
        sql_str = matches[-1].group(1).strip()
    except Exception as e:
        return sql_str
    return sql_str

def cold_start(args):
    """
    鏋勫缓鍐峰惎鍔ㄦ暟鎹?think>鐨勬暟鎹甽lamafactory
    python construct_sft.py \
        --out2 /root/autodl-tmp/humansql_data/processed_data/sft_train_cold_start_data_GEN7BCorrect_Alpaca_filter.json\
        --out1 /root/autodl-tmp/humansql_data/processed_data/sft_train_data_GEN7BCorrect_Alpaca_filter.json 
    
    python construct_sft.py \
        --out2 /root/autodl-fs/tmp/correct_res_bird_trainset/correct_sft_data_Alpaca_think.json\
        --out1 /root/autodl-fs/tmp/correct_res_bird_trainset/correct_sft_data_Alpaca.json
    """
    result = []
    cnt = 0
    data = load_json(args.out1)
    for x in data:
        sql = extract_sql_from_text(x['output'])
        if sql != "":
            result.append({
                "instruction" :x["instruction"],
                "input": "",
                "output": f"""<think>{x['output']}</think>\n<answer>\n```sql\n{sql}\n```\n</answer>"""
            })
        else:
            cnt += 1
            print(x['output'])
    with open(args.out2, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(cnt)
def dpo_sft(args):
    """
    鏋勫缓dpo鏁版嵁闆嗭紝杩欓噷鐨勬暟鎹敤GEN7B鐨勮瘯涓€涓嬫垨鑰呯敤璁粌濂界殑妯″瀷璇曚竴涓嬩篃琛岋紝鐪嬮偅涓晥鏋滆濂姐€?    python construct_sft.py \
        --out1 /root/autodl-tmp/humansql_data/eval_result/self_trainset_result_for_dpo/res_stage3_60steps_maj.json \
        --out2 /root/autodl-tmp/humansql_data/processed_data/bird_dev_with_schema_groundtruth_replaced_path.json\
        --out3 /root/autodl-tmp/humansql_data/eval_result/self_trainset_result_for_dpo/res_stage3_60steps_dpo.json
        
    python construct_sft.py \
        --out1 /root/autodl-tmp/humansql_data/eval_result/GEN7B_result/res.json \
        --out2 /root/autodl-tmp/humansql_data/processed_data/bird_train_with_schema_groundtruth_replaced_path.json\
        --out3 /root/autodl-tmp/humansql_data/eval_result/GEN7B_result/res_dpo.json
    """
    from collections import defaultdict
    from transformers import AutoTokenizer
    generated_data = load_json(args.out1)
    data_prompt = load_json(args.out2)
    # data_prompt = load_dataset("parquet", data_files=args.out2, split="train")
    print(len(data_prompt))
    m = defaultdict(str)
    for x in data_prompt:
        if x['question'] in m: print(x['question'])
        m[x['question']] = prompt.replace("{question}", x['text']).replace("{db_details}", x['create_format'])

    
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B", trust_remote_code=True)
    # todo : 杩欓噷鐨剅esponse 鏄痗old start鍓嶇殑鏁版嵁锛屽厛璇曚竴涓?    map_question = defaultdict(list)
    for data in tqdm(generated_data, desc="generate map..."):
        if len(m[data['question'].replace("\n", " ")]) < 5: print(m[data['question'].replace("\n", " ")])
        map_question[data['question']].append({
            # "response": f"""<think>{data['response']}</think>\n<answer>\n```sql\n{data['pred_sql']}\n```\n</answer>""",
            "response": data['response'],
            "correctness": data['correctness'],
            "prompt": m[data['question'].replace("\n", " ")],
            "response_tokens": len(tokenizer.encode(data['response'], add_special_tokens=False))
        })
    cnt = 0
    dpo_dataset = []
    for q, arr in tqdm(map_question.items(), desc="geneerate dpo..."):
        chosen_candidates = [x for x in arr if x['correctness'] == 1]
        if not chosen_candidates:
            continue
        
        chosen = min(chosen_candidates, key=lambda x: x['response_tokens'])
        if len(tokenizer.encode(chosen["prompt"], add_special_tokens=False)) > 5400: continue
        # 鎸?correctness 鍊煎垎缁勯敊璇牱鏈?        error_map = defaultdict(list)
        for x in arr:
            if x['correctness'] != 1:
                error_map[x['correctness']].append(x)
        cnt += 1
        for correctness, rej_list in error_map.items():
            rej = max(rej_list, key=lambda x: x['response_tokens'])
            dpo_dataset.append({
                "conversations": [
                    {"from": "human", "value": chosen["prompt"]}
                ],
                "chosen": {
                    "from": "gpt",
                    "value": chosen["response"]
                },
                "rejected": {
                    "from": "gpt",
                    "value": rej["response"]
                }
            })
    print("original len is:",len(list(map_question)))
    print("dpo len is:",cnt)
    print("rate",cnt / len(list(map_question)))
    with open(args.out3, "w", encoding="utf-8") as f:
        json.dump(dpo_dataset, f, ensure_ascii=False, indent=4)


def parse_option():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type = str, default = "predict_dev.json")
    parser.add_argument('--out1', type = str, default = "predict_dev.json")
    parser.add_argument('--out2', type = str, default = "predict_dev.json")
    parser.add_argument('--out3', type = str, default = "predict_dev.json")
    opt = parser.parse_args()

    return opt

if __name__ == "__main__":
    opt = parse_option()
    catgory(opt)
    # get_sft(opt)
    # get_sft_correct(opt)
    # get_parquet(opt)
    # for_llama(opt)
    # cold_start(opt)
    # dpo_sft(opt)
