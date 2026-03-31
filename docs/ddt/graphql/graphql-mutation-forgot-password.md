# Design Doc: Forgot Password (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-23
**Jira Epic/Ticket:** KFC-1

---

## 1. Context & Goal

This mutation initiates a password reset flow for a user who has forgotten their credentials. The client submits an email address and the backend dispatches a reset link or token out-of-band (e.g. via email). The response is deliberately opaque to prevent user enumeration.

**Goal:** Allow a user to trigger a password reset email without requiring them to be authenticated.

---

## 2. Proposed Solution

The gateway accepts a `forgotPassword` mutation, validates that the input is a well-formed email address, and proxies the request to the Django REST password-reset endpoint via `DjangoProxyService`. Django handles the lookup and dispatches the reset email. The gateway returns only a status/message envelope — no user data, no token — regardless of whether the email exists in the system.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. The password reset token and its expiry are managed entirely by Django. No cache read or write occurs for this operation.

---

## 4. API Contracts

### Request Headers

- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing. If omitted, the gateway generates one automatically and returns it in `meta.correlationId`.
- `X-Market-ID`: (Optional) Market scope override (e.g. "ZA", "KE"). Sourced from `input.marketId`.

### Mutation

```graphql
mutation ForgotPassword($input: ForgotPasswordRequest!) {
  forgotPassword(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
  }
}
```

### Input: `ForgotPasswordRequest`

| Field               | Type                           | Required | Validation              | Description                          |
|---------------------|--------------------------------|----------|-------------------------|--------------------------------------|
| `preferredLanguage` | `String`                       | No       | Optional string         | Preferred language for localization  |
| `apiVersion`        | `String`                       | No       | Optional string         | API version to use                   |
| `marketId`          | `String`                       | No       | Optional string         | Optional market scope override       |
| `input`             | `ForgotPasswordRequestPayload` | Yes      | Object                  | The forgot password details          |

#### `input` — `ForgotPasswordRequestPayload`

| Field   | Type     | Required | Validation                    | Description                                    |
|---------|----------|----------|-------------------------------|------------------------------------------------|
| `email` | `String` | Yes      | Valid email format, non-empty | Email address associated with the user account |

### Response: `StandardEmptyResponse`

This mutation returns no payload — only the status/message envelope. This is intentional: returning different responses for known vs unknown emails would leak account existence.

| Field     | Type      | Nullable | Description                                                      |
|-----------|-----------|----------|------------------------------------------------------------------|
| `success` | `Boolean` | No       | Whether the operation succeeded                                  |
| `status`  | `Int`     | No       | The HTTP status code as received from the Django Service         |
| `message` | `String`  | No       | Generic confirmation message — identical whether email exists or not |
| `meta`    | `Object`  | Yes      | Pagination and tracing metadata                                  |

### Example Request Variables

```json
{
  "input": {
    "preferredLanguage": "en",
    "apiVersion": "v1",
    "marketId": "ZA",
    "input": {
      "email": "jane.doe@example.com"
    }
  }
}
```

### Example Success Response (email exists or not — response is identical)

```json
{
  "data": {
    "forgotPassword": {
      "success": true,
      "status": 200,
      "message": "If an account with that email exists, a password reset link has been sent.",
      "meta": null
    }
  }
}
```

### Example Error Response (malformed email — caught at validation layer)

```json
{
  "errors": [
    {
      "message": "email must be an email",
      "extensions": { "success": false }
    }
  ]
}
```

---

## 5. Security & Edge Cases

| Concern | Mitigation |
|---|---|
| **User enumeration** | The response message and status are identical whether or not the email is registered. Never differentiate "email not found" from "email sent". |
| **Reset link abuse** | Rate limiting is enforced at the Django layer; the gateway surfaces the upstream `429` response. Frontend should disable the submit button after the first successful submission. |
| **Email format validation** | `@IsEmail()` is enforced at the gateway input layer — malformed addresses are rejected with a `400` before reaching Django. |
| **Expired reset tokens** | Token expiry is managed by Django. The gateway is not involved in the token redemption step (that is a separate flow). |
| **Transport security** | All traffic must be over HTTPS/TLS to prevent email address interception. |
| **No auth required** | This mutation is intentionally unauthenticated — do not apply `@UseGuards(GraphQLAuthGuard)` to it. |
