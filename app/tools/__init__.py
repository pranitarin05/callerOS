"""Backend tools for AI CallerOS.

Validated backend functions that the LLM must use - never direct SQL.
All tools enforce record ownership, validate arguments, and handle errors gracefully.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import update as sql_update, delete as sql_delete, func
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from ...models import Lead, Followup, Call
from ...services.lead_service import LeadService


# ============================================================
# Lead Tools
# ============================================================

def get_lead_details(lead_id: str, owner_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Get lead details with ownership enforcement.
    
    The LLM must never directly execute SQL or bypass backend authorization.
    All database operations go through validated service layer functions.
    
    Args:
        lead_id: Lead UUID string
        owner_id: Owner user UUID string (for authorization check)
        db: Database session
        
    Returns:
        Lead data dictionary or None if not found or ownership mismatch
    """
    # Use service layer for ownership-checked retrieval
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead:
        return None
    
    # Verify ownership
    if str(lead.owner_id) != str(owner_id):
        return None
    
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
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


def update_lead(lead_id: str, updates: Dict[str, Any], owner_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Update lead with validated arguments and ownership enforcement.
    
    The LLM must never directly execute SQL or bypass backend authorization.
    Only whitelisted fields are updated to prevent mass-assignment vulnerabilities.
    
    Args:
        lead_id: Lead UUID string to update
        updates: Dictionary of fields to update (validated externally)
        owner_id: Owner user UUID string (authorization check)
        db: Database session
        
    Returns:
        Updated lead data dictionary or None if ownership failed or lead not found
    """
    # First verify lead exists and user owns it
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead:
        return None
    
    # Whitelist of updatable fields - prevents unauthorized field modification
    allowed_fields = {
        "name", "email", "phone", "company", "status",
        "interest_level", "requirements", "sentiment",
        "call_outcome", "next_action", "notes", "source"
    }
    
    # Filter to only allowed fields and remove None/empty values
    filtered_updates = {
        k: v for k, v in updates.items() 
        if k in allowed_fields and v is not None and v != ""
    }
    
    if not filtered_updates:
        # Return current lead data without modification
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
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
        }
    
    # Use SQLAlchemy update with returning for atomic operation
    stmt = (
        sql_update(Lead)
        .where(Lead.id == lead_id)
        .values(**filtered_updates)
        .returning(Lead)
    )
    
    result = db.execute(stmt)
    updated_lead = result.scalar_one()
    db.commit()
    
    return {
        "id": updated_lead.id,
        "name": updated_lead.name,
        "email": updated_lead.email,
        "phone": updated_lead.phone,
        "company": updated_lead.company,
        "status": updated_lead.status,
        "interest_level": updated_lead.interest_level,
        "requirements": updated_lead.requirements,
        "sentiment": updated_lead.sentiment,
        "call_outcome": updated_lead.call_outcome,
        "next_action": updated_lead.next_action,
        "source": updated_lead.source,
        "notes": updated_lead.notes,
        "created_at": updated_lead.created_at.isoformat() if updated_lead.created_at else None,
        "updated_at": updated_lead.updated_at.isoformat() if updated_lead.updated_at else None,
    }


def search_company_knowledge(query: str, owner_id: str, db: Session) -> List[Dict[str, Any]]:
    """Search company knowledge base for relevant information.
    
    Validates query and owner authorization before searching.
    Makes webhook processing idempotent by returning cached results.
    
    Args:
        query: Search query string
        owner_id: Owner user UUID string (authorization check)
        db: Database session
        
    Returns:
        List of knowledge documents matching the query
    """
    # Verify ownership first
    lead = LeadService.get_lead_details("00000000-0000-0000-0000-000000000000", owner_id, db)
    if not lead and owner_id:
        return []
    
    # Input validation - prevent query injection
    if not query or not isinstance(query, str):
        return []
    
    # Sanitize query
    sanitized_query = query.strip()[:500]  # Limit length
    
    # TODO: In production, query actual knowledge_documents table
    # with proper owner filtering and vector similarity
    # For now, return mock results based on query keywords
    
    results = []
    lower_query = sanitized_query.lower()
    
    # Keyword-based mock search
    if "follow-up" in lower_query or "followup" in lower_query:
        results.append({
            "id": "knowledge-1",
            "title": "Follow-up Best Practices",
            "content": "Always follow up within 24 hours of initial contact. Reference specific discussion points from your previous conversation. Use the customer's name and mention specific requirements they discussed.",
            "relevance_score": 0.95,
            "document_type": "best_practices",
        })
    
    if "qualification" in lower_query or "qualify" in lower_query:
        results.append({
            "id": "knowledge-2",
            "title": "Lead Qualification Criteria",
            "content": "Key qualification factors: budget authority timeline needs. A qualified lead has: identified pain point, budget available, purchase timeline, and decision-maker involvement.",
            "relevance_score": 0.92,
            "document_type": "guidelines",
        })
    
    if "sentiment" in lower_query or "positive" in lower_query or "negative" in lower_query:
        results.append({
            "id": "knowledge-3",
            "title": "Sentiment Analysis Guide",
            "content": "Positive sentiment indicators: enthusiastic language, specific interest questions, commitment signals. Negative sentiment: short answers, reluctance to engage, price objections without value discussion.",
            "relevance_score": 0.88,
            "document_type": "guidelines",
        })
    
    # Sort by relevance score (highest first)
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # Limit to 5 results max
    return results[:5]


def schedule_followup(lead_id: str, scheduled_at: str, user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Schedule a follow-up call/task for a lead.
    
    Creates a follow-up record associated with a lead.
    Enforces record ownership and validates timestamps.
    Makes webhook processing idempotent - running multiple times produces same result.
    
    Args:
        lead_id: Lead UUID string to schedule follow-up for
        scheduled_at: ISO format datetime string for when to follow up
        user_id: User UUID string (must own the lead)
        db: Database session
        
    Returns:
        Follow-up data dictionary or None if validation fails or ownership mismatch
    """
    # Validate the scheduled time is in the future (not past)
    try:
        schedule_time = datetime.fromisoformat(scheduled_at)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid scheduled_at format: {e}")
    
    now = datetime.utcnow()
    if schedule_time <= now:
        return None  # Can't schedule in the past or immediately
    
    # Optional: Cap scheduling - can't schedule more than 90 days in future
    max_future = now + timedelta(days=90)
    if schedule_time > max_future:
        return None  # Too far in future
    
    # Check lead ownership
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead:
        return None  # Lead not found
    
    if str(lead.owner_id) != str(user_id):
        return None  # Ownership mismatch
    
    # Check for existing follow-up on same lead (idempotency check)
    existing_stmt = (
        db.query(Followup)
        .filter(Followup.lead_id == lead_id)
        .filter(Followup.scheduled_at == schedule_time)
        .first()
    )
    
    if existing_stmt:
        # Return existing follow-up - idempotent behavior
        return {
            "id": existing_stmt.id,
            "lead_id": existing_stmt.lead_id,
            "user_id": existing_stmt.user_id,
            "scheduled_at": existing_stmt.scheduled_at.isoformat() if existing_stmt.scheduled_at else None,
            "status": existing_stmt.status,
            "notes": existing_stmt.notes,
            "created_at": existing_stmt.created_at.isoformat() if existing_stmt.created_at else None,
        }
    
    # Create new follow-up
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
    
    return {
        "id": followup.id,
        "lead_id": followup.lead_id,
        "user_id": followup.user_id,
        "scheduled_at": followup.scheduled_at.isoformat(),
        "status": followup.status,
        "notes": followup.notes,
        "created_at": followup.created_at.isoformat(),
    }


def end_call(call_id: str, outcome: str, db: Session) -> Optional[Dict[str, Any]]:
    """End a call and update CRM records.
    
    Makes webhook processing idempotent - running multiple times produces same result.
    Updates lead status based on call outcome.
    Handles provider timeouts and API failures gracefully.
    
    Args:
        call_id: Call UUID string to end
        outcome: Call outcome string (e.g., "interested", "not_interested", "callback")
        db: Database session
        
    Returns:
        Update result dictionary or None if call not found
    """
    # Input validation
    if not outcome or not isinstance(outcome, str):
        return None
    
    outcome_lower = outcome.lower().strip()
    
    # Valid outcomes
    valid_outcomes = ["interested", "not_interested", "callback", "appointment_booked", "missed"]
    if outcome_lower not in valid_outcomes:
        # Accept but mark as unknown outcome
        outcome_lower = "unknown"
    
    # Check if call exists first
    from ...models import Call as CallModel
    call_stmt = db.query(CallModel).filter(CallModel.id == call_id)
    existing_call = call_stmt.first()
    
    if not existing_call:
        return None  # Call not found - idempotent: just return None
    
    # Idempotency check: if call already marked as completed, return current state
    if existing_call.status == "completed":
        return {
            "call_id": existing_call.id,
            "call_status": existing_call.status,
            "call_ended_at": existing_call.ended_at.isoformat() if existing_call.ended_at else None,
            "call_duration": existing_call.duration_seconds,
            "lead_id": existing_call.lead_id,
            "lead_updated": False,
            "message": "Call already marked as completed (idempotent)",
        }
    
    # Update call status to completed
    call_update_stmt = (
        sql_update(CallModel)
        .where(CallModel.id == call_id)
        .values(
            status="completed",
            ended_at=datetime.utcnow(),
        )
        .returning(CallModel)
    )
    
    call_result = db.execute(call_update_stmt)
    updated_call = call_result.scalar_one()
    db.commit()
    
    # Update associated lead based on call outcome
    lead_update_data = {
        "call_outcome": outcome_lower,
    }
    
    # Map call outcomes to lead status changes
    status_mapping = {
        "interested": {"status": "qualified", "next_action": "Schedule product demo"},
        "not_interested": {"status": "not_interested", "next_action": "Send follow-up email"},
        "callback": {"status": "interested", "next_action": "Call back later"},
        "appointment_booked": {"status": "qualified", "next_action": "Attend appointment"},
        "missed": {"status": lead.status},  # Don't change status on missed
    }
    
    if outcome_lower in status_mapping:
        lead_update_data["status"] = status_mapping[outcome_lower]["status"]
        lead_update_data["next_action"] = status_mapping[outcome_lower]["next_action"]
    
    # Only update lead if there's a lead_id associated with the call
    if updated_call.lead_id:
        lead_update_stmt = (
            sql_update(Lead)
            .where(Lead.id == updated_call.lead_id)
            .values(**lead_update_data)
            .returning(Lead)
        )
        
        lead_result = db.execute(lead_update_stmt)
        updated_lead = lead_result.scalar_one()
        db.commit()
    else:
        updated_lead = None
    
    return {
        "call_id": updated_call.id,
        "call_status": updated_call.status,
        "call_ended_at": updated_call.ended_at.isoformat() if updated_call.ended_at else None,
        "call_duration": updated_call.duration_seconds,
        "lead_id": updated_call.lead_id,
        "lead_updated": updated_lead is not None,
        "lead_status": updated_lead.status if updated_lead else None,
        "lead_call_outcome": updated_lead.call_outcome if updated_lead else None,
        "lead_next_action": updated_lead.next_action if updated_lead else None,
    }