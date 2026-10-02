from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "MAHA-GR" in data["message"]
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/v1/health"


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "MAHA-GR"
    assert "services" in data
    assert "supabase_db" in data["services"]
    assert "supabase_storage" in data["services"]
    assert "pinecone" in data["services"]
    assert "gemini_api" in data["services"]
