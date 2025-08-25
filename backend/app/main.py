import logging, time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .db import init_db, get_db
from .jwt_utils import parse_token
from .auth import router as auth_router
from .sync import router as sync_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 Starting Budget PWA Backend...")
    await init_db()
    log.info("✅ Database initialized")
    yield

app = FastAPI(title="Budget PWA API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# Простая аутентификация через Authorization header → request.state.claims
@app.middleware("http")
async def auth_context(request: Request, call_next):
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
        try:
            request.state.claims = parse_token(token)
        except Exception:
            request.state.claims = None
    else:
        request.state.claims = None
    return await call_next(request)

@app.get("/api/health")
async def health(db = get_db):
    status = {"api": "healthy", "database": "healthy"}
    try:
        async for conn in db:
            await conn.execute("SELECT 1")
            await conn.commit()
    except Exception:
        status["database"] = "unhealthy"
    return {"status": "ok" if status["database"]=="healthy" else "unhealthy",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "version": "1.0.0",
            "services": status}

@app.get("/api/auth/me")
async def me(request: Request):
    if not request.state.claims:
        raise HTTPException(403, "Not authenticated")
    return {"user_id": request.state.claims["uid"], "email": request.state.claims["eml"]}

app.include_router(auth_router)
app.include_router(sync_router)