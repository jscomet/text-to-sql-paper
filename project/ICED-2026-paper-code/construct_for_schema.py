import json
from collections import defaultdict
from typing import Dict, List
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import argparse
import pdb
def load_json(file_path):
    """
    加载 JSON 文件内容。

    参数:
        file_path (str): JSON 文件的路径。

    返回:
        dict 或 list: JSON 文件解析后的内容。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在。")
        return None
    except json.JSONDecodeError:
        print(f"错误：文件 {file_path} 格式不正确。")
        return None
    except Exception as e:
        print(f"加载 JSON 文件时发生错误：{e}")
        return None
def extract_labels(file_path, save_path) -> None:
    """Extracts schema labels from a JSON file and saves the results to a new JSON file.
    Args:
        file_path (str): Path to the input JSON file containing dataset.
        save_path (str): Path to save the output JSON file with schema labels.
    """

    with open(file_path, 'r') as file:
        dataset = json.load(file)

    for data in dataset:
        schema = data.get("schema", {})
        schema_items = schema.get("schema_items", [])
        table_labels = data.get("table_labels", [])
        column_labels = data.get("column_labels", [])

        schema_groundtruth = {}

        for table_idx, table_item in enumerate(schema_items):
            table_name = table_item.get("table_name")
            table_label = table_labels[table_idx] if table_idx < len(table_labels) else -1
            if table_label == 1:
                if table_name not in schema_groundtruth:
                    schema_groundtruth[table_name] = []
            # 获取当前表的列名和对应的列标签
            column_names = table_item.get("column_names", [])
            table_column_labels = column_labels[table_idx] if table_idx < len(column_labels) else []

            for column_idx, column_name in enumerate(column_names):
                column_label = table_column_labels[column_idx] if column_idx < len(table_column_labels) else -1

                # 如果列标签为1，则将该列名添加到结果中
                if column_label == 1:
                    if table_name not in schema_groundtruth:
                        schema_groundtruth[table_name] = []
                    schema_groundtruth[table_name].append(column_name)

        # 将 schema_groundtruth 添加到原始数据中
        data['schema_groundtruth'] = schema_groundtruth

    # 将更新后的数据集转换为 JSON 格式
    output_json = json.dumps(dataset, indent=4)
    with open(save_path, 'w') as f:
        f.write(json_result)

    
def convert_json_to_structured_text_json(args) -> None:
    import os
    from collections import defaultdict
    with open(args.input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mode = args.mode
    data_with_difficult_path = args.data_with_difficult_path
    similarity_info_dir = args.similarity_info_dir
    strip_comments =args.strip_comments

    if data_with_difficult_path != None:
        with open(data_with_difficult_path, 'r', encoding='utf-8') as f:
            data_with_difficult = json.load(f)
        mp_question_to_diff = defaultdict(str)
        for x in data_with_difficult:
            mp_question_to_diff[x['question']] = x['difficulty']
    else:
        print("data_with_difficult_path is none so without difficulty")
    def convert_entry(entry: Dict, schema_linking=None) -> Dict:
        # 构建 inputtext, question, sql, evidence, text, db_path, db_id, difficulty
        result = []
        schema = entry["schema"]
        table_labels = entry.get("table_labels", [])
        column_labels = entry.get("column_labels", [])
        schema_groundtruth = {}
        schema_items = schema.get("schema_items", [])

        db_id = entry["db_id"]
        similarity_path = os.path.join(similarity_info_dir, f"{db_id}.json")
        similar_fields = []
        if os.path.exists(similarity_path):
            with open(similarity_path, 'r', encoding='utf-8') as f:
                similar_fields = json.load(f)
        else:
            print("similarity_info_dir not exist", similarity_path)
        injected_foreign_keys = []
        field_sim_annotation = defaultdict(list)  # map full_field_name -> list of comment strings
        
        for sim_item in similar_fields:
            fk_field = sim_item['fk']
            pk_field = sim_item['pk']
            sim = sim_item['sim']
            sim_type = sim_item['type']

            fk_table, fk_col = fk_field.split(".")
            pk_table, pk_col = pk_field.split(".")

            if sim >= 0.95 and fk_table != pk_table:
                injected_foreign_keys.append((fk_table, fk_col, pk_table, pk_col))
            else:
                if args.sim_desc:
                    percent = sim * 100
                    field_sim_annotation[fk_field.lower()].append(
                        f"{percent:.0f}% values in this column are identical in {pk_field}"
                    )
                    field_sim_annotation[pk_field.lower()].append(
                        f"{percent:.0f}% values in this column are identical in {fk_field}"
                    )
        for table_idx, table in enumerate(schema_items):
            col_strs = []
            table_name = table.get("table_name")
            table_label = table_labels[table_idx] if table_idx < len(table_labels) else -1
            if table_label == 1:
                if table_name not in schema_groundtruth:
                    schema_groundtruth[table_name] = []
            column_names = table.get("column_names", [])
            table_column_labels = column_labels[table_idx] if table_idx < len(column_labels) else []
            for column_idx, (name, typ, comment, values, pk) in enumerate(zip(
                    table["column_names"],
                    table["column_types"],
                    table["column_comments"],
                    table["column_contents"],
                    table["pk_indicators"]
            )):
                column_label = table_column_labels[column_idx] if column_idx < len(table_column_labels) else -1
                if strip_comments:
                    comment = ""
                    values = []
                if column_label == 1:
                    if table_name not in schema_groundtruth:
                        schema_groundtruth[table_name] = []
                    schema_groundtruth[table_name].append(name)
                name_full = f"{table['table_name']}.{name}"
                type_str = typ
                pk_str = "PRIMARY KEY" if pk == 1 else ""
                comment_str = f"comment : {comment}" if comment else ""
                values_str = f"values : {', '.join(values[:2])}" if values else ""
                parts = " | ".join(filter(None, [type_str, pk_str, comment_str]))
                col_strs.append(f"{name_full} ( {parts} )")
                
            result.append(f"table {table['table_name']} , columns = [ {', '.join(col_strs)} ]")

        # foreign keys
        if schema.get("foreign_keys") or len(injected_foreign_keys):
            fk_all = schema.get("foreign_keys", []) + injected_foreign_keys
            fk_strs = [
                f"{src_table}.{src_col} = {tgt_table}.{tgt_col}"
                for src_table, src_col, tgt_table, tgt_col in fk_all
            ]
            result.append("foreign keys :\n" + "\n".join(fk_strs))
        # 构建 create_format，将 values 和 comment 放在注释中
        create_format = []
        # 构建外键约束字典
        fk_constraints_dict = defaultdict(list)
        if schema.get("foreign_keys"):
            #############
            # 要不要加外键
            #############
            if len(injected_foreign_keys):
                for src_table, src_col, tgt_table, tgt_col in schema["foreign_keys"] + injected_foreign_keys:
                    fk_constraints_dict[src_table].append((src_col, tgt_table, tgt_col))
            else:
                for src_table, src_col, tgt_table, tgt_col in schema["foreign_keys"]: 
                    fk_constraints_dict[src_table].append((src_col, tgt_table, tgt_col))
        if schema_linking != None:
            tables_set = set(schema_linking['tables'])
            column_set = set(schema_linking['columns'])
        for table_idx, table in enumerate(schema_items):
            # schemalinking code
            if schema_linking != None and table['table_name'].lower() not in tables_set: continue
            table_column_labels = column_labels[table_idx] if table_idx < len(column_labels) else []
            table_name = table["table_name"]
            columns = []
            fk_constraints = fk_constraints_dict.get(table_name, [])
            for column_idx, (name, typ, comment, values, pk) in enumerate(zip(
                    table["column_names"],
                    table["column_types"],
                    table["column_comments"],
                    table["column_contents"],
                    table["pk_indicators"]
            )):
                # schemalinking code
                if schema_linking != None and f"{table['table_name']}.{name}".lower() not in column_set : continue
                # 构建字段的注释信息
                name_full = f"{table['table_name']}.{name}".lower()
                if strip_comments is False:
                    comment_parts = ['--']
                    if comment:
                        comment_parts.append(f" {comment},")
                    if values:
                        comment_parts.append(f"example: [{', '.join(values[:2])}]")
                    # if field_sim_annotation.get(name_full):
                    #     comment_parts.append(", " + ", ".join(field_sim_annotation[name_full]))
                    if comment_parts:
                        comment_str = f" {' '.join(comment_parts)}"
                    else:
                        comment_str = ""

                pk_str = " PRIMARY KEY" if pk == 1 else ""
                column_line = f"    `{name}` {typ}{pk_str}{comment_str}"
                columns.append(column_line)

            # 添加外键约束
            for src_col, tgt_table, tgt_col in fk_constraints:
                columns.append(
                    f"    CONSTRAINT fk_{table_name}_{src_col} FOREIGN KEY (`{src_col}`) REFERENCES `{tgt_table}` (`{tgt_col}`)"
                )
            # 构建 CREATE TABLE 语句"
            newline = '\n'
            table_create = f"CREATE TABLE `{table_name}` ({newline}{',' + newline.join(columns)}{newline});"
            create_format.append(table_create)
        extra_knowledge = entry.get("evidence", "")
        return {
            # "inputtext": "\n".join(result),
            "question": entry["question"],
            "sql": entry["sql"],
            "evidence": entry["evidence"],
            "text": entry["text"],
            "db_path": entry["db_path"],
            "db_id": entry["db_id"],
            "difficulty": mp_question_to_diff[entry["question"]] if data_with_difficult_path != None else None,
            "create_format": "\n\n".join(create_format),
            "extra_knowledge": extra_knowledge if extra_knowledge is not None else "",
            "matched_content": entry["matched_contents"],
            "schema_groundtruth": schema_groundtruth
        }
    ########################
    # 构建schemalinking
    ########################
    if args.schema_data != None:
        schema_data = load_json(args.schema_data)
        schema_candidates = {}
        for idx, data_ in enumerate(schema_data):
            schema_candidates[data_['question'].lower()] = data_['schema']
        structured_entries = [convert_entry(entry, schema_candidates[entry['question'].lower().replace("\n", "")]) for entry in data]
    else:
        structured_entries = [convert_entry(entry) for entry in data]
    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(structured_entries, f, indent=2)


if __name__ == '__main__':
    """Main function to convert JSON data to a structured format.
    This script reads a converted from codes json file and convert it with 
    :cteate format, inputtext, question, sql, evidence, text, db_path, db_id, difficulty, schema_label, extra_knowledge
    inpputtext is : table frpm , columns = [ frpm.cdscode ( type, pk, comment, values ) , ... ] , foreign keys ...
    Usage:
        python construct_for_schema.py --input_path <input_json_path> --output_path <output_json_path> --data_with_difficult_path <data_with_difficult_path> --mode train
    """
    parser = argparse.ArgumentParser(description="Convert JSON data to a structured format.")
    parser.add_argument('--input_path', type=str, required=True, help='Path to the input JSON file.')
    parser.add_argument('--output_path', type=str, required=True, help='Path to save the converted JSON file.')
    parser.add_argument('--data_with_difficult_path', type=str, help='data_with_difficult_path--pure data-- dev', default=None)
    parser.add_argument('--similarity_info_dir', type=str, default="xxx", help='similarity info dir')
    parser.add_argument('--sim_desc', type=bool, help='if need desc of similarity info, please set this', default=False)
    parser.add_argument('--mode', type=str, help='schemalinking')
    parser.add_argument('--schema_data', type=str, help='train/dev', default=None)
    parser.add_argument('--strip_comments', type=bool, help='if true, clear column_comments and column_contents in schema', default=False)
    
    
    args = parser.parse_args()
    convert_json_to_structured_text_json(args)

