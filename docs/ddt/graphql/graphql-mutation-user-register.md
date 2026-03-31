# Design Doc: User Registration (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-23
**Jira Epic/Ticket:** KFC-1

---

## 1. Context & Goal

This mutation creates a new user account in the system. It accepts the user's personal details, market assignment, and password pair, proxies the registration to the Django backend, and returns the newly created user profile.

**Goal:** Allow a new visitor to create an account and receive their user profile upon successful registration.

---

## 2. Proposed Solution

The gateway receives a `register` mutation, runs field-level validation (email format, required fields, password match), then forwards the payload to the Django REST registration endpoint via `DjangoProxyService`. Django creates the user record and returns the profile. The gateway wraps this in the standard response envelope. No cache write occurs — user data is always read from Django on subsequent requests.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All user records are persisted by the Django backend. No local state is written.

---

## 4. API Contracts

### Request Headers

- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing. If omitted, the gateway generates one automatically and returns it in `meta.correlationId`.
- `X-Market-ID`: (Optional) Market scope override (e.g. "ZA", "KE"). Sourced from `input.marketId`. Note that `marketId` is required for registration.

### Mutation

```graphql
mutation Register($input: RegisterRequest!) {
  register(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
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
  }
}
```

### Input: `RegisterRequest`

| Field               | Type                         | Required | Validation              | Description                          |
|---------------------|------------------------------|----------|-------------------------|--------------------------------------|
| `preferredLanguage` | `String`                     | No       | Optional string         | Preferred language for localization  |
| `apiVersion`        | `String`                     | No       | Optional string         | API version to use                   |
| `marketId`          | `String`                     | No       | Optional string         | Optional market scope override       |
| `input`             | `RegisterUserRequestPayload` | Yes      | Object                  | The registration details             |

#### `input` — `RegisterUserRequestPayload`

| Field             | Type     | Required | Validation                   | Description                                          |
|-------------------|----------|----------|------------------------------|------------------------------------------------------|
| `email`           | `String` | Yes      | Valid email format, non-empty | Primary identifier and contact address               |
| `firstName`       | `String` | Yes      | Non-empty string             | User's given name                                    |
| `lastName`        | `String` | Yes      | Non-empty string             | User's family name                                   |
| `marketId`        | `String` | Yes      | Non-empty string             | Market/region code (e.g. `"ke"`, `"ng"`)             |
| `phoneNumber`     | `String` | No       | Optional string              | Phone number in international format; defaults to `""` |
| `password`        | `String` | Yes      | Non-empty string             | Desired account password (plain-text; TLS in transit) |
| `passwordConfirm` | `String` | Yes      | Non-empty string             | Must match `password`; validated by Django           |

### Response: `RegisterResponse`

Wraps `AuthnUserDto` inside the standard envelope.

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the operation succeeded                  |
| `status`  | `Int`     | No       | The HTTP status code as received from the Django Service |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Pagination and tracing metadata                  |
| `payload` | object    | Yes      | Present on success; absent on validation failure |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload` — `AuthnUserDto`

| Field           | Type      | Description                                      |
|-----------------|-----------|--------------------------------------------------|
| `id`            | `String`  | UUID of the newly created user account           |
| `email`         | `String`  | Registered email address                         |
| `firstName`     | `String`  | Given name                                       |
| `lastName`      | `String`  | Family name                                      |
| `phoneNumber`   | `String`  | Registered phone number (may be empty string)    |
| `isActive`      | `Boolean` | Typically `true` immediately after registration  |
| `emailVerified` | `Boolean` | `false` until the user verifies their email      |
| `phoneVerified` | `Boolean` | `false` until the user verifies their phone      |
| `marketId`      | `String`  | Market/region the user was registered under      |
| `dateJoined`    | `String`  | ISO 8601 timestamp of account creation           |
| `createdAt`     | `String`  | ISO 8601 timestamp of record creation            |

### Example Request Variables

```json
{
  "input": {
    "preferredLanguage": "en",
    "apiVersion": "v1",
    "marketId": "ke",
    "input": {
      "email": "jane.doe@example.com",
      "firstName": "Jane",
      "lastName": "Doe",
      "marketId": "ke",
      "phoneNumber": "+254700000000",
      "password": "S3cur3P@ssword!",
      "passwordConfirm": "S3cur3P@ssword!"
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "register": {
      "success": true,
      "status": 201,
      "message": "Registration successful.",
      "meta": null,
      "payload": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "email": "jane.doe@example.com",
        "firstName": "Jane",
        "lastName": "Doe",
        "phoneNumber": "+254700000000",
        "isActive": true,
        "emailVerified": false,
        "phoneVerified": false,
        "marketId": "ke",
        "dateJoined": "2026-03-23T10:00:00Z",
        "createdAt": "2026-03-23T10:00:00Z"
      }
    }
  }
}
```

### Example Error Response (email already in use)

```json
{
  "errors": [
    {
      "message": "A user with this email already exists.",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (password mismatch)

```json
{
  "errors": [
    {
      "message": "Passwords do not match.",
      "extensions": { "success": false }
    }
  ]
}
```

---

## 5. Security & Edge Cases

| Concern | Mitigation |
|---|---|
| **Duplicate email** | Django enforces uniqueness at the database level; the gateway surfaces the `409` upstream error. |
| **Password mismatch** | `passwordConfirm` is validated by Django; a `400` is returned and surfaced through the error envelope. |
| **Password exposure in logs** | The `password` and `passwordConfirm` fields must never be logged. |
| **Invalid `marketId`** | Django validates that the supplied `marketId` references an existing market; an invalid value returns `400`. |
| **Email verification** | `emailVerified` will be `false` post-registration. Frontend should prompt the user to verify their email before granting full access. |
| **Transport security** | All registration traffic must be over HTTPS/TLS. |
| **`phoneNumber` format** | The field is optional and has no regex validation at the gateway level; format enforcement is Django's responsibility. |
