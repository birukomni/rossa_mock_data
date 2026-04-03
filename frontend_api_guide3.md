# Rossa Mock Server — Frontend API Guide 3 (Missing GraphQL Operations)

This document details the newly added 11 operations to fill the capabilities gap in the `Stores` and `Catalog` GraphQL domains, keeping the mock server in sync with the design (DDT) documentation.

All GraphQL requests should be made via **POST** to `/graphql` on your local instance (`http://localhost:4000/graphql`) or your production Railway instance (`https://rossamockdata-production.up.railway.app/graphql`).

---

## 1. Stores Domain (GraphQL)

### Query: `findAllStores`

Returns a paginated list of all stores in the platform. No authentication required.

**Example Request:**
```graphql
query FindAllStores {
  findAllStores {
    success
    status
    message
    count
    payload {
      id
      name
      code
      isActive
      capabilities
      location {
        lat
        lng
      }
    }
  }
}
```

### Query: `findOneStore`

Fetch a single store by its ID. No authentication required.

**Variables:**
```json
{
  "id": "rest-001"
}
```

**Example Request:**
```graphql
query FindOneStore($id: String!) {
  findOneStore(id: $id) {
    success
    payload {
      id
      name
      code
      address
      version
    }
  }
}
```

### Mutation: `createStore`

Create a new store. **Requires Admin/Operator Authentication** (`Authorization: Bearer mock-token-jane`).

**Variables:**
```json
{
  "input": {
    "name": "KFC Lavington",
    "code": "NAI-LAV-05",
    "address": "Lavington Mall",
    "isActive": true,
    "capabilities": "pickup,delivery",
    "location": {
      "lat": -1.277,
      "lng": 36.78
    }
  }
}
```

**Example Request:**
```graphql
mutation CreateStore($input: CreateStoreInput!) {
  createStore(input: $input) {
    success
    payload {
      id
      code
      name
    }
  }
}
```

### Mutation: `updateStore`

Partially update a store. Contains optimistic locking using `version`. **Requires Authentication**.

**Variables:**
```json
{
  "input": {
    "id": "rest-001",
    "isActive": false,
    "version": 3
  }
}
```

**Example Request:**
```graphql
mutation UpdateStore($input: UpdateStoreInput!) {
  updateStore(input: $input) {
    success
    payload {
      id
      isActive
      version
    }
  }
}
```

### Mutation: `deleteStore`

Permanently delete a store. **Requires Authentication**.

**Variables:**
```json
{
  "input": {
    "id": "rest-001"
  }
}
```

**Example Request:**
```graphql
mutation DeleteStore($input: DeleteStoreInput!) {
  deleteStore(input: $input) {
    success
    message
  }
}
```

---

## 2. Catalog Domain (GraphQL)

### Query: `listCategories`

Returns a paginated list of catalog categories. No authentication required.

**Example Request:**
```graphql
query ListCategories {
  listCategories {
    success
    count
    payload {
      id
      name
      description
      isActive
    }
  }
}
```

### Query: `listMenuItems`

