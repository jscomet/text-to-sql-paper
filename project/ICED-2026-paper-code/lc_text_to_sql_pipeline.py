# -*- coding: utf-8 -*-
# Author: LangChain Text2SQL Pipeline

import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import torch

# Local/offline dataset loading aligned with infer.py
from datasets import load_dataset
from datasets import config as hf_config
hf_config.HF_DATASETS_OFFLINE = True

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

# LangChain core components
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda


# =============================
# Configuration (templated)
# =============================
@dataclass
class ModelConfig:
    """Templated model configuration for local vLLM inference."""
    # Paths
    gen_model_path: str = \
        "/share/home/tm902089733300000/a904062950/text-to-sql/workplace/ICED-2026-paper-code/models/Qwen2.5-Coder-7B-Instruct"
    check_model_path: str = \
        "/share/home/tm902089733300000/a904062950/text-to-sql/workplace/ICED-2026-paper-code/models/Chinastark-Diss"

    # vLLM runtime
    tensor_parallel_size_gen: int = 4
    tensor_parallel_size_check: int = 4
    max_model_len_gen: int = 1024 * 14
    max_model_len_check: int = 1024 * 14
    gpu_memory_utilization_gen: float = 0.35
    gpu_memory_utilization_check: float = 0.35

    # Sampling params
    temperature_gen: float = 1.0
    temperature_check: float = 1.0
    max_output_len: int = 1024 * 2
    n_gen: int = 1
    n_check: int = 1


# =============================
# Data IO aligned with infer.py
# =============================
def get_input_data(data_path: str):
    """Load dataset (JSON/Parquet) just like infer.py."""
    if data_path.lower().endswith(".parquet") or "parquet" in data_path.lower():
        data = load_dataset("parquet", data_files=data_path)["train"]
    else:
        data = load_dataset("json", data_files=data_path, split="train")
    return data


# =============================
# Prompt templates
# =============================
GEN_PROMPT = """Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
SQLite

Database Schema:
{SCHEMA}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{QUESTION}

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

SQL_CHECK_PROMPT = """Task Overview:
You are a data science expert. Below, you are provided with a database schema, natural language question and a SQL query written by the developer. Your task is to understand the schema and determine whether the SQL query written by the developer can correctly answer the natural language question.

Database Engine:
SQLite

Database Schema:
{SCHEMA}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

User Question:
{QUESTION}

Developer SQL:
{FILTER_SQL}

Instructions:
- First, carefully understand the question and identify exactly what information the question expects (columns, filters, aggregations, ordering, limit, and any other constraints).
- Then, analyze the provided SQL and determine whether it returns exactly what the question asks for — no more, no less.
- Even small mismatches should be considered incorrect (e.g., extra columns, missing filters, wrong table joins, wrong ordering, wrong limit, wrong logic, etc.).
- Note that while the reasoning process and you decision need to be enclosed within <think> </think> and <answer> </answer> tags respectively, this should not affect the quality of you decision.

Output format Example:
<think>
(Your step-by-step reasoning in natural language here)
</think>
<answer>
YES or NO
</answer>

Take a deep breath and think step by step to make important decision.
"""

SQL_CORRECTION_PROMPT = """Task Overview:
Please review my feedback above and reconsider your initial answer. If modifications are needed, generate a new, corrected SQL query that accurately addresses the original user question.

Original User Question:
{user_question}

Your Initial SQL Attempt:
{initial_sql}

Reviewer's Feedback:
{review_feedback}

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


# =============================
# Text processing helpers
# =============================
def extract_sql_from_text(answer_text: str) -> str:
    """Return last ```sql ...``` block content or empty string."""
    pattern = r"```sql(.*?)```"
    matches = list(re.finditer(pattern, answer_text, re.DOTALL))
    if not matches:
        return ""
    try:
        return matches[-1].group(1).strip()
    except Exception:
        return ""


def extract_answer_tag(answer_text: str) -> str:
    """Return last <answer>...</answer> content (YES/NO expected) or empty."""
    pattern = r"<answer>(.*?)</answer>"
    matches = list(re.finditer(pattern, answer_text, re.DOTALL))
    if not matches:
        return ""
    try:
        return matches[-1].group(1).strip()
    except Exception:
        return ""


def extract_think_text(text: str) -> str:
    m = list(re.finditer(r"<think>([\s\S]*?)</think>", text, re.DOTALL))
    think_inner = m[-1].group(1).strip() if m else ""
    if think_inner:
        return think_inner
    cleaned = re.sub(r"</?think>", "", text)
    return cleaned.strip()


def build_review_feedback(check_raw: str, ans: str) -> str:
    feedback = extract_think_text(check_raw)
    note = "Please consider my preliminary advice above to decide whether to revise your answer."
    if feedback:
        return f"{feedback}\n\nAnswer: {ans}\n\n{note}"
    else:
        return f"Answer: {ans}\n\n{note}"


