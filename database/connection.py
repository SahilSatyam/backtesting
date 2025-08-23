"""
Database connection management using SQLAlchemy.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from config.database import DATABASE_URL, ENGINE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine."""
        try:
            self.engine = create_engine(
                DATABASE_URL,
                **ENGINE_CONFIG
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info("Database engine initialized successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.info("Database connection test successful")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            # Try alternative method for older SQLAlchemy versions
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                logger.info("Database connection test successful (alternative method)")
                return True
            except Exception as e2:
                logger.error(f"Alternative connection test also failed: {e2}")
                return False
    
    def close(self):
        """Close database engine."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Get database session for dependency injection."""
    return db_manager.get_session()
