# Patient-Sovereign Prescription Intelligence Network
## Module 2 - Part A: Patient Healthcare Vault Backend

### Production-Grade FastAPI Backend for Patient-Owned Healthcare Data

---

## 📋 Overview

This is a complete backend implementation for a patient-owned healthcare vault system following the **patient-sovereign model** where:

- **Patients own their medical data**
- Providers request access through a consent system
- Family members can be granted view-only permissions
- All data is encrypted and access-controlled
- Complete audit trail of all health events

### Key Features

✅ Patient Profile Management with Health Metrics  
✅ Medical Records Repository (Reports, Prescriptions, Clinical Notes)  
✅ Appointment Scheduling & Management  
✅ Medical Timeline Engine (Chronological Health History)  
✅ Family Access Control with Approval Workflow  
✅ Secure Health Vault Storage (AES-256 Encrypted)  
✅ Wearable Metrics Integration (Health Tracking)  
✅ Full JWT-Based Authentication & Authorization  
✅ Production-Ready Error Handling & Logging  
✅ OpenAPI Documentation (Swagger/ReDoc)  

---

## 🏗️ Architecture

### Technology Stack

```
Language:        Python 3.12+
Framework:       FastAPI (async)
Database:        PostgreSQL 14+ via Supabase
AI Backend:      HuggingFace (BioMistral/MedGemma), PaddleOCR
Vector DB:       ChromaDB (Local embedding RAG)
Auth:            JWT (from Module 1)
Encryption:      AES-256
Storage:         Supabase Storage
ORM:             SQLAlchemy (async)
Validation:      Pydantic v2
API Docs:        OpenAPI 3.0 (Swagger/ReDoc)
```

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│         API Routes (FastAPI)                │
│    /api/v1/patients, /dashboard, etc.       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Services (Business Logic)           │
│   PatientService, DashboardService, etc.    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│       Repositories (Data Access)            │
│   PatientRepository, MedicalRecordRepo, etc.│
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│     SQLAlchemy Models (ORM)                 │
│   Patient, MedicalRecord, Appointment, etc. │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│    PostgreSQL Database (Supabase)           │
└─────────────────────────────────────────────┘
```

### Database Schema

```
patients (1) ──────────────────┐
                                │
                   ┌────────────┼────────────┬────────────┬───────────┐
                   │            │            │            │           │
              (1:N)│         (1:N)│        (1:N)│       (1:N)│      (1:N)│
                   │            │            │            │           │
            medical_records  appointments  timeline_events family_access vault_files wearable_metrics
            └─ reports       └─ status      └─ events     └─ access   └─ files    └─ metrics
            └─ prescriptions └─ dates       └─ timeline   └─ approval └─ encrypt  └─ timestamps
            └─ clinical      └─ doctors     └─ years      └─ roles    └─ storage  └─ devices
```

---

## 📁 Project Structure

```
healthcare-vault-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization
│   ├── config.py                  # Configuration & environment variables
│   ├── dependencies.py            # Dependency injection & auth
│   │
│   ├── models/
│   │   ├── base.py                # Base model with audit fields
│   │   └── (all models in models.py)
│   │
│   ├── schemas/
│   │   └── (all schemas in schemas.py)
│   │
│   ├── repositories/
│   │   └── (all repositories in repositories.py)
│   │
│   ├── services/
│   │   └── (all services in services.py)
│   │
│   ├── routes/
│   │   └── (all routes in routes.py)
│   │
│   ├── utils/
│   │   ├── encryption.py          # AES-256 encryption
│   │   ├── validators.py          # Validation helpers
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging.py             # Logging setup
│   │
│   └── database/
│       ├── session.py             # Database session management
│       └── init_db.py             # Database initialization
│
├── tests/
│   ├── test_patient_api.py
│   ├── test_medical_records.py
│   ├── test_appointments.py
│   └── test_integration.py
│
├── .env.example                   # Environment variables template
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── docker-compose.yml             # Local development setup
└── main.py                        # Entry point
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Check Python version
python --version  # Should be 3.12 or higher

# Install pip and venv
pip install --upgrade pip
```

### 2. Installation

```bash
# Clone repository
git clone <repo-url>
cd healthcare-vault-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (Warning: ML packages may take a few minutes to download)
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
vim .env

# Required variables:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/healthcare_vault
# JWT_SECRET=your-secret-from-module-1
# ENCRYPTION_KEY=32-byte-aes-256-key
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-supabase-key

# AI Intelligence Required variables:
# HUGGINGFACE_API_TOKEN=your-hf-token (Required for MedGemma)
# CHROMA_DB_PATH=./chroma_db
```

### 4. Database Setup

```bash
# Start PostgreSQL (via docker-compose)
docker-compose up -d