def get_stop_token_ids(model_path: str) -> List[int]:
    """Model-specific stop token ids aligned with infer.py."""
    if "Qwen2.5-" in model_path:
        return [151645]
    if "deepseek-coder-" in model_path:
        return [32021]
    if "DeepSeek-Coder-V2" in model_path:
        return [100001]
    if "OpenCoder-" in model_path:
        return [96539]
    if "Meta-Llama-" in model_path:
        return [128009, 128001]
    if "granite-" in model_path:
        return [0]
    if "starcoder2-" in model_path:
        return [0]
    if "Codestral-" in model_path:
        return [2]
    if "Mixtral-" in model_path:
        return [2]
    if "OmniSQL-" in model_path:
        return [151645]
    return [151645]


# =============================
# vLLM initialization
# =============================
def init_vllm_and_tokenizer(model_path: str,
                            tensor_parallel_size: int,
                            max_model_len: int,
                            gpu_memory_utilization: float) -> Dict[str, Any]:
    """Initialize local tokenizer and vLLM engine."""
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, local_files_only=True)

    if "Qwen3-" in model_path:
        raise ValueError(f"Unsupported model: {model_path}")

    llm = LLM(
        model=model_path,
        dtype="bfloat16",
        tensor_parallel_size=tensor_parallel_size,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        swap_space=42,
        enforce_eager=True,
        disable_custom_all_reduce=True,
        trust_remote_code=True,
    )

    return {"llm": llm, "tokenizer": tokenizer}




# =============================
# Core pipeline per item
# =============================


def generate_batch(dataset, cfg: ModelConfig, gen_env: Dict[str, Any], log_first_dialogue: bool = False) -> List[Dict[str, Any]]:
    llm = gen_env["llm"]
    tok = gen_env["tokenizer"]
    stop_ids = get_stop_token_ids(cfg.gen_model_path)
    sampling = SamplingParams(temperature=cfg.temperature_gen, max_tokens=cfg.max_output_len, n=cfg.n_gen, stop_token_ids=stop_ids)
    chat_prompts: List[str] = []
    schemas: List[str] = []
    questions: List[str] = []
    for idx, item in enumerate(dataset):
        schema = item.get("create_format") or item.get("schema") or ""
        question = item.get("text") or item.get("question") or ""
        gen_prompt = ChatPromptTemplate.from_messages([("user", GEN_PROMPT)])
        gen_content = gen_prompt.format(SCHEMA=schema, QUESTION=question)
        
        prompt_str = tok.apply_chat_template([{"role": "user", "content": gen_content}], add_generation_prompt=True, tokenize=False)
        if log_first_dialogue and idx == 0:
            print("=== First Dialogue Prompt === [generate]")
            print(prompt_str)
            print("=== End First Dialogue Prompt ===")
        chat_prompts.append(prompt_str)
        schemas.append(schema)
        questions.append(question)
    outputs = llm.generate(chat_prompts, sampling)
    results: List[Dict[str, Any]] = []
    for item, schema, question, output in zip(dataset, schemas, questions, outputs):
        text = output.outputs[0].text if output.outputs else ""
        sql = extract_sql_from_text(text)
        results.append({
            "db_id": item.get("db_id"),
            "question": question,
            "schema": schema,
            "gen_raw": text,
            "pred_sql": sql,
            "assistant_history": [text] if text else [],
            "user_feedback_history": [],
        })
    return results


def check_batch(dataset, partial_results: List[Dict[str, Any]], cfg: ModelConfig, check_env: Dict[str, Any]) -> List[Dict[str, Any]]:
    llm = check_env["llm"]
    tok = check_env["tokenizer"]
    stop_ids = get_stop_token_ids(cfg.check_model_path)
    sampling = SamplingParams(temperature=cfg.temperature_check, max_tokens=cfg.max_output_len, n=cfg.n_check, stop_token_ids=stop_ids)
    results = [dict(r) for r in partial_results]
    indices: List[int] = []
    chat_prompts: List[str] = []
    for i, (item, partial) in enumerate(zip(dataset, partial_results)):
        if partial.get("check_answer") == "YES":
            continue
        schema = partial.get("schema") or item.get("create_format") or item.get("schema") or ""
        question = partial.get("question") or item.get("text") or item.get("question") or ""
        gen_sql = partial.get("corrected_sql") or partial.get("pred_sql") or ""
        check_prompt = ChatPromptTemplate.from_messages([("user", SQL_CHECK_PROMPT)])
        check_content = check_prompt.format(SCHEMA=schema, QUESTION=question, FILTER_SQL=gen_sql)
        prompt_str = tok.apply_chat_template([{"role": "user", "content": check_content}], add_generation_prompt=True, tokenize=False)
        chat_prompts.append(prompt_str)
        indices.append(i)
    outputs = llm.generate(chat_prompts, sampling) if chat_prompts else []
    for idx, output in zip(indices, outputs):
        text = output.outputs[0].text if output.outputs else ""
        ans = extract_answer_tag(text).upper()
        feedback_final = build_review_feedback(text, ans)
        results[idx]["check_raw"] = text
        results[idx]["check_answer"] = ans if ans in {"YES", "NO"} else ""
        results[idx]["review_answer"] = ans
        results[idx]["review_feedback"] = feedback_final
        if "user_feedback_history" not in results[idx] or results[idx]["user_feedback_history"] is None:
            results[idx]["user_feedback_history"] = []
        results[idx]["user_feedback_history"].append(feedback_final)
    return results


