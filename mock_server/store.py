"""
In-memory mutable state store.
All mutations (createAddress, grantConsents, etc.) update this store.
Resets to seed data on server restart.
"""
from __future__ import annotations
import copy
import uuid
from mock_server.seed import (
    SEED_USERS,
    SEED_PROFILES,
    SEED_ADDRESSES,
    SEED_MARKETS,
    SEED_CHECKLISTS,
    SEED_CONSENTS,
    SEED_RESTAURANTS,
    SEED_CATALOG_CATEGORIES,
    SEED_MENU_ITEMS,
    SEED_ORDERS,
)


class MockStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.users: list[dict] = copy.deepcopy(SEED_USERS)
        self.profiles: list[dict] = copy.deepcopy(SEED_PROFILES)
        self.addresses: list[dict] = copy.deepcopy(SEED_ADDRESSES)
        self.markets: list[dict] = copy.deepcopy(SEED_MARKETS)
        self.checklists: dict[str, dict] = copy.deepcopy(SEED_CHECKLISTS)
        self.consents: list[dict] = copy.deepcopy(SEED_CONSENTS)
        self.deleted_users: set[str] = set()
        self.restaurants: list[dict] = copy.deepcopy(SEED_RESTAURANTS)
        self.categories: list[dict] = copy.deepcopy(SEED_CATALOG_CATEGORIES)
        self.menu_items: list[dict] = copy.deepcopy(SEED_MENU_ITEMS)
        self.orders: list[dict] = copy.deepcopy(SEED_ORDERS)

    # ── User helpers ─────────────────────────────────────────────────────────
    def get_user(self, user_id: str) -> dict | None:
        return next((u for u in self.users if u["id"] == user_id), None)

    def add_user(self, user: dict) -> dict:
        self.users.append(user)
        return user

    def delete_user(self, user_id: str) -> None:
        self.deleted_users.add(user_id)
        self.users = [u for u in self.users if u["id"] != user_id]

    # ── Profile helpers ───────────────────────────────────────────────────────
    def get_profile(self, account_id: str) -> dict | None:
        return next((p for p in self.profiles if p["account_id"] == account_id), None)

    def update_profile(self, account_id: str, fields: dict) -> dict | None:
        for p in self.profiles:
            if p["account_id"] == account_id:
                p.update(fields)
                return p
        return None

    def add_profile(self, profile: dict) -> dict:
        self.profiles.append(profile)
        return profile

    # ── Address helpers ───────────────────────────────────────────────────────
    def get_addresses(self, account_id: str) -> list[dict]:
        return [a for a in self.addresses if a["account_id"] == account_id]

    def get_address(self, address_id: str, account_id: str) -> dict | None:
        return next(
            (a for a in self.addresses if a["id"] == address_id and a["account_id"] == account_id),
            None,
        )

    def add_address(self, address: dict) -> dict:
        self.addresses.append(address)
        return address

    def set_default_address(self, address_id: str, account_id: str) -> dict | None:
        found = None
        for a in self.addresses:
            if a["account_id"] == account_id:
                a["is_default"] = a["id"] == address_id
                if a["is_default"]:
                    found = a
        return found

    def delete_address(self, address_id: str, account_id: str) -> bool:
        before = len(self.addresses)
        self.addresses = [
            a for a in self.addresses
            if not (a["id"] == address_id and a["account_id"] == account_id)
        ]
        return len(self.addresses) < before

    # ── Market helpers ────────────────────────────────────────────────────────
    def get_membership(self, user_id: str, market_id: str) -> dict | None:
        return next(
            (m for m in self.markets if m["user_id"] == user_id and m["market_id"] == market_id),
            None,
        )

    def activate_market(self, user_id: str, market_id: str, activated_at: str) -> dict:
        existing = self.get_membership(user_id, market_id)
        if existing:
            existing["status"] = "active"
            existing["activated_at"] = activated_at
            return existing
        membership = {"user_id": user_id, "market_id": market_id, "status": "active", "activated_at": activated_at}
        self.markets.append(membership)
        return membership

    def update_membership_status(self, user_id: str, market_id: str, status: str) -> dict | None:
        m = self.get_membership(user_id, market_id)
        if m:
            m["status"] = status
        return m

    def get_checklist(self, market_id: str) -> dict | None:
        return self.checklists.get(market_id)

    # ── Consent helpers ───────────────────────────────────────────────────────
    def get_consents(self, user_id: str) -> list[dict]:
        return [c for c in self.consents if c["user_id"] == user_id]

    def grant_consents(self, user_id: str, consent_types: list[str], granted_at: str) -> list[dict]:
        results = []
        for ct in consent_types:
            existing = next(
                (c for c in self.consents if c["user_id"] == user_id and c["consent_type"] == ct),
                None,
            )
            if existing:
                existing["granted"] = True
                existing["granted_at"] = granted_at
                existing["withdrawn_at"] = None
                results.append(existing)
            else:
                new_consent = {
                    "user_id": user_id,
                    "consent_type": ct,
                    "granted": True,
                    "granted_at": granted_at,
                    "withdrawn_at": None,
                }
                self.consents.append(new_consent)
                results.append(new_consent)
        return results

    def withdraw_consent(self, user_id: str, consent_type: str, withdrawn_at: str) -> dict | None:
        for c in self.consents:
            if c["user_id"] == user_id and c["consent_type"] == consent_type:
                c["granted"] = False
                c["withdrawn_at"] = withdrawn_at
                return c
        return None

    # ── Restaurant helpers ────────────────────────────────────────────────────

    def get_restaurants(
        self, city: str | None = None, is_open: bool | None = None, search: str | None = None
    ) -> list[dict]:
        results = self.restaurants
        if city is not None:
            results = [r for r in results if r["city"].lower() == city.lower()]
        if is_open is not None:
            results = [r for r in results if r["is_open"] == is_open]
        if search:
            q = search.lower()
            results = [
                r for r in results
                if q in r["name"].lower() or q in r["address"].lower() or q in r["city"].lower()
            ]
        return results

    def get_top_restaurants(self, limit: int = 10) -> list[dict]:
        return sorted(self.restaurants, key=lambda r: r["rating"], reverse=True)[:limit]

    def get_restaurant(self, restaurant_id: str) -> dict | None:
        return next((r for r in self.restaurants if r["id"] == restaurant_id), None)

    def add_restaurant(self, r: dict) -> dict:
        self.restaurants.append(r)
        return r

    def update_restaurant(self, restaurant_id: str, fields: dict) -> dict | None:
        for r in self.restaurants:
            if r["id"] == restaurant_id:
                r.update(fields)
                return r
        return None

    def delete_restaurant(self, restaurant_id: str) -> bool:
        before = len(self.restaurants)
        self.restaurants = [r for r in self.restaurants if r["id"] != restaurant_id]
        return len(self.restaurants) < before

    # ── Catalog helpers ───────────────────────────────────────────────────────

    def get_categories(self) -> list[dict]:
        return self.categories

    def get_category(self, category_id: str) -> dict | None:
        return next((c for c in self.categories if c["id"] == category_id), None)

    def add_category(self, c: dict) -> dict:
        self.categories.append(c)
        return c

    def update_category(self, category_id: str, fields: dict) -> dict | None:
        for c in self.categories:
            if c["id"] == category_id:
                c.update(fields)
                return c
        return None

    def delete_category(self, category_id: str) -> bool:
        before = len(self.categories)
        self.categories = [c for c in self.categories if c["id"] != category_id]
        return len(self.categories) < before

    # ── Menu item helpers ─────────────────────────────────────────────────────

    def get_menu_items(
        self,
        restaurant_id: str | None = None,
        category_id: str | None = None,
        is_available: bool | None = None,
        is_featured: bool | None = None,
    ) -> list[dict]:
        results = self.menu_items
        if restaurant_id:
            results = [i for i in results if i["restaurant_id"] == restaurant_id]
        if category_id:
            results = [i for i in results if i["category_id"] == category_id]
        if is_available is not None:
            results = [i for i in results if i["is_available"] == is_available]
        if is_featured is not None:
            results = [i for i in results if i["is_featured"] == is_featured]
        return results

    def get_menu_item(self, item_id: str) -> dict | None:
        return next((i for i in self.menu_items if i["id"] == item_id), None)

    def add_menu_item(self, item: dict) -> dict:
        self.menu_items.append(item)
        return item

    def update_menu_item(self, item_id: str, fields: dict) -> dict | None:
        for i in self.menu_items:
            if i["id"] == item_id:
                i.update(fields)
                return i
        return None

    def delete_menu_item(self, item_id: str) -> bool:
        before = len(self.menu_items)
        self.menu_items = [i for i in self.menu_items if i["id"] != item_id]
        return len(self.menu_items) < before

    # ── Order helpers ─────────────────────────────────────────────────────────

    def get_orders(self, user_id: str | None = None, status: str | None = None) -> list[dict]:
        results = self.orders
        if user_id:
            results = [o for o in results if o["user_id"] == user_id]
        if status:
            results = [o for o in results if o["status"] == status]
        return results

    def get_order(self, order_id: str, user_id: str | None = None) -> dict | None:
        return next(
            (o for o in self.orders if o["id"] == order_id and (user_id is None or o["user_id"] == user_id)),
            None,
        )

    def add_order(self, o: dict) -> dict:
        self.orders.append(o)
        return o

    def update_order(self, order_id: str, fields: dict) -> dict | None:
        for o in self.orders:
            if o["id"] == order_id:
                o.update(fields)
                return o
        return None

    def cancel_order(self, order_id: str, user_id: str) -> dict | None:
        o = self.get_order(order_id, user_id)
        if o and o["status"] not in ("delivered", "cancelled"):
            o["status"] = "cancelled"
            return o
        return None


# Module-level singleton — shared across all resolvers
store = MockStore()

