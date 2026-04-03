"""
REST: operator RBAC user profile (mock).
GET /api/v1/me/operator-profile — current user's operator profile, or 404 for consumer-only accounts.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from mock_server.auth import rest_auth
from mock_server.store import store

router = APIRouter(prefix="/api/v1/me", tags=["operator-profile"])


class OperatorUserProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    role: str
    permissions: list[str]
    allowed_stores: list[str] = Field(serialization_alias="allowedStores")


@router.get("/operator-profile", response_model=OperatorUserProfile)
def get_my_operator_profile(user_id: str = rest_auth) -> OperatorUserProfile:
    prof = store.get_operator_user_profile(user_id)
    if not prof:
        raise HTTPException(
            status_code=404,
            detail="No operator user profile for this account. Use mock-token-admin, "
            "mock-token-analyst, mock-token-operator, or mock-token-wrong-store.",
        )
    return OperatorUserProfile(
        id=prof["id"],
        role=prof["role"],
        permissions=prof["permissions"],
        allowed_stores=prof["allowed_stores"],
    )
