# Design Doc: Create Address (GraphQL Mutation)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This mutation adds a new delivery address to the authenticated user's address book. It accepts full address details including geocoordinates and an optional label.

**Goal:** Allow an authenticated user to save a new address to their account for use in checkout or profile management.

---

## 2. Proposed Solution

The gateway receives a `createAddress` mutation, enforces authentication via `GraphQLAuthGuard`, validates all input fields, and proxies the request to the Django REST address creation endpoint via `DjangoProxyService`. Django persists the address against the authenticated user's account and returns the created record. The gateway wraps it in the standard response envelope.

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
mutation CreateAddress($input: CreateAddressRequest!) {
  createAddress(input: $input) {
    success
    status
    message
    meta {
      correlationId
      timestamp
    }
    payload {
      id
      label
      street
      suburb
      city
      postalCode
      country
      latitude
      longitude
      isDefault
      deliverable
      createdAt
      updatedAt
    }
  }
}
```

### Input: `CreateAddressRequest`

| Field        | Type     | Required | Validation      | Description                          |
|--------------|----------|----------|-----------------|--------------------------------------|
| `apiVersion` | `String` | No       | Optional string | API version to use (default `"v1"`)  |
| `marketId`   | `String` | No       | Optional string | Optional market scope override       |
| `input`      | `CreateAddressPayloadDto` | Yes | Object | Address details to save |

#### `input` — `CreateAddressPayloadDto`

| Field        | Type     | Required | Validation                              | Description                                        |
|--------------|----------|----------|-----------------------------------------|----------------------------------------------------|
| `label`      | `String` | No       | Max 50 chars                            | User-defined label (e.g. `"Home"`, `"Office"`)    |
| `street`     | `String` | Yes      | Non-empty, max 255 chars                | Street address                                     |
| `suburb`     | `String` | No       | Max 100 chars                           | Suburb or neighbourhood                            |
| `city`       | `String` | Yes      | Non-empty, max 100 chars                | City name                                          |
| `postalCode` | `String` | Yes      | Non-empty, max 20 chars                 | Postal/ZIP code                                    |
| `country`    | `String` | Yes      | Exactly 2 chars (ISO 3166-1 alpha-2)   | Country code (e.g. `"KE"`, `"ZA"`)               |
| `latitude`   | `Float`  | Yes      | Numeric, -90 to 90                      | Geographic latitude                                |
| `longitude`  | `Float`  | Yes      | Numeric, -180 to 180                    | Geographic longitude                               |

### Response: `CreateAddressResponse`

| Field     | Type      | Nullable | Description                                      |
|-----------|-----------|----------|--------------------------------------------------|
| `success` | `Boolean` | No       | Whether the address was successfully created     |
| `status`  | `Int`     | No       | HTTP status code from the Django service         |
| `message` | `String`  | No       | Human-readable result message                    |
| `meta`    | `Object`  | Yes      | Tracing metadata                                 |
| `payload` | `Object`  | Yes      | Created address record; absent on failure        |
| `count`   | `Int`     | Yes      | Not used by this mutation; always `null`         |

#### `payload` — `AddressPayloadDto`

| Field         | Type      | Nullable | Description                                             |
|---------------|-----------|----------|---------------------------------------------------------|
| `id`          | `String`  | No       | UUID of the newly created address record                |
| `label`       | `String`  | Yes      | User-defined label; `null` if not provided             |
| `street`      | `String`  | No       | Street address                                          |
| `suburb`      | `String`  | Yes      | Suburb; `null` if not provided                         |
| `city`        | `String`  | No       | City name                                               |
| `postalCode`  | `String`  | No       | Postal/ZIP code                                         |
| `country`     | `String`  | No       | ISO 3166-1 alpha-2 country code                         |
| `latitude`    | `Float`   | No       | Geographic latitude                                     |
| `longitude`   | `Float`   | No       | Geographic longitude                                    |
| `isDefault`   | `Boolean` | No       | Whether this is the user's default address (Django-managed) |
| `deliverable` | `Boolean` | No       | Whether the address is confirmed deliverable            |
| `createdAt`   | `String`  | No       | ISO 8601 timestamp of creation                          |
| `updatedAt`   | `String`  | No       | ISO 8601 timestamp of last update                       |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke",
    "input": {
      "label": "Home",
      "street": "14 Riverside Drive",
      "suburb": "Westlands",
      "city": "Nairobi",
      "postalCode": "00100",
      "country": "KE",
      "latitude": -1.2671,
      "longitude": 36.8103
    }
  }
}
```

### Example Success Response

```json
{
  "data": {
    "createAddress": {
      "success": true,
      "status": 201,
      "message": "Address created successfully.",
      "meta": null,
      "payload": {
        "id": "addr-0001-0000-0000-0000-000000000001",
        "label": "Home",
        "street": "14 Riverside Drive",
        "suburb": "Westlands",
        "city": "Nairobi",
        "postalCode": "00100",
        "country": "KE",
        "latitude": -1.2671,
        "longitude": 36.8103,
        "isDefault": false,
        "deliverable": false,
        "createdAt": "2026-03-31T10:00:00Z",
        "updatedAt": "2026-03-31T10:00:00Z"
      }
    }
  }
}
```

### Example Error Response (invalid country code)

```json
{
  "errors": [
    {
      "message": "country must be longer than or equal to 2 and shorter than or equal to 2 characters",
      "extensions": { "success": false }
    }
  ]
}
```

### Example Error Response (latitude out of range)

```json
{
  "errors": [
    {
      "message": "latitude must not be greater than 90",
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
| **Cross-user write** | The address is always created under the account identified by the JWT — a user cannot add addresses to another user's account. |
| **Coordinate range** | `latitude` and `longitude` are validated with `@Min`/`@Max` at the gateway layer — out-of-range values are rejected before reaching Django. |
| **Country code format** | `@Length(2, 2)` enforces exactly 2 characters at the gateway; format correctness (valid ISO code) is Django's responsibility. |
| **Cache invalidation** | A successful `createAddress` should trigger invalidation of any cached `myAddresses` response for this user. |
| **Deliverability** | `deliverable` is set by Django after an asynchronous address verification step — it may be `false` immediately after creation. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
