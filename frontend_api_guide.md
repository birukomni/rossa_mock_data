# Rossa Frontend & Mobile API Guide
> **Complete reference** for React, Next.js, and Flutter developers consuming the Rossa GraphQL API.  
> This guide covers every operation, every happy/unhappy path, full request+response shapes, and mobile-specific tips.

---

## ✅ Verified API Status

All endpoints below were tested and confirmed working on **2026-03-31**.

| # | Operation | Type | Auth Required | Status |
|---|-----------|------|--------------|--------|
| 1 | `requestOtp` | Mutation | ❌ No | ✅ Pass |
| 2 | `verifyOtp` | Mutation | ❌ No | ✅ Pass |
| 3 | `login` | Mutation | ❌ No | ✅ Pass |
| 4 | `login` (wrong email) | Mutation | ❌ No | ✅ Returns error |
| 5 | `login` (wrong password) | Mutation | ❌ No | ✅ Returns error |
| 6 | `register` | Mutation | ❌ No | ✅ Pass (201) |
| 7 | `forgotPassword` | Mutation | ❌ No | ✅ Pass |
| 8 | `refreshTokens` | Mutation | ❌ No | ✅ Pass |
| 9 | `myProfile` | Query | ✅ Yes | ✅ Pass |
| 10 | `myProfile` (no token) | Query | ✅ Yes | ✅ Returns Unauthorized |
| 11 | `updateProfile` | Mutation | ✅ Yes | ✅ Pass |
| 12 | `myAddresses` (paginated) | Query | ✅ Yes | ✅ Pass |
| 13 | `createAddress` | Mutation | ✅ Yes | ✅ Pass (201, stateful) |
| 14 | `setDefaultAddress` | Mutation | ✅ Yes | ✅ Pass |
| 15 | `deleteAddress` | Mutation | ✅ Yes | ✅ Pass |
| 16 | `marketOnboardingChecklist` | Query | ✅ Yes | ✅ Pass |
| 17 | `activateMarket` | Mutation | ✅ Yes | ✅ Pass |
| 18 | `updateMarketMembershipStatus` | Mutation | ✅ Yes | ✅ Pass |
| 19 | `myConsents` | Query | ✅ Yes | ✅ Pass |
| 20 | `grantConsents` | Mutation | ✅ Yes | ✅ Pass (stateful) |
| 21 | `withdrawConsent` | Mutation | ✅ Yes | ✅ Pass (stateful) |
| 22 | `requestDataExport` | Mutation | ✅ Yes | ✅ Pass |
| 23 | `POST /api/v1/files/avatar` | REST | ✅ Yes | ✅ Pass |
| 24 | REST upload (wrong MIME type) | REST | ✅ Yes | ✅ Returns HTTP 400 |
| 25 | REST upload (no token) | REST | ❌ No | ✅ Returns HTTP 401 |
| 26 | `mock-token-john` profile | Query | ✅ Yes | ✅ Returns John Smith (za) |

---

