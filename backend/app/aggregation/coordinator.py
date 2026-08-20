"""Aggregation coordinator orchestrating embedding, clustering, taxonomy creation, and opportunity scoring."""

import time
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.extraction import Extraction
from app.models.taxonomy_node import TaxonomyNode
from app.models.opportunity_score import OpportunityScore
from app.models.pipeline_run import PipelineRun
from app.aggregation.embeddings import embedding_generator
from app.aggregation.clustering import hierarchical_clusterer
from app.aggregation.taxonomy import taxonomy_manager
from app.aggregation.opportunity_scorer import opportunity_scorer

logger = logging.getLogger("pulse.aggregation.coordinator")


class AggregationCoordinator:
    """End-to-end execution coordinator for Layer 3 & Layer 4 batch analytics."""

    def run(
        self,
        db: Optional[Session] = None,
        run_id: Optional[str] = None,
        target_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute full aggregation pipeline: embed -> cluster -> label taxonomy -> score opportunities."""
        start_time = time.time()
        close_db_at_end = False

        if db is None:
            db = SessionLocal()
            close_db_at_end = True

        try:
            logger.info("Starting Phase 3 Aggregation & Scoring Pipeline...")

            # 1. Update pipeline run status if provided
            pipeline_run = None
            if run_id:
                pipeline_run = db.query(PipelineRun).filter_by(run_id=run_id).first()
                if pipeline_run:
                    pipeline_run.status = "running"
                    pipeline_run.stage = "clustering"
                    db.commit()

            # 2. Fetch extractions from DB
            extractions = db.query(Extraction).all()
            total_extractions = len(extractions)

            if total_extractions == 0:
                msg = "No extraction records found in database to cluster."
                logger.warning(msg)
                if pipeline_run:
                    pipeline_run.status = "completed"
                    pipeline_run.stats = {"message": msg, "nodes_created": 0}
                    pipeline_run.completed_at = datetime.now(timezone.utc)
                    db.commit()
                return {"status": "empty", "message": msg, "nodes": 0}

            logger.info(f"Loaded {total_extractions} extractions for clustering.")

            # Prepare records
            records = [
                {
                    "extraction_id": e.extraction_id,
                    "reason_text": e.reason_text,
                    "verbatim_quote": e.verbatim_quote or "",
                }
                for e in extractions
            ]
            texts = [r["reason_text"] for r in records]

            # 3. Generate embeddings
            logger.info("Step 1/4: Generating vector embeddings...")
            embeddings = embedding_generator.generate_embeddings(texts)

            # 4. Run semantic clustering
            logger.info("Step 2/4: Performing agglomerative clustering...")
            cluster_results = hierarchical_clusterer.cluster(
                embeddings=embeddings,
                extraction_records=records,
                target_k=target_k,
            )
            logger.info(f"Generated {len(cluster_results)} semantic clusters.")

            # 5. Generate taxonomy labels & descriptions (context-light)
            logger.info("Step 3/4: Synthesizing taxonomy labels & descriptions via LLM...")
            cluster_data_list = []
            for idx, c in enumerate(cluster_results, start=1):
                label_info = taxonomy_manager.label_cluster(
                    exemplar_reasons=c.exemplar_reasons,
                    exemplar_quotes=c.exemplar_quotes,
                    cluster_index=idx,
                )
                cluster_data_list.append({
                    "label": label_info["label"],
                    "description": label_info["description"],
                    "representative_quotes": label_info.get("representative_quotes", []),
                    "extraction_ids": c.extraction_ids,
                })

            # Save taxonomy nodes to DB
            created_nodes = taxonomy_manager.sync_taxonomy_to_db(db, cluster_data_list)

            # 6. Score opportunities (with business context)
            logger.info("Step 4/4: Evaluating conversion relevance & computing composite scores...")
            if pipeline_run:
                pipeline_run.stage = "scoring"
                db.commit()

            created_scores = opportunity_scorer.score_all_nodes(
                db=db,
                nodes=created_nodes,
                scoring_run_id=run_id,
            )

            elapsed_seconds = round(time.time() - start_time, 2)
            logger.info(f"Phase 3 Pipeline Complete! Processed {total_extractions} extractions into {len(created_nodes)} ranked opportunity nodes in {elapsed_seconds}s.")

            # Update pipeline run record
            if pipeline_run:
                pipeline_run.status = "completed"
                pipeline_run.stage = "scoring"
                pipeline_run.completed_at = datetime.now(timezone.utc)
                pipeline_run.stats = {
                    "extractions_processed": total_extractions,
                    "taxonomy_nodes_created": len(created_nodes),
                    "opportunity_scores_computed": len(created_scores),
                    "duration_seconds": elapsed_seconds,
                    "top_opportunity": created_nodes[0].label if created_nodes else None,
                }
                db.commit()

            return {
                "status": "success",
                "extractions_count": total_extractions,
                "clusters_count": len(created_nodes),
                "duration_seconds": elapsed_seconds,
                "top_opportunities": [
                    {
                        "rank": s.rank,
                        "label": s.taxonomy_node.label,
                        "composite_score": s.composite_score,
                        "frequency_score": s.frequency_score,
                        "triangulation_score": s.triangulation_score,
                        "conversion_relevance_score": s.conversion_relevance_score,
                        "confidence_level": s.confidence_level,
                    }
                    for s in created_scores[:5]
                ],
            }

        except Exception as e:
            logger.error(f"Aggregation pipeline failed: {e}", exc_info=True)
            if pipeline_run:
                pipeline_run.status = "failed"
                pipeline_run.completed_at = datetime.now(timezone.utc)
                pipeline_run.stats = {"error": str(e)}
                db.commit()
            raise e
        finally:
            if close_db_at_end:
                db.close()


# Global singleton
aggregation_coordinator = AggregationCoordinator()
