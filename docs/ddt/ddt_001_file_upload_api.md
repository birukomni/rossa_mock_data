# DDT-001: File Upload API

**Version:** 1.0
**Gateway:** REST (`rest-gateway`)
**Date:** 2026-03-25

---

## Overview

File uploads are handled exclusively by the REST gateway via `multipart/form-data`. This document covers the avatar upload endpoint — the only current file upload surface. See [ADR-003](../adr/adr_003_file_uploads_via_rest_gateway.md) for the rationale behind this design.

---

## Endpoint

### Upload Avatar

```
POST /api/:version/files/avatar
```

Atomically validates the file, uploads it to S3, confirms the new avatar with Django, and returns the full updated profile in a single response.

#### Path parameters

| Parameter | Type   | Description                        |
|-----------|--------|------------------------------------|
| `version` | string | API version, e.g. `v1`             |

#### Required headers

| Header          | Value                          | Description                                    |
|-----------------|--------------------------------|------------------------------------------------|
| `Authorization` | `Bearer <access_token>`        | Short-lived JWT access token from OTP verify   |
| `X-Market-ID`   | ISO 3166-1 alpha-2 market code | Market scope, e.g. `ZA`                        |

#### Request body

`Content-Type: multipart/form-data`

| Field  | Type | Required | Description                                   |
|--------|------|----------|-----------------------------------------------|
| `file` | File | Yes      | Image file. Accepted MIME types: `image/jpeg`, `image/png`, `image/webp`. Max size: governed by `MAX_REQUEST_FILE_SIZE` env var (default 10 MB). |

#### Success response — `200 OK`

```json
{
  "success": true,
  "message": "Avatar updated successfully.",
  "data": {
    "id": "01930a1b-1234-7abc-8def-000000000001",
    "accountId": "01930a1b-1234-7abc-8def-000000000000",
    "marketId": "ZA",
    "displayName": "Jane Doe",
    "avatarUrl": "https://my-bucket.s3.us-east-1.amazonaws.com/uploads/avatars/01930a.../uuid.jpg",
    "language": "en",
    "timezone": "Africa/Johannesburg",
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-03-25T12:00:00.000Z"
  },
  "meta": {
    "timestamp": "2026-03-25T12:00:00.000Z"
  }
}
```

#### Error responses

| Status | When |
|--------|------|
| `400 Bad Request` | No file provided, file too large, or unsupported MIME type |
| `401 Unauthorized` | Missing or invalid `Authorization` header |
| `403 Forbidden` | Token present but insufficient scope or market mismatch |

#### Example error — `400 Bad Request` (unsupported type)

```json
{
  "statusCode": 400,
  "message": "File type is not supported. Accepted: JPEG, PNG, WebP.",
  "error": "Bad Request"
}
```

---

## Request flow

```
Client
  │
  │  POST /api/v1/files/avatar
  │  Authorization: Bearer <token>
  │  X-Market-ID: ZA
  │  Content-Type: multipart/form-data
  │  [file field]
  ▼
REST Gateway (FileUploadController)
  │
  ├─ 1. RESTAuthGuard — verifies JWT, sets req.userId
  │
  ├─ 2. FileValidationPipe — validates size and MIME type
  │
  ├─ 3. FileUploadService.uploadAvatar()
  │       │
  │       ├─ 3a. Generates deterministic S3 key:
  │       │       uploads/avatars/{userId}/{uuid}.{ext}
  │       │
  │       ├─ 3b. IStorageService.upload() → S3
  │       │       returns { objectKey, url }
  │       │
  │       └─ 3c. UsersService.confirmAvatar(objectKey, version, authHeader)
  │               PATCH /api/v1/profiles/me/avatar/confirm/ → Django
  │               returns ProfilePayloadDto
  │
  └─ 4. Returns StandardResponse-shaped JSON with ProfilePayloadDto
  │
  ▼
Client — single round trip, updated profile in response
```

---

## Configuration

| Env var                 | Description                                    | Default     |
|-------------------------|------------------------------------------------|-------------|
| `STORAGE_PROVIDER`      | Storage backend: `s3` or `gcs`                | `s3`        |
| `AWS_REGION`            | AWS region for S3                              | —           |
| `AWS_ACCESS_KEY_ID`     | AWS access key                                 | —           |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key                                 | —           |
| `AWS_S3_BUCKET_NAME`    | Target S3 bucket                               | —           |
| `AWS_S3_KEY_PREFIX`     | Key prefix for all uploaded objects            | `uploads/`  |
| `MAX_REQUEST_FILE_SIZE` | Max file size in bytes                         | `10485760`  |

---

## Storage provider plug-in

The `IStorageService` injection token enables provider switching without code changes:

```
STORAGE_PROVIDER=s3   → S3StorageService   (implemented)
STORAGE_PROVIDER=gcs  → GcsStorageService  (stub — throws NotImplementedException)
```

The factory in `FileUploadModule` reads `STORAGE_PROVIDER` at startup and wires the correct implementation. No controller or service code changes are required to switch providers.
