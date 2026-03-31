## ADR-002: API Contract Alignment and Request Context
Date: 2026-03-24
Status: Accepted

### Context
The NestJS API Gateway needs to align with the RoSSA Platform API Contracts DDT (v1.0, 2026-03-23). This involves standardizing the response envelope to include `success` and `meta` fields, propagating `X-Correlation-ID` and `X-Market-ID` headers to the Django backend, and updating the JWT payload structure. We need a clean and maintainable way to thread request-scoped data (like correlation IDs and market IDs) through the application without excessive prop drilling.

### Decision
1. **Response Envelope:** We will update `StandardResponse`, `StandardListResponse`, and `StandardEmptyResponse` to include `success: boolean`, `status: number`, and `meta?: ResponseMetaDto`.
2. **Request Context:** We will use `AsyncLocalStorage` from `node:async_hooks` to create a `RequestContext` store. This allows us to implicitly pass `correlationId` and `marketId` down the asynchronous execution chain.
3. **Middlewares:** We will introduce `CorrelationIdMiddleware` to generate or extract `X-Correlation-ID` and initialize the `RequestContext`. We will also introduce `MarketIdMiddleware` to extract `marketId` from the GraphQL request body and add it to the `RequestContext` (initializes it if it isn't already). Both middlewares will be scoped to the `/graphql` route.
4. **Interceptors:** We will update `LoggingInterceptor` to log `success`, `meta.correlationId`, `meta.page`, and `meta.total`. We will introduce `ResponseTimestampInterceptor` to autopopulate `meta.timestamp` on all responses.
5. **HTTP Client:** `HttpClientService` will automatically read `correlationId` and `marketId` from the `RequestContext` and inject them as `X-Correlation-ID` and `X-Market-ID` headers on all outbound requests to Django. It will also return the full `DjangoResponseEnvelope` instead of just the `data` field.
6. **Auth Guard:** `GraphQLAuthGuard` will validate the `marketId` in the `RequestContext` against the `scope_context.market_id` in the JWT payload. If the `marketId` is invalid or missing, it will default to the `scope_context.market_id`. If `scope_context` is null, the `marketId` will not be piped.
7. **Standard Request:** We will update `StandardRequest` to include `apiVersion` to support versioning. ~~`preferredLanguage` was initially added here but was later removed — see ADR-005.~~

### Consequences
Pros:
- Aligns the API Gateway with the platform API contracts.
- `AsyncLocalStorage` eliminates the need to pass request-scoped data through every service method signature, keeping the code clean and focused on business logic.
- Centralized header injection in `HttpClientService` ensures consistent propagation of tracing and routing information.
- Auto-populating `meta.timestamp` and logging response metadata improves observability and debugging.

Cons:
- `AsyncLocalStorage` introduces a slight performance overhead, though generally negligible for typical API workloads.
- Implicit context passing can make it harder to trace where data is coming from if developers are unfamiliar with the pattern.
