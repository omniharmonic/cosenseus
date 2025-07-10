import requests
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with Ollama for local AI analysis.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api"
        
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Ollama API.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Returns:
            API response
        """
        try:
            url = f"{self.api_url}/{endpoint}"
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise Exception(f"Ollama API request failed: {e}")
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate a response using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            
        Returns:
            Generated response
        """
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            data["system"] = system_prompt
            
        try:
            response = self._make_request("generate", data)
            return response.get("response", "")
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {e}"
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using Ollama.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis results
        """
        system_prompt = """You are a sentiment analysis expert. Analyze the sentiment of the given text and return a JSON response with the following structure:
        {
            "sentiment": "positive|negative|neutral",
            "confidence": 0.0-1.0,
            "emotions": ["emotion1", "emotion2"],
            "summary": "brief summary of the sentiment"
        }"""
        
        prompt = f"Analyze the sentiment of this text: {text}"
        
        try:
            response = self.generate_response(prompt, system_prompt)
            # Try to parse JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "emotions": [],
                    "summary": "Unable to parse sentiment analysis"
                }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "emotions": [],
                "summary": f"Error in sentiment analysis: {e}"
            }
    
    def cluster_responses(self, responses: List[str], num_clusters: int = 3) -> Dict[str, Any]:
        """
        Cluster similar responses using Ollama and generate 2D coordinates for visualization.
        Args:
            responses: List of response texts
            num_clusters: Number of clusters to create
        Returns:
            Clustering results with 2D coordinates for each response
        """
        if not responses:
            return {"clusters": [], "summary": "No responses to cluster"}
        system_prompt = f"""You are a clustering expert. Group the given responses into {num_clusters} clusters based on similarity of ideas and themes. Return a JSON response with the following structure:\n{{\n    \"clusters\": [\n        {{\n            \"id\": \"cluster_1\",\n            \"theme\": \"main theme of this cluster\",\n            \"responses\": [\"response1\", \"response2\"],\n            \"summary\": \"summary of this cluster's main points\"\n        }}\n    ],\n    \"overall_summary\": \"summary of all clusters\"\n}}"""
        responses_text = "\n".join([f"{i+1}. {response}" for i, response in enumerate(responses)])
        prompt = f"Cluster these responses:\n{responses_text}"
        try:
            response = self.generate_response(prompt, system_prompt)
            # Try to parse JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed = json.loads(json_str)
                # Add 2D coordinates for each response in each cluster
                import math
                clusters = parsed.get("clusters", [])
                total_clusters = len(clusters)
                for cidx, cluster in enumerate(clusters):
                    points = []
                    n = len(cluster.get("responses", []))
                    for ridx, resp_text in enumerate(cluster.get("responses", [])):
                        # Spread points in a circle per cluster
                        angle = 2 * math.pi * ridx / max(n, 1)
                        radius = 0.5 + 0.5 * cidx  # Different radius per cluster
                        x = radius * math.cos(angle)
                        y = radius * math.sin(angle)
                        points.append({"x": x, "y": y, "text": resp_text})
                    cluster["points"] = points
                parsed["clusters"] = clusters
                return parsed
            else:
                return {
                    "clusters": [],
                    "summary": "Unable to parse clustering results"
                }
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return {
                "clusters": [],
                "summary": f"Error in clustering: {e}"
            }
    
    def generate_insights(self, event_data: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate insights from event responses using Ollama.
        
        Args:
            event_data: Event information
            responses: List of response data
            
        Returns:
            Generated insights
        """
        system_prompt = """You are a civic engagement expert. Analyze the event responses and generate insights. Return a JSON response with the following structure:
        {
            "key_themes": ["theme1", "theme2"],
            "common_concerns": ["concern1", "concern2"],
            "suggested_actions": ["action1", "action2"],
            "participant_sentiment": "overall sentiment",
            "summary": "comprehensive summary of findings"
        }"""
        
        # Prepare response data for analysis
        response_texts = []
        for response in responses:
            if isinstance(response, dict):
                content = response.get('content', '')
                inquiry_title = response.get('inquiry_title', '')
                response_texts.append(f"Inquiry: {inquiry_title}\nResponse: {content}")
            else:
                response_texts.append(str(response))
        
        responses_text = "\n\n".join(response_texts)
        
        prompt = f"""Event: {event_data.get('title', 'Unknown Event')}
Description: {event_data.get('description', 'No description')}

Responses:
{responses_text}

Please analyze these responses and provide insights."""
        
        try:
            response = self.generate_response(prompt, system_prompt)
            # Try to parse JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {
                    "key_themes": [],
                    "common_concerns": [],
                    "suggested_actions": [],
                    "participant_sentiment": "neutral",
                    "summary": "Unable to parse analysis results"
                }
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            return {
                "key_themes": [],
                "common_concerns": [],
                "suggested_actions": [],
                "participant_sentiment": "neutral",
                "summary": f"Error in insights generation: {e}"
            }
    
    def generate_round_insights(self, event_data: Dict[str, Any], responses: List[Dict[str, Any]], round_number: int) -> Dict[str, Any]:
        """
        Generate insights for a specific round with context from previous rounds.
        
        Args:
            event_data: Event information
            responses: List of response data for this round
            round_number: Current round number
            
        Returns:
            Generated insights with round-specific analysis
        """
        system_prompt = f"""You are a civic engagement expert analyzing round {round_number} of a dialogue. 
        Based on the responses and the round context, provide insights that build on previous rounds.
        Return a JSON response with the following structure:
        {{
            "key_themes": ["theme1", "theme2"],
            "common_concerns": ["concern1", "concern2"],
            "suggested_actions": ["action1", "action2"],
            "consensus_points": ["consensus1", "consensus2"],
            "dialogue_opportunities": ["opportunity1", "opportunity2"],
            "participant_sentiment": "overall sentiment",
            "summary": "comprehensive summary of findings for this round"
        }}"""
        
        response_texts = [resp.get('content', '') for resp in responses]
        responses_text = "\n\n".join(response_texts)
        
        prompt = f"""Event: {event_data.get('title', 'Unknown Event')}
Round {round_number} Responses:
{responses_text}

Please analyze these round-specific responses and provide insights."""
        
        try:
            response = self.generate_response(prompt, system_prompt)
            logger.info(f"[DEBUG] Ollama raw response for round {round_number}: {response}")
            
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_result = json.loads(json_str)
                logger.info(f"[DEBUG] Parsed analysis result: {parsed_result}")
                return parsed_result
            else:
                logger.warning(f"[DEBUG] No valid JSON found in response: {response}")
                return {"summary": "Unable to parse round analysis"}
        except Exception as e:
            logger.error(f"Round insights generation failed: {e}")
            return {"summary": f"Error in round insights generation: {e}"}

    def generate_next_inquiries(self, synthesis_summary: str, previous_inquiries: List[str]) -> List[Dict[str, str]]:
        """
        Generate new inquiries for the next round based on a synthesis of the previous one.
        Args:
            synthesis_summary: A summary of the previous round's discussion.
            previous_inquiries: A list of questions from the previous round.
        Returns:
            A list of new inquiries, each as a dictionary with 'title' and 'content'.
        """
        system_prompt = """You are an expert dialogue facilitator. Your task is to generate 2-3 new, open-ended questions for the next round of a discussion. These questions should build upon the provided synthesis of the previous round, encouraging deeper reflection and moving the conversation forward. Avoid repeating previous questions.

Return a JSON response with a single key "inquiries" which is a list of objects, where each object has "title" and "content" keys. Example:
{
    "inquiries": [
        {
            "title": "Exploring Solutions",
            "content": "Based on the identified challenges, what potential solutions or new approaches could we explore as a group?"
        },
        {
            "title": "Uncovering Assumptions",
            "content": "What underlying assumptions might be shaping the different perspectives we've heard so far?"
        }
    ]
}
"""
        previous_inquiries_text = "\n".join(previous_inquiries)
        prompt = f"""Given the following synthesis of our last round of discussion:
---
{synthesis_summary}
---
And keeping in mind the previous questions that have already been asked:
---
{previous_inquiries_text}
---
Please generate the next set of inquiries."""

        try:
            response_str = self.generate_response(prompt, system_prompt)
            if "{" in response_str and "}" in response_str:
                start = response_str.find("{")
                end = response_str.rfind("}") + 1
                json_str = response_str[start:end]
                parsed_json = json.loads(json_str)
                # Ensure the response is a list of dicts with the correct keys
                inquiries = parsed_json.get("inquiries", [])
                if isinstance(inquiries, list) and all("title" in i and "content" in i for i in inquiries):
                    return inquiries
                else:
                    logger.warning(f"Ollama returned malformed inquiries: {inquiries}")
                    return []
            else:
                logger.warning(f"Ollama did not return valid JSON for inquiries: {response_str}")
                return []
        except Exception as e:
            logger.error(f"Failed to generate next inquiries: {e}")
            return []

    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the Ollama service.
        
        Returns:
            Health status
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                return {
                    "status": "healthy",
                    "available_models": model_names,
                    "target_model": self.model,
                    "model_available": self.model in model_names
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def extract_keywords(self, responses: List[str], max_words: int = 50) -> Dict[str, Any]:
        """
        Extract keywords and their frequencies from a list of responses using Ollama.
        Args:
            responses: List of response texts
            max_words: Maximum number of keywords to return
        Returns:
            Dict with 'keywords': list of {word, frequency}
        """
        if not responses:
            return {"keywords": []}
        system_prompt = f"""You are a keyword extraction expert. Analyze the following responses and extract the top {max_words} most important keywords or key phrases, along with their frequency counts. Return a JSON response with the following structure:\n{{\n  \"keywords\": [{{\"word\": \"keyword1\", \"frequency\": 5}}, ...]\n}}"""
        responses_text = "\n".join([f"- {response}" for response in responses])
        prompt = f"Extract keywords from these responses:\n{responses_text}"
        try:
            response = self.generate_response(prompt, system_prompt)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Keyword extraction failed to parse JSON: {e}. Response: {response_str}")
                    return {"keywords": []}
            else:
                logger.warning(f"Ollama did not return valid JSON for keywords: {response_str}")
                return {"keywords": []}
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return {"keywords": []}

    def detect_consensus(self, responses: List[str]) -> Dict[str, Any]:
        """
        Detect consensus and disagreement among responses using Ollama.
        Args:
            responses: List of response texts
        Returns:
            Dict with 'consensus_clusters': list of {cluster_label, responses, agreement_score}, 'summary': str
        """
        if not responses:
            return {"consensus_clusters": [], "summary": "No responses to analyze"}
        system_prompt = """You are a consensus detection expert. Group the following responses into clusters of agreement and disagreement. For each cluster, provide a label, the responses in that cluster, and an agreement_score from 0 (no agreement) to 1 (full agreement). Return a JSON response with the following structure:\n{\n  \"consensus_clusters\": [\n    {\n      \"cluster_label\": \"Agreement on X\",\n      \"responses\": [\"response1\", ...],\n      \"agreement_score\": 0.8\n    }\n  ],\n  \"summary\": \"brief summary of consensus and disagreement\"\n}"""
        responses_text = "\n".join([f"- {response}" for response in responses])
        prompt = f"Detect consensus in these responses:\n{responses_text}"
        try:
            response = self.generate_response(prompt, system_prompt)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"consensus_clusters": [], "summary": "Unable to parse consensus results"}
        except Exception as e:
            logger.error(f"Consensus detection failed: {e}")
            return {"consensus_clusters": [], "summary": f"Error in consensus detection: {e}"}

    def extract_statements(self, responses: List[str]) -> Dict[str, Any]:
        """
        Extract a concise list of key statements from a batch of responses.
        
        Args:
            responses: List of response texts
            
        Returns:
            Dict containing extracted statements
        """
        if not responses:
            return {"statements": []}
            
        system_prompt = """You are an expert at extracting key statements from participant responses. Analyze the provided responses and identify 5-8 core statements that capture the main ideas and opinions expressed. Each statement should be:
        - Concise and specific
        - Representative of a distinct viewpoint
        - Something people can agree or disagree with
        
        Return a JSON response with the following structure:
        {
            "statements": [
                "Clear, concise statement 1",
                "Clear, concise statement 2",
                ...
            ]
        }"""
        
        responses_text = "\n".join([f"Response {i+1}: {response}" for i, response in enumerate(responses)])
        prompt = f"Extract key statements from these responses:\n\n{responses_text}"
        
        try:
            response = self.generate_response(prompt, system_prompt)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_result = json.loads(json_str)
                statements = parsed_result.get("statements", [])
                # Ensure we have a reasonable number of statements
                if len(statements) > 10:
                    statements = statements[:10]
                elif len(statements) < 3:
                    # Generate some default statements if too few
                    statements.extend([
                        "This issue affects our community",
                        "Action is needed to address this concern",
                        "Multiple perspectives should be considered"
                    ])
                return {"statements": statements}
            else:
                logger.warning(f"No valid JSON found in statement extraction: {response}")
                return {"statements": ["Unable to extract statements"]}
        except Exception as e:
            logger.error(f"Statement extraction failed: {e}")
            return {"statements": ["Error extracting statements"]}

    def map_response_to_statements(self, response_text: str, statements: List[str]) -> Dict[str, Any]:
        """
        Map an individual response to the extracted statements.
        
        Args:
            response_text: The individual response to map
            statements: List of extracted statements
            
        Returns:
            Dict containing the mapping results
        """
        if not statements:
            return {"mapping": []}
            
        system_prompt = """You are an expert at analyzing how participant responses relate to key statements. For each statement provided, determine whether the given response agrees, disagrees, or is neutral/passes on that statement.

        Return a JSON response with the following structure:
        {
            "mapping": [
                {
                    "statement": "exact statement text",
                    "position": "agree|disagree|pass"
                }
            ]
        }
        
        Guidelines:
        - "agree": The response clearly supports or aligns with the statement
        - "disagree": The response clearly opposes or contradicts the statement  
        - "pass": The response is neutral, unclear, or doesn't address the statement"""
        
        statements_text = "\n".join([f"{i+1}. {stmt}" for i, stmt in enumerate(statements)])
        prompt = f"""Response to analyze: "{response_text}"

Statements to map against:
{statements_text}

For each statement, determine if the response agrees, disagrees, or passes."""
        
        try:
            response = self.generate_response(prompt, system_prompt)
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed_result = json.loads(json_str)
                mapping = parsed_result.get("mapping", [])
                
                # Ensure all statements are covered
                covered_statements = {m.get("statement", "") for m in mapping}
                for statement in statements:
                    if statement not in covered_statements:
                        mapping.append({
                            "statement": statement,
                            "position": "pass"
                        })
                
                return {"mapping": mapping}
            else:
                logger.warning(f"No valid JSON found in response mapping: {response}")
                # Return default pass mapping for all statements
                return {"mapping": [{"statement": stmt, "position": "pass"} for stmt in statements]}
        except Exception as e:
            logger.error(f"Response mapping failed: {e}")
            # Return default pass mapping for all statements
            return {"mapping": [{"statement": stmt, "position": "pass"} for stmt in statements]}

# Global Ollama client instance
ollama_client = OllamaClient() 