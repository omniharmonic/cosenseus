"""
Sentiment Analysis Engine for Civic Discourse
Analyzes emotional tone, certainty, and civic engagement sentiment
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from textblob import TextBlob
import numpy as np

@dataclass
class SentimentScores:
    """Comprehensive sentiment analysis results"""
    polarity: float  # -1 (negative) to 1 (positive)
    subjectivity: float  # 0 (objective) to 1 (subjective)
    certainty: float  # 0 (uncertain) to 1 (certain)
    civic_engagement: float  # 0 (low) to 1 (high civic engagement)
    emotional_intensity: float  # 0 (neutral) to 1 (highly emotional)
    constructiveness: float  # 0 (destructive) to 1 (constructive)
    
class SentimentAnalyzer:
    """
    Advanced sentiment analysis for civic discourse
    """
    
    def __init__(self):
        """Initialize sentiment analyzer with civic-specific lexicons"""
        
        # Civic engagement indicators
        self.civic_positive_terms = {
            'democracy', 'citizen', 'community', 'together', 'collaborate', 'participate',
            'vote', 'engage', 'discuss', 'listen', 'understand', 'compromise', 'solution',
            'progress', 'improve', 'build', 'develop', 'contribute', 'support', 'help',
            'fair', 'justice', 'equal', 'rights', 'freedom', 'transparent', 'accountable'
        }
        
        self.civic_negative_terms = {
            'corrupt', 'broken', 'fail', 'problem', 'crisis', 'disaster', 'terrible',
            'awful', 'disgrace', 'shameful', 'outrageous', 'unacceptable', 'ridiculous'
        }
        
        # Certainty indicators
        self.certainty_high = {
            'definitely', 'absolutely', 'certainly', 'clearly', 'obviously', 'undoubtedly',
            'without question', 'no doubt', 'sure', 'confident', 'positive', 'convinced',
            'always', 'never', 'must', 'will', 'fact', 'truth', 'proven', 'established'
        }
        
        self.certainty_low = {
            'maybe', 'perhaps', 'possibly', 'might', 'could', 'seems', 'appears',
            'think', 'believe', 'suppose', 'guess', 'uncertain', 'unsure', 'doubt',
            'probably', 'likely', 'tend to', 'may be', 'sort of', 'kind of'
        }
        
        # Constructiveness indicators
        self.constructive_terms = {
            'solution', 'resolve', 'fix', 'improve', 'better', 'progress', 'develop',
            'build', 'create', 'innovate', 'collaborate', 'cooperate', 'work together',
            'compromise', 'find common ground', 'understand', 'learn', 'grow', 'move forward'
        }
        
        self.destructive_terms = {
            'destroy', 'ruin', 'damage', 'harm', 'attack', 'blame', 'fight', 'war',
            'enemy', 'hate', 'stupid', 'idiot', 'moron', 'ridiculous', 'pathetic',
            'waste', 'pointless', 'hopeless', 'impossible', 'never work'
        }
        
        # Emotional intensity markers
        self.high_intensity_markers = {
            'extremely', 'incredibly', 'absolutely', 'totally', 'completely', 'utterly',
            'shocking', 'outrageous', 'amazing', 'terrible', 'wonderful', 'awful',
            'fantastic', 'horrible', 'brilliant', 'disgusting', 'love', 'hate'
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive sentiment analysis of text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with detailed sentiment analysis
        """
        if not text or not isinstance(text, str):
            return self._empty_sentiment_result()
        
        # Clean and prepare text
        clean_text = self._prepare_text(text)
        
        # Basic sentiment using TextBlob
        blob = TextBlob(clean_text)
        
        # Calculate various sentiment dimensions
        scores = SentimentScores(
            polarity=blob.sentiment.polarity,
            subjectivity=blob.sentiment.subjectivity,
            certainty=self._analyze_certainty(clean_text),
            civic_engagement=self._analyze_civic_engagement(clean_text),
            emotional_intensity=self._analyze_emotional_intensity(clean_text),
            constructiveness=self._analyze_constructiveness(clean_text)
        )
        
        # Generate sentiment classification
        sentiment_class = self._classify_sentiment(scores)
        
        # Extract emotional indicators
        emotions = self._extract_emotions(clean_text)
        
        # Calculate confidence scores
        confidence = self._calculate_confidence(clean_text, scores)
        
        return {
            "sentiment_scores": {
                "polarity": round(scores.polarity, 3),
                "subjectivity": round(scores.subjectivity, 3),
                "certainty": round(scores.certainty, 3),
                "civic_engagement": round(scores.civic_engagement, 3),
                "emotional_intensity": round(scores.emotional_intensity, 3),
                "constructiveness": round(scores.constructiveness, 3)
            },
            "sentiment_classification": sentiment_class,
            "emotional_indicators": emotions,
            "confidence_score": round(confidence, 3),
            "civic_analysis": {
                "engagement_level": self._classify_engagement(scores.civic_engagement),
                "tone": self._classify_tone(scores.polarity, scores.constructiveness),
                "certainty_level": self._classify_certainty(scores.certainty)
            },
            "text_length": len(text),
            "word_count": len(clean_text.split())
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        return [self.analyze_sentiment(text) for text in texts]
    
    def _prepare_text(self, text: str) -> str:
        """Prepare text for analysis"""
        # Basic cleaning while preserving sentiment markers
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned.lower()
    
    def _analyze_certainty(self, text: str) -> float:
        """Analyze certainty level in text"""
        words = set(text.split())
        
        high_certainty_count = len(words.intersection(self.certainty_high))
        low_certainty_count = len(words.intersection(self.certainty_low))
        
        # Calculate certainty score
        if high_certainty_count + low_certainty_count == 0:
            return 0.5  # Neutral certainty
        
        certainty_ratio = high_certainty_count / (high_certainty_count + low_certainty_count + 1)
        return min(1.0, max(0.0, certainty_ratio))
    
    def _analyze_civic_engagement(self, text: str) -> float:
        """Analyze civic engagement level"""
        words = set(text.split())
        
        positive_civic = len(words.intersection(self.civic_positive_terms))
        negative_civic = len(words.intersection(self.civic_negative_terms))
        
        # Calculate civic engagement (positive civic terms indicate higher engagement)
        total_civic = positive_civic + negative_civic
        if total_civic == 0:
            return 0.3  # Low baseline engagement
        
        engagement_score = (positive_civic + 0.3 * negative_civic) / (len(words) / 10)
        return min(1.0, max(0.0, engagement_score))
    
    def _analyze_emotional_intensity(self, text: str) -> float:
        """Analyze emotional intensity"""
        words = set(text.split())
        
        intensity_markers = len(words.intersection(self.high_intensity_markers))
        
        # Check for caps (emotional indicator)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        # Check for exclamation marks
        exclamation_count = text.count('!')
        
        # Combine indicators
        intensity_score = (
            (intensity_markers / max(len(words), 1)) * 0.5 +
            caps_ratio * 0.3 +
            min(exclamation_count / 3, 1) * 0.2
        )
        
        return min(1.0, max(0.0, intensity_score))
    
    def _analyze_constructiveness(self, text: str) -> float:
        """Analyze constructiveness of the discourse"""
        words = set(text.split())
        
        constructive_count = len(words.intersection(self.constructive_terms))
        destructive_count = len(words.intersection(self.destructive_terms))
        
        if constructive_count + destructive_count == 0:
            return 0.5  # Neutral constructiveness
        
        constructive_ratio = constructive_count / (constructive_count + destructive_count + 1)
        return min(1.0, max(0.0, constructive_ratio))
    
    def _classify_sentiment(self, scores: SentimentScores) -> str:
        """Classify overall sentiment"""
        if scores.polarity > 0.3:
            return "positive"
        elif scores.polarity < -0.3:
            return "negative"
        else:
            return "neutral"
    
    def _classify_engagement(self, engagement_score: float) -> str:
        """Classify civic engagement level"""
        if engagement_score > 0.7:
            return "high"
        elif engagement_score > 0.4:
            return "moderate"
        else:
            return "low"
    
    def _classify_tone(self, polarity: float, constructiveness: float) -> str:
        """Classify discourse tone"""
        if constructiveness > 0.6 and polarity > 0:
            return "constructive_positive"
        elif constructiveness > 0.6 and polarity < 0:
            return "constructive_critical"
        elif constructiveness < 0.4 and polarity < -0.3:
            return "destructive_negative"
        elif polarity > 0.5:
            return "enthusiastic"
        elif polarity < -0.5:
            return "critical"
        else:
            return "neutral"
    
    def _classify_certainty(self, certainty_score: float) -> str:
        """Classify certainty level"""
        if certainty_score > 0.7:
            return "highly_certain"
        elif certainty_score > 0.5:
            return "moderately_certain"
        elif certainty_score > 0.3:
            return "somewhat_uncertain"
        else:
            return "highly_uncertain"
    
    def _extract_emotions(self, text: str) -> List[str]:
        """Extract emotional indicators from text"""
        emotions = []
        
        # Simple emotion detection based on keywords
        emotion_keywords = {
            "joy": ["happy", "joy", "excited", "pleased", "delighted", "cheerful"],
            "anger": ["angry", "mad", "furious", "outraged", "frustrated", "irritated"],
            "fear": ["afraid", "scared", "worried", "anxious", "concerned", "nervous"],
            "sadness": ["sad", "depressed", "disappointed", "upset", "unhappy"],
            "hope": ["hope", "optimistic", "confident", "hopeful", "positive"],
            "concern": ["concerned", "worried", "troubled", "bothered", "uneasy"]
        }
        
        words = text.split()
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text for keyword in keywords):
                emotions.append(emotion)
        
        return emotions
    
    def _calculate_confidence(self, text: str, scores: SentimentScores) -> float:
        """Calculate confidence in sentiment analysis"""
        # Base confidence on text length and clarity of indicators
        text_length_factor = min(len(text.split()) / 20, 1.0)  # Longer text = higher confidence
        
        # Higher certainty and emotional intensity usually mean clearer sentiment
        clarity_factor = (scores.certainty + scores.emotional_intensity) / 2
        
        # Moderate polarity often more reliable than extreme
        polarity_confidence = 1 - abs(abs(scores.polarity) - 0.5) * 2
        
        confidence = (text_length_factor * 0.3 + clarity_factor * 0.4 + polarity_confidence * 0.3)
        return min(1.0, max(0.1, confidence))
    
    def _empty_sentiment_result(self) -> Dict[str, Any]:
        """Return empty sentiment result for invalid input"""
        return {
            "sentiment_scores": {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "certainty": 0.0,
                "civic_engagement": 0.0,
                "emotional_intensity": 0.0,
                "constructiveness": 0.5
            },
            "sentiment_classification": "neutral",
            "emotional_indicators": [],
            "confidence_score": 0.0,
            "civic_analysis": {
                "engagement_level": "none",
                "tone": "neutral",
                "certainty_level": "uncertain"
            },
            "text_length": 0,
            "word_count": 0
        } 