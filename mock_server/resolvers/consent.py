"""Consent / GDPR resolvers — all authenticated."""
from __future__ import annotations
import strawberry
from mock_server.types import (
    MyConsentsInput, ConsentListResponse,
    GrantConsentsInput, WithdrawConsentInput, ConsentResponse,
    RequestDataExportInput, EmptyResponse,
    ResponseMetaDto, consent_from_dict,
)
from mock_server.store import store
from mock_server.auth import require_auth
from mock_server.utils import utc_now, maybe_delay


async def my_consents(
    info: strawberry.types.Info,
    input: MyConsentsInput,
) -> ConsentListResponse:
    await maybe_delay()
    user = require_auth(info)
    consents = store.get_consents(user["id"])
    return ConsentListResponse(
        success=True,
        status=200,
        message="Consents retrieved successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=[consent_from_dict(c) for c in consents],
    )


async def grant_consents(
    info: strawberry.types.Info,
    input: GrantConsentsInput,
) -> ConsentListResponse:
    await maybe_delay()
    user = require_auth(info)
    now = utc_now()
    updated = store.grant_consents(user["id"], input.consent_types, now)
    return ConsentListResponse(
        success=True,
        status=200,
        message="Consents granted successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=[consent_from_dict(c) for c in updated],
    )


async def withdraw_consent(
    info: strawberry.types.Info,
    input: WithdrawConsentInput,
) -> ConsentResponse:
    await maybe_delay()
    user = require_auth(info)
    now = utc_now()
    consent = store.withdraw_consent(user["id"], input.consent_type, now)
    if not consent:
        raise Exception(f"Consent '{input.consent_type}' not found for this user.")
    return ConsentResponse(
        success=True,
        status=200,
        message="Consent withdrawn successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=consent_from_dict(consent),
    )


async def request_data_export(
    info: strawberry.types.Info,
    input: RequestDataExportInput,
) -> EmptyResponse:
    await maybe_delay()
    require_auth(info)
    return EmptyResponse(
        success=True,
        status=200,
        message="Data export request received. You will receive an email within 30 days.",
        meta=ResponseMetaDto(timestamp=utc_now()),
    )
