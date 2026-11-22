"""Service layer for lead business logic.

Keep business logic outside route handlers. This layer handles:
- Ownership enforcement
- CRUD operations with validation
- Business rules and invariants
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, update as sql_update, delete as sql_delete
from typing import Optional, List, Dict, Any
from uuid import UUID

from ...models import Lead, Followup


class LeadService:
    """Service layer for lead business logic - keeps business logic outside route handlers."""
    
    @staticmethod
    def get_lead_details(lead_id: str, db: Session) -> Optional[Lead]:
        """Get lead details by ID."""
        stmt = select(Lead).where(Lead.id == lead_id)
        result = db.execute(stmt)
        lead = result.scalar_one_or_none()
        return lead
    
    @staticmethod
    def create_lead(
        name: str,
        email: str,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        owner_id: str = "",
        source: Optional[str] = None,
    ) -> Optional[Lead]:
        """Create a new lead with validation."""
        # Validate required fields
        if not name or not name.strip():
            return None
        
        if not email or not email.strip():
            return None
        
        # Validate email format basic check
        if "@" not in email:
            return None
        
        # Check if lead with same email already exists for this user
        stmt = select(Lead).where(Lead.email == email)
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            return None  # Lead with same email already exists
        
        # Create new lead
        from uuid import uuid4
        
        lead = Lead(
            id=str(uuid4()),
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip() if phone else None,
            company=company.strip() if company else None,
            status="new",
            interest_level="low",
            source=source,
            owner_id=owner_id,
        )
        
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        return lead
    
    @staticmethod
    def list_leads(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> List[Lead]:
        """List leads with optional filtering and ownership."""
        stmt = select(Lead).offset(skip).limit(limit)
        
        if status_filter:
            stmt = stmt.where(Lead.status == status_filter)
        
        if owner_id:
            stmt = stmt.where(Lead.owner_id == owner_id)
        
        # Order by creation date, newest first
        stmt = stmt.order_by(Lead.created_at.desc())
        
        result = db.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def update_lead_fields(
        lead_id: str,
        updates: Dict[str, Any],
        owner_id: str,
        db: Session,
    ) -> Optional[Lead]:
        """Update lead fields with ownership enforcement.
        
        Only allowed fields are updated to prevent mass-assignment vulnerabilities.
        """
        # First verify lead exists and user owns it
        lead = LeadService.get_lead_details(lead_id, db)
        if not lead or str(lead.owner_id) != str(owner_id):
            return None
        
        # Whitelist of updatable fields
        allowed_fields = {
            "name", "email", "phone", "company", "status",
            "interest_level", "requirements", "sentiment",
            "call_outcome", "next_action", "notes", "source"
        }
        
        # Filter to only allowed fields
        filtered_updates = {
            k: v for k, v in updates.items() 
            if k in allowed_fields and v is not None
        }
        
        if not filtered_updates:
            return lead  # No valid updates provided
        
        # Apply updates
        for field, value in filtered_updates.items():
            setattr(lead, field, value)
        
        lead.updated_at = func.now()
        db.commit()
        db.refresh(lead)
        
        return lead
    
    @staticmethod
    def delete_lead(lead_id: str, owner_id: str, db: Session) -> bool:
        """Delete a lead with ownership enforcement."""
        lead = LeadService.get_lead_details(lead_id, db)
        if not lead or str(lead.owner_id) != str(owner_id):
            return False  # Don't reveal if lead exists or not
        
        stmt = sql_delete(Lead).where(Lead.id == lead_id)
        db.execute(stmt)
        db.commit()
        
        return True
    
    @staticmethod
    def get_leads_by_status(
        db: Session,
        status: str,
        owner_id: Optional[str] = None,
    ) -> List[Lead]:
        """Get leads filtered by status."""
        stmt = select(Lead).where(Lead.status == status)
        
        if owner_id:
            stmt = stmt.where(Lead.owner_id == owner_id)
        
        stmt = stmt.order_by(Lead.created_at.desc())
        
        result = db.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def get_leads_by_interest(
        db: Session,
        interest_level: str,
        owner_id: Optional[str] = None,
    ) -> List[Lead]:
        """Get leads filtered by interest level."""
        stmt = select(Lead).where(Lead.interest_level == interest_level)
        
        if owner_id:
            stmt = stmt.where(Lead.owner_id == owner_id)
        
        stmt = stmt.order_by(Lead.created_at.desc())
        
        result = db.execute(stmt)
        return list(result.scalars().all())