def correct_batch(dataset, checked_results: List[Dict[str, Any]], cfg: ModelConfig, gen_env: Dict[str, Any]) -> List[Dict[str, Any]]:
    llm = gen_env["llm"]
    tok = gen_env["tokenizer"]
    stop_ids = get_stop_token_ids(cfg.gen_model_path)
    sampling = SamplingParams(temperature=cfg.temperature_gen, max_tokens=cfg.max_output_len, n=cfg.n_gen, stop_token_ids=stop_ids)
    chat_prompts: List[str] = []
    idx_map: List[int] = []
    for idx, (item, res) in enumerate(zip(dataset, checked_results)):
        if res.get("check_answer") != "NO":
            continue
        schema = res.get("schema") or item.get("create_format") or item.get("schema") or ""
        question = res.get("question") or item.get("text") or item.get("question") or ""
        prompt1 = GEN_PROMPT.format(SCHEMA=schema, QUESTION=question)
        messages = [{"role": "user", "content": prompt1}]
        assistants = res.get("assistant_history") or ([] if not res.get("gen_raw") else [res.get("gen_raw")])
        feedbacks = res.get("user_feedback_history") or []
        if assistants:
            messages.append({"role": "assistant", "content": assistants[0]})
        for i, fb in enumerate(feedbacks):
            messages.append({"role": "user", "content": fb})
            if i + 1 < len(assistants):
                messages.append({"role": "assistant", "content": assistants[i + 1]})
        prompt_str = tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        res["last_prompt_str"] = prompt_str
        chat_prompts.append(prompt_str)
        idx_map.append(idx)
    outputs = llm.generate(chat_prompts, sampling) if chat_prompts else []
    results = [dict(r) for r in checked_results]
    for map_idx, output in zip(idx_map, outputs):
        text = output.outputs[0].text if output.outputs else ""
        sql = extract_sql_from_text(text)
        results[map_idx]["corrected_raw"] = text
        results[map_idx]["corrected_sql"] = sql
        if "assistant_history" not in results[map_idx] or results[map_idx]["assistant_history"] is None:
            results[map_idx]["assistant_history"] = []
        results[map_idx]["assistant_history"].append(text)
    return results


