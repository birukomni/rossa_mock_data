## ADR-004: Cookie Propagation and Request Context Middleware Refactor
Date: 2026-03-26
Status: Accepted

### Context

The NestJS API Gateway acts as a Backend-for-Frontend (BFF) sitting between browser clients and the Django backend. Django issues an HttpOnly refresh token cookie on successful authentication. Two problems existed:

1. **Django → Frontend (outbound):** `HttpClientService.handleResponse` only extracted `res.data` from Axios responses and discarded `res.headers`. Any `Set-Cookie` header Django sent was silently dropped — the browser never received the HttpOnly cookie.

2. **Frontend → Django (inbound):** `RequestContext` stored `Authorization`, `correlationId`, and `marketId`, but not the incoming `Cookie` header. When the browser sent a refresh token cookie on subsequent requests, `HttpClientService` never forwarded it to Django, making token refresh flows impossible.

A secondary problem emerged during the fix: `AuthorizationMiddleware` was incorrectly responsible for both *creating* the `AsyncLocalStorage` context store and *populating* one of its fields. This conflated two distinct responsibilities and made the chain harder to reason about — any developer reading `CorrelationIdMiddleware` or `MarketIdMiddleware` had to know that a completely different middleware was responsible for context creation.

### Decision

#### 1. Dedicated `RequestContextMiddleware`

Introduce `RequestContextMiddleware` as the sole middleware responsible for calling `requestContextStorage.run(...)` and creating the `AsyncLocalStorage` store. It runs first in the middleware chain and initialises the context with safe defaults:

```ts
requestContextStorage.run({ correlationId: '', outboundCookies: [] }, next);
```

All other middleware (`AuthorizationMiddleware`, `CorrelationIdMiddleware`, `MarketIdMiddleware`) are simplified to only read and mutate the existing store via `requestContextStorage.getStore()`. None of them call `.run()`.

This makes the single-responsibility of each middleware explicit and removes the implicit ordering dependency that previously existed between `AuthorizationMiddleware` and the others.

#### 2. Inbound cookie forwarding via `RequestContext`

A dedicated `CookieMiddleware` captures `req.headers.cookie` into `ctx.cookieHeader`. Keeping this separate from `AuthorizationMiddleware` gives each middleware a single, named responsibility and makes the chain self-documenting. `HttpClientService.getOutboundHeaders()` forwards the value as the `Cookie` header on every outbound Django request, ensuring the browser's HttpOnly refresh token cookie reaches Django transparently on every call with no resolver or service involvement.

#### 3. Outbound cookie forwarding via `CookieForwardingInterceptor`

Rather than threading `Set-Cookie` values through the envelope chain (which would require every resolver to handle cookie logic), outbound cookies are accumulated in the request context:

- `HttpClientService.handleResponse` pushes any `set-cookie` header values from the Axios response into `ctx.outboundCookies`.
- A new global `CookieForwardingInterceptor` runs after every handler and drains `ctx.outboundCookies` onto the Express response via `res.setHeader('Set-Cookie', cookies)`. It handles both HTTP and GraphQL execution contexts.

The interceptor is registered once in `AppModule` as `APP_INTERCEPTOR`. No resolver, service, or DTO is ever aware of cookies.

### Consequences

**Pros:**

- **Universality:** Cookie forwarding is completely automatic in both directions. Any Django endpoint that sets or reads cookies works correctly without any per-feature code.
- **Single responsibility:** `RequestContextMiddleware` owns context creation. Each other middleware owns exactly one field. The chain is self-documenting.
- **No schema leakage:** `Set-Cookie` values never appear in `DjangoResponseEnvelope`, `ProxyResponseEnvelope`, or any GraphQL type. The internal transport mechanism is fully encapsulated in the infrastructure layer.
- **Correctness of `Set-Cookie`:** Node.js `http.ServerResponse.setHeader('Set-Cookie', string[])` emits one `Set-Cookie` header line per array element, which is the correct wire format (unlike most headers, `Set-Cookie` must not be comma-joined).

**Cons:**

- `AsyncLocalStorage` introduces a very slight per-request overhead (nanosecond-range), which is negligible for typical API workloads.
- The implicit context passing pattern can be unfamiliar to developers new to `AsyncLocalStorage`. The `RequestContextMiddleware` comment and this ADR serve as the primary orientation point.
- Developers adding a new middleware must remember to call `getStore()` rather than `.run()`, and must ensure `RequestContextMiddleware` runs before their middleware in the chain.
