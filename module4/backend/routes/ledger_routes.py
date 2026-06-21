from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from module4.backend.blockchain.ledger import verify_chain
from module4.backend.core.auth import CurrentUser, require_super_admin
from module4.backend.core.database import get_db
from module4.backend.schemas.audit import LedgerVerifyOut

router = APIRouter(prefix="/ledger", tags=["Immutable Audit Ledger"])


@router.get("/verify", response_model=LedgerVerifyOut)
def verify_ledger(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_super_admin),
):
    """
    Walk the entire hash chain and confirm no historical event has
    been tampered with. Great live-demo moment for judges.
    """
    return verify_chain(db)

from module4.backend.schemas.audit import LedgerEventOut
from module4.backend.schemas.pagination import PaginatedResponse
from module4.backend.models.ledger_event import LedgerEvent
from sqlalchemy import desc

@router.get("", response_model=PaginatedResponse[LedgerEventOut])
def get_ledger_events(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_super_admin),
    limit: int = 50,
    offset: int = 0
):
    """
    Get paginated ledger events.
    """
    query = db.query(LedgerEvent).order_by(desc(LedgerEvent.timestamp))
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return PaginatedResponse(total=total, items=items, limit=limit, offset=offset)
