"""MemberBridge API — FastAPI entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from config import settings
from routers import webhooks, workspace, integrations, members, automations, events, dashboard

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"MemberBridge API starting — env={settings.environment}")
    yield
    print("MemberBridge API shutting down")


app = FastAPI(
    title="MemberBridge API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(webhooks.router,     prefix=PREFIX)
app.include_router(workspace.router,    prefix=PREFIX)
app.include_router(integrations.router, prefix=PREFIX)
app.include_router(members.router,      prefix=PREFIX)
app.include_router(automations.router,  prefix=PREFIX)
app.include_router(events.router,       prefix=PREFIX)
app.include_router(dashboard.router,    prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "memberbridge-api"}
