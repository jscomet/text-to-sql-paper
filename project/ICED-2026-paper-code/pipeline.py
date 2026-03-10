import argparse
import os
import sys
import json
import glob
import subprocess
from typing import Any, Dict


def _read_yaml(path: str) -> Dict[str, Any]:
    import yaml
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _lookup(cfg: Dict[str, Any], dotted: str) -> Any:
    cur = cfg
    for part in dotted.split('.'):
        if part not in cur:
            raise KeyError(f"Config reference not found: {dotted}")
        cur = cur[part]
    return cur


def _resolve_placeholders(cfg: Dict[str, Any]) -> Dict[str, Any]:
    import re

    def repl(val: str) -> str:
        # Replace ${a.b.c} with value from cfg
        def sub_fn(m):
            key = m.group(1)
            v = _lookup(cfg, key)
            return str(v)

        return re.sub(r"\$\{([^}]+)\}", sub_fn, val)

    def walk(x):
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, str):
            return repl(x)
        return x

    return walk(cfg)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def step_bm25_index(cfg: Dict[str, Any]):
    if not cfg.get('bm25_index', {}).get('enabled', False):
        return
    threads = int(cfg['bm25_index'].get('threads', 16))

    # Import builder functions
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
    from build_contens_index import build_content_index, remove_contents_of_a_folder

    for split in ['train', 'dev']:
        db_dir = cfg['paths'][split]['db_dir']
        index_base = cfg['paths'][split]['db_index_dir']
        ensure_dir(index_base)
        # Clear existing indices
        remove_contents_of_a_folder(index_base)

        # Build an index per db_id
        for db_id in os.listdir(db_dir):
            if db_id.endswith('.json'):
                continue
            db_path = os.path.join(db_dir, db_id, f"{db_id}.sqlite")
            if not os.path.isfile(db_path):
                continue
            out_index = os.path.join(index_base, db_id)
            ensure_dir(out_index)
            print(f"[BM25] Building index for {db_id} -> {out_index}")
            # build_content_index internally shells out to pyserini
            build_content_index(db_path, out_index)


def step_prepare_sft(cfg: Dict[str, Any]):
    if not cfg.get('prepare_sft', {}).get('enabled', False):
        return
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
    from prepare_sft_datasets import spider_style_dataset

    # Train
    print("[SFT] Preparing train with evidence...")
    train_data = spider_style_dataset(
        dataset_path=cfg['paths']['train']['dataset_json'],
        db_path=cfg['paths']['train']['db_dir'],
        db_content_index_path=cfg['paths']['train']['db_index_dir'],
        source=cfg['prepare_sft'].get('train_source', 'bird-train'),
        table_json_path=cfg['paths']['train']['tables_json'],
        use_evidence=bool(cfg['prepare_sft'].get('use_evidence', True)),
        mode='train'
    )
    ensure_dir(os.path.dirname(cfg['prepare_sft']['train_out']))
    with open(cfg['prepare_sft']['train_out'], 'w', encoding='utf-8') as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)

    # Dev
    print("[SFT] Preparing dev with evidence...")
    dev_data = spider_style_dataset(
        dataset_path=cfg['paths']['dev']['dataset_json'],
        db_path=cfg['paths']['dev']['db_dir'],
        db_content_index_path=cfg['paths']['dev']['db_index_dir'],
        source=cfg['prepare_sft'].get('dev_source', 'bird_dev_20240627'),
        table_json_path=cfg['paths']['dev']['tables_json'],
        use_evidence=bool(cfg['prepare_sft'].get('use_evidence', True)),
        mode='dev'
    )
    with open(cfg['prepare_sft']['dev_out'], 'w', encoding='utf-8') as f:
        json.dump(dev_data, f, indent=2, ensure_ascii=False)


def step_minhash(cfg: Dict[str, Any]):
    if not cfg.get('minhash', {}).get('enabled', False):
        return
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
    import minihash as mh

    workers = int(cfg['minhash'].get('workers', 32))

    def process_dir(db_dir: str, out_dir: str):
        ensure_dir(out_dir)
        sqlite_files = glob.glob(os.path.join(db_dir, '**', '*.sqlite'), recursive=True)
        print(f"[MinHash] Found {len(sqlite_files)} sqlite files under {db_dir}")
        for db_path in sqlite_files:
            print(f"[MinHash] {db_path}")
            res = mh.find_foreign_key_candidates(db_path)
            if not res:
                continue
            potential, same = res
            base = os.path.splitext(os.path.basename(db_path))[0]
            out_path = os.path.join(out_dir, f"{base}.json")
            mh.save_candidates_json(db_path, potential, same, out_path)

    process_dir(cfg['paths']['train']['db_dir'], cfg['minhash']['out_train_dir'])
    process_dir(cfg['paths']['dev']['db_dir'], cfg['minhash']['out_dev_dir'])


