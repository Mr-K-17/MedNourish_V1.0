"""MEDNOURISH FastAPI Application Entry Point.

Phase 1A Foundation & Safety Shell Scaffold.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.health import router as health_router
from app.api.v1.profile import router as profile_router
from app.api.v1.explorer import router as explorer_router
from app.api.v1.reports import router as reports_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Educational prototype exploring nutritional deficiency reference matching.",
)

# Local development CORS policy for frontend Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned API routes under /v1
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(profile_router, prefix=settings.API_V1_STR, tags=["Profile"])
app.include_router(explorer_router, prefix=settings.API_V1_STR, tags=["Explorer"])
app.include_router(reports_router, prefix=settings.API_V1_STR, tags=["Reports"])


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "disclaimer": settings.EDUCATIONAL_PROTOTYPE_DISCLAIMER,
        "docs_url": "/docs",
    }
