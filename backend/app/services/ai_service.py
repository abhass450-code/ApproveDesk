"""Grounded AI assistant: deterministic answers from saved records first (M6 guide Step 5),
optional provider polish when AI_API_KEY is configured (Step 7 bounded behaviour)."""
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.application import Application
from app.models.compliance import ComplianceResult
from app.models.document import Document
from app.models.query import Query
from app.models.user import User
from app.schemas.common import UserRole
from app.services.workflow_service import ALLOWED_TRANSITIONS


def visible_application(db: Session, user: User, application_id: int) -> Application | None:
    app = db.get(Application, application_id)
    if app is None:
        return None
    if user.role == UserRole.ADMIN.value:
        return app
    if user.role == UserRole.INSTITUTION.value and app.institution_id == user.institution_id:
        return app
    if user.role == UserRole.OFFICER.value and app.assigned_officer_id == user.id:
        return app
    return None


def pick_application(db: Session, user: User, application_id: int | None) -> Application | None:
    if application_id is not None:
        return visible_application(db, user, application_id)
    stmt = select(Application).order_by(Application.updated_at.desc())
    if user.role == UserRole.INSTITUTION.value:
        if user.institution_id is None:
            return None
        stmt = stmt.where(Application.institution_id == user.institution_id)
    elif user.role == UserRole.OFFICER.value:
        stmt = stmt.where(Application.assigned_officer_id == user.id)
    return db.scalars(stmt.limit(1)).first()


def latest_results(db: Session, application_id: int) -> list[ComplianceResult]:
    rows = db.scalars(select(ComplianceResult).where(ComplianceResult.application_id == application_id)
                      .order_by(ComplianceResult.evaluated_at.desc(), ComplianceResult.id.desc())).all()
    seen: set[str] = set()
    latest: list[ComplianceResult] = []
    for row in rows:
        if row.rule_code not in seen:
            seen.add(row.rule_code)
            latest.append(row)
    return latest


