"""CLI runner script for LLM reason extraction pipeline across the raw documents corpus."""

import sys
import os
import argparse
import logging
from sqlalchemy import func

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.extraction.batch_processor import batch_processor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pulse.run_extraction")


def main():
    parser = argparse.ArgumentParser(description="Run Pulse LLM Reason Extraction Pipeline")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum documents to process (default: all unextracted documents)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Number of documents per Gemini API call (default: 25)",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default=None,
        help="Filter by specific platform (playstore, appstore, reddit, youtube, ecommerce)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter by category (ethnic_wear, western, footwear, accessories, general)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        total_docs = db.query(RawDocument).count()
        extracted_docs = db.query(func.count(func.distinct(Extraction.doc_id))).scalar() or 0
        total_extractions = db.query(Extraction).count()

        logger.info(f"Total documents in corpus: {total_docs}")
        logger.info(f"Already extracted documents: {extracted_docs} ({total_extractions} extractions)")
        logger.info(f"Pending extraction: {total_docs - extracted_docs}")

        logger.info(
            f"Starting LLM extraction run (limit={args.limit}, batch_size={args.batch_size}, platform={args.platform}, category={args.category})..."
        )

        run = batch_processor.run(
            limit=args.limit,
            batch_size=args.batch_size,
            filter_platform=args.platform,
            filter_category=args.category,
            db=db,
        )

        logger.info(f"Extraction Pipeline Run Finished with status: {run.status.upper()}")
        logger.info(f"Run Statistics: {run.stats}")

        # Final corpus state
        final_extracted = db.query(func.count(func.distinct(Extraction.doc_id))).scalar() or 0
        final_extractions = db.query(Extraction).count()
        logger.info(f"Updated total extractions in database: {final_extractions} across {final_extracted} documents.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
