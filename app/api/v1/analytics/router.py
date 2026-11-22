from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select, cast, Integer as SQLInteger
from typing import List, Optional

from ...db.session import get_db
from ...models import Lead, Call, Followup, Profile
from ...schemas.lead import LeadResponse


router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=dict)
async def dashboard_metrics(
    db: Session = Depends(get_db),
):
    """Get dashboard metrics for the leads dashboard."""
    
    # Total leads
    total_leads = db.scalar(select(func.count(Lead.id)))
    
    # Leads by status
    status_query = (
        select(Lead.status, func.count(Lead.id))
        .group_by(Lead.status)
    )
    status_results = db.execute(status_query).all()
    leads_by_status = {status: count for status, count in status_results}
    
    # Leads by interest level
    interest_query = (
        select(Lead.interest_level, func.count(Lead.id))
        .group_by(Lead.interest_level)
    )
    interest_results = db.execute(interest_query).all()
    leads_by_interest = {level: count for level, count in interest_results}
    
    # Total calls
    total_calls = db.scalar(select(func.count(Call.id)))
    
    # Completed calls
    completed_calls = db.scalar(
        select(func.count(Call.id)).where(Call.status == "completed")
    )
    
    # Active follow-ups
    active_followups = db.scalar(
        select(func.count(Followup.id)).where(Followup.status == "pending")
    )
    
    # Recent activity - last 5 leads created
    recent_leads_query = (
        select(Lead.id, Lead.name, Lead.email, Lead.created_at)
        .order_by(Lead.created_at.desc())
        .limit(5)
    )
    recent_leads = db.execute(recent_leads_query).all()
    
    # Calls over time (last 7 days data structure)
    # Simple placeholder for now
    calls_over_time = {
        "labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
        "data": [0, 0, 0, 0, 0, 0, 0],
    }
    
    # Sentiment distribution
    sentiment_query = (
        select(Lead.sentiment, func.count(Lead.id))
        .group_by(Lead.sentiment)
    )
    sentiment_results = db.execute(sentiment_query).all()
    sentiment_distribution = {sentiment: count for sentiment, count in sentiment_results}
    
    return {
        "total_leads": total_leads or 0,
        "leads_by_status": leads_by_status,
        "leads_by_interest": leads_by_interest,
        "total_calls": total_calls or 0,
        "completed_calls": completed_calls or 0,
        "active_followups": active_followups or 0,
        "recent_leads": [
            {
                "id": str(lead.id),
                "name": lead.name,
                "email": lead.email,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            }
            for lead in recent_leads
        ],
        "calls_over_time": calls_over_time,
        "sentiment_distribution": sentiment_distribution,
    }