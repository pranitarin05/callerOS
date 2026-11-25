from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.services import appointment_service

router = APIRouter(tags=["appointments"])


class AppointmentCreate(BaseModel):
    lead_id: str
    scheduled_at: str
    duration_minutes: Optional[int] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    call_id: Optional[str] = None
    allow_outside_hours: bool = False


class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.get("/slots", response_model=List[str])
async def available_slots(
    days: int = 3,
    date: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return appointment_service.get_available_slots(db, user_id, days=days, date_str=date)


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def create_appointment(
    payload: AppointmentCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    result = appointment_service.book_appointment(
        db,
        user_id=user_id,
        lead_id=payload.lead_id,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        title=payload.title,
        notes=payload.notes,
        location=payload.location,
        call_id=payload.call_id,
        allow_outside_hours=payload.allow_outside_hours,
    )
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Invalid lead, invalid time, or slot unavailable",
        )
    return result


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
async def list_appointments(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return [appointment_service.appointment_to_dict(item) for item in appointment_service.list_appointments(db, user_id)]


@router.patch("/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    item = appointment_service.update_appointment(
        db,
        user_id,
        appointment_id,
        scheduled_at=payload.scheduled_at,
        status=payload.status,
        notes=payload.notes,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment_service.appointment_to_dict(item)
