# Implementation Plan: "Pulse" — Wishlist-to-Purchase Discovery Engine
**Phase-Wise Build Plan | Myntra Growth Team**  
*August 2026*

---

## Plan Overview

This document breaks the Pulse Discovery Engine build into **6 sequential phases**, each producing a working, testable increment. Phases are ordered by dependency — each phase builds on the artifacts of the previous one. The total estimated timeline is **4–5 weeks** for a solo developer working full-time.

```
Phase 0          Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
Scaffold &  ──►  Data         ──►  LLM          ──►  Clustering   ──►  Frontend     ──►  Deploy &
Foundation       Ingestion        Extraction        & Scoring        Dashboard        Polish
(3 days)         (5 days)         (5 days)          (4 days)         (6 days)         (3 days)
```

### Phase Dependency Chain

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Phase 0    │────▶│   Phase 1    │────▶│   Phase 2    │
│  Foundation  │     │  Ingestion   │     │  Extraction  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Phase 5    │◀────│   Phase 4    │◀────│   Phase 3    │
│  Deploy &    │     │  Frontend    │     │  Clustering  │
│  Polish      │     │  Dashboard   │     │  & Scoring   │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Phase 0: Project Scaffold & Foundation
**Duration:** 3 days  
**Goal:** Establish the monorepo structure, development environment, database schema, and CI pipeline so all subsequent phases build on stable ground.

### 0.1 Tasks

| # | Task | Files / Artifacts | Done Criteria |
|---|------|-------------------|---------------|
| 0.1 | Initialize monorepo with `backend/` and `frontend/` directories | Root `README.md`, `.gitignore` | Clean repo structure |
| 0.2 | **Backend scaffold:** Initialize Python project with FastAPI, create virtualenv, install core dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `celery`, `redis`, `google-genai`, `pydantic`) | `backend/requirements.txt`, `backend/app/main.py`, `backend/app/config.py` | `uvicorn` starts, `/health` returns `200 OK` |
| 0.3 | **Database setup:** Define all SQLAlchemy ORM models per Architecture §4 | `backend/app/models/document.py`, `extraction.py`, `taxonomy_node.py`, `opportunity_score.py`, `pipeline_run.py` | Models importable, no circular deps |
| 0.4 | **Alembic migrations:** Generate initial migration from ORM models, apply to local PostgreSQL | `backend/alembic/`, `backend/alembic.ini` | `alembic upgrade head` succeeds, all tables exist |
| 0.5 | **Database indexes:** Add performance indexes per Architecture §4.2 | Migration file | Indexes created, verified via `\di` |
| 0.6 | **Frontend scaffold:** Initialize Next.js project with TypeScript, CSS Modules | `frontend/` directory, `package.json`, `tsconfig.json` | `npm run dev` starts, default page loads |
| 0.7 | **Shared types:** Define TypeScript interfaces mirroring backend API schemas | `frontend/lib/types.ts` | Types compile cleanly |
| 0.8 | **Environment configuration:** Create `.env.example` files for both backend and frontend with all required variables (per Architecture §8.3) | `backend/.env.example`, `frontend/.env.local.example` | All env vars documented |
| 0.9 | **API client stub:** Create frontend API client wrapper with base URL config and auth header | `frontend/lib/api.ts` | Client instantiable, types aligned |

### 0.2 Deliverables
- [x] Monorepo with backend (FastAPI) and frontend (Next.js) scaffolds
- [x] PostgreSQL schema fully migrated with all 5 tables and indexes
- [x] `/health` endpoint live on backend
- [x] Frontend dev server running with empty shell

### 0.3 Dependencies
- Local PostgreSQL instance (or Railway dev DB)
- Local Redis instance (or Railway dev Redis)
- Google AI Studio API key for Gemini
- Node.js 20+ and Python 3.12+

---

## Phase 1: Data Ingestion Pipeline (Layer 1)
**Duration:** 5 days  
**Goal:** Build the complete ingestion layer — scrapers, normalizer, de-duplicator, metadata enricher — and populate the `raw_documents` table with a representative multi-source corpus.

### 1.1 Tasks

