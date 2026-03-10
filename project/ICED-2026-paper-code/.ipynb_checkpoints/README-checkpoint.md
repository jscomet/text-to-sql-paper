DatA-SQL Pipeline - Prebuilt datasets and model on HF: [Huggingface](https://huggingface.co/Chinastark)

This folder contains a self-contained, config-driven pipeline for DatA-SQL.

Environment (minimal)
- vllm==0.8.3
- func_timeout (e.g., >= 4.3.5)

Table of Contents
- What's Inside
- Templates (no imports needed)
- Paths & Privacy
- Stage 1 - Data Generation
- Prebuilt Datasets (HuggingFace)
- Training (LLaMAFactory)
- Stage 2 - Final Inference
- Common Flags
- Step Reference
- Tips
- Troubleshooting

What's Inside
- pipeline.py - Orchestrates steps via YAML configs (no external imports for templates)
- config_data.yaml - Stage 1 (data generation with a strong base model)
- config_infer.yaml - Stage 2 (final inference with your trained model)
- config.yaml - General config (you can copy patterns from the above two)
- Core modules: infer.py, evaluate_bird.py, prepare_sft_datasets.py, construct_for_schema.py, construct_sft.py, process_pred_sql.py, minihash.py, build_contens_index.py, utils/db_utils.py, utils/bridge_content_encoder.py

Templates (no imports needed)
- Templates are defined and applied inside infer.py (ported from evaluation/infer.py).
- You choose templates by name; the pipeline just passes the name to infer:
  - gen (recommended for Stage 1 generation)
  - infer (recommended for Stage 2 inference)

Paths & Privacy
- All examples use placeholders like /path/to/... to avoid exposing local paths. Replace them with your own.

Stage 1 - Data Generation (32B base, build SFT)
1) Edit config_data.yaml:
   - paths.dataset_root: /path/to/data/bird
   - inference.model_path: /path/to/base-32B-model
   - inference.generator.prompt_template: gen
2) Run (choose the steps you need) from this folder:
   - python pipeline.py --config config_data.yaml --steps hash,schema,infer,categorize,train_sync
   - Outputs (examples):
     - outputs/generator_out.json - raw candidates
     - outputs/sft_data_Alpaca.json - SFT for training
     - data/correct_bird_trainset/train.json - synced for LLaMAFactory

Prebuilt Datasets (HuggingFace)
- To simplify reproduction, we also provide the generated SFT datasets on HuggingFace:
  - Link: [huggingface](https://huggingface.co/Chinastark)
- You can download and use them directly for training (e.g., save as data/correct_bird_trainset/train.json, or point your trainer to the downloaded JSON).

Training (LLaMAFactory WebUI)
- Use your project's training config (e.g., train/config.yaml)
- Key LoRA params (see root README): lora_target, lora_rank, lora_alpha, cutoff_len, batch_size, grad_accum, lr, epochs
- Launch (example):
  - llamafactory-cli webui
  - The relevant parameters is mention in our paper.

Stage 2 - Final Inference (use trained model)
1) Edit config_infer.yaml:
   - paths.dataset_root: /path/to/data/bird
   - inference.model_path: /path/to/DatA-SQL-trained
   - inference.generator.prompt_template: infer
2) Run final inference and evaluation (from this folder):
   - python pipeline.py --config config_infer.yaml --steps schema,infer,eval
   - Outputs (examples):
     - outputs_infer/generator_out.json - final predictions
     - Console will print EX accuracy (major voting)

Common Flags (in YAML)
- inference.n: number of sampled responses per question (e.g., 8)
- inference.temperature: sampling temperature
- evaluation.mode: major_voting or greedy_search
- categorize_sft.length_filter: filter prompts by tokenizer length (default <= 6144)

Step Reference
- bm25 (optional): build BM25 content index per DB (pyserini)
- prepare: build SFT data with evidence
- hash: discover FK candidates with MinHash
- schema: convert schema JSON to readable create_format
- infer: run vLLM with chosen template (via name)
- categorize: execute results, split correctness, build SFT (and Alpaca)
- train_sync: copy SFT JSON to LLaMAFactory data dir
- eval: compute EX (greedy or major voting)

Tips
- Long runs: increase GPU parallelism via tensor_parallel_size and keep n moderate
- Major voting can be heavy; start with small n to validate the pipeline

Troubleshooting
- If infer complains about templates: ensure templates block maps your logical names to infer.py's real names
- If evaluate fails: confirm paths.dev.db_dir and gold_json are correct (and DBs are <db_id>/<db_id>.sqlite)
- If tokenizer length is exceeded: use mix_data or enable categorize_sft.length_filter