# Alternatively, use existing Supabase PostgreSQL
# Just update DATABASE_URL in .env
```

### 5. Run Application

```bash
# Start development server
uvicorn app.main:app --reload --port 8000

# Note: The first time you run this, sentence-transformers and HuggingFace models
# will be downloaded to your local cache (~5GB+). This can take several minutes.
```

### 6. Access Documentation

```
Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
Health:      http://localhost:8000/health
Readiness:   http://localhost:8000/ready
```

---

## 📚 API Endpoints

### Patient Management

```
POST   /api/v1/patients              # Create patient
GET    /api/v1/patients/{id}         # Get patient profile
PUT    /api/v1/patients/{id}         # Update patient info
```

### Dashboard

```
GET    /api/v1/dashboard/{patient_id}  # Get patient dashboard
```

### Medical Records

```
POST   /api/v1/patients/{id}/medical-records              # Create record
GET    /api/v1/patients/{id}/medical-records              # List records (paginated)
GET    /api/v1/patients/{id}/medical-records/{record_id}  # Get specific record
PUT    /api/v1/patients/{id}/medical-records/{record_id}  # Update record
DELETE /api/v1/patients/{id}/medical-records/{record_id}  # Delete record
GET    /api/v1/patients/{id}/medical-records/critical     # Get critical records
```

### Appointments

```
POST   /api/v1/patients/{id}/appointments              # Request appointment
GET    /api/v1/patients/{id}/appointments              # List appointments
GET    /api/v1/patients/{id}/appointments/upcoming     # Get upcoming
GET    /api/v1/patients/{id}/appointments/{apt_id}    # Get specific
PUT    /api/v1/patients/{id}/appointments/{apt_id}/status        # Update status
POST   /api/v1/patients/{id}/appointments/{apt_id}/reschedule    # Reschedule
```

### Timeline

```
GET    /api/v1/patients/{id}/timeline              # Get chronological timeline
GET    /api/v1/patients/{id}/timeline/by-year      # Get timeline grouped by year
```

### Family Access

```
POST   /api/v1/patients/{id}/family/invite          # Invite family member
GET    /api/v1/patients/{id}/family                 # List family members
PUT    /api/v1/patients/{id}/family/{access_id}/approve  # Approve access
PUT    /api/v1/patients/{id}/family/{access_id}/reject   # Reject access
DELETE /api/v1/patients/{id}/family/{access_id}         # Revoke access
```

### Vault Storage

```
POST   /api/v1/patients/{id}/vault/upload        # Upload file
GET    /api/v1/patients/{id}/vault               # List vault files
GET    /api/v1/patients/{id}/vault/stats         # Get storage stats
DELETE /api/v1/patients/{id}/vault/{file_id}     # Delete file
```

### Wearable Metrics

```
POST   /api/v1/patients/{id}/wearable             # Create metric
POST   /api/v1/patients/{id}/wearable/batch       # Batch upload
GET    /api/v1/patients/{id}/wearable             # List metrics (paginated)
GET    /api/v1/patients/{id}/wearable/types       # Get available metric types
GET    /api/v1/patients/{id}/wearable/recent/{type}  # Get recent by type
```

---

## 🔐 Authentication

### JWT Token Format

All endpoints require JWT token from Module 1:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Claims

```json
{
  "sub": "usr_123456",
  "email": "user@example.com",
  "roles": ["patient"],
  "patient_id": "pat_abc123",
  "exp": 1704067200,
  "iat": 1704050800
}
```

---

## 📊 Data Models

See `02_models.py` for complete SQLAlchemy ORM definitions:

- **Patient**: Core patient profile with health metrics
- **MedicalRecord**: Lab reports, prescriptions, clinical notes
- **Appointment**: Scheduled visits with providers
- **TimelineEvent**: Chronological health events
- **FamilyAccess**: Family member access control
- **VaultFile**: Encrypted file storage metadata
- **WearableMetric**: Health tracking from devices

---

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_patient_api.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/test_integration.py -v
```

### Load Testing

```bash
# Run load tests with Locust
locust -f tests/load_tests.py --host=http://localhost:8000
```

---

## 📖 API Examples

See `10_API_EXAMPLES.md` for complete request/response examples including:

- ✅ Create patient
- ✅ Get dashboard
- ✅ Create medical record
- ✅ Request appointment
- ✅ Get medical timeline
- ✅ Invite family member
- ✅ Upload to vault
- ✅ Create wearable metric
- ✅ Batch upload wearable data
- ✅ Error responses

---

## 🔗 Integration with Other Modules

### Module 1: Authentication & Authorization
- Consumes JWT tokens
- Validates against JWT_SECRET
- Extracts user roles and permissions

### Module 3: Document Processing (OCR & AI)
- Stores raw files in Supabase Storage
- Exposes APIs for OCR processing
- Stores extracted data and OCR text

