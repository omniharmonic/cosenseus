"""
Database models for the Civic Sense-Making Platform
Core entities: Users, Events, Responses, and related tables
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, JSON, Float, Enum, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    a string representation.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        # Always store as a string
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        # Convert back to UUID object when reading
        if not isinstance(value, uuid.UUID):
            try:
                return uuid.UUID(value)
            except (ValueError, TypeError):
                return value 
        return value

class EventStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"

class UserRole(PyEnum):
    PARTICIPANT = "participant"
    ORGANIZER = "organizer"
    ADMIN = "admin"
    MODERATOR = "moderator"

class ResponseType(PyEnum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"

class ProcessingStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Legacy User model, preserved for reference.
# class User(Base):
#     """User model for platform participants and organizers"""
#     __tablename__ = "users"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     email = Column(String(255), unique=True, index=True, nullable=True)
#     username = Column(String(100), unique=True, index=True, nullable=True)
#     hashed_password = Column(String(255), nullable=True)
#     is_temporary = Column(Boolean, default=False)
    
#     # Profile information
#     first_name = Column(String(100), nullable=True)
#     last_name = Column(String(100), nullable=True)
#     display_name = Column(String(200), nullable=True)
#     bio = Column(Text, nullable=True)
    
#     # Demographics (optional, for analysis)
#     age_range = Column(String(20), nullable=True)  # "18-25", "26-35", etc.
#     location = Column(String(200), nullable=True)
#     occupation = Column(String(200), nullable=True)
    
#     # Account status
#     is_active = Column(Boolean, default=True)
#     is_verified = Column(Boolean, default=False)
#     role = Column(Enum(UserRole), default=UserRole.PARTICIPANT)
    
#     # Privacy settings
#     profile_visibility = Column(String(20), default="public")  # public, private, selective
#     data_sharing_consent = Column(Boolean, default=False)
#     analytics_consent = Column(Boolean, default=False)
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
#     last_login = Column(DateTime(timezone=True), nullable=True)
    
#     # Relationships
#     organized_events = relationship("Event", back_populates="organizer")
#     responses = relationship("Response", back_populates="user")
#     event_participations = relationship("EventParticipant", back_populates="user")
#     profile_embeddings = relationship("UserProfileEmbedding", back_populates="user")

class TemporaryUser(Base):
    """Temporary User model based on a persistent session code."""
    __tablename__ = "temporary_users"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    display_name = Column(String(200), nullable=False)
    session_code = Column(String(255), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    role = Column(String(50), nullable=False, default='user')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organized_events = relationship("Event", back_populates="organizer")
    responses = relationship("Response", back_populates="user")
    event_participations = relationship("EventParticipant", back_populates="user")
    profile_embeddings = relationship("UserProfileEmbedding", back_populates="user", cascade="all, delete-orphan")

class Event(Base):
    """Event model for civic sense-making sessions"""
    __tablename__ = "events"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    organizer_id = Column(GUID, ForeignKey("temporary_users.id"), nullable=False)
    
    # Basic event information
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    context = Column(Text, nullable=True)  # Background context for AI processing
    event_type = Column(String(50), default="discussion")
    
    # Event configuration
    status = Column(Enum(EventStatus, name="eventstatus", native_enum=False, length=50, values_callable=lambda obj: [e.value for e in obj]), default=EventStatus.DRAFT)
    is_public = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    max_participants = Column(Integer, nullable=True)
    
    # Multi-round configuration
    supports_multiple_rounds = Column(Boolean, default=True)
    current_round = Column(Integer, default=1)
    max_rounds = Column(Integer, default=5)
    
    # AI processing settings
    enable_realtime_processing = Column(Boolean, default=True)
    synthesis_threshold = Column(Integer, default=10)  # Min responses before synthesis
    consensus_threshold = Column(Float, default=0.7)  # Threshold for consensus detection
    
    # Access and sharing
    access_code = Column(String(20), unique=True, nullable=True)
    public_results = Column(Boolean, default=False)
    allow_anonymous = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organizer = relationship("TemporaryUser", back_populates="organized_events")
    inquiries = relationship("Inquiry", back_populates="event", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="event")
    participants = relationship("EventParticipant", back_populates="event")
    syntheses = relationship("Synthesis", back_populates="event")
    rounds = relationship("EventRound", back_populates="event")

class Inquiry(Base):
    """Inquiry/Question model within events"""
    __tablename__ = "inquiries"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_id = Column(GUID, ForeignKey("events.id"), nullable=False)
    
    # Inquiry content
    question_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    
    # Configuration
    order_index = Column(Integer, default=0)
    round_number = Column(Integer, default=1, nullable=False)
    is_required = Column(Boolean, default=True)
    response_type = Column(String(20), default="text")  # text, audio, video, multiple_choice
    
    # Constraints
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    time_limit_seconds = Column(Integer, nullable=True)
    
    # Multiple choice options (JSON)
    options = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="inquiries")
    responses = relationship("Response", back_populates="inquiry")

class Response(Base):
    """Response model for participant submissions"""
    __tablename__ = "responses"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_id = Column(GUID, ForeignKey("events.id"), nullable=False)
    inquiry_id = Column(GUID, ForeignKey("inquiries.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("temporary_users.id"), nullable=True)  # Nullable for anonymous
    
    # Response content
    content = Column(Text, nullable=False)
    response_type = Column(Enum(ResponseType), default=ResponseType.TEXT)
    
    # Audio/Video metadata
    file_path = Column(String(500), nullable=True)
    transcription = Column(Text, nullable=True)
    transcription_confidence = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Processing metadata
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # AI analysis results (JSON)
    embeddings = Column(JSON, nullable=True)  # Vector embeddings
    sentiment_scores = Column(JSON, nullable=True)  # Sentiment analysis
    entities = Column(JSON, nullable=True)  # Named entities
    topics = Column(JSON, nullable=True)  # Topic classifications
    
    # Participant metadata
    round_number = Column(Integer, default=1)
    is_anonymous = Column(Boolean, default=False)
    ip_address = Column(String(45), nullable=True)  # For anonymous tracking
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="responses")
    inquiry = relationship("Inquiry", back_populates="responses")
    user = relationship("TemporaryUser", back_populates="responses")

class EventParticipant(Base):
    """Junction table for event participation with metadata"""
    __tablename__ = "event_participants"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_id = Column(GUID, ForeignKey("events.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("temporary_users.id"), nullable=False)
    role = Column(String(50), default="participant", nullable=False)
    
    # Participation metadata
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    response_count = Column(Integer, default=0)
    completion_status = Column(String(20), default="in_progress")  # in_progress, completed, abandoned
    
    # Permissions
    can_view_results = Column(Boolean, default=True)
    can_receive_notifications = Column(Boolean, default=True)
    
    # Relationships
    event = relationship("Event", back_populates="participants")
    user = relationship("TemporaryUser", back_populates="event_participations")
    
    __table_args__ = (UniqueConstraint('event_id', 'user_id', name='unique_event_participant'),)

class EventRoundStatus(PyEnum):
    WAITING_FOR_RESPONSES = "waiting_for_responses"
    IN_ANALYSIS = "in_analysis"
    ADMIN_REVIEW = "admin_review"
    COMPLETED = "completed"

class EventRound(Base):
    """Model for tracking multiple rounds within an event"""
    __tablename__ = "event_rounds"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_id = Column(GUID, ForeignKey("events.id"), nullable=False)
    
    round_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Round status
    status = Column(Enum(EventRoundStatus), default=EventRoundStatus.WAITING_FOR_RESPONSES)
    response_count = Column(Integer, default=0)
    target_response_count = Column(Integer, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="rounds")
    
    __table_args__ = (UniqueConstraint('event_id', 'round_number', name='unique_event_round'),)

class Synthesis(Base):
    """AI-generated synthesis of responses for events/rounds"""
    __tablename__ = "syntheses"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_id = Column(GUID, ForeignKey("events.id"), nullable=False)
    round_number = Column(Integer, default=1)
    
    # Synthesis content
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # AI-generated prompts for the next round, pending admin approval
    next_round_prompts = Column(JSON, nullable=True)

    # Consensus analysis - fields that match frontend expectations
    key_themes = Column(JSON, nullable=True)  # Key themes from analysis
    consensus_points = Column(JSON, nullable=True)  # Areas of agreement/consensus
    dialogue_opportunities = Column(JSON, nullable=True)  # Opportunities for further dialogue
    
    # Additional analysis fields
    consensus_areas = Column(JSON, nullable=True)  # Areas of agreement
    divergent_perspectives = Column(JSON, nullable=True)  # Areas of disagreement
    nuanced_positions = Column(JSON, nullable=True)  # Complex middle positions
    
    # Quality metrics
    representativeness_score = Column(Float, nullable=True)
    participant_feedback_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Generation metadata
    algorithm_version = Column(String(50), nullable=True)
    response_count_basis = Column(Integer, nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Status
    status = Column(String(20), default="draft")  # draft, published, revised
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="syntheses")

class UserProfileEmbedding(Base):
    """Persistent user profile embeddings for cross-event continuity"""
    __tablename__ = "user_profile_embeddings"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("temporary_users.id"), nullable=False)
    
    # Embedding data
    embedding_vector = Column(JSON, nullable=False)  # Vector representation
    model_version = Column(String(50), nullable=False)
    dimension_count = Column(Integer, nullable=False)
    
    # Context metadata
    topic_areas = Column(JSON, nullable=True)  # Topics this embedding covers
    confidence_score = Column(Float, nullable=True)
    event_count_basis = Column(Integer, default=1)  # Number of events contributing
    
    # Evolution tracking
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("TemporaryUser", back_populates="profile_embeddings")


# Indexes for performance
Index('idx_responses_event_user', Response.event_id, Response.user_id)
Index('idx_responses_user_event', Response.user_id, Response.event_id)
Index('idx_event_participants_user_event', EventParticipant.user_id, EventParticipant.event_id)
Index('idx_syntheses_event_round', Synthesis.event_id, Synthesis.round_number)
Index('idx_events_status_public', Event.status, Event.is_public)
Index('idx_events_organizer_created', Event.organizer_id, Event.created_at)
Index('idx_participants_event_active', EventParticipant.event_id, EventParticipant.last_active)
Index('idx_responses_processing_status', Response.processing_status) 