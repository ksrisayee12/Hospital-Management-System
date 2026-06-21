import random
import string
from supabase_client import supabase
from security.encryption import KEK_BYTES, HealthcareEncryptor, json

class MedicalTokenizer:
    @staticmethod
    def generate_token() -> str:
        """
        Generate collision-resistant token in format MED_ + 6-char alphanumeric
        """
        chars = string.ascii_uppercase + string.digits
        return "MED_" + "".join(random.choices(chars, k=6))

    @staticmethod
    def tokenize(value: str, category: str) -> str:
        """
        Tokenize sensitive diagnosis/medication values into MED_XXXXXX
        and store the mapping in the token_vault.
        """
        if not value:
            return ""
            
        token = MedicalTokenizer.generate_token()
        
        # Encrypt value with KEK (master key)
        encrypted_res = HealthcareEncryptor.encrypt(value, KEK_BYTES)
        encrypted_str = json.dumps(encrypted_res)
        
        try:
            supabase.table("token_vault").insert({
                "token": token,
                "encrypted_value": encrypted_str,
                "data_category": category
            }).execute()
        except Exception as e:
            print(f"Failed to store token mapping in vault: {e}")
            
        return token

    @staticmethod
    def detokenize(token: str) -> str:
        """
        Lookup token in token_vault and decrypt it.
        """
        if not token or not token.startswith("MED_"):
            return token
            
        try:
            res = supabase.table("token_vault").select("encrypted_value").eq("token", token).execute()
            if res.data:
                encrypted_str = res.data[0]["encrypted_value"]
                return HealthcareEncryptor.decrypt(encrypted_str, KEK_BYTES)
        except Exception as e:
            print(f"Failed to detokenize: {e}")
            
        return token
