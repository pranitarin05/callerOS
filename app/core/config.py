import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    secret_key: str = os.getenv("SECRET_KEY", "calleros-super-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    api_v1_str: str = os.getenv("API_V1_STR", "/api/v1")
    project_name: str = os.getenv("PROJECT_NAME", "AI CallerOS")
    
    @property
    def backend_cors_origins(self) -> list:
        return [origin.strip() for origin in self.supabase_url.split(",") if origin.strip()]

settings = Settings()