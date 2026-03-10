#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
MODELS_DIR="${MODELS_DIR:-$REPO_ROOT/models}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
OUTPUT_DIR="$REPO_ROOT/outputs/$TIMESTAMP"
EVAL_LOG="$OUTPUT_DIR/eval_results.txt"
mkdir -p "$OUTPUT_DIR"
echo "==== Eval Results ($(date '+%Y-%m-%d %H:%M:%S')) ====" > "$EVAL_LOG"
found_any=false
MODEL_DIR="${MODEL_DIR:-}"

# 指定要运行的模型名称列表
TARGET_MODELS=(
    # "Meta-Llama-3.1-8B-Instruct"
    # "Qwen2.5-Coder-7B-Instruct"
    "Mistral-7B-Instruct-v0.3"
    # "Qwen2.5-Coder-3B-Instruct"
    # "deepseek-coder-6.7b-instruct"
)

if [[ ${#TARGET_MODELS[@]} -gt 0 ]]; then
  model_dirs=()
  for model_name in "${TARGET_MODELS[@]}"; do
    model_dirs+=("$MODELS_DIR/$model_name")
  done
elif [[ -n "$MODEL_DIR" ]]; then
  model_dirs=("$MODEL_DIR")
else
  model_dirs=("$MODELS_DIR"/*/)
fi
for model_dir in "${model_dirs[@]}"; do
  if [[ -d "$model_dir" ]]; then
    found_any=true
    model_name="$(basename "$model_dir")"
    if [[ "$model_name" == Qwen3-* ]]; then
      echo "[SKIP] unsupported model: $model_name" | tee -a "$EVAL_LOG"
      continue
    fi
    model_out_dir="$OUTPUT_DIR/$model_name"
    mkdir -p "$model_out_dir"
    pred_file="$model_out_dir/bird_dev_sql_not_comment_vote8.json"
    echo "[MODEL] $model_name" | tee -a "$EVAL_LOG"
    if ! NL2SQL_CKPT_PATH="$model_dir" OUTPUT_DIR="$model_out_dir" OUTPUT_FILE="$pred_file" GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.9}" MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}" HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 bash "$REPO_ROOT/scripts/infer.sh"; then
      echo "[ERROR] infer failed for $model_name" | tee -a "$EVAL_LOG"
      continue
    fi
    if ! PRED_FILE="$pred_file" bash "$REPO_ROOT/scripts/eval.sh" | tee -a "$EVAL_LOG" | tee "$model_out_dir/eval.txt" > /dev/null; then
      echo "[ERROR] eval failed for $model_name" | tee -a "$EVAL_LOG"
      continue
    fi
    echo "" | tee -a "$EVAL_LOG"
  fi
done
if [[ "$found_any" == false ]]; then
  echo "No models found under $MODELS_DIR"
  exit 1
fi
