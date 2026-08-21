from celery import Celery
from app.core.config import settings


celery_app = Celery(
    "task_management",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.celery_tasks"]
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "auto-cancel-overdue-tasks-every-minute": {
            "task": "auto_cancel_overdue_tasks_task",
            "schedule": 60.0,
        },
    },
)