import logging
from supabase import create_client, Client
from .config import settings

logger = logging.getLogger(__name__)

_supabase_client: Client = None  # type: ignore

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured")
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
    return _supabase_client

# For module-level access, use get_supabase_client()
class SupabaseProxy:
    def __getattr__(self, name):
        return getattr(get_supabase_client(), name)

supabase_client = SupabaseProxy()