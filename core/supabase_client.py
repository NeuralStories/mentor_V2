from supabase import create_client, Client
from core.config import settings

_client: Client = None
_admin_client: Client = None


def get_supabase() -> Client | None:
    """Cliente Supabase con anon key (para operaciones normales)."""
    global _client
    if not settings.supabase_enabled:
        return None
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


def get_supabase_admin() -> Client | None:
    """Cliente Supabase con service key (para operaciones admin)."""
    global _admin_client
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        return None
    if _admin_client is None:
        _admin_client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_KEY
        )
    return _admin_client
