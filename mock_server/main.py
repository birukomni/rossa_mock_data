"""
FastAPI application entry point.
Mounts: GraphQL at /graphql, REST upload at /api/{version}/files/avatar, health at /health.
"""
from __future__ import annotations
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from mock_server.schema import schema
# from mock_server.rest.upload import router as upload_router
# from mock_server.rest.restaurants import router as restaurants_router
# from mock_server.rest.catalog import router as catalog_router
# from mock_server.rest.menu import router as menu_router
# from mock_server.rest.orders import router as orders_router
from mock_server.rest.operator_profile import router as operator_profile_router


async def get_context(request: Request) -> dict:
    return {"request": request}


app = FastAPI(
    title="Rossa Mock Server",
    description="Mock GraphQL + REST server implementing all RoSSA Experience API DDTs.",
    version="1.0.0",
    docs_url="/docs",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
cors_origins = ["*"] if cors_origins_env.strip() == "*" else [
    o.strip() for o in cors_origins_env.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── GraphQL ───────────────────────────────────────────────────────────────────
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

# ── REST ──────────────────────────────────────────────────────────────────────
# app.include_router(upload_router)
# app.include_router(restaurants_router)
# app.include_router(catalog_router)
# app.include_router(menu_router)
# app.include_router(orders_router)
app.include_router(operator_profile_router)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "rossa-mock-server"}


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "4000"))
    uvicorn.run("mock_server.main:app", host="0.0.0.0", port=port, reload=True)
