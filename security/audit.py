import hashlib
import uuid
from datetime import datetime
from supabase_client import supabase

class AuditLogger:
    @staticmethod
    def get_last_event_hash() -> str:
        """
        Fetch the hash of the last event in the audit chain.
        """
        try:
            res = supabase.table("audit_log").select("event_hash").order("created_at", desc=True).limit(1).execute()
            if res.data:
                return res.data[0]["event_hash"]
        except Exception as e:
            print(f"Error fetching last event hash: {e}")
        # Base genesis hash
        return "0000000000000000000000000000000000000000000000000000000000000000"

    @staticmethod
    def log_event(actor_id: str, actor_role: str, patient_id: str, action: str, resource_type: str, resource_id: str, ip_address: str = "127.0.0.1", success: bool = True) -> str:
        """
        Create a secure, chained audit log record.
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        previous_hash = AuditLogger.get_last_event_hash()
        
        # event_content format to hash
        content = f"{event_id}|{timestamp}|{actor_id}|{actor_role}|{patient_id}|{action}|{resource_type}|{resource_id}|{ip_address}|{success}|{previous_hash}"
        event_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        try:
            supabase.table("audit_log").insert({
                "event_id": event_id,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "patient_id": patient_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "ip_address": ip_address,
                "success": success,
                "previous_hash": previous_hash,
                "event_hash": event_hash
            }).execute()
        except Exception as e:
            print(f"Failed to write to immutable audit log: {e}")
            
        return event_hash

    @staticmethod
    def verify_chain() -> bool:
        """
        Verifies that the entire hash chain is unbroken and untampered.
        """
        try:
            res = supabase.table("audit_log").select("*").order("created_at", desc=False).execute()
            events = res.data
            
            expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
            for event in events:
                if event["previous_hash"] != expected_prev_hash:
                    print(f"Audit chain broken at event: {event['event_id']}")
                    return False
                
                content = f"{event['event_id']}|{event['created_at']}|{event['actor_id']}|{event['actor_role']}|{event['patient_id']}|{event['action']}|{event['resource_type']}|{event['resource_id']}|{event['ip_address']}|{event['success']}|{event['previous_hash']}"
                calculated_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                
                if calculated_hash != event["event_hash"]:
                    print(f"Hash mismatch at event: {event['event_id']}")
                    return False
                    
                expected_prev_hash = event["event_hash"]
                
            return True
        except Exception as e:
            print(f"Error verifying audit chain: {e}")
            return False
