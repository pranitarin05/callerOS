from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QualificationOutput(BaseModel):
    lead_status: str = Field(..., description="Lead status")
    interest: str = Field(..., description="Interest level")
    requirements: str = Field(..., description="Extracted requirements")
    sentiment: str = Field(..., description="Conversation sentiment")
    call_outcome: str = Field(..., description="Call outcome")
    next_action: str = Field(..., description="Recommended next action")


class ConversationTurn(BaseModel):
    speaker: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationSummary(BaseModel):
    lead_id: str
    transcript: str
    qualification: QualificationOutput
    summary: str
    duration_seconds: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FollowupCreate(BaseModel):
    lead_id: str
    scheduled_at: str
    notes: Optional[str] = None


class FollowupResponse(BaseModel):
    id: str
    lead_id: str
    user_id: str
    scheduled_at: datetime
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CallCreate(BaseModel):
    lead_id: str
    phone_number: Optional[str] = None
    mode: str = "demo"


class CallResponse(BaseModel):
    id: str
    lead_id: str
    provider: str = "elevenlabs_exotel"
    conversation_id: Optional[str] = None
    exotel_call_sid: Optional[str] = None
    direction: str
    status: str
    initiation_status: str = "submitted"
    call_outcome: Optional[str] = None
    followup_required: bool = False
    error_message: Optional[str] = None
    phone_number: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TranscriptOut(BaseModel):
    id: str
    call_id: str
    content: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CallSummaryOut(BaseModel):
    id: str
    call_id: str
    summary: str
    sentiment: str
    call_outcome: Optional[str] = None
    requirements: Optional[str] = None
    interest: str
    next_action: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CallInsightsResponse(BaseModel):
    call: CallResponse
    live_transcript: Optional[str] = None
    transcript: Optional[TranscriptOut] = None
    summary: Optional[CallSummaryOut] = None
    qualification: Optional[QualificationOutput] = None
