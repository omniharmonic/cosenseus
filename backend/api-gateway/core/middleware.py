"""
Middleware setup for the API Gateway
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog
from prometheus_client import Counter, Histogram, generate_latest
import uuid

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Update metrics
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        # Log response
        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_seconds=round(duration, 3)
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time() / 60)  # Current minute
        
        # Clean old entries
        self.request_counts = {
            key: value for key, value in self.request_counts.items()
            if key[1] >= current_time - 1
        }
        
        # Count requests for this IP in current minute
        current_requests = sum(
            count for (ip, minute), count in self.request_counts.items()
            if ip == client_ip and minute == current_time
        )
        
        if current_requests >= self.requests_per_minute:
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"}
            )
        
        # Increment counter
        key = (client_ip, current_time)
        self.request_counts[key] = self.request_counts.get(key, 0) + 1
        
        return await call_next(request)

def setup_middleware(app: FastAPI):
    """Set up all middleware for the application"""
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        ) 