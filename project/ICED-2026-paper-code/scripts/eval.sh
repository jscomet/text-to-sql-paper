#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
# PRED_FILE="${PRED_FILE:-$REPO_ROOT/outputs/bird_dev_sql_not_comment_vote8.json}"
PRED_FILE="${PRED_FILE:-$REPO_ROOT/outputs/Qwen2.5-Coder-7B-Instruct/bird_dev_sql_comment_vote8.json}"
GOLD_FILE="${GOLD_FILE:-$REPO_ROOT/data/bird/dev.json}"
DB_PATH="${DB_PATH:-$REPO_ROOT/data/bird/dev_databases}"
if [[ ! -f "$PRED_FILE" ]]; then echo "Missing pred file: $PRED_FILE"; exit 1; fi
if [[ ! -f "$GOLD_FILE" ]]; then echo "Missing gold file: $GOLD_FILE"; exit 1; fi
if [[ ! -d "$DB_PATH" ]]; then echo "Missing db path: $DB_PATH"; exit 1; fi

# derive per-model eval output directory
MODEL_NAME="$(basename "$(dirname "$PRED_FILE")")"
if [[ "$MODEL_NAME" == "outputs" ]]; then MODEL_NAME="default"; fi
python "$REPO_ROOT/evaluate_bird.py" \
  --pred "$PRED_FILE" \
  --gold "$GOLD_FILE" \
  --db_path "$DB_PATH" \
  --mode major_voting 
