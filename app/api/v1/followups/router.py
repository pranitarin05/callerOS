from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.models import Followup
from app.schemas.qualification import FollowupCreate, FollowupResponse
from app.services.lead_service import LeadService
from app.tools import schedule_followup

router = APIRouter(tags=["followups"])


class FollowupUpdate(BaseModel):
    status: str


def _response(item: Followup) -> FollowupResponse:
    return FollowupResponse.model_validate(item, from_attributes=True)


@router.post("", response_model=FollowupResponse, status_code=201)
@router.post("/", response_model=FollowupResponse, status_code=201)
async def create_followup(
    payload: FollowupCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    result = schedule_followup(payload.lead_id, payload.scheduled_at, user_id, db)
    if not result:
        raise HTTPException(status_code=400, detail="Invalid lead, owner, or scheduled_at")
    item = db.get(Followup, result["id"])
    return _response(item)


@router.get("", response_model=List[FollowupResponse])
@router.get("/", response_model=List[FollowupResponse])
async def list_followups(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    items = db.query(Followup).filter(Followup.user_id == user_id).order_by(Followup.scheduled_at.asc()).all()
    return [_response(item) for item in items]


@router.patch("/{followup_id}", response_model=FollowupResponse)
async def update_followup(
    followup_id: str,
    payload: FollowupUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    item = db.get(Followup, followup_id)
    if not item or str(item.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Follow-up not found")
    if payload.status not in {"pending", "completed", "cancelled"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return _response(item)
