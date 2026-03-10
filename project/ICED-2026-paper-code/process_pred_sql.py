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

evaluation_results = []
random.seed(42)
import sqlite3


def compare_sql(question_id, db_file, question, response, ground_truth, pred_sql, prompt):
    """
    correctness = 0 琛ㄧず棰勬祴缁撴灉閿欎簡
    correctness = 1 琛ㄧず棰勬祴姝ｇ‘
    correctness = 2 琛ㄧず pred_sql 鏈夐敊璇?    correctness = 3 琛ㄧず ground_truth 鎵ц閿欒锛堝嵆涓嶅悎娉曪級
    """
    correctness = 0
    error_msg = ""
    conn = None
    if question_id % 1000 == 0 : print("exec idx:", question_id)
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION;")
        # 灏濊瘯鎵ц ground_truth SQL
        try:
            cursor.execute(ground_truth)
            ground_truth_res = cursor.fetchall()
        except Exception as e:
            correctness = 3
            error_msg = str(e)
            conn.rollback()
            return question_id, db_file, question, response, ground_truth, pred_sql, prompt, correctness, error_msg
        # 灏濊瘯鎵ц pred_sql
        try:
            cursor.execute(pred_sql)
            pred_res = cursor.fetchall()
            if set(pred_res) == set(ground_truth_res):
                correctness = 1
        except Exception as e:
            correctness = 2
            error_msg = str(e)
        conn.rollback()
    except Exception as outer_e:
        correctness = 4
        print(db_file)
        error_msg = f"DB connection error: {str(outer_e)}"
        print(error_msg)
    finally:
        conn.close()
    return question_id, db_file, question, response, ground_truth, pred_sql, prompt, correctness, error_msg
def compare_sql_wrapper(args, timeout):
    '''Wrap execute_sql for timeout'''
    try:
        result = func_timeout(timeout, compare_sql, args=args)
    except KeyboardInterrupt:
        sys.exit(0)
    except FunctionTimedOut:
        result = (*args, 0, "Time Out")
    except Exception as e:
        result = (*args, 0, str(e))
        print(args[0],0,"Unknow error")
    return result

def execute_callback_evaluate_sql(result):
    '''Store the execution result in the collection'''
    idx, db_file, question, response, ground_truth, pred_sql, prompt, correctness, error_msg = result

    record = {
        "idx": idx,
        "db_file": db_file,
        "question": question,
        "ground_truth": ground_truth,
        "pred_sql": pred_sql,
        "response": response,
        "correctness": correctness,
        "error_msg": error_msg, 
        "prompt": prompt
    }
    evaluation_results.append(record)
    if len(evaluation_results) % 5000 == 0:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(evaluation_results, f, ensure_ascii=False, indent=4)
    sys.stdout.flush()
    sys.stderr.flush()

def evaluate_sqls_parallel(db_files, questions, responses, pred_sqls, ground_truth_sqls, prompts,  num_cpus=1, timeout=1):
    '''Execute the sqls in parallel'''
    """ground_truth_sqls shape 鏄拰predsqls鏄竴鏍风殑"""
    print(len(db_files))
    pool = mp.Pool(processes=num_cpus)
    for idx, (db_file, question, response, pred_sql, ground_truth, prompt) in enumerate(zip(db_files, questions, responses, pred_sqls, ground_truth_sqls, prompts)):
        pool.apply_async(compare_sql_wrapper, args=((idx, db_file, question, response, ground_truth, pred_sql, prompt), timeout),callback=execute_callback_evaluate_sql)
    pool.close()
    pool.join()


def run_process(gold_file, pred_file, db_path, save_pred_sqls, num_cpus=128, timeout=30):
    global evaluation_results
    global output_path
    output_path = save_pred_sqls
    gold = json.load(open(gold_file, encoding='utf-8'))
    pred_results = json.load(open(pred_file, encoding='utf-8'))

    pred_sql_key = "pred_sql"
    db_files = []
    gt_sqls = []
    pred_sqls = []
    questions = []
    responses = []

    # 寤虹珛 gold 鐨?question -> gold_data 鐨勬槧灏勶紙缁熶竴灏忓啓 & strip锛岄伩鍏嶅尮閰嶅け璐ワ級
    gold_map = {
        item["question"].replace("\n", " ").lower(): item
        for item in gold
    }

    missing_questions = []
    prompts = []
    for pred_result in pred_results:
        question = pred_result["question"].replace("\n", " ").lower()
        if question not in gold_map:
            print("miss:", question)
            continue

        gold_data = gold_map[question]
        sampling_num = len(pred_result[pred_sql_key])

        db_files.extend([os.path.join(db_path, gold_data["db_id"], gold_data["db_id"] + ".sqlite")] * sampling_num)
        if "SQL" not in gold_data:
            gt_sqls.extend([gold_data['query']] * sampling_num)
        else:
            gt_sqls.extend([gold_data['SQL']] * sampling_num)
        
        pred_sqls.extend(pred_result[pred_sql_key])
        questions.extend([gold_data["question"]] * sampling_num)
        responses.extend(pred_result['responses'])
        # print(pred_result.keys())
        if pred_result.get('prompt', "") == "" :
            if len(prompts) == 0:
                print("=" * 10, "no prompt ", "=" * 10 )
            prompts.extend([""] * sampling_num)
        else:
            prompts.extend([pred_result['prompt']] * sampling_num)

    print(f"sampling_num (from first example): {len(pred_results[0][pred_sql_key])}")
    print(f"Total samples processed: {len(pred_sqls)}")

    if missing_questions:
        print(f"Warning: {len(missing_questions)} questions in pred_results not found in gold file.")

    # 鍙€? 鍔犱笂 sanity check
    assert len(db_files) == len(gt_sqls) == len(pred_sqls) == len(questions) == len(responses)
    evaluate_sqls_parallel(db_files, questions, responses, pred_sqls, gt_sqls, prompts, num_cpus, timeout)
    print("finish")
    with open(save_pred_sqls, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, ensure_ascii=False, indent=4)


