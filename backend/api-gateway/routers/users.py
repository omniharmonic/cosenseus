"""
Users router for the API Gateway
Routes user-related requests to the profile service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import httpx
from sqlalchemy.orm import Session
from core.database_local import get_local_db, create_temporary_user, get_user_by_id

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/profile")
async def get_user_profile() -> Dict[str, Any]:
    """Get current user's profile"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.PROFILE_SERVICE_URL}/profile")
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Profile service unavailable"
            )

@router.put("/profile")
async def update_user_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update current user's profile"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{settings.PROFILE_SERVICE_URL}/profile",
                json=profile_data
            )
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Profile service unavailable"
            )

@router.get("/users/{user_id}/events")
async def get_user_events(user_id: str) -> Dict[str, Any]:
    """Get events associated with current user"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.EVENT_SERVICE_URL}/user/{user_id}/events")
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Event service unavailable"
            )

@router.post("/users/temporary")
def create_temp_user(db: Session = Depends(get_local_db)):
    user = create_temporary_user(db)
    return {"id": user.id, "is_temporary": user.is_temporary}

@router.get("/users/{user_id}")
def fetch_user(user_id: str, db: Session = Depends(get_local_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "is_temporary": user.is_temporary, "email": user.email, "username": user.username} 