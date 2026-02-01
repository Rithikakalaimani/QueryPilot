"""Benchmark set: NL question -> expected SQL / expected output for RAGAS evaluation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkItem:
    question: str
    expected_sql: str | None  # optional gold SQL
    expected_output_sample: list[dict[str, Any]] | None  # optional gold result sample
    expected_row_count: int | None  # optional expected count


# Example benchmark set; extend with your own DB schema-specific questions.
DEFAULT_BENCHMARK: list[BenchmarkItem] = [
    BenchmarkItem(
        question="How many users are there?",
        expected_sql="SELECT COUNT(*) FROM users",
        expected_output_sample=None,
        expected_row_count=1,
    ),
    BenchmarkItem(
        question="List the first 10 orders",
        expected_sql="SELECT * FROM orders LIMIT 10",
        expected_output_sample=None,
        expected_row_count=10,
    ),
    BenchmarkItem(
        question="What are the names of all products?",
        expected_sql="SELECT name FROM products",
        expected_output_sample=None,
        expected_row_count=None,
    ),
]


def get_benchmark() -> list[BenchmarkItem]:
    """Return the benchmark set (load from file or use default)."""
    return list(DEFAULT_BENCHMARK)
