import sys
import os

# Ensure backend root is on Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.alert import Base
from app.services.alert_service import scan_and_create_alerts

def run_job():
    print("--- Running AICTE ApprovalOS Deadline Scanner ---")
    engine = create_engine("sqlite:///./alerts.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        results = scan_and_create_alerts(db)
        print(f"Scan Completed Successfully!")
        print(f" -> Created: {results['created_count']}")
        print(f" -> Updated: {results['updated_count']}")
        print(f" -> Skipped: {results['skipped_count']}")
    finally:
        db.close()

if __name__ == "__main__":
    run_job()