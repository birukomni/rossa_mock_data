"""
Strawberry schema — wires all queries and mutations together.
"""
from __future__ import annotations
from typing import Optional, List
import strawberry

from mock_server.types import (
    # ── Input types ─────────────────────────────────────────────────────────
    OtpRequestInput, VerifyOtpInput, LoginInput, RegisterInput, ForgotPasswordInput,
    RefreshTokensInput,
    GetMyProfileInput, GetMyOperatorUserProfileInput, UpdateProfileInput, DeleteAccountInput,
    ListAddressesInput, CreateAddressInput, SetDefaultAddressInput, DeleteAddressInput,
    GetOnboardingChecklistInput, ActivateMarketInput, UpdateMarketMembershipStatusInput,
    MyConsentsInput, GrantConsentsInput, WithdrawConsentInput, RequestDataExportInput,
    # Stores input
    FindAllStoresInput, FindOneStoreInput, CreateStoreInput, UpdateStoreInput, DeleteStoreInput,
    # Catalog input
    ListCategoriesInput, CreateCategoryInput,
    ListMenuItemsInput, CreateMenuItemInput,
    CreateModifierGroupInput, CreateStoreOverrideInput,
    # ── Response types ───────────────────────────────────────────────────────
    OtpRequestResponse, LoginResponse, AuthnUserResponse, EmptyResponse,
    ProfileResponse, OperatorUserProfileResponse, AddressListResponse, AddressResponse,
    OnboardingChecklistResponse, MarketMembershipResponse,
    ConsentListResponse, ConsentResponse,
    # Stores responses
    StoreListResponse, StoreResponse, DeleteStoreResponse,
    # Catalog responses
    CategoryListResponse, CategoryResponse,
    MenuItemListResponse, MenuItemResponse,
    ModifierGroupResponse, StoreOverrideResponse,
)
from mock_server.resolvers import operator_user_profile
from mock_server.resolvers import stores_gql, catalog_gql


@strawberry.type
class Query:
    # User / Profile
    # my_profile: ProfileResponse = strawberry.field(resolver=profile.my_profile)
    my_operator_user_profile: OperatorUserProfileResponse = strawberry.field(
        resolver=operator_user_profile.my_operator_user_profile
    )
    # my_addresses: AddressListResponse = strawberry.field(resolver=address.my_addresses)
    # market_onboarding_checklist: OnboardingChecklistResponse = strawberry.field(
    #     resolver=market.market_onboarding_checklist
    # )
    # my_consents: ConsentListResponse = strawberry.field(resolver=consent.my_consents)
    # Stores
    find_all_stores: StoreListResponse = strawberry.field(resolver=stores_gql.find_all_stores)
    find_one_store: StoreResponse = strawberry.field(resolver=stores_gql.find_one_store)
    # Catalog
    list_categories: CategoryListResponse = strawberry.field(resolver=catalog_gql.list_categories)
    list_menu_items: MenuItemListResponse = strawberry.field(resolver=catalog_gql.list_menu_items)


@strawberry.type
class Mutation:
    # Auth (unauthenticated)
    # request_otp: OtpRequestResponse = strawberry.mutation(resolver=auth.request_otp)
    # verify_otp: LoginResponse = strawberry.mutation(resolver=auth.verify_otp)
    # login: LoginResponse = strawberry.mutation(resolver=auth.login)
    # register: AuthnUserResponse = strawberry.mutation(resolver=auth.register)
    # forgot_password: EmptyResponse = strawberry.mutation(resolver=auth.forgot_password)
    # refresh_tokens: LoginResponse = strawberry.mutation(resolver=auth.refresh_tokens)

    # Profile (authenticated)
    # update_profile: ProfileResponse = strawberry.mutation(resolver=profile.update_profile)
    # delete_account: EmptyResponse = strawberry.mutation(resolver=profile.delete_account)

    # Addresses (authenticated + stateful)
    # create_address: AddressResponse = strawberry.mutation(resolver=address.create_address)
    # set_default_address: AddressResponse = strawberry.mutation(resolver=address.set_default_address)
    # delete_address: EmptyResponse = strawberry.mutation(resolver=address.delete_address)

    # Markets (authenticated)
    # activate_market: MarketMembershipResponse = strawberry.mutation(resolver=market.activate_market)
    # update_market_membership_status: MarketMembershipResponse = strawberry.mutation(
    #     resolver=market.update_market_membership_status
    # )

    # Consents / GDPR (authenticated)
    # grant_consents: ConsentListResponse = strawberry.mutation(resolver=consent.grant_consents)
    # withdraw_consent: ConsentResponse = strawberry.mutation(resolver=consent.withdraw_consent)
    # request_data_export: EmptyResponse = strawberry.mutation(resolver=consent.request_data_export)

    # Stores (authenticated for writes)
    create_store: StoreResponse = strawberry.mutation(resolver=stores_gql.create_store)
    update_store: StoreResponse = strawberry.mutation(resolver=stores_gql.update_store)
    delete_store: DeleteStoreResponse = strawberry.mutation(resolver=stores_gql.delete_store)

    # Catalog (authenticated for writes)
    create_category: CategoryResponse = strawberry.mutation(resolver=catalog_gql.create_category)
    create_menu_item: MenuItemResponse = strawberry.mutation(resolver=catalog_gql.create_menu_item)
    create_modifier_group: ModifierGroupResponse = strawberry.mutation(resolver=catalog_gql.create_modifier_group)
    create_store_override: StoreOverrideResponse = strawberry.mutation(resolver=catalog_gql.create_store_override)


schema = strawberry.Schema(query=Query, mutation=Mutation)

