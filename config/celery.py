import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / "deploy" / "configs" / ".env"
load_dotenv(dotenv_path=env_path)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev")
)

app = Celery("MiniTieba")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "refresh_forum_member_counts_daily": {
        "task": "apps.forum.tasks.refresh_forum_member_counts",
        "schedule": crontab(minute=0, hour=2),  # 每天2点执行
    },
}

"""
 celery -A config.celery worker -l info -P solo
 celery -A config.celery beat -l info -P solo
"""
