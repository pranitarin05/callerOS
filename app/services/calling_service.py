"""ElevenLabs Conversational AI + Exotel calling service.

The official ElevenLabs Exotel endpoint is the only outbound calling path.
Exotel credentials stay inside ElevenLabs' imported phone number record.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.ai import generate_qualification
from app.core.config import settings
from app.models import Call, CallSummary, Lead
from app.services.lead_service import LeadService
from app.tools import ConversationSimulator, update_lead
from app.tools.transcripts import (
    extract_sentiment_and_outcome,
    process_call_completion,
    store_call_summary,
    store_transcript,
)

logger = logging.getLogger(__name__)

OUTBOUND_URL = f"{settings.elevenlabs_api_base_url}/v1/convai/exotel/outbound-call"
DUPLICATE_WINDOW_SECONDS = 60


def normalize_phone_number(value: str) -> str:
    raw = (value or "").strip()
    raw = raw.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if raw.startswith("00"):
        raw = "+" + raw[2:]

    if raw.startswith("+"):
        candidate = raw
    else:
        digits = raw
        if digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]
        if len(digits) == 10 and digits[0] in "6789":
            candidate = "+91" + digits
        elif len(digits) == 12 and digits.startswith("91"):
            candidate = "+" + digits
        elif 8 <= len(digits) <= 15:
            candidate = "+" + digits
        else:
            candidate = raw

    if not re.fullmatch(r"\+[1-9]\d{7,14}", candidate):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in international E.164 format, e.g. +919876543210",
        )
    return candidate


def validate_live_configuration() -> None:
    missing = []
    if not settings.elevenlabs_api_key:
        missing.append("ELEVENLABS_API_KEY")
    if not settings.elevenlabs_agent_id:
        missing.append("ELEVENLABS_AGENT_ID")
    if not settings.elevenlabs_phone_number_id:
        missing.append("ELEVENLABS_PHONE_NUMBER_ID")
    if missing:
        raise HTTPException(
            status_code=503,
            detail="Missing live calling configuration: " + ", ".join(missing),
        )


def calling_config() -> Dict[str, Any]:
    return {
        "mode": settings.call_mode,
        "live_ready": settings.live_call_ready,
        "demo_ready": True,
        "agent_id_configured": bool(settings.elevenlabs_agent_id),
        "phone_number_configured": bool(settings.elevenlabs_phone_number_id),
        "webhook_configured": bool(settings.elevenlabs_webhook_url),
        "webhook_secret_configured": bool(settings.elevenlabs_webhook_secret),
        "provider": "elevenlabs_exotel",
        "agent_name": settings.elevenlabs_agent_name,
        "exotel_region": settings.exotel_region,
        "groq_configured": bool(settings.groq_api_keys),
    }


def _find_recent_duplicate(db: Session, lead_id: Optional[str], phone: str) -> Optional[Call]:
    cutoff = datetime.utcnow() - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
    query = db.query(Call).filter(Call.created_at >= cutoff)
    if lead_id:
        query = query.filter(Call.lead_id == lead_id)
    else:
        query = query.filter(Call.phone_number == phone)
    return query.order_by(Call.created_at.desc()).first()


def _demo_call(call: Call, lead: Lead, db: Session) -> Dict[str, Any]:
    conversation = ConversationSimulator.run_demo_conversation(lead_name=lead.name)
    process_call_completion(call.id, conversation["transcript"], db)
    call.status = "completed"
    call.initiation_status = "completed"
    call.call_outcome = "interested"
    call.ended_at = datetime.utcnow()
    call.duration_seconds = conversation.get("duration_seconds")
    db.commit()
    db.refresh(call)
    return {
        "success": True,
        "simulated": True,
        "mode": "demo",
        "call_id": call.id,
        "conversation_id": None,
        "exotel_call_sid": None,
        "status": call.status,
        "initiation_status": call.initiation_status,
        "message": "Demo conversation completed. No real phone call was placed.",
    }


async def initiate_call(
    db: Session,
    user_id: str,
    phone_number: str,
    lead_id: Optional[str] = None,
    name: Optional[str] = None,
    mode: str = "live",
) -> Dict[str, Any]:
    mode = mode if mode in {"demo", "live"} else settings.call_mode
    if mode not in {"demo", "live"}:
        mode = "demo"

    phone = normalize_phone_number(phone_number)

    lead = None
    if lead_id:
        lead = LeadService.get_lead_details(lead_id, db)
        if not lead or str(lead.owner_id) != str(user_id):
            raise HTTPException(status_code=404, detail="Lead not found")
        phone = normalize_phone_number(phone or lead.phone or "")
        if (lead.status or "").lower() in {"do_not_call", "opted_out", "dnc"}:
            raise HTTPException(status_code=409, detail="Lead has opted out / do-not-call")
    else:
        lead = LeadService.create_lead(
            db=db,
            owner_id=user_id,
            name=(name or "Phone Lead").strip(),
            email=f"phone-{phone.lstrip('+')}@calleros.local",
            phone=phone,
            source=mode,
        )

    duplicate = _find_recent_duplicate(db, lead.id, phone)
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"A call was already initiated for this lead recently (call {duplicate.id}).",
        )

    call = Call(
        id=str(uuid4()),
        lead_id=lead.id,
        provider="elevenlabs_exotel",
        direction="outbound",
        status="submitting",
        initiation_status="submitting",
        phone_number=phone,
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    if mode == "demo":
        return _demo_call(call, lead, db)

    validate_live_configuration()

    payload = {
        "agent_id": settings.elevenlabs_agent_id,
        "agent_phone_number_id": settings.elevenlabs_phone_number_id,
        "to_number": phone,
        "conversation_initiation_client_data": {
            "user_id": user_id,
            "source_info": {"source": "exotel"},
            "dynamic_variables": {
                "call_id": call.id,
                "lead_id": lead.id,
                "crm_user_id": user_id,
                "prospect_name": lead.name,
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                OUTBOUND_URL,
                headers={
                    "xi-api-key": settings.elevenlabs_api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        call.status = "failed"
        call.initiation_status = "failed"
        call.error_message = f"Provider request failed: {type(exc).__name__}"
        db.commit()
        raise HTTPException(status_code=502, detail="ElevenLabs request failed") from None

    if response.status_code >= 400:
        call.status = "failed"
        call.initiation_status = "failed"
        call.error_message = f"Provider rejected request ({response.status_code})"
        db.commit()
        detail = response.text[:300] if response.text else "no error body"
        raise HTTPException(
            status_code=502,
            detail=f"ElevenLabs rejected request ({response.status_code}): {detail}",
        )

    try:
        data = response.json()
    except ValueError:
        data = {}

    if not data.get("success"):
        call.status = "failed"
        call.initiation_status = "failed"
        call.error_message = str(data.get("message") or "Provider did not accept the call")
        db.commit()
        raise HTTPException(status_code=502, detail="ElevenLabs did not initiate the call")

    call.conversation_id = data.get("conversation_id")
    call.exotel_call_sid = data.get("callSid")
    call.status = "initiated"
    call.initiation_status = "submitted"
    db.commit()
    db.refresh(call)

    return {
        "success": True,
        "simulated": False,
        "mode": "live",
        "call_id": call.id,
        "conversation_id": call.conversation_id,
        "exotel_call_sid": call.exotel_call_sid,
        "status": call.status,
        "initiation_status": call.initiation_status,
        "message": (
            "Call request accepted by ElevenLabs. Connection status will update via webhook."
        ),
    }


def verify_webhook(raw_body: bytes, signature: Optional[str]) -> dict:
    if not settings.elevenlabs_webhook_secret:
        raise HTTPException(
            status_code=503,
            detail="ELEVENLABS_WEBHOOK_SECRET is not configured; webhook cannot be verified",
        )
    if not signature:
        raise HTTPException(status_code=401, detail="Missing ElevenLabs-Signature header")
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.errors import BadRequestError

        client = ElevenLabs(api_key=settings.elevenlabs_api_key or "unused")
        return client.webhooks.construct_event(
            rawBody=raw_body.decode("utf-8"),
            sig_header=signature,
            secret=settings.elevenlabs_webhook_secret,
        )
    except Exception as exc:
        logger.warning("Webhook verification failed: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Invalid webhook signature") from None


def _transcript_text(transcript: Any) -> str:
    if isinstance(transcript, str):
        return transcript
    lines = []
    for turn in transcript or []:
        if not isinstance(turn, dict):
            continue
        role = str(turn.get("role") or "speaker").capitalize()
        message = turn.get("message") or turn.get("text") or ""
        if message:
            lines.append(f"{role}: {message}")
    return "\n".join(lines)


def _find_call_for_event(db: Session, data: dict) -> Optional[Call]:
    conversation_id = data.get("conversation_id")
    if conversation_id:
        call = db.query(Call).filter(Call.conversation_id == conversation_id).first()
        if call:
            return call

    init_data = data.get("conversation_initiation_client_data") or {}
    dynamic = init_data.get("dynamic_variables") or {}
    call_id = dynamic.get("call_id")
    if call_id:
        call = db.get(Call, str(call_id))
        if call:
            return call

    lead_id = dynamic.get("lead_id")
    if lead_id:
        return (
            db.query(Call)
            .filter(Call.lead_id == str(lead_id))
            .order_by(Call.created_at.desc())
            .first()
        )
    return None


async def fetch_conversation(conversation_id: str) -> Optional[dict]:
    if not settings.elevenlabs_api_key:
        return None
    url = f"{settings.elevenlabs_api_base_url}/v1/convai/conversations/{conversation_id}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                headers={"xi-api-key": settings.elevenlabs_api_key},
            )
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None


async def process_conversation_data(call: Call, data: dict, db: Session) -> Dict[str, Any]:
    existing = db.query(CallSummary).filter(CallSummary.call_id == call.id).first()
    if existing:
        return {"status": "already_processed", "call_id": call.id}

    transcript = _transcript_text(data.get("transcript"))
    analysis = data.get("analysis") if isinstance(data.get("analysis"), dict) else {}
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    summary = analysis.get("transcript_summary") or "Call completed"
    extracted = extract_sentiment_and_outcome(transcript)

    context_text = "\n".join(
        [
            transcript,
            summary,
            json.dumps(analysis.get("data_collection_results") or {}, default=str),
        ]
    )
    qualification = await generate_qualification(
        context_text,
        {
            "lead_status": "qualified" if extracted["call_outcome"] == "interested" else "new",
            "interest": "high" if extracted["call_outcome"] == "interested" else "medium",
            "requirements": "Automate customer follow-ups",
            "sentiment": extracted["sentiment"],
            "call_outcome": extracted["call_outcome"],
            "next_action": "Schedule product demo",
        },
    )

    if analysis.get("call_successful") == "failure":
        qualification["call_outcome"] = "not_interested"

    store_transcript(call.id, transcript, db)
    store_call_summary(
        call_id=call.id,
        summary=str(summary),
        sentiment=qualification["sentiment"],
        call_outcome=qualification["call_outcome"],
        requirements=qualification["requirements"],
        interest=qualification["interest"],
        next_action=qualification["next_action"],
        db=db,
        lead_id=call.lead_id,
    )

    phone_call = metadata.get("phone_call") if isinstance(metadata.get("phone_call"), dict) else {}
    call_result = str(phone_call.get("call_result") or "").lower()
    call.status = "completed" if analysis.get("call_successful") != "failure" else "failed"
    call.initiation_status = "completed"
    call.call_outcome = qualification["call_outcome"]
    call.qualification_json = json.dumps(qualification)
    call.followup_required = bool(qualification.get("next_action"))
    duration = metadata.get("call_duration_secs") or 0
    if duration:
        try:
            call.duration_seconds = int(duration)
        except (TypeError, ValueError):
            pass
    started = metadata.get("start_time_unix_secs")
    if started:
        try:
            call.started_at = datetime.fromtimestamp(int(started), tz=timezone.utc).replace(tzinfo=None)
            if call.duration_seconds:
                call.ended_at = call.started_at + timedelta(seconds=call.duration_seconds)
        except (TypeError, ValueError):
            pass
    if phone_call.get("call_sid") and not call.exotel_call_sid:
        call.exotel_call_sid = str(phone_call["call_sid"])
    if data.get("conversation_id") and not call.conversation_id:
        call.conversation_id = str(data["conversation_id"])

    lead = LeadService.get_lead_details(call.lead_id, db) if call.lead_id else None
    if lead:
        update_lead(
            call.lead_id,
            {
                "status": qualification["lead_status"],
                "interest_level": qualification["interest"],
                "call_outcome": qualification["call_outcome"],
                "next_action": qualification["next_action"],
            },
            lead.owner_id,
            db,
        )

    call.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(call)
    return {"status": "processed", "call_id": call.id, "qualification": qualification}


async def process_webhook(payload: dict, db: Session) -> Dict[str, Any]:
    event_type = str(payload.get("type") or "")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    call = _find_call_for_event(db, data)
    if not call:
        return {"status": "ignored", "reason": "unknown_call", "type": event_type}

    if event_type == "call_initiation_failure":
        if call.status in {"failed", "completed"}:
            return {"status": "already_processed", "call_id": call.id}
        call.status = "failed"
        call.initiation_status = "failed"
        call.call_outcome = "call_failed"
        call.error_message = str(data.get("failure_reason") or "call initiation failed")
        call.ended_at = datetime.utcnow()
        db.commit()
        return {"status": "processed", "call_id": call.id, "type": event_type}

    if event_type == "post_call_transcription":
        result = await process_conversation_data(call, data, db)
        result["type"] = event_type
        return result

    if event_type == "post_call_audio":
        return {"status": "ignored", "reason": "audio_only", "call_id": call.id}

    return {"status": "ignored", "reason": "unsupported_event", "type": event_type}


async def sync_call_from_provider(call_id: str, db: Session) -> Dict[str, Any]:
    call = db.get(Call, call_id)
    if not call or not call.conversation_id:
        raise HTTPException(status_code=404, detail="Call conversation not found")
    data = await fetch_conversation(call.conversation_id)
    if not data:
        raise HTTPException(status_code=502, detail="Unable to retrieve conversation details")
    return await process_conversation_data(call, data, db)
