"""
REST endpoints for Orders.
GET    /api/v1/orders                  — list caller's orders (filter: status, page, page_size)
GET    /api/v1/orders/{id}             — single order (must belong to caller)
POST   /api/v1/orders                  — place new order
PUT    /api/v1/orders/{id}             — full replace order (admin)
PATCH  /api/v1/orders/{id}/status      — advance order status
DELETE /api/v1/orders/{id}             — cancel order

All endpoints require Bearer token auth.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mock_server.auth import rest_auth
from mock_server.store import store

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

# Valid status transitions (state machine)
VALID_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["preparing", "cancelled"],
    "preparing": ["out_for_delivery"],
    "out_for_delivery": ["delivered"],
    "delivered": [],
    "cancelled": [],
}


# ── Pydantic models ───────────────────────────────────────────────────────────

class DeliveryAddressInput(BaseModel):
    street: str
    suburb: Optional[str] = None
    city: str
    postal_code: str
    country: str
    latitude: float
    longitude: float


class OrderItemInput(BaseModel):
    menu_item_id: str
    quantity: int


class OrderCreate(BaseModel):
    restaurant_id: str
    items: list[OrderItemInput]
    payment_method: str  # card | mpesa | cash
    delivery_address: DeliveryAddressInput
    special_instructions: Optional[str] = ""


class OrderStatusPatch(BaseModel):
    status: str


class OrderPut(BaseModel):
    restaurant_id: str
    status: str
    payment_status: str
    payment_method: str
    items: list[dict]
    subtotal: float
    delivery_fee: float
    tax: float
    total: float
    currency: str
    delivery_address: DeliveryAddressInput
    special_instructions: Optional[str] = ""
    estimated_delivery_minutes: int


# ── Helper ────────────────────────────────────────────────────────────────────

def _resolve_order_items(raw_items: list[OrderItemInput]) -> tuple[list[dict], float]:
    """Look up each menu item, attach image + name, compute subtotal."""
    enriched = []
    subtotal = 0.0
    for itm in raw_items:
        menu_item = store.get_menu_item(itm.menu_item_id)
        if not menu_item:
            raise HTTPException(status_code=400, detail=f"Menu item not found: {itm.menu_item_id}")
        line_total = menu_item["price"] * itm.quantity
        subtotal += line_total
        enriched.append({
            "menu_item_id": itm.menu_item_id,
            "name": menu_item["name"],
            "image_url": menu_item.get("image_url"),
            "quantity": itm.quantity,
            "unit_price": menu_item["price"],
            "subtotal": line_total,
        })
    return enriched, subtotal


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", summary="List my orders")
def list_orders(
    user_id: str = rest_auth,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    all_orders = store.get_orders(user_id=user_id, status=status)
    start = (page - 1) * page_size
    paginated = all_orders[start: start + page_size]
    return {
        "success": True,
        "status": 200,
        "count": len(all_orders),
        "page": page,
        "page_size": page_size,
        "data": paginated,
    }


@router.get("/{order_id}", summary="Get single order")
def get_order(order_id: str, user_id: str = rest_auth):
    order = store.get_order(order_id, user_id=user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"success": True, "status": 200, "data": order}


@router.post("", summary="Place new order", status_code=201)
def place_order(body: OrderCreate, user_id: str = rest_auth):
    restaurant = store.get_restaurant(body.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=400, detail="Restaurant not found")

    now = datetime.now(timezone.utc).isoformat()
    enriched_items, subtotal = _resolve_order_items(body.items)

    delivery_fee = restaurant.get("delivery_fee", 0)
    tax = round(subtotal * 0.16, 2)
    total = round(subtotal + delivery_fee + tax, 2)

    new_order = {
        "id": f"ord-{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "restaurant_id": body.restaurant_id,
        "status": "pending",
        "payment_status": "pending",
        "payment_method": body.payment_method,
        "items": enriched_items,
        "subtotal": round(subtotal, 2),
        "delivery_fee": delivery_fee,
        "tax": tax,
        "total": total,
        "currency": restaurant.get("currency", "KES"),
        "delivery_address": body.delivery_address.model_dump(),
        "special_instructions": body.special_instructions or "",
        "estimated_delivery_minutes": restaurant.get("avg_preparation_minutes", 15) + 10,
        "placed_at": now,
        "updated_at": now,
    }
    store.add_order(new_order)
    return {"success": True, "status": 201, "data": new_order}


@router.put("/{order_id}", summary="Full replace order")
def replace_order(order_id: str, body: OrderPut, user_id: str = rest_auth):
    if not store.get_order(order_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="Order not found")
    now = datetime.now(timezone.utc).isoformat()
    updated = store.update_order(
        order_id,
        {
            **body.model_dump(),
            "delivery_address": body.delivery_address.model_dump(),
            "updated_at": now,
        },
    )
    return {"success": True, "status": 200, "data": updated}


@router.patch("/{order_id}/status", summary="Advance order status")
def patch_order_status(order_id: str, body: OrderStatusPatch, user_id: str = rest_auth):
    order = store.get_order(order_id, user_id=user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    current = order["status"]
    allowed = VALID_TRANSITIONS.get(current, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot transition from '{current}' to '{body.status}'. Allowed: {allowed}",
        )

    now = datetime.now(timezone.utc).isoformat()
    updated = store.update_order(order_id, {"status": body.status, "updated_at": now})
    return {"success": True, "status": 200, "data": updated}


@router.delete("/{order_id}", summary="Cancel order")
def cancel_order(order_id: str, user_id: str = rest_auth):
    cancelled = store.cancel_order(order_id, user_id)
    if not cancelled:
        raise HTTPException(
            status_code=422,
            detail="Order not found or cannot be cancelled (already delivered or cancelled)",
        )
    return {"success": True, "status": 200, "data": cancelled}
