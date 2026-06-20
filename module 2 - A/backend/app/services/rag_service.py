"""
RAG Service using ChromaDB + sentence-transformers.
Handles chunking, embedding, and retrieval of medical records.
"""

import os
import uuid
import logging
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    _chroma_client = None
    _embedding_model = None
    _initialized = False

    @classmethod
    def _initialize(cls):
        if cls._initialized:
            return
            
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            
            # Setup ChromaDB
            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
            cls._chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            
            # Setup Embeddings
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            cls._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
            cls._initialized = True
            logger.info("RAG Service initialized successfully")
        except ImportError:
            logger.error("chromadb or sentence-transformers not installed. RAG disabled.")

    def _get_collection(self, patient_id: str):
        self._initialize()
        if not self._chroma_client:
            raise Exception("ChromaDB not available")
            
        collection_name = f"{settings.CHROMA_COLLECTION_PREFIX}{patient_id.replace('-', '_')}"
        return self._chroma_client.get_or_create_collection(name=collection_name)

    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
        """Simple character-based chunking with overlap."""
        if not text:
            return []
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    async def index_record(
        self, patient_id: str, record_id: str, record_type: str, title: str, text: str, date_str: str = ""
    ) -> List[str]:
        """Chunk, embed, and index a record into the patient's Chroma collection."""
        self._initialize()
        if not self._embedding_model or not text.strip():
            return []
            
        collection = self._get_collection(patient_id)
        chunks = self._chunk_text(text, settings.RAG_CHUNK_SIZE, settings.RAG_CHUNK_OVERLAP)
        
        if not chunks:
            return []
            
        embeddings = self._embedding_model.encode(chunks).tolist()
        
        doc_ids = [f"{record_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{
            "record_id": record_id,
            "record_type": record_type,
            "title": title,
            "date": date_str,
            "chunk_index": i
        } for i in range(len(chunks))]
        
        # Upsert to Chroma
        collection.upsert(
            ids=doc_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        logger.info(f"Indexed {len(chunks)} chunks for record {record_id} (Patient: {patient_id})")
        return doc_ids

    async def remove_record(self, patient_id: str, record_id: str):
        """Remove a record's chunks from ChromaDB (e.g. on soft delete/archive)."""
        self._initialize()
        if not self._chroma_client:
            return
            
        collection = self._get_collection(patient_id)
        # ChromaDB allows deleting by metadata
        collection.delete(where={"record_id": record_id})
        logger.info(f"Removed chunks for record {record_id} (Patient: {patient_id})")

    async def query(self, patient_id: str, query_text: str, top_k: int = 5, allowed_record_types: List[str] = None) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for a question."""
        self._initialize()
        if not self._embedding_model:
            return []
            
        collection = self._get_collection(patient_id)
        
        # If collection is empty, querying will fail. Check count.
        if collection.count() == 0:
            return []
            
        query_embedding = self._embedding_model.encode(query_text).tolist()
        
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }
        
        if allowed_record_types:
            query_kwargs["where"] = {"record_type": {"$in": allowed_record_types}}
            
        results = collection.query(**query_kwargs)
        
        retrieved = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]
            
            for doc, meta, dist in zip(docs, metas, dists):
                # Convert distance to a pseudo-relevance score (1 - normalized distance)
                # Note: exact conversion depends on distance metric (L2 vs Cosine)
                score = max(0.0, 1.0 - (dist / 2.0)) 
                retrieved.append({
                    "text": doc,
                    "record_id": meta.get("record_id"),
                    "record_type": meta.get("record_type"),
                    "record_title": meta.get("title"),
                    "record_date": meta.get("date"),
                    "score": score
                })
                
        return retrieved

rag_service = RAGService()
