from flask import Blueprint, request
from supabase_client import supabase
from utils.response import success, error
from ai_engine.rag_pipeline import retrieve_patient_context
from ai_engine.llm_challenger import generate_clinical_review

ai_bp = Blueprint("ai_bp", __name__)

def log_audit(doctor_code, patient_id, report_id, ai_response):
    """
    Log the AI review to the ai_reviews table for compliance.
    """
    try:
        supabase.table("ai_reviews").insert({
            "doctor_code": doctor_code,
            "patient_id": patient_id,
            "report_id": report_id,
            "risk_level": ai_response.get("risk_level", "UNKNOWN"),
            "confidence": ai_response.get("confidence", 0.0),
            "raw_ai_output": str(ai_response)
        }).execute()
    except Exception as e:
        print(f"Failed to log audit: {e}")

@ai_bp.route("/ai/review-report", methods=["POST"])
def review_report():
    try:
        body = request.get_json()
        doctor_code = body.get("doctor_code")
        patient_id = body.get("patient_id")
        diagnosis = body.get("diagnosis", "")
        clinical_notes = body.get("clinical_notes", "")
        
        if not doctor_code or not patient_id:
            return error("doctor_code and patient_id are required", 400)
            
        # 1. Save the doctor's report to Supabase
        report_res = supabase.table("doctor_reports").insert({
            "doctor_code": doctor_code,
            "patient_id": patient_id,
            "diagnosis": diagnosis,
            "clinical_notes": clinical_notes
        }).execute()
        
        report_id = report_res.data[0]["id"] if report_res.data else None
        
        # 2. Retrieve Patient Context using RAG
        # Combine diagnosis and notes as query
        query = f"Diagnosis: {diagnosis}. Notes: {clinical_notes}"
        rag_context_docs = retrieve_patient_context(patient_id, query)
        rag_context_str = "\n".join(rag_context_docs) if rag_context_docs else "No historical context found."
        
        # 3. Generate Challenger Review
        current_report_str = f"Diagnosis: {diagnosis}\nNotes: {clinical_notes}"
        ai_response = generate_clinical_review(current_report_str, rag_context_str)
        
        # 4. Save AI Findings
        if report_id:
            for category in ["contradictions", "clinical_questions", "missing_evidence", "wearable_observations"]:
                for finding in ai_response.get(category, []):
                    supabase.table("ai_findings").insert({
                        "report_id": report_id,
                        "category": category.upper(),
                        "finding_text": finding,
                        "evidence_used": rag_context_str[:200] # Snippet
                    }).execute()
                    
            log_audit(doctor_code, patient_id, report_id, ai_response)

        return success({
            "report_id": report_id,
            "ai_review": ai_response
        }, "AI Review completed successfully")

    except Exception as e:
        return error(str(e), 500)

@ai_bp.route("/ai/review-prescription", methods=["POST"])
def review_prescription():
    try:
        body = request.get_json()
        doctor_code = body.get("doctor_code")
        patient_id = body.get("patient_id")
        medicine_name = body.get("medicine_name", "")
        dosage = body.get("dosage", "")
        
        if not doctor_code or not patient_id:
            return error("doctor_code and patient_id are required", 400)
            
        # RAG Context
        query = f"Prescribing {medicine_name} at {dosage}"
        rag_context_docs = retrieve_patient_context(patient_id, query)
        rag_context_str = "\n".join(rag_context_docs) if rag_context_docs else "No historical context found."
        
        current_report_str = f"Prescription: {medicine_name}, Dosage: {dosage}"
        ai_response = generate_clinical_review(current_report_str, rag_context_str)
        
        log_audit(doctor_code, patient_id, None, ai_response)
        
        return success({
            "ai_review": ai_response
        }, "AI Prescription Review completed successfully")

    except Exception as e:
        return error(str(e), 500)

@ai_bp.route("/ai/history/<patient_id>", methods=["GET"])
def get_ai_history(patient_id):
    try:
        result = supabase.table("ai_reviews").select("*").eq("patient_id", patient_id).order("created_at", desc=True).execute()
        return success(result.data, "AI History fetched successfully")
    except Exception as e:
        return error(str(e), 500)

@ai_bp.route("/ai/findings/<report_id>", methods=["GET"])
def get_ai_findings(report_id):
    try:
        result = supabase.table("ai_findings").select("*").eq("report_id", report_id).execute()
        return success(result.data, "AI Findings fetched successfully")
    except Exception as e:
        return error(str(e), 500)

