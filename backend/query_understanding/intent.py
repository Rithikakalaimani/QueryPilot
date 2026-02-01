"""Convert natural language into structured intent (SELECT/aggregation/filter/join)."""
from __future__ import annotations
from dataclasses import dataclass
from config import get_settings
from llm import chat_completion


@dataclass
class QueryIntent:
    intent: str  # SELECT | aggregation | filter | join
    entities: list[str]  # table/column hints
    conditions: list[str]  # filter hints
    summary: str  # one-line summary for retrieval


class QueryUnderstanding:
    """Identify intent and entities from user NL query."""

    def __init__(self):
        self.settings = get_settings()

    def understand(self, user_query: str) -> QueryIntent:
        """Parse NL into intent, entities, conditions, summary."""
        prompt = f"""Analyze this natural language database question. Output a structured representation.

User question: {user_query}

Respond in this exact format (one line each):
INTENT: [one of: SELECT, aggregation, filter, join]
ENTITIES: [comma-separated likely table/column names or concepts, e.g. customers, orders, customer_name]
CONDITIONS: [comma-separated filter hints, e.g. status=active, date range]
SUMMARY: [one short sentence describing what the user wants, for semantic search]
"""
        text = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=self.settings.llm_model,
            temperature=0,
        )
        return self._parse_response(text, user_query)

    def _parse_response(self, text: str, fallback_query: str) -> QueryIntent:
        intent = "SELECT"
        entities: list[str] = []
        conditions: list[str] = []
        summary = fallback_query

        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("INTENT:"):
                intent = line.split(":", 1)[1].strip().upper() or "SELECT"
            elif line.upper().startswith("ENTITIES:"):
                raw = line.split(":", 1)[1].strip()
                entities = [x.strip() for x in raw.split(",") if x.strip()]
            elif line.upper().startswith("CONDITIONS:"):
                raw = line.split(":", 1)[1].strip()
                conditions = [x.strip() for x in raw.split(",") if x.strip()]
            elif line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip() or fallback_query

        return QueryIntent(intent=intent, entities=entities, conditions=conditions, summary=summary)
