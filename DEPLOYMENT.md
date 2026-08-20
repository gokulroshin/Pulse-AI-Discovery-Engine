# Pulse Discovery Engine — Production Deployment Guide

This guide provides end-to-end instructions for deploying the **Pulse Discovery Engine** across cloud platforms:
- **Backend & Workers:** Railway (FastAPI + Celery + PostgreSQL + Redis)
- **Frontend:** Vercel (Next.js 15 App Router)
- **Local / Self-Hosted:** Docker Compose (Multi-container stack)

---

## 1. Cloud Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Edge Network                      │
│        Pulse Frontend Dashboard (Next.js 15 App)            │
│         https://pulse-discovery.vercel.app                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / REST (X-API-Key)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Railway Cloud Services                   │
│                                                             │
│   ┌─────────────────────────┐   ┌───────────────────────┐  │
│   │   FastAPI Web API       │   │ Celery Worker Engine  │  │
│   │  (Port 8000 / $PORT)    │   │  (Scraping & Scoring) │  │
│   └────────────┬────────────┘   └───────────┬───────────┘  │
│                │                            │               │
│                ├────────────────────────────┤               │
│                ▼                            ▼               │
│   ┌─────────────────────────┐   ┌───────────────────────┐  │
│   │  Managed PostgreSQL 16  │   │    Managed Redis 7    │  │
│   │   (Relational Corpus)   │   │   (Queue & Broker)    │  │
│   └─────────────────────────┘   └───────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Railway Deployment (Backend, Workers & DBs)

### Step 2.1: Provision PostgreSQL & Redis on Railway
1. Open [Railway Dashboard](https://railway.app) and create a **New Project**.
2. Click **Add Service** $\rightarrow$ **Database** $\rightarrow$ **PostgreSQL**.
3. Click **Add Service** $\rightarrow$ **Database** $\rightarrow$ **Redis**.

### Step 2.2: Deploy FastAPI Web Service
1. In your Railway project, click **New** $\rightarrow$ **GitHub Repo** $\rightarrow$ Select this repository.
2. Under **Settings**:
   - **Root Directory:** `/backend`
   - **Build Command:** Auto-detected via Nixpacks or Dockerfile (`backend/Dockerfile`).
3. Set the following **Environment Variables**:
   | Variable | Example / Value | Description |
   |---|---|---|
   | `ENVIRONMENT` | `production` | Runtime mode |
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Auto-populated by Railway Postgres |
   | `REDIS_URL` | `${{Redis.REDIS_URL}}` | Auto-populated by Railway Redis |
   | `CELERY_BROKER_URL` | `${{Redis.REDIS_URL}}` | Celery broker queue URL |
   | `CELERY_RESULT_BACKEND` | `${{Redis.REDIS_URL}}` | Celery result storage |
   | `GEMINI_API_KEY` | `AIzaSy...` | Google AI Studio API key |
   | `API_SECRET_KEY` | `pulse-production-secret-key-64hex` | Shared API authentication key |
   | `CORS_ORIGINS` | `["https://pulse-discovery.vercel.app","https://*.vercel.app"]` | Allowed CORS origins |

4. Click **Deploy**. Note your generated Railway public domain (e.g. `https://pulse-backend-production.up.railway.app`).

### Step 2.3: Deploy Celery Background Worker Service
1. Click **New** $\rightarrow$ **GitHub Repo** $\rightarrow$ Select this repository.
2. Under **Settings**:
   - **Root Directory:** `/backend`
   - **Custom Start Command:** `celery -A app.workers worker --loglevel=info -c 4`
3. Add the same Environment Variables (`DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, `API_SECRET_KEY`).
4. Click **Deploy**.

### Step 2.4: Apply Database Migrations & Initial Corpus
Run migration and clustering scripts directly via Railway CLI or one-off deployment task:
```bash
# In Railway CLI or backend console:
alembic upgrade head
python scripts/run_aggregation.py
```

---

## 3. Vercel Deployment (Frontend)

1. Open [Vercel Dashboard](https://vercel.com) and click **Add New Project**.
2. Import the GitHub repository.
3. Configure Project Settings:
   - **Framework Preset:** `Next.js`
   - **Root Directory:** `frontend`
4. Set Environment Variables:
   | Variable | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://pulse-backend-production.up.railway.app` |
   | `NEXT_PUBLIC_API_KEY` | `pulse-production-secret-key-64hex` |
5. Click **Deploy**.
6. Once deployed, add your Vercel production domain to the `CORS_ORIGINS` environment variable on the Railway backend.

---

## 4. Local Deployment with Docker Compose

To run the entire multi-container production stack locally:

1. Clone the repository and navigate to root:
   ```bash
   git clone <repo-url>
   cd "AI Discovery Engine"
   ```

2. Configure environment file `.env`:
   ```bash
   cp backend/.env.example .env
   # Add your GEMINI_API_KEY inside .env
   ```

3. Launch all 5 containers:
   ```bash
   docker-compose up --build
   ```

4. Access services:
   - **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
   - **FastAPI API & Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 5. Production Health & Verification Checklist

Run verification after deployment:

- [ ] **Health Endpoint:** `GET https://<railway-domain>/health` returns `{"status": "healthy"}`
- [ ] **Opportunities Endpoint:** `GET https://<railway-domain>/api/v1/opportunities` returns 15 ranked opportunities.
- [ ] **AI Insight Search:** `POST https://<railway-domain>/api/v1/insights/ask` responds with grounded synthesis.
- [ ] **Evidence Drilldown:** Clicking any opportunity on the Vercel dashboard loads real verbatim quotes.
- [ ] **CORS Verification:** No browser CORS warnings on the Vercel domain.
- [ ] **Audit Validation:** `python scripts/audit_evidence.py` and `python scripts/audit_bias.py` both report `[PASSED]`.
