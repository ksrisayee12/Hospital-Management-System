-- 1. Patient Key Store for Envelope Encryption
CREATE TABLE IF NOT EXISTS patient_key_store (
    patient_id VARCHAR(255) PRIMARY KEY,
    encrypted_vault_key TEXT NOT NULL,
    key_version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rotated_at TIMESTAMP WITH TIME ZONE
);

-- 2. Token Vault for Medical Data Tokenization
CREATE TABLE IF NOT EXISTS token_vault (
    token VARCHAR(255) PRIMARY KEY,
    encrypted_value TEXT NOT NULL,
    data_category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Immutable Audit Log for Chain Verification
CREATE TABLE IF NOT EXISTS audit_log (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id VARCHAR(255) NOT NULL,
    actor_role VARCHAR(100) NOT NULL,
    patient_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    ip_address VARCHAR(100) DEFAULT '127.0.0.1',
    success BOOLEAN DEFAULT TRUE,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Secure Patient Reports Metadata (pointing to private storage bucket)
CREATE TABLE IF NOT EXISTS patient_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR(255) NOT NULL,
    uploaded_by VARCHAR(255) NOT NULL, -- doctor_code
    file_type VARCHAR(100) NOT NULL,
    encrypted_blob_path TEXT NOT NULL,
    content_hash VARCHAR(255) NOT NULL, -- SHA-256 integrity hash of plaintext file
    nonce VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL,
    key_version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disable Row Level Security for easy sandbox operation or use Supabase service role
ALTER TABLE patient_key_store DISABLE ROW LEVEL SECURITY;
ALTER TABLE token_vault DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE patient_reports DISABLE ROW LEVEL SECURITY;
