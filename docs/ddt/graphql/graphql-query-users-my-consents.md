# Design Doc: My Consents (GraphQL Query)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This query returns all consent records for the authenticated user — indicating which consent types have been granted, their versions, and whether they are required. It is the primary way a client populates a consent management UI.

**Goal:** Allow an authenticated user to view the current state of all consents recorded against their account.

---

## 2. Proposed Solution

The gateway receives a `myConsents` query, enforces authentication via `GraphQLAuthGuard`, and proxies the request to the Django REST consents endpoint via `DjangoProxyService`. Django returns all consent records scoped to the authenticated user's account. The gateway wraps results in the standard list response envelope.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All consent data is persisted by Django. No local state is written.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Query

```graphql
query MyConsents($input: GetMyConsentsRequest!) {
  myConsents(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      consentType
      version
      granted
      grantedAt
      required
    }
  }
}
```

### Input: `GetMyConsentsRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |

### Response: `GetMyConsentsResponse`

| Field     | Type                 | Nullable | Description                                      |
|-----------|----------------------|----------|--------------------------------------------------|
| `success` | `Boolean`            | No       | Whether the operation succeeded                  |
| `status`  | `Int`                | No       | HTTP status code from the Django service         |
| `message` | `String`             | No       | Human-readable result message                    |
| `meta`    | `Object`             | Yes      | Tracing metadata                                 |
| `payload` | `[ConsentPayloadDto]` | No      | Array of consent records (empty array if none)   |

#### `payload[]` — `ConsentPayloadDto`

| Field         | Type      | Description                                                          |
|---------------|-----------|----------------------------------------------------------------------|
| `consentType` | `String`  | Consent type identifier (e.g. `"terms_of_service"`, `"marketing"`) |
| `version`     | `String`  | Version of the consent document the user responded to               |
| `granted`     | `Boolean` | Whether the user granted (`true`) or declined (`false`) this consent |
| `grantedAt`   | `String`  | ISO 8601 timestamp when the consent decision was recorded           |
| `required`    | `Boolean` | Whether this consent is mandatory for platform access               |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "myConsents": {
      "success": true,
      "status": 200,
      "message": "Consents retrieved successfully.",
      "meta": null,
      "payload": [
        {
          "consentType": "terms_of_service",
          "version": "2026-01-01",
          "granted": true,
          "grantedAt": "2026-01-10T08:05:00Z",
          "required": true
        },
        {
          "consentType": "marketing_email",
          "version": "2026-01-01",
          "granted": false,
          "grantedAt": "2026-01-10T08:05:00Z",
          "required": false
        }
      ]
    }
  }
}
```

### Example Success Response (no consents recorded)

```json
{
  "data": {
    "myConsents": {
      "success": true,
      "status": 200,
      "message": "Consents retrieved successfully.",
      "meta": null,
      "payload": []
    }
  }
}
```

---

## 5. Security & Edge Cases

| Concern | Mitigation |
|---|---|
| **Unauthenticated access** | `@UseGuards(GraphQLAuthGuard)` is applied — unauthenticated requests are rejected before reaching the resolver. |
| **Cross-user access** | Consent records are always fetched scoped to the account identified by the JWT — a user cannot retrieve another user's consents. |
| **Empty result** | An empty `payload` array is a valid response — it means no consent records have been recorded yet. Clients must handle this and not treat it as an error. |
| **Required consent enforcement** | Clients should inspect the `required` field and gate access to platform features if a required consent has not been granted (`granted: false`). |
| **Stale consent versions** | Clients should compare `version` against the current consent document version to detect when the user needs to re-consent to an updated policy. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
