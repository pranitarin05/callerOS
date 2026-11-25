"""Protected endpoint that lets the ElevenLabs agent call our validated backend tools."""

import hmac
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import DEMO_USER_ID, SessionLocal
from app.services import rag_service
from app.tools import (
    book_appointment,
    end_call,
    get_available_slots,
    get_lead_details,
    schedule_followup,
    search_company_knowledge,
    update_lead,
)

router = APIRouter(tags=["agent-tools"])
public_router = APIRouter(tags=["agent-tools"])
logger = logging.getLogger(__name__)

TOOL_NAMES = {
    "get_lead_details",
    "update_lead",
    "search_company_knowledge",
    "search_knowledge",
    "schedule_followup",
    "book_appointment",
    "get_available_slots",
    "end_call",
}


def _authorize(secret: str | None) -> None:
    if not settings.elevenlabs_tool_secret:
        raise HTTPException(status_code=503, detail="ELEVENLABS_TOOL_SECRET is not configured")
    if not secret or not hmac.compare_digest(secret, settings.elevenlabs_tool_secret):
        raise HTTPException(status_code=401, detail="Invalid tool secret")


def _extract(payload: Dict[str, Any]) -> tuple:
    call = payload.get("tool_call") if isinstance(payload.get("tool_call"), dict) else payload
    function = call.get("function") if isinstance(call.get("function"), dict) else {}
    name = (
        call.get("name")
        or call.get("tool_name")
        or function.get("name")
        or payload.get("name")
        or ""
    )
    arguments = (
        call.get("arguments")
        or call.get("args")
        or call.get("parameters")
        or function.get("arguments")
        or payload.get("arguments")
        or {}
    )
    if isinstance(arguments, str):
        import json

        try:
            arguments = json.loads(arguments)
        except ValueError:
            arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    if str(name) not in TOOL_NAMES:
        found = _find_known_name(payload)
        if found:
            name = found
    return str(name), arguments


def _find_known_name(value) -> Optional[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"name", "tool_name", "function_name"} and str(item) in TOOL_NAMES:
                return str(item)
            found = _find_known_name(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_known_name(item)
            if found:
                return found
    return None


def _user_id(payload: Dict[str, Any], arguments: Dict[str, Any]) -> str:
    dynamic = payload.get("dynamic_variables") if isinstance(payload.get("dynamic_variables"), dict) else {}
    init = (
        payload.get("conversation_initiation_client_data")
        if isinstance(payload.get("conversation_initiation_client_data"), dict)
        else {}
    )
    init_dynamic = init.get("dynamic_variables") if isinstance(init.get("dynamic_variables"), dict) else {}
    return str(
        arguments.get("crm_user_id")
        or dynamic.get("crm_user_id")
        or init_dynamic.get("crm_user_id")
        or payload.get("user_id")
        or DEMO_USER_ID
    )


def _dispatch(name: str, args: Dict[str, Any], user_id: str, db: Session) -> Any:
    if name == "get_lead_details":
        return get_lead_details(str(args.get("lead_id") or ""), user_id, db)
    if name == "update_lead":
        updates = args.get("updates") if isinstance(args.get("updates"), dict) else args
        return update_lead(str(args.get("lead_id") or ""), updates, user_id, db)
    if name in {"search_company_knowledge", "search_knowledge"}:
        return search_company_knowledge(str(args.get("query") or ""), user_id, db)
    if name == "schedule_followup":
        return schedule_followup(
            str(args.get("lead_id") or ""),
            str(args.get("scheduled_at") or ""),
            user_id,
            db,
        )
    if name in {"book_appointment", "get_available_slots"}:
        if name == "get_available_slots":
            return get_available_slots(user_id, db, days=int(args.get("days") or 3))
        return book_appointment(
            str(args.get("lead_id") or ""),
            str(args.get("scheduled_at") or ""),
            user_id,
            db,
            title=str(args.get("title") or "Product demo"),
            notes=str(args.get("notes") or ""),
        )
    if name == "end_call":
        return end_call(str(args.get("call_id") or ""), str(args.get("outcome") or ""), db)
    raise HTTPException(status_code=400, detail=f"Unknown tool: {name}")


async def receive(
    request: Request,
    x_elevenlabs_tool_secret: str | None = Header(default=None, alias="X-ElevenLabs-Tool-Secret"),
    x_tool_secret: str | None = Header(default=None, alias="X-Tool-Secret"),
):
    _authorize(x_elevenlabs_tool_secret or x_tool_secret)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be an object")

    name, arguments = _extract(payload)
    user_id = _user_id(payload, arguments)
    db = SessionLocal()
    try:
        result = _dispatch(name, arguments, user_id, db)
        return {"status": "ok", "tool": name, "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Agent tool %s failed: %s", name, type(exc).__name__)
        raise HTTPException(status_code=500, detail="Tool execution failed") from None
    finally:
        db.close()


router.add_api_route("/tools", receive, methods=["POST"])
public_router.add_api_route("/tools", receive, methods=["POST"])
