"""
MODULE 2 — PART B: Custom Exceptions
"""

from fastapi import HTTPException, status


class PartBBaseException(Exception):
    """Base for all Part B exceptions."""

# ── OCR ──────────────────────────────────────
class OCRProcessingError(PartBBaseException): pass
class OCRFileTooLargeError(PartBBaseException): pass
class OCRUnsupportedFormatError(PartBBaseException): pass
class OCRLowConfidenceError(PartBBaseException): pass

# ── RAG / Embedding ───────────────────────────
class EmbeddingError(PartBBaseException): pass
class ChromaDBError(PartBBaseException): pass
class NoRelevantContextError(PartBBaseException): pass

# ── AI ────────────────────────────────────────
class AIModelError(PartBBaseException): pass
class AIModelUnavailableError(PartBBaseException): pass

# ── Auth / Access ─────────────────────────────
class PatientAccessDeniedError(PartBBaseException): pass
class ConsentNotGrantedError(PartBBaseException): pass

# ── Analytics ─────────────────────────────────
class InsufficientDataError(PartBBaseException): pass
class AnalyticsComputationError(PartBBaseException): pass


# ── HTTP Mappings ─────────────────────────────

def to_http_exception(exc: PartBBaseException) -> HTTPException:
    mapping = {
        OCRFileTooLargeError: (status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large"),
        OCRUnsupportedFormatError: (status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported file format"),
        OCRProcessingError: (status.HTTP_422_UNPROCESSABLE_ENTITY, "OCR processing failed"),
        OCRLowConfidenceError: (status.HTTP_422_UNPROCESSABLE_ENTITY, "OCR confidence too low"),
        EmbeddingError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Embedding generation failed"),
        ChromaDBError: (status.HTTP_503_SERVICE_UNAVAILABLE, "Vector store unavailable"),
        NoRelevantContextError: (status.HTTP_200_OK, "No relevant records found"),
        AIModelError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "AI model error"),
        AIModelUnavailableError: (status.HTTP_503_SERVICE_UNAVAILABLE, "AI model unavailable"),
        PatientAccessDeniedError: (status.HTTP_403_FORBIDDEN, "Access denied"),
        ConsentNotGrantedError: (status.HTTP_403_FORBIDDEN, "Patient consent not granted"),
        InsufficientDataError: (status.HTTP_404_NOT_FOUND, "Insufficient data for analysis"),
        AnalyticsComputationError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Analytics computation failed"),
    }
    code, detail = mapping.get(type(exc), (500, str(exc)))
    return HTTPException(status_code=code, detail=detail)
