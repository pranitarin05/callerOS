"""Rolling per-lead conversational memory."""

import json
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.ai import summarize_memory
from app.core.config import settings
from app.models import LeadMemory

logger = logging.getLogger(__name__)


def get_memory(db: Session, lead_id: str) -> Optional[LeadMemory]:
    return db.query(LeadMemory).filter(LeadMemory.lead_id == lead_id).first()


def memory_to_dict(record: Optional[LeadMemory]) -> Dict[str, Any]:
    if not record:
        return {"summary": "", "key_facts": [], "language": "en", "updated_at": None}
    try:
        facts = json.loads(record.key_facts) if record.key_facts else []
    except (TypeError, ValueError):
        facts = []
    return {
        "summary": record.summary or "",
        "key_facts": facts,
        "language": record.language or "en",
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def get_memory_context(db: Session, lead_id: str, max_chars: Optional[int] = None) -> str:
    record = get_memory(db, lead_id)
    if not record or not record.summary:
        return ""
    limit = max_chars or settings.memory_max_chars
    return f"Previous conversation context: {record.summary[:limit]}"


async def update_memory(
    db: Session,
    lead_id: str,
    transcript: str,
    summary: str,
    qualification: Dict[str, Any],
    language: str = "en",
) -> LeadMemory:
    record = get_memory(db, lead_id)
    previous = record.summary if record else ""

    facts: Dict[str, Any] = {}
    if record and record.key_facts:
        try:
            loaded = json.loads(record.key_facts)
            if isinstance(loaded, dict):
                facts = loaded
        except (TypeError, ValueError):
            facts = {}
    for key in ("requirements", "interest", "sentiment", "call_outcome", "next_action"):
        value = qualification.get(key) if qualification else None
        if value:
            facts[key] = str(value)
    facts["language"] = language

    new_note = "\n".join(
        part
        for part in [
            summary,
            f"Requirements: {qualification.get('requirements')}" if qualification else "",
            f"Next action: {qualification.get('next_action')}" if qualification else "",
        ]
        if part
    )
    merged = await summarize_memory(previous, new_note, language)
    merged = (merged or new_note)[: settings.memory_max_chars]

    if not record:
        record = LeadMemory(
            id=str(uuid4()),
            lead_id=lead_id,
            summary=merged,
            key_facts=json.dumps(facts, ensure_ascii=False),
            language=language,
        )
        db.add(record)
    else:
        record.summary = merged
        record.key_facts = json.dumps(facts, ensure_ascii=False)
        record.language = language
    db.commit()
    db.refresh(record)
    return record
