# Module 2 - Part A: Patient Healthcare Vault - Backend Architecture

## Project Folder Structure

```
healthcare-vault-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Configuration & environment variables
│   ├── dependencies.py              # Dependency injection
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base model with common fields
│   │   ├── patient.py               # Patient model
│   │   ├── medical_record.py        # Medical records, reports, prescriptions
│   │   ├── appointment.py           # Appointment model
│   │   ├── timeline.py              # Timeline events
│   │   ├── family_access.py         # Family access control
│   │   ├── vault.py                 # Vault files metadata
│   │   └── wearable.py              # Wearable metrics
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── patient.py               # Patient request/response schemas
│   │   ├── medical_record.py        # Medical record schemas
│   │   ├── appointment.py           # Appointment schemas
│   │   ├── timeline.py              # Timeline schemas
│   │   ├── family.py                # Family access schemas
│   │   ├── vault.py                 # Vault schemas
│   │   ├── wearable.py              # Wearable schemas
│   │   └── common.py                # Common response schemas
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base repository class
│   │   ├── patient_repo.py          # Patient repository
│   │   ├── medical_record_repo.py   # Medical record repository
│   │   ├── appointment_repo.py      # Appointment repository
│   │   ├── timeline_repo.py         # Timeline repository
│   │   ├── family_access_repo.py    # Family access repository
│   │   ├── vault_repo.py            # Vault repository
│   │   └── wearable_repo.py         # Wearable repository
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── patient_service.py       # Patient business logic
│   │   ├── dashboard_service.py     # Dashboard aggregation
│   │   ├── medical_record_service.py # Medical record logic
│   │   ├── appointment_service.py   # Appointment logic
│   │   ├── timeline_service.py      # Timeline logic
│   │   ├── family_service.py        # Family access logic
│   │   ├── vault_service.py         # Vault storage logic
│   │   └── wearable_service.py      # Wearable data logic
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── patient.py               # Patient endpoints
│   │   ├── dashboard.py             # Dashboard endpoints
│   │   ├── medical_records.py       # Medical record endpoints
│   │   ├── appointments.py          # Appointment endpoints
│   │   ├── timeline.py              # Timeline endpoints
│   │   ├── family.py                # Family access endpoints
│   │   ├── vault.py                 # Vault endpoints
│   │   └── wearable.py              # Wearable endpoints
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── encryption.py            # AES-256 encryption utilities
│   │   ├── validators.py            # Validation utilities
│   │   ├── helpers.py               # Helper functions
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── logging.py               # Logging configuration
│   │
│   └── database/
│       ├── __init__.py
│       ├── session.py               # Database session management
│       └── init_db.py               # Database initialization
│
├── alembic/                         # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_patient_api.py
│   ├── test_medical_records.py
│   ├── test_appointments.py
│   └── test_integration.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml               # Local Supabase setup
├── README.md
└── main.py                          # Entry point


## Key Design Principles

1. **Clean Architecture**: Separation of concerns with layers (routes → services → repositories → models)
2. **SOLID Principles**: Single responsibility, open/closed, interface segregation
3. **Dependency Injection**: All dependencies injected, easy to test
4. **Security First**: AES-256 encryption, JWT validation, RBAC
5. **Error Handling**: Comprehensive exception handling and logging
6. **Database Transactions**: Proper rollback and error handling
7. **Pagination & Filtering**: Production-ready pagination for list endpoints
8. **Audit Trail**: Created_at, updated_at, created_by tracking
9. **Type Safety**: Full Pydantic validation and type hints
10. **Documentation**: OpenAPI/Swagger auto-generated from docstrings

## Database Schema Overview

```
┌─────────────────────────────────────────────────────┐
│                   PATIENTS                          │
│  id | email | phone | dob | encrypted_health_id   │
└─────────────────────────────────────────────────────┘
              ↓
    ┌──────────┴──────────────┬─────────────────┐
    ↓                         ↓                 ↓
MEDICAL_RECORDS      APPOINTMENTS        FAMILY_ACCESS
PRESCRIPTIONS        TIMELINE_EVENTS     VAULT_FILES
REPORTS              WEARABLE_METRICS
ALLERGIES
VACCINATIONS
```

## Integration Points

### Module 1 (Authentication & Authorization)
- Consume JWT tokens from Module 1
- Extract user_id and patient_id from token claims
- Use existing authorization middleware

### Module 3 (OCR & Document Processing)
- Store raw files in Supabase Storage
- Reference file_id in medical_records
- Module 3 processes and extracts structured data

### Module 4 (AI & Analytics)
- Timeline events available for AI processing
- Wearable metrics analytics-ready
- Medical records structured for LLM context

## Deployment Notes

- All environment variables in `.env`
- Supabase connection pooling configured
- Connection timeout: 30s
- Max pool connections: 20
- Async database operations throughout
- Prepared statements prevent SQL injection
- Encryption keys managed via environment
