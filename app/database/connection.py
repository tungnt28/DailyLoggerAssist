"""
Database Connection - Daily Logger Assist

Database connection setup and session management using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Create database engine
if "sqlite" in settings.DATABASE_URL:
    # SQLite configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Dependency to get database session.
    
    This function is used as a FastAPI dependency to provide
    database sessions to route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables"""
    from app.models import Base
    Base.metadata.drop_all(bind=engine)

def init_db():
    """Initialize the database by creating all tables"""
    create_tables() 