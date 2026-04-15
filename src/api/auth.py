from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import jwt
import hashlib
import secrets

from src.utils.config import get_settings

settings = get_settings()
security_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class Role:
    WORKER = "worker"
    ADMIN = "admin"
    HR = "hr"
    IT = "it"
    MANAGER = "manager"


@dataclass
class AuthenticatedUser:
    worker_id: str
    name: str
    department: str
    role: str
    access_level: str
    permissions: list[str]


class APIKeyManager:
    def __init__(self):
        self._keys: dict[str, dict] = {}

    def generate_key(self, name: str, permissions: list[str] = None, expires_days: int = 365) -> str:
        key = f"mk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self._keys[key_hash] = {
            "name": name,
            "permissions": permissions or ["query"],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
            "is_active": True,
        }
        return key

    def validate_key(self, key: str) -> Optional[dict]:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        data = self._keys.get(key_hash)
        if not data or not data["is_active"]:
            return None
        if datetime.fromisoformat(data["expires_at"]) < datetime.utcnow():
            return None
        return data

    def revoke_key(self, key: str) -> bool:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        if key_hash in self._keys:
            self._keys[key_hash]["is_active"] = False
            return True
        return False


api_key_manager = APIKeyManager()


def create_token(worker_id: str, name: str, department: str, role: str, access_level: str = "all") -> str:
    payload = {
        "sub": worker_id, "name": name, "department": department,
        "role": role, "access_level": access_level,
        "iat": datetime.utcnow(), "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)) -> AuthenticatedUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales requeridas", headers={"WWW-Authenticate": "Bearer"})

    token = credentials.credentials

    if token.startswith("mk_"):
        key_data = api_key_manager.validate_key(token)
        if key_data:
            return AuthenticatedUser(
                worker_id=f"api_{key_data['name']}", name=key_data["name"],
                department="integration", role="api", access_level="all",
                permissions=key_data["permissions"],
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida o expirada")

    payload = decode_token(token)
    role_permissions = {
        Role.WORKER: ["query", "feedback"],
        Role.MANAGER: ["query", "feedback", "team_analytics"],
        Role.HR: ["query", "feedback", "analytics", "kb_read", "tickets_read"],
        Role.IT: ["query", "feedback", "analytics", "kb_manage", "tickets_manage"],
        Role.ADMIN: ["query", "feedback", "analytics", "kb_manage", "tickets_manage", "workers_manage", "api_keys"],
    }
    role = payload.get("role", Role.WORKER)
    permissions = role_permissions.get(role, role_permissions[Role.WORKER])

    return AuthenticatedUser(
        worker_id=payload["sub"], name=payload.get("name", ""),
        department=payload.get("department", ""), role=role,
        access_level=payload.get("access_level", "all"), permissions=permissions,
    )


def require_permission(permission: str):
    async def check_permission(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if permission not in user.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permiso requerido: {permission}")
        return user
    return check_permission
