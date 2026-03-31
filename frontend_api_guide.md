# Rossa Frontend API Guide

This document outlines the flows, request shapes, and expected behaviors of the Rossa API (both the mock server and the eventual real backend).

---

## 🏗 Core Concepts: Request & Response Shapes

### 1. The Standard Request Wrapper
Almost every GraphQL query and mutation is heavily nested in a standard input wrapper containing routing info:

```graphql
input: {
  apiVersion: "v1",       # Always required, defaults to "v1"
  marketId: "ke",         # Often required for market-specific operations (e.g. "ke", "za")
  input: {                # The ACTUAL payload for the mutation/query goes inside here
    ... 
  }
}
```

### 2. The Standard Response Wrapper
Every successful query or mutation returns a Standard Response Envelope:

```json
{
  "success": true,        // Boolean indicating overall operation success
  "status": 200,          // HTTP-like status code (200, 201, 400, etc.)
  "message": "Success",   // Human-readable message
  "payload": { ... },     // The actual requested data (if any)
  "meta": {               // Metadata like pagination, timestamps
    "timestamp": "2026-03-31T08:00:00.000Z",
    "page": 1,
    "totalPages": 5
  }
}
```

### 3. Error Handling (Unhappy Paths)
When something goes wrong at the server level (e.g., expired token, bad inputs), GraphQL returns `errors` outside alongside `data: null`:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Unauthorized",
      "path": ["myProfile"]
    }
  ]
}
```

---

## 🔐 Auth Flows & Scenarios

### Flow 1: Login & Token Management
*   **Happy Path**: User logs in with any standard email/password. Server returns a User object and Access+Refresh tokens.
*   **Failed Login (Mock Backend)**: To test the frontend "Red Error Message" states, the mock server has built-in triggers:
    *   If you type **`wrong@example.com`** as the email: The server throws `Invalid credentials. User not found.`
    *   If you type **`wrong`**, **`error`**, or **`invalid`** as the password: The server throws `Invalid credentials. Incorrect password.`
    *   For *any other* email and password combo, the server logs you in successfully as "Jane Doe".
*   **Expired Token Flow**:
    1. Frontend sends request with expired `accessToken`.
    2. Server returns GraphQL error: `Unauthorized` / `Token expired`.
    3. Frontend intercepts error, calls `refreshTokens` mutation with the `refreshToken`.
    4. Server returns fresh `accessToken`.
    5. Frontend retries the original request.

**Login Mutation:**
```graphql
mutation Login($email: String!, $password: String!) {
  login(input: {
    apiVersion: "v1",
    marketId: "ke",
    input: { login: $email, password: $password }
  }) {
    success
    payload {
      user { id email firstName }
      tokens { accessToken refreshToken expiresIn }
    }
  }
}
```

### Flow 2: Registration & Onboarding
*   **Happy Path**:
    1. User calls `register`. Server returns the created User object.
    2. User is NOT automatically verified yet.
    3. User must call `requestOtp` -> `verifyOtp` to verify phone/email.
    4. App hits `marketOnboardingChecklist` to see what steps are pending (e.g., ID verification).
*   **Unhappy Path (User Already Exists)**: Real backend throws "User already registered" error on `register`.
*   **Mock Server Behavior**: The mock server allows free registration to simulate successful flows, storing the new user in-memory.

**Register Mutation:**
```graphql
mutation Register {
  register(input: {
    apiVersion: "v1",
    marketId: "ke",
    input: {
      email: "new@example.com",
      firstName: "Jane",
      lastName: "Doe",
      password: "pass",
      passwordConfirm: "pass",
      phoneNumber: "+254700000000"
    }
  }) {
    success
    payload {
      id email dateJoined
    }
  }
}
```

---

## 👤 Authenticated Flows (Requires `Authorization: Bearer <token>`)

For all queries below, the request header must include:
`Authorization: Bearer <your_access_token>`

If the token is missing, invalid, or expired, the backend will return a GraphQL Error `Unauthorized`.

### Addresses 
Addresses are **stateful** in the mock server.
1.  **Read**: `myAddresses(page: 1, size: 20)` -> Returns a paginated list of addresses.
2.  **Create**: `createAddress(...)` -> Appends a new address object payload. (In the mock server, if you query `myAddresses` again, the new address will be in the list!)
3.  **Delete**: `deleteAddress(addressId: "...")` -> Removes it from the list. 

### Profile Management
1.  **Read**: `myProfile` returns the user's name, display picture URL, language, and timezone.
2.  **Update**: `updateProfile` can safely change name or language fields.
3.  **Account Deletion**: `deleteAccount` triggers the GDPR deletion process across the backend.

### Market Onboarding
To enter a new market context (e.g., user travels from Kenya `ke` to South Africa `za`):
1.  App calls `marketOnboardingChecklist(marketId: "za")`.
2.  Server returns steps needed.
3.  Once steps are done, call `activateMarket(marketId: "za")` to unlock features for that market.

---

## 🖼 Avatar Image Uploads (REST API)

Because GraphQL does not handle binary file blobs well, file uploads use standard REST.

**Endpoint:** `POST /api/v1/files/avatar`
**Headers:** `Authorization: Bearer <token>`
**Body Form-Data:** `file` (the binary image data)

### Scenarios:
*   **Happy Path**: File is an image under 10MB. Server saves binary to S3, updates the user's `myProfile` table with the new URL, and returns the updated `ProfilePayloadDto`.
*   **Too Large**: Server returns HTTP 400 Bad Request with a clear error payload ("File exceeds 10 MB").
*   **Wrong Type**: Server returns HTTP 400 Bad Request ("Only JPEG/PNG accepted").
*   **Unauthorized**: Server returns HTTP 401.

**Curl Example:**
```bash
curl -X POST https://rossa-mock.up.railway.app/api/v1/files/avatar \
  -H "Authorization: Bearer mock-token-jane" \
  -F "file=@/path/to/profile.jpg"
```

---

## 🤖 Mock Server Specifics for Frontend Testers

Because this is a Mock Server designed to keep you unblocked:

1.  **Tokens**: You don't *have* to register. If you send **any** Bearer token (literally `Bearer abcdef`), you will be authenticated as the mock user "Jane Doe" in the Kenya (`ke`) market.
2.  **Resetting Data**: If you mess up your addresses or profile name during testing, just restart the mock server. It lives "in-memory", meaning stopping and starting the server completely resets the database back to the fresh seed data.
3.  **No Emails Sent**: Calling `forgotPassword` or `requestOtp` will return "Success", but no actual SMS or Email will arrive on your phone. Just type "1234" to pass any code checks in your UI.
