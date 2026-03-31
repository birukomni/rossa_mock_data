# Design Doc: Request Data Export (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation enqueues a full data export job for the authenticated user. The export is an asynchronous operation — the response confirms the job was accepted and provides an estimated completion time. The actual export file is delivered out-of-band (e.g. via email) once the job completes.

**Goal:** Allow an authenticated user to exercise their right to data portability by requesting an export of all personal data held against their account.

---

## 2. Proposed Solution

The gateway receives a `requestDataExport` mutation, enforces authentication via `GraphQLAuthGuard`, and proxies the request to the Django REST data export endpoint via `DjangoProxyService`. Django enqueues an async export job, records the job ID and estimated completion, and returns a confirmation. The gateway wraps it in the standard response envelope. No additional input beyond the authenticated identity is required.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. Export job state is managed entirely by Django. No cache read or write occurs for this operation.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Mutation

```graphql
mutation RequestDataExport($input: RequestDataExportRequest!) {
  requestDataExport(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      jobId
      status
      estimatedCompletion
    }
  }
}
```

### Input: `RequestDataExportRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |

No additional input fields are required. The authenticated user's identity is derived from the JWT.

### Response: `RequestDataExportResponse`

| Field     | Type      | Nullable | Description                                       |
|-----------|-----------|----------|---------------------------------------------------|
| `success` | `Boolean` | No       | Whether the export job was successfully enqueued  |
| `status`  | `Int`     | No       | HTTP status code from the Django service          |
| `message` | `String`  | No       | Human-readable result message                     |
| `meta`    | `Object`  | Yes      | Tracing metadata                                  |
| `payload` | `Object`  | Yes      | Present on success; absent on failure             |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`          |

#### `payload` — `DataExportPayloadDto`

| Field                 | Type     | Description                                              |
|-----------------------|----------|----------------------------------------------------------|
| `jobId`               | `String` | Unique identifier for the export job                     |
| `status`              | `String` | Initial job status (e.g. `"queued"`)                    |
| `estimatedCompletion` | `String` | ISO 8601 timestamp of estimated export completion        |

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
    "requestDataExport": {
      "success": true,
      "status": 202,
      "message": "Data export request accepted. You will receive an email when your export is ready.",
      "meta": null,
      "payload": {
        "jobId": "export-job-01950000-0000-7000-0000-000000000099",
        "status": "queued",
        "estimatedCompletion": "2026-04-01T10:00:00Z"
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

### Example Error Response (export already in progress)

```json
{
  "errors": [
    {
      "message": "A data export is already in progress for this account.",
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
| **Cross-user export** | The export is always scoped to the account identified by the authenticated JWT — a user cannot trigger an export for another user's data. |
| **Duplicate job prevention** | Django enforces a limit on concurrent export jobs per account and returns an error if one is already in progress. |
| **Export file delivery** | The export file is delivered out-of-band (e.g. via a time-limited download link sent to the registered email). The gateway is not involved in file delivery. |
| **Sensitive data in export** | The export may contain all personal data held for the user. Delivery must be to a verified channel only (Django's responsibility). |
| **Rate limiting** | Django may enforce a cooldown period between export requests. The gateway surfaces upstream `429` or `409` responses. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
