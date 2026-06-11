"""健康检查测试"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_200():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["message"] == "ok"


def test_health_has_db_status():
    resp = client.get("/api/health")
    assert "db" in resp.json()
