# Design Doc: Market Onboarding Checklist (GraphQL Query)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This query retrieves the authenticated user's onboarding checklist for a specific market — a structured list of steps the user must complete before they can transact within that market. Each step indicates whether it is required and whether it has been completed.

**Goal:** Allow a client to determine which onboarding steps remain for a given market and gate access to market features accordingly.

---

## 2. Proposed Solution

The gateway receives a `marketOnboardingChecklist` query, enforces authentication via `GraphQLAuthGuard`, validates that `marketId` is present, and proxies the request to the Django REST onboarding checklist endpoint via `DjangoProxyService`. Django evaluates the user's onboarding state for the given market and returns the checklist. The gateway wraps it in the standard response envelope.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All onboarding state is tracked by Django. No local state is written.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: Sourced from the required `marketId` field in this request — unlike other operations, `marketId` is mandatory for this query.

### Query

```graphql
query MarketOnboardingChecklist($input: GetOnboardingChecklistRequest!) {
  marketOnboardingChecklist(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      marketId
      status
      allRequiredComplete
      steps {
        step
        required
        completed
      }
    }
  }
}
```

### Input: `GetOnboardingChecklistRequest`

| Field        | Type     | Required | Validation       | Description                                                            |
|--------------|----------|----------|------------------|------------------------------------------------------------------------|
| `apiVersion` | `String` | No       | Optional string  | API version to use (default `"v1"`)                                    |
| `marketId`   | `String` | **Yes**  | Non-empty string | Market to retrieve the checklist for. Required — overrides `StandardRequest.marketId`. |

### Response: `GetOnboardingChecklistResponse`

| Field     | Type      | Nullable | Description                                       |
|-----------|-----------|----------|---------------------------------------------------|
| `success` | `Boolean` | No       | Whether the operation succeeded                   |
| `status`  | `Int`     | No       | HTTP status code from the Django service          |
| `message` | `String`  | No       | Human-readable result message                     |
| `meta`    | `Object`  | Yes      | Tracing metadata                                  |
| `payload` | `Object`  | Yes      | Onboarding checklist; absent on failure           |
| `count`   | `Int`     | Yes      | Not used by this query; always `null`             |

#### `payload` — `OnboardingChecklistPayloadDto`

| Field                 | Type                      | Description                                                      |
|-----------------------|---------------------------|------------------------------------------------------------------|
| `marketId`            | `String`                  | The market this checklist applies to                             |
| `status`              | `String`                  | Overall onboarding status (e.g. `"in_progress"`, `"complete"`) |
| `allRequiredComplete` | `Boolean`                 | Whether all required steps have been completed                   |
| `steps`               | `[OnboardingStepPayloadDto]` | Ordered list of onboarding steps                              |

#### `payload.steps[]` — `OnboardingStepPayloadDto`

| Field       | Type      | Description                                                          |
|-------------|-----------|----------------------------------------------------------------------|
| `step`      | `String`  | Step identifier (e.g. `"id_verification"`, `"phone_verification"`) |
| `required`  | `Boolean` | Whether this step must be completed before transacting              |
| `completed` | `Boolean` | Whether the user has completed this step                            |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ng"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "marketOnboardingChecklist": {
      "success": true,
      "status": 200,
      "message": "Onboarding checklist retrieved successfully.",
      "meta": null,
      "payload": {
        "marketId": "ng",
        "status": "in_progress",
        "allRequiredComplete": false,
        "steps": [
          {
            "step": "phone_verification",
            "required": true,
            "completed": true
          },
          {
            "step": "id_verification",
            "required": true,
            "completed": false
          },
          {
            "step": "address_confirmation",
            "required": false,
            "completed": false
          }
        ]
      }
    }
  }
}
```

### Example Error Response (market not activated for this user)

```json
{
  "errors": [
    {
      "message": "User does not have an active membership in this market.",
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
| **Cross-user access** | The checklist is always scoped to the account identified by the JWT — a user cannot retrieve another user's onboarding state. |
| **`marketId` is required** | Unlike other operations where `marketId` is optional, this query requires it. The field overrides `StandardRequest.marketId` and is enforced as non-empty. Missing or empty `marketId` is rejected at the gateway validation layer. |
| **No active membership** | If the user has not activated the given market, Django returns an error. Clients should call `activateMarket` before calling this query. |
| **Access gating** | Clients should inspect `allRequiredComplete` before allowing the user to transact in the market. Individual `required` steps that are `completed: false` should be used to drive the user through the onboarding flow. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
