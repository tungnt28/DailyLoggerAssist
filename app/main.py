"""
Daily Logger Assist - Main Application

FastAPI application for automated daily work tracking with AI-powered
JIRA integration, Teams/Email data collection, and productivity analytics.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import traceback
import time

from app.config import settings
from app.database.connection import init_db
from app.api import auth, data, reports, admin, ai

# Initialize Sentry for error tracking in production
if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist",
    description="Intelligent daily work tracking system with AI-powered JIRA automation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if settings.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "status_code": 422
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    error_id = f"error_{int(time.time())}"
    logger.error(f"Unhandled exception [{error_id}]: {str(exc)} - {request.url}")
    logger.error(f"Traceback [{error_id}]: {traceback.format_exc()}")
    
    # In development, return detailed error info
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Internal server error: {str(exc)}",
                "error_id": error_id,
                "traceback": traceback.format_exc().split('\n'),
                "status_code": 500
            }
        )
    
    # In production, return generic error
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": error_id,
            "status_code": 500
        }
    )

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")  # Phase 3: Enhanced AI Processing

# Health check endpoint with rate limiting
@app.get("/health")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/hour")
async def health_check(request: Request):
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "Daily Logger Assist",
        "version": "1.0.0",
        "phase": "5",
        "environment": settings.ENVIRONMENT,
        "features": [
            "Authentication & User Management",
            "Data Collection (Teams, Email, JIRA)",
            "Background Task Processing",
            "Enhanced AI Content Analysis",
            "Intelligent Task Categorization", 
            "Advanced Time Estimation",
            "Automated JIRA Work Logging",
            "Productivity Analytics",
            "Comprehensive Report Generation",
            "Daily & Weekly Reports",
            "JIRA Updates Integration",
            "Report Templates & Analytics",
            "Comprehensive Testing Framework",
            "Performance & Security Testing",
            "Production Deployment Configuration",
            "Monitoring & Logging Integration",
            "Docker & Container Support",
            "Global Error Handling",
            "Rate Limiting",
            "Security Hardening"
        ]
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Daily Logger Assist API",
        "documentation": "/docs",
        "health": "/health",
        "version": "1.0.0",
        "phase": "5 - Production-Ready with Testing & Deployment"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("Daily Logger Assist application starting...")
    logger.info("Phase 5: Production-Ready with Comprehensive Testing & Deployment")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"OpenAPI documentation available at: /docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Daily Logger Assist application shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 