from supabase import create_client, Client
from core.config import settings

_client: Client = None
_admin_client: Client = None

def get_supabase() -> Client:
    """Cliente Supabase con anon key (para operaciones normales)."""
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en el .env")
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client

def get_supabase_admin() -> Client:
    """Cliente Supabase con service key (para operaciones admin)."""
    global _admin_client
    if _admin_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_KEY deben estar configurados en el .env")
        _admin_client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_KEY
        )
    return _admin_client
