from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.models import Appointment, Call, CallSummary, Followup, Lead

router = APIRouter(tags=["analytics"])


def _calls_over_time(calls: list) -> dict:
    today = datetime.utcnow().date()
    labels = [(today - timedelta(days=offset)).strftime("%a") for offset in range(6, -1, -1)]
    counts = {label: 0 for label in labels}
    for call in calls:
        moment = call.started_at or call.created_at
        if not moment:
            continue
        label = moment.date().strftime("%a")
        if label in counts:
            counts[label] += 1
    return {"labels": labels, "data": [counts[label] for label in labels]}


def _metrics(user_id: str, db: Session) -> dict:
    leads = list(db.scalars(select(Lead).where(Lead.owner_id == user_id)).all())
    calls = list(db.scalars(select(Call).join(Lead).where(Lead.owner_id == user_id)).all())
    followups = list(db.scalars(select(Followup).where(Followup.user_id == user_id)).all())

    status_counts = Counter(lead.status for lead in leads)
    interest_counts = Counter(lead.interest_level for lead in leads)
    sentiment_counts = Counter(lead.sentiment for lead in leads)

    recent = sorted(leads, key=lambda lead: lead.created_at or datetime.min, reverse=True)[:5]

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
        "calls_over_time": _calls_over_time(calls),
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


@router.get("/insights")
async def insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    metrics = _metrics(user_id, db)
    leads = list(db.scalars(select(Lead).where(Lead.owner_id == user_id)).all())
    calls = list(db.scalars(select(Call).join(Lead).where(Lead.owner_id == user_id)).all())
    summaries = list(
        db.scalars(
            select(CallSummary).join(Call).join(Lead).where(Lead.owner_id == user_id)
        ).all()
    )
    appointments = list(
        db.scalars(select(Appointment).where(Appointment.user_id == user_id)).all()
    )

    qualified = sum(
        1
        for lead in leads
        if (lead.status or "").lower() in {"qualified", "interested"}
    )
    durations = [call.duration_seconds for call in calls if call.duration_seconds]
    outcomes = Counter(call.call_outcome or "unknown" for call in calls)
    requirements = Counter(
        summary.requirements for summary in summaries if summary.requirements
    )
    languages = Counter(call.language or "en" for call in calls)

    metrics.update(
        {
            "conversion_rate": round(qualified / len(leads), 4) if leads else 0.0,
            "avg_call_duration_seconds": (
                round(sum(durations) / len(durations), 1) if durations else 0
            ),
            "outcomes_breakdown": dict(outcomes),
            "top_requirements": [
                {"label": label, "count": count}
                for label, count in requirements.most_common(5)
            ],
            "languages_breakdown": dict(languages),
            "appointments_scheduled": sum(
                1 for item in appointments if item.status in {"scheduled", "confirmed"}
            ),
        }
    )
    return metrics
