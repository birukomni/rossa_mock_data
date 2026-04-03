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


@strawberry.type
class OperatorUserProfilePayloadDto:
    """RBAC-style operator / back-office user (mock)."""

    id: str
    role: str
    permissions: List[str]
    allowed_stores: List[str]


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
class OperatorUserProfileResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[OperatorUserProfilePayloadDto] = None
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
class GetMyOperatorUserProfileInput:
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


def operator_user_profile_from_dict(d: dict) -> OperatorUserProfilePayloadDto:
    return OperatorUserProfilePayloadDto(
        id=d["id"],
        role=d["role"],
        permissions=list(d["permissions"]),
        allowed_stores=list(d["allowed_stores"]),
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


# ─── Stores — enums ───────────────────────────────────────────────────────────

@strawberry.enum
class ItemType(Enum):
    single = "single"
    combo = "combo"


@strawberry.enum
class OverrideType(Enum):
    hidden = "hidden"
    price_override = "price_override"
    unavailable = "unavailable"


# ─── Stores — output types ────────────────────────────────────────────────────

@strawberry.type
class StoreLocationDto:
    lat: float
    lng: float


@strawberry.type
class StorePayloadDto:
    id: str
    name: str
    code: str
    address: str
    location: Optional[StoreLocationDto]
    is_active: bool
    capabilities: Optional[List[str]]
    version: Optional[int]
    created_at: str
    updated_at: str


# ─── Catalog — output types ───────────────────────────────────────────────────

@strawberry.type
class CategoryPayloadDto:
    id: str
    market_id: Optional[str]
    name: str
    description: Optional[str]
    is_active: bool
    sort_order: Optional[int]
    created_at: str
    updated_at: str


@strawberry.type
class CategorySummaryDto:
    id: str
    name: str


@strawberry.type
class ModifierPayloadDto:
    id: str
    name: str
    price_adjustment: str
    is_active: bool


@strawberry.type
class ModifierGroupPayloadDto:
    id: str
    name: str
    min_selections: int
    max_selections: int
    is_required: bool
    modifiers: List[ModifierPayloadDto]


@strawberry.type
class ComboSlotPayloadDto:
    name: str
    min_selections: int
    max_selections: int
    eligible_item_ids: List[str]


@strawberry.type
class MenuItemPayloadDto:
    id: str
    market_id: Optional[str]
    category: Optional[CategorySummaryDto]
    name: str
    description: Optional[str]
    item_type: str
    base_price: str
    cost_price: Optional[str]
    image_url: Optional[str]
    calories: Optional[int]
    is_active: bool
    sort_order: Optional[int]
    effective_price: Optional[str]
    store_override: Optional[str]
    availability_rule: Optional[str]
    modifier_groups: Optional[List[ModifierGroupPayloadDto]]
    combo_slots: Optional[List[ComboSlotPayloadDto]]
    created_at: str
    updated_at: str


@strawberry.type
class StoreOverridePayloadDto:
    id: str
    store_id: str
    menu_item_id: str
    override_type: str
    override_price: Optional[str]
    reason: str
    effective_from: Optional[str]
    effective_until: Optional[str]


# ─── Stores — response envelopes ─────────────────────────────────────────────

@strawberry.type
class StoreResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[StorePayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class StoreListResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: List[StorePayloadDto] = strawberry.field(default_factory=list)
    count: Optional[int] = None


@strawberry.type
class DeleteStoreResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    count: Optional[int] = None


# ─── Catalog — response envelopes ────────────────────────────────────────────

@strawberry.type
class CategoryResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[CategoryPayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class CategoryListResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: List[CategoryPayloadDto] = strawberry.field(default_factory=list)
    count: Optional[int] = None


@strawberry.type
class MenuItemResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[MenuItemPayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class MenuItemListResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: List[MenuItemPayloadDto] = strawberry.field(default_factory=list)
    count: Optional[int] = None


@strawberry.type
class ModifierGroupResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[ModifierGroupPayloadDto] = None
    count: Optional[int] = None


@strawberry.type
class StoreOverrideResponse:
    success: bool
    status: int
    message: str
    meta: Optional[ResponseMetaDto] = None
    payload: Optional[StoreOverridePayloadDto] = None
    count: Optional[int] = None


# ─── Stores — input types ─────────────────────────────────────────────────────

@strawberry.input
class StoreLocationInput:
    lat: float
    lng: float


@strawberry.input
class FindAllStoresInput:
    page: Optional[int] = 1
    size: Optional[int] = 25
    order_by: Optional[str] = "createdAt"
    order: Optional[SortOrder] = SortOrder.DESC
    api_version: Optional[str] = "v1"


@strawberry.input
class FindOneStoreInput:
    id: str
    api_version: Optional[str] = "v1"


@strawberry.input
class CreateStoreInput:
    name: str
    code: str
    address: str
    is_active: bool
    location: Optional[StoreLocationInput] = None
    capabilities: Optional[str] = None
    api_version: Optional[str] = "v1"


@strawberry.input
class UpdateStoreInput:
    id: str
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    location: Optional[StoreLocationInput] = None
    is_active: Optional[bool] = None
    capabilities: Optional[str] = None
    version: Optional[int] = None
    api_version: Optional[str] = "v1"


@strawberry.input
class DeleteStoreInput:
    id: str
    api_version: Optional[str] = "v1"


# ─── Catalog — input types ────────────────────────────────────────────────────

@strawberry.input
class ListCategoriesInput:
    page: Optional[int] = 1
    size: Optional[int] = 20
    order_by: Optional[str] = "createdAt"
    order: Optional[SortOrder] = SortOrder.DESC
    market_id: Optional[str] = None
    is_active: Optional[bool] = None
    api_version: Optional[str] = "v1"


@strawberry.input
class CreateCategoryInput:
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True
    sort_order: Optional[int] = None
    market_id: Optional[str] = None
    api_version: Optional[str] = "v1"


@strawberry.input
class ListMenuItemsInput:
    page: Optional[int] = 1
    size: Optional[int] = 20
    order_by: Optional[str] = "createdAt"
    order: Optional[SortOrder] = SortOrder.DESC
    market_id: Optional[str] = None
    category_id: Optional[str] = None
    item_type: Optional[ItemType] = None
    is_active: Optional[bool] = None
    store_id: Optional[str] = None
    api_version: Optional[str] = "v1"


@strawberry.input
class ComboSlotInput:
    name: str
    min_selections: int
    max_selections: int
    eligible_item_ids: List[str]


@strawberry.input
class CreateMenuItemInput:
    name: str
    item_type: ItemType
    base_price: str
    category_id: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[str] = None
    image_url: Optional[str] = None
    calories: Optional[int] = None
    is_active: Optional[bool] = True
    sort_order: Optional[int] = None
    combo_slots: Optional[List[ComboSlotInput]] = None
    market_id: Optional[str] = None
    api_version: Optional[str] = "v1"


@strawberry.input
class ModifierInput:
    name: str
    price_adjustment: Optional[str] = "0.00"


@strawberry.input
class CreateModifierGroupInput:
    name: str
    min_selections: int
    max_selections: int
    modifiers: List[ModifierInput]
    is_required: Optional[bool] = False
    api_version: Optional[str] = "v1"


@strawberry.input
class CreateStoreOverrideInput:
    store_id: str
    menu_item_id: str
    override_type: OverrideType
    reason: str
    override_price: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    api_version: Optional[str] = "v1"


# ─── Stores / Catalog factory helpers ────────────────────────────────────────

def store_location_from_dict(d: dict | None) -> Optional[StoreLocationDto]:
    if not d:
        return None
    return StoreLocationDto(lat=d["lat"], lng=d["lng"])


def store_from_dict(d: dict) -> StorePayloadDto:
    caps = d.get("capabilities")
    if isinstance(caps, str):
        caps = [c.strip() for c in caps.split(",") if c.strip()]
    return StorePayloadDto(
        id=d["id"],
        name=d["name"],
        code=d.get("code", d["id"]),
        address=d.get("address", ""),
        location=store_location_from_dict(d.get("location")),
        is_active=d.get("is_active", d.get("is_open", True)),
        capabilities=caps or [],
        version=d.get("version", 1),
        created_at=d.get("created_at", "2025-01-01T00:00:00Z"),
        updated_at=d.get("updated_at", "2025-01-01T00:00:00Z"),
    )


def category_from_dict(d: dict) -> CategoryPayloadDto:
    return CategoryPayloadDto(
        id=d["id"],
        market_id=d.get("market_id"),
        name=d["name"],
        description=d.get("description"),
        is_active=d.get("is_active", True),
        sort_order=d.get("sort_order"),
        created_at=d.get("created_at", "2025-01-01T00:00:00Z"),
        updated_at=d.get("updated_at", "2025-01-01T00:00:00Z"),
    )


def modifier_group_from_dict(d: dict) -> ModifierGroupPayloadDto:
    return ModifierGroupPayloadDto(
        id=d["id"],
        name=d["name"],
        min_selections=d["min_selections"],
        max_selections=d["max_selections"],
        is_required=d.get("is_required", False),
        modifiers=[
            ModifierPayloadDto(
                id=m["id"],
                name=m["name"],
                price_adjustment=m.get("price_adjustment", "0.00"),
                is_active=m.get("is_active", True),
            )
            for m in d.get("modifiers", [])
        ],
    )


def menu_item_from_dict(d: dict, category_dict: dict | None = None, effective_price: str | None = None, store_override_price: str | None = None, modifier_groups: list | None = None) -> MenuItemPayloadDto:
    cat = None
    if category_dict:
        cat = CategorySummaryDto(id=category_dict["id"], name=category_dict["name"])
    # price as string
    raw_price = d.get("price", d.get("base_price", 0))
    base_price = d.get("base_price", f"{raw_price:.2f}" if isinstance(raw_price, (int, float)) else str(raw_price))
    combo_slots = None
    if d.get("combo_slots"):
        combo_slots = [
            ComboSlotPayloadDto(
                name=cs["name"],
                min_selections=cs["min_selections"],
                max_selections=cs["max_selections"],
                eligible_item_ids=cs["eligible_item_ids"],
            )
            for cs in d["combo_slots"]
        ]
    mods = None
    if modifier_groups is not None:
        mods = [modifier_group_from_dict(mg) for mg in modifier_groups]
    return MenuItemPayloadDto(
        id=d["id"],
        market_id=d.get("market_id"),
        category=cat,
        name=d["name"],
        description=d.get("description"),
        item_type=d.get("item_type", "single"),
        base_price=base_price,
        cost_price=d.get("cost_price"),
        image_url=d.get("image_url"),
        calories=d.get("calories"),
        is_active=d.get("is_active", d.get("is_available", True)),
        sort_order=d.get("sort_order"),
        effective_price=effective_price,
        store_override=store_override_price,
        availability_rule=d.get("availability_rule"),
        modifier_groups=mods,
        combo_slots=combo_slots,
        created_at=d.get("created_at", "2025-01-01T00:00:00Z"),
        updated_at=d.get("updated_at", "2025-01-01T00:00:00Z"),
    )


def store_override_from_dict(d: dict) -> StoreOverridePayloadDto:
    return StoreOverridePayloadDto(
        id=d["id"],
        store_id=d["store_id"],
        menu_item_id=d["menu_item_id"],
        override_type=d["override_type"],
        override_price=d.get("override_price"),
        reason=d["reason"],
        effective_from=d.get("effective_from"),
        effective_until=d.get("effective_until"),
    )
