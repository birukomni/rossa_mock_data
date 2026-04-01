"""
REST endpoints for Catalog Categories.
GET    /api/v1/catalog/categories        — list all categories
GET    /api/v1/catalog/categories/{id}   — single category
POST   /api/v1/catalog/categories        — create  [auth required]
PUT    /api/v1/catalog/categories/{id}   — full replace [auth required]
PATCH  /api/v1/catalog/categories/{id}   — partial update [auth required]
DELETE /api/v1/catalog/categories/{id}   — delete [auth required]
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mock_server.auth import rest_auth
from mock_server.store import store

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 99
    is_active: bool = True


class CategoryPatch(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/categories", summary="List all categories")
def list_categories():
    cats = store.get_categories()
    return {"success": True, "status": 200, "count": len(cats), "data": cats}


@router.get("/categories/{category_id}", summary="Get single category")
def get_category(category_id: str):
    cat = store.get_category(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "status": 200, "data": cat}


@router.post("/categories", summary="Create category", status_code=201)
def create_category(body: CategoryCreate, user_id: str = rest_auth):
    now = datetime.now(timezone.utc).isoformat()
    new_c = {
        "id": f"cat-{uuid.uuid4().hex[:8]}",
        **body.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    store.add_category(new_c)
    return {"success": True, "status": 201, "data": new_c}


@router.put("/categories/{category_id}", summary="Full replace category")
def replace_category(category_id: str, body: CategoryCreate, user_id: str = rest_auth):
    if not store.get_category(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    now = datetime.now(timezone.utc).isoformat()
    updated = store.update_category(category_id, {**body.model_dump(), "updated_at": now})
    return {"success": True, "status": 200, "data": updated}


@router.patch("/categories/{category_id}", summary="Partial update category")
def patch_category(category_id: str, body: CategoryPatch, user_id: str = rest_auth):
    if not store.get_category(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    now = datetime.now(timezone.utc).isoformat()
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    fields["updated_at"] = now
    updated = store.update_category(category_id, fields)
    return {"success": True, "status": 200, "data": updated}


@router.delete("/categories/{category_id}", summary="Delete category")
def delete_category(category_id: str, user_id: str = rest_auth):
    deleted = store.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "status": 200, "message": "Category deleted"}
