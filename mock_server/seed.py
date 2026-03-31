"""
Seed data — sourced from DDT example payloads.
Two users: Jane (ke) and John (za).
"""
from __future__ import annotations

# ─── Token → User ID map ────────────────────────────────────────────────────
TOKEN_MAP: dict[str, str] = {
    "mock-token-jane": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "mock-token-john": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
}
DEFAULT_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # Jane is default

MOCK_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.bW9jay1qYW5l.mock-sig"
MOCK_REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiJ9.bW9jay1qYW5lLXJlZnJlc2g.mock-sig"

# ─── Users ───────────────────────────────────────────────────────────────────
SEED_USERS: list[dict] = [
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "email": "jane@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone_number": "+254700000000",
        "is_active": True,
        "email_verified": True,
        "phone_verified": True,
        "market_id": "ke",
        "date_joined": "2025-01-15T08:00:00Z",
        "created_at": "2025-01-15T08:00:00Z",
    },
    {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Smith",
        "phone_number": "+27700000000",
        "is_active": True,
        "email_verified": True,
        "phone_verified": False,
        "market_id": "za",
        "date_joined": "2025-03-01T08:00:00Z",
        "created_at": "2025-03-01T08:00:00Z",
    },
]

# ─── Profiles ────────────────────────────────────────────────────────────────
SEED_PROFILES: list[dict] = [
    {
        "id": "prof-0001-0000-0000-000000000001",
        "account_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "market_id": "ke",
        "display_name": "Jane Doe",
        "avatar_url": "https://cdn.example.com/avatars/jane.jpg",
        "language": "en",
        "timezone": "Africa/Nairobi",
        "created_at": "2026-01-10T08:00:00Z",
        "updated_at": "2026-03-20T14:30:00Z",
    },
    {
        "id": "prof-0002-0000-0000-000000000002",
        "account_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "market_id": "za",
        "display_name": "John Smith",
        "avatar_url": None,
        "language": "en",
        "timezone": "Africa/Johannesburg",
        "created_at": "2026-03-01T08:00:00Z",
        "updated_at": "2026-03-01T08:00:00Z",
    },
]

# ─── Addresses ───────────────────────────────────────────────────────────────
SEED_ADDRESSES: list[dict] = [
    {
        "id": "addr-0001-0000-0000-000000000001",
        "account_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "label": "Home",
        "street": "14 Riverside Drive",
        "suburb": "Westlands",
        "city": "Nairobi",
        "postal_code": "00100",
        "country": "KE",
        "latitude": -1.2671,
        "longitude": 36.8103,
        "is_default": True,
        "deliverable": True,
        "created_at": "2026-01-15T08:00:00Z",
        "updated_at": "2026-02-10T12:00:00Z",
    },
    {
        "id": "addr-0002-0000-0000-000000000002",
        "account_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "label": "Office",
        "street": "The Oval, Ring Road Parklands",
        "suburb": None,
        "city": "Nairobi",
        "postal_code": "00100",
        "country": "KE",
        "latitude": -1.2595,
        "longitude": 36.8065,
        "is_default": False,
        "deliverable": True,
        "created_at": "2026-02-20T09:00:00Z",
        "updated_at": "2026-02-20T09:00:00Z",
    },
]

# ─── Market memberships ───────────────────────────────────────────────────────
SEED_MARKETS: list[dict] = [
    {
        "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "market_id": "ke",
        "status": "active",
        "activated_at": "2026-01-15T08:00:00Z",
    },
    {
        "user_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "market_id": "za",
        "status": "active",
        "activated_at": "2026-03-01T08:00:00Z",
    },
]

# ─── Onboarding checklists ────────────────────────────────────────────────────
SEED_CHECKLISTS: dict[str, dict] = {
    "ke": {
        "market_id": "ke",
        "status": "in_progress",
        "all_required_complete": False,
        "steps": [
            {"step": "phone_verification", "required": True, "completed": True},
            {"step": "id_verification", "required": True, "completed": False},
            {"step": "address_confirmation", "required": False, "completed": False},
        ],
    },
    "za": {
        "market_id": "za",
        "status": "complete",
        "all_required_complete": True,
        "steps": [
            {"step": "phone_verification", "required": True, "completed": True},
            {"step": "id_verification", "required": True, "completed": True},
        ],
    },
    "ng": {
        "market_id": "ng",
        "status": "not_started",
        "all_required_complete": False,
        "steps": [
            {"step": "phone_verification", "required": True, "completed": False},
            {"step": "id_verification", "required": True, "completed": False},
            {"step": "address_confirmation", "required": False, "completed": False},
        ],
    },
}

# ─── Consents ────────────────────────────────────────────────────────────────
SEED_CONSENTS: list[dict] = [
    {
        "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "consent_type": "marketing_email",
        "granted": True,
        "granted_at": "2026-01-15T08:00:00Z",
        "withdrawn_at": None,
    },
    {
        "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "consent_type": "data_analytics",
        "granted": True,
        "granted_at": "2026-01-15T08:00:00Z",
        "withdrawn_at": None,
    },
    {
        "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "consent_type": "third_party_sharing",
        "granted": False,
        "granted_at": None,
        "withdrawn_at": None,
    },
    {
        "user_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "consent_type": "marketing_email",
        "granted": True,
        "granted_at": "2026-03-01T08:00:00Z",
        "withdrawn_at": None,
    },
]
