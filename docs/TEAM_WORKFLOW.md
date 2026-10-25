# Team ownership and Git workflow

## Shared ownership map

| Member | Primary area |
|---|---|
| 1 — Backend + Workflow Lead | FastAPI foundation, DB/session, users/institutions/applications/documents/queries/audit models, auth, assignment, workflow, API contract and initial migration |
| 2 — Compliance | Compliance rules/checks, result schema, compliance logic, contract with Member 1 |
| 3 — Alerts | Alerts, deadlines/SLA, escalation logic and alert contract |
| 4 — Institution portal | Institution-facing Next.js UI |
| 5 — Officer/Admin portal | Officer/admin UI and shared frontend API helper/types |
| 6 — AI + QA + deployment coordination | Optional AI integration, end-to-end QA, deployment coordination |

## Branches

- `main`: tested releases only.
- `dev`: integration branch.
- Feature branches: `feat/backend-workflow`, `feat/compliance-engine`, `feat/alerts`, `feat/institution-portal`, `feat/officer-admin-portal`, `feat/ai-qa-deploy`.

## First-time setup

The repository owner creates the base scaffold on `main`, creates and pushes `dev`, then begins implementation on `feat/backend-workflow`. Other members clone the repository after the scaffold is pushed and branch from the latest `dev`.

```powershell
git switch dev
git pull origin dev
git switch -c feat/your-feature
# work and test
git status
git add .
git commit -m "feat: describe your change"
git push -u origin feat/your-feature
```

Open a pull request to `dev`. Never commit `.env` files. Discuss shared schema, API and migration changes before coding them.
