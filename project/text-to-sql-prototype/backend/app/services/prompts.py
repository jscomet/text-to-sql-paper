"""Prompt templates for Text-to-SQL generation."""

# NL2SQL generation prompt template
NL2SQL_TEMPLATE = """You are a SQL expert. Your task is to convert natural language questions into SQL queries.

Database Schema:
{schema}

User Question:
{question}

Instructions:
1. Generate a valid SQL query based on the schema and question
2. Use only the tables and columns defined in the schema
3. Use proper SQL syntax for {dialect}
4. Add appropriate JOINs if querying multiple tables
5. Use meaningful aliases for tables if needed
6. Return ONLY the SQL query without any explanation
7. Do not use markdown code blocks, just the raw SQL

SQL Query:"""

# SQL explanation prompt template
SQL_EXPLAIN_TEMPLATE = """You are a SQL expert. Explain the following SQL query in simple terms.

SQL Query:
{sql}

Explanation:"""

# SQL optimization prompt template
SQL_OPTIMIZE_TEMPLATE = """You are a SQL optimization expert. Analyze and optimize the following SQL query.

Database Schema:
{schema}

Original SQL:
{sql}

Instructions:
1. Identify potential performance issues
2. Suggest an optimized version if possible
3. Explain your optimizations

Optimized SQL:"""

# Schema understanding prompt template
SCHEMA_UNDERSTAND_TEMPLATE = """You are a database expert. Analyze the following database schema and provide insights.

Database Schema:
{schema}

Please provide:
1. A brief summary of the database purpose
2. Key tables and their relationships
3. Important columns and their meanings
4. Any potential data quality concerns

Analysis:"""


def format_schema_for_prompt(tables: list[dict]) -> str:
    """Format schema information for prompt.

    Args:
        tables: List of table dictionaries with columns info.

    Returns:
        Formatted schema string.
    """
    schema_parts = []

    for table in tables:
        table_name = table.get("name", "")
        columns = table.get("columns", [])
        comment = table.get("comment", "")

        schema_parts.append(f"Table: {table_name}")
        if comment:
            schema_parts.append(f"  Comment: {comment}")

        schema_parts.append("  Columns:")
        for col in columns:
            col_name = col.get("name", "")
            col_type = col.get("type", "")
            nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
            col_comment = col.get("comment", "")

            col_desc = f"    - {col_name} ({col_type}, {nullable})"
            if col_comment:
                col_desc += f" - {col_comment}"
            schema_parts.append(col_desc)

        # Add primary keys
        primary_keys = table.get("primary_keys", [])
        if primary_keys:
            schema_parts.append(f"  Primary Keys: {', '.join(primary_keys)}")

        # Add foreign keys
        foreign_keys = table.get("foreign_keys", [])
        if foreign_keys:
            schema_parts.append("  Foreign Keys:")
            for fk in foreign_keys:
                col = fk.get("column", "")
                ref_table = fk.get("referenced_table", "")
                ref_col = fk.get("referenced_column", "")
                schema_parts.append(f"    - {col} -> {ref_table}({ref_col})")

        schema_parts.append("")  # Empty line between tables

    return "\n".join(schema_parts)


def build_nl2sql_prompt(
    question: str,
    schema: str | list[dict],
    dialect: str = "MySQL"
) -> str:
    """Build NL2SQL prompt.

    Args:
        question: Natural language question.
        schema: Database schema (string or list of table dicts).
        dialect: SQL dialect (MySQL, PostgreSQL, SQLite).

    Returns:
        Formatted prompt string.
    """
    if isinstance(schema, list):
        schema = format_schema_for_prompt(schema)

    return NL2SQL_TEMPLATE.format(
        schema=schema,
        question=question,
        dialect=dialect
    )


def build_sql_explain_prompt(sql: str) -> str:
    """Build SQL explanation prompt.

    Args:
        sql: SQL query to explain.

    Returns:
        Formatted prompt string.
    """
    return SQL_EXPLAIN_TEMPLATE.format(sql=sql)


def build_sql_optimize_prompt(sql: str, schema: str | list[dict]) -> str:
    """Build SQL optimization prompt.

    Args:
        sql: SQL query to optimize.
        schema: Database schema.

    Returns:
        Formatted prompt string.
    """
    if isinstance(schema, list):
        schema = format_schema_for_prompt(schema)

    return SQL_OPTIMIZE_TEMPLATE.format(sql=sql, schema=schema)
