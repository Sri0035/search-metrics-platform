import os

from sqlalchemy.orm import Session

from api.models import get_session_factory

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://searchmetrics:searchmetrics@localhost:5432/search_metrics",
)

SessionLocal = get_session_factory(DATABASE_URL)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
