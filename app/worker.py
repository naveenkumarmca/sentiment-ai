import io, uuid
from sqlalchemy import update
from supabase import create_client
import os
from.db import AsyncSessionLocal
from.models import Job, Result
from.pdf_parser import extract_feedbacks
from.llm import analyze_feedback
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

async def process_job(job_id: uuid.UUID):
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(update(Job).where(Job.id == job_id).values(status="running"))
            await db.commit()

            job = await db.get(Job, job_id)
            res = supabase.storage.from_("pdfs").download(job.file_path)
            pdf_bytes = io.BytesIO(res)

            feedbacks = extract_feedbacks(pdf_bytes)
            result_data = await analyze_feedback(feedbacks)

            db.add(Result(job_id=job_id, **result_data))
            await db.execute(update(Job).where(Job.id == job_id).values(status="completed"))
            await db.commit()

        except Exception as e:
            await db.execute(update(Job).where(Job.id == job_id)
                          .values(status="failed", error=str(e)))
            await db.commit()