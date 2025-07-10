from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import sys
import os
import json
from datetime import datetime, timezone
from pydantic import BaseModel

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from core.database_local import get_local_db
# Import local database models
from shared.models.database import Event, Inquiry, Response
from nlp_service.ollama_client import ollama_client
from nlp_service.core.opinion_analyzer import OpinionAnalyzer
from .auth import get_current_user

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
        from sqlalchemy import text
        
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
        from sqlalchemy import text
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
        from sqlalchemy import text
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
        from sqlalchemy import text
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

def _run_polis_analysis(responses: List[str]):
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
        user_statement_matrix.append({
            "user_id": f"participant_{i+1}",  # Using index as a placeholder user ID
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
        "user_positions": analysis_results
    }


@router.post("/ai/polis-analysis/event/{event_id}/round/{round_number}")
async def polis_analysis_for_event_round(event_id: str, round_number: int, db: Session = Depends(get_local_db)):
    """
    Performs a Polis-style analysis on a round of responses for a specific event.
    """
    try:
        # Get responses for this specific round
        responses_result = db.execute(text("""
            SELECT r.content
            FROM responses r
            WHERE r.event_id = :event_id AND r.round_number = :round_number
        """), {"event_id": event_id, "round_number": round_number})
        responses = [row[0] for row in responses_result.fetchall()]
        
        if not responses:
            raise HTTPException(status_code=404, detail="No responses found for this event round.")

        return _run_polis_analysis(responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polis-style analysis for event round failed: {str(e)}") 