def parse_option():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pred', type = str, default = "predict_dev.json")
    parser.add_argument('--gold', type = str, default = "./bird/dev/dev.json")
    parser.add_argument('--db_path', type = str, default = "./bird/dev/dev_databases")
    parser.add_argument('--save_pred_sqls', type = str, default = None)
    parser.add_argument('--nums_cpu', type = int, default = 8)
    parser.add_argument('--timeout', type = int, default = 30)

    opt = parser.parse_args()

    return opt

if __name__ == "__main__":
    opt = parse_option()
    run_process(opt.gold, opt.pred, opt.db_path, opt.save_pred_sqls, num_cpus=opt.nums_cpu, timeout=opt.timeout)
    # import os
    # os.system("/usr/bin/shutdown")

    """
    杩欓噷鏄妸妯″瀷鎺ㄧ悊鐨勬暟鎹繚瀛樹笅鏉ワ紙maj鎶曠エ鏈哄埗鐨勬暟鎹級
    python process_pred_sql.py \
      --pred /root/autodl-tmp/humansql_data/eval_result/Qwen2.5-Coder-7B-Instruct_out_OmniSQL-7B-maj.json \
      --gold /root/autodl-fs/OmniSQL-datasets/data/bird/dev_20240627/dev.json \
      --db_path /root/autodl-fs/OmniSQL-datasets/data/bird/dev_20240627/dev_databases \
      --nums_cpu 8 \
      --save_pred_sqls /root/autodl-tmp/humansql_data/eval_result/res.json
    
    /root/autodl-tmp/humansql_data/eval_result/Qwen2.5-Coder-3B-Instruct_out_grpo_stage3_grpo_maj.json
    /root/autodl-tmp/humansql_data/eval_result/Qwen2.5-Coder-32B-Instruct_out_intcorrect_train_data_get.json
    python process_pred_sql.py \
      --pred /root/autodl-fs/tmp/Qwen2.5-Coder-7B-Instruct_out_Model-7B-spider-train.json \
      --gold /root/autodl-fs/data/spider_data/train_merged.json \
      --db_path /root/autodl-tmp/database/train_spider/database \
      --nums_cpu 32 \
      --save_pred_sqls /root/autodl-fs/tmp/Model7Bmaj_results.json

    python process_pred_sql.py \
      --pred /root/autodl-tmp/humansql_data/eval_result/Qwen2.5-Coder-32B-Instruct_out_intcorrect_train_data_get.json \
      --gold /root/autodl-fs/OmniSQL-datasets/data/bird/train/train.json \
      --db_path /root/autodl-fs/OmniSQL-datasets/data/bird/train/train_databases \
      --nums_cpu 15 \
      --save_pred_sqls /root/autodl-tmp/humansql_data/eval_result/incorrect_data/res_32B.json

    python process_pred_sql.py \
      --pred /root/autodl-tmp/data/Qwen2.5-Coder-3B-Instruct_out_grpo_stage3_maj.json \
      --gold /root/autodl-fs/OmniSQL-datasets/data/bird/dev_20240627/dev.json \
      --db_path /root/autodl-tmp/database_dev/dev_databases  \
      --nums_cpu 32 \
      --save_pred_sqls res_dev_3B.json

    python process_pred_sql.py \
      --pred /root/autodl-fs/tmp/Qwen2.5-Coder-3B-Instruct_out_stage2_1_mid_step.json \
      --gold /root/autodl-fs/data/bird/dev_20240627/dev.json \
      --db_path /root/autodl-fs/data/bird/dev_20240627/dev_databases \
      --nums_cpu 32 \
      --save_pred_sqls /root/autodl-fs/tmp/res_stage2_1_mid_step_maj.json
    
    python process_pred_sql.py \
      --pred /root/autodl-fs/tmp/Qwen2.5-Coder-3B-Instruct_out_stage_2_1_midstep_bird_train.json \
      --gold /root/autodl-fs/data/bird/train/train.json \
      --db_path /root/autodl-fs/data/bird/train/train_databases \
      --nums_cpu 32 \
      --save_pred_sqls /root/autodl-fs/tmp/stage_2_1_midstep_bird/res_stage2_1_mid_step_maj.json

    

    python /root/autodl-fs/humansql_code/eval/evaluate_bird.py \
      --pred  /root/autodl-fs/tmp/Qwen2.5-Coder-3B-Instruct_out_models_60step_0814.json   \
      --gold  /root/autodl-fs/data/bird/dev_20240627/dev.json\
      --db_path /root/autodl-fs/data/bird/dev_20240627/dev_databases \
      --mode major_voting

    python process_pred_sql.py \
      --pred /root/autodl-fs/tmp/correct_output_base_8_maj_8.json \
      --gold /root/autodl-fs/data/bird/dev_20240627/dev.json \
      --db_path /root/autodl-tmp/database/dev_databases \
      --nums_cpu 32 \
      --save_pred_sqls /root/autodl-tmp/correct_results_base_8_8_correct.json
    """


