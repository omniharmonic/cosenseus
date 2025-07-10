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

from core.database_local import get_local_db, LocalSessionLocal
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
    role: str  # Include role in the response
    created_at: datetime

    class Config:
        from_attributes = True


def get_current_user(session_code: str = Header(..., alias="X-Session-Code")):
    """
    Dependency to get the current user from the session code in the header.
    This now manually manages its own database session to ensure consistency.
    """
    db = LocalSessionLocal()
    try:
        print(f"🔍 Validating session code from header: {session_code}")
        if not session_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Header"},
            )
        
        user = db.query(TemporaryUser).filter(TemporaryUser.session_code == session_code).first()
        
        if not user:
            print(f"❌ Session code not found in database: {session_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session code",
                headers={"WWW-Authenticate": "Header"},
            )
        
        print(f"✅ Session validated for user: {user.display_name}")
        return user
    finally:
        db.close()

@router.post("/session/create", response_model=TemporaryUserResponse, status_code=status.HTTP_201_CREATED)
def create_session(request: CreateSessionRequest):
    """
    Creates a new temporary user. The first user created is an admin.
    Manually manages the DB session for guaranteed commit.
    """
    db = LocalSessionLocal()
    try:
        if not request.display_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Display name cannot be empty."
            )

        # Check if this is the first user
        is_first_user = db.query(TemporaryUser).first() is None
        user_role = 'admin' if is_first_user else 'user'
        
        new_user = TemporaryUser(
            display_name=request.display_name,
            role=user_role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✨ New session created. User: {new_user.display_name}, Role: {new_user.role}, Session Code: {new_user.session_code}")
        
        # --- DIAGNOSTIC STEP ---
        # Immediately try to read the user back from the DB to verify the commit.
        print(f"🔬 Verifying persistence for session code: {new_user.session_code}")
        verified_user = db.query(TemporaryUser).filter(TemporaryUser.session_code == new_user.session_code).first()
        if verified_user:
            print(f"✅ User successfully read back from DB. Display Name: {verified_user.display_name}")
        else:
            print(f"❌ CRITICAL: User could NOT be read back from DB immediately after commit.")
        # --- END DIAGNOSTIC STEP ---
        
        # Return a Pydantic model instance, not the ORM object, as the session is closed.
        return TemporaryUserResponse.from_orm(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    finally:
        db.close()


@router.post("/session/login", response_model=TemporaryUserResponse)
def login_with_session_code(request: LoginRequest):
    """
    Logs in a user. Manually manages the DB session for guaranteed lookup.
    """
    db = LocalSessionLocal()
    try:
        user = db.query(TemporaryUser).filter(TemporaryUser.session_code == request.session_code).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session code not found."
            )
        
        return TemporaryUserResponse.from_orm(user)
    finally:
        db.close() 