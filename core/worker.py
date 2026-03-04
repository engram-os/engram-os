import os
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "engram_os",
    broker=BROKER_URL,
    backend=BROKER_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.imports = ['agents.tasks']

celery_app.conf.beat_schedule = {
    'check-calendar-every-15-mins': {
        'task': 'agents.tasks.fan_out_calendar',
        'schedule': 900.0,
    },
    'check-email-every-hour': {
        'task': 'agents.tasks.fan_out_email',
        'schedule': 3600.0,
    },
}