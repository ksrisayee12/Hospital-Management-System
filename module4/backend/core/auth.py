"""
Module 4 - Auth dependencies.

Module 1 owns identity/auth issuance. Module 4 only VERIFIES the JWT
and extracts role + identity for authorization checks (admin vs
super_admin vs doctor vs patient).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from module4.backend.core.config import settings

bearer_scheme = HTTPBearer()


class CurrentUser:
    def __init__(self, user_id: str, role: str, hospital_id: str | None = None):
        self.user_id = user_id
        self.role = role
        self.hospital_id = hospital_id


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_id = payload.get("sub")
    role = payload.get("role")
    hospital_id = payload.get("hospital_id")

    if user_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
        )

    return CurrentUser(user_id=user_id, role=role, hospital_id=hospital_id)


def require_roles(*allowed_roles: str):
    """Dependency factory: restrict an endpoint to specific roles."""

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not permitted. Requires one of {allowed_roles}.",
            )
        return user

    return checker


# Common shortcuts
require_admin = require_roles("admin", "super_admin")
require_super_admin = require_roles("super_admin")
require_doctor = require_roles("doctor")
require_patient = require_roles("patient")

from datetime import datetime, timedelta

def create_access_token(sub: str, role: str, hospital_id: str | None = None) -> str:
    expires_delta = timedelta(hours=24)
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": sub, "role": role, "hospital_id": hospital_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
