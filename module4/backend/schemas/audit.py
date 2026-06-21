from datetime import datetime
from pydantic import BaseModel, Field, root_validator
from typing import Optional, Dict, Any

class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    hospital_id: str
    user_id: str
    action: str
    resource: Optional[str] = None
    details: Optional[str] = None
    hash_signature: str

    class Config:
        orm_mode = True
        from_attributes = True

class LedgerEventOut(BaseModel):
    id: str = Field(alias="event_id")
    timestamp: datetime
    event_type: str
    event_data: str
    sequence_number: int
    current_hash: str
    previous_hash: Optional[str] = None
    summary: Optional[str] = None

    @root_validator(pre=True)
    def extract_summary(cls, values):
        # Allow accessing ORM objects via dict or obj
        if hasattr(values, "event_data"):
            event_data = values.event_data
        else:
            event_data = values.get("event_data", "")
        # Assuming event_data was seeded as "1|TYPE|summary|..."
        parts = event_data.split("|")
        summary_val = parts[2] if len(parts) > 2 else "Ledger event recorded"
        
        # Depending on pydantic version root_validator gives dict or obj. If dict, set it.
        if isinstance(values, dict):
            values["summary"] = summary_val
            values["id"] = str(values.get("event_id"))
        return values

    class Config:
        orm_mode = True
        from_attributes = True

class LedgerVerifyOut(BaseModel):
    valid: bool
    broken_at_sequence: Optional[int] = None
    message: str
