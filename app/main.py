from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import uuid, os
from supabase import create_client
from dotenv import load_dotenv
from.db import get_db
from.models import Job, Result
from.schemas import JobCreateResponse, JobStatus, ResultResponse
from.worker import process_job

load_dotenv()
app = FastAPI(title="Sentiment AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

@app.post("/jobs", status_code=202, response_model=JobCreateResponse)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type!= "application/pdf":
        raise HTTPException(400, "PDF only")
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(400, "Max 2MB")

    job_id = uuid.uuid4()
    key = f"uploads/{job_id}.pdf"

    supabase.storage.from_("pdfs").upload(key, content, {"content-type": "application/pdf"})

    job = Job(id=job_id, status="queued", file_path=key)
    db.add(job)
    await db.commit()

    background_tasks.add_task(process_job, job_id)
    return {"job_id": job_id}

@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    return job

@app.get("/jobs/{job_id}/result", response_model=ResultResponse)
async def get_result(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.get(Result, job_id)
    if not result: raise HTTPException(404, "Result not ready")
    return result

@app.get("/health")
async def health():
    return {"status": "ok"}