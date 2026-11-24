"""Validated backend tools for AI CallerOS.

The LLM never executes SQL. All database access goes through these
service-backed functions with ownership checks and argument validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.session import DEMO_USER_ID
from app.models import Call, Followup, Lead
from app.services.lead_service import LeadService


LEAD_FIELDS = {
    "id", "name", "email", "phone", "company", "status",
    "interest_level", "requirements", "sentiment", "call_outcome",
    "next_action", "source", "notes", "created_at", "updated_at",
}


def _lead_to_dict(lead: Lead) -> Dict[str, Any]:
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "status": lead.status,
        "interest_level": lead.interest_level,
        "requirements": lead.requirements,
        "sentiment": lead.sentiment,
        "call_outcome": lead.call_outcome,
        "next_action": lead.next_action,
        "source": lead.source,
        "notes": lead.notes,
        "owner_id": lead.owner_id,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


def get_lead_details(lead_id: str, owner_id: str, db: Session) -> Optional[Dict[str, Any]]:
    owner_id = owner_id or DEMO_USER_ID
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(owner_id):
        return None
    return _lead_to_dict(lead)


def update_lead(
    lead_id: str,
    updates: Dict[str, Any],
    owner_id: str,
    db: Session,
) -> Optional[Dict[str, Any]]:
    owner_id = owner_id or DEMO_USER_ID
    allowed = {k: v for k, v in updates.items() if k in LEAD_FIELDS and k not in {"id", "created_at", "updated_at"}}
    lead = LeadService.update_lead_fields(lead_id, allowed, owner_id, db)
    return _lead_to_dict(lead) if lead else None


def search_company_knowledge(query: str, owner_id: str, db: Session) -> List[Dict[str, Any]]:
    if not query or not isinstance(query, str):
        return []
    q = query.strip().lower()[:300]
    knowledge = [
        {
            "id": "kb-followup",
            "title": "Follow-up Best Practices",
            "content": "Follow up within 24 hours. Reference specific requirements discussed on the call.",
            "keywords": ["follow", "followup", "callback", "next"],
        },
        {
            "id": "kb-qualification",
            "title": "Lead Qualification Criteria",
            "content": "Qualify on need, urgency, budget, authority, and fit.",
            "keywords": ["qualify", "qualification", "budget", "interest"],
        },
        {
            "id": "kb-objection",
            "title": "Handling Objections",
            "content": "Acknowledge the concern, clarify value, and offer a human callback when requested.",
            "keywords": ["objection", "expensive", "human", "callback", "handoff"],
        },
    ]
    results = []
    for item in knowledge:
        if any(word in q for word in item["keywords"]) or q in item["content"].lower():
            results.append({k: v for k, v in item.items() if k != "keywords"})
    return results[:5]


def _parse_future_datetime(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    now = datetime.utcnow()
    if parsed <= now or parsed > now + timedelta(days=90):
        return None
    return parsed


def schedule_followup(lead_id: str, scheduled_at: str, user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    user_id = user_id or DEMO_USER_ID
    schedule_time = _parse_future_datetime(scheduled_at)
    if not schedule_time:
        return None

    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(user_id):
        return None

    existing = db.query(Followup).filter(
        Followup.lead_id == lead_id,
        Followup.scheduled_at == schedule_time,
        Followup.status == "pending",
    ).first()
    if existing:
        return _followup_to_dict(existing)

    followup = Followup(
        id=str(uuid4()),
        lead_id=lead_id,
        user_id=user_id,
        scheduled_at=schedule_time,
        status="pending",
        notes=f"Follow-up scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M')}",
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return _followup_to_dict(followup)


def _followup_to_dict(followup: Followup) -> Dict[str, Any]:
    return {
        "id": followup.id,
        "lead_id": followup.lead_id,
        "user_id": followup.user_id,
        "scheduled_at": followup.scheduled_at.isoformat() if followup.scheduled_at else None,
        "status": followup.status,
        "notes": followup.notes,
        "created_at": followup.created_at.isoformat() if followup.created_at else None,
    }


def end_call(call_id: str, outcome: str, db: Session) -> Optional[Dict[str, Any]]:
    if not outcome or not isinstance(outcome, str):
        return None
    outcome_key = outcome.strip().lower().replace(" ", "_")
    valid = {"interested", "not_interested", "callback", "appointment_booked", "missed"}
    if outcome_key not in valid:
        outcome_key = "unknown"

    call = db.get(Call, call_id)
    if not call:
        return None

    already_done = call.status == "completed"
    if not already_done:
        call.status = "completed"
        call.ended_at = call.ended_at or datetime.utcnow()
        db.add(call)

    lead = db.get(Lead, call.lead_id) if call.lead_id else None
    lead_updated = False
    if lead and not already_done:
        lead.call_outcome = outcome_key
        if outcome_key == "interested":
            lead.status = "qualified"
            lead.next_action = "Schedule product demo"
        elif outcome_key == "not_interested":
            lead.status = "not_interested"
            lead.next_action = "Send follow-up email"
        elif outcome_key == "callback":
            lead.status = "interested"
            lead.next_action = "Call back later"
        elif outcome_key == "appointment_booked":
            lead.status = "qualified"
            lead.next_action = "Attend appointment"
        lead.updated_at = datetime.utcnow()
        db.add(lead)
        lead_updated = True

    db.commit()
    if lead:
        db.refresh(lead)
    db.refresh(call)

    return {
        "call_id": call.id,
        "call_status": call.status,
        "call_ended_at": call.ended_at.isoformat() if call.ended_at else None,
        "call_duration": call.duration_seconds,
        "lead_id": call.lead_id,
        "lead_updated": lead_updated,
        "lead_status": lead.status if lead else None,
        "lead_call_outcome": lead.call_outcome if lead else None,
        "lead_next_action": lead.next_action if lead else None,
        "idempotent": already_done,
    }


class ConversationSimulator:
    """Deterministic demo conversation; no telephony credentials required."""

    @staticmethod
    def run_demo_conversation(lead_name: str = "Prospect") -> Dict[str, Any]:
        turns = [
            {"speaker": "agent", "text": f"Hello, this is an AI assistant calling from AI CallerOS. May I speak with {lead_name}?"},
            {"speaker": "user", "text": "Yes, this is them. I have a few minutes."},
            {"speaker": "agent", "text": "Are you available to talk about how we can help automate your customer follow-ups?"},
            {"speaker": "user", "text": "Yes. We often forget to follow up with new leads."},
            {"speaker": "agent", "text": "What is the main challenge you want to solve?"},
            {"speaker": "user", "text": "We need to automate customer follow-ups and understand which leads are interested."},
            {"speaker": "agent", "text": "How soon are you looking to implement a solution?"},
            {"speaker": "user", "text": "We would like to start soon, ideally in the next few weeks."},
            {"speaker": "agent", "text": "Would you like a product demo or a human callback?"},
            {"speaker": "user", "text": "A product demo would be great. Please schedule one."},
        ]

        qualification = {
            "lead_status": "qualified",
            "interest": "high",
            "requirements": "Automate customer follow-ups and identify interested leads",
            "sentiment": "positive",
            "call_outcome": "interested",
            "next_action": "Schedule product demo",
        }
        transcript = "\n".join(f"{t['speaker'].capitalize()}: {t['text']}" for t in turns)
        return {
            "mode": "demo",
            "turns": turns,
            "transcript": transcript,
            "qualification": qualification,
            "summary": f"{lead_name} is interested in automating customer follow-ups and requested a product demo.",
            "duration_seconds": 180,
        }
