"""Main FastAPI application"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.startup_checks import run_startup_checks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    logger.info("Starting application...")
    checks_passed = await run_startup_checks()
    if not checks_passed:
        logger.warning("Some startup checks failed, but continuing anyway...")

    yield

    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies external dependencies

    Returns:
        200: All services are healthy
        503: One or more services are unhealthy
    """
    from fastapi.responses import JSONResponse
    from app.core.startup_checks import check_database, check_victoria_metrics

    checks = {}
    all_healthy = True

    # Check database
    db_success, db_msg = check_database()
    checks["database"] = {"status": "healthy" if db_success else "unhealthy", "message": db_msg}
    if not db_success:
        all_healthy = False

    # Check Victoria Metrics
    vm_success, vm_msg = await check_victoria_metrics()
    checks["victoria_metrics"] = {
        "status": "healthy" if vm_success else "unhealthy",
        "message": vm_msg,
    }
    if not vm_success:
        all_healthy = False

    response_data = {"status": "healthy" if all_healthy else "unhealthy", "checks": checks}

    # Return 503 if any check failed
    status_code = 200 if all_healthy else 503

    return JSONResponse(content=response_data, status_code=status_code)
