# Rossa Mock Server

A **FastAPI + Strawberry GraphQL** mock server that implements all RoSSA Experience API DDT operations. Runs locally or deploys to Railway in one click. No real database — all state is in-memory.

---

## Quick Start (Local)

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file
cp .env.example .env

# 4. Run
uvicorn mock_server.main:app --reload --port 4000
```

| URL | What it is |
|-----|-----------|
| `http://localhost:4000/graphql` | GraphQL API + interactive playground |
| `http://localhost:4000/docs` | REST API docs (Swagger) |
| `http://localhost:4000/health` | Health check |

---

## Mock Tokens

Use these in the `Authorization` header:

| Token | User | Market |
|-------|------|--------|
| `mock-token-jane` | Jane Doe (`jane@example.com`) | `ke` (Kenya) |
| `mock-token-john` | John Smith (`john@example.com`) | `za` (South Africa) |
| **Any other Bearer token** | Resolves to Jane (default) | — |

---

## GraphQL Operations

### Unauthenticated (no header needed)

```graphql
mutation Login {
  login(input: { apiVersion: "v1", marketId: "ke",
    input: { login: "jane@example.com", password: "any" }
  }) {
    success status message
    payload { user { email firstName } tokens { accessToken } }
  }
}
```

```graphql
mutation Register {
  register(input: { apiVersion: "v1", marketId: "ke",
    input: { email: "new@example.com", firstName: "Test", lastName: "User",
             marketId: "ke", password: "pass", passwordConfirm: "pass" }
  }) {
    success payload { id email }
  }
}
```

```graphql
mutation RequestOtp {
  requestOtp(input: { apiVersion: "v1",
    input: { identifier: "+254700000000", identifierType: phone }
  }) {
    success payload { otpSent expiresInSeconds deliveryMethod }
  }
}
```

### Authenticated (add header: `Authorization: Bearer mock-token-jane`)

```graphql
query MyProfile {
  myProfile(input: { apiVersion: "v1" }) {
    success payload { displayName avatarUrl language timezone }
  }
}
```

```graphql
query MyAddresses {
  myAddresses(input: { apiVersion: "v1", page: 1, size: 20 }) {
    success
    meta { total page totalPages }
    payload { id label street city isDefault }
  }
}
```

```graphql
mutation CreateAddress {
  createAddress(input: { apiVersion: "v1",
    input: { label: "Home", street: "123 Main St", city: "Nairobi",
             postalCode: "00100", country: "KE",
             latitude: -1.2921, longitude: 36.8219 }
  }) {
    success payload { id street isDefault }
  }
}
```

```graphql
query MarketChecklist {
  marketOnboardingChecklist(input: { apiVersion: "v1", marketId: "ke" }) {
    success payload { status allRequiredComplete steps { step required completed } }
  }
}
```

---

## REST Upload

```bash
curl -X POST http://localhost:4000/api/v1/files/avatar \
  -H "Authorization: Bearer mock-token-jane" \
  -F "file=@/path/to/image.jpg"
```

---

## Client Connection Guides

### Flutter

```dart
import 'package:graphql_flutter/graphql_flutter.dart';

final httpLink = HttpLink('http://localhost:4000/graphql');
// On Railway: HttpLink('https://rossa-mock-xxxx.railway.app/graphql')

final authLink = AuthLink(
  getToken: () async => 'Bearer mock-token-jane',
);

final client = GraphQLClient(
  link: authLink.concat(httpLink),
  cache: GraphQLCache(),
);
```

### React / Apollo Client

```ts
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

const httpLink = createHttpLink({
  uri: process.env.REACT_APP_GRAPHQL_URL ?? 'http://localhost:4000/graphql',
});

const authLink = setContext((_, { headers }) => ({
  headers: { ...headers, Authorization: 'Bearer mock-token-jane' },
}));

export const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
});
```

### Next.js (App Router)

```ts
// lib/apollo-client.ts
import { ApolloClient, InMemoryCache } from '@apollo/client';

export const apolloClient = new ApolloClient({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL ?? 'http://localhost:4000/graphql',
  headers: { Authorization: 'Bearer mock-token-jane' },
  cache: new InMemoryCache(),
});
```

```env
# .env.local
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
# When backend is ready:
# NEXT_PUBLIC_GRAPHQL_URL=https://real-api.example.com/graphql
```

> **Switching to real backend = change one env var. Zero code changes.**

---

## Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Railway auto-detects Python via `requirements.txt` (Nixpacks)
4. Set environment variables in the Railway dashboard:

| Variable | Value |
|----------|-------|
| `CORS_ORIGINS` | `https://your-app.vercel.app` (or `*` for open) |
| `MOCK_DELAY_MS` | `200` (optional, simulates latency) |

> Do **NOT** set `PORT` — Railway injects it automatically.

5. Your public URL: `https://rossa-mock-xxxx.railway.app`
6. Update client `.env` files to point at this URL

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `4000` | Auto-set by Railway — don't override |
| `MOCK_DELAY_MS` | `0` | Artificial latency per request (ms) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
