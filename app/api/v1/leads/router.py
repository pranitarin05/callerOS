from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate
from app.services.lead_service import LeadService
from app.services.memory_service import memory_to_dict, get_memory

router = APIRouter(tags=["leads"])


def _response(lead) -> LeadResponse:
    return LeadResponse.model_validate(lead, from_attributes=True)


@router.post("", response_model=LeadResponse, status_code=201)
@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(
    payload: LeadCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead = LeadService.create_lead(
        db=db,
        owner_id=user_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        company=payload.company,
        source=payload.source,
        notes=payload.notes,
        preferred_language=payload.preferred_language,
    )
    return _response(lead)


@router.get("", response_model=List[LeadResponse])
@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    search: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    leads = LeadService.list_leads(
        db,
        owner_id=user_id,
        skip=skip,
        limit=limit,
        status_filter=status,
        search=search,
    )
    return [_response(lead) for lead in leads]


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return _response(lead)


@router.get("/{lead_id}/memory")
async def get_lead_memory(
    lead_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead = LeadService.get_lead_details(lead_id, db)
    if not lead or str(lead.owner_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return memory_to_dict(get_memory(db, lead_id))


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    lead = LeadService.update_lead_fields(
        lead_id,
        payload.model_dump(exclude_unset=True),
        user_id,
        db,
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _response(lead)


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not LeadService.delete_lead(lead_id, user_id, db):
        raise HTTPException(status_code=404, detail="Lead not found")
    return None
