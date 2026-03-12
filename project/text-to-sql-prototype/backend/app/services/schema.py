"""Schema service for fetching and managing database schema information."""
from typing import Any, Dict, List

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from app.schemas.connection import ColumnSchema, ForeignKeySchema, TableSchema


class SchemaService:
    """Service for fetching database schema information."""

    @staticmethod
    async def get_tables(engine: AsyncEngine) -> List[str]:
        """Get all table names from the database."""
        async with engine.connect() as conn:
            result = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            return result

    @staticmethod
    async def get_table_schema(engine: AsyncEngine, table_name: str) -> TableSchema:
        """Get schema information for a specific table."""
        async with engine.connect() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))

            columns_info = await conn.run_sync(
                lambda sync_conn: inspector.get_columns(table_name)
            )
            columns = []
            for col in columns_info:
                columns.append(ColumnSchema(
                    name=col['name'],
                    type=str(col['type']),
                    nullable=col.get('nullable', True),
                    default=str(col['default']) if col.get('default') is not None else None,
                    comment=col.get('comment')
                ))

            pk_info = await conn.run_sync(
                lambda sync_conn: inspector.get_pk_constraint(table_name)
            )
            primary_keys = pk_info.get('constrained_columns', [])

            fk_info = await conn.run_sync(
                lambda sync_conn: inspector.get_foreign_keys(table_name)
            )
            foreign_keys = []
            for fk in fk_info:
                referred_table = fk.get('referred_table')
                referred_columns = fk.get('referred_columns', [])
                constrained_columns = fk.get('constrained_columns', [])

                for i, col in enumerate(constrained_columns):
                    if i < len(referred_columns):
                        foreign_keys.append(ForeignKeySchema(
                            column=col,
                            referenced_table=referred_table,
                            referenced_column=referred_columns[i]
                        ))

            comment = None
            try:
                comment = await conn.run_sync(
                    lambda sync_conn: inspector.get_table_comment(table_name)
                )
                if comment:
                    comment = comment.get('text')
            except Exception:
                pass

            return TableSchema(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                comment=comment
            )

    @staticmethod
    async def get_all_schemas(engine: AsyncEngine) -> List[TableSchema]:
        """Get schema information for all tables."""
        tables = await SchemaService.get_tables(engine)
        schemas = []
        for table_name in tables:
            try:
                schema = await SchemaService.get_table_schema(engine, table_name)
                schemas.append(schema)
            except Exception:
                continue
        return schemas

    @staticmethod
    async def get_foreign_keys(engine: AsyncEngine) -> List[ForeignKeySchema]:
        """Get all foreign key relationships from the database."""
        async with engine.connect() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

            all_foreign_keys = []
            for table_name in tables:
                try:
                    fk_info = await conn.run_sync(
                        lambda sync_conn: inspector.get_foreign_keys(table_name)
                    )
                    for fk in fk_info:
                        referred_table = fk.get('referred_table')
                        referred_columns = fk.get('referred_columns', [])
                        constrained_columns = fk.get('constrained_columns', [])

                        for i, col in enumerate(constrained_columns):
                            if i < len(referred_columns):
                                all_foreign_keys.append(ForeignKeySchema(
                                    column=f"{table_name}.{col}",
                                    referenced_table=referred_table,
                                    referenced_column=referred_columns[i]
                                ))
                except Exception:
                    continue

            return all_foreign_keys

    @staticmethod
    def build_schema_text(tables: List[TableSchema]) -> str:
        """Build CREATE TABLE statements from table schemas."""
        statements = []

        for table in tables:
            lines = [f"CREATE TABLE {table.name} ("]

            column_defs = []
            for col in table.columns:
                col_def = f"    {col.name} {col.type}"
                if not col.nullable:
                    col_def += " NOT NULL"
                if col.default:
                    col_def += f" DEFAULT {col.default}"
                column_defs.append(col_def)

            if table.primary_keys:
                pk_def = f"    PRIMARY KEY ({', '.join(table.primary_keys)})"
                column_defs.append(pk_def)

            for fk in table.foreign_keys:
                fk_def = f"    FOREIGN KEY ({fk.column}) REFERENCES {fk.referenced_table}({fk.referenced_column})"
                column_defs.append(fk_def)

            lines.append(",\n".join(column_defs))
            lines.append(");")

            if table.comment:
                lines.append(f"-- {table.comment}")

            statements.append("\n".join(lines))

        return "\n\n".join(statements)

    @staticmethod
    def serialize_schemas(tables: List[TableSchema]) -> List[Dict[str, Any]]:
        """Serialize table schemas to dictionary format for JSON storage."""
        result = []
        for table in tables:
            table_dict = {
                "name": table.name,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "nullable": col.nullable,
                        "default": col.default,
                        "comment": col.comment
                    }
                    for col in table.columns
                ],
                "primary_keys": table.primary_keys,
                "foreign_keys": [
                    {
                        "column": fk.column,
                        "referenced_table": fk.referenced_table,
                        "referenced_column": fk.referenced_column
                    }
                    for fk in table.foreign_keys
                ],
                "comment": table.comment
            }
            result.append(table_dict)
        return result

    @staticmethod
    def deserialize_schemas(data: List[Dict[str, Any]]) -> List[TableSchema]:
        """Deserialize table schemas from dictionary format."""
        result = []
        for table_dict in data:
            columns = [
                ColumnSchema(
                    name=col["name"],
                    type=col["type"],
                    nullable=col.get("nullable", True),
                    default=col.get("default"),
                    comment=col.get("comment")
                )
                for col in table_dict.get("columns", [])
            ]

            foreign_keys = [
                ForeignKeySchema(
                    column=fk["column"],
                    referenced_table=fk["referenced_table"],
                    referenced_column=fk["referenced_column"]
                )
                for fk in table_dict.get("foreign_keys", [])
            ]

            table = TableSchema(
                name=table_dict["name"],
                columns=columns,
                primary_keys=table_dict.get("primary_keys", []),
                foreign_keys=foreign_keys,
                comment=table_dict.get("comment")
            )
            result.append(table)
        return result
