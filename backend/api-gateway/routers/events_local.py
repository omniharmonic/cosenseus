"""
Local Events router for the API Gateway - Simplified for SQLite
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from core.database_local import get_local_db
from shared.models.database import Event, Inquiry, TemporaryUser, EventParticipant, EventStatus, EventRound, EventRoundStatus, Synthesis, Response
from .auth import get_current_user
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/events", tags=["events"])

class InquiryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    inquiry_type: str = Field(default="open_ended")
    required: bool = Field(default=True)
    order_index: int = Field(default=0)

class InquiryResponse(BaseModel):
    id: str
    question_text: str
    description: Optional[str] = None
    response_type: str
    is_required: bool
    order_index: int
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    event_type: str = Field(default="discussion")
    max_participants: Optional[int] = Field(default=None, ge=1)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_public: bool = Field(default=True)
    allow_anonymous: bool = Field(default=False)
    inquiries: List[InquiryCreate] = Field(default=[])
    session_code: str

class EventResponse(BaseModel):
    id: str
    title: str
    description: str
    event_type: str
    status: str
    max_participants: Optional[int]
    current_participants: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_public: bool
    allow_anonymous: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    inquiries: List[InquiryResponse] = []

    class Config:
        from_attributes = True

class EventSummary(BaseModel):
    id: str
    title: str
    description: str
    event_type: str
    status: str
    current_participants: int
    max_participants: Optional[int]
    start_time: Optional[datetime]
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    organized_events: List[EventSummary]
    participating_events: List[EventSummary]

class ResponseModel(BaseModel):
    id: str
    inquiry_id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RoundStateResponse(BaseModel):
    current_round: int
    status: str

class SynthesisResponse(BaseModel):
    id: str
    round_number: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class RoundResultsResponse(BaseModel):
    round_number: int
    synthesis: Optional[SynthesisResponse]
    # TODO: Add analysis results here when available

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_events(
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """Get all events for the current user's dashboard."""
    # Get events organized by the user
    organized_events = db.query(Event).filter(Event.organizer_id == current_user.id).all()
    
    # Get events the user is participating in
    participating_events_query = db.query(Event).join(EventParticipant, Event.id == EventParticipant.event_id).filter(EventParticipant.user_id == current_user.id)
    participating_events = participating_events_query.all()
    
    organized_summaries = [EventSummary(
        id=str(e.id),
        title=e.title,
        description=e.description,
        event_type=e.event_type,
        status=e.status.value,
        current_participants=len(e.participants),
        max_participants=e.max_participants,
        start_time=e.start_time,
        is_public=e.is_public,
        created_at=e.created_at
    ) for e in organized_events]

    participating_summaries = [EventSummary(
        id=str(e.id),
        title=e.title,
        description=e.description,
        event_type=e.event_type,
        status=e.status.value,
        current_participants=len(e.participants),
        max_participants=e.max_participants,
        start_time=e.start_time,
        is_public=e.is_public,
        created_at=e.created_at
    ) for e in participating_events]

    return DashboardResponse(
        organized_events=organized_summaries,
        participating_events=participating_summaries
    )

@router.get("/{event_id}/responses", response_model=List[ResponseModel])
async def get_event_responses(event_id: str, db: Session = Depends(get_local_db)):
    """Get all responses for a specific event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    responses = db.query(Response).join(Inquiry).filter(Inquiry.event_id == event_id).all()
    return responses

@router.get("/", response_model=List[EventSummary])
async def list_events(
    db: Session = Depends(get_local_db),
    skip: int = 0,
    limit: int = 100
):
    events = db.query(Event).offset(skip).limit(limit).all()
    return [
        EventSummary(
            id=str(e.id),
            title=e.title,
            description=e.description,
            event_type=e.event_type,
            status=e.status.value,
            current_participants=len(e.participants),
            max_participants=e.max_participants,
            start_time=e.start_time,
            is_public=e.is_public,
            created_at=e.created_at
        ) for e in events
    ]

@router.get("/{event_id}/round-state", response_model=RoundStateResponse)
async def get_event_round_state(event_id: str, db: Session = Depends(get_local_db)):
    """Get the current round state for an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    current_round = db.query(EventRound).filter(
        EventRound.event_id == event_id,
        EventRound.round_number == event.current_round
    ).first()
    
    if not current_round:
        # If no round exists, assume round 1 is open
        return {
            "current_round": 1,
            "status": EventRoundStatus.WAITING_FOR_RESPONSES.value
        }

    return {
        "current_round": event.current_round,
        "status": current_round.status.value
    }


@router.get("/{event_id}/round-results", response_model=RoundResultsResponse)
async def get_event_round_results(event_id: str, round_number: Optional[int] = None, db: Session = Depends(get_local_db)):
    """Get the analysis and synthesis results for a specific round of an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    target_round = round_number if round_number is not None else event.current_round - 1
    
    if target_round < 1:
        raise HTTPException(status_code=400, detail="No results available for this round.")

    synthesis = db.query(Synthesis).filter(
        Synthesis.event_id == event_id,
        Synthesis.round_number == target_round
    ).first()

    return {
        "round_number": target_round,
        "synthesis": synthesis
    }

@router.post("/{event_id}/next-round", status_code=202)
async def advance_to_next_round(
    event_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """Admin-only endpoint to end the current round and start the next."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event organizer can advance rounds.")

    current_round_db = db.query(EventRound).filter_by(event_id=event_id, round_number=event.current_round).first()
    if not current_round_db:
        raise HTTPException(status_code=404, detail=f"Round {event.current_round} not found.")

    if current_round_db.status != EventRoundStatus.WAITING_FOR_RESPONSES:
        raise HTTPException(status_code=400, detail=f"Round {event.current_round} is not open for responses.")

    # Update status to in_analysis
    current_round_db.status = EventRoundStatus.IN_ANALYSIS
    db.commit()

    # Define the background task for AI analysis
    def run_analysis_and_advance():
        try:
            # Re-fetch objects in the background task's session if needed
            db_bg = next(get_local_db())
            event_bg = db_bg.query(Event).filter(Event.id == event_id).first()
            current_round_bg = db_bg.query(EventRound).filter_by(event_id=event_id, round_number=event_bg.current_round).first()

            # 1. Perform AI Analysis and create a Synthesis object
            # This is a placeholder for your actual analysis logic
            # You would call your NLP service here
            responses_for_round = db_bg.query(Response).join(Inquiry).filter(
                Inquiry.event_id == event_id,
                Inquiry.round_number == event_bg.current_round
            ).all()

            response_texts = [r.content for r in responses_for_round]
            
            # Simple synthesis for now
            synthesis_content = f"Synthesis for round {event_bg.current_round}. Total responses: {len(response_texts)}. "
            if response_texts:
                synthesis_content += "Key themes appear to be: " + ", ".join(list(set(response_texts))[:3])


            new_synthesis = Synthesis(
                event_id=event_id,
                round_number=event_bg.current_round,
                content=synthesis_content
            )
            db_bg.add(new_synthesis)

            # 2. Update current round status to ADMIN_REVIEW
            current_round_bg.status = EventRoundStatus.ADMIN_REVIEW
            
            # 3. Create the next round
            new_round = EventRound(
                event_id=event_id,
                round_number=event_bg.current_round + 1,
                status=EventRoundStatus.WAITING_FOR_RESPONSES
            )
            db_bg.add(new_round)
            
            # 4. Update the event's current_round counter
            event_bg.current_round += 1
            
            db_bg.commit()
        except Exception as e:
            # Log error, potentially update round status to an error state
            print(f"Error during background analysis for event {event_id}, round {event_bg.current_round}: {e}")
            db_bg.rollback()
        finally:
            db_bg.close()

    background_tasks.add_task(run_analysis_and_advance)

    return {"message": f"Round {event.current_round} analysis started. The next round will be available after admin review."}


@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_local_db)
):
    user = db.query(TemporaryUser).filter(TemporaryUser.session_code == event_data.session_code).first()
    if not user:
        raise HTTPException(status_code=404, detail="Session code not found.")

    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        status=EventStatus.DRAFT,
        max_participants=event_data.max_participants,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        is_public=event_data.is_public,
        allow_anonymous=event_data.allow_anonymous,
        organizer_id=user.id,
    )
    db.add(new_event)
    db.flush()

    for i, inquiry_data in enumerate(event_data.inquiries):
        new_inquiry = Inquiry(
            event_id=new_event.id,
            question_text=inquiry_data.title,
            description=inquiry_data.content,
            response_type=inquiry_data.inquiry_type,
            is_required=inquiry_data.required,
            order_index=inquiry_data.order_index if inquiry_data.order_index > 0 else i
        )
        db.add(new_inquiry)

    db.commit()
    db.refresh(new_event)

    return EventResponse(
        id=str(new_event.id),
        title=new_event.title,
        description=new_event.description,
        event_type=new_event.event_type,
        status=new_event.status.value,
        max_participants=new_event.max_participants,
        current_participants=0,
        start_time=new_event.start_time,
        end_time=new_event.end_time,
        is_public=new_event.is_public,
        allow_anonymous=new_event.allow_anonymous,
        created_at=new_event.created_at,
        updated_at=new_event.updated_at,
        created_by=user.display_name,
        inquiries=[inq for inq in new_event.inquiries]
    )

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: Session = Depends(get_local_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    organizer_name = event.organizer.display_name if event.organizer else "Unknown"

    return EventResponse(
        id=str(event.id),
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        status=event.status.value,
        max_participants=event.max_participants,
        current_participants=len(event.participants),
        start_time=event.start_time,
        end_time=event.end_time,
        is_public=event.is_public,
        allow_anonymous=event.allow_anonymous,
        created_at=event.created_at,
        updated_at=event.updated_at,
        created_by=organizer_name,
        inquiries=[inq for inq in event.inquiries]
    )

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_data: EventCreate,
    db: Session = Depends(get_local_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user = db.query(TemporaryUser).filter(TemporaryUser.session_code == event_data.session_code).first()
    if not user:
        raise HTTPException(status_code=404, detail="Session code not found.")

    event.title = event_data.title
    event.description = event_data.description
    event.event_type = event_data.event_type
    event.max_participants = event_data.max_participants
    event.start_time = event_data.start_time
    event.end_time = event_data.end_time
    event.is_public = event_data.is_public
    event.allow_anonymous = event_data.allow_anonymous
    event.organizer_id = user.id

    db.commit()
    db.refresh(event)

    return EventResponse(
        id=str(event.id),
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        status=event.status.value,
        max_participants=event.max_participants,
        current_participants=len(event.participants),
        start_time=event.start_time,
        end_time=event.end_time,
        is_public=event.is_public,
        allow_anonymous=event.allow_anonymous,
        created_at=event.created_at,
        updated_at=event.updated_at,
        created_by=user.display_name,
        inquiries=[InquiryResponse.model_validate(inq) for inq in event.inquiries]
    ) 