def build_grounded_answer(db: Session, user: User, message: str,
                          application: Application | None) -> tuple[str, list[dict], list[dict], bool]:
    """Returns (answer, sources, suggested_actions, needs_human_review). Facts come only from the DB."""
    if application is None:
        return ("I could not find an application in your permitted scope. Open a case page and ask again from there.",
                [], [], True)

    lower = message.lower()
    code = application.application_code
    prefix = {"INSTITUTION": "/institution", "OFFICER": "/officer", "ADMIN": "/admin"}.get(user.role, "/institution")
    sources: list[dict] = [{"type": "application", "id": str(application.id),
                            "label": f"Application {code} (stage {application.current_stage})"}]
    actions: list[dict] = [{"label": "Open case", "route": f"{prefix}/applications/{application.id}"}]

    if any(word in lower for word in ("fail", "compliance", "rule", "violation")):
        results = latest_results(db, application.id)
        if not results:
            return (f"No compliance results are recorded for {code} yet. An officer must run a compliance check first.",
                    sources, actions, True)
        lines = [f"Compliance results for {code} (latest per rule):"]
        for result in results:
            gap = f", gap {result.gap:g}" if result.gap is not None else ""
            lines.append(f"- {result.rule_code} v{result.rule_version}: {result.status} "
                         f"(expected {result.expected}, actual {result.actual}{gap}). {result.explanation or ''}")
            sources.append({"type": "compliance_result", "id": str(result.id),
                            "label": f"Rule result {result.rule_code} v{result.rule_version}"})
        failed = [r for r in results if r.status == "FAIL"]
        if failed:
            lines.append("Corrective next step: update the declared value/evidence, then ask the reviewing officer to re-run the check.")
        return ("\n".join(lines), sources, actions, False)

    if "document" in lower or "upload" in lower:
        docs = db.scalars(select(Document).where(Document.application_id == application.id)
                          .order_by(Document.created_at.desc())).all()
        if not docs:
            return (f"No documents are uploaded for {code} yet. Upload the required evidence from the case page. "
                    "The system has no configured checklist for this case, so the reviewing officer must verify requirements manually.",
                    sources, actions, True)
        lines = [f"Documents recorded for {code}:"]
        for doc in docs:
            status = "verified" if doc.verified else "not yet verified"
            lines.append(f"- {doc.filename} ({status}, uploaded {doc.created_at.isoformat()})")
            sources.append({"type": "document", "id": str(doc.id), "label": f"Document {doc.filename}"})
        lines.append("Note: this prototype has no verified official checklist configured; confirm requirements with the reviewing officer.")
        return ("\n".join(lines), sources, actions, False)

    if "urgent" in lower or "overdue" in lower or "priority" in lower:
        if user.role == UserRole.INSTITUTION.value:
            return (f"For {code}: current stage is {application.current_stage}. "
                    f"Open queries and deadlines are listed on the case page; responding to open queries is the usual next action.",
                    sources, actions, False)
        stmt = select(Application)
        if user.role == UserRole.OFFICER.value:
            stmt = stmt.where(Application.assigned_officer_id == user.id)
        apps = db.scalars(stmt).all()
        terminal = {"APPROVED", "REJECTED"}
        urgent = [a for a in apps if a.due_at is not None and a.current_stage not in terminal]
        lines = [f"You have {len(apps)} case(s) in scope; {len(urgent)} have deadlines:"]
        for item in urgent[:5]:
            lines.append(f"- {item.application_code}: stage {item.current_stage}, deadline {item.due_at.isoformat()}")
            sources.append({"type": "application", "id": str(item.id), "label": f"Case {item.application_code}"})
        return ("\n".join(lines) if urgent else "No urgent deadlines in your assigned cases right now.",
                sources, actions, False)

    if "next" in lower or "do now" in lower or "what should" in lower:
        allowed = sorted(ALLOWED_TRANSITIONS.get(application.current_stage, set()))
        queries = db.scalars(select(Query).where(Query.application_id == application.id, Query.status == "OPEN")).all()
        lines = [f"{code} is at stage {application.current_stage}."]
        if queries:
            lines.append(f"There {len(queries)} open query(s) - responding to them is required before review can continue.")
            for query in queries[:3]:
                lines.append(f"- Query #{query.id}: {query.message[:120]}")
                sources.append({"type": "query", "id": str(query.id), "label": f"Query #{query.id}"})
        if user.role in (UserRole.OFFICER.value, UserRole.ADMIN.value) and allowed:
            lines.append(f"Permitted stage actions: {', '.join(allowed)}.")
        elif application.due_at is not None:
            lines.append(f"Deadline: {application.due_at.isoformat()}.")
        return ("\n".join(lines), sources, actions, not queries and not allowed)

    # default: grounded status summary
    results = latest_results(db, application.id)
    failed = [r.rule_code for r in results if r.status == "FAIL"]
    queries = db.scalars(select(Query).where(Query.application_id == application.id, Query.status == "OPEN")).all()
    summary = (f"{code} is currently at stage {application.current_stage}"
               + (f" with a deadline of {application.due_at.isoformat()}." if application.due_at else "."))
    if failed:
        summary += f" Failing sample rule(s): {', '.join(failed)}."
    if queries:
        summary += f" Open query(s): {len(queries)}."
    if application.current_stage == "CORRECTION_REQUIRED":
        summary += " The case is waiting for the institution to submit a correction/response."
    return (summary, sources, actions, False)


def maybe_ai_polish(question: str, grounded_answer: str, context_lines: list[str]) -> str | None:
    """Optional provider call. Any failure -> None -> deterministic answer is used."""
    settings = get_settings()
    if not settings.ai_api_key:
        return None
    try:
        prompt = ("You are a concise assistant inside an approval-workflow prototype. Rewrite the answer below "
                  "in at most 3 short sentences. Use ONLY the facts given. Never invent statuses, rules or numbers. "
                  "If facts are missing, say the system cannot verify them.\n\nFACTS:\n"
                  + "\n".join(context_lines) + "\n\nDRAFT ANSWER:\n" + grounded_answer)
        response = httpx.post(
            f"{settings.ai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.ai_api_key.get_secret_value()}"},
            json={"model": settings.ai_model,
                  "messages": [{"role": "user", "content": prompt}], "max_tokens": 220, "temperature": 0.2},
            timeout=20.0)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content or None
    except Exception:
        return None
