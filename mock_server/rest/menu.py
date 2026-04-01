"""
REST endpoints for Menu Items.
GET    /api/v1/menu/items           — list (filter: restaurant_id, category_id, is_available, is_featured)
GET    /api/v1/menu/items/{id}      — single item
POST   /api/v1/menu/items           — create  [auth required]
PUT    /api/v1/menu/items/{id}      — full replace [auth required]
PATCH  /api/v1/menu/items/{id}      — partial update [auth required]
DELETE /api/v1/menu/items/{id}      — delete [auth required]
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mock_server.auth import rest_auth
from mock_server.store import store

router = APIRouter(prefix="/api/v1/menu", tags=["menu"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class MenuItemCreate(BaseModel):
    restaurant_id: str
    category_id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "KES"
    image_url: Optional[str] = None
    calories: Optional[int] = None
    is_available: bool = True
    is_featured: bool = False
    tags: list[str] = []


class MenuItemPatch(BaseModel):
    restaurant_id: Optional[str] = None
    category_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    calories: Optional[int] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    tags: Optional[list[str]] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/items", summary="List menu items")
def list_menu_items(
    restaurant_id: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
):
    results = store.get_menu_items(
        restaurant_id=restaurant_id,
        category_id=category_id,
        is_available=is_available,
        is_featured=is_featured,
    )
    return {"success": True, "status": 200, "count": len(results), "data": results}


@router.get("/items/{item_id}", summary="Get single menu item")
def get_menu_item(item_id: str):
    item = store.get_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"success": True, "status": 200, "data": item}


@router.post("/items", summary="Create menu item", status_code=201)
def create_menu_item(body: MenuItemCreate, user_id: str = rest_auth):
    now = datetime.now(timezone.utc).isoformat()
    new_item = {
        "id": f"item-{uuid.uuid4().hex[:8]}",
        **body.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    store.add_menu_item(new_item)
    return {"success": True, "status": 201, "data": new_item}


@router.put("/items/{item_id}", summary="Full replace menu item")
def replace_menu_item(item_id: str, body: MenuItemCreate, user_id: str = rest_auth):
    if not store.get_menu_item(item_id):
        raise HTTPException(status_code=404, detail="Menu item not found")
    now = datetime.now(timezone.utc).isoformat()
    updated = store.update_menu_item(item_id, {**body.model_dump(), "updated_at": now})
    return {"success": True, "status": 200, "data": updated}


@router.patch("/items/{item_id}", summary="Partial update menu item")
def patch_menu_item(item_id: str, body: MenuItemPatch, user_id: str = rest_auth):
    if not store.get_menu_item(item_id):
        raise HTTPException(status_code=404, detail="Menu item not found")
    now = datetime.now(timezone.utc).isoformat()
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    fields["updated_at"] = now
    updated = store.update_menu_item(item_id, fields)
    return {"success": True, "status": 200, "data": updated}


@router.delete("/items/{item_id}", summary="Delete menu item")
def delete_menu_item(item_id: str, user_id: str = rest_auth):
    deleted = store.delete_menu_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"success": True, "status": 200, "message": "Menu item deleted"}
