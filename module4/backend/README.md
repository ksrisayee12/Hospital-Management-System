# Module 4 — Governance & Security Intelligence

## What This Module Does

Module 4 is the **trust, audit, and fraud layer** for the Patient-Sovereign Prescription Intelligence Network. It provides:

| Capability | Description |
|---|---|
| **Immutable Audit Ledger** | SHA-256 hash-chain (Postgres-backed) — every critical action is tamper-evident |
| **Fraud Detection** | Rule-based anomaly detectors + IsolationForest ML upgrade path |
| **Trust Score Engine** | Per-doctor score (0–100), auto-penalised on complaints/alerts/override abuse |
| **Complaint Management** | Patient-submitted, AI-prioritised complaint queue with admin triage |
| **Emergency Override** | Doctor requests → Admin approves → access window with ledger entry |
| **Hospital Risk Analytics** | Super-admin dashboard: weighted 0–100 risk score per hospital |

## Architecture Fit (4-Module System)

```
Module 1 (Identity & Consent)  ─────►  JWT tokens consumed here for auth
Module 2 (Patient Vault)        ─────►  Writes VIEW_REPORT / DOWNLOAD_REPORT audit events
Module 3 (Doctor Clinical)      ─────►  Writes PRESCRIPTION_SIGNED / CONSENT_APPROVED events
Module 4 (THIS MODULE)          ────────  Governance, audit, fraud, trust, complaints
```

All four modules share the same Supabase Postgres instance and the same JWT secret (`JWT_SECRET_KEY`).

## Environment Variables

Create a `.env` file in `module4/`:

```env
# Database — Supabase Postgres connection string
DATABASE_URL=postgresql://postgres:<PASSWORD>@db.<PROJECT>.supabase.co:5432/postgres

# Shared JWT secret with Module 1
JWT_SECRET_KEY=<your-jwt-secret>
JWT_ALGORITHM=HS256

# App environment
ENVIRONMENT=production

# Feature flag: set to true to enable MiniLM semantic complaint classifier
# Requires sentence-transformers to be installed (see requirements.txt)
ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER=false
```

## Running Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run database migrations

```bash
# Against Supabase Postgres (set DATABASE_URL in .env first)
alembic upgrade head
```

> **Note**: If Postgres is unavailable, the app falls back to `create_all()` in development mode (`ENVIRONMENT=development`).

### 3. Start the server

```bash
uvicorn main:app --reload --port 8004
```

API docs available at: `http://localhost:8004/docs`

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Health

```bash
# Deep health check (verifies DB connectivity)
curl http://localhost:8004/health
```

### Complaints

```bash
# Submit a complaint (patient role)
curl -X POST http://localhost:8004/api/v1/complaints \
  -H "Authorization: Bearer <PATIENT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-001",
    "doctor_id": "doctor-001",
    "category": "MEDICAL_ERROR",
    "description": "Doctor prescribed wrong medication.",
    "hospital_id": "hospital-A"
  }'

# List complaints with pagination (admin role)
curl "http://localhost:8004/api/v1/complaints?limit=20&offset=0" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Update complaint status (admin role)
curl -X PATCH http://localhost:8004/api/v1/complaints/<complaint_id> \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "RESOLVED", "admin_notes": "Investigated and resolved."}'
```

### Audit Logs

```bash
# Get paginated audit logs (admin/super_admin)
curl "http://localhost:8004/api/v1/audit?limit=50&offset=0&action=VIEW_REPORT" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Immutable Ledger

```bash
# Verify the hash chain (super_admin only) — great live demo moment
curl http://localhost:8004/api/v1/ledger/verify \
  -H "Authorization: Bearer <SUPER_ADMIN_TOKEN>"
```

### Security Alerts

```bash
# List alerts (admin/super_admin)
curl "http://localhost:8004/api/v1/alerts?status=NEW&limit=20" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Triage an alert
curl -X PATCH http://localhost:8004/api/v1/alerts/<alert_id> \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "ESCALATED"}'
```

### Trust Score

```bash
# Get own trust score (doctor — self only)
curl http://localhost:8004/api/v1/trust-score/doctor-001 \
  -H "Authorization: Bearer <DOCTOR_TOKEN>"

# List all scores for a hospital (admin)
curl "http://localhost:8004/api/v1/trust-score?limit=50" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Emergency Override

```bash
# Request an override (doctor — self only)
curl -X POST http://localhost:8004/api/v1/emergency \
  -H "Authorization: Bearer <DOCTOR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": "doctor-001",
    "patient_id": "patient-001",
    "reason": "Emergency surgery",
    "urgency": "HIGH",
    "hospital_id": "hospital-A"
  }'

# Approve / reject (admin)
curl -X POST http://localhost:8004/api/v1/emergency/<request_id>/approve \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"approve": true, "review_notes": "Justified.", "access_window_hours": 24}'
```

### Hospital Risk Analytics

```bash
# All hospitals (super_admin only)
curl "http://localhost:8004/api/v1/hospital-risk?limit=10" \
  -H "Authorization: Bearer <SUPER_ADMIN_TOKEN>"

# Recompute risk for a specific hospital
curl -X POST "http://localhost:8004/api/v1/hospital-risk/hospital-A/recompute" \
  -H "Authorization: Bearer <SUPER_ADMIN_TOKEN>"
```

### Fraud Intelligence (NEW)

```bash
# Get combined rule + ML fraud explanation for a user (super_admin only)
curl http://localhost:8004/api/v1/fraud/explain/doctor-001 \
  -H "Authorization: Bearer <SUPER_ADMIN_TOKEN>"

# Response example:
# {
#   "user_id": "doctor-001",
#   "features": {"views_per_hour": 3.5, "downloads_per_hour": 0.8, ...},
#   "rule_flags": ["EXCESSIVE_VIEWS"],
#   "isolation_score": -0.23,
#   "isolation_display_score": 61.5,
#   "ml_anomaly": true,
#   "disagreement": false,
#   "explanation": "BOTH rule-based and ML detectors flagged this user."
# }
```

---

## Access Policy

| Role | Permitted Actions |
|---|---|
| `patient` | Submit complaints for themselves only |
| `doctor` | Request emergency overrides for themselves only; view own trust score |
| `admin` | Full CRUD on complaints/alerts/overrides/audit — **scoped to their hospital_id from JWT** |
| `super_admin` | Everything, unscoped. Only role that can call `/ledger/verify`, `/hospital-risk`, `/fraud/explain` |

---

## Running Tests

```bash
pytest tests/ -v --tb=short
```

Tests use an in-memory SQLite database — no external dependencies needed.

## Retraining the Fraud Model

```bash
# After accumulating ≥500 audit log rows:
python -m fraud_detection.training.train_isolation_forest
```

Intended cadence: **nightly or on-demand by a super_admin**. Not part of the request path.
