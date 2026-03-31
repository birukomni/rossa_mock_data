"""Market & onboarding resolvers — all authenticated."""
from __future__ import annotations
import strawberry
from mock_server.types import (
    GetOnboardingChecklistInput, OnboardingChecklistResponse,
    ActivateMarketInput, MarketMembershipResponse,
    UpdateMarketMembershipStatusInput, ResponseMetaDto,
    checklist_from_dict, membership_from_dict,
)
from mock_server.store import store
from mock_server.auth import require_auth
from mock_server.utils import utc_now, maybe_delay


async def market_onboarding_checklist(
    info: strawberry.types.Info,
    input: GetOnboardingChecklistInput,
) -> OnboardingChecklistResponse:
    await maybe_delay()
    user = require_auth(info)
    market_id = input.market_id.lower()
    checklist = store.get_checklist(market_id)
    if not checklist:
        # Return a default not-started checklist for unknown markets
        checklist = {
            "market_id": market_id,
            "status": "not_started",
            "all_required_complete": False,
            "steps": [
                {"step": "phone_verification", "required": True, "completed": False},
                {"step": "id_verification", "required": True, "completed": False},
            ],
        }
    return OnboardingChecklistResponse(
        success=True,
        status=200,
        message="Onboarding checklist retrieved successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=checklist_from_dict(checklist),
    )


async def activate_market(
    info: strawberry.types.Info,
    input: ActivateMarketInput,
) -> MarketMembershipResponse:
    await maybe_delay()
    user = require_auth(info)
    now = utc_now()
    membership = store.activate_market(user["id"], input.market_id.lower(), now)
    return MarketMembershipResponse(
        success=True,
        status=200,
        message="Market activated successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=membership_from_dict(membership),
    )


async def update_market_membership_status(
    info: strawberry.types.Info,
    input: UpdateMarketMembershipStatusInput,
) -> MarketMembershipResponse:
    await maybe_delay()
    user = require_auth(info)
    membership = store.update_membership_status(user["id"], input.market_id.lower(), input.status)
    if not membership:
        raise Exception("Market membership not found. Please activate the market first.")
    return MarketMembershipResponse(
        success=True,
        status=200,
        message="Market membership status updated successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=membership_from_dict(membership),
    )
