"""
BERT Embeddings Generator for Semantic Text Analysis
Generates dense vector representations for text similarity and clustering
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Try to import transformers, fallback to sentence-transformers if available
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Fallback to basic word embeddings
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_length: int = 512
    batch_size: int = 32
    use_gpu: bool = False
    normalize_embeddings: bool = True
    pooling_strategy: str = "mean"  # mean, max, cls

class EmbeddingsGenerator:
    """
    Generates BERT embeddings for text semantic analysis
    Falls back to TF-IDF if BERT models unavailable
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embeddings generator"""
        self.config = config or EmbeddingConfig()
        self.model = None
        self.tokenizer = None
        self.embedding_dim = None
        self.model_type = None
        
        # Initialize the best available model
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the best available embedding model"""
        
        # Try Sentence Transformers first (easiest)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(self.config.model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                self.model_type = "sentence_transformers"
                logging.info(f"Initialized Sentence Transformers model: {self.config.model_name}")
                return
            except Exception as e:
                logging.warning(f"Failed to load Sentence Transformers: {e}")
        
        # Try direct Transformers library
        if TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
                self.model = AutoModel.from_pretrained('distilbert-base-uncased')
                self.embedding_dim = self.model.config.hidden_size
                self.model_type = "transformers"
                logging.info("Initialized DistilBERT model via Transformers")
                return
            except Exception as e:
                logging.warning(f"Failed to load Transformers model: {e}")
        
        # Fallback to TF-IDF
        self._initialize_tfidf_fallback()
        
    def _initialize_tfidf_fallback(self):
        """Initialize TF-IDF as fallback embedding method"""
        self.model = TfidfVectorizer(
            max_features=300,  # Reasonable embedding dimension
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        self.embedding_dim = 300
        self.model_type = "tfidf"
        self._tfidf_fitted = False
        logging.warning("Using TF-IDF fallback for embeddings (BERT not available)")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            NumPy array of embedding vector
        """
        if not text or not isinstance(text, str):
            return np.zeros(self.embedding_dim)
        
        if self.model_type == "sentence_transformers":
            return self._generate_sentence_transformer_embedding(text)
        elif self.model_type == "transformers":
            return self._generate_transformer_embedding(text)
        else:  # tfidf
            return self._generate_tfidf_embedding(text)
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        if self.model_type == "sentence_transformers":
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb for emb in embeddings]
        elif self.model_type == "transformers":
            return [self._generate_transformer_embedding(text) for text in texts]
        else:  # tfidf
            return self._generate_tfidf_batch(texts)
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        emb1 = self.generate_embedding(text1)
        emb2 = self.generate_embedding(text2)
        
        return self._cosine_similarity(emb1, emb2)
    
    def find_similar_texts(self, query_text: str, candidate_texts: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find most similar texts to a query
        
        Args:
            query_text: Text to find similarities for
            candidate_texts: List of candidate texts
            top_k: Number of top results to return
            
        Returns:
            List of (text, similarity_score) tuples
        """
        query_embedding = self.generate_embedding(query_text)
        similarities = []
        
        for text in candidate_texts:
            text_embedding = self.generate_embedding(text)
            similarity = self._cosine_similarity(query_embedding, text_embedding)
            similarities.append((text, similarity))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def _generate_sentence_transformer_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Sentence Transformers"""
        embedding = self.model.encode([text], convert_to_numpy=True)[0]
        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def _generate_transformer_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using raw Transformers"""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=self.config.max_length
        )
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Use mean pooling of last hidden states
        embeddings = outputs.last_hidden_state
        attention_mask = inputs['attention_mask']
        
        # Mean pooling
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
        sum_embeddings = torch.sum(embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        embedding = (sum_embeddings / sum_mask).squeeze().numpy()
        
        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)
            
        return embedding
    
    def _generate_tfidf_embedding(self, text: str) -> np.ndarray:
        """Generate TF-IDF embedding (fallback)"""
        if not self._tfidf_fitted:
            # Need to fit on some data first
            sample_texts = [text, "sample civic text", "democracy community participation"]
            self.model.fit(sample_texts)
            self._tfidf_fitted = True
        
        try:
            embedding = self.model.transform([text]).toarray()[0]
        except:
            # If transform fails, fit on current text
            self.model.fit([text])
            embedding = self.model.transform([text]).toarray()[0]
            self._tfidf_fitted = True
        
        if self.config.normalize_embeddings:
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
        
        return embedding
    
    def _generate_tfidf_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate TF-IDF embeddings for batch"""
        if not self._tfidf_fitted:
            self.model.fit(texts)
            self._tfidf_fitted = True
        
        try:
            embeddings = self.model.transform(texts).toarray()
        except:
            self.model.fit(texts)
            embeddings = self.model.transform(texts).toarray()
            self._tfidf_fitted = True
        
        result = []
        for embedding in embeddings:
            if self.config.normalize_embeddings:
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
            result.append(embedding)
        
        return result
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        if len(vec1) == 0 or len(vec2) == 0:
            return 0.0
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "model_type": self.model_type,
            "model_name": self.config.model_name if self.model_type != "tfidf" else "TF-IDF Fallback",
            "embedding_dimension": self.embedding_dim,
            "max_length": self.config.max_length,
            "normalization": self.config.normalize_embeddings,
            "available_libraries": {
                "transformers": TRANSFORMERS_AVAILABLE,
                "sentence_transformers": SENTENCE_TRANSFORMERS_AVAILABLE
            }
        }
    
    def save_model(self, path: str):
        """Save the current model state"""
        model_info = {
            "config": self.config,
            "model_type": self.model_type,
            "embedding_dim": self.embedding_dim
        }
        
        if self.model_type == "tfidf" and self._tfidf_fitted:
            model_info["tfidf_model"] = self.model
        
        with open(path, 'wb') as f:
            pickle.dump(model_info, f)
    
    def load_model(self, path: str):
        """Load a saved model state"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        
        with open(path, 'rb') as f:
            model_info = pickle.load(f)
        
        self.config = model_info["config"]
        self.model_type = model_info["model_type"]
        self.embedding_dim = model_info["embedding_dim"]
        
        if self.model_type == "tfidf" and "tfidf_model" in model_info:
            self.model = model_info["tfidf_model"]
            self._tfidf_fitted = True 