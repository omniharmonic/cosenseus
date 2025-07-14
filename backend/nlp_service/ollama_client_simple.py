import requests
import json
import re
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleOllamaClient:
    """
    Simplified Ollama client focused on reliability over performance.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        self.base_url = base_url
        self.model = model  # Use smaller 3b model for stability
        self.api_url = f"{base_url}/api"
        self.timeout = 60  # Longer timeout
        self.max_retries = 1  # Reduce retries to avoid overload
        
    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama is running and model is available."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code != 200:
                return {"status": "unhealthy", "error": "Ollama not responding"}
            
            # Check available models
            models_response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if models_response.status_code == 200:
                models = models_response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                return {
                    "status": "healthy",
                    "available_models": model_names,
                    "target_model": self.model,
                    "model_available": self.model in model_names
                }
            else:
                return {"status": "unhealthy", "error": "Cannot check models"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from response with fallback strategies."""
        if not response:
            return None
            
        # Try to parse entire response
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
            
        # Extract JSON from braces
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
            
        logger.warning(f"Failed to extract JSON from response: {response[:200]}...")
        return None
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response with simplified error handling."""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 512  # Limit response length
            }
        }
        
        if system_prompt:
            data["system"] = system_prompt
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Ollama request attempt {attempt + 1}/{self.max_retries + 1}")
                response = requests.post(
                    f"{self.api_url}/generate", 
                    json=data, 
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"Ollama returned status {response.status_code}: {response.text}")
                    if attempt < self.max_retries:
                        time.sleep(5)  # Wait before retry
                        continue
                    else:
                        return f"Error: Ollama returned status {response.status_code}"
                        
            except requests.exceptions.Timeout:
                logger.error(f"Ollama request timed out after {self.timeout} seconds")
                if attempt < self.max_retries:
                    time.sleep(5)
                    continue
                else:
                    return "Error: Request timed out"
            except Exception as e:
                logger.error(f"Ollama request failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(5)
                    continue
                else:
                    return f"Error: {e}"
        
        return "Error: All attempts failed"
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment with fallback structure."""
        system_prompt = """You are a sentiment analysis expert. Analyze the sentiment and return JSON:
        {
            "sentiment": "positive|negative|neutral",
            "confidence": 0.0-1.0,
            "emotions": ["emotion1", "emotion2"],
            "summary": "brief summary"
        }"""
        
        prompt = f"Analyze sentiment: {text}"
        
        response = self.generate_response(prompt, system_prompt)
        
        # Try to extract JSON
        parsed = self._extract_json_from_response(response)
        if parsed:
            return parsed
        
        # Fallback structure
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "emotions": [],
            "summary": "Analysis unavailable"
        }
    
    def generate_insights(self, event_data: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights with conservative approach."""
        system_prompt = """You are a civic engagement expert. Analyze responses and return JSON:
        {
            "key_themes": ["theme1", "theme2"],
            "common_concerns": ["concern1", "concern2"],
            "suggested_actions": ["action1", "action2"],
            "consensus_points": ["consensus1", "consensus2"],
            "dialogue_opportunities": ["opportunity1", "opportunity2"],
            "common_desired_outcomes": ["outcome1", "outcome2"],
            "common_strategies": ["strategy1", "strategy2"],
            "common_values": ["value1", "value2"],
            "participant_sentiment": "overall sentiment",
            "summary": "summary of findings"
        }"""
        
        # Prepare simplified response data
        response_texts = []
        for response in responses[:10]:  # Limit to 10 responses to avoid overwhelming
            if isinstance(response, dict):
                content = response.get('content', '')
                response_texts.append(content[:200])  # Limit length
            else:
                response_texts.append(str(response)[:200])
        
        responses_text = "\n".join(response_texts)
        
        prompt = f"""Event: {event_data.get('title', 'Unknown Event')}
        
Responses:
{responses_text}

Analyze these responses."""
        
        response = self.generate_response(prompt, system_prompt)
        
        # Try to extract JSON
        parsed = self._extract_json_from_response(response)
        if parsed:
            return parsed
        
        # Fallback structure
        return {
            "key_themes": ["Analysis in progress"],
            "common_concerns": ["Gathering feedback"],
            "suggested_actions": ["Continue dialogue"],
            "consensus_points": ["Shared participation"],
            "dialogue_opportunities": ["Further discussion needed"],
            "common_desired_outcomes": ["Collaborative outcomes"],
            "common_strategies": ["Inclusive approach"],
            "common_values": ["Community engagement"],
            "participant_sentiment": "neutral",
            "summary": "Analysis is being processed"
        }

# Create a simple client instance
simple_ollama_client = SimpleOllamaClient()