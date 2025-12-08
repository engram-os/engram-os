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
        'task': 'agents.tasks.run_calendar_agent',
        'schedule': 900.0,
    },
    'check-email-every-hour': {
        'task': 'agents.tasks.run_email_agent',
        'schedule': 3600.0,
    },
}