# =============================
# CLI entrypoint
# =============================
def main():
    parser = argparse.ArgumentParser(description="LangChain-based Text2SQL pipeline (local vLLM)")
    parser.add_argument("--input_file", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)

    # Model paths
    parser.add_argument("--gen_model_path", type=str, default=ModelConfig.gen_model_path)
    parser.add_argument("--check_model_path", type=str, default=ModelConfig.check_model_path)

    # vLLM params
    parser.add_argument("--tensor_parallel_size_gen", type=int, default=ModelConfig.tensor_parallel_size_gen)
    parser.add_argument("--tensor_parallel_size_check", type=int, default=ModelConfig.tensor_parallel_size_check)
    parser.add_argument("--max_model_len_gen", type=int, default=ModelConfig.max_model_len_gen)
    parser.add_argument("--max_model_len_check", type=int, default=ModelConfig.max_model_len_check)
    parser.add_argument("--gpu_memory_utilization_gen", type=float, default=ModelConfig.gpu_memory_utilization_gen)
    parser.add_argument("--gpu_memory_utilization_check", type=float, default=ModelConfig.gpu_memory_utilization_check)

    # Sampling params
    parser.add_argument("--temperature_gen", type=float, default=ModelConfig.temperature_gen)
    parser.add_argument("--temperature_check", type=float, default=ModelConfig.temperature_check)
    parser.add_argument("--max_output_len", type=int, default=ModelConfig.max_output_len)
    parser.add_argument("--n_gen", type=int, default=ModelConfig.n_gen)
    parser.add_argument("--n_check", type=int, default=ModelConfig.n_check)
    parser.add_argument("--with_stats_in_output", action="store_true")
    parser.add_argument("--compat_output_file", type=str, default=None)

    parser.add_argument("--log_first_dialogue", action="store_true", help="Print the first generation dialogue prompt")
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    cfg = ModelConfig(
        gen_model_path=args.gen_model_path,
        check_model_path=args.check_model_path,
        tensor_parallel_size_gen=args.tensor_parallel_size_gen,
        tensor_parallel_size_check=args.tensor_parallel_size_check,
        max_model_len_gen=args.max_model_len_gen,
        max_model_len_check=args.max_model_len_check,
        gpu_memory_utilization_gen=args.gpu_memory_utilization_gen,
        gpu_memory_utilization_check=args.gpu_memory_utilization_check,
        temperature_gen=args.temperature_gen,
        temperature_check=args.temperature_check,
        max_output_len=args.max_output_len,
        n_gen=args.n_gen,
        n_check=args.n_check,
    )

    dataset = get_input_data(args.input_file)

    gen_init = init_vllm_and_tokenizer(
        cfg.gen_model_path,
        cfg.tensor_parallel_size_gen,
        cfg.max_model_len_gen,
        cfg.gpu_memory_utilization_gen,
    )
    partial_results = generate_batch(dataset, cfg, gen_env=gen_init, log_first_dialogue=args.log_first_dialogue)
    if partial_results:
        print("[STEP1-FIRST] Generation first record:")
        print(json.dumps(partial_results[0], ensure_ascii=False, indent=2))
    del gen_init
    torch.cuda.empty_cache()

    results = [dict(r) for r in partial_results]
    rounds = max(1, int(args.rounds))
    for ri in range(rounds):
        check_init = init_vllm_and_tokenizer(
            cfg.check_model_path,
            cfg.tensor_parallel_size_check,
            cfg.max_model_len_check,
            cfg.gpu_memory_utilization_check,
        )
        results = check_batch(dataset, results, cfg, check_env=check_init)
        del check_init
        torch.cuda.empty_cache()

        gen2_init = init_vllm_and_tokenizer(
            cfg.gen_model_path,
            cfg.tensor_parallel_size_gen,
            cfg.max_model_len_gen,
            cfg.gpu_memory_utilization_gen,
        )
        results = correct_batch(dataset, results, cfg, gen_env=gen2_init)
        del gen2_init
        torch.cuda.empty_cache()

        if results:
            print(f"[ROUND {ri+1}] First record:")
            print(json.dumps(results[0], ensure_ascii=False, indent=2))

        yes_cnt = sum(1 for r in results if r.get("check_answer") == "YES")
        no_cnt = sum(1 for r in results if r.get("check_answer") == "NO")
        print(f"[ROUND {ri+1} STATS] YES: {yes_cnt}, NO: {no_cnt}")

        out_round = f"{args.output_file}.round{ri+1}.json"
        with open(out_round, "w", encoding="utf-8") as f:
            if args.with_stats_in_output:
                payload = {"results": results, "stats": {"YES": yes_cnt, "NO": no_cnt}}
                f.write(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                f.write(json.dumps(results, indent=2, ensure_ascii=False))

        if args.compat_output_file:
            compat_results: List[Dict[str, Any]] = []
            for item, out in zip(dataset, results):
                compat_results.append({
                    "responses": [out.get("gen_raw", "")],
                    "pred_sql": [out.get("corrected_sql") or out.get("pred_sql") or ""],
                    "question": item.get("question") or item.get("text") or "",
                    "db_id": item.get("db_id"),
                    "gt_sql": item.get("sql")
                })
            compat_round = f"{args.compat_output_file}.round{ri+1}.json"
            with open(compat_round, "w", encoding="utf-8") as f:
                f.write(json.dumps(compat_results, indent=2, ensure_ascii=False))

    yes_cnt = sum(1 for r in results if r.get("check_answer") == "YES")
    no_cnt = sum(1 for r in results if r.get("check_answer") == "NO")
    print(f"[FINAL STATS] YES: {yes_cnt}, NO: {no_cnt}")

    final_prompts = [r.get("last_prompt_str") for r in results if r.get("last_prompt_str")]
    if final_prompts:
        out_prompt_file = f"{args.output_file}.final_prompts.json"
        with open(out_prompt_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(final_prompts, indent=2, ensure_ascii=False))

    with open(args.output_file, "w", encoding="utf-8") as f:
        if args.with_stats_in_output:
            payload = {"results": results, "stats": {"YES": yes_cnt, "NO": no_cnt}}
            f.write(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            f.write(json.dumps(results, indent=2, ensure_ascii=False))

    if args.compat_output_file:
        compat_results: List[Dict[str, Any]] = []
        for item, out in zip(dataset, results):
            compat_results.append({
                "responses": [out.get("gen_raw", "")],
                "pred_sql": [out.get("corrected_sql") or out.get("pred_sql") or ""],
                "question": item.get("question") or item.get("text") or "",
                "db_id": item.get("db_id"),
                "gt_sql": item.get("sql")
            })
        with open(args.compat_output_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(compat_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