@ai_bp.route("/ai/chat", methods=["POST"])
def ai_chat():
    try:
        body = request.get_json()
        doctor_code = body.get("doctor_code")
        patient_id = body.get("patient_id")
        message = body.get("message", "")
        chat_history = body.get("chat_history", [])
        
        if not doctor_code or not patient_id:
            return error("doctor_code and patient_id are required", 400)
            
        # 1. Retrieve RAG context
        rag_context_docs = retrieve_patient_context(patient_id, message)
        rag_context_str = "\n".join(rag_context_docs) if rag_context_docs else "No historical context found."
        
        # 2. Get AI Chatbot Response
        from ai_engine.llm_challenger import generate_chat_response
        ai_res = generate_chat_response(message, rag_context_str, chat_history)
        
        # 3. Log findings & audit
        findings_metadata = ai_res.get("findings", {})
        log_audit(doctor_code, patient_id, None, findings_metadata)
        
        return success({
            "response": ai_res.get("message", "I have reviewed your note."),
            "findings": findings_metadata
        }, "AI Chat completed successfully")
        
    except Exception as e:
        return error(str(e), 500)

@ai_bp.route("/patient/<patient_id>/upload-report", methods=["POST"])
def upload_patient_report(patient_id):
    try:
        doctor_code = request.form.get("doctor_code", "DOC001")
        uploaded_file = request.files.get("file")
        
        if not uploaded_file:
            return error("No file provided", 400)
            
        filename = uploaded_file.filename
        file_type = uploaded_file.content_type or "text/plain"
        raw_bytes = uploaded_file.read()
        size = len(raw_bytes)
        
        # 1. Calculate SHA-256 content hash (Layer 9)
        from security.integrity import IntegrityVerifier
        content_hash = IntegrityVerifier.calculate_hash_bytes(raw_bytes)
        
        # 2. Retrieve/Create patient key (Layer 2 & 3)
        from security.vault_keys import PatientVaultKeyService
        patient_dek = PatientVaultKeyService.get_or_create_patient_dek(patient_id)
        
        # 3. Encrypt data using AES-256-GCM (Layer 1)
        from security.encryption import HealthcareEncryptor, json
        encrypted_res = HealthcareEncryptor.encrypt_bytes(raw_bytes, patient_dek)
        
        # We store the full JSON payload (ciphertext, nonce, tag) as a string
        encrypted_payload_str = json.dumps(encrypted_res)
        encrypted_payload_bytes = encrypted_payload_str.encode("utf-8")
        
        # 4. Upload file to Supabase storage with Local Fallback
        import uuid
        import os
        bucket_name = "patient-vault-reports"
        blob_path = f"{patient_id}/{uuid.uuid4()}_{filename}.enc"
        
        try:
            supabase.storage.from_(bucket_name).upload(
                path=blob_path,
                file=encrypted_payload_bytes,
                file_options={"content-type": "application/json"}
            )
        except Exception as storage_ex:
            print(f"Supabase Storage failed, falling back to local file storage: {storage_ex}")
            local_dir = os.path.join(os.getcwd(), "local_vault_storage", bucket_name, patient_id)
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, f"{uuid.uuid4()}_{filename}.enc")
            with open(local_path, "wb") as f:
                f.write(encrypted_payload_bytes)
            blob_path = os.path.relpath(local_path, os.getcwd())

        # 5. Insert secure report metadata row to Supabase
        report_res = supabase.table("patient_reports").insert({
            "patient_id": patient_id,
            "uploaded_by": doctor_code,
            "file_type": file_type,
            "encrypted_blob_path": blob_path,
            "content_hash": content_hash,
            "nonce": encrypted_res["nonce"],
            "size": size,
            "key_version": 1
        }).execute()
        
        report_id = report_res.data[0]["id"] if report_res.data else "UNKNOWN"
        
        # 6. Immutable Audit Log (Layer 8)
        from security.audit import AuditLogger
        AuditLogger.log_event(
            actor_id=doctor_code,
            actor_role="doctor",
            patient_id=patient_id,
            action="UPLOAD",
            resource_type="report",
            resource_id=str(report_id)
        )
        
        # Extract plaintext for RAG context indexing if it's a readable text file
        plaintext_summary = ""
        if file_type.startswith("text/") or filename.endswith(".txt") or filename.endswith(".md"):
            try:
                plaintext_summary = raw_bytes.decode("utf-8")
            except Exception:
                plaintext_summary = f"Uploaded secure file: {filename} ({size} bytes)"
        else:
            plaintext_summary = f"Uploaded secure file: {filename} ({size} bytes)"

        # Tokenize sensitive diagnostic terms (Layer 4)
        from security.tokenizer import MedicalTokenizer
        tokenized_summary = plaintext_summary
        for word in ["hypertension", "diabetes", "metformin", "sleep deprivation", "insomnia", "cardiac"]:
            if word in tokenized_summary.lower():
                token = MedicalTokenizer.tokenize(word, "condition")
                tokenized_summary = tokenized_summary.replace(word, token)
                
        # 7. Add tokenized summary to ChromaDB Vector DB (RAG)
        from ai_engine.rag_pipeline import add_to_rag_context
        try:
            add_to_rag_context(patient_id, "patient_reports", f"Report File: {filename}. Content: {tokenized_summary}")
        except Exception as ex:
            print(f"Failed to update ChromaDB RAG: {ex}")
            
        return success({
            "report_id": report_id,
            "filename": filename,
            "hash": content_hash,
            "tokenized_preview": tokenized_summary[:200]
        }, "Secure Patient Report uploaded and vectorized successfully")
        
    except Exception as e:
        return error(str(e), 500)

