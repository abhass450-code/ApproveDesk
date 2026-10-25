import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Keep the API's module-level engine pointed at Postgres for real runs; tests override the dependency.
os.environ.setdefault("JWT_SECRET", "pytest-only-secret-never-used-in-production-123456789")
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import hash_password
from app.models import Institution, User


@pytest.fixture()
def test_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    demo_inst = Institution(institution_code="TEST-INST-1", name="Test Institution", state="Test State")
    other_inst = Institution(institution_code="TEST-INST-2", name="Other Institution", state="Test State")
    db.add_all([demo_inst, other_inst])
    db.flush()
    users = [
        User(email="institution1@example.com", full_name="Institution One", role="INSTITUTION", institution_id=demo_inst.id, password_hash=hash_password("TestPassword123!")),
        User(email="institution2@example.com", full_name="Institution Two", role="INSTITUTION", institution_id=other_inst.id, password_hash=hash_password("TestPassword123!")),
        User(email="officer@example.com", full_name="Assigned Officer", role="OFFICER", password_hash=hash_password("TestPassword123!")),
        User(email="admin@example.com", full_name="Test Admin", role="ADMIN", password_hash=hash_password("TestPassword123!")),
    ]
    db.add_all(users)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
