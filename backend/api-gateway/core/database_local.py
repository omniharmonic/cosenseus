from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from pathlib import Path
import uuid
from datetime import datetime, timezone
from sqlalchemy import text

# Import the single, shared Base and all models that need to be created
from shared.models.database import (
    Base, TemporaryUser, Event, Inquiry, Response, 
    EventParticipant, EventRound, Synthesis, UserProfileEmbedding
)

# Local development database path
LOCAL_DB_PATH = Path(__file__).parent.parent.parent.parent / "local_data" / "census_local.db"
LOCAL_DB_PATH.parent.mkdir(exist_ok=True)

# SQLite database URL for local development
LOCAL_DATABASE_URL = f"sqlite:///{LOCAL_DB_PATH}"

# Create SQLAlchemy engine for local development
local_engine = create_engine(
    LOCAL_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False  # Set to True for SQL query logging
)

# Create SessionLocal class for local development
LocalSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)

def get_local_db() -> Generator[Session, None, None]:
    """
    Dependency to get local database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = LocalSessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_local_db() -> None:
    """
    Initialize local database tables and seed with initial data.
    This should be called when the local application starts.
    """
    print("Initializing local database...")
    # Only create and seed the DB if it doesn't exist
    if not LOCAL_DB_PATH.exists():
        print("Database file not found. Creating and seeding a new one.")
        print("Creating all tables from Base metadata...")
        # Now that all models are imported, Base.metadata knows about them.
        Base.metadata.create_all(bind=local_engine)
        print("✅ All tables created.")
        
        # Create a new session for seeding data
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
    else:
        print("✅ Database already exists. Skipping creation and seeding.")


def get_inquiry_by_id(db: Session, inquiry_id: str):
    """
    Fetch an inquiry by its ID from the local database.
    """
    return db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()

def create_initial_local_data(db: Session):
    """
    Create initial data for local development using ORM.
    """
    # Create a default admin user
    admin_user = TemporaryUser(
        display_name="local_admin",
        session_code=str(uuid.uuid4())
    )
    db.add(admin_user)
    db.flush() # Flush to get the admin_user.id
    
    # Create a sample event
    sample_event = Event(
        title="Local Community Planning Discussion",
        description="A sample local event for testing the platform",
        status="active",
        is_public=True,
        organizer_id=admin_user.id
    )
    db.add(sample_event)
    db.flush() # Flush to get sample_event.id

    # Create sample inquiries
    inquiries = [
        {"question": "What are the most important priorities for our community?", "order_index": 1},
        {"question": "How can we improve transportation in our area?", "order_index": 2},
        {"question": "What environmental concerns concern you most?", "order_index": 3}
    ]
    
    for inquiry_data in inquiries:
        inquiry = Inquiry(
            event_id=sample_event.id,
            question_text=inquiry_data["question"],
            order_index=inquiry_data["order_index"]
        )
        db.add(inquiry)

def reset_local_db():
    """
    Drop all tables and recreate them.
    """
    try:
        # Drop all tables using the single, shared Base
        Base.metadata.drop_all(bind=local_engine)
        print("Local database tables dropped.")
        
        # Recreate tables and initial data
        init_local_db()
        print("Local database initialized with fresh data.")
        
    except Exception as e:
        print(f"Error resetting local database: {e}")

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