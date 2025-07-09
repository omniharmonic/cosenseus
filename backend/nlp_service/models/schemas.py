"""
Pydantic models for NLP service requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ProcessingOptions(BaseModel):
    """Text processing configuration options"""
    remove_punctuation: bool = Field(default=True, description="Remove punctuation marks")
    remove_numbers: bool = Field(default=False, description="Remove numeric tokens")
    remove_stopwords: bool = Field(default=False, description="Remove common stopwords")
    lowercase: bool = Field(default=True, description="Convert text to lowercase")
    remove_extra_whitespace: bool = Field(default=True, description="Normalize whitespace")
    remove_urls: bool = Field(default=True, description="Remove URL patterns")
    remove_emails: bool = Field(default=True, description="Remove email addresses")
    remove_html: bool = Field(default=True, description="Remove HTML tags")
    normalize_unicode: bool = Field(default=True, description="Normalize unicode characters")
    stem_words: bool = Field(default=False, description="Apply word stemming")
    lemmatize_words: bool = Field(default=False, description="Apply word lemmatization")
    min_word_length: int = Field(default=1, ge=1, description="Minimum word length")
    max_word_length: int = Field(default=50, le=100, description="Maximum word length")
    preserve_sentence_structure: bool = Field(default=False, description="Maintain sentence boundaries")

class TextProcessingRequest(BaseModel):
    """Request model for text preprocessing"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to process")
    options: Optional[ProcessingOptions] = Field(default=None, description="Processing configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello world! This is a sample text for processing.",
                "options": {
                    "remove_punctuation": True,
                    "lowercase": True,
                    "remove_stopwords": False
                }
            }
        }

