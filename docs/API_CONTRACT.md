# API contract (MVP)

Base prefix: `/api`. JSON is used unless a route accepts `multipart/form-data`. Protected endpoints use `Authorization: Bearer <access_token>`.

## Health and authentication

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/health` | Public | Liveness check; returns `{"status":"ok"}` |
| POST | `/api/auth/login` | Public | Accepts `{ "email": "...", "password": "..." }`; returns `access_token`, `token_type`, and `user` |
| GET | `/api/auth/me` | Authenticated | Returns the current user profile and role |

## Applications and workflow

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/api/applications` | INSTITUTION | Create a fictional application for the logged-in institution; server assigns its institution ID and initial stage `SUBMITTED` |
| GET | `/api/applications` | Authenticated | List only records visible to the caller; supports `skip`, `limit`, optional `status` |
| GET | `/api/applications/{id}` | Authenticated | Read a single permitted application; returns 404 for inaccessible records |
| POST | `/api/applications/{id}/transition` | Assigned OFFICER, ADMIN | Body: `{ "to_stage": "INITIAL_SCRUTINY", "note": "..." }`; validates transition and records stage history + audit log atomically |
| PATCH | `/api/applications/{id}/assignment` | ADMIN | Body: `{ "assigned_officer_id": 3 }`; assigns an active OFFICER and writes an audit event |
| GET | `/api/applications/{id}/history` | Application participants | Returns stage history and application audit events |
| GET | `/api/applications/{id}/queries` | Application participants | Lists queries raised for this application |
| POST | `/api/applications/{id}/documents` | Application participants | Upload a document for the application (MVP local storage only) |
| POST | `/api/applications/{id}/queries` | Application participants | Raise a query with a message and optional due date |
| POST | `/api/queries/{id}/responses` | Application participants | Add a query response |

## Roles and visibility

- `INSTITUTION`: can create applications and access only applications belonging to its linked institution.
- `OFFICER`: can access only applications assigned to that officer.
- `ADMIN`: can access system-wide demo records.
- Stage transitions are server-authorized and restricted to `OFFICER` or `ADMIN`. Only authorized roles can make final decisions.

## Canonical stage values

`SUBMITTED`, `INITIAL_SCRUTINY`, `DOCUMENT_VERIFICATION`, `COMPLIANCE_CHECK`, `OFFICER_REVIEW`, `INSPECTION`, `FINAL_REVIEW`, `CORRECTION_REQUIRED`, `APPROVED`, `REJECTED`.

Correction flow: an authorized reviewer may send an eligible case to `CORRECTION_REQUIRED`. The system records the stage to resume; a reviewer then returns the case to that recorded stage after a response/correction. Normal transitions cannot skip stages or move backwards.

## Error responses

Use standard FastAPI status codes and JSON detail messages:

- `401 Unauthorized`: missing/invalid token or incorrect login.
- `403 Forbidden`: authenticated user lacks the required role.
- `404 Not Found`: record missing or not visible to the caller.
- `422 Unprocessable Entity`: request validation failed or workflow transition is invalid.

Do not change a path, stage name or request/response field without coordinating with the team and updating this contract.
