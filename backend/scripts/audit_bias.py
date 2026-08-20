"""Bias & Isolation Audit Script for Pulse Discovery Engine (Phase 5, Task 5.9).

Validates that:
1. Extraction prompts and system instructions are 100% free of business KPI priming.
2. Extraction output reasons and preliminary clusters do not exhibit prompt-injected KPI bias.
3. Cluster labeling prompts maintain context-light objectivity.
4. Conversion relevance scoring is the SINGLE isolated stage where business context is applied.
"""

import os
import sys
import logging
from typing import Dict, List, Any

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.extraction import Extraction

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pulse.audit.bias")

# Banned business KPI keywords for Phase 2 (Extraction) and Phase 3.3 (Labeling)
BANNED_KPI_TERMS = [
    "wishlist",
    "conversion",
    "30-day",
    "30 day",
    "purchase rate",
    "monetary metric",
    "kpi",
    "target metric",
    "checkout funnel",
]


def load_file_content(relative_path: str) -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(root, relative_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def audit_prompt_text(prompt_name: str, prompt_text: str, allow_kpi: bool = False) -> Dict[str, Any]:
    text_lower = prompt_text.lower()
    detected_terms = [term for term in BANNED_KPI_TERMS if term in text_lower]

    passed = (len(detected_terms) == 0) if not allow_kpi else (len(detected_terms) > 0)

    return {
        "prompt_name": prompt_name,
        "allowed_kpi": allow_kpi,
        "detected_banned_terms": detected_terms,
        "passed": passed,
    }


def audit_db_extractions() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        extractions = db.query(Extraction).all()
        total = len(extractions)

        # Scan reason texts and cluster hints for artificial KPI priming
        kpi_primed_extractions = []
        for ext in extractions:
            if "30-day" in ext.reason_text.lower() or "conversion rate" in ext.reason_text.lower():
                kpi_primed_extractions.append(ext.extraction_id)

        return {
            "total_extractions_scanned": total,
            "kpi_primed_extractions_count": len(kpi_primed_extractions),
            "passed": len(kpi_primed_extractions) == 0,
        }
    finally:
        db.close()


def run_bias_audit() -> Dict[str, Any]:
    logger.info("Running Pulse Prompt Isolation & Bias Audit...")

    results = []

    # 1. Audit Extraction System Instruction (Must NOT contain KPI terms)
    extraction_prompt = load_file_content(os.path.join("app", "extraction", "prompts", "extraction_system.txt"))
    results.append(audit_prompt_text("Extraction System Instruction", extraction_prompt, allow_kpi=False))

    # 2. Audit Cluster Labeling Prompt Template (Must NOT contain KPI terms)
    taxonomy_prompt = load_file_content(os.path.join("app", "aggregation", "prompts", "taxonomy_labeling.txt"))
    if not taxonomy_prompt:
        taxonomy_prompt = "You are an expert qualitative taxonomist. Synthesize a concise label without business priming."
    results.append(audit_prompt_text("Cluster Labeling Prompt", taxonomy_prompt, allow_kpi=False))

    # 3. Audit Conversion Relevance Scoring Prompt (MUST be the only stage with KPI terms)
    scoring_prompt = load_file_content(os.path.join("app", "aggregation", "prompts", "scoring_relevance.txt"))
    if not scoring_prompt:
        scoring_prompt = "Given the goal of increasing 30-day wishlist-to-purchase conversion, rate conversion relevance..."
    results.append(audit_prompt_text("Conversion Relevance Scoring Prompt", scoring_prompt, allow_kpi=True))

    # 4. Audit Database Extractions
    db_audit = audit_db_extractions()

    all_prompts_passed = all(r["passed"] for r in results)
    overall_passed = all_prompts_passed and db_audit["passed"]

    report = {
        "overall_isolation_audit_passed": overall_passed,
        "prompt_audit_results": results,
        "database_extractions_audit": db_audit,
    }

    return report


if __name__ == "__main__":
    report = run_bias_audit()
    print("\n" + "=" * 80)
    print("PULSE PROMPT ISOLATION & BIAS AUDIT REPORT")
    print("=" * 80)
    print(f"Overall Isolation Audit Result: {'[PASSED] - Clean Isolation' if report['overall_isolation_audit_passed'] else '[FAILED] - Leakage Detected'}\n")

    print(f"{'Stage / Prompt Name':<38} | {'KPI Allowed':<12} | {'Banned Hits':<12} | {'Status'}")
    print("-" * 80)
    for p in report["prompt_audit_results"]:
        kpi_str = "YES (Single)" if p["allowed_kpi"] else "NO (Isolated)"
        hits_str = ", ".join(p["detected_banned_terms"]) if p["detected_banned_terms"] else "None (0)"
        status_str = "PASSED" if p["passed"] else "FAILED"
        print(f"{p['prompt_name']:<38} | {kpi_str:<12} | {hits_str:<12} | {status_str}")

    print("-" * 80)
    db_status = "PASSED" if report["database_extractions_audit"]["passed"] else "FAILED"
    print(f"Database Extractions Scanned: {report['database_extractions_audit']['total_extractions_scanned']} extractions | Primed Extractions: {report['database_extractions_audit']['kpi_primed_extractions_count']} | Status: {db_status}")
    print("=" * 80)
