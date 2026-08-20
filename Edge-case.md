# Edge Case Matrix & Corner Scenario Manual: "Intently"

**Comprehensive Resilience & Failure Mode Catalog | Myntra Growth Discovery Engine**  
*Version 1.0 — August 2026*

---

## 1. Executive Summary & Edge-Case Taxonomy

Intently operates on unstructured, noisy, multi-source public discourse across millions of words. High analytical fidelity requires explicit detection, isolation, and handling of failure modes across every pipeline layer:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EDGE-CASE TAXONOMY                                │
├──────────────────────────┬──────────────────────────┬───────────────────────┤
│ Layer 1: Ingestion       │ Layer 2: Extraction      │ Layer 3 & 4: Agg/Score│
│ • API Rate Limits / Bans │ • Context Bias Leakage   │ • Single-Platform Bias│
│ • Brand Name Collisions  │ • Hallucinated Quotes    │ • Price Contamination │
│ • Hinglish / Noise Text  │ • Multilingual Hinglish  │ • Sparse Segment Div/0│
│ • Cross-Platform Dups    │ • Checkpoint Failure     │ • Taxonomy Hierarchy  │
└──────────────────────────┴──────────────────────────┴───────────────────────┘
```

---

## 2. Layer 1: Data Ingestion & Scrapers (Edge Cases 1.1 – 1.10)

### 1.1 Brand Name Collision in Plain Text
* **Scenario:** Fashion brands like `ONLY`, `W`, `GAP`, `MANGO`, `BEING HUMAN`, or `NEXT` are common English words or individual letters.
* **Failure Mode:** A review saying *"I only wanted to check the size"* or *"The w in the name was missing"* incorrectly tags the document as Brand: `ONLY` or `W` (Tier: `mid`).
* **Mitigation:**
  - Case-sensitive matching on original raw text for short acronyms (`ONLY`, `GAP`).
  - Contextual phrase matching for single-letter/ambiguous brands (`"W for Woman"`, `"W kurti"`, `"brand ONLY"`, `"ONLY jeans"`).
  - Explicit negation of common grammatical patterns (`"only wanted"`, `"only if"`, `"only then"`).

### 1.2 UTF-8 Byte Order Mark (BOM) & Encoding Artifacts
* **Scenario:** CSV files exported from Windows Excel or legacy systems prepend `\ufeff` (UTF-8 BOM) or encode text in Windows-1252 / ISO-8859-1.
* **Failure Mode:** The first column header `content_text` is parsed as `\ufeffcontent_text`, causing key lookups to fail and records to be dropped.
* **Mitigation:**
  - In `ManualUploadHandler`, decode inputs using `utf-8-sig` (auto-strips BOM).
  - Case-insensitive, fuzzy column matching (`content_text`, `text`, `review`, `comment`, `body`).

### 1.3 Reddit Public Endpoint 403 / Cloudflare Rate Limiting
* **Scenario:** Reddit blocks unauthenticated requests to `.json` endpoints with HTTP `403 Blocked` or `429 Too Many Requests`.
* **Failure Mode:** Live Reddit ingestion halts completely.
* **Mitigation:**
  - Implement PRAW OAuth with app credentials (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`).
  - Custom compliant User-Agent headers (`IntentlyFashionDiscovery/1.0`).
  - Exponential backoff with jitter and fallback to curated domain datasets when unconfigured.

### 1.4 Apple App Store Multi-Page RSS Structure Changes
* **Scenario:** Apple's iTunes RSS endpoint returns XML/JSON with summary metadata in index 0, or returns a dictionary instead of an array when page count = 1.
* **Failure Mode:** `TypeError: string indices must be integers` or reviews parsing zero items.
* **Mitigation:**
  - Type-safe entry parsing: explicitly detect if `entry` is a `dict` or `list`.
  - Check for required sub-keys (`im:rating`, `title`, `content`) before extracting.
  - Safe integer coercion with fallback defaults.

### 1.5 Pure Emoji / Low-Information Submissions
* **Scenario:** Reviews containing only emojis (e.g. `😍😍😍`, `👍👍`), spam repetitions (`good good good`), or single words (`Nice`, `Super`).
* **Failure Mode:** Pollutes corpus with zero qualitative value, wasting LLM tokens in Phase 2.
* **Mitigation:**
  - `TextNormalizer` enforces minimum alphanumeric character count ($\ge 10$) and minimum character length ($\ge 15$).
  - Filters out documents where alphanumeric density is $< 30\%$ of total string length.

