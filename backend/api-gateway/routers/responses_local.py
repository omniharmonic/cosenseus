"""
Local Responses router for the API Gateway - Simplified for SQLite
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from core.database_local import get_local_db
from shared.models.database import Inquiry, Response, ProcessingStatus, Event, TemporaryUser
from pydantic import BaseModel, Field
from routers.auth import get_current_user

router = APIRouter(prefix="/responses", tags=["responses"])

class ResponseSubmission(BaseModel):
    inquiry_id: str = Field(..., description="ID of the inquiry being responded to")
    content: str = Field(..., min_length=1, max_length=50000, description="Response content")
    is_anonymous: bool = Field(default=False, description="Submit as anonymous")
    round_number: int = Field(default=1, ge=1, description="Event round number")

class ResponseResponse(BaseModel):
    id: str
    event_id: str
    inquiry_id: str
    user_id: Optional[str]
    content: str
    response_type: str
    processing_status: str
    is_anonymous: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", status_code=201)
async def create_response(
    response_data: ResponseSubmission,
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """Create a new response to an inquiry."""
    try:
        inquiry = db.query(Inquiry).filter(Inquiry.id == response_data.inquiry_id).first()
        if not inquiry:
            raise HTTPException(status_code=404, detail="Inquiry not found")

        new_response = Response(
            event_id=inquiry.event_id,
            inquiry_id=response_data.inquiry_id,
            user_id=current_user.id if not response_data.is_anonymous else None,
            content=response_data.content,
            is_anonymous=response_data.is_anonymous,
            round_number=response_data.round_number,
            processing_status=ProcessingStatus.PENDING,
        )
        
        db.add(new_response)
        db.commit()
        db.refresh(new_response)
        
        return {"id": str(new_response.id), "status": "created", "content": response_data.content}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating response: {str(e)}")

@router.get("/", response_model=List[ResponseResponse])
async def list_responses(
    event_id: Optional[str] = None,
    inquiry_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_local_db)
):
    """List responses with filtering and pagination."""
    query = db.query(Response)
    if event_id:
        query = query.filter(Response.event_id == event_id)
    if inquiry_id:
        query = query.filter(Response.inquiry_id == inquiry_id)
    
    responses = query.order_by(Response.created_at.desc()).offset(skip).limit(limit).all()
    return responses

@router.get("/{response_id}", response_model=ResponseResponse)
async def get_response(
    response_id: str,
    db: Session = Depends(get_local_db)
):
    """Get a specific response by ID."""
    response = db.query(Response).filter(Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response

@router.get("/event/{event_id}/responses")
async def get_event_responses(
    event_id: str,
    db: Session = Depends(get_local_db)
):
    """Get all responses for a specific event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    responses = db.query(Response).filter(Response.event_id == event_id).order_by(Response.created_at.desc()).all()
    
    return {
        "event_id": event_id,
        "responses": responses,
        "total_count": len(responses)
    }

@router.post("/batch", status_code=201)
async def submit_round_responses(
    responses: List[ResponseSubmission],
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """Submit multiple responses for a round."""
    submitted_responses = []
    for response_data in responses:
        inquiry = db.query(Inquiry).filter(Inquiry.id == response_data.inquiry_id).first()
        if not inquiry:
            # Maybe we should collect errors and continue? For now, fail fast.
            raise HTTPException(status_code=404, detail=f"Inquiry with id {response_data.inquiry_id} not found.")

        new_response = Response(
            event_id=inquiry.event_id,
            inquiry_id=response_data.inquiry_id,
            user_id=current_user.id if not response_data.is_anonymous else None,
            content=response_data.content,
            is_anonymous=response_data.is_anonymous,
            round_number=response_data.round_number,
            processing_status=ProcessingStatus.PENDING
        )
        db.add(new_response)
        submitted_responses.append(new_response)

    db.commit()
    for res in submitted_responses:
        db.refresh(res)
        
    return {"message": "Batch responses submitted successfully", "count": len(submitted_responses), "responses": submitted_responses} 