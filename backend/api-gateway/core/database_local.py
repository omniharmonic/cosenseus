from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from pathlib import Path
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.pool import StaticPool

# Import the single, shared Base and all models that need to be created
from shared.models.database import (
    Base, TemporaryUser, Event, Inquiry, Response, 
    EventParticipant, EventRound, Synthesis, UserProfileEmbedding
)

# Define the path to the local database file
# Use local system directory to avoid iCloud Drive sync conflicts
LOCAL_DB_PATH = Path.home() / ".cosenseus" / "cosenseus_local.db"
LOCAL_DB_URL = f"sqlite:///{LOCAL_DB_PATH}"

# Ensure the local_data directory exists
LOCAL_DB_PATH.parent.mkdir(exist_ok=True)

# Create SQLAlchemy engine for local development
local_engine = create_engine(
    LOCAL_DB_URL,
    connect_args={
        "check_same_thread": False,  # Required for SQLite
        "timeout": 60,  # 60 second timeout for better network reliability
    },
    echo=False,  # Set to True for SQL query logging
    poolclass=StaticPool,  # Use StaticPool for SQLite single connection
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=-1,  # Disable connection recycling for SQLite
)

# Create SessionLocal class for local development
LocalSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)

def get_local_db() -> Generator[Session, None, None]:
    """
    Dependency to get local database session with improved error handling.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = LocalSessionLocal()
    try:
        # Test the connection before yielding
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        print(f"Database connection error: {e}")
        db.rollback()
        raise
    finally:
        try:
            db.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")

def init_local_db() -> None:
    """
    Initialize local database tables and seed with initial data.
    For local development, we will reset the database on every startup
    to ensure the schema is always in sync with the models.
    """
    print("Initializing local database (with reset)...")
    reset_local_db()


def get_inquiry_by_id(db: Session, inquiry_id: str):
    """
    Fetch an inquiry by its ID from the local database.
    """
    return db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()

def create_initial_local_data(db: Session):
    """
    Create initial data for local development using ORM.
    This is kept empty to allow the "first user is admin" logic to work correctly.
    Sample data can be created through the UI.
    """
    # This function is intentionally left empty.
    # The first user to sign up via the UI will be an admin.
    pass


def reset_local_db():
    """
    Utility function to manually drop all tables and recreate them.
    This is NOT called on startup anymore.
    """
    print("Resetting local database...")
    try:
        # Drop all tables using the single, shared Base
        Base.metadata.drop_all(bind=local_engine)
        print("✅ Local database tables dropped.")
        
        # Recreate tables and initial data
        init_local_db_internal()
        print("✅ Local database initialized with fresh data.")
        
    except Exception as e:
        print(f"❌ Error resetting local database: {e}")

def init_local_db_internal():
    """The actual implementation of creating and seeding the database."""
    print("Creating all tables from Base metadata...")
    Base.metadata.create_all(bind=local_engine)
    print("✅ All tables created.")

    db = LocalSessionLocal()
    try:
        print("Seeding initial data...")
        create_initial_local_data(db)
        db.commit()
        print("✅ Initial data seeded and committed.")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()
        print("Database session closed.")

def create_temporary_user(db: Session) -> TemporaryUser:
    """
    Create a new temporary user for local development.
    """
    new_user = TemporaryUser(display_name="Local Dev User")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_id(db: Session, user_id: str) -> TemporaryUser:
    """
    Fetch a user by their ID from the local database.
    """
    return db.query(TemporaryUser).filter(TemporaryUser.id == user_id).first() 