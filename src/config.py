import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    WHATSAPP_ENABLED: bool = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)

    ADMIN_USER: str = os.getenv("ADMIN_USER", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

    cors_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:8000")
    CORS_ORIGINS: list = [o.strip() for o in cors_raw.split(",") if o.strip()]

    ENV: str = os.getenv("ENV", "development")

settings = Settings()
