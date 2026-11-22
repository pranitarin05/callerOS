from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class QualificationOutput(BaseModel):
    """Structured output from AI lead qualification."""
    lead_status: str = Field(
        ..., description "Lead status: new, qualified, interested, not_interested"
    )
    interest: str = Field(
        ..., description "Interest level: low, medium, high"
    )
    requirements: str = Field(
        ..., description "Lead requirements or pain points extracted from conversation"
    )
    sentiment: str = Field(
        ..., description "Conversation sentiment: positive, negative, neutral"
    )
    call_outcome: str = Field(
        ..., description "Call outcome: interested, not_interested, callback, appointment_booked"
    )
    next_action: str = Field(
        ..., description "Recommended next action"
    )


class ConversationTurn(BaseModel):
    """Represents a single turn in the conversation."""
    speaker: str = Field(..., description "Speaker: user or agent")
    text: str = Field(..., description "The conversation text")
    timestamp: datetime = Field(
        default_factory=datetime.now, description "Turn timestamp"
    )


class ConversationSummary(BaseModel):
    """Summary of a completed conversation."""
    lead_id: str = Field(..., description "Associated lead ID")
    transcript: str = Field(..., description "Full conversation transcript")
    qualification: QualificationOutput = Field(
        ..., description "Structured qualification data"
    )
    summary: str = Field(
        ..., description "Brief conversation summary"
    )
    duration_seconds: Optional[int] = Field(
        default=None, description "Call duration in seconds"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description "Summary creation time"
    )