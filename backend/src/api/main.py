"""FastAPI application entrypoint for ClauseLens.

Provides CORS configuration, centralized exception handlers,
and registers document ingestion and hybrid query routers.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.src.api.routes import documents, query
from backend.src.config import get_settings
from backend.src.exceptions import ClauseLensError

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("clauselens.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan handler."""
    settings = get_settings()
    logger.info("Starting ClauseLens API in '%s' environment...", settings.app_env)
    yield
    logger.info("Shutting down ClauseLens API...")


app = FastAPI(
    title="ClauseLens API",
    description="Enterprise-grade Document Intelligence and Contract Analysis RAG Engine.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ClauseLensError)
async def domain_exception_handler(request: Request, exc: ClauseLensError) -> JSONResponse:
    """Centralized handler for custom ClauseLens domain exceptions."""
    logger.error("Domain exception on %s: %s (details: %s)", request.url.path, exc.message, exc.details)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_type": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
        },
    )


# Mount routers
app.include_router(documents.router, prefix="/api")
app.include_router(query.router, prefix="/api")


@app.get("/health", tags=["system"], summary="Service health check")
def health_check() -> dict[str, str]:
    """Return service health status and timestamp."""
    return {
        "status": "healthy",
        "service": "ClauseLens API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

