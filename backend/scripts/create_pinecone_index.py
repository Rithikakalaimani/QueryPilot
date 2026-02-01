"""Create Pinecone index for schema embeddings. Run once before first sync."""
import os
import sys

# Add parent to path so config is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

import pinecone

# OpenAI text-embedding-3-small = 1536; text-embedding-ada-002 = 1536; MiniLM = 384
EMBEDDING_DIM = 1536
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "text2sql-schema")

def main():
    api_key = os.getenv("PINECONE_API_KEY")
    env = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    if not api_key:
        print("Set PINECONE_API_KEY in .env")
        sys.exit(1)
    pinecone.init(api_key=api_key, environment=env)
    if INDEX_NAME in pinecone.list_indexes():
        print(f"Index {INDEX_NAME} already exists.")
        return
    pinecone.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIM,
        metric="cosine",
    )
    print(f"Created index {INDEX_NAME} with dimension={EMBEDDING_DIM}.")

if __name__ == "__main__":
    main()
