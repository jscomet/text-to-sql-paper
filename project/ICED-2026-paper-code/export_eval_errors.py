#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sqlite3
from typing import List, Dict, Any


def parse_args():
    p = argparse.ArgumentParser(description="Export mispredicted cases with details")
    p.add_argument('--pred', type=str, required=True)
    p.add_argument('--gold', type=str, required=True)
    p.add_argument('--db_path', type=str, required=True)
    p.add_argument('--mode', type=str, default='greedy_search', choices=['greedy_search'])
    p.add_argument('--out_file', type=str, default=None)
    return p.parse_args()


def _strip_semicolon(s: str) -> str:
    return s.strip().rstrip(';')


def _get_db_file(db_path: str, db_id: str) -> str:
    return os.path.join(db_path, db_id, f"{db_id}.sqlite")


def _compare_sql_symmetric(conn: sqlite3.Connection, pred_sql: str, gt_sql: str) -> int:
    pred_sql = _strip_semicolon(pred_sql)
    gt_sql = _strip_semicolon(gt_sql)
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION;")
        sql_eq = (
            "SELECT CASE "
            "WHEN EXISTS(SELECT 1 FROM (" + pred_sql + ") EXCEPT SELECT * FROM (" + gt_sql + ")) THEN 0 "
            "WHEN EXISTS(SELECT 1 FROM (" + gt_sql + ") EXCEPT SELECT * FROM (" + pred_sql + ")) THEN 0 "
            "ELSE 1 END;"
        )
        cursor.execute(sql_eq)
        row = cursor.fetchone()
        conn.rollback()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception:
        conn.rollback()
        return 0
    finally:
        cursor.close()


def _open_conn(db_file: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA synchronous=OFF;")
    conn.execute("PRAGMA journal_mode=OFF;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-100000;")
    return conn


def derive_default_out(pred_file: str) -> str:
    base = os.path.splitext(os.path.basename(pred_file))[0]
    out_dir = os.path.dirname(pred_file)
    return os.path.join(out_dir, f"{base}.errors.json")


def main():
    args = parse_args()
    gold: List[Dict[str, Any]] = json.load(open(args.gold, 'r', encoding='utf-8'))
    preds: List[Dict[str, Any]] = json.load(open(args.pred, 'r', encoding='utf-8'))

    if len(gold) != len(preds):
        raise ValueError(f"gold len {len(gold)} != preds len {len(preds)}")

    out_file = args.out_file or derive_default_out(args.pred)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    errors: List[Dict[str, Any]] = []

    for idx, (g, p) in enumerate(zip(gold, preds)):
        db_id = g.get('db_id')
        db_file = _get_db_file(args.db_path, db_id)
        if not os.path.isfile(db_file):
            errors.append({
                'index': idx,
                'db_id': db_id,
                'db_file': db_file,
                'question': g.get('question') or g.get('SpiderSynQuestion') or '',
                'ground_truth': g.get('SQL') or '',
                'pred_sql': (p.get('pred_sql') or [''])[0],
                'difficulty': g.get('difficulty') or g.get('hardness') or g.get('Hardness') or g.get('Difficulty'),
                'error': 'missing_db_file'
            })
            continue

        conn = _open_conn(db_file)
        try:
            pred_sqls = p.get('pred_sql') or []
            if len(pred_sqls) == 0:
                pred_sql = ''
            else:
                pred_sql = pred_sqls[0]  # greedy_search: use first

            gt_sql = g.get('SQL') or ''
            question = g.get('question') or g.get('SpiderSynQuestion') or ''
            difficulty = g.get('difficulty') or g.get('hardness') or g.get('Hardness') or g.get('Difficulty')

            correctness = _compare_sql_symmetric(conn, pred_sql, gt_sql)
            if correctness == 0:
                errors.append({
                    'index': idx,
                    'db_id': db_id,
                    'db_file': db_file,
                    'question': question,
                    'ground_truth': gt_sql,
                    'pred_sql': pred_sql,
                    'difficulty': difficulty
                })
        finally:
            conn.close()

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(errors, indent=2, ensure_ascii=False))

    print(f"Exported {len(errors)} error cases to: {out_file}")


if __name__ == '__main__':
    main()

