"""
Celery configuration for background tasks
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "sentiment_analysis",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-analyses": {
        "task": "app.services.tasks.cleanup_old_analyses",
        "schedule": 3600.0,  # Every hour
    },
    "warm-up-models": {
        "task": "app.services.tasks.warm_up_models",
        "schedule": 300.0,  # Every 5 minutes (keep warm)
    },
}