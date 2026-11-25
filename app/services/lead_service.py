from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lead


ALLOWED_UPDATE_FIELDS = {
    "name", "email", "phone", "company", "status",
    "interest_level", "requirements", "sentiment",
    "call_outcome", "next_action", "notes", "source",
    "preferred_language", "last_contact_at",
}


class LeadService:
    @staticmethod
    def get_lead_details(lead_id: str, db: Session) -> Optional[Lead]:
        return db.scalar(select(Lead).where(Lead.id == lead_id))

    @staticmethod
    def create_lead(
        db: Session,
        owner_id: str,
        name: str,
        email: str,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None,
        preferred_language: Optional[str] = None,
    ) -> Lead:
        lead = Lead(
            id=str(uuid4()),
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone,
            company=company,
            status="new",
            interest_level="low",
            sentiment="neutral",
            source=source,
            notes=notes,
            preferred_language=preferred_language or "auto",
            owner_id=owner_id,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def list_leads(
        db: Session,
        owner_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Lead]:
        stmt = select(Lead)
        if owner_id:
            stmt = stmt.where(Lead.owner_id == owner_id)
        if status_filter:
            stmt = stmt.where(Lead.status == status_filter)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(Lead.name).like(like)
                | func.lower(Lead.email).like(like)
                | func.lower(Lead.company).like(like)
            )
        stmt = stmt.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update_lead_fields(
        lead_id: str,
        updates: Dict[str, object],
        owner_id: str,
        db: Session,
    ) -> Optional[Lead]:
        lead = LeadService.get_lead_details(lead_id, db)
        if not lead:
            return None
        if owner_id and str(lead.owner_id) != str(owner_id):
            return None
        for field, value in updates.items():
            if field in ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(lead, field, value)
        lead.updated_at = func.now()
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def delete_lead(lead_id: str, owner_id: str, db: Session) -> bool:
        lead = LeadService.get_lead_details(lead_id, db)
        if not lead or str(lead.owner_id) != str(owner_id):
            return False
        db.delete(lead)
        db.commit()
        return True
