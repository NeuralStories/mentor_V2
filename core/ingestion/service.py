"""
Fábrica singleton del IngestionStore.
"""
from functools import lru_cache
import logging

from core.config import settings
from core.supabase_client import get_supabase_admin

from .store import IngestionStore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_store() -> IngestionStore:
    supabase = get_supabase_admin()
    if not supabase:
        logger.info("IngestionStore en modo local: sin réplica a Supabase")
    return IngestionStore(settings.INGESTION_DB_PATH, supabase=supabase)