### 1.6 Hinglish Code-Mixed Text & Colloquial Slang
* **Scenario:** Indian shoppers frequently mix Hindi and English: *"Kurta bohot sundar hai but shoulder fitting tight nikli"*, *"Fitting ekdum bekar hai, return daal diya"*.
* **Failure Mode:** Language filters misidentify Hinglish as non-English and drop valid feedback.
* **Mitigation:**
  - Do NOT reject text based purely on strict English dictionary lookup.
  - Filter based on Latin script presence ($\ge 80\%$ ASCII/Latin characters).
  - Feed Hinglish directly to Gemini 2.5 Flash, which natively understands Hindi/Hinglish contextual idioms.

### 1.7 Cross-Category Overlap (Hybrid Garments)
* **Scenario:** Products combining multiple category keywords (e.g. *"denim kurti"*, *"sneaker boots"*, *"dress with jacket"*).
* **Failure Mode:** Incorrect or fluctuating category assignment.
* **Mitigation:**
  - Weighted keyword density scoring in `MetadataEnricher`.
  - Specific hybrid rules (e.g. *"denim kurti"* matches `ethnic_wear` over generic `western` due to garment silhouette).

### 1.8 Cross-Gender Ambiguity in Gifting & Mentions
* **Scenario:** Female reviewer buying for male partner (*"Bought this HRX shirt for my husband, sizing was tight"*) or unisex references (*"Loved the oversized men's blazer on myself"*).
* **Failure Mode:** False gender categorization.
* **Mitigation:**
  - Distinguish author pronouns from target recipient references using priority rules (recipient nouns like *"husband"*, *"boyfriend"*, *"brother"* assign target context to `men`).

### 1.9 Cross-Platform Duplicate Content & Bot Mirrors
* **Scenario:** Identical promotional posts or copy-pasted reviews syndicated across Reddit, Play Store, and forums.
* **Failure Mode:** Artificially inflates triangulation scores by counting identical text multiple times across sources.
* **Mitigation:**
  - Global SHA-256 content hash check across the entire `raw_documents` table on insert.
  - Case-insensitive, whitespace-collapsed canonical string hashing.

### 1.10 Extremely Long Reddit Threads & Review Dumps
* **Scenario:** Reddit megathreads or long review essays exceeding 10,000 characters.
* **Failure Mode:** Database bloat and LLM batch context exhaustion.
* **Mitigation:**
  - Safe truncation at 4,000 characters with ellipsis.
  - Sentence-boundary-aware clipping (splits on period/newline rather than cutting words mid-token).

---

## 3. Layer 2: LLM Reason Extraction Pipeline (Edge Cases 2.1 – 2.10)

### 2.1 Prompt Context Priming & Confirmation Bias Leakage
* **Scenario:** Extraction prompt mentions "wishlist", "conversion", "30-day target", or "purchase frictions".
* **Failure Mode:** LLM only extracts reasons related to wishlists and ignores unanticipated behavioral nuances (e.g. gifting hesitation, moodboard hoarding, post-order anxiety).
* **Mitigation (Strict Guardrail):**
  - Prompt contains **ZERO** business keywords.
  - Frame instructions strictly as open-ended qualitative research: *"Extract ALL discrete reasons, behaviors, frictions, uncertainties, motivations, and decision factors."*

### 2.2 Hallucinated Verbatim Quotes
* **Scenario:** LLM paraphrases the reason and fabricates or slightly alters the `verbatim_quote` (e.g. fixes typos in user text).
* **Failure Mode:** Breaks 100% evidence traceability back to source text.
* **Mitigation (Automated Post-Validation):**
  - Extraction validator programmatically verifies: `clean_quote in clean_source_text`.
  - If quote is not an exact substring, search for fuzzy match ($\ge 90\%$ token overlap); if invalid, reject extraction item.

### 2.3 Gemini API Rate Limiting (429 / 503 Overloaded)
* **Scenario:** High concurrency batches exceed Gemini RPM/TPM quota or hit transient Google infrastructure 503s.
* **Failure Mode:** Incomplete batch extraction and lost worker state.
* **Mitigation:**
  - Token bucket rate limiter configured at 80% of max API quota.
  - Exponential backoff with jitter: initial wait 2s, max 32s, 3 retry attempts.
  - Dead-letter queue for failed document batches.

