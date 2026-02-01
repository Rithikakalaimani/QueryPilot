"""QueryPilot API."""
from __future__ import annotations
import hashlib
import uuid
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

from schema_ingestion.pipeline import SchemaIngestionPipeline
from sql_generation.pipeline import SQLGenerationPipeline
from execution.runner import QueryRunner
from execution.formatter import ResultFormatter
from config import get_settings
from connection import connection_from_request, ConnectionConfig
from cache import sync_job_set, sync_job_get, chat_cache_get, chat_cache_set, schema_tables_set, schema_tables_get

app = FastAPI(title="QueryPilot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionBody(BaseModel):
    """Per-request DB connection (each user can use their own MySQL)."""
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    database_type: str | None = None  # mysql | postgres


class ChatRequest(BaseModel):
    message: str
    include_summary: bool = True
    connection: ConnectionBody | None = None  # omit = use server default (.env)


class SingleResult(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int


class ChatResponse(BaseModel):
    sql: str
    valid: bool
    error: str | None
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    summary: str | None
    intent: dict | None = None
    multi_results: list[SingleResult] | None = None  # when user asks for "tables separately"


class SyncSchemaRequest(BaseModel):
    connection: ConnectionBody | None = None
    async_mode: bool = False  # if True, return job_id and run in background; poll /api/sync-status


class SyncSchemaResponse(BaseModel):
    tables: int
    chunks: int
    vectors_upserted: int


class SyncSchemaAsyncResponse(BaseModel):
    job_id: str
    status: str = "running"
    message: str = "Schema sync started. Poll GET /api/sync-status?job_id=..."


class EvaluationResponse(BaseModel):
    n: int
    faithfulness_avg: float
    answer_relevancy_avg: float
    context_precision_avg: float
    context_recall_avg: float
    execution_accuracy_avg: float
    results: list[dict[str, Any]]


@app.get("/health")
def health():
    return {"status": "ok"}


def _run_sync_job(job_id: str, connection_config: ConnectionConfig | None) -> None:
    """Background task: run schema sync and store result in Redis or in-memory."""
    try:
        pipeline = SchemaIngestionPipeline(connection_config=connection_config)
        stats = pipeline.run()
        sync_job_set(job_id, "done", result=stats, error=None)
        if connection_config:
            from schema_ingestion.extractor import SchemaExtractor
            ext = SchemaExtractor(connection_config=connection_config)
            schema = ext.extract()
            schema_tables_set(connection_config.connection_key(), [t.name for t in schema.tables])
    except Exception as e:
        sync_job_set(job_id, "failed", result=None, error=str(e))


@app.post("/api/sync-schema", response_model=SyncSchemaResponse | SyncSchemaAsyncResponse)
def sync_schema(req: SyncSchemaRequest = SyncSchemaRequest(), background_tasks: BackgroundTasks = None):  # noqa: B008
    """Phase 1: Ingest schema from DB into FAISS. Optional async for large schemas."""
    conn_dict = req.connection.model_dump() if req.connection else None
    if conn_dict:
        conn_dict = {k: v for k, v in conn_dict.items() if v is not None}
    connection_config = connection_from_request(conn_dict)
    if req and req.async_mode:
        job_id = str(uuid.uuid4())[:8]
        sync_job_set(job_id, "running", result=None, error=None)
        background_tasks.add_task(_run_sync_job, job_id, connection_config)
        return SyncSchemaAsyncResponse(job_id=job_id)
    try:
        pipeline = SchemaIngestionPipeline(connection_config=connection_config)
        stats = pipeline.run()
        from schema_ingestion.extractor import SchemaExtractor
        ext = SchemaExtractor(connection_config=connection_config)
        schema = ext.extract()
        schema_tables_set(connection_config.connection_key(), [t.name for t in schema.tables])
        return SyncSchemaResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sync-status")
def sync_status(job_id: str):
    """Poll after POST /api/sync-schema with async_mode=true. Returns status, result, or error."""
    job = sync_job_get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    out = {"job_id": job_id, "status": job["status"]}
    if job.get("status") == "done" and job.get("result"):
        out["result"] = job["result"]
    if job.get("status") == "failed" and job.get("error"):
        out["error"] = job["error"]
    return out


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Phase 2–4: NL -> intent + retrieval -> SQL -> validate -> execute -> format."""
    conn_dict = None
    if req.connection:
        conn_dict = {k: v for k, v in req.connection.model_dump().items() if v is not None}
    connection_config = connection_from_request(conn_dict)
    ckey = connection_config.connection_key()
    msg_hash = hashlib.sha256(req.message.strip().encode()).hexdigest()[:16]
    cached = chat_cache_get(ckey, msg_hash)
    if cached:
        return ChatResponse(**cached)
    try:
        gen = SQLGenerationPipeline(connection_config=connection_config)
        out = gen.run(req.message)
        if not out["valid"]:
            return ChatResponse(
                sql=out["sql"],
                valid=False,
                error=out["error"],
                columns=[],
                rows=[],
                row_count=0,
                summary=None,
                intent=out.get("intent"),
            )
        runner = QueryRunner(connection_config=connection_config)

        # Multiple tables separately (one SELECT per table, no joins)
        if out.get("sql_list"):
            multi_results = []
            errors = []
            for one_sql in out["sql_list"]:
                valid_one, err_one = gen.validator.validate(one_sql)
                if not valid_one:
                    errors.append(f"{one_sql[:50]}...: {err_one}")
                    continue
                rows_one, exec_err = runner.execute(one_sql)
                if exec_err:
                    errors.append(f"{one_sql[:50]}...: {exec_err}")
                    continue
                cols = list(rows_one[0].keys()) if rows_one else []
                row_list = [list(r.values()) for r in rows_one]
                multi_results.append(
                    SingleResult(sql=one_sql, columns=cols, rows=row_list, row_count=len(rows_one))
                )
            summary = f"Returned {len(multi_results)} table(s) separately."
            if errors:
                summary += " " + "; ".join(errors[:3])
            resp = ChatResponse(
                sql=out["sql"],
                valid=True,
                error=None,
                columns=[],
                rows=[],
                row_count=sum(r.row_count for r in multi_results),
                summary=summary,
                intent=out.get("intent"),
                multi_results=multi_results,
            )
            chat_cache_set(ckey, msg_hash, resp.model_dump())
            return resp

        # Single query
        rows, exec_err = runner.execute(out["sql"])
        if exec_err:
            return ChatResponse(
                sql=out["sql"],
                valid=True,
                error=exec_err,
                columns=[],
                rows=[],
                row_count=0,
                summary=None,
                intent=out.get("intent"),
            )
        formatter = ResultFormatter()
        formatted = formatter.format(
            rows, out["sql"], req.message, include_summary=req.include_summary
        )
        resp = ChatResponse(
            sql=out["sql"],
            valid=True,
            error=None,
            columns=formatted["columns"],
            rows=formatted["rows"],
            row_count=formatted["row_count"],
            summary=formatted.get("summary"),
            intent=out.get("intent"),
        )
        chat_cache_set(ckey, msg_hash, resp.model_dump())
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate", response_model=EvaluationResponse)
def run_evaluation():
    """Run RAGAS benchmark and return metrics (requires ragas/datasets; not in requirements-railway.txt)."""
    try:
        from evaluation.benchmark import BenchmarkRunner
        runner = BenchmarkRunner()
        out = runner.run()
        return EvaluationResponse(**out)
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="RAGAS evaluation is not available in this deployment. Install full requirements.txt (ragas, datasets) for /evaluate, or use requirements-railway.txt with OpenAI embeddings only.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
