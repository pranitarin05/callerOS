"""Transcript and summary persistence helpers."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Call, CallSummary, Transcript
from app.services.lead_service import LeadService
from app.tools import update_lead


POSITIVE_WORDS = [
    "interested", "demo", "automate", "soon", "help", "solution",
    "great", "yes", "definitely", "please", "schedule",
]
NEGATIVE_WORDS = [
    "not interested", "expensive", "not needed", "already have",
    "stop", "don't want", "waste of time",
]


def extract_sentiment_and_outcome(conversation_text: str) -> Dict[str, str]:
    text = (conversation_text or "").lower()
    positive = sum(1 for word in POSITIVE_WORDS if word in text)
    negative = sum(1 for word in NEGATIVE_WORDS if word in text)

    if positive > negative:
        sentiment = "positive"
    elif negative > positive:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    if "not interested" in text or "don't want" in text:
        outcome = "not_interested"
    elif "demo" in text or "interested" in text:
        outcome = "interested"
    elif "callback" in text or "call back" in text:
        outcome = "callback"
    elif "appointment" in text or "schedule" in text:
        outcome = "appointment_booked"
    else:
        outcome = "callback"

    return {"sentiment": sentiment, "call_outcome": outcome}


def store_transcript(call_id: str, content: str, db: Session) -> Optional[Dict[str, Any]]:
    call = db.get(Call, call_id)
    if not call:
        return None

    transcript = db.query(Transcript).filter(Transcript.call_id == call_id).first()
    if transcript:
        transcript.content = content
        transcript.updated_at = datetime.utcnow()
    else:
        transcript = Transcript(id=str(uuid4()), call_id=call_id, content=content)
        db.add(transcript)

    call.transcript_id = transcript.id
    db.commit()
    db.refresh(transcript)
    return {
        "id": transcript.id,
        "call_id": transcript.call_id,
        "content": transcript.content,
        "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
    }


def store_call_summary(
    call_id: str,
    summary: str,
    sentiment: str,
    call_outcome: str,
    requirements: str,
    interest: str,
    next_action: str,
    db: Session,
    lead_id: str = "",
) -> Optional[Dict[str, Any]]:
    call = db.get(Call, call_id)
    if not call:
        return None
    lead_id = lead_id or call.lead_id
    lead = LeadService.get_lead_details(lead_id, db) if lead_id else None
    if not lead:
        return None

    record = db.query(CallSummary).filter(CallSummary.call_id == call_id).first()
    if record:
        record.summary = summary
        record.sentiment = sentiment
        record.call_outcome = call_outcome
        record.requirements = requirements
        record.interest = interest
        record.next_action = next_action
        record.updated_at = datetime.utcnow()
    else:
        record = CallSummary(
            id=str(uuid4()),
            call_id=call_id,
            summary=summary,
            sentiment=sentiment,
            call_outcome=call_outcome,
            requirements=requirements,
            interest=interest,
            next_action=next_action,
        )
        db.add(record)

    call.summary_id = record.id
    update_lead(
        lead_id,
        {
            "call_outcome": call_outcome,
            "requirements": requirements,
            "sentiment": sentiment,
            "interest_level": interest,
            "next_action": next_action,
        },
        lead.owner_id,
        db,
    )
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "call_id": record.call_id,
        "summary": record.summary,
        "sentiment": record.sentiment,
        "call_outcome": record.call_outcome,
        "requirements": record.requirements,
        "interest": record.interest,
        "next_action": record.next_action,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def process_call_completion(
    call_id: str,
    conversation_text: str,
    db: Session,
    lead_id: str = "",
) -> Dict[str, Any]:
    call = db.get(Call, call_id)
    if not call:
        return {"error": "call_not_found", "call_id": call_id}
    lead_id = lead_id or call.lead_id

    extracted = extract_sentiment_and_outcome(conversation_text)
    requirements = "Automate customer follow-ups"
    lower = conversation_text.lower()
    if "customer service" in lower:
        requirements = "Improve customer service response times"
    elif "sales" in lower:
        requirements = "Automate sales follow-ups"

    next_action_map = {
        "interested": "Schedule product demo",
        "not_interested": "Send follow-up email",
        "callback": "Call back later",
        "appointment_booked": "Attend appointment",
    }
    next_action = next_action_map.get(extracted["call_outcome"], "Send follow-up information")

    transcript_result = store_transcript(call_id, conversation_text, db)
    summary_result = store_call_summary(
        call_id=call_id,
        summary=(
            f"Call outcome: {extracted['call_outcome']}. "
            f"Sentiment: {extracted['sentiment']}. Requirements: {requirements}."
        ),
        sentiment=extracted["sentiment"],
        call_outcome=extracted["call_outcome"],
        requirements=requirements,
        interest="high" if extracted["call_outcome"] == "interested" else "medium",
        next_action=next_action,
        db=db,
        lead_id=lead_id,
    )

    return {
        "call_id": call_id,
        "sentiment": extracted["sentiment"],
        "call_outcome": extracted["call_outcome"],
        "requirements": requirements,
        "next_action": next_action,
        "transcript_stored": transcript_result is not None,
        "summary_stored": summary_result is not None,
    }
