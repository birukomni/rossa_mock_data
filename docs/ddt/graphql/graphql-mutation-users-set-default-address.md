# Design Doc: Set Default Address (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation marks one of the authenticated user's saved addresses as their default delivery address. Only one address can be the default at a time — Django demotes any previously default address automatically.

**Goal:** Allow an authenticated user to designate a preferred delivery address from their address book.

---

## 2. Proposed Solution

The gateway receives a `setDefaultAddress` mutation, enforces authentication via `GraphQLAuthGuard`, validates that `id` is present, and proxies the request to the Django REST set-default address endpoint via `DjangoProxyService`. Django verifies that the address belongs to the authenticated user, updates the default flag, and returns a confirmation. The gateway wraps it in the standard response envelope.

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
mutation SetDefaultAddress($input: SetDefaultAddressRequest!) {
  setDefaultAddress(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      id
      isDefault
    }
  }
}
```

### Input: `SetDefaultAddressRequest`

| Field        | Type     | Required | Validation      | Description                                    |
|--------------|----------|----------|-----------------|------------------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)            |
| `marketId`   | `String` | No       | Optional string | Optional market scope override                 |
| `id`         | `String` | Yes      | Non-empty string | UUID of the address to set as default          |

### Response: `SetDefaultAddressResponse`

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the default was successfully updated     |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |
| `payload` | `Object`  | Yes      | Present on success; absent on failure            |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload` — `SetDefaultAddressResponsePayloadDto`

| Field       | Type      | Description                                      |
|-------------|-----------|--------------------------------------------------|
| `id`        | `String`  | UUID of the address that is now the default      |
| `isDefault` | `Boolean` | Always `true` on success                         |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "id": "addr-0002-0000-0000-0000-000000000002"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "setDefaultAddress": {
      "success": true,
      "status": 200,
      "message": "Default address updated successfully.",
      "meta": null,
      "payload": {
        "id": "addr-0002-0000-0000-0000-000000000002",
        "isDefault": true
      }
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
| **Cross-user modification** | Django verifies that the address identified by `id` belongs to the authenticated user before updating the default flag. An address belonging to a different user returns `404`, not `403`, to avoid leaking address existence. |
| **Previous default demotion** | Django automatically unsets `isDefault` on the previously default address when a new one is set. The gateway does not need to make a separate call. |
| **Cache invalidation** | A successful `setDefaultAddress` should trigger invalidation of any cached `myAddresses` response for this user. |
| **Invalid UUID** | The gateway does not validate UUID format for `id` — Django returns `404` for an unrecognised value. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
