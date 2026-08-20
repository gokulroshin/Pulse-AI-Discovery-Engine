"""Layer 3 & Layer 4 Aggregation, Semantic Clustering & Opportunity Scoring Package."""

from app.aggregation.embeddings import embedding_generator, EmbeddingGenerator
from app.aggregation.clustering import hierarchical_clusterer, HierarchicalClusterer, ClusterResult
from app.aggregation.taxonomy import taxonomy_manager, TaxonomyManager
from app.aggregation.triangulation import triangulation_scorer, TriangulationScorer
from app.aggregation.segment_analyzer import segment_analyzer, SegmentAnalyzer
from app.aggregation.opportunity_scorer import opportunity_scorer, OpportunityScorer
from app.aggregation.coordinator import aggregation_coordinator, AggregationCoordinator

__all__ = [
    "embedding_generator",
    "EmbeddingGenerator",
    "hierarchical_clusterer",
    "HierarchicalClusterer",
    "ClusterResult",
    "taxonomy_manager",
    "TaxonomyManager",
    "triangulation_scorer",
    "TriangulationScorer",
    "segment_analyzer",
    "SegmentAnalyzer",
    "opportunity_scorer",
    "OpportunityScorer",
    "aggregation_coordinator",
    "AggregationCoordinator",
]
