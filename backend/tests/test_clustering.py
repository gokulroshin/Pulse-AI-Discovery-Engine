"""Unit and integration tests for Phase 3 semantic clustering and taxonomy creation."""

import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.models.taxonomy_node import TaxonomyNode
from app.aggregation.embeddings import EmbeddingGenerator
from app.aggregation.clustering import HierarchicalClusterer
from app.aggregation.taxonomy import TaxonomyManager


@pytest.fixture
def test_db():
    """In-memory SQLite test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_embedding_generator_tfidf_fallback():
    """Test that embedding generator produces normalized unit vectors and caches results."""
    generator = EmbeddingGenerator(api_key="")
    texts = [
        "Uncertain about garment fit based on contradictory reviews",
        "Fabric quality feels transparent and thin in person",
        "Size chart says medium but users recommend large",
        "Love the dress styling but not sure which occasion to wear it to",
    ]

    embeddings = generator.generate_embeddings(texts)
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == len(texts)
    assert embeddings.shape[1] > 0

    # Verify unit normalization
    norms = np.linalg.norm(embeddings, axis=1)
    for norm in norms:
        assert np.isclose(norm, 1.0, atol=1e-3)

    # Verify caching
    cached_embeddings = generator.generate_embeddings(texts)
    assert np.allclose(embeddings, cached_embeddings)


def test_hierarchical_clusterer():
    """Test clustering grouping and exemplar extraction."""
    generator = EmbeddingGenerator(api_key="")
    clusterer = HierarchicalClusterer(min_clusters=2, max_clusters=3)

    texts = [
        "Size chart says medium but runs small",
        "Confused whether to buy size M or L",
        "Garment fit is tight around shoulders",
        "Distrust paid reviews and want authentic try-on photos",
        "Review looks sponsored and fake, cannot trust star rating",
    ]
    records = [
        {"extraction_id": f"ext-{i}", "reason_text": text, "verbatim_quote": f"Quote {i}"}
        for i, text in enumerate(texts)
    ]

    embeddings = generator.generate_embeddings(texts)
    clusters = clusterer.cluster(embeddings, records, target_k=2)

    assert len(clusters) == 2
    total_assigned = sum(c.size for c in clusters)
    assert total_assigned == len(texts)

    for c in clusters:
        assert len(c.exemplar_reasons) > 0
        assert len(c.extraction_ids) == c.size
        assert c.centroid is not None


def test_taxonomy_manager_sync_to_db(test_db):
    """Test persisting taxonomy nodes and mapping extractions in database."""
    # Seed raw document and extractions
    doc = RawDocument(
        source_platform="playstore",
        content_text="Size is totally off, size chart misled me.",
        content_hash="test_hash_tax_1",
    )
    test_db.add(doc)
    test_db.flush()

    ext1 = Extraction(
        doc_id=doc.doc_id,
        reason_text="Size chart is misleading regarding true dimensions",
        verbatim_quote="size chart misled me",
        confidence="high",
        signal_type="uncertainty",
    )
    ext2 = Extraction(
        doc_id=doc.doc_id,
        reason_text="Garment fits smaller than expected standard sizes",
        verbatim_quote="Size is totally off",
        confidence="high",
        signal_type="friction",
    )
    test_db.add_all([ext1, ext2])
    test_db.commit()

    manager = TaxonomyManager()
    cluster_data = [
        {
            "label": "Fit & Sizing Confidence Gap",
            "description": "User uncertainty and frustration regarding size charts and garment fit consistency.",
            "representative_quotes": ["size chart misled me"],
            "extraction_ids": [ext1.extraction_id, ext2.extraction_id],
        }
    ]

    nodes = manager.sync_taxonomy_to_db(test_db, cluster_data)
    assert len(nodes) == 1
    node = nodes[0]
    assert node.label == "Fit & Sizing Confidence Gap"
    assert node.extraction_count == 2

    # Verify extractions foreign key linkage
    linked_exts = test_db.query(Extraction).filter_by(taxonomy_node_id=node.node_id).all()
    assert len(linked_exts) == 2
