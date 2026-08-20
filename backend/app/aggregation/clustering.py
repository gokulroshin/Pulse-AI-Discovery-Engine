"""Hierarchical Agglomerative Semantic Clustering for qualitative extractions."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("pulse.aggregation.clustering")


@dataclass
class ClusterResult:
    cluster_index: int
    extraction_indices: List[int]
    extraction_ids: List[str]
    exemplar_reasons: List[str]
    exemplar_quotes: List[str]
    size: int
    centroid: np.ndarray


class HierarchicalClusterer:
    """Agglomerative semantic clustering with automatic cluster count selection and medoid extraction."""

    def __init__(
        self,
        min_clusters: int = 8,
        max_clusters: int = 15,
        linkage: str = "average",
    ):
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters
        self.linkage = linkage

    def find_optimal_clusters(
        self,
        embeddings: np.ndarray,
        min_k: Optional[int] = None,
        max_k: Optional[int] = None,
    ) -> int:
        """Find optimal k using silhouette score over cosine distance."""
        n_samples = len(embeddings)
        if n_samples <= 3:
            return max(1, n_samples)

        low = min_k or self.min_clusters
        high = max_k or self.max_clusters

        low = max(2, min(low, n_samples - 1))
        high = max(low, min(high, n_samples - 1))

        if low == high:
            return low

        best_k = low
        best_score = -1.0

        for k in range(low, high + 1):
            try:
                clusterer = AgglomerativeClustering(
                    n_clusters=k,
                    metric="cosine",
                    linkage=self.linkage,
                )
                labels = clusterer.fit_predict(embeddings)
                
                # Check that we have at least 2 distinct clusters
                if len(set(labels)) > 1:
                    score = silhouette_score(embeddings, labels, metric="cosine")
                    if score > best_score:
                        best_score = score
                        best_k = k
            except Exception as e:
                logger.debug(f"Silhouette test failed for k={k}: {e}")
                continue

        logger.info(f"Optimal cluster count determined: k={best_k} (silhouette={best_score:.3f})")
        return best_k

    def cluster(
        self,
        embeddings: np.ndarray,
        extraction_records: List[Dict[str, Any]],
        target_k: Optional[int] = None,
    ) -> List[ClusterResult]:
        """Group extractions into semantic clusters and identify exemplars.
        
        Args:
            embeddings: (N, D) normalized embedding array.
            extraction_records: List of dicts with 'extraction_id', 'reason_text', 'verbatim_quote'.
            target_k: Optional explicit cluster count.
            
        Returns:
            List of ClusterResult dataclasses.
        """
        n_samples = len(embeddings)
        if n_samples == 0:
            return []

        if n_samples == 1:
            record = extraction_records[0]
            return [
                ClusterResult(
                    cluster_index=0,
                    extraction_indices=[0],
                    extraction_ids=[record["extraction_id"]],
                    exemplar_reasons=[record["reason_text"]],
                    exemplar_quotes=[record.get("verbatim_quote", "")],
                    size=1,
                    centroid=embeddings[0],
                )
            ]

        # Determine number of clusters
        k = target_k or self.find_optimal_clusters(embeddings)
        k = min(k, n_samples)

        clusterer = AgglomerativeClustering(
            n_clusters=k,
            metric="cosine",
            linkage=self.linkage,
        )
        labels = clusterer.fit_predict(embeddings)

        clusters: List[ClusterResult] = []

        for c_idx in range(k):
            indices = np.where(labels == c_idx)[0].tolist()
            if not indices:
                continue

            cluster_embeddings = embeddings[indices]
            # Compute centroid
            centroid = np.mean(cluster_embeddings, axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm

            # Compute similarity of each member to centroid to find medoids/exemplars
            sims = cosine_similarity(cluster_embeddings, centroid.reshape(1, -1)).flatten()
            sorted_local_indices = np.argsort(-sims)  # Highest similarity first

            # Pick top 5 exemplars
            top_exemplar_indices = [indices[i] for i in sorted_local_indices[:5]]
            exemplar_reasons = [extraction_records[i]["reason_text"] for i in top_exemplar_indices]
            exemplar_quotes = [extraction_records[i].get("verbatim_quote", "") for i in top_exemplar_indices if extraction_records[i].get("verbatim_quote")]

            extraction_ids = [extraction_records[i]["extraction_id"] for i in indices]

            clusters.append(
                ClusterResult(
                    cluster_index=c_idx,
                    extraction_indices=indices,
                    extraction_ids=extraction_ids,
                    exemplar_reasons=exemplar_reasons,
                    exemplar_quotes=exemplar_quotes,
                    size=len(indices),
                    centroid=centroid,
                )
            )

        # Sort clusters by size descending
        clusters.sort(key=lambda c: c.size, reverse=True)
        return clusters


# Global singleton
hierarchical_clusterer = HierarchicalClusterer()
