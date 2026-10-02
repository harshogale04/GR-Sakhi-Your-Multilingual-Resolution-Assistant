# MAHA-GR Deployment & Production Handover Guide

**Cloud Deployment Guide for Backend (Render / Railway) and Frontend (Vercel)**  
*Hackathon Track: AI for Bharat in Indian Languages*

---

## 1. Deployment Overview & Architecture

MAHA-GR is designed for cloud-native deployment:
- **Backend**: FastAPI Python application deployed as a Web Service on **Render** or **Railway**.
- **Frontend**: Vite + React Single-Page Application (SPA) deployed on **Vercel**.
- **Managed Databases**: Supabase (PostgreSQL & Storage) and Pinecone (Serverless Vector DB).

```
[ Citizen Browser ]
        │
        ├─────────────────────────────┐
        ▼                             ▼
[ Vercel CDN ]               [ Render / Railway ]
(React SPA Static Assets)     (FastAPI Python Web Service)
        │                             │
        │                             ├─► [ Supabase PostgreSQL & Storage ]
        │                             ├─► [ Pinecone Vector DB ]
        │                             └─► [ Google Gemini Flash & Embeddings ]
```

---

## 2. Backend Deployment (Render or Railway)

### 2.1. Production Startup Command
The backend dynamically reads the `$PORT` environment variable provided by Render or Railway:

```bash
# If Root Directory is project root:
uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}

# If Root Directory is configured as 'backend/':
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

A `Procfile` is pre-configured in both the project root and `backend/`:
```text
web: uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### 2.2. Environment Variables Configuration
Set the following environment variables in the Render / Railway Dashboard:

| Variable | Value / Example | Required | Description |
|---|---|---|---|
| `PROJECT_NAME` | `MAHA-GR` | Yes | Application identifier |
| `ENVIRONMENT` | `production` | Yes | App environment (`production` disables debug docs) |
| `DEBUG` | `false` | Yes | Set to `false` in production |
| `API_V1_PREFIX` | `/api/v1` | Yes | API path prefix |
| `CORS_ORIGINS` | `https://your-app.vercel.app,http://localhost:5173` | Yes | Allowed frontend domains (comma-separated) |
| `SUPABASE_URL` | `https://xyzcompany.supabase.co` | Yes | Supabase Project URL |
| `SUPABASE_KEY` | `eyJhbGciOi...` | Yes | Supabase **Service Role Key** (server-side only) |
| `SUPABASE_STORAGE_BUCKET` | `government-resolutions` | Yes | Storage bucket name |
| `PINECONE_API_KEY` | `pcsk_...` | Yes | Pinecone API Key |
| `PINECONE_INDEX_NAME` | `maha-gr-index` | Yes | Pinecone Index (768-dim, cosine) |
| `GEMINI_API_KEY` | `AIzaSy...` | Yes | Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Yes | LLM for grounded Q&A |
| `GEMINI_EMBEDDING_MODEL`| `models/gemini-embedding-001`| Yes | 768-dim embedding model |
| `PYTHONPATH` | `.` | Yes | Python module resolution |

### 2.3. Health Check Configuration
- **Health Check Path**: `/api/v1/health`
- **Expected Status**: `200 OK`
- When deploying, configure your PaaS health check to probe `/api/v1/health`.

### 2.4. Production Limitations & Background Processing Considerations
- **FastAPI BackgroundTasks**: The prototype processes document uploads asynchronously using FastAPI's in-process `BackgroundTasks`. 
  - *Limitation on Free PaaS*: On free-tier instances (e.g. Render Free Dyno), background threads may be terminated if the container sleeps or restarts during a heavy OCR job on a 20-page PDF.
  - *Production Recommendation*: For high-concurrency enterprise deployments, replace `BackgroundTasks` with a dedicated job queue (**Celery** or **ARQ**) backed by **Redis**, running on a separate worker container.
- **Timeouts**: Configure the web service timeout to at least **60 seconds** to accommodate large PDF uploads and external Gemini multimodal API calls.

---

## 3. Frontend Deployment (Vercel)

### 3.1. Build Settings
In the Vercel Project Dashboard:
- **Framework Preset**: `Vite`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (runs `tsc -b && vite build`)
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### 3.2. Single-Page Application (SPA) Routing Configuration
Because MAHA-GR uses React Router v7 with browser history routes (`/ask`, `/search`, `/library`, `/settings`), refreshing any subpage will return an HTTP 404 error unless client-side routing is configured.

This is solved by the pre-configured `frontend/vercel.json`:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### 3.3. Frontend Environment Variables
Set the following variables in Vercel:

| Variable | Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `https://your-backend.onrender.com` | Base URL of deployed FastAPI backend (no trailing slash) |
| `VITE_API_V1_PATH` | `/api/v1` | API version path |

> [!CAUTION]
> **No Exposed Secrets**: Never prefix Supabase service-role keys, Pinecone keys, or Gemini keys with `VITE_`. In MAHA-GR, all external service credentials are kept strictly on the backend.

---

## 4. Supabase & Pinecone Cloud Checklist

Before deploying the backend, ensure your managed services are ready:

### Supabase Checklist
1. **Existing Tables**: Confirm `documents` and `chunks` tables exist in your Supabase database.
2. **Storage Bucket**: Create a bucket named `government-resolutions` (or matching `SUPABASE_STORAGE_BUCKET`).
3. **Bucket Permissions**: The bucket can remain private because the backend accesses it via the Service Role Key and streams downloads via `/api/v1/documents/{id}/download`.
4. **Service Role Key**: Obtain the service role key from `Project Settings -> API -> Project API keys -> service_role`.

### Pinecone Checklist
1. **Index Creation**: Create an index named `maha-gr-index`.
2. **Dimensions**: Set dimensions to **768** (must match `gemini-embedding-001`).
3. **Metric**: Select **Cosine** similarity.
4. **Environment**: Serverless (AWS / us-east-1 or GCP / us-central1).

---

## 5. Prototype vs. Enterprise Production Infrastructure

| Feature | Hackathon Prototype (Current) | Enterprise Production (Next Steps) |
|---|---|---|
| **Background Jobs** | In-process FastAPI `BackgroundTasks` | Celery / Redis / AWS SQS with worker autoscaling |
| **OCR Processing** | Local Tesseract + Gemini Vision fallback | Distributed OCR cluster (PaddleOCR / TrOCR on GPU) |
| **Database Pooling** | Direct async Supabase connection | PgBouncer / Supabase Connection Pooler (Port 6543) |
| **Rate Limiting** | Open API endpoints | Redis-backed token bucket (`slowapi` or Cloudflare WAF) |
| **Observability** | Structured console logger | OpenTelemetry + Datadog / Grafana Loki |
| **PDF Storage** | Supabase Storage with API streaming proxy | Cloudflare R2 / AWS S3 with signed CDN URLs |

---

## 6. Actual Deployment Status

> [!NOTE]
> **Deployment Status Declaration**:
> - The codebase is **fully prepared and verified locally**:
>   - Backend production entrypoint with dynamic `$PORT` handling verified.
>   - `frontend/vercel.json` SPA rewrites created and validated.
>   - Frontend build tested (`tsc -b && vite build` passed with 0 errors).
>   - Backend test suite verified (90/90 tests passed).
>   - Standalone Marathi benchmark verified (9/9 passed, 100%).
> - **The project has NOT yet been deployed to live cloud URLs** (waiting for student team's cloud account credentials and domain selection).
