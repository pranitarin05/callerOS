from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.agent_config.router import router as agent_config_router
from app.api.v1.analytics.router import router as analytics_router
from app.api.v1.appointments.router import router as appointments_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.calls.router import public_router as public_calls_router
from app.api.v1.calls.router import router as calls_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.followups.router import router as followups_router
from app.api.v1.knowledge.router import router as knowledge_router
from app.api.v1.leads.router import router as leads_router
from app.api.v1.voice.router import router as voice_router
from app.api.v1.webhooks.router import public_router as public_webhooks_router
from app.api.v1.webhooks.router import router as webhooks_router
from app.api.v1.webhooks.tools.router import public_router as public_agent_tools_router
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="AI CallerOS - AI Voice Agent + CRM SaaS (ElevenLabs + Exotel)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(leads_router, prefix="/api/v1/leads")
app.include_router(calls_router, prefix="/api/v1/calls")
app.include_router(public_calls_router, prefix="/api/calls")
app.include_router(followups_router, prefix="/api/v1/followups")
app.include_router(knowledge_router, prefix="/api/v1/knowledge")
app.include_router(appointments_router, prefix="/api/v1/appointments")
app.include_router(agent_config_router, prefix="/api/v1/agent-config")
app.include_router(analytics_router, prefix="/api/v1/analytics")
app.include_router(conversations_router, prefix="/api/v1/conversations")
app.include_router(voice_router, prefix="/api/v1/voice")
app.include_router(webhooks_router, prefix="/api/v1/webhooks")
app.include_router(public_webhooks_router, prefix="/api/webhooks")
app.include_router(public_agent_tools_router, prefix="/api/webhooks/elevenlabs")


@app.get("/")
async def root():
    return {"message": "AI CallerOS backend is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
