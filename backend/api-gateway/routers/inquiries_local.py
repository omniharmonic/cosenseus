"""
Local Inquiries router for the API Gateway
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from core.database_local import get_local_db
from shared.models.database import Inquiry, Event
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/inquiries", tags=["inquiries"])

class InquiryResponse(BaseModel):
    id: str
    question_text: str
    description: Optional[str] = None
    response_type: str
    is_required: bool
    order_index: int

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True

@router.get("/event/{event_id}", response_model=List[InquiryResponse])
async def get_inquiries_for_event(
    event_id: str, 
    round_number: Optional[int] = None, 
    db: Session = Depends(get_local_db)
):
    """
    Get inquiries for a specific event.
    If round_number is provided, it filters inquiries for that round.
    If not, it defaults to the event's current active round.
    """
    query = db.query(Inquiry).filter(Inquiry.event_id == event_id)
    
    if round_number is not None:
        query = query.filter(Inquiry.round_number == round_number)
    else:
        # If no round number is provided, fetch for the event's current round.
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        query = query.filter(Inquiry.round_number == event.current_round)

    inquiries = query.order_by(Inquiry.order_index).all()
    if not inquiries:
        return []
    return inquiries 