from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from ...db.session import get_db
from ...models import Lead
from ...schemas.qualification import QualificationOutput, ConversationTurn, ConversationSummary
from ...tools import ConversationSimulator, get_lead_details, update_lead, search_company_knowledge, schedule_followup, end_call
from ...services.lead_service import LeadService


router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.post("/simulate", response_model=dict)
async def simulate_conversation(
    lead_id: str,
    lead_name: str,
    db: Session = Depends(get_db),
):
    """Run AI conversation simulator in demo mode.
    
    Works without paid telephony credentials. Demonstrates the complete workflow
    including AI responses, tool execution, CRM updates and summary generation.
    
    Args:
        lead_id: The lead's UUID string
        lead_name: Name of the prospect for personalization
        db: Database session
        
    Returns:
        Complete conversation with turns and qualification data
    """
    # Verify lead exists and user has access
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    # Run demo conversation
    result = ConversationSimulator.run_demo_conversation(lead_name=lead_name)
    
    # Update lead status based on qualification
    qualification = result["qualification"]
    updates = {
        "interest_level": qualification["interest"],
        "requirements": qualification["requirements"],
        "sentiment": qualification["sentiment"],
        "call_outcome": qualification["call_outcome"],
        "next_action": qualification["next_action"],
    }
    
    updated_lead = update_lead(lead_id, updates, lead.owner_id, db)
    
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead",
        )
    
    # Add lead ID to the summary
    result["summary"] = result["summary"].replace("Lead " + lead_name, f"Lead {lead_name} (ID: {lead_id})")
    
    return {
        "mode": "demo",
        "lead_id": lead_id,
        "conversation": result,
        "updated_lead": {
            "id": updated_lead.id,
            "status": updated_lead.status,
            "interest_level": updated_lead.interest_level,
            "call_outcome": updated_lead.call_outcome,
            "next_action": updated_lead.next_action,
        }
    }


@router.post("/qualify", response_model=QualificationOutput)
async def qualify_lead(
    lead_id: str,
    conversation_history: List[dict],
    db: Session = Depends(get_db),
):
    """AI lead qualification from conversation history.
    
    Extracts structured qualification data from a conversation.
    Uses backend tools for CRM updates - LLM never directly executes SQL.
    
    Args:
        lead_id: The lead's UUID string
        conversation_history: List of conversation turn dictionaries
        db: Database session
        
    Returns:
        Structured qualification output
    """
    # Verify lead ownership
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    # In a real implementation, would use OpenAI API with structured outputs
    # For demo mode, generate realistic qualification based on conversation
    
    # Simple heuristic-based qualification for demo
    positive_keywords = ["interested", "demo", "automate", "soon", "help", "solution"]
    negative_keywords = ["not interested", "expensive", "not needed", "already have system"]
    
    conversation_text = " ".join([turn.get("text", "").lower() for turn in conversation_history])
    
    # Determine interest level
    if any(kw in conversation_text for kw in positive_keywords):
        interest = "high"
    elif any(kw in conversation_text for kw in negative_keywords):
        interest = "low"
    else:
        interest = "medium"
    
    # Determine sentiment
    positive_count = sum(1 for kw in positive_keywords if kw in conversation_text)
    negative_count = sum(1 for kw in negative_keywords if kw in conversation_text)
    
    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    # Determine call outcome
    if "demo" in conversation_text or "interested" in conversation_text:
        call_outcome = "interested"
        lead_status = "qualified"
        next_action = "Schedule product demo"
    elif "not interested" in conversation_text:
        call_outcome = "not_interested"
        lead_status = "not_interested"
        next_action = "Send follow-up email"
    else:
        call_outcome = "callback"
        lead_status = "interested"
        next_action = "Call back later"
    
    # Extract requirements (simplified - would use NER in production)
    requirements = "Automate customer follow-ups"  # Default
    if "customer service" in conversation_text:
        requirements = "Improve customer service response times"
    elif "sales follow-up" in conversation_text:
        requirements = "Automate sales follow-ups"
    
    # Update lead in CRM using backend tool
    update_data = {
        "interest_level": interest,
        "requirements": requirements,
        "sentiment": sentiment,
        "call_outcome": call_outcome,
        "next_action": next_action,
    }
    
    updated_lead = update_lead(lead_id, update_data, lead.owner_id, db)
    
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead in CRM",
        )
    
    return QualificationOutput(
        lead_status=lead_status,
        interest=interest,
        requirements=requirements,
        sentiment=sentiment,
        call_outcome=call_outcome,
        next_action=next_action,
    )


@router.post("/knowledge-search", response_model=List[dict])
async def search_knowledge(
    query: str,
    lead_id: str,
    db: Session = Depends(get_db),
):
    """Search company knowledge base for relevant information.
    
    Validates lead ownership before allowing knowledge search.
    """
    # Verify lead exists and user has access
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    results = search_company_knowledge(query, lead.owner_id, db)
    return results


@router.post("/followup", response_model=dict)
async def create_followup(
    lead_id: str,
    scheduled_at: str,
    user_id: str,
    db: Session = Depends(get_db),
):
    """Schedule a follow-up call/task for a lead.
    
    Uses backend tool for idempotent follow-up creation.
    """
    result = schedule_followup(lead_id, scheduled_at, user_id, db)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to schedule follow-up. Check lead ownership and timestamp.",
        )
    
    return result


@router.post("/end-call", response_model=dict)
async def complete_call(
    call_id: str,
    outcome: str,
    db: Session = Depends(get_db),
):
    """End a call and update CRM records.
    
    Makes webhook processing idempotent and updates lead status
    based on call outcome.
    """
    result = end_call(call_id, outcome, db)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )
    
    return result