| # | Task | Files / Artifacts | Done Criteria |
|---|------|-------------------|---------------|
| 1.1 | **Base scraper interface:** Define abstract base class for all source adapters with common methods (`fetch`, `normalize`, `store`) | `backend/app/ingestion/base_scraper.py` | Interface defined, documented |
| 1.2 | **Play Store scraper:** Implement Google Play Store review fetcher for Myntra, AJIO, Amazon Fashion, Nykaa Fashion, Tata CLiQ using `google-play-scraper` | `backend/app/ingestion/scrapers/playstore.py` | Reviews fetched and printed for Myntra app |
| 1.3 | **App Store scraper:** Implement Apple App Store review fetcher using `app-store-scraper` | `backend/app/ingestion/scrapers/appstore.py` | Reviews fetched for target apps |
| 1.4 | **Reddit scraper:** Implement Reddit API client using PRAW for target subreddits (`r/IndianFashionAddicts`, `r/india`, `r/TwoXIndia`, fashion-related subs) — fetch posts + comments | `backend/app/ingestion/scrapers/reddit.py` | Posts + comments retrieved, rate-limited |
| 1.5 | **YouTube scraper:** Implement YouTube Data API v3 comment fetcher for fashion haul/review videos | `backend/app/ingestion/scrapers/youtube.py` | Comments fetched for target video IDs |
| 1.6 | **Manual upload handler:** CSV/JSON upload endpoint for curated corpus data | `backend/app/ingestion/scrapers/manual_upload.py`, API route | File uploaded, parsed, stored |
| 1.7 | **Text normalizer:** Strip HTML, handle emoji, detect language (filter non-English), truncate very long posts, normalize whitespace | `backend/app/ingestion/normalizer.py` | Unit tests pass for edge cases |
| 1.8 | **De-duplicator:** Compute SHA-256 content hashes, reject duplicate documents on insert | Integrated into normalizer/storage | Duplicate detection verified |
| 1.9 | **Metadata enricher:** Infer `product_category`, `brand_tier`, `gender_context` from text heuristics + keyword matching; attach `engagement_score` | `backend/app/ingestion/metadata_enricher.py` | Metadata fields populated on stored docs |
| 1.10 | **Ingestion API routes:** `POST /api/v1/pipeline/run` (trigger ingestion), `GET /api/v1/corpus/stats`, `POST /api/v1/corpus/upload` | `backend/app/api/routes/corpus.py`, `pipeline.py` | Endpoints return correct responses |
| 1.11 | **Celery ingestion task:** Wrap scraper execution in Celery task for background processing | `backend/app/workers/ingestion_tasks.py` | Task queues and executes via Redis |
| 1.12 | **Pipeline run tracking:** Log ingestion runs to `pipeline_runs` table with status, counts, timestamps | Integrated into task | Run status queryable via API |
| 1.13 | **Seed corpus:** Execute full ingestion pipeline to build initial corpus of ~3,000–5,000 documents across ≥4 platforms | Database populated | `GET /api/v1/corpus/stats` confirms counts |

### 1.2 Deliverables
- [x] 5 source adapters (Play Store, App Store, Reddit, YouTube, Manual Upload)
- [x] Normalizer + de-duplicator + metadata enricher
- [x] Corpus of ~3,000–5,000 documents stored in `raw_documents`
- [x] Pipeline trigger and corpus stats API endpoints functional
- [x] Background task execution via Celery

### 1.3 Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Reddit API rate limits / OAuth complexity | Use PRAW with OAuth app credentials; implement exponential backoff |
| YouTube API daily quota (10K units) | Pre-select target video IDs, fetch in batches across days |
| App Store scraper reliability | Fallback to manual CSV upload for App Store data if scraper unstable |
| Insufficient corpus size from APIs alone | Supplement with manual upload of curated datasets |

---

## Phase 2: LLM Extraction Pipeline (Layer 2)
**Duration:** 5 days  
**Goal:** Build the Gemini-powered structured extraction layer that processes every document in the corpus and outputs discrete behavioral reason tags in validated JSON — with zero business context priming.

### 2.1 Tasks

