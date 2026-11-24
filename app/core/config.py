import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    project_name: str = os.getenv("PROJECT_NAME", "AI CallerOS")
    api_v1_str: str = os.getenv("API_V1_STR", "/api/v1")

    # Groq: kept for qualification / analysis / CRM insights
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_api_keys: list = [
        key.strip()
        for key in [
            os.getenv("GROQ_API_KEY", ""),
            os.getenv("GROQ_API_KEY_BACKUP_1", ""),
            os.getenv("GROQ_API_KEY_BACKUP_2", ""),
        ]
        if key.strip()
    ]
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # ElevenLabs Conversational AI + Exotel telephony
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_agent_id: str = os.getenv("ELEVENLABS_AGENT_ID", "")
    elevenlabs_phone_number_id: str = os.getenv("ELEVENLABS_PHONE_NUMBER_ID", "")
    elevenlabs_webhook_secret: str = os.getenv("ELEVENLABS_WEBHOOK_SECRET", "")
    elevenlabs_webhook_url: str = os.getenv("ELEVENLABS_WEBHOOK_URL", "")
    elevenlabs_api_base_url: str = os.getenv(
        "ELEVENLABS_API_BASE_URL", "https://api.elevenlabs.io"
    ).rstrip("/")
    elevenlabs_agent_name: str = os.getenv(
        "ELEVENLABS_AGENT_NAME", "Student Project Demo Qualifier"
    )

    exotel_account_sid: str = os.getenv("EXOTEL_ACCOUNT_SID", "")
    exotel_api_key: str = os.getenv("EXOTEL_API_KEY", "")
    exotel_api_token: str = os.getenv("EXOTEL_API_TOKEN", "")
    exotel_phone_number: str = os.getenv("EXOTEL_PHONE_NUMBER", "")
    exotel_region: str = os.getenv("EXOTEL_REGION", "api.in.exotel.com")

    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    call_mode: str = os.getenv("CALL_MODE", "demo").lower()

    @property
    def database_url(self) -> str:
        explicit = os.getenv("DATABASE_URL", "").strip()
        if explicit:
            return explicit
        return os.getenv("LOCAL_DATABASE_URL", "sqlite:///./calleros.db").strip()

    @property
    def cors_origins(self) -> list:
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]

    @property
    def is_demo_mode(self) -> bool:
        return self.call_mode != "live"

    @property
    def live_call_ready(self) -> bool:
        return bool(
            self.elevenlabs_api_key
            and self.elevenlabs_agent_id
            and self.elevenlabs_phone_number_id
        )


settings = Settings()
