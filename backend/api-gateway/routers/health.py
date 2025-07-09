"""
Health check router for the API Gateway service
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import asyncio
import httpx
import time
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-gateway",
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check that verifies all dependencies are available"""
    start_time = time.time()
    
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "auth_service": await check_service(settings.AUTH_SERVICE_URL),
        "event_service": await check_service(settings.EVENT_SERVICE_URL),
        "nlp_service": await check_service(settings.NLP_SERVICE_URL),
        "profile_service": await check_service(settings.PROFILE_SERVICE_URL)
    }
    
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    
    response_time = time.time() - start_time
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-gateway",
        "checks": checks,
        "response_time_seconds": round(response_time, 3)
    }

@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-gateway"
    }

async def check_database() -> Dict[str, Any]:
    """Check PostgreSQL database connectivity"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database error: {str(e)}"}

async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return {"status": "healthy", "message": "Redis connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Redis error: {str(e)}"}

async def check_service(service_url: str) -> Dict[str, Any]:
    """Check microservice health"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            if response.status_code == 200:
                return {"status": "healthy", "message": f"Service {service_url} is healthy"}
            else:
                return {"status": "unhealthy", "message": f"Service {service_url} returned {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Service {service_url} error: {str(e)}"} 