### 2.4 Neutral or Non-Actionable Reviews ("Good Product")
* **Scenario:** Review states *"Nice dress, timely delivery, 5 stars"* with no friction or decision factors.
* **Failure Mode:** LLM attempts to invent friction or returns malformed schema.
* **Mitigation:**
  - Explicit prompt instruction: *"If no causal behavior, hesitation, friction, or decision factor is present, return an empty items list: `[]`."*
  - Schema allows `items: []`.

### 2.5 Document Batch Chunking Token Overflow
* **Scenario:** A batch of 20 unusually lengthy documents exceeds the token limit per call.
* **Failure Mode:** LLM response truncated mid-JSON, resulting in JSON parse failure.
* **Mitigation:**
  - Dynamic token-budgeted batch chunking: chunk by token count ($\le 4,000$ tokens/batch) rather than fixed document count.
  - Enforce `response_mime_type="application/json"` and strict Pydantic schema validation.

### 2.6 Checkpoint Recovery on Worker Crash
* **Scenario:** Worker server restarts when 2,400 out of 5,000 documents have been processed.
* **Failure Mode:** Rerunning extraction from scratch doubles API costs ($5–10) and creates duplicate extractions.
* **Mitigation:**
  - Idempotent query: `SELECT * FROM raw_documents WHERE doc_id NOT IN (SELECT DISTINCT doc_id FROM extractions)`.
  - Pipeline checkpoints saved every 100 documents to `pipeline_runs.stats`.

### 2.7 Conflicting Signals in a Single Document
* **Scenario:** User loves the design but hates the sizing (*"Design is gorgeous 10/10, but chest fits like an XS instead of M"*).
* **Failure Mode:** Extractor only captures positive motivation and misses the conversion blocker.
* **Mitigation:**
  - Prompt requires granular multi-item extraction: each document can produce multiple distinct items with different `signal_type` tags (`motivation` AND `friction`).

### 2.8 Vernacular & Hinglish Slang Translation
* **Scenario:** Review uses regional slang: *"Kapda ekdum raddi hai"* (Cloth is completely trash) or *"Dabba packing phata hua tha"*.
* **Failure Mode:** English-only reasoning models fail to parse sentiment correctly.
* **Mitigation:**
  - Leverage Gemini 2.5's native multilingual understanding to parse vernacular idioms into accurate English `reason_text` while preserving the exact Hinglish `verbatim_quote`.

### 2.9 Low-Confidence Extractions
* **Scenario:** Ambiguous text where the LLM guesses the user's intent with low certainty.
* **Failure Mode:** Garbage extractions skewing downstream clustering.
* **Mitigation:**
  - Schema enforces `confidence: "high" | "medium" | "low"`.
  - In Phase 3 clustering, `low` confidence items are downweighted ($0.3\times$) or excluded from core taxonomy formation.

### 2.10 PII (Personally Identifiable Information) in Extractions
* **Scenario:** User review contains phone numbers, order IDs, email addresses, or delivery addresses.
* **Failure Mode:** PII stored in downstream analytics tables and presented on frontend dashboard.
* **Mitigation:**
  - Pre-extraction regex sanitizer redacts phone numbers, email patterns, and 10-digit tracking numbers into `[REDACTED]`.

---

## 4. Layer 3: Thematic Clustering & Taxonomy (Edge Cases 3.1 – 3.8)

### 3.1 Megaclusters vs. Microclusters (Cluster Imbalance)
* **Scenario:** Sizing issues represent 45% of all extractions, forming a massive cluster of 4,000 items, while niche issues have 5 items.
* **Failure Mode:** Monolithic opportunity area that lacks actionable product specificity.
* **Mitigation:**
  - Two-tier hierarchical clustering: automatically split clusters with $> 500$ extractions into sub-nodes (e.g. `Fit & Sizing` $\rightarrow$ `Size Chart Discrepancy`, `Body Type Fit Mismatch`, `Between-Sizes Uncertainty`).

