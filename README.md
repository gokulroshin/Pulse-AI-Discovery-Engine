# Pulse — AI Consumer Discovery & Wishlist Behavior Engine

> **Myntra Product & Growth | AI Discovery Engine**  
> An AI-powered qualitative discovery and batch analytics engine designed to diagnose why consumers hesitate or abandon wishlisted items and uncover actionable product/UX levers.

---

## 🏛️ System Architecture

Pulse operates as a **three-tier, continuous customer intelligence platform**:
1. **Layer 1 (Multi-Channel Ingestion)**: Scrapes, normalizes, and deduplicates customer reviews and discussions across Google Play, Apple App Store, Reddit (`r/IndianFashionAddicts`, `r/Myntra`), and YouTube haul comments.
2. **Layer 2 (Context-Light Causal Extraction)**: Extracts objective causal reasons, behavioral frictions, and verbatim quotes with Gemini (`gemini-2.5-flash`) without business KPI priming.
3. **Layer 3 (Semantic Clustering & Taxonomy)**: Agglomerative hierarchical clustering with cosine distance and automated silhouette score optimization to construct an interpretable opportunity taxonomy.
4. **Layer 4 (Business Opportunity Scoring & Q&A)**: Ranks opportunity areas by multi-dimensional composite impact ($\text{Frequency} \times \text{Triangulation} \times \text{Conversion Relevance} \times \text{Segment Breadth} \times \text{Actionability}$) and powers an interactive AI Question-Answering engine over the scraped corpus.

```
┌───────────────────────────────┐     ┌────────────────────────────────┐     ┌──────────────────────────────┐
│  Multi-Source Customer Voice  │     │   Gemini Causal Extraction     │     │  Clustering & Taxonomy       │
│  - Reddit Fashion Communities │ ──> │   - Verbatim quote isolation   │ ──> │  - Cosine Agglomeration      │
│  - Play Store & App Store     │     │   - Unbiased reason parsing    │     │  - Silhouette score opt      │
│  - YouTube Haul Discussions   │     │   - Confidence & Signal Tags   │     │  - Node labeling & hierarchy │
└───────────────────────────────┘     └────────────────────────────────┘     └──────────────┬───────────────┘
                                                                                            │
                                                                                            ▼
┌───────────────────────────────┐     ┌────────────────────────────────┐     ┌──────────────────────────────┐
│  Next.js 15 App Dashboard     │     │   Corpus AI Question Search    │     │  Multi-Metric Scoring Layer  │
│  - Executive Opportunity Table│ <── │   - Q&A grounded in 1,900+ docs│ <── │  - Cross-Source Triangulation│
│  - Cross-Channel Heatmap      │     │   - 10 core discovery queries  │     │  - Intent & Segment Breadth  │
│  - Segment Prevalence Explorer│     │   - Verbatim quote citations   │     │  - Product Lever Feasibility │
└───────────────────────────────┘     └────────────────────────────────┘     └──────────────────────────────┘
```

---

## 📁 Repository Structure

```
├── backend/                  # FastAPI + SQLAlchemy + Celery backend
│   ├── alembic/              # Database schema migrations
│   ├── app/
│   │   ├── api/              # REST API routes (12 endpoints + AI search)
│   │   ├── db/               # SQLAlchemy engine & session factory
│   │   ├── models/           # 5 core ORM models
│   │   ├── ingestion/        # Layer 1 scrapers & normalizers
│   │   ├── extraction/       # Layer 2 LLM extractors
│   │   ├── aggregation/      # Layer 3 & 4 clustering & scoring
│   │   ├── workers/          # Celery background tasks
│   │   ├── config.py         # App configuration & settings
│   │   └── main.py           # FastAPI entrypoint
│   ├── scripts/              # Aggregation, extraction & audit CLI scripts
│   ├── tests/                # 58 automated unit, integration & E2E tests
│   ├── Dockerfile            # Container definition for backend
│   └── railway.toml          # Railway production configuration
│
├── frontend/                 # Next.js 15 (App Router) + TypeScript frontend
│   ├── app/                  # Pages: Dashboard, Opportunity Detail, Segments, Corpus
│   ├── components/           # UI components, AI search bar, charts, evidence explorers
│   ├── lib/                  # API client, TypeScript models, constants
│   ├── styles/               # Design system tokens & CSS styling
│   ├── Dockerfile            # Container definition for frontend
│   └── vercel.json           # Vercel production deployment config
│
├── docker-compose.yml        # Multi-container orchestration (FastAPI + Worker + Postgres + Redis + Next.js)
├── DEPLOYMENT.md             # Production deployment guide for Railway & Vercel
├── Architecture.md           # Technical architecture specifications
├── Context.md                # Strategic business context & 10 core discovery inquiries
├── implementation-plan.md    # 6-Phase implementation roadmap
└── Problem_Statement         # Myntra growth problem statement
```

---

## 🚀 Quick Start Guide

### 1. Local Development (Standard)

#### Backend Setup
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run migrations & start FastAPI server
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- **Dashboard:** [http://localhost:3000](http://localhost:3000)

---

### 2. Local Containerized Stack (Docker Compose)

Launch the full stack (PostgreSQL, Redis, FastAPI, Celery worker, and Next.js frontend):
```bash
docker-compose up --build
```

---

### 3. Production Cloud Deployment

Detailed step-by-step instructions are available in [DEPLOYMENT.md](file:///d:/3.%20Career/Product%20Management/IDE/Myntra-%20Grad%20Project/AI%20Discovery%20Engine/DEPLOYMENT.md):
- **Railway:** Deploys FastAPI backend + Celery worker + Managed PostgreSQL 16 + Redis 7.
- **Vercel:** Deploys Next.js 15 frontend with automatic edge routing.

---

## 🧪 Testing & Verification Audits

### Run Automated Pytest Suite (58 Test Cases)
```bash
cd backend
.venv\Scripts\pytest
```
*Validates API endpoints, clustering algorithms, scoring models, prompt isolation, error handling, and E2E pipeline state machine.*

### Run Evidence Traceability Audit
```bash
python backend/scripts/audit_evidence.py
```
*Verifies that 100% of top opportunity areas link directly to real, verbatim customer quotes from authentic source documents (99.76% verification rate).*

### Run Prompt Isolation & Bias Audit
```bash
python backend/scripts/audit_bias.py
```
*Validates that extraction and cluster labeling prompts contain zero business KPI priming words, ensuring 100% clean isolation.*
