"""Database engine, session factory and the FastAPI dependency."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")

# check_same_thread=False is required for SQLite when FastAPI uses a threadpool.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Dependency injection: yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
