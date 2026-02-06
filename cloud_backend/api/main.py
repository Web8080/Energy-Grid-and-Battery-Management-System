"""
Cloud Backend API Main Application

FastAPI application providing REST API endpoints for schedule management,
device management, and system health monitoring.

This is the entry point for the cloud backend service, handling HTTP
requests and coordinating with database, message queue, and other services.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from cloud_backend.api.routes import admin, auth, devices, health, ml, schedules
from cloud_backend.config.database import init_db
from cloud_backend.config.settings import get_settings
from cloud_backend.utils.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from cloud_backend.utils.rate_limiter import RateLimitMiddleware

logger = logging.getLogger(__name__)
settings = get_settings()

http_request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    logger.info("Starting cloud backend API")
    
    if settings.DEBUG:
        logger.warning("DEBUG mode is enabled - this should not be used in production")
    
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info("Shutting down cloud backend API")


app = FastAPI(
    title="Energy Grid Battery Management API",
    description="API for managing battery schedules and device fleet",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None
)

allowed_origins = settings.CORS_ORIGINS
if "*" in allowed_origins and settings.ENVIRONMENT == "production":
    logger.error("CORS wildcard (*) not allowed in production")
    allowed_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    expose_headers=["X-Correlation-ID"],
    max_age=3600
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CorrelationIdMiddleware)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect HTTP metrics."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request processing error: {e}", exc_info=True)
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An error occurred processing your request"}
        )
    
    duration = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code
    
    http_request_count.labels(
        method=method,
        endpoint=endpoint,
        status=status_code
    ).inc()
    
    http_request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    correlation_id = getattr(request.state, "correlation_id", None)
    
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An internal error occurred",
            "correlation_id": correlation_id
        }
    )


app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(ml.router, prefix="/ml", tags=["ml"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Energy Grid Battery Management API",
        "version": "1.0.0",
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "cloud_backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
