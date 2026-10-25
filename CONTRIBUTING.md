# Contributing to ApproveDesk

1. Pull the latest `dev` branch before starting work.
2. Use a focused feature branch, for example `feat/backend-workflow`, `feat/compliance-engine`, `feat/alerts`, or `feat/institution-portal`.
3. Keep endpoint paths, status names, schema fields and shared model contracts aligned with `docs/API_CONTRACT.md` and `docs/DATABASE_SCHEMA.md`.
4. Add or update tests for behavior you change.
5. Never commit `.env`, access tokens, API keys, production credentials, uploaded files or real personal data.
6. Open a pull request into `dev`; do not push untested changes straight to `main`.
7. Coordinate Alembic migrations. Do not silently edit a shared model or migration another member is using.

## Commit examples

- `feat: add application workflow transitions`
- `feat: add compliance rules`
- `fix: restrict institution application access`
- `test: cover invalid workflow transitions`
- `docs: clarify query response contract`
