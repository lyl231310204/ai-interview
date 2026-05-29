"""
面试核心服务 —— 连接数据库、Claude API、消息处理的总调度。
"""

import json
import re
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Interview, Job, Candidate
from ..models.message import Message, MessageRole
from ..prompts.system_prompt import build_system_prompt
from .question_service import build_question_instruction
from .scoring_service import parse_scores


class InterviewService:
    """面试会话管理器。"""

    def __init__(self, db: Session):
        self.db = db
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    # ════════════════════════════════════════════════════════════════
    # 路由器对接方法
    # ════════════════════════════════════════════════════════════════

    async def process_chat(self, interview_id: int, candidate_message: str) -> dict:
        """
        处理一条候选人消息，调用 AI 生成回复，持久化到数据库。
        返回 { user_message, assistant_response, message_id }
        """
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError("面试不存在")

        job = self.db.query(Job).filter(Job.id == interview.job_id).first()
        candidate = self.db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()

        # 获取历史消息
        history = (
            self.db.query(Message)
            .filter(Message.interview_id == interview_id)
            .order_by(Message.id)
            .all()
        )

        # 统计已考察知识点
        covered_topics = []
        for msg in history:
            if msg.scores and isinstance(msg.scores, dict):
                topic = msg.scores.get("topic", "")
                if topic:
                    covered_topics.append(topic)

        question_number = len([m for m in history if m.role == "interviewer"]) + 1

        # 构建 System Prompt
        system_prompt = build_system_prompt(
            job_title=job.title,
            job_description=job.description or "",
            job_requirements=job.requirements or "",
            candidate_name=candidate.name,
            candidate_resume=candidate.resume_text or "",
            total_questions=settings.DEFAULT_QUESTION_COUNT,
        )

        # 调用 AI
        ai_response = await self._call_ai(
            system_prompt=system_prompt,
            history=history,
            candidate_answer=candidate_message,
            question_number=question_number,
            total_questions=settings.DEFAULT_QUESTION_COUNT,
            covered_topics=covered_topics,
        )

        # 持久化
        candidate_msg = Message(
            interview_id=interview_id,
            role=MessageRole.CANDIDATE,
            content=candidate_message,
            question_number=question_number,
        )
        self.db.add(candidate_msg)

        ai_msg = Message(
            interview_id=interview_id,
            role=MessageRole.INTERVIEWER,
            content=ai_response["content"],
            question_number=ai_response.get("question_number"),
            scores=ai_response.get("scores"),
        )
        self.db.add(ai_msg)

        # 首条消息时标记面试开始
        if interview.status.value == "pending":
            from datetime import datetime
            interview.status = interview.status.__class__.IN_PROGRESS
            interview.started_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(ai_msg)

        return {
            "user_message": candidate_message,
            "assistant_response": ai_response["content"],
            "message_id": ai_msg.id,
        }

    async def process_chat_stream(self, interview_id: int, candidate_message: str) -> AsyncGenerator[str, None]:
        """
        SSE 流式版本：逐 token yield AI 回复文本。
        """
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            yield f"data: ERROR: 面试不存在\n\n"
            return

        job = self.db.query(Job).filter(Job.id == interview.job_id).first()
        candidate = self.db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()

        history = (
            self.db.query(Message)
            .filter(Message.interview_id == interview_id)
            .order_by(Message.id)
            .all()
        )

        covered_topics = []
        for msg in history:
            if msg.scores and isinstance(msg.scores, dict):
                topic = msg.scores.get("topic", "")
                if topic:
                    covered_topics.append(topic)

        question_number = len([m for m in history if m.role == "interviewer"]) + 1

        system_prompt = build_system_prompt(
            job_title=job.title,
            job_description=job.description or "",
            job_requirements=job.requirements or "",
            candidate_name=candidate.name,
            candidate_resume=candidate.resume_text or "",
            total_questions=settings.DEFAULT_QUESTION_COUNT,
        )

        # 流式调用 AI
        full_content = ""
        try:
            messages = self._build_messages(
                system_prompt, history, candidate_message,
                question_number, settings.DEFAULT_QUESTION_COUNT, covered_topics,
            )
            async with self.client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=4096,
                temperature=0.5,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text_delta in stream.text_stream:
                    full_content += text_delta
                    yield f"data: {json.dumps({'type': 'token', 'content': text_delta})}\n\n"

            # 解析
            result = self._parse_ai_response(full_content)

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        # 持久化
        candidate_msg = Message(
            interview_id=interview_id,
            role=MessageRole.CANDIDATE,
            content=candidate_message,
            question_number=question_number,
        )
        self.db.add(candidate_msg)

        ai_msg = Message(
            interview_id=interview_id,
            role=MessageRole.INTERVIEWER,
            content=result["content"],
            question_number=result.get("question_number"),
            scores=result.get("scores"),
        )
        self.db.add(ai_msg)

        if interview.status.value == "pending":
            from datetime import datetime
            interview.status = interview.status.__class__.IN_PROGRESS
            interview.started_at = datetime.utcnow()

        self.db.commit()

        # 推送评分
        if result.get("scores"):
            yield f"data: {json.dumps({'type': 'scores', 'question_number': result.get('question_number'), 'scores': result['scores']})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'message_id': ai_msg.id, 'content': result['content'], 'question_number': result.get('question_number')})}\n\n"

    # ════════════════════════════════════════════════════════════════
    # 内部方法
    # ════════════════════════════════════════════════════════════════

    async def _call_ai(self, system_prompt, history, candidate_answer, question_number, total_questions, covered_topics) -> dict:
        messages = self._build_messages(system_prompt, history, candidate_answer, question_number, total_questions, covered_topics)
        response = await self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            temperature=0.5,
            system=system_prompt,
            messages=messages,
        )
        return self._parse_ai_response(_extract_text_block(response))

    def _build_messages(self, system_prompt, history, candidate_answer, question_number, total_questions, covered_topics) -> list[dict]:
        messages = []
        for msg in history:
            role = "assistant" if msg.role == MessageRole.INTERVIEWER else "user"
            messages.append({"role": role, "content": msg.content})
        messages.append({"role": "user", "content": candidate_answer})
        instruction = build_question_instruction(question_number, total_questions, covered_topics)
        messages.append({"role": "user", "content": instruction})
        return messages

    def _parse_ai_response(self, content: str) -> dict:
        cleaned = content.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    data = {"action": "question", "content": content, "question_number": 1, "question_topic": "", "scores": None}
            else:
                data = {"action": "question", "content": content, "question_number": 1, "question_topic": "", "scores": None}

        return {
            "action": data.get("action", "question"),
            "content": data.get("content", content),
            "question_number": data.get("question_number"),
            "question_topic": data.get("question_topic", ""),
            "scores": parse_scores(data.get("scores")),
        }


def _extract_text_block(response) -> str:
    """从 Claude 响应中提取 type='text' 的文本（跳过 thinking block）。"""
    for block in response.content:
        if block.type == "text" and block.text:
            return block.text
    return response.content[-1].text or ""