| # | Task | Files / Artifacts | Done Criteria |
|---|------|-------------------|---------------|
| 2.1 | **Extraction prompt engineering:** Write the context-light system prompt and few-shot examples per Architecture §3.2 — verify NO mention of wishlist/conversion/purchase goals | `backend/app/extraction/prompts/extraction_system.txt`, `extraction_few_shot.json` | Prompt reviewed, bias-free |
| 2.2 | **Pydantic extraction schema:** Define structured output models (`ExtractionItem`, `ExtractionResponse`) matching the JSON schema in Architecture §3.2 | `backend/app/extraction/schema.py` | Schema validates sample outputs |
| 2.3 | **Gemini client wrapper:** Build reusable client with rate limiting (token bucket), retry logic (exponential backoff, 3 retries), and JSON schema response validation | `backend/app/extraction/gemini_client.py` | Client handles errors gracefully |
| 2.4 | **Batch processor:** Orchestrate document batching (20 docs/call), parallel execution (5 workers), and result persistence to `extractions` table | `backend/app/extraction/batch_processor.py` | Batch of 100 docs processes without errors |
| 2.5 | **Celery extraction task:** Wrap batch processor in background task with progress tracking and checkpointing (resume on failure) | `backend/app/workers/extraction_tasks.py` | Task resumes from last checkpoint on retry |
| 2.6 | **Extraction validation:** Post-processing step to reject low-confidence or malformed extractions; log rejection rates | Integrated into batch processor | Rejection rate < 5% on test batch |
| 2.7 | **Pipeline integration:** Wire extraction stage into the pipeline state machine (`INGESTING → EXTRACTING`) with status tracking | `pipeline_run` updates | Pipeline status reflects extraction progress |
| 2.8 | **Golden set regression test:** Create a set of 20 manually-annotated documents with expected extractions; verify Gemini output quality against ground truth | `backend/tests/golden_set/` | ≥80% recall on expected reasons |
| 2.9 | **Full corpus extraction:** Run extraction across entire ~5,000 document corpus | Database populated | `extractions` table populated, stats logged |
| 2.10 | **Extraction API endpoint:** `GET /api/v1/extractions?doc_id=` for debugging/auditing individual document extractions | `backend/app/api/routes/extractions.py` | Returns extraction JSON for any doc |

### 2.2 Deliverables
- [x] Context-light extraction prompt validated as bias-free
- [x] Gemini client with rate limiting, retry, and schema validation
- [x] Full corpus processed (~5,000 docs → ~15,000–25,000 discrete extraction items)
- [x] Golden set tests passing with ≥80% recall
- [x] Pipeline state machine tracks extraction stage

### 2.3 Critical Guardrail Checklist

> These items must be verified before extraction runs on the full corpus:

- [ ] **Prompt contains ZERO references to:** "wishlist," "conversion," "purchase rate," "30-day," "Myntra Growth," or any business KPI
- [ ] **Prompt instructs open-ended extraction:** "Extract ALL discrete reasons, behaviors, frictions, hesitations, motivations, and decision factors"
- [ ] **Schema enforces `verbatim_quote`:** Every extraction links back to the original user text
- [ ] **Temperature set to 0.1:** Maximizes extraction consistency
- [ ] **Structured output mode enabled:** Gemini returns validated JSON, not free text

---

## Phase 3: Clustering, Taxonomy & Scoring (Layers 3 & 4)
**Duration:** 4 days  
**Goal:** Cluster extracted reasons into a coherent opportunity taxonomy, compute triangulation and frequency metrics, and apply business-context-aware scoring to produce a ranked opportunity list.

### 3.1 Tasks

