from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.ai import generate_qualification
from app.db.session import get_db
from app.models import Call
from app.schemas.qualification import QualificationOutput
from app.services.lead_service import LeadService
from app.tools import (
    ConversationSimulator,
    end_call,
    get_lead_details,
    schedule_followup,
    search_company_knowledge,
    update_lead,
)
from app.tools.transcripts import process_call_completion

router = APIRouter(tags=["conversations"])


@router.post("/simulate")
async def simulate(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead_id = str(payload.get("lead_id") or "")
    lead_name = str(payload.get("lead_name") or "Prospect")
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Lead not found")

    conversation = ConversationSimulator.run_demo_conversation(lead_name=lead_name)
    call = Call(
        id=str(uuid4()),
        lead_id=lead_id,
        direction="outbound",
        status="initiated",
        phone_number=lead.phone,
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()

    processed = process_call_completion(call.id, conversation["transcript"], db)
    end_call(call.id, "interested", db)
    updated_lead = get_lead_details(lead_id, user_id, db)

    return {
        "mode": "demo",
        "lead_id": lead_id,
        "conversation": conversation,
        "processed": processed,
        "updated_lead": updated_lead,
    }


@router.post("/qualify", response_model=QualificationOutput)
async def qualify(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead_id = str(payload.get("lead_id") or "")
    turns = payload.get("conversation_history") or payload.get("turns") or []
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Lead not found")

    texts = []
    for turn in turns:
        if isinstance(turn, dict):
            texts.append(str(turn.get("text") or ""))
        else:
            texts.append(str(turn))
    text = " ".join(texts).lower()

    positive = sum(word in text for word in ["interested", "demo", "soon", "great", "automate"])
    negative = sum(word in text for word in ["not interested", "no", "expensive", "stop"])

    fallback_sentiment = "positive" if positive > negative else "negative" if negative > positive else "neutral"
    if "not interested" in text:
        fallback_outcome, fallback_status, fallback_next = "not_interested", "not_interested", "Send follow-up email"
    elif "demo" in text or "interested" in text:
        fallback_outcome, fallback_status, fallback_next = "interested", "qualified", "Schedule product demo"
    else:
        fallback_outcome, fallback_status, fallback_next = "callback", "interested", "Call back later"

    fallback_interest = "high" if fallback_outcome == "interested" else "low" if fallback_outcome == "not_interested" else "medium"
    fallback_requirements = "Improve customer service response times" if "customer service" in text else "Automate customer follow-ups"

    result = await generate_qualification(
        "\n".join(texts),
        {
            "lead_status": fallback_status,
            "interest": fallback_interest,
            "requirements": fallback_requirements,
            "sentiment": fallback_sentiment,
            "call_outcome": fallback_outcome,
            "next_action": fallback_next,
        },
    )

    status = str(result["lead_status"])
    interest = str(result["interest"])
    requirements = str(result["requirements"])
    sentiment = str(result["sentiment"])
    outcome = str(result["call_outcome"])
    next_action = str(result["next_action"])

    updated = update_lead(
        lead_id,
        {
            "status": status,
            "interest_level": interest,
            "requirements": requirements,
            "sentiment": sentiment,
            "call_outcome": outcome,
            "next_action": next_action,
        },
        user_id,
        db,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update lead")

    return QualificationOutput(
        lead_status=status,
        interest=interest,
        requirements=requirements,
        sentiment=sentiment,
        call_outcome=outcome,
        next_action=next_action,
    )


@router.post("/knowledge-search")
async def knowledge_search(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = str(payload.get("query") or "")
    return search_company_knowledge(query, user_id, db)


@router.post("/followup")
async def create_followup(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead_id = str(payload.get("lead_id") or "")
    scheduled_at = str(payload.get("scheduled_at") or "")
    result = schedule_followup(lead_id, scheduled_at, user_id, db)
    if not result:
        raise HTTPException(status_code=400, detail="Invalid lead, owner, or scheduled_at")
    return result


@router.post("/end-call")
async def complete_call(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    call_id = str(payload.get("call_id") or "")
    outcome = str(payload.get("outcome") or "")
    result = end_call(call_id, outcome, db)
    if not result:
        raise HTTPException(status_code=404, detail="Call not found")
    return result
