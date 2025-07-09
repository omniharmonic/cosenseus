"""
Civic Sense-Making Platform - API Gateway Service
Main entry point for the API gateway that routes requests to microservices
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from typing import Optional

from .core.config import get_settings
from .core.middleware import setup_middleware
from .core.database import init_db
from .routers import auth, events, users, health
from .core.security import verify_token

# Initialize FastAPI app
app = FastAPI(
    title="Civic Sense-Making Platform API",
    description="API Gateway for the Civic Sense-Making Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Get application settings
settings = get_settings()

# Security
security = HTTPBearer(auto_error=False)

# Setup middleware
setup_middleware(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Initialize database
init_db()

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(events.router)  # Events router already has /events prefix

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Civic Sense-Making Platform API Gateway",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/info")
async def info():
    """API information endpoint"""
    return {
        "name": "Civic Sense-Making Platform",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "auth": f"{settings.AUTH_SERVICE_URL}/health",
            "events": f"{settings.EVENT_SERVICE_URL}/health",
            "nlp": f"{settings.NLP_SERVICE_URL}/health",
            "profiles": f"{settings.PROFILE_SERVICE_URL}/health"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    ) 