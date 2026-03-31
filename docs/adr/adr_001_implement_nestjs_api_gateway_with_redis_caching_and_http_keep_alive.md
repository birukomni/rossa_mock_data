## ADR-001: Implement NestJS API Gateway with Redis Caching and HTTP Keep-Alive
Date: 2026-03-13
Status: Accepted (Superseded in part by removal of manual proxy caching)

### Context
Our core Django backend contains complex business logic but is constrained by synchronous WSGI workers. As client traffic scales, handling massive amounts of concurrent I/O and translating complex GraphQL queries directly within Django risks worker starvation, high latency, and platform degradation. We need a way to shield the Django core from raw client load and optimize read-heavy operations.

### Decision
We will introduce a NestJS application to act as an API Gateway / Backend-For-Frontend (BFF).
1. NestJS will terminate client connections, validate payloads using strict DTOs, and translate GraphQL queries into REST calls.
2. We will implement a caching layer in NestJS using Redis via Apollo Server for GraphQL queries. (Note: Manual caching in the proxy layer was subsequently removed to simplify the architecture).
3. Communication between NestJS and Django will utilize Connection Pooling (`keepAlive: true`, `maxSockets: 100`) via Axios to eliminate TCP handshake overhead.

### Consequences
Pros:
- Massively offloads network I/O and connection management from Django workers.
- Drastically reduces latency for read-heavy operations via the Redis cache.
- Connection pooling minimizes internal network latency between the gateway and core.
- Isolates GraphQL schema management and payload validation from the core business logic.

Cons:
- Adds a new network hop for un-cached requests.
- Introduces operational complexity by adding a new service (NestJS) and datastore (Redis) to the deployment pipeline.
