"""CLI script to run Layer 3 & Layer 4 Clustering, Taxonomy & Opportunity Scoring."""

import sys
import os
import argparse
import logging

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.aggregation.coordinator import aggregation_coordinator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pulse.run_aggregation")


def main():
    parser = argparse.ArgumentParser(description="Run Pulse Semantic Clustering & Opportunity Scoring Pipeline")
    parser.add_argument(
        "--target-k",
        type=int,
        default=None,
        help="Optional fixed number of clusters (default: auto-detected via silhouette score)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional pipeline run tracking UUID",
    )
    args = parser.parse_args()

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    logger.info("=" * 60)
    logger.info(" PULSE DISCOVERY ENGINE — PHASE 3 AGGREGATION & SCORING")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        results = aggregation_coordinator.run(
            db=db,
            run_id=args.run_id,
            target_k=args.target_k,
        )

        logger.info("\n" + "=" * 60)
        logger.info(" RANKED OPPORTUNITY AREAS")
        logger.info("=" * 60)
        
        top_opps = results.get("top_opportunities", [])
        if not top_opps:
            logger.info("No opportunity areas found or processed.")
        else:
            for opp in top_opps:
                logger.info(
                    f"#{opp['rank']} [{opp['composite_score']:.2f}] {opp['label']} "
                    f"(Freq: {opp['frequency_score']:.2f}, Tri: {opp['triangulation_score']:.2f}, "
                    f"Conv: {opp['conversion_relevance_score']:.2f}, Conf: {opp['confidence_level']})"
                )
        logger.info("=" * 60)
        logger.info(f"Total Clusters: {results.get('clusters_count', 0)} | Total Extractions: {results.get('extractions_count', 0)} | Duration: {results.get('duration_seconds', 0)}s")
        logger.info("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
