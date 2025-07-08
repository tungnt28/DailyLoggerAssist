"""
Daily Logger Assist - Main Application

FastAPI application for automated daily work tracking with AI-powered
JIRA integration, Teams/Email data collection, and productivity analytics.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database.connection import init_db
from app.api import auth, data, reports, admin, ai

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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")  # Phase 3: Enhanced AI Processing

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "Daily Logger Assist",
        "version": "1.0.0",
        "phase": "5",
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
            "Docker & Container Support"
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