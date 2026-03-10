#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

INPUT_PATH="${INPUT_PATH:-$REPO_ROOT/data/bird/sft_bird_evidence_dev_text2sql.json}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/outputs}"
OUTPUT_FILE="${OUTPUT_FILE:-$OUTPUT_DIR/bird_dev.generated.json}"
DATA_WITH_DIFFICULT_PATH="${DATA_WITH_DIFFICULT_PATH:-$REPO_ROOT/data/bird/dev.json}"
SIMILARITY_INFO_DIR="${SIMILARITY_INFO_DIR:-xxx}"
MODE="${MODE:-dev}"
SCHEMA_DATA="${SCHEMA_DATA:-}"
SIM_DESC="${SIM_DESC:-}"
STRIP_COMMENTS="${STRIP_COMMENTS:-True}"

mkdir -p "$OUTPUT_DIR"

python3 "$REPO_ROOT/construct_for_schema.py" \
  --input_path "$INPUT_PATH" \
  --output_path "$OUTPUT_FILE" \
  --data_with_difficult_path "$DATA_WITH_DIFFICULT_PATH" \
  --mode "$MODE" \
  --similarity_info_dir "$SIMILARITY_INFO_DIR" \
  $( [[ -n "$SCHEMA_DATA" ]] && echo --schema_data "$SCHEMA_DATA" ) \
  $( [[ -n "$SIM_DESC" ]] && echo --sim_desc "$SIM_DESC" ) \
  $( [[ -n "$STRIP_COMMENTS" ]] && echo --strip_comments "$STRIP_COMMENTS" )
