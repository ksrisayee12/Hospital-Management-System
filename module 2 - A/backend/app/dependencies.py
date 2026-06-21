"""
Dependency injection and utility functions for FastAPI.
"""

from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import jwt
from functools import lru_cache

from app.config import settings


# ============================================================================
# DATABASE DEPENDENCIES
# ============================================================================

class DatabaseManager:
    """Manage database connections and sessions."""

    _engine = None
    _session_maker = None

    @classmethod
    def initialize(cls):
        if not cls._engine:
            if "sqlite" in settings.DATABASE_URL:
                cls._engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DATABASE_ECHO,
                    connect_args={"check_same_thread": False}
                )
            else:
                cls._engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DATABASE_ECHO,
                    pool_size=settings.DATABASE_POOL_SIZE,
                    max_overflow=settings.DATABASE_MAX_OVERFLOW,
                    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                    pool_recycle=settings.DATABASE_POOL_RECYCLE,
                    connect_args={
                        "timeout": 30,
                        "server_settings": {"jit": "off"}
                    }
                )
        cls._session_maker = async_sessionmaker(
            cls._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @classmethod
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        if not cls._session_maker:
            cls.initialize()
        async with cls._session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @classmethod
    async def close(cls):
        if cls._engine:
            await cls._engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in DatabaseManager.get_session():
        yield session


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Extract and validate JWT token from request."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {
            "sub": user_id,
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "patient_id": payload.get("patient_id"),
            "provider_id": payload.get("provider_id"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_patient(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    patient_id = current_user.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a patient")
    return patient_id


async def get_current_provider(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    provider_id = current_user.get("provider_id")
    if not provider_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a healthcare provider")
    return provider_id


def require_role(required_role: str):
    async def check_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if required_role not in current_user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This operation requires {required_role} role",
            )
        return current_user
    return check_role


# ============================================================================
# AUTHORIZATION UTILITIES
# ============================================================================

async def verify_patient_access(
    patient_id: str,
    current_user: Dict[str, Any],
    session: AsyncSession
) -> bool:
    if current_user.get("patient_id") == patient_id:
        return True
    if current_user.get("provider_id"):
        pass  # Module 1 consent check hook
    if current_user.get("role") == "family":
        pass  # Family access check hook
    return False


async def verify_family_access(
    patient_id: str,
    family_member_id: str,
    session: AsyncSession,
    record_type: Optional[str] = None
) -> bool:
    from app.repositories import FamilyAccessRepository
    repo = FamilyAccessRepository(session)
    access = await repo.get_by_family_member(patient_id, family_member_id)
    if not access or access.status != "approved":
        return False
    if access.expires_at and access.expires_at < datetime.utcnow():
        return False
    if record_type and access.allowed_record_types:
        if record_type not in access.allowed_record_types:
            return False
    return True


@lru_cache()
def get_settings():
    return settings


async def get_pagination_params(page: int = 1, page_size: int = 20) -> Dict[str, int]:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    return {"page": page, "page_size": page_size, "skip": (page - 1) * page_size}
