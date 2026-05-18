"""
Vector Store - Persistent Semantic Memory

Uses ChromaDB (local, embedded) for:
  - Storing research findings, competitor data, industry context
  - Semantic similarity retrieval for the Memory Agent

Assignment requirement: Section B - Long-Term Memory
  - Persistent vector memory
  - Retrieval system
  - Context recall
"""

import hashlib
import structlog
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

from app.config import settings

logger = structlog.get_logger()

if HAS_CHROMADB:
    # Persist to disk so memory survives restarts
    _chroma_client = chromadb.Client(
        ChromaSettings(
            is_persistent=True,
            persist_directory=settings.chroma_persist_dir,
            anonymized_telemetry=False,
        )
    )
else:
    class MockCollection:
        def __init__(self, name: str):
            self.name = name
            self._data = {}

        def upsert(self, ids, embeddings, documents, metadatas=None):
            for i, id_ in enumerate(ids):
                self._data[id_] = {
                    "id": id_,
                    "embedding": embeddings[i],
                    "document": documents[i],
                    "metadata": metadatas[i] if metadatas else {}
                }

        def count(self):
            return len(self._data)

        def query(self, query_embeddings, n_results=5, where=None, include=None):
            ids = list(self._data.keys())[:n_results]
            documents = [self._data[id_]["document"] for id_ in ids]
            metadatas = [self._data[id_]["metadata"] for id_ in ids]
            distances = [0.1 for _ in ids]
            return {
                "ids": [ids],
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [distances]
            }

    class MockChromaClient:
        def __init__(self, *args, **kwargs):
            self._collections = {}

        def get_or_create_collection(self, name: str, metadata=None):
            if name not in self._collections:
                self._collections[name] = MockCollection(name)
            return self._collections[name]

        def delete_collection(self, name: str):
            if name in self._collections:
                del self._collections[name]

    _chroma_client = MockChromaClient()
    logger.warning("chromadb_fallback_activated", reason="chromadb not installed on platform")



def _get_collection(collection_name: str):
    """Get or create a named ChromaDB collection."""
    return _chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_document(
    collection_name: str,
    text: str,
    embedding: list[float],
    metadata: Optional[dict] = None,
    doc_id: Optional[str] = None,
) -> str:
    """
    Store a document with its embedding in the vector store.
    Returns the document ID.
    Idempotent: same content will not be duplicated (hash-based ID).
    """
    if doc_id is None:
        # Deterministic ID based on content hash — prevents duplicates
        doc_id = hashlib.sha256(text.encode()).hexdigest()[:32]

    collection = _get_collection(collection_name)
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata or {}],
    )

    logger.info(
        "vector_upsert",
        collection=collection_name,
        doc_id=doc_id,
        text_preview=text[:80],
    )
    return doc_id


def query_similar(
    collection_name: str,
    query_embedding: list[float],
    n_results: int = 5,
    where: Optional[dict] = None,
) -> list[dict]:
    """
    Query the vector store for semantically similar documents.
    Returns list of {id, document, metadata, distance} dicts.
    """
    collection = _get_collection(collection_name)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),  # guard: n_results > collection size
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.error("vector_query_failed", collection=collection_name, error=str(e))
        return []

    if not results["ids"] or not results["ids"][0]:
        return []

    return [
        {
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "distance": results["distances"][0][i] if results["distances"] else 1.0,
        }
        for i in range(len(results["ids"][0]))
    ]


def delete_collection(collection_name: str):
    """Delete an entire collection (e.g., when a job is purged)."""
    try:
        _chroma_client.delete_collection(collection_name)
        logger.info("collection_deleted", collection=collection_name)
    except Exception as e:
        logger.warning("collection_delete_failed", collection=collection_name, error=str(e))
