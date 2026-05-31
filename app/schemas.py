from pydantic import BaseModel, UUID4
from typing import List, Optional, Literal
from datetime import datetime

class JobCreateResponse(BaseModel):
    job_id: UUID4

class JobStatus(BaseModel):
    id: UUID4
    status: Literal["queued", "running", "completed", "failed"]
    error: Optional[str] = None
    created_at: datetime

class Theme(BaseModel):
    name: str
    evidence_ids: List[str]

class ResultResponse(BaseModel):
    summary: str
    overall_sentiment: Literal["positive", "neutral", "mixed", "negative"]
    themes: List[Theme]
    recommended_actions: List[str]
    limitations: Optional[str] = None