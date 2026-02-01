"""Redis cache: sync job status, schema table list, optional chat result cache."""
from __future__ import annotations
import json
from typing import Any

_redis_client: Any = None
_sync_jobs_fallback: dict[str, dict[str, Any]] = {}


def get_redis():
    """Return Redis client if configured, else None."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        from config import get_settings
        s = get_settings()
        if not s.redis_host or not s.redis_password:
            return None
        import redis
        _redis_client = redis.Redis(
            host=s.redis_host,
            port=s.redis_port,
            username=s.redis_username or "default",
            password=s.redis_password,
            decode_responses=True,
        )
        _redis_client.ping()
        return _redis_client
    except Exception:
        return None


def _key_sync_job(job_id: str) -> str:
    return f"querypilot:sync:job:{job_id}"


def _key_schema_tables(connection_key: str) -> str:
    return f"querypilot:schema:tables:{connection_key}"


def _key_chat_cache(connection_key: str, message_hash: str) -> str:
    return f"querypilot:chat:{connection_key}:{message_hash}"


# --- Sync job status (Redis or in-memory fallback) ---

def sync_job_set(job_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
    payload = {"status": status, "result": result, "error": error}
    r = get_redis()
    if r:
        try:
            r.set(_key_sync_job(job_id), json.dumps(payload), ex=86400)
        except Exception:
            pass
    _sync_jobs_fallback[job_id] = payload


def sync_job_get(job_id: str) -> dict | None:
    r = get_redis()
    if r:
        try:
            raw = r.get(_key_sync_job(job_id))
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _sync_jobs_fallback.get(job_id)


# --- Schema table list cache (so "tables separately" doesn't hit DB every time) ---

def schema_tables_set(connection_key: str, table_names: list[str]) -> None:
    r = get_redis()
    if r:
        try:
            r.set(_key_schema_tables(connection_key), json.dumps(table_names), ex=3600)
        except Exception:
            pass


def schema_tables_get(connection_key: str) -> list[str] | None:
    r = get_redis()
    if r:
        try:
            raw = r.get(_key_schema_tables(connection_key))
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return None


# --- Chat result cache (optional - same question returns cached response) ---

CHAT_CACHE_TTL = 300  # 5 min


def chat_cache_set(connection_key: str, message_hash: str, response: dict) -> None:
    r = get_redis()
    if r:
        try:
            r.set(_key_chat_cache(connection_key, message_hash), json.dumps(response), ex=CHAT_CACHE_TTL)
        except Exception:
            pass


def chat_cache_get(connection_key: str, message_hash: str) -> dict | None:
    r = get_redis()
    if r:
        try:
            raw = r.get(_key_chat_cache(connection_key, message_hash))
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return None
