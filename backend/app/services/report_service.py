"""
报告生成服务 —— 调用 Claude API 生成终评报告。
"""

import json
from anthropic import AsyncAnthropic
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import settings
from ..models import Interview, Job, Candidate
from ..models.message import Message
from ..prompts.report_prompts import build_report_prompt


class ReportService:
    """报告生成器。"""

    def __init__(self, db: Session):
        self.db = db
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate(self, interview_id: int) -> dict:
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError("面试不存在")

        job = self.db.query(Job).filter(Job.id == interview.job_id).first()
        candidate = self.db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
        messages = (
            self.db.query(Message)
            .filter(Message.interview_id == interview_id)
            .order_by(Message.id)
            .all()
        )

        # 计算时长
        duration = "约30分钟"
        if interview.started_at:
            delta = datetime.utcnow() - interview.started_at
            minutes = int(delta.total_seconds() // 60)
            duration = f"约{minutes}分钟"

        total_questions = len([m for m in messages if m.role == "interviewer"])

        # 构建 Q&A 记录
        qa_parts = []
        for msg in messages:
            if msg.role == "interviewer" and msg.question_number:
                answer = _find_answer(messages, msg.question_number)
                topic = msg.scores.get("topic", "") if msg.scores else ""
                qa_parts.append(
                    f"第{msg.question_number}题 | {topic}\n"
                    f"面试官：{msg.content}\n"
                    f"候选人：{answer}\n"
                )
        qa_records = "\n---\n".join(qa_parts)

        prompt = build_report_prompt(
            job_title=job.title,
            candidate_name=candidate.name,
            duration=duration,
            total_questions=total_questions,
            qa_records=qa_records,
        )

        response = await self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        content = _extract_text_block(response)
        return _parse_report_json(content)


def _parse_report_json(content: str) -> dict:
    """从 AI 回复中提取 JSON。"""
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0].strip()
    elif not content.startswith("{"):
        idx = content.find("{")
        if idx != -1:
            content = content[idx:]
    return json.loads(content)


def _find_answer(messages: list, question_number: int) -> str:
    for msg in messages:
        if msg.role == "candidate" and msg.question_number == question_number:
            return msg.content
    return "（未找到回答）"


def _extract_text_block(response) -> str:
    for block in response.content:
        if block.type == "text" and block.text:
            return block.text
    return response.content[-1].text or ""
