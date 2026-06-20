import base64
from supabase_client import supabase
from security.encryption import KEK_BYTES, EnvelopeEncryptionService, PatientVaultKeyManager

class PatientVaultKeyService:
    @staticmethod
    def get_or_create_patient_dek(patient_id: str) -> bytes:
        """
        On lookup: patient_id -> encrypted_vault_key.
        If it doesn't exist, generate, wrap with KEK and store in patient_key_store.
        """
        try:
            res = supabase.table("patient_key_store").select("encrypted_vault_key").eq("patient_id", patient_id).execute()
            if res.data:
                encrypted_dek_b64 = res.data[0]["encrypted_vault_key"]
                encrypted_dek = base64.b64decode(encrypted_dek_b64)
                # Unwrap using KEK
                return EnvelopeEncryptionService.unwrap_key(encrypted_dek, KEK_BYTES)
        except Exception as e:
            print(f"Error fetching patient key: {e}")

        # Generating a brand-new key since one doesn't exist yet
        raw_dek = PatientVaultKeyManager.generate_patient_key()
        wrapped_dek = EnvelopeEncryptionService.wrap_key(raw_dek, KEK_BYTES)
        wrapped_dek_b64 = base64.b64encode(wrapped_dek).decode('utf-8')
        
        try:
            supabase.table("patient_key_store").insert({
                "patient_id": patient_id,
                "encrypted_vault_key": wrapped_dek_b64,
                "key_version": 1
            }).execute()
        except Exception as e:
            print(f"Failed to save wrapped patient key: {e}")
            
        return raw_dek
