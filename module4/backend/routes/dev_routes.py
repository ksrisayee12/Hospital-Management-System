from fastapi import APIRouter
from pydantic import BaseModel
from module4.backend.core.auth import create_access_token

router = APIRouter(prefix="/dev", tags=["dev"])

class DevTokenRequest(BaseModel):
    sub: str
    role: str
    hospital_id: str | None = None

@router.post("/token")
def generate_dev_token(request: DevTokenRequest):
    """Temporary developer endpoint to mint JWTs since Module 1 is out of scope."""
    token = create_access_token(
        sub=request.sub,
        role=request.role,
        hospital_id=request.hospital_id
    )
    return {"access_token": token, "token_type": "bearer"}
