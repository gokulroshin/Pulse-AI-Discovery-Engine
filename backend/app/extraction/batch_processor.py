"""Batch extraction processor orchestrating LLM reason extraction, quote validation, and database persistence."""

import uuid
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.models.pipeline_run import PipelineRun
from app.ingestion.normalizer import normalizer
from app.extraction.gemini_client import GeminiExtractionClient, gemini_client
from app.extraction.schema import BatchExtractionResponse, ExtractionItem

logger = logging.getLogger("pulse.extraction.processor")


class ExtractionBatchProcessor:
    """Orchestrates end-to-end LLM reason extraction across raw documents."""

    def __init__(self, client: Optional[GeminiExtractionClient] = None, batch_size: int = 20):
        self.client = client or gemini_client
        self.batch_size = batch_size

    def get_unextracted_documents(
        self,
        db: Session,
        limit: Optional[int] = None,
        filter_platform: Optional[str] = None,
        filter_category: Optional[str] = None,
    ) -> List[RawDocument]:
        """Fetch raw documents that have not yet been extracted (resilient checkpointing)."""
        # Subquery for already extracted doc_ids
        extracted_subquery = db.query(Extraction.doc_id).distinct().subquery()

        query = db.query(RawDocument).filter(
            ~RawDocument.doc_id.in_(extracted_subquery.select())
        )

        if filter_platform:
            query = query.filter(RawDocument.source_platform == filter_platform)
        if filter_category:
            query = query.filter(RawDocument.inferred_category == filter_category)

        query = query.order_by(RawDocument.created_at.asc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def process_batch(
        self,
        batch_docs: List[RawDocument],
        extraction_run_id: str,
        db: Session,
        stats: Dict[str, Any],
    ) -> List[Extraction]:
        """Process a single chunk of documents through Gemini, validate quotes, and prepare ORM records."""
        doc_map = {doc.doc_id: doc for doc in batch_docs}
        prompt_docs = [{"doc_id": doc.doc_id, "content_text": doc.content_text} for doc in batch_docs]

        extraction_response = self.client.extract_batch(prompt_docs)
        if not extraction_response or not extraction_response.documents:
            stats["errors"].append(f"Failed extraction for batch of {len(batch_docs)} documents.")
            return []

        valid_extractions: List[Extraction] = []

        for doc_res in extraction_response.documents:
            source_doc = doc_map.get(doc_res.doc_id)
            if not source_doc:
                continue

            for item in doc_res.items:
                # 1. Verbatim Quote Validation Guardrail
                is_valid_quote = normalizer.verify_verbatim_quote(
                    item.verbatim_quote, source_doc.content_text
                )
                if not is_valid_quote:
                    stats["total_rejected_quotes"] += 1
                    logger.debug(
                        f"Rejected hallucinated quote for doc {source_doc.doc_id}: '{item.verbatim_quote}'"
                    )
                    continue

                # 2. Track Signal and Confidence stats
                sig_type = item.signal_type
                conf = item.confidence
                stats["by_signal_type"][sig_type] = stats["by_signal_type"].get(sig_type, 0) + 1
                stats["by_confidence"][conf] = stats["by_confidence"].get(conf, 0) + 1

                # 3. Create Extraction ORM model
                db_extraction = Extraction(
                    doc_id=source_doc.doc_id,
                    reason_text=item.reason_text.strip(),
                    verbatim_quote=item.verbatim_quote.strip(),
                    confidence=conf,
                    signal_type=sig_type,
                    extraction_run_id=extraction_run_id,
                )
                valid_extractions.append(db_extraction)

        if valid_extractions:
            db.bulk_save_objects(valid_extractions)
            db.commit()
            stats["total_extractions"] += len(valid_extractions)

        stats["total_documents_processed"] += len(batch_docs)
        return valid_extractions

    def run(
        self,
        limit: Optional[int] = None,
        batch_size: Optional[int] = None,
        filter_platform: Optional[str] = None,
        filter_category: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> PipelineRun:
        """Run complete extraction across unextracted documents in the corpus."""
        effective_batch_size = batch_size or self.batch_size
        owns_db_session = db is None
        session = db or SessionLocal()

        pipeline_run = PipelineRun(
            stage="extraction",
            status="running",
            config={
                "limit": limit,
                "batch_size": effective_batch_size,
                "filter_platform": filter_platform,
                "filter_category": filter_category,
                "model": self.client.model,
            },
            stats={
                "total_documents_processed": 0,
                "total_extractions": 0,
                "total_rejected_quotes": 0,
                "by_signal_type": {},
                "by_confidence": {},
                "errors": [],
            },
        )
        session.add(pipeline_run)
        session.commit()
        session.refresh(pipeline_run)

        try:
            unextracted_docs = self.get_unextracted_documents(
                db=session,
                limit=limit,
                filter_platform=filter_platform,
                filter_category=filter_category,
            )

            total_to_process = len(unextracted_docs)
            logger.info(
                f"Starting extraction run [{pipeline_run.run_id}]: {total_to_process} unextracted documents found."
            )

            stats = pipeline_run.stats

            # Chunk into batches
            for i in range(0, total_to_process, effective_batch_size):
                chunk = unextracted_docs[i : i + effective_batch_size]
                batch_num = (i // effective_batch_size) + 1
                logger.info(
                    f"Processing extraction batch {batch_num} ({len(chunk)} docs, {min(i + effective_batch_size, total_to_process)}/{total_to_process})..."
                )

                self.process_batch(
                    batch_docs=chunk,
                    extraction_run_id=pipeline_run.run_id,
                    db=session,
                    stats=stats,
                )

                # Checkpoint progress to pipeline_run
                pipeline_run.stats = dict(stats)
                session.commit()

            # Mark completed
            pipeline_run.status = "completed"
            pipeline_run.completed_at = datetime.now(timezone.utc)
            session.commit()
            logger.info(
                f"Extraction pipeline completed: {stats['total_extractions']} extractions saved from {stats['total_documents_processed']} documents ({stats['total_rejected_quotes']} hallucinated quotes rejected)."
            )

        except Exception as e:
            session.rollback()
            logger.error(f"Extraction pipeline failed: {e}", exc_info=True)
            pipeline_run.status = "failed"
            pipeline_run.completed_at = datetime.now(timezone.utc)
            if "stats" in locals():
                stats["errors"].append(str(e))
                pipeline_run.stats = dict(stats)
            session.commit()

        finally:
            if owns_db_session:
                session.close()

        return pipeline_run


# Global singleton instance
batch_processor = ExtractionBatchProcessor()
