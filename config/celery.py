import os
from celery import Celery
from dotenv import load_dotenv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / "deploy" / "configs" / ".env"
load_dotenv(dotenv_path=env_path)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev")
)

app = Celery("MiniTieba", broker=os.getenv("CELERY_BROKER_URL"))
app.autodiscover_tasks()

"""
 celery -A config.celery worker -l info -P solo
"""
