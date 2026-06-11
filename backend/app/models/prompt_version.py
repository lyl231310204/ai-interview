"""
Prompt 版本管理 —— 存储和追踪 AI Prompt 的版本变更。
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database import Base


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    system_prompt = Column(Text, nullable=False)
    description = Column(String(200))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
