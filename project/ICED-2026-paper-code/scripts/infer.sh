#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
NL2SQL_CKPT_PATH="${NL2SQL_CKPT_PATH:-$REPO_ROOT/models/qwen-coder-3b}"
INPUT_FILE="${INPUT_FILE:-$REPO_ROOT/outputs/bird_dev.generated.json}"
# INPUT_FILE="${INPUT_FILE:-$REPO_ROOT/data/bird/bird_dev.json}"
MODEL_NAME="$(basename "$NL2SQL_CKPT_PATH")"
DEFAULT_OUTPUT_DIR="$REPO_ROOT/outputs/$MODEL_NAME"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT_DIR}"
# OUTPUT_FILE="${OUTPUT_FILE:-$OUTPUT_DIR/bird_dev_sql_not_comment_vote8.json}"
OUTPUT_FILE="${OUTPUT_FILE:-$OUTPUT_DIR/bird_dev_sql_vote8.json}"
mkdir -p "$OUTPUT_DIR"
python "$REPO_ROOT/infer.py" \
  --nl2sql_ckpt_path "$NL2SQL_CKPT_PATH" \
  --input_file "$INPUT_FILE" \
  --output_file "$OUTPUT_FILE" \
  --tensor_parallel_size "${TENSOR_PARALLEL_SIZE:-2}" \
  --n "${N:-1}" \
  --temperature "${TEMPERATURE:-0.8}" \
  --output_format sql \
  --prompt_key xxx \
  --mix_data "$REPO_ROOT/data/bird/dev.json" \
  --gpu_memory_utilization "${GPU_MEMORY_UTILIZATION:-0.9}" \
  --max_model_len "${MAX_MODEL_LEN:-8192}"
