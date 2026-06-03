"""Supabase client factory. Uses service role key (bypasses RLS)."""
from functools import lru_cache
from supabase import AsyncClient, Client, acreate_client, create_client
from config import settings


@lru_cache(maxsize=1)
def get_sync_db() -> Client:
    """Synchronous client for Celery workers."""
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def get_db() -> AsyncClient:
    """Async client for FastAPI dependency injection."""
    return await acreate_client(settings.supabase_url, settings.supabase_service_key)
