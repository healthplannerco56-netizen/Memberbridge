"""Celery application factory."""
from celery import Celery
from config import settings

celery_app = Celery(
    "memberbridge",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,                  # Ack only after success (safer)
    worker_prefetch_multiplier=1,         # One task at a time per worker
    task_soft_time_limit=120,             # 2 min soft limit
    task_time_limit=180,                  # 3 min hard limit
    beat_schedule={},                     # Periodic tasks added in Phase 3
)
