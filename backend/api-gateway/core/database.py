from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://census_user:census_password@localhost:5432/census_db"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=20,        # Number of connections to maintain
    max_overflow=0,      # Additional connections beyond pool_size
    echo=False           # Set to True for SQL query logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize database tables.
    This should be called when the application starts.
    """
    # Import all models to ensure they are registered with SQLAlchemy
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from backend.shared.models.database import User, Event, EventParticipant, Inquiry, Response
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

def get_db_session() -> Session:
    """
    Get a database session for manual use.
    Remember to close the session when done.
    
    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal() 