"""
REST file upload endpoint — POST /api/{version}/files/avatar
DDT-001: File Upload API
"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from mock_server.auth import get_user_id
from mock_server.store import store
from mock_server.utils import utc_now

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/api/{version}/files/avatar")
async def upload_avatar(version: str, request: Request, file: UploadFile = File(...)):
    # 1. Auth check
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2. MIME type validation
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="File type is not supported. Accepted: JPEG, PNG, WebP.",
        )

    # 3. Size validation (read full content to check size)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds the maximum allowed size of 10 MB.",
        )

    # 4. Generate a mock S3 URL
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    mock_url = f"https://mock-bucket.s3.amazonaws.com/uploads/avatars/{user_id}/{uuid.uuid4()}.{ext}"

    # 5. Update profile avatar in store
    now = utc_now()
    profile = store.update_profile(user_id, {"avatar_url": mock_url, "updated_at": now})
    if not profile:
        # Fallback: return mock profile data even if user not in store
        profile = {
            "id": str(uuid.uuid4()),
            "account_id": user_id,
            "market_id": "ke",
            "display_name": "Mock User",
            "avatar_url": mock_url,
            "language": "en",
            "timezone": "Africa/Nairobi",
            "created_at": now,
            "updated_at": now,
        }

    # 6. Return StandardResponse shape (as per DDT-001)
    return {
        "success": True,
        "message": "Avatar updated successfully.",
        "data": {
            "id": profile["id"],
            "accountId": profile["account_id"],
            "marketId": profile["market_id"],
            "displayName": profile["display_name"],
            "avatarUrl": profile["avatar_url"],
            "language": profile.get("language"),
            "timezone": profile.get("timezone"),
            "createdAt": profile["created_at"],
            "updatedAt": profile["updated_at"],
        },
        "meta": {"timestamp": now},
    }
