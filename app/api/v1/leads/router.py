from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_
from typing import List, Optional

from ...db.session import get_db
from ...models import Lead, Profile
from ...schemas.lead import LeadCreate, LeadUpdate, LeadInDB, LeadResponse


router = APIRouter(prefix="/v1/leads", tags=["leads"])


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
):
    """Create a new lead."""
    # Check if lead with same email already exists for this user
    stmt = select(Lead).where(Lead.email == lead_data.email)
    existing = db.scalar(stmt)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists",
        )
    
    # Associate with authenticated user (owner_id from context)
    # In production, this would come from auth middleware
    from uuid import uuid4
    owner_id = str(uuid4())
    
    new_lead = Lead(
        id=str(uuid4()),
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
        company=lead_data.company,
        status="new",
        interest_level="low",
        requirements=lead_data.requirements,
        sentiment="neutral",
        call_outcome=None,
        next_action=None,
        source=lead_data.source,
        notes=lead_data.notes,
        owner_id=owner_id,
    )
    
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    return LeadResponse(
        id=new_lead.id,
        name=new_lead.name,
        email=new_lead.email,
        phone=new_lead.phone,
        company=new_lead.company,
        status=new_lead.status,
        interest_level=new_lead.interest_level,
        requirements=new_lead.requirements,
        sentiment=new_lead.sentiment,
        call_outcome=new_lead.call_outcome,
        next_action=new_lead.next_action,
        source=new_lead.source,
        notes=new_lead.notes,
        owner_id=new_lead.owner_id,
        created_at=new_lead.created_at,
        updated_at=new_lead.updated_at,
    )


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List leads with optional filtering."""
    stmt = select(Lead).offset(skip).limit(limit)
    
    if status_filter:
        stmt = stmt.where(Lead.status == status_filter)
    
    leads = db.scalars(stmt).all()
    
    return [
        LeadResponse(
            id=lead.id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            status=lead.status,
            interest_level=lead.interest_level,
            requirements=lead.requirements,
            sentiment=lead.sentiment,
            call_outcome=lead.call_outcome,
            next_action=lead.next_action,
            source=lead.source,
            notes=lead.notes,
            owner_id=lead.owner_id,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )
        for lead in leads
    ]


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
):
    """Get a single lead by ID."""
    stmt = select(Lead).where(Lead.id == lead_id)
    lead = db.scalar(stmt)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    return LeadResponse(
        id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        status=lead.status,
        interest_level=lead.interest_level,
        requirements=lead.requirements,
        sentiment=lead.sentiment,
        call_outcome=lead.call_outcome,
        next_action=lead.next_action,
        source=lead.source,
        notes=lead.notes,
        owner_id=lead.owner_id,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db),
):
    """Update a lead."""
    stmt = select(Lead).where(Lead.id == lead_id)
    lead = db.scalar(stmt)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    # Update only provided fields
    update_dict = lead_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(lead, field, value)
    
    db.commit()
    db.refresh(lead)
    
    return LeadResponse(
        id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        status=lead.status,
        interest_level=lead.interest_level,
        requirements=lead.requirements,
        sentiment=lead.sentiment,
        call_outcome=lead.call_outcome,
        next_action=lead.next_action,
        source=lead.source,
        notes=lead.notes,
        owner_id=lead.owner_id,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )