from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1.leads.router import router as leads_router
from .api.v1.analytics.router import router as analytics_router
from .api.v1.conversations.router import router as conversations_router
from .api.v1.vapi.router import router as vapi_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI CallerOS - AI Voice Agent + CRM SaaS",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routers
app.include_router(leads_router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(conversations_router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(vapi_router, prefix="/api/v1/vapi", tags=["vapi"])


@app.get("/")
async def root():
    return {"message": "AI CallerOS Backend is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}