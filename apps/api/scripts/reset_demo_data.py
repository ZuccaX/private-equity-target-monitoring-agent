import sys
from pathlib import Path

from sqlalchemy import text

API_ROOT = Path(__file__).resolve().parents[1]

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import models
from app.core.database import Base, SessionLocal, engine


def reset_demo_data() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    audit_logs,
                    approvals,
                    email_drafts,
                    priority_scores,
                    agent_runs,
                    triggers,
                    news_articles,
                    crm_interactions,
                    contacts,
                    document_chunks,
                    documents,
                    companies
                RESTART IDENTITY CASCADE
                """
            )
        )

        db.commit()

        print("Demo data reset successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    reset_demo_data()