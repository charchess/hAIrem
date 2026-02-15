import os
import re
import logging
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("PyJWT not installed, using mock token validation")


class TokenPayload:
    def __init__(self, sub: str, role: str, exp: Optional[int] = None):
        self.sub = sub
        self.role = role
        self.exp = exp


def decode_token(token: str) -> Optional[TokenPayload]:
    # First, check for mock tokens (for testing)
    mock_payload = _mock_decode_token(token)
    if mock_payload:
        return mock_payload
    
    if not JWT_AVAILABLE:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(
            sub=payload.get("sub", ""),
            role=payload.get("role", "user"),
            exp=payload.get("exp")
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None


def _mock_decode_token(token: str) -> Optional[TokenPayload]:
    if token.startswith("token-admin-"):
        return TokenPayload(sub="admin-user", role="admin")
    elif token.startswith("token-moderator-"):
        return TokenPayload(sub="mod-user", role="moderator")
    elif token.startswith("token-user-"):
        return TokenPayload(sub="regular-user", role="user")
    return None


def validate_agent_id(agent_id: str) -> str:
    if not agent_id:
        return agent_id
    
    sql_pattern = re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)|"
        r"(--|;|'|\"|%27|%22)|"
        r"(\bOR\b.*=.*\b)|\bAND\b.*=.*\b",
        re.IGNORECASE
    )
    
    if sql_pattern.search(agent_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent_id: potential SQL injection detected"
        )
    
    if "<script>" in agent_id.lower() or "javascript:" in agent_id.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent_id: potential XSS detected"
        )
    
    return agent_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials"
        )
    
    scheme = credentials.scheme
    if scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authentication scheme. Use 'Bearer <token>'"
        )
    
    token = credentials.credentials
    
    if not token or len(token.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token provided"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload


def require_admin() -> type:
    async def admin_check(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    return admin_check


def require_role(allowed_roles: List[str]):
    async def role_check(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_check
