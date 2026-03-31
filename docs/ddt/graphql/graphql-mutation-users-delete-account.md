# Design Doc: Delete Account (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation initiates account deletion for the authenticated user. It does not destroy the account immediately — it schedules it for deletion after a grace period, giving the user a window to cancel. The response confirms the scheduled deletion timestamp.

**Goal:** Allow an authenticated user to request deletion of their own account in compliance with data retention and right-to-erasure requirements.

---

## 2. Proposed Solution

The gateway receives a `deleteAccount` mutation, enforces authentication via `GraphQLAuthGuard`, and proxies the request to the Django REST account deletion endpoint via `DjangoProxyService`. Django marks the account status as `pending_deletion` and records the scheduled deletion timestamp. The gateway returns the confirmation envelope. No additional input beyond the authenticated identity is required — the user is identified by the JWT.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. Account status and deletion scheduling are managed entirely by Django.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation DeleteAccount($input: RequestAccountDeletionRequest!) {
  deleteAccount(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      id
      status
      deletionScheduledAt
    }
  }
}
```

### Input: `RequestAccountDeletionRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |

No additional input fields are required. The authenticated user's identity is derived from the JWT.

### Response: `RequestAccountDeletionResponse`

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the deletion was successfully scheduled  |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |
| `payload` | `Object`  | Yes      | Present on success; absent on failure            |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload` — `AccountDeletionPayloadDto`

| Field                  | Type     | Description                                              |
|------------------------|----------|----------------------------------------------------------|
| `id`                   | `String` | UUID of the account scheduled for deletion               |
| `status`               | `String` | Account status after scheduling (e.g. `"pending_deletion"`) |
| `deletionScheduledAt`  | `String` | ISO 8601 timestamp when the deletion will be executed    |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "deleteAccount": {
      "success": true,
      "status": 200,
      "message": "Account deletion scheduled successfully.",
      "meta": null,
      "payload": {
        "id": "01950000-0000-7000-0000-000000000001",
        "status": "pending_deletion",
        "deletionScheduledAt": "2026-04-14T10:00:00Z"
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

### Example Error Response (already pending deletion)

```json
{
  "errors": [
    {
      "message": "Account is already scheduled for deletion.",
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
| **Cross-user deletion** | The account deleted is always the one identified by the authenticated JWT — a user cannot schedule deletion of another user's account. |
| **Irreversibility** | Deletion is scheduled, not immediate, giving a grace period for cancellation. The grace period duration is defined by Django policy. Clients should present a prominent warning before calling this mutation. |
| **Re-submission** | Django returns an error if the account is already in `pending_deletion` state. The gateway surfaces this upstream error. |
| **Post-deletion token use** | Clients should invalidate local tokens immediately after a successful response and redirect the user to a sign-out flow. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
