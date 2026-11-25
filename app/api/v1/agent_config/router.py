from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.services import agent_config_service

router = APIRouter(tags=["agent-config"])


class AgentScriptUpdate(BaseModel):
    instructions: str = Field("", max_length=20000)
    first_message: str = Field("", max_length=4000)
    language: str = Field("auto", max_length=10)


@router.get("")
@router.get("/")
async def get_agent_script(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return await agent_config_service.get_config(db, user_id)


@router.put("")
@router.put("/")
async def save_agent_script(
    payload: AgentScriptUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    language = payload.language.strip().lower()
    if language not in agent_config_service.ALLOWED_LANGUAGES:
        raise HTTPException(status_code=400, detail="language must be auto, en, or hi")
    if not payload.instructions.strip() and not payload.first_message.strip():
        raise HTTPException(status_code=400, detail="Provide a system prompt or a first message")
    return agent_config_service.save_config(
        db,
        owner_id=user_id,
        instructions=payload.instructions.strip(),
        first_message=payload.first_message.strip(),
        language=language,
    )


@router.delete("")
@router.delete("/")
async def reset_agent_script(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, bool]:
    return {"reset": agent_config_service.reset_config(db, user_id)}
