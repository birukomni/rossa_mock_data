# Design Doc: User Login (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-23
**Jira Epic/Ticket:** KFC-1

---

## 1. Context & Goal

This mutation authenticates an existing user using their login identifier and password. On success, it returns a JWT access token, refresh token, and a snapshot of the authenticated user's profile — everything the client needs to bootstrap an authenticated session.

**Goal:** Allow a registered user to sign in and receive auth tokens for subsequent authorised requests.

---

## 2. Proposed Solution

The gateway accepts a `login` mutation, validates the input, and proxies the credentials to the Django REST backend via `DjangoProxyService`. Django performs credential verification and issues the JWT pair. The gateway returns the tokens and user profile directly to the client with no local state written.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All user and session data is persisted by the Django backend. No cache write occurs on login — tokens are ephemeral client-side state.

---

## 4. API Contracts

### Request Headers

- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing. If omitted, the gateway generates one automatically and returns it in `meta.correlationId`.
- `X-Market-ID`: (Optional) Market scope override (e.g. "ZA", "KE"). Sourced from `input.marketId`.

### Mutation

```graphql
mutation Login($input: LoginRequest!) {
  login(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      user {
        id
        email
        firstName
        lastName
        phoneNumber
        isActive
        emailVerified
        phoneVerified
        marketId
        dateJoined
        createdAt
      }
      tokens {
        accessToken
        refreshToken
        tokenType
        expiresIn
        scope
      }
    }
  }
}
```

### Input: `LoginRequest`

| Field               | Type                  | Required | Validation              | Description                          |
|---------------------|-----------------------|----------|-------------------------|--------------------------------------|
| `preferredLanguage` | `String`              | No       | Optional string         | Preferred language for localization  |
| `apiVersion`        | `String`              | No       | Optional string         | API version to use                   |
| `marketId`          | `String`              | No       | Optional string         | Optional market scope override       |
| `input`             | `LoginRequestPayload` | Yes      | Object                  | The login credentials                |

#### `input` — `LoginRequestPayload`

| Field      | Type     | Required | Validation              | Description                          |
|------------|----------|----------|-------------------------|--------------------------------------|
| `login`    | `String` | Yes      | Non-empty string        | Username or email used to identify the account |
| `password` | `String` | Yes      | Non-empty string        | Account password (plain-text; TLS in transit) |

### Response: `LoginResponse`

Wraps `LoginPayloadDto` inside the standard envelope.

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the operation succeeded                  |
| `status`  | `Int`     | No       | The HTTP status code as received from the Django Service |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Pagination and tracing metadata                  |
| `payload` | object    | Yes      | Present on success; absent on auth failure       |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload.user` — `AuthnUserDto`

| Field           | Type      | Description                                      |
|-----------------|-----------|--------------------------------------------------|
| `id`            | `String`  | UUID of the user account                         |
| `email`         | `String`  | Registered email address                         |
| `firstName`     | `String`  | Given name                                       |
| `lastName`      | `String`  | Family name                                      |
| `phoneNumber`   | `String`  | Registered phone number (may be empty string)    |
| `isActive`      | `Boolean` | Whether the account is active                    |
| `emailVerified` | `Boolean` | Whether the email address has been verified      |
| `phoneVerified` | `Boolean` | Whether the phone number has been verified       |
| `marketId`      | `String`  | Market/region the user belongs to                |
| `dateJoined`    | `String`  | ISO 8601 timestamp of account creation           |
| `createdAt`     | `String`  | ISO 8601 timestamp of record creation            |

#### `payload.tokens` — `AuthTokensDto`

| Field          | Type     | Description                                      |
|----------------|----------|--------------------------------------------------|
| `accessToken`  | `String` | Short-lived JWT for authorising requests         |
| `refreshToken` | `String` | Long-lived token for obtaining new access tokens |
| `tokenType`    | `String` | Token scheme — typically `"Bearer"`              |
| `expiresIn`    | `Int`    | Access token TTL in seconds                      |
| `scope`        | `String` | OAuth-style scope string                         |

### Example Request Variables

```json
{
  "input": {
    "preferredLanguage": "en",
    "apiVersion": "v1",
    "marketId": "ZA",
    "input": {
      "login": "user@example.com",
      "password": "S3cur3P@ssword!"
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "login": {
      "success": true,
      "status": 200,
      "message": "Login successful.",
      "meta": null,
      "payload": {
        "user": {
          "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "email": "user@example.com",
          "firstName": "Jane",
          "lastName": "Doe",
          "phoneNumber": "+254700000000",
          "isActive": true,
          "emailVerified": true,
          "phoneVerified": false,
          "marketId": "ke",
          "dateJoined": "2025-01-15T08:00:00Z",
          "createdAt": "2025-01-15T08:00:00Z"
        },
        "tokens": {
          "accessToken": "<jwt>",
          "refreshToken": "<jwt>",
          "tokenType": "Bearer",
          "expiresIn": 3600,
          "scope": "read write"
        }
      }
    }
  }
}
```

### Example Error Response (invalid credentials)

```json
{
  "errors": [
    {
      "message": "Invalid credentials.",
      "extensions": { "success": false }
    }
  ]
}
```

---

## 5. Security & Edge Cases

| Concern | Mitigation |
|---|---|
| **Credential brute-force** | Rate limiting is enforced at the Django layer; the gateway passes through the upstream `429` response. |
| **Password exposure in logs** | The `password` field must never be logged. The logging interceptor operates at response level only. |
| **Token storage** | Clients must store `accessToken` and `refreshToken` in memory or a secure storage mechanism — never in `localStorage`. |
| **Inactive accounts** | Django returns a non-`200` status for inactive accounts; the gateway surfaces this via the error envelope. |
| **Transport security** | All traffic must be over HTTPS/TLS. Plaintext connections are rejected at the infrastructure level. |
| **Empty `payload` on error** | Clients must guard against `payload` being `null` — it is nullable in the schema and will be absent on auth failure. |
