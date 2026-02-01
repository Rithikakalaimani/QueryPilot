"""Extract schema (tables, columns, types, FKs) from MySQL/Postgres."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from config import get_settings
from connection import get_connection, ConnectionConfig


@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    default: str | None = None


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)
    sample_row_count: int = 0


@dataclass
class SchemaInfo:
    tables: list[TableInfo] = field(default_factory=list)
    raw_text: str = ""


class SchemaExtractor:
    """Extract full schema from MySQL or Postgres."""

    def __init__(self, connection_config: ConnectionConfig | None = None):
        self.conn = get_connection(connection_config)
        self.database_type = self.conn.database_type
        self._engine: Engine | None = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self.conn.sqlalchemy_url())
        return self._engine

    def extract(self) -> SchemaInfo:
        """Extract tables, columns, types, FKs (and optional sample stats)."""
        engine = self._get_engine()
        inspector = inspect(engine)
        tables: list[TableInfo] = []

        for table_name in inspector.get_table_names():
            columns: list[ColumnInfo] = []
            for col in inspector.get_columns(table_name):
                columns.append(
                    ColumnInfo(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=col.get("nullable", True),
                        default=str(col["default"]) if col.get("default") else None,
                    )
                )

            pk = inspector.get_pk_constraint(table_name)
            primary_key = list(pk.get("constrained_columns", [])) if pk else []

            foreign_keys: list[dict[str, str]] = []
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append(
                    {
                        "columns": ", ".join(fk.get("constrained_columns", [])),
                        "referred_table": fk.get("referred_table", ""),
                        "referred_columns": ", ".join(fk.get("referred_columns", [])),
                    }
                )

            # Optional: sample row count (lightweight)
            try:
                quoted = f'"{table_name}"' if self.database_type == "postgres" else f"`{table_name}`"
                with engine.connect() as conn:
                    r = conn.execute(text(f"SELECT COUNT(*) FROM {quoted}"))
                    sample_row_count = r.scalar() or 0
            except Exception:
                sample_row_count = 0

            tables.append(
                TableInfo(
                    name=table_name,
                    columns=columns,
                    primary_key=primary_key,
                    foreign_keys=foreign_keys,
                    sample_row_count=sample_row_count,
                )
            )

        schema = SchemaInfo(tables=tables)
        schema.raw_text = self._schema_to_text(schema)
        return schema

    def _schema_to_text(self, schema: SchemaInfo) -> str:
        """Convert schema to human-readable text for chunking."""
        lines: list[str] = []
        for t in schema.tables:
            cols = ", ".join(f"{c.name} ({c.type})" for c in t.columns)
            lines.append(f"Table: {t.name}")
            lines.append(f"  Columns: {cols}")
            if t.primary_key:
                lines.append(f"  Primary key: {', '.join(t.primary_key)}")
            for fk in t.foreign_keys:
                lines.append(
                    f"  Foreign key: {fk['columns']} -> {fk['referred_table']}({fk['referred_columns']})"
                )
            if t.sample_row_count:
                lines.append(f"  Row count: {t.sample_row_count}")
            lines.append("")
        return "\n".join(lines).strip()
