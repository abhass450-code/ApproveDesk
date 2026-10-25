# Demo flow

Use the fictional seed data only. The example rules and numeric thresholds used by compliance modules must be labelled as sample/demo rules until verified against an applicable official AICTE source.

1. A synthetic institution signs in and submits a new application.
2. The application appears with status `SUBMITTED`; stage history and audit history are recorded.
3. An officer is assigned the case (assignment UI/API is an integration task; use a database/demo fixture until that feature is added).
4. The officer advances the case one valid stage at a time.
5. A missing document or clarification triggers a query and, when appropriate, `CORRECTION_REQUIRED`.
6. The institution posts a response; the reviewer returns the case to the recorded stage and re-checks it.
7. The reviewer completes `INSPECTION` and `FINAL_REVIEW`, then records `APPROVED` or `REJECTED`.
8. Show the audit log and stage history to demonstrate traceability.

The core sequence must work without AI. AI may summarize documents or assist review, but must not silently make the final approval/rejection decision.
