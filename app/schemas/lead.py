from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    interest_level: Optional[str] = None
    requirements: Optional[str] = None
    sentiment: Optional[str] = None
    call_outcome: Optional[str] = None
    next_action: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


LeadInDB = LeadResponse
