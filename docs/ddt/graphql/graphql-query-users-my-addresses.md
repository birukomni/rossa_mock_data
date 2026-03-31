# Design Doc: My Addresses (GraphQL Query)

**Author:** Brian Baliach
**Date:** 2026-03-31
**Jira Epic/Ticket:** TODO

---

## 1. Context & Goal

This query returns a paginated list of the authenticated user's saved delivery addresses. It is the primary way a client populates an address book UI for checkout or profile management.

**Goal:** Allow an authenticated user to retrieve all addresses saved against their account, with pagination and sort control.

---

## 2. Proposed Solution

The gateway receives a `myAddresses` query, enforces authentication via `GraphQLAuthGuard`, and proxies the paginated request to the Django REST addresses endpoint via `DjangoProxyService`. Django returns the address list scoped to the authenticated user's account. The gateway wraps results in the standard list response envelope.

Results are cached at the gateway layer via `@DynamicGqlCache()`. The cache key is derived from the authenticated user's identity and the query arguments. Any mutation that modifies the address book (`createAddress`, `setDefaultAddress`, `deleteAddress`) must invalidate this cache.

---

## 3. Data Model / Schema Changes

None. This gateway owns no database. All address data is persisted by Django. No local write occurs — the cache is read-only at the gateway level.

---

## 4. API Contracts

### Request Headers

- `Authorization`: **Required.** `Bearer <accessToken>` — enforced by `GraphQLAuthGuard`.
- `X-Correlation-ID`: (Optional) UUID v7 for distributed tracing.
- `X-Market-ID`: (Optional) Market scope override. Sourced from `input.marketId`.

### Query

```graphql
query MyAddresses($input: ListAddressesRequest!) {
  myAddresses(input: $input) {
    success
    status
    message
    meta {
      page
      pageSize
      total
      totalPages
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

### Input: `ListAddressesRequest`

| Field        | Type        | Required | Validation                          | Description                                    |
|--------------|-------------|----------|-------------------------------------|------------------------------------------------|
| `apiVersion` | `String`    | No       | Optional string                     | API version to use (default `"v1"`)            |
| `marketId`   | `String`    | No       | Optional string                     | Optional market scope override                 |
| `page`       | `Int`       | No       | Min 1, default `1`                  | Page number to retrieve                        |
| `size`       | `Int`       | No       | Min 1, default `20`                 | Number of addresses per page                   |
| `orderBy`    | `String`    | No       | Optional string, default `createdAt` | Field to sort results by                      |
| `order`      | `SortOrder` | No       | Enum: `ASC` \| `DESC`, default `DESC` | Sort direction                               |

### Response: `ListAddressesResponse`

| Field     | Type               | Nullable | Description                                      |
|-----------|--------------------|----------|--------------------------------------------------|
| `success` | `Boolean`          | No       | Whether the operation succeeded                  |
| `status`  | `Int`              | No       | HTTP status code from the Django service         |
| `message` | `String`           | No       | Human-readable result message                    |
| `meta`    | `Object`           | Yes      | Pagination and tracing metadata                  |
| `payload` | `[AddressPayloadDto]` | No    | Array of address records (empty array if none)   |

#### `meta` — `ResponseMetaDto` (pagination fields)

| Field        | Type  | Nullable | Description                              |
|--------------|-------|----------|------------------------------------------|
| `page`       | `Int` | Yes      | Current page number                      |
| `pageSize`   | `Int` | Yes      | Number of items per page                 |
| `total`      | `Int` | Yes      | Total number of addresses across all pages |
| `totalPages` | `Int` | Yes      | Total number of pages                    |

#### `payload[]` — `AddressPayloadDto`

| Field         | Type      | Nullable | Description                                             |
|---------------|-----------|----------|---------------------------------------------------------|
| `id`          | `String`  | No       | UUID of the address record                              |
| `label`       | `String`  | Yes      | User-defined label (e.g. `"Home"`, `"Office"`)         |
| `street`      | `String`  | No       | Street address                                          |
| `suburb`      | `String`  | Yes      | Suburb or neighbourhood                                 |
| `city`        | `String`  | No       | City name                                               |
| `postalCode`  | `String`  | No       | Postal/ZIP code                                         |
| `country`     | `String`  | No       | ISO 3166-1 alpha-2 country code (e.g. `"KE"`)         |
| `latitude`    | `Float`   | No       | Geographic latitude (-90 to 90)                         |
| `longitude`   | `Float`   | No       | Geographic longitude (-180 to 180)                      |
| `isDefault`   | `Boolean` | No       | Whether this is the user's default delivery address     |
| `deliverable` | `Boolean` | No       | Whether the address is confirmed deliverable            |
| `createdAt`   | `String`  | No       | ISO 8601 timestamp of address creation                  |
| `updatedAt`   | `String`  | No       | ISO 8601 timestamp of last address update               |

### Example Request Variables

```json
{
  "input": {
    "apiVersion": "v1",
    "marketId": "ke",
    "page": 1,
    "size": 20,
    "orderBy": "createdAt",
    "order": "DESC"
  }
}
```

### Example Success Response

```json
{
  "data": {
    "myAddresses": {
      "success": true,
      "status": 200,
      "message": "Addresses retrieved successfully.",
      "meta": {
        "page": 1,
        "pageSize": 20,
        "total": 2,
        "totalPages": 1,
        "correlationId": "01950000-0000-7000-0000-000000000abc",
        "timestamp": "2026-03-31T10:00:00Z"
      },
      "payload": [
        {
          "id": "addr-0001-0000-0000-0000-000000000001",
          "label": "Home",
          "street": "14 Riverside Drive",
          "suburb": "Westlands",
          "city": "Nairobi",
          "postalCode": "00100",
          "country": "KE",
          "latitude": -1.2671,
          "longitude": 36.8103,
          "isDefault": true,
          "deliverable": true,
          "createdAt": "2026-01-15T08:00:00Z",
          "updatedAt": "2026-02-10T12:00:00Z"
        },
        {
          "id": "addr-0002-0000-0000-0000-000000000002",
          "label": "Office",
          "street": "The Oval, Ring Road Parklands",
          "suburb": null,
          "city": "Nairobi",
          "postalCode": "00100",
          "country": "KE",
          "latitude": -1.2595,
          "longitude": 36.8065,
          "isDefault": false,
          "deliverable": true,
          "createdAt": "2026-02-20T09:00:00Z",
          "updatedAt": "2026-02-20T09:00:00Z"
        }
      ]
    }
  }
}
```

### Example Success Response (empty address book)

```json
{
  "data": {
    "myAddresses": {
      "success": true,
      "status": 200,
      "message": "Addresses retrieved successfully.",
      "meta": {
        "page": 1,
        "pageSize": 20,
        "total": 0,
        "totalPages": 0
      },
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
| **Cross-user access** | Addresses are always fetched scoped to the account identified by the JWT — a user cannot retrieve another user's addresses. |
| **Cache staleness** | `@DynamicGqlCache()` caches responses per user/query-args combination. Address-modifying mutations (`createAddress`, `setDefaultAddress`, `deleteAddress`) must invalidate this cache to prevent serving stale data. |
| **Empty result** | An empty `payload` array is a valid response — clients must handle this and not treat it as an error. |
| **Pagination overflow** | Requesting a `page` beyond `totalPages` returns an empty `payload` array, not an error. |
| **Transport security** | All traffic must be over HTTPS/TLS. The `Authorization` header must not be logged. |
