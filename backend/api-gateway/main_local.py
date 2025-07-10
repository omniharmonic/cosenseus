from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import sys
import socket
import ipaddress

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.config import get_settings
settings = get_settings()

# Import routers
from routers.health import router as health_router
from routers.events_local import router as events_router  # Use local events router
from routers.ai_analysis_local import router as ai_analysis_router
from routers.responses_local import router as responses_router  # Use local responses router
from routers.users import router as users_router
from routers.auth import router as auth_router
from routers.inquiries_local import router as inquiries_router # Add new inquiries router

# Import local database initialization
from core.database_local import init_local_db

def get_local_network_origins():
    """Generate CORS origins for local network access"""
    origins = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000"
    ]
    
    try:
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        origins.append(f"http://{local_ip}:3000")
        
        # Add common local network ranges
        network_ranges = [
            "192.168.0.0/16",  # 192.168.x.x
            "10.0.0.0/8",      # 10.x.x.x  
            "172.16.0.0/12"    # 172.16.x.x - 172.31.x.x
        ]
        
        for network_str in network_ranges:
            network = ipaddress.IPv4Network(network_str, strict=False)
            # Add a few common IPs from each range
            for i in [1, 2, 100, 101, 254]:
                try:
                    test_ip = str(network.network_address + i)
                    origins.append(f"http://{test_ip}:3000")
                except:
                    continue
                    
    except Exception as e:
        print(f"Warning: Could not determine local network IPs: {e}")
    
    return origins

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting cosenseus Local Development Server...")
    
    # Initialize local database
    init_local_db()
    
    print("✅ Local database initialized")
    print("📊 API Documentation available at: http://localhost:8000/docs")
    print("🔗 Frontend should be running at: http://localhost:3000")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down cosenseus Local Development Server...")

# Create FastAPI app
app = FastAPI(
    title="cosenseus Local Development API",
    description="API for local development of the cosenseus platform, using SQLite and local AI models.",
    version="0.2.0",
    lifespan=lifespan
)

# Add CORS middleware with local network support  
local_origins = get_local_network_origins()
print(f"🌐 CORS enabled for origins: {local_origins[:5]}... ({len(local_origins)} total)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=local_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")  # Use local events router
app.include_router(ai_analysis_router, prefix="/api/v1")
app.include_router(responses_router, prefix="/api/v1")  # Use local responses router
app.include_router(users_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth") # Add /auth prefix
app.include_router(inquiries_router, prefix="/api/v1") # Add new inquiries router

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "cosenseus Local Development API",
        "version": "1.0.0",
        "environment": "local",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    print("🌐 Starting local development server...")
    uvicorn.run(
        "main_local:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    ) 