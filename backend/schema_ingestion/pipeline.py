"""Phase 1 pipeline: extract schema -> chunk -> embed -> store in FAISS."""
from __future__ import annotations
import uuid
from schema_ingestion.extractor import SchemaExtractor
from schema_ingestion.chunker import SchemaChunker
from schema_ingestion.embedder import SchemaEmbedder
from schema_ingestion.vector_store import FAISSSchemaStore
from connection import ConnectionConfig, get_connection


class SchemaIngestionPipeline:
    """Orchestrate schema extraction, chunking, embedding, and vector storage."""

    def __init__(self, connection_config: ConnectionConfig | None = None):
        conn = get_connection(connection_config)
        self.extractor = SchemaExtractor(connection_config=conn)
        self.chunker = SchemaChunker()
        self.embedder = SchemaEmbedder()
        self.store = FAISSSchemaStore(connection_key=conn.connection_key())

    def run(self) -> dict:
        """Run full pipeline. Returns stats (tables, chunks, vectors)."""
        schema = self.extractor.extract()
        chunks = self.chunker.chunk(schema)
        embedded = self.embedder.embed_chunks(chunks)

        ids = [f"chunk-{uuid.uuid4().hex[:12]}" for _ in chunks]
        vectors = [v for _, v in embedded]
        metadatas = [
            {
                "table_name": c.table_name,
                "chunk_type": c.chunk_type,
                "text": c.text[:1000],  # Pinecone metadata size limit
            }
            | c.metadata
            for c in chunks
        ]
        # Normalize metadata values for JSON/store
        for m in metadatas:
            for k in list(m.keys()):
                val = m[k]
                if isinstance(val, list):
                    m[k] = ",".join(str(x) for x in val)

        self.store.upsert(ids=ids, vectors=vectors, metadatas=metadatas)

        return {
            "tables": len(schema.tables),
            "chunks": len(chunks),
            "vectors_upserted": len(ids),
        }
