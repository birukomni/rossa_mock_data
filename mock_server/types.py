"""
All Strawberry types: enums, inputs, outputs, and response envelopes.
Strawberry auto-converts snake_case → camelCase in the GraphQL schema.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, List
import strawberry


# ─── Enums ────────────────────────────────────────────────────────────────────

@strawberry.enum
class IdentifierType(Enum):
    phone = "phone"
    email = "email"


@strawberry.enum
class SortOrder(Enum):
    ASC = "ASC"
    DESC = "DESC"


# ─── Shared meta ─────────────────────────────────────────────────────────────

@strawberry.type
class ResponseMetaDto:
    timestamp: Optional[str] = None
    correlation_id: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    total: Optional[int] = None
    total_pages: Optional[int] = None


# ─── Auth / User output types ─────────────────────────────────────────────────

@strawberry.type
class AuthnUserDto:
    id: str
    email: str
    first_name: str
    last_name: str
    phone_number: str
    is_active: bool
    email_verified: bool
    phone_verified: bool
    market_id: str
    date_joined: str
    created_at: str


@strawberry.type
class AuthTokensDto:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    scope: str


@strawberry.type
class LoginPayloadDto:
    user: AuthnUserDto
    tokens: AuthTokensDto


@strawberry.type
class OtpResponsePayloadDto:
    otp_sent: bool
    expires_in_seconds: int
    delivery_method: str


# ─── Profile output types ─────────────────────────────────────────────────────

@strawberry.type
class ProfilePayloadDto:
    id: str
    account_id: str
    market_id: str
    display_name: str
    avatar_url: Optional[str]
    language: Optional[str]
    timezone: Optional[str]
    created_at: str
    updated_at: str


# ─── Address output types ─────────────────────────────────────────────────────

@strawberry.type
class AddressPayloadDto:
    id: str
    label: Optional[str]
    street: str
    suburb: Optional[str]
    city: str
    postal_code: str
    country: str
    latitude: float
    longitude: float
    is_default: bool
    deliverable: bool
    created_at: str
    updated_at: str


# ─── Market / Onboarding output types ────────────────────────────────────────

@strawberry.type
class MarketMembershipPayloadDto:
    market_id: str
    status: str
    activated_at: str


@strawberry.type
class OnboardingStepPayloadDto:
    step: str
    required: bool
    completed: bool


@strawberry.type
class OnboardingChecklistPayloadDto:
    market_id: str
    status: str
    all_required_complete: bool
    steps: List[OnboardingStepPayloadDto]


# ─── Consent output types ─────────────────────────────────────────────────────

@strawberry.type
class ConsentDto:
    consent_type: str
    granted: bool
    granted_at: Optional[str]
    withdrawn_at: Optional[str]


# ─── Response envelopes ───────────────────────────────────────────────────────

@strawberry.type
class AuthnUserResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[AuthnUserDto] = None
    count: Optional[int] = None


@strawberry.type
class LoginResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[LoginPayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class OtpRequestResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[OtpResponsePayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class ProfileResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[ProfilePayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class AddressResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[AddressPayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class AddressListResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: List[AddressPayloadDto] = strawberry.field(default_factory=list)
    count: Optional[int] = None


@strawberry.type
class MarketMembershipResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[MarketMembershipPayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class OnboardingChecklistResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[OnboardingChecklistPayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class ConsentListResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: List[ConsentDto] = strawberry.field(default_factory=list)
    count: Optional[int] = None


@strawberry.type
class ConsentResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[ConsentDto] = None
    count: Optional[int] = None


@strawberry.type
class EmptyResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    count: Optional[int] = None


# ─── Input types ──────────────────────────────────────────────────────────────

@strawberry.input
class OtpRequestPayloadInput:
    identifier: str
    identifier_type: IdentifierType


@strawberry.input
class OtpRequestInput:
    input: OtpRequestPayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class VerifyOtpPayloadInput:
    identifier: str
    identifier_type: IdentifierType
    otp: str


@strawberry.input
class VerifyOtpInput:
    input: VerifyOtpPayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class LoginRequestPayloadInput:
    login: str
    password: str


@strawberry.input
class LoginInput:
    input: LoginRequestPayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None
    preferred_language: Optional[str] = None


@strawberry.input
class RegisterUserPayloadInput:
    email: str
    first_name: str
    last_name: str
    market_id: str
    password: str
    password_confirm: str
    phone_number: Optional[str] = ""


@strawberry.input
class RegisterInput:
    input: RegisterUserPayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None
    preferred_language: Optional[str] = None


@strawberry.input
class ForgotPasswordPayloadInput:
    identifier: str
    identifier_type: IdentifierType


@strawberry.input
class ForgotPasswordInput:
    input: ForgotPasswordPayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class RefreshTokensPayloadInput:
    refresh_token: str


@strawberry.input
class RefreshTokensInput:
    input: RefreshTokensPayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class GetMyProfileInput:
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class UpdateProfilePayloadInput:
    display_name: str
    avatar_url: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


@strawberry.input
class UpdateProfileInput:
    input: UpdateProfilePayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class DeleteAccountInput:
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class ListAddressesInput:
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None
    page: Optional[int] = 1
    size: Optional[int] = 20
    order_by: Optional[str] = "createdAt"
    order: Optional[SortOrder] = SortOrder.DESC


@strawberry.input
class CreateAddressPayloadInput:
    street: str
    city: str
    postal_code: str
    country: str
    latitude: float
    longitude: float
    label: Optional[str] = None
    suburb: Optional[str] = None


@strawberry.input
class CreateAddressInput:
    input: CreateAddressPayloadInput
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class SetDefaultAddressInput:
    address_id: str
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class DeleteAddressInput:
    address_id: str
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class GetOnboardingChecklistInput:
    market_id: str
    api_version: Optional[str] = "v1"


@strawberry.input
class ActivateMarketInput:
    market_id: str
    api_version: Optional[str] = "v1"


@strawberry.input
class UpdateMarketMembershipStatusInput:
    market_id: str
    status: str
    api_version: Optional[str] = "v1"


@strawberry.input
class MyConsentsInput:
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class GrantConsentsInput:
    consent_types: List[str]
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class WithdrawConsentInput:
    consent_type: str
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


@strawberry.input
class RequestDataExportInput:
    api_version: Optional[str] = "v1"
    market_id: Optional[str] = None


# ─── Dict → type factories ────────────────────────────────────────────────────

def authn_user_from_dict(d: dict) -> AuthnUserDto:
    return AuthnUserDto(
        id=d["id"],
        email=d["email"],
        first_name=d["first_name"],
        last_name=d["last_name"],
        phone_number=d.get("phone_number", ""),
        is_active=d["is_active"],
        email_verified=d["email_verified"],
        phone_verified=d["phone_verified"],
        market_id=d["market_id"],
        date_joined=d["date_joined"],
        created_at=d["created_at"],
    )


def profile_from_dict(d: dict) -> ProfilePayloadDto:
    return ProfilePayloadDto(
        id=d["id"],
        account_id=d["account_id"],
        market_id=d["market_id"],
        display_name=d["display_name"],
        avatar_url=d.get("avatar_url"),
        language=d.get("language"),
        timezone=d.get("timezone"),
        created_at=d["created_at"],
        updated_at=d["updated_at"],
    )


def address_from_dict(d: dict) -> AddressPayloadDto:
    return AddressPayloadDto(
        id=d["id"],
        label=d.get("label"),
        street=d["street"],
        suburb=d.get("suburb"),
        city=d["city"],
        postal_code=d["postal_code"],
        country=d["country"],
        latitude=d["latitude"],
        longitude=d["longitude"],
        is_default=d["is_default"],
        deliverable=d["deliverable"],
        created_at=d["created_at"],
        updated_at=d["updated_at"],
    )


def membership_from_dict(d: dict) -> MarketMembershipPayloadDto:
    return MarketMembershipPayloadDto(
        market_id=d["market_id"],
        status=d["status"],
        activated_at=d.get("activated_at", ""),
    )


def checklist_from_dict(d: dict) -> OnboardingChecklistPayloadDto:
    return OnboardingChecklistPayloadDto(
        market_id=d["market_id"],
        status=d["status"],
        all_required_complete=d["all_required_complete"],
        steps=[
            OnboardingStepPayloadDto(
                step=s["step"],
                required=s["required"],
                completed=s["completed"],
            )
            for s in d["steps"]
        ],
    )


def consent_from_dict(d: dict) -> ConsentDto:
    return ConsentDto(
        consent_type=d["consent_type"],
        granted=d["granted"],
        granted_at=d.get("granted_at"),
        withdrawn_at=d.get("withdrawn_at"),
    )
