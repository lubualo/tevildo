"""
Database connection and session management.

Sets up SQLAlchemy engine for SQLite with proper configuration.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.settings import settings


# Create SQLAlchemy engine
# connect_args required for SQLite threading
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=settings.debug,  # Log SQL queries when debug=True
)


# Enable foreign key constraints for SQLite
# SQLite has foreign keys disabled by default - we must enable them!
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints on SQLite connections."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory for database transactions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for all ORM models
Base = declarative_base()


# Dependency for FastAPI routes to get database sessions
def get_db():
    """
    FastAPI dependency that provides a database session.

    Yields a session and ensures it's closed after the request.

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
