from contextlib import asynccontextmanager
from collections import defaultdict, deque
from time import monotonic
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routers import health, users, properties, tokens
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app=FastAPI(title="LandChain Real Estate Tokenization Platform", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

class PublicDemoWriteLimit:
    """Small per-client POST limit for the single-instance public test demo."""
    def __init__(self, app, limit: int, window_seconds: int = 60):
        self.app = app
        self.limit = max(1, limit)
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.next_cleanup = monotonic() + window_seconds

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] == "POST" and scope["path"].startswith("/api/"):
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"
            now = monotonic()
            if now >= self.next_cleanup:
                for ip, queue in list(self.requests.items()):
                    if not queue or now - queue[-1] >= self.window_seconds:
                        self.requests.pop(ip, None)
                self.next_cleanup = now + self.window_seconds
            timestamps = self.requests[client_ip]
            while timestamps and now - timestamps[0] >= self.window_seconds:
                timestamps.popleft()
            if len(timestamps) >= self.limit:
                response = JSONResponse({"detail": "Too many write requests. Please wait a minute and try again."}, status_code=429)
                await response(scope, receive, send)
                return
            timestamps.append(now)
        await self.app(scope, receive, send)

app.add_middleware(PublicDemoWriteLimit, limit=settings.public_demo_posts_per_minute)
for router in (health.router,users.router,properties.router,tokens.router): app.include_router(router,prefix="/api")
@app.get("/")
def root(): return {"name":"LandChain API","docs":"/docs"}
