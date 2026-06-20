You are a Principal AI Architect, Healthcare AI Engineer, FastAPI Architect, RAG Engineer, Security Engineer, and Enterprise Software Architect.

Analyze the existing codebase first.

Do NOT assume AI Chatbot already exists.

Verify whether Module 2 AI architecture exists.

If it exists:

* Audit it
* Improve it
* Refactor it if needed

If it does not exist:

* Create it

The final implementation must integrate with the existing Module 2 architecture.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECT

Patient-Sovereign Prescription Intelligence Network

Module 2

Patient Healthcare Vault

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OBJECTIVE

Implement a secure healthcare AI assistant architecture.

This is NOT a general chatbot.

This is NOT ChatGPT.

This is a patient-specific healthcare intelligence assistant.

The chatbot must use only authorized patient data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AI MODELS

Use existing configured models.

Priority:

1. BioMistral

2. MedGemma

3. MedLlama (if already configured)

Use HuggingFace implementations.

Reuse existing model integrations if available.

Do not introduce unnecessary models.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT SECURITY REQUIREMENT

The AI must NEVER reveal raw medical reports.

The AI must NEVER dump report contents.

The AI must NEVER display full report values.

The AI must NEVER expose sensitive report details.

Example:

Patient asks:

"Show my blood report."

AI response:

❌ NOT ALLOWED

Showing report contents.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Instead:

AI should respond:

✅ ALLOWED

"Your recent blood report appears stable. For detailed laboratory values, please view the report through the secure reports section."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Another example:

Patient asks:

"What are my MRI findings?"

AI should respond:

"Your doctor noted findings that require follow-up discussion. Please review the report in the reports section or consult your healthcare provider."

Do not expose raw findings.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AI RESPONSIBILITIES

The patient chatbot may:

* Explain trends
* Explain medications
* Explain appointments
* Explain health improvements
* Explain compliance
* Explain wearable trends
* Explain health history

The patient chatbot may NOT:

* Reveal raw reports
* Reveal complete OCR output
* Reveal doctor notes verbatim
* Reveal encrypted records
* Reveal database content

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PATIENT CHATBOT

Create:

PatientHealthAssistant

Data Source:

Only current patient records.

Context Sources:

* Medical History
* Prescriptions
* Appointments
* Analytics
* Wearable Data
* OCR Structured Data

Never use data belonging to another patient.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PATIENT RAG SYSTEM

Question

↓

Retrieve Current Patient Dataset

↓

Vector Search

↓

Relevant Chunks

↓

BioMistral / MedGemma

↓

Safe Response

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RAG DATA SOURCES

Patient Dataset Only

Allowed:

* Analytics
* Medication Records
* Appointment Records
* Timeline Events
* Wearable Trends

Restricted:

* Raw Reports
* Raw PDFs
* Raw OCR Dumps
* Sensitive Notes

Create filtering layer.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WEARABLE INTELLIGENCE

The chatbot must understand:

Heart Rate

Sleep

Steps

Calories

Blood Oxygen

Activity Trends

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example

Patient asks:

"How is my sleep quality?"

AI:

"Your average sleep duration improved by 18% during the past month."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example

Patient asks:

"Am I improving?"

AI:

"Based on your medication adherence, appointment compliance, and wearable metrics, your health indicators show a positive trend."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOCTOR CHATBOT

Create separate architecture.

Doctor chatbot must NOT reuse patient chatbot.

Create:

DoctorPatientAssistant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORKFLOW

Doctor

↓

Opens Specific Patient

PAT001

↓

Doctor Chatbot Loads

PAT001 Dataset Only

↓

Doctor Asks Question

↓

RAG Retrieval

↓

PAT001 Records Only

↓

Response

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERY IMPORTANT

Doctor chatbot context must be isolated.

Doctor viewing:

PAT001

Must never receive:

PAT002 Data

PAT003 Data

PAT004 Data

Generate patient-scoped retrieval.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOCTOR CHATBOT CAPABILITIES

Allowed:

* Summarize patient history
* Summarize medications
* Summarize appointments
* Summarize wearable trends
* Summarize OCR results
* Summarize timeline

Allowed:

Clinical assistance

Pattern recognition

Trend explanation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VECTOR DATABASE

Verify existence of:

ChromaDB

If absent:

Implement.

Create:

patient_id scoped collections

or

patient metadata filtering

Every embedding must contain:

patient_id

doctor_id

record_type

timestamp

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECURITY REQUIREMENTS

Implement:

Patient Data Isolation

Doctor Context Isolation

Consent Verification

RAG Access Control

Secure Embedding Retrieval

Prompt Injection Protection

Sensitive Data Filtering

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FILES TO VERIFY

chatbot/

rag/

embeddings/

analytics/

wearables/

patient_assistant/

doctor_assistant/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT

Step 1

Audit Existing AI Architecture

List:

Existing Components

Missing Components

Broken Components

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 2

Implementation Plan

Files To Modify

Files To Create

Files To Refactor

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 3

Implementation

Generate production-grade code.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 4

Security Verification

Verify:

Patient Isolation

Doctor Isolation

Dataset Isolation

Report Protection

Prompt Protection

RAG Security

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FINAL OBJECTIVE

Create two secure healthcare AI assistants:

1. Patient Health Assistant

Uses only current patient's dataset.

Provides explanations and insights.

Never exposes raw reports.

2. Doctor Patient Assistant

Loads only currently selected patient's dataset.

Provides clinical summaries and insights.

Never leaks information from other patients.

(this is how doctor ai chatbot works for that particular patient where their report dataset & patient data will be there to use for doctor chat bot )
