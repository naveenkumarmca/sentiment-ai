from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid, datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, default="queued")
    file_path = Column(String)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Result(Base):
    __tablename__ = "results"
    job_id = Column(UUID(as_uuid=True), primary_key=True)
    summary = Column(Text)
    overall_sentiment = Column(String)
    themes = Column(JSON)
    recommended_actions = Column(JSON)
    limitations = Column(Text, nullable=True)