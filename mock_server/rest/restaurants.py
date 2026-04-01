"""
REST endpoints for Restaurants.
GET    /api/v1/restaurants           — list (filter: city, is_open, search)
GET    /api/v1/restaurants/top       — top-rated restaurants (query: limit)
GET    /api/v1/restaurants/{id}      — single restaurant
POST   /api/v1/restaurants           — create  [auth required]
PUT    /api/v1/restaurants/{id}      — full replace [auth required]
PATCH  /api/v1/restaurants/{id}      — partial update [auth required]
DELETE /api/v1/restaurants/{id}      — delete [auth required]
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mock_server.auth import rest_auth
from mock_server.store import store

router = APIRouter(prefix="/api/v1/restaurants", tags=["restaurants"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class OpeningHours(BaseModel):
    mon_fri: str
    sat_sun: str


class RestaurantCreate(BaseModel):
    name: str
    address: str
    city: str
    postal_code: Optional[str] = ""
    country: str
    latitude: float
    longitude: float
    phone: str
    email: Optional[str] = None
    is_open: bool = True
    rating: float = 0.0
    review_count: int = 0
    distance_km: float = 0.0
    avg_preparation_minutes: int = 15
    delivery_fee: float = 0.0
    min_order_amount: float = 0.0
    currency: str = "KES"
    image_url: Optional[str] = None
    tags: list[str] = []
    opening_hours: Optional[OpeningHours] = None


class RestaurantPatch(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_open: Optional[bool] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    distance_km: Optional[float] = None
    avg_preparation_minutes: Optional[int] = None
    delivery_fee: Optional[float] = None
    min_order_amount: Optional[float] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[list[str]] = None
    opening_hours: Optional[OpeningHours] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", summary="List restaurants")
def list_restaurants(
    city: Optional[str] = Query(None),
    is_open: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
):
    results = store.get_restaurants(city=city, is_open=is_open, search=search)
    return {"success": True, "status": 200, "count": len(results), "data": results}


@router.get("/top", summary="Get top-rated restaurants")
def get_top_restaurants(limit: int = Query(5, ge=1, le=50)):
    results = store.get_top_restaurants(limit=limit)
    return {"success": True, "status": 200, "count": len(results), "data": results}


@router.get("/{restaurant_id}", summary="Get single restaurant")
def get_restaurant(restaurant_id: str):
    r = store.get_restaurant(restaurant_id)
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return {"success": True, "status": 200, "data": r}


@router.post("", summary="Create restaurant", status_code=201)
def create_restaurant(body: RestaurantCreate, user_id: str = rest_auth):
    now = datetime.now(timezone.utc).isoformat()
    new_r = {
        "id": f"rest-{uuid.uuid4().hex[:8]}",
        **body.model_dump(),
        "opening_hours": body.opening_hours.model_dump() if body.opening_hours else None,
        "created_at": now,
        "updated_at": now,
    }
    store.add_restaurant(new_r)
    return {"success": True, "status": 201, "data": new_r}


@router.put("/{restaurant_id}", summary="Full replace restaurant")
def replace_restaurant(restaurant_id: str, body: RestaurantCreate, user_id: str = rest_auth):
    if not store.get_restaurant(restaurant_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")
    now = datetime.now(timezone.utc).isoformat()
    updated = store.update_restaurant(
        restaurant_id,
        {
            **body.model_dump(),
            "opening_hours": body.opening_hours.model_dump() if body.opening_hours else None,
            "updated_at": now,
        },
    )
    return {"success": True, "status": 200, "data": updated}


@router.patch("/{restaurant_id}", summary="Partial update restaurant")
def patch_restaurant(restaurant_id: str, body: RestaurantPatch, user_id: str = rest_auth):
    if not store.get_restaurant(restaurant_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")
    now = datetime.now(timezone.utc).isoformat()
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    fields["updated_at"] = now
    updated = store.update_restaurant(restaurant_id, fields)
    return {"success": True, "status": 200, "data": updated}


@router.delete("/{restaurant_id}", summary="Delete restaurant")
def delete_restaurant(restaurant_id: str, user_id: str = rest_auth):
    deleted = store.delete_restaurant(restaurant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return {"success": True, "status": 200, "message": "Restaurant deleted"}
