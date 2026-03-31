# Design Doc: Update Market Membership Status (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation updates the status of the authenticated user's membership in a given market. It is used to transition a market membership through its lifecycle states (e.g. suspending, reactivating, or closing a membership).

**Goal:** Allow an authenticated user to update their own market membership status for a specific market.

---

## 2. Proposed Solution

The gateway receives an `updateMarketMembershipStatus` mutation, enforces authentication via `GraphQLAuthGuard`, validates the `marketId` and `status` fields, and proxies the request to the Django REST market membership update endpoint via `DjangoProxyService`. Django verifies the membership belongs to the authenticated user, validates the requested status transition, and applies the update. The gateway returns a standard empty response envelope — no payload on success.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. Market membership state is managed entirely by Django. No local state is written.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation UpdateMarketMembershipStatus($input: UpdateMarketMembershipStatusRequest!) {
  updateMarketMembershipStatus(input: $input) {
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

### Input: `UpdateMarketMembershipStatusRequest`

| Field        | Type     | Required | Validation       | Description                                                       |
|--------------|----------|----------|------------------|-------------------------------------------------------------------|
| `apiVersion` | `String` | No       | Optional string  | API version to use (default `"v1"`)                               |
| `marketId`   | `String` | Yes      | Non-empty string | Market whose membership status to update (e.g. `"ke"`, `"ng"`)  |
| `status`     | `String` | Yes      | Non-empty string | Target status (valid values enforced by Django)                   |

### Response: `StandardEmptyResponse`

This mutation returns no payload. A successful update is indicated by `success: true`.

| Field     | Type      | Nullable | Description                                           |
|-----------|-----------|----------|-------------------------------------------------------|
| `success` | `Boolean` | No       | Whether the membership status was successfully updated |
| `status`  | `Int`     | No       | HTTP status code from the Django service              |
| `message` | `String`  | No       | Human-readable result message                         |
| `meta`    | `Object`  | Yes      | Tracing metadata                                      |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ng",
    "status": "suspended"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "updateMarketMembershipStatus": {
      "success": true,
      "status": 200,
      "message": "Market membership status updated successfully.",
      "meta": null
    }
  }
}
```

### Example Error Response (invalid status transition)

```json
{
  "errors": [
    {
      "message": "Invalid status transition for this membership.",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (membership not found)

```json
{
  "errors": [
    {
      "message": "Market membership not found.",
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
| **Cross-user modification** | The membership is always updated for the account identified by the JWT — a user cannot modify another user's market membership. |
| **Invalid status values** | The `status` field is a free string at the gateway layer — valid status values and transition rules are enforced entirely by Django. An invalid value returns a `400` or `422` upstream error. |
| **Invalid market** | If the user has no membership in the given `marketId`, Django returns `404`. Clients should verify the user has an active membership before calling this mutation. |
| **Status transition rules** | Not all status transitions are valid (e.g. a `pending_deletion` membership may not be reactivated). Django enforces these rules and returns an error for invalid transitions. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
