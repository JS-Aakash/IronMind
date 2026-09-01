from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.backend.app.api.v1.router import api_router
from apps.backend.app.core.config import settings
from apps.backend.app.core.errors import register_error_handlers
from apps.backend.app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Setup structured logging
    setup_logging()
    
    # Ensure all local storage directories exist
    for dir_path in [
        settings.STORAGE_UPLOADS_DIR,
        settings.STORAGE_KNOWLEDGE_DIR,
        settings.STORAGE_ARTIFACTS_DIR,
        settings.STORAGE_TEMP_DIR,
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work (MRPL).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Configure CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register centralized error handlers
register_error_handlers(app)

# Include API v1 router under /api/v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root level /health endpoint for fast health checks
@app.get("/health", tags=["Health & System"])
async def root_health():
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": "Sovereign On-Premise Airgap",
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "sovereignty": "100% Local On-Premise",
    }
