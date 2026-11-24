from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.models import Call, Followup, Lead

router = APIRouter(tags=["analytics"])


def _metrics(user_id: str, db: Session) -> dict:
    leads = list(db.scalars(select(Lead).where(Lead.owner_id == user_id)).all())
    calls = list(db.scalars(select(Call).join(Lead).where(Lead.owner_id == user_id)).all())
    followups = list(db.scalars(select(Followup).where(Followup.user_id == user_id)).all())

    status_counts = Counter(lead.status for lead in leads)
    interest_counts = Counter(lead.interest_level for lead in leads)
    sentiment_counts = Counter(lead.sentiment for lead in leads)

    recent = sorted(leads, key=lambda lead: lead.created_at or 0, reverse=True)[:5]

    return {
        "total_leads": len(leads),
        "leads_by_status": dict(status_counts),
        "leads_by_interest": dict(interest_counts),
        "total_calls": len(calls),
        "completed_calls": sum(1 for call in calls if call.status == "completed"),
        "active_followups": sum(1 for followup in followups if followup.status == "pending"),
        "recent_leads": [
            {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "status": lead.status,
                "interest_level": lead.interest_level,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            }
            for lead in recent
        ],
        "calls_over_time": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "data": [0, 0, 0, 0, 0, 0, 0],
        },
        "sentiment_distribution": dict(sentiment_counts),
    }


@router.get("/dashboard")
@router.get("")
@router.get("/")
async def dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _metrics(user_id, db)
