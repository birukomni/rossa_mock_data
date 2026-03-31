# Design Doc: Update Profile (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation allows an authenticated user to update their profile — display name, avatar URL, preferred language, and timezone. It is the primary way a client persists personalisation changes.

**Goal:** Allow an authenticated user to modify their own profile fields without affecting other users' data.

---

## 2. Proposed Solution

The gateway receives an `updateProfile` mutation, enforces authentication via `GraphQLAuthGuard`, validates the input fields, and proxies the request to the Django REST profile update endpoint via `DjangoProxyService`. Django applies the changes and returns the updated profile record. The gateway wraps it in the standard response envelope.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All profile data is persisted by Django. No local state is written.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation UpdateProfile($input: UpdateProfileRequest!) {
  updateProfile(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      id
      accountId
      marketId
      displayName
      avatarUrl
      language
      timezone
      createdAt
      updatedAt
    }
  }
}
```

### Input: `UpdateProfileRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |
| `input`      | `UpdateProfilePayloadDto` | Yes | Object | Profile fields to update |

#### `input` — `UpdateProfilePayloadDto`

| Field         | Type     | Required | Validation                  | Description                                        |
|---------------|----------|----------|-----------------------------|-----------------------------------------------------|
| `displayName` | `String` | Yes      | Non-empty, max 100 chars    | User's chosen display name                         |
| `avatarUrl`   | `String` | No       | Valid URL format            | Public URL of the avatar image                     |
| `language`    | `String` | No       | Optional string             | BCP 47 language tag (e.g. `"en"`, `"sw"`)         |
| `timezone`    | `String` | No       | Optional string             | IANA timezone identifier (e.g. `"Africa/Nairobi"`) |

### Response: `UpdateProfileResponse`

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the operation succeeded                  |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |
| `payload` | `Object`  | Yes      | Updated profile; absent on failure               |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload` — `ProfilePayloadDto`

| Field         | Type     | Nullable | Description                                          |
|---------------|----------|----------|------------------------------------------------------|
| `id`          | `String` | No       | UUID of the profile record                           |
| `accountId`   | `String` | No       | UUID of the associated user account                  |
| `marketId`    | `String` | No       | Market the profile belongs to (e.g. `"ke"`)         |
| `displayName` | `String` | No       | Updated display name                                 |
| `avatarUrl`   | `String` | Yes      | Updated avatar URL; `null` if not set                |
| `language`    | `String` | Yes      | Updated BCP 47 language tag; `null` if not set       |
| `timezone`    | `String` | Yes      | Updated IANA timezone identifier; `null` if not set  |
| `createdAt`   | `String` | No       | ISO 8601 timestamp of profile creation               |
| `updatedAt`   | `String` | No       | ISO 8601 timestamp of this update                    |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke",
    "input": {
      "displayName": "Jane Doe",
      "avatarUrl": "https://cdn.example.com/avatars/jane-updated.jpg",
      "language": "sw",
      "timezone": "Africa/Nairobi"
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "updateProfile": {
      "success": true,
      "status": 200,
      "message": "Profile updated successfully.",
      "meta": null,
      "payload": {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "accountId": "01950000-0000-7000-0000-000000000001",
        "marketId": "ke",
        "displayName": "Jane Doe",
        "avatarUrl": "https://cdn.example.com/avatars/jane-updated.jpg",
        "language": "sw",
        "timezone": "Africa/Nairobi",
        "createdAt": "2026-01-10T08:00:00Z",
        "updatedAt": "2026-03-31T10:15:00Z"
      }
    }
  }
}
```

### Example Error Response (displayName too long)

```json
{
  "errors": [
    {
      "message": "displayName must be shorter than or equal to 100 characters",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (invalid avatar URL)

```json
{
  "errors": [
    {
      "message": "avatarUrl must be a URL address",
      "extensions": { "success": false }
    }
  ]
}
```

---

## 5. Security & Edge Cases

| Concern | Mitigation |
|---|---|
| **Unauthenticated access** | `@UseGuards(GraphQLAuthGuard)` is applied — unauthenticated requests are rejected before reaching the resolver. |
| **Cross-user modification** | The profile is always updated by the account ID extracted from the authenticated JWT — a user cannot modify another user's profile. |
| **Avatar URL injection** | `@IsUrl()` validation at the gateway ensures only valid URLs are accepted; rendered clients must treat avatar URLs as untrusted external content. |
| **Display name content** | `displayName` is not sanitised at the gateway layer for HTML/script content — rendering clients must escape this field before display. |
| **Null optional fields** | `avatarUrl`, `language`, and `timezone` are nullable in the response — clients must guard against `null`. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
