# Shadow AI Detector - Frontend Console

Shadow AI Detector is an enterprise cybersecurity console designed to discover AI-related network traffic, catalog AI providers and endpoints, evaluate data egress risks, and monitor organizational compliance.

---

## Getting Started

### Prerequisites

- Node.js (v20+ recommended)
- npm (v10+)

### Local Development

```bash
cd frontend
npm install
npm run dev
```

The frontend development server starts on `http://localhost:5173`.

---

## Configuration

### Environment Variables (`frontend/.env`)

Configure the target backend URL in your `.env` file (copied from `.env.example`):

```bash
VITE_API_BASE_URL=http://localhost:8000
```

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Target URL for backend REST API calls. Trailing slashes are automatically stripped. |

---

## Containerized Deployment (Frontend)

The frontend includes a self-contained production Dockerfile with an optimized Nginx web server:

```bash
cd frontend
docker build -t shadow-ai-frontend .
docker run -p 3000:80 shadow-ai-frontend
```

Access the console at `http://localhost:3000`.

---

## API Contract Alignment

The frontend communicates with the Shadow AI detection backend (`feat/traffic-analyzer-backend` branch) through the following endpoints:

| Feature | Backend Route | Method | Contract & Frontend Integration Status |
| :--- | :--- | :--- | :--- |
| **System Health** | `/health` | `GET` | **Integrated**: Probes backend status and connectivity. |
| **Traffic Ingestion** | `/api/traffic/analyze` | `POST` | **Integrated**: Multipart form-data upload (`.csv`, `.json`). Returns analysis UUID and row ingestion summary. |
| **Analysis Detail** | `/api/traffic/{analysis_id}` | `GET` | **Integrated**: Retrieves metadata and telemetry summary metrics. |
| **Analysis Records** | `/api/traffic/{analysis_id}/records` | `GET` | **Integrated**: Paginated flow records (source IP, destination domain, port, bytes, protocol). |
| **Analysis History** | `/api/traffic` | `GET` | **Integrated**: Historical analysis runs. |
| **AI Inventory** | `/api/inventory` | `GET` | *Pending Backend*: Frontend renders honest zero-mock empty state awaiting endpoint implementation. |
| **Risk Findings** | `/api/risks` | `GET` | *Pending Backend*: Frontend renders honest zero-mock empty state awaiting endpoint implementation. |
| **Dashboard Stats** | `/api/dashboard/stats` | `GET` | *Pending Backend*: Renders first-use state with guidance until metrics are exposed. |
| **Test Reports** | `/api/reports/metrics` | `GET` | *Pending Backend*: Renders *"No evaluation results available."* until metrics are recorded. |

---

## Frontend Quality & Verification

```bash
cd frontend

# Run automated unit and integration tests
npm test

# Run TypeScript check
npm run typecheck

# Run linter
npm run lint

# Build production bundle
npm run build
```
