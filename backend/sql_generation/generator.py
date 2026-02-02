"""Generate SQL from NL query + schema context using LLM (OpenAI or Ollama)."""
from __future__ import annotations
from config import get_settings
from llm import chat_completion


SQL_RULES = """
- Use explicit column names; avoid SELECT *.
- Use table aliases for clarity (e.g. c for customers, o for orders).
- Always add a reasonable LIMIT (e.g. LIMIT 100) unless the question asks for all/count.
- Use valid table and column names only from the schema context.
- For "unique", "distinct", or "without duplicates" on a column: use SELECT DISTINCT TRIM(column) AS column (or LOWER(TRIM(column)) if case should not matter) so values that differ only by whitespace/case collapse to one row.
- Output only the SQL statement, no markdown or explanation.
"""


class SQLGenerator:
    """Generate executable SQL from natural language + retrieved schema."""

    def __init__(self):
        self.settings = get_settings()

    def generate(self, user_query: str, schema_context: str) -> str:
        """Return a single SQL string (no markdown)."""
        prompt = f"""You are a SQL expert. Generate a single, executable SQL query.

Schema context (use only these tables and columns):
{schema_context}

Rules:
{SQL_RULES}

User question: {user_query}

Output only the SQL query, nothing else."""
        raw = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=self.settings.llm_model,
            temperature=0,
        )
        return self._extract_sql(raw)

    def _extract_sql(self, raw: str) -> str:
        """Remove markdown code fences if present."""
        if raw.startswith("```"):
            lines = raw.split("\n")
            start = 1 if lines[0].startswith("```sql") else 0
            end = next((i for i, l in enumerate(lines) if l.strip() == "```"), len(lines))
            raw = "\n".join(lines[start:end])
        return raw.strip()
