# Design Doc: Withdraw Consent (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation withdraws a specific consent type for the authenticated user. It allows a user to revoke a previously granted consent (e.g. opting out of marketing emails). Withdrawing a required consent may restrict access to platform features.

**Goal:** Allow an authenticated user to revoke a specific consent by its type identifier.

---

## 2. Proposed Solution

The gateway receives a `withdrawConsent` mutation, enforces authentication via `GraphQLAuthGuard`, validates that `consentType` is present and non-empty, and proxies the request to the Django REST consent withdrawal endpoint via `DjangoProxyService`. Django updates the consent record for the authenticated user. The gateway returns a standard empty response envelope — no payload on success.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All consent data is persisted by Django. No local state is written.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation WithdrawConsent($input: WithdrawConsentRequest!) {
  withdrawConsent(input: $input) {
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

### Input: `WithdrawConsentRequest`

| Field         | Type     | Required | Validation       | Description                                                         |
|---------------|----------|----------|------------------|---------------------------------------------------------------------|
| `apiVersion`  | `String` | No       | Optional string  | API version to use (default `"v1"`)                                 |
| `marketId`    | `String` | No       | Optional string  | Optional market scope override                                      |
| `consentType` | `String` | Yes      | Non-empty string | Consent type identifier to withdraw (e.g. `"marketing_email"`)     |

### Response: `StandardEmptyResponse`

This mutation returns no payload. A successful withdrawal is indicated by `success: true`.

| Field     | Type      | Nullable | Description                                       |
|-----------|-----------|----------|---------------------------------------------------|
| `success` | `Boolean` | No       | Whether the consent was successfully withdrawn    |
| `status`  | `Int`     | No       | HTTP status code from the Django service          |
| `message` | `String`  | No       | Human-readable result message                     |
| `meta`    | `Object`  | Yes      | Tracing metadata                                  |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke",
    "consentType": "marketing_email"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "withdrawConsent": {
      "success": true,
      "status": 200,
      "message": "Consent withdrawn successfully.",
      "meta": null
    }
  }
}
```

### Example Error Response (consent type not found for this user)

```json
{
  "errors": [
    {
      "message": "Consent record not found.",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (empty consentType)

```json
{
  "errors": [
    {
      "message": "consentType should not be empty",
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
| **Cross-user withdrawal** | The consent is always withdrawn for the account identified by the JWT — a user cannot revoke another user's consent. |
| **Required consent withdrawal** | Withdrawing a required consent (`required: true`) may restrict the user's access to the platform. Clients should warn the user before calling this mutation for required consent types. Enforcement of access restrictions is the client's and Django's responsibility. |
| **Non-existent consent type** | If the user has no recorded consent for the given `consentType`, Django returns an error. The gateway surfaces this upstream error. |
| **Idempotency** | Withdrawing an already-withdrawn consent is Django's responsibility to handle gracefully. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