class BatchTextProcessingRequest(BaseModel):
    """Request model for batch text preprocessing"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to process")
    options: Optional[ProcessingOptions] = Field(default=None, description="Processing configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "First text to process.",
                    "Second text for batch processing."
                ],
                "options": {
                    "remove_punctuation": True,
                    "lowercase": True
                }
            }
        }

class ProcessingMetadata(BaseModel):
    """Metadata about text processing operations"""
    original_length: int = Field(..., description="Original text length")
    final_length: int = Field(..., description="Final text length")
    token_count: int = Field(..., description="Number of tokens")
    compression_ratio: float = Field(..., description="Text compression ratio")
    processing_steps: List[str] = Field(..., description="Applied processing steps")
    language: str = Field(default="en", description="Detected or assumed language")
    civic_terms_found: List[str] = Field(default=[], description="Civic discourse terms found")
    tokens_filtered: Optional[int] = Field(default=None, description="Number of tokens filtered out")
    processing_complete: bool = Field(default=True, description="Processing completion status")
    error: Optional[str] = Field(default=None, description="Error message if any")

class TextProcessingResponse(BaseModel):
    """Response model for text preprocessing"""
    original_text: str = Field(..., description="Original input text")
    processed_text: str = Field(..., description="Fully processed text")
    tokens: List[str] = Field(..., description="Extracted tokens")
    cleaned_text: str = Field(..., description="Cleaned text")
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "Hello world! This is a sample text.",
                "processed_text": "hello world sample text",
                "tokens": ["hello", "world", "sample", "text"],
                "cleaned_text": "hello world sample text",
                "metadata": {
                    "original_length": 36,
                    "final_length": 24,
                    "token_count": 4,
                    "compression_ratio": 0.67,
                    "processing_steps": ["whitespace_normalization", "token_processing"],
                    "language": "en",
                    "civic_terms_found": [],
                    "processing_complete": True
                }
            }
        }

class BatchProcessingResult(BaseModel):
    """Single result in batch processing"""
    original_text: str = Field(..., description="Original input text")
    processed_text: str = Field(..., description="Fully processed text")
    tokens: List[str] = Field(..., description="Extracted tokens")
    cleaned_text: str = Field(..., description="Cleaned text")
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")

class BatchTextProcessingResponse(BaseModel):
    """Response model for batch text preprocessing"""
    results: List[BatchProcessingResult] = Field(..., description="Processing results for each text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "original_text": "First text to process.",
                        "processed_text": "first text process",
                        "tokens": ["first", "text", "process"],
                        "cleaned_text": "first text process",
                        "metadata": {
                            "original_length": 21,
                            "final_length": 18,
                            "token_count": 3,
                            "compression_ratio": 0.86,
                            "processing_steps": ["whitespace_normalization"],
                            "language": "en",
                            "civic_terms_found": [],
                            "processing_complete": True
                        }
                    }
                ]
            }
        }

# Additional response models for specific endpoints

class NormalizationResponse(BaseModel):
    """Response for text normalization"""
    original_text: str = Field(..., description="Original input text")
    normalized_text: str = Field(..., description="Normalized text")

class CleaningResponse(BaseModel):
    """Response for text cleaning"""
    original_text: str = Field(..., description="Original input text")
    cleaned_text: str = Field(..., description="Cleaned text")

class TokenizationResponse(BaseModel):
    """Response for text tokenization"""
    original_text: str = Field(..., description="Original input text")
    tokens: List[str] = Field(..., description="Extracted tokens")
    token_count: int = Field(..., description="Number of tokens")
    tokenize_by: str = Field(..., description="Tokenization method used")

# Error response models

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error: str = Field(default="Validation Error", description="Error type")
    details: List[Dict[str, Any]] = Field(..., description="Validation error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

# Sentiment Analysis Models

class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to analyze for sentiment")
    include_emotions: bool = Field(default=True, description="Include emotional indicators")
    include_civic_analysis: bool = Field(default=True, description="Include civic discourse analysis")

class SentimentScores(BaseModel):
    """Detailed sentiment scores"""
    polarity: float = Field(..., ge=-1, le=1, description="Sentiment polarity (-1 negative to 1 positive)")
    subjectivity: float = Field(..., ge=0, le=1, description="Subjectivity (0 objective to 1 subjective)")
    certainty: float = Field(..., ge=0, le=1, description="Certainty level (0 uncertain to 1 certain)")
    civic_engagement: float = Field(..., ge=0, le=1, description="Civic engagement level")
    emotional_intensity: float = Field(..., ge=0, le=1, description="Emotional intensity")
    constructiveness: float = Field(..., ge=0, le=1, description="Constructiveness of discourse")

class CivicAnalysis(BaseModel):
    """Civic discourse analysis"""
    engagement_level: str = Field(..., description="Level of civic engagement")
    tone: str = Field(..., description="Overall tone of discourse")
    certainty_level: str = Field(..., description="Level of certainty expressed")

class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis"""
    text: str = Field(..., description="Original text analyzed")
    sentiment_scores: SentimentScores = Field(..., description="Detailed sentiment scores")
    sentiment_classification: str = Field(..., description="Overall sentiment classification")
    emotional_indicators: List[str] = Field(..., description="Detected emotional indicators")
    civic_analysis: CivicAnalysis = Field(..., description="Civic discourse analysis")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in analysis")
    text_length: int = Field(..., description="Length of analyzed text")
    word_count: int = Field(..., description="Number of words analyzed")
    processing_time_seconds: float = Field(..., description="Time taken for analysis")

class BatchSentimentRequest(BaseModel):
    """Request model for batch sentiment analysis"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to analyze")
    include_emotions: bool = Field(default=True, description="Include emotional indicators")
    include_civic_analysis: bool = Field(default=True, description="Include civic discourse analysis")

class BatchSentimentResponse(BaseModel):
    """Response model for batch sentiment analysis"""
    results: List[SentimentAnalysisResponse] = Field(..., description="List of sentiment analysis results")
    total_analyzed: int = Field(..., description="Total number of texts analyzed")
    average_confidence: float = Field(..., description="Average confidence across all analyses")
    processing_time_seconds: float = Field(..., description="Total processing time")

# Embeddings Models

class EmbeddingRequest(BaseModel):
    """Request model for text embedding generation"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to generate embeddings for")

