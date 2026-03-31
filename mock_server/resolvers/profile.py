"""Profile resolvers — all authenticated."""
from __future__ import annotations
import strawberry
from mock_server.types import (
    GetMyProfileInput, ProfileResponse, UpdateProfileInput,
    DeleteAccountInput, EmptyResponse, ResponseMetaDto, profile_from_dict,
)
from mock_server.store import store
from mock_server.auth import require_auth
from mock_server.utils import utc_now, maybe_delay


async def my_profile(info: strawberry.types.Info, input: GetMyProfileInput) -> ProfileResponse:
    await maybe_delay()
    user = require_auth(info)
    profile = store.get_profile(user["id"])
    if not profile:
        raise Exception("Profile not found.")
    return ProfileResponse(
        success=True,
        status=200,
        message="Profile retrieved successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=profile_from_dict(profile),
    )


async def update_profile(info: strawberry.types.Info, input: UpdateProfileInput) -> ProfileResponse:
    await maybe_delay()
    user = require_auth(info)
    payload = input.input
    updates = {
        "display_name": payload.display_name,
        "updated_at": utc_now(),
    }
    if payload.avatar_url is not None:
        updates["avatar_url"] = payload.avatar_url
    if payload.language is not None:
        updates["language"] = payload.language
    if payload.timezone is not None:
        updates["timezone"] = payload.timezone

    profile = store.update_profile(user["id"], updates)
    if not profile:
        raise Exception("Profile not found.")
    return ProfileResponse(
        success=True,
        status=200,
        message="Profile updated successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=profile_from_dict(profile),
    )


async def delete_account(info: strawberry.types.Info, input: DeleteAccountInput) -> EmptyResponse:
    await maybe_delay()
    user = require_auth(info)
    store.delete_user(user["id"])
    return EmptyResponse(
        success=True,
        status=200,
        message="Account deletion requested successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
    )
