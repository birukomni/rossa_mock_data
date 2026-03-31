# Design Doc: Grant Consents (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation records one or more consent decisions for the authenticated user. A single call can submit multiple consent types in one request — for example, submitting all required consents at onboarding. Each item can represent either a grant (`granted: true`) or a decline (`granted: false`).

**Goal:** Allow an authenticated user to submit their consent decisions for one or more consent types in a single operation.

---

## 2. Proposed Solution

The gateway receives a `grantConsents` mutation, enforces authentication via `GraphQLAuthGuard`, validates the `consents` array (including each nested item), and proxies the request to the Django REST consent recording endpoint via `DjangoProxyService`. Django records each consent decision against the authenticated user's account. The gateway returns a standard empty response envelope — no payload on success.

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
mutation GrantConsents($input: GrantConsentsRequest!) {
  grantConsents(input: $input) {
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

### Input: `GrantConsentsRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |
| `input`      | `GrantConsentsPayloadDto` | Yes | Object | Consent decisions to record |

#### `input` — `GrantConsentsPayloadDto`

| Field      | Type                        | Required | Validation                                       | Description                           |
|------------|-----------------------------|----------|--------------------------------------------------|---------------------------------------|
| `consents` | `[GrantConsentItemPayloadDto]` | Yes   | Non-empty array; each item validated individually | Array of consent decisions to record |

#### `consents[]` — `GrantConsentItemPayloadDto`

| Field         | Type      | Required | Validation       | Description                                                         |
|---------------|-----------|----------|------------------|---------------------------------------------------------------------|
| `consentType` | `String`  | Yes      | Non-empty string | Consent type identifier (e.g. `"terms_of_service"`, `"marketing"`) |
| `version`     | `String`  | Yes      | Non-empty string | Version of the consent document the user is responding to           |
| `granted`     | `Boolean` | Yes      | Boolean          | Whether the user grants (`true`) or declines (`false`) this consent |

### Response: `StandardEmptyResponse`

This mutation returns no payload. A successful recording is indicated by `success: true`.

| Field     | Type      | Nullable | Description                                       |
|-----------|-----------|----------|---------------------------------------------------|
| `success` | `Boolean` | No       | Whether all consents were successfully recorded   |
| `status`  | `Int`     | No       | HTTP status code from the Django service          |
| `message` | `String`  | No       | Human-readable result message                     |
| `meta`    | `Object`  | Yes      | Tracing metadata                                  |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke",
    "input": {
      "consents": [
        {
          "consentType": "terms_of_service",
          "version": "2026-01-01",
          "granted": true
        },
        {
          "consentType": "marketing_email",
          "version": "2026-01-01",
          "granted": false
        }
      ]
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "grantConsents": {
      "success": true,
      "status": 200,
      "message": "Consents recorded successfully.",
      "meta": null
    }
  }
}
```

### Example Error Response (empty consents array)

```json
{
  "errors": [
    {
      "message": "consents must be an array",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (missing required field in item)

```json
{
  "errors": [
    {
      "message": "consents.0.version should not be empty",
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
| **Cross-user write** | Consent records are always written under the account identified by the JWT — a user cannot submit consents on behalf of another user. |
| **Nested validation** | Each item in the `consents` array is validated with `@ValidateNested({ each: true })` and `@Type(() => GrantConsentItemPayloadDto)` at the gateway layer — malformed items are rejected before reaching Django. |
| **Idempotency** | Django handles re-submission of a consent type — a second `grantConsents` call for the same `consentType` + `version` should update the existing record rather than creating a duplicate. |
| **Required consents declined** | Clients must handle the case where a user declines a required consent (`required: true`) and prevent access to platform features accordingly. Enforcement is the client's responsibility — the gateway does not block a decline. |
| **Partial failures** | The operation is atomic per Django's implementation — either all consent decisions are recorded or none are. The gateway surfaces any upstream error. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
