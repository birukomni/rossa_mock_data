"""
Mock auth helpers.
- Any Bearer token resolves to Jane (default).
- `mock-token-john` resolves to John.
- No token → raises Unauthorized.
"""
from __future__ import annotations

from mock_server.seed import TOKEN_MAP, DEFAULT_USER_ID
from mock_server.store import store


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
    # Named tokens map to specific users; any other token → Jane
    return TOKEN_MAP.get(token, DEFAULT_USER_ID)


def require_auth(info) -> dict:
    """
    Call from authenticated resolvers.
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