class BatchEmbeddingRequest(BaseModel):
    """Request model for batch embedding generation"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to generate embeddings for")

class EmbeddingResponse(BaseModel):
    """Response model for text embedding"""
    text: str = Field(..., description="Original text")
    embedding: List[float] = Field(..., description="Generated embedding vector")
    embedding_dimension: int = Field(..., description="Dimension of embedding vector")
    model_type: str = Field(..., description="Type of model used for embeddings")

class BatchEmbeddingResponse(BaseModel):
    """Response model for batch embedding generation"""
    results: List[EmbeddingResponse] = Field(..., description="List of embedding results")
    total_processed: int = Field(..., description="Total number of texts processed")
    processing_time_seconds: float = Field(..., description="Total processing time")

class SimilarityRequest(BaseModel):
    """Request model for text similarity computation"""
    text1: str = Field(..., min_length=1, max_length=50000, description="First text")
    text2: str = Field(..., min_length=1, max_length=50000, description="Second text")

class SimilarityResponse(BaseModel):
    """Response model for text similarity"""
    text1: str = Field(..., description="First text")
    text2: str = Field(..., description="Second text")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score between 0 and 1")
    processing_time_seconds: float = Field(..., description="Time taken for computation")

class SimilarTextSearchRequest(BaseModel):
    """Request model for finding similar texts"""
    query_text: str = Field(..., min_length=1, max_length=50000, description="Query text to find similarities for")
    candidate_texts: List[str] = Field(..., min_items=1, max_items=1000, description="Candidate texts to search through")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top results to return")

class SimilarTextResult(BaseModel):
    """Single result in similar text search"""
    text: str = Field(..., description="Similar text found")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score")

class SimilarTextSearchResponse(BaseModel):
    """Response model for similar text search"""
    query_text: str = Field(..., description="Original query text")
    results: List[SimilarTextResult] = Field(..., description="Similar texts found")
    total_candidates: int = Field(..., description="Total number of candidate texts searched")
    processing_time_seconds: float = Field(..., description="Time taken for search")

# Clustering Models

class ClusteringRequest(BaseModel):
    """Request model for response clustering"""
    responses: List[str] = Field(..., min_items=2, max_items=1000, description="List of responses to cluster")
    algorithm: str = Field(default="kmeans", description="Clustering algorithm to use")
    n_clusters: Optional[int] = Field(default=None, ge=2, le=20, description="Number of clusters (for K-means)")
    min_cluster_size: int = Field(default=2, ge=1, description="Minimum responses per cluster")

class ClusterInfo(BaseModel):
    """Information about a single cluster"""
    cluster_id: int = Field(..., description="Cluster identifier")
    centroid: List[float] = Field(..., description="Cluster centroid vector")
    responses: List[str] = Field(..., description="Responses in this cluster")
    response_indices: List[int] = Field(..., description="Indices of responses in this cluster")
    size: int = Field(..., description="Number of responses in cluster")
    coherence_score: float = Field(..., ge=0, le=1, description="Cluster coherence score")
    representative_text: str = Field(..., description="Most representative text in cluster")

class ConsensusArea(BaseModel):
    """Information about a consensus area"""
    cluster_id: int = Field(..., description="Cluster identifier")
    representative_text: str = Field(..., description="Representative text for consensus")
    coherence_score: float = Field(..., ge=0, le=1, description="Coherence score")
    size: int = Field(..., description="Number of responses in consensus")
    consensus_strength: float = Field(..., description="Overall consensus strength")

class ClusteringStatistics(BaseModel):
    """Statistics about clustering results"""
    total_clusters: int = Field(..., description="Total number of clusters")
    average_cluster_size: float = Field(..., description="Average responses per cluster")
    min_cluster_size: int = Field(..., description="Minimum cluster size")
    max_cluster_size: int = Field(..., description="Maximum cluster size")
    average_coherence: float = Field(..., ge=0, le=1, description="Average cluster coherence")
    min_coherence: float = Field(..., ge=0, le=1, description="Minimum cluster coherence")
    max_coherence: float = Field(..., ge=0, le=1, description="Maximum cluster coherence")
    cluster_size_distribution: Dict[str, int] = Field(..., description="Distribution of cluster sizes")

class ClusteringResponse(BaseModel):
    """Response model for clustering operation"""
    clusters: List[ClusterInfo] = Field(..., description="List of clusters")
    statistics: ClusteringStatistics = Field(..., description="Clustering statistics")
    consensus_areas: List[ConsensusArea] = Field(..., description="Identified consensus areas")
    total_responses: int = Field(..., description="Total number of responses clustered")
    total_clusters: int = Field(..., description="Total number of clusters formed")
    algorithm_used: str = Field(..., description="Algorithm used for clustering")
    optimal_clusters: int = Field(..., description="Optimal number of clusters determined")
    processing_time_seconds: float = Field(..., description="Time taken for clustering") 