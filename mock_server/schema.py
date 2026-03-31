"""
Strawberry schema — wires all queries and mutations together.
"""
from __future__ import annotations
from typing import Optional, List
import strawberry

from mock_server.types import (
    # Input types
    OtpRequestInput, VerifyOtpInput, LoginInput, RegisterInput, ForgotPasswordInput,
    RefreshTokensInput,
    GetMyProfileInput, UpdateProfileInput, DeleteAccountInput,
    ListAddressesInput, CreateAddressInput, SetDefaultAddressInput, DeleteAddressInput,
    GetOnboardingChecklistInput, ActivateMarketInput, UpdateMarketMembershipStatusInput,
    MyConsentsInput, GrantConsentsInput, WithdrawConsentInput, RequestDataExportInput,
    # Response types
    OtpRequestResponse, LoginResponse, AuthnUserResponse, EmptyResponse,
    ProfileResponse, AddressListResponse, AddressResponse,
    OnboardingChecklistResponse, MarketMembershipResponse,
    ConsentListResponse, ConsentResponse,
)
from mock_server.resolvers import auth, profile, address, market, consent


@strawberry.type
class Query:
    my_profile: ProfileResponse = strawberry.field(resolver=profile.my_profile)
    my_addresses: AddressListResponse = strawberry.field(resolver=address.my_addresses)
    market_onboarding_checklist: OnboardingChecklistResponse = strawberry.field(
        resolver=market.market_onboarding_checklist
    )
    my_consents: ConsentListResponse = strawberry.field(resolver=consent.my_consents)


@strawberry.type
class Mutation:
    # Auth (unauthenticated)
    request_otp: OtpRequestResponse = strawberry.mutation(resolver=auth.request_otp)
    verify_otp: LoginResponse = strawberry.mutation(resolver=auth.verify_otp)
    login: LoginResponse = strawberry.mutation(resolver=auth.login)
    register: AuthnUserResponse = strawberry.mutation(resolver=auth.register)
    forgot_password: EmptyResponse = strawberry.mutation(resolver=auth.forgot_password)
    refresh_tokens: LoginResponse = strawberry.mutation(resolver=auth.refresh_tokens)

    # Profile (authenticated)
    update_profile: ProfileResponse = strawberry.mutation(resolver=profile.update_profile)
    delete_account: EmptyResponse = strawberry.mutation(resolver=profile.delete_account)

    # Addresses (authenticated + stateful)
    create_address: AddressResponse = strawberry.mutation(resolver=address.create_address)
    set_default_address: AddressResponse = strawberry.mutation(resolver=address.set_default_address)
    delete_address: EmptyResponse = strawberry.mutation(resolver=address.delete_address)

    # Markets (authenticated)
    activate_market: MarketMembershipResponse = strawberry.mutation(resolver=market.activate_market)
    update_market_membership_status: MarketMembershipResponse = strawberry.mutation(
        resolver=market.update_market_membership_status
    )

    # Consents / GDPR (authenticated)
    grant_consents: ConsentListResponse = strawberry.mutation(resolver=consent.grant_consents)
    withdraw_consent: ConsentResponse = strawberry.mutation(resolver=consent.withdraw_consent)
    request_data_export: EmptyResponse = strawberry.mutation(resolver=consent.request_data_export)


schema = strawberry.Schema(query=Query, mutation=Mutation)
