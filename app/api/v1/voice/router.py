"""Browser WebRTC voice sessions backed by ElevenLabs Conversational AI."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.db.session import get_db
from app.models import Call, Lead
from app.services import agent_config_service
from app.services.calling_service import process_conversation_data
from app.services.lead_service import LeadService
from app.services.memory_service import get_memory_context

router = APIRouter(tags=["voice"])
logger = logging.getLogger(__name__)

TOKEN_PATH = "/v1/convai/conversation/token"


class TranscriptPayload(BaseModel):
    call_id: str
    text: str
    role: str = "agent"


class CompletePayload(BaseModel):
    call_id: str
    transcript: str = ""
    summary: str = ""


async def _conversation_token(agent_id: str) -> Optional[str]:
    if not settings.elevenlabs_api_key or not agent_id:
        return None
    url = f"{settings.elevenlabs_api_base_url}{TOKEN_PATH}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                params={"agent_id": agent_id},
                headers={"xi-api-key": settings.elevenlabs_api_key},
            )
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        logger.warning("Conversation token request failed (%s)", response.status_code)
        return None
    try:
        data = response.json()
        return data.get("token") or data.get("conversation_token")
    except ValueError:
        return None


def _owned_call(call_id: str, user_id: str, db: Session) -> Call:
    call = (
        db.query(Call)
        .join(Lead)
        .filter(Call.id == call_id, Lead.owner_id == user_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.get("/config")
async def voice_config(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    token = await _conversation_token(settings.web_agent_id) if settings.voice_ready else None
    return {
        "voice_ready": settings.voice_ready,
        "agent_id": settings.web_agent_id if settings.voice_ready else "",
        "conversation_token": token,
        "provider": "elevenlabs_webrtc",
        "default_language": settings.default_language,
        "max_minutes": settings.voice_session_max_minutes,
    }


@router.post("/session", status_code=201)
async def create_session(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead_id = str(payload.get("lead_id") or "")
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    if (lead.status or "").lower() in {"do_not_call", "opted_out", "dnc"}:
        raise HTTPException(status_code=409, detail="Lead has opted out / do-not-call")

    call = Call(
        id=str(uuid4()),
        lead_id=lead.id,
        provider="elevenlabs_webrtc",
        direction="outbound",
        status="initiated",
        initiation_status="submitted",
        channel="web",
        language=lead.preferred_language or settings.default_language,
        phone_number=lead.phone,
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    token = await _conversation_token(settings.web_agent_id)
    if not token:
        raise HTTPException(
            status_code=503,
            detail="Browser voice is not configured (ELEVENLABS_API_KEY / agent missing)",
        )

    return {
        "call_id": call.id,
        "conversation_token": token,
        "agent_id": settings.web_agent_id,
        "language": call.language,
        "dynamic_variables": {
            "call_id": call.id,
            "lead_id": lead.id,
            "crm_user_id": user_id,
            "prospect_name": lead.name,
            "language": call.language,
            "lead_memory": get_memory_context(db, lead.id),
        },
        "overrides": agent_config_service.get_override(db, user_id),
    }


@router.post("/transcript")
async def append_transcript(
    payload: TranscriptPayload,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    call = _owned_call(payload.call_id, user_id, db)
    line = f"{payload.role}: {payload.text.strip()}"
    existing = call.live_transcript or ""
    call.live_transcript = f"{existing}\n{line}" if existing else line
    db.commit()
    return {"status": "ok", "call_id": call.id}


@router.post("/complete")
async def complete_session(
    payload: CompletePayload,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    call = _owned_call(payload.call_id, user_id, db)
    transcript = payload.transcript.strip() or (call.live_transcript or "")
    data = {
        "conversation_id": call.conversation_id,
        "transcript": transcript,
        "analysis": {
            "call_successful": "success",
            "transcript_summary": payload.summary or "Browser voice conversation completed",
            "data_collection_results": {},
        },
        "metadata": {"source": "webrtc"},
    }
    result = await process_conversation_data(call, data, db)
    if "conversation_id" not in result:
        result["conversation_id"] = call.conversation_id
    return result
