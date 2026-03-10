import argparse
import glob
import json
import multiprocessing
import sqlite3
import sys
import concurrent.futures
import mmh3  # A fast, high-quality non-cryptographic hash function
import itertools
from collections import defaultdict
import os

# --- Configuration ---
# The number of hash functions for the MinHash sketch.
# It determines the accuracy of the similarity estimation. The error rate is roughly 1/sqrt(NUM_HASH_FUNCTIONS).
# A smaller number is faster but less accurate. 96 offers a good balance.
NUM_HASH_FUNCTIONS = 128

# For very large tables, analyzing all unique values can be slow.
# Set SAMPLE_SIZE to a positive integer (e.g., 10000) to create the sketch from a random sample of that many rows.
# Set to 0 or a negative number to disable sampling and analyze all unique values in the column.
SAMPLE_SIZE = 10000

# The Jaccard similarity threshold to report a potential relationship.
# A high threshold (e.g., > 0.8) is recommended for finding foreign keys.
SIMILARITY_THRESHOLD = 0.85


def get_existing_foreign_keys(cursor):
    """
    返回数据库里已经声明的外键列表 [(from_table, from_col, to_table, to_col), ...]
    """
    cursor.execute("""
        SELECT m.name, fk."from", fk."table", fk."to"
        FROM sqlite_master AS m
        JOIN pragma_foreign_key_list(m.name) AS fk
        WHERE m.type='table'
    """)
    return [(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]

def get_db_schema(cursor):
    """
    Retrieves all tables and their relevant columns (TEXT, INTEGER types) from the database.

    Args:
        cursor: A sqlite3 database cursor.

    Returns:
        A dictionary mapping table names to a list of their column names.
    """
    # Query for all table names, excluding sqlite's internal tables.
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]

    schema = defaultdict(list)
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}")')
        for row in cursor.fetchall():
            # row[1] is name, row[2] is type
            col_name, col_type = row[1], row[2].upper()
            # # We are interested in columns that can act as keys.
            # if 'INT' in col_type or 'TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
            schema[table].append(col_name)
    return schema


def create_minhash_sketch(cursor, table_name, column_name):
    """
    Creates a MinHash sketch for the set of unique values in a database column.
    It uses random sampling for large tables if SAMPLE_SIZE is configured.

    Args:
        cursor: A sqlite3 database cursor.
        table_name: The name of the table.
        column_name: The name of the column.

    Returns:
        A list of integers representing the MinHash sketch.
    """
    # Initialize the sketch with infinity for each hash function.
    sketch = [float('inf')] * NUM_HASH_FUNCTIONS

    # Use a set to efficiently store unique values from the (potentially sampled) data.
    unique_values = set()

    if SAMPLE_SIZE > 0:
        # Use random sampling for large tables. This is much faster than a full scan.
        # ORDER BY RANDOM() is specific to SQLite for random sampling.
        query = f'SELECT "{column_name}" FROM "{table_name}" WHERE "{column_name}" IS NOT NULL ORDER BY "{column_name}" ASC LIMIT {SAMPLE_SIZE}'
        cursor.execute(query)
        for row in cursor.fetchall():
            unique_values.add(row[0])
    else:
        # For smaller tables or when sampling is disabled, get all distinct values.
        query = f'SELECT DISTINCT "{column_name}" FROM "{table_name}" WHERE "{column_name}" IS NOT NULL'
        cursor.execute(query)
        for row in cursor.fetchall():
            unique_values.add(row[0])

    if not unique_values:
        return sketch  # Return the initial empty sketch if no data

    for value in unique_values:
        # --- Value Normalization ---
        # Convert value to a consistent string representation and then to lowercase.
        # Finally, encode to bytes, which is required by the hash function.
        processed_value = str(value).lower().encode('utf-8')

        # Apply all K hash functions to the value and update the sketch.
        for i in range(NUM_HASH_FUNCTIONS):
            # Using the loop index 'i' as a seed is a standard and effective way
            # to simulate K independent hash functions for MinHash.
            # The goal is deterministically different hashes, not cryptographic security.
            hash_value = mmh3.hash(processed_value, seed=i, signed=False)

            # If the new hash is smaller than the current one in the sketch, update it.
            if hash_value < sketch[i]:
                sketch[i] = hash_value

    return sketch


def estimate_jaccard_similarity(sketch1, sketch2):
    """
    Estimates the Jaccard similarity between two sets based on their MinHash sketches.

    Args:
        sketch1: The first MinHash sketch.
        sketch2: The second MinHash sketch.

    Returns:
        An estimated Jaccard similarity score (float between 0.0 and 1.0).
    """
    if len(sketch1) != NUM_HASH_FUNCTIONS or len(sketch2) != NUM_HASH_FUNCTIONS:
        raise ValueError(f"Sketches must have the length {NUM_HASH_FUNCTIONS}.")

    # The similarity is the ratio of matching minimum hashes to the total number of hashes.
    matching_hashes = sum(1 for i in range(NUM_HASH_FUNCTIONS) if sketch1[i] == sketch2[i])
    return matching_hashes / NUM_HASH_FUNCTIONS