## Table of Contents
1. [Core Concepts](#-core-concepts)
2. [Client Setup](#-client-setup)
3. [Authentication — Full Flow](#-authentication--full-flow)
4. [Profile](#-profile)
5. [Addresses](#-addresses)
6. [Market & Onboarding](#-market--onboarding)
7. [Consents & GDPR](#-consents--gdpr)
8. [File Uploads (REST)](#-file-uploads-rest)
9. [Error Handling Strategy](#-error-handling-strategy)
10. [Mock Server Testing Cheat Sheet](#-mock-server-testing-cheat-sheet)

---

## 🏗 Core Concepts

### The Standard Request Shape
Every GraphQL operation uses a **double-nested** input:

```graphql
input: {
  apiVersion: "v1"       # always "v1" — don't skip this
  marketId: "ke"         # market context: "ke" (Kenya), "za" (South Africa), "ng" (Nigeria)
  input: {               # ← actual payload lives inside here
    ...fields...
  }
}
```

### The Standard Response Envelope
Every operation returns the same wrapper shape:

```json
{
  "success": true,
  "status": 200,
  "message": "Operation successful.",
  "payload": { ... },
  "meta": {
    "timestamp": "2026-03-31T09:00:00.000Z",
    "correlationId": null,
    "page": 1,
    "pageSize": 20,
    "total": 5,
    "totalPages": 1
  },
  "count": null
}
```

| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Top-level pass/fail |
| `status` | Int | HTTP-like code (200, 201, 400…) |
| `message` | String | Human-readable message — safe to display in UI |
| `payload` | Object/null | The data you actually want |
| `meta` | Object | Timestamp + pagination info (page, total, etc.) |
| `count` | Int/null | Total count shortcut for list operations |

### GraphQL Error Shape (Unhappy Paths)
When authentication fails or the server throws, the response looks like:

```json
{
  "data": { "myProfile": null },
  "errors": [
    {
      "message": "Unauthorized",
      "locations": [{ "line": 1, "column": 9 }],
      "path": ["myProfile"]
    }
  ]
}
```

> **Important for Flutter/React**: Always check `response.errors` BEFORE accessing `response.data`. If `errors` is not empty, `data` may be null.

---

## ⚙️ Client Setup

### React — Apollo Client
```ts
// lib/apollo-client.ts
import { ApolloClient, InMemoryCache, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL ?? 'http://localhost:4000/graphql',
});

// Attach token from storage on every request
const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('access_token');
  return {
    headers: { ...headers, Authorization: token ? `Bearer ${token}` : '' }
  };
});

// Global error handler — intercepts Unauthorized errors to trigger token refresh
const errorLink = onError(({ graphQLErrors, operation, forward }) => {
  if (graphQLErrors?.some(e => e.message === 'Unauthorized')) {
    // call refreshTokens here, then retry
  }
});

export const client = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: new InMemoryCache(),
});
```

### Flutter — graphql_flutter
```dart
// lib/graphql_client.dart
import 'package:graphql_flutter/graphql_flutter.dart';

GraphQLClient buildClient(String? token) {
  final httpLink = HttpLink('http://localhost:4000/graphql');
  // On Railway: 'https://rossa-mock.up.railway.app/graphql'

  final authLink = AuthLink(
    getToken: () async => token != null ? 'Bearer $token' : '',
  );

  return GraphQLClient(
    link: authLink.concat(httpLink),
    cache: GraphQLCache(store: HiveStore()),
  );
}
```

---

## 🔐 Authentication — Full Flow

### Step-by-Step: New User Journey

```
Register → RequestOtp → VerifyOtp → MarketOnboardingChecklist → ActivateMarket
```

---

### 1. `requestOtp` — Send a verification code
> No auth required.

**Request:**
```graphql
mutation RequestOtp($identifier: String!, $type: IdentifierType!) {
  requestOtp(input: {
    apiVersion: "v1"
    input: { identifier: $identifier, identifierType: $type }
  }) {
    success
    message
    payload {
      otpSent
      expiresInSeconds
      deliveryMethod
    }
  }
}
```

**Variables:**
```json
{
  "identifier": "+254700000000",
  "type": "phone"
}
```

**✅ Success Response:**
```json
{
  "data": {
    "requestOtp": {
      "success": true,
      "message": "OTP sent successfully.",
      "payload": {
        "otpSent": true,
        "expiresInSeconds": 300,
        "deliveryMethod": "sms"
      }
    }
  }
}
```

**❌ Error (mock):** This operation never fails in the mock — always returns success.

---

### 2. `verifyOtp` — Confirm the OTP code
> No auth required.

**Request:**
```graphql
mutation VerifyOtp($identifier: String!, $type: IdentifierType!, $otp: String!) {
  verifyOtp(input: {
    apiVersion: "v1"
    input: { identifier: $identifier, identifierType: $type, otp: $otp }
  }) {
    success
    message
    payload {
      user { id email firstName lastName phoneNumber }
      tokens { accessToken refreshToken tokenType expiresIn }
    }
  }
}
```

**Variables:**
```json
{
  "identifier": "+254700000000",
  "type": "phone",
  "otp": "1234"
}
```

**✅ Success Response:**
```json
{
  "data": {
    "verifyOtp": {
      "success": true,
      "message": "OTP verified successfully.",
      "payload": {
        "user": {
          "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "email": "jane@example.com",
          "firstName": "Jane",
          "lastName": "Doe",
          "phoneNumber": "+254700000000"
        },
        "tokens": {
          "accessToken": "eyJhbGciOiJI....",
          "refreshToken": "eyJhbGciOiJI....",
          "tokenType": "Bearer",
          "expiresIn": 3600
        }
      }
    }
  }
}
```

> **After this:** Store both `accessToken` and `refreshToken` in secure storage. `expiresIn` is in seconds (3600 = 1 hour).

---

### 3. `login` — Email or Phone + Password
> No auth required.

**Request:**
```graphql
mutation Login($login: String!, $password: String!) {
  login(input: {
    apiVersion: "v1"
    marketId: "ke"
    input: { login: $login, password: $password }
  }) {
    success
    message
    payload {
      user {
        id email firstName lastName
        phoneNumber isActive emailVerified phoneVerified
        marketId dateJoined
      }
      tokens { accessToken refreshToken tokenType expiresIn }
    }
  }
}
```

**Variables:**
```json
{ "login": "jane@example.com", "password": "mypassword" }
```

**✅ Success Response:**
```json
{
  "data": {
    "login": {
      "success": true,
      "message": "Login successful.",
      "payload": {
        "user": {
          "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "email": "jane@example.com",
          "firstName": "Jane",
          "lastName": "Doe",
          "isActive": true,
          "emailVerified": true,
          "phoneVerified": true,
          "marketId": "ke"
        },
        "tokens": {
          "accessToken": "eyJhbGciOiJI....",
          "refreshToken": "eyJhbGciOiJI....",
          "tokenType": "Bearer",
          "expiresIn": 3600
        }
      }
    }
  }
}
```

**❌ Error (wrong email):**
```json
{
  "data": null,
  "errors": [{ "message": "Invalid credentials. User not found." }]
}
```

**❌ Error (wrong password):**
```json
{
  "data": null,
  "errors": [{ "message": "Invalid credentials. Incorrect password." }]
}
```

> **Mock Note**: Type `wrong@example.com` as email or `wrong`/`error`/`invalid` as password to trigger these errors in the mock server.

---

### 4. `register` — Create a new account
> No auth required.

**Request:**
```graphql
mutation Register(
  $email: String!, $firstName: String!, $lastName: String!,
  $marketId: String!, $password: String!, $passwordConfirm: String!,
  $phoneNumber: String
) {
  register(input: {
    apiVersion: "v1"
    marketId: $marketId
    input: {
      email: $email
      firstName: $firstName
      lastName: $lastName
      marketId: $marketId
      password: $password
      passwordConfirm: $passwordConfirm
      phoneNumber: $phoneNumber
    }
  }) {
    success
    status
    message
    payload {
      id email firstName lastName phoneNumber
      isActive emailVerified phoneVerified
      marketId dateJoined createdAt
    }
  }
}
```

**✅ Success Response (status 201):**
```json
{
  "data": {
    "register": {
      "success": true,
      "status": 201,
      "message": "Registration successful.",
      "payload": {
        "id": "new-uuid-here",
        "email": "new@example.com",
        "firstName": "Test",
        "lastName": "User",
        "isActive": true,
        "emailVerified": false,
        "phoneVerified": false,
        "marketId": "ke",
        "dateJoined": "2026-03-31T09:00:00.000Z"
      }
    }
  }
}
```

> **After register**, the user's `emailVerified` and `phoneVerified` are both `false`. You should redirect to OTP verification.

---

### 5. `forgotPassword` — Send reset link
> No auth required.

**Request:**
```graphql
mutation ForgotPassword($identifier: String!, $type: IdentifierType!) {
  forgotPassword(input: {
    apiVersion: "v1"
    input: { identifier: $identifier, identifierType: $type }
  }) {
    success
    message
  }
}
```

**✅ Success (always — even if account doesn't exist, for security):**
```json
{
  "data": {
    "forgotPassword": {
      "success": true,
      "message": "If an account with that identifier exists, a reset link has been sent."
    }
  }
}
```

---

### 6. `refreshTokens` — Get a new access token
> No auth required — uses the refresh token itself.

**Request:**
```graphql
mutation RefreshTokens($refreshToken: String!) {
  refreshTokens(input: {
    apiVersion: "v1"
    input: { refreshToken: $refreshToken }
  }) {
    success
    message
    payload {
      tokens { accessToken refreshToken expiresIn }
    }
  }
}
```

**✅ Success:**
```json
{
  "data": {
    "refreshTokens": {
      "success": true,
      "message": "Tokens refreshed successfully.",
      "payload": {
        "user": { "id": "...", "email": "jane@example.com" },
        "tokens": { "accessToken": "NEW_TOKEN_HERE", "expiresIn": 3600 }
      }
    }
  }
}
```

> **When to call this**: When any authenticated request returns an `Unauthorized` error, call this first. If this also fails, log the user out and redirect to login.

---

## 👤 Profile

> All profile operations require `Authorization: Bearer <token>` header.

### 7. `myProfile` — Get the current user's profile

**Request:**
```graphql
query MyProfile {
  myProfile(input: { apiVersion: "v1" }) {
    success
    message
    payload {
      id accountId marketId displayName
      avatarUrl language timezone
      createdAt updatedAt
    }
  }
}
```

**✅ Success:**
```json
{
  "data": {
    "myProfile": {
      "success": true,
      "message": "Profile retrieved successfully.",
      "payload": {
        "id": "prof-0001-0000-0000-000000000001",
        "accountId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "marketId": "ke",
        "displayName": "Jane Doe",
        "avatarUrl": "https://cdn.example.com/avatars/jane.jpg",
        "language": "en",
        "timezone": "Africa/Nairobi",
        "createdAt": "2026-01-10T08:00:00Z",
        "updatedAt": "2026-03-20T14:30:00Z"
      }
    }
  }
}
```

**❌ Error (no token):**
```json
{ "data": null, "errors": [{ "message": "Unauthorized", "path": ["myProfile"] }] }
```

---

### 8. `updateProfile` — Edit name, language, or timezone

**Request:**
```graphql
mutation UpdateProfile($displayName: String!, $language: String, $timezone: String) {
  updateProfile(input: {
    apiVersion: "v1"
    input: {
      displayName: $displayName
      language: $language
      timezone: $timezone
    }
  }) {
    success
    message
    payload {
      displayName language timezone updatedAt
    }
  }
}
```

**✅ Success:** Returns the full updated `ProfilePayloadDto`.

> `avatarUrl` is updated separately via the REST file upload endpoint, not this mutation.

---

### 9. `deleteAccount` — Request account deletion (GDPR)

**Request:**
```graphql
mutation DeleteAccount {
  deleteAccount(input: { apiVersion: "v1" }) {
    success
    message
  }
}
```

**✅ Success:**
```json
{
  "data": {
    "deleteAccount": {
      "success": true,
      "message": "Account deletion requested successfully."
    }
  }
}
```

> After this call, your frontend should immediately clear local storage/tokens and redirect to the welcome screen.

---

## 📍 Addresses

> All address operations require auth. **State is persisted** in the mock — create, then re-query to see the new address!

### 10. `myAddresses` — Paginated list

**Request:**
```graphql
query MyAddresses($page: Int, $size: Int) {
  myAddresses(input: {
    apiVersion: "v1"
    page: $page
    size: $size
    orderBy: "createdAt"
    order: DESC
  }) {
    success
    message
    meta { page pageSize total totalPages }
    payload {
      id label street suburb city postalCode country
      latitude longitude isDefault deliverable
      createdAt updatedAt
    }
  }
}
```

**Variables:** `{ "page": 1, "size": 20 }`

**✅ Success:**
```json
{
  "data": {
    "myAddresses": {
      "success": true,
      "meta": { "page": 1, "pageSize": 20, "total": 2, "totalPages": 1 },
      "payload": [
        {
          "id": "addr-0001-0000-0000-000000000001",
          "label": "Home",
          "street": "14 Riverside Drive",
          "suburb": "Westlands",
          "city": "Nairobi",
          "postalCode": "00100",
          "country": "KE",
          "latitude": -1.2671,
          "longitude": 36.8103,
          "isDefault": true,
          "deliverable": true
        }
      ]
    }
  }
}
```

---

### 11. `createAddress` — Add a new address

**Request:**
```graphql
mutation CreateAddress(
  $street: String!, $city: String!, $postalCode: String!,
  $country: String!, $lat: Float!, $lng: Float!,
  $label: String, $suburb: String
) {
  createAddress(input: {
    apiVersion: "v1"
    input: {
      label: $label
      street: $street
      suburb: $suburb
      city: $city
      postalCode: $postalCode
      country: $country
      latitude: $lat
      longitude: $lng
    }
  }) {
    success
    status
    message
    payload {
      id label street city isDefault deliverable
    }
  }
}
```

**✅ Success (status 201):**
```json
{
  "data": {
    "createAddress": {
      "success": true,
      "status": 201,
      "message": "Address created successfully.",
      "payload": {
        "id": "new-uuid-here",
        "label": "Work",
        "street": "Ngong Road",
        "city": "Nairobi",
        "isDefault": false,
        "deliverable": false
      }
    }
  }
}
```

> New addresses have `isDefault: false` and `deliverable: false` until the backend validates delivery coverage.

---

### 12. `setDefaultAddress` — Mark one address as default

**Request:**
```graphql
mutation SetDefaultAddress($addressId: String!) {
  setDefaultAddress(input: {
    apiVersion: "v1"
    addressId: $addressId
  }) {
    success
    message
    payload { id isDefault }
  }
}
```

**✅ Success:** Returns the now-default address with `isDefault: true`. All other addresses for the user are automatically set to `false`.

**❌ Error (address not found):**
```json
{ "data": null, "errors": [{ "message": "Address not found." }] }
```

---

### 13. `deleteAddress` — Remove an address

**Request:**
```graphql
mutation DeleteAddress($addressId: String!) {
  deleteAddress(input: {
    apiVersion: "v1"
    addressId: $addressId
  }) {
    success
    message
  }
}
```

**✅ Success:** `{ "success": true, "message": "Address deleted successfully." }`

**❌ Error:** `{ "errors": [{ "message": "Address not found." }] }`

---

## 🗺 Market & Onboarding

### 14. `marketOnboardingChecklist` — What's left to complete?

> Use this to determine whether the user can access market features. Call this right after login.

**Request:**
```graphql
query OnboardingChecklist($marketId: String!) {
  marketOnboardingChecklist(input: {
    apiVersion: "v1"
    marketId: $marketId
  }) {
    success
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

**✅ Success (in-progress):**
```json
{
  "data": {
    "marketOnboardingChecklist": {
      "payload": {
        "marketId": "ke",
        "status": "in_progress",
        "allRequiredComplete": false,
        "steps": [
          { "step": "phone_verification", "required": true, "completed": true },
          { "step": "id_verification", "required": true, "completed": false },
          { "step": "address_confirmation", "required": false, "completed": false }
        ]
      }
    }
  }
}
```

**Possible `status` values:**

| Status | Meaning |
|--------|---------|
| `not_started` | User has not done any onboarding steps |
| `in_progress` | Some steps done, some pending |
| `complete` | All required steps done — full access granted |

> **UI Logic**: If `allRequiredComplete` is `false`, show an onboarding banner/screen. If `true`, unlock the main features.

---

### 15. `activateMarket` — Enable a new market for the user

**Request:**
```graphql
mutation ActivateMarket($marketId: String!) {
  activateMarket(input: {
    apiVersion: "v1"
    marketId: $marketId
  }) {
    success
    message
    payload { marketId status activatedAt }
  }
}
```

**✅ Success:**
```json
{
  "payload": {
    "marketId": "za",
    "status": "active",
    "activatedAt": "2026-03-31T09:15:00.000Z"
  }
}
```

---

### 16. `updateMarketMembershipStatus` — Pause/resume market access

**Request:**
```graphql
mutation UpdateMembership($marketId: String!, $status: String!) {
  updateMarketMembershipStatus(input: {
    apiVersion: "v1"
    marketId: $marketId
    status: $status
  }) {
    success
    payload { marketId status }
  }
}
```

**Valid `status` values:** `"active"`, `"paused"`, `"suspended"`

---

## ✅ Consents & GDPR

### 17. `myConsents` — See what the user has agreed to

**Request:**
```graphql
query MyConsents {
  myConsents(input: { apiVersion: "v1" }) {
    success
    payload {
      consentType
      granted
      grantedAt
      withdrawnAt
    }
  }
}
```

**✅ Success:**
```json
{
  "payload": [
    { "consentType": "marketing_email", "granted": true, "grantedAt": "2026-01-15T08:00:00Z", "withdrawnAt": null },
    { "consentType": "data_analytics",  "granted": true, "grantedAt": "2026-01-15T08:00:00Z", "withdrawnAt": null },
    { "consentType": "third_party_sharing", "granted": false, "grantedAt": null, "withdrawnAt": null }
  ]
}
```

---

### 18. `grantConsents` — Opt in to one or more consent types

**Request:**
```graphql
mutation GrantConsents($types: [String!]!) {
  grantConsents(input: {
    apiVersion: "v1"
    consentTypes: $types
  }) {
    success
    payload { consentType granted grantedAt }
  }
}
```

**Variables:** `{ "types": ["marketing_email", "data_analytics"] }`

---

### 19. `withdrawConsent` — Opt out of a single consent type

**Request:**
```graphql
mutation WithdrawConsent($type: String!) {
  withdrawConsent(input: {
    apiVersion: "v1"
    consentType: $type
  }) {
    success
    payload { consentType granted withdrawnAt }
  }
}
```

**✅ Success:**
```json
{
  "payload": {
    "consentType": "marketing_email",
    "granted": false,
    "withdrawnAt": "2026-03-31T09:30:00.000Z"
  }
}
```

**❌ Error (type not found):**
```json
{ "errors": [{ "message": "Consent 'marketing_email' not found for this user." }] }
```

---

### 20. `requestDataExport` — Download all personal data (GDPR Article 20)

**Request:**
```graphql
mutation RequestDataExport {
  requestDataExport(input: { apiVersion: "v1" }) {
    success
    message
  }
}
```

**✅ Success:**
```json
{
  "success": true,
  "message": "Data export request received. You will receive an email within 30 days."
}
```

---

## 🖼 File Uploads (REST)

GraphQL doesn't efficiently handle binary data, so avatar uploads use a dedicated REST endpoint.

**Endpoint:** `POST /api/v1/files/avatar`

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <your_token>` |
| `Content-Type` | `multipart/form-data` (set automatically by HTTP clients) |

**Body:** Form field named `file` = your image binary

### Accepted Formats
| Type | MIME Type |
|------|----------|
| JPEG | `image/jpeg` |
| PNG | `image/png` |
| WebP | `image/webp` |

**Max size:** 10 MB

**✅ Success Response:**
```json
{
  "success": true,
  "message": "Avatar updated successfully.",
  "data": {
    "id": "prof-0001-0000-0000-000000000001",
    "accountId": "a1b2c3d4...",
    "marketId": "ke",
    "displayName": "Jane Doe",
    "avatarUrl": "https://mock-bucket.s3.amazonaws.com/uploads/avatars/.../photo.jpg",
    "language": "en",
    "timezone": "Africa/Nairobi",
    "updatedAt": "2026-03-31T09:00:00.000Z"
  }
}
```

**❌ Error (too large):** `HTTP 400` — `"File exceeds the maximum allowed size of 10 MB."`  
**❌ Error (wrong type):** `HTTP 400` — `"File type is not supported. Accepted: JPEG, PNG, WebP."`  
**❌ Error (no token):** `HTTP 401` — `"Unauthorized"`

### Flutter Upload Example
```dart
final request = http.MultipartRequest(
  'POST',
  Uri.parse('http://localhost:4000/api/v1/files/avatar'),
);
request.headers['Authorization'] = 'Bearer $accessToken';
request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
final response = await request.send();
final json = await response.stream.bytesToString();
```

### React Upload Example
```ts
const uploadAvatar = async (file: File, token: string) => {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/files/avatar`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  return res.json();
};
```

---

## 🚨 Error Handling Strategy

### Recommended Frontend Logic

```
Response received
├── Check response.errors
│   ├── "Unauthorized" → call refreshTokens → retry original request
│   │                    └── if refreshTokens also fails → logout user
│   ├── "Address not found." → show toast "Address no longer exists"
│   ├── "Invalid credentials..." → show inline error under form field
│   └── Any other error → show generic "Something went wrong" toast
└── Check response.data.{operation}.success
    ├── true  → update UI state with payload
    └── false → show response.data.{operation}.message to user
```

### Token Refresh Flow (Apollo Client)
```ts
import { onError } from '@apollo/client/link/error';
import { fromPromise } from '@apollo/client';

let isRefreshing = false;
let pendingRequests: Array<() => void> = [];

const errorLink = onError(({ graphQLErrors, operation, forward }) => {
  if (graphQLErrors?.some(e => e.message === 'Unauthorized')) {
    if (!isRefreshing) {
      isRefreshing = true;
      // Call refreshTokens mutation, save new token, then retry
      fromPromise(
        client.mutate({ mutation: REFRESH_TOKENS_MUTATION, ... })
          .then(({ data }) => {
            const newToken = data.refreshTokens.payload.tokens.accessToken;
            localStorage.setItem('access_token', newToken);
            pendingRequests.forEach(cb => cb());
            pendingRequests = [];
          })
          .finally(() => { isRefreshing = false; })
      ).flatMap(() => forward(operation));
    }
  }
});
```

---

## 🤖 Mock Server Testing Cheat Sheet

| Scenario | What to do |
|---------|-----------|
| Login as Jane (Kenya) | Any email + any password |
| Login as John (S. Africa) | Use `Bearer mock-token-john` in headers |
| Trigger "User not found" error | Use email `wrong@example.com` |
| Trigger "Wrong password" error | Use password `wrong`, `error`, or `invalid` |
| Test auth guard on any query | Remove `Authorization` header |
| Test token refresh flow | Use any expired/fake token, then call `refreshTokens` |
| Reset all data to seed state | Restart the mock server (in-memory state clears) |
| Test OTP (don't wait for SMS) | Any OTP code works — mock always accepts it |
| Test multiple pages of addresses | `createAddress` several times, then query `page: 2` |
| Test image rejection | Upload a `.gif` file — server rejects it |
| Test 401 on REST upload | Send no `Authorization` header to `/api/v1/files/avatar` |

### Seed User Reference

| Token | Email | Name | Market | Phone |
|-------|-------|------|--------|-------|
| `mock-token-jane` | `jane@example.com` | Jane Doe | `ke` (Kenya) | `+254700000000` |
| `mock-token-john` | `john@example.com` | John Smith | `za` (S. Africa) | `+27700000000` |

### GraphQL Playground
After starting the server, open **http://localhost:4000/graphql** in your browser.  
Set request headers in the bottom-left panel:
```json
{ "Authorization": "Bearer mock-token-jane" }
```
