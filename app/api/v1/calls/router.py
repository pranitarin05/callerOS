import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.models import Call, CallSummary, Lead, Transcript
from app.schemas.call import CallInitiateRequest, CallInitiateResponse, CallingConfigResponse
from app.schemas.qualification import (
    CallCreate,
    CallInsightsResponse,
    CallResponse,
    QualificationOutput,
)
from app.services.calling_service import (
    calling_config,
    initiate_call,
    refresh_call_status,
    sync_call_from_provider,
)

router = APIRouter(tags=["calls"])
public_router = APIRouter(tags=["calls"])


def _response(call: Call) -> CallResponse:
    response = CallResponse.model_validate(call, from_attributes=True)
    if call.summary and call.summary.sentiment:
        response.sentiment = call.summary.sentiment
    elif call.qualification_json:
        try:
            response.sentiment = json.loads(call.qualification_json).get("sentiment")
        except (TypeError, ValueError):
            pass
    return response


async def initiate_endpoint(
    payload: CallInitiateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    result = await initiate_call(
        db=db,
        user_id=user_id,
        phone_number=payload.phone_number,
        lead_id=payload.lead_id,
        name=payload.name,
        mode=payload.mode,
    )
    return CallInitiateResponse(**result)


async def config_endpoint():
    return CallingConfigResponse(**calling_config())


public_router.add_api_route(
    "/initiate",
    initiate_endpoint,
    methods=["POST"],
    response_model=CallInitiateResponse,
    summary="Initiate an ElevenLabs + Exotel outbound call",
)
public_router.add_api_route(
    "/config",
    config_endpoint,
    methods=["GET"],
    response_model=CallingConfigResponse,
    summary="Calling provider configuration status",
)


@router.post("/initiate", response_model=CallInitiateResponse)
async def initiate_v1(
    payload: CallInitiateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return await initiate_endpoint(payload, user_id, db)


@router.get("/config", response_model=CallingConfigResponse)
async def config_v1():
    return await config_endpoint()


@router.post("/outbound", response_model=CallInitiateResponse)
async def outbound_call(
    payload: CallCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return await initiate_endpoint(
        CallInitiateRequest(
            lead_id=payload.lead_id,
            phone_number=payload.phone_number or "",
            mode=payload.mode,
        ),
        user_id,
        db,
    )


@router.get("", response_model=List[CallResponse])
@router.get("/", response_model=List[CallResponse])
async def list_calls(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    calls = (
        db.query(Call)
        .join(Lead)
        .filter(Lead.owner_id == user_id)
        .order_by(Call.created_at.desc())
        .all()
    )
    return [_response(call) for call in calls]


@router.get("/{call_id}/insights", response_model=CallInsightsResponse)
async def get_call_insights(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    call = (
        db.query(Call)
        .join(Lead)
        .filter(Call.id == call_id, Lead.owner_id == user_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if call.conversation_id and call.status not in {"completed", "failed"}:
        try:
            await refresh_call_status(call, db)
        except Exception:
            pass

    transcript = db.query(Transcript).filter(Transcript.call_id == call_id).first()
    summary = db.query(CallSummary).filter(CallSummary.call_id == call_id).first()

    qualification = None
    if call.qualification_json:
        import json

        try:
            qualification = QualificationOutput(**json.loads(call.qualification_json))
        except (ValueError, TypeError):
            qualification = None
    if not qualification and summary:
        qualification = QualificationOutput(
            lead_status=(db.query(Lead).filter(Lead.id == call.lead_id).first().status if call.lead_id else "new"),
            interest=summary.interest,
            requirements=summary.requirements or "",
            sentiment=summary.sentiment,
            call_outcome=summary.call_outcome or "unknown",
            next_action=summary.next_action or "",
        )

    return CallInsightsResponse(
        call=_response(call),
        live_transcript=call.live_transcript,
        transcript=transcript,
        summary=summary,
        qualification=qualification,
    )


@router.post("/{call_id}/sync", response_model=dict)
async def sync_call(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    call = (
        db.query(Call)
        .join(Lead)
        .filter(Call.id == call_id, Lead.owner_id == user_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return await sync_call_from_provider(call_id, db)


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    call = (
        db.query(Call)
        .join(Lead)
        .filter(Call.id == call_id, Lead.owner_id == user_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return _response(call)
