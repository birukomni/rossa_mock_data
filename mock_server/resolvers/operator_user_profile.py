"""Operator RBAC profile query — authenticated; payload null for consumer-only users."""
from __future__ import annotations

import strawberry

from mock_server.types import (
    GetMyOperatorUserProfileInput,
    OperatorUserProfileResponse,
    ResponseMetaDto,
    operator_user_profile_from_dict,
)
from mock_server.store import store
from mock_server.auth import require_auth
from mock_server.utils import utc_now, maybe_delay


async def my_operator_user_profile(
    info: strawberry.types.Info, input: GetMyOperatorUserProfileInput
) -> OperatorUserProfileResponse:
    await maybe_delay()
    user = require_auth(info)
    prof = store.get_operator_user_profile(user["id"])
    return OperatorUserProfileResponse(
        success=True,
        status=200,
        message="Operator user profile retrieved." if prof else "No operator user profile for this account.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=operator_user_profile_from_dict(prof) if prof else None,
    )
