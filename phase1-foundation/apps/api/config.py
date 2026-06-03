"""App configuration — reads from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # Clerk
    clerk_secret_key: str
    clerk_webhook_secret: str = ""

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # Resend
    resend_api_key: str
    resend_from_email: str = "noreply@memberbridge.io"
    resend_from_name: str = "MemberBridge"

    # Encryption key for stored API keys (32 chars)
    encryption_key: str

    # CORS
    app_url: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.app_url]
        if self.environment == "development":
            origins += ["http://localhost:3000", "http://127.0.0.1:3000"]
        return origins


settings = Settings()
