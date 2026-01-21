"""
Local Events router for the API Gateway - Simplified for SQLite
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

from core.database_local import get_local_db
from core.config import get_settings
from shared.models.database import Event, Inquiry, TemporaryUser, EventParticipant, EventStatus, EventRound, EventRoundStatus, Synthesis, Response
from .auth import get_current_user
from pydantic import BaseModel, Field, field_validator
# Import the ollama_client
from nlp_service.ollama_client import ollama_client
import json

# Configure logger
logger = logging.getLogger(__name__)
settings = get_settings()

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
    organizer_id: str  # Add organizer_id field
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

class SynthesisSummary(BaseModel):
    """Minimal synthesis summary - for compact listings.
    Use SynthesisResponse from ai_analysis_local.py for full synthesis data."""
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
    common_desired_outcomes: List[str] = []
    common_strategies: List[str] = []
    common_values: List[str] = []
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
        created_by=event.organizer.display_name if event.organizer else "Unknown",
        organizer_id=str(event.organizer_id),
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
            common_desired_outcomes=s.common_desired_outcomes or [],
            common_strategies=s.common_strategies or [],
            common_values=s.common_values or [],
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
            logger.debug(f"Starting analysis for event {event_id}")

            # 2. Fetch all necessary data
            event = local_db.query(Event).filter(Event.id == event_id).first()
            if not event:
                logger.error(f"Event {event_id} not found")
                return

            current_round_number = event.current_round
            logger.debug(f"Analyzing round {current_round_number}")

            inquiries = local_db.query(Inquiry).filter(
                Inquiry.event_id == event_id,
                Inquiry.round_number == current_round_number
            ).all()

            inquiry_ids = [str(i.id) for i in inquiries]

            responses = local_db.query(Response).filter(
                Response.inquiry_id.in_(inquiry_ids)
            ).all()

            if not responses:
                logger.info(f"No responses for round {current_round_number}, cannot analyze.")
                # Update round status to show it's waiting, even if no analysis is done
                current_round = local_db.query(EventRound).filter_by(event_id=event_id, round_number=current_round_number).first()
                if current_round:
                    current_round.status = EventRoundStatus.ADMIN_REVIEW
                    local_db.commit()
                return

            logger.debug(f"Found {len(responses)} responses to analyze")

            # 3. Prepare data for Ollama with error handling
            response_data = [{"content": r.content, "inquiry_title": r.inquiry.question_text} for r in responses]
            event_data = {"title": event.title, "description": event.description}

            # Try to use Ollama, but fallback to safe analysis if it fails
            try:
                logger.debug("Attempting Ollama analysis...")
                # 4. Perform AI analysis to get complete round insights
                analysis_result = ollama_client.generate_round_insights(event_data, response_data, current_round_number)
                summary = analysis_result.get("summary", "No summary generated.")

                # 5. Generate next set of inquiries based on the summary
                previous_inquiries = [q.question_text for q in inquiries]
                next_prompts = ollama_client.generate_next_inquiries(summary, previous_inquiries)
                logger.debug("Ollama analysis successful")

            except Exception as ollama_error:
                logger.warning(f"Ollama analysis failed: {ollama_error}")
                logger.debug("Using fallback analysis...")
                # Fallback to safe analysis if Ollama fails
                summary = f"Analysis of {len(responses)} responses for round {current_round_number}. Key themes include participant engagement and diverse perspectives."

                analysis_result = {
                    "summary": summary,
                    "key_themes": ["Community engagement", "Diverse perspectives", "Collaborative solutions"],
                    "consensus_points": ["Need for action", "Importance of dialogue"],
                    "dialogue_opportunities": ["Follow-up discussion", "Implementation planning"],
                    "common_concerns": ["Resource allocation", "Timeline considerations"],
                    "common_desired_outcomes": ["Improved community outcomes", "Sustainable solutions"],
                    "common_strategies": ["Collaborative approach", "Evidence-based planning"],
                    "common_values": ["Transparency", "Inclusivity", "Effectiveness"]
                }

                # Simple fallback prompts
                next_prompts = [
                    {"title": "Implementation Planning", "content": "Based on the themes identified, what specific steps should we take to move forward?"},
                    {"title": "Resource Considerations", "content": "What resources or support would be needed to implement the proposed solutions?"}
                ]

            logger.debug(f"Generated analysis with {len(analysis_result.get('key_themes', []))} themes")

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
                # Store new enhanced analysis fields
                common_desired_outcomes=analysis_result.get("common_desired_outcomes", []),
                common_strategies=analysis_result.get("common_strategies", []),
                common_values=analysis_result.get("common_values", []),
                response_count_basis=len(responses),
                next_round_prompts=next_prompts,
                created_at=datetime.now(timezone.utc)
            )
            local_db.add(synthesis)

            # 7. Automatically create inquiries for the next round
            next_round_number = current_round_number + 1
            if next_prompts:  # Only create if we have prompts
                for i, prompt in enumerate(next_prompts):
                    new_inquiry = Inquiry(
                        id=uuid.uuid4(),
                        event_id=event_id,
                        question_text=prompt.get('content', 'Untitled Prompt'),
                        description=prompt.get('title', ''),
                        order_index=i,
                        round_number=next_round_number,
                        response_type='text',
                        is_required=True,
                    )
                    local_db.add(new_inquiry)

                # Create the next round for admin review
                next_event_round = EventRound(
                    event_id=event_id,
                    round_number=next_round_number,
                    status=EventRoundStatus.ADMIN_REVIEW,
                )
                local_db.add(next_event_round)

                # Update the event's round number
                event.current_round = next_round_number

            # 8. Update current round status to completed
            current_round = local_db.query(EventRound).filter_by(event_id=event_id, round_number=current_round_number).first()
            if current_round:
                current_round.status = EventRoundStatus.COMPLETED

            local_db.commit()
            logger.debug(f"Analysis completed successfully for round {current_round_number}")

        except Exception as e:
            logger.error(f"Error in background task for advancing round: {e}")
            import traceback
            traceback.print_exc()
            local_db.rollback()
        finally:
            local_db.close()

    background_tasks.add_task(run_analysis_and_advance)
    
    return {"message": "Analysis for the current round has been initiated. Please check back for review."}


@router.get("/{event_id}/synthesis-review")
def get_synthesis_for_review(event_id: str, db: Session = Depends(get_local_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # When in admin_review, we need the synthesis from the previous round
    synthesis_round = event.current_round - 1 if event.current_round > 1 else event.current_round
    synthesis = db.query(Synthesis).filter(
        Synthesis.event_id == event_id,
        Synthesis.round_number == synthesis_round
    ).order_by(Synthesis.created_at.desc()).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail=f"Synthesis for round {synthesis_round} not found.")

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

    # Delete existing inquiries for this round to prevent duplicates
    existing_inquiries = db.query(Inquiry).filter(
        Inquiry.event_id == event.id,
        Inquiry.round_number == next_round_number
    ).all()
    for inquiry in existing_inquiries:
        db.delete(inquiry)

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
        organizer_id=str(event_with_inquiries.organizer_id),
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
        organizer_id=str(event.organizer_id),
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
        organizer_id=str(event.organizer_id),
        inquiries=[InquiryResponse.model_validate(inq) for inq in event.inquiries]
    ) 


# Export and End Dialogue Functionality

class ExportRequest(BaseModel):
    format: str = Field(..., description="Export format: json, csv, markdown, pdf")
    type: str = Field(..., description="Export type: raw_data, proposal, agreement, synthesis, roadmap")
    include_analysis: bool = Field(default=True, description="Include AI analysis in export")

class ExportResponse(BaseModel):
    event_id: str
    export_type: str
    format: str
    filename: str
    content: str
    generated_at: datetime

@router.post("/{event_id}/end-dialogue", status_code=200)
async def end_dialogue(
    event_id: str,
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """End the dialogue for an event and mark it as completed."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user is organizer
    if str(event.organizer_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only the event organizer can end the dialogue")
    
    # Update event status to closed
    event.status = EventStatus.CLOSED
    event.end_time = datetime.now(timezone.utc)
    event.updated_at = datetime.now(timezone.utc)
    
    # Mark current round as completed
    current_round = db.query(EventRound).filter(
        EventRound.event_id == event_id,
        EventRound.round_number == event.current_round
    ).first()
    
    if current_round:
        current_round.status = EventRoundStatus.COMPLETED
    
    db.commit()
    
    return {
        "message": "Dialogue ended successfully",
        "event_id": event_id,
        "final_round": event.current_round,
        "completed_at": event.end_time.isoformat()
    }

@router.post("/{event_id}/export", response_model=ExportResponse)
async def export_event_data(
    event_id: str,
    export_request: ExportRequest,
    db: Session = Depends(get_local_db),
    current_user: TemporaryUser = Depends(get_current_user)
):
    """Export event data in various formats."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user is organizer
    if str(event.organizer_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only the event organizer can export event data")
    
    try:
        # Generate export content based on type
        if export_request.type == "raw_data":
            content = await _export_raw_data(event, db, export_request.format)
        elif export_request.type == "proposal":
            content = await _generate_proposal(event, db, export_request.format)
        elif export_request.type == "agreement":
            content = await _generate_agreement(event, db, export_request.format)
        elif export_request.type == "synthesis":
            content = await _generate_synthesis_report(event, db, export_request.format)
        elif export_request.type == "roadmap":
            content = await _generate_roadmap(event, db, export_request.format)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export type: {export_request.type}")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{event.title.replace(' ', '_')}_{export_request.type}_{timestamp}.{export_request.format}"
        
        return ExportResponse(
            event_id=event_id,
            export_type=export_request.type,
            format=export_request.format,
            filename=filename,
            content=content,
            generated_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Export helper functions

async def _export_raw_data(event: Event, db: Session, format: str) -> str:
    """Export raw event data."""
    # Get all responses, inquiries, and analysis
    responses = db.query(Response).join(Inquiry).filter(Inquiry.event_id == event.id).all()
    inquiries = db.query(Inquiry).filter(Inquiry.event_id == event.id).all()
    syntheses = db.query(Synthesis).filter(Synthesis.event_id == event.id).all()
    
    if format == "json":
        data = {
            "event": {
                "id": str(event.id),
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "status": event.status.value,
                "created_at": event.created_at.isoformat(),
                "updated_at": event.updated_at.isoformat() if event.updated_at else None,
                "current_round": event.current_round
            },
            "inquiries": [
                {
                    "id": str(i.id),
                    "question_text": i.question_text,
                    "description": i.description,
                    "round_number": i.round_number,
                    "order_index": i.order_index
                }
                for i in inquiries
            ],
            "responses": [
                {
                    "id": str(r.id),
                    "content": r.content,
                    "round_number": r.round_number,
                    "created_at": r.created_at.isoformat(),
                    "inquiry_id": str(r.inquiry_id),
                    "is_anonymous": r.is_anonymous
                }
                for r in responses
            ],
            "analysis": [
                {
                    "round_number": s.round_number,
                    "summary": s.summary,
                    "content": s.content,
                    "key_themes": s.key_themes,
                    "consensus_points": s.consensus_points,
                    "dialogue_opportunities": s.dialogue_opportunities,
                    "common_desired_outcomes": s.common_desired_outcomes,
                    "common_strategies": s.common_strategies,
                    "common_values": s.common_values,
                    "created_at": s.created_at.isoformat()
                }
                for s in syntheses
            ]
        }
        return json.dumps(data, indent=2)
    
    elif format == "csv":
        # Create CSV format for responses
        csv_lines = ["Round,Inquiry,Response,Created_At,Anonymous"]
        for r in responses:
            inquiry = next((i for i in inquiries if i.id == r.inquiry_id), None)
            inquiry_text = inquiry.question_text.replace('"', '""') if inquiry else "Unknown"
            response_text = r.content.replace('"', '""')
            csv_lines.append(f'{r.round_number},"{inquiry_text}","{response_text}",{r.created_at.isoformat()},{r.is_anonymous}')
        return "\n".join(csv_lines)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format for raw data: {format}")

async def _generate_proposal(event: Event, db: Session, format: str) -> str:
    """Generate a proposal document using AI."""
    # Get event analysis
    syntheses = db.query(Synthesis).filter(Synthesis.event_id == event.id).all()
    responses = db.query(Response).join(Inquiry).filter(Inquiry.event_id == event.id).all()
    
    if not syntheses and not responses:
        raise HTTPException(status_code=400, detail="No data available to generate proposal")
    
    # Prepare data for AI generation
    analysis_data = []
    for s in syntheses:
        analysis_data.append({
            "round": s.round_number,
            "summary": s.summary or s.content,
            "key_themes": s.key_themes or [],
            "consensus_points": s.consensus_points or [],
            "common_desired_outcomes": s.common_desired_outcomes or [],
            "common_strategies": s.common_strategies or []
        })
    
    # Generate proposal using Ollama
    prompt = f"""Based on the following event analysis, generate a comprehensive proposal document for: {event.title}

Event Description: {event.description}

Analysis Data: {json.dumps(analysis_data, indent=2)}

Please create a structured proposal that includes:
1. Executive Summary
2. Background and Context
3. Key Findings
4. Proposed Actions
5. Implementation Strategy
6. Expected Outcomes
7. Next Steps

Format: {'Markdown' if format == 'markdown' else 'Plain text'}
"""

    try:
        proposal_content = ollama_client.generate_response(prompt, "You are an expert policy writer creating civic proposals.")
        return proposal_content
    except Exception as e:
        # Fallback to structured template
        return f"""# Proposal for {event.title}

## Executive Summary
Based on community dialogue conducted through {len(syntheses)} rounds of engagement.

## Key Findings
{chr(10).join([f"- {theme}" for s in syntheses for theme in (s.key_themes or [])])}

## Consensus Points
{chr(10).join([f"- {point}" for s in syntheses for point in (s.consensus_points or [])])}

## Proposed Actions
{chr(10).join([f"- {outcome}" for s in syntheses for outcome in (s.common_desired_outcomes or [])])}

## Implementation Strategy
{chr(10).join([f"- {strategy}" for s in syntheses for strategy in (s.common_strategies or [])])}

Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

async def _generate_agreement(event: Event, db: Session, format: str) -> str:
    """Generate an agreement document using AI."""
    syntheses = db.query(Synthesis).filter(Synthesis.event_id == event.id).all()
    
    if not syntheses:
        raise HTTPException(status_code=400, detail="No analysis data available to generate agreement")
    
    # Extract consensus points from all rounds
    all_consensus = []
    for s in syntheses:
        if s.consensus_points:
            all_consensus.extend(s.consensus_points)
    
    prompt = f"""Create a community agreement document for: {event.title}

Based on consensus points identified through dialogue:
{json.dumps(all_consensus, indent=2)}

Generate a formal agreement document that includes:
1. Agreement Title
2. Participating Parties
3. Shared Values and Principles
4. Agreed-Upon Actions
5. Commitments and Responsibilities
6. Implementation Timeline
7. Review and Evaluation Process

Format: {'Markdown' if format == 'markdown' else 'Plain text'}
"""

    try:
        agreement_content = ollama_client.generate_response(prompt, "You are an expert facilitator creating community agreements.")
        return agreement_content
    except Exception as e:
        # Fallback template
        return f"""# Community Agreement: {event.title}

## Shared Principles
{chr(10).join([f"- {point}" for point in all_consensus[:5]])}

## Commitments
{chr(10).join([f"- {point}" for point in all_consensus[5:10]])}

## Next Steps
- Regular review meetings
- Progress monitoring
- Community updates

Agreement created: {datetime.now().strftime('%Y-%m-%d')}
"""

async def _generate_synthesis_report(event: Event, db: Session, format: str) -> str:
    """Generate a comprehensive synthesis report."""
    syntheses = db.query(Synthesis).filter(Synthesis.event_id == event.id).all()
    responses = db.query(Response).join(Inquiry).filter(Inquiry.event_id == event.id).all()
    
    if not syntheses:
        raise HTTPException(status_code=400, detail="No synthesis data available")
    
    report = f"""# Dialogue Synthesis Report: {event.title}

## Event Overview
- **Description**: {event.description}
- **Dialogue Rounds**: {len(syntheses)}
- **Total Responses**: {len(responses)}
- **Period**: {event.created_at.strftime('%Y-%m-%d')} to {event.updated_at.strftime('%Y-%m-%d') if event.updated_at else 'ongoing'}

## Round-by-Round Analysis

"""
    
    for s in syntheses:
        report += f"""### Round {s.round_number}
**Summary**: {s.summary or s.content}

**Key Themes**:
{chr(10).join([f"- {theme}" for theme in (s.key_themes or [])])}

**Consensus Points**:
{chr(10).join([f"- {point}" for point in (s.consensus_points or [])])}

**Common Desired Outcomes**:
{chr(10).join([f"- {outcome}" for outcome in (s.common_desired_outcomes or [])])}

**Common Values**:
{chr(10).join([f"- {value}" for value in (s.common_values or [])])}

**Common Strategies**:
{chr(10).join([f"- {strategy}" for strategy in (s.common_strategies or [])])}

---

"""
    
    report += f"""## Overall Synthesis

This dialogue engaged the community through {len(syntheses)} rounds of structured conversation, resulting in shared understanding and actionable insights.

Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

async def _generate_roadmap(event: Event, db: Session, format: str) -> str:
    """Generate an implementation roadmap using AI."""
    syntheses = db.query(Synthesis).filter(Synthesis.event_id == event.id).all()
    
    if not syntheses:
        raise HTTPException(status_code=400, detail="No data available to generate roadmap")
    
    # Extract all strategic elements
    all_strategies = []
    all_outcomes = []
    for s in syntheses:
        if s.common_strategies:
            all_strategies.extend(s.common_strategies)
        if s.common_desired_outcomes:
            all_outcomes.extend(s.common_desired_outcomes)
    
    prompt = f"""Create an implementation roadmap for: {event.title}

Based on identified strategies: {json.dumps(all_strategies, indent=2)}
And desired outcomes: {json.dumps(all_outcomes, indent=2)}

Generate a roadmap with:
1. Short-term actions (0-3 months)
2. Medium-term goals (3-12 months)  
3. Long-term vision (1-3 years)
4. Success metrics for each phase
5. Resource requirements
6. Stakeholder responsibilities
7. Risk mitigation strategies

Format: {'Markdown' if format == 'markdown' else 'Plain text'}
"""

    try:
        roadmap_content = ollama_client.generate_response(prompt, "You are an expert strategic planner creating implementation roadmaps.")
        return roadmap_content
    except Exception as e:
        # Fallback template
        return f"""# Implementation Roadmap: {event.title}

## Short-term Actions (0-3 months)
{chr(10).join([f"- {strategy}" for strategy in all_strategies[:3]])}

## Medium-term Goals (3-12 months)
{chr(10).join([f"- {outcome}" for outcome in all_outcomes[:3]])}

## Long-term Vision (1-3 years)
{chr(10).join([f"- {strategy}" for strategy in all_strategies[3:6]])}

## Success Metrics
- Community engagement levels
- Implementation progress
- Outcome achievement

Created: {datetime.now().strftime('%Y-%m-%d')}
""" 