### Module 4: Analytics & Insights
- Provides medical records for aggregation
- Exposes timeline events for trend analysis
- Provides wearable metrics for statistics

See `11_INTEGRATION_NOTES.md` for detailed integration specifications.

---

## ⚙️ Configuration

All configuration via environment variables in `.env`:

```ini
# Application
APP_NAME="Patient-Sovereign Prescription Intelligence Network"
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/healthcare_vault
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Security
SECRET_KEY=your-app-secret
JWT_SECRET=your-jwt-secret-from-module-1
ENCRYPTION_KEY=your-32-byte-encryption-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-api-key

# Pagination
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

---

## 📈 Performance

### Database Optimization

- ✅ Connection pooling (size: 20)
- ✅ Eager loading for relationships
- ✅ Composite indexes for common queries
- ✅ Pagination enforced (max 100 items)
- ✅ Query timeouts configured

### Response Times (Target)

- Patient lookup: <50ms
- Medical records list: <100ms (with pagination)
- Dashboard aggregation: <500ms
- File upload: <2s

---

## 🔒 Security

### Data Encryption

- AES-256 encryption for sensitive data
- Supabase Storage SSL/TLS
- Database connection encrypted
- Encryption keys rotated regularly

### Authentication & Authorization

- JWT token validation on all endpoints
- Role-based access control (RBAC)
- Patient data isolation
- Provider consent workflow
- Family access approval system

### Security Headers

- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Content-Security-Policy configured
- CORS restricted to allowed origins

---

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t healthcare-vault:latest .

# Run container
docker run -p 8000:8000 --env-file .env healthcare-vault:latest
```

### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Kubernetes

```yaml
# See deployment configs in k8s/ directory
kubectl apply -f k8s/
```

### Cloud Platforms

- **AWS**: ECS/EKS with RDS PostgreSQL
- **Google Cloud**: Cloud Run with Cloud SQL
- **Azure**: Container Instances with Database
- **Heroku**: `heroku create` and deploy

---

## 📊 Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Readiness check (includes DB)
curl http://localhost:8000/ready
```

### Structured Logging

Logs in JSON format for easy parsing:

```json
{
  "timestamp": "2026-06-20T10:30:00Z",
  "level": "INFO",
  "message": "Patient created",
  "patient_id": "pat_abc123",
  "user_id": "usr_123456",
  "service": "patient_service"
}
```

### Key Metrics

- Request latency (p95, p99)
- Database query performance
- Token validation rate
- Authorization failures
- File upload success rate

---

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```
Fix: Verify DATABASE_URL and PostgreSQL is running
Check: psql -U user -d healthcare_vault -c "SELECT 1"
```

**JWT Token Invalid**
```
Fix: Verify JWT_SECRET matches Module 1
Check: Token not expired, correct algorithm
```

**File Upload Failed**
```
Fix: Verify SUPABASE_URL, SUPABASE_KEY, storage bucket exists
Check: Supabase dashboard for bucket configuration
```

**Port Already in Use**
```
Fix: Change port or kill process
Command: lsof -i :8000 && kill -9 <PID>
```

---

## 📝 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger)
- **API Schema**: http://localhost:8000/redoc (ReDoc)
- **Examples**: See `10_API_EXAMPLES.md`
- **Integration**: See `11_INTEGRATION_NOTES.md`
- **Models**: See `02_models.py` (inline SQLAlchemy comments)
- **Schemas**: See `03_schemas.py` (inline Pydantic documentation)

---

## 🤝 Contributing

Contribution guidelines:

1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Create descriptive commit messages
5. Submit pull request with description

---

## 📄 License

Copyright © 2026 SIMATS Engineering College  
All rights reserved.

---

## 👥 Contact

For questions or support:
- **Email**: development@simats.edu.in
- **Issues**: GitHub Issues
- **Documentation**: See included .md files

---

## ✅ Deployment Checklist

Before production deployment:

- [ ] Environment variables configured
- [ ] Database created and tested
- [ ] Supabase Storage bucket created
- [ ] JWT secret from Module 1 configured
- [ ] Encryption key generated (32 bytes)
- [ ] CORS origins updated
- [ ] Database backups configured
- [ ] Logging configured for production
- [ ] API documentation reviewed
- [ ] Health checks working
- [ ] Performance tested
- [ ] Security audit completed
- [ ] HTTPS/TLS enabled
- [ ] Monitoring alerts configured

---

## 🎯 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure environment**: `cp .env.example .env && vim .env`
3. **Start database**: `docker-compose up -d`
4. **Run application**: `uvicorn app.main:app --reload`
5. **View API docs**: http://localhost:8000/docs
6. **Read examples**: See `10_API_EXAMPLES.md`

---

**Happy Coding! 🚀**