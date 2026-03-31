# Design Doc: My Profile (GraphQL Query)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This query returns the authenticated user's profile record — their display name, avatar, language preference, and timezone. It is the primary way a client fetches personalisation data after sign-in.

**Goal:** Allow an authenticated user to retrieve their own profile without exposing other users' data.

---

## 2. Proposed Solution

The gateway receives a `myProfile` query, enforces authentication via `GraphQLAuthGuard`, extracts the user identity from the JWT, and proxies the request to the Django REST profile endpoint via `DjangoProxyService`. Django looks up the profile by the authenticated user's account ID and returns the record. The gateway wraps it in the standard response envelope. No cache layer is applied to this query — profile data is always read fresh.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All profile data is persisted by Django. No local state is written.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Query

```graphql
query MyProfile($input: GetMyProfileRequest!) {
  myProfile(input: $input) {
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

### Input: `GetMyProfileRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |

### Response: `GetMyProfileResponse`

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the operation succeeded                  |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |
| `payload` | `Object`  | Yes      | Present on success; absent on auth failure       |
| `count`   | `Int`     | Yes      | Not used by this query; always `null`            |

#### `payload` — `ProfilePayloadDto`

| Field         | Type     | Nullable | Description                                      |
|---------------|----------|----------|--------------------------------------------------|
| `id`          | `String` | No       | UUID of the profile record                       |
| `accountId`   | `String` | No       | UUID of the associated user account              |
| `marketId`    | `String` | No       | Market the profile belongs to (e.g. `"ke"`)     |
| `displayName` | `String` | No       | User's chosen display name                       |
| `avatarUrl`   | `String` | Yes      | Public URL of the avatar image                   |
| `language`    | `String` | Yes      | BCP 47 language tag (e.g. `"en"`, `"sw"`)       |
| `timezone`    | `String` | Yes      | IANA timezone identifier (e.g. `"Africa/Nairobi"`) |
| `createdAt`   | `String` | No       | ISO 8601 timestamp of profile creation           |
| `updatedAt`   | `String` | No       | ISO 8601 timestamp of last profile update        |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "myProfile": {
      "success": true,
      "status": 200,
      "message": "Profile retrieved successfully.",
      "meta": null,
      "payload": {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "accountId": "01950000-0000-7000-0000-000000000001",
        "marketId": "ke",
        "displayName": "Jane Doe",
        "avatarUrl": "https://cdn.example.com/avatars/jane.jpg",
        "language": "en",
        "timezone": "Africa/Nairobi",
        "createdAt": "2026-01-10T08:00:00Z",
        "updatedAt": "2026-03-20T14:30:00Z"
      }
    }
  }
}
```

### Example Error Response (unauthenticated)

```json
{
  "errors": [
    {
      "message": "Unauthorized",
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
| **Cross-user access** | The profile is always fetched by the account ID extracted from the authenticated JWT — a user cannot request another user's profile via this query. |
| **Null optional fields** | `avatarUrl`, `language`, and `timezone` are nullable — clients must guard against `null` before rendering. |
| **Stale data** | No cache is applied to this query. Data is always read fresh from Django on each request. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