### 3.2 Semantic Drift in Embeddings
* **Scenario:** Extractions with similar words but opposite meanings (e.g. *"Loved the tight fit"* vs *"Hated the tight fit"*).
* **Failure Mode:** Clustered into the same opportunity area.
* **Mitigation:**
  - Cluster separately by `signal_type` (`friction` vs `motivation`) or include `signal_type` prefix in the embedding text string.

### 3.3 Isolated Noise Outliers
* **Scenario:** A 1-off complaint (*"App icon color looks bad on my phone"*).
* **Failure Mode:** Creates a singleton taxonomy node that clutters the PM dashboard.
* **Mitigation:**
  - Cluster pruning threshold: clusters with fewer than $N=5$ extractions are categorized into `Unclustered / Miscellaneous` and excluded from opportunity rankings.

### 3.4 Taxonomy Hierarchy Cycles
* **Scenario:** A parent node is set as child of its own descendant during PM manual editing.
* **Failure Mode:** Infinite loop during tree traversal queries.
* **Mitigation:**
  - Database check constraint and API validation preventing circular `parent_node_id` references.

### 3.5 Taxonomy Renaming & Historical Run Comparison
* **Scenario:** PM modifies cluster label from *"Size Gap"* to *"Fit & Body-Type Confidence Gap"*.
* **Failure Mode:** Historical scoring runs become disconnected or report inconsistent naming.
* **Mitigation:**
  - Stable immutable `node_id` (UUID).
  - Versioned scoring runs store snapshot of taxonomy labels at compute time.

### 3.6 Synonym Divergence
* **Scenario:** *"runs small"*, *"need to size up"*, *"tight on bust"*, *"chota size"* all mean the same friction.
* **Failure Mode:** Scattered into multiple separate nodes.
* **Mitigation:**
  - Agglomerative clustering with cosine distance threshold calibrated at 0.78 on sentence embeddings.

### 3.7 LLM Cluster Naming Hallucination
* **Scenario:** Gemini names a cluster with overly generic or business-biased labels (e.g. *"Myntra Conversion Opportunity #1"*).
* **Failure Mode:** Uninformative taxonomy labels.
* **Mitigation:**
  - Cluster naming prompt isolation: instructions restrict labels to descriptive qualitative summaries based strictly on top 5 exemplar quotes.

### 3.8 Merging Two Existing Nodes
* **Scenario:** PM merges *"Occasion Mismatch"* into *"Seasonality Shift"*.
* **Failure Mode:** Orphaned extractions and duplicate score records.
* **Mitigation:**
  - Atomic database transaction updating all `extractions.taxonomy_node_id` and archiving the merged node.

---

## 5. Layer 4: Business Quantification & Scoring (Edge Cases 4.1 – 4.9)

### 5.1 Single-Platform Complaint Spikes
* **Scenario:** Play Store receives 500 reviews complaining about a delivery partner delay after a holiday sale.
* **Failure Mode:** High frequency creates a false #1 rank for a non-wishlist problem.
* **Mitigation (Triangulation by Design):**
  - Composite formula multiplies by `Triangulation Score` ($\frac{\text{platforms confirmed}}{\text{total platforms}}$).
  - If an issue appears on only 1 platform, triangulation score is capped at $0.20$, suppressing single-source spikes.

