"""In-memory FAISS vector store: no disk I/O (production-friendly, stateless across restarts)."""
from __future__ import annotations
import numpy as np
import faiss
from config import get_settings
from typing import Any

# Global in-process store per connection_key so sync and chat share the same index
_stores: dict[str, tuple[faiss.IndexFlatIP, list[str], list[dict]]] = {}


def _store_key(connection_key: str | None) -> str:
    return connection_key or "default"


class FAISSSchemaStore:
    """In-memory vector store: upsert and query by connection_key. No disk persistence."""

    def __init__(self, connection_key: str | None = None):
        self.settings = get_settings()
        self.connection_key = connection_key
        self._key = _store_key(connection_key)
        self._index: faiss.IndexFlatIP | None = None
        self._id_list: list[str] = []
        self._metadatas: list[dict] = []
        if self._key in _stores:
            self._index, self._id_list, self._metadatas = _stores[self._key]

    def upsert(self, ids: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None:
        """Replace store with these vectors (full replace). Vectors should be normalized for cosine."""
        if not vectors:
            return
        dim = len(vectors[0])
        arr = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(arr)
        index = faiss.IndexFlatIP(dim)
        index.add(arr)
        self._index = index
        self._id_list = list(ids)
        self._metadatas = list(metadatas)
        _stores[self._key] = (self._index, self._id_list, self._metadatas)

    def query(self, vector: list[float], top_k: int = 10) -> list[dict]:
        """Return top_k matches with id, score, and metadata."""
        if self._index is None or not self._id_list:
            return []
        arr = np.array([vector], dtype=np.float32)
        faiss.normalize_L2(arr)
        scores, indices = self._index.search(arr, min(top_k, len(self._id_list)))
        out = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:
                continue
            id_ = self._id_list[idx]
            score = float(scores[0][i])
            meta = self._metadatas[idx] if idx < len(self._metadatas) else {}
            out.append({"id": id_, "score": score, "metadata": meta})
        return out
