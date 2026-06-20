Patient-Sovereign Prescription Intelligence Network — Module 2: Patient Healthcare Vault

ROLE
You are a Principal Software Architect and Senior FastAPI Engineer implementing Module 2 (Patient Healthcare Vault) into an existing production codebase.

MANDATORY FIRST STEP — CODEBASE ANALYSIS
Before writing a single line of code:

Recursively scan the entire project tree
Read and understand every existing file
Document your findings in this exact format:

ANALYSIS REPORT
===============
Files Inspected: [list]
Architecture Pattern: [detected pattern]
Existing DB Models: [list]
Existing Routes: [list]
Existing Services: [list]
Existing Repositories: [list]
Existing Auth/DI Pattern: [describe]
Naming Conventions: [describe]
Reusable Components: [list]
Files to Modify: [list with reason]
Files to Create: [list with reason]
Files to Remove/Consolidate: [list with reason]
Conflicts Found: [list]
Do NOT skip this step. Do NOT begin implementation until analysis is complete.

PROJECT CONTEXT
System: Patient-Sovereign Prescription Intelligence Network

Module Being Implemented: Module 2 — Patient Healthcare Vault

Existing Modules (do not break): Module 1 (Identity & Consent), Module 3 (Doctor Clinical Intelligence), Module 4 (Governance & Security)
Tech Stack:

Backend: FastAPI + Python
Database: Supabase PostgreSQL
Storage: Supabase Storage (files, images, documents)
AI Models: BioMistral, MedGemma (via Ollama or HuggingFace)
OCR: PaddleOCR
Vector DB: ChromaDB (patient-scoped collections)
Encryption: AES-256 (data at rest), RSA-2048 (key exchange), SHA-256 (integrity)


MODULE 2 — FULL SPECIFICATION
PART 1: Core Vault Infrastructure
1. Patient Dashboard

Aggregate endpoint returning: active prescriptions, upcoming appointments, recent health metrics, risk alerts, family member summaries
All data filtered by authenticated patient's consent scope

2. Health Records Repository

CRUD for: lab reports, prescriptions, doctor notes, discharge summaries, vaccination records
File storage via Supabase Storage with AES-256 encrypted metadata
Record versioning (never hard-delete; use is_archived flag)
Record access log (who viewed, when, from which module)

3. Medical Timeline

Chronological aggregation across all record types
Filter by: date range, record type, doctor, severity
Returns structured timeline events with source references

4. Family Access Management

Patient can grant/revoke access to family members
Access tiers: VIEW_ONLY, EMERGENCY_ONLY, FULL_PROXY
Family member actions are audit-logged
Consent tokens expire; cron job or background task to invalidate

5. Appointment Management

CRUD for appointments
Status: SCHEDULED, COMPLETED, MISSED, CANCELLED
Appointment compliance tracking (feeds into analytics)
Reminder scheduling (store reminder timestamps; actual delivery is external)

6. Health Vault Storage

Generic encrypted document store
Supports: PDF, JPEG, PNG, DICOM (store as-is, extract metadata)
SHA-256 checksum on upload for integrity verification
Presigned URL generation for authorized access

7. Wearable Data Storage

Raw metric storage: heart_rate, steps, sleep_hours, calories, blood_oxygen, timestamp, source_device
Batch insert endpoint (wearable sync)
Source devices: DaFit, generic smartwatch, fitness app import


PART 2: AI Intelligence Layer
8. OCR Prescription Extraction
Input: uploaded image (handwritten, scanned, screenshot)
Pipeline:
Upload → Supabase Storage → PaddleOCR → Field Extraction → Validation → DB Insert → Return Structured Data
Extract these fields:

medicine_name, dosage, frequency, duration
prescribing_doctor, prescription_date, notes
health_metrics (if wearable screenshot)

