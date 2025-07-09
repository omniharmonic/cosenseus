from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import sys

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Census Local Development Server...")
    
    # Initialize local database
    init_local_db()
    
    print("✅ Local database initialized")
    print("📊 API Documentation available at: http://localhost:8000/docs")
    print("🔗 Frontend should be running at: http://localhost:3000")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Census Local Development Server...")

# Create FastAPI app
app = FastAPI(
    title="Census Local Development API",
    description="Local development API for the Civic Sense-Making Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
        "message": "Census Local Development API",
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