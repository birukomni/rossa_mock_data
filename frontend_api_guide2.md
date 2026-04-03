# Rossa API Guide — Part 2: REST Endpoints
> **Version:** v1 &nbsp;|&nbsp; **Updated:** 2026-04-02  
> Complete reference for **React**, **Next.js**, and **Flutter** developers.  
> Covers **Restaurants**, **Categories (Catalog)**, **Menu Items (Meals)**, **Orders**, and **Operator user profile (RBAC mock)**.

---

## Table of Contents

1. [API Overview](#1-api-overview)
2. [Authentication](#2-authentication)
3. [Standard Response Format](#3-standard-response-format)
4. [HTTP Status Codes](#4-http-status-codes)
5. [Error Handling](#5-error-handling)
6. [Restaurants](#6-restaurants)
7. [Categories (Catalog)](#7-categories-catalog)
8. [Menu Items (Meals)](#8-menu-items-meals)
9. [Orders](#9-orders)

---

## 1. API Overview

| Property | Value |
|---|---|
| **Base URL** | `http://localhost:4000` |
| **Production URL** | `https://rossa-mock.up.railway.app` |
| **API Prefix** | `/api/v1` |
| **Content-Type** | `application/json` |
| **Docs (Swagger)** | `http://localhost:4000/docs` |
| **Health Check** | `http://localhost:4000/health` |

**cURL — Health Check:**
```bash
curl -X GET "http://localhost:4000/health"
```

**✅ Health Check Response:**
```json
{ "status": "ok", "service": "rossa-mock-server" }
```

---

## 2. Authentication

Some endpoints require a Bearer token in the `Authorization` header.

```
Authorization: Bearer <token>
```

### Mock Tokens (for testing)

| Token | Resolves To | User ID |
|---|---|---|
| `mock-token-jane` | Jane Doe (Kenya) | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `mock-token-john` | John Smith (South Africa) | `b2c3d4e5-f6a7-8901-bcde-f12345678901` |
| `mock-token-admin` | Operator — admin (full RBAC mock) | `user-123` |
| `mock-token-analyst` | Operator — analytics-only | `user-analytics-1` |
| `mock-token-operator` | Operator — orders view, one store | `user-orders-1` |
| `mock-token-wrong-store` | Operator — admin scope, wrong store allow-list | `user-wrong-store-1` |
| _any other token_ | Defaults to Jane Doe | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |

> ⚠️ **No token at all** → `401 Unauthorized`.

### Operator user profile (RBAC mock)

Use this to test permission and store-scoping UI against fixed personas.

| | |
|---|---|
| **Method & path** | `GET /api/v1/me/operator-profile` |
| **Auth** | `Authorization: Bearer <token>` (operator tokens above) |
| **Consumer tokens** | Jane / John → **404** `No operator user profile for this account` |

**GraphQL (same data):** query `myOperatorUserProfile(input: {})` with the same `Authorization` header. `payload` is `null` for consumer-only users.

**cURL — admin profile**

```bash
curl -s -H "Authorization: Bearer mock-token-admin" \
  "http://localhost:4000/api/v1/me/operator-profile"
```

**Admin (full permissions)**

```json
{
  "id": "user-123",
  "role": "admin",
  "permissions": [
    "orders:view",
    "orders:update",
    "orders:delete",
    "orders:export",

    "menu:view",
    "menu:manage",

    "staff:view",
    "staff:manage",

    "analytics:view",
    "analytics:export",

    "stores:access_all",
    "stores:manage",

    "settings:view",
    "settings:manage"
  ],
  "allowedStores": ["store-a", "store-b"]
}
```

**Analytics-only user**

```json
{
  "id": "user-analytics-1",
  "role": "analyst",
  "permissions": ["analytics:view"],
  "allowedStores": ["store-a"]
}
```

**Orders view-only for one store**

```json
{
  "id": "user-orders-1",
  "role": "operator",
  "permissions": ["orders:view"],
  "allowedStores": ["store-a"]
}
```

**Wrong store access**

```json
{
  "id": "user-wrong-store-1",
  "role": "admin",
  "permissions": ["orders:view", "analytics:view", "menu:view"],
  "allowedStores": ["store-z"]
}
```

### Unauthorized Error (No / Bad Token)
```json
{
  "detail": "Missing or invalid Authorization header"
}
```

---

## 3. Standard Response Format

### Success (single item)
```json
{
  "success": true,
  "status": 200,
  "data": { ... }
}
```

### Success (list)
```json
{
  "success": true,
  "status": 200,
  "count": 3,
  "data": [ ... ]
}
```

### Success (paginated — used for Orders)
```json
{
  "success": true,
  "status": 200,
  "count": 25,
  "page": 1,
  "page_size": 10,
  "data": [ ... ]
}
```

### Created (201)
```json
{
  "success": true,
  "status": 201,
  "data": { ... }
}
```

### Deleted / Action
```json
{
  "success": true,
  "status": 200,
  "message": "Resource deleted"
}
```

---

## 4. HTTP Status Codes

| Code | Meaning | When it occurs |
|---|---|---|
| `200 OK` | Request succeeded | GET, PUT, PATCH, DELETE success |
| `201 Created` | Resource created | Successful POST |
| `400 Bad Request` | Invalid request body | Invalid field values (e.g. missing menu item) |
| `401 Unauthorized` | Missing or invalid token | Accessing protected endpoint without auth |
| `404 Not Found` | Resource does not exist | ID not found in the mock store |
| `422 Unprocessable Entity` | Validation failed / Business rule violated | Invalid status transition, missing required field |
| `500 Internal Server Error` | Server crash | Should not happen in the mock |

---

## 5. Error Handling

All errors follow FastAPI's standard error shape:

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422), `detail` is an array:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Frontend Checklist
- Always check the HTTP status code first.
- If `4xx`, read `response.detail` for the error message.
- If `5xx`, show a generic error and log it.

---

## 6. Restaurants

Base path: `/api/v1/restaurants`

### Fields Reference

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique restaurant ID (e.g. `rest-001`) |
| `name` | string | Restaurant display name |
| `address` | string | Street address |
| `city` | string | City name |
| `postal_code` | string | Postal code |
| `country` | string | ISO 2-letter country code (`KE`, `ZA`) |
| `latitude` | float | GPS latitude |
| `longitude` | float | GPS longitude |
| `phone` | string | Contact phone number |
| `email` | string | Contact email |
| `is_open` | boolean | Whether the branch is currently open |
| `rating` | float | Average customer rating (0.0–5.0) |
| `review_count` | int | Number of reviews |
| `distance_km` | float | Distance from user in km |
| `avg_preparation_minutes` | int | Average food prep time |
| `delivery_fee` | float | Delivery charge |
| `min_order_amount` | float | Minimum order value |
| `currency` | string | Currency code (`KES`, `ZAR`) |
| `image_url` | string | Branch image URL |
| `tags` | array | Labels like `fast-food`, `delivery` |
| `opening_hours` | object | `{ "mon_fri": "HH:MM–HH:MM", "sat_sun": "..." }` |
| `created_at` | ISO 8601 | Creation timestamp |
| `updated_at` | ISO 8601 | Last update timestamp |

---

### `GET /api/v1/restaurants` — List Restaurants

> **Auth:** Not required

Lists all restaurants. Supports filtering via query parameters.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `city` | string | Filter by city name (case-insensitive) |
| `is_open` | boolean | Filter by open status (`true` / `false`) |
| `search` | string | Search by name, address, or city |

**cURL — All restaurants:**
```bash
curl -X GET "http://localhost:4000/api/v1/restaurants"
```

**cURL — Filter by city:**
```bash
curl -X GET "http://localhost:4000/api/v1/restaurants?city=Nairobi"
```

**cURL — Search:**
```bash
curl -X GET "http://localhost:4000/api/v1/restaurants?search=westlands"
```

**cURL — Only open restaurants:**
```bash
curl -X GET "http://localhost:4000/api/v1/restaurants?is_open=true"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "count": 2,
  "data": [
    {
      "id": "rest-001",
      "name": "KFC Westlands",
      "address": "Westlands Square, Waiyaki Way",
      "city": "Nairobi",
      "postal_code": "00100",
      "country": "KE",
      "latitude": -1.2673,
      "longitude": 36.8123,
      "phone": "+254711000001",
      "email": "westlands@kfc.co.ke",
      "is_open": true,
      "rating": 4.6,
      "review_count": 312,
      "distance_km": 1.2,
      "avg_preparation_minutes": 12,
      "delivery_fee": 150.0,
      "min_order_amount": 500.0,
      "currency": "KES",
      "image_url": "https://cdn.kfc-mock.com/branches/westlands.jpg",
      "tags": ["fast-food", "chicken", "delivery"],
      "opening_hours": {
        "mon_fri": "08:00-22:00",
        "sat_sun": "09:00-23:00"
      },
      "created_at": "2025-01-10T08:00:00Z",
      "updated_at": "2026-03-15T10:00:00Z"
    }
  ]
}
```

---

### `GET /api/v1/restaurants/top` — Top Rated Restaurants

> **Auth:** Not required

Returns restaurants sorted by `rating` descending.

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 5 | Max results returned (1–50) |

**cURL:**
```bash
curl -X GET "http://localhost:4000/api/v1/restaurants/top?limit=3"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "count": 3,
  "data": [
    {
      "id": "rest-003",
      "name": "KFC Sandton City",
      "rating": 4.8,
      "distance_km": 8.4
    }
  ]
}
```

---

### `GET /api/v1/restaurants/{id}` — Get Single Restaurant

> **Auth:** Not required

**cURL:**
```bash
curl -X GET "http://localhost:4000/api/v1/restaurants/rest-001"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "rest-001",
    "name": "KFC Westlands"
  }
}
```

**❌ Error Response (404 Not Found):**
```json
{
  "detail": "Restaurant not found"
}
```

---

### `POST /api/v1/restaurants` — Create Restaurant

> **Auth:** Required (`Authorization: Bearer <token>`)

**Required Body Fields:** `name`, `address`, `city`, `country`, `latitude`, `longitude`, `phone`

**cURL:**
```bash
curl -X POST "http://localhost:4000/api/v1/restaurants" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "KFC Kisumu",
    "address": "Mega City, Kisumu",
    "city": "Kisumu",
    "country": "KE",
    "latitude": -0.0917,
    "longitude": 34.7680,
    "phone": "+254722100001",
    "email": "kisumu@kfc.co.ke",
    "is_open": true,
    "rating": 0.0,
    "distance_km": 0.5,
    "avg_preparation_minutes": 15,
    "delivery_fee": 100,
    "min_order_amount": 500,
    "currency": "KES"
  }'
```

**✅ Success Response (201 Created):**
```json
{
  "success": true,
  "status": 201,
  "data": {
    "id": "rest-a3f291b2",
    "name": "KFC Kisumu",
    "city": "Kisumu",
    "is_open": true,
    "rating": 0.0,
    "created_at": "2026-04-01T22:00:00Z",
    "updated_at": "2026-04-01T22:00:00Z"
  }
}
```

**❌ Error Response (401 Unauthorized — no token):**
```json
{
  "detail": "Missing or invalid Authorization header"
}
```

**❌ Error Response (422 Validation Error — missing required field):**
```json
{
  "detail": [
    {
      "loc": ["body", "phone"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### `PUT /api/v1/restaurants/{id}` — Full Replace Restaurant

> **Auth:** Required  
> Replaces the entire restaurant object. All required fields must be sent.

**cURL:**
```bash
curl -X PUT "http://localhost:4000/api/v1/restaurants/rest-001" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "KFC Westlands (Renovated)",
    "address": "New Westlands Square",
    "city": "Nairobi",
    "country": "KE",
    "latitude": -1.2673,
    "longitude": 36.8123,
    "phone": "+254711000001",
    "is_open": false,
    "rating": 4.6,
    "distance_km": 1.2,
    "avg_preparation_minutes": 20,
    "delivery_fee": 180,
    "min_order_amount": 500,
    "currency": "KES"
  }'
```

**✅ Success Response (200 OK):** Returns the full updated restaurant object.

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Restaurant not found" }
```

---

### `PATCH /api/v1/restaurants/{id}` — Partial Update Restaurant

> **Auth:** Required  
> Send only the fields you want to change.

**cURL — Mark a restaurant as closed:**
```bash
curl -X PATCH "http://localhost:4000/api/v1/restaurants/rest-001" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "is_open": false
  }'
```

**cURL — Update rating and prep time:**
```bash
curl -X PATCH "http://localhost:4000/api/v1/restaurants/rest-002" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4.5,
    "avg_preparation_minutes": 10
  }'
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "rest-001",
    "is_open": false,
    "updated_at": "2026-04-01T22:30:00Z"
  }
}
```

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Restaurant not found" }
```

---

### `DELETE /api/v1/restaurants/{id}` — Delete Restaurant

> **Auth:** Required

**cURL:**
```bash
curl -X DELETE "http://localhost:4000/api/v1/restaurants/rest-001" \
  -H "Authorization: Bearer mock-token-jane"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "message": "Restaurant deleted"
}
```

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Restaurant not found" }
```

---

## 7. Categories (Catalog)

Base path: `/api/v1/catalog/categories`

### Fields Reference

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique category ID (e.g. `cat-001`) |
| `name` | string | Display name (e.g. "Burgers") |
| `slug` | string | URL-friendly key (e.g. "burgers") |
| `description` | string | Short description |
| `image_url` | string | Category image URL |
| `sort_order` | int | Display order (lower = first) |
| `is_active` | boolean | Whether to show this category |
| `created_at` | ISO 8601 | Creation timestamp |
| `updated_at` | ISO 8601 | Last update timestamp |

### Seed Categories

| ID | Name | Slug |
|---|---|---|
| `cat-001` | Burgers | `burgers` |
| `cat-002` | Combos | `combos` |
| `cat-003` | Sides | `sides` |
| `cat-004` | Drinks | `drinks` |
| `cat-005` | Desserts | `desserts` |

---

### `GET /api/v1/catalog/categories` — List All Categories

> **Auth:** Not required

**cURL:**
```bash
curl -X GET "http://localhost:4000/api/v1/catalog/categories"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "count": 5,
  "data": [
    {
      "id": "cat-001",
      "name": "Burgers",
      "slug": "burgers",
      "description": "Flame-grilled and crispy chicken burgers",
      "image_url": "https://cdn.kfc-mock.com/categories/burgers.jpg",
      "sort_order": 1,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": "cat-002",
      "name": "Combos",
      "slug": "combos",
      "description": "Value meal combos with drink and side",
      "image_url": "https://cdn.kfc-mock.com/categories/combos.jpg",
      "sort_order": 2,
      "is_active": true
    }
  ]
}
```

---

### `GET /api/v1/catalog/categories/{id}` — Get Single Category

> **Auth:** Not required

**cURL:**
```bash
curl -X GET "http://localhost:4000/api/v1/catalog/categories/cat-001"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "cat-001",
    "name": "Burgers",
    "slug": "burgers"
  }
}
```

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Category not found" }
```

---

### `POST /api/v1/catalog/categories` — Create Category

> **Auth:** Required

**Required Body Fields:** `name`, `slug`

**cURL:**
```bash
curl -X POST "http://localhost:4000/api/v1/catalog/categories" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Limited Time Offers",
    "slug": "lto",
    "description": "Seasonal and limited menu items",
    "image_url": "https://cdn.kfc-mock.com/categories/lto.jpg",
    "sort_order": 6,
    "is_active": true
  }'
```

**✅ Success Response (201 Created):**
```json
{
  "success": true,
  "status": 201,
  "data": {
    "id": "cat-b7f3a1e2",
    "name": "Limited Time Offers",
    "slug": "lto",
    "is_active": true,
    "created_at": "2026-04-01T22:00:00Z",
    "updated_at": "2026-04-01T22:00:00Z"
  }
}
```

**❌ Error Response (401 — Missing token):**
```json
{ "detail": "Missing or invalid Authorization header" }
```

---

### `PUT /api/v1/catalog/categories/{id}` — Full Replace Category

> **Auth:** Required

**cURL:**
```bash
curl -X PUT "http://localhost:4000/api/v1/catalog/categories/cat-001" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Burgers & Sandwiches",
    "slug": "burgers",
    "description": "Crispy and grilled chicken burgers and sandwiches",
    "sort_order": 1,
    "is_active": true
  }'
```

**✅ Success Response (200 OK):** Returns the fully replaced category object.

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Category not found" }
```

---

### `PATCH /api/v1/catalog/categories/{id}` — Partial Update Category

> **Auth:** Required

**cURL — Deactivate a category:**
```bash
curl -X PATCH "http://localhost:4000/api/v1/catalog/categories/cat-005" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "cat-005",
    "name": "Desserts",
    "is_active": false,
    "updated_at": "2026-04-01T22:30:00Z"
  }
}
```

---

### `DELETE /api/v1/catalog/categories/{id}` — Delete Category

> **Auth:** Required

**cURL:**
```bash
curl -X DELETE "http://localhost:4000/api/v1/catalog/categories/cat-005" \
  -H "Authorization: Bearer mock-token-jane"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "message": "Category deleted"
}
```

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Category not found" }
```

---

## 8. Menu Items (Meals)

Base path: `/api/v1/menu/items`

### Fields Reference

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique item ID (e.g. `item-001`) |
| `restaurant_id` | string | Owning restaurant's ID |
| `category_id` | string | Category this item belongs to |
| `name` | string | Item display name |
| `description` | string | Short description |
| `price` | float | Item price |
| `currency` | string | Currency code |
| `image_url` | string | Item image URL |
| `calories` | int | Calorie count |
| `is_available` | boolean | Whether this item can be ordered |
| `is_featured` | boolean | Featured / promoted item |
| `tags` | array | Labels like `spicy`, `bestseller` |
| `created_at` | ISO 8601 | Creation timestamp |
| `updated_at` | ISO 8601 | Last update timestamp |

---

### `GET /api/v1/menu/items` — List Menu Items

> **Auth:** Not required

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `restaurant_id` | string | Filter by restaurant |
| `category_id` | string | Filter by category |
| `is_available` | boolean | Only show available items |
| `is_featured` | boolean | Only show featured items |

**cURL — All items:**
```bash
curl -X GET "http://localhost:4000/api/v1/menu/items"
```

**cURL — Featured items only:**
```bash
curl -X GET "http://localhost:4000/api/v1/menu/items?is_featured=true"
```

**cURL — Items for a specific restaurant:**
```bash
curl -X GET "http://localhost:4000/api/v1/menu/items?restaurant_id=rest-001"
```

**cURL — Items by category:**
```bash
curl -X GET "http://localhost:4000/api/v1/menu/items?category_id=cat-002"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "count": 2,
  "data": [
    {
      "id": "item-001",
      "restaurant_id": "rest-001",
      "category_id": "cat-001",
      "name": "Zinger Burger",
      "description": "Spicy crispy chicken fillet with zinger sauce in a toasted bun",
      "price": 520.0,
      "currency": "KES",
      "image_url": "https://cdn.kfc-mock.com/items/zinger-burger.jpg",
      "calories": 540,
      "is_available": true,
      "is_featured": true,
      "tags": ["spicy", "bestseller"],
      "created_at": "2025-01-10T08:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    },
    {
      "id": "item-004",
      "restaurant_id": "rest-001",
      "category_id": "cat-002",
      "name": "Trilogy Box Meal",
      "description": "3-piece chicken, large fries, coleslaw and a drink",
      "price": 1050.0,
      "currency": "KES",
      "image_url": "https://cdn.kfc-mock.com/items/trilogy-box.jpg",
      "is_available": true,
      "is_featured": true
    }
  ]
}
```

---

### `GET /api/v1/menu/items/{id}` — Get Single Menu Item

> **Auth:** Not required

**cURL:**
```bash
curl -X GET "http://localhost:4000/api/v1/menu/items/item-001"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "item-001",
    "name": "Zinger Burger",
    "price": 520.0,
    "currency": "KES",
    "is_available": true
  }
}
```

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Menu item not found" }
```

---

### `POST /api/v1/menu/items` — Create Menu Item

> **Auth:** Required

**Required Body Fields:** `restaurant_id`, `category_id`, `name`, `price`

**cURL:**
```bash
curl -X POST "http://localhost:4000/api/v1/menu/items" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "rest-001",
    "category_id": "cat-001",
    "name": "Double Crunch Burger",
    "description": "Two crispy chicken fillets stacked high",
    "price": 750,
    "currency": "KES",
    "image_url": "https://cdn.kfc-mock.com/items/double-crunch.jpg",
    "calories": 820,
    "is_available": true,
    "is_featured": false,
    "tags": ["new", "double"]
  }'
```

**✅ Success Response (201 Created):**
```json
{
  "success": true,
  "status": 201,
  "data": {
    "id": "item-c9a2f3b1",
    "restaurant_id": "rest-001",
    "category_id": "cat-001",
    "name": "Double Crunch Burger",
    "price": 750.0,
    "is_available": true,
    "created_at": "2026-04-01T22:00:00Z",
    "updated_at": "2026-04-01T22:00:00Z"
  }
}
```

**❌ Error Response (401 — Missing token):**
```json
{ "detail": "Missing or invalid Authorization header" }
```

**❌ Error Response (422 — Missing required field):**
```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### `PUT /api/v1/menu/items/{id}` — Full Replace Menu Item

> **Auth:** Required

**cURL:**
```bash
curl -X PUT "http://localhost:4000/api/v1/menu/items/item-001" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "rest-001",
    "category_id": "cat-001",
    "name": "Zinger Burger XL",
    "description": "All-new bigger Zinger",
    "price": 590,
    "currency": "KES",
    "is_available": true,
    "is_featured": true,
    "tags": ["spicy", "xl"]
  }'
```

**✅ Success Response (200 OK):** Returns the fully replaced menu item.

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Menu item not found" }
```

---

### `PATCH /api/v1/menu/items/{id}` — Partial Update Menu Item

> **Auth:** Required

**cURL — Mark item as unavailable:**
```bash
curl -X PATCH "http://localhost:4000/api/v1/menu/items/item-001" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "is_available": false
  }'
```

**cURL — Update price:**
```bash
curl -X PATCH "http://localhost:4000/api/v1/menu/items/item-002" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 700,
    "is_featured": true
  }'
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "item-001",
    "name": "Zinger Burger",
    "is_available": false,
    "updated_at": "2026-04-01T22:30:00Z"
  }
}
```

---

### `DELETE /api/v1/menu/items/{id}` — Delete Menu Item

> **Auth:** Required

**cURL:**
```bash
curl -X DELETE "http://localhost:4000/api/v1/menu/items/item-001" \
  -H "Authorization: Bearer mock-token-jane"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "message": "Menu item deleted"
}
```

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Menu item not found" }
```

---

## 9. Orders

Base path: `/api/v1/orders`

> **All order endpoints require authentication.**

### Order Status Machine

Orders follow a strict lifecycle:

```
pending → confirmed → preparing → out_for_delivery → delivered
   ↓              ↓
cancelled    cancelled
```

| Transition | Allowed From |
|---|---|
| `confirmed` | `pending` |
| `cancelled` | `pending`, `confirmed` |
| `preparing` | `confirmed` |
| `out_for_delivery` | `preparing` |
| `delivered` | `out_for_delivery` |

### Fields Reference

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique order ID (e.g. `ord-001`) |
| `user_id` | string | The user who placed this order |
| `restaurant_id` | string | The restaurant fulfilling the order |
| `status` | string | `pending` / `confirmed` / `preparing` / `out_for_delivery` / `delivered` / `cancelled` |
| `payment_status` | string | `pending` / `paid` / `failed` / `refunded` |
| `payment_method` | string | `card` / `mpesa` / `cash` |
| `items` | array | Order line items (see below) |
| `subtotal` | float | Sum of all item subtotals |
| `delivery_fee` | float | Delivery charge from the restaurant |
| `tax` | float | 16% VAT (auto-calculated) |
| `total` | float | `subtotal + delivery_fee + tax` |
| `currency` | string | Currency code |
| `delivery_address` | object | Delivery location details |
| `special_instructions` | string | Free-text instructions |
| `estimated_delivery_minutes` | int | `avg_preparation_minutes + 10` |
| `placed_at` | ISO 8601 | When the order was placed |
| `updated_at` | ISO 8601 | Last status update |

**Item fields inside `items[]`:**

| Field | Type | Description |
|---|---|---|
| `menu_item_id` | string | Reference to the menu item |
| `name` | string | Item name (resolved from menu) |
| `image_url` | string | Item image (resolved from menu) |
| `quantity` | int | Number of units |
| `unit_price` | float | Price per unit |
| `subtotal` | float | `unit_price × quantity` |

---

### `GET /api/v1/orders` — List My Orders

> Returns only the orders belonging to the authenticated user.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | Filter by status (e.g. `pending`, `delivered`) |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 10, max: 100) |

**cURL — All my orders:**
```bash
curl -X GET "http://localhost:4000/api/v1/orders" \
  -H "Authorization: Bearer mock-token-jane"
```

**cURL — Filter by status:**
```bash
curl -X GET "http://localhost:4000/api/v1/orders?status=delivered" \
  -H "Authorization: Bearer mock-token-jane"
```

**cURL — Paginated:**
```bash
curl -X GET "http://localhost:4000/api/v1/orders?page=2&page_size=5" \
  -H "Authorization: Bearer mock-token-jane"
```

**cURL — John's orders:**
```bash
curl -X GET "http://localhost:4000/api/v1/orders" \
  -H "Authorization: Bearer mock-token-john"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "count": 3,
  "page": 1,
  "page_size": 10,
  "data": [
    {
      "id": "ord-001",
      "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "restaurant_id": "rest-001",
      "status": "delivered",
      "payment_status": "paid",
      "payment_method": "card",
      "items": [
        {
          "menu_item_id": "item-004",
          "name": "Trilogy Box Meal",
          "image_url": "https://cdn.kfc-mock.com/items/trilogy-box.jpg",
          "quantity": 2,
          "unit_price": 1050.0,
          "subtotal": 2100.0
        }
      ],
      "subtotal": 2340.0,
      "delivery_fee": 150.0,
      "tax": 374.4,
      "total": 2864.4,
      "currency": "KES",
      "delivery_address": {
        "street": "14 Riverside Drive",
        "city": "Nairobi",
        "postal_code": "00100",
        "country": "KE",
        "latitude": -1.2671,
        "longitude": 36.8103
      },
      "special_instructions": "",
      "estimated_delivery_minutes": 22,
      "placed_at": "2026-03-28T10:00:00Z",
      "updated_at": "2026-03-28T10:45:00Z"
    }
  ]
}
```

**❌ Error Response (401 — No token):**
```json
{ "detail": "Missing or invalid Authorization header" }
```

---

### `GET /api/v1/orders/{id}` — Get Single Order

> Returns full order details. Only accessible by the user who placed it.

**cURL:**
```bash
curl -X GET "http://localhost:4000/api/v1/orders/ord-001" \
  -H "Authorization: Bearer mock-token-jane"
```

**✅ Success Response (200 OK):** Returns the full order object (same shape as the list endpoint).

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Order not found" }
```

---

### `POST /api/v1/orders` — Place a New Order

> The server automatically:
> - Resolves `menu_item_id` → fetches `name`, `image_url`, `price`
> - Calculates `subtotal`, `delivery_fee` (from restaurant), `tax` (16% VAT), and `total`
> - Sets `estimated_delivery_minutes = avg_preparation_minutes + 10`

**Required Body Fields:** `restaurant_id`, `items` (at least one), `payment_method`, `delivery_address`

**cURL:**
```bash
curl -X POST "http://localhost:4000/api/v1/orders" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "rest-001",
    "items": [
      { "menu_item_id": "item-001", "quantity": 2 },
      { "menu_item_id": "item-008", "quantity": 1 }
    ],
    "payment_method": "mpesa",
    "delivery_address": {
      "street": "14 Riverside Drive",
      "suburb": "Westlands",
      "city": "Nairobi",
      "postal_code": "00100",
      "country": "KE",
      "latitude": -1.2671,
      "longitude": 36.8103
    },
    "special_instructions": "Extra ketchup please"
  }'
```

**✅ Success Response (201 Created):**
```json
{
  "success": true,
  "status": 201,
  "data": {
    "id": "ord-f1a3c8b2",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "restaurant_id": "rest-001",
    "status": "pending",
    "payment_status": "pending",
    "payment_method": "mpesa",
    "items": [
      {
        "menu_item_id": "item-001",
        "name": "Zinger Burger",
        "image_url": "https://cdn.kfc-mock.com/items/zinger-burger.jpg",
        "quantity": 2,
        "unit_price": 520.0,
        "subtotal": 1040.0
      },
      {
        "menu_item_id": "item-008",
        "name": "Large Fries",
        "image_url": "https://cdn.kfc-mock.com/items/large-fries.jpg",
        "quantity": 1,
        "unit_price": 230.0,
        "subtotal": 230.0
      }
    ],
    "subtotal": 1270.0,
    "delivery_fee": 150.0,
    "tax": 203.2,
    "total": 1623.2,
    "currency": "KES",
    "estimated_delivery_minutes": 22,
    "placed_at": "2026-04-01T22:00:00Z",
    "updated_at": "2026-04-01T22:00:00Z"
  }
}
```