def find_foreign_key_candidates(db_path):
    """
    Main function to analyze a SQLite database and find potential foreign key relationships.

    Args:
        db_path: The file path to the SQLite database.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        existing_fks = get_existing_foreign_keys(cursor)
        existing_pairs = {
            (f"{tbl}.{col}", f"{ref_tbl}.{ref_col}") for tbl, col, ref_tbl, ref_col in existing_fks
        }
        schema = get_db_schema(cursor)
        if not schema:
            print("Could not find any tables or relevant columns to analyze.")
            conn.close()
            return

        all_sketches = {}
        for table, columns in schema.items():
            for column in columns:
                field_id = f"{table}.{column}"
                print(f"  - Processing {field_id}")
                all_sketches[field_id] = create_minhash_sketch(cursor, table, column)

        potential_candidates = []
        same_table_candidates = []
        field_ids = list(all_sketches.keys())

        # Use itertools.combinations to efficiently get all unique pairs of columns.
        for field1, field2 in itertools.combinations(field_ids, 2):
            sketch1, sketch2 = all_sketches[field1], all_sketches[field2]

            # Skip comparison if either column was empty (sketch will be all 'inf').
            if sketch1[0] == float('inf') or sketch2[0] == float('inf'):
                continue

            similarity = estimate_jaccard_similarity(sketch1, sketch2)

            if similarity >= SIMILARITY_THRESHOLD:
                # If similarity is high, get distinct value counts to infer direction (FK -> PK).
                table1, col1 = field1.split('.')
                table2, col2 = field2.split('.')

                pair1 = (f"{table1}.{col1}", f"{table2}.{col2}")
                pair2 = (f"{table2}.{col2}", f"{table1}.{col1}")
                if pair1 in existing_pairs or pair2 in existing_pairs:
                    continue

                cursor.execute(f'SELECT COUNT(DISTINCT "{col1}") FROM "{table1}"')
                count1 = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(DISTINCT "{col2}") FROM "{table2}"')
                count2 = cursor.fetchone()[0]

                if table1 == table2:
                    same_table_candidates.append((field1, field2, similarity, count1, count2))
                else:
                    if count1 <= count2:
                        potential_candidates.append((field1, field2, similarity, count1, count2))
                    else:
                        potential_candidates.append((field2, field1, similarity, count2, count1))
        print("\n" + "=" * 50)
        print("--- Potential Foreign Key Candidates ---")
        print(f"(Based on a similarity threshold of {SIMILARITY_THRESHOLD:.0%})")
        print("=" * 50)

        if not potential_candidates:
            print("\nNo strong candidates found.")
            return None

        # Sort candidates by their similarity score in descending order for relevance.
        potential_candidates.sort(key=lambda x: x[2], reverse=True)

        for fk_candidate, pk_candidate, sim, fk_count, pk_count in potential_candidates:
            print(
                f"\n🔗 Suggestion: `{fk_candidate}` may be a FOREIGN KEY referencing `{pk_candidate}`"
            )
            print(f"   - Jaccard Similarity: {sim:.2%}")
            print(f"   - Unique Value Counts: {fk_count} in '{fk_candidate}' | {pk_count} in '{pk_candidate}'")
        return potential_candidates, same_table_candidates
    finally:
        conn.close()

def save_candidates_json(db_path, potential_candidates, same_table_candidates, saved_path):
    

    def to_dict(lst, cand_type):
        return [
            {
                "type": cand_type,
                "fk": fk,
                "pk": pk,
                "sim": sim,
                "fk_unique_cnt": fk_cnt,
                "pk_unique_cnt": pk_cnt
            }
            for fk, pk, sim, fk_cnt, pk_cnt in lst
        ]

    all_candidates = (
        to_dict(potential_candidates, "cross_table") +
        to_dict(same_table_candidates, "same_table")
    )

    with open(saved_path, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, indent=2, ensure_ascii=False)
def main():
    parser = argparse.ArgumentParser(description="Find FK candidates for all SQLite files in a directory.")
    parser.add_argument("-d", "--dir", required=True, help="Directory containing *.sqlite files")
    parser.add_argument("-j", "--jobs", type=int, default=multiprocessing.cpu_count(), help="Number of threads (default: CPU count)")
    parser.add_argument("-od", "--output_dir", required=True, help="Directory to save output JSON files")
    args = parser.parse_args()

    db_dir = args.dir
    if not os.path.isdir(db_dir):
        print(f"Error: '{db_dir}' is not a valid directory")
        sys.exit(1)

    # 找到所有 .sqlite 文件
    db_files = glob.glob(os.path.join(db_dir, "**", "*.sqlite"), recursive=True)
    if not db_files:
        print("No .sqlite files found.")
        return
    print(f"🔍 Found {len(db_files)} SQLite files. Using {args.jobs} threads.\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        future_to_db = {pool.submit(find_foreign_key_candidates, db): db for db in db_files}
        for future in concurrent.futures.as_completed(future_to_db):
            db_path = future_to_db[future]
            try:
                result = future.result()
                if result:
                    potential, same = result
                    base = os.path.splitext(os.path.basename(db_path))[0]
                    save_candidates_json(db_path, potential, same, os.path.join(args.output_dir, f"{base}.json"))
                    print(f"✅ {os.path.basename(db_path)} 分析完成，已写入 JSON")
                else:
                    print(f"⚠️  {os.path.basename(db_path)} 跳过（空或无表）")
            except Exception as e:
                print(f"❌ Error processing {os.path.basename(db_path)}: {e}")
    print("\n✅ All done. Check the generated *_all_candidates.json files.")
if __name__ == '__main__':
    main()

