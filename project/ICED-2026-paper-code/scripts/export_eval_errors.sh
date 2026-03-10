#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

if command -v conda >/dev/null 2>&1; then
  . "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate vllm_env
else
  echo "conda not found; please activate vllm_env manually" >&2
fi

if [[ "${CONDA_DEFAULT_ENV:-}" != "vllm_env" ]]; then
  echo "conda env vllm_env is required" >&2
  exit 1
fi

PRED_FILE="${PRED_FILE:-$REPO_ROOT/outputs/Qwen2.5-Coder-7B-Instruct/bird_dev_sql_comment_vote8.json}"
GOLD_FILE="${GOLD_FILE:-$REPO_ROOT/data/bird/dev.json}"
DB_PATH="${DB_PATH:-$REPO_ROOT/data/bird/dev_databases}"
OUT_FILE="${OUT_FILE:-}"

if [[ ! -f "$PRED_FILE" ]]; then echo "Missing pred file: $PRED_FILE"; exit 1; fi
if [[ ! -f "$GOLD_FILE" ]]; then echo "Missing gold file: $GOLD_FILE"; exit 1; fi
if [[ ! -d "$DB_PATH" ]]; then echo "Missing db path: $DB_PATH"; exit 1; fi

if [[ -n "$OUT_FILE" ]]; then
  python "$REPO_ROOT/export_eval_errors.py" --pred "$PRED_FILE" --gold "$GOLD_FILE" --db_path "$DB_PATH" --out_file "$OUT_FILE"
else
  python "$REPO_ROOT/export_eval_errors.py" --pred "$PRED_FILE" --gold "$GOLD_FILE" --db_path "$DB_PATH"
fi

