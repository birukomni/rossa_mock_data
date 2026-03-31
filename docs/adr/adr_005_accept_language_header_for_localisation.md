## ADR-005: Accept-Language Header for Localisation
Date: 2026-03-30
Status: Accepted

### Context

ADR-002 added a `preferredLanguage` field to `StandardRequest` so that resolvers could accept a locale from clients and pass it to services for localised error messages. This approach had several problems:

1. **Schema leakage:** Every GraphQL `@InputType` that extended `StandardRequest` exposed `preferredLanguage` as a first-class field in the schema, even though it is purely an infrastructure concern.
2. **Redundant transport:** HTTP already defines a standard mechanism for content negotiation: the `Accept-Language` header. Asking clients to also set a body field for the same information forced them to manage two sources of truth.
3. **Prop drilling:** Resolvers had to destructure `preferredLanguage` from the DTO and thread it down into every service method, adding noise to every method signature without adding domain value.
4. **Guard/filter coupling:** Exception filters and auth guards needed the language for translating error responses, but they do not receive resolver arguments — they had to dig through the request body or GraphQL variables, which is fragile and transport-specific.

### Decision

Remove `preferredLanguage` from `StandardRequest` entirely and replace it with a dedicated middleware + helper pair that reads the standard `Accept-Language` HTTP header and stores the validated locale in `RequestContext` via `AsyncLocalStorage`.

#### 1. `AcceptLanguageMiddleware`

A new middleware reads `req.headers['accept-language']`, extracts the primary language tag (the first entry before any `;q=` weight), validates it against the `supportedLanguages` set, and writes the result into the existing context store:

```ts
const ctx = requestContextStorage.getStore();
ctx.preferredLanguage = validated ?? undefined;
```

It runs last in both gateway middleware chains (after `MarketIdMiddleware`), consistent with the single-responsibility ownership model established in ADR-004.

#### 2. `getPreferredLanguage()` helper

A zero-argument utility function:

```ts
export function getPreferredLanguage(): SupportedLanguages | undefined {
  return requestContextStorage.getStore()?.preferredLanguage;
}
```

Guards and exception filters call this directly — no `ExecutionContext` or `ArgumentsHost` parameter needed. Because the value lives in `AsyncLocalStorage`, it is available anywhere in the request's execution chain without being passed explicitly.

#### 3. `@AcceptLanguage()` param decorator

A thin NestJS param decorator wrapping `getPreferredLanguage()`, usable in both GraphQL resolvers and REST controllers:

```ts
@Mutation(() => LoginResponse)
async login(
  @Args() input: LoginRequest,
  @AcceptLanguage() lang: SupportedLanguages | undefined,
) {
  return this.authnService.login(input, lang);
}
```

Service method signatures accept `preferredLanguage` as a plain parameter — no DTO destructuring required.

#### 4. Registration

`AcceptLanguageMiddleware` is registered in both `AppModule` implementations (`graphql-gateway` and `rest-gateway`) in the same `.apply()` chain as the other context-populating middlewares:

```ts
consumer
  .apply(
    RequestContextMiddleware,
    AuthorizationMiddleware,
    CookieMiddleware,
    CorrelationIdMiddleware,
    MarketIdMiddleware,
    AcceptLanguageMiddleware,   // ← last; depends on context being initialised
  )
  .forRoutes('*');
```

### Consequences

**Pros:**

- **Standard behaviour:** Clients use the `Accept-Language` header exactly as the HTTP spec intends. No custom field documentation is needed.
- **No schema leakage:** `preferredLanguage` is invisible to the GraphQL schema. The generated SDL has no knowledge of localisation infrastructure.
- **Clean service signatures:** Services accept `preferredLanguage` as a plain, optional parameter. The param decorator and helper eliminate all the DTO destructuring boilerplate.
- **Uniform guard/filter access:** Exception filters and auth guards call `getPreferredLanguage()` without any context-unwrapping logic. The same call works identically in GraphQL and REST contexts.
- **Single-responsibility:** `AcceptLanguageMiddleware` owns exactly one field (`preferredLanguage`) in the request context, consistent with the pattern established in ADR-004.

**Cons:**

- Developers adding a new resolver or controller must remember to add `@AcceptLanguage() lang` as a parameter if the downstream service requires it — there is no compile-time enforcement that it is passed.
- Clients relying on the old `preferredLanguage` DTO field must migrate to the `Accept-Language` header. This is a breaking change to the GraphQL schema for any deployed consumer.
