"""Phase 3 pipeline: NL -> intent + retrieval -> generate SQL -> validate."""
from __future__ import annotations
from query_understanding.intent import QueryUnderstanding
from query_understanding.retriever import SchemaRetriever
from sql_generation.generator import SQLGenerator
from sql_generation.validator import SQLValidator
from schema_ingestion.extractor import SchemaExtractor
from config import get_settings
from connection import ConnectionConfig, get_connection


def _wants_tables_separately(user_query: str) -> bool:
    """True if user asks for each table's result separately (no joins)."""
    q = user_query.lower().strip()
    if not q:
        return False
    separately = "separately" in q or "each table" in q or "per table" in q
    no_joins = "no join" in q or "without join" in q or "don't use join" in q or "dont use join" in q
    all_tables = "all table" in q or "list table" in q or "every table" in q or "each table" in q
    return (separately or no_joins) and (all_tables or "table" in q)


class SQLGenerationPipeline:
    """End-to-end: user query -> validated SQL."""

    def __init__(self, connection_config: ConnectionConfig | None = None):
        conn = get_connection(connection_config)
        self.conn = conn
        self.understanding = QueryUnderstanding()
        self.retriever = SchemaRetriever(connection_key=conn.connection_key(), top_k=10)
        self.generator = SQLGenerator()
        self.validator = SQLValidator(connection_config=conn)
        self.settings = get_settings()

    def run(self, user_query: str) -> dict:
        """Return { sql, valid, error, intent, context_used, sql_list? }."""
        intent = self.understanding.understand(user_query)

        # When user wants "all tables separately, no joins" -> one SELECT per table
        if _wants_tables_separately(user_query):
            sql_list = self._generate_separate_table_queries()
            if sql_list:
                sql_display = ";\n\n".join(sql_list)
                return {
                    "sql": sql_display,
                    "valid": True,
                    "error": "",
                    "sql_list": sql_list,
                    "intent": {
                        "intent": intent.intent,
                        "entities": intent.entities,
                        "summary": intent.summary,
                    },
                    "context_used": "",
                }
        # Normal single-query path
        retrieval_query = f"{intent.summary} {user_query}"
        schema_context = self.retriever.get_context_for_prompt(retrieval_query)
        sql = self.generator.generate(user_query, schema_context)

        # Enforce LIMIT if missing
        if self.settings.max_rows_limit and "LIMIT" not in sql.upper() and "SELECT" in sql.upper():
            sql = sql.rstrip()
            if not sql.rstrip().endswith(";"):
                sql = sql + f" LIMIT {self.settings.max_rows_limit}"
            else:
                sql = sql[:-1].rstrip() + f" LIMIT {self.settings.max_rows_limit};"

        valid, err = self.validator.validate(sql)
        return {
            "sql": sql,
            "valid": valid,
            "error": err,
            "intent": {
                "intent": intent.intent,
                "entities": intent.entities,
                "summary": intent.summary,
            },
            "context_used": schema_context[:500] + "..." if len(schema_context) > 500 else schema_context,
        }

    def _generate_separate_table_queries(self) -> list[str]:
        """One SELECT per table, no joins. Use Redis cache for table list if available."""
        from cache import schema_tables_get
        limit = self.settings.max_rows_limit or 1000
        is_pg = self.conn.database_type == "postgres"
        table_names = schema_tables_get(self.conn.connection_key())
        if not table_names:
            extractor = SchemaExtractor(connection_config=self.conn)
            schema = extractor.extract()
            table_names = [t.name for t in schema.tables]
        out = []
        for name in table_names:
            quoted = f'"{name}"' if is_pg else f"`{name}`"
            out.append(f"SELECT * FROM {quoted} LIMIT {limit}")
        return out