Post-extraction: automatically trigger Prescription Safety Analysis (feature #9)
9. Prescription Safety Analysis
Inputs: extracted prescription data + patient's existing medication list + allergy profile
Analysis checks:

Drug-drug interactions (use open database: OpenFDA API or local interaction matrix)
Duplicate active ingredients
Allergy conflicts against patient's stored allergy list
Dangerous combinations (e.g., MAOIs + SSRIs)
Dosage outliers vs. standard ranges

Output:
json{
  "risk_score": 0-100,
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "warnings": [{"type": "INTERACTION", "drugs": [...], "description": "..."}],
  "recommendations": [...],
  "auto_flagged": true/false
}
If risk_level is HIGH or CRITICAL: create a governance alert (hook into Module 4's alert system if it exists, otherwise create a local alert record).
10. AI Health Assistant
Models: BioMistral (primary), MedGemma (fallback or specialty)
Capabilities:

/explain/report/{record_id} — explain lab report in plain language
/explain/prescription/{prescription_id} — explain prescription, side effects, instructions
/explain/trends — explain health metric trends
/chat — general health Q&A (RAG-backed, see #11)

System prompt must enforce: "You are a medical information assistant. You do not diagnose. You do not prescribe. You explain existing patient records only."
11. RAG Architecture
Patient Question
      ↓
Generate Embedding (sentence-transformers/all-MiniLM-L6-v2 or BioMistral embeddings)
      ↓
Query ChromaDB (patient-scoped collection: collection_id = patient_id)
      ↓
Retrieve top-k relevant chunks from authorized records only
      ↓
Build context: [retrieved chunks] + [patient profile summary]
      ↓
LLM (BioMistral/MedGemma) generates answer
      ↓
Return answer + source citations (record_id, record_type, date)
Indexing:

On every new record insert → chunk → embed → upsert to ChromaDB
On record archive → remove from ChromaDB
ChromaDB collection per patient; namespace strictly enforced

12. Health Analytics
Computed metrics (can be on-demand or cached):

Medication compliance rate: doses_taken / doses_prescribed * 100
Appointment compliance rate: COMPLETED / (SCHEDULED + COMPLETED + MISSED) * 100
Health trends: 7d / 30d / 90d moving averages for all wearable metrics
Anomaly flags: metric outside 2σ of patient's own baseline

Endpoints:

/analytics/compliance — medication + appointment compliance
/analytics/trends/{metric} — time-series for specific metric
/analytics/summary — full health score dashboard

13. Wearable Analytics
Dedicated analytics for wearable data:

Sleep trend analysis (avg, quality score if deep/light available)
Heart rate variability trend
Blood oxygen trend with low-SpO2 alerts (<95%)
Steps/activity trend vs. patient's set goal

14. Screenshot Analysis
Workflow:
Image Upload (wearable app screenshot)
      ↓
PaddleOCR extracts all text
      ↓
Regex + LLM parsing to identify metric type and value
      ↓
Structured wearable metric record created
      ↓
Stored in wearable_data table
      ↓
Triggers wearable analytics update
15. AI Health Insights
Scheduled or on-demand:

Weekly insight generation per patient
Inputs: wearable trends + compliance rates + recent records
Output: 3-5 natural language insights + 1-2 action recommendations
Stored as health_insight records with generated_at timestamp


DATABASE SCHEMA REQUIREMENTS
Design or extend tables. Never duplicate existing tables — check first.
Required tables (create only if not existing):
health_records         — all medical documents
prescriptions          — structured prescription data  
prescription_safety    — safety analysis results
appointments           — appointment records
family_access          — family member consent grants
wearable_data          — raw metric readings
wearable_goals         — patient-set targets
health_insights        — AI-generated insights
rag_index_status       — ChromaDB sync state per record
record_access_log      — audit trail for record views
All tables must have: id (UUID), patient_id (UUID FK), created_at, updated_at, is_archived (bool)

API STRUCTURE
Mount all routes under: /api/v1/patient/
/dashboard
/records          (CRUD)
/timeline
/family           (CRUD + consent)
/appointments     (CRUD)
/vault/upload
/vault/{file_id}
/wearable/sync
/wearable/goals
/ocr/upload
/ocr/{extraction_id}
/safety/{prescription_id}
/ai/explain/report/{id}
/ai/explain/prescription/{id}
/ai/chat
/analytics/compliance
/analytics/trends/{metric}
/analytics/summary
/insights
/screenshots/upload

ARCHITECTURE RULES
Follow the existing architecture pattern detected in your analysis. If the existing pattern is:

Repository pattern → add repositories for each new entity
Service layer → add services, never put business logic in routes
Dependency injection → use FastAPI Depends() consistently
Async → all DB calls must be async
Pydantic models → request/response schemas for every endpoint

Create these layers for each feature:
router → service → repository → database
              ↓
         external services (OCR, AI, ChromaDB, OpenFDA)

SECURITY REQUIREMENTS

Every endpoint requires authenticated patient JWT (reuse Module 1's auth middleware)
Patients can only access their own records (enforce at repository layer, not just route layer)
Family access checks before returning any data to family member tokens
All file uploads: validate MIME type, scan for malicious content (at minimum: check file headers)
Encrypt sensitive fields before DB insert (reuse Module 1's encryption utilities if present)
All AI inputs must be sanitized before passing to LLM


EXTERNAL INTEGRATIONS
PaddleOCR:
pythonfrom paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')
Run in thread pool executor (CPU-bound).
ChromaDB:
pythonimport chromadb
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(f"patient_{patient_id}")
OpenFDA Drug Interaction (fallback if no local DB):
GET https://api.fda.gov/drug/label.json?search=openfda.brand_name:{drug_name}
AI Models:

If Ollama is running locally: use ollama Python client
If HuggingFace: use transformers pipeline
Detect which is available at startup; log which backend is used


IMPLEMENTATION ORDER
Implement in this sequence:

DB schema migrations
Pydantic schemas
Repositories
Services (non-AI first)
Routers
OCR pipeline
Safety analysis
ChromaDB indexing
RAG service
AI assistant endpoints
Analytics services
Health insights
Background tasks / scheduled jobs
Integration tests (at least one per router)


FINAL DELIVERABLES
After implementation, provide:
IMPLEMENTATION REPORT
=====================
New Files Created: [list]
Modified Files: [list]
Removed/Consolidated Files: [list]
New DB Tables: [list]
Modified DB Tables: [list]
New API Endpoints: [count + list]
External Dependencies Added: [list with pip install commands]
ChromaDB Setup: [instructions]
AI Model Setup: [instructions]
Environment Variables Required: [list]

Integration Notes (Module 1): [how auth hooks in]
Integration Notes (Module 3): [data Module 3 can read]
Integration Notes (Module 4): [alerts/governance hooks]
Migration Notes: [any data migration needed]
Breaking Changes: [list or NONE]

CONSTRAINTS

Do NOT hardcode patient IDs, API keys, or secrets
Do NOT create duplicate tables — check existing schema first
Do NOT create a second auth system — reuse Module 1
Do NOT use synchronous DB calls in async endpoints
Do NOT skip the analysis phase
Do NOT implement features that conflict with Module 3 or 4 without documenting the integration point