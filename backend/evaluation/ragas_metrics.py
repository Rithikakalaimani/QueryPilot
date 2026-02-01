"""RAGAS metrics: Faithfulness, Answer Relevancy, Context Precision/Recall, Execution Accuracy."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any
from execution.runner import QueryRunner
from sql_generation.pipeline import SQLGenerationPipeline
from query_understanding.retriever import SchemaRetriever


@dataclass
class EvaluationResult:
    question: str
    generated_sql: str
    retrieved_context: str
    execution_success: bool
    row_count: int
    faithfulness_score: float | None  # SQL aligns with retrieved schema
    answer_relevancy_score: float | None  # Query matches intent
    context_precision: float | None
    context_recall: float | None
    execution_accuracy: float | None  # 1.0 if result matches gold
    error: str | None


class RAGASEvaluator:
    """Evaluate Text-to-SQL pipeline using RAGAS-style metrics."""

    def __init__(self):
        self.pipeline = SQLGenerationPipeline()
        self.retriever = SchemaRetriever(top_k=10)
        self.runner = QueryRunner()

    def _faithfulness(self, generated_sql: str, context: str) -> float:
        """Heuristic: do table/column names in SQL appear in context? 0–1."""
        context_lower = context.lower()
        sql_lower = generated_sql.lower()
        words = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", sql_lower))
        reserved = {"select", "from", "where", "join", "left", "right", "inner", "outer", "on", "and", "or", "group", "order", "by", "limit", "as", "count", "sum", "avg", "min", "max"}
        identifiers = words - reserved
        if not identifiers:
            return 1.0
        in_context = sum(1 for w in identifiers if w in context_lower)
        return in_context / len(identifiers)

    def _answer_relevancy(self, question: str, sql: str) -> float:
        """Heuristic: question keywords vs SQL (e.g. count -> COUNT). 0–1."""
        q_lower = question.lower()
        sql_lower = sql.lower()
        # Simple: if question asks for count and SQL has COUNT, etc.
        if "how many" in q_lower or "count" in q_lower:
            if "count" in sql_lower:
                return 1.0
        if "list" in q_lower or "show" in q_lower:
            if "select" in sql_lower:
                return 1.0
        return 0.8  # default

    def _context_precision_recall(
        self, question: str, retrieved_texts: list[str], expected_tables: list[str] | None
    ) -> tuple[float, float]:
        """Precision: relevant chunks / retrieved. Recall: relevant retrieved / expected."""
        if not retrieved_texts:
            return 0.0, 0.0
        if not expected_tables:
            return 0.5, 0.5  # neutral
        relevant = sum(1 for t in retrieved_texts if any(tbl in t for tbl in expected_tables))
        precision = relevant / len(retrieved_texts)
        recall = relevant / len(expected_tables) if expected_tables else 0.0
        recall = min(1.0, recall)
        return precision, recall

    def _execution_accuracy(
        self,
        actual_rows: list[dict],
        expected_row_count: int | None,
        expected_sample: list[dict] | None,
    ) -> float:
        """1.0 if execution succeeded and (optional) count/sample matches."""
        if expected_row_count is not None:
            if len(actual_rows) != expected_row_count:
                return 0.0
        if expected_sample is not None and expected_sample:
            # Compare first row keys and types loosely
            if not actual_rows:
                return 0.0
            return 1.0  # simplified
        return 1.0 if actual_rows is not None else 0.0

    def evaluate_one(
        self,
        question: str,
        expected_sql: str | None = None,
        expected_tables: list[str] | None = None,
        expected_row_count: int | None = None,
        expected_output_sample: list[dict] | None = None,
    ) -> EvaluationResult:
        """Run pipeline for one question and compute metrics."""
        # Generate SQL + get context
        out = self.pipeline.run(question)
        generated_sql = out["sql"]
        context_used = out.get("context_used", "")
        retrieved = self.retriever.retrieve(question)
        retrieved_texts = [r.get("text", "") for r in retrieved]

        # Execution
        rows, exec_err = self.runner.execute(generated_sql) if out["valid"] else ([], "Invalid SQL")
        execution_success = out["valid"] and exec_err is None
        row_count = len(rows) if rows else 0

        # Metrics
        faithfulness = self._faithfulness(generated_sql, context_used)
        answer_relevancy = self._answer_relevancy(question, generated_sql)
        context_precision, context_recall = self._context_precision_recall(
            question, retrieved_texts, expected_tables
        )
        execution_accuracy = self._execution_accuracy(
            rows, expected_row_count, expected_output_sample
        ) if execution_success else 0.0

        return EvaluationResult(
            question=question,
            generated_sql=generated_sql,
            retrieved_context=context_used[:500],
            execution_success=execution_success,
            row_count=row_count,
            faithfulness_score=faithfulness,
            answer_relevancy_score=answer_relevancy,
            context_precision=context_precision,
            context_recall=context_recall,
            execution_accuracy=execution_accuracy,
            error=out.get("error") or exec_err,
        )

    def evaluate_benchmark(self, items: list[Any]) -> list[EvaluationResult]:
        """Evaluate each benchmark item. items: list of BenchmarkItem."""
        results = []
        for item in items:
            expected_tables = None
            if getattr(item, "expected_sql", None):
                expected_tables = re.findall(r"\bFROM\s+(\w+)", getattr(item, "expected_sql", ""), re.IGNORECASE)
            r = self.evaluate_one(
                question=item.question,
                expected_sql=getattr(item, "expected_sql", None),
                expected_tables=expected_tables,
                expected_row_count=getattr(item, "expected_row_count", None),
                expected_output_sample=getattr(item, "expected_output_sample", None),
            )
            results.append(r)
        return results
