from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(..., description="Lead full name")
    email: str = Field(..., description="Lead email address")
    phone: Optional[str] = Field(None, description="Lead phone number")
    company: Optional[str] = Field(None, description="Company name")
    source: Optional[str] = Field(None, description="Lead source (vapi, manual, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes")


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Lead full name")
    email: Optional[str] = Field(None, description="Lead email address")
    phone: Optional[Optional[str]] = Field(None, description="Lead phone number")
    company: Optional[str] = Field(None, description="Company name")
    status: Optional[str] = Field(None, description="Lead status")
    interest_level: Optional[str] = Field(None, description="Interest level")
    requirements: Optional[str] = Field(None, description="Lead requirements")
    sentiment: Optional[str] = Field(None, description="Sentiment")
    call_outcome: Optional[str] = Field(None, description="Call outcome")
    next_action: Optional[str] = Field(None, description="Next action")
    notes: Optional[str] = Field(None, description="Additional notes")


class LeadInDB(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str
    interest_level: str
    requirements: Optional[str] = None
    sentiment: str
    call_outcome: Optional[str] = None
    next_action: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str
    interest_level: str
    requirements: Optional[str] = None
    sentiment: str
    call_outcome: Optional[str] = None
    next_action: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True