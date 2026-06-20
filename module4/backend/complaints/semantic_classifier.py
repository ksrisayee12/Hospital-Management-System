"""
MiniLM-based semantic complaint classifier.

This implements the upgrade path stubbed in complaints/service.py.
It uses sentence-transformers (all-MiniLM-L6-v2) to embed the
complaint description and compare via cosine similarity against a
labeled seed set of example complaints per priority level.

Blend strategy (healthcare governance rule):
  If the embedding classifier and the keyword classifier DISAGREE,
  escalate to the HIGHER of the two priorities. NEVER silently downgrade
  — false negatives on priority are worse than false positives in
  healthcare governance contexts.

Feature flag:
  This module is only imported when ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER=True.
  Default is False — the existing keyword classifier remains the default.
"""

from module4.backend.models.complaint import ComplaintPriority

# ---------------------------------------------------------------------------
# Labeled seed set: ≥5 realistic examples per priority level.
# In production, grow this set from confirmed complaints in the DB.
# ---------------------------------------------------------------------------
SEED_EXAMPLES: list[dict] = [
    # CRITICAL
    {"text": "Patient died due to wrong medication administered by the doctor after ignoring allergies.", "priority": ComplaintPriority.CRITICAL},
    {"text": "Overdose occurred because physician prescribed 10x the correct dosage.", "priority": ComplaintPriority.CRITICAL},
    {"text": "Doctor gave medication intended for another patient causing severe allergic reaction.", "priority": ComplaintPriority.CRITICAL},
    {"text": "Wrong patient received surgery due to mislabelled records, resulting in death.", "priority": ComplaintPriority.CRITICAL},
    {"text": "Patient went into anaphylactic shock after doctor ignored documented allergy and prescribed penicillin.", "priority": ComplaintPriority.CRITICAL},

    # HIGH
    {"text": "Doctor prescribed wrong medication for my condition without reviewing my history.", "priority": ComplaintPriority.HIGH},
    {"text": "My private medical records were leaked to unauthorized parties without my consent.", "priority": ComplaintPriority.HIGH},
    {"text": "Physician accessed my records without consent or authorization.", "priority": ComplaintPriority.HIGH},
    {"text": "Doctor updated my prescription without my knowledge or approval.", "priority": ComplaintPriority.HIGH},
    {"text": "Unauthorized person viewed my sensitive health information.", "priority": ComplaintPriority.HIGH},
    {"text": "Doctor prescribed incorrect dosage leading to hospitalization.", "priority": ComplaintPriority.HIGH},

    # MEDIUM
    {"text": "The doctor made an error in my diagnosis which led to unnecessary treatment.", "priority": ComplaintPriority.MEDIUM},
    {"text": "Wrong medication was listed on my prescription, though caught before dispensing.", "priority": ComplaintPriority.MEDIUM},
    {"text": "Doctor missed important symptoms and misdiagnosed my condition initially.", "priority": ComplaintPriority.MEDIUM},
    {"text": "There was an error in my medical records that the doctor failed to correct.", "priority": ComplaintPriority.MEDIUM},
    {"text": "Physician overlooked a critical lab result, delaying proper treatment.", "priority": ComplaintPriority.MEDIUM},

    # LOW
    {"text": "Doctor was rude and dismissive during the consultation.", "priority": ComplaintPriority.LOW},
    {"text": "The appointment was cancelled without notice and I had to wait 3 weeks.", "priority": ComplaintPriority.LOW},
    {"text": "Doctor did not explain the side effects of the prescribed medication.", "priority": ComplaintPriority.LOW},
    {"text": "I had to wait over two hours past my scheduled appointment time.", "priority": ComplaintPriority.LOW},
    {"text": "The doctor seemed rushed and did not listen to all my concerns.", "priority": ComplaintPriority.LOW},
]

# Priority ordering for comparison (higher index = higher priority)
_PRIORITY_RANK = {
    ComplaintPriority.LOW: 0,
    ComplaintPriority.MEDIUM: 1,
    ComplaintPriority.HIGH: 2,
    ComplaintPriority.CRITICAL: 3,
}

_RANK_TO_PRIORITY = {v: k for k, v in _PRIORITY_RANK.items()}

# Lazy-loaded model and embeddings
_model = None
_seed_embeddings = None
_seed_labels = None


def _load():
    """Lazy-load the sentence-transformers model and pre-encode seed examples."""
    global _model, _seed_embeddings, _seed_labels
    if _model is not None:
        return

    from sentence_transformers import SentenceTransformer  # type: ignore
    import numpy as np

    _model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [s["text"] for s in SEED_EXAMPLES]
    _seed_labels = [s["priority"] for s in SEED_EXAMPLES]
    _seed_embeddings = _model.encode(texts, normalize_embeddings=True)


def classify_priority_semantic(description: str) -> ComplaintPriority:
    """
    Classify complaint priority using cosine similarity against the seed set.

    Returns the priority label of the most similar seed example.

    Args:
        description: The complaint's free-text description.

    Returns:
        ComplaintPriority enum value.
    """
    import numpy as np

    _load()
    query_embedding = _model.encode([description], normalize_embeddings=True)[0]
    # Cosine similarity = dot product when both vectors are L2-normalized
    similarities = _seed_embeddings @ query_embedding
    best_idx = int(similarities.argmax())
    return _seed_labels[best_idx]


def blend_priorities(keyword_priority: ComplaintPriority, semantic_priority: ComplaintPriority) -> ComplaintPriority:
    """
    Blend two priority assessments using the healthcare escalation rule:
    always take the HIGHER priority. Never silently downgrade.

    Args:
        keyword_priority:  Result from keyword/category classifier.
        semantic_priority: Result from semantic embedding classifier.

    Returns:
        The higher of the two priorities.
    """
    kw_rank = _PRIORITY_RANK[keyword_priority]
    sem_rank = _PRIORITY_RANK[semantic_priority]
    return _RANK_TO_PRIORITY[max(kw_rank, sem_rank)]
