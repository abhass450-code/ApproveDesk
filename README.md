# ApproveDesk (AICTE NiyamSetu prototype)

One role-based web application for the SIH26262 problem statement: institutions submit
applications and respond to queries; officers review documents, run compliance checks and
take authorized workflow actions; admins assign officers, configure sample rules and monitor
alerts. An AI assistant summarizes grounded record facts — it never approves or rejects.

> Prototype with synthetic/demo data only. No official AICTE affiliation is implied.
> Sample compliance thresholds are demo assumptions, NOT official requirements, until
> verified against the applicable AICTE Approval Process Handbook / circulars.

## Stack

Next.js (App Router, TypeScript, Tailwind) · FastAPI · SQLAlchemy + Alembic · SQLite locally
(Postgres via `compose.yaml` optional) · JWT + Argon2 auth · optional OpenAI-compatible AI provider.

## Repository layout

- `frontend/` — one Next.js app with role-based routes (`/institution`, `/officer`, `/admin`)
- `backend/` — FastAPI app (`app/api/routes`, `app/models`, `app/services`, `app/scripts/seed_demo.py`)
- `docs/` — API contract, database schema, demo flow

## Local setup (Fedora/Linux)

```bash
# Backend
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # SQLite default works out of the box
alembic upgrade head
python -m app.scripts.seed_demo
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
cp .env.example .env.local    # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
npm install && npm run dev
Open http://localhost:3000 and sign in. API docs: http://localhost:8000/docs

### Synthetic demo accounts (local only — never deploy these)

| Role        | Email                        | Password                  |
|-------------|------------------------------|---------------------------|
| INSTITUTION | institution.demo@example.com | Demo-Only-ChangeMe-2026!  |
| OFFICER     | officer.demo@example.com     | Demo-Only-ChangeMe-2026!  |
| ADMIN       | admin.demo@example.com       | Demo-Only-ChangeMe-2026!  |

## Golden demo (repeatable)

`python -m app.scripts.seed_demo` resets the scenario: DEMO-APP-0001 (faculty_count 18 fails
the sample rule >= 20, due-soon deadline, open officer query) and DEMO-APP-0002 (overdue).
Flow: institution submits -> admin assigns officer -> officer advances stages -> compliance
FAIL -> alert (deduplicated on repeat scans) -> officer query -> institution responds and
corrects data -> re-check PASS -> authorized stage advance -> full audit trail. The AI
assistant answers from recorded facts with source labels, with or without an AI provider key.

## AI assistance disclosure

`AI_API_KEY`/`AI_BASE_URL`/`AI_MODEL` are optional backend-only settings. Without a key the
assistant returns deterministic, grounded answers from the database. AI output is never used
to approve/reject an application or override a deterministic compliance result.

## Tests and checks

```bash
cd backend && pytest -q
cd frontend && npm run lint && npm run build
Deployment

    Backend (Render): Web Service, root directory backend; build pip install -r requirements.txt;
    start alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT.
    Env: DATABASE_URL (hosted Postgres), long random JWT_SECRET, CORS_ORIGINS (exact frontend origin),
    optional AI_API_KEY.
    Frontend (Vercel): import the repo, root directory frontend;
    env NEXT_PUBLIC_API_BASE_URL=https://<your-backend>/api. Add the Vercel origin to backend CORS_ORIGINS.
    Note: local uploads/ storage is for development; production needs durable object storage.

Known limitations (hackathon prototype)
Sample rule values are demo-only; no official checklist mapping is loaded; OCR/document
authenticity checks are out of scope; alerts use an on-demand scan (scheduler optional);
IDs are integers (documented convention) not UUIDs.
