#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"


# Defaults
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/outputs/Qwen2.5-Coder-32B-Instruct}"
BASE_NAME="${BASE_NAME:-bird_dev_sql_comment_vote8.json}"
ROUNDS="${ROUNDS:-}"  # if empty, auto-detect
MODE="${MODE:-major_voting}"
GOLD_FILE="${GOLD_FILE:-$REPO_ROOT/data/bird/dev.json}"
DB_PATH="${DB_PATH:-$REPO_ROOT/data/bird/dev_databases}"
SUMMARY_FILE="${SUMMARY_FILE:-$OUTPUT_DIR/eval_rounds_summary.json}"

# Validate paths
if [[ ! -d "$OUTPUT_DIR" ]]; then echo "Missing output dir: $OUTPUT_DIR"; exit 1; fi
if [[ ! -f "$GOLD_FILE" ]]; then echo "Missing gold file: $GOLD_FILE"; exit 1; fi
if [[ ! -d "$DB_PATH" ]]; then echo "Missing db path: $DB_PATH"; exit 1; fi

# Build round list
declare -a ROUND_FILES
declare -a ROUNDS_LIST
if [[ -n "$ROUNDS" ]]; then
  for ((i=1; i<=ROUNDS; i++)); do
    f="$OUTPUT_DIR/$BASE_NAME.round${i}.json"
    if [[ -f "$f" ]]; then
      ROUND_FILES+=("$f")
      ROUNDS_LIST+=("$i")
    else
      echo "Skip missing: $f" >&2
    fi
  done
else
  while IFS= read -r f; do
    r="${f##*.round}"
    r="${r%.json}"
    ROUND_FILES+=("$f")
    ROUNDS_LIST+=("$r")
  done < <(ls -1 "$OUTPUT_DIR/$BASE_NAME".round*.json 2>/dev/null | sort -t '.' -k 3,3V)
fi

if [[ ${#ROUND_FILES[@]} -eq 0 ]]; then
  echo "No round files found under $OUTPUT_DIR for base $BASE_NAME" >&2
  exit 1
fi

# Evaluate per round and collect accuracies
TMP_SUMMARY="$(mktemp)"
echo "[" > "$TMP_SUMMARY"

for idx in "${!ROUND_FILES[@]}"; do
  round="${ROUNDS_LIST[$idx]}"
  pred_file="${ROUND_FILES[$idx]}"
  echo "Evaluating round $round: $pred_file (mode=$MODE)" >&2
  # Capture accuracy line
  acc_line=$(python "$REPO_ROOT/evaluate_bird.py" --pred "$pred_file" --gold "$GOLD_FILE" --db_path "$DB_PATH" --mode "$MODE" 2>&1 | grep -E "^EX Accuracy" | tail -n 1 || true)
  acc_val=""
  if [[ -n "$acc_line" ]]; then
    acc_val=$(echo "$acc_line" | sed -E 's/.*: *([0-9.]+)/\1/')
  else
    acc_val="NaN"
  fi
  printf '{"round": %s, "pred_file": "%s", "mode": "%s", "accuracy": %s}%s\n' \
    "$round" "$pred_file" "$MODE" "$acc_val" \
    $([[ "$idx" -lt $(( ${#ROUND_FILES[@]} - 1 )) ]] && echo "," || echo "") >> "$TMP_SUMMARY"
done

echo "]" >> "$TMP_SUMMARY"
mv "$TMP_SUMMARY" "$SUMMARY_FILE"
echo "Wrote summary: $SUMMARY_FILE" >&2

