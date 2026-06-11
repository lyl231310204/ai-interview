"""岗位 API 测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, SessionLocal
from app.models import Job

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    yield
    db = SessionLocal()
    db.query(Job).delete()
    db.commit()
    db.close()


def test_create_job():
    resp = client.post("/api/jobs/", json={"title": "测试岗位", "description": "测试描述", "requirements": "Python"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "测试岗位"
    assert data["source"] == "seeker"


def test_create_hr_job():
    resp = client.post("/api/jobs/?role=hr", json={"title": "HR岗位", "description": "D", "requirements": "R"})
    assert resp.status_code == 201
    assert resp.json()["source"] == "hr"


def test_list_jobs():
    client.post("/api/jobs/", json={"title": "A", "description": "D", "requirements": "R"})
    client.post("/api/jobs/", json={"title": "B", "description": "D", "requirements": "R"})
    resp = client.get("/api/jobs/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_delete_job():
    r = client.post("/api/jobs/", json={"title": "待删除", "description": "D", "requirements": "R"})
    jid = r.json()["id"]
    resp = client.delete(f"/api/jobs/{jid}")
    assert resp.status_code == 204
    # 确认已删除
    resp2 = client.get(f"/api/jobs/{jid}")
    assert resp2.status_code == 404
