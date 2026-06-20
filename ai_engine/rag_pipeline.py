import chromadb
from sentence_transformers import SentenceTransformer
import os
import uuid

# Initialize ChromaDB in a local directory
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'chroma_data')
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# We use a single collection for all patient records, filtering by metadata.
collection = chroma_client.get_or_create_collection(name="patient_records")

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def add_to_rag_context(patient_id, record_type, content):
    """
    Adds a new record (prescription, smartwatch summary, old diagnosis) to the patient's RAG context.
    """
    doc_id = str(uuid.uuid4())
    embedding = embedder.encode(content).tolist()
    
    collection.add(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"patient_id": patient_id, "type": record_type}]
    )
    return doc_id

def retrieve_patient_context(patient_id, query, n_results=5):
    """
    Retrieves the most relevant past records for the patient given a specific query.
    """
    query_embedding = embedder.encode(query).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"patient_id": patient_id}
    )
    
    if not results or not results['documents'] or not results['documents'][0]:
        return []
    
    # Return list of matched documents
    return results['documents'][0]

def init_mock_data():
    """
    Initialize some mock historical data for DOC001/PAT001 for demonstration purposes.
    """
    add_to_rag_context("PAT001", "smartwatch", "Patient's average heart rate has been stable at 72 bpm. Blood pressure stable. Sleep average 7.5 hours.")
    add_to_rag_context("PAT001", "prescription_history", "Previously prescribed Metformin 500mg twice a day for Diabetes.")
    add_to_rag_context("PAT001", "patient_history", "Patient is allergic to Penicillin.")
    add_to_rag_context("PAT001", "doctor_reports", "Last visit showed normal blood pressure, no signs of acute cardiac conditions.")

# Ensure some mock data exists
try:
    if collection.count() == 0:
        init_mock_data()
except Exception:
    pass
