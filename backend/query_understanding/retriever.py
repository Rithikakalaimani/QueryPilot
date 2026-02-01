"""Retrieve relevant schema chunks via similarity search (FAISS + embeddings)."""
from __future__ import annotations
from schema_ingestion.embedder import SchemaEmbedder
from schema_ingestion.vector_store import FAISSSchemaStore
from config import get_settings


class SchemaRetriever:
    """Fetch schema context for a user query using RAG retrieval."""

    def __init__(self, connection_key: str | None = None, top_k: int = 10):
        self.embedder = SchemaEmbedder()
        self.store = FAISSSchemaStore(connection_key=connection_key)
        self.top_k = top_k

    def retrieve(self, query_text: str) -> list[dict]:
        """Return top_k relevant schema chunks (text + metadata)."""
        vectors = self.embedder.embed_texts([query_text])
        matches = self.store.query(vectors[0], top_k=self.top_k)
        return [
            {
                "id": m["id"],
                "score": m["score"],
                "text": m["metadata"].get("text", ""),
                "table_name": m["metadata"].get("table_name", ""),
                "chunk_type": m["metadata"].get("chunk_type", ""),
            }
            for m in matches
        ]

    def get_context_for_prompt(self, query_text: str) -> str:
        """Return a single string of retrieved schema context for the LLM prompt."""
        chunks = self.retrieve(query_text)
        if not chunks:
            return "No schema context retrieved."
        lines = []
        seen = set()
        for c in chunks:
            text = c.get("text") or ""
            if text and text not in seen:
                seen.add(text)
                lines.append(text)
        return "\n\n---\n\n".join(lines)
