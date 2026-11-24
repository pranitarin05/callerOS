import json
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from app.db.session import SessionLocal
from app.services.calling_service import process_webhook, verify_webhook

router = APIRouter(tags=["webhooks"])
public_router = APIRouter(tags=["webhooks"])


def _process_in_background(payload: dict) -> None:
    db = SessionLocal()
    try:
        import asyncio

        asyncio.run(process_webhook(payload, db))
    except Exception:
        # Webhook delivery must still be acknowledged; errors are logged by the service.
        pass
    finally:
        db.close()


async def receive(
    request: Request,
    background_tasks: BackgroundTasks,
    elevenlabs_signature: str | None = Header(default=None, alias="ElevenLabs-Signature"),
):
    raw = await request.body()
    event = verify_webhook(raw, elevenlabs_signature)
    background_tasks.add_task(_process_in_background, event)
    return {"status": "received", "type": event.get("type")}


router.add_api_route("/elevenlabs", receive, methods=["POST"])
public_router.add_api_route("/elevenlabs", receive, methods=["POST"])
