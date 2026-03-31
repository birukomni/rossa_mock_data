# Design Doc: Activate Market (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation activates a new market for the authenticated user's account, creating a market membership record. A user must have an active membership in a market before they can transact within it. This is typically called during market onboarding.

**Goal:** Allow an authenticated user to enrol their account in a new market.

---

## 2. Proposed Solution

The gateway receives an `activateMarket` mutation, enforces authentication via `GraphQLAuthGuard`, validates the `marketId` input, and proxies the request to the Django REST market membership activation endpoint via `DjangoProxyService`. Django creates the membership record and returns the new market membership details. The gateway wraps it in the standard response envelope.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. Market membership records are persisted entirely by Django. No local state is written.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation ActivateMarket($input: ActivateMarketRequest!) {
  activateMarket(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      id
      marketId
      status
      createdAt
    }
  }
}
```

### Input: `ActivateMarketRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |
| `input`      | `ActivateMarketPayloadDto` | Yes | Object | Market to activate |

#### `input` — `ActivateMarketPayloadDto`

| Field      | Type     | Required | Validation       | Description                                    |
|------------|----------|----------|------------------|------------------------------------------------|
| `marketId` | `String` | Yes      | Non-empty string | Market identifier to activate (e.g. `"ke"`, `"za"`) |

### Response: `ActivateMarketResponse`

| Field     | Type      | Nullable | Description                                       |
|-----------|-----------|----------|---------------------------------------------------|
| `success` | `Boolean` | No       | Whether the market was successfully activated     |
| `status`  | `Int`     | No       | HTTP status code from the Django service          |
| `message` | `String`  | No       | Human-readable result message                     |
| `meta`    | `Object`  | Yes      | Tracing metadata                                  |
| `payload` | `Object`  | Yes      | New market membership record; absent on failure   |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`          |

#### `payload` — `MarketMembershipPayloadDto`

| Field       | Type     | Description                                              |
|-------------|----------|----------------------------------------------------------|
| `id`        | `String` | UUID of the newly created market membership record       |
| `marketId`  | `String` | Market identifier for this membership                    |
| `status`    | `String` | Initial membership status (e.g. `"active"`)             |
| `createdAt` | `String` | ISO 8601 timestamp of membership creation                |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "input": {
      "marketId": "ng"
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "activateMarket": {
      "success": true,
      "status": 201,
      "message": "Market activated successfully.",
      "meta": null,
      "payload": {
        "id": "mem-0001-0000-0000-0000-000000000001",
        "marketId": "ng",
        "status": "active",
        "createdAt": "2026-03-31T10:00:00Z"
      }
    }
  }
}
```

### Example Error Response (market already active)

```json
{
  "errors": [
    {
      "message": "User is already enrolled in this market.",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (invalid market ID)

```json
{
  "errors": [
    {
      "message": "Market not found.",
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
| **Cross-user activation** | The membership is always created for the account identified by the JWT — a user cannot activate a market on behalf of another user. |
| **Duplicate activation** | Django enforces uniqueness on (account, market) membership and returns an error if the user is already enrolled. |
| **Invalid market** | Django validates that `marketId` corresponds to a configured market. An unrecognised market ID returns `404` or `400`. |
| **Onboarding checklist** | After activating a market, clients should call `marketOnboardingChecklist` to determine what steps are required before the user can transact in the new market. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
