"""Custom exceptions for the healthcare vault backend."""

from fastapi import HTTPException, status


class HealthcareException(Exception):
    """Base healthcare application exception."""
    pass


class PatientNotFound(HealthcareException):
    pass


class MedicalRecordNotFound(HealthcareException):
    pass


class AppointmentNotFound(HealthcareException):
    pass


class PrescriptionNotFound(HealthcareException):
    pass


class UnauthorizedAccess(HealthcareException):
    pass


class InvalidOperation(HealthcareException):
    pass


class EncryptionError(HealthcareException):
    pass


class ValidationError(HealthcareException):
    pass


class OCRProcessingError(HealthcareException):
    pass


class AIServiceError(HealthcareException):
    pass


class RAGIndexError(HealthcareException):
    pass


def exception_to_http_exception(exc: HealthcareException) -> HTTPException:
    """Convert healthcare exception to HTTP exception."""
    status_code_map = {
        PatientNotFound: status.HTTP_404_NOT_FOUND,
        MedicalRecordNotFound: status.HTTP_404_NOT_FOUND,
        AppointmentNotFound: status.HTTP_404_NOT_FOUND,
        PrescriptionNotFound: status.HTTP_404_NOT_FOUND,
        UnauthorizedAccess: status.HTTP_403_FORBIDDEN,
        InvalidOperation: status.HTTP_400_BAD_REQUEST,
        EncryptionError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        OCRProcessingError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        AIServiceError: status.HTTP_503_SERVICE_UNAVAILABLE,
        RAGIndexError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(status_code=code, detail=str(exc))
