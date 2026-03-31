# Design Doc: Verify OTP (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation verifies a one-time password submitted by the user. On success it returns a short-lived JWT access token and sets a long-lived refresh token as an HttpOnly cookie. It is the second and final step of the OTP authentication flow.

**Goal:** Allow a user to complete OTP-based sign-in and receive an authenticated session.

---

## 2. Proposed Solution

The gateway accepts a `verifyOtp` mutation, validates the `identifier`, `identifierType`, and `otp` (must be exactly 6 numeric digits), then proxies the request to the Django REST OTP verification endpoint via `DjangoProxyService`. On success Django validates the OTP against its stored value, issues tokens, and the gateway returns the access token in the response body while setting the refresh token as an HttpOnly `Set-Cookie` header — it is never surfaced in the GraphQL payload. The `refreshTokenSet` boolean in the payload confirms the cookie was written.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. OTP state, token generation, and session management are handled entirely by Django. No cache read or write occurs for this operation.

---

## 4. API Contracts

### Request Headers

- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing. If omitted, the gateway generates one automatically and returns it in `meta.correlationId`.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation VerifyOtp($input: OtpVerifyRequest!) {
  verifyOtp(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      accessToken
      tokenType
      expiresIn
      refreshTokenSet
      mfaRequired
      user {
        id
        phone
        email
        marketId
        status
        createdAt
        updatedAt
      }
    }
  }
}
```

### Input: `OtpVerifyRequest`

| Field        | Type     | Required | Validation      | Description                              |
|--------------|----------|----------|-----------------|------------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)      |
| `marketId`   | `String` | No       | Optional string | Optional market scope override           |
| `input`      | `OtpVerifyPayloadDto` | Yes | Object | Identifier, type, and OTP code |

#### `input` — `OtpVerifyPayloadDto`

| Field            | Type             | Required | Validation                          | Description                                        |
|------------------|------------------|----------|-------------------------------------|----------------------------------------------------|
| `identifier`     | `String`         | Yes      | Non-empty string                    | Phone number in E.164 format or email address      |
| `identifierType` | `IdentifierType` | Yes      | Enum: `phone` \| `email`            | Whether the identifier is a phone number or email  |
| `otp`            | `String`         | Yes      | Exactly 6 numeric digits (`^\d{6}$`) | The OTP code received out-of-band                 |

### Response: `OtpVerifyResponse`

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether OTP verification succeeded               |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |
| `payload` | `Object`  | Yes      | Present on success; absent on verification failure |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload` — `OtpVerifyResponsePayloadDto`

| Field             | Type              | Description                                                                 |
|-------------------|-------------------|-----------------------------------------------------------------------------|
| `accessToken`     | `String`          | Short-lived JWT for authorising subsequent requests                         |
| `tokenType`       | `String`          | Token scheme — always `"Bearer"`                                            |
| `expiresIn`       | `Int`             | Access token TTL in seconds                                                 |
| `refreshTokenSet` | `Boolean`         | Whether the HttpOnly refresh token cookie was set on the HTTP response      |
| `mfaRequired`     | `Boolean`         | Whether a second MFA factor is still required to complete sign-in           |
| `user`            | `CustomerPayloadDto` | Authenticated user identity snapshot                                     |

#### `payload.user` — `CustomerPayloadDto`

| Field       | Type                    | Nullable | Description                                             |
|-------------|-------------------------|----------|---------------------------------------------------------|
| `id`        | `String`                | No       | UUID v7 account identifier                              |
| `phone`     | `String`                | Yes      | Verified phone number in E.164 format                   |
| `email`     | `String`                | Yes      | Verified email address                                  |
| `marketId`  | `String`                | No       | Market the account belongs to (e.g. `"ZA"`)            |
| `status`    | `CustomerAccountStatus` | No       | Current lifecycle status of the account                 |
| `createdAt` | `String`                | Yes      | ISO 8601 timestamp when the account was created         |
| `updatedAt` | `String`                | Yes      | ISO 8601 timestamp of the last account update           |

**`CustomerAccountStatus` enum values:** `pending_verification` | `active` | `suspended` | `pending_deletion`

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke",
    "input": {
      "identifier": "+254700000000",
      "identifierType": "phone",
      "otp": "482916"
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "verifyOtp": {
      "success": true,
      "status": 200,
      "message": "OTP verified successfully.",
      "meta": null,
      "payload": {
        "accessToken": "<jwt>",
        "tokenType": "Bearer",
        "expiresIn": 3600,
        "refreshTokenSet": true,
        "mfaRequired": false,
        "user": {
          "id": "01950000-0000-7000-0000-000000000001",
          "phone": "+254700000000",
          "email": null,
          "marketId": "ke",
          "status": "active",
          "createdAt": "2026-01-10T08:00:00Z",
          "updatedAt": "2026-03-31T09:00:00Z"
        }
      }
    }
  }
}
```

### Example Error Response (invalid or expired OTP)

```json
{
  "errors": [
    {
      "message": "Invalid or expired OTP.",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (OTP format validation failure)

```json
{
  "errors": [
    {
      "message": "otp must match /^\\d{6}$/ regular expression",
      "extensions": { "success": false }
    }
  ]
}
```

---

## 5. Security & Edge Cases

| Concern | Mitigation |
|---|---|
| **Refresh token exposure** | The refresh token is set as an HttpOnly cookie by the gateway — it is never present in the GraphQL response body. `refreshTokenSet: true` is the only client-side signal that the cookie was written. |
| **OTP brute-force** | Django enforces attempt limits and TTL expiry. The gateway surfaces upstream `429` and `400` errors. |
| **Expired OTP** | Django tracks OTP expiry; an expired code returns a non-`200` status. Clients must guide the user to request a new OTP. |
| **MFA continuation** | When `mfaRequired: true`, the `accessToken` in the response is a limited-scope token sufficient only to complete the MFA step — not a full session token. |
| **OTP length enforcement** | The `otp` field is validated with `@Length(6, 6)` and `@Matches(/^\d{6}$/)` at the gateway layer — non-numeric or wrong-length values are rejected before reaching Django. |
| **Unauthenticated access** | This mutation is intentionally unauthenticated — do not apply `@UseGuards(GraphQLAuthGuard)` to it. |
| **Transport security** | All traffic must be over HTTPS/TLS. The refresh token cookie must be `Secure` to prevent transmission over plaintext connections. |