def step_construct_schema(cfg: Dict[str, Any]):
    if not cfg.get('construct_schema', {}).get('enabled', False):
        return
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
    import types
    from construct_for_schema import convert_json_to_structured_text_json

    # Train
    class Args:  # simple container
        pass
    a = Args()
    a.input_path = cfg['prepare_sft']['train_out']
    a.output_path = cfg['construct_schema']['train_out']
    a.data_with_difficult_path = None
    a.similarity_info_dir = cfg['minhash']['out_train_dir'] if cfg['construct_schema'].get('inject_train_similarities', True) else 'xxx'
    a.sim_desc = False
    a.mode = 'train'
    a.schema_data = None
    ensure_dir(os.path.dirname(a.output_path))
    print("[Schema] Converting train to create_format...")
    convert_json_to_structured_text_json(a)

    # Dev
    b = Args()
    b.input_path = cfg['prepare_sft']['dev_out']
    b.output_path = cfg['construct_schema']['dev_out']
    b.data_with_difficult_path = None
    b.similarity_info_dir = 'xxx'
    b.sim_desc = False
    b.mode = 'dev'
    b.schema_data = None
    print("[Schema] Converting dev to create_format...")
    convert_json_to_structured_text_json(b)


def _run_infer(input_file: str, output_file: str, model_path: str, tps: int, n: int, temp: float, out_fmt: str, template: str, metadata: str = None, mix_data: str = None):
    infer_script = os.path.join(os.path.dirname(__file__), 'infer.py')
    cmd = [
        sys.executable, infer_script,
        '--nl2sql_ckpt_path', model_path,
        '--input_file', input_file,
        '--output_file', output_file,
        '--tensor_parallel_size', str(tps),
        '--n', str(n),
        '--temperature', str(temp),
        '--output_format', out_fmt,
        '--prompt_template', template
    ]
    if metadata:
        cmd.extend(['--metadata', metadata])
    if mix_data:
        cmd.extend(['--mix_data', mix_data])
    print('[Infer] ' + ' '.join(cmd))
    subprocess.check_call(cmd)


def step_inference(cfg: Dict[str, Any]):
    if not cfg.get('inference', {}).get('enabled', False):
        return
    inf = cfg['inference']
    model_path = inf['model_path']
    tps = int(inf.get('tensor_parallel_size', 1))
    n = int(inf.get('n', 8))
    temp = float(inf.get('temperature', 0.8))
    out_fmt = inf.get('output_format', 'sql')
    metadata = inf.get('metadata')
    mix_data = inf.get('mix_data')
    # Optional template indirection
    templates = cfg.get('templates', {})

    # Generator
    gen = inf['generator']
    gen_template = gen.get('prompt_template', 'infer')
    if gen_template in templates:
        gen_template = templates[gen_template]
    _run_infer(gen['input_json'], gen['output_json'], model_path, tps, n, temp, out_fmt, gen_template, metadata, mix_data)

    # Corrector (optional)
    corr = inf.get('corrector', {})
    if corr.get('enabled', False):
        corr_template = corr.get('prompt_template', 'sql_correct_prompt')
        if corr_template in templates:
            corr_template = templates[corr_template]
        _run_infer(corr['input_json'], corr['output_json'], model_path, tps, n, temp, out_fmt, corr_template, metadata, mix_data)


