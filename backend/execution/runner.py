"""Execute validated SQL on MySQL/Postgres and fetch results."""
from __future__ import annotations
from typing import Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from connection import get_connection, ConnectionConfig


class QueryRunner:
    """Execute read-only SQL and return rows."""

    def __init__(self, connection_config: ConnectionConfig | None = None):
        self.conn = get_connection(connection_config)
        self._engine: Engine | None = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self.conn.sqlalchemy_url())
        return self._engine

    def execute(self, sql: str) -> tuple[list[dict[str, Any]], str | None]:
        """Run SQL; return (list of row dicts, error_message). error_message is None on success."""
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = [dict(row._mapping) for row in result]
                # Coerce non-JSON-serializable types
                for row in rows:
                    for k, v in list(row.items()):
                        if hasattr(v, "isoformat"):
                            row[k] = v.isoformat()
                        elif type(v).__name__ == "Decimal" and hasattr(v, "__float__"):
                            row[k] = float(v)
                return rows, None
        except Exception as e:
            return [], str(e)
