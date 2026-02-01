"""Convert schema text into chunks for embedding."""
from __future__ import annotations
from dataclasses import dataclass
from schema_ingestion.extractor import SchemaInfo, TableInfo


@dataclass
class SchemaChunk:
    text: str
    table_name: str
    chunk_type: str  # "table" | "columns" | "relationships"
    metadata: dict


class SchemaChunker:
    """Split schema into retrievable chunks (per-table + relationship chunks)."""

    def chunk(self, schema: SchemaInfo) -> list[SchemaChunk]:
        chunks: list[SchemaChunk] = []
        for table in schema.tables:
            # One chunk per table: name + columns + PK
            table_chunk = self._table_to_chunk(table)
            chunks.append(table_chunk)
            # Relationship chunk if FKs exist
            if table.foreign_keys:
                rel_chunk = self._relationships_to_chunk(table)
                chunks.append(rel_chunk)
        return chunks

    def _table_to_chunk(self, table: TableInfo) -> SchemaChunk:
        lines = [
            f"Table: {table.name}",
            "Columns: " + ", ".join(f"{c.name} ({c.type})" for c in table.columns),
        ]
        if table.primary_key:
            lines.append("Primary key: " + ", ".join(table.primary_key))
        text = "\n".join(lines)
        return SchemaChunk(
            text=text,
            table_name=table.name,
            chunk_type="table",
            metadata={"columns": [c.name for c in table.columns], "pk": table.primary_key},
        )

    def _relationships_to_chunk(self, table: TableInfo) -> SchemaChunk:
        lines = [f"Table {table.name} relationships:"]
        for fk in table.foreign_keys:
            lines.append(
                f"  {fk['columns']} references {fk['referred_table']}({fk['referred_columns']})"
            )
        text = "\n".join(lines)
        return SchemaChunk(
            text=text,
            table_name=table.name,
            chunk_type="relationships",
            metadata={"foreign_keys": table.foreign_keys},
        )
