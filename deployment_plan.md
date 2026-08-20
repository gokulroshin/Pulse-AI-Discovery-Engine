# Pulse Discovery Engine — Cloud Deployment Plan

This document outlines the step-by-step production deployment plan for the **Pulse AI Consumer Discovery Engine**:
- **Frontend Dashboard:** [Vercel](https://vercel.com) (Next.js 15 App Router)
- **Backend API & Data Engine:** [Railway](https://railway.app) (FastAPI + Uvicorn + PostgreSQL 16 + Celery)
- **GitHub Repository:** [`https://github.com/gokulroshin/Pulse-AI-Discovery-Engine`](https://github.com/gokulroshin/Pulse-AI-Discovery-Engine)

---

## 1. Cloud Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Edge Network                      │
│             Next.js 15 Frontend Dashboard                   │
│         https://pulse-ai-discovery-engine.vercel.app        │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / REST (X-API-Key)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Railway Cloud Platform                   │
│                                                             │
│   ┌─────────────────────────┐   ┌───────────────────────┐  │
│   │   FastAPI Web API       │   │ Managed PostgreSQL 16 │  │
│   │  (Port 8000 / $PORT)    │──▶│  (Scraped Corpus &    │  │
│   │                         │   │   Opportunity Nodes)  │  │
│   └────────────┬────────────┘   └───────────────────────┘  │
│                │                                            │
│                ▼                                            │
│   ┌─────────────────────────┐   ┌───────────────────────┐  │
│   │   Google Gemini API     │   │ Managed Redis 7 (Opt) │  │
│   │  (gemini-3.6-flash RAG) │   │  (Celery Job Queue)   │  │
│   └─────────────────────────┘   └───────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Pre-Deployment Checklist

Before starting, ensure you have:
1. **GitHub Access:** Code pushed to `https://github.com/gokulroshin/Pulse-AI-Discovery-Engine`.
2. **Railway Account:** Sign up at [railway.app](https://railway.app) (Free tier / Hobby plan).
3. **Vercel Account:** Sign up at [vercel.com](https://vercel.com) (Hobby / Pro tier).
4. **Google AI Studio Key:** Active Gemini API key from [aistudio.google.com](https://aistudio.google.com).

---

## 3. Phase 1: Deploy Backend on Railway

### Step 3.1: Create Project & Provision PostgreSQL
1. Log into your **Railway Dashboard**.
2. Click **New Project** $\rightarrow$ **Provision PostgreSQL**.
3. Railway will provision a dedicated PostgreSQL 16 instance and generate a connection variable: `${{Postgres.DATABASE_URL}}`.

---

### Step 3.2: Deploy FastAPI Backend Service
1. In the same Railway project, click **New** $\rightarrow$ **GitHub Repo**.
2. Select repository: `gokulroshin/Pulse-AI-Discovery-Engine`.
3. Open the newly added service and go to **Settings**:
   - **Service Name:** `pulse-backend`
   - **Root Directory:** `/backend`
   - **Build Command:** Auto-detected (or leave default, Railway reads `backend/Dockerfile` / `backend/requirements.txt`)
   - **Start Command:** Auto-detected via `backend/Procfile` (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`)

---

### Step 3.3: Configure Backend Environment Variables
Under the **Variables** tab of the `pulse-backend` service, add the following key-value pairs:

| Variable Name | Recommended Value | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables production mode |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Auto-references the Railway PostgreSQL database |
| `GEMINI_API_KEY` | `your_gemini_api_key` | Google AI Studio API key |
| `GEMINI_FLASH_MODEL` | `gemini-3.6-flash` | Primary fast RAG synthesis model |
| `GEMINI_PRO_MODEL` | `gemini-3.6-flash` | Fallback RAG synthesis model |
| `API_SECRET_KEY` | `pulse-production-secret-key-64hex` | Shared API authentication key |
| `PUBLIC_ACCESS_MODE` | `true` | Allows public read-access for portfolio/demo |
| `CORS_ORIGINS` | `["https://*.vercel.app","http://localhost:3000"]` | Permitted cross-origin dashboard domains |
| `LOG_LEVEL` | `INFO` | Application logging level |

*(Optional Redis for async scraping queue: Click **New** $\rightarrow$ **Database** $\rightarrow$ **Redis** and set `REDIS_URL=${{Redis.REDIS_URL}}`)*.

---

### Step 3.4: Generate Public Domain
1. In the `pulse-backend` service settings, scroll to **Networking** $\rightarrow$ **Public Networking**.
2. Click **Generate Domain**.
3. Copy your live backend URL (e.g. `https://pulse-backend-production.up.railway.app`).

---

### Step 3.5: Run Initial Database Migrations & Seed Corpus
You can execute initial setup directly via the **Railway Web Terminal** (or Railway CLI):

1. Go to the `pulse-backend` service $\rightarrow$ click the **Terminal** tab.
2. Run database migration:
   ```bash
   alembic upgrade head
   ```
3. Seed the multi-channel qualitative corpus & precompute taxonomy rankings:
   ```bash
   python scripts/seed_corpus.py
   python scripts/extract_multichannel.py
   python scripts/run_aggregation.py
   ```
4. Verify backend health by opening in your browser:
   `https://pulse-backend-production.up.railway.app/api/v1/health`
   *(Expected response: `{"status":"healthy","version":"0.1.0","environment":"production"}`)*

---

## 4. Phase 2: Deploy Frontend on Vercel

### Step 4.1: Import Repository
1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Select `gokulroshin/Pulse-AI-Discovery-Engine` from the GitHub repository list.

---

### Step 4.2: Configure Build Settings
In the Vercel project configuration screen:
- **Framework Preset:** `Next.js`
- **Root Directory:** Click **Edit** and select `frontend` (Click **Continue**).
- **Build Command:** `npm run build` (Default)
- **Output Directory:** `.next` (Default)
- **Install Command:** `npm install` (Default)

---

### Step 4.3: Set Frontend Environment Variables
In the **Environment Variables** section on Vercel, configure:

| Key | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://pulse-backend-production.up.railway.app` | Your Railway public backend URL |
| `NEXT_PUBLIC_API_KEY` | `pulse-production-secret-key-64hex` | Matches `API_SECRET_KEY` on Railway |

---

### Step 4.4: Deploy Frontend
1. Click **Deploy**.
2. Vercel will build the Next.js production bundle and deploy to the global Edge Network.
3. Once finished, note your live Vercel URL (e.g. `https://pulse-ai-discovery-engine.vercel.app`).

---

## 5. Phase 3: Final Security & CORS Handshake

To allow the live Vercel frontend to query the Railway backend without browser CORS issues:

1. Return to your **Railway Dashboard** $\rightarrow$ `pulse-backend` $\rightarrow$ **Variables**.
2. Update `CORS_ORIGINS` to include your exact Vercel production domain:
   ```json
   ["https://pulse-ai-discovery-engine.vercel.app", "https://*.vercel.app", "http://localhost:3000"]
   ```
3. Railway will automatically redeploy the backend service with the updated CORS configuration in seconds.

---

## 6. Phase 4: Post-Deployment Verification Runbook

Perform the following smoke tests on your live production URL:

| Test Case | Method / Endpoint | Expected Outcome |
|---|---|---|
| **1. Backend Health Check** | `GET https://<railway-url>/api/v1/health` | HTTP 200: `{"status": "healthy"}` |
| **2. Interactive Swagger Docs** | `GET https://<railway-url>/docs` | OpenAPI interactive documentation renders |
| **3. Opportunity Rankings** | `GET https://<railway-url>/api/v1/opportunities` | Returns 15 ranked opportunities with composite scores and multi-platform badges |
| **4. Frontend Dashboard** | `https://<vercel-url>` | Loads Overview table, summary header metrics (1,938 raw docs, 1,554 extractions) |
| **5. AI Insight Search Bar** | Click suggestion: *"Why do users add fashion products to their wishlist?"* | RAG engine returns Executive Takeaway, Key Drivers, and grounded quotes within 2-3 seconds |
| **6. Custom User Inquiry** | Search: *"Do users face decision fatigue while choosing?"* | Gemini 3.6 Flash dynamically synthesizes grounded analysis with authentic verbatim quotes |
| **7. Multi-Source Evidence** | Navigate to Opportunity Details $\rightarrow$ Evidence tab | Displays corroborating quotes from Reddit, App Store, Google Play, and YouTube |

---

## 7. Operational Maintenance & CI/CD

- **Automated CI/CD:** Any commit pushed to `main` on GitHub will automatically trigger:
  - An instant Next.js production rebuild on **Vercel**.
  - An automated container rebuild and zero-downtime rolling deployment on **Railway**.
- **Monitoring & Logs:**
  - View real-time API logs in **Railway** under `pulse-backend` $\rightarrow$ **Deployments** $\rightarrow$ **View Logs**.
  - View frontend edge analytics and web vitals in **Vercel** under **Analytics**.
- **Model Fallbacks:**
  - The backend dynamically cascades across `gemini-3.6-flash`, `gemini-3.5-flash-lite`, and `gemini-3.7-flash` to ensure 100% uptime even during external API demand spikes.
