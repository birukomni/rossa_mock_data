# Design Doc: Delete Address (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation permanently removes a saved address from the authenticated user's address book. The deletion is immediate and irreversible.

**Goal:** Allow an authenticated user to remove an address they no longer need from their address book.

---

## 2. Proposed Solution

The gateway receives a `deleteAddress` mutation, enforces authentication via `GraphQLAuthGuard`, validates that `id` is present, and proxies the request to the Django REST address deletion endpoint via `DjangoProxyService`. Django verifies ownership and deletes the record. The gateway returns a standard empty response envelope — no payload on success.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All address data is persisted by Django. No local state is written. Any cached result from `myAddresses` should be considered stale after this mutation succeeds.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation DeleteAddress($input: DeleteAddressRequest!) {
  deleteAddress(input: $input) {
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

### Input: `DeleteAddressRequest`

| Field        | Type     | Required | Validation       | Description                                    |
|--------------|----------|----------|------------------|------------------------------------------------|
| `apiVersion` | `String` | No       | Optional string  | API version to use (default `"v1"`)            |
| `marketId`   | `String` | No       | Optional string  | Optional market scope override                 |
| `id`         | `String` | Yes      | Non-empty string | UUID of the address to delete                  |

### Response: `StandardEmptyResponse`

This mutation returns no payload. A successful deletion is indicated by `success: true` and `status: 200` (or `204`).

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the address was successfully deleted     |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "id": "addr-0001-0000-0000-0000-000000000001"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "deleteAddress": {
      "success": true,
      "status": 200,
      "message": "Address deleted successfully.",
      "meta": null
    }
  }
}
```

### Example Error Response (address not found or not owned by user)

```json
{
  "errors": [
    {
      "message": "Address not found.",
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
| **Cross-user deletion** | Django verifies that the address identified by `id` belongs to the authenticated user before deleting. An address belonging to a different user returns `404`, not `403`, to avoid leaking address existence. |
| **Default address deletion** | If the deleted address was the user's default, Django may either unset the default (leaving no default) or promote another address. The client should re-fetch the address list after deletion to reflect the current state. |
| **Irreversibility** | Deletion is permanent. Clients should present a confirmation prompt before calling this mutation. |
| **Cache invalidation** | A successful `deleteAddress` should trigger invalidation of any cached `myAddresses` response for this user. |
| **Invalid UUID** | The gateway does not validate UUID format for `id` — Django returns `404` for an unrecognised value. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
