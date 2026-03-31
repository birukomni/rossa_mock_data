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


# Module-level singleton — shared across all resolvers
store = MockStore()
