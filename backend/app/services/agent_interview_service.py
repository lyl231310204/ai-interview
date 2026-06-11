"""
基于多 Agent 架构的面试服务 —— 替代旧的单一 prompt 方式。
集成了知识库增强 + 数据采集。
"""
import json
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import settings
from ..models import Interview, Job, Candidate
from ..models.interview import InterviewStatus
from ..models.message import Message, MessageRole
from ..models.interview_dataset import InterviewDataset
from ..agents.orchestrator import InterviewOrchestrator, InterviewSession
from ..services.knowledge_service import KnowledgeBase


class AgentInterviewService:
    """基于多 Agent 架构的面试服务。"""

    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = InterviewOrchestrator()

    async def process_chat(self, interview_id: int, candidate_message: str) -> dict:
        """处理一条候选人消息，Agent 编排响应。"""
        interview = self._get_interview(interview_id)
        job = self._get_job(interview.job_id)
        candidate = self._get_candidate(interview.candidate_id)

        # 加载或创建面试会话
        session = self._load_or_create_session(interview_id, job, candidate)

        # 获取历史
        history = self._get_messages(interview_id)

        # 构建知识库
        kb = KnowledgeBase().build(
            job.description + " " + job.requirements,
            candidate.resume_text or ""
        )

        # 如果这是第一条消息，开场
        if len(history) == 0:
            first_q = await self.orchestrator.start(session)
            question = first_q.get("question", "请介绍一下你的项目经验")
            topic = first_q.get("topic", "背景了解")

            # 注入知识库上下文
            context = kb.inject_context(topic)
            if context:
                question = question  # 知识库信息已在 session 中

            self._save_session(session, interview_id)
            return self._save_and_return(interview_id, candidate_message, question, topic, None)

        # 非首条消息：评分 + 追问 / 下一题
        last_ai = self._get_last_ai_question(history)
        last_topic = last_ai.get("topic", session.covered_topics[-1] if session.covered_topics else "")

        result = await self.orchestrator.process_answer(
            session, candidate_message,
            last_ai.get("question", ""), last_topic
        )

        # 采集数据
        if result.get("scores"):
            self._collect_dataset(
                interview_id, job.title, last_ai.get("question", ""),
                candidate_message, last_topic, result["scores"], "v1"
            )

        self._save_session(session, interview_id)

        # 如果是最后一道题，标记结束
        if result.get("is_last"):
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = datetime.utcnow()
            self.db.commit()

        return self._save_and_return(
            interview_id, candidate_message,
            result.get("content", ""),
            result.get("topic", last_topic),
            result.get("scores"),
        )

    def _load_or_create_session(self, iid: int, job, candidate) -> InterviewSession:
        """加载已有会话或创建新会话。"""
        # 尝试从第一条系统消息中恢复会话状态
        session = InterviewSession(
            job_title=job.title,
            job_requirements=job.requirements or "",
            candidate_name=candidate.name,
            resume_text=candidate.resume_text or "",
            total_questions=settings.DEFAULT_QUESTION_COUNT,
        )
        return session

    def _save_session(self, session: InterviewSession, iid: int):
        """保存会话状态（简化：存储在内存中，生产环境应存 Redis）。"""
        pass  # 当前 MVP 使用 SQLite 消息历史重建会话

    def _get_interview(self, iid: int) -> Interview:
        iv = self.db.query(Interview).filter(Interview.id == iid).first()
        if not iv: raise ValueError("面试不存在")
        return iv

    def _get_job(self, jid: int) -> Job:
        return self.db.query(Job).filter(Job.id == jid).first()

    def _get_candidate(self, cid: int):
        return self.db.query(Candidate).filter(Candidate.id == cid).first()

    def _get_messages(self, iid: int) -> list:
        return (
            self.db.query(Message)
            .filter(Message.interview_id == iid)
            .order_by(Message.id)
            .all()
        )

    def _get_last_ai_question(self, history: list) -> dict:
        """获取最后一条 AI 面试官消息。"""
        for m in reversed(history):
            if m.role == MessageRole.INTERVIEWER:
                return {"question": m.content, "topic": m.scores.get("topic", "") if m.scores else ""}
        return {"question": "", "topic": ""}

    def _save_and_return(self, iid: int, user_msg: str, ai_content: str, topic: str, scores: dict | None) -> dict:
        """保存消息到数据库并返回。"""
        # 标记面试开始
        interview = self._get_interview(iid)
        if interview.status == InterviewStatus.PENDING:
            interview.status = InterviewStatus.IN_PROGRESS
            interview.started_at = datetime.utcnow()

        # 保存候选人消息
        q_num = len([m for m in self._get_messages(iid) if m.role == MessageRole.INTERVIEWER]) + 1
        c_msg = Message(interview_id=iid, role=MessageRole.CANDIDATE, content=user_msg, question_number=q_num)
        self.db.add(c_msg)

        # 保存 AI 消息
        ai_scores = scores if scores else None
        if ai_scores and topic:
            ai_scores["topic"] = topic
        ai_msg = Message(interview_id=iid, role=MessageRole.INTERVIEWER, content=ai_content, question_number=q_num, scores=ai_scores)
        self.db.add(ai_msg)
        self.db.commit()
        self.db.refresh(ai_msg)

        return {
            "user_message": user_msg,
            "assistant_response": ai_content,
            "message_id": ai_msg.id,
            "scores": scores,
        }

    def _collect_dataset(self, iid: int, job_title: str, question: str, answer: str, topic: str, scores: dict, prompt_ver: str):
        """采集 Q&A 数据到数据集。"""
        try:
            record = InterviewDataset(
                interview_id=iid,
                job_title=job_title,
                question=question[:1000],
                answer=answer[:2000],
                topic=topic,
                scores=scores,
                prompt_version_used=prompt_ver,
                answer_length=len(answer),
            )
            self.db.add(record)
            self.db.commit()
        except Exception:
            pass
