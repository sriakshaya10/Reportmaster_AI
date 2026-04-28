from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Financial reporting manual retrieval assistant powered by RAG",
)

# API routes FIRST (highest priority)
app.include_router(router, prefix=settings.api_v1_prefix)

# Static assets (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

# Frontend SPA at root (lowest priority fallback) - serves index.html for all routes
app.mount("/", StaticFiles(directory="app/frontend", html=True), name="frontend")
