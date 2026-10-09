# Shadow AI Detector

Shadow AI Detector is an enterprise cybersecurity solution designed to discover AI-related network traffic, catalog AI providers and endpoints, evaluate data egress risks, and monitor compliance.

---

## Architecture Overview

```
                                      +------------------------------------+
                                      |          Browser Client            |
                                      |   (React + TypeScript + Vite)      |
                                      +-----------------+------------------+
                                                        |
                              Direct CORS:              |   Via Reverse Proxy:
                              http://localhost:8000/    |   http://localhost:3000/api/...
                                                        |
                                                        v
+-------------------------------+              +------------------------------------+
|        FastAPI Backend        |<-------------|          Nginx Web Server          |
|   (Python 3.11 + Uvicorn)     |   internal   |   (Serves SPA & Proxies /api)      |
+---------------+---------------+              +------------------------------------+
                |
                v
+-------------------------------+
|      PostgreSQL Database      |
|        (v16-alpine)           |
+-------------------------------+
```

---

## Quick Start with Docker Compose

Ensure Docker and Docker Compose are installed and running.

### 1. Start the Full Stack (Database, Backend, and Frontend)

```bash
docker compose up --build
```

- **Frontend Console**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **PostgreSQL**: `localhost:5432`

To run in the background (detached mode):
```bash
docker compose up -d --build
```

To stop containers:
```bash
docker compose down
```

---

## Local Development (Without Docker)

### 1. Backend Service

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Console

```bash
cd frontend
npm install
npm run dev
```

The frontend development server starts on `http://localhost:5173`.

---

## Environment Variables

### Frontend Configuration (`frontend/.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Target URL for backend REST API calls. Trailing slashes are automatically stripped. Set to empty string `""` when relying exclusively on the Nginx `/api` reverse proxy. |

### Docker Compose Configuration (`compose.yaml` / `.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `FRONTEND_PORT` | `3000` | Host port exposing the frontend Nginx web server. |
| `POSTGRES_USER` | `postgres` | Database administrator username. |
| `POSTGRES_PASSWORD` | `postgres` | Database administrator password. |
| `POSTGRES_DB` | `shadow_ai_detector` | PostgreSQL database name. |
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL database. |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173","http://localhost:8000"]` | Allowed CORS origins for browser client communication. |

---

## API Routes & Backend Alignment

| Feature | Backend Route | Method | Contract & Frontend Integration Status |
| :--- | :--- | :--- | :--- |
| **System Health** | `/health` or `/api/v1/health` | `GET` | **Integrated**: Probes backend status and database connectivity. |
| **Traffic Ingestion** | `/api/traffic/analyze` | `POST` | **Integrated**: Multipart form-data upload (`.csv`, `.json`). Returns analysis UUID and row ingestion summary. |
| **Analysis Detail** | `/api/traffic/{analysis_id}` | `GET` | **Integrated**: Retrieves metadata and telemetry summary metrics. |
| **Analysis Records** | `/api/traffic/{analysis_id}/records` | `GET` | **Integrated**: Paginated flow records (source IP, destination domain, port, bytes, protocol). |
| **Analysis History** | `/api/traffic` | `GET` | **Integrated**: Historical runs list. |
| **AI Inventory** | `/api/inventory` | `GET` | *Pending Backend*: Frontend renders honest zero-mock empty state awaiting endpoint implementation. |
| **Risk Findings** | `/api/risks` | `GET` | *Pending Backend*: Frontend renders honest zero-mock empty state awaiting endpoint implementation. |
| **Dashboard Stats** | `/api/dashboard/stats` | `GET` | *Pending Backend*: Renders first-use state with guidance until metrics are exposed. |
| **Test Reports** | `/api/reports/metrics` | `GET` | *Pending Backend*: Renders *"No evaluation results available."* until metrics are recorded. |

---

## Troubleshooting

### 1. CORS Errors (`Cross-Origin Request Blocked`)
- **Cause**: The browser origin (e.g. `http://localhost:3000` or `http://localhost:5173`) is missing from backend's `BACKEND_CORS_ORIGINS`.
- **Solution**: Check that `BACKEND_CORS_ORIGINS` includes your frontend origin. The default includes `3000`, `5173`, and `8000`.

### 2. Large File Upload Errors (`HTTP 413 Payload Too Large`)
- **Cause**: Traffic captures exceeding 50 MB exceed server limits.
- **Solution**: The frontend dropzone validates file size up to 50 MB, matching backend's `MAX_UPLOAD_SIZE_BYTES: 52428800`. Ensure Nginx `client_max_body_size` is configured to `50M` (already set in `frontend/nginx.conf`).

### 3. API Timeout on Large Files
- **Cause**: Network analysis parsing may take time on dense CSV logs.
- **Solution**: `submitTrafficAnalysis` has an extended 60-second timeout. Ensure files do not exceed row limit thresholds.

### 4. SPA Refresh Returns 404 in Production
- **Cause**: Web server attempting to serve non-existent physical directories for client routes like `/traffic`.
- **Solution**: Nginx includes `try_files $uri $uri/ /index.html;` so React Router handles routing seamlessly.

---

## Frontend Quality & Verification

```bash
cd frontend

# Run automated tests
npm test

# Run TypeScript check
npm run typecheck

# Run linter
npm run lint

# Build production bundle
npm run build
```