def step_categorize_sft(cfg: Dict[str, Any]):
    if not cfg.get('categorize_sft', {}).get('enabled', False):
        return

    # 1) Evaluate predictions and annotate correctness
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
    import process_pred_sql

    predictions_json = cfg['categorize_sft']['predictions_json']
    gold = cfg['paths']['dev']['dataset_json']
    db_dir = cfg['paths']['dev']['db_dir']
    eval_out = os.path.join(cfg['paths']['work_dir'], 'generator_eval.json')
    ensure_dir(os.path.dirname(eval_out))
    print("[Eval] Computing correctness for predictions (dev)...")
    process_pred_sql.run_process(gold, predictions_json, db_dir, eval_out, num_cpus=8, timeout=30)

    # 2) Split into correct, error, mismatch by correctness
    from types import SimpleNamespace
    from construct_sft import catgory, get_sft, for_llama

    args = SimpleNamespace()
    args.input_file = eval_out
    args.out1 = cfg['categorize_sft']['correct_json']
    args.out2 = cfg['categorize_sft']['error_json']
    args.out3 = cfg['categorize_sft']['mismatch_json']
    print("[SFT] Splitting predictions by correctness...")
    catgory(args)

    # 3) Build SFT prompts for generator
    sft_args = SimpleNamespace()
    sft_args.out1 = cfg['categorize_sft']['correct_json']
    sft_args.out2 = cfg['categorize_sft']['prompt_source_json']
    sft_args.out3 = cfg['categorize_sft']['sft_correct_json']
    print("[SFT] Composing SFT prompts for generator...")
    get_sft(sft_args)

    # 4) Convert SFT to Alpaca format
    alp_args = SimpleNamespace()
    alp_args.out1 = cfg['categorize_sft']['sft_correct_json']
    alp_args.out2 = cfg['categorize_sft']['sft_alpaca_json']
    print("[SFT] Converting SFT to Alpaca format...")
    for_llama(alp_args)

    # 5) Optional: length filter by prompt tokens (<= max_prompt_tokens)
    lf_cfg = cfg['categorize_sft'].get('length_filter', {})
    if lf_cfg.get('enabled', False):
        try:
            from transformers import AutoTokenizer
            tokenizer_path = lf_cfg.get('tokenizer_path') or cfg.get('inference', {}).get('model_path')
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)

            # Filter SFT JSON (prompt/response)
            with open(cfg['categorize_sft']['sft_correct_json'], 'r', encoding='utf-8') as f:
                sft_data = json.load(f)
            filtered = []
            for item in sft_data:
                prompt = item.get('prompt', '')
                if len(tokenizer(prompt)['input_ids']) <= int(lf_cfg.get('max_prompt_tokens', 6144)):
                    filtered.append(item)
            with open(lf_cfg['out_correct_json'], 'w', encoding='utf-8') as f:
                json.dump(filtered, f, ensure_ascii=False, indent=2)
            print(f"[SFT] Length-filtered (<= {lf_cfg.get('max_prompt_tokens', 6144)}) correct SFT: {len(filtered)} items")

            # Filter Alpaca JSON (instruction as prompt)
            with open(cfg['categorize_sft']['sft_alpaca_json'], 'r', encoding='utf-8') as f:
                alp_data = json.load(f)
            filtered_alp = []
            for item in alp_data:
                instr = item.get('instruction', '')
                if len(tokenizer(instr)['input_ids']) <= int(lf_cfg.get('max_prompt_tokens', 6144)):
                    filtered_alp.append(item)
            with open(lf_cfg['out_alpaca_json'], 'w', encoding='utf-8') as f:
                json.dump(filtered_alp, f, ensure_ascii=False, indent=2)
            print(f"[SFT] Length-filtered Alpaca: {len(filtered_alp)} items")
        except Exception as e:
            print(f"[SFT] Length filtering skipped due to error: {e}")


def step_evaluation(cfg: Dict[str, Any]):
    if not cfg.get('evaluation', {}).get('enabled', False):
        return
    mode = cfg['evaluation'].get('mode', 'major_voting')
    gold_json = cfg['evaluation']['gold_json']
    pred_json = cfg['evaluation']['pred_json']
    db_dir = cfg['evaluation']['db_dir']

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from new_code.evaluate_bird import run_eval
    print(f"[Eval] Running evaluation mode={mode}...")
    acc, _ = run_eval(gold_json, pred_json, db_dir, mode, True)
    print(f"[Eval] Accuracy: {acc:.4f}")


def step_training_sync(cfg: Dict[str, Any]):
    ts = cfg.get('training_sync', {})
    if not ts or not ts.get('enabled', False):
        return
    prefer_filtered = bool(ts.get('prefer_filtered', True))
    src_default = ts.get('src_default')
    src_filtered = ts.get('src_filtered')
    src = None
    if prefer_filtered and src_filtered and os.path.isfile(src_filtered):
        src = src_filtered
    elif src_default and os.path.isfile(src_default):
        src = src_default
    if not src:
        print('[TrainSync] No source SFT JSON found to copy.')
        return
    dest_dir = ts.get('dest_dir', 'data/correct_bird_trainset')
    dest_file = ts.get('dest_file') or os.path.join(dest_dir, 'train.json')
    ensure_dir(dest_dir)
    import shutil
    shutil.copyfile(src, dest_file)
    print(f"[TrainSync] Copied {src} -> {dest_file}")

def main():
    parser = argparse.ArgumentParser(description='ICDE2026 config-driven data pipeline')
    parser.add_argument('--config', type=str, default='new_code/config.yaml')
    parser.add_argument('--steps', type=str, default='all', help='Comma separated steps or "all". Steps: bm25,prepare,hash,schema,infer,categorize,eval')
    args = parser.parse_args()

    cfg = _resolve_placeholders(_read_yaml(args.config))
    ensure_dir(cfg['paths']['work_dir'])

    # Default 'all' covers data prep and training data sync only.
    # After training is finished, run a second pass with steps like: infer,categorize,eval
    steps = [s.strip() for s in args.steps.split(',')] if args.steps != 'all' else ['bm25', 'prepare', 'hash', 'schema', 'train_sync']

    if 'bm25' in steps:
        step_bm25_index(cfg)
    if 'prepare' in steps:
        step_prepare_sft(cfg)
    if 'hash' in steps:
        step_minhash(cfg)
    if 'schema' in steps:
        step_construct_schema(cfg)
    if 'train_sync' in steps:
        step_training_sync(cfg)
    if 'infer' in steps:
        step_inference(cfg)
    if 'categorize' in steps:
        step_categorize_sft(cfg)
    if 'eval' in steps:
        step_evaluation(cfg)


if __name__ == '__main__':
    main()










