"""
NLP Service - Text Processing and Analysis
Main FastAPI application for natural language processing tasks
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import numpy as np
from typing import List, Optional, Dict, Any

from core.text_processor import TextProcessor
from core.sentiment_analyzer import SentimentAnalyzer
from core.embeddings_generator import EmbeddingsGenerator, EmbeddingConfig
from core.clustering_engine import ClusteringEngine, ClusterConfig
from models.schemas import (
    TextProcessingRequest,
    TextProcessingResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    BatchSentimentRequest,
    BatchSentimentResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    SimilarityRequest,
    SimilarityResponse,
    SimilarTextSearchRequest,
    SimilarTextSearchResponse,
    ClusteringRequest,
    ClusteringResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Civic Sense-Making NLP Service",
    description="Natural Language Processing service for text analysis and processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
text_processor = TextProcessor()
sentiment_analyzer = SentimentAnalyzer()
embeddings_generator = EmbeddingsGenerator()
clustering_engine = ClusteringEngine()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Civic Sense-Making NLP Service",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "nlp_service",
        "version": "1.0.0"
    }

@app.post("/text/preprocess", response_model=TextProcessingResponse)
async def preprocess_text(request: TextProcessingRequest):
    """
    Preprocess text input with tokenization, cleaning, and normalization
    """
    try:
        result = text_processor.preprocess(
            text=request.text,
            options=request.options
        )
        
        return TextProcessingResponse(
            original_text=request.text,
            processed_text=result["processed_text"],
            tokens=result["tokens"],
            cleaned_text=result["cleaned_text"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")

@app.post("/text/preprocess/batch", response_model=BatchTextProcessingResponse)
async def preprocess_text_batch(request: BatchTextProcessingRequest):
    """
    Batch preprocess multiple text inputs
    """
    try:
        results = []
        for text in request.texts:
            result = text_processor.preprocess(
                text=text,
                options=request.options
            )
            results.append({
                "original_text": text,
                "processed_text": result["processed_text"],
                "tokens": result["tokens"],
                "cleaned_text": result["cleaned_text"],
                "metadata": result["metadata"]
            })
        
        return BatchTextProcessingResponse(results=results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch text processing failed: {str(e)}")

@app.post("/text/normalize")
async def normalize_text(request: dict):
    """
    Normalize text for consistent processing
    """
    try:
        text = request.get("text", "")
        normalized = text_processor.normalize_text(text)
        
        return {
            "original_text": text,
            "normalized_text": normalized
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text normalization failed: {str(e)}")

@app.post("/text/clean")
async def clean_text(request: dict):
    """
    Clean text by removing unwanted characters and formatting
    """
    try:
        text = request.get("text", "")
        options = request.get("options", {})
        
        cleaned = text_processor.clean_text(text, options)
        
        return {
            "original_text": text,
            "cleaned_text": cleaned
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text cleaning failed: {str(e)}")

@app.post("/text/tokenize")
async def tokenize_text(request: dict):
    """
    Tokenize text into words, sentences, or other units
    """
    try:
        text = request.get("text", "")
        tokenize_by = request.get("tokenize_by", "words")  # words, sentences, paragraphs
        
        tokens = text_processor.tokenize(text, tokenize_by)
        
        return {
            "original_text": text,
            "tokens": tokens,
            "token_count": len(tokens),
            "tokenize_by": tokenize_by
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text tokenization failed: {str(e)}")

# Sentiment Analysis Endpoints

@app.post("/sentiment/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """
    Analyze sentiment of text with civic discourse focus
    """
    try:
        import time
        start_time = time.time()
        
        result = sentiment_analyzer.analyze_sentiment(request.text)
        
        processing_time = time.time() - start_time
        
        return SentimentAnalysisResponse(
            text=request.text,
            sentiment_scores=result["sentiment_scores"],
            sentiment_classification=result["sentiment_classification"],
            emotional_indicators=result["emotional_indicators"] if request.include_emotions else [],
            civic_analysis=result["civic_analysis"] if request.include_civic_analysis else {
                "engagement_level": "none",
                "tone": "neutral", 
                "certainty_level": "uncertain"
            },
            confidence_score=result["confidence_score"],
            text_length=result["text_length"],
            word_count=result["word_count"],
            processing_time_seconds=round(processing_time, 4)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@app.post("/sentiment/analyze/batch", response_model=BatchSentimentResponse)
async def analyze_sentiment_batch(request: BatchSentimentRequest):
    """
    Batch analyze sentiment for multiple texts
    """
    try:
        import time
        start_time = time.time()
        
        results = []
        confidence_scores = []
        
        for text in request.texts:
            result = sentiment_analyzer.analyze_sentiment(text)
            confidence_scores.append(result["confidence_score"])
            
            results.append(SentimentAnalysisResponse(
                text=text,
                sentiment_scores=result["sentiment_scores"],
                sentiment_classification=result["sentiment_classification"],
                emotional_indicators=result["emotional_indicators"] if request.include_emotions else [],
                civic_analysis=result["civic_analysis"] if request.include_civic_analysis else {
                    "engagement_level": "none",
                    "tone": "neutral",
                    "certainty_level": "uncertain"
                },
                confidence_score=result["confidence_score"],
                text_length=result["text_length"],
                word_count=result["word_count"],
                processing_time_seconds=0.0  # Individual timing not tracked in batch
            ))
        
        processing_time = time.time() - start_time
        average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return BatchSentimentResponse(
            results=results,
            total_analyzed=len(results),
            average_confidence=round(average_confidence, 3),
            processing_time_seconds=round(processing_time, 4)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch sentiment analysis failed: {str(e)}")

@app.post("/sentiment/civic-engagement")
async def analyze_civic_engagement(request: dict):
    """
    Analyze civic engagement level in text
    """
    try:
        text = request.get("text", "")
        
        if not text:
            raise ValueError("Text is required")
        
        result = sentiment_analyzer.analyze_sentiment(text)
        
        return {
            "text": text,
            "civic_engagement_score": result["sentiment_scores"]["civic_engagement"],
            "engagement_level": result["civic_analysis"]["engagement_level"],
            "civic_terms_detected": [], # Could extract specific civic terms
            "constructiveness": result["sentiment_scores"]["constructiveness"],
            "tone": result["civic_analysis"]["tone"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Civic engagement analysis failed: {str(e)}")

@app.post("/text/analyze-complete")
async def complete_text_analysis(request: dict):
    """
    Complete text analysis combining preprocessing and sentiment analysis
    """
    try:
        text = request.get("text", "")
        options = request.get("options", {})
        
        if not text:
            raise ValueError("Text is required")
        
        # Text preprocessing
        preprocessing_result = text_processor.preprocess(text=text, options=options)
        
        # Sentiment analysis
        sentiment_result = sentiment_analyzer.analyze_sentiment(text)
        
        return {
            "original_text": text,
            "preprocessing": preprocessing_result,
            "sentiment_analysis": sentiment_result,
            "combined_insights": {
                "civic_engagement_level": sentiment_result["civic_analysis"]["engagement_level"],
                "overall_tone": sentiment_result["civic_analysis"]["tone"],
                "text_complexity": len(preprocessing_result["tokens"]),
                "civic_terms_count": len(preprocessing_result["metadata"]["civic_terms_found"]),
                "emotional_indicators": sentiment_result["emotional_indicators"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete text analysis failed: {str(e)}")

# Embeddings Endpoints

@app.post("/embeddings/generate", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate BERT embeddings for text
    """
    try:
        import time
        start_time = time.time()
        
        embedding = embeddings_generator.generate_embedding(request.text)
        model_info = embeddings_generator.get_embedding_info()
        
        processing_time = time.time() - start_time
        
        return EmbeddingResponse(
            text=request.text,
            embedding=embedding.tolist(),
            embedding_dimension=len(embedding),
            model_type=model_info["model_type"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@app.post("/embeddings/generate/batch", response_model=BatchEmbeddingResponse)
async def generate_embeddings_batch(request: BatchEmbeddingRequest):
    """
    Generate BERT embeddings for multiple texts
    """
    try:
        import time
        start_time = time.time()
        
        embeddings = embeddings_generator.generate_embeddings_batch(request.texts)
        model_info = embeddings_generator.get_embedding_info()
        
        results = []
        for text, embedding in zip(request.texts, embeddings):
            results.append(EmbeddingResponse(
                text=text,
                embedding=embedding.tolist(),
                embedding_dimension=len(embedding),
                model_type=model_info["model_type"]
            ))
        
        processing_time = time.time() - start_time
        
        return BatchEmbeddingResponse(
            results=results,
            total_processed=len(results),
            processing_time_seconds=round(processing_time, 4)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")

@app.post("/embeddings/similarity", response_model=SimilarityResponse)
async def compute_similarity(request: SimilarityRequest):
    """
    Compute cosine similarity between two texts
    """
    try:
        import time
        start_time = time.time()
        
        similarity = embeddings_generator.compute_similarity(request.text1, request.text2)
        
        processing_time = time.time() - start_time
        
        return SimilarityResponse(
            text1=request.text1,
            text2=request.text2,
            similarity_score=float(similarity),
            processing_time_seconds=round(processing_time, 4)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity computation failed: {str(e)}")

@app.post("/embeddings/search", response_model=SimilarTextSearchResponse)
async def search_similar_texts(request: SimilarTextSearchRequest):
    """
    Find texts most similar to a query
    """
    try:
        import time
        start_time = time.time()
        
        similar_texts = embeddings_generator.find_similar_texts(
            request.query_text,
            request.candidate_texts,
            request.top_k
        )
        
        results = []
        for text, score in similar_texts:
            results.append({
                "text": text,
                "similarity_score": float(score)
            })
        
        processing_time = time.time() - start_time
        
        return SimilarTextSearchResponse(
            query_text=request.query_text,
            results=results,
            total_candidates=len(request.candidate_texts),
            processing_time_seconds=round(processing_time, 4)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar text search failed: {str(e)}")

@app.get("/embeddings/info")
async def get_embeddings_info():
    """
    Get information about the current embeddings model
    """
    try:
        return embeddings_generator.get_embedding_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get embeddings info: {str(e)}")

# Clustering Endpoints

@app.post("/clustering/analyze", response_model=ClusteringResponse)
async def cluster_responses(request: ClusteringRequest):
    """
    Cluster responses using embeddings and identify consensus areas
    """
    try:
        import time
        start_time = time.time()
        
        # Generate embeddings for all responses
        embeddings = embeddings_generator.generate_embeddings_batch(request.responses)
        
        # Configure clustering engine
        config = ClusterConfig(
            algorithm=request.algorithm,
            n_clusters=request.n_clusters or 5,
            min_cluster_size=request.min_cluster_size
        )
        
        # Perform clustering
        clustering_engine.config = config
        result = clustering_engine.cluster_responses(request.responses, embeddings)
        
        processing_time = time.time() - start_time
        
        return ClusteringResponse(
            clusters=result["clusters"],
            statistics=result["statistics"],
            consensus_areas=result["consensus_areas"],
            total_responses=result["total_responses"],
            total_clusters=result["total_clusters"],
            algorithm_used=result["algorithm_used"],
            optimal_clusters=result["optimal_clusters"],
            processing_time_seconds=round(processing_time, 4)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")

@app.post("/clustering/complete-analysis")
async def complete_response_analysis(request: ClusteringRequest):
    """
    Complete analysis pipeline: preprocessing, sentiment, embeddings, and clustering
    """
    try:
        import time
        start_time = time.time()
        
        # Step 1: Text preprocessing
        preprocessing_results = []
        for text in request.responses:
            result = text_processor.preprocess(text=text)
            preprocessing_results.append(result)
        
        # Step 2: Sentiment analysis
        sentiment_results = []
        for text in request.responses:
            result = sentiment_analyzer.analyze_sentiment(text)
            sentiment_results.append(result)
        
        # Step 3: Generate embeddings
        embeddings = embeddings_generator.generate_embeddings_batch(request.responses)
        
        # Step 4: Clustering
        config = ClusterConfig(
            algorithm=request.algorithm,
            n_clusters=request.n_clusters or 5,
            min_cluster_size=request.min_cluster_size
        )
        clustering_engine.config = config
        clustering_result = clustering_engine.cluster_responses(request.responses, embeddings)
        
        processing_time = time.time() - start_time
        
        # Calculate overall insights
        overall_sentiment = {
            "average_polarity": np.mean([s["sentiment_scores"]["polarity"] for s in sentiment_results]),
            "average_civic_engagement": np.mean([s["sentiment_scores"]["civic_engagement"] for s in sentiment_results]),
            "average_constructiveness": np.mean([s["sentiment_scores"]["constructiveness"] for s in sentiment_results]),
            "dominant_tone": _get_dominant_tone(sentiment_results)
        }
        
        return {
            "preprocessing": preprocessing_results,
            "sentiment_analysis": sentiment_results,
            "embeddings": [emb.tolist() for emb in embeddings],
            "clustering": clustering_result,
            "overall_insights": overall_sentiment,
            "processing_time_seconds": round(processing_time, 4)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete analysis failed: {str(e)}")

@app.get("/clustering/info")
async def get_clustering_info():
    """
    Get information about the clustering configuration
    """
    try:
        return clustering_engine.get_clustering_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get clustering info: {str(e)}")

def _get_dominant_tone(sentiment_results: List[Dict]) -> str:
    """Helper method to determine dominant tone"""
    tones = [result["civic_analysis"]["tone"] for result in sentiment_results]
    tone_counts = {}
    for tone in tones:
        tone_counts[tone] = tone_counts.get(tone, 0) + 1
    
    return max(tone_counts.items(), key=lambda x: x[1])[0] if tone_counts else "neutral"

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    ) 