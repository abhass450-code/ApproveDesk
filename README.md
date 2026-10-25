# ApproveDesk

**SIH26262 — AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System**

ApproveDesk is a prototype for coordinating institutional applications, document scrutiny, compliance checks, officer review, queries, inspections, decisions and audit history. The repository is a monorepo so all six team members can work against the same agreed contracts.

> **Prototype disclaimer:** This is a student/demo system using fictional data. Numerical compliance thresholds are sample rules, not official AICTE regulations unless verified against applicable official sources. AI assistance is optional; the core workflow must work without an AI provider.

## Technology

- **Frontend:** Next.js App Router, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, Pydantic
- **Database:** PostgreSQL, SQLAlchemy 2, Alembic
- **Authentication:** JWT access tokens; passwords hashed with Argon2 through `pwdlib`
- **Local services:** Docker Compose
- **Planned deployment:** Vercel (frontend) + Render (backend), subject to team account/provider availability

## Repository layout

```text
ApproveDesk/
├── .github/workflows/ci.yml
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/routes/          # Auth, applications, queries
│   │   ├── core/                # Settings and security
│   │   ├── db/                  # SQLAlchemy base/session
│   │   ├── models/              # Shared database models
│   │   ├── schemas/             # Request/response contracts
│   │   ├── services/            # Workflow/state-machine logic
│   │   └── main.py
│   ├── scripts/seed_demo.py     # Fictional local-only demo accounts
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── docs/
│   ├── API_CONTRACT.md
│   ├── DATABASE_SCHEMA.md
│   ├── DEMO_FLOW.md
│   └── TEAM_WORKFLOW.md
├── frontend/                    # Next.js + TypeScript + Tailwind
├── compose.yaml                 # Local PostgreSQL
└── CONTRIBUTING.md
```

## Quick start (Windows PowerShell)

### 1. Start PostgreSQL

From the repository root:

```powershell
docker compose up -d db
docker compose ps
```

### 2. Configure and run the backend

```powershell
cd backend
Copy-Item .env.example .env
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed_demo
uvicorn app.main:app --reload --port 8000
```

If Python 3.13 is not installed, use a Python version agreed by the backend team and keep it consistent across developers. The local `.env` must stay untracked.

- Health check: http://localhost:8000/api/health
- Interactive API docs: http://localhost:8000/docs

### 3. Run the frontend

Open a second terminal at the repository root:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. `NEXT_PUBLIC_API_BASE_URL` should point to `http://localhost:8000/api` for local development.

### 4. Run backend tests

From the repository root:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Tests use an isolated in-memory SQLite database and do not need the local Postgres service.

## Fictional demo accounts

The seed script creates synthetic accounts for one institution, one officer and one admin. It uses a clearly documented **local demo password only**; change it before any shared deployment. Never use real personal data, production credentials or secrets in this repository.

## Workflow at a glance

`SUBMITTED → INITIAL_SCRUTINY → DOCUMENT_VERIFICATION → COMPLIANCE_CHECK → OFFICER_REVIEW → INSPECTION → FINAL_REVIEW → APPROVED / REJECTED`

A defined `CORRECTION_REQUIRED` route allows a case to return to the stage where correction was requested. Transitions create stage-history and audit records in the same database transaction. Only an authorized OFFICER or ADMIN can change stages or make a final decision.

## Team ownership

See [docs/TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md). Work in feature branches, open pull requests into `dev`, and keep `main` for tested releases. Coordinate model and migration changes before editing shared schema.
