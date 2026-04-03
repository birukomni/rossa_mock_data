"""
Mock auth helpers.
- Unknown Bearer token → Jane (default user id).
- `mock-token-john` → John; `mock-token-admin` / `mock-token-analyst` /
  `mock-token-operator` / `mock-token-wrong-store` → operator RBAC mock users.
- No token → raises Unauthorized (REST) / Exception (GraphQL).
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from mock_server.seed import TOKEN_MAP, DEFAULT_USER_ID
from mock_server.store import store


# ── GraphQL helpers ───────────────────────────────────────────────────────────

def _extract_token(request) -> str | None:
    auth: str = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth[7:].strip() or None


def get_user_id(request) -> str | None:
    """Return user_id for the token, or None if no token present."""
    token = _extract_token(request)
    if token is None:
        return None
    return TOKEN_MAP.get(token, DEFAULT_USER_ID)


def require_auth(info) -> dict:
    """
    GraphQL auth guard.
    Returns the seed user dict or raises Exception('Unauthorized').
    """
    request = info.context["request"]
    user_id = get_user_id(request)
    if not user_id:
        raise Exception("Unauthorized")
    user = store.get_user(user_id)
    if not user:
        raise Exception("Unauthorized")
    return user


# ── REST auth helpers ─────────────────────────────────────────────────────────

def _parse_bearer(authorization: str = Header(..., alias="Authorization")) -> str:
    """
    FastAPI dependency: reads 'Authorization: Bearer <token>' header,
    validates it, and returns the resolved user_id.
    Raises HTTP 401 if the header is missing or malformed.
    """
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must start with 'Bearer'")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return TOKEN_MAP.get(token, DEFAULT_USER_ID)


# Convenience alias — import this in REST routers
rest_auth = Depends(_parse_bearer)
