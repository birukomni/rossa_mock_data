"""Address resolvers — all authenticated + stateful."""
from __future__ import annotations
import uuid
import strawberry
from mock_server.types import (
    ListAddressesInput, AddressListResponse,
    CreateAddressInput, AddressResponse,
    SetDefaultAddressInput, DeleteAddressInput, EmptyResponse,
    ResponseMetaDto, address_from_dict,
)
from mock_server.store import store
from mock_server.auth import require_auth
from mock_server.utils import utc_now, maybe_delay


async def my_addresses(info: strawberry.types.Info, input: ListAddressesInput) -> AddressListResponse:
    await maybe_delay()
    user = require_auth(info)
    page = input.page or 1
    size = input.size or 20
    all_addrs = store.get_addresses(user["id"])

    # Sort
    reverse = (input.order and input.order.value == "DESC")
    order_field = (input.order_by or "created_at").replace("createdAt", "created_at").replace("updatedAt", "updated_at")
    all_addrs.sort(key=lambda a: a.get(order_field, ""), reverse=bool(reverse))

    total = len(all_addrs)
    total_pages = max(1, -(-total // size))  # ceiling division
    start = (page - 1) * size
    page_addrs = all_addrs[start: start + size]

    return AddressListResponse(
        success=True,
        status=200,
        message="Addresses retrieved successfully.",
        meta=ResponseMetaDto(
            timestamp=utc_now(),
            page=page,
            page_size=size,
            total=total,
            total_pages=total_pages,
        ),
        payload=[address_from_dict(a) for a in page_addrs],
    )


async def create_address(info: strawberry.types.Info, input: CreateAddressInput) -> AddressResponse:
    await maybe_delay()
    user = require_auth(info)
    p = input.input
    now = utc_now()
    new_address = {
        "id": str(uuid.uuid4()),
        "account_id": user["id"],
        "label": p.label,
        "street": p.street,
        "suburb": p.suburb,
        "city": p.city,
        "postal_code": p.postal_code,
        "country": p.country.upper(),
        "latitude": p.latitude,
        "longitude": p.longitude,
        "is_default": False,
        "deliverable": False,
        "created_at": now,
        "updated_at": now,
    }
    store.add_address(new_address)
    return AddressResponse(
        success=True,
        status=201,
        message="Address created successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=address_from_dict(new_address),
    )


async def set_default_address(info: strawberry.types.Info, input: SetDefaultAddressInput) -> AddressResponse:
    await maybe_delay()
    user = require_auth(info)
    updated = store.set_default_address(input.address_id, user["id"])
    if not updated:
        raise Exception("Address not found.")
    return AddressResponse(
        success=True,
        status=200,
        message="Default address updated successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=address_from_dict(updated),
    )


async def delete_address(info: strawberry.types.Info, input: DeleteAddressInput) -> EmptyResponse:
    await maybe_delay()
    user = require_auth(info)
    deleted = store.delete_address(input.address_id, user["id"])
    if not deleted:
        raise Exception("Address not found.")
    return EmptyResponse(
        success=True,
        status=200,
        message="Address deleted successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
    )
