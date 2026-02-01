"""Format execution results for API: table view + optional LLM summary."""
from __future__ import annotations
from typing import Any
from config import get_settings
from llm import chat_completion


class ResultFormatter:
    """Format query results and optionally add LLM-generated summary."""

    def __init__(self):
        self.settings = get_settings()

    def format(
        self,
        rows: list[dict[str, Any]],
        sql: str,
        user_query: str,
        include_summary: bool = True,
    ) -> dict:
        """Return { columns, rows, summary?, row_count }."""
        if not rows:
            return {"columns": [], "rows": [], "row_count": 0, "summary": "No rows returned."}
        columns = list(rows[0].keys())
        out_rows = [list(r.values()) for r in rows]
        summary = None
        if include_summary and rows:
            summary = self._generate_summary(user_query, sql, columns, out_rows[:20])
        return {
            "columns": columns,
            "rows": out_rows,
            "row_count": len(rows),
            "summary": summary or f"Returned {len(rows)} row(s).",
        }

    def _generate_summary(self, query: str, sql: str, columns: list[str], sample: list) -> str:
        try:
            sample_str = str(sample[:10])
            return chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": f"User asked: {query}\nSQL: {sql}\nColumns: {columns}\nSample rows (first 10): {sample_str}\nWrite one short sentence summarizing what the result shows.",
                    }
                ],
                model=self.settings.llm_model,
                temperature=0.3,
                max_tokens=150,
            )
        except Exception:
            return f"Returned {len(sample)} row(s)."
