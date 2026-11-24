from typing import Optional

from pydantic import BaseModel, Field


class CallInitiateRequest(BaseModel):
    phone_number: str = Field(..., min_length=5, description="Customer number in E.164 or national format")
    lead_id: Optional[str] = Field(None, description="Existing CRM lead ID")
    name: Optional[str] = Field(None, description="Prospect name when no lead is selected")
    mode: str = Field("live", description="demo or live")


class CallInitiateResponse(BaseModel):
    success: bool
    simulated: bool
    mode: str
    call_id: str
    conversation_id: Optional[str] = None
    exotel_call_sid: Optional[str] = None
    status: str
    initiation_status: str
    message: str


class CallingConfigResponse(BaseModel):
    mode: str
    live_ready: bool
    demo_ready: bool = True
    agent_id_configured: bool
    phone_number_configured: bool
    webhook_configured: bool
    webhook_secret_configured: bool
    provider: str = "elevenlabs_exotel"
    agent_name: str
    exotel_region: str
    groq_configured: bool
