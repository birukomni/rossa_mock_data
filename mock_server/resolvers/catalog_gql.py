"""
GraphQL resolvers for the Catalog domain.
Implements listCategories, listMenuItems (with store-contextual pricing),
createCategory, createMenuItem, createModifierGroup, createStoreOverride
as defined in docs/ddt/graphql/graphql-*-catalog-*.md
"""
from __future__ import annotations

import uuid
import strawberry

from typing import Optional

from mock_server.types import (
    ListCategoriesInput, CreateCategoryInput,
    ListMenuItemsInput, CreateMenuItemInput,
    CreateModifierGroupInput, CreateStoreOverrideInput,
    CategoryListResponse, CategoryResponse,
    MenuItemListResponse, MenuItemResponse,
    ModifierGroupResponse, StoreOverrideResponse,
    ResponseMetaDto,
    category_from_dict, menu_item_from_dict,
    modifier_group_from_dict, store_override_from_dict,
    ModifierPayloadDto,
)
from mock_server.store import store
from mock_server.auth import require_auth
from mock_server.utils import utc_now, maybe_delay


async def list_categories(
    info: strawberry.types.Info,
    input: Optional[ListCategoriesInput] = None,
) -> CategoryListResponse:
    """Public — returns a paginated list of menu categories."""
    await maybe_delay()
    input = input or ListCategoriesInput()
    cats = store.categories

    # Filters
    if input.market_id:
        cats = [c for c in cats if c.get("market_id") == input.market_id]
    if input.is_active is not None:
        cats = [c for c in cats if c.get("is_active", True) == input.is_active]

    # Pagination
    page = max(1, input.page or 1)
    size = min(100, max(1, input.size or 20))
    total = len(cats)
    start = (page - 1) * size
    page_items = cats[start:start + size]

    return CategoryListResponse(
        success=True,
        status=200,
        message="Categories retrieved successfully.",
        count=total,
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=[category_from_dict(c) for c in page_items],
    )


async def list_menu_items(
    info: strawberry.types.Info,
    input: Optional[ListMenuItemsInput] = None,
) -> MenuItemListResponse:
    """Public — returns paginated menu items with optional store-level price overrides."""
    await maybe_delay()
    input = input or ListMenuItemsInput()
    items = store.menu_items

    # Filters
    if input.market_id:
        items = [i for i in items if i.get("market_id") == input.market_id]
    if input.category_id:
        items = [i for i in items if i.get("category_id") == input.category_id]
    if input.item_type:
        items = [i for i in items if i.get("item_type", "single") == input.item_type.value]
    if input.is_active is not None:
        items = [i for i in items if i.get("is_active", i.get("is_available", True)) == input.is_active]

    # Build store overrides map for this storeId if provided
    override_map: dict[str, dict] = {}
    hidden_items: set[str] = set()
    if input.store_id:
        overrides = store.get_store_overrides(store_id=input.store_id)
        for ov in overrides:
            if ov["override_type"] == "hidden":
                hidden_items.add(ov["menu_item_id"])
            else:
                override_map[ov["menu_item_id"]] = ov

        # Remove hidden items
        items = [i for i in items if i["id"] not in hidden_items]

    # Pagination
    page = max(1, input.page or 1)
    size = min(100, max(1, input.size or 20))
    total = len(items)
    start = (page - 1) * size
    page_items = items[start:start + size]

    result = []
    for item in page_items:
        cat_dict = store.get_category(item.get("category_id", ""))
        mod_groups = store.get_modifier_groups(item["id"])
        ov = override_map.get(item["id"])
        effective_price = None
        store_override_price = None
        if ov:
            store_override_price = ov.get("override_price")
            effective_price = store_override_price
        elif input.store_id:
            # No override → effective price equals base price
            raw = item.get("price", item.get("base_price", 0))
            effective_price = f"{raw:.2f}" if isinstance(raw, (int, float)) else str(raw)
        result.append(
            menu_item_from_dict(
                item,
                category_dict=cat_dict,
                effective_price=effective_price,
                store_override_price=store_override_price,
                modifier_groups=mod_groups,
            )
        )

    return MenuItemListResponse(
        success=True,
        status=200,
        message="Menu items retrieved successfully.",
        count=total,
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=result,
    )


async def create_category(
    info: strawberry.types.Info,
    input: CreateCategoryInput,
) -> CategoryResponse:
    """Authenticated (catalog.manage) — creates a new menu category."""
    await maybe_delay()
    require_auth(info)

    # Duplicate name check
    mkt = input.market_id
    if any(
        c["name"].lower() == input.name.lower() and c.get("market_id") == mkt
        for c in store.categories
    ):
        raise Exception(f"A category named '{input.name}' already exists{' in market ' + mkt if mkt else ''}.")

    now = utc_now()
    new_cat = {
        "id": str(uuid.uuid4()),
        "market_id": input.market_id,
        "name": input.name,
        "description": input.description,
        "is_active": input.is_active if input.is_active is not None else True,
        "sort_order": input.sort_order,
        "created_at": now,
        "updated_at": now,
    }
    store.add_category(new_cat)
    return CategoryResponse(
        success=True,
        status=201,
        message="Category created successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=category_from_dict(new_cat),
    )


