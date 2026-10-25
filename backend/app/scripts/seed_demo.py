"""Seed synthetic local accounts. Do not use the demo password in shared or production deployments."""
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.institution import Institution
from app.models.user import User
from app.core.security import hash_password

DEMO_PASSWORD = "Demo-Only-ChangeMe-2026!"


def main() -> None:
    with SessionLocal() as db:
        institution = db.scalar(select(Institution).where(Institution.institution_code == "DEMO-INST-001"))
        if institution is None:
            institution = Institution(institution_code="DEMO-INST-001", name="Demo Engineering Institute", state="Demo State")
            db.add(institution)
            db.flush()

        accounts = [
            ("institution.demo@example.com", "Demo Institution User", "INSTITUTION", institution.id),
            ("officer.demo@example.com", "Demo Review Officer", "OFFICER", None),
            ("admin.demo@example.com", "Demo System Admin", "ADMIN", None),
        ]
        for email, name, role, institution_id in accounts:
            existing = db.scalar(select(User).where(User.email == email))
            if existing is None:
                db.add(User(email=email, full_name=name, role=role, institution_id=institution_id,
                            password_hash=hash_password(DEMO_PASSWORD), is_active=True))
        db.commit()
    print("Synthetic demo accounts are ready.")
    print("Local-only password for all three: Demo-Only-ChangeMe-2026!")
    print("Do not use these credentials in a deployed environment.")


if __name__ == "__main__":
    main()
