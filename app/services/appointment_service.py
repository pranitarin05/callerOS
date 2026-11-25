"""Internal appointment scheduler with business-hours availability and conflict checks."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Appointment, Lead
from app.services.lead_service import LeadService

ACTIVE_STATUSES = {"scheduled", "confirmed", "reminder"}


def _local_timezone():
    try:
        return ZoneInfo(settings.business_timezone)
    except Exception:
        return timezone.utc


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def parse_datetime(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return _to_utc_naive(parsed)


def to_iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def appointment_to_dict(item: Appointment) -> Dict[str, Any]:
    return {
        "id": item.id,
        "lead_id": item.lead_id,
        "user_id": item.user_id,
        "scheduled_at": to_iso(item.scheduled_at),
        "duration_minutes": item.duration_minutes,
        "status": item.status,
        "title": item.title,
        "location": item.location,
        "notes": item.notes,
        "call_id": item.call_id,
        "created_at": to_iso(item.created_at),
        "updated_at": to_iso(item.updated_at),
    }


def _window_local(when_naive_utc: datetime) -> datetime:
    aware = when_naive_utc.replace(tzinfo=timezone.utc).astimezone(_local_timezone())
    return aware


def is_slot_available(
    db: Session,
    user_id: str,
    when: datetime,
    duration_minutes: Optional[int] = None,
    exclude_id: Optional[str] = None,
) -> bool:
    when = _to_utc_naive(when)
    duration = duration_minutes or settings.appointment_slot_minutes
    local_start = _window_local(when)
    local_end = _window_local(when + timedelta(minutes=duration))

    if local_start.weekday() not in settings.allowed_weekdays:
        return False
    if local_start.hour < settings.business_hours_start:
        return False
    if local_end.hour > settings.business_hours_end or (
        local_end.hour == settings.business_hours_end and local_end.minute > 0
    ):
        return False
    if when <= datetime.utcnow():
        return False

    existing = (
        db.query(Appointment)
        .filter(
            Appointment.user_id == user_id,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
        .all()
    )
    end = when + timedelta(minutes=duration)
    for item in existing:
        if exclude_id and item.id == exclude_id:
            continue
        if not item.scheduled_at:
            continue
        item_end = item.scheduled_at + timedelta(minutes=item.duration_minutes or settings.appointment_slot_minutes)
        if when < item_end and item.scheduled_at < end:
            return False
    return True


def get_available_slots(
    db: Session,
    user_id: str,
    days: int = 3,
    date_str: Optional[str] = None,
) -> List[str]:
    tz = _local_timezone()
    if date_str:
        try:
            start_day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return []
    else:
        start_day = datetime.now(tz).date() + timedelta(days=1)

    slot = settings.appointment_slot_minutes
    slots: List[str] = []
    for offset in range(max(1, days) + 1):
        day = start_day + timedelta(days=offset)
        if day.weekday() not in settings.allowed_weekdays:
            continue
        for hour in range(settings.business_hours_start, settings.business_hours_end):
            for minute in range(0, 60, slot):
                local = datetime(
                    day.year, day.month, day.day, hour, minute, tzinfo=tz
                )
                utc_naive = local.astimezone(timezone.utc).replace(tzinfo=None)
                if is_slot_available(db, user_id, utc_naive, slot):
                    slots.append(utc_naive.isoformat())
        if len(slots) >= 12:
            break
    return slots[:12]


def book_appointment(
    db: Session,
    user_id: str,
    lead_id: str,
    scheduled_at: str,
    duration_minutes: Optional[int] = None,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    location: Optional[str] = None,
    call_id: Optional[str] = None,
    allow_outside_hours: bool = False,
) -> Optional[Dict[str, Any]]:
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(user_id):
        return None
    when = parse_datetime(scheduled_at)
    if not when:
        return None
    duration = duration_minutes or settings.appointment_slot_minutes
    if not allow_outside_hours and not is_slot_available(db, user_id, when, duration):
        return None

    item = Appointment(
        id=str(uuid4()),
        lead_id=lead_id,
        user_id=user_id,
        scheduled_at=when,
        duration_minutes=duration,
        status="scheduled",
        title=(title or "Product demo").strip(),
        notes=notes,
        location=location,
        call_id=call_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return appointment_to_dict(item)


def list_appointments(db: Session, user_id: str) -> List[Appointment]:
    return (
        db.query(Appointment)
        .filter(Appointment.user_id == user_id)
        .order_by(Appointment.scheduled_at.asc())
        .all()
    )


def update_appointment(
    db: Session,
    user_id: str,
    appointment_id: str,
    scheduled_at: Optional[str] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[Appointment]:
    item = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.user_id == user_id,
        )
        .first()
    )
    if not item:
        return None
    if status is not None:
        if status not in {"scheduled", "confirmed", "completed", "cancelled", "no_show"}:
            raise HTTPException(status_code=400, detail="Invalid appointment status")
        item.status = status
    if notes is not None:
        item.notes = notes
    if scheduled_at is not None:
        when = parse_datetime(scheduled_at)
        if not when or not is_slot_available(
            db, user_id, when, item.duration_minutes, exclude_id=item.id
        ):
            raise HTTPException(status_code=400, detail="Slot is unavailable")
        item.scheduled_at = when
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item


def next_fallback_time(db: Session, user_id: str) -> Optional[datetime]:
    slots = get_available_slots(db, user_id, days=2)
    if slots:
        return parse_datetime(slots[0])
    return datetime.utcnow() + timedelta(days=1)
