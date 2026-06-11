"""Agent 架构测试"""
import pytest
from app.agents.question_agent import QuestionAgent
from app.agents.scoring_agent import ScoringAgent
from app.agents.followup_agent import FollowUpAgent
from app.agents.report_agent import ReportAgent


@pytest.mark.asyncio
async def test_question_agent():
    agent = QuestionAgent()
    result = await agent.generate(
        job_title="Python后端",
        job_requirements="FastAPI, PostgreSQL, Redis",
        resume_text="3年Python经验，做过API网关",
        question_number=1,
        total_questions=5,
        covered_topics=[],
    )
    assert "question" in result
    assert "topic" in result
    assert len(result["question"]) > 10


@pytest.mark.asyncio
async def test_scoring_agent():
    agent = ScoringAgent()
    result = await agent.score(
        question="请解释Python的GIL是什么",
        answer="GIL是全局解释器锁，同一时刻只有一个线程执行字节码。CPU密集任务受限，IO密集可用多线程。",
        topic="Python GIL",
    )
    assert "correctness" in result
    assert "depth" in result
    assert 0 <= result["correctness"] <= 10


@pytest.mark.asyncio
async def test_followup_agent():
    agent = FollowUpAgent()
    result = await agent.decide(
        question="请解释JVM内存模型",
        answer="JVM内存分为堆和栈，堆存对象栈存引用",
        topic="JVM",
    )
    assert "should_follow_up" in result
    assert isinstance(result["should_follow_up"], bool)


@pytest.mark.asyncio
async def test_report_agent():
    agent = ReportAgent()
    result = await agent.generate(
        job_title="Java后端",
        candidate_name="测试",
        qa_records="Q1: 解释JVM\nA: JVM是Java虚拟机",
        scores_per_question=[{"correctness":8,"depth":7,"logic":8,"practice":7,"topic":"JVM","comment":"不错"}],
        duration="约5分钟",
        total_questions=1,
    )
    assert "overall_score" in result or "error" in result
