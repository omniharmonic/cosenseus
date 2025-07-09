"""
Authentication router for the API Gateway
Handles session-based temporary user creation and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
import sys
import os
from datetime import datetime
import uuid

from core.database_local import get_local_db
from shared.models.database import TemporaryUser

router = APIRouter()

# Pydantic models for request bodies
class CreateSessionRequest(BaseModel):
    display_name: str

class LoginRequest(BaseModel):
    session_code: str

# Pydantic model for the response to avoid serialization issues
class TemporaryUserResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    session_code: str
    created_at: datetime

    class Config:
        from_attributes = True


def get_current_user(session_code: str = Header(..., alias="X-Session-Code"), db: Session = Depends(get_local_db)):
    """
    Dependency to get the current user from the session code in the header.
    """
    if not session_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Header"},
        )
    
    user = db.query(TemporaryUser).filter(TemporaryUser.session_code == session_code).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session code",
            headers={"WWW-Authenticate": "Header"},
        )
        
    return user

@router.post("/session/create", response_model=TemporaryUserResponse, status_code=status.HTTP_201_CREATED)
def create_session(request: CreateSessionRequest, db: Session = Depends(get_local_db)):
    """
    Creates a new temporary user and returns their session information.
    """
    print(f"Received request to create session for: {request.display_name}")
    
    if not request.display_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display name cannot be empty."
        )
    
    new_user = TemporaryUser(display_name=request.display_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/session/login", response_model=TemporaryUserResponse)
def login_with_session_code(request: LoginRequest, db: Session = Depends(get_local_db)):
    """
    Logs in a user using their persistent session code.
    """
    user = db.query(TemporaryUser).filter(TemporaryUser.session_code == request.session_code).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session code not found."
        )
        
    return user 