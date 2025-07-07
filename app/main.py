"""
Daily Logger Assist - FastAPI Main Application

Entry point for the Daily Logger Assist FastAPI application.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn

from app.config import settings
from app.api import auth, data, reports, admin
from app.database.connection import engine
from app.models import Base

# Create FastAPI instance
app = FastAPI(
    title="Daily Logger Assist API",
    description="Intelligent daily status update automation for JIRA tickets",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(data.router, prefix="/api/v1/data", tags=["Data Management"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Daily Logger Assist API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 