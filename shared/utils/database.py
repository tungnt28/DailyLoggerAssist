"""
Shared Database Utilities for Daily Logger Assist Microservices

Provides database connection management and session handling.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Import Base from models to ensure all models are registered
from shared.models.base import Base

class DatabaseManager:
    """Manages database connections and sessions for microservices"""
    
    def __init__(self, database_url: str, service_name: str):
        self.database_url = database_url
        self.service_name = service_name
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database engine and session factory"""
        try:
            if "sqlite" in self.database_url:
                # SQLite configuration for development
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                # PostgreSQL configuration for production
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    pool_size=20,
                    max_overflow=30,
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database initialized for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database for {self.service_name}: {e}")
            raise
    
    def create_tables(self):
        """Create all tables for this service"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Tables created for {self.service_name}")
        except Exception as e:
            logger.error(f"Failed to create tables for {self.service_name}: {e}")
            raise
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error in {self.service_name}: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """Get database session with context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Database transaction error in {self.service_name}: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_session_context() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed for {self.service_name}: {e}")
            return False

# Global database instance (will be initialized by each service)
db_manager: DatabaseManager = None

def init_database(database_url: str, service_name: str) -> DatabaseManager:
    """Initialize database for a microservice"""
    global db_manager
    db_manager = DatabaseManager(database_url, service_name)
    return db_manager

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session"""
    if not db_manager:
        raise RuntimeError("Database not initialized. Call init_database first.")
    
    yield from db_manager.get_session() 