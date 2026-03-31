# Design Doc: Request OTP (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation dispatches a one-time password to a user's phone number or email address. It is the first step in an OTP-based authentication flow (e.g. passwordless login, phone verification).

**Goal:** Allow a client to request an OTP delivery to a given identifier without requiring the user to be authenticated.

---

## 2. Proposed Solution

The gateway accepts a `requestOtp` mutation, validates the `identifier` and `identifierType`, and proxies the request to the Django REST OTP endpoint via `DjangoProxyService`. Django generates the OTP, stores it with a TTL, and dispatches it via the appropriate channel (SMS or email). The gateway returns a confirmation envelope indicating delivery status and expiry — no OTP value is ever returned to the client.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. The OTP and its expiry are managed entirely by Django. No cache read or write occurs for this operation.

---

## 4. API Contracts

### Request Headers

- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing. If omitted, the gateway generates one automatically and returns it in `meta.correlationId`.
- `X-Market-ID`: (Optional) Market scope override (e.g. "ZA", "KE"). Sourced from `input.marketId`.

### Mutation

```graphql
mutation RequestOtp($input: OtpRequestRequest!) {
  requestOtp(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      otpSent
      expiresInSeconds
      deliveryMethod
    }
  }
}
```

### Input: `OtpRequestRequest`

| Field        | Type     | Required | Validation      | Description                              |
|--------------|----------|----------|-----------------|------------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)      |
| `marketId`   | `String` | No       | Optional string | Optional market scope override           |
| `input`      | `OtpRequestPayloadDto` | Yes | Object | Identifier and delivery type |

#### `input` — `OtpRequestPayloadDto`

| Field            | Type             | Required | Validation                      | Description                                        |
|------------------|------------------|----------|---------------------------------|----------------------------------------------------|
| `identifier`     | `String`         | Yes      | Non-empty string                | Phone number in E.164 format or email address      |
| `identifierType` | `IdentifierType` | Yes      | Enum: `phone` \| `email`        | Whether the identifier is a phone number or email  |

### Response: `OtpRequestResponse`

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the OTP was successfully dispatched      |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |
| `payload` | `Object`  | Yes      | Present on success; absent on failure            |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload` — `OtpRequestResponsePayloadDto`

| Field              | Type      | Description                                      |
|--------------------|-----------|--------------------------------------------------|
| `otpSent`          | `Boolean` | Whether the OTP was successfully dispatched      |
| `expiresInSeconds` | `Int`     | Seconds until the OTP expires                    |
| `deliveryMethod`   | `String`  | Delivery channel used (e.g. `"sms"`, `"email"`) |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke",
    "input": {
      "identifier": "+254700000000",
      "identifierType": "phone"
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "requestOtp": {
      "success": true,
      "status": 200,
      "message": "OTP sent successfully.",
      "meta": null,
      "payload": {
        "otpSent": true,
        "expiresInSeconds": 300,
        "deliveryMethod": "sms"
      }
    }
  }
}
```

### Example Error Response (invalid identifier type)

```json
{
  "errors": [
    {
      "message": "identifierType must be a valid enum value",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (delivery failure)

```json
{
  "errors": [
    {
      "message": "Failed to deliver OTP. Please try again.",
      "extensions": { "success": false }
    }
  ]
}
```

---

## 5. Security & Edge Cases

| Concern | Mitigation |
|---|---|
| **OTP brute-force** | Rate limiting is enforced at the Django layer; the gateway surfaces the upstream `429` response. Clients should disable the resend button after a successful request. |
| **OTP value exposure** | The OTP code is never returned to the client — only delivery confirmation. Django dispatches the value out-of-band. |
| **Phone number enumeration** | The response does not differentiate between a registered and unregistered identifier. Django returns the same envelope regardless. |
| **Invalid E.164 format** | Format validation of `identifier` is Django's responsibility; the gateway passes the value through and surfaces any `400` upstream error. |
| **Unauthenticated access** | This mutation is intentionally unauthenticated — do not apply `@UseGuards(GraphQLAuthGuard)` to it. |
| **Transport security** | All traffic must be over HTTPS/TLS to prevent identifier interception in transit. |
