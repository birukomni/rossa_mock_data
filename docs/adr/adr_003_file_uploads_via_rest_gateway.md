# ADR-003: File Uploads via REST Gateway (not GraphQL)

**Status:** Accepted
**Date:** 2026-03-25

---

## Context

The platform needs to support avatar and document uploads. The initial design considered routing uploads through the GraphQL gateway using the `graphql-multipart-request` spec. On investigation, this approach has several serious drawbacks that make it unsuitable for production use.

---

## Decision

All file upload operations are routed through the dedicated REST gateway (`rest-gateway`) using standard `multipart/form-data`. A new `FileUploadModule` in `libs/modules/file-upload/` owns the entire upload lifecycle: validation, storage, and downstream Django confirmation. The GraphQL gateway is not involved in file uploads at any level.

---

## Rationale

### 1. CSRF exposure

The `graphql-multipart-request` spec requires a CORS-preflight bypass via the `operations` and `map` fields. Apollo Server's multipart implementation is a known CSRF attack surface that requires explicit mitigation (`csrfPrevention: true`), adding operational overhead and non-obvious failure modes.

### 2. Apollo memory pressure

Parsing multipart streams in Apollo buffers the entire file in the GraphQL resolver layer. The GraphQL gateway is a thin middleware and should never hold multi-megabyte payloads in memory mid-request. This creates GC pressure and risks OOM errors under concurrent upload load.

### 3. Spec brittleness

The `graphql-upload` package is a community spec, not part of the GraphQL specification. Breaking changes between Apollo Server versions have repeatedly required manual shimming. Depending on it creates an ongoing maintenance burden.

### 4. Tooling incompatibility

Standard REST tooling (Postman, cURL, browser `fetch`) handles `multipart/form-data` natively. GraphQL multipart requires custom request construction and is poorly supported by most API testing tools.

### 5. Independent observability

REST file endpoints can be independently rate-limited, monitored, cached, and scaled without touching the GraphQL schema or its cache layer. Upload traffic has a fundamentally different profile (bursty, large payloads, slower) from API query traffic.

### 6. Separation of concerns

The GraphQL gateway expresses *intent* (queries and mutations over domain state). The REST gateway handles *side effects* with binary data. Keeping the full upload lifecycle — validate → store → confirm with Django → respond — in a single REST endpoint gives the client a clean, atomic request/response cycle with no multi-step coordination.

---

## Consequences

- **Atomic upload flow:** `POST /api/:version/files/avatar` validates the file, uploads to S3, PATCHes Django to confirm the new avatar URL, and returns a `StandardResponse`-shaped JSON body with the updated `ProfilePayloadDto`. The client makes one call and gets back the updated profile — no second round trip required.
- **Pluggable storage:** The `IStorageService` interface (injection token: `STORAGE_SERVICE`) ensures the storage provider is swappable. Switching from S3 to GCS requires only changing `STORAGE_PROVIDER=gcs` in the env file — no TypeScript changes.
- **File validation enforced at the pipe layer:** Size, MIME type, and file presence are validated in `FileValidationPipe` using the existing `MAX_REQUEST_FILE_SIZE` and `MAX_REQUEST_FILES` config values. Invalid files are rejected before any storage or Django calls are made.
- **GraphQL schema stays clean:** No upload mutations in the schema. `ProfilePayloadDto` remains a standard GraphQL ObjectType used for profile queries/mutations. The REST endpoint returns the same shape as JSON — consistent data model across both transports.
- **`FileUploadModule` is REST-gateway-only:** It is never imported into the `graphql-gateway` AppModule, avoiding GraphQL resolver conflicts and keeping the module boundary clear.
