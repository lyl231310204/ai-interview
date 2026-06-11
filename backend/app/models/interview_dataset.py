"""
面试数据集 —— 存储结构化的 Q&A 对，用于后续分析和模型微调。
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
from app.database import Base


class InterviewDataset(Base):
    __tablename__ = "interview_datasets"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    job_title = Column(String(200))
    question = Column(Text)
    answer = Column(Text)
    topic = Column(String(200))
    scores = Column(JSON)
    prompt_version_used = Column(String(20))
    answer_length = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
