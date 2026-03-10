# -*- coding: utf-8 -*-
# Author: Zhiliang Long
# File: infer.py

import argparse
import json
import re
import os
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
from typing import Any, List, Dict
from datasets import load_dataset
from datasets import config; 
config.HF_DATASETS_OFFLINE = True

def get_input_data(data_path: str):
    """Load dataset from a JSON/Parquet file via datasets.load_dataset."""
    if data_path.lower().endswith(".parquet") or "parquet" in data_path.lower():
        data = load_dataset("parquet", data_files=data_path)["train"]
    else:
        data = load_dataset("json", data_files=data_path, split="train")
    return data


def extract_json_from_text(answer_text: str) -> Dict[str, Any]:
    """Extract last ```json ...``` block and parse to dict; return {} on failure."""
    pattern = r"```json(.*?)```"
    matches = list(re.finditer(pattern, answer_text, re.DOTALL))
    if not matches:
        return {}
    json_str = matches[-1].group(1).strip()
    try:
        return json.loads(json_str)
    except Exception:
        return {}


def extract_sql_from_text(answer_text: str) -> str:
    pattern = r"```sql(.*?)```"
    matches = list(re.finditer(pattern, answer_text, re.DOTALL))
    if not matches:
        return ""
    try:
        return matches[-1].group(1).strip()
    except Exception:
        return ""


def extract_explain_from_text(answer_text: str) -> str:
    pattern = r"```plaintext(.*?)```"
    matches = list(re.finditer(pattern, answer_text, re.DOTALL))
    if not matches:
        return ""
    try:
        return matches[-1].group(1).strip()
    except Exception:
        return ""


def extract_filter_from_text(answer_text: str) -> str:
    pattern = r"<answer>(.*?)</answer>"
    matches = list(re.finditer(pattern, answer_text, re.DOTALL))
    if not matches:
        return ""
    try:
        return matches[-1].group(1).strip()
    except Exception:
        return ""


# ================================
# Templates (no external imports)
# ================================
gen = """Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
SQLite

Database Schema:
{{SCHEMA}}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{{QUESTION}}

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

Take a deep breath and think step by step to find the correct SQL query.
"""

infer = """Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
SQLite

Database Schema:
{{SCHEMA}}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{{QUESTION}}

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

Take a deep breath and think step by step to find the correct SQL query.
"""

SLM_template = """
You first think about the reasoning process in your mind and then provide the answer.
Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
SQLite

Database Schema:
{{SCHEMA}}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{{QUESTION}}

Instructions:
- Return only what is asked in the question. If the question asks for a specific column, include only that column in SELECT.
- The query must return all required information without missing or extra data.
- Before writing the final SQL, think through the steps.

Output Format:
Show your work in <think> </think> tags. Return the final SQLite SQL that starts with keyword 'SELECT' in <answer> </answer> tags, for example <answer>SELECT AVG(rating_score) FROM movies</answer>.

Let me solve this step by step.
"""

sql_correct_prompt = """Task Overview:
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
- Based on the database schema provided, the error sql written by your colleague and its error messages, generate one SQL query that answers the question
- You should try to fix the error of the sql written by your colleague and avoid it from happening again.
- Consider all constraints of each table, including primary keys, foreign keys, and data types.
- Provide your query in standard SQL format with appropriate use of SQL functions, joins, and conditions.
- The answer must contain the SQL query within ```sql ``` tags.

Output Format:
In your answer, please enclose the generated SQL query in a code block:
```sql
-- You SQL query
```
Take a deep breath and think step by step to find the correct SQL query.
"""


def get_prompt_template_by_name(name: str) -> str:
    name = (name or '').strip()
    if name == 'infer':
        return infer
    if name == 'gen':
        return gen
    if name == 'SLM_template':
        return SLM_template
    if name == 'sql_correct_prompt':
        return sql_correct_prompt
    return infer


def get_input_seq(data: Dict[str, Any], prompt_template: str, metadata: Dict[str, str] | None = None) -> str:
    if "{{ERROR}}" in prompt_template:
        prompt = (
            prompt_template
            .replace("{{SCHEMA}}", str(data.get('create_format') if metadata is None else metadata.get(data['db_id'], data.get('create_format'))))
            .replace("{{QUESTION}}", data.get('text', ''))
            .replace("{{ERROR}}", data.get('error_msg', ''))
            .replace("{{SQL}}", data.get('gen_sql', ''))
        )
    elif "{{CAND_SQL}}" in prompt_template:
        prompt = (
            prompt_template
            .replace("{{SCHEMA}}", str(data.get('schema') if metadata is None else metadata.get(data['db_id'], data.get('schema'))))
            .replace("{{CAND_SQL}}", data.get('pred_sql', ''))
            .replace("{{External}}", data.get('evidence', ''))
        )
    elif "{{FILTER_SQL}}" in prompt_template:
        prompt = (
            prompt_template
            .replace("{{SCHEMA}}", str(data.get('create_format') if metadata is None else metadata.get(data['db_id'], data.get('create_format'))))
            .replace("{{FILTER_SQL}}", data.get('pred_sql', ''))
            .replace("{{QUESTION}}", data.get('text', ''))
        )
    else:
        prompt = (
            prompt_template
            .replace("{{SCHEMA}}", str(data.get('create_format') if metadata is None else metadata.get(data['db_id'], data.get('create_format'))))
            .replace("{{QUESTION}}", data.get('text', ''))
        )
    return prompt


def main(opt):
    # 加载输入数据集（JSON/Parquet）
    input_dataset = get_input_data(opt.input_file)
    # 若提供了 mix_data 路径，则加载备用数据集；否则为 None
    mix_dataset = get_input_data(opt.mix_data) if opt.mix_data else None

    # 若提供了 metadata 文件，则加载并构建 db_id -> schema_lang 的映射字典
    if opt.metadata is not None:
        r = get_input_data(opt.metadata)
        metadata: Dict[str, str] = {}
        for x in r:
            metadata[x['db_id']] = x['schema_lang']
    else:
        metadata = None

    # 加载与模型配套的分词器，仅使用本地文件
    tokenizer = AutoTokenizer.from_pretrained(opt.nl2sql_ckpt_path, trust_remote_code=True, local_files_only=True)

    # 根据模型名称设置对应的 stop_token_ids，用于生成时提前终止
    if "Qwen2.5-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [151645]
    elif "deepseek-coder-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [32021]
    elif "DeepSeek-Coder-V2" in opt.nl2sql_ckpt_path:
        stop_token_ids = [100001]
    elif "OpenCoder-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [96539]
    elif "Meta-Llama-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [128009, 128001]
    elif "granite-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [0]
    elif "starcoder2-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [0]
    elif "Codestral-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [2]
    elif "Mixtral-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [2]
    elif "OmniSQL-" in opt.nl2sql_ckpt_path:
        stop_token_ids = [151645]
    else:
        # 默认使用 Qwen2.5 的 stop token
        print("Use Qwen2.5's stop tokens by default.")
        stop_token_ids = [151645]

    # 打印当前使用的 stop token id 列表
    print("stop_token_ids:", stop_token_ids)

    # 设置模型最大长度、输入长度与输出长度
    max_model_len = opt.max_model_len if hasattr(opt, 'max_model_len') and opt.max_model_len else 1024 * 14
    max_input_len = 1024 * 12
    max_output_len = 1024 * 2
    print("max_model_len:", max_model_len)
    print("temperature:", opt.temperature)

    # 若检测到 Qwen3 系列模型，直接抛出异常（暂不支持）
    if "Qwen3-" in opt.nl2sql_ckpt_path:
        raise ValueError(f"Unsupported model: {opt.nl2sql_ckpt_path}")
    else:
        # 配置采样参数：温度、最大 token 数、返回条数、停止 token
        sampling_params = SamplingParams(
            temperature=opt.temperature,
            max_tokens=max_output_len,
            n=opt.n,
            stop_token_ids=stop_token_ids,
        )

    # 初始化 vLLM 引擎
    llm = LLM(
        model=opt.nl2sql_ckpt_path,
        dtype="bfloat16",
        tensor_parallel_size=opt.tensor_parallel_size,
        max_model_len=max_model_len,
        gpu_memory_utilization=opt.gpu_memory_utilization if hasattr(opt, 'gpu_memory_utilization') and opt.gpu_memory_utilization else 0.35,
        swap_space=42,
        enforce_eager=True,
        disable_custom_all_reduce=True,
        trust_remote_code=True,
    )

    # 再次检查模型类型，若 Qwen3 则抛出异常（与上面重复，确保保险）
    if "Qwen3-" in opt.nl2sql_ckpt_path:
        raise ValueError(f"Unsupported model: {opt.nl2sql_ckpt_path}")
    else:
        # 存放最终用于生成的 prompt 列表
        chat_prompts: List[str] = []
        # 根据命令行参数选择 prompt 模板，默认为 infer
        chosen_template = get_prompt_template_by_name(getattr(opt, 'prompt_template', 'infer'))
        # 遍历输入数据，为每条样本构建 prompt
        for i, data in enumerate(input_dataset):
            # 步骤1：根据 prompt_key 决定使用哪种方式构建 prompt
            if opt.prompt_key == "prompt":
                prompt = tokenizer.apply_chat_template(
                    [{"role": "user", "content": data["prompt"]}],
                    add_generation_prompt=True,
                    tokenize=False,
                )
            else:
                prompt = tokenizer.apply_chat_template(
                    [{"role": "user", "content": get_input_seq(data, chosen_template, metadata=metadata)}],
                    add_generation_prompt=True,
                    tokenize=False,
                )
            # 步骤2：若 prompt token 长度超过 6144 且存在 mix_dataset，则回退到 mix_data 对应样本
            token_len = len(tokenizer(prompt)["input_ids"])
            if token_len > 6144 and mix_dataset is not None:
                print(f"[INFO] Prompt #{i} > 6144 tokens; using mix_data fallback")
                backup_data = mix_dataset[i]
                if opt.prompt_key == "prompt":
                    prompt = tokenizer.apply_chat_template(
                        [{"role": "user", "content": backup_data["prompt"]}],
                        add_generation_prompt=True,
                        tokenize=False,
                    )
                else:
                    prompt = tokenizer.apply_chat_template(
                        [{"role": "user", "content": get_input_seq(backup_data, chosen_template, metadata=metadata)}],
                        add_generation_prompt=True,
                        tokenize=False,
                    )
            chat_prompts.append(prompt)

    # 计算所有 prompt 的 token 长度，并打印最大长度及首个 prompt 示例
    token_lens = [len(tokenizer(prompt)["input_ids"]) for prompt in chat_prompts]
    max_token_len = max(token_lens)
    print("Max token length:", max_token_len)
    print(chat_prompts[0])

    # 调用 vLLM 批量生成
    outputs = llm.generate(chat_prompts, sampling_params)

    # 根据 output_format 选择不同的后处理与保存逻辑
    results: List[Dict[str, Any]] = []
    if opt.output_format == "schema":
        # schema 模式：提取 json 块作为预测 schema
        for data, output in zip(input_dataset, outputs):
            responses = [o.text for o in output.outputs]
            schema = [extract_json_from_text(response) for response in responses]
            data["responses"] = responses
            data["pred_schema"] = schema
            results.append(dict(data))
        with open(opt.output_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(results, indent=2, ensure_ascii=False))

    elif opt.output_format == "sql":
        # sql 模式：提取 ```sql 代码块作为预测 SQL
        for data, output in zip(input_dataset, outputs):
            save_data: Dict[str, Any] = {}
            responses = [o.text for o in output.outputs]
            sqls = [extract_sql_from_text(response) for response in responses]
            save_data["responses"] = responses
            save_data["pred_sql"] = sqls
            save_data["question"] = data.get('question')
            save_data["db_id"] = data.get('db_id')
            save_data["gt_sql"] = data.get('sql')
            if "prompt" in data:
                save_data["prompt"] = data["prompt"]
            results.append(save_data)
        with open(opt.output_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(results, indent=2, ensure_ascii=False))

    elif opt.output_format == "explain":
        # explain 模式：提取 ```plaintext 块作为解释文本
        for data, output in zip(input_dataset, outputs):
            save_data: Dict[str, Any] = {}
            responses = [o.text for o in output.outputs]
            explain_text = [extract_explain_from_text(response) for response in responses]
            save_data["responses"] = responses
            save_data["explain_text"] = explain_text
            save_data["question"] = data.get('question')
            save_data["ground_truth"] = data.get('ground_truth')
            save_data["idx"] = data.get('idx')
            save_data["pred_sql"] = data.get('pred_sql')
            if "prompt" in data:
                save_data["prompt"] = data["prompt"]
            results.append(save_data)
        with open(opt.output_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(results, indent=2, ensure_ascii=False))

    elif opt.output_format == "filter":
        # filter 模式：提取 <answer> 标签内的内容作为答案
        for data, output in zip(input_dataset, outputs):
            save_data: Dict[str, Any] = {}
            responses = [o.text for o in output.outputs]
            answer_text = [extract_filter_from_text(response) for response in responses]
            save_data["responses"] = responses
            save_data["answer_text"] = answer_text
            save_data["question"] = data.get('question')
            save_data["ground_truth"] = data.get('ground_truth')
            save_data["idx"] = data.get('idx')
            save_data["pred_sql"] = data.get('pred_sql')
            if "prompt" in data:
                save_data["prompt"] = data["prompt"]
            results.append(save_data)
        with open(opt.output_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(results, indent=2, ensure_ascii=False))
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nl2sql_ckpt_path", type=str)
    parser.add_argument("--input_file", type=str, help="the input file path (prompts)")
    parser.add_argument("--output_file", type=str, help="the output file path (results)")
    parser.add_argument("--tensor_parallel_size", type=int, help="the number of used GPUs", default=4)
    parser.add_argument("--n", type=int, help="the number of generated responses", default=4)
    parser.add_argument("--temperature", type=float, help="temperature of llm's sampling", default=1.0)
    parser.add_argument("--output_format", type=str, help="the format of the output file", default="json")
    parser.add_argument("--prompt_key", type=str, help="the key for the prompt in the output file", default="prompt")
    parser.add_argument(
        "--prompt_template",
        type=str,
        default="infer",
        help="template selector: infer | gen | SLM_template | sql_correct_prompt",
    )
    parser.add_argument("--match_text", type=bool, default=False, help="whether to match text in the input file")
    parser.add_argument("--think_mode", type=bool, default=False)
    parser.add_argument(
        "--mix_data",
        type=str,
        default=None,
        help="Fallback dataset without extra FK info to avoid overly long prompts (used when >6144 tokens)",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default=None,
        help="Optional JSON summarizing DB schema in natural language (db_id -> schema_lang)",
    )
    parser.add_argument(
        "--gpu_memory_utilization",
        type=float,
        default=0.35,
        help="vLLM GPU memory utilization ratio (try 0.6~0.9 if KV-cache fails)",
    )
    parser.add_argument(
        "--max_model_len",
        type=int,
        default=1024 * 14,
        help="Max model context length for vLLM engine",
    )

    opt = parser.parse_args()
    print(opt)
    main(opt)

