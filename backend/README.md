# Shadow AI Detector - Traffic Analyzer Backend

Backend service for the **Shadow AI Detector** platform, responsible for analyzing network traffic, identifying unauthorized AI service usage, and evaluating organizational AI risk.

---

## Architecture & Project Structure

The backend is structured according to modular FastAPI production conventions:

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & middleware setup
│   ├── api/                     # API routers and endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py        # Centralized v1 router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── health.py    # Health check endpoint with real component verification
│   ├── core/                    # Core application configuration and logging
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic Settings management
│   │   └── logging.py           # Structured logging configuration
│   ├── db/                      # Database connectivity & session handling
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   └── session.py           # Engine initialization and real DB health checks
│   ├── models/                  # SQLAlchemy ORM models (reserved for upcoming phases)
│   │   └── __init__.py
│   ├── schemas/                 # Pydantic data schemas and validation models
│   │   ├── __init__.py
│   │   └── health.py            # Health response schemas
│   └── services/                # Business logic services (reserved for upcoming phases)
│       └── __init__.py
├── tests/                       # Automated test suite
│   ├── __init__.py
│   ├── conftest.py              # TestClient fixtures
│   └── test_health.py           # Health endpoint and routing tests
├── .env.example                 # Example environment variables
├── requirements.txt             # Phase 1 backend dependencies
└── README.md                    # Backend documentation and run instructions
```

---

## Getting Started

### 1. Prerequisites
- **Python**: 3.10+ (tested on Python 3.13)
- **Git**
- **PostgreSQL**: (Optional for Phase 1 health checks; required for persistence in later phases)

---

### 2. Virtual Environment Setup

Navigate to the `backend` directory and create an isolated virtual environment:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```

---

### 3. Install Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Copy the example configuration to `.env`:

```bash
cp .env.example .env
```

On Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

Edit `.env` to configure your settings (e.g. database credentials, host, port, CORS origins).  
*Note: If no database URL is specified, the application will still start and report the database as `not_configured` without throwing errors.*

---

### 5. Running the Application

Run the development server using Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively, from the `backend/` directory:

```bash
python -m app.main
```

The service will be accessible at:
- **Root**: [http://localhost:8000/](http://localhost:8000/)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health) or [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 6. Running Tests

Run the test suite using `pytest`:

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

---

## Health Check Details

The `GET /health` endpoint checks and reports real operational status:
- `status`: Overall application status (`healthy`, `degraded`, or `unhealthy`).
- `components.app`: Confirms FastAPI process responsiveness (`up`).
- `components.database`:
  - `up`: Successfully executed `SELECT 1` on the configured PostgreSQL instance.
  - `not_configured`: No database URL is configured in the environment.
  - `down`: Database is configured but unreachable.

---

## Upcoming Phases
- **Traffic Ingestion**: Ingestion pipelines for proxy logs, PCAP, and NetFlow data.
- **AI Service Signatures**: Pattern recognition and signatures for generative AI services.
- **Risk Scoring Engine**: Calculation of enterprise risk scores based on data sensitivity and unauthorized service usage.