Returns menu items. Pass `storeId` to apply contextual overrides (e.g., hidden items won't return, and `effectivePrice` will match the override rather than `basePrice`). No authentication required.

**Variables:**
```json
{
  "input": {
    "storeId": "rest-001"
  }
}
```

**Example Request:**
```graphql
query ListMenuItems($input: ListMenuItemsInput!) {
  listMenuItems(input: $input) {
    success
    count
    payload {
      id
      name
      itemType
      basePrice
      effectivePrice
      modifierGroups {
        id
        name
        modifiers {
          name
          priceAdjustment
        }
      }
    }
  }
}
```

### Mutation: `createCategory`

Create a new menu category. **Requires Authentication**.

**Variables:**
```json
{
  "input": {
    "name": "Wraps",
    "description": "Tasty chicken wraps"
  }
}
```

**Example Request:**
```graphql
mutation CreateCategory($input: CreateCategoryInput!) {
  createCategory(input: $input) {
    success
    payload {
      id
      name
    }
  }
}
```

### Mutation: `createMenuItem`

Create a new menu item, passing down its `itemType` (`single` or `combo`). If `combo` type, `comboSlots` must be defined. **Requires Authentication**.

**Variables:**
```json
{
  "input": {
    "name": "Zinger Wrap",
    "itemType": "single",
    "basePrice": "400.00",
    "isActive": true
  }
}
```

**Example Request:**
```graphql
mutation CreateMenuItem($input: CreateMenuItemInput!) {
  createMenuItem(input: $input) {
    success
    payload {
      id
      name
      basePrice
    }
  }
}
```

### Mutation: `createModifierGroup`

Attach a new modifier group to an existing menu item. **Requires Authentication**.

**Variables:**
```json
{
  "itemId": "item-001",
  "input": {
    "name": "Drink Upgrade",
    "minSelections": 0,
    "maxSelections": 1,
    "isRequired": false,
    "modifiers": [
      {
        "name": "Switch to Fanta",
        "priceAdjustment": "10.00"
      }
    ]
  }
}
```

**Example Request:**
```graphql
mutation CreateModifierGroup($itemId: String!, $input: CreateModifierGroupInput!) {
  createModifierGroup(itemId: $itemId, input: $input) {
    success
    payload {
      id
      name
      modifiers {
        name
      }
    }
  }
}
```

### Mutation: `createStoreOverride`

Create a local store override, e.g. change an item's price solely at one store (`price_override`), or mark it completely unavailable (`unavailable`), or hide it (`hidden`). **Requires Authentication**.

**Variables:**
```json
{
  "input": {
    "storeId": "rest-002",
    "menuItemId": "item-001",
    "overrideType": "price_override",
    "overridePrice": "550.00",
    "reason": "Slight location premium"
  }
}
```

**Example Request:**
```graphql
mutation CreateStoreOverride($input: CreateStoreOverrideInput!) {
  createStoreOverride(input: $input) {
    success
    payload {
      id
      overrideType
      overridePrice
    }
  }
}
```

---

## 3. Quick Start: Native cURL Examples

Below are the direct bash `curl` commands for all testing purposes (use these on your frontend / bash scripts).

### Stores

**Find all stores**
```bash
curl -s -X POST "https://rossamockdata-production.up.railway.app/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { findAllStores { success count payload { id name code isActive capabilities } } }"}'
```

**Find one store**
```bash
curl -s -X POST "https://rossamockdata-production.up.railway.app/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { findOneStore(id: \"rest-001\") { success payload { id name code capabilities } } }"}'
```

**Store mutations (auth required):**
```bash
curl -s -X POST "https://rossamockdata-production.up.railway.app/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token-jane" \
  -d '{"query":"mutation { createStore(input: { name: \"Test Store\", code: \"TST-01\", address: \"123 Main St\", isActive: true }) { success payload { id name code } } }"}'
```

### Catalog

**List categories**
```bash
curl -s -X POST "https://rossamockdata-production.up.railway.app/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { listCategories { success count payload { id name description isActive } } }"}'
```

**List menu items with a storeId (effectivePrice test)**
```bash
curl -s -X POST "https://rossamockdata-production.up.railway.app/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { listMenuItems(storeId: \"rest-001\") { success count payload { id name basePrice effectivePrice itemType } } }"}'
```

**Catalog mutations:**

*Create modifier group*
```bash
curl -s -X POST "https://rossamockdata-production.up.railway.app/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token-jane" \
  -d '{"query":"mutation { createModifierGroup(itemId: \"item-001\", input: { name: \"Spice Level\", minSelections: 1, maxSelections: 1, modifiers: [{ name: \"Mild\" }, { name: \"Hot\" }] }) { success payload { id name modifiers { name } } } }"}'
```

*Create store override*
```bash
curl -s -X POST "https://rossamockdata-production.up.railway.app/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token-jane" \
  -d '{"query":"mutation { createStoreOverride(input: { storeId: \"rest-001\", menuItemId: \"item-001\", overrideType: price_override, overridePrice: \"49.90\", reason: \"Promo\" }) { success payload { id overrideType overridePrice } } }"}'
```
