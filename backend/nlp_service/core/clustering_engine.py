"""
Clustering Engine for Response Grouping
Groups similar responses using K-means and other clustering algorithms
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import json

@dataclass
class ClusterConfig:
    """Configuration for clustering algorithms"""
    algorithm: str = "kmeans"  # kmeans, dbscan, hierarchical
    n_clusters: int = 5  # For K-means
    min_cluster_size: int = 2  # Minimum responses per cluster
    eps: float = 0.3  # For DBSCAN
    random_state: int = 42
    max_iter: int = 300
    n_init: int = 10

@dataclass
class ClusterResult:
    """Result of clustering operation"""
    cluster_id: int
    centroid: List[float]
    responses: List[str]
    response_indices: List[int]
    size: int
    coherence_score: float
    representative_text: str

class ClusteringEngine:
    """
    Clustering engine for grouping similar responses
    """
    
    def __init__(self, config: Optional[ClusterConfig] = None):
        """Initialize clustering engine"""
        self.config = config or ClusterConfig()
        self.scaler = StandardScaler()
        self.pca = None
        self.model = None
        self.embeddings = None
        self.labels = None
        
    def cluster_responses(self, responses: List[str], embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """
        Cluster responses based on their embeddings
        
        Args:
            responses: List of response texts
            embeddings: List of embedding vectors
            
        Returns:
            Dictionary with clustering results
        """
        if len(responses) < 2:
            return self._empty_clustering_result(responses)
        
        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings)
        
        # Determine optimal number of clusters
        optimal_k = self._determine_optimal_clusters(embeddings_array, responses)
        
        # Perform clustering
        if self.config.algorithm == "kmeans":
            clusters = self._kmeans_clustering(embeddings_array, responses, optimal_k)
        elif self.config.algorithm == "dbscan":
            clusters = self._dbscan_clustering(embeddings_array, responses)
        else:
            clusters = self._kmeans_clustering(embeddings_array, responses, optimal_k)
        
        # Calculate cluster statistics
        cluster_stats = self._calculate_cluster_statistics(clusters, embeddings_array)
        
        # Find consensus areas
        consensus_areas = self._identify_consensus_areas(clusters, embeddings_array)
        
        return {
            "clusters": [cluster.__dict__ for cluster in clusters],
            "statistics": cluster_stats,
            "consensus_areas": consensus_areas,
            "total_responses": len(responses),
            "total_clusters": len(clusters),
            "algorithm_used": self.config.algorithm,
            "optimal_clusters": optimal_k
        }
    
    def _determine_optimal_clusters(self, embeddings: np.ndarray, responses: List[str]) -> int:
        """Determine optimal number of clusters using silhouette analysis"""
        if len(embeddings) < 4:
            return min(2, len(embeddings))
        
        max_k = min(10, len(embeddings) // 2)
        if max_k < 2:
            return 2
        
        best_score = -1
        optimal_k = 2
        
        for k in range(2, max_k + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=self.config.random_state, n_init=self.config.n_init)
                labels = kmeans.fit_predict(embeddings)
                
                if len(set(labels)) > 1:  # At least 2 clusters
                    score = silhouette_score(embeddings, labels)
                    if score > best_score:
                        best_score = score
                        optimal_k = k
            except Exception as e:
                logging.warning(f"Failed to evaluate k={k}: {e}")
                continue
        
        return optimal_k
    
    def _kmeans_clustering(self, embeddings: np.ndarray, responses: List[str], n_clusters: int) -> List[ClusterResult]:
        """Perform K-means clustering"""
        # Standardize embeddings
        embeddings_scaled = self.scaler.fit_transform(embeddings)
        
        # Apply PCA for dimensionality reduction if needed
        if embeddings_scaled.shape[1] > 50:
            self.pca = PCA(n_components=min(50, len(embeddings_scaled) - 1))
            embeddings_reduced = self.pca.fit_transform(embeddings_scaled)
        else:
            embeddings_reduced = embeddings_scaled
        
        # Perform K-means clustering
        self.model = KMeans(
            n_clusters=n_clusters,
            random_state=self.config.random_state,
            n_init=self.config.n_init,
            max_iter=self.config.max_iter
        )
        
        self.labels = self.model.fit_predict(embeddings_reduced)
        self.embeddings = embeddings_reduced
        
        # Group responses by cluster
        clusters = []
        for cluster_id in range(n_clusters):
            cluster_indices = np.where(self.labels == cluster_id)[0]
            
            if len(cluster_indices) < self.config.min_cluster_size:
                continue
            
            cluster_responses = [responses[i] for i in cluster_indices]
            cluster_embeddings = embeddings_reduced[cluster_indices]
            
            # Calculate centroid
            centroid = np.mean(cluster_embeddings, axis=0).tolist()
            
            # Calculate coherence score
            coherence = self._calculate_cluster_coherence(cluster_embeddings)
            
            # Find representative text
            representative = self._find_representative_text(cluster_responses, cluster_embeddings, centroid)
            
            clusters.append(ClusterResult(
                cluster_id=cluster_id,
                centroid=centroid,
                responses=cluster_responses,
                response_indices=cluster_indices.tolist(),
                size=len(cluster_responses),
                coherence_score=coherence,
                representative_text=representative
            ))
        
        return clusters
    
    def _dbscan_clustering(self, embeddings: np.ndarray, responses: List[str]) -> List[ClusterResult]:
        """Perform DBSCAN clustering"""
        # Standardize embeddings
        embeddings_scaled = self.scaler.fit_transform(embeddings)
        
        # Apply PCA for dimensionality reduction if needed
        if embeddings_scaled.shape[1] > 50:
            self.pca = PCA(n_components=min(50, len(embeddings_scaled) - 1))
            embeddings_reduced = self.pca.fit_transform(embeddings_scaled)
        else:
            embeddings_reduced = embeddings_scaled
        
        # Perform DBSCAN clustering
        self.model = DBSCAN(eps=self.config.eps, min_samples=self.config.min_cluster_size)
        self.labels = self.model.fit_predict(embeddings_reduced)
        self.embeddings = embeddings_reduced
        
        # Group responses by cluster
        clusters = []
        unique_labels = set(self.labels)
        
        for cluster_id in unique_labels:
            if cluster_id == -1:  # Noise points
                continue
                
            cluster_indices = np.where(self.labels == cluster_id)[0]
            
            if len(cluster_indices) < self.config.min_cluster_size:
                continue
            
            cluster_responses = [responses[i] for i in cluster_indices]
            cluster_embeddings = embeddings_reduced[cluster_indices]
            
            # Calculate centroid
            centroid = np.mean(cluster_embeddings, axis=0).tolist()
            
            # Calculate coherence score
            coherence = self._calculate_cluster_coherence(cluster_embeddings)
            
            # Find representative text
            representative = self._find_representative_text(cluster_responses, cluster_embeddings, centroid)
            
            clusters.append(ClusterResult(
                cluster_id=cluster_id,
                centroid=centroid,
                responses=cluster_responses,
                response_indices=cluster_indices.tolist(),
                size=len(cluster_responses),
                coherence_score=coherence,
                representative_text=representative
            ))
        
        return clusters
    
    def _calculate_cluster_coherence(self, cluster_embeddings: np.ndarray) -> float:
        """Calculate coherence score for a cluster"""
        if len(cluster_embeddings) < 2:
            return 1.0
        
        # Calculate average pairwise cosine similarity
        similarities = []
        for i in range(len(cluster_embeddings)):
            for j in range(i + 1, len(cluster_embeddings)):
                similarity = self._cosine_similarity(cluster_embeddings[i], cluster_embeddings[j])
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _find_representative_text(self, responses: List[str], embeddings: np.ndarray, centroid: List[float]) -> str:
        """Find the most representative text in a cluster"""
        if not responses:
            return ""
        
        if len(responses) == 1:
            return responses[0]
        
        # Find response closest to centroid
        centroid_array = np.array(centroid)
        distances = [np.linalg.norm(emb - centroid_array) for emb in embeddings]
        closest_idx = np.argmin(distances)
        
        return responses[closest_idx]
    
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
        return max(0.0, min(1.0, similarity))
    
    def _calculate_cluster_statistics(self, clusters: List[ClusterResult], embeddings: np.ndarray) -> Dict[str, Any]:
        """Calculate overall clustering statistics"""
        if not clusters:
            return {}
        
        cluster_sizes = [cluster.size for cluster in clusters]
        coherence_scores = [cluster.coherence_score for cluster in clusters]
        
        return {
            "total_clusters": len(clusters),
            "average_cluster_size": np.mean(cluster_sizes),
            "min_cluster_size": min(cluster_sizes),
            "max_cluster_size": max(cluster_sizes),
            "average_coherence": np.mean(coherence_scores),
            "min_coherence": min(coherence_scores),
            "max_coherence": max(coherence_scores),
            "cluster_size_distribution": {
                "small": len([s for s in cluster_sizes if s <= 3]),
                "medium": len([s for s in cluster_sizes if 3 < s <= 10]),
                "large": len([s for s in cluster_sizes if s > 10])
            }
        }
    
    def _identify_consensus_areas(self, clusters: List[ClusterResult], embeddings: np.ndarray) -> List[Dict[str, Any]]:
        """Identify areas of consensus across clusters"""
        consensus_areas = []
        
        # Find clusters with high coherence and reasonable size
        high_quality_clusters = [
            cluster for cluster in clusters 
            if cluster.coherence_score > 0.7 and cluster.size >= 3
        ]
        
        for cluster in high_quality_clusters:
            consensus_areas.append({
                "cluster_id": cluster.cluster_id,
                "representative_text": cluster.representative_text,
                "coherence_score": cluster.coherence_score,
                "size": cluster.size,
                "consensus_strength": cluster.coherence_score * np.log(cluster.size + 1)
            })
        
        # Sort by consensus strength
        consensus_areas.sort(key=lambda x: x["consensus_strength"], reverse=True)
        
        return consensus_areas
    
    def _empty_clustering_result(self, responses: List[str]) -> Dict[str, Any]:
        """Return empty clustering result for insufficient data"""
        return {
            "clusters": [],
            "statistics": {
                "total_clusters": 0,
                "average_cluster_size": 0,
                "min_cluster_size": 0,
                "max_cluster_size": 0,
                "average_coherence": 0.0,
                "min_coherence": 0.0,
                "max_coherence": 0.0,
                "cluster_size_distribution": {"small": 0, "medium": 0, "large": 0}
            },
            "consensus_areas": [],
            "total_responses": len(responses),
            "total_clusters": 0,
            "algorithm_used": self.config.algorithm,
            "optimal_clusters": 0
        }
    
    def get_clustering_info(self) -> Dict[str, Any]:
        """Get information about the clustering configuration"""
        return {
            "algorithm": self.config.algorithm,
            "n_clusters": self.config.n_clusters,
            "min_cluster_size": self.config.min_cluster_size,
            "eps": self.config.eps,
            "random_state": self.config.random_state,
            "max_iter": self.config.max_iter,
            "n_init": self.config.n_init
        } 