# Shadow AI Detector - Frontend Console

A cybersecurity web console built with **React**, **TypeScript**, **Vite**, **Tailwind CSS**, **TanStack Query**, and **Axios**, following the **Pixel Arcade Design System**.

Shadow AI Detector empowers organizational security administrators to discover AI-related network traffic, catalog AI providers and endpoints, evaluate data egress risks, and monitor compliance.

---

## 1. API Configuration

The frontend communicates with the Shadow AI detection backend through a centralized Axios client.

### Environment Variable

Configure the target backend URL in your `.env` file (copied from `.env.example`):

```bash
# Default local development server runs at http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000
```

- If `VITE_API_BASE_URL` is omitted, the application automatically defaults to `http://localhost:8000`.
- All requests are configured with a 15-second default timeout (extended to 60s for file uploads).
- Network disconnections and server errors trigger consistent error handling without substituting mock or dummy data.

---

## 2. API Contract with Backend

The following REST endpoints form the contract between the frontend and the backend detection service:

| Method | Endpoint | Description | Request Format | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Backend availability probe (if implemented) | None | `{ status: string, version?: string, uptime?: number }` |
| `POST` | `/api/traffic/analyze` | Submit traffic capture file for AI analysis | `multipart/form-data` (`file: File`) | `{ analysisId: string, status: string, message: string }` |
| `GET` | `/api/traffic/{analysis_id}` | Retrieve results of traffic analysis job | None | `{ analysisId, status, summary, records: [...] }` |
| `GET` | `/api/inventory` | Retrieve catalog of discovered AI endpoints | None | `EndpointInventoryItem[]` |
| `GET` | `/api/inventory/{endpoint_id}` | Retrieve detailed endpoint metadata | None | `EndpointDetail` |
| `GET` | `/api/dashboard/stats` | Retrieve summary operational counts | None | `DashboardStats` |
| `GET` | `/api/reports/metrics` | Retrieve model evaluation metrics | None | `TestEvaluationMetrics` |
| `GET` | `/api/risks` | Retrieve detected risk policy violations | None | `RiskAssessment[]` |

### File Uploads (`/api/traffic/analyze`)
Traffic captures (`.pcap`, `.pcapng`, `.json`, `.csv`, `.log`) are submitted as **`multipart/form-data`** containing the file payload. The frontend does not send raw JSON for file upload requests.

---

## 3. Data Integrity & Honest UI States

- **Zero Mock Policy**: The application strictly avoids fabricated metrics, dummy charts, or synthetic endpoint records.
- When an API endpoint is not yet reachable or implemented, the UI renders informative **Query Error States** with the exact error details and a **Retry** action.
- When an API endpoint responds with empty datasets, the UI renders styled **Empty States** awaiting ingestion.
- The top header features a live **API Status Indicator** showing `CONNECTED`, `CHECKING`, or `OFFLINE` with a direct retest action.

---

## 4. Development & Build Scripts

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run TypeScript type check
npm run typecheck

# Run linter
npm run lint

# Build production bundle
npm run build
```
