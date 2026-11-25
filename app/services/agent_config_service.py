"""Per-user agent script configuration sent as ElevenLabs conversation overrides."""

from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AgentConfig

ALLOWED_LANGUAGES = {"auto", "en", "hi"}


def _active_config(db: Session, owner_id: str) -> Optional[AgentConfig]:
    return (
        db.query(AgentConfig)
        .filter(
            AgentConfig.owner_id == owner_id,
            AgentConfig.is_active.is_(True),
        )
        .order_by(AgentConfig.created_at.desc())
        .first()
    )


def get_override(db: Session, owner_id: str) -> Optional[Dict[str, Any]]:
    config = _active_config(db, owner_id)
    if not config:
        return None

    agent: Dict[str, Any] = {}
    if config.instructions and config.instructions.strip():
        agent["prompt"] = {"prompt": config.instructions.strip()}
    if config.first_message and config.first_message.strip():
        agent["first_message"] = config.first_message.strip()
    if config.language in {"en", "hi"}:
        agent["language"] = config.language
    return {"agent": agent} if agent else None


async def fetch_elevenlabs_defaults() -> Dict[str, str]:
    defaults = {"instructions": "", "first_message": "", "language": "auto"}
    if not settings.elevenlabs_api_key or not settings.web_agent_id:
        return defaults
    url = f"{settings.elevenlabs_api_base_url}/v1/convai/agents/{settings.web_agent_id}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                headers={"xi-api-key": settings.elevenlabs_api_key},
            )
        if response.status_code != 200:
            return defaults
        data = response.json()
        agent = (data.get("conversation_config") or {}).get("agent") or {}
        prompt = agent.get("prompt") or {}
        defaults["instructions"] = str(prompt.get("prompt") or "")
        defaults["first_message"] = str(agent.get("first_message") or "")
        defaults["language"] = str(agent.get("language") or "en")
    except Exception:
        return defaults
    return defaults


async def get_config(db: Session, owner_id: str) -> Dict[str, Any]:
    config = _active_config(db, owner_id)
    defaults = await fetch_elevenlabs_defaults()
    return {
        "instructions": config.instructions if config else "",
        "first_message": (config.first_message or "") if config else "",
        "language": (config.language or "auto") if config else "auto",
        "customized": bool(config),
        "defaults": defaults,
    }


def save_config(
    db: Session,
    owner_id: str,
    instructions: str,
    first_message: str,
    language: str,
) -> Dict[str, Any]:
    config = _active_config(db, owner_id)
    if not config:
        config = AgentConfig(
            id=str(__import__("uuid").uuid4()),
            name="Custom agent script",
            owner_id=owner_id,
            instructions="",
            first_message="",
            language="auto",
            is_active=True,
        )
        db.add(config)
    config.instructions = instructions
    config.first_message = first_message
    config.language = language if language in ALLOWED_LANGUAGES else "auto"
    config.is_active = True
    db.commit()
    db.refresh(config)
    return {
        "instructions": config.instructions,
        "first_message": config.first_message or "",
        "language": config.language,
        "customized": True,
    }


def reset_config(db: Session, owner_id: str) -> bool:
    configs = (
        db.query(AgentConfig)
        .filter(AgentConfig.owner_id == owner_id, AgentConfig.is_active.is_(True))
        .all()
    )
    if not configs:
        return False
    for config in configs:
        db.delete(config)
    db.commit()
    return True
