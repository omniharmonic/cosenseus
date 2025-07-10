"""
Local Events router for the API Gateway - Simplified for SQLite
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from core.database_local import get_local_db
from shared.models.database import Event, Inquiry, TemporaryUser, EventParticipant, EventStatus, EventRound, EventRoundStatus, Synthesis, Response
from .auth import get_current_user
from pydantic import BaseModel, Field, field_validator
# Import the ollama_client
from nlp_service.ollama_client import ollama_client

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
    user_id: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator('id', 'inquiry_id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

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

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True

class RoundResultsResponse(BaseModel):
    round_number: int
    summary: Optional[str] = None
    key_themes: List[str] = []
    consensus_points: List[str] = []
    dialogue_opportunities: List[str] = []
    participant_count: Optional[int] = 0
    created_at: datetime
    next_round_prompts: Optional[List[Dict[str, Any]]] = None

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
    """Get the current round state for an event with improved error handling."""
    try:
        # Use a more robust query with explicit error handling
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Query the current round with safer handling
        current_round = db.query(EventRound).filter(
            EventRound.event_id == event_id,
            EventRound.round_number == event.current_round
        ).first()
        
        if not current_round:
            # If no round exists, assume round 1 is open
            return RoundStateResponse(
                current_round=1,
                status=EventRoundStatus.WAITING_FOR_RESPONSES.value
            )

        return RoundStateResponse(
            current_round=event.current_round,
            status=current_round.status.value
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Database error in round-state endpoint: {e}")
        # Return a safe fallback response instead of crashing
        return RoundStateResponse(
            current_round=1,
            status=EventRoundStatus.WAITING_FOR_RESPONSES.value
        )


@router.post("/{event_id}/publish", response_model=EventResponse)
async def publish_event(
    event_id: str,
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """Publish an event, changing its status from draft to active."""
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if str(event.organizer_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to publish this event")

    if event.status != EventStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Event cannot be published from its current state: {event.status.value}")

    event.status = EventStatus.ACTIVE
    event.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)

    participant_count = db.query(EventParticipant).filter(EventParticipant.event_id == event.id).count()

    return EventResponse(
        id=str(event.id),
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        status=event.status.value,
        max_participants=event.max_participants,
        current_participants=participant_count,
        start_time=event.start_time,
        end_time=event.end_time,
        is_public=event.is_public,
        allow_anonymous=event.allow_anonymous,
        created_at=event.created_at,
        updated_at=event.updated_at,
        created_by=str(event.organizer_id),
        inquiries=[InquiryResponse.from_orm(i) for i in event.inquiries]
    )


@router.get("/{event_id}/round-results", response_model=List[RoundResultsResponse])
async def get_event_round_results(event_id: str, round_number: Optional[int] = None, db: Session = Depends(get_local_db)):
    """
    Get the analysis results for all completed rounds of an event up to a specific round number.
    """
    if round_number is None:
        raise HTTPException(status_code=400, detail="round_number query parameter is required.")

    syntheses = db.query(Synthesis).filter(
        Synthesis.event_id == event_id,
        Synthesis.round_number <= round_number,
        Synthesis.status == "approved"
    ).order_by(Synthesis.round_number).all()

    if not syntheses:
        return []

    results = []
    for s in syntheses:
        # Here we map the Synthesis model to the RoundResultsResponse model.
        results.append(RoundResultsResponse(
            round_number=s.round_number,
            summary=s.summary or s.content,
            key_themes=s.key_themes or [],
            consensus_points=s.consensus_points or [],
            dialogue_opportunities=s.dialogue_opportunities or [],
            participant_count=s.response_count_basis,
            created_at=s.created_at,
            next_round_prompts=s.next_round_prompts
        ))
    return results


@router.post("/{event_id}/advance-round", status_code=202)
async def advance_to_next_round(
    event_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """
    Moves the event to the next round, triggering AI analysis in the background.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if str(event.organizer_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only the event organizer can advance the round")
    
    current_round = db.query(EventRound).filter_by(event_id=event_id, round_number=event.current_round).first()
    if current_round:
        current_round.status = EventRoundStatus.IN_ANALYSIS
        db.commit()

    def run_analysis_and_advance():
        # 1. Get a new database session for this background task
        from core.database_local import LocalSessionLocal
        local_db = LocalSessionLocal()
        try:
            # 2. Fetch all necessary data
            event = local_db.query(Event).filter(Event.id == event_id).first()
            current_round_number = event.current_round if event else 1
            
            inquiries = local_db.query(Inquiry).filter(
                Inquiry.event_id == event_id,
                Inquiry.round_number == current_round_number
            ).all()
            
            inquiry_ids = [str(i.id) for i in inquiries]
            
            responses = local_db.query(Response).filter(
                Response.inquiry_id.in_(inquiry_ids)
            ).all()

            if not responses:
                print(f"No responses for round {current_round_number}, cannot analyze.")
                # Update round status to show it's waiting, even if no analysis is done
                current_round = local_db.query(EventRound).filter_by(event_id=event_id, round_number=current_round_number).first()
                if current_round:
                    current_round.status = EventRoundStatus.ADMIN_REVIEW
                    local_db.commit()
                return

            # 3. Prepare data for Ollama
            response_data = [{"content": r.content, "inquiry_title": r.inquiry.question_text} for r in responses]
            event_data = {"title": event.title, "description": event.description}

            # 4. Perform AI analysis to get complete round insights
            analysis_result = ollama_client.generate_round_insights(event_data, response_data, current_round_number)
            summary = analysis_result.get("summary", "No summary generated.")

            # 5. Generate next set of inquiries based on the summary
            previous_inquiries = [q.question_text for q in inquiries]
            next_prompts = ollama_client.generate_next_inquiries(summary, previous_inquiries)

            # 6. Create and store a new synthesis record for admin review with complete analysis
            synthesis = Synthesis(
                id=uuid.uuid4(),
                event_id=event_id,
                round_number=current_round_number,
                status="approved",
                content=summary,
                summary=summary,
                # Store complete analysis results
                key_themes=analysis_result.get("key_themes", []),
                consensus_points=analysis_result.get("consensus_points", []),
                dialogue_opportunities=analysis_result.get("dialogue_opportunities", []),
                consensus_areas=analysis_result.get("common_concerns", []),  # Map common_concerns to consensus_areas
                response_count_basis=len(responses),
                next_round_prompts=next_prompts,
                created_at=datetime.now(timezone.utc)
            )
            local_db.add(synthesis)

            # 7. Update event round status
            current_round = local_db.query(EventRound).filter_by(event_id=event_id, round_number=current_round_number).first()
            if current_round:
                current_round.status = EventRoundStatus.ADMIN_REVIEW
                local_db.commit()

        except Exception as e:
            print(f"Error in background task for advancing round: {e}")
            # Optionally, revert state or log to a persistent store
        finally:
            local_db.close()

    background_tasks.add_task(run_analysis_and_advance)
    
    return {"message": "Analysis for the current round has been initiated. Please check back for review."}


@router.get("/{event_id}/synthesis-review")
def get_synthesis_for_review(event_id: str, db: Session = Depends(get_local_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    synthesis = db.query(Synthesis).filter(
        Synthesis.event_id == event_id,
        Synthesis.round_number == event.current_round
    ).order_by(Synthesis.created_at.desc()).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis for the current round not found.")

    return {
        "round_number": synthesis.round_number,
        "synthesis_content": synthesis.content,
        "next_round_prompts": synthesis.next_round_prompts
    }

class ApprovedPrompts(BaseModel):
    prompts: List[Dict[str, str]]

@router.post("/{event_id}/approve-synthesis")
def approve_synthesis_and_advance(
    event_id: str, 
    payload: ApprovedPrompts,
    db: Session = Depends(get_local_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    next_round_number = event.current_round + 1

    # Create new inquiries from the approved prompts
    for i, prompt_data in enumerate(payload.prompts):
        new_inquiry = Inquiry(
            id=uuid.uuid4(),
            event_id=event.id,
            round_number=next_round_number,
            question_text=prompt_data.get('title', 'Untitled Inquiry'),
            description=prompt_data.get('content', ''),
            order_index=i
        )
        db.add(new_inquiry)

    # Update the event's round number
    event.current_round = next_round_number
    
    # Create the new round object
    new_round = EventRound(
        id=uuid.uuid4(),
        event_id=event.id,
        round_number=next_round_number,
        status=EventRoundStatus.WAITING_FOR_RESPONSES
    )
    db.add(new_round)

    db.commit()

    return {"message": f"Successfully advanced to round {next_round_number}"}


@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_local_db)
):
    creator = db.query(TemporaryUser).filter(TemporaryUser.session_code == event_data.session_code).first()
    if not creator or creator.session_code != event_data.session_code:
        raise HTTPException(status_code=403, detail="Invalid session code for event creation.")

    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        max_participants=event_data.max_participants,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        is_public=event_data.is_public,
        allow_anonymous=event_data.allow_anonymous,
        organizer_id=creator.id
    )
    db.add(new_event)
    db.flush()  # Use flush to get the new_event.id for the inquiries

    for inquiry_data in event_data.inquiries:
        new_inquiry = Inquiry(
            event_id=new_event.id,
            question_text=inquiry_data.title, # Assuming title maps to question_text
            description=inquiry_data.content, # Assuming content maps to description
            order_index=inquiry_data.order_index,
            is_required=inquiry_data.required,
            response_type="text",
            round_number=1 # Inquiries created with the event are always for round 1
        )
        db.add(new_inquiry)

    # Also create the first round for the event
    first_round = EventRound(
        event_id=new_event.id,
        round_number=1,
        status=EventRoundStatus.WAITING_FOR_RESPONSES
    )
    db.add(first_round)

    db.commit() # Commit all new records to the database
    db.refresh(new_event)

    # Re-query to construct the response model accurately
    db.refresh(new_event)
    event_with_inquiries = db.query(Event).filter(Event.id == new_event.id).one()
    
    current_participants = db.query(EventParticipant).filter(EventParticipant.event_id == new_event.id).count()

    return EventResponse(
        id=str(event_with_inquiries.id),
        title=event_with_inquiries.title,
        description=event_with_inquiries.description,
        event_type=event_with_inquiries.event_type,
        status=event_with_inquiries.status.value,
        max_participants=event_with_inquiries.max_participants,
        current_participants=current_participants,
        start_time=event_with_inquiries.start_time,
        end_time=event_with_inquiries.end_time,
        is_public=event_with_inquiries.is_public,
        allow_anonymous=event_with_inquiries.allow_anonymous,
        created_at=event_with_inquiries.created_at,
        updated_at=event_with_inquiries.updated_at,
        created_by=event_with_inquiries.organizer.display_name,
        inquiries=[InquiryResponse.from_orm(i) for i in event_with_inquiries.inquiries]
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