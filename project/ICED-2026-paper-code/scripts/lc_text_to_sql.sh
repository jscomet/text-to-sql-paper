#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Model paths (can be overridden via env)
GEN_MODEL_PATH="${GEN_MODEL_PATH:-$REPO_ROOT/models/Qwen2.5-Coder-32B-Instruct}"
# CHECK_MODEL_PATH="/share/home/tm902089733300000/a902092450/zhiliang/code/Pre-train/logs/Diss_train_3B_stage2/merged_model_SATGE2_400_steps"
CHECK_MODEL_PATH="${CHECK_MODEL_PATH:-$REPO_ROOT/models/Qwen2.5-Coder-32B-Instruct}"
# CHECK_MODEL_PATH="${CHECK_MODEL_PATH:-$REPO_ROOT/models/Chinastark-Diss}"

# Input data (default to the same pattern used in infer.sh)

INPUT_FILE="${INPUT_FILE:-$REPO_ROOT/data/bird/bird_dev.json}"
# INPUT_FILE="${INPUT_FILE:-$REPO_ROOT/outputs/bird_dev.generated.json}"

# Output directory and files
GEN_MODEL_NAME="$(basename "$GEN_MODEL_PATH")"
DEFAULT_OUTPUT_DIR="$REPO_ROOT/outputs/$GEN_MODEL_NAME"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT_DIR}"
mkdir -p "$OUTPUT_DIR"

# Main pipeline output (rich results + stats optional)
OUTPUT_FILE="${OUTPUT_FILE:-$OUTPUT_DIR/pipeline_results.json}"

# Compatibility output for downstream checks
COMPAT_OUTPUT_FILE="${COMPAT_OUTPUT_FILE:-$OUTPUT_DIR/bird_dev_sql_comment_vote8.json}"

# Build arguments array to allow conditional flags
ARGS=(
  "$REPO_ROOT/lc_text_to_sql_pipeline.py"
  --input_file "$INPUT_FILE"
  --output_file "$OUTPUT_FILE"
  --gen_model_path "$GEN_MODEL_PATH"
  --check_model_path "$CHECK_MODEL_PATH"
  --tensor_parallel_size_gen "${TENSOR_PARALLEL_SIZE_GEN:-2}"
  --tensor_parallel_size_check "${TENSOR_PARALLEL_SIZE_CHECK:-2}"
  --max_model_len_gen "${MAX_MODEL_LEN_GEN:-32768}"
  --max_model_len_check "${MAX_MODEL_LEN_CHECK:-32768}"
  --gpu_memory_utilization_gen "${GPU_MEMORY_UTILIZATION_GEN:-0.95}"
  --gpu_memory_utilization_check "${GPU_MEMORY_UTILIZATION_CHECK:-0.95}"
  --temperature_gen "${TEMPERATURE_GEN:-0.8}"
  --temperature_check "${TEMPERATURE_CHECK:-0.8}"
  --n_gen "${N_GEN:-1}"
  --n_check "${N_CHECK:-1}"
  --rounds "${ROUNDS:-5}"
  --compat_output_file "$COMPAT_OUTPUT_FILE"
)

# Optional flags
if [[ "${LOG_FIRST_DIALOGUE:-}" == "1" || "${LOG_FIRST_DIALOGUE:-}" == "true" ]]; then
  ARGS+=(--log_first_dialogue)
fi

if [[ "${WITH_STATS_IN_OUTPUT:-}" == "1" || "${WITH_STATS_IN_OUTPUT:-}" == "true" ]]; then
  ARGS+=(--with_stats_in_output)
fi

# 允许覆盖模型配置中的 max_model_len 上限（请确保显存充足）
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1

python "${ARGS[@]}"
