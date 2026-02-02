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
            prompt = (
                f"User asked: {query}\nSQL: {sql}\nColumns: {columns}\n"
                f"Sample rows (first 10 only): {sample_str}\n\n"
                "Reply with ONLY one short sentence. Do NOT list rows or repeat data. "
                "Example: 'Returned 4 customers.' or 'Query returned 4 rows.'"
            )
            raw = chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.settings.llm_model,
                temperature=0.2,
                max_tokens=80,
            )
            # Take only the first sentence so we never show hallucinated lists
            summary = (raw or "").strip()
            first_sentence = summary.split(".")[0].strip()
            if first_sentence:
                return first_sentence + "." if not first_sentence.endswith(".") else first_sentence
            return f"Returned {len(sample)} row(s)."
        except Exception:
            return f"Returned {len(sample)} row(s)."