@ai_bp.route("/patient/<patient_id>/reports", methods=["GET"])
def get_patient_reports(patient_id):
    try:
        doctor_code = request.args.get("doctor_code", "DOC001")
        
        # 1. Fetch encrypted reports metadata from Supabase
        res = supabase.table("patient_reports").select("*").eq("patient_id", patient_id).execute()
        
        # 2. Retrieve patient DEK (Layer 2 & 3)
        from security.vault_keys import PatientVaultKeyService
        patient_dek = PatientVaultKeyService.get_or_create_patient_dek(patient_id)
        
        decrypted_reports = []
        from security.encryption import HealthcareEncryptor, json
        from security.integrity import IntegrityVerifier
        from security.audit import AuditLogger
        import os
        
        bucket_name = "patient-vault-reports"
        for row in res.data:
            # 3. Download encrypted file blob from storage
            blob_path = row["encrypted_blob_path"]
            try:
                if blob_path.startswith("local_vault_storage"):
                    with open(blob_path, "rb") as f:
                        encrypted_payload_bytes = f.read()
                else:
                    res_storage = supabase.storage.from_(bucket_name).download(blob_path)
                    encrypted_payload_bytes = res_storage
            except Exception as storage_read_ex:
                print(f"Failed to read file from storage for report {row['id']}: {storage_read_ex}")
                continue
                
            try:
                encrypted_payload_str = encrypted_payload_bytes.decode("utf-8")
                decrypted_bytes = HealthcareEncryptor.decrypt_bytes(encrypted_payload_str, patient_dek)
                
                # Verify SHA-256 integrity (Layer 9)
                if not IntegrityVerifier.verify_bytes(decrypted_bytes, row["content_hash"]):
                    # Log critical tampering event
                    AuditLogger.log_event(
                        actor_id=doctor_code,
                        actor_role="doctor",
                        patient_id=patient_id,
                        action="DECRYPT",
                        resource_type="report",
                        resource_id=row["id"],
                        success=False
                    )
                    return error("Tampering detected! File integrity mismatch.", 422)
                
                # Log successful decryption audit
                AuditLogger.log_event(
                    actor_id=doctor_code,
                    actor_role="doctor",
                    patient_id=patient_id,
                    action="DECRYPT",
                    resource_type="report",
                    resource_id=row["id"]
                )
                
                # Try decoding to string for dashboard preview
                try:
                    decrypted_text = decrypted_bytes.decode("utf-8")
                except Exception:
                    decrypted_text = "[Binary File - Preview Unavailable]"
                    
                # Get original filename from path
                clean_filename = os.path.basename(blob_path).split('_', 1)[-1].replace('.enc', '')
                if clean_filename.endswith('.enc'):
                    clean_filename = clean_filename[:-4]
                
                decrypted_reports.append({
                    "id": row["id"],
                    "filename": clean_filename,
                    "file_type": row["file_type"],
                    "size": row["size"],
                    "summary": decrypted_text,
                    "created_at": row["created_at"]
                })
            except Exception as dec_error:
                print(f"Decryption failed for row {row['id']}: {dec_error}")
                
        return success(decrypted_reports, "Decrypted patient reports retrieved successfully")
        
    except Exception as e:
        return error(str(e), 500)


