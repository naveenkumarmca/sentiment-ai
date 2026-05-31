# app/tasks.py
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task
def process_job(job_id: str):
    # import here to avoid circular imports
    from app.main import process_job_sync
    import asyncio
    asyncio.run(process_job_sync(job_id))