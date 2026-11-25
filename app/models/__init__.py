from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, Text,
    Index, ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    leads = relationship("Lead", back_populates="owner", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="user", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    agent_configs = relationship("AgentConfig", back_populates="owner", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="owner", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_profiles_email", "email", unique=True),
    )


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    status = Column(String, default="new", nullable=False)
    interest_level = Column(String, default="low", nullable=False)
    requirements = Column(Text, nullable=True)
    sentiment = Column(String, default="neutral", nullable=False)
    call_outcome = Column(String, nullable=True)
    next_action = Column(String, nullable=True)
    source = Column(String, nullable=True)  # manual, elevenlabs_exotel, etc.
    notes = Column(Text, nullable=True)
    preferred_language = Column(String, default="auto", nullable=False)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    owner = relationship("Profile", back_populates="leads")
    calls = relationship("Call", back_populates="lead", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="lead", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="lead", cascade="all, delete-orphan")
    memory = relationship(
        "LeadMemory", back_populates="lead", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        Index("ix_leads_owner_id", "owner_id"),
        Index("ix_leads_status", "status"),
        Index("ix_leads_email", "email"),
    )


class Call(Base):
    __tablename__ = "calls"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    lead_id = Column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False
    )
    provider = Column(String, default="elevenlabs_exotel", nullable=False)
    conversation_id = Column(String(128), unique=True, nullable=True)
    exotel_call_sid = Column(String(128), unique=True, nullable=True)
    direction = Column(String, default="outbound", nullable=False)
    status = Column(String, default="initiated", nullable=False)
    initiation_status = Column(String, default="submitted", nullable=False)
    call_outcome = Column(String, nullable=True)
    qualification_json = Column(Text, nullable=True)
    followup_required = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    phone_number = Column(String, nullable=True)
    live_transcript = Column(Text, nullable=True)
    language = Column(String, nullable=True)
    channel = Column(String, default="outbound", nullable=False)
    transcript_id = Column(String(36), nullable=True)
    summary_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    lead = relationship("Lead", back_populates="calls")
    summary = relationship(
        "CallSummary", back_populates="call", uselist=False, foreign_keys="CallSummary.call_id"
    )

    __table_args__ = (
        Index("ix_calls_lead_id", "lead_id"),
        Index("ix_calls_status", "status"),
        Index("ix_calls_conversation_id", "conversation_id"),
        Index("ix_calls_exotel_call_sid", "exotel_call_sid"),
    )


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    call_id = Column(
        String(36),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_transcripts_call_id", "call_id"),
    )


class CallSummary(Base):
    __tablename__ = "call_summaries"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    call_id = Column(
        String(36),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False
    )
    summary = Column(Text, nullable=False)
    sentiment = Column(String, default="neutral", nullable=False)
    call_outcome = Column(String, nullable=True)
    requirements = Column(Text, nullable=True)
    interest = Column(String, default="low", nullable=False)
    next_action = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    call = relationship("Call", back_populates="summary", foreign_keys=[call_id])

    __table_args__ = (
        Index("ix_call_summaries_call_id", "call_id"),
    )


class Followup(Base):
    __tablename__ = "followups"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    lead_id = Column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = Column(
        String(36),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    lead = relationship("Lead", back_populates="followups")
    user = relationship("Profile", back_populates="followups")

    __table_args__ = (
        Index("ix_followups_lead_id", "lead_id"),
        Index("ix_followups_status", "status"),
        Index("ix_followups_scheduled_at", "scheduled_at"),
    )


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    name = Column(String, nullable=False)
    instructions = Column(Text, nullable=False)
    first_message = Column(Text, nullable=True)
    language = Column(String, default="auto", nullable=False)
    voice_id = Column(String, nullable=True)
    model = Column(String, default="gpt-4o-mini", nullable=False)
    temperature = Column(Float, default=0.3, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    is_active = Column(Boolean, default=True)
    owner_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("Profile", back_populates="agent_configs")

    __table_args__ = (
        Index("ix_agent_configs_owner_id", "owner_id"),
        Index("ix_agent_configs_is_active", "is_active"),
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    file_url = Column(String, nullable=True)
    chunked = Column(Boolean, default=False, nullable=False)
    status = Column(String, default="pending", nullable=False)
    mime_type = Column(String, nullable=True)
    char_count = Column(Integer, default=0, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Profile", back_populates="knowledge_documents")
    chunks = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_knowledge_documents_owner_id", "owner_id"),
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    document_id = Column(
        String(36),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, default=0, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON-encoded float array
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_knowledge_chunks_document_id", "document_id"),
        Index("ix_knowledge_chunks_owner_id", "owner_id"),
    )


class LeadMemory(Base):
    __tablename__ = "lead_memories"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    lead_id = Column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary = Column(Text, nullable=True)
    key_facts = Column(Text, nullable=True)  # JSON-encoded list/dict
    language = Column(String, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="memory")

    __table_args__ = (
        Index("ix_lead_memories_lead_id", "lead_id", unique=True),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, index=True, default=func.gen_random_uuid())
    lead_id = Column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        String(36),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    status = Column(String, default="scheduled", nullable=False)
    title = Column(String, default="Product demo", nullable=False)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    call_id = Column(String(36), ForeignKey("calls.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    lead = relationship("Lead", back_populates="appointments")
    user = relationship("Profile", back_populates="appointments")

    __table_args__ = (
        Index("ix_appointments_lead_id", "lead_id"),
        Index("ix_appointments_user_id", "user_id"),
        Index("ix_appointments_scheduled_at", "scheduled_at"),
        Index("ix_appointments_status", "status"),
    )