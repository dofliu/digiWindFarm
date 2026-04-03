from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "version" in data

def test_logs_flow():
    # add a log
    r = client.post("/logs", json={"message": "hello"})
    assert r.status_code == 200
    # list logs
    r = client.get("/logs")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert any(i["message"] == "hello" for i in items)
