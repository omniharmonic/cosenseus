from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import sys
import os
import json
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator, Field

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from core.database_local import get_local_db
# Import local database models
from shared.models.database import Event, Inquiry, Response, EventRound, EventRoundStatus, Synthesis
from nlp_service.ollama_client import ollama_client
from .auth import get_current_user
from nlp_service.core.opinion_analyzer import OpinionAnalyzer

router = APIRouter()

@router.get("/ai/health")
async def ai_health():
    """
    Check the health of the local AI service (Ollama).
    """
    try:
        health_status = ollama_client.check_health()
        return {
            "service": "ollama",
            "status": health_status["status"],
            "model": ollama_client.model,
            "details": health_status
        }
    except Exception as e:
        return {
            "service": "ollama",
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/ai/analyze-event/{event_id}")
async def analyze_event(
    event_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_local_db)
):
    """
    Analyze an event's responses using local Ollama AI.
    """
    try:
        # Get event data using ORM
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get all responses for this event using ORM
        responses = db.query(Response).join(Inquiry).filter(Inquiry.event_id == event_id).all()
        
        if not responses:
            return {
                "event_id": event_id,
                "message": "No responses found for analysis",
                "analysis": {
                    "key_themes": [],
                    "common_concerns": [],
                    "suggested_actions": [],
                    "participant_sentiment": "neutral",
                    "summary": "No responses available for analysis"
                }
            }
        
        # Prepare response data for analysis
        response_data = [
            {
                "content": r.content,
                "inquiry_title": r.inquiry.question_text,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in responses
        ]
        
        # Perform AI analysis
        event_data = {
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type
        }
        
        analysis = ollama_client.generate_insights(event_data, response_data)
        
        return {
            "event_id": event_id,
            "event_title": event.title,
            "response_count": len(responses),
            "analysis": analysis,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/ai/sentiment-analysis")
async def analyze_sentiment(text: str):
    """
    Analyze sentiment of text using local Ollama AI.
    """
    try:
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text is required")
        
        sentiment_result = ollama_client.analyze_sentiment(text)
        
        return {
            "text": text,
            "sentiment_analysis": sentiment_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

class ClusterRequest(BaseModel):
    responses: List[str]
    num_clusters: int = 3

class SynthesisUpdateRequest(BaseModel):
    next_round_prompts: List[Dict[str, Any]]

class SynthesisResponse(BaseModel):
    id: str
    event_id: str
    round_number: int
    title: Optional[str] = None
    content: str
    summary: Optional[str] = None
    next_round_prompts: Optional[List[Dict[str, Any]]] = None
    
    # Analysis fields that match frontend expectations
    key_themes: Optional[List[str]] = None
    consensus_points: Optional[List[str]] = None
    dialogue_opportunities: Optional[List[str]] = None
    consensus_areas: Optional[List[str]] = None
    divergent_perspectives: Optional[List[str]] = None
    nuanced_positions: Optional[List[str]] = None
    
    # New enhanced analysis fields
    common_desired_outcomes: Optional[List[str]] = None
    common_strategies: Optional[List[str]] = None
    common_values: Optional[List[str]] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator('id', 'event_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


@router.post("/ai/cluster-responses")
async def cluster_responses(request: ClusterRequest):
    """
    Cluster similar responses using local Ollama AI.
    """
    try:
        if not request.responses:
            raise HTTPException(status_code=400, detail="Responses list is required")
        
        if request.num_clusters < 1 or request.num_clusters > len(request.responses):
            request.num_clusters = min(3, len(request.responses))
        
        clustering_result = ollama_client.cluster_responses(request.responses, request.num_clusters)
        
        return {
            "responses_count": len(request.responses),
            "num_clusters": request.num_clusters,
            "clustering_result": clustering_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")

@router.get("/ai/event-summary/{event_id}")
async def get_event_summary(event_id: str, db: Session = Depends(get_local_db)):
    """
    Get a comprehensive summary of an event using local Ollama AI.
    """
    try:
        # Use ORM to fetch data
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        inquiries = event.inquiries
        responses_count = len(event.responses)
        participant_count = len(event.participants)
        
        # Prepare summary data
        summary_data = {
            "event": {
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "status": event.status.value if event.status else "N/A"
            },
            "statistics": {
                "inquiries_count": len(inquiries),
                "responses_count": responses_count,
                "participants_count": participant_count
            },
            "inquiries": [
                {
                    "title": inquiry.question_text,
                    "content": inquiry.description,
                    "type": inquiry.response_type
                } for inquiry in inquiries
            ]
        }
        
        # Generate AI summary
        system_prompt = """You are an expert event summarizer. Create a comprehensive summary of the civic engagement event. Return a JSON response with the following structure:
        {
            "event_overview": "brief overview of the event",
            "key_insights": ["insight1", "insight2"],
            "participant_engagement": "description of engagement level",
            "recommendations": ["recommendation1", "recommendation2"],
            "next_steps": "suggested next steps"
        }"""
        
        prompt = f"""Event: {event.title}
Description: {event.description}
Inquiries: {len(inquiries)} total
Responses: {responses_count} total
Participants: {participant_count} total

Please provide a comprehensive summary of this civic engagement event."""
        
        ai_summary = ollama_client.generate_response(prompt, system_prompt)
        
        # Try to parse JSON from response
        try:
            if "{" in ai_summary and "}" in ai_summary:
                start = ai_summary.find("{")
                end = ai_summary.rfind("}") + 1
                json_str = ai_summary[start:end]
                parsed_summary = json.loads(json_str)
            else:
                parsed_summary = {
                    "event_overview": ai_summary,
                    "key_insights": [],
                    "participant_engagement": "Analysis pending",
                    "recommendations": [],
                    "next_steps": "Review responses manually"
                }
        except json.JSONDecodeError:
            parsed_summary = {"error": "Failed to parse AI summary response."}
        
        return {
            "event_id": event_id,
            "summary_data": summary_data,
            "ai_summary": parsed_summary
        }
        
    except Exception as e:
        # Log the exception for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@router.get("/ai/synthesis-review/{event_id}/{round_number}", response_model=SynthesisResponse)
async def get_synthesis_for_review(
    event_id: str,
    round_number: int,
    db: Session = Depends(get_local_db)
):
    """
    Fetches the AI-generated synthesis for a specific round that is pending admin review.
    """
    event_round = db.query(EventRound).filter(
        EventRound.event_id == event_id,
        EventRound.round_number == round_number
    ).first()

    if not event_round:
        raise HTTPException(status_code=404, detail="Event round not found.")

    if event_round.status != EventRoundStatus.ADMIN_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Round is not in review state. Current state: {event_round.status.value}"
        )

    # When in admin_review, we need the synthesis from the previous round
    synthesis_round = round_number - 1 if round_number > 1 else round_number
    synthesis = db.query(Synthesis).filter(
        Synthesis.event_id == event_id,
        Synthesis.round_number == synthesis_round
    ).order_by(Synthesis.created_at.desc()).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis for this round not found.")

    # Explicitly construct the response to ensure all fields are included
    response_data = SynthesisResponse(
        id=str(synthesis.id),
        event_id=str(synthesis.event_id),
        round_number=synthesis.round_number,
        title=synthesis.title,
        content=synthesis.content,
        summary=synthesis.summary,
        next_round_prompts=synthesis.next_round_prompts,
        key_themes=synthesis.key_themes,
        consensus_points=synthesis.consensus_points,
        dialogue_opportunities=synthesis.dialogue_opportunities,
        consensus_areas=synthesis.consensus_areas,
        divergent_perspectives=synthesis.divergent_perspectives,
        nuanced_positions=synthesis.nuanced_positions,
        common_desired_outcomes=synthesis.common_desired_outcomes,
        common_strategies=synthesis.common_strategies,
        common_values=synthesis.common_values,
        created_at=synthesis.created_at,
        updated_at=synthesis.updated_at
    )
    
    return response_data


@router.put("/ai/synthesis-review/{synthesis_id}", response_model=SynthesisResponse)
async def update_synthesis_review(
    synthesis_id: str,
    request: SynthesisUpdateRequest,
    db: Session = Depends(get_local_db)
):
    """
    Updates the next round prompts in a synthesis record.
    """
    try:
        synthesis_uuid = uuid.UUID(synthesis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid synthesis ID format.")

    synthesis = db.query(Synthesis).filter(Synthesis.id == synthesis_uuid).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found.")

    synthesis.next_round_prompts = request.next_round_prompts
    synthesis.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(synthesis)

    return synthesis


class RegeneratePromptsRequest(BaseModel):
    creativity_level: str = Field(default="moderate", description="Creativity level: conservative, moderate, creative")
    focus_areas: Optional[List[str]] = Field(default=None, description="Areas to emphasize in regeneration")
    tone: str = Field(default="analytical", description="Tone: analytical, engaging, challenging")
    length: str = Field(default="standard", description="Length: brief, standard, detailed")

@router.post("/ai/synthesis-review/{synthesis_id}/regenerate", response_model=SynthesisResponse)
async def regenerate_synthesis_prompts(
    synthesis_id: str,
    regenerate_request: RegeneratePromptsRequest,
    db: Session = Depends(get_local_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Regenerate prompts for a synthesis review with different parameters.
    """
    # Get the synthesis
    synthesis = db.query(Synthesis).options(joinedload(Synthesis.event)).filter(
        Synthesis.id == synthesis_id
    ).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found")

    event = synthesis.event
    if str(event.organizer_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only the event organizer can regenerate prompts")

    try:
        # Get the original analysis data to regenerate from
        current_round_number = synthesis.round_number
        
        # Get responses for the current round
        inquiries = db.query(Inquiry).filter(
            Inquiry.event_id == event.id,
            Inquiry.round_number == current_round_number
        ).all()
        
        inquiry_ids = [str(i.id) for i in inquiries]
        responses = db.query(Response).filter(
            Response.inquiry_id.in_(inquiry_ids)
        ).all()

        if not responses:
            raise HTTPException(status_code=400, detail="No responses available for regeneration")

        # Prepare data for regeneration
        response_data = [
            {
                "content": r.content,
                "inquiry_title": r.inquiry.question_text if r.inquiry else "Unknown"
            }
            for r in responses
        ]
        
        event_data = {
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type
        }
        
        # Adjust Ollama parameters based on request
        temperature = {
            "conservative": 0.3,
            "moderate": 0.7,
            "creative": 1.0
        }.get(regenerate_request.creativity_level, 0.7)
        
        # Create enhanced prompt with additional instructions
        enhanced_instructions = []
        
        if regenerate_request.focus_areas:
            enhanced_instructions.append(f"Focus particularly on these areas: {', '.join(regenerate_request.focus_areas)}")
        
        if regenerate_request.tone == "engaging":
            enhanced_instructions.append("Use an engaging, conversational tone that encourages participation.")
        elif regenerate_request.tone == "challenging":
            enhanced_instructions.append("Pose challenging questions that push participants to think deeper.")
        elif regenerate_request.tone == "analytical":
            enhanced_instructions.append("Use an analytical, thoughtful tone focused on understanding different perspectives.")
        
        if regenerate_request.length == "brief":
            enhanced_instructions.append("Keep questions concise and focused.")
        elif regenerate_request.length == "detailed":
            enhanced_instructions.append("Provide detailed context and multi-part questions.")
        
        # Store current prompts as backup
        original_prompts = synthesis.next_round_prompts.copy() if synthesis.next_round_prompts else []
        
        # Generate new prompts with enhanced parameters
        try:
            # Use generate_round_insights for consistency but with modified parameters
            analysis_result = ollama_client.generate_round_insights(
                event_data, 
                response_data, 
                current_round_number,
                temperature=temperature,
                additional_instructions=enhanced_instructions
            )
            
            # Extract new prompts from the analysis
            if "dialogue_opportunities" in analysis_result:
                new_prompts = [
                    {
                        "title": f"Follow-up Question {i+1}",
                        "content": opportunity,
                        "regenerated": True,
                        "parameters": {
                            "creativity_level": regenerate_request.creativity_level,
                            "tone": regenerate_request.tone,
                            "length": regenerate_request.length,
                            "focus_areas": regenerate_request.focus_areas
                        }
                    }
                    for i, opportunity in enumerate(analysis_result["dialogue_opportunities"][:3])
                ]
            else:
                # Fallback: Use previous inquiries as base for modification
                previous_inquiries = [q.question_text for q in inquiries]
                new_prompts = ollama_client.generate_next_inquiries(
                    synthesis.summary or synthesis.content,
                    previous_inquiries,
                    temperature=temperature
                )
                
                # Add regeneration metadata
                for prompt in new_prompts:
                    prompt["regenerated"] = True
                    prompt["parameters"] = {
                        "creativity_level": regenerate_request.creativity_level,
                        "tone": regenerate_request.tone,
                        "length": regenerate_request.length,
                        "focus_areas": regenerate_request.focus_areas
                    }
            
            # Update synthesis with new prompts
            synthesis.next_round_prompts = new_prompts
            synthesis.updated_at = datetime.now(timezone.utc)
            
            # Store regeneration history
            if not hasattr(synthesis, 'prompt_history'):
                synthesis.prompt_history = []
            
            synthesis.prompt_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompts": original_prompts,
                "regeneration_count": len(synthesis.prompt_history) + 1
            })
            
            db.commit()
            db.refresh(synthesis)
            
            return synthesis
            
        except Exception as ollama_error:
            # Fallback to template-based regeneration
            print(f"Ollama regeneration failed, using template fallback: {ollama_error}")
            
            # Create varied prompts based on parameters
            base_prompts = [
                "What new perspectives emerged from the previous discussion?",
                "How can we build on the areas of agreement identified?",
                "What concerns need further exploration?",
                "What would an ideal solution look like from your perspective?"
            ]
            
            # Modify prompts based on parameters
            if regenerate_request.tone == "challenging":
                base_prompts = [prompt.replace("What", "Why do you think").replace("How", "What challenges arise when") for prompt in base_prompts]
            elif regenerate_request.tone == "engaging":
                base_prompts = [f"Let's explore: {prompt.lower()}" for prompt in base_prompts]
            
            new_prompts = [
                {
                    "title": f"Generated Question {i+1}",
                    "content": prompt,
                    "regenerated": True,
                    "fallback": True,
                    "parameters": {
                        "creativity_level": regenerate_request.creativity_level,
                        "tone": regenerate_request.tone,
                        "length": regenerate_request.length
                    }
                }
                for i, prompt in enumerate(base_prompts[:3])
            ]
            
            synthesis.next_round_prompts = new_prompts
            synthesis.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(synthesis)
            
            return synthesis
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt regeneration failed: {str(e)}")


@router.post("/ai/synthesis-review/{synthesis_id}/approve", response_model=SynthesisResponse)
async def approve_synthesis_review(
    synthesis_id: str,
    db: Session = Depends(get_local_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Approve a synthesis review, making the prompts available for the next round.
    """
    # Verify the user is the event organizer
    synthesis = db.query(Synthesis).options(
        joinedload(Synthesis.event)
    ).filter(Synthesis.id == synthesis_id).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis review not found")
    
    event = synthesis.event
    if not event:
        # This case should ideally not happen due to database constraints
        raise HTTPException(status_code=500, detail="Associated event not found for synthesis")

    if str(event.organizer_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only the event organizer can approve the synthesis")

    # 1. Update the synthesis status to "approved"
    synthesis.status = "approved"
    synthesis.updated_at = datetime.now(timezone.utc)

    # 2. Create inquiries for the NEXT round
    next_round_number = synthesis.round_number + 1
    new_inquiries = []
    for i, prompt in enumerate(synthesis.next_round_prompts):
        new_inquiry = Inquiry(
            id=uuid.uuid4(),
            event_id=synthesis.event_id,
            question_text=prompt.get('content', 'Untitled Prompt'),
            description=prompt.get('title', ''),
            order_index=i,
            round_number=next_round_number,
            response_type='text',
            is_required=True,
        )
        new_inquiries.append(new_inquiry)
    db.add_all(new_inquiries)

    # 3. Find or create the NEXT round and set its status to 'open'
    next_event_round = db.query(EventRound).filter(
        EventRound.event_id == synthesis.event_id,
        EventRound.round_number == next_round_number
    ).first()

    if not next_event_round:
        next_event_round = EventRound(
            event_id=synthesis.event_id,
            round_number=next_round_number,
            status=EventRoundStatus.WAITING_FOR_RESPONSES,
        )
        db.add(next_event_round)
    else:
        next_event_round.status = EventRoundStatus.WAITING_FOR_RESPONSES

    # 4. Mark current round as completed
    current_round = db.query(EventRound).filter(
        EventRound.event_id == synthesis.event_id,
        EventRound.round_number == synthesis.round_number
    ).first()

    if current_round:
        current_round.status = EventRoundStatus.COMPLETED

    # 5. Update the event's main round counter
    event.current_round = next_round_number

    db.commit()
    db.refresh(synthesis)
    db.refresh(next_event_round)
    if current_round:
        db.refresh(current_round)

    return synthesis


@router.post("/ai/analyze-event/{event_id}/round/{round_number}")
async def analyze_event_round(
    event_id: str,
    round_number: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_local_db)
):
    """
    Analyze a specific round of an event using local Ollama AI.
    """
    try:
        # Get event data using raw SQL
        event_result = db.execute(text("""
            SELECT id, title, description, event_type, status
            FROM events 
            WHERE id = :event_id
        """), {"event_id": event_id})
        event = event_result.fetchone()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get responses for this specific round
        responses_result = db.execute(text("""
            SELECT r.id, r.content, r.created_at, i.question_text as inquiry_title
            FROM responses r
            JOIN inquiries i ON r.inquiry_id = i.id
            WHERE i.event_id = :event_id AND r.round_number = :round_number
        """), {"event_id": event_id, "round_number": round_number})
        responses = responses_result.fetchall()
        
        if not responses:
            return {
                "event_id": event_id,
                "round_number": round_number,
                "message": f"No responses found for round {round_number}",
                "analysis": {
                    "key_themes": [],
                    "common_concerns": [],
                    "suggested_actions": [],
                    "consensus_points": [],
                    "dialogue_opportunities": [],
                    "participant_sentiment": "neutral",
                    "summary": f"No responses available for round {round_number} analysis"
                }
            }
        
        # Prepare response data for analysis
        response_data = []
        for response in responses:
            created_at = response.created_at
            if isinstance(created_at, str):
                created_at_str = created_at
            elif hasattr(created_at, 'isoformat'):
                created_at_str = created_at.isoformat()
            else:
                created_at_str = str(created_at) if created_at else None
                
            response_data.append({
                "content": response.content,
                "inquiry_title": response.inquiry_title,
                "created_at": created_at_str
            })
        
        # Perform AI analysis with round-specific prompts
        event_data = {
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "round_number": round_number
        }
        
        # Use different prompts based on round number
        if round_number == 1:
            analysis = ollama_client.generate_insights(event_data, response_data)
        else:
            # For subsequent rounds, include previous round context
            analysis = ollama_client.generate_round_insights(event_data, response_data, round_number)
        
        return {
            "event_id": event_id,
            "round_number": round_number,
            "event_title": event.title,
            "response_count": len(responses),
            "analysis": analysis,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Round analysis failed: {str(e)}")

@router.get("/ai/models")
async def get_available_models():
    """
    Get available Ollama models.
    """
    try:
        health_status = ollama_client.check_health()
        return {
            "available_models": health_status.get("available_models", []),
            "current_model": ollama_client.model,
            "status": health_status.get("status", "unknown")
        }
    except Exception as e:
        return {
            "available_models": [],
            "current_model": ollama_client.model,
            "status": "error",
            "error": str(e)
        } 

@router.get("/ai/sentiment-timeline/{event_id}")
async def sentiment_timeline(event_id: str, db: Session = Depends(get_local_db)):
    """
    Return a timeline of sentiment analysis for all responses in an event.
    """
    try:
        # Get all responses for the event
        responses_result = db.execute(text("""
            SELECT r.id, r.content, r.created_at
            FROM responses r
            JOIN inquiries i ON r.inquiry_id = i.id
            WHERE i.event_id = :event_id
            ORDER BY r.created_at ASC
        """), {"event_id": event_id})
        responses = responses_result.fetchall()
        if not responses:
            return {"event_id": event_id, "timeline": []}
        timeline = []
        for response in responses:
            content = response.content
            created_at = response.created_at
            if isinstance(created_at, str):
                created_at_str = created_at
            elif hasattr(created_at, 'isoformat'):
                created_at_str = created_at.isoformat()
            else:
                created_at_str = str(created_at) if created_at else None
            sentiment = ollama_client.analyze_sentiment(content)
            timeline.append({
                "response_id": response.id,
                "created_at": created_at_str,
                "sentiment": sentiment.get("sentiment", "neutral"),
                "confidence": sentiment.get("confidence", 0.0),
                "emotions": sentiment.get("emotions", []),
                "summary": sentiment.get("summary", "")
            })
        return {"event_id": event_id, "timeline": timeline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sentiment timeline: {str(e)}") 

@router.get("/ai/word-cloud/{event_id}")
async def word_cloud(event_id: str, db: Session = Depends(get_local_db), max_words: int = 50):
    """
    Return a list of keywords and their frequencies for all responses in an event, for word cloud visualization.
    """
    try:
        # Get all responses for the event
        responses_result = db.execute(text("""
            SELECT r.content
            FROM responses r
            JOIN inquiries i ON r.inquiry_id = i.id
            WHERE i.event_id = :event_id
        """), {"event_id": event_id})
        responses = [row.content for row in responses_result.fetchall() if row.content]
        if not responses:
            return {"event_id": event_id, "keywords": []}
        keywords_result = ollama_client.extract_keywords(responses, max_words)
        return {"event_id": event_id, "keywords": keywords_result.get("keywords", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate word cloud: {str(e)}") 

@router.get("/ai/consensus-graph/{event_id}")
async def consensus_graph(event_id: str, db: Session = Depends(get_local_db)):
    """
    Return consensus clusters and summary for all responses in an event, for consensus graph visualization.
    """
    try:
        # Get all responses for the event
        responses_result = db.execute(text("""
            SELECT r.content
            FROM responses r
            JOIN inquiries i ON r.inquiry_id = i.id
            WHERE i.event_id = :event_id
        """), {"event_id": event_id})
        responses = [row.content for row in responses_result.fetchall() if row.content]
        if not responses:
            return {"event_id": event_id, "consensus_clusters": [], "summary": "No responses found."}
        consensus_result = ollama_client.detect_consensus(responses)
        return {"event_id": event_id, "consensus_clusters": consensus_result.get("consensus_clusters", []), "summary": consensus_result.get("summary", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate consensus graph: {str(e)}") 

def _run_polis_analysis(responses: List[str], user_ids: List[str] = None):
    """
    Helper function to run the full Polis-style analysis pipeline.
    This function orchestrates the entire process from raw text to clustered opinions.
    """
    # Step 1: Extract a concise list of key statements from the batch of all responses.
    # This uses an LLM to find the core ideas expressed by participants.
    statements_result = ollama_client.extract_statements(responses)
    statements = statements_result.get("statements", [])
    if not statements:
        raise HTTPException(status_code=500, detail="Failed to extract statements for analysis.")

    # Step 2: For each individual response, map it against the list of extracted statements.
    # This determines whether a participant agrees, disagrees, or is neutral on each key statement.
    user_statement_matrix = []
    for i, response_text in enumerate(responses):
        mapping_result = ollama_client.map_response_to_statements(response_text, statements)
        # Use actual user_id if available, otherwise fall back to index-based ID
        actual_user_id = user_ids[i] if user_ids and i < len(user_ids) else f"participant_{i+1}"
        user_statement_matrix.append({
            "user_id": actual_user_id,
            "response": response_text,
            "mapping": mapping_result.get("mapping", [])
        })

    # Step 3: Perform dimensionality reduction and clustering on the user-statement matrix.
    # This converts the text-based agreement data into a numerical format,
    # then uses PCA and K-Means to find opinion groups.
    opinion_analyzer = OpinionAnalyzer()
    analysis_results = opinion_analyzer.analyze(user_statement_matrix, statements)

    return {
        "statements": statements,
        "analysis_results": analysis_results
    }


@router.get("/ai/polis-analysis/{event_id}/{round_number}")
async def polis_analysis_for_event_round(event_id: str, round_number: int, db: Session = Depends(get_local_db)):
    """
    Performs a Polis-style analysis on a round of responses for a specific event.
    """
    try:
        # Get responses for this specific round
        responses_result = db.execute(text("""
            SELECT r.content, r.user_id
            FROM responses r
            JOIN inquiries i ON r.inquiry_id = i.id
            WHERE i.event_id = :event_id AND i.round_number = :round_number
        """), {"event_id": event_id, "round_number": round_number})
        response_rows = responses_result.fetchall()
        responses = [row.content for row in response_rows]
        user_ids = [row.user_id for row in response_rows]
        
        if not responses:
            raise HTTPException(status_code=404, detail="No responses found for this event round.")

        return _run_polis_analysis(responses, user_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polis-style analysis for event round failed: {str(e)}") 