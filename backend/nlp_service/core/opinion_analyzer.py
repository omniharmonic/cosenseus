import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from typing import List, Dict, Any

class OpinionAnalyzer:
    """
    Performs dimensionality reduction and clustering on a user-statement matrix.
    """
    def __init__(self, n_clusters: int = 3, n_components: int = 2):
        self.n_clusters = n_clusters
        self.n_components = n_components
        self.pca = PCA(n_components=self.n_components)
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)

    def _convert_to_numerical_matrix(self, user_statement_matrix: List[Dict[str, Any]], statements: List[str]) -> np.ndarray:
        """
        Converts the list of user mappings into a NumPy matrix.
        'agree' -> 1, 'disagree' -> -1, 'pass'/'neutral' -> 0.
        """
        statement_map = {statement: i for i, statement in enumerate(statements)}
        num_users = len(user_statement_matrix)
        num_statements = len(statements)
        
        matrix = np.zeros((num_users, num_statements))

        for user_index, user_data in enumerate(user_statement_matrix):
            for mapping in user_data.get('mapping', []):
                statement_text = mapping.get('statement')
                position = mapping.get('position', 'pass').lower()
                
                if statement_text in statement_map:
                    statement_index = statement_map[statement_text]
                    if position == 'agree':
                        matrix[user_index, statement_index] = 1
                    elif position == 'disagree':
                        matrix[user_index, statement_index] = -1
        
        return matrix

    def analyze(self, user_statement_matrix: List[Dict[str, Any]], statements: List[str]) -> Dict[str, Any]:
        """
        Analyzes the user-statement matrix to find opinion clusters.
        
        The process is as follows:
        1. Convert the input data into a numerical matrix.
        2. Apply PCA to reduce the dimensionality of the data to 2D for visualization.
        3. Apply K-Means clustering to the reduced data to group users by opinion.
        4. Combine the original user data with their new 2D coordinates and cluster ID.
        """
        if not user_statement_matrix:
            return {"users": []}

        numerical_matrix = self._convert_to_numerical_matrix(user_statement_matrix, statements)
        
        # If we don't have enough data to perform PCA, return a simplified result
        if self.n_components >= min(numerical_matrix.shape):
            clusters = np.zeros(numerical_matrix.shape[0], dtype=int)
            reduced_matrix = np.zeros((numerical_matrix.shape[0], self.n_components))
        else:
            # Reduce dimensionality using PCA
            reduced_matrix = self.pca.fit_transform(numerical_matrix)
            # Perform K-Means clustering
            clusters = self.kmeans.fit_predict(reduced_matrix)

        # Combine results with original user data
        results = []
        for i, user_data in enumerate(user_statement_matrix):
            results.append({
                "user_id": user_data['user_id'],
                "response": user_data['response'],
                "x": float(reduced_matrix[i, 0]),
                "y": float(reduced_matrix[i, 1]),
                "cluster": int(clusters[i])
            })
            
        return {"users": results} 