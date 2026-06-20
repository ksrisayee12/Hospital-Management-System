"""
MODULE 2 — PART B: Embedding Service
Sentence-Transformers → ChromaDB, per-patient isolated collections.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from core.config import get_settings
from core.exceptions import EmbeddingError, ChromaDBError
from core.logging_config import get_logger
from core.security import hash_patient_collection_name

settings = get_settings()
logger = get_logger(__name__)


class EmbeddingService:
    """
    Manages per-patient ChromaDB collections.
    Each patient gets an isolated collection named by hashed patient_id.
    """

    _model: Optional[SentenceTransformer] = None
    _chroma_client: Optional[chromadb.HttpClient] = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", settings.embedding_model_name)
            self._model = SentenceTransformer(settings.embedding_model_name)
        return self._model

    def _get_chroma(self) -> chromadb.HttpClient:
        if self._chroma_client is None:
            self._chroma_client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._chroma_client

    def _get_patient_collection(self, patient_id: str) -> chromadb.Collection:
        """Get or create an isolated ChromaDB collection for this patient."""
        collection_name = hash_patient_collection_name(patient_id)
        try:
            return self._get_chroma().get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            raise ChromaDBError(f"Cannot access ChromaDB collection: {exc}") from exc

    # ── Text Chunking ────────────────────────────

    def chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping token-approximate chunks."""
        words = text.split()
        chunk_size = settings.rag_chunk_size
        overlap = settings.rag_chunk_overlap
        chunks, i = [], 0
        while i < len(words):
            chunk = " ".join(words[i: i + chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap
        return [c for c in chunks if c.strip()]

    # ── Embedding ────────────────────────────────

    async def embed_document(
        self,
        patient_id: str,
        source_type: str,
        source_id: str,
        text: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> list[str]:
        """
        Chunk, embed and upsert a document for a patient.
        Returns list of chroma document IDs created.
        """
        if not text.strip():
            raise EmbeddingError("Empty text — nothing to embed")

        chunks = self.chunk_text(text)
        try:
            model = self._get_model()
            vectors = model.encode(chunks, batch_size=settings.embedding_batch_size).tolist()
        except Exception as exc:
            raise EmbeddingError(f"Embedding model error: {exc}") from exc

        collection = self._get_patient_collection(patient_id)
        chroma_ids = []
        documents, embeddings, metas, ids = [], [], [], []

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            doc_id = f"{source_type}_{source_id}_chunk_{idx}"
            chroma_ids.append(doc_id)
            ids.append(doc_id)
            documents.append(chunk)
            embeddings.append(vector)
            metas.append({
                "patient_id": patient_id,
                "source_type": source_type,
                "source_id": source_id,
                "chunk_index": idx,
                "embedded_at": datetime.utcnow().isoformat(),
                **(metadata or {}),
            })

        try:
            collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metas)
        except Exception as exc:
            raise ChromaDBError(f"ChromaDB upsert failed: {exc}") from exc

        logger.info(
            "Embedded document",
            extra={"patient_id": patient_id, "source": source_type, "chunks": len(chunks)},
        )
        return chroma_ids

    async def delete_document(self, patient_id: str, source_type: str, source_id: str) -> int:
        """Remove all chunks for a document from the patient's collection."""
        collection = self._get_patient_collection(patient_id)
        prefix = f"{source_type}_{source_id}_chunk_"
        results = collection.get(where={"source_id": source_id})
        ids_to_delete = [i for i in results.get("ids", []) if i.startswith(prefix)]
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

    async def query(
        self,
        patient_id: str,
        query_text: str,
        top_k: int = None,
        source_type_filter: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Semantic search within a patient's isolated collection.
        Enforces patient isolation — no cross-patient access possible.
        """
        top_k = top_k or settings.rag_top_k
        try:
            model = self._get_model()
            query_vector = model.encode([query_text])[0].tolist()
        except Exception as exc:
            raise EmbeddingError(f"Query embedding failed: {exc}") from exc

        collection = self._get_patient_collection(patient_id)
        where = {}
        if source_type_filter:
            where["source_type"] = source_type_filter

        try:
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where if where else None,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise ChromaDBError(f"ChromaDB query failed: {exc}") from exc

        output = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
            similarity = 1 - dist  # cosine distance → similarity
            if similarity >= settings.rag_similarity_threshold:
                output.append({
                    "chroma_document_id": doc_id,
                    "source_type": meta.get("source_type"),
                    "source_id": meta.get("source_id"),
                    "chunk_text": doc,
                    "relevance_score": round(similarity, 4),
                    "metadata": meta,
                })

        return output

    async def patient_collection_stats(self, patient_id: str) -> dict[str, Any]:
        collection = self._get_patient_collection(patient_id)
        count = collection.count()
        return {"collection_name": hash_patient_collection_name(patient_id), "document_chunks": count}
