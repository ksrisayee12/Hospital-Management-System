"""
AI Intelligence Layer API routes.
Includes OCR, Safety, Analytics, RAG Chat, and Insights.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.schemas import (
    OCRExtractionResponse, PrescriptionSafetyResponse, AIChatRequest, AIChatResponse,
    AIExplainResponse, ComplianceResponse, TrendResponse, AnalyticsSummaryResponse,
    HealthInsightListResponse, HealthInsightResponse, ScreenshotAnalysisResponse,
    WearableGoalCreateRequest, WearableGoalResponse, PrescriptionCreateRequest,
    PrescriptionResponse
)
from app.services import (
    ocr_service, safety_service, ai_service, rag_service, AnalyticsService,
    WearableAnalyticsService, ScreenshotService, InsightService
)
from app.dependencies import get_db, get_current_user
from app.models import Prescription, WearableGoal
from app.repositories import PrescriptionRepository, WearableGoalRepository
from app.services.patient_assistant import patient_assistant
from app.services.doctor_assistant import doctor_assistant
from app.dependencies import require_role

router_ai = APIRouter(prefix="/api/v1/patient", tags=["AI Intelligence"])
router_doctor_ai = APIRouter(prefix="/api/v1/doctor", tags=["Doctor AI Intelligence"])

# Temporary dir for uploads
UPLOAD_DIR = "./temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================================
# OCR & SCREENSHOTS
# ============================================================================

@router_ai.post("/screenshots/upload", response_model=ScreenshotAnalysisResponse)
async def upload_screenshot(
    patient_id: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload a smartwatch screenshot for OCR extraction and analysis."""
    service = ScreenshotService(session)
    from app.services.patient_services import VaultService
    vault_service = VaultService(session)
    content = await file.read()
    
    saved_file = await vault_service.upload_and_encrypt_file(
        patient_id=patient_id,
        file_name=file.filename,
        content=content,
        file_type=file.content_type or "image/png",
        category="wearable_screenshot"
    )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as f:
            f.write(content)
            
        result = await service.analyze_smartwatch_screenshot(patient_id, saved_file.id, file_path)
        return result
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router_ai.post("/ocr/upload", response_model=OCRExtractionResponse)
async def upload_prescription_image(
    patient_id: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload a prescription image for OCR extraction."""
    from app.services.patient_services import VaultService
    vault_service = VaultService(session)
    content = await file.read()
    
    saved_file = await vault_service.upload_and_encrypt_file(
        patient_id=patient_id,
        file_name=file.filename,
        content=content,
        file_type=file.content_type or "image/jpeg",
        category="prescription"
    )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as f:
            f.write(content)
            
        text, conf = await ocr_service.process_image(file_path)
        fields = await ocr_service.parse_prescription(text)
        
        repo = PrescriptionRepository(session)
        import uuid
        p = Prescription(
            id=str(uuid.uuid4()), patient_id=patient_id, created_by=patient_id,
            medicine_name=fields.get("medicine_name") or "Unknown Medicine",
            dosage=fields.get("dosage"),
            frequency=fields.get("frequency"),
            duration=fields.get("duration"),
            prescribing_doctor=fields.get("prescribing_doctor"),
            ocr_extraction_id=saved_file.id
        )
        p = await repo.create(p)
        await session.commit()
        
        return OCRExtractionResponse(
            extraction_id=saved_file.id, patient_id=patient_id, extraction_type="prescription",
            status="completed", extracted_fields=fields, confidence_score=conf,
            raw_text=text, prescription_id=p.id, processed_at=datetime.utcnow()
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ============================================================================
# PRESCRIPTION & SAFETY
# ============================================================================

@router_ai.post("/prescriptions", response_model=PrescriptionResponse)
async def create_prescription(
    request: PrescriptionCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = PrescriptionRepository(session)
    # Mock patient context
    patient_id = current_user.get("patient_id", "mock_patient")
    
    import uuid
    from datetime import datetime
    p = Prescription(
        id=str(uuid.uuid4()), patient_id=patient_id, created_by=patient_id,
        **request.model_dump()
    )
    p = await repo.create(p)
    await session.commit()
    return PrescriptionResponse.model_validate(p)


@router_ai.get("/safety/{prescription_id}", response_model=PrescriptionSafetyResponse)
async def analyze_prescription_safety(
    prescription_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = PrescriptionRepository(session)
    p = await repo.get_by_id(prescription_id)
    if not p:
         raise HTTPException(status_code=404, detail="Prescription not found")
         
    from app.repositories import PatientRepository
    patient_repo = PatientRepository(session)
    patient = await patient_repo.get_by_id(p.patient_id)
    
    # Fetch actual allergies
    allergies = patient.known_allergies or []
    
    # Fetch actual active medications
    patient_prescriptions = await repo.get_by_patient_id(p.patient_id, limit=100)
    prescriptions_list = patient_prescriptions[0] if isinstance(patient_prescriptions, tuple) else patient_prescriptions
    active = [med.medicine_name for med in prescriptions_list if getattr(med, 'is_active', True) and med.id != p.id]
    
    result = await safety_service.analyze_prescription(
        patient_id=p.patient_id, prescription_id=p.id, medicine_name=p.medicine_name,
        dosage=p.dosage, patient_allergies=allergies, active_medicines=active
    )
    return result


# ============================================================================
# ANALYTICS & WEARABLE GOALS
# ============================================================================

@router_ai.get("/{patient_id}/analytics/compliance", response_model=ComplianceResponse)
async def get_compliance(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = AnalyticsService(session)
    return await service.get_compliance_metrics(patient_id)


@router_ai.get("/{patient_id}/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from datetime import datetime
    c_service = AnalyticsService(session)
    w_service = WearableAnalyticsService(session)
    
    comp = await c_service.get_compliance_metrics(patient_id)
    wear = await w_service.get_summary(patient_id)
    
    return AnalyticsSummaryResponse(
        patient_id=patient_id, compliance=comp, wearable_summary=wear,
        risk_flags=[], generated_at=datetime.utcnow()
    )


@router_ai.post("/wearable/goals", response_model=WearableGoalResponse)
async def create_wearable_goal(
    request: WearableGoalCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = WearableGoalRepository(session)
    patient_id = current_user.get("patient_id", "mock_patient")
    import uuid
    g = WearableGoal(
        id=str(uuid.uuid4()), patient_id=patient_id, created_by=patient_id, **request.model_dump()
    )
    g = await repo.create(g)
    await session.commit()
    return WearableGoalResponse.model_validate(g)


# ============================================================================
# RAG CHAT & EXPLAIN
# ============================================================================

@router_ai.post("/{patient_id}/chat", response_model=AIChatResponse)
async def chat_with_records(
    patient_id: str,
    request: AIChatRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Enforce patient assistant constraints
    response = await patient_assistant.chat(
        patient_id=patient_id,
        question=request.question,
        top_k=request.top_k
    )
    return response

@router_doctor_ai.post("/patients/{patient_id}/chat", response_model=AIChatResponse)
async def doctor_chat_with_records(
    patient_id: str,
    request: AIChatRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("doctor"))
):
    # Enforce doctor assistant constraints (allows deep clinical lookups)
    response = await doctor_assistant.chat(
        patient_id=patient_id,
        question=request.question,
        top_k=request.top_k
    )
    return response


# ============================================================================
# INSIGHTS
# ============================================================================

@router_ai.post("/{patient_id}/insights/generate", response_model=HealthInsightResponse)
async def generate_weekly_insights(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = InsightService(session)
    return await service.generate_weekly_insights(patient_id)


def include_ai_routes(app):
    app.include_router(router_ai)
    app.include_router(router_doctor_ai)
