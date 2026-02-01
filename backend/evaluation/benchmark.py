"""Run RAGAS benchmark and log metrics."""
from __future__ import annotations
from dataclasses import asdict
from .benchmark_data import get_benchmark
from .ragas_metrics import RAGASEvaluator, EvaluationResult


class BenchmarkRunner:
    """Run full benchmark set and aggregate RAGAS metrics."""

    def __init__(self):
        self.evaluator = RAGASEvaluator()

    def run(self) -> dict:
        """Run benchmark and return aggregated metrics + per-item results."""
        items = get_benchmark()
        results: list[EvaluationResult] = self.evaluator.evaluate_benchmark(items)

        # Aggregate
        n = len(results)
        faithfulness = [r.faithfulness_score for r in results if r.faithfulness_score is not None]
        relevancy = [r.answer_relevancy_score for r in results if r.answer_relevancy_score is not None]
        precision = [r.context_precision for r in results if r.context_precision is not None]
        recall = [r.context_recall for r in results if r.context_recall is not None]
        exec_acc = [r.execution_accuracy for r in results if r.execution_accuracy is not None]

        return {
            "n": n,
            "faithfulness_avg": sum(faithfulness) / len(faithfulness) if faithfulness else 0,
            "answer_relevancy_avg": sum(relevancy) / len(relevancy) if relevancy else 0,
            "context_precision_avg": sum(precision) / len(precision) if precision else 0,
            "context_recall_avg": sum(recall) / len(recall) if recall else 0,
            "execution_accuracy_avg": sum(exec_acc) / len(exec_acc) if exec_acc else 0,
            "results": [
                {
                    "question": r.question,
                    "generated_sql": r.generated_sql,
                    "execution_success": r.execution_success,
                    "faithfulness": r.faithfulness_score,
                    "answer_relevancy": r.answer_relevancy_score,
                    "context_precision": r.context_precision,
                    "context_recall": r.context_recall,
                    "execution_accuracy": r.execution_accuracy,
                    "error": r.error,
                }
                for r in results
            ],
        }