### 5.2 Price Complaint Contamination (Discount Demands)
* **Scenario:** 30% of reviews demand *"Give 50% discount"* or *"Too expensive"*.
* **Failure Mode:** Crowds out non-monetary discovery levers (violates Myntra's core strategic constraint).
* **Mitigation:**
  - `Actionability Score` penalizes pure monetary/price complaints with a near-zero multiplier ($0.05$).
  - System isolates *perceived quality-to-price ratio* from *raw price complaints*.

### 5.3 Division by Zero on Sparse Sub-Segments
* **Scenario:** Calculating category conversion relevance for a segment with 0 documents (e.g. `accessories` in `non-metro`).
* **Failure Mode:** `ZeroDivisionError` crashing scoring batch.
* **Mitigation:**
  - Laplace smoothing / safe division wrapper: `(count + 1) / (total + categories_count)`.

### 5.4 Extreme Score Saturation (All Scores = 1.0 or 0.0)
* **Scenario:** Linear scaling compresses scores into identical numbers.
* **Failure Mode:** Ranking ties where top 5 opportunities all have score `0.85`.
* **Mitigation:**
  - Normalized percentile ranking and multi-factor tie-breaking using raw extraction counts.

### 5.5 Score Drift Between Corpus Updates
* **Scenario:** Ingesting 500 new documents changes rank ordering of existing opportunities unexpectedly.
* **Failure Mode:** PM loses trust in trend stability.
* **Mitigation:**
  - Score runs are strictly versioned (`scoring_run_id`).
  - Delta reporting showing $\pm \Delta$ rank movement relative to previous scoring run.

### 5.6 Skewed Platform Distribution in Corpus
* **Scenario:** Corpus has 3,000 Play Store reviews but only 50 YouTube comments.
* **Failure Mode:** Platform percentages dominate weighted frequency calculations.
* **Mitigation:**
  - Platform-normalized frequency: calculate within-platform prevalence first, then take the macro-average across platforms.

### 5.7 Conversion Relevance LLM Scoring Bias
* **Scenario:** LLM rates every opportunity as "highly relevant" ($0.95+$) to wishlist conversion.
* **Failure Mode:** Loses discrimination power between opportunities.
* **Mitigation:**
  - Pairwise comparative ranking prompt or calibrated 5-point Rubric with explicit anchors (1 = Pure post-purchase/delivery, 5 = Direct pre-purchase hesitation blocker).

### 5.8 High Engagement Score Outliers (Viral Posts)
* **Scenario:** A viral Reddit meme post gets 5,000 upvotes while normal reviews get 2 upvotes.
* **Failure Mode:** A single post distorts the opportunity score.
* **Mitigation:**
  - Logarithmic engagement scaling: $\text{score} = \log_{10}(1 + \text{upvotes})$.

### 5.9 Category-Specific Noise (Footwear Sizing vs Apparel Sizing)
* **Scenario:** Shoe size charts (UK/US/EU) mixed with Kurta chest sizes (38/40/42).
* **Failure Mode:** Generic "Sizing" recommendation that is not actionable for category PMs.
* **Mitigation:**
  - Category-segmented scores: compute separate composite score breakdowns for Ethnic Wear, Western, Footwear, and Accessories.

---

## 6. Layer 5: Frontend Dashboard & Visualization (Edge Cases 6.1 – 6.7)

### 6.1 Zero-State on Narrow Filter Combinations
* **Scenario:** PM filters for `Category: Footwear` + `Gender: Men` + `Brand Tier: Value` + `Platform: YouTube` and returns 0 evidence quotes.
* **Failure Mode:** Blank screen or broken chart rendering.
* **Mitigation:**
  - Dedicated rich `EmptyState` component displaying the active filter pills and a one-click *"Clear Filters"* button.

### 6.2 XSS Injection via User-Generated Discourse Text
* **Scenario:** Public review contains malicious script tags: `<script>alert('xss')</script>`.
* **Failure Mode:** Script execution in PM browser session when rendering quote explorer.
* **Mitigation:**
  - React automatic JSX escaping + backend sanitization via `TextNormalizer`.

### 6.3 Extremely Long Verbatim Quotes Breaking Card Grids
* **Scenario:** A user quote spans 2,500 characters of unbroken text.
* **Failure Mode:** Distorts dashboard layout and pushes adjacent cards out of viewport.
* **Mitigation:**
  - CSS line-clamping (`-webkit-line-clamp: 4`) with an expandable *"Show full quote"* modal.

### 6.4 Slow Network / Long Pipeline Execution Timeouts
* **Scenario:** Ingestion or scoring takes 45 seconds to process thousands of records.
* **Failure Mode:** Browser fetch timeout or unresponsive UI.
* **Mitigation:**
  - Asynchronous background task pattern: `POST /api/v1/pipeline/run` returns immediately with `run_id` (`202 Accepted`).
  - Frontend polls `GET /api/v1/pipeline/status/{run_id}` with animated progress bar and auto-refresh on completion.

### 6.5 Mobile & Tablet Responsive Matrix Layouts
* **Scenario:** PM opens Triangulation Heatmap ($10 \times 6$ grid) on mobile screen.
* **Failure Mode:** Columns collapse into illegible slivers.
* **Mitigation:**
  - Responsive horizontal scroll container with fixed row headers and touch tooltips.

### 6.6 Stale Backend Cache After Manual Upload
* **Scenario:** PM uploads new CSV, but dashboard continues displaying old corpus stats.
* **Failure Mode:** Confusion over whether upload succeeded.
* **Mitigation:**
  - TanStack Query cache invalidation triggers on mutation completion for `['corpus-stats', 'opportunities']`.

### 6.7 Missing Favicons / Fonts on Offline or Air-Gapped Networks
* **Scenario:** Google Fonts CDN fails to load.
* **Failure Mode:** Invisible text or layout flash (FOIT).
* **Mitigation:**
  - System font stack fallback (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`) defined in CSS tokens.

---

## 7. Infrastructure, Database & Concurrency (Edge Cases 7.1 – 7.6)

### 7.1 SQLite vs. PostgreSQL JSON/JSONB Dialect Discrepancies
* **Scenario:** Local development uses SQLite (which stores JSON as text), while production on Railway uses PostgreSQL `JSONB`.
* **Failure Mode:** Queries using PostgreSQL-specific operators (`->`, `@>`) crash during local testing.
* **Mitigation:**
  - Use SQLAlchemy standard cross-dialect `JSON` type and ORM abstraction layer.
  - Test suites validate queries across both SQLite in-memory and PostgreSQL.

### 7.2 Database Connection Pool Exhaustion Under Concurrent Worker Load
* **Scenario:** 10 Celery workers execute batch extractions simultaneously, opening 50 connections.
* **Failure Mode:** PostgreSQL `too many clients already` error.
* **Mitigation:**
  - Connection pool configuration: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, with context-managed sessions (`SessionLocal`).

### 7.3 Deadlocks on Concurrent Pipeline Runs
* **Scenario:** Ingestion run and scoring run update `raw_documents` and `pipeline_runs` simultaneously.
* **Failure Mode:** Transaction rollback and failed pipeline status.
* **Mitigation:**
  - Pipeline state machine enforces sequential stage execution per run ID.
  - Row-level locking and idempotent upsert queries.

### 7.4 Redis Memory Spikes During Large Batch Extraction
* **Scenario:** 20,000 extraction task payloads queued in Redis.
* **Failure Mode:** Redis OOM eviction and dropped task messages.
* **Mitigation:**
  - Pass document IDs / chunk references in Celery task parameters rather than entire raw document text payloads.

### 7.5 Database Migrations on Live Data Tables
* **Scenario:** Applying Alembic migrations with `NOT NULL` columns to existing tables with 50,000 rows.
* **Failure Mode:** Migration fails on existing NULL values.
* **Mitigation:**
  - Alembic migrations provide server defaults for all new non-nullable columns (`server_default='...'`).

### 7.6 Graceful Handling of Unhandled Exceptions in Fast-API Lifespan
* **Scenario:** Database connection is temporarily unreachable during application startup.
* **Failure Mode:** FastAPI app crashes in boot loop on Railway/Docker.
* **Mitigation:**
  - Lifespan context manager catches database initialization errors, logs warning, and keeps HTTP server live to report degraded status on `/health`.

---

## 8. Summary Edge-Case Action Matrix

| Component | Primary Edge Case | Implemented Defensive Code | Test Coverage |
| :--- | :--- | :--- | :--- |
| **Normalizer** | Pure emojis / noise / length overflows | `normalizer.py`: Length checks, alphanumeric threshold, truncation | `test_ingestion.py::test_normalizer_*` |
| **Enricher** | Brand name collisions (`ONLY`, `W`, `GAP`) | `metadata_enricher.py`: Context-aware regex & casing | `test_ingestion.py::test_enricher_*` |
| **Deduplicator** | Multi-source duplicate submissions | `pipeline.py`: SHA-256 hash unique constraint | `test_ingestion.py::test_pipeline_deduplication` |
| **App Store Scraper** | iTunes RSS pagination format shifts | `appstore.py`: Safe dictionary extraction & type-guards | `test_ingestion.py::test_appstore` |
| **Reddit Scraper** | Public 403 blocks / Rate limits | `reddit.py`: PRAW OAuth integration + graceful fallback | `test_ingestion.py::test_reddit` |
| **API Layer** | Missing DB / Network drops | `health.py` & `dependencies.py`: Database check & try/catch | `test_health.py::test_health_check` |
| **ORM Models** | Self-referencing tree cycles & FK cascades | `taxonomy_node.py` & `document.py`: Cascade rules | `test_models.py::test_models` |