**❌ Error Response (400 — Invalid menu item):**
```json
{ "detail": "Menu item not found: item-999" }
```

**❌ Error Response (400 — Invalid restaurant):**
```json
{ "detail": "Restaurant not found" }
```

---

### `PUT /api/v1/orders/{id}` — Full Replace Order

> **Auth:** Required  
> Used for admin-level overrides. Replaces the entire order.

**cURL:**
```bash
curl -X PUT "http://localhost:4000/api/v1/orders/ord-001" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "rest-001",
    "status": "delivered",
    "payment_status": "paid",
    "payment_method": "card",
    "items": [],
    "subtotal": 1000.0,
    "delivery_fee": 150.0,
    "tax": 160.0,
    "total": 1310.0,
    "currency": "KES",
    "delivery_address": {
      "street": "14 Riverside Drive",
      "city": "Nairobi",
      "postal_code": "00100",
      "country": "KE",
      "latitude": -1.2671,
      "longitude": 36.8103
    },
    "estimated_delivery_minutes": 20
  }'
```

**✅ Success Response (200 OK):** Returns the fully replaced order.

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Order not found" }
```

---

### `PATCH /api/v1/orders/{id}/status` — Advance Order Status

> **Auth:** Required  
> Must follow the valid status machine rules.

**cURL — Confirm a pending order:**
```bash
curl -X PATCH "http://localhost:4000/api/v1/orders/ord-001/status" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{ "status": "confirmed" }'
```

**cURL — Mark as preparing:**
```bash
curl -X PATCH "http://localhost:4000/api/v1/orders/ord-001/status" \
  -H "Authorization: Bearer mock-token-jane" \
  -H "Content-Type: application/json" \
  -d '{ "status": "preparing" }'
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "ord-001",
    "status": "confirmed",
    "updated_at": "2026-04-01T22:30:00Z"
  }
}
```

**❌ Error Response (422 — Invalid transition):**
```json
{
  "detail": "Cannot transition from 'delivered' to 'preparing'. Allowed: []"
}
```

**❌ Error Response (404 Not Found):**
```json
{ "detail": "Order not found" }
```

---

### `DELETE /api/v1/orders/{id}` — Cancel Order

> **Auth:** Required  
> Only works if order is in `pending` or `confirmed` status. Cannot cancel an order that is `preparing`, `out_for_delivery`, `delivered`, or already `cancelled`.

**cURL:**
```bash
curl -X DELETE "http://localhost:4000/api/v1/orders/ord-001" \
  -H "Authorization: Bearer mock-token-jane"
```

**✅ Success Response (200 OK):**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "ord-001",
    "status": "cancelled",
    "updated_at": "2026-04-01T22:35:00Z"
  }
}
```

**❌ Error Response (422 — Cannot cancel):**
```json
{
  "detail": "Order not found or cannot be cancelled (already delivered or cancelled)"
}
```
