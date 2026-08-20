# System Context: "Intently" — Wishlist-to-Purchase Discovery Engine
**Product Management | Myntra Growth Team**  
*AI-Powered User Feedback Analysis & Qualitative Discovery System*

---

## 1. Executive Summary & Strategic Context

### 1.1 Business Problem
Myntra's Growth Team has established a top-line strategic priority:
> **Target Metric:** Increase the percentage of users who purchase at least one item from their wishlist within 30 days of adding it.

Millions of users actively add fashion products to their wishlists as a clear signal of explicit purchase intent. However, only a small fraction convert into purchases within a 30-day window. This gap represents a massive, high-leverage revenue and growth opportunity because **demand is already captured on-platform**—the core challenge is diagnosing *why* and *where* conversion stalls.

### 1.2 Non-Monetary Constraint
- **Strict Boundary:** The eventual product interventions must **NOT** rely on monetary incentives (discounts, markdowns, coupons, cashback, or price drops).
- **Discovery Mandate:** Discovery must diagnose psychological, behavioral, informational, and experiential blockers to unlock **non-monetary levers** (e.g., fit/size confidence, styling context, social validation, trust/credibility, decision fatigue, moodboard ambiguity, urgency framing, and UX friction removal).

---

## 2. System Role & Scope Definition

### 2.1 Core Identity
`Intently` is an **AI-powered qualitative discovery and batch analytics engine** designed to ingest, normalize, analyze, and quantify unstructured public feedback at scale.

```
       [ Public Multi-Source Conversations ]
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  Layer 1: Ingestion & Metadata   │
        └──────────────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  Layer 2: Unbiased LLM Reason    │
        │           Extraction (Gemini)    │
        └──────────────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  Layer 3: Thematic Clustering &  │
        │           Taxonomy Building      │
        └──────────────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  Layer 4: Business Scoring &     │
        │           Prioritization Engine  │
        └──────────────────────────────────┘
                         │
                         ▼
       [ Ranked Opportunity Areas Dashboard ]
```

### 2.2 What This System IS vs. IS NOT

| System Dimension | What It IS | What It IS NOT |
| :--- | :--- | :--- |
| **Pipeline Nature** | Corpus-wide batch extraction & analytics pipeline | A one-off RAG chatbot or conversational assistant |
| **LLM Output** | Structured, causal behavioral tag extraction (JSON) | Free-form sentiment scoring or generic review summarization |
| **Analytical Depth** | Multi-source triangulation with segment breakdowns & scores | Subjective anecdote collation or single-source quoting |
| **Phase Scope** | Rigorous, evidence-backed problem discovery & ranking | Designing or building the consumer-facing shopping feature |

---

## 3. Data Sources to Ingest

The engine ingests multi-channel user discourse across public touchpoints via scrapers, APIs, or curated uploads:

1. **App Store & Play Store Reviews:** Myntra, AJIO, Nykaa Fashion, Tata CLiQ, Amazon Fashion.
2. **Reddit Communities:** `r/IndianFashionAddicts`, `r/india`, `r/TwoXIndia`, `r/IndianSkincareAddicts`, fashion & deal subreddits.
3. **Fashion & Shopping Community Forums:** Niche fashion blogs, user forums, and styling threads.
4. **Social Media Conversations:** Public posts and threads on X (Twitter) and Instagram comments.
5. **Video Platform Comments:** YouTube haul videos, fit reviews, unboxing, trial rooms, and styling breakdowns.
6. **E-Commerce Q&A & Product Reviews:** On-site user queries, sizing debates, quality complaints, and review threads.

---

## 4. Key Research Questions

The discovery engine must extract actionable signals answering 10 primary behavioral questions:

1. **Wishlist Motivation:** Why do users add items to their wishlist initially (intent vs. aspirational moodboarding)?
2. **Drop-Off Frictions:** What specific hurdles prevent a wishlisted product from being purchased?
3. **Lingering Uncertainty:** What doubts remain active *after* a user has already found an item they like?
4. **Postponement Drivers:** What triggers deliberate purchase delay or procrastination?
5. **Evaluation & Comparison:** How do shoppers evaluate and eliminate multiple wishlisted alternatives?
6. **Off-Platform Exploration:** What external validation do users seek outside the app (sizing charts, YouTube try-ons, influencer reels, price tracking)?
7. **Psychological & Practical Levers:** What roles do fit confidence, outfit styling, review authenticity, social validation, and occasion-relevance play?
8. **Intent Ambiguity:** How can the system distinguish active near-term purchasing intent from passive "maybe someday" hoarding?
9. **Segment Disparities:** How do behaviors vary by category (ethnic vs. western vs. footwear), gender, price tier, shopper tenure (new vs. repeat), and tier/geography (metro vs. non-metro)?
10. **Triangulated Signal:** Which pain points recur consistently across $\ge 2$ independent channels versus isolated complaints?

---

## 5. Four-Layer Analytical Architecture

```
Raw Multi-Channel Data
  └─► Layer 1: Ingestion & Normalization
        • De-duplication, cleanup, source metadata (platform, date, category, engagement/upvotes)
  └─► Layer 2: Thematic Causal Extraction (Gemini)
        • Zero-shot / Few-shot structured extraction (Reasons, frictions, behavioral cues)
        • NO business context priming (Preserves unbiased truth)
  └─► Layer 3: Dynamic Taxonomy & Clustering
        • Opportunity clusters: Fit Uncertainty, Styling Friction, Social Validation, Review Distrust, Deferred Decision, Moodboard Ambiguity, etc.
  └─► Layer 4: Quantification & Opportunity Scoring
        • Metrics: Frequency % × Triangulation Index × Inferred Conversion Impact
        • Segment prevalence breakdown
```

### Layer 1: Ingestion & Normalization
- Aggregates raw text across platforms into a unified schema.
- Enriches records with metadata: `source_platform`, `timestamp`, `product_category`, `brand_tier`, `engagement_metrics` (upvotes, likes, helpful votes).

### Layer 2: Thematic Reason Extraction (Gemini)
- Extracts discrete, causal behavioral statements per comment/review into structured JSON.
- **Examples of Discrete Signals:**
  - *"Unsure if the waist will gap based on mixed reviews"* (Fit/Size Uncertainty)
  - *"Waiting to see how I would pair this jacket with existing tops"* (Styling Uncertainty)
  - *"Added to show my friend before ordering"* (Social Validation Dependency)
  - *"Wishlisted 5 similar kurtas to compare later but forgot"* (Choice Overload / Decision Fatigue)

### Layer 3: Clustering & Taxonomy Generation
- Groups atomic extractions into structured, non-overlapping opportunity taxonomy categories:
  - Fit & Sizing Confidence Gap
  - Styling & Outfit Context Deficit
  - Review Authenticity & Trust Deficit
  - Decision Deferral & Procrastination
  - Social Proof & Peer Validation Needs
  - Bookmarking vs. High-Intent Ambiguity
  - Cross-Option Evaluation Friction
  - Occasion Mismatch & Seasonality Shift

### Layer 4: Quantification & Prioritization
- Computes metrics for each taxonomy node:
  - **Frequency:** Share of total corpus mentions.
  - **Triangulation Score:** Number of independent platform types confirming the signal ($\ge 2$ required for high-confidence classification).
  - **Segment Skew:** Normalized prevalence across demographic/category slices.
  - **Composite Opportunity Score:**
    $$\text{Opportunity Score} = \text{Frequency} \times \text{Triangulation Index} \times \text{Inferred Conversion Relevance}$$

---

## 6. Architectural Principles & Guardrails

### 6.1 Strict Separation of Business Context: Extraction vs. Scoring
To eliminate confirmation bias and prevent "leading-the-witness" AI outputs:

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Extraction (Context-Light, Objective Discovery)    │
│ • Prompt instruction: "Extract all discrete frictions,     │
│   reasons, and behaviors mentioned in this text."           │
│ • ZERO mention of "wishlist-to-purchase 30-day conversion"  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Scoring (Context-Aware, Business Prioritization)   │
│ • Apply conversion weighting & business filters to the      │
│   aggregated taxonomy to rank high-leverage opportunity     │
│   areas for Myntra Growth.                                  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Auditability & Evidence Traceability
- Every ranked opportunity area must link back to exact source quotes, timestamps, and platform origins.
- An optional drill-down query layer allows Product Managers to inspect source quotes backing any quantified score.

---

## 7. Technology Stack & Deployment Architecture

```
  ┌──────────────────────────────────────────────────────────┐
  │                 Frontend (Vercel)                        │
  │  • Next.js / React / Vite Dashboard                     │
  │  • Faithful implementation of Google Stitch UI/UX        │
  │  • Interactive filters, opportunity tables, heatmaps    │
  └────────────────────────────┬─────────────────────────────┘
                               │ REST / JSON
                               ▼
  ┌──────────────────────────────────────────────────────────┐
  │                 Backend (Railway)                        │
  │  • Python / FastAPI or Node.js pipeline runner          │
  │  • Data ingestion, normalization, aggregation engine     │
  │  • Google Gemini API client (Structured outputs)         │
  │  • Database / Store for corpus and clustered insights    │
  └──────────────────────────────────────────────────────────┘
```

- **LLM Engine:** Google Gemini API (Structured JSON Schema extraction).
- **Backend Deployment:** Railway (API server, batch workers, database).
- **Frontend Deployment:** Vercel (Interactive insights dashboard).
- **Design System:** Google Stitch UI/UX specifications.
- **Development Tooling:** Antigravity IDE.

---

## 8. Success Criteria & Phase Milestones

1. **Unbiased Extraction:** Clean separation between unbiased LLM extraction and business-weighted scoring.
2. **Cross-Platform Triangulation:** Identified opportunity areas are backed by $\ge 2$ distinct channel types.
3. **Data-Driven Prioritization:** Clear mathematical ranking of friction areas to determine product discovery direction.
4. **Segment Granularity:** Ability to slice results by category, user segment, and intent level.
5. **Readiness for Phase 2:** A prioritized, evidence-backed problem shortlist ready to drive non-monetary solution ideation.