| # | Task | Files / Artifacts | Done Criteria |
|---|------|-------------------|---------------|
| 3.1 | **Embedding generation:** Compute sentence embeddings for all `reason_text` values using `text-embedding-004` | `backend/app/aggregation/embeddings.py` | Embeddings generated and cached |
| 3.2 | **Hierarchical clustering:** Implement agglomerative clustering with cosine distance; auto-determine cluster count via silhouette score or dendrogram cut | `backend/app/aggregation/clustering.py` | Clusters generated, 8–15 clusters expected |
| 3.3 | **LLM-assisted cluster labeling:** Pass top-10 representative extractions per cluster to Gemini to generate human-readable taxonomy labels and descriptions (context-light prompt — no business priming) | `backend/app/aggregation/taxonomy.py` | Each cluster has a clear, descriptive label |
| 3.4 | **Taxonomy CRUD API:** `GET /api/v1/taxonomy`, `PUT /api/v1/taxonomy/{id}` for PM review, merge, rename, archive | `backend/app/api/routes/taxonomy.py` | Taxonomy viewable and editable via API |
| 3.5 | **Extraction-to-taxonomy mapping:** Assign each extraction to its parent taxonomy node; store foreign key relationship | Migration + code update | Every extraction linked to a taxonomy node |
| 3.6 | **Frequency computation:** Calculate share-of-corpus for each taxonomy node (extraction count / total extractions) | `backend/app/aggregation/opportunity_scorer.py` | Frequency scores sum to ~1.0 |
| 3.7 | **Triangulation scoring:** For each taxonomy node, count how many distinct `source_platform` values contributed extractions; normalize to 0.0–1.0 | `backend/app/aggregation/triangulation.py` | Scores reflect cross-platform confirmation |
| 3.8 | **Segment prevalence analysis:** Compute per-taxonomy breakdown by `inferred_category`, `inferred_gender_context`, `inferred_brand_tier` | `backend/app/aggregation/segment_analyzer.py` | Segment JSON populated per taxonomy node |
| 3.9 | **Conversion relevance scoring (business-context-aware):** Use Gemini (Pro model, temperature 0.1) with a business-context prompt to assess each taxonomy node's relevance to 30-day wishlist-to-purchase conversion. **This is the ONLY stage where business context is injected.** | Scoring prompt + `opportunity_scorer.py` | Relevance scores generated per node |
| 3.10 | **Composite opportunity score:** Combine `frequency × triangulation × conversion_relevance × segment_breadth × actionability` → ranked list | `opportunity_scorer.py` | Ranked opportunity list generated |
| 3.11 | **Scoring API endpoints:** `GET /api/v1/opportunities`, `GET /api/v1/opportunities/{id}`, `GET /api/v1/opportunities/{id}/evidence`, `GET /api/v1/segments/{dimension}/breakdown` | `backend/app/api/routes/opportunities.py`, `segments.py`, `evidence.py` | All endpoints return correct JSON shapes |
| 3.12 | **Celery aggregation task:** Background task for full re-clustering and re-scoring | `backend/app/workers/aggregation_tasks.py` | Re-scoring triggered via API |
| 3.13 | **Pipeline completion:** Wire scoring into state machine (`CLUSTERING → SCORING → COMPLETE`) | Pipeline run updates | Full pipeline runs end-to-end |

### 3.2 Deliverables
- [x] 8–15 opportunity taxonomy nodes with labels and descriptions
- [x] Composite opportunity scores computed and ranked
- [x] Triangulation, frequency, segment breakdown, and conversion relevance scores per node
- [x] Full REST API serving ranked opportunities, evidence, segments
- [x] End-to-end pipeline executable from `IDLE → COMPLETE`

### 3.3 Scoring Stage Prompt Policy

