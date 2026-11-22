"""Transcript and Summary storage for AI CallerOS.

Handles storing call transcripts, AI-generated summaries, sentiment analysis,
and call outcomes in the database.
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update as sql_update
from typing import Optional, Dict, Any

from ...models import Call, Transcript, CallSummary, Lead
from ...services.lead_service import LeadService
from ...tools import get_lead_details, update_lead


# ============================================================
# Transcript Storage
# ============================================================

def store_transcript(
    call_id: str,
    content: str,
    db: Session,
) -> Optional[Dict[str, Any]]:
    """Store a call transcript in the database.
    
    Args:
        call_id: Call UUID string
        content: Full transcript text
        db: Database session
        
    Returns:
        Transcript data dictionary or None if call not found
    """
    # Verify call exists
    from ...models import Call as CallModel
    call_stmt = db.query(CallModel).filter(CallModel.id == call_id)
    call = call_stmt.first()
    
    if not call:
        return None
    
    # Check for existing transcript (idempotent)
    existing_stmt = (
        db.query(Transcript)
        .filter(Transcript.call_id == call_id)
        .first()
    )
    
    if existing_stmt:
        # Update existing transcript - idempotent
        existing_stmt.content = content
        existing_stmt.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_stmt)
        return {
            "id": existing_stmt.id,
            "call_id": existing_stmt.call_id,
            "content": existing_stmt.content,
            "created_at": existing_stmt.created_at.isoformat() if existing_stmt.created_at else None,
            "updated_at": existing_stmt.updated_at.isoformat() if existing_stmt.updated_at else None,
        }
    
    # Create new transcript
    transcript_id = str(uuid4())
    transcript = Transcript(
        id=transcript_id,
        call_id=call_id,
        content=content,
    )
    
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    return {
        "id": transcript_id,
        "call_id": call_id,
        "content": content,
        "created_at": transcript.created_at.isoformat() if hasattr(transcript, 'created_at') else None,
    }


# ============================================================
# Call Summary Storage
# ============================================================

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
    """Store an AI-generated call summary in the database.
    
    Args:
        call_id: Call UUID string
        summary: AI-generated call summary text
        sentiment: Sentiment classification (positive, negative, neutral)
        call_outcome: Call outcome (interested, not_interested, callback, etc.)
        requirements: Lead requirements extracted from conversation
        interest: Interest level (low, medium, high)
        next_action: Recommended next action
        db: Database session
        lead_id: Lead UUID string (for ownership enforcement)
        
    Returns:
        CallSummary data dictionary or None if call not found
    """
    # Verify call exists and user has access
    lead = LeadService.get_lead_details(lead_id, db) if lead_id else None
    if not lead:
        return None
    
    # Check for existing summary (idempotent)
    existing_stmt = (
        db.query(CallSummary)
        .filter(CallSummary.call_id == call_id)
        .first()
    )
    
    if existing_stmt:
        # Update existing summary - idempotent
        existing_stmt.summary = summary
        existing_stmt.sentiment = sentiment
        existing_stmt.call_outcome = call_outcome
        existing_stmt.requirements = requirements
        existing_stmt.interest = interest
        existing_stmt.next_action = next_action
        existing_stmt.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_stmt)
        return {
            "id": existing_stmt.id,
            "call_id": existing_stmt.call_id,
            "summary": existing_stmt.summary,
            "sentiment": existing_stmt.sentiment,
            "call_outcome": existing_stmt.call_outcome,
            "requirements": existing_stmt.requirements,
            "interest": existing_stmt.interest,
            "next_action": existing_stmt.next_action,
            "created_at": existing_stmt.created_at.isoformat() if existing_stmt.created_at else None,
            "updated_at": existing_stmt.updated_at.isoformat() if existing_stmt.updated_at else None,
        }
    
    # Create new summary
    summary_id = str(uuid4())
    summary_record = CallSummary(
        id=summary_id,
        call_id=call_id,
        summary=summary,
        sentiment=sentiment,
        call_outcome=call_outcome,
        requirements=requirements,
        interest=interest,
        next_action=next_action,
    )
    
    db.add(summary_record)
    db.commit()
    db.refresh(summary_record)
    
    # Update lead with call outcome and requirements
    if lead_id:
        update_data = {}
        if call_outcome:
            update_data["call_outcome"] = call_outcome
        if requirements:
            update_data["requirements"] = requirements
        if sentiment:
            update_data["sentiment"] = sentiment
        if next_action:
            update_data["next_action"] = next_action
        
        if update_data:
            updated_lead = update_lead(lead_id, update_data, lead.owner_id, db)
    
    return {
        "id": summary_id,
        "call_id": call_id,
        "summary": summary_record.summary,
        "sentiment": summary_record.sentiment,
        "call_outcome": summary_record.call_outcome,
        "requirements": summary_record.requirements,
        "interest": summary_record.interest,
        "next_action": summary_record.next_action,
        "created_at": summary_record.created_at.isoformat() if hasattr(summary_record, 'created_at') else None,
    }


# ============================================================
# Sentiment and Outcome Extraction
# ============================================================

def extract_sentiment_and_outcome(
    conversation_text: str,
) -> Dict[str, str]:
    """Extract sentiment and call outcome from conversation text.
    
    Uses heuristic-based analysis for demo mode. In production, would use
    OpenAI/NLP models with structured outputs.
    
    Args:
        conversation_text: Full conversation transcript
        
    Returns:
        Dictionary with sentiment and call_outcome
    """
    positive_keywords = [
        "interested", "demo", "automate", "soon", "help", "solution",
        "great", "yes", "definitely", "please", "contact", "follow-up"
    ]
    
    negative_keywords = [
        "not interested", "expensive", "not needed", "already have",
        "no", "stop", "don't want", "waste of time"
    ]
    
    conversation_lower = conversation_text.lower()
    
    positive_count = sum(1 for kw in positive_keywords if kw in conversation_lower)
    negative_count = sum(1 for kw in negative_keywords if kw in conversation_lower)
    
    # Determine sentiment
    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    # Determine call outcome
    if any(kw in conversation_lower for kw in ["demo", "interested", "please contact"]):
        call_outcome = "interested"
    elif any(kw in conversation_lower for kw in ["not interested", "no", "stop"]):
        call_outcome = "not_interested"
    elif any(kw in conversation_lower for kw in ["callback", "call back"]):
        call_outcome = "callback"
    elif any(kw in conversation_lower for kw in ["appointment", "schedule"]):
        call_outcome = "appointment_booked"
    else:
        call_outcome = "callback"
    
    return {
        "sentiment": sentiment,
        "call_outcome": call_outcome,
    }


# ============================================================
# Complete Call Flow End-to-End
# ============================================================

def process_call_completion(
    call_id: str,
    conversation_text: str,
    db: Session,
    lead_id: str = "",
) -> Dict[str, Any]:
    """Complete end-to-end process for call completion.
    
    1. Store transcript
    2. Extract sentiment and outcome
    3. Store call summary
    4. Update lead records
    
    Makes the entire process idempotent - running multiple times produces same result.
    
    Args:
        call_id: Call UUID string
        conversation_text: Full conversation transcript
        db: Database session
        lead_id: Lead UUID string
        
    Returns:
        Complete processing result dictionary
    """
    # Step 1: Extract sentiment and outcome
    extraction = extract_sentiment_and_outcome(conversation_text)
    sentiment = extraction["sentiment"]
    call_outcome = extraction["call_outcome"]
    
    # Step 2: Identify requirements (simple heuristic)
    requirements = "Automate customer follow-ups"  # Default
    if "customer service" in conversation_text.lower():
        requirements = "Improve customer service response times"
    elif "sales follow-up" in conversation_text.lower():
        requirements = "Automate sales follow-ups"
    
    # Step 3: Determine next action based on outcome
    next_action_map = {
        "interested": "Schedule product demo",
        "not_interested": "Send follow-up email",
        "callback": "Call back later",
        "appointment_booked": "Attend appointment",
    }
    next_action = next_action_map.get(call_outcome, "Send follow-up information")
    
    # Step 4: Store transcript
    transcript_result = store_transcript(call_id, conversation_text, db)
    
    # Step 5: Store call summary
    # Get lead_id from call if not provided
    if not lead_id:
        from ...models import Call as CallModel
        call_stmt = db.query(CallModel).filter(CallModel.id == call_id)
        call = call_stmt.first()
        lead_id = call.lead_id if call else ""
    
    summary_result = store_call_summary(
        call_id=call_id,
        summary=f"Call with {call_outcome} outcome. {sentiment.capitalize()} sentiment. "
                f"Key requirements: {requirements}",
        sentiment=sentiment,
        call_outcome=call_outcome,
        requirements=requirements,
        interest="medium",  # Default - would be extracted from conversation
        next_action=next_action,
        db=db,
        lead_id=lead_id,
    )
    
    # Step 6: Update lead with call results
    if lead_id:
        update_data = {
            "call_outcome": call_outcome,
            "sentiment": sentiment,
            "next_action": next_action,
        }
        # Only update non-empty values
        update_data = {k: v for k, v in update_data.items() if v}
        if update_data:
            updated_lead = update_lead(lead_id, update_data, "", db)
    
    return {
        "call_id": call_id,
        "sentiment": sentiment,
        "call_outcome": call_outcome,
        "requirements": requirements,
        "next_action": next_action,
        "transcript_stored": transcript_result is not None,
        "summary_stored": summary_result is not None,
        "lead_updated": update_data is not None,
    }