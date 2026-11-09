from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_homepage_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Asistente Académico FISI" in response.text


def test_query_rejects_too_short_question():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "hi"},
    )
    assert response.status_code == 422


def test_query_requires_question():
    response = client.post("/api/v1/assistant/query", json={})
    assert response.status_code == 422
