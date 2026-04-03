"""
GraphQL resolvers for the Stores domain.
Implements findAllStores, findOneStore, createStore, updateStore, deleteStore
as defined in docs/ddt/graphql/graphql-*-stores-*.md
"""
from __future__ import annotations

import uuid
import strawberry

from typing import Optional

from mock_server.types import (
    FindAllStoresInput, FindOneStoreInput, CreateStoreInput,
    UpdateStoreInput, DeleteStoreInput,
    StoreListResponse, StoreResponse, DeleteStoreResponse,
    ResponseMetaDto, store_from_dict,
)
from mock_server.store import store
from mock_server.auth import require_auth
from mock_server.utils import utc_now, maybe_delay


async def find_all_stores(
    info: strawberry.types.Info,
    input: Optional[FindAllStoresInput] = None,
) -> StoreListResponse:
    """Public — returns a paginated list of all stores."""
    await maybe_delay()
    input = input or FindAllStoresInput()
    restaurants = store.restaurants

    # Pagination
    page = max(1, input.page or 1)
    size = min(100, max(1, input.size or 25))
    total = len(restaurants)
    start = (page - 1) * size
    end = start + size
    page_items = restaurants[start:end]

    return StoreListResponse(
        success=True,
        status=200,
        message="Stores retrieved successfully.",
        count=total,
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=[store_from_dict(r) for r in page_items],
    )


async def find_one_store(
    info: strawberry.types.Info,
    input: FindOneStoreInput,
) -> StoreResponse:
    """Public — returns a single store by ID."""
    await maybe_delay()
    r = next((x for x in store.restaurants if x["id"] == input.id), None)
    if not r:
        return StoreResponse(
            success=False,
            status=404,
            message="Store not found.",
            meta=ResponseMetaDto(timestamp=utc_now()),
        )
    return StoreResponse(
        success=True,
        status=200,
        message="Store retrieved successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=store_from_dict(r),
    )


async def create_store(
    info: strawberry.types.Info,
    input: CreateStoreInput,
) -> StoreResponse:
    """Authenticated — creates a new store."""
    await maybe_delay()
    require_auth(info)

    # Check for duplicate code
    if any(r.get("code") == input.code for r in store.restaurants):
        raise Exception(f"A store with code {input.code} already exists.")

    caps: list[str] = []
    if input.capabilities:
        caps = [c.strip() for c in input.capabilities.split(",") if c.strip()]

    now = utc_now()
    new_store = {
        "id": str(uuid.uuid4()),
        "name": input.name,
        "code": input.code,
        "address": input.address,
        "location": {"lat": input.location.lat, "lng": input.location.lng} if input.location else None,
        "is_active": input.is_active,
        "is_open": input.is_active,
        "capabilities": caps,
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    store.restaurants.append(new_store)
    return StoreResponse(
        success=True,
        status=201,
        message="Store created successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=store_from_dict(new_store),
    )


async def update_store(
    info: strawberry.types.Info,
    input: UpdateStoreInput,
) -> StoreResponse:
    """Authenticated — partially updates a store."""
    await maybe_delay()
    require_auth(info)

    r = next((x for x in store.restaurants if x["id"] == input.id), None)
    if not r:
        raise Exception("Store not found.")

    # Optimistic locking check
    if input.version is not None and r.get("version") != input.version:
        raise Exception("Conflict: the store has been modified by another request. Refresh and retry.")

    now = utc_now()
    if input.name is not None:
        r["name"] = input.name
    if input.code is not None:
        r["code"] = input.code
    if input.address is not None:
        r["address"] = input.address
    if input.location is not None:
        r["location"] = {"lat": input.location.lat, "lng": input.location.lng}
    if input.is_active is not None:
        r["is_active"] = input.is_active
        r["is_open"] = input.is_active
    if input.capabilities is not None:
        r["capabilities"] = [c.strip() for c in input.capabilities.split(",") if c.strip()]
    r["version"] = r.get("version", 1) + 1
    r["updated_at"] = now

    return StoreResponse(
        success=True,
        status=200,
        message="Store updated successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=store_from_dict(r),
    )


async def delete_store(
    info: strawberry.types.Info,
    input: DeleteStoreInput,
) -> DeleteStoreResponse:
    """Authenticated — permanently deletes a store."""
    await maybe_delay()
    require_auth(info)

    deleted = store.delete_restaurant(input.id)
    if not deleted:
        raise Exception("Store not found.")

    return DeleteStoreResponse(
        success=True,
        status=204,
        message="Store deleted successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
    )
