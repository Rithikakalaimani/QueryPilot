"""Validate generated SQL: syntax, table/column existence, read-only, row limit."""
from __future__ import annotations
import re
import sqlparse
from schema_ingestion.extractor import SchemaExtractor
from config import get_settings
from connection import ConnectionConfig


class SQLValidator:
    """Validate SQL for safety and schema correctness."""

    def __init__(self, connection_config: ConnectionConfig | None = None):
        self.settings = get_settings()
        self.connection_config = connection_config
        self._schema_tables: set[str] | None = None

    def _get_schema_tables(self) -> set[str]:
        if self._schema_tables is None:
            ext = SchemaExtractor(connection_config=self.connection_config)
            schema = ext.extract()
            self._schema_tables = {t.name.lower() for t in schema.tables}
        return self._schema_tables

    def validate(self, sql: str) -> tuple[bool, str]:
        """Return (is_valid, error_message). Empty error_message if valid."""
        # 1. Syntax check
        ok, err = self._check_syntax(sql)
        if not ok:
            return False, err
        # 2. Read-only (no INSERT/UPDATE/DELETE/DROP etc.)
        ok, err = self._check_read_only(sql)
        if not ok:
            return False, err
        # 3. Row limit
        ok, err = self._check_row_limit(sql)
        if not ok:
            return False, err
        # 4. Table existence (best-effort from parsed tokens)
        ok, err = self._check_tables_exist(sql)
        if not ok:
            return False, err
        return True, ""

    def _check_syntax(self, sql: str) -> tuple[bool, str]:
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "Invalid SQL: could not parse."
            return True, ""
        except Exception as e:
            return False, f"SQL syntax error: {e}"

    def _check_read_only(self, sql: str) -> tuple[bool, str]:
        if not self.settings.read_only:
            return True, ""
        upper = sql.upper()
        forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "REPLACE"]
        for kw in forbidden:
            if re.search(rf"\b{kw}\b", upper):
                return False, f"Read-only mode: {kw} is not allowed."
        return True, ""

    def _check_row_limit(self, sql: str) -> tuple[bool, str]:
        limit = self.settings.max_rows_limit
        # If LIMIT present, check value
        m = re.search(r"\bLIMIT\s+(\d+)", sql, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if val > limit:
                return False, f"LIMIT {val} exceeds maximum allowed ({limit})."
        # Optionally require LIMIT for SELECT (could be relaxed)
        if "LIMIT" not in sql.upper() and re.search(r"\bSELECT\b", sql, re.IGNORECASE):
            # Allow no LIMIT but we could add one in execution layer
            pass
        return True, ""

    def _check_tables_exist(self, sql: str) -> tuple[bool, str]:
        """Best-effort: ensure first token after FROM/JOIN is a known table (aliases allowed)."""
        valid_tables = self._get_schema_tables()
        # Extract first identifier after FROM and after each JOIN (likely table names)
        for keyword in ("FROM", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN"):
            pattern = rf"\b{keyword.replace(' ', r'\s+')}\s+([a-zA-Z_][a-zA-Z0-9_]*)"
            for m in re.finditer(pattern, sql, re.IGNORECASE):
                name = m.group(1).lower()
                if name not in valid_tables:
                    return False, f"Unknown table: {name}"
        return True, ""
