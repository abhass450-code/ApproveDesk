# Database schema (shared contract)

PostgreSQL is the shared database. SQLAlchemy models live under `backend/app/models/`; Alembic migration changes must be coordinated.

| Table / model | Purpose | Primary ownership |
|---|---|---|
| `institutions` / `Institution` | Synthetic institution directory and tenant key | Member 1 |
| `users` / `User` | Login identity, Argon2 password hash, role, linked institution | Member 1 |
| `applications` / `Application` | Main application and current workflow stage | Member 1 |
| `application_stages` / `ApplicationStage` | Append-only stage transition history | Member 1 |
| `documents` / `Document` | Document metadata and storage location | Member 1 foundation; coordinate upload requirements |
| `queries` / `Query` | Questions, due dates and status | Member 1 foundation |
| `query_responses` / `QueryResponse` | Responses to a query | Member 1 foundation |
| `audit_logs` / `AuditLog` | Actor, action, entity and JSON details | Member 1 foundation |
| Compliance models | Rules, checks, result details | Member 2; own model files and coordinated migration |
| Alert models | Alert status, due/SLA, escalation | Member 3; own model files and coordinated migration |

## Important fields and indexes

- `users.email` is unique; `users.role` is one of `INSTITUTION`, `OFFICER`, `ADMIN`.
- `applications.application_code` is unique and indexed.
- `applications.institution_id`, `applications.assigned_officer_id`, and `applications.current_stage` are indexed.
- Applications are tenant-scoped using `institution_id`; never accept an institution ID from the institution portal as proof of access.
- `application_stages` records the prior and new stage, actor, note and timestamp.
- `audit_logs` records submission, assignment, query/response and transitions. Do not rely only on the mutable current-stage field for history.
- `documents.storage_path` is a local prototype path. Before production, use controlled object storage, upload limits/type checks and malware scanning.
- Timestamps are UTC-aware at the application layer; normalize and document any database-driver differences.

## Migration rules

1. Pull `dev` before creating a migration.
2. Generate and inspect migrations after model changes; do not blindly accept destructive autogeneration.
3. Tell all affected members the migration revision and schema changes.
4. Test `alembic upgrade head` against a fresh empty database.