```
┌──────────────────────────────────────────────────────────────────┐
│  STAGES WITHOUT BUSINESS CONTEXT                                  │
│  ✗ Extraction prompt (Phase 2)                                    │
│  ✗ Cluster labeling prompt (Phase 3, Task 3.3)                   │
├──────────────────────────────────────────────────────────────────┤
│  STAGE WITH BUSINESS CONTEXT                                      │
│  ✓ Conversion relevance scoring prompt (Phase 3, Task 3.9)       │
│    → "Given the Myntra Growth Team's goal of increasing the      │
│       percentage of users who purchase a wishlisted item within   │
│       30 days, rate how relevant this opportunity area is to      │
│       improving that metric (0.0 – 1.0)."                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase 4: Frontend Dashboard
**Duration:** 6 days  
**Goal:** Build the interactive discovery dashboard that consumes backend APIs and presents ranked opportunities, segment breakdowns, evidence drill-downs, and pipeline controls — faithfully implementing Google Stitch design specifications.

### 4.1 Tasks

| # | Task | Files / Artifacts | Done Criteria |
|---|------|-------------------|---------------|
| 4.1 | **Design system setup:** Define CSS custom properties (colors, typography, spacing, border radii) from Google Stitch specs; configure Google Fonts (Inter or equivalent) | `frontend/styles/globals.css` | Design tokens applied globally |
| 4.2 | **Layout shell:** Build root layout with sidebar navigation (Home, Opportunities, Segments, Corpus, Pipeline) and top header | `frontend/app/layout.tsx`, `frontend/components/shared/Navbar.tsx`, `Sidebar.tsx` | Navigation between pages works |
| 4.3 | **API integration layer:** Connect frontend API client to live backend endpoints; configure React Query (TanStack Query) for data fetching, caching, loading states | `frontend/lib/api.ts`, query hooks | Data fetches from backend successfully |
| 4.4 | **Dashboard home page — Corpus Summary Header:** Display headline metrics (total documents, platforms, opportunity areas count, last pipeline run timestamp) | `frontend/app/page.tsx`, `CorpusSummaryHeader.tsx` | Metrics render correctly from API |
| 4.5 | **Dashboard home page — Opportunity Ranking Table:** Sortable table showing all opportunity areas ranked by composite score, with columns for rank, label, composite score, frequency, triangulation, conversion relevance, extraction count | `OpportunityRankingTable.tsx` | Table renders, sorts by any column |
| 4.6 | **Dashboard home page — Score Visualization:** Stacked/grouped bar chart or radial chart showing score component breakdown per opportunity area | `CompositeScoreBar.tsx` | Visual matches design spec |
| 4.7 | **Triangulation Heatmap:** Platform × Opportunity matrix heatmap showing which platforms surface which opportunity areas and at what intensity | `TriangulationHeatmap.tsx` | Heatmap renders with correct data |
| 4.8 | **Opportunity Detail Page:** Deep-dive view for a single opportunity — full score breakdown, segment analysis charts, representative quotes, description | `frontend/app/opportunities/[id]/page.tsx` | Click-through from table works |
| 4.9 | **Evidence Explorer:** Paginated list of source quotes backing an opportunity area, with platform badges, confidence indicators, engagement scores, timestamps, and source URL links | `EvidenceQuoteList.tsx`, `QuoteCard.tsx`, `SourceFilter.tsx` | Evidence loads, filters work |
| 4.10 | **Segment Explorer Page:** Interactive breakdown charts — filter opportunities by category (ethnic/western/footwear), gender, price tier, geography; bar/radar visualizations | `frontend/app/segments/page.tsx`, `SegmentBreakdownChart.tsx` | Filters update charts dynamically |
| 4.11 | **Source Distribution Chart:** Pie/donut chart showing platform contribution to total corpus and per-opportunity | `SourceDistributionPie.tsx` | Chart renders with correct proportions |
| 4.12 | **Corpus Stats Page:** Overview of ingested corpus — document count by platform, date range, category distribution; manual upload interface | `frontend/app/corpus/page.tsx` | Stats display, upload form functional |
| 4.13 | **Pipeline Control Page:** Show pipeline run history (status, duration, stage, error logs); trigger new pipeline runs | `frontend/app/pipeline/page.tsx` | Pipeline status displays, trigger button works |
| 4.14 | **Loading, empty, and error states:** Skeleton loaders, empty state illustrations, error boundaries with retry | `LoadingState.tsx`, `EmptyState.tsx` | All states handled gracefully |
| 4.15 | **Responsive layout:** Ensure dashboard is usable on tablet and desktop viewports (1024px+) | CSS adjustments | Layout doesn't break at target widths |
| 4.16 | **Micro-animations & polish:** Hover effects on table rows, smooth transitions on filter changes, chart entrance animations | CSS transitions + Framer Motion (optional) | Interactions feel polished and responsive |

### 4.2 Deliverables
- [x] Fully functional dashboard with 5 pages (Home, Opportunity Detail, Segments, Corpus, Pipeline)
- [x] 6+ chart/visualization components (ranking table, score bars, heatmap, segment charts, pie chart, evidence list)
- [x] Google Stitch design implementation
- [x] Loading/error/empty states throughout
- [x] Responsive on desktop and tablet

### 4.3 Page → API Mapping

| Frontend Page | Primary API Endpoints Consumed |
|---------------|-------------------------------|
| Dashboard Home | `GET /api/v1/opportunities`, `GET /api/v1/corpus/stats` |
| Opportunity Detail | `GET /api/v1/opportunities/{id}`, `GET /api/v1/opportunities/{id}/evidence` |
| Segment Explorer | `GET /api/v1/segments`, `GET /api/v1/segments/{dimension}/breakdown` |
| Corpus Stats | `GET /api/v1/corpus/stats`, `POST /api/v1/corpus/upload` |
| Pipeline Control | `GET /api/v1/pipeline/status`, `POST /api/v1/pipeline/run` |

---

## Phase 5: Deployment, Integration Testing & Polish
**Duration:** 3 days  
**Goal:** Deploy backend to Railway, frontend to Vercel, run end-to-end integration tests, fix issues, and validate the complete system against success criteria.

### 5.1 Tasks

| # | Task | Files / Artifacts | Done Criteria |
|---|------|-------------------|---------------|
| 5.1 | **Railway backend deployment:** Configure `railway.toml`, `Procfile`, `Dockerfile`; provision PostgreSQL and Redis plugins; set environment variables | `backend/railway.toml`, `Procfile`, `Dockerfile` | Backend API reachable at Railway URL |
| 5.2 | **Railway worker deployment:** Deploy Celery worker as separate Railway service | Railway service config | Worker processes tasks from queue |
| 5.3 | **Database migration on Railway:** Run `alembic upgrade head` against production PostgreSQL | Migration applied | All tables exist in prod DB |
| 5.4 | **Vercel frontend deployment:** Connect repo to Vercel, configure build settings and environment variables (`NEXT_PUBLIC_API_BASE_URL` → Railway URL) | `vercel.json` | Frontend loads at Vercel URL |
| 5.5 | **CORS configuration:** Ensure backend allows requests from Vercel domain only | `backend/app/main.py` CORS middleware | Frontend fetches data without CORS errors |
| 5.6 | **End-to-end smoke test:** Trigger full pipeline on deployed system (ingest → extract → cluster → score); verify dashboard displays ranked results | Manual testing | Full pipeline completes on prod |
| 5.7 | **API response validation:** Verify all 11 API endpoints return correct response shapes with production data | Manual + automated checks | All endpoints return valid JSON |
| 5.8 | **Evidence traceability audit:** For the top-3 ranked opportunity areas, manually verify that source quotes are real, correctly attributed, and link to actual platform content | Manual review | Evidence is accurate and traceable |
| 5.9 | **Bias audit:** Review extraction results for signs of business-goal priming; confirm extraction prompt isolation was maintained | Manual review of extractions | No wishlist/conversion language in extraction prompts or outputs |
| 5.10 | **Performance optimization:** Check dashboard load times, optimize slow API queries (add caching, pagination, query tuning) | Code + config changes | Dashboard pages load in < 3s |
| 5.11 | **Security hardening:** Verify API key auth works, CORS is restrictive, no PII in database, Gemini key not exposed to frontend | Security checklist | All items pass |
| 5.12 | **Error handling review:** Verify graceful degradation when Gemini API is unavailable, database connection drops, or scraper fails | Manual fault injection | Errors are caught, logged, user-friendly |
| 5.13 | **Documentation update:** Update `README.md` with setup instructions, architecture overview, deployment guide, and environment variable reference | Root `README.md` | New developer can set up locally from README |

### 5.2 Deliverables
- [x] Backend live on Railway (API + Worker + PostgreSQL + Redis)
- [x] Frontend live on Vercel
- [x] Full pipeline executes end-to-end on production
- [x] Dashboard displays ranked, evidence-backed opportunity areas
- [x] All success criteria validated (see §6 below)

---

## 6. Success Criteria Validation Matrix

Each success criterion from the Problem Statement and Context is mapped to the phase where it is implemented and the phase where it is validated:

| # | Success Criterion | Implemented In | Validated In | Verification Method |
|---|-------------------|----------------|-------------|---------------------|
| 1 | Opportunity areas traceable back to source evidence (auditable) | Phase 2 (verbatim quotes), Phase 3 (evidence API) | Phase 5, Task 5.8 | Manual audit of top-3 opportunities → source quotes → original URLs |
| 2 | Findings triangulated across ≥2 independent sources | Phase 3 (triangulation scoring) | Phase 5, Task 5.6 | Verify `triangulation_score` computation; confirm no high-ranked item has single-source backing |
| 3 | Output distinguishes correlation-level vs. cross-validated patterns | Phase 3 (confidence_level field) | Phase 5, Task 5.6 | Check that `confidence_level` differentiates `high` (≥2 sources) from `low` (single source) |
| 4 | Segment-level differences surfaced, not averaged away | Phase 3 (segment analyzer) | Phase 4, Task 4.10 | Segment Explorer page shows meaningful variance across categories/genders |
| 5 | Extraction free of business-goal priming | Phase 2 (prompt design) | Phase 5, Task 5.9 | Manual review of extraction prompt + sample extraction outputs |
| 6 | Business context applied only at scoring layer | Phase 3, Task 3.9 | Phase 5, Task 5.9 | Confirm only the conversion relevance prompt references the business KPI |
| 7 | Clear, ranked shortlist of opportunity areas | Phase 3 (composite scoring) | Phase 4 (dashboard table) | Dashboard displays sortable ranked table with composite scores |
| 8 | Non-monetary constraint respected | Phase 3 (actionability score) | Phase 5, Task 5.6 | Verify actionability score penalizes pure-price complaints |

---

## 7. Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|-----------|--------|------------|-------|
| R1 | Gemini API rate limits block full-corpus extraction | Medium | High | Implement token-bucket rate limiter; batch processing with checkpointing; fallback to smaller batches | Backend |
| R2 | Scraper APIs change or block access (Reddit, YouTube) | Medium | Medium | Manual CSV upload as fallback; curate datasets offline | Ingestion |
| R3 | Extraction quality is inconsistent across document types | Medium | High | Golden set regression tests; iterative prompt tuning; reject low-confidence extractions | Extraction |
| R4 | Clustering produces too many or too few taxonomy nodes | Medium | Medium | Tune distance threshold; support PM manual merge/split via taxonomy API | Aggregation |
| R5 | Railway free tier resource limits (memory, compute) | Low | Medium | Monitor resource usage; optimize batch sizes; upgrade plan if needed | Deployment |
| R6 | Corpus is too small or skewed toward one platform | Medium | High | Diversify sources early; use manual upload to supplement; track platform distribution | Ingestion |
| R7 | Google Stitch designs not finalized in time | Medium | Low | Build with sensible defaults; refactor styling when Stitch specs arrive | Frontend |
| R8 | Business-context leaks into extraction prompts accidentally | Low | Critical | Prompt review checklist (Phase 2, §2.3); automated prompt scanning for banned keywords | Extraction |

---

## 8. Milestone Summary

| Milestone | Phase | Deliverable | Target |
|-----------|-------|-------------|--------|
| **M0: Foundation Ready** | 0 | Backend + frontend scaffolds running locally, DB schema migrated | Day 3 |
| **M1: Corpus Populated** | 1 | ~5,000 documents from ≥4 platforms in `raw_documents` | Day 8 |
| **M2: Extractions Complete** | 2 | ~15K–25K structured extraction items in `extractions` table | Day 13 |
| **M3: Ranked Opportunities** | 3 | Top-10 opportunity areas ranked by composite score, API serving | Day 17 |
| **M4: Dashboard Live** | 4 | Interactive dashboard with all 5 pages functional locally | Day 23 |
| **M5: Production Launch** | 5 | Backend on Railway, Frontend on Vercel, pipeline validated end-to-end | Day 26 |

---

## 9. Post-Launch: Optional Enhancements (Not In Scope)

These items are explicitly deferred but documented for future consideration:

| Enhancement | Description | Prerequisite |
|-------------|-------------|--------------|
| **Evidence Drill-Down Chatbot** | RAG-based "show me examples of X from Reddit" query interface for PMs | Core pipeline complete |
| **Temporal Trend Analysis** | Track how opportunity area prevalence shifts over time with repeated pipeline runs | ≥3 pipeline runs over weeks |
| **Active Learning Feedback Loop** | PM corrections to taxonomy feed back into clustering model | Taxonomy CRUD + usage data |
| **Automated Pipeline Scheduling** | Cron-triggered re-ingestion and re-extraction | Celery Beat or Railway cron |
| **Multi-Language Support** | Extend extraction to Hindi, Hinglish, and regional language content | Language detection + multilingual Gemini prompts |
| **Export & Reporting** | PDF/CSV export of ranked opportunity reports for stakeholder decks | Dashboard data + export library |
