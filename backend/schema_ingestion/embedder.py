"""Generate embeddings for schema chunks (OpenAI or HuggingFace)."""
from __future__ import annotations
from openai import OpenAI
from schema_ingestion.chunker import SchemaChunk
from config import get_settings


class SchemaEmbedder:
    """Embed schema chunks using OpenAI or HuggingFace (local, no API key)."""

    def __init__(self):
        self.settings = get_settings()
        self._client: OpenAI | None = None
        self._hf_model = None

    def _use_openai(self) -> bool:
        """Use OpenAI only when provider is openai and API key is set."""
        return (
            self.settings.embedding_provider == "openai"
            and bool(self.settings.openai_api_key)
        )

    def _get_openai_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return list of embedding vectors for each text."""
        if self._use_openai():
            client = self._get_openai_client()
            resp = client.embeddings.create(
                model=self.settings.embedding_model,
                input=texts,
            )
            return [d.embedding for d in resp.data]
        return self._embed_hf(texts)

    def _embed_hf(self, texts: list[str]) -> list[list[float]]:
        try:
            from sentence_transformers import SentenceTransformer
            if self._hf_model is None:
                model_name = self.settings.embedding_model or "all-MiniLM-L6-v2"
                self._hf_model = SentenceTransformer(model_name)
            emb = self._hf_model.encode(texts)
            return [e.tolist() for e in emb]
        except Exception as e:
            raise RuntimeError(f"HuggingFace embedding failed: {e}") from e

    def embed_chunks(self, chunks: list[SchemaChunk]) -> list[tuple[SchemaChunk, list[float]]]:
        """Embed all chunks; return (chunk, vector) pairs."""
        texts = [c.text for c in chunks]
        vectors = self.embed_texts(texts)
        return list(zip(chunks, vectors))