async def create_menu_item(
    info: strawberry.types.Info,
    input: CreateMenuItemInput,
) -> MenuItemResponse:
    """Authenticated (catalog.manage) — creates a new menu item (single or combo)."""
    await maybe_delay()
    require_auth(info)

    # Validate combo slots
    if input.item_type.value == "combo":
        if not input.combo_slots or len(input.combo_slots) == 0:
            raise Exception("comboSlots must contain at least 1 element for combo items.")

    now = utc_now()
    combo_slots_data = None
    if input.combo_slots:
        combo_slots_data = [
            {
                "name": cs.name,
                "min_selections": cs.min_selections,
                "max_selections": cs.max_selections,
                "eligible_item_ids": cs.eligible_item_ids,
            }
            for cs in input.combo_slots
        ]

    new_item = {
        "id": str(uuid.uuid4()),
        "market_id": input.market_id,
        "category_id": input.category_id,
        "name": input.name,
        "description": input.description,
        "item_type": input.item_type.value,
        "base_price": input.base_price,
        "price": float(input.base_price),
        "cost_price": input.cost_price,
        "image_url": input.image_url,
        "calories": input.calories,
        "is_active": input.is_active if input.is_active is not None else True,
        "is_available": input.is_active if input.is_active is not None else True,
        "sort_order": input.sort_order,
        "combo_slots": combo_slots_data,
        "created_at": now,
        "updated_at": now,
    }
    store.add_menu_item(new_item)
    cat_dict = store.get_category(input.category_id or "") if input.category_id else None
    return MenuItemResponse(
        success=True,
        status=201,
        message="Menu item created successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=menu_item_from_dict(new_item, category_dict=cat_dict, modifier_groups=[]),
    )


async def create_modifier_group(
    info: strawberry.types.Info,
    item_id: str,
    input: CreateModifierGroupInput,
) -> ModifierGroupResponse:
    """Authenticated (catalog.manage) — attaches a modifier group to a menu item."""
    await maybe_delay()
    require_auth(info)

    # Verify item exists
    item = store.get_menu_item(item_id)
    if not item:
        raise Exception("Menu item not found.")

    # Validate at least one modifier
    if not input.modifiers or len(input.modifiers) == 0:
        raise Exception("At least one modifier option must be provided.")

    now = utc_now()
    group_id = str(uuid.uuid4())
    modifiers_data = [
        {
            "id": str(uuid.uuid4()),
            "name": m.name,
            "price_adjustment": m.price_adjustment or "0.00",
            "is_active": True,
        }
        for m in input.modifiers
    ]
    new_group = {
        "id": group_id,
        "item_id": item_id,
        "name": input.name,
        "min_selections": input.min_selections,
        "max_selections": input.max_selections,
        "is_required": input.is_required if input.is_required is not None else False,
        "modifiers": modifiers_data,
    }
    store.add_modifier_group(new_group)
    return ModifierGroupResponse(
        success=True,
        status=201,
        message="Modifier group created successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=modifier_group_from_dict(new_group),
    )


async def create_store_override(
    info: strawberry.types.Info,
    input: CreateStoreOverrideInput,
) -> StoreOverrideResponse:
    """Authenticated (catalog.manage or store.manage) — applies a store-level override."""
    await maybe_delay()
    require_auth(info)

    # Validate price_override requires override_price
    if input.override_type.value == "price_override" and not input.override_price:
        raise Exception("overridePrice is required when overrideType is price_override.")

    # Validate store and item exist
    if not any(r["id"] == input.store_id for r in store.restaurants):
        raise Exception("Store not found.")
    if not store.get_menu_item(input.menu_item_id):
        raise Exception("Menu item not found.")

    now = utc_now()
    new_override = {
        "id": str(uuid.uuid4()),
        "store_id": input.store_id,
        "menu_item_id": input.menu_item_id,
        "override_type": input.override_type.value,
        "override_price": input.override_price,
        "reason": input.reason,
        "effective_from": input.effective_from,
        "effective_until": input.effective_until,
    }
    store.add_store_override(new_override)
    return StoreOverrideResponse(
        success=True,
        status=201,
        message="Store override applied successfully.",
        meta=ResponseMetaDto(timestamp=now),
        payload=store_override_from_dict(new_override),
    )
