"""
API Gateway Service for Daily Logger Assist

Central gateway that routes requests to appropriate microservices.
Handles authentication, rate limiting, and load balancing.
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import asyncio
import sys
import os
from typing import Optional
import logging

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.config.base import BaseConfig
from shared.utils.auth import init_auth, get_auth, TokenData
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Initialize configuration
config = BaseConfig()

# Initialize authentication
auth_manager = init_auth(config.SECRET_KEY, config.REDIS_URL)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist - API Gateway",
    description="Central API Gateway for Daily Logger Assist microservices",
    version="1.0.0"
)

# Add middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS if config.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Service URLs mapping
SERVICE_URLS = {
    "user": config.USER_SERVICE_URL,
    "data": config.DATA_COLLECTION_SERVICE_URL,
    "ai": config.AI_PROCESSING_SERVICE_URL,
    "reports": config.REPORTING_SERVICE_URL,
    "notifications": config.NOTIFICATION_SERVICE_URL,
    "data-sources": config.DATA_SOURCE_SERVICE_URL,
}

# HTTP client for service communication
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[TokenData]:
    """Get current user from JWT token"""
    if not credentials:
        return None
    
    token_data = auth_manager.verify_token(credentials.credentials)
    return token_data

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Require authentication for protected endpoints"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = auth_manager.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

async def forward_request(
    service_name: str,
    path: str,
    method: str,
    request: Request,
    token_data: Optional[TokenData] = None
):
    """Forward request to appropriate microservice"""
    if service_name not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    service_url = SERVICE_URLS[service_name]
    url = f"{service_url}{path}"
    
    # Prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    # Add user context if authenticated
    if token_data:
        headers["X-User-ID"] = token_data.user_id
        headers["X-User-Email"] = token_data.email
        headers["X-User-Scopes"] = ",".join(token_data.scopes)
    
    try:
        # Get request body
        body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params
        )
        
        # Prepare response headers
        response_headers = dict(response.headers)
        response_headers.pop("content-length", None)  # Let FastAPI handle content length
        
        # Return response based on content type
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                content = response.json()
                return JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers=response_headers
                )
            except Exception:
                # Fallback to text if JSON parsing fails
                return JSONResponse(
                    content={"error": "Invalid JSON response"},
                    status_code=response.status_code,
                    headers=response_headers
                )
        else:
            # For non-JSON responses, return as text
            return JSONResponse(
                content={"message": response.text},
                status_code=response.status_code,
                headers=response_headers
            )
        
    except httpx.RequestError as e:
        logging.error(f"Error forwarding request to {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service {service_name} unavailable"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Service error: {e.response.text}"
        )

# Health check endpoint
@app.get("/health")
@limiter.limit(f"{config.RATE_LIMIT_REQUESTS}/hour")
async def health_check(request: Request):
    """Gateway health check"""
    service_health = {}
    
    # Create a separate client for health checks
    async with httpx.AsyncClient(timeout=10.0, limits=httpx.Limits(max_connections=10)) as health_client:
        # Check all services
        for service_name, service_url in SERVICE_URLS.items():
            try:
                response = await health_client.get(f"{service_url}/health", timeout=5.0)
                service_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                logging.error(f"Health check failed for {service_name}: {e}")
                service_health[service_name] = {
                    "status": "unreachable",
                    "response_time": None
                }
    
    overall_status = "healthy" if all(
        s["status"] == "healthy" for s in service_health.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "service": "API Gateway",
        "version": "1.0.0",
        "services": service_health
    }

# Authentication routes (public)
@app.post("/api/v1/auth/{path:path}")
@limiter.limit("10/minute")
async def auth_routes(path: str, request: Request):
    """Forward authentication requests to user service"""
    return await forward_request("user", f"/api/v1/auth/{path}", request.method, request)

# User management routes (require auth)
@app.api_route("/api/v1/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def user_routes(path: str, request: Request, user: TokenData = Depends(require_auth)):
    """Forward user management requests to user service"""
    return await forward_request("user", f"/api/v1/users/{path}", request.method, request, user)

# Data collection routes (require auth)
@app.api_route("/api/v1/data/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def data_routes(path: str, request: Request, user: TokenData = Depends(require_auth)):
    """Forward data collection requests to data collection service"""
    return await forward_request("data", f"/api/v1/data/{path}", request.method, request, user)

# AI processing routes (require auth)
@app.api_route("/api/v1/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def ai_routes(path: str, request: Request, user: TokenData = Depends(require_auth)):
    """Forward AI processing requests to AI processing service"""
    return await forward_request("ai", f"/api/v1/ai/{path}", request.method, request, user)

# Reporting routes (require auth)
@app.api_route("/api/v1/reports/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def report_routes(path: str, request: Request, user: TokenData = Depends(require_auth)):
    """Forward reporting requests to reporting service"""
    return await forward_request("reports", f"/api/v1/reports/{path}", request.method, request, user)

# Notification routes (require auth)
@app.api_route("/api/v1/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def notification_routes(path: str, request: Request, user: TokenData = Depends(require_auth)):
    """Forward notification requests to notification service"""
    return await forward_request("notifications", f"/api/v1/notifications/{path}", request.method, request, user)

# Data Source routes (require auth)
@app.api_route("/api/v1/data-sources", methods=["GET", "POST"])
async def data_sources_root(request: Request, user: TokenData = Depends(require_auth)):
    """Handle root data sources endpoint"""
    return await forward_request("data-sources", "/api/v1/data-sources", request.method, request, user)

@app.api_route("/api/v1/data-sources/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def data_source_routes(path: str, request: Request, user: TokenData = Depends(require_auth)):
    """Forward data source requests to data source service"""
    return await forward_request("data-sources", f"/api/v1/data-sources/{path}", request.method, request, user)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Daily Logger Assist API Gateway",
        "documentation": "/docs",
        "health": "/health",
        "version": "1.0.0",
        "services": list(SERVICE_URLS.keys())
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logging.info("API Gateway starting...")
    logging.info(f"Environment: {config.ENVIRONMENT}")
    logging.info(f"Services: {list(SERVICE_URLS.keys())}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    await http_client.aclose()
    logging.info("API